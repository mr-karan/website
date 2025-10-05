+++
title = "State of My Homelab 2025"
date = 2025-10-04
type = "post"
description = "An overview of my current homelab architecture, focusing on a transition from complex orchestration to a simplified Docker Compose-based setup."
in_search_index = true
[taxonomies]
tags = ["Homelab", "Docker", "Self-hosting", "Infrastructure"]
[extra]
og_preview_img = "/images/homelab-gatus.png"
+++

## Introduction

For the past five years, I have maintained a homelab in various configurations. This journey has served as a practical exploration of different technologies, from [Raspberry Pi clusters running K3s](https://mrkaran.dev/posts/home-server-setup/) to a [hybrid cloud setup](https://mrkaran.dev/posts/home-server-updates/) and eventually a [cloud-based Nomad setup](https://mrkaran.dev/posts/home-server-nomad/). Each iteration provided valuable lessons, consistently highlighting the operational benefits of simplicity.

This article details the current state of my homelab. A primary motivation for this build was to dip my toes into "actual" homelabbing—that is, maintaining a physical server at home. The main design goal was to build a dedicated, reliable, and performant server that is easy to maintain. This led me to move away from complex container orchestrators like Kubernetes in favor of a more straightforward Docker Compose workflow. I will cover the hardware build, software architecture, and the rationale behind the key decisions.

## Hardware Configuration

After considerable research, I selected components to balance performance, power efficiency, and cost. The server is designed for 24/7 operation in a home environment, making noise and power consumption important considerations.

### The Build

| Component       | Choice                              | Price         |
| --------------- | ----------------------------------- | ------------- |
| **CPU**         | AMD Ryzen 5 7600X (6-core, 4.7 GHz) | $167.58       |
| **CPU Cooler**  | ARCTIC Liquid Freezer III Pro 360   | $89.99        |
| **Motherboard** | MSI B650M Gaming Plus WiFi          | $225.83       |
| **RAM**         | Kingston FURY Beast 32GB DDR5-6000  | $136.99       |
| **Boot Drive**  | WD Blue SN580 500GB NVMe            | $88.76        |
| **Storage 1**   | WD Red Plus 4TB (5400 RPM)          | $99.99        |
| **Storage 2**   | Seagate IronWolf Pro 4TB (7200 RPM) | $150.00       |
| **Case**        | ASUS Prime AP201 MicroATX           | $89.99        |
| **PSU**         | Corsair SF750 (80+ Platinum)        | $169.99       |
| **Total**       |                                     | **$1,219.12** |

<div class="image-grid">
<a href="/images/homelab_2025_1_opt.jpg" class="lightbox-thumbnail"><img src="/images/homelab_2025_1_opt.jpg" alt="Homelab build in progress"></a>
<a href="/images/homelab_2025_2_opt.jpg" class="lightbox-thumbnail"><img src="/images/homelab_2025_2_opt.jpg" alt="Completed build with RGB and storage drives"></a>
<a href="/images/homelab_2025_3_opt.jpeg" class="lightbox-thumbnail"><img src="/images/homelab_2025_3_opt.jpeg" alt="MSI BIOS showing system information"></a>
</div>

### Component Rationale

- **CPU**: The Ryzen 5 7600X provides a strong price-to-performance ratio. Its 6 cores offer ample headroom for concurrent containerized workloads and future experimentation.
- **Storage**: The boot drive is a 500GB NVMe for fast OS and application performance. The primary storage consists of two 4TB HDDs in a **BTRFS RAID 1** configuration. To mitigate the risk of correlated failures, I chose drives from different manufacturers (WD and Seagate) purchased at different times.
- **RAM**: 32GB of DDR5-6000 provides sufficient memory for a growing number of services without risking contention.
- **Case & PSU**: The ASUS Prime AP201 is a compact MicroATX case with a clean aesthetic suitable for a home office. The Corsair SF750 (80+ Platinum) PSU was chosen for its efficiency and to provide capacity for a future GPU for local LLM or transcoding workloads.

## System Architecture & Deployment

My previous setups involved Kubernetes and Nomad, but the operational overhead proved unnecessary for my use case. I have since standardized on a Git-based, Docker Compose workflow that prioritizes simplicity and transparency.

### Directory Structure and "Stacks"

The core of the system is a Git repository that holds all configurations. Each service is defined as a self-contained "stack" in its own directory. The structure is organized by machine, making it easy to manage multiple environments:

```sh
homelab/
├── deploy.sh                 # Main deployment script
├── justfile                  # Task runner for common commands
└── machines/
    ├── floyd-homelab-1/      # Primary home server
    │   ├── config.sh         # SSH and deployment settings
    │   └── stacks/
    │       ├── immich/
    │       │   └── docker-compose.yml
    │       └── paperless/
    │           └── docker-compose.yml
    └── floyd-pub-1/          # Public-facing VPS
        ├── config.sh
        └── stacks/
            ├── caddy/
            └── ntfy/
```

This modular approach allows me to manage each application's configuration, including its `docker-compose.yml` and any related files, as an independent unit.

### Deployment Workflow

Deployments are handled by a custom `deploy.sh` script, with a `justfile` providing a convenient command-runner interface. The process is fundamentally simple:

1.  **Sync**: `rsync` copies the specified stack's directory from the local Git repository to a `REMOTE_BASE_PATH` (e.g., `/opt/homelab`) on the target machine.
2.  **Execute**: `ssh` runs the appropriate `docker compose` command on the remote machine.

Each machine's connection settings (`SSH_HOST`, `SSH_USER`, `REMOTE_BASE_PATH`) are defined in its `machines/<name>/config.sh` file. This file can also contain `pre_deploy` and `post_deploy` hooks for custom actions.

The `justfile` makes daily operations trivial:

```bash
# Deploy a single stack to a machine
just deploy-stack floyd-homelab-1 immich

# View the logs for a stack
just logs floyd-homelab-1 immich

# Test a deployment without making changes
just dry-run floyd-homelab-1
```

![Deployment workflow demonstration](/images/homelab-deploy.gif)

This system provides fine-grained control over deployments, with support for actions like `up`, `down`, `restart`, `pull`, and `recreate` (which also removes persistent volumes).

### Container & Configuration Patterns

To keep the system consistent, I follow a few key patterns:

- **Data Persistence**: Instead of using Docker named volumes, I use host bind mounts. All persistent data for a service is stored in a dedicated directory on the host, typically `/data/<service-name>`. This makes backups and data management more transparent.
- **Reverse Proxy Network**: The Caddy stack defines a shared Docker network called `public_proxy`. Other stacks that need to be exposed to the internet are configured to join this network. This allows Caddy to discover and proxy them without exposing their ports on the host machine. I have written about this pattern in detail in a [previous post](https://mrkaran.dev/posts/exposing-services/).
- **Port Exposure**: Services behind the reverse proxy use the `expose` directive in their `docker-compose.yml` to make ports available to Caddy within the Docker network. I avoid binding ports directly with `ports` unless absolutely necessary.

## Multi-Machine Topology

The homelab comprises three distinct machines to provide isolation and redundancy.

- **floyd-homelab-1 (Primary Server)**: The core of the homelab, running on the AMD hardware detailed above. It runs data-intensive personal services (e.g., Immich, Paperless-ngx) and is accessible only via the Tailscale network.
- **floyd-pub-1 (Public VPS)**: A small cloud VPS that hosts public-facing services requiring high availability, such as DNS utilities, analytics, and notification relays.
- **floyd-monitor-public (Monitoring VPS)**: A small Hetzner VM running Gatus for health checks. Its independence ensures that I am alerted if the primary homelab or home network goes offline.

This distributed setup isolates my home network from the public internet and ensures that critical public services remain online even if the home server is down for maintenance.

## Hosted Services

The following is a breakdown of the services, or "stacks," running on each machine. A few key services that are central to the homelab are detailed further in the next section.

### floyd-homelab-1 (Primary Server)

*   **[Actual](https://github.com/actualbudget/actual-server)**: A local-first personal finance and budgeting tool.
*   **[Caddy](https://caddyserver.com/)**: A powerful, enterprise-ready, open source web server with automatic HTTPS.
*   **[Gitea](https://gitea.io/)**: A Git service for personal projects.
*   **[Glance](https://github.com/glanceapp/glance)**: A dashboard for viewing all my feeds and data in one place.
*   **[Immich](https://immich.app/)**: A photo and video backup solution, directly from my mobile phone.
*   **[Karakeep](https://karakeep.app/)**: An app for bookmarking everything, with AI-based tagging and full-text search.
*   **[Owntracks](https://owntracks.org/)**: A private location tracker for recording my own location data.
*   **[Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)**: A document management system that transforms physical documents into a searchable online archive.
*   **[Silverbullet](https://silverbullet.md/)**: A Markdown-based knowledge management and note-taking tool.

### floyd-monitor-public (Monitoring VPS)

*   **[Caddy](https://caddyserver.com/)**: Reverse proxy for the services on this node.

### floyd-pub-1 (Public VPS)

*   **[Beszel-agent](https://beszel.dev/)**: The agent for the Beszel monitoring platform.
*   **[Caddy](https://caddyserver.com/)**: Reverse proxy for the services on this node.
*   **[Cloak](https://github.com/mr-karan/cloak)**: A service to securely share sensitive text with others.
*   **[Doggo](https://doggo.mrkaran.dev/)**: A command-line DNS Client for Humans, written in Golang.
*   **[Ntfy](https://ntfy.sh/)**: A self-hosted push notification service.
*   **[prom2grafana](https://github.com/mr-karan/prom2grafana)**: A tool to convert Prometheus metrics to Grafana dashboards and alert rules using AI.
*   **[Umami](https://umami.is/)**: A simple, fast, privacy-focused alternative to Google Analytics.

## Service Highlights

### Technitium: A Powerful DNS Server

I came across Technitium DNS after seeing a recommendation from [@oddtazz](https://twitter.com/oddtazz), and it has been a revelation. For anyone who wants more than just basic ad blocking from their DNS server, it's a game-changer. It serves as both a recursive and authoritative server, meaning I don't need a separate tool like `unbound` to resolve from root hints. The level of configuration is incredible—from DNSSEC, custom zones, and SOA records to fine-grained caching control.

The UI is a bit dated, but that's a minor point for me given the raw power it provides. It is a vastly underrated tool for any homelabber who wants to go beyond Pi-hole or AdGuard Home.

<div style="text-align: center;">
<a href="/images/homelab-technitium.png" class="lightbox-thumbnail" data-featherlight="image"><img src="/images/homelab-technitium.png" alt="Technitium DNS Server UI" width="400"></a>
</div>

### Beszel: Lightweight Monitoring

For a long time, I felt that monitoring a homelab meant spinning up a full Prometheus and Grafana stack. Beszel is the perfect antidote to that complexity. It provides exactly what I need for basic node monitoring—CPU, memory, disk, and network usage—in a simple, lightweight package.

It’s incredibly easy to set up and provides a clean, real-time view of my servers without the overhead of a more complex system. For a simple homelab monitoring setup, it's hard to beat.

<div style="text-align: center;">
<a href="/images/homelab-beszel-1.png" class="lightbox-thumbnail" data-featherlight="image"><img src="/images/homelab-beszel-1.png" alt="Beszel Monitoring UI" width="400"></a>
</div>

### Gatus: External Health Checks

While Beszel monitors the servers from the inside, Gatus watches them from the outside. Running on an independent Hetzner VM, its job is to ensure my services are reachable from the public internet. It validates HTTP status codes, response times, and more.

This separation is crucial; if my entire home network goes down, Gatus is still online to send an alert to my phone. It's the final piece of the puzzle for robust monitoring, ensuring I know when things are broken even if the monitoring service itself is part of the outage.

<div style="text-align: center;">
<a href="/images/homelab-gatus.png" class="lightbox-thumbnail" data-featherlight="image"><img src="/images/homelab-gatus.png" alt="Gatus Health Checks UI" width="400"></a>
</div>

## Storage and Backup Strategy

Data integrity and recoverability are critical. My strategy is built on layers of redundancy and encryption.

### Storage: BTRFS RAID 1 + LUKS Encryption

I chose BTRFS for its modern features:

- **Checksumming**: Protects against silent data corruption.
- **Copy-on-Write**: Enables instantaneous, low-cost snapshots.
- **Transparent Compression**: `zstd` compression saves space without significant performance overhead.

The two 4TB drives are mirrored in a RAID 1 array, providing redundancy against a single drive failure. The entire array is encrypted using LUKS2, with the key stored on the boot SSD for automatic mounting. This protects data at rest in case of physical theft or drive disposal.

Mount options in `/etc/fstab`:

```bash
/dev/mapper/crypt-sda /mnt/storage btrfs defaults,noatime,compress=zstd 0 2
```

### Backup: Restic + Cloudflare R2

RAID does not protect against accidental deletion, file corruption, or catastrophic failure. My backup strategy follows the 3-2-1 rule.

Daily, automated backups are managed by systemd timers running `restic`. Backups are encrypted and sent to Cloudflare R2, providing an off-site copy. R2 was chosen for its zero-cost egress, which is a significant advantage for restores.

The backup script covers critical application data and the Docker Compose configurations:

```bash
BACKUP_PATHS=(
    "/mnt/storage"        # All application data
    "/home/karan/stacks"  # Docker Compose configs
)
```

Each backup run reports its status to a [healthchecks.io](https://healthchecks.io) endpoint, which sends a push notification on failure. I must appreciate its generous free tier, which is more than sufficient for my needs.

<div style="text-align: center;">
<a href="/images/homelab-healthcheck.png" class="lightbox-thumbnail" data-featherlight="image"><img src="/images/homelab-healthcheck.png" alt="Healthchecks.io backup monitoring dashboard" width="400"></a>
</div>

## Conclusion

This homelab represents a shift in philosophy from exploring complexity to valuing simplicity and reliability. The upfront hardware investment of ~$1,200 is offset by eliminating recurring cloud hosting costs and providing complete control over my data and services.

For those considering a homelab, my primary recommendation is to start with a simple, well-understood foundation. A reliable machine with a solid backup strategy is more valuable than a complex, hard-to-maintain cluster. The goal is to build a system that serves your needs, not one that you serve.

---
