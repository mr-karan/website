+++
title = "Control Brightness"
date = 2021-08-25
type = "post"
in_search_index = true
[taxonomies]
til = ["Misc"]
+++

## Get a list of devices connected

```
xrandr | grep " connected" | cut -f1 -d " "
```

## Tweak the brightness value

```
xrandr --output eDP-1 --brightness 0.7
```
