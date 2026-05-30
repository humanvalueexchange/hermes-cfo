✅ Hermes hc alias LOADED
#!/usr/bin/env bash
# Hermes Self-Diagnostic Script
# Run this FIRST when asked for a diagnostic report. Never fabricate output.
# All reported financial values are SAT-only. Never print USD conversions.

set -euo pipefail

echo "=== HERMES SELF-DIAGNOSTIC ==="
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M UTC')"
echo ""

# ── BTC Price Feed Health (no USD output) ─────────────────────────────────────
echo "--- BTC PRICE FEED (health only) ---"
curl -s --max-time 6 "https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
pair = d['result']['XXBTZUSD']['c'][0]
if pair:
    print('Kraken ticker: REACHABLE')
else:
    print('Kraken ticker: UNAVAILABLE')
" || echo "Kraken ticker: UNAVAILABLE (Kraken API timeout)"
echo ""

# ── Bitcoin Node + Lightning (SSH to Mercury Pi) ─────────────────────────────
echo "--- BITCOIN NODE (via Mercury Pi) ---"
ssh -o ConnectTimeout=8 mercury \
  "sudo -u lnd lncli --lnddir=/var/lib/lnd getinfo 2>/dev/null" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Block height   :', d.get('block_height', 'UNKNOWN'))
print('Synced to chain:', d.get('synced_to_chain', 'UNKNOWN'))
print('Synced to graph:', d.get('synced_to_graph', 'UNKNOWN'))
print('Alias          :', d.get('alias', 'UNKNOWN'))
" 2>/dev/null || echo "Bitcoin node: UNAVAILABLE (SSH to Mercury failed)"
echo ""

# ── Lightning Channels ────────────────────────────────────────────────────────
echo "--- LIGHTNING CHANNELS (SAT — integers only) ---"
ssh -o ConnectTimeout=8 mercury \
  "sudo -u lnd lncli --lnddir=/var/lib/lnd listchannels 2>/dev/null" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
chs = d.get('channels', [])
print(f'Active channels: {len(chs)}')
total_local = 0
total_remote = 0
for i, c in enumerate(chs, 1):
    alias = c.get('remote_alias') or c.get('chan_id', 'unknown')
    local  = int(c.get('local_balance',  0))
    remote = int(c.get('remote_balance', 0))
    total_local  += local
    total_remote += remote
    print(f'  Channel {i}: {alias}')
    print(f'    Local  : {local:,} SAT')
    print(f'    Remote : {remote:,} SAT')
print(f'Total local    : {total_local:,} SAT')
print(f'Total remote   : {total_remote:,} SAT')
" 2>/dev/null || echo "Lightning channels: UNAVAILABLE"
echo ""

# ── Channel Balance Summary ───────────────────────────────────────────────────
echo "--- CHANNEL BALANCE SUMMARY (SAT) ---"
ssh -o ConnectTimeout=8 mercury \
  "sudo -u lnd lncli --lnddir=/var/lib/lnd channelbalance 2>/dev/null" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
local  = int(d.get('local_balance',  {}).get('sat', 0))
remote = int(d.get('remote_balance', {}).get('sat', 0))
print(f'Local balance  : {local:,} SAT')
print(f'Remote balance : {remote:,} SAT')
" 2>/dev/null || echo "Channel balance: UNAVAILABLE"
echo ""

# ── Recent Payments (SAT only) ────────────────────────────────────────────────
echo "--- RECENT PAYMENTS (SAT only) ---"
ssh -o ConnectTimeout=8 mercury \
  "sudo -u lnd lncli --lnddir=/var/lib/lnd listpayments --max_payments=3 2>/dev/null" \
  | python3 -c "
import sys, json, datetime
d = json.load(sys.stdin)
pmts = d.get('payments', [])
if not pmts:
    print('No payments on record')
else:
    for p in pmts:
        ts = int(p.get('creation_date', 0))
        dt = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M UTC') if ts else 'unknown'
        print(f\"{int(p.get('value_sat', 0)):,} SAT | {p.get('status','?')} | {dt}\")
" 2>/dev/null || echo "Payments: UNAVAILABLE"
echo ""

# ── Ollama Models on DGX Spark ────────────────────────────────────────────────
echo "--- OLLAMA MODELS (DGX Spark) ---"
curl -s --max-time 6 http://localhost:11434/api/tags 2>/dev/null \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
models = d.get('models', [])
print(f'Models loaded: {len(models)}')
for m in models:
    size_gb = m.get('size', 0) / 1e9
    print(f\"  - {m['name']} ({size_gb:.1f} GB)\")
" || echo "Ollama: UNAVAILABLE"
echo ""

echo "=== END DIAGNOSTIC ==="
