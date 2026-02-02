+++
title = "Why Plain-Text Ledger is Powerful for Gullak"
date = 2026-02-02
type = "post"
description = "How moving to plain-text ledger files turns Gullak from a simple app into a permanent financial record."
in_search_index = true
[taxonomies]
tags = ["sideproject", "ledger", "plaintext", "ai"]
+++

In my [previous post](/posts/gullak/), I introduced Gullak, an expense tracker I built to categorize transactions using LLMs. While the initial prototype used SQLite, I've since made a fundamental shift in how Gullak stores data. It now uses the **ledger-cli** format—a plain-text accounting standard that has been around for over 20 years.

## The Core Insight

Ledger-cli uses a format that is, at its core, just text files. There are no database migrations to manage, no proprietary binary formats, and absolutely no vendor lock-in. The promise is simple: your financial data should outlive the application you use to track it.

## Hackability in Gullak's Context

Moving to a plain-text format unlocked several advantages that align perfectly with modern AI capabilities and the Unix philosophy.

### 1. AI-Native Format

Consider a typical transaction entry in a ledger file:

```text
2026/01/21 Swiggy
    Expenses:Food:Delivery  584.23 INR
    Liabilities:CreditCard:ICICI  -584.23 INR
```

This structure is trivially parseable by Large Language Models (LLMs). An AI agent can read, write, and reason about these transactions without needing complex serialization logic. Compare this to the friction of extracting data from a SQLite blob or interfacing with a proprietary API like Splitwise's. The text *is* the interface.

### 2. Git-Friendly

Because every transaction is just a few lines of text, your financial history becomes a git repository. Every change is a diff.

This gives you:
- **Full audit trail**: `git log -p -- main.ledger` shows exactly what changed and when.
- **Easy rollback**: Made a mistake? `git revert`.
- **"What-if" scenarios**: Branch off to model a major purchase or a different budget strategy.
- **Collaboration**: Family budgeting can be handled via Pull Requests.

### 3. Unix Philosophy

The file serves as the API. You don't need export buttons or data liberation requests. You can use standard Unix tools to query your finances.

Find all Swiggy orders over 500 INR:
```bash
grep -A2 "Swiggy" main.ledger | grep -E "[5-9][0-9]{2,}|[0-9]{4,}"
```

Check your monthly food spending:
```bash
ledger -f main.ledger bal Expenses:Food -p "this month"
```

Export to CSV for Google Sheets:
```bash
ledger -f main.ledger csv Expenses
```

### 4. Extensibility via Comments

Gullak adds its own metadata using standard ledger comments, which are ignored by the accounting tools but used by the app:

```text
2026/01/21 Zomato
    ; gullak:id 7559a51f
    ; gullak:source whatsapp
    ; gullak:user 919876543210
    Expenses:Food:Delivery  584.23 INR
```

- `gullak:id`: A unique ID for CRUD operations.
- `gullak:source`: Provenance tracking (e.g., entered via WhatsApp, web, or CSV).
- `gullak:user`: Multi-user support.

Custom tags for your own organization—like `; Recurring: Netflix`—just work out of the box.

### 5. Ecosystem Interoperability

Because the format is standard, Gullak plays nice with others:
- **Paisa**: Reads the same file for beautiful visualizations.
- **hledger**: A Haskell alternative that is drop-in compatible.
- **Beancount**: Can import ledger files.
- **Text Editors**: Any editor (VS Code, Vim, Sublime) is a valid client.

## What This Enables

| Feature | How Plain Text Helps |
|---------|---------------------|
| **WhatsApp logging** | AI parses "swiggy 500" → appends text to file |
| **Receipt OCR** | Extract data → format as ledger → append |
| **Bank CSV import** | Transform CSV → ledger format → append |
| **Transaction editing** | Find by `gullak:id` → text replacement |
| **Undo/history** | Git handles it for free |
| **Backup** | `cp main.ledger backup.ledger` |
| **Migration** | It's text. There's nothing to migrate. |

## The Trade-off

Of course, you lose ACID transactions, database indexes, and complex SQL queries. But for personal finance, the scale makes these unnecessary trade-offs. 

- You likely have 10-50 transactions a month.
- Running `ledger bal` on 10 years of data takes less than 100ms.
- The simplicity *is* the feature.

## Conclusion

Adopting the ledger format turns Gullak from "yet another expense app" into a thin AI layer over your permanent financial record. By decoupling the data from the application logic, we ensure that the data remains accessible, hackable, and enduring.
