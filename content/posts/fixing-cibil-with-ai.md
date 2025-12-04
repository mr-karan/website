+++
title = "Fixing a CIBIL Score Disaster with AI"
date = 2025-12-04
type = "post"
description = "How a wrong date of birth merged two credit histories into one, and how I used AI to untangle the mess."
in_search_index = true
[taxonomies]
tags = ["AI", "Finance", "Personal"]
+++

About a month ago, I downloaded my CIBIL report expecting a routine check. Instead, I found loans from lenders I had never interacted with, written-off accounts, overdues from fintechs I had never installed, and even two-wheeler loan enquiries. I don't even ride a bike.

My credit score had collapsed to under 680. I stared at the report trying to understand how this could happen.

## The Root Cause: A Wrong Date of Birth

Buried in my profile section was the problem: my date of birth was wrong. Not a typo, but a completely different year.

Because of this mismatch, CIBIL's system had paired my PAN and mobile number with someone else's DOB, effectively merging two individuals' credit histories into one report. The accounts mapped to me included:

- **Aditya Birla Capital**: Short-term personal loan marked as doubtful/substandard
- **Clix Capital**: A loan marked written-off (₹50,000+)
- **Poonawalla Fincorp**: Personal loans with delayed payments
- **Ring / Kissht**: Unsecured digital loans
- **InCred**: Personal loan I never took
- **Dhani Loans**: BNPL-style loan with unrecognized activity
- **Axio (Capital Float)**: Old consumer loan
- **KrazyBee**: Various short-term loans
- **Transactree**: Small-ticket personal loan
- Multiple enquiries from HDFC, ICICI, IDFC First, Shriram Finance, and others

Some were written-off, others 90+ days overdue, others still active. On paper, I looked like a serial defaulter.

## Using AI to Understand the Problem

I opened ChatGPT and uploaded the entire PDF with a simple prompt: identify everything wrong in this report.

Within minutes, it had mapped every suspicious account, flagged which ones didn't match my history, highlighted the incorrect DOB, and explained why CIBIL systems mis-map accounts when demographic data is inconsistent.

More usefully, it drafted formal dispute letters citing relevant RBI regulations and prepared lender-specific escalations with the right legal language. It felt like having a credit compliance team on demand.

## The Dispute Process

With the AI-drafted communications as a starting point, I sent disputes to CIBIL and direct emails to each lender. The key was being specific: every email included the CIBIL report control number, the exact account identifiers from the report, and references to specific RBI regulations.

For example, when writing to Poonawalla Fincorp about a co-lending arrangement with Kissht, the email included:

> **CIBIL Report details:**
>
> - Control Number: [REDACTED]
> - Downloaded on: [DATE]
> - Where your name appears: "POONAFIN – Personal Loan – Account No. [REDACTED]"
> - Delinquency trail in history: DPD values 35 / 62 / 93 / 124 during [MONTHS]
>
> I reiterate that I have never applied for, signed, or availed any facility from Poonawalla/Kissht. This appears to be erroneous mapping / data contamination.

The emails also cited the relevant regulations explicitly:

> Under Section 45-A(2) of the Credit Information Companies (Regulation) Act 2005 and Para 7.2.2 & 8.1.3 of the RBI Master Directions on Credit Information Companies (2021), please verify this record against your origination/KYC systems. If the record is not verifiable or was created with misused/incorrect KYC, immediately instruct TransUnion CIBIL to delete/correct the entry.

This kind of precise, regulation-backed language gets results. Vague complaints are likely to get ignored or deprioritized. Specific complaints with control numbers, account IDs, and regulatory citations get escalated to teams that can actually fix things.

For co-lending cases (common with fintechs like Kissht, Ring, etc.), I learned to CC both parties and explicitly request a "consolidated correction" so the entry gets fully removed rather than bouncing between two institutions.

When initial responses were slow, I sent reminders that referenced the original complaint number and the 30-day statutory deadline:

> This is a reminder regarding my complaint Ref No. [REDACTED]. The acknowledgement stated that the issue would be resolved by [DATE], yet I have not received any confirmation.
>
> Failure to resolve within the statutory period will leave me with no option but to escalate to the RBI Integrated Ombudsman.

CIBIL started closing disputes. One by one, accounts were removed. Eight fraudulent accounts were purged in the first wave.

But there was a catch: even after the fraudulent accounts were removed, my DOB was still wrong. CIBIL kept closing my DOB correction disputes without actually fixing the underlying data. Their responses were templated and generic, treating it like a lender issue when DOB is actually a CIBIL demographic field that they control directly.

This required escalating to the Nodal Officer with a sharper tone:

> My Date of Birth correction dispute has been closed twice, yet my DOB remains incorrect in every new CIBIL report. This is a CIBIL demographic field — it is not lender-controlled and should have been corrected immediately once KYC was submitted.
>
> Because of this incorrect DOB, my profile was wrongly merged with another individual's data. Although many wrong accounts have been removed, the root cause remains uncorrected — the wrong DOB is still mapped, and therefore the risk of future wrongful linkages still exists.

Only after escalating to the Nodal Officer did the DOB finally get corrected. Once that happened, the system stopped associating the other person's accounts with my profile. It was an algorithmic identity collision, and fixing the DOB resolved it.

## The Outcome

My latest CIBIL report shows the correct date of birth, zero fraudulent loans, no written-off or overdue accounts, and a score back in a healthy range. Only my actual accounts remain.

## What I Learned

Credit bureaus are not infallible. A single incorrect demographic detail (in my case, a mismatched DOB) can cause wrong loan mappings, score drops, false delinquencies, and a complete distortion of your financial identity.

The resolution required documentation, persistence with escalations, and an understanding of RBI regulations. AI made the last part significantly easier. Instead of spending hours researching dispute procedures and drafting formal letters, I could focus on gathering the right documents and following up with the right people.

If you haven't checked your CIBIL report recently, it's worth verifying that your basic details are correct: DOB, PAN, address, mobile, email. One wrong field can create problems that take weeks to untangle.

Fin!
