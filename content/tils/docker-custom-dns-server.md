+++
title = "Setting Custom DNS in Docker"
date = 2022-06-12
type = "til"
description = "A guide to configuring Docker to use a custom DNS server, overcoming the challenge of unavailable '--dns' flag during build."
in_search_index = true
[taxonomies]
tags = ["Docker", "DNS"]
+++


Docker makes it impossible to supply a `--dns` flag with `docker build` which makes it harder to use an internal service in your org. There are workarounds like `--add-host=xyz.internal:<IP>` but imagine doing this for dozen of services. Yep it's not maintainable, especially if the DNS records of these services change (for eg if they are behind ALB).

A cleaner solution is to forward the queries to your host DNS server itself. You can use various techniques like Split Tunnel (if your VPN supports that) or custom routing to different upstream DNS servers (eg with CoreDNS).

To make this happen, you need to edit the `/etc/docker/daemon.json` file:

```
{
        "dns": ["x.x.x.x"]
}
```

Docker uses `8.8.8.8` as a default, but if you override the above setting, it will start using the DNS server you provided.
