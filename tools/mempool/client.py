from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

BASE_URL = "https://mempool.space"
TIMEOUT = 5
MAX_RETRIES = 2
USER_AGENT = "HermesMempool/1.0"


def fetch(path: str) -> dict | int | list:
    """Fetch and decode JSON from the mempool.space public API."""
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"User-Agent": USER_AGENT},
    )
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"mempool.space {path} returned {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            last_error = exc
            if attempt == MAX_RETRIES:
                break

    raise RuntimeError(f"mempool.space {path} unavailable — {last_error}") from last_error
