+++
title = "Converting Python Requests to cURL Commands"
date = "2022-05-02"
type = "til"
description = "A brief guide on how to transform Python requests into cURL commands using the curlify library."
in_search_index = true
[taxonomies]
tags = ["Python"]
+++


```python
$ pip install curlify
...
import curlify
print(curlify.to_curl(r.request))  # r is the response object from the requests library.
```