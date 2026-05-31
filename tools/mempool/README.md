# Mempool.space tools

Read-only Bitcoin on-chain and Lightning intelligence for the Hermes MCP server.

## Tools

1. `get_mempool_fees` — recommended fee tiers from `/api/v1/fees/recommended`
2. `get_mempool_depth` — backlog size and top fee bucket from `/api/mempool`
3. `get_block_status` — chain tip and recent blocks from `/api/blocks/tip/height` + `/api/v1/blocks`
4. `get_lightning_network_stats` — daily Lightning snapshot from `/api/v1/lightning/statistics/latest`

## Design rules

- Public mempool.space API only
- `urllib.request` only; no new dependencies
- 5 second timeout, 2 retries on connection errors only
- SAT / sat-vB / ppm / msat output only — never USD
- String returns with `ERROR:` prefix on failure
