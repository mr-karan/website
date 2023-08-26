+++
date = "2023-07-17T05:45:04+00:00"
description = "A practical guide which delves into Linux network namespaces, iptables and routing to understand bridge networking in Nomad"
in_search_index = true
slug = "bridge-network-in-nomad"
title = "Bridge Networking in Nomad"
type = "post"

[taxonomies]
  tags = ["nomad", "networking"]

+++
To set the stage, it's crucial to understand what we mean by "bridge networking". In a nutshell, it is a type of network connection in Linux that allows virtual interfaces, like the ones used by virtual machines and containers, to share a physical network interface.

With Nomad, when a task is allocated, it creates a network namespace with its own network stack. Within this, a virtual ethernet (veth) pair is established, one end of which is assigned to the network namespace of the allocation, and the other remains in the host namespace.

![](/images/bridge-network-in-nomad-4.png)

## **The Network Journey**

To illustrate this practically, let's assume a packet is sent from a task within an allocation. The packet would first be received by the local end of the veth pair, it would then traverse to the other end residing in the host's namespace. From there, it is sent to the bridge on the host (in this case, the "nomad" bridge), which finally sends the packet out to the world via the host's physical network interface (typically "eth0" or equivalent in your machine).

The journey of a packet from the outside world to a task inside an allocation is the exact mirror image. The packet reaches "eth0" first, then the nomad bridge, it is then forwarded to the appropriate veth interface in the host's namespace. From there, it crosses over to the other end of the veth pair in the allocation's network namespace and finally gets routed to the destination task.

## To bridge or not to

Let's take a look at the following jobspec which is for deploying my tiny side project - [Cloak](https://github.com/mr-karan/cloak) on Nomad

```hcl
job "cloak" {
  datacenters = ["dc1"]
  type        = "service"

  group "redis" {
    network {
      mode = "host"
      port "redis" {
        to = 6379
      }
    }

    service {
      name     = "cloak-redis"
      port     = "redis"
      provider = "nomad"
    }


    task "redis" {
      driver = "docker"


      config {
        image                  = "redis:7"
        advertise_ipv6_address = false

        ports = [
          "redis",
        ]

        volumes = [
          "/data/cloak/redis:/data",
        ]
      }

      resources {
        cpu    = 500 # MHz
        memory = 256 # MB
      }
    }
  }

  group "cloak" {
    network {
      mode = "host"
      port "cloak" {
        static = 7000
        to     = 7000
      }
    }

    task "cloak" {
      driver = "docker"

      config {
        image   = "ghcr.io/mr-karan/cloak:v0.2.0"
        command = "--config=config.toml"
        ports = [
          "cloak",
        ]
      }

      template {
        data        = <<EOH
# Configuration for 1 redis instances, as assigned via rendezvous hashing.
{{$allocID := env "NOMAD_ALLOC_ID" -}}
{{range nomadService 1 $allocID "cloak-redis"}}
CLOAK_REDIS__address={{ .Address }}:{{ .Port }}
{{- end}}
EOH
        destination = "secrets/file.env"
        env         = true
      }


      resources {
        cpu    = 500 # MHz
        memory = 700 # MB
      }
    }
  }
}
```

Our focus should be on the `network.mode` stanza. To illustrate what happens behind the scenes when an alloc runs in `network.mode=host` (host network), we can run the above job.

On the machine, we can see that port 7000 (static) and port 27042 (dynamic) are allocated on the host network interface (eth0):

![](/images/bridge-network-in-nomad-1.png)

We can also see the port and process details using `ss`:

```bash
sudo ss -ltpn 'sport = :7000'
State    Recv-Q   Send-Q      Local Address:Port       Peer Address:Port   Process
LISTEN 0 4096      95.216.165.210:7000    0.0.0.0:*  users:(("docker-proxy",pid=67068,fd=4))
```

This config is more suitable for specific workloads - like load balancers or similar deployments where you want to expose the network interface on the host. It's also helpful for applications running outside of Nomad on that host to connect via the host network interface.

