+++
title = "Debugging DNS Issues in Nomad"
date = 2022-07-14T00:00:00+05:30
type = "post"
description = "Debugging and solving DNS Issues when running Kafka clients inside a Nomad cluster"
in_search_index = true
[taxonomies]
tags = ["DNS", "Nomad"]
[extra]
og_preview_img = "/images/haiku-dns.png"
+++

At work, my colleagues and I stumbled upon a hair-pulling networking issue involving a specific problem when connecting to a Kafka cluster. We use the [franz-go](https://github.com/twmb/franz-go) library in our Golang applications to interact with an external Kafka cluster. These Go apps are hosted inside a [Nomad](https://www.nomadproject.io/) cluster and running with the [exec](https://www.nomadproject.io/docs/drivers/exec) driver.

## The Issue

Solving issues where a specific condition happens _only_ sometimes is terribly difficult to debug because you need to reproduce the bug in a controlled environment. Our issue was that writing the **first** message to a Kafka topic took unusually high time (>5 seconds) while the writes of subsequent messages were instant. The following messages were instant for the next 30s, and then the write again took >5s.

The request flow looks something like this:

_Go app in Nomad cluster (bridge mode) -> Kafka node in a Kafka cluster_

Both apps are inside the same VPC running on AWS EC2 instances. The Nomad task is running with `network.mode=bridge`, which means that there are some `iptables` rules configured to do SNAT/DNAT translation to forward packets from the default bridge network (`nomad`) to the default ethernet interface (`ens5`).

We have a couple of other Nomad clusters in our environment and regularly use external EC2 instances to communicate, and we've never observed any slowdowns in our existing applications. This behaviour seemed something specific to Kafka. However, we discovered that we could not reproduce the high wait time issue in Kafka when the message was sent from a task running as _host_ mode. So now, we had two conflicting things which made this issue strange:

- Issue happens in `bridge` mode, not in `host` mode.
- Issue happens only with Kafka nodes, not with any external services - even in bridge mode.

We spent a lot of time dissecting our apps, turning on `TRACE` level logging for Kafka clusters and enabling debug mode in `franz-go`. One of the significant challenges for us was that even an idle Kafka cluster could be super **chatty**, producing ~1Mn records for a few minutes when run with `TRACE`. Cutting through the noise and finding the exact point where the slowdown happened turned out to be more difficult than expected.

However, with the debug logs in `franz-go`, we'd arrived at a breakthrough which helped us narrow down the issue. We saw the `write_wait` time to be ~5s in the logs [emitted](https://github.com/twmb/franz-go/blob/6c87885d13a36dfadd42ffa2c2c58cb81646a93a/pkg/kgo/broker.go#L969) by `franz-go`. The subsequent messages had `write_wait` as low as a few microseconds. What was puzzling was why Kafka took so much time to wait before writing the bytes to the underlying socket.

We forked the franz-go library and added a bunch of our custom logs to figure out where and why exactly the slowdown happens. One issue in the logs emitted by franz-go was that no timestamps were attached to the logger. We added that and deployed the binaries with the patched version. This time we immediately found the logs, which pointed that it took ~5s from the time it [initiated the connection](https://github.com/twmb/franz-go/blob/6c87885d13a36dfadd42ffa2c2c58cb81646a93a/pkg/kgo/broker.go#L570) to the Kafka broker node and the time it was able to [connect to the node](https://github.com/twmb/franz-go/blob/6c87885d13a36dfadd42ffa2c2c58cb81646a93a/pkg/kgo/broker.go#L570).

## The Fix

The node's address was an internal hostname `kafka-abc.private-zone.internal`. We postulated that it could be a DNS resolver issue. We did a `dig kafka-abc.private-zone.internal` and instantly got the record. Maybe it's cached? We decided to verify the `/etc/resolv.conf` till we waited for the TTL of the record to expire. Opening this seemingly innocent `/etc/resolv.conf` revealed what the issue was DNS indeed. 

```
nameserver bad
nameserver good
```

We had an _unreachable_ nameserver address in the `nameserver` list. The first message has ~5s write timeout because `/etc/resolv.conf` has a 5s default timeout in case the nameserver is unreachable. Go's DNS resolver picked up the second resolver, which cached the DNS records until the record's TTL (30 seconds). Subsequent Kafka write messages on the topic worked without any issues in the TTL window. When the DNS record expires, rinse, and repeat. We later found the source of the bad nameserver came from our Nomad client initialising script.

## Takeaways

We use a custom Nomad client initialising script in our Nomad clusters to populate the `chroot_env`. Since, by default, the [chroot](https://www.nomadproject.io/docs/drivers/exec#chroot) provided by Nomad copies the`/usr`/ directory, we found that it increased the initial startup time of the alloc. It made sense to customise the `chroot_env` with the list of binaries and config files we would need.

One of the configs happens to be `/etc/resolv.conf`, which DNS resolvers use to resolve queries. On the host, we have `systemd-resolve` running and `/etc/resolv.conf` is configured with the stub resolver address. However, since that address (`127.0.0.53`) is unreachable by the _bridge_ network in Nomad, we mount our custom config, which looks like:

```
nameserver 10.100.0.2
options edns0 trust-ad
search ap-south-1.compute.internal
```

The `nameserver` represents the AWS R53 resolver running in all VPCs if configured with [enableDnsSupport](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html) in VPC settings.

The above config ensures that all DNS queries for the tasks inside the bridge network go directly to the AWS R53 resolver. The resolver can do DNS Lookups for the private zones associated with the R53 in that VPC and forward all other hostnames to their own upstream DNS resolver.

### Fun Fact

If you don't mount a custom `/etc/resolv.conf`, then DNS resolution is broken by default in any Nomad exec task. You can quickly reproduce it with this task definition:

```hcl
job "sleep" {
  datacenters = ["dc1"]
  type        = "service"
  group "sleep" {
    count = 1
    task "sleep" {
      driver = "exec"
      config {
        command = "bash"
        args    = ["-c", "sleep infinity"]
      }
    }
  }
}
```

Run a Nomad agent in `-dev` mode:

```bash
nomad agent -dev
nomad run sleep.nomad
```

When you exec inside the alloc:

```bash
$ nomad alloc exec -i -t -task sleep 8b4a0a82 /bin/sh
$ cat /etc/resolv.conf
nameserver 127.0.0.1
$ dig mrkaran.dev
;; communications error to 127.0.0.1#53: connection refused
```

I believe Nomad should bootstrap some DNS resolver or a relevant `iptables` rule for the exec tasks so that DNS can be resolved by default without the need to mount a custom config. For comparison, a `docker` also bootstraps the container with a customisable `/etc/resolv.conf`, and the settings can be specified either at runtime and fallback to the global settings in `/etc/docker/daemon.json`.

---

I hope this post helps someone solve these weird DNS issues when running tasks with the bridge network and exec task driver in the Nomad cluster.

Like they say:

![image](/images/haiku-dns.png)


Fin!