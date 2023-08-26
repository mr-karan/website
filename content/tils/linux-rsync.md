+++
title = "Useful rsync Command Snippets for Linux"
date = 2022-06-12
type = "til"
description = "A collection of useful rsync command snippets for copying files locally and passing SSH extra options."
in_search_index = true
[taxonomies]
tags = ["Linux"]
+++

## Copying files locally

```
rsync -avhW --no-compress --progress /src/ /dst/
```

## Passing SSH Extra Options

```
rsync -avzhP --stats -e 'ssh -o "Hostname <ip>"' <bastion_host>:/src/ /dst/
```
