+++
title = "Use netcat for port scanning"
date = 2020-01-11T08:10:55+05:30
type = "post"
description = "A very quick guide to debug port connectivity issues"
in_search_index = true
[taxonomies]
tags = ["Networking"]
+++

Quite often you'd need to check if a port on a target node is opened or blocked by firewall. I've always used `telnet` to test that but it has a few drawbacks:

- Need to use dirty [hacks](https://stackoverflow.com/questions/41476089/auto-exit-telnet-command-back-to-prompt-without-human-intervention-quit-close) in shell scripts to auto close the connection. Also, telnet outputs some errors to `/dev/stdout` instead of the standard `/dev/stderr` which makes it harder to use in scripts.

- Non standard implementation across different OSes. On Alpine Linux (mostly used in containers), if you install telnet using the `/busybox-extras` package, the behaviour is different from what it is on standard Ubuntu/Arch environments. I've even faced weird issues on Alpine where telnet will simply wait endlessley for the connection to be established, while netcat would not indicate any issues.

- Telnet is actually a protocol and the telnet-client initiates the [negotiation](http://mud-dev.wikidot.com/telnet:negotiation) with the server before a connection is established.

So, after all these issues, I looked at other tools to eventually replace `telnet` with something better. I tried `nmap` which is also a port scanner, but is unreliable since a lot of hipster sysadmins drinking the security koolaid block port scanning tools like these. I wanted a dependable tooling and after a bit of Google-fu, I stumbled across `netcat`.

`netcat` is basically a swiss army knife to perform all kind of ops with TCP/UDP. You can create a file server, chat client/server, TCP client etc. We are simply interested in the port scanning abilities of this for this blog post, so let's actually see how to use it for the same.

**Note**: Install `netcat-openbsd` as it is a rewritten version of `netcat-traditional` with some more bells and whistles.

The basic syntax for port scanning looks like:

`nc -z host port`

`-z` tells nc to not send any data, just _scan_ for any process listening on the target port. This is much better (and faster) than `telnet` client initiating a connection with the upstream.

To make it more usable however, let's pepper our command with some helpful flags:

`nc -vz -w 3 host port`

`-v` turns on verbose mode which outputs diagnostic messages. `-w` adds the timeout for the connection to be established. If you want to set a timeout in `telnet` there's a [hack](https://unix.stackexchange.com/questions/224623/telnet-command-with-custom-timeout-duration) for it.

You can even supply a range of ports to netcat like:

`nc -vz -w 3 host 8000-9000`

_Quick Tip_: You can also give an alias for port instead of the number. For example:

```shell
$nc -vz -w 3 google.com https
Connection to google.com 443 port [tcp/https] succeeded!

$nc -vz -w 3 google.com ssh
nc: connect to google.com port 22 (tcp) timed out: Operation now in progress
nc: connect to google.com port 22 (tcp) failed: Network is unreachable
```

Hope this post pretty much sums up the usage of netcat for port scanning! Read the [man page](https://linux.die.net/man/1/nc) for more info.

Fin!
