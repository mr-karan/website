+++
title = "Managing Processes in Linux"
date = 2022-06-12
type = "til"
description = "A guide on how to manage processes in Linux using ps, kill, and pkill commands."
in_search_index = true
[taxonomies]
tags = ["Linux", "Processes", "ps", "kill", "pkill"]
+++

### List of running process
```bash
ps aux
```

### Kill a process

```sh
kill -9
```

### Kill a process by name

```bash
pkill -9 -f '././bin/app.bin'
```