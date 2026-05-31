from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.mempool import tools


class MempoolToolTests(unittest.TestCase):
    def test_get_mempool_fees_formats_all_tiers(self) -> None:
        payload = {
            "fastestFee": 2,
            "halfHourFee": 1,
            "hourFee": 1,
            "economyFee": 1,
            "minimumFee": 1,
        }
        with mock.patch("tools.mempool.tools.fetch", return_value=payload), mock.patch(
            "tools.mempool.tools._now_et", return_value="2026-05-31 21:30 ET"
        ):
            result = tools.get_mempool_fees()

        self.assertIn("Bitcoin Fee Rates — 2026-05-31 21:30 ET", result)
        self.assertIn("Fastest (next block):  2 sat/vB", result)
        self.assertIn("Half-hour target:      1 sat/vB", result)
        self.assertIn("Source:                mempool.space public API (live)", result)

    def test_get_mempool_depth_omits_top_bucket_when_histogram_empty(self) -> None:
        payload = {"count": 53265, "vsize": 10888842, "total_fee": 4394223, "fee_histogram": []}
        with mock.patch("tools.mempool.tools.fetch", return_value=payload), mock.patch(
            "tools.mempool.tools._now_et", return_value="2026-05-31 21:30 ET"
        ):
            result = tools.get_mempool_depth()

        self.assertIn("Pending transactions: 53,265", result)
        self.assertIn("Backlog size:         10,888 kB", result)
        self.assertIn("Total fees waiting:   4,394,223 SAT", result)
        self.assertNotIn("Top fee bucket:", result)
        self.assertNotIn("USD", result)
        self.assertNotIn("$", result)

    def test_get_block_status_clamps_recent_count_to_fifteen(self) -> None:
        blocks = [
            {
                "height": 951779 - index,
                "tx_count": 2000 + index,
                "size": 1500000 + (index * 1000),
                "timestamp": 1748748480 - (index * 600),
            }
            for index in range(20)
        ]
        with mock.patch("tools.mempool.tools.fetch", side_effect=[951779, blocks]), mock.patch(
            "tools.mempool.tools._now_et", return_value="2026-05-31 21:30 ET"
        ):
            result = tools.get_block_status(recent_count=99)

        self.assertIn("Chain tip height: 951,779", result)
        self.assertEqual(sum(1 for line in result.splitlines() if line.startswith("  #")), 15)
        self.assertIn("2025", result.replace("UTC", "UTC"))  # ensures timestamp formatting path ran

    def test_get_lightning_network_stats_formats_snapshot(self) -> None:
        payload = {
            "latest": {
                "channel_count": 41332,
                "node_count": 17439,
                "total_capacity": 487794772574,
                "tor_nodes": 8972,
                "clearnet_nodes": 4674,
                "unannounced_nodes": 2010,
                "avg_capacity": 11801867,
                "avg_fee_rate": 822,
                "avg_base_fee_mtokens": 925,
                "med_capacity": 2002002,
                "med_fee_rate": 100,
                "clearnet_tor_nodes": 1783,
                "added": "2026-05-31T00:00:00.000Z",
            }
        }
        with mock.patch("tools.mempool.tools.fetch", return_value=payload), mock.patch(
            "tools.mempool.tools._now_et", return_value="2026-05-31 21:30 ET"
        ):
            result = tools.get_lightning_network_stats()

        self.assertIn("Snapshot date:       2026-05-31", result)
        self.assertIn("Total capacity:      487,794,772,574 SAT", result)
        self.assertIn("Avg fee rate:        822 ppm", result)
        self.assertIn("Avg base fee:        925 msat", result)
        self.assertIn("clearnet+tor 1,783", result)
        self.assertNotIn("USD", result)
        self.assertNotIn("$", result)

    def test_tools_return_error_prefix_on_failures(self) -> None:
        cases = [
            (tools.get_mempool_fees, "ERROR: fee data unavailable"),
            (tools.get_mempool_depth, "ERROR: mempool data unavailable"),
            (tools.get_block_status, "ERROR: block data unavailable"),
            (tools.get_lightning_network_stats, "ERROR: Lightning stats unavailable"),
        ]

        for func, prefix in cases:
            with self.subTest(func=func.__name__), mock.patch(
                "tools.mempool.tools.fetch", side_effect=RuntimeError("boom")
            ):
                self.assertEqual(func().split(" — ", 1)[0], prefix)


if __name__ == "__main__":
    unittest.main()
