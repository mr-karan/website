+++
title = "Karakeep to Kindle: KOReader over Tailscale"
date = 2026-08-09
type = "post"
description = "Jailbreaking a Kindle Oasis, putting it on my tailnet, and pointing KOReader at my self-hosted Karakeep so saved articles actually get read."
in_search_index = true
[taxonomies]
tags = ["Kindle", "Self-hosting", "Tailscale", "Karakeep", "KOReader"]
[extra]
og_preview_img = "/images/karakeep-kindle-koreader.jpg"
+++

I own a Kindle Oasis that mostly sat on the nightstand while I doomscrolled on the phone next to it. Not for lack of reading material: I save articles to [Karakeep](https://karakeep.app/), my self-hosted bookmark manager, all the time. But saving had quietly become a way of closing tabs without guilt. Everything was tagged, searchable, and well... _unread_.

So I jailbroke the Kindle, installed [KOReader](https://koreader.rocks/), joined it to my tailnet, and pointed KOReader's news reader at a list in Karakeep. The loop is now:

```text
save an article → add it to "Kindle Inbox" → sync in KOReader → read
```

No emailing files to an `@kindle.com` address, no dragging files over a USB cable. And an article sitting on the Kindle stands a far better chance of being read than one buried in a bookmark list.

## Jailbreaking the Oasis

Mine is a 10th-gen Oasis on firmware 5.16.x. Jailbreaks are specific to both model and firmware, and the methods change as Amazon ships updates, so any steps I paste here would be stale in a few months. Follow the [Kindle Modding jailbreak guide](https://kindlemodding.org/jailbreaking/) instead; it's kept current. Your model and firmware are under **Settings → Device Options → Device Info**.

The usual disclaimer: a jailbreak can brick the device, weakens its security, and may void the warranty. Keep the Kindle in airplane mode when the guide tells you to, and don't improvise around an over-the-air update.

After the jailbreak, I installed three things:

- [KUAL and MRPI](https://kindlemodding.org/jailbreaking/Legacy/post-jailbreak/installing-kual-mrpi/), the launcher and package installer most Kindle homebrew depends on.
- KOReader, via the Kindle Package Manager: search for `;kpm install koreader`.
- The OTA blocker recommended in the guide, so a routine update doesn't undo all of this.

The stock reader stays intact. KOReader is just another app launched from KUAL: it opens EPUBs directly, has far better typography controls, and ships a News Downloader plugin that fetches RSS and Atom feeds. That plugin is what makes this setup work.

## Getting it on the tailnet

Karakeep isn't exposed to the public internet. It's reachable only over [Tailscale](https://tailscale.com/), and I wanted to keep it that way, which meant the Kindle had to join the tailnet.

Underneath, a Kindle is a small ARM Linux computer — an old and weird one. Mine runs a 4.1 kernel from 2015, there's no package manager, and Amazon never meant for anyone to have a shell on it. So there's no `apt install tailscale`; the [Tailscale KUAL extension](https://github.com/mitanshu7/tailscale_kual) does the wiring, using the official static ARM binaries. Tailscale's own posts on [getting a Kindle onto a tailnet](https://tailscale.com/blog/tailscale-jailbroken-kindle) and [proxy and TUN modes](https://tailscale.com/blog/jailbroken-kindle-proxy-tun-modes) are useful background.

I changed a few of the extension's defaults:

- Removed `--ssh` from `up.args`. The Kindle doesn't need to accept SSH connections to download articles.
- Disabled the self-updater. It replaces the local binaries with the latest release, with no checksum verification and no rollback. I'd rather update two binaries by hand.
- Enrolled with a one-off, pre-approved, **untagged** auth key, then deleted it from the device. Untagged matters: Taildrop doesn't work with tagged nodes, and I wanted Taildrop later.

### Proxy mode

The extension offers three modes. Standard userspace mode makes the Kindle reachable *from* the tailnet, but doesn't let apps on the Kindle reach a `100.x.y.z` address. Kernel TUN gives real system-wide routing, but needs kernel support that not every firmware has. Proxy mode works everywhere: it exposes an HTTP/SOCKS proxy on `127.0.0.1:1055`, and KOReader already knows how to use one.

From KUAL, the startup order is:

```text
Tailscale → Start Tailscaled → Proxy Mode
Tailscale → Start Tailscale
```

![The Tailscale KUAL extension menu on the Kindle, including a custom action to collect Taildrop files](/images/karakeep-kindle-kual-tailscale.jpg)

Then point KOReader's HTTP proxy at `http://127.0.0.1:1055`, or set it directly in `settings.reader.lua`:

```lua
["http_proxy"] = "http://127.0.0.1:1055",
["http_proxy_enabled"] = true,
```

I don't run Tailscale at boot. It costs a few taps before each sync, but battery life is the whole point of an e-reader, and a VPN daemon doesn't need to run around the clock for a device that syncs once a day. I bring it up, sync, and stop it.

## Turning a Karakeep list into a feed

Karakeep already had the plumbing: any manual list can be [published as an RSS feed](https://docs.karakeep.app/integrations/rss-feeds/), protected by a token in the URL. I created a list called **Kindle Inbox**, enabled RSS in its sharing settings, and copied the URL. The token in the URL is the only thing protecting the feed — anyone who has it can read everything in the list.

KOReader's News Downloader keeps its feeds in `/mnt/us/koreader/news/feed_config.lua`. My whole config is one feed:

```lua
return {
    {
        "KARAKEEP_RSS_URL_WITH_SECRET_TOKEN",
        limit = 20,
        download_full_article = true,
        include_images = true,
    },
}
```

`download_full_article` is the important one. The feed entries only point back to the saved articles; with this on, KOReader fetches each page and converts it into a local EPUB.

I started with `include_images = false`, reasoning that an e-ink queue didn't need images and smaller downloads meant faster syncs. That theory survived about three articles: anything with screenshots or diagrams read noticeably worse, so I turned it back on. If you flip it later like I did, note that already-downloaded EPUBs don't gain images on the next sync. Delete them from the news folder, restart KOReader, and sync again.

To sync:

```text
KOReader → Tools → News downloader → Sync news feeds
```

The EPUBs land under `/mnt/us/koreader/news/`, grouped by feed, and work fully offline.

![A saved article from Karakeep, rendered as an EPUB in KOReader on the Oasis](/images/karakeep-kindle-koreader.jpg)

I like where the boundary sits: Karakeep is where I capture, tag, and archive. KOReader is only where I read.

## The feed with zero articles

My first sync created the right folder and downloaded nothing. Zero articles, no errors — technically a success.

The cause was one HTTP header. Karakeep returns:

```http
Content-Type: text/html; charset=utf-8
```

and the News Downloader version on my Kindle compared that entire string against the literal `text/html`. The `charset` parameter made every valid HTML response look like an unsupported type, so the plugin silently dropped all of them.

The fix is a one-liner in `koreader/plugins/newsdownloader.koplugin/main.lua`, right after the page is fetched:

```lua
local content_type, content = DownloadBackend:loadPage(link, cookies, extra_headers)

-- Compare the media type, ignoring parameters such as charset=utf-8.
content_type = content_type and content_type:match("^%s*([^;]+)")
```

This may well be fixed upstream by the time you read this, so check the current plugin source before patching. But if your feed syncs "successfully" with zero articles, look at the server's `Content-Type` header before blaming the network.

## Books go over Taildrop

RSS is right for articles. For DRM-free books and documents I use [Taildrop](https://tailscale.com/docs/features/taildrop). From the Mac, sending a file is one command:

```bash
tailscale file cp "The Great Gatsby - F. Scott Fitzgerald.epub" kindle-oasis:
```

The Kindle still has to collect the waiting file, so I added a small KUAL action for it:

```sh
mkdir -p /mnt/us/documents/Books
/mnt/us/extensions/tailscale/bin/tailscale \
    file get --conflict=rename /mnt/us/documents/Books
```

EPUB is my default because the text reflows around whatever font size and margins I pick. PDF only makes sense when the page layout itself matters, and even then an Oasis is a small screen for an A4 page. Worth repeating: Taildrop can't send to or from tagged nodes, so the Kindle has to be enrolled as a personal, untagged device.

## Don't leave a root shell lying around

Jailbreaking changes what you can assume about the device's security. During cleanup I found a passwordless root `telnetd` listening on port 23. Handy during setup — also handy for anyone else on the network. I killed it and confirmed the port was closed.

The rest of the checklist:

- Delete the auth key from the extension once the Kindle has joined the tailnet.
- Apply tailnet ACLs. Being on my private network doesn't mean it needs access to every machine on it.
- Check listening ports after installing any networking tool.
- Update the extension and binaries manually, from a known source, with verified checksums.
- Don't use a factory reset as cleanup. It deregisters the device, wipes your data, and can complicate the jailbreak, without touching Amazon's server-side data anyway.

For daily use I skip Amazon's home screen entirely: KOReader opens straight into my library, with no recommendations for books I never asked about.

## Will I actually use it?

The obvious failure mode: spend a weekend on the pipeline, admire the Kindle's green dot in the Tailscale admin console, write this post, and go back to reading rubbish on my phone. No amount of plumbing automates the part where I put the phone down.

What the plumbing does is remove the excuses. Karakeep catches things while I'm moving fast; the Kindle hands them back when I've slowed down. The network in between was complicated exactly once, and I haven't had to think about it since.
