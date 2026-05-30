#!/usr/bin/env python3
"""Hermes drawdown monitor and emergency halt daemon."""
from __future__ import annotations

import argparse
import base64
import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_log import check_halt, log_circuit_breaker, log_halt

UTC = timezone.utc
DEFAULT_CONFIG_PATH = Path.home() / "freqtrade" / "user_data" / "config-kraken-paper.json"
DEFAULT_DB_PATHS = (
    Path.home() / "freqtrade" / "user_data" / "tradesv3.sqlite",
    Path.home() / "freqtrade" / "user_data" / "tradesv3.dryrun.sqlite",
)
HALT_FLAG_PATH = Path.home() / ".hermes" / "halt"
DEFAULT_STARTING_CAPITAL = 1000.0
DEFAULT_WATCH_INTERVAL = 60
EXIT_SOFT = 1
EXIT_HARD = 2
EXIT_ERROR = 3


class DataSourceError(RuntimeError):
    """Raised when Freqtrade data cannot be loaded."""


@dataclass(frozen=True)
class CircuitBreakerEvent:
    name: str
    reason: str
    severity: str

    @property
    def key(self) -> str:
        return f"{self.name}:{self.reason}"

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "reason": self.reason}


@dataclass
class RuntimeConfig:
    api_base: str
    api_username: str
    api_password: str
    config_path: Path
    db_candidates: list[Path]
    starting_capital: float


@dataclass
class MonitorSnapshot:
    ts: str
    source: str
    account_equity: float
    daily_pnl_pct: float
    weekly_pnl_pct: float
    consecutive_losses: int
    open_positions: list[dict[str, Any]]
    latest_closed_trade: dict[str, Any] | None
    circuit_breakers: list[CircuitBreakerEvent]
    halt_active: bool
    halt_reason: str | None

    def check_payload(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "account_equity": round(self.account_equity, 4),
            "daily_pnl_pct": round(self.daily_pnl_pct, 4),
            "weekly_pnl_pct": round(self.weekly_pnl_pct, 4),
            "consecutive_losses": self.consecutive_losses,
            "circuit_breakers": [event.as_dict() for event in self.circuit_breakers],
            "halt_active": self.halt_active,
            "halt_reason": self.halt_reason,
        }

    def status_payload(self) -> dict[str, Any]:
        payload = self.check_payload()
        payload["source"] = self.source
        payload["open_positions"] = self.open_positions
        return payload


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        stamp = float(value)
        if stamp > 1_000_000_000_000:
            stamp /= 1000.0
        return datetime.fromtimestamp(stamp, tz=UTC)

    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    if text.endswith("+0000"):
        text = f"{text[:-5]}+00:00"

    for candidate in (text, text.replace(" ", "T", 1)):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            continue

    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue

    raise DataSourceError(f"Unable to parse timestamp: {value!r}")


def parse_sqlite_db_url(db_url: str, user_data_dir: Path) -> Path | None:
    if not db_url.startswith("sqlite://"):
        return None
    raw_path = db_url[len("sqlite://") :]
    if not raw_path:
        return None
    if raw_path.startswith("/"):
        return Path(raw_path)
    return user_data_dir / raw_path.lstrip("/")


