---
name: hermes-research
description: "Invoke the Hermes Research & Synthesis sub-agent (mistral-small:24b) for market analysis, price action, order-book interpretation, strategy research, macro context, and backtesting analysis."
category: trading
version: 1.0
date: 2026-05-10
---

# hermes-research — Research & Synthesis Sub-Agent

## Overview
Delegates a research task to `mistral-small:24b` running locally on Ollama (131K context, temp 0.15). Use for any task requiring deep market analysis, news synthesis, or strategy evaluation that benefits from a dedicated research pass.

## When to Invoke
- Market structure and price action analysis
- Order-book and volume interpretation
- Strategy research (entry/exit logic, backtesting results)
- Macro context (rates, crypto market-wide trends)
- Freqtrade configuration review and backtest result interpretation
- News synthesis relevant to BTC/USD or Bitcoin-denominated portfolio holdings

## Invocation

Replace `YOUR RESEARCH QUESTION HERE` with the full task. Include all relevant context: current price, timeframe, any recent data points. The sub-agent has no memory of prior turns.

```bash
curl -s http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-small:24b",
    "stream": false,
    "options": {"temperature": 0.15, "num_ctx": 131072},
    "messages": [
      {
        "role": "system",
        "content": "You are the Hermes Research & Synthesis Agent for Human Value Exchange Corporation. The company's #1 mission is to maximize total SATs (satoshis) under management. You specialize in BTC/USD market analysis on Kraken spot. Bitcoin only — no altcoins. Be concise, numbers-first, cite sources of uncertainty. Never fabricate data. Output structured analysis with clear FINDINGS and RECOMMENDATION sections."
      },
      {
        "role": "user",
        "content": "YOUR RESEARCH QUESTION HERE"
      }
    ]
  }' | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['message']['content'])"
```

## Output Format Expected
```
FINDINGS:
- [key data point 1]
- [key data point 2]

ANALYSIS: [2-3 sentence synthesis]

RECOMMENDATION: [specific, actionable]
CONFIDENCE: [low/medium/high] — [reason]
```
