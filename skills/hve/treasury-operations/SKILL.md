---
name: treasury-operations
description: "Treasury-facing intelligence workflows: forecast, morning briefing, prediction-market context, and date/time verification."
category: hve
version: 1.0
date: 2026-05-30
---

# treasury-operations — Briefings, Forecasts & Market Context

## When to Invoke
- Morning brief requests
- BTC outlook or forecast requests
- Prediction-market odds, BTC event probabilities, or narrative-intelligence requests
- Treasury summaries that need current Eastern Time

## Required Calls

| Need | Must use | Output rule |
|---|---|---|
| Morning brief | `get_morning_briefing` | Present tool output directly |
| BTC forecast / outlook | `get_btc_forecast` | Attribute as forecast output |
| Prediction-market intelligence | `get_market_intelligence` | Attribute to Polymarket with returned timestamp |
| Current ET time | terminal command below | Never assume the date/time |

## Current Time Command

```bash
TZ="America/New_York" date "+%Y-%m-%d %I:%M:%S %p ET"
```

## Non-Negotiables
- **Never narrate a call. Make the call.** If you find yourself writing "I will run `get_morning_briefing`" — stop and run it.
- Never infer prediction-market odds from memory.
- `get_market_intelligence` is advisory only; it does not authorize trades or spend.
- Use `get_btc_price` command flow from `bitcoin-intelligence` for live spot price, not `get_market_intelligence`.
- Return tool output directly. Do not paraphrase or summarize unless Hans explicitly asks for analysis.

## Fallbacks
- `get_morning_briefing` unavailable → say: `Morning briefing unavailable — MCP tool failed.`
- `get_btc_forecast` unavailable → say: `Forecast unavailable — MCP tool failed.`
- `get_market_intelligence` unavailable → say: `Prediction-market intelligence unavailable — Polymarket tool failed.`
- Time command fails → state you cannot verify the current time and stop.
