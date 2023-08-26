+++
title = "Controlling Screen Brightness in Linux"
date = 2022-06-21
type = "til"
description = "A guide on how to control screen brightness in Linux using xrandr command."
in_search_index = true
[taxonomies]
tags = ["Linux"]
+++

## Get a list of devices connected

```
xrandr | grep " connected" | cut -f1 -d " "
```

## Tweak the brightness value

```
xrandr --output eDP-1 --brightness 0.7
```
