+++
title = "DNS Lookups in Kubernetes"
date = 2020-02-02T10:57:55+05:30
type = "post"
description = "In this post, I'll talk about how I learnt about FQDN, Search Paths and ndots to tackle slow DNS resolution in Kubernetes"
in_search_index = true
[taxonomies]
tags = ["DNS","Kubernetes"]
+++

One of the primary advantages of deploying workloads in Kubernetes is seamless application discovery. Intra cluster communication becomes easy with the concept of [Service](https://kubernetes.io/docs/concepts/services-networking/service/) which represents a Virtual IP backing a set of Pod IPs. For example, if `vanilla` service needs to talk to a `chocolate` service, it can directly use the Virtual IP for `chocolate`. Now the question is who resolves the DNS query for `chocolate` and how?

DNS resolution is configured in Kubernetes cluster through [CoreDNS](https://coredns.io/). The kubelet configures each Pod's `/etc/resolv.conf` to use the coredns pod as the `nameserver`. You can see the contents of `/etc/resolv.conf` inside any pod, they'll look something like:

```shell
search hello.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.152.183.10
options ndots:5
```

This config is used by DNS clients to forward the DNS queries to a DNS server. `resolv.conf` is the resolver configuration file which has information about:

- **nameserver** : Where the DNS queries are forwarded to. In our case this is the address of `CoreDNS` service.

- **search**: Represents the search path for a particular domain. Interestingly `google.com` or `mrkaran.dev` is not FQDN (fully qualified domain name). A standard convention that most DNS resolvers follow is that if a domain ends with `.` (representing the root zone), the domain is considered to be FQDN. Some resolvers try to act smart and append the `.` themselves. So `mrkaran.dev.` is an FQDN but `mrkaran.dev` is not.

- **ndots**: This is the most interesting value and is the _highlight_ of this post. `ndots` represents the threshold value of the number of dots in a query name to consider it as a "fully qualified" domain name. More on this later, as we discover the flow of DNS lookup.

![image](/images/dns-k8s.png)

Let's check what happens when we query for `mrkaran.dev` in a pod.

```shell
$ nslookup mrkaran.dev
Server: 10.152.183.10
Address: 10.152.183.10#53

Non-authoritative answer:
Name: mrkaran.dev
Address: 157.230.35.153
Name: mrkaran.dev
Address: 2400:6180:0:d1::519:6001
```

For this experiment, I've also turned on CoreDNS logging level to `all` which makes it highly verbose. Let's look at the logs of `coredns` pod:

```shell
[INFO] 10.1.28.1:35998 - 11131 "A IN mrkaran.dev.hello.svc.cluster.local. udp 53 false 512" NXDOMAIN qr,aa,rd 146 0.000263728s
[INFO] 10.1.28.1:34040 - 36853 "A IN mrkaran.dev.svc.cluster.local. udp 47 false 512" NXDOMAIN qr,aa,rd 140 0.000214201s
[INFO] 10.1.28.1:33468 - 29482 "A IN mrkaran.dev.cluster.local. udp 43 false 512" NXDOMAIN qr,aa,rd 136 0.000156107s
[INFO] 10.1.28.1:58471 - 45814 "A IN mrkaran.dev. udp 29 false 512" NOERROR qr,rd,ra 56 0.110263459s
[INFO] 10.1.28.1:54800 - 2463 "AAAA IN mrkaran.dev. udp 29 false 512" NOERROR qr,rd,ra 68 0.145091744s
```

Whew. So 2 things piqued my interest here:

- The query iterates through all search paths until the answer contains a `NOERROR` code (which the DNS clients understand and store it as the result). `NXDOMAIN` simply indicates no record found for that domain name. Since `mrkaran.dev` isn't an FQDN (according to `ndots=5` setting), the resolver looks at search path and determines the order of query.

- `A` and `AAAA` records are fired parallelly. This is because `single-request` option in `/etc/resolv.conf` has a default configuration to perform parallel IPv4 and IPv6 lookups. You can disable this using `single-request` option.

_Note_: `glibc` can be configured to send these requests sequentially but `musl` cannot, so Alpine users must take note.

### Playing around with ndots

Let's play around with `ndots` a bit more and see how it behaves. The idea is simple, for the DNS client to know whether a domain is an absolute one or not is through this `ndots` setting. For example, if you query for `google` simply, how will the DNS client know if this is an absolute domain. If you set `ndots` as `1`, the DNS client will say "oh, `google` doesn't have even one 1 dot, let me try going through search list. However, if you query for `google.com`, the search list will be completely ignored since the query name satisfies the `ndots` threshold (At least one dot).

We can see this by actually doing it:

```shell
$ cat /etc/resolv.conf
options ndots:1
```

```shell
$ nslookup mrkaran
Server: 10.152.183.10
Address: 10.152.183.10#53

** server can't find mrkaran: NXDOMAIN
```

CoreDNS logs:

```shell
[INFO] 10.1.28.1:52495 - 2606 "A IN mrkaran.hello.svc.cluster.local. udp 49 false 512" NXDOMAIN qr,aa,rd 142 0.000524939s
[INFO] 10.1.28.1:59287 - 57522 "A IN mrkaran.svc.cluster.local. udp 43 false 512" NXDOMAIN qr,aa,rd 136 0.000368277s
[INFO] 10.1.28.1:53086 - 4863 "A IN mrkaran.cluster.local. udp 39 false 512" NXDOMAIN qr,aa,rd 132 0.000355344s
[INFO] 10.1.28.1:56863 - 41678 "A IN mrkaran. udp 25 false 512" NXDOMAIN qr,rd,ra 100 0.034629206s
```

Since `mrkaran` didn't specify any `.` so the search list was used to find the answer.

_Note_: `ndots` value is silently capped to `15` and is `5` in Kubernetes as default.

### Handling this in Production

If your application is of the nature that makes a lot of external network calls, the DNS can become a bottleneck in case of heavy traffic since a lot of extra queries are made before the real DNS query is even fired. It's quite uncommon to see applications appending the root zone in the domain names, but that can be considered as a hack. So instead of using `api.twitter.com`, you can hardcode your application to include `api.twitter.com.` which would force the DNS clients to do an authoritative lookup directly on the absolute domain.

Alternatively, since K8s 1.14, the `dnsConfig` and `dnsPolicy` feature gates have become stable. So while deploying a pod you can specify `ndots` setting to something lesser, say `3` or if you want to be really aggressive you can turn it down to `1`. The consequences of this will be that every intra-node communication now has to include the full domain. This is one of the classic tradeoffs where you have to choose between performance and portability. If the app doesn't demand super low latencies, I guess you need not worry about this at all since DNS results are cached internally too.

### References

I got to know about this peculiarity first, in a K8s [meetup](https://failuremodes.dev/) which I went to, last weekend where the folks mentioned about having to deal with this.

Here are some additional links you can read on the web:

- [Explainer on why ndots=5 in kubernetes](https://github.com/kubernetes/kubernetes/issues/33554#issuecomment-266251056)
- [Great read on how ndots affects application performance](https://pracucci.com/kubernetes-dns-resolution-ndots-options-and-why-it-may-affect-application-performances.html)
- [musl and glibc resolver inconsistencies](https://www.openwall.com/lists/musl/2017/03/15/3)

_Note_: I'm particularly not using `dig` in this post. `dig` apparently automatically adds a `.` (root zone identifier) to make the domain an FQDN one **without** even first going through the search path. I've mentioned about this briefly in one of my [older](https://mrkaran.dev/posts/dig-overview/) posts. Nonetheless, it's quite surprising to see that you need to give a flag to make it behave in what seems to be a standard way.

#### It's always DNS, isn't it ;)

Fin!

### Update

**2020-12-24**:

In case you want to play around with `ndots` and DNS more, I've worked on a DNS Client which lets you tweak these params on the fly. Feel free to checkout [doggo](https://github.com/mr-karan/doggo) if interested!
