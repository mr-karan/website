+++
title = "Minimal SystemD Starter Template"
date = 2022-06-12
type = "til"
description = "A reusable systemd service unit template for registering new services on a Linux system."
in_search_index = true
[taxonomies]
tags = ["Linux"]
+++

Here's a barebone/re-usable `systemd` service unit snippet that I often use to copy/paste for registering new services:

```ini
[Unit]
Description=Program Description
Documentation=https://program.url
After=network-online.target
Requires=network-online.target
StartLimitIntervalSec=0

[Service]
User=ubuntu
Group=ubuntu
ExecStart=/usr/local/bin/app.bin --config=/etc/app/config.toml
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```