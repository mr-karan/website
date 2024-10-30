+++
title = "How I use LLMs"
date = 2024-10-30
type = "post"
description = "How I use Aider CLI and LLMs to streamline my coding workflow"
in_search_index = true
[taxonomies]
tags= ["Programming", "ai"]
+++

Just yesterday, GitHub [announced](https://github.blog/news-insights/product-news/bringing-developer-choice-to-copilot/) integrating Claude 3.5 Sonnet with Copilot. Interesting times ahead. In my experience, Claude has been remarkably better than the GPT-4 family of models for programming tasks. I've tried a bunch of tools like Cursor, Continue.dev but finally settled with [Aider](https://aider.chat/) for most of my tasks. In this post, I want to write about my workflow of using Aider when working on small coding tasks.

Aider is an open source Python CLI which supports multiple models, including Claude 3.5 Sonnet. Aider describes itself as "AI pair programming in your terminal". The tool integrates `git` quite well in its workflow so it can edit files, create new files, and track all changes via git. In case you want to revert, simply reverting the commit or using the `/undo` shortcut would do the same.

The tool has multiple modes that serve different purposes:

- `/ask`: Use it when you simply want to chat with the model about the codebase or explain some pieces of it. This mode won't touch your files. It's great for understanding existing code or getting explanations.
- `/architect`: Use it to discuss a broad overall idea. The model will propose some changes to your files. You can further chat and tune it to your preferences.
- `/code`: This will directly edit your files and commit them.

My typical workflow involves running Aider in a terminal while keeping VSCode open for manual code review. I often use the `--no-auto-commits` flag to view the diffs before committing. Despite advances in LLM technology, I believe they haven't yet reached the stage where they can fully understand your team's coding style guides, and I prefer not to have a certain style forced upon me. Manually tweaking portions of AI-generated functions still proves helpful and saves considerable time.

To begin, `aider --sonnet` would open the interactive window where you can begin writing prompts.

![image](/images/aider-4.png)

To add context, you need to add files using commands like `/add main.py`. What makes Aider powerful is its control over the LLM context - you can `/add` or `/drop` source code, or even `/reset` to drop all files and start with a fresh context. This granular control helps manage the context window effectively.

A really cool thing about it is that it gives an approximate idea of the number of tokens (cost) associated with each prompt. I find it useful to remove unnecessary files from the context window, which not only helps in getting sharper, more accurate responses but also helps with the costs. There's a nice `/tokens` command which will show the cost of sending each file added in context with the prompt.

![image](/images/aider-3.png)

I find the Aider + Claude 3.5 combo works really well when you have a narrow-scoped, well-defined task. For example, this is the prompt I used on a codebase I was working on:

> Theme preference is not preserved when reloading pages or navigating to new pages. We should store this setting in localStorage. Please implement using standard best practices.

![image](/images/aider-1.png)

Under the hood, Aider uses [tree-sitter](https://aider.chat/2023/10/22/repomap.html) to improve code generation and provide rich context about your codebase. Tree-sitter parses your code into an Abstract Syntax Tree (AST), which helps Aider understand the structure and relationships in your code. Unlike simpler tools that might just grep through your codebase, tree-sitter understands the actual syntax of your programming language.

- It can identify function definitions, class declarations, variable scopes, and their relationships
- It extracts full function signatures and type information
- It builds a dependency graph showing how different parts of your code relate to each other
- It helps rank the importance of different code sections based on how often they're referenced

This means when you're working on a task, Aider isn't just blindly sending your entire codebase to the LLM. Instead, it creates an optimized "repository map" that fits within your token budget (default is 1k tokens, adjustable via `--map-tokens`). This map focuses on the most relevant pieces of your code, making sure the LLM understands the context without wasting tokens.

Aider's approach to AI pair programming feels natural and productive. Here are some example prompts where it helped me build stuff in less than a minute:

> Modify fetch method in store/store.go to filter out expired entries

> Write a k6 load test script to benchmark the `POST /submit` endpoint and simulate real-world traffic patterns

> Create a Makefile, Dockerfile, goreleaser.yml for my Go binary. Target platforms: arm64 and amd64

![image](/images/aider-2.png)

Make sure to go through the [Tips](https://aider.chat/docs/usage/tips.html) page to effectively try out Aider on your existing projects.

Fin!