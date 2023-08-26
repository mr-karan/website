+++
title = "Working with the Linux Filesystem"
date = 2022-07-11
type = "til"
description = "A guide on how to check disk size of directories and list files with modification timestamps in Linux."
in_search_index = true
[taxonomies]
tags = ["Linux"]
+++

## Check disk size of a directory

```bash
du -sh /var/log/*
```

## List files with modification timestamp

```sh
ls -laht
```

To see the files with the _oldest_ file modification timestamp, use `-r`

```sh
ls -lahtr
```