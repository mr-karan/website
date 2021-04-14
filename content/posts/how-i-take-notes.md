+++
title = "How I take Notes"
date = 2021-04-14T08:10:55+05:30
type = "post"
description = "My note-taking system using Joplin."
in_search_index = true
[taxonomies]
tags = ["Productivity", "Tools"]
[extra]
og_preview_img = "/images/joplin-desktop.png"
+++

Over the past 2-3 years, note-taking apps have become all the rage. Note-taking is an extremely subjective topic and a lot of it depends on the individual's workflow. There's no one size fits all and maybe that justifies the ever-expanding landscape of such apps. I've tried a few popular ones (Notion, Roam Research) in the recent past but never really quite stuck to any after the initial hype phase.

I even collaborated with [@iamd3vil](https://sarat.dev/) to make our [own version](https://github.com/hackstream/zettel/) of the Zettelkasten based note-taking app. I found the Zettelkasten system to be really useful on paper but then again, I didn't use it after a few weeks.

Tried the old school way of Bullet Journal (and I did end up liking it quite a lot) but it was not so practical in many cases (like documenting code snippets, URLs etc).

Disgruntled with all the options, I just had a simple folder on my laptop with some markdown files in it. It was a stop-gap solution until I found something better.

**TL;DR**: I've been through a pendulum phase of finding a new note-taking app, wasting time to set it up the "proper way" and then just end up not using it.

## Enter Joplin

![image](/images/joplin-desktop.png)

Thanks to [@shantanugoel](https://shantanugoel.com) who introduced me to [Joplin](https://joplinapp.org/). He's a [heavy user](https://shantanugoel.com/2020/03/20/hammerspoon-backup-joplin-notes-dotfiles-git-macos/) of it as well and that gave me some confidence to try it out. I initially disliked it because of _not-so-great-looking_ UI theme and how it essentially looked _just_ an editor. Admittedly, I was proven wrong quickly in my initial judgement. As I gave more time to it, I noticed I kept coming back to Joplin "naturally" and stuck through it because it's so damn simple to use. Notion, for people who have tried it would know it complicates a lot of simple tasks. You need to create databases to render a simple table, every component is a "block" (a new page) and yes it's slow (although they are [working on it to make it better](https://www.notion.so/notion/Focus-on-performance-reliability-89f937a6ccc04905b1dcfa878537e08d), just to be fair). Notion focuses a lot on team collaboration features, which I didn't need for my "personal" note-taking system.

**TL;DR**: Joplin is fast, it's open-source, it's based on Markdown, and it's simple to use. A tool you just forget that it exists, because it becomes a natural extension to your workflow. It has a great plugin system that you can use to extend it and build your own utilities on top of it. The search is based on `sqlite3` FTS which is pretty awesome!

## Workflow

Joplin revolves around the concept of **notebooks**. Notebooks are broader categories for your content and you can nest multiple subnotebooks for specific categories.

I've the following notebooks and subnotebooks in my Joplin setup:

```
- Bookmarks
  - Twitter Threads
  - HN Threads
  - Articles
  - Design Inspo
  - Youtube Videos
- Inbox
  - Links
  - Adhoc Notes
- Personal
  - Finance
  - Dev Setup
  - OSS Ideas
  - Self Hosted Setup
- Work
  - Org-Stuff
  - Redacted
```

Over the week, I primarily use the `Inbox/Adhoc Notes` notebook as a brain dump. I don't focus much on the structure, the aim is to get the content out and stored. I'm also someone who doesn't like to keep more than 5 browser tabs open at any time, so I use `Links` notebook with Joplin's [Web Clipper](https://joplinapp.org/clipper/) service to store these links to read later.

Every weekend, I clean up these notebooks to achieve "Inbox Zero". The idea is to move all these ad-hoc notes to their proper notebooks, annotated with tags. All the useful links are moved in the appropriate `Bookmarks/...` notebook as well. This helps me find stuff quicker at a later time.

I heavily use Tags in all my notebooks, which allows me to have a unified view of different kind of stuff I’ve. For example “golang” tag in my Work notes and Personal notes, allows me to see all the “golang” stuff together in one place.

For stuff that can be shared publicly, I basically copy-paste those notes in my [public wiki](https://notes.mrkaran.dev/) as well. This allows me to share snippets/commands with others, which Joplin cannot do.

## Synchronisation

Joplin provides a bunch of different [sync](https://joplinapp.org/#synchronisation) options. I've tried Dropbox, Nextcloud and AWS S3 targets in the past but off late there's a new sync option, [Joplin Server](https://github.com/laurent22/joplin/blob/dev/packages/server/README.md) which provides native sync for Joplin files. I found this option to be the best so far because Dropbox/OneNote etc have API limits and syncing on an initial device with lots of notes will be time-consuming.

I self-host this Joplin Sync Server on my server and have configured the Android app and the Desktop app to use this server endpoint as the sync `target`. So far so good, although it's relatively a newer sync option so it's pertinent to have alternate backups.

## Backups and Export

Joplin stores all the files locally on a device in a `sqlite3` DB. It can export notes in markdown/HTML format however the file names are all named with the `id` of the note (and not really the title of the note). I found this to be a bit of a drawback, however, one can quickly whip up a small Python script to fix this using the Joplin API.

Joplin also has the option to export all of the notes and notebooks with their metadata (Geolocation, creation time etc), tags in a custom format called Joplin Export File (JEX). This option is pretty convenient to re-import in a new Joplin installation as well.

Sidenote for people using Joplin Server: Once https://github.com/laurent22/joplin/issues/4836 gets resolved, it'll be possible to do `joplin sync` and cron it, just like other sync targets. 

## Support

Joplin is 100% FOSS and is actively developed by [`@laurent22`](https://github.com/laurent22/) and a few other regular contributors. I contribute `$5/mo` to laurent22 via Github Sponsors. It's more or less the same amount that most note-taking apps charge for personal use as well, so this is just me expressing gratitude for building such a lovely software for the world to use it. I'm not sure of the motivations of `laurent22` behind building this and I don't wanna incorrectly assume anything either, but I guess some amount of financial incentive makes the whole deal sustainable for the open-source ecosystem.

Thanks for reading! It's been around a year that I am using Joplin and I posted this blog post only after really really using it a lot.

I'd love to know about your note-taking setups too, so please reach out to me on the usual channels that I'm available on and feel free to discuss!

Fin!

#### (Bonus Section) Why Not Obsidian

Yes, Obsidian is comparable to Joplin in a lot of ways. However there's a term in the [license](https://obsidian.md/eula) of Obsidian for personal use that makes it **impossible** to use it for your work stuff:

> You need to pay for Obsidian if and only if you use it for revenue-generating, work-related activities in a company that has two or more people. Get a commercial license for each user if that's the case

I don't have a problem for "paying" for software but such kinda licenses are just BS.
