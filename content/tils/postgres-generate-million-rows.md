+++
title = "Generating a Million Rows of Random Data in PostgreSQL"
date = "2022-05-02"
type = "til"
description = "A guide to generating a million rows of random data in a PostgreSQL database using UUIDv4."
in_search_index = true
[taxonomies]
tags = ["Postgres"]
+++

I wanted a quick way to generate some random data in a PostgreSQL database and insert 1mn rows.

The following query shows how to generate a `UUIDv4` and insert 1mn rows:

```sql
INSERT INTO table (uuid, name)
SELECT uuid_in(overlay(overlay(md5(random()::text || ':' || clock_timestamp()::text) placing '4' from 13) placing to_hex(floor(random()*(11-8+1) + 8)::int)::text from 17)::cstring), 'load tests'
FROM generate_series(1, 1000000);
```