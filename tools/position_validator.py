#!/usr/bin/env python3
"""Hermes position sizing cross-validator."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

try:
    from audit_log import check_halt
except ImportError:  # pragma: no cover
    from src.tools.audit_log import check_halt  # type: ignore


APPROVE = "APPROVE"
REJECT = "REJECT"
PASS = "PASS"
FAIL = "FAIL"


class InputError(ValueError):
    """Raised when the validator input is malformed."""


def utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def positive_float(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{field} must be a float") from exc
    return result


def load_from_stdin() -> Dict[str, Any]:
    if sys.stdin.isatty():
        raise InputError("No CLI args or JSON stdin provided")
    raw = sys.stdin.read().strip()
    if not raw:
        raise InputError("JSON stdin was empty")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"Invalid JSON stdin: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise InputError("JSON stdin must be an object")
    return payload


def load_payload() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Validate a Hermes BTC long trade proposal")
    parser.add_argument("--side")
    parser.add_argument("--entry")
    parser.add_argument("--stop")
    parser.add_argument("--target")
    parser.add_argument("--size-usd", dest="size_usd")
    parser.add_argument("--account-equity", dest="account_equity")
    args = parser.parse_args()

    cli_payload = {k: v for k, v in vars(args).items() if v is not None}
    if cli_payload:
        return cli_payload
    return load_from_stdin()


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, float | str]:
    required = ("side", "entry", "stop", "target", "size_usd", "account_equity")
    missing = [field for field in required if field not in payload]
    if missing:
        raise InputError(f"Missing required fields: {', '.join(missing)}")

    normalized: Dict[str, float | str] = {"side": str(payload["side"]).strip().lower()}
    for field in required[1:]:
        normalized[field] = positive_float(payload[field], field)

    if normalized["account_equity"] <= 0:
        raise InputError("account_equity must be greater than 0")
    if normalized["size_usd"] <= 0:
        raise InputError("size_usd must be greater than 0")
    return normalized


def check_status(condition: bool) -> str:
    return PASS if condition else FAIL


def build_response(trade: Dict[str, float | str]) -> Tuple[Dict[str, Any], int]:
    side = str(trade["side"])
    entry = float(trade["entry"])
    stop = float(trade["stop"])
    target = float(trade["target"])
    size_usd = float(trade["size_usd"])
    account_equity = float(trade["account_equity"])

    entry_sanity = entry > 0 and stop > 0 and target > 0
    side_check = side == "long"
    halt_active = check_halt()

    stop_distance_ratio = ((entry - stop) / entry) if entry > 0 else 0.0
    valid_stop_below_entry = entry_sanity and stop < entry
    valid_target_above_entry = entry_sanity and target > entry
    reward_ratio_numerator = target - entry
    reward_ratio_denominator = entry - stop
    reward_risk_ratio = (
        reward_ratio_numerator / reward_ratio_denominator
        if valid_stop_below_entry and valid_target_above_entry
        else 0.0
    )

    risk_usd = stop_distance_ratio * size_usd if entry > 0 else 0.0
    risk_pct = (risk_usd / account_equity * 100.0) if account_equity > 0 else 0.0
    reward_usd = ((target - entry) / entry) * size_usd if entry > 0 else 0.0
    size_sats = round((size_usd / entry) * 1e8) if entry > 0 else 0
    expected_sats_gained = round((reward_usd / entry) * 1e8) if entry > 0 else 0

    checks = {
        "risk_per_trade": check_status(valid_stop_below_entry and risk_usd <= account_equity * 0.01),
        "reward_risk_ratio": check_status(reward_risk_ratio >= 2.0),
        "position_size": check_status(size_usd <= account_equity * 0.10),
        "stop_distance_min": check_status(valid_stop_below_entry and stop_distance_ratio >= 0.003),
        "stop_distance_max": check_status(valid_stop_below_entry and stop_distance_ratio <= 0.02),
        "entry_sanity": check_status(entry_sanity),
        "side_check": check_status(side_check),
        "halt_flag": check_status(not halt_active),
    }

    reject_reasons = []
    if checks["risk_per_trade"] == FAIL:
        reject_reasons.append("Risk per trade exceeds 1% of account equity")
    if checks["reward_risk_ratio"] == FAIL:
        reject_reasons.append("Reward:Risk ratio is below 2.0 or target is not above entry")
    if checks["position_size"] == FAIL:
        reject_reasons.append("Position size exceeds 10% of account equity")
    if checks["stop_distance_min"] == FAIL:
        reject_reasons.append("Stop must be below entry by at least 0.3%")
    if checks["stop_distance_max"] == FAIL:
        reject_reasons.append("Stop must be below entry by no more than 2.0%")
    if checks["entry_sanity"] == FAIL:
        reject_reasons.append("Entry, stop, and target must all be greater than 0")
    if checks["side_check"] == FAIL:
        reject_reasons.append("Only long trades are permitted")
    if checks["halt_flag"] == FAIL:
        reject_reasons.append("HALT FLAG ACTIVE")

    verdict = APPROVE if all(result == PASS for result in checks.values()) else REJECT

    response = {
        "verdict": verdict,
        "side": side,
        "entry": entry,
        "stop": stop,
        "target": target,
        "size_usd": size_usd,
        "size_sats": size_sats,
        "account_equity": account_equity,
        "risk_usd": risk_usd,
        "risk_pct": risk_pct,
        "reward_usd": reward_usd,
        "reward_risk_ratio": reward_risk_ratio,
        "expected_sats_gained": expected_sats_gained,
        "checks": checks,
        "reject_reasons": reject_reasons,
        "ts": utc_now_z(),
    }
    return response, (0 if verdict == APPROVE else 1)


def emit_error(message: str) -> int:
    print(json.dumps({"verdict": "ERROR", "error": message, "ts": utc_now_z()}))
    return 2


def main() -> int:
    try:
        payload = load_payload()
        trade = normalize_payload(payload)
        response, exit_code = build_response(trade)
    except InputError as exc:
        return emit_error(str(exc))

    print(json.dumps(response))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