However, typically in a job where you want to connect to multiple different allocs - you'd want to set up a bridge network. This generally avoids exposing the workload on the host network directly. It's a typical setup where you want to put applications behind a reverse proxy (NGINX/Caddy).

Let's change `network.mode=bridge` in the above job spec and see the changes.

```sh
$ nomad job plan cloak.nomad

+/- Job: "cloak"
+/- Task Group: "cloak" (1 create/destroy update)
  + Network {
      Hostname: ""
    + MBits:    "0"
    + Mode:     "bridge"
    + Static Port {
      + HostNetwork: "default"
      + Label:       "cloak"
      + To:          "7000"
      + Value:       "7000"
      }
    }
  - Network {
      Hostname: ""
    - MBits:    "0"
    - Mode:     "host"
    - Static Port {
      - HostNetwork: "default"
      - Label:       "cloak"
      - To:          "7000"
      - Value:       "7000"
      }
    }
    Task: "cloak"

+/- Task Group: "redis" (1 create/destroy update)
  + Network {
      Hostname: ""
    + MBits:    "0"
    + Mode:     "bridge"
    + Dynamic Port {
      + HostNetwork: "default"
      + Label:       "redis"
      + To:          "6379"
      }
    }
  - Network {
      Hostname: ""
    - MBits:    "0"
    - Mode:     "host"
    - Dynamic Port {
      - HostNetwork: "default"
      - Label:       "redis"
      - To:          "6379"
      }
    }
    Task: "redis"
```

Now we don't see the ports forwarded on the host network:

![](/images/bridge-network-in-nomad-2.png)

Similarly, `ss` also shows no process listening on the host network

![](/images/bridge-network-in-nomad-3.png)

## **IPTables and Routing**

To understand what happened when we switched the networking mode to `bridge`, we need to take a look at the Nomad `iptables` magic which comes into play when using `bridge` network.

I pulled up the `iptables` and saw specific rules under the chains `CNI-FORWARD` and `NOMAD-ADMIN`. These rules, in essence, allow all traffic to and from the allocation's network namespace.

```sh
$ sudo iptables -L CNI-FORWARD
Chain CNI-FORWARD (1 references)
target     prot opt source               destination         
NOMAD-ADMIN  all  --  anywhere             anywhere             /* CNI firewall plugin admin overrides */
ACCEPT     all  --  anywhere             172.26.64.5          ctstate RELATED,ESTABLISHED
ACCEPT     all  --  172.26.64.5          anywhere            
ACCEPT     all  --  anywhere             172.26.64.6          ctstate RELATED,ESTABLISHED
ACCEPT     all  --  172.26.64.6          anywhere

sudo iptables -L NOMAD-ADMIN
Chain NOMAD-ADMIN (1 references)
target     prot opt source               destination         
ACCEPT     all  --  anywhere             172.26.64.0/20
```

