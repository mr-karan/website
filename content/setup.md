+++
title = "My Setup"
images = ["/images/night-setup.jpg"]
template = "page.html"
in_search_index = true
+++

![image](/images/day-setup.jpg)

## Hardware

My work laptop is a [Dell Latitude 7400](https://www.dell.com/en-in/work/shop/business-laptop-notebook-computers/latitude-7400-business-laptop/spd/latitude-14-7400-laptop). I do have a 2016 Apple Macbook Pro (13"/8GB/128GB version) which is _rarely_ used these days.

The other stuff on the desk includes:

- **Monitor**: [Acer ET322QK](https://www.amazon.in/gp/product/B0788GQM7C/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1). Purchased this recently. I used to drool over multi-monitor setups before but I just decided to get one big monitor (this one is 31.5"). The 4K UHD really really does make the whole experience better. The texts look crisper, extra room size to stack multiple windows and the colours are overall so much better than my old monitor which was a cheap BenQ 24" which I used for about 4 years.

- **Mouse**: [Logitech MX Master 2S](https://www.logitech.com/en-in/product/mx-master-2s-flow)
- **Keyboard**: [Redgear Invador MK881](https://www.amazon.in/Redgear-MK881-Professional-Mechanical-Lightning/dp/B01N0UMPCR). I really can't use this in an office environment because the keys are a ripoff of Cherry MX Blue switches and they make a _lot_ of noise. But this is 2020, who's going to the office anyway?
- **Headphones**: Bose QC25. Best purchase ever. Picked it up for a great discount after they were discontinued. They are really comfortable to wear for 3-4 hours of continuous usage and produced a very balanced sound.
- **Mousepad**: [AmazonBasics Extended Mouse Pad](https://www.amazon.in/AmazonBasics-Extended-Gaming-Mouse-Black/dp/B06X19FLTC)
- **Gaming Console**: [Sony PS4 Slim 1TB](https://www.playstation.com/en-in/explore/ps4/). I've switched on my console for about 50 hours in 3 years. Talk about bad financial decisions.
- **External Storage**: [WD Elements 2TB](https://www.amazon.in/gp/product/B00PLOXG42?pf_rd_r=K16PZ9NJVTH3BNNA3M3S&pf_rd_p=649eac15-05ce-45c0-86ac-3e413b8ba3d4&th=1)

The desk is an [IKEA Linnmon](https://www.ikea.com/in/en/p/linnmon-adils-table-white-s49246449/) and chair is a 2nd hand Featherlite chair which I picked up for quite cheap from a local store in Bengaluru, India.

I use a [OnePlus 7](https://www.oneplus.in/7) with stock OxygenOS as my primary phone. I pair it up with [Bose SoundSport Wireless](https://www.boseindia.com/en_in/products/headphones/earbuds/soundsport-free-wireless.html) earbuds because the world decided that there will be no headphones jack in a phone costing 30k+ and somehow we are fine with that? I also take notes on my [Apple iPad](https://www.apple.com/in/ipad-10.2/) when I am reading a long article or collating notes.

## Home Server

I run 2 Raspberry Pi 4 (4GB RAM + 2GB RAM) for self-hosting a few applications for personal use. If you want to read a detailed post on my home server post, you should check out [this](/posts/home-server-updates/).

## Software

I run [EndeavourOS](https://endeavouros.com/) which is a painless setup for running Arch Linux. I like to stay on the bleeding edge.

![image](/images/setup-terminal.png)

I use [KDE Plasma](https://kde.org/plasma-desktop) as my primary desktop environment with [Breeze](https://github.com/KDE/breeze) dark theme.

Some of the applications I use daily:

- **Browser**: [Firefox Developer Edition](https://www.mozilla.org/en-US/firefox/developer/).
- **Mail**: [Thunderbird](https://www.thunderbird.net/en-US/).
- **Music Player**: [Spotify](https://open.spotify.com/). I scrobble all tracks to my [last.fm](https://www.last.fm/user/thetechfreak) account. I use [spicetify-cli](https://github.com/khanhas/spicetify-cli) to use a custom [theme](https://github.com/morpheusthewhite/spicetify-themes/tree/master/Aritim-Dark).
- **Notes**: [Joplin](https://joplinapp.org/) for all notes + wiki. Synced to my Dropbox account.
- **Editor**: [VSCode](https://code.visualstudio.com/).
- **Terminal**: [Konsole](https://kde.org/applications/en/system/org.kde.konsole) with `zsh` and [starship](https://starship.rs/) prompt.

### Fonts

I use [Noto Sans](https://fonts.google.com/specimen/Noto+Sans) as my primary reading font and [Cascadia](https://github.com/microsoft/cascadia-code) as a monospace font.

### Code

**Theme**: [Night Owl](https://marketplace.visualstudio.com/items?itemName=sdras.night-owl) with _italics_ disabled.

**Extensions**:

- [better-toml](https://marketplace.visualstudio.com/items?itemName=bungcip.better-toml)
- [golang](https://marketplace.visualstudio.com/items?itemName=golang.go)
- [terraform](https://marketplace.visualstudio.com/items?itemName=hashicorp.terraform)
- [docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)
- [kubernetes-tools](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools)
- [python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [liveshare](https://marketplace.visualstudio.com/items?itemName=ms-vsliveshare.vsliveshare)
- [yaml](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
- [todo highlight](https://marketplace.visualstudio.com/items?itemName=wayou.vscode-todo-highlight)
- [gitlens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)

### Terminal

I use [Konsole](https://konsole.kde.org/) since it comes with KDE Plasma. I use `zsh` shell with a standard off the shelf config from [OhMyZsh](https://ohmyz.sh/).

Some of the extra plugins that I use and found helpful:

- [fzf](https://github.com/junegunn/fzf)
- [zsh-z](https://github.com/agkozak/zsh-z)
- [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions)
- [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting)

I pair `zsh` with [starship](https://starship.rs/) which makes the entire terminal config very portable and easy to setup.

## Future Goals

It took me a good amount of experimentation with different apps, peripherals and distro-hopping but I finally feel like my current workflow is reliable and something that won't require any tweaking for a good amount of time. Shortly, I'd like to figure out a setup to automate my backups from my self hosted `git` server as well as set up a Nextcloud WebDAV to get rid of Joplin's Dropbox sync.

But that's for some other day, the weather in Bengaluru is amazing for a month like July, so I'll make some hot ginger tea and enjoy the rainy evening for now.

Also, bonus picture. This is how my setup looks at night!

![image](/images/night-setup.jpg)

Fin!
