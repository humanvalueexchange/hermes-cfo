#!/usr/bin/env bash
# Hermes pre_llm_call hook: inject live BTC price + current datetime
cat - >/dev/null  # discard stdin JSON payload

TICKER_URL="https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD"
OHLC_URL="https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1"

# Try Ticker up to 2 times (cold connections can stall on first attempt)
BTC_DATA=""
for attempt in 1 2; do
    BTC_DATA=$(curl -s --max-time 6 "$TICKER_URL" 2>/dev/null)
    if echo "$BTC_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if not d.get('error') else 1)" 2>/dev/null; then
        break
    fi
    BTC_DATA=""
done

# Fallback: use OHLC last close if Ticker unavailable
PRICE_SOURCE="Kraken Ticker"
if [ -z "$BTC_DATA" ]; then
    OHLC_DATA=$(curl -s --max-time 8 "$OHLC_URL" 2>/dev/null)
    if echo "$OHLC_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if not d.get('error') else 1)" 2>/dev/null; then
        BTC_DATA="$OHLC_DATA"
        PRICE_SOURCE="Kraken OHLC"
    fi
fi

if [ -z "$BTC_DATA" ]; then
    NOW=$(date -u "+%Y-%m-%d %H:%M:%S UTC")
    python3 -c "
import json
msg = '--- LIVE CONTEXT (injected at $NOW) ---\nBTC/USD: UNAVAILABLE (Kraken API unreachable — do NOT recall a price from memory)\nCurrent datetime: $NOW\n--- END LIVE CONTEXT ---'
print(json.dumps({'context': msg}))
"
    exit 0
fi

python3 - "$BTC_DATA" "$PRICE_SOURCE" << 'PYEOF'
import sys, json
from datetime import datetime, timezone

try:
    data = json.loads(sys.argv[1])
    source = sys.argv[2]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if source == "Kraken Ticker":
        price = float(data['result']['XXBTZUSD']['c'][0])
    else:
        # OHLC fallback: last close is index 4 of the final candle
        price = float(data['result']['XXBTZUSD'][-1][4])

    context = (
        f"--- LIVE CONTEXT (auto-injected {now}) ---\n"
        f"BTC/USD ({source}, last trade): ${price:,.2f}\n"
        f"Current datetime: {now}\n"
        f"--- END LIVE CONTEXT ---\n"
        f"RULE: Use the price above. Never recall a price from training memory."
    )
    print(json.dumps({"context": context}))
except Exception as e:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    context = f"--- LIVE CONTEXT ---\nBTC/USD: PARSE ERROR ({e}) — do not fabricate a price\nCurrent datetime: {now}\n---"
    print(json.dumps({"context": context}))
PYEOF
