+++
title = "AI and Home-Cooked Software"
date = 2025-10-05
type = "post"
description = "AI is enabling a new category of personal software. Welcome to the era of home-cooked applications."
in_search_index = true
[taxonomies]
tags = ["Programming", "AI", "Philosophy"]
[extra]
og_preview_img = "/images/homecook-ai-1.png"
+++

Everyone is worried that AI will replace programmers. They're missing the real revolution: AI is turning everyone into one.

I've been noticing a new pattern: people with deep domain knowledge but no coding experience are now building their own tools. Armed with AI assistants, they can create custom workflows in a matter of days, bypassing traditional development cycles. Are these solutions production-ready? Not even close. But they solve urgent, specific problems, and that's what matters. Tasks that once required weeks of specialized training are quickly becoming weekend projects.

This trend is happening even within the AI companies themselves. Anthropic, for example, shared how their own teams use Claude to accelerate their work. Crucially, this isn't limited to developers. [Their post details how non-technical staff now build their own solutions](https://www.anthropic.com/news/how-anthropic-teams-use-claude-code) and create custom automations, providing a powerful real-world example of this new paradigm.

## Home-Cooked Software

Why search for a generic tool when you can build exactly what you need? This question leads to what I call 'home-cooked software': small, personal applications we build for ourselves, tailored to our specific needs. [Robin Sloan](https://www.robinsloan.com/notes/home-cooked-app/) beautifully describes building an app as making "a home-cooked meal," while [Maggie Appleton](https://maggieappleton.com/home-cooked-software/) writes about "barefoot developers" creating software outside traditional industry structures.

What's new isn't the concept but the speed and accessibility. With AI, a custom export format, a specific workflow, or the perfect integration is now an afternoon's work. We're entering an unprecedented era where the barrier between wanting a tool and having it has nearly vanished.

But let's be clear: the journey from a prototype to a production-ready application is as challenging as ever. In my experience, an AI can churn out a first draft in a few hours, which gets you surprisingly far. But the devil is in the details, and the last stretch of the journey – handling edge cases, ensuring security, and debugging subtle issues – can stretch into weeks. This distinction is crucial. AI isn't replacing programmers; it's creating millions of people who can build simple tools. There's a significant difference.

## The New Economics

AI is fundamentally reshaping the economics of building software. Before AI, even a simple tool required a significant time investment in learning programming basics, understanding frameworks, and debugging. Only tools with broad appeal or critical importance justified the effort. Now, that effort is measured in hours, not months, and the primary barrier is no longer technical knowledge, but imagination and a clear understanding of one's own needs.

This doesn't apply to complex or security-critical systems, where deep expertise remains essential. But for the long tail of personal utilities, automation scripts, and custom workflows, the math has changed completely. I'm talking about solving all those minor irritations that pile up: the script to reformat a specific CSV export, the dashboard showing exactly the three metrics you care about, or a script that pulls data from a personal project management tool to sync with an obscure time-tracking app.

These tools might be held together with digital duct tape, but they solve real problems for real people. And increasingly, that's all that matters.

## The Hidden Costs

But this newfound capability isn't free. It comes with what I call the "AI Tax": a set of hidden costs that are rarely discussed.

First, prompt engineering can be surprisingly time-consuming, especially for tasks of moderate complexity. While simple requests are often straightforward, anything more nuanced can become an iterative dialogue. You prompt, the AI generates a flawed output, you clarify the requirements, and it returns a new version that misses a different detail. It’s a classic 80/20 scenario: you get 80% of the way there with a simple prompt, but achieving the final 20% of correctness requires a disproportionate amount of effort in refining, correcting, and clarifying your intent to the model.

Second, there's the verification burden. Every line of AI-generated code is a plausible-looking liability. It may pass basic tests, only to fail spectacularly in production with an edge case you never considered. AI learned from the public internet, which means it absorbed all the bad code along with the good. SQL injection vulnerabilities, hardcoded secrets, race conditions—an AI will happily generate them all with complete confidence.

Perhaps the most frustrating aspect is "hallucination debugging": the uniquely modern challenge of troubleshooting plausible-looking code that relies on APIs or methods that simply don't exist. Your codebase becomes a patchwork of different AI-generated styles and patterns. Six months later, it's an archaeological exercise to determine which parts you wrote and which parts an AI contributed.

But the most significant danger is that AI enables you to build systems you don't fundamentally understand. When that system inevitably breaks, you lack the foundational knowledge to debug it effectively.

## Building for One

Despite these challenges, there’s something profoundly liberating about building software just for yourself. Instead of just sketching out ideas, I've started building these small, specific tools. For this blog, I wanted a simple lightbox for images; instead of pulling in a heavy external library, I had Claude write a 50-line JavaScript snippet that did exactly what I needed. I built a simple, single-page [compound interest calculator](https://cagr.mrkaran.dev) tailored for my own financial planning. To save myself from boilerplate at work, I created [prom2grafana](https://prom2grafana.mrkaran.dev), a tool that uses an LLM to convert Prometheus metrics into Grafana dashboards.

Ten years ago, I might have thought about generalizing these tools, making them useful for others, perhaps even starting an open source project. Today? I just want a tool that works exactly how I think. I don't need to handle anyone else's edge cases or preferences. Home-cooked software doesn't need product-market fit—it just needs to fit you.

We're witnessing the emergence of a new software layer. At the base are the professionally-built, robust systems that power our world: databases, operating systems, and rock-solid frameworks. In the middle are commercial applications built for broad audiences. And at the top, a new layer is forming: millions of tiny, personal tools that solve individual problems in highly specific ways.

This top layer is messy, fragile, and often incomprehensible to anyone but its creator. It's also incredibly empowering. Creating simple software is becoming as accessible as writing. And just as most writing isn't professional literature, most of this new software won't be professional-grade. That's not just okay; it's the point.

The implications are profound. Subject-matter experts can now solve their own problems without waiting for engineering resources, and tools can be hyper-personalized to a degree that is impossible for commercial software. This unlocks a wave of creativity, completely unconstrained by the need to generalize or find a market.

Yes, there are legitimate concerns. Security is a real risk, though the profile changes when a tool runs locally on personal data with no external access. We're creating personal technical debt, but when a personal tool breaks, the owner is the only one affected. They can choose to fix it, rebuild it, or abandon it without impacting anyone else. Organizations, on the other hand, will soon have to grapple with the proliferation of incompatible personal tools and establish new patterns for managing them.

But these challenges pale in comparison to the opportunities. The barrier between user and creator is dissolving. We're entering the age of home-cooked software, where building your own tool is becoming as natural as cooking your own meal.

The kitchen is open. What will you cook?


