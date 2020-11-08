+++
title = "Migrating my blog to Zola"
date = 2020-11-08T08:10:55+05:30
type = "post"
description = "The reasons I ported my blog from Hugo and my first experience with Zola"
in_search_index = true
[taxonomies]
tags = ["Meta"]
+++

I've been writing on this blog for about 2 years now. This has been the longest I've stuck on to the same _technology stack_ for my blog. I've previously jumped from a Jekyll based static site to a Medium blog before finally settling for [Hugo](https://gohugo.io/).

I've been using Hugo since 2018 but I don't recall as to _why_ I went ahead with it. Maybe it was increasingly popular at that time and everyone touted Hugo as _the_ solution to Static Site Generator (referred to as SSG from here on). There are 1000s of SSGs and at least a dozen of websites which lists all the SSGs out there. This is crazy by any standards. Hugo started as a generic blog generator but over the years it has become a _website generator_. It's no longer aimed at people who just want to have a small little static website/blog but supports all the use cases for people building full-fledged static websites. IMHO these two goals are overarching however this has resulted in a simple project to become incredibly complex over time.

### Tipping Point

Anyway, so I wanted to change the look of the homepage on my website so I decided to look at Hugo's documentation. Hugo's documentation is great for someone who knows what exactly are they looking for. The documentation is so huge that you simply cannot grok it in one evening. I had zero ideas on how to customise the damn homepage of my blog and after spending hours buried in the documentation I was able to kind of figure the solution but it was unintuitive, to say the least. Apparently, to override any template from the theme, you have to mirror the directory structure of the theme in your root directory. Which meant, I needed to look at the source code of the theme, figure out the project structure, copy-paste all the folder names and put my override of `index.html` there. Which, BTW **magically** overrides it. This whole magic thing is BS and I am being strongly opinionated here.

There is more than one way to do something in Hugo. Different theme authors use different styles, which makes the whole thing even more complex. It also means for my customisations to work across themes, well you guessed it right: **it's impossible**.

Recently I discovered that I was unable to preview my Hugo website locally without internet because I had a Twitter [shortcode](https://gohugo.io/content-management/shortcodes/#tweet) in one of my blog post (which makes an API call to Twitter to render a nice card preview). The site completely failed to render instead of just logging a warning. Bollocks.

The tipping point for me, however, was when the theme I was using stopped working with the latest version of Hugo at that point. So, picture this -- You make dozens of custom changes and then one update just _breaks_ your website. Now not only you have to fix your shit but the theme you were using, you've to make upstream changes to the theme or maintain your own fork. And no, this is not a one-off experience. Hugo upgrades are a joke, they are known to break very very often.

I was done at this point. I didn't want to deal with this BS of continuously fighting the generator for my blog.

### A fresh change

Being a practitioner of [Yak Shaving](https://projects.csail.mit.edu/gsb/old-archive/gsb-archive/gsb2000-02-11.html), I discussed the idea of a "tinyhugo" with [Kailash](https://nadh.in/) and [Sarat](https://www.saratchandra.in/). We'd arrived at a spec and I started writing some code to pander to my NIH syndrome.

However, I was still not convinced that a simpler solution doesn't exist. I spent countless hours exploring other alternatives. I'd used [Lektor](https://www.getlektor.com/), [Pelican](https://blog.getpelican.com/), [Eleventy](https://www.11ty.dev/) before finally stumbling upon [Zola](https://www.getzola.org/) from HN/Lobster discussions. I've got to say, the landing page gave a _fresh_ feeling - one that I've not seen with any other alternatives. In fact quite opposite to the Eleventy landing page which looks like an over-engineered piece of software to generate websites (Not hating on it, there might be use cases for it, but the JS tooling and dependency system is something that I would not want to touch with a 10ft pole).

Zola's primary appeal to me was that like Hugo it's extremely fast and comes as a single binary no dependency package. I looked at the docs the first impression was they are concise enough to get a basic idea. Zola is strongly opinionated, even to the extent of dictating a project structure and sometimes filenames too. I actually preferred this over the _magic_ Hugo does. In less than 2 hours I was able to port the home page of my blog (and tweak it to my liking) in Zola. I decided to abandon my own `tinyhugo` attempt because for the very fact Zola fits my needs very well.

The thing that I really loved about Zola is how it enforces a separation between [Section](https://www.getzola.org/documentation/content/section/) and [Pages](https://www.getzola.org/documentation/content/page/). The section represents a "collection" of posts. So a _blog_ can be a section, and I can have another section called "Book Reviews". I could easily tell Zola where to look for the templates by specifying the same in `content/book_reviews/_index.md`. I don't have to read Hugo docs or do _Google-fu_ to figure this out, it's right there in the docs and very apparent.

For the record, I still don't know how to customise different templates for different sections in Hugo, but I couldn't care less.

### Migration

The migration was pretty straightforward -- I had to copy the `content folder`s of my blog (which are just a bunch of `.md` fikes) and replace `YAML` frontmatter to `TOML`. There were a few variable changes that I needed to do manually but since they were a manageable 20-25 posts, I did it by hand. I could potentially automate but then rabbit deep in the rabbit hole of Yak Shaving. The good part was that I was able to retain the same URL structure for my new blog because the URL scheme was based on the file paths.

I spent some time porting [hugo-ink](https://github.com/knadh/hugo-ink) to Zola and did minor CSS tweaks to it. Zola uses the Terra language for templating and it's much more pleasing to eyes than the Go Template syntax. Zola comes with pretty neat features like Search, RSS/Atom Feeds, Syntax Highlighting and SASS->CSS Processors.

What took me time however was to figure out how to get `opengraph` tags in each page. Hugo provides nifty [template](https://github.com/gohugoio/hugo/blob/master/tpl/tplimpl/embedded/templates/opengraph.html) for this use case but Zola is pretty barebones like that. People who care a lot about SEO need to spend some extra efforts here.

### Future

Zola is still a pretty new kid on the block but the author shares the same frustration about Hugo:

>  it personally drives me insane, to the point of writing my own template engine and static site generator. Yes, this is a bit biased. -- [Source](https://github.com/getzola/zola#-explanations)

This also reflects in the issues/PRs I've seen for Zola and the author is opinionated about not adding features which would make Zola complicated. Overall I am very happy with the switch and it was long due. I feel more confident in tweaking certain sections of my website. I plan to open-source the current theme in the next few days.

You can read the [Source Code](https://git.mrkaran.dev/karan/website) of this website if you'd like to explore how this website is built.

Fin!