+++
title = "rsync"
date = 2021-09-01
type = "post"
in_search_index = true
[taxonomies]
til = ["CLI"]
+++

## Copying files locally

```
rsync -avhW --no-compress --progress /src/ /dst/
```

## Passing SSH Extra Options

```
rsync -avzhP --stats -e 'ssh -o "Hostname <ip>"' <bastion_host>:/src/ /dst/
```
