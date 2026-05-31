"""Mempool.space MCP tools — On-Chain & Mempool Intelligence.

Four read-only tools exposing live Bitcoin network data:
  get_mempool_fees           — recommended fee rates in sat/vB
  get_mempool_depth          — mempool backlog size and fee distribution
  get_block_status           — chain tip height and recent block summary
  get_lightning_network_stats — Lightning channel/node/capacity snapshot

All monetary values are reported in SAT. USD is never used.
Source: mempool.space public API (no key required).
"""
from __future__ import annotations

from datetime import datetime, timezone

from tools.mempool.client import fetch


def get_mempool_fees() -> str:
    """Get live Bitcoin fee recommendations in sat/vB.

    Returns fastest (next-block), half-hour, hour, economy, and minimum
    fee tiers from the mempool.space public API. Use this to inform
    Lightning channel management and on-chain treasury operations.
    """
    try:
        data = fetch("/api/v1/fees/recommended")
    except Exception as exc:
        return f"ERROR: fee data unavailable — {exc}"

    now = datetime.now().strftime("%Y-%m-%d %H:%M ET")
    return (
        f"Bitcoin Fee Rates — {now}\n"
        f"Fastest (next block):  {data['fastestFee']} sat/vB\n"
        f"Half-hour target:      {data['halfHourFee']} sat/vB\n"
        f"Hour target:           {data['hourFee']} sat/vB\n"
        f"Economy (no rush):     {data['economyFee']} sat/vB\n"
        f"Minimum:               {data['minimumFee']} sat/vB\n"
        f"Source: mempool.space public API (live)"
    )


def get_mempool_depth() -> str:
    """Get current mempool backlog size, transaction count, and fee distribution.

    Reports pending transaction count, backlog in kB, total fees waiting
    in SAT, and the top (highest-rate) fee bucket. Use this to assess
    network congestion before scheduling on-chain operations.
    """
    try:
        data = fetch("/api/mempool")
    except Exception as exc:
        return f"ERROR: mempool data unavailable — {exc}"

    now = datetime.now().strftime("%Y-%m-%d %H:%M ET")
    count = data.get("count", 0)
    vsize_kb = data.get("vsize", 0) // 1000
    total_fee = data.get("total_fee", 0)
    histogram = data.get("fee_histogram", [])

    lines = [
        f"Mempool Depth — {now}",
        f"Pending transactions: {count:,}",
        f"Backlog size:         {vsize_kb:,} kB",
        f"Total fees waiting:   {total_fee:,} SAT",
    ]
    if histogram:
        top_rate, top_count = histogram[0][0], histogram[0][1]
        lines.append(f"Top fee bucket:       {top_rate:.2f} sat/vB ({int(top_count):,} transactions)")
    lines.append("Source: mempool.space public API (live)")

    return "\n".join(lines)


def get_block_status(recent_count: int = 3) -> str:
    """Get current Bitcoin chain tip height and a summary of recent blocks.

    Args:
        recent_count: Number of recent blocks to summarise (default 3, max 15).

    Returns current tip height and per-block tx count, size, and timestamp.
    Use this to confirm node sync state and monitor block pace.
    """
    try:
        tip_height = fetch("/api/blocks/tip/height")
        blocks = fetch("/api/v1/blocks")
    except Exception as exc:
        return f"ERROR: block data unavailable — {exc}"

    recent_count = min(int(recent_count), 15)
    now = datetime.now().strftime("%Y-%m-%d %H:%M ET")

    lines = [
        f"Block Status — {now}",
        f"Chain tip height: {int(tip_height):,}",
        "",
        "Recent blocks:",
    ]
    for block in blocks[:recent_count]:
        height = block.get("height", "?")
        tx_count = block.get("tx_count", 0)
        size_kb = block.get("size", 0) // 1000
        ts = datetime.fromtimestamp(block.get("timestamp", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"  #{height} — {tx_count:,} txs | {size_kb:,} kB | {ts}")

    lines.append("Source: mempool.space public API (live)")
    return "\n".join(lines)


def get_lightning_network_stats() -> str:
    """Get a Lightning Network health snapshot: channels, nodes, capacity, and fees.

    Reports channel count, node count, total network capacity in SAT,
    average and median channel sizes, fee rates (ppm), and node visibility
    breakdown. Use this to benchmark our node and inform channel management.
    """
    try:
        data = fetch("/api/v1/lightning/statistics/latest")
    except Exception as exc:
        return f"ERROR: Lightning stats unavailable — {exc}"

    latest = data.get("latest", data)
    now = datetime.now().strftime("%Y-%m-%d %H:%M ET")
    snapshot_date = latest.get("added", "")[:10]

    return (
        f"Lightning Network Stats — {now}\n"
        f"Snapshot date:       {snapshot_date}\n"
        f"Channels:            {latest.get('channel_count', 0):,}\n"
        f"Nodes:               {latest.get('node_count', 0):,}\n"
        f"Total capacity:      {latest.get('total_capacity', 0):,} SAT\n"
        f"Avg channel size:    {latest.get('avg_capacity', 0):,} SAT\n"
        f"Median channel size: {latest.get('med_capacity', 0):,} SAT\n"
        f"Avg fee rate:        {latest.get('avg_fee_rate', 0):,} ppm\n"
        f"Median fee rate:     {latest.get('med_fee_rate', 0):,} ppm\n"
        f"Avg base fee:        {latest.get('avg_base_fee_mtokens', 0):,} msat\n"
        f"Node visibility:     clearnet {latest.get('clearnet_nodes', 0):,} | "
        f"tor {latest.get('tor_nodes', 0):,} | "
        f"clearnet+tor {latest.get('clearnet_tor_nodes', 0):,} | "
        f"unannounced {latest.get('unannounced_nodes', 0):,}\n"
        f"Source: mempool.space public API (live, daily snapshot)"
    )
