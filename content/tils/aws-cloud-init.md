+++
title = "Working with cloud-init in AWS"
date = 2022-09-21
type = "til"
description = "A guide on how to use cloud-init for running scripts and managing logs in AWS."
in_search_index = true
[taxonomies]
tags = ["AWS"]
+++

## Run the script manually

```bash
cd /var/lib/cloud/instance/scripts
sudo ./part-001
```
## To view logs

```
sudo journalctl -u cloud-final -b
```

## To output logs to a different file

```
#!/usr/bin/env bash
set -Eeuo pipefail
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
```

Logs will be available on `/var/log/user-data.log`.