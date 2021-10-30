+++
title = "Self Hosting 101"
date = 2021-04-27T08:10:55+05:30
type = "talk"
description = "Presented at FOSS United April 2021 Meetup"
in_search_index = true
[extra]
link = "/talks/self-hosting-fossunited.html"
[taxonomies]
tags = ["Self Hosting"]
+++

---
theme: dracula
paginate: true
marp: true
size: 4K
footer: Hydra Repo: [git.mrkaran.dev/karan/hydra](https://git.mrkaran.dev/karan/hydra)
---

<!-- _class: lead -->

# Self Hosting 101

FOSS United - April 2021

*@mrkaran*

---

# `whoami`

👨‍💻 Writes YAML at Zerodha

📈 Interested in Monitoring and Observability systems

📓 Blogs about things I find interesting

🧩 **Self hosted enthusiast**

![bg right 66%](./img/cycle.jpg)

---

# Why (I) Self Host

- Break from the Big Tech Co

---

# Why (I) Self Host

- Break from the Big Tech Co
- Own your data

---

# Why (I) Self Host

- Break from the Big Tech Co
- Own your data
- No lock ins for data which is critical

---

# Why (I) Self Host

- Break from the Big Tech Co
- Own your data
- No lock ins for data which is critical
- Chance to contribute to OSS

---

# Why (I) Self Host

- Break from the Big Tech Co
- Own your data
- No lock ins for data which is critical
- Chance to contribute to OSS
- Experiment and learn

---

# My Setup

## Servers

- DigitalOcean Droplet (2vCPU, 4GB RAM, blr1 Region)
- 1 * RPi 4 Node (4GB RAM)
- 1 * RPi 4 Node (2GB RAM)

---

![bg 66%](./img/home-server-arch.png)

---

![bg 66%](./img/rpi.jpeg)

---

# Infra and Deployments

- Ansible
- Terraform
- Nomad + Consul

---

## Ansible

- Boostrap the server
    - Harden SSH. User, Shell setups.
    - Install `node-exporter`, `docker`, `tailscale`.

---

## Terraform

- DigitalOcean infra
    - Droplet
    - Firewalls
    - SSH Keys, Volumes, Floating IPs etc.

- Cloudflare DNS
    - `mrkaran.dev` hosted zone
    - DNS Records in ^ the zone.

---

## Nomad + Consul

- Single node cluster.
- Runs every workload (mostly) as a docker container.

---

# Services I run

- Pi-hole
- Gitea
- Joplin Sync Server
- Shynet
- Firefly III
- Nextcloud
- `doggo` (Shameless self plug)

---

# Monitoring

- Grafana
- Prometheus
- Telegraf to collect home ISP stats
    - Ping Input plugin
    - DNS Input Plugin

---

![bg 90%](./img/isp-monitoring.png)

---

![bg 90%](./img/isp-monitoring-2.png)

---

# Networking

- Tailscale for Mesh Network
    - Based on Wireguard VPN.
    - Authenticated sessions only.
    - Expose services on RPi easily without any static IP.

- Tailscale uses `100.64.0.0/10` subnet from the Carrier Grade NAT space.

---

# Networking

## Dont expose to the world

```s
doggo pihole.mrkaran.dev
NAME                    TYPE    CLASS   TTL     ADDRESS         NAMESERVER        
pihole.mrkaran.dev.     A       IN      300s    100.119.138.27  100.119.138.27:53
```

## unless required

```s
doggo git.mrkaran.dev       
NAME                    TYPE    CLASS   TTL     ADDRESS         NAMESERVER        
git.mrkaran.dev.        A       IN      300s    104.21.7.168    100.119.138.27:53
git.mrkaran.dev.        A       IN      300s    172.67.187.239  100.119.138.27:53
```

---

# Networking

- Caddy as a proxy for all services.
    - Running 2 instances of Caddy.
        - Private: Listens on Tailscale Interface.
        - Public: Listens on DO's public IPv4 Interface.

    - Automatic SSL with ACME DNS challenge
        - Built my own image: https://github.com/mr-karan/caddy-plugins-docker

---

# Storage

- DONT use RPi for storage.
    - Atleast not with SD cards.
    - Newer RPis can boot off SSDs.

- Enable snapshots for volumes provided by cloud provider.

- Use separate DB instances for different applications.

---

# Storage

![bg 90%](./img/shynet-blog.png)

---

# Storage

- Use separate DB instances for different applications.


- Traffic spike in the blog
    - Shynet requires more resources
    - Server upgrade was done abruptly
    - Postgres required a WAL Log Reset to start

---

# Backups

- Restic
    - Periodic Job in Nomad.
    - Single vault with everything inside `/data`.
    - All applications mount inside `/data` folder.
    - Upload to Backblaze B2.

---

# Security

- If it should not be public facing, don't expose to WWW.
    - Prefer to use a VPN or mesh network instead of IP whitelists.
    - Tighter Firewall rules otherwise.

- Pi-Hole, Gitea, etc Admin interfaces must always be protected with strong passwords.

- Periodic **updates** to App and OS.

---

# Takeaways

- Don't overthink. Pick something really simple (like Pi-hole) and host it.
    - You'll feel pretty happy about it.

- Don't blindly copy/paste this stack.
    - Took me 2 years of constant iteration and experimentation.
    - KISS.

---

# Resources

- [r/selfhosted](https://www.reddit.com/r/selfhosted)
    - Incredible, beginner friendly wiki: https://wiki.r-selfhosted.com/

- [github.com/awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted)

---


<!-- _class: lead -->

# Thank You

## Questions?
