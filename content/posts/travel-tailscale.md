+++
title = "Travelling with Tailscale"
date = 2024-03-27
type = "post"
description = "How I used Tailscale exit nodes and various IP routing hacks to achieve selective routing with exit nodes"
in_search_index = true
[taxonomies]
tags= ["Linux", "Devops", "Networking"]
+++

I have an upcoming trip to Europe, which I am quite excited about. I wanted to set up a Tailscale exit node to ensure that critical apps I depend on, such as banking portals continue working from outside the country. Tailscale provides a feature called "Exit nodes". These nodes can be setup to route all traffic (0.0.0.0/0, ::/0) through them.

I deployed a tiny DigitalOcean droplet in `BLR` region and setup Tailscale as an exit node. The steps are quite simple and can be found [here](https://tailscale.com/kb/1103/exit-nodes).

```bash
$ echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
$ echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
$ sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
$ sudo tailscale up --advertise-exit-node
```

The node is now advertised as an exit node, and we can confirm that from the output of `tailscale status`:

```bash
$ sudo tailscale status                       
100.78.212.33   pop-os               mr-karan@    linux   -
100.75.180.88   homelab              mr-karan@    linux   -
100.100.191.57  iphone               mr-karan@    iOS     offline
100.123.189.14  karans-macbook-pro   mr-karan@    macOS   offline
100.104.67.7    lab                  mr-karan@    linux   offline
100.108.220.87  tailscale-exit       mr-karan@    linux   active; exit node; direct 167.71.236.222:41641, tx 21540 rx 17356
```

On the client side, I was able to start Tailscale and configure it to send all the traffic to the exit node with:

```bash
sudo tailscale up --exit-node=100.108.220.87
```

We can confirm that the traffic is going via the exit node by checking our public IP from this device:

```bash
➜ curl  https://ipinfo.io 
{
  "ip": "167.x.x.222",
  "city": "Doddaballapura",
  "region": "Karnataka",
  "country": "IN",
  "loc": "13.2257,77.5750",
  "org": "AS14061 DigitalOcean, LLC",
  "postal": "560100",
  "timezone": "Asia/Kolkata",
  "readme": "https://ipinfo.io/missingauth"
}                            
```

However, I encountered a minor issue since I needed to bring my work laptop for on-call duties, in case any critical production incidents required my attention during my travels. At my organization, we use Netbird as our VPN, which, like Tailscale, creates a P2P overlay network between different devices.

The problem was that all 0.0.0.0 traffic was routed to the exit node, meaning the internal traffic meant for Netbird to access internal sites on our private AWS VPC network was no longer routed via the Netbird interface.

Netbird automatically propagates a bunch of IP routing rules when connected to the system. These routes are to our internal AWS VPC infrastructure. For example:

```bash
10.0.0.0/16 via 100.107.12.215 dev wt0
```

Here, `wt0` is the Netbird interface. So, for example, any IP like `10.0.1.100` will go via this interface. To verify this:


```bash
$ ip route get 10.0.1.100
10.0.1.100 dev wt0 src 100.107.12.215 uid 1000 
```

However, after connecting to the Tailscale exit node, this was no longer the case. Now, even the private IP meant to be routed via Netbird was being routed through Tailscale:

```bash
$ ip route get 10.0.1.100
10.0.1.100 dev tailscale0 table 52 src 100.78.212.33 uid 1000 
```

Although Tailscale nodes allow for the selective whitelisting of CIDRs to route only the designated network packets through them, my scenario was different. I needed to selectively bypass certain CIDRs and route all other traffic through the exit nodes. I came across a relevant [GitHub issue](https://github.com/tailscale/tailscale/issues/1916), but unfortunately, it was closed due to limited demand.

This led me to dig deeper into understanding how Tailscale propagates IP routes, to see if there was a way for me to add custom routes with a higher priority.

Initially, I examined the IP routes for Tailscale. Typically, one can view the route table list using `ip route`, which displays the routes in the `default` and `main` tables. However, Tailscale uses routing table 52 for its routes, instead of the default or main table.

```bash
$ ip route show table 52                                                           

default dev tailscale0 
100.75.180.88 dev tailscale0 
... others ...
throw 127.0.0.0/8 
192.168.29.0/24 dev tailscale0 
```

A few notes on the route table:

- `default dev tailscale0` is the default route for this table. Traffic that doesn’t match any other route in this table will be sent through the `tailscale0` interface. This ensures that any traffic not destined for a more specific route will go through the Tailscale network.

- `throw 127.0.0.0/8`: This is a special route that tells the system to "throw" away traffic destined for 127.0.0.0/8 (local host addresses) if it arrives at this table, effectively discarding it before it reaches the local routing table.

We can see the priority of these IP rules are evaluated using `ip rule show`:

```bash
➜ ip rule show          
0:	from all lookup local
5210:	from all fwmark 0x80000/0xff0000 lookup main
5230:	from all fwmark 0x80000/0xff0000 lookup default
5250:	from all fwmark 0x80000/0xff0000 unreachable
5270:	from all lookup 52
32766:	from all lookup main
32767:	from all lookup default
```

This command lists all the current policy routing rules, including their priority (look for the pref or priority value). Each rule is associated with a priority, with lower numbers having higher priority.

By default, Linux uses three main routing tables:

- Local (priority 0)
- Main (priority 32766)
- Default (priority 32767)

Since Netbird already propagates the IP routes in the main routing table, we only need to add a higher priority rule to lookup in the `main` table before Tailscale takes over.

```bash
$ sudo ip rule add to 10.0.0.0/16 pref 5000 lookup main
```

Now, our `ip rule` looks like:

```bash
$ ip rule show          
0:	from all lookup local
5000:	from all to 10.0.0.0/16 lookup main
5210:	from all fwmark 0x80000/0xff0000 lookup main
5230:	from all fwmark 0x80000/0xff0000 lookup default
5250:	from all fwmark 0x80000/0xff0000 unreachable
5270:	from all lookup 52
32766:	from all lookup main
32767:	from all lookup default
```

To confirm whether the packets for destination `10.0.0.0/16` get routed via `wt0` instead of `tailscale0`, we can use the good ol' `ip route get`:

```bash
$ ip route get 10.0.1.100 
10.0.1.100 dev wt0 src 100.107.12.215 uid 1000
```

Perfect! This setup allows us to route all our public traffic via exit node and only the internal traffic meant for internal AWS VPCs get routed via Netbird VPN.

Since, these rules are ephemeral and I wanted to add a bunch of similar network routes, I created a small shell script to automate the process of adding/deleting rules:

```bash
#!/bin/bash

# Function to add IP rules for specified CIDRs
add() {
    echo "Adding IP rules..."
    sudo ip rule add to 10.0.0.0/16 pref 5000 lookup main
    # ... others ...
}

# Function to remove IP rules based on preference numbers
remove() {
    echo "Removing IP rules..."
    sudo ip rule del pref 5000
    # ... others ....
}

# Check the first argument to determine which function to call
case $1 in
    add)
        add
        ;;
    remove)
        remove
        ;;
    *)
        echo "Invalid argument: $1"
        echo "Usage: $0 add|remove"
        exit 1
        ;;
esac
```

Fin!
