+++
title = "Configuring Custom Subnets in Docker"
date = 2022-06-13
type = "til"
description = "Guide to customizing Docker's default subnets to avoid conflicts with existing infrastructure and address errors in multi-project scenarios."
in_search_index = true
[taxonomies]
tags = ["Docker"]
+++

Docker uses `172.17.0.0/16` as the CIDR for it's own network and all the other bridge network it creates. It maybe sometimes useful to change the default subnet to a custom one, in case it conflitcts with other resources (like AWS VPC) in your infra.
Not just this, it can also happen if you've multiple `docker-compose` projects in your server and you face an error similar to:

```bash
ERROR: could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network
```


```bash
$ ip a show docker0

8: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
    link/ether 02:42:18:b7:60:80 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:18ff:feb7:6080/64 scope link
       valid_lft forever preferred_lft forever
```

## Docker-compose
If you're using `docker-compose`, then you can simply update the subnet for the bridge network created in that file by giving custom IPAM options in the network section of the file.

```yml

services:
  app:
    image: app/app:latest
    networks:
      - monitor-net

networks:
  monitor-net:
    ipam:
      driver: default
      config:
        - subnet: 192.168.96.0/27
```

## Docker settings

If you wish to update the base address of `docker0` interface and define these subnets globally, you can update `daemon.json` settings.

```json
{
  "bip": "10.200.0.1/24",
  "default-address-pools":[
    {"base":"10.201.0.0/16","size":24},
    {"base":"10.202.0.0/16","size":24}
  ]
}
```

Add the following to `/etc/docker/daemon.json`

```bash
sudo systemctl restart docker
```

### Verify the settings

```bash
ip a show docker0
```

You should see `10.200.0.1`

### Explanation

1. `"bip": "10.200.0.1/24"`
   - `bip` stands for "Bridge IP".
   - This specifies the IP address and subnet for the Docker daemon's default bridge network. The default bridge network is used for communications between the Docker host and containers that do not specify a network.
   - `10.200.0.1` is the IP address assigned to the bridge interface on the Docker host.
   - `/24` indicates that the subnet mask is 255.255.255.0, which means that the IP addresses from `10.200.0.1` to `10.200.0.254` are available for use by containers connected to this bridge.

2. `"default-address-pools": [...]`
   - This is an array defining pools of network addresses that Docker can use for creating user-defined networks (i.e., networks created using `docker network create`).

   Inside the `default-address-pools` array, we have two objects, each specifying a base subnet and a size for the network pools:

   - `{"base":"10.201.0.0/16","size":24}`
     - This pool defines a range of IP addresses starting with the base `10.201.0.0/16`.
     - `/16` means that any address from `10.201.0.0` to `10.201.255.255` can be used to create smaller subnets.
     - `"size":24` specifies that when Docker creates a user-defined network from this pool, it should use a subnet size of `/24`. Therefore, each user-defined network created from this pool will have a range of IP addresses like `10.201.x.0/24`, where `x` is a variable that increments for each new network, providing 254 usable addresses for each subnet.

   - `{"base":"10.202.0.0/16","size":24}`
     - Similar to the first pool, but this uses the `10.202.0.0/16` range.
     - Again, the `"size":24` means that Docker will create user-defined networks with a `/24` subnet from this range, for example `10.202.x.0/24`, where `x` is an incrementing value.

## Ref
- [https://straz.to/2021-09-08-docker-address-pools/](https://straz.to/2021-09-08-docker-address-pools/)
- [https://github.com/docker/docker.github.io/issues/8663#issuecomment-956438889](https://github.com/docker/docker.github.io/issues/8663#issuecomment-956438889)
- [https://serverfault.com/questions/916941/configuring-docker-to-not-use-the-172-17-0-0-range](https://serverfault.com/questions/916941/configuring-docker-to-not-use-the-172-17-0-0-range)
