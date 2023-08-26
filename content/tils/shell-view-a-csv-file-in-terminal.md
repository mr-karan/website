+++
title = "How to View CSV Files in Terminal"
date = 2022-06-21
type = "til"
description = "A brief guide on how to view CSV files directly in the terminal using shell commands."
in_search_index = true
[taxonomies]
tags = ["Shell"]
+++


```sh
column -s, -t < my.csv | less -#2 -N -S
```
