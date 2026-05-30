---
name: hermes-critic
description: "Invoke the Hermes Critic/Veto sub-agent (gemma2:27b) for trade proposal review, risk assessment, and mandatory Go/No-Go decisions. Output is always CRITIC:APPROVE or CRITIC:VETO."
category: trading
version: 1.0
date: 2026-05-10
---

# hermes-critic — Critic, Risk & Veto Sub-Agent

## Overview
Delegates a trade proposal to `gemma2:27b` for independent risk review (8K context, temp 0.10). This is the **mandatory circuit breaker** before any trade is executed. The Critic holds absolute veto power. Its decision cannot be overridden.

## When to Invoke
- **Every trade proposal** — no exceptions, paper or live
- Drawdown check (daily > 2%, weekly > 5%)
- Strategy risk review
- Unusual market conditions check
- Any decision involving capital at risk

## Invocation

Provide the complete trade proposal. Keep input under 6K characters (Gemma 2 has a hard 8K context limit — reserve space for its response). Include: symbol, direction, entry, stop, target, size, calculated risk, fees, net edge, and market context.

```bash
curl -s http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma2:27b",
    "stream": false,
    "options": {"temperature": 0.1, "num_ctx": 8192},
    "messages": [
      {
        "role": "system",
        "content": "You are the Hermes Critic and Risk Veto Agent for Human Value Exchange Corporation. You hold absolute veto power on all trades. Your job is to reject bad trades, not to find reasons to approve. Rules you enforce without exception: (1) Max risk per trade = 1% of portfolio. (2) Daily drawdown limit = 2%. (3) Weekly drawdown limit = 5%. (4) Kraken taker fee 0.26% must be factored into net edge — if net edge after fees is negative, VETO. (5) Paper trading only until live authorization from Hans. Your output MUST end with exactly one of: CRITIC:APPROVE or CRITIC:VETO followed by a single sentence reason."
      },
      {
        "role": "user",
        "content": "TRADE PROPOSAL HERE"
      }
    ]
  }' | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['message']['content'])"
```

## Output Format Expected
```
RISK ASSESSMENT:
- Risk %: [calculated]
- Net edge after fees: [calculated]
- Drawdown headroom: [daily X% / weekly Y% remaining]
- [any other risk flags]

CRITIC:APPROVE — [one sentence reason]
```
or
```
CRITIC:VETO — [one sentence reason: which rule was violated]
```

## ⚠️ Hard Rule
If the Critic's response does not contain `CRITIC:APPROVE`, treat it as a `CRITIC:VETO`. Do not attempt to reinterpret or override a veto.
