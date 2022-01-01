+++
title = "Transform requests to cURL"
date = 2021-09-21
type = "post"
in_search_index = true
[taxonomies]
til = ["Python"]
+++

```python
$ pip install curlify
...
import curlify
print(curlify.to_curl(r.request))  # r is the response object from the requests library.
```