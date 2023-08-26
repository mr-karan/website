+++
title = "Using the Nomad API to Manage Allocations"
date = "2022-07-26"
type = "til"
description = "A guide to using the Nomad API for listing and filtering allocations."
in_search_index = true
[taxonomies]
tags = ["Nomad"]
+++

## List allocations

```sh
curl -vvvv --get http://localhost:4646/v1/allocations\?namespace\=\*
```

### Filter

By using `--filter` param, we can restrict the list of allocations with specific filter queries.

```sh
curl -vvvv --get http://localhost:4646/v1/allocations\?namespace\=\* \
    --data-urlencode 'filter=NodeID == "a7542cd4-491d-26c8-64d4-db4db979f61b"'
```