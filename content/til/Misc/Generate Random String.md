+++
title = "Generate Random String"
date = 2021-06-15
type = "post"
in_search_index = true
[taxonomies]
til = ["Misc"]
+++

You can use the following ways to generate a random string (helpful in cases like generating a random password in a shell script etc):

- `tr -dc A-Za-z0-9 </dev/urandom | head -c 13 ; echo ''`
- `openssl rand -base64 12`
