+++
title = "How I expose services while self hosting"
date = 2022-02-10
type = "post"
description = "This post delves into details of how I use Caddy along with Tailscale to expose public and private services"
in_search_index = true
[taxonomies]
tags = ["Devops", "Docker", "Self Hosting"]
[extra]
og_preview_img = "/images/selfhosted-networking-setup.png"
+++

I've often been asked how to expose public and private services running on DigitalOcean droplets/RPis when self hosting apps. Most people don't have access to a static IP for their RPis. I felt I'd summarize my approach to this in this blog post and hope it'll be useful for others trying to do the same.

### Tools I use

- [Tailscale](https://tailscale.com/): I love this and I've [written about it in the past](https://mrkaran.dev/posts/home-server-updates/). I am one of the early adopters, using this for 2 years now and while it can be replaced with other similar Wireguard based mesh services that have popped up recently, I still like the UX of this application a lot. In simpler words, _it just works!_
- [Caddy](https://caddyserver.com/): I use Caddy as a webserver to host some static websites and as a reverse proxy for all the applications I've deployed. It makes the SSL setup a breeze, the config is nice to read as well. There's nothing about Caddy to not like it if you're not in the business of dealing with super high concurrent traffic on your website (in which case NGINX/HAProxy/Envoy et al might be worth looking at). I've never used Traefik myself, and while I know it makes the routing simple with Docker labels, I think my current approach with Caddy is also similar and easier for me to use without having to learn a new config.
- [Docker](https://www.docker.com/): All the services are containerized and I make special use of Docker networks, which I'll show in the post.

## Setup Overview

![image](/images/selfhosted-networking-setup.png)

I use 2 instances of Caddy for my setup:

- Public: This is to reverse proxy all the public-facing websites.
- Private: This is to reverse proxy all the internal websites.

The `docker-compose` looks like this:

```yml
version: "3.7"

services:
  caddy_public:
    ...
    ports:
      - "<do_floating_ip>:80:80"
      - "<do_floating_ip>:443:443"
    networks:
      - public
    ...

  caddy_internal:
    ...
    ports:
      - "100.111.91.100:80:80"
      - "100.111.91.100:443:443"
    networks:
      - internal
    ...

networks:
  public:
    name: caddy_public
  internal:
    name: caddy_internal
```

This is where most of the magic lies. I use 2 Docker networks `caddy_public` and `caddy_internal`. Both these networks are configured as Bridge Networks. The containers connected to the same bridge network can even reach other containers using internal DNS.

The _published_ port section is the one of importance here.

In the `internal` caddy instance, the TCP port 80 in the container is mapped to port 80 on the Docker host for connections to host IP `100.111.91.100` (this is a private IP and belongs to the [CGNAT space](https://tailscale.com/kb/1015/100.x-addresses/)). The same is done for `caddy_public` where instead of Tailscale IP, the Floating IP of the DigitalOcean droplet is used.

Next comes the part where we'll attach these networks to our applications. `docker-compose` by default creates a user-defined bridge network if you leave `networks` unspecified. However, if you want more granular control, you can specify the networks in the Compose spec itself.

Here's an example of `Plausible` compose spec which is exposed publicly:

```yml
  plausible_events_db:
    image: yandex/clickhouse-server:21.3.2.5
    networks:
      - plausible

  plausible:
    image: plausible/analytics:latest
    networks:
      - web
      - plausible

networks:
  web:
    name: caddy_public
    external: true
  plausible:
    name: plausible
```

Here you can see that the ClickHouse container is only attached to the `plausible` network. This `plausible` network is scoped only to these services defined in this file. 

We can `exec` inside the `caddy_public` container and find out the IP of `plausible` and verify if the network is correctly configured and reachable:

```bash
$ host plausible
plausible has address 172.20.0.3
$ curl plausible:8000
<html><body>You are being <a href="/login">redirected</a>.</body></html>/srv # 
```

Some notes on this setup:

- You'll also note that I haven't _published_ the port 8000 anywhere. Publishing is only required if you want to forward the traffic from your host network to the docker network (via the bridge). But here, since both are attached to the same network (`caddy_public`), that is not required anymore.
- This also means that the only way someone can reach port 8000 on Plausible is only via the Caddy container (which is firewall restricted to Cloudflare IPs.)
- The DB container doesn't need to be accessed at all from Caddy, so we've not attached the `web` network there

Here's another example of exposing an internal service, which works on the same principles:

```yml
  grafana:
    image: grafana/grafana:8.3.4
    networks:
      - monitoring
      - internal

networks:
  internal:
    name: caddy_internal
    external: true
  monitoring:
    name: monitoring
```

Here, the Grafana container is attached to `caddy_internal` network. Since the `caddy_internal` container only publishes ports on the Tailscale IP, anyone who is not inside the Tailscale network will not be able to access this. Tailscale can do much more by setting up ACL rules per device for each user, but since I am the only user, I've not configured ACL rules on it yet.

Hope this approach was simplistic enough. I follow this pattern across all the applications I self-host and honestly pretty happy with it

Fin!
