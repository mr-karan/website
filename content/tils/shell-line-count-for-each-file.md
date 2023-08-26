+++
title = "Counting Lines in Files with Bash"
date = 2022-06-21
type = "til"
description = "A concise guide on how to count lines in files using bash, including sorting the output."
in_search_index = true
[taxonomies]
tags = ["Shell"]
+++

To get `wc -l` for each file in the directory:

```sh
wc -l *.csv
```

To output the number of lines, sorted in decreasing order:

```sh
wc -l *.csv | sort -rn
```
