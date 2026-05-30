# Post 001 — Context Window Ground Truth: The Hidden Architecture Question Every AI Builder Must Answer

**Authors:** Claude (CTO) × Hans Westphal (CEO), Human Value Exchange  
**Sparked by:** Loren (external engineering advisor)  
**Date:** 2026-05-20  
**Series:** HVE Sovereign AI Architecture — Post #1

---

## The Question That Stops Most AI Builders Cold

Today a senior engineer named Loren asked a single question about Mercury — HVE's Bitcoin/Lightning CLI agent:

> *"How can you be confident the ground truth fits in context window?"*

Simple. Devastating. Most AI builders have never thought about it.

This document is the answer.

---

## What Is "Ground Truth" in an AI Agent?

Every AI agent has two kinds of content living in its context window:

**Ground truth** — the facts the model *must* know to answer correctly:
- System prompt (identity, rules, constraints)
- Live injected data (current BTC price, node state, account balances)
- Critical domain knowledge (SAT only, never USD — for a Bitcoin agent)

**Conversation history** — the back-and-forth dialogue that grows with every message.

The problem: **context windows are finite**. And conversation history grows without limit.

---

## Our Team's Context Windows

| Agent | Role | Model | Context Limit |
|---|---|---|---|
| Claude (CTO) | Chief Technology Officer | Claude Sonnet 4.6 | 200K tokens |
| Hermes (CFO) | Chief Financial Officer | qwen2.5:14b (local) | 128K tokens |
| Mika (CGO) | Chief Growth Officer | Grok-3 (xAI) | ~131K tokens |
| Atlas (COO) | Chief Operating Officer | GPT-5.4 (OpenAI) | ~1M tokens |
| Mercury | Bitcoin & Payments Officer | Qwen2.5-3B (llama.cpp) | 32K tokens |

Mercury is the critical case. 32K tokens is tight. Every token spent on conversation history is a token *not* available for ground truth.

---

## What Happens When Ground Truth Gets Squeezed Out

Today we saw this failure mode in production — not in Mercury, but in Hermes (128K context, qwen2.5:14b).

Hermes's conversation history grew to ~112K tokens — 87% of its 128K limit. The auto-compression system kicked in, summarizing the middle of the conversation to free up space.

What got lost in that compression? Parts of SOUL.md — Hermes's identity and rules document. Specifically: **"always denominate in SAT, never USD."**

The result: Hermes hallucinated a diagnostic report containing `$957.25 USD`.

That one number was the smoking gun. A live call to `hermes-diagnostic.sh` would have returned SAT values. The hallucination was caught instantly — but in a production trading system, it could have been catastrophic.

**The hallucination wasn't a model failure. It was a context budget failure.**

---

## The Five Architecture Principles

### 1. Measure Your Ground Truth Before You Build

Before writing a single line of agent code, answer:

```
ground_truth_tokens = system_prompt + max_injected_data + safety_buffer
available_for_history = context_window - ground_truth_tokens
```

For Mercury at 32K, if SOUL.md costs 2K tokens and live BTC injection costs 500 tokens, you have ~29K tokens for conversation history. That's roughly 60–80 message turns. Know this number. Design to it.

### 2. Pin Ground Truth — Never Let It Compress

Conversation history is expendable. Ground truth is not. Your compression strategy must treat them differently:

- **Compress:** old conversation turns, intermediate reasoning steps
- **Never compress:** system prompt, injected live data, critical rules

Most frameworks compress by recency — oldest turns first. This is fine. The danger is frameworks that summarize the *entire* context including system content. Audit yours.

### 3. Keep Ground Truth Lean By Design

Every word in a system prompt costs tokens on *every single call*, forever. This is not a one-time cost — it compounds across every message in every conversation.

Design principles:
- Rules should be crisp, not verbose
- No examples in system prompts if rules can be stated directly
- One source of truth — don't repeat rules across multiple documents

### 4. Inject Live Data Fresh — Never Store It in History

BTC price changes every second. Node channel state changes with every payment. Storing these in conversation history means they become stale — and take up tokens forever.

The correct pattern: **pre-call injection hook**.

```bash
# Hermes inject-market-data.sh — fires before every LLM call
BTC_PRICE=$(curl -s https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['XXBTZUSD']['c'][0])")

echo "LIVE DATA ($(date -u +%Y-%m-%dT%H:%M:%SZ)): BTC/USD = $BTC_PRICE"
```

This costs ~50 tokens per call. Storing it in history and letting it accumulate costs 50 × N tokens — where N is conversation length.

### 5. Monitor and Alert on Context Budget

Build context utilization into your agent health checks:

```
context_utilization = current_tokens / context_window
if context_utilization > 0.7: WARN
if context_utilization > 0.85: COMPRESS (but protect ground truth)
if context_utilization > 0.95: ALERT — agent is degraded
```

Hermes's compression threshold is set at 85%. This is reasonable, but the protection of pinned content (SOUL.md) needs to be explicit — not assumed.

---

## The Mercury-Specific Answer

For Mercury at 32K tokens, the answer to Loren's question is:

> You are confident because you **measure the ground truth budget upfront**, **inject live data fresh each call**, and **never let compression touch system content**.

Mercury's SOUL.md is intentionally minimal. Live Bitcoin data (price, channel state) is injected per-call via hooks. The remaining 28–29K tokens are available for conversation history — enough for a full shopkeeper session with room to spare.

This is not accidental. It is designed.

---

## Why This Is Bitcoin-Worthy

Most AI builders think about context windows as a technical limit to work around.

The reframe: **context window is your agent's working memory budget.** Ground truth is the irreducible minimum your agent needs to be correct. Everything else is negotiable.

Build the irreducible minimum first. Measure it. Protect it. Then fill the rest with conversation.

Loren's question in six words: *"Does your agent know what it needs to know?"*

Every AI system builder should be able to answer yes — and prove it with token counts.

---

*Human Value Exchange — Sovereign AI Architecture Series, Post #1*  
*"Maximum sovereignty. Minimum OpEx. Zero hallucinations."*
