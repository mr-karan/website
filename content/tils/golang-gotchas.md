+++
title = "Golang Gotchas"
date = 2022-09-24
type = "til"
description = "Gotchas"
in_search_index = true
[taxonomies]
tags = ["Golang"]
+++

## HTTP Responses

If you've a `http.ResponseWriter` object and using it to directly write the response to the connection, the order in which you write different parts of response is **very important**:

```go
// First write headers.
wr.Header().Set("Content-Type", "text/plain; version=0.0.4")
// Then set the status code. And yes, this is the function name for setting status code!
wr.WriteHeader(http.StatusOK)
// Then finally write the response body.
wr.Write([]byte("hello world"))
```

{% admonition(kind="Note") %}
- Headers should be written first. If any extra header is set after calling `WriteHeader` it's a no-op.
- Body should be after `WriteHeader`. Else it's a no-op.
{% end %}
