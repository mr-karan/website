+++
title = "TIL: WireGuard's Misleading \"No Route to Host\" Error"
date = 2025-07-30
type = "post"
description = "Why firewalld silently drops TCP traffic while letting pings through"
in_search_index = true
[taxonomies]
tags = ["Networking", "WireGuard", "Firewall"]
+++

I recently spent some time debugging a WireGuard tunnel that was acting weird. The handshake was successful, pings worked perfectly, but any TCP connection failed with `connect: no route to host`. 

Classic misleading error message. The routing was fine.

## The Setup

Server with a public IP running WireGuard (`wg0`) with IP `10.100.0.1/24`. Client connects and gets assigned `10.100.0.2/32`. I wanted to proxy TCP traffic from the server to a service running on the client at `10.100.0.2:7778`.

## The Investigation

Diagnostics showed contradictory results:

**Routing worked fine:** Server routing table correctly directed `10.100.0.0/24` traffic to `wg0`. Pings were successful:

```bash
# On the server
$ ping -c 3 10.100.0.2
PING 10.100.0.2 (10.100.0.2) 56(84) bytes of data.
64 bytes from 10.100.0.2: icmp_seq=1 ttl=64 time=150 ms
...
```

**TCP failed immediately:**

```bash
# On the server
$ curl -v http://10.100.0.2:7778
* Trying 10.100.0.2:7778...
* connect to 10.100.0.2 port 7778 from 10.100.0.1 port 59812 failed: No route to host
```

The key insight: `ICMP` was being treated differently than `TCP`. This pointed to a firewall issue, not routing. The "no route to host" error was the kernel interpreting an ICMP "Destination Unreachable" message from the remote peer.

But when I ran `tcpdump` on the client, things got stranger:

```bash
# On the client
$ sudo tcpdump -i any -n 'host 10.100.0.1'

# Output when the server tries to connect
17:36:03.043147 wg0 In  IP 10.100.0.1.14808 > 10.100.0.2.7778: Flags [S], seq 324784341, win 42780, ...
```

The `TCP SYN` packet arrived successfully through `wg0`. But no response. No `SYN-ACK` (success), no `ICMP` error (rejection). The packet was being silently dropped.

## The Culprit: `firewalld`

The client was running Arch Linux with `firewalld`. My mistake was trying to manage firewall rules with `iptables` commands in the WireGuard `PostUp` script. While `iptables` was installed, `firewalld` was the active manager, using `nftables` as its backend.

When a new interface like `wg0` comes up, `firewalld` needs to know which "zone" it belongs to. If unassigned, it gets handled by a restrictive default policy that silently `DROP`s unsolicited TCP packets while allowing ICMP (pings).

## The Fix

Don't add `iptables` rules. Just assign the WireGuard interface to the right `firewalld` zone. For internal tunnels, `trusted` works well.

On the **client**:

```bash
sudo firewall-cmd --permanent --zone=trusted --add-interface=wg0
sudo firewall-cmd --reload
```

TCP connections worked instantly after this.

**TL;DR:** If WireGuard pings work but TCP fails with "no route to host", it's probably a client firewall issue. On `firewalld` systems, assign the WireGuard interface to the right zone instead of messing with `iptables`.

Fin!