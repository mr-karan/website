+++
title = "Determining CPU Cores in Bash"
date = 2022-06-12
type = "til"
description = "A quick guide on how to determine the number of CPU cores using bash and the 'nproc' utility."
in_search_index = true
[taxonomies]
tags = ["Shell"]
+++

`nproc` is part of coreutils package that gives the number of cores available in an easy to consume way (no more grepping and parsing ). 

I wanted this to set `VECTOR_THREADS` variable for `vector` CLI to 1/2 of what is available on system.

```bash
#!/bin/bash

set -e

cores=`nproc --all`
cap=2
VECTOR_THREADS=$((cores / cap))

vector --config /etc/vector
```