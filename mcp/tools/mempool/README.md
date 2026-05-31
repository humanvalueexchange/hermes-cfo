# Mempool.space MCP Tools

On-chain and Lightning network intelligence for Hermes CFO via the [mempool.space](https://mempool.space) public API.

**No API key required.** All endpoints are public.

---

## Tools

| Tool | API Endpoint | Purpose |
|------|-------------|---------|
| `get_mempool_fees` | `/api/v1/fees/recommended` | Fee rates in sat/vB (fastest / half-hour / hour / economy / minimum) |
| `get_mempool_depth` | `/api/mempool` | Mempool backlog: tx count, vsize (kB), total fees (SAT), top fee bucket |
| `get_block_status` | `/api/blocks/tip/height` + `/api/v1/blocks` | Chain tip height + recent block summary (tx count, size, timestamp) |
| `get_lightning_network_stats` | `/api/v1/lightning/statistics/latest` | Channel count, node count, total capacity, fee rates (ppm) |

---

## Units

- All monetary values are **SAT** — never USD
- Fee rates are **sat/vB** (on-chain) or **ppm** (Lightning)
- Base fees are **msat** (millisatoshi)
- Block/mempool sizes are **kB**

---

## Example Output

### `get_mempool_fees()`
```
Bitcoin Fee Rates — 2026-05-31 21:30 ET
Fastest (next block):  4 sat/vB
Half-hour target:      2 sat/vB
Hour target:           1 sat/vB
Economy (no rush):     1 sat/vB
Minimum:               1 sat/vB
Source: mempool.space public API (live)
```

### `get_mempool_depth()`
```
Mempool Depth — 2026-05-31 21:30 ET
Pending transactions: 53,265
Backlog size:         10,888 kB
Total fees waiting:   4,394,223 SAT
Top fee bucket:       4.41 sat/vB (50,009 transactions)
Source: mempool.space public API (live)
```

### `get_block_status(recent_count=3)`
```
Block Status — 2026-05-31 21:30 ET
Chain tip height: 951,779

Recent blocks:
  #951779 — 2,341 txs | 1,643 kB | 2026-05-31 21:28 UTC
  #951778 — 1,987 txs | 1,402 kB | 2026-05-31 21:15 UTC
  #951777 — 2,105 txs | 1,501 kB | 2026-05-31 21:03 UTC
Source: mempool.space public API (live)
```

### `get_lightning_network_stats()`
```
Lightning Network Stats — 2026-05-31 21:30 ET
Snapshot date:       2026-05-31
Channels:            41,332
Nodes:               17,439
Total capacity:      487,794,772,574 SAT
Avg channel size:    11,801,867 SAT
Median channel size: 2,002,002 SAT
Avg fee rate:        822 ppm
Median fee rate:     100 ppm
Avg base fee:        925 msat
Node visibility:     clearnet 4,674 | tor 8,972 | clearnet+tor 1,783 | unannounced 2,010
Source: mempool.space public API (live, daily snapshot)
```

---

## Error Handling

All tools return a string prefixed with `ERROR:` on failure:
```
ERROR: fee data unavailable — <urllib.error.URLError: ...>
```

---

## Rate Limits

mempool.space public API has generous limits (no authentication required). The client enforces a 5-second timeout and 2 retries on connection errors only (not on 4xx/5xx).
