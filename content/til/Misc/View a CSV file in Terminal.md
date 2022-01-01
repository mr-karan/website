+++
title = "View a CSV file in Terminal"
date = 2021-09-21
type = "post"
in_search_index = true
[taxonomies]
til = ["Misc"]
+++

```
column -s, -t < my.csv | less -#2 -N -S
```

// TODO: Add `cut` command examples too.
