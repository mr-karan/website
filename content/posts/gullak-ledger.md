+++
title = "Rewriting Gullak: SQLite -> .ledger files (and WhatsApp)"
date = 2026-02-02
type = "post"
description = "I rewrote Gullak to write to plain-text ledger files. LLM still helps, but it now has seatbelts."
in_search_index = true
[taxonomies]
tags = ["sideproject", "ledger", "plaintext", "ai", "python", "whatsapp"]
[extra]
og_preview_img = "/images/gullak-cover.png"
+++

So… I rewrote Gullak. Again.

If you missed v1: I built [Gullak](/posts/gullak/) last year — Go + Vue + SQLite + Telegram — and the whole gimmick was: I can type something like "Coffee 150" and it gets logged. It worked. Saumya used it too. Life was good.

And then slowly… it started annoying me.

**TL;DR**: Gullak v2 stores transactions in a `.ledger` file (double-entry), uses WhatsApp (because… India), streams responses to a tiny web UI, and forces every LLM output through a "preview + confirm" workflow. Also yes, there is still SQLite in the stack (lol) — but only for chat history, not for the ledger.

## Why I ditched SQLite (for transactions)

The biggest problem with v1 wasn't "SQLite bad". SQLite is great.

The problem was: I ended up treating my *expenses* like "application data". Which meant:

- If I wanted to fix a wrong entry, I was back to raw dogging `UPDATE` queries (twss!)
- If I wanted to answer basic questions ("how much did we spend on Swiggy this month?"), I needed SQL + dashboards + my own motivation
- Transfers / credit cards / "paid from this account" got messy fast without proper double-entry

What I actually wanted was: a boring append-only journal that will outlive the app.

Enter: [Plain Text Accounting](https://plaintextaccounting.org/) and `ledger-cli`.

Now Gullak writes transactions like this (this is *literally* what it writes):

```ledger
2026/02/07 Swiggy
    ; gullak:id a1b2c3d4
    ; gullak:source whatsapp
    ; gullak:user 919876543210
    ; Lunch delivery
    Expenses:Food:Delivery  350.00 INR
    Liabilities:CreditCard:Axis  -350.00 INR
```

It's a text file. I can open it in vim. I can `git commit` it if I want. And every transaction is double-entry, so totals and balances actually mean something.

## "LLM-powered" but with seatbelts

LLMs are great at parsing. They are also great at confidently being wrong.

So in v2, the LLM does *not* directly "save an expense". It creates a preview (a pending transaction), and I confirm it.

A very real thing I added: pending transactions are persisted to disk in a `.pending.json` file so restarts don't nuke the state. Because of course the one time you'll need it is when Docker restarts mid-conversation.

When I confirm, Gullak writes to the ledger file and runs `ledger-cli` validation. If the transaction would make the file invalid (unbalanced postings, etc.), it simply refuses to write. Simple and brutal.

## WhatsApp, because that's where my life is

Telegram was fine for v1, but it's not where my life happens.

WhatsApp is where:
- families coordinate
- society groups spam PDFs
- your bank sends OTPs
- your friends decide plans and then cancel

So I built a small WhatsApp bridge using [Baileys](https://github.com/WhiskeySockets/Baileys). It's not a "puppet browser" — it talks the WhatsApp Web protocol over WebSockets.

Architecture is intentionally boring:

- A Node.js + Express bridge receives messages via Baileys
- It persists the WhatsApp session in `/data/whatsapp-session` (so you don't scan QR codes every day)
- It forwards the payload to Gullak at `POST /api/whatsapp/webhook`
- Gullak replies back via the bridge (`/api/sendText`), with typing indicators and all that drama

Also: I run an allowlist. Only my number (and Saumya's / our group) can talk to it. I am not trying to build the next "expense bot" SaaS here.

## The stuff that makes it feel "fast" (without pretending it's magic)

Two tricks that helped a lot:

### 1) Regex patterns for obvious merchants

There's a big list of regex patterns for common Indian merchants (Swiggy, DMart, Netflix, ACT, etc.). So even if the LLM is having a "creative" day, the system has a strong prior.

Example vibe:
- "Swiggy" → `Expenses:Food:Delivery`
- "Netflix" → `Expenses:Entertainment:Streaming`

### 2) Payee memory (stored inside the ledger file)

When I confirm a transaction, Gullak learns a mapping and stores it as a comment in the ledger file:

```ledger
; gullak:payee_map Swiggy=Expenses:Food:Delivery|Liabilities:CreditCard:Axis
```

Next time, it can suggest both the expense account *and* the payment account.

And no, it's not some fancy embedding model. It's `SequenceMatcher` with:
- exact match
- substring match
- fuzzy match (threshold `0.7`)

It's dumb in a good way.

## Receipt OCR (aka: forward the photo, don't type)

This was missing in v1 and honestly it's the feature I use the most when we travel.

You can send a photo/PDF of a receipt (WhatsApp or web UI). Gullak runs it through a vision-capable model (configured separately if you want), extracts merchant/date/amount, and creates pending transactions.

Then I just "confirm" or "edit that" like a normal chat.

## CSV import (for the monthly ritual)

If you're doing PTA seriously, you know the ritual:
download statement → import → categorize → fix duplicates → cry.

Gullak has an `import_csv` tool now:
- upload a CSV (or Excel)
- it creates pending transactions for each row
- it dedupes against what's already in the ledger
- you confirm in bulk

The monthly ritual becomes reconciliation, not data entry (which is what I wanted all along).

## The stack (v2)

I kept it intentionally small:

- Python 3.13 + FastAPI + Pydantic
- LiteLLM for model routing (my default is `openrouter/google/gemini-2.0-flash-001`)
- A tiny web UI: Jinja2 + Tailwind + Alpine.js
- Server-Sent Events (SSE) for streaming responses/previews in the browser
- `ledger-cli` for validation (source of truth stays the ledger file)
- SQLite (`chat_history.db`) for chat threads/history only (yes, I know)

Docker compose runs three services: Gullak + Paisa + WhatsApp bridge, sharing a `/data` volume. Timezone is set to `Asia/Kolkata` because relative dates like "yesterday" should not become an accounting surprise.

## Paisa for reports (because I don't want to build charts)

[Paisa](https://paisa.fyi/) is fantastic. Gullak is good at capture; Paisa is good at telling me "where is the money going".

After every confirmed write, Gullak triggers a Paisa sync, so the dashboard stays updated without me doing anything.

---

Source code: https://github.com/mr-karan/gullak

If you try it and it breaks (it will), feel free to open a GitHub issue or [reach out](/contact/).

Fin!