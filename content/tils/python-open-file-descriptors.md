+++
title = "Handling Open File Descriptors Limit in Python"
date = "2022-07-01"
type = "til"
description = "A demonstration of the 'Too many open files' OSError in Python, which occurs when the open file descriptors limit is reached."
in_search_index = true
[taxonomies]
tags = ["Python"]
+++

See [Golang/Open File Descriptors](/tils/golang-open-file-descriptors) version for context.

```python
>>> [open("FD_TEST_%d.txt" % i, "w") for i in range(1, 1025)]

OSError: [Errno 24] Too many open files: 'FD_TEST_1021.txt'
>>> 
```