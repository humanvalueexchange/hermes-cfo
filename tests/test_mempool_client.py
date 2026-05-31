from __future__ import annotations

import json
import sys
import urllib.error
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.mempool import client


class _FakeResponse:
    def __init__(self, payload: object):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class MempoolClientTests(unittest.TestCase):
    def test_fetch_retries_connection_errors(self) -> None:
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=[urllib.error.URLError("temporary failure"), _FakeResponse({"ok": True})],
        ) as urlopen:
            self.assertEqual(client.fetch("/api/example"), {"ok": True})
            self.assertEqual(urlopen.call_count, 2)

    def test_fetch_does_not_retry_http_errors(self) -> None:
        error = urllib.error.HTTPError(
            url="https://mempool.space/api/example",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )
        with mock.patch("urllib.request.urlopen", side_effect=error) as urlopen:
            with self.assertRaisesRegex(RuntimeError, "returned 503"):
                client.fetch("/api/example")
            self.assertEqual(urlopen.call_count, 1)


if __name__ == "__main__":
    unittest.main()
