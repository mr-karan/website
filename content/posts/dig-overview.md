+++
title = "A quick primer on dig"
date = 2019-11-11T10:57:55+05:30
type = "post"
description = "Learn how to use dig (DNS lookup tool) effectively with practical examples"
in_search_index = true
[taxonomies]
tags = ["DNS","Devops"]
+++

Dig is a DNS lookup utility developed by [BIND](https://en.wikipedia.org/wiki/BIND) which helps a lot while troubleshooting DNS issues (which are more common than you probably think #hugops). I use `dig` fairly often and thought to write an introductory guide on how you can use `dig` with some practical examples that'll help you `dig` through DNS issues faster (sorry for the lame pun, couldn't resist.)

## Basics

The most basic and common usage for `dig` is to query the authorative servers for a particular domain and retrieve the IP. If it's an IPv4 then you should be looking at `A` record, while if it's IPv6 then `AAAA` record is your friend. Let's see the DNS records for the site you're currently on:

```sh
➜  ~ dig mrkaran.dev

; <<>> DiG 9.10.6 <<>> mrkaran.dev
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 23292
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1220
;; QUESTION SECTION:
;mrkaran.dev.			IN	A

;; ANSWER SECTION:
mrkaran.dev.		60	IN	A	206.189.89.118

;; Query time: 6 msec
;; SERVER: 127.0.0.1#53(127.0.0.1)
;; WHEN: Tue Oct 29 23:13:31 IST 2019
;; MSG SIZE  rcvd: 67

```

This is the most basic example for `dig`. Let's explore some of the additional options.

### Keep it short

`dig +short` keeps the information to bare minimum and only displays the `ANSWER`.

```sh
dig +short mrkaran.dev
206.189.89.118
```

### Nameserver details

If you want to find the `Nameserver` for your DNS records, you can use the query type `ns`.

```sh
$ dig mrkaran.dev ns +short
alec.ns.cloudflare.com.
cruz.ns.cloudflare.com.
```

`ns` is one of the many query types you can use to indicate which type of DNS record you want to fetch. Default is `A` record which returns the IPv4 address of the domain (unless it's a root domain, in which case the default query type is `NS`). Some other examples of query types are `mx`, `AAAA`, `TXT` etc.

Fun Fact: `ANY` query type has become [obsolete](https://blog.cloudflare.com/rfc8482-saying-goodbye-to-any/) as per the new [RFC8482](https://tools.ietf.org/html/rfc8482) and DNS operators can choose to not respond to this query. The reason for this is that the payload response size for an `ANY` query is quite huge (since it has to return all type of DNS records) and this could affect the performance of authoritative servers in case of a [DNS amplification](https://blog.cloudflare.com/deep-inside-a-dns-amplification-ddos-attack/) attack.

### Using different DNS server

Let's say you want to switch to a different resolver, you can use `@` followed by the address of your DNS server.

```sh
$ dig mrkaran.dev @9.9.9.9
```

### Reverse DNS Lookup

This one's actually pretty cool. `dig -x` lets you query the IP and retrieve the hostname details for that IP.

```sh
dig -x 206.189.89.118
```

### Multiple queries

You can input a list of domain names and pass the file with the arg `-f` to dig.

```sh
$ cat digfile
mrkaran.dev
joinmastodon.org
zoho.com
```

To list down all MX records for the domains in a file, you can use something like:

```sh
$ dig -f digfile +noall mx +answer
mrkaran.dev.		242	IN	MX	10 mx.zoho.in.
mrkaran.dev.		242	IN	MX	20 mx2.zoho.in.
mrkaran.dev.		242	IN	MX	50 mx3.zoho.in.
joinmastodon.org.	21599	IN	MX	10 in1-smtp.messagingengine.com.
joinmastodon.org.	21599	IN	MX	20 in2-smtp.messagingengine.com.
zoho.com.		299	IN	MX	10 smtpin.zoho.com.
zoho.com.		299	IN	MX	20 smtpin2.zoho.com.
zoho.com.		299	IN	MX	50 smtpin3.zoho.com.
```

### Search List

I learnt this recently while debugging a DNS issue in one of the Kubernetes pods. Dig doesn't use search paths by default, so if you have a service say `redis` inside a namespace dig won't fetch any result:

```sh
$ dig redis +short
# empty output, indicates no record found
```

This is because a service name in Kubernetes is of the form `service.namespace.svc.cluster.local`. So, we should actually be querying for `redis.myns.svc.cluster.local` and we'll get our result. But isn't that too long and painful (sorry for the pun) to type?

So, there's another option `+search` which can be used to find all domains matching the search path defined in `/etc/resolv.conf` namesever configurations.

```sh
$ cat /etc/resolv.conf
nameserver 10.100.0.10
search myns.svc.cluster.local svc.cluster.local cluster.local
```

We can now query for `redis` with this search list:

```sh
dig redis +search +short
10.100.32.73
```

### DNSSec Validation

`dig` even lets you validate the DNS records you received using `DNSSEC` validation.

```sh
$ dig mrkaran.dev +dnssec
; <<>> DiG 9.10.6 <<>> mrkaran.dev +dnssec
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 36275
;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags: do; udp: 1452
;; QUESTION SECTION:
;mrkaran.dev.			IN	A

;; ANSWER SECTION:
mrkaran.dev.		20	IN	A	178.128.17.49
mrkaran.dev.		20	IN	RRSIG	A 13 2 20 20191112173050 20191110153050 34505 mrkaran.dev. Tl3zD6EqfVRvZi79ahePQcAXnbSUY9ZEYx/KwXnDUyonlrCKuBHzIYYC MJoVns410+sOwbIrcAdLgx+eiMYqRQ==

;; Query time: 65 msec
;; SERVER: 1.1.1.1#53(1.1.1.1)
;; WHEN: Mon Nov 11 22:01:01 IST 2019
;; MSG SIZE  rcvd: 163
```

The important bit to note here is the `ad` flag set which represents Authenticated Data. The records will only be returned if the validation succeeds (unless you also specify `+cd` which indicates Checking Disabled flag.)

On a server which doesn't have DNSSEC enabled, you can see no records are returned with the `+dnssec` flag.

```sh
$ dig dnssec-failed.org +dnssec
; <<>> DiG 9.10.6 <<>> dnssec-failed.org +dnssec
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 19886
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;dnssec-failed.org.		IN	A

;; Query time: 335 msec
;; SERVER: 1.1.1.1#53(1.1.1.1)
;; WHEN: Mon Nov 11 22:03:50 IST 2019
;; MSG SIZE  rcvd: 35
```

That pretty much broadly covers some practical examples with `dig`. I will soon write a detailed post on how `DNSSEC` validation works and why it needs to be mainstream.

Fin!
