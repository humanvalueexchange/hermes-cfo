---
name: bitcoin-intelligence
description: "Live BTC spot, fee, mempool, block, and Lightning intelligence for Hermes. Uses Kraken spot and mempool.space-backed MCP tools."
category: hve
version: 1.0
date: 2026-05-30
---

# bitcoin-intelligence — BTC Spot, On-Chain & Lightning

## When to Invoke
- Live BTC spot price
- On-chain fee estimation or channel open/close planning
- Mempool congestion, fee-bucket pressure, or backlog size
- Block cadence, chain-tip status, or recent block summaries
- Lightning network health, capacity, fee-rate, or node-count questions

## Required Calls

| Need | Must use | Output rule |
|---|---|---|
| BTC spot price | Kraken curl command below | Show exact result; never approximate |
| Fee estimation | `get_mempool_fees` | sat/vB only |
| Mempool congestion | `get_mempool_depth` | SAT / sat-vB only |
| Chain tip / blocks | `get_block_status` | recent block timestamps stay UTC |
| Lightning network stats | `get_lightning_network_stats` | SAT / ppm / msat only |

## BTC Spot Command

```bash
curl -s "https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD" | python3 -c "import sys,json; d=json.load(sys.stdin); print('BTC/USD:', d['result']['XXBTZUSD']['c'][0])"
```

If the command fails, say: `I cannot fetch a live price — Kraken unreachable.`

## Non-Negotiables
- Never describe a tool call instead of making it.
- Never fabricate price, fee, mempool, block, or Lightning data.
- `get_block_status(recent_count)` is capped at 15 blocks.
- Use SAT, sat/vB, ppm, and msat only. No USD conversions for on-chain or Lightning outputs.
- If the tool or Kraken command fails, say it is unavailable and stop.