def load_runtime_config() -> RuntimeConfig:
    config_path = Path(os.environ.get("HERMES_FREQTRADE_CONFIG", str(DEFAULT_CONFIG_PATH))).expanduser()
    data: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open() as handle:
            data = json.load(handle)

    api_server = data.get("api_server", {}) if isinstance(data, dict) else {}
    listen_ip = api_server.get("listen_ip_address") or "localhost"
    if listen_ip in {"0.0.0.0", "::"}:
        listen_ip = "localhost"
    listen_port = api_server.get("listen_port", 8080)
    api_base = os.environ.get("HERMES_FREQTRADE_API_URL", f"http://{listen_ip}:{listen_port}/api/v1")

    db_candidates: list[Path] = []
    db_override = os.environ.get("HERMES_FREQTRADE_DB_PATH")
    if db_override:
        db_candidates.append(Path(db_override).expanduser())

    db_url = data.get("db_url") if isinstance(data, dict) else None
    if isinstance(db_url, str):
        db_path = parse_sqlite_db_url(db_url, config_path.parent)
        if db_path is not None and db_path not in db_candidates:
            db_candidates.append(db_path)

    for default_path in DEFAULT_DB_PATHS:
        if default_path not in db_candidates:
            db_candidates.append(default_path)

    starting_capital = float(data.get("dry_run_wallet", DEFAULT_STARTING_CAPITAL)) if isinstance(data, dict) else DEFAULT_STARTING_CAPITAL

    return RuntimeConfig(
        api_base=api_base.rstrip("/"),
        api_username=str(api_server.get("username") or ""),
        api_password=str(api_server.get("password") or ""),
        config_path=config_path,
        db_candidates=db_candidates,
        starting_capital=starting_capital,
    )


