"""Mempool.space HTTP client — shared by all mempool MCP tools."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE_URL = "https://mempool.space"
TIMEOUT = 5       # seconds — hard limit; target < 3s
MAX_RETRIES = 2


def fetch(path: str) -> dict | list | int:
    """GET {BASE_URL}{path} with timeout + retry on connection errors only.

    Raises RuntimeError on non-200 or exhausted retries.
    """
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "HermesMCP/1.0"})

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
                if resp.status != 200:
                    raise RuntimeError(f"mempool.space {path} returned {resp.status}")
                raw = resp.read().decode()
                # Some endpoints return a plain integer (e.g. /api/blocks/tip/height)
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return int(raw.strip())
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(0.5)
            continue
        except RuntimeError:
            raise

    raise RuntimeError(f"mempool.space {path} unreachable after {MAX_RETRIES + 1} attempts: {last_exc}")
