from __future__ import annotations

import argparse
import csv
import json
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError


HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
ORDERLY_PUBLIC_QUERY_URL = "https://api.orderly.org/v1/public/query"
DEFAULT_HYPERLIQUID_COIN = "ETH"
DEFAULT_ORDERLY_SYMBOL = "PERP_ETH_USDC"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = RAW_DIR / "spread_samples_1m.csv"
ERROR_LOG_PATH = RAW_DIR / "spread_sampler_errors.log"

SHOULD_STOP = False


def handle_stop_signal(signum: int, frame: Any) -> None:
    global SHOULD_STOP
    SHOULD_STOP = True


signal.signal(signal.SIGINT, handle_stop_signal)
signal.signal(signal.SIGTERM, handle_stop_signal)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def post_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def spread_bps(best_bid: float, best_ask: float) -> tuple[float, float]:
    mid_price = (best_bid + best_ask) / 2
    spread = (best_ask - best_bid) / mid_price * 10_000
    return mid_price, spread


def fetch_hyperliquid_spread(coin: str, timeout: int) -> dict[str, Any]:
    response = post_json(
        HYPERLIQUID_INFO_URL,
        {
            "type": "l2Book",
            "coin": coin,
        },
        timeout,
    )
    levels = response.get("levels", [])
    if len(levels) < 2 or not levels[0] or not levels[1]:
        raise ValueError(f"Unexpected Hyperliquid l2Book response shape: {response}")

    best_bid = float(levels[0][0]["px"])
    best_ask = float(levels[1][0]["px"])
    mid_price, spread = spread_bps(best_bid, best_ask)

    return {
        "exchange": "Hyperliquid",
        "market": coin,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid_price,
        "spread_bps": spread,
    }


def fetch_orderly_spread(symbol: str, timeout: int) -> dict[str, Any]:
    response = post_json(
        ORDERLY_PUBLIC_QUERY_URL,
        {
            "type": "marketSummary",
            "symbols": [symbol],
        },
        timeout,
    )
    if not response.get("success"):
        raise ValueError(f"Orderly marketSummary returned unsuccessful response: {response}")

    markets = response.get("data", {}).get("markets", [])
    market = next((row for row in markets if row.get("symbol") == symbol), None)
    if market is None:
        raise ValueError(f"Orderly marketSummary does not contain {symbol}: {response}")

    best_bid = float(market["bid_price"])
    best_ask = float(market["ask_price"])
    mid_price, spread = spread_bps(best_bid, best_ask)

    return {
        "exchange": "Orderly",
        "market": symbol,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid_price,
        "spread_bps": spread,
    }


def ensure_output_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames())
        writer.writeheader()
        file.flush()


def fieldnames() -> list[str]:
    return [
        "sample_id",
        "scheduled_timestamp",
        "observed_timestamp",
        "exchange",
        "market",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread_bps",
        "status",
        "error",
    ]


def append_row(path: Path, row: dict[str, Any]) -> None:
    ensure_output_header(path)
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames())
        writer.writerow(row)
        file.flush()


def log_error(message: str) -> None:
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(f"{utc_now().isoformat()} {message}\n")
        file.flush()


def sample_once(
    sample_id: int,
    scheduled_timestamp: datetime,
    hyperliquid_coin: str,
    orderly_symbol: str,
    timeout: int,
    output_path: Path,
) -> None:
    tasks = [
        ("Hyperliquid", lambda: fetch_hyperliquid_spread(hyperliquid_coin, timeout)),
        ("Orderly", lambda: fetch_orderly_spread(orderly_symbol, timeout)),
    ]

    for exchange, fetcher in tasks:
        observed_timestamp = utc_now()
        try:
            data = fetcher()
            append_row(
                output_path,
                {
                    "sample_id": sample_id,
                    "scheduled_timestamp": scheduled_timestamp.isoformat(),
                    "observed_timestamp": observed_timestamp.isoformat(),
                    "exchange": data["exchange"],
                    "market": data["market"],
                    "best_bid": data["best_bid"],
                    "best_ask": data["best_ask"],
                    "mid_price": data["mid_price"],
                    "spread_bps": data["spread_bps"],
                    "status": "ok",
                    "error": "",
                },
            )
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            append_row(
                output_path,
                {
                    "sample_id": sample_id,
                    "scheduled_timestamp": scheduled_timestamp.isoformat(),
                    "observed_timestamp": observed_timestamp.isoformat(),
                    "exchange": exchange,
                    "market": hyperliquid_coin if exchange == "Hyperliquid" else orderly_symbol,
                    "best_bid": "",
                    "best_ask": "",
                    "mid_price": "",
                    "spread_bps": "",
                    "status": "error",
                    "error": error_message,
                },
            )
            log_error(f"sample_id={sample_id} exchange={exchange} {error_message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect 1-minute top-of-book spread samples.")
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--duration-minutes", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--hyperliquid-coin", default=DEFAULT_HYPERLIQUID_COIN)
    parser.add_argument("--orderly-symbol", default=DEFAULT_ORDERLY_SYMBOL)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--mirror-output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_time = time.monotonic()
    max_duration_seconds = args.duration_minutes * 60 if args.duration_minutes > 0 else None
    sample_id = 0

    ensure_output_header(args.output)
    print(f"Writing spread samples to {args.output}")
    print("Press Ctrl+C to stop gracefully.")

    while not SHOULD_STOP:
        scheduled_timestamp = utc_now()
        sample_id += 1
        sample_started = time.monotonic()

        sample_once(
            sample_id=sample_id,
            scheduled_timestamp=scheduled_timestamp,
            hyperliquid_coin=args.hyperliquid_coin,
            orderly_symbol=args.orderly_symbol,
            timeout=args.timeout,
            output_path=args.output,
        )
        if args.mirror_output is not None:
            args.mirror_output.parent.mkdir(parents=True, exist_ok=True)
            args.mirror_output.write_bytes(args.output.read_bytes())

        if max_duration_seconds is not None and time.monotonic() - start_time >= max_duration_seconds:
            break

        elapsed = time.monotonic() - sample_started
        sleep_seconds = max(0, args.interval_seconds - elapsed)
        end_sleep_at = time.monotonic() + sleep_seconds
        while not SHOULD_STOP and time.monotonic() < end_sleep_at:
            time.sleep(min(1, end_sleep_at - time.monotonic()))

    print("Spread sampler stopped.")


if __name__ == "__main__":
    main()
