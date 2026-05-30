#!/usr/bin/env python3
"""
btc_price.py — Live BTC/USDT price fetcher for Hermes CFO

Queries Binance public API (no key needed) for current BTC/USDT price.
Falls back to CoinGecko if Binance is unreachable.

Usage:
    python3 btc_price.py                      # current price
    python3 btc_price.py --ohlcv 1h           # last closed 1h candle
    python3 btc_price.py --ohlcv 1d           # last closed daily candle

Output (JSON):
    {"price": 82210.5, "source": "binance", "pair": "BTC/USDT", "ts": "2026-05-10T21:07:00Z"}
"""

import sys
import json
import argparse
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
BINANCE_KLINES  = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={tf}&limit=2"
COINGECKO       = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

TF_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "1d": "1d",
}


def fetch(url: str, timeout: int = 8) -> dict | list:
    req = Request(url, headers={"User-Agent": "Hermes-CFO/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_price() -> dict:
    # Try Binance first
    try:
        data = fetch(BINANCE_TICKER)
        price = float(data["price"])
        return {
            "price": price,
            "price_sats_per_dollar": round(1e8 / price, 2),
            "source": "binance",
            "pair": "BTC/USDT",
            "ts": now_utc(),
        }
    except (URLError, KeyError, ValueError):
        pass

    # Fallback: CoinGecko
    try:
        data = fetch(COINGECKO)
        price = float(data["bitcoin"]["usd"])
        return {
            "price": price,
            "price_sats_per_dollar": round(1e8 / price, 2),
            "source": "coingecko",
            "pair": "BTC/USD",
            "ts": now_utc(),
        }
    except (URLError, KeyError, ValueError) as e:
        return {"error": f"All price sources failed: {e}", "ts": now_utc()}


def get_ohlcv(tf: str) -> dict:
    if tf not in TF_MAP:
        return {"error": f"Unknown timeframe '{tf}'. Use: {list(TF_MAP)}"}

    try:
        klines = fetch(BINANCE_KLINES.format(tf=TF_MAP[tf]))
        # klines[-2] = last CLOSED candle; klines[-1] = current (open) candle
        k = klines[-2]
        return {
            "timeframe": tf,
            "open_time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "close_time": datetime.fromtimestamp(k[6] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open":   float(k[1]),
            "high":   float(k[2]),
            "low":    float(k[3]),
            "close":  float(k[4]),
            "volume": float(k[5]),
            "source": "binance",
            "pair":   "BTC/USDT",
            "ts":     now_utc(),
        }
    except (URLError, IndexError, ValueError) as e:
        return {"error": f"OHLCV fetch failed: {e}", "ts": now_utc()}


def main():
    parser = argparse.ArgumentParser(description="Live BTC price fetcher for Hermes CFO")
    parser.add_argument(
        "--ohlcv",
        metavar="TIMEFRAME",
        help="Return last closed OHLCV candle (e.g. 1m 5m 15m 1h 4h 1d)",
    )
    args = parser.parse_args()

    if args.ohlcv:
        result = get_ohlcv(args.ohlcv)
    else:
        result = get_price()

    print(json.dumps(result, indent=2))
    sys.exit(0 if "error" not in result else 1)


if __name__ == "__main__":
    main()