Nomad uses `172.26.64.0/20` as the [default subnet](https://developer.hashicorp.com/nomad/docs/configuration/client#bridge_network_subnet) for the bridge network. The IPs `172.26.64.5` and `172.26.64.6` are assigned to 2 different allocs in this CIDR. The `iptables` rules allow complete traffic to flow on this subnet.

To check the routing,`ip route` command can be used.

```sh
$ ip route show 172.26.64.0/20
172.26.64.0/20 dev nomad proto kernel scope link src 172.26.64.1
```

It uses the `nomad` network interface for routing packets related to the default bridge network.

Using `nsenter` we can find more details about the network namespace created for an alloc. Let's find details about the `redis` alloc:

```bash
sudo nsenter -t $(pgrep redis) --net ip addr

1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0@if113: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 76:47:6d:49:00:c0 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.26.64.5/20 brd 172.26.79.255 scope global eth0
       valid_lft forever preferred_lft forever

```

We can see that one end of the pair is `eth0` (container's default gateway) which is connected to a network interface with an index `113`. For the tunnel to actually work, the veth pair should also exist on the host:

```sh
$ ip a
113: veth3402deda@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master nomad state UP group default 
    link/ether 3a:85:1b:37:75:17 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet6 fe80::3885:1bff:fe37:7517/64 scope link 
       valid_lft forever preferred_lft forever
```

So, when we see `veth3402deda@if2` in the host's network namespace (with the index `113`), and then we see `eth0@if113` inside the Redis container, we can infer that these two interfaces form a `veth` pair: `veth3402deda@if2` on the host side and `eth0` inside the container. This connection enables the container to communicate with the external network through the host's network stack.

## Capturing packets

We can capture TCP packets on the `veth` interface to see the routing work:

```sh
sudo tcpdump -i veth971858d5 -n
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on veth971858d5, link-type EN10MB (Ethernet), snapshot length 262144 bytes
10:51:27.801319 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [S], seq 1331933249, win 65495, options [mss 65495,sackOK,TS val 248300785 ecr 0,nop,wscale 7], length 0
10:51:27.801549 IP 172.26.64.6.7000 > 172.26.64.1.35826: Flags [S.], seq 107697826, ack 1331933250, win 65160, options [mss 1460,sackOK,TS val 3965422857 ecr 248300785,nop,wscale 7], length 0
10:51:27.801616 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [.], ack 1, win 512, options [nop,nop,TS val 248300785 ecr 3965422857], length 0
10:51:27.801737 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [P.], seq 1:79, ack 1, win 512, options [nop,nop,TS val 248300786 ecr 3965422857], length 78
10:51:27.801751 IP 172.26.64.6.7000 > 172.26.64.1.35826: Flags [.], ack 79, win 509, options [nop,nop,TS val 3965422858 ecr 248300786], length 0
10:51:27.802022 IP 172.26.64.6.7000 > 172.26.64.1.35826: Flags [P.], seq 1:4097, ack 79, win 509, options [nop,nop,TS val 3965422858 ecr 248300786], length 4096
10:51:27.802059 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [.], ack 4097, win 491, options [nop,nop,TS val 248300786 ecr 3965422858], length 0
10:51:27.802120 IP 172.26.64.6.7000 > 172.26.64.1.35826: Flags [P.], seq 4097:5396, ack 79, win 509, options [nop,nop,TS val 3965422858 ecr 248300786], length 1299
10:51:27.802135 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [.], ack 5396, win 502, options [nop,nop,TS val 248300786 ecr 3965422858], length 0
10:51:27.803484 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [F.], seq 79, ack 5396, win 512, options [nop,nop,TS val 248300787 ecr 3965422858], length 0
10:51:27.803567 IP 172.26.64.6.7000 > 172.26.64.1.35826: Flags [F.], seq 5396, ack 80, win 509, options [nop,nop,TS val 3965422859 ecr 248300787], length 0
10:51:27.803597 IP 172.26.64.1.35826 > 172.26.64.6.7000: Flags [.], ack 5397, win 512, options [nop,nop,TS val 248300787 ecr 3965422859], length 0
10:53:08.523431 IP 172.26.64.6.53042 > 95.216.165.210.27372: Flags [.], ack 2169295212, win 501, options [nop,nop,TS val 735542538 ecr 4133067854], length 0
10:53:08.523551 IP 95.216.165.210.27372 > 172.26.64.6.53042: Flags [.], ack 1, win 509, options [nop,nop,TS val 4133379150 ecr 735231242], length 0
10:53:08.523554 IP 95.216.165.210.27372 > 172.26.64.6.53042: Flags [.], ack 1, win 509, options [nop,nop,TS val 4133379150 ecr 735231242], length 0
10:53:08.523562 IP 172.26.64.6.53042 > 95.216.165.210.27372: Flags [.], ack 1, win 501, options [nop,nop,TS val 735542538 ecr 4133379150], length 0

```

To summarize the output, we can see that the log is showing a TCP connection between 172.26.64.1 (source) and 172.26.64.6 (destination), specifically on port 7000. `172.26.64.1` happens to be the gateway for `nomad` subnet.

## Summary

Hope this post clarified some networking internals and behind the scenes magic when using Nomad bridge networking. Refer to my other post - [Nomad networking explained](/posts/nomad-networking-explained/) for a practical breakdown of all the different ways to expose and connect applications in a Nomad cluster.

Fin!

