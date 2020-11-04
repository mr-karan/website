+++
title = "sshuttle - A better ssh tunnel"
date = 2020-01-12T09:57:55+05:30
type = "post"
description = "Poor man's VPN"
in_search_index = true
[taxonomies]
tags = ["Networking"]
+++

## The Motivation

Sometime back I had to access a Kubernetes API server which was firewalled to a private VPC network. I didn't want to setup a separate bastion instance just to access this cluster, cause TBH bastions are kinda redundant in K8s as every task can be performed through the client-server APIs using `kubectl`. So, all I needed was access to this API server from a trusted network in a secure way. Thanks to my friend [@sarat](https://twitter.com/iamd3vil), I got to know about [sshuttle](https://sshuttle.readthedocs.io/en/stable/). `sshuttle` is quite unique in the sense that it's not really a VPN but acts like one (for most practical purposes). `sshuttle` lets you access an internal network through a trusted node inside the VPC, without you having to deal with the mess of port forwarding or VPNs.

The basic idea is pretty simple, `sshuttle` starts a local `python` server in your host machine and creates `iptables` rules to route the destination packets of the specified CIDR blocks to this local server. At the server, the packets are multiplexed over an `ssh` session and sent to the server. The server disassembles the multiplexed packet and the routes them to upstream. So, basically this is a clever hack to avoid TCP over TCP (which again is a mess on unreliable networks). Multiplexed streams on `ssh` is just a single stateful TCP connection (as compared to VPN connections which are stateless). Now you must be wondering, how come the target server disassembles the packets. Yes, there needs to be some kind of `sshuttle` daemon running which does that for you. This is where `sshuttle` does some magic, it _automagically_ deploys a python script on your target host to perform this task. So yes, for `sshuttle` to work, both the client and target need to have `python ` and `iptables` installed.

### Usage

`sshuttle -r user@port x.x.x.x`

All the packets routed to the CIDR block will now go through `sshuttle` daemon, since it configured `iptables` rules for them.
Also, `sshuttle` starts a local python server on your host machine. You can see it using `netstat`:

```shell
$ sudo netstat -tunapl | grep python
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:12300         0.0.0.0:*               LISTEN      27425/python
```

There's a `python` server listening on port `12300` in my host machine. To actually verify, this indeed is started by `sshuttle`, you can use `pstree -p | less` and search for `sshuttle`. Here you can see `sshuttle` did indeed start a `python` server and the PID (`27425`) matches with the one we saw in `netstat` command.

```shell
    -zsh(13201)---sshuttle(27425)-+-ssh(27446)---ssh(27447)
                                    `-sudo(27427)---python(27445)
```

You can even forward DNS queries with the `--dns` flag. This is super helpful if you have something like Route53 to host your DNS records on a private zone (for eg tld like `.internal`).

### Better than SSH tunnels?

Yes, you can also port forward with ssh using:
`ssh -nNT -L <local-port>:{upstream-host}:{upstream-port} user@remote`

The problem with `ssh` tunnels is that they experience frequent packet loss on a normal WiFi connection and it's quite frustrating to deal with them. Moreover, sometimes you need access to multiple ports in your private network which requires you to explictly provide them with `-L` flag which I find it as cumbersome. Also, you cannot forward DNS queries (over UDP) since `ssh` can only do TCP.

`sshuttle` has made my life so simple!

Fin!
