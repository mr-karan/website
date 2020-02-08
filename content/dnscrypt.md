---
title: "DNSCrypt Server"
date: 2019-10-08T08:10:55+05:30
type: "page"
---

I am running a public [DNSCrypt](https://dnscrypt.info/) Server hosted in Bengaluru, India on a tiny Digital Ocean droplet. It supports `DNSSEC validation`, `DNScrypt protocol` and has caching enabled for faster responses. The DNS queries are forwarded to a vanilla Unbound DNS resolver. To use this DNSCrypt server, you will need a client-side proxy which can forward the queries and resolve them for you. Since `DNSCrypt` is not widely adopted, you will have to rely on a local proxy like [dnscrypt-proxy](https://github.com/DNSCrypt/dnscrypt-proxy) or [dnsproxy](https://github.com/AdguardTeam/dnsproxy).

### Connection Info

**Resolver Address**

```
Public server address: 139.59.55.13:4343
Provider public key: c23f7077e04331c5614892f26da0851f088fd9dbf3c1106570180e53a1046866
Provider name: 2.dnscrypt-cert.dns.mrkaran.dev
```

**Stamp**

```
sdns://AQcAAAAAAAAAETEzOS41OS41NS4xMzo0MzQzIMI_cHfgQzHFYUiS8m2ghR8Ij9nb88EQZXAYDlOhBGhmHzIuZG5zY3J5cHQtY2VydC5kbnMubXJrYXJhbi5kZXY
```

### Filtering and Adblocking

I am also hosting a `DOH` and `DOT` server on [Adguard](https://github.com/AdguardTeam/AdGuardHome/) which blocks ads and trackers by default. The upstream queries are forwarded to my `DNSCrypt` server itself.

**DOH**

```
https://dns.mrkaran.dev:4430/dns-query
```

**DOT**

```
tls://dns.mrkaran.dev:853
```

## Privacy

I have no intentions of logging the DNS queries and if at all I have to turn on the logs to debug any outages, they will be pruned immediately after. Self hosting a public DNS server came out of my frustration of centralizing the DNS queries in the name of better privacy (DOH!), while forgetting the fact that DNS was always meant to be distributed.

## Uptime

I am taking this as a personal challenge to minimise the downtime as much possible and provide a solid DNS service that you can rely on. However there are no guarantees, but don't let that discourage you.
Status page coming soon!