def build_headers(config: RuntimeConfig) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "HermesDrawdownMonitor/1.0",
    }
    if config.api_username or config.api_password:
        token = base64.b64encode(f"{config.api_username}:{config.api_password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    return headers


def fetch_json(config: RuntimeConfig, endpoint: str, params: dict[str, Any] | None = None) -> Any:
    query = f"?{urlencode(params)}" if params else ""
    request = Request(f"{config.api_base}{endpoint}{query}", headers=build_headers(config))
    try:
        with urlopen(request, timeout=5) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8", "replace")
    except HTTPError as exc:
        raise DataSourceError(f"{endpoint} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise DataSourceError(f"{endpoint} unreachable: {exc.reason}") from exc

    stripped = body.lstrip()
    if stripped.startswith("<") or ("json" not in content_type.lower() and not stripped.startswith(("{", "["))):
        raise DataSourceError(f"{endpoint} returned non-JSON content ({content_type or 'unknown'})")

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"{endpoint} returned invalid JSON") from exc


def monitored_pair(pair: str | None, base_currency: str | None = None) -> bool:
    if base_currency and str(base_currency).upper() == "BTC":
        return True
    if not pair:
        return False
    return str(pair).upper().startswith("BTC/")


def normalize_position(row: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "pair": row.get("pair"),
        "open_date": row.get("open_date"),
        "open_rate": row.get("open_rate"),
        "stake_amount": row.get("stake_amount") or row.get("open_trade_value"),
        "amount": row.get("amount"),
        "profit_pct": row.get("profit_pct"),
        "profit_abs": row.get("profit_abs") if row.get("profit_abs") is not None else row.get("total_profit_abs"),
    }
    if row.get("current_rate") is not None:
        payload["current_rate"] = row.get("current_rate")
    return payload


def normalize_closed_trade(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("is_open"):
        return None
    if not monitored_pair(row.get("pair"), row.get("base_currency")):
        return None

    closed_at = parse_timestamp(row.get("close_date") or row.get("close_timestamp"))
    if closed_at is None:
        return None

    profit_ratio = row.get("close_profit")
    if profit_ratio is None and row.get("close_profit_pct") is not None:
        profit_ratio = float(row["close_profit_pct"]) / 100.0

    profit_abs = row.get("close_profit_abs")
    if profit_abs is None:
        profit_abs = row.get("profit_abs")
    if profit_abs is None and profit_ratio is not None and row.get("stake_amount") is not None:
        profit_abs = float(row["stake_amount"]) * float(profit_ratio)
    if profit_ratio is None and profit_abs is not None and row.get("stake_amount"):
        stake_amount = float(row["stake_amount"])
        profit_ratio = float(profit_abs) / stake_amount if stake_amount else 0.0

    return {
        "trade_id": row.get("trade_id") or row.get("id"),
        "pair": row.get("pair"),
        "closed_at": closed_at,
        "profit_ratio": float(profit_ratio or 0.0),
        "profit_abs": float(profit_abs or 0.0),
    }


def compute_metrics(
    starting_capital: float,
    closed_trades: list[dict[str, Any]],
) -> tuple[float, float, int, dict[str, Any] | None]:
    now = utc_now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=day_start.weekday())
    capital = starting_capital or DEFAULT_STARTING_CAPITAL

    daily_abs = sum(trade["profit_abs"] for trade in closed_trades if trade["closed_at"] >= day_start)
    weekly_abs = sum(trade["profit_abs"] for trade in closed_trades if trade["closed_at"] >= week_start)

    ordered = sorted(closed_trades, key=lambda trade: trade["closed_at"], reverse=True)
    consecutive_losses = 0
    for trade in ordered:
        if trade["profit_abs"] < 0:
            consecutive_losses += 1
            continue
        break

    return (
        (daily_abs / capital) * 100.0,
        (weekly_abs / capital) * 100.0,
        consecutive_losses,
        ordered[0] if ordered else None,
    )


def highest_halt_severity(events: list[CircuitBreakerEvent]) -> str | None:
    if any(event.severity == "hard" for event in events):
        return "hard"
    if any(event.severity == "soft" for event in events):
        return "soft"
    return None


def halt_exit_code(reason: str | None) -> int:
    if not reason:
        return 0
    upper = reason.upper()
    if "HARD HALT" in upper or "CB-2" in upper or "CB-4" in upper:
        return EXIT_HARD
    if "SOFT HALT" in upper or "CB-1" in upper or "CB-5" in upper:
        return EXIT_SOFT
    return EXIT_SOFT if check_halt() else 0


def read_halt_reason() -> str | None:
    if not HALT_FLAG_PATH.exists():
        return None
    text = HALT_FLAG_PATH.read_text().strip()
    return text or None


def resolve_db_path(config: RuntimeConfig) -> Path:
    for candidate in config.db_candidates:
        if candidate.exists():
            return candidate
    checked = ", ".join(str(path) for path in config.db_candidates)
    raise DataSourceError(f"no SQLite database found; checked {checked}")


def query_db_trades(config: RuntimeConfig) -> tuple[Path, list[sqlite3.Row]]:
    db_path = resolve_db_path(config)
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                pair,
                base_currency,
                is_open,
                stake_amount,
                amount,
                open_rate,
                close_rate,
                open_date,
                close_date,
                close_profit,
                close_profit_abs,
                realized_profit
            FROM trades
            ORDER BY COALESCE(close_date, open_date) DESC
            """
        ).fetchall()
        return db_path, rows
    except sqlite3.Error as exc:
        raise DataSourceError(f"unable to query trades table in {db_path}: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


def load_closed_trades_from_db(config: RuntimeConfig) -> list[dict[str, Any]]:
    _, rows = query_db_trades(config)
    trades: list[dict[str, Any]] = []
    for raw_row in rows:
        trade = normalize_closed_trade(dict(raw_row))
        if trade is not None:
            trades.append(trade)
    return trades


def load_db_snapshot(config: RuntimeConfig) -> MonitorSnapshot:
    db_path, rows = query_db_trades(config)
    open_positions: list[dict[str, Any]] = []
    closed_trades: list[dict[str, Any]] = []
    realized_closed_profit = 0.0
    open_realized_profit = 0.0

    for raw_row in rows:
        row = dict(raw_row)
        if not monitored_pair(row.get("pair"), row.get("base_currency")):
            continue

        if row.get("is_open"):
            open_positions.append(
                normalize_position(
                    {
                        "pair": row.get("pair"),
                        "open_date": row.get("open_date"),
                        "open_rate": row.get("open_rate"),
                        "stake_amount": row.get("stake_amount"),
                        "amount": row.get("amount"),
                        "profit_pct": None,
                        "profit_abs": row.get("realized_profit"),
                    }
                )
            )
            open_realized_profit += float(row.get("realized_profit") or 0.0)
            continue

        trade = normalize_closed_trade(row)
        if trade is None:
            continue
        closed_trades.append(trade)
        realized_closed_profit += trade["profit_abs"]

    daily_pct, weekly_pct, consecutive_losses, latest_trade = compute_metrics(config.starting_capital, closed_trades)
    halt_reason = read_halt_reason()
    # SQLite fallback has no live mark price, so equity uses realized P&L and cost basis.
    account_equity = config.starting_capital + realized_closed_profit + open_realized_profit

    return MonitorSnapshot(
        ts=utc_now_iso(),
        source=f"sqlite:{db_path}",
        account_equity=account_equity,
        daily_pnl_pct=daily_pct,
        weekly_pnl_pct=weekly_pct,
        consecutive_losses=consecutive_losses,
        open_positions=open_positions,
        latest_closed_trade=latest_trade,
        circuit_breakers=[],
        halt_active=bool(halt_reason),
        halt_reason=halt_reason,
    )


def load_api_snapshot(config: RuntimeConfig) -> MonitorSnapshot:
    balance = fetch_json(config, "/balance")
    status = fetch_json(config, "/status")
    profit = fetch_json(config, "/profit")

    closed_trade_count = int(profit.get("closed_trade_count", 0) or 0)
    trade_history: list[dict[str, Any]] = []
    if closed_trade_count > 0:
        try:
            trades_payload = fetch_json(config, "/trades", {"limit": 500, "offset": 0})
            trade_rows = trades_payload.get("trades", trades_payload)
            for row in trade_rows:
                trade = normalize_closed_trade(row)
                if trade is not None:
                    trade_history.append(trade)
        except DataSourceError as api_trade_error:
            try:
                trade_history = load_closed_trades_from_db(config)
            except DataSourceError as db_error:
                raise DataSourceError(
                    "closed-trade history unavailable from both /trades and SQLite fallback: "
                    f"API={api_trade_error}; SQLite={db_error}"
                ) from db_error

    daily_pct, weekly_pct, consecutive_losses, latest_trade = compute_metrics(config.starting_capital, trade_history)
    halt_reason = read_halt_reason()
    open_positions = [normalize_position(row) for row in status if monitored_pair(row.get("pair"), row.get("base_currency"))]
    account_equity = float(balance.get("total_bot") or balance.get("value_bot") or config.starting_capital)

    return MonitorSnapshot(
        ts=utc_now_iso(),
        source="api",
        account_equity=account_equity,
        daily_pnl_pct=daily_pct,
        weekly_pnl_pct=weekly_pct,
        consecutive_losses=consecutive_losses,
        open_positions=open_positions,
        latest_closed_trade=latest_trade,
        circuit_breakers=[],
        halt_active=bool(halt_reason),
        halt_reason=halt_reason,
    )


def collect_snapshot(config: RuntimeConfig) -> MonitorSnapshot:
    errors: list[str] = []
    try:
        return load_api_snapshot(config)
    except DataSourceError as exc:
        errors.append(f"API: {exc}")

    try:
        return load_db_snapshot(config)
    except DataSourceError as exc:
        errors.append(f"SQLite: {exc}")

    raise DataSourceError("No usable Freqtrade datasource. " + " | ".join(errors))


def evaluate_circuit_breakers(snapshot: MonitorSnapshot) -> list[CircuitBreakerEvent]:
    events: list[CircuitBreakerEvent] = []

    if snapshot.daily_pnl_pct <= -2.0:
        events.append(
            CircuitBreakerEvent(
                name="CB-1",
                reason=f"Daily drawdown is {snapshot.daily_pnl_pct:.2f}% (limit -2.00%).",
                severity="soft",
            )
        )
    if snapshot.weekly_pnl_pct <= -5.0:
        events.append(
            CircuitBreakerEvent(
                name="CB-2",
                reason=f"Weekly drawdown is {snapshot.weekly_pnl_pct:.2f}% (limit -5.00%).",
                severity="hard",
            )
        )
    if snapshot.latest_closed_trade and snapshot.latest_closed_trade["profit_ratio"] <= -0.015:
        events.append(
            CircuitBreakerEvent(
                name="CB-3",
                reason=(
                    f"Latest closed trade {snapshot.latest_closed_trade['trade_id']} on {snapshot.latest_closed_trade['pair']} "
                    f"lost {snapshot.latest_closed_trade['profit_ratio'] * 100:.2f}% (alert threshold -1.50%)."
                ),
                severity="alert",
            )
        )
    if snapshot.account_equity < 800.0:
        events.append(
            CircuitBreakerEvent(
                name="CB-4",
                reason=f"Account equity is ${snapshot.account_equity:.2f} (minimum $800.00).",
                severity="hard",
            )
        )
    if snapshot.consecutive_losses >= 3:
        events.append(
            CircuitBreakerEvent(
                name="CB-5",
                reason=f"Loss streak reached {snapshot.consecutive_losses} consecutive closed trades.",
                severity="soft",
            )
        )
    return events


def apply_actions(snapshot: MonitorSnapshot, suppress_keys: set[str] | None = None) -> int:
    suppress_keys = suppress_keys or set()
    for event in snapshot.circuit_breakers:
        if event.key not in suppress_keys:
            log_circuit_breaker(event.name, event.reason)

    halt_events = [event for event in snapshot.circuit_breakers if event.severity in {"soft", "hard"}]
    halt_severity = highest_halt_severity(halt_events)
    if halt_severity is None:
        return halt_exit_code(snapshot.halt_reason)

    if halt_severity == "hard":
        relevant_events = halt_events
    else:
        relevant_events = [event for event in halt_events if event.severity == "soft"]

    halt_reason = f"{halt_severity.upper()} HALT | " + " | ".join(
        f"{event.name}: {event.reason}" for event in relevant_events
    )
    if snapshot.halt_reason != halt_reason:
        log_halt(halt_reason)
        snapshot.halt_reason = halt_reason
    snapshot.halt_active = True
    return EXIT_HARD if halt_severity == "hard" else EXIT_SOFT


def run_check(
    config: RuntimeConfig,
    *,
    apply_side_effects: bool,
    suppress_keys: set[str] | None = None,
) -> tuple[MonitorSnapshot, int]:
    snapshot = collect_snapshot(config)
    snapshot.circuit_breakers = evaluate_circuit_breakers(snapshot)
    exit_code = halt_exit_code(snapshot.halt_reason)
    if apply_side_effects:
        exit_code = max(exit_code, apply_actions(snapshot, suppress_keys=suppress_keys))
    return snapshot, exit_code


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2))


def handle_check(args: argparse.Namespace) -> int:
    del args
    config = load_runtime_config()
    snapshot, exit_code = run_check(config, apply_side_effects=True)
    print_json(snapshot.check_payload())
    if exit_code == EXIT_HARD:
        print(snapshot.halt_reason or "HARD HALT", file=sys.stderr)
    elif exit_code == EXIT_SOFT:
        print(snapshot.halt_reason or "SOFT HALT", file=sys.stderr)
    return exit_code


def handle_status(args: argparse.Namespace) -> int:
    del args
    config = load_runtime_config()
    snapshot, _ = run_check(config, apply_side_effects=False)
    print_json(snapshot.status_payload())
    return 0


def handle_watch(args: argparse.Namespace) -> int:
    config = load_runtime_config()
    seen_keys: set[str] = set()
    while True:
        snapshot, _ = run_check(config, apply_side_effects=True, suppress_keys=seen_keys)
        print_json(snapshot.check_payload())
        seen_keys = {event.key for event in snapshot.circuit_breakers}
        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes drawdown monitor and halt daemon")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Run one drawdown check and print JSON status")
    check_parser.set_defaults(func=handle_check)

    watch_parser = subparsers.add_parser("watch", help="Monitor drawdown continuously")
    watch_parser.add_argument("--interval", type=int, default=DEFAULT_WATCH_INTERVAL, help="Polling interval in seconds")
    watch_parser.set_defaults(func=handle_watch)

    status_parser = subparsers.add_parser("status", help="Print current account state")
    status_parser.set_defaults(func=handle_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except DataSourceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
