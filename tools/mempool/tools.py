from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from tools.mempool.client import fetch

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def _now_et() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d %H:%M ET")


def _format_rate(value: object) -> str:
    rate = float(value)
    if rate.is_integer():
        return str(int(rate))
    return f"{rate:.2f}".rstrip("0").rstrip(".")


def _to_int(value: object) -> int:
    return int(float(value))


def _utc_from_epoch(value: object) -> str:
    return datetime.fromtimestamp(_to_int(value), UTC).strftime("%Y-%m-%d %H:%M UTC")


def _snapshot_date(value: object) -> str:
    if not value:
        return "unknown"
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()


def get_mempool_fees() -> str:
    """Return live Bitcoin fee recommendations from mempool.space."""
    try:
        data = fetch("/api/v1/fees/recommended")
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: fee data unavailable — {exc}"

    return "\n".join(
        [
            f"Bitcoin Fee Rates — {_now_et()}",
            f"Fastest (next block):  {_format_rate(data['fastestFee'])} sat/vB",
            f"Half-hour target:      {_format_rate(data['halfHourFee'])} sat/vB",
            f"Hour target:           {_format_rate(data['hourFee'])} sat/vB",
            f"Economy (no rush):     {_format_rate(data['economyFee'])} sat/vB",
            f"Minimum:               {_format_rate(data['minimumFee'])} sat/vB",
            "Source:                mempool.space public API (live)",
        ]
    )


def get_mempool_depth() -> str:
    """Return live mempool backlog depth and fee-bucket summary."""
    try:
        data = fetch("/api/mempool")
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: mempool data unavailable — {exc}"

    lines = [
        f"Mempool Depth — {_now_et()}",
        f"Pending transactions: {data['count']:,}",
        f"Backlog size:         {_to_int(data['vsize']) // 1000:,} kB",
        f"Total fees waiting:   {_to_int(data['total_fee']):,} SAT",
    ]

    fee_histogram = data.get("fee_histogram") or []
    if fee_histogram:
        top_rate, top_count = fee_histogram[0]
        lines.append(
            f"Top fee bucket:       {_format_rate(top_rate)} sat/vB ({_to_int(top_count):,} transactions)"
        )

    lines.append("Source:               mempool.space public API (live)")
    return "\n".join(lines)


def get_block_status(recent_count: int = 3) -> str:
    """Return chain-tip height and a summary of recent blocks."""
    safe_count = max(1, min(int(recent_count), 15))

    try:
        tip_height = fetch("/api/blocks/tip/height")
        blocks = fetch("/api/v1/blocks")
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: block data unavailable — {exc}"

    lines = [
        f"Block Status — {_now_et()}",
        f"Chain tip height: {_to_int(tip_height):,}",
        "",
        "Recent blocks:",
    ]

    for block in blocks[:safe_count]:
        lines.append(
            "  "
            f"#{_to_int(block['height']):,} — {_to_int(block['tx_count']):,} txs"
            f" | {_to_int(block['size']) // 1000:,} kB"
            f" | {_utc_from_epoch(block['timestamp'])}"
        )

    lines.append("Source: mempool.space public API (live)")
    return "\n".join(lines)


def get_lightning_network_stats() -> str:
    """Return the latest Lightning network health snapshot."""
    try:
        data = fetch("/api/v1/lightning/statistics/latest")
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: Lightning stats unavailable — {exc}"

    latest = data["latest"] if isinstance(data, dict) and "latest" in data else data

    return "\n".join(
        [
            f"Lightning Network Stats — {_now_et()}",
            f"Snapshot date:       {_snapshot_date(latest.get('added'))}",
            f"Channels:            {_to_int(latest['channel_count']):,}",
            f"Nodes:               {_to_int(latest['node_count']):,}",
            f"Total capacity:      {_to_int(latest['total_capacity']):,} SAT",
            f"Avg channel size:    {_to_int(latest['avg_capacity']):,} SAT",
            f"Median channel size: {_to_int(latest['med_capacity']):,} SAT",
            f"Avg fee rate:        {_to_int(latest['avg_fee_rate']):,} ppm",
            f"Median fee rate:     {_to_int(latest['med_fee_rate']):,} ppm",
            f"Avg base fee:        {_to_int(latest['avg_base_fee_mtokens']):,} msat",
            "Node visibility:     "
            f"clearnet {_to_int(latest['clearnet_nodes']):,}"
            f" | tor {_to_int(latest['tor_nodes']):,}"
            f" | clearnet+tor {_to_int(latest['clearnet_tor_nodes']):,}"
            f" | unannounced {_to_int(latest['unannounced_nodes']):,}",
            "Source:              mempool.space public API (live, daily snapshot)",
        ]
    )
