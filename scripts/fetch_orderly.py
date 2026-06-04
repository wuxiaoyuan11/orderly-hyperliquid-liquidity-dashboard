from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request


BASE_URL = "https://api.orderly.org"
DEFAULT_SYMBOL = "PERP_ETH_USDC"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def utc_now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def ms_to_iso(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()


def post_public_query(payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}/v1/public/query",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_klines(symbol: str, interval: str, limit: int) -> dict[str, Any]:
    return post_public_query(
        {
            "type": "candles",
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
    )


def fetch_funding_history(symbol: str, start_ms: int, end_ms: int, size: int) -> dict[str, Any]:
    return post_public_query(
        {
            "type": "fundingRateHistory",
            "symbol": symbol,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": size,
        }
    )


def fetch_market_summary(symbol: str) -> dict[str, Any]:
    return post_public_query(
        {
            "type": "marketSummary",
            "symbols": [symbol],
        }
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def orderly_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    if not response.get("success"):
        raise ValueError(f"Orderly API returned unsuccessful response: {response}")
    data = response.get("data") or {}
    rows = data.get("rows")
    if rows is None:
        raise ValueError(f"Orderly API response does not contain data.rows: {response}")
    return rows


def write_klines_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "exchange",
        "symbol",
        "interval",
        "start_time",
        "open",
        "high",
        "low",
        "close",
        "volume_eth",
        "notional_volume_usd",
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            close = float(row["close"])
            volume_eth = float(row["volume"])
            writer.writerow(
                {
                    "exchange": "Orderly",
                    "symbol": DEFAULT_SYMBOL,
                    "interval": "1h",
                    "start_time": ms_to_iso(int(row["timestamp"])),
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume_eth": volume_eth,
                    "notional_volume_usd": volume_eth * close,
                }
            )


def write_funding_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["exchange", "symbol", "timestamp", "funding_rate", "mark_price"]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "exchange": "Orderly",
                    "symbol": DEFAULT_SYMBOL,
                    "timestamp": ms_to_iso(int(row["funding_rate_timestamp"])),
                    "funding_rate": row["funding_rate"],
                    "mark_price": row.get("mark_price"),
                }
            )


def top_of_book_from_market_summary(symbol: str, response: dict[str, Any]) -> dict[str, Any]:
    if not response.get("success"):
        raise ValueError(f"Orderly API returned unsuccessful market summary response: {response}")

    data = response.get("data") or {}
    markets = data.get("markets") or []
    market = next((row for row in markets if row.get("symbol") == symbol), None)
    if market is None:
        raise ValueError(f"Orderly market summary response does not contain {symbol}: {response}")

    best_bid = float(market["bid_price"])
    best_ask = float(market["ask_price"])
    mid = (best_bid + best_ask) / 2
    spread_bps = (best_ask - best_bid) / mid * 10_000

    return {
        "exchange": "Orderly",
        "symbol": symbol,
        "timestamp_ms": int(response.get("ts") or utc_now_ms()),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid,
        "spread_bps": spread_bps,
    }


def write_spread_csv(path: Path, top_of_book: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "exchange",
        "symbol",
        "timestamp",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread_bps",
    ]

    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "exchange": top_of_book["exchange"],
                "symbol": top_of_book["symbol"],
                "timestamp": ms_to_iso(top_of_book["timestamp_ms"]),
                "best_bid": top_of_book["best_bid"],
                "best_ask": top_of_book["best_ask"],
                "mid_price": top_of_book["mid_price"],
                "spread_bps": top_of_book["spread_bps"],
            }
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Orderly ETH perp market data.")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--limit", type=int, default=336)
    parser.add_argument("--funding-size", type=int, default=500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    end_ms = utc_now_ms()
    start_ms = end_ms - args.limit * 60 * 60 * 1000
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    klines = fetch_klines(args.symbol, args.interval, args.limit)
    funding = fetch_funding_history(args.symbol, start_ms, end_ms, args.funding_size)
    market_summary = fetch_market_summary(args.symbol)

    kline_rows = orderly_rows(klines)
    funding_rows = orderly_rows(funding)
    top_of_book = top_of_book_from_market_summary(args.symbol, market_summary)

    write_json(RAW_DIR / f"orderly_{args.symbol}_klines_{stamp}.json", klines)
    write_json(RAW_DIR / f"orderly_{args.symbol}_funding_{stamp}.json", funding)
    write_json(RAW_DIR / f"orderly_{args.symbol}_market_summary_{stamp}.json", market_summary)

    write_klines_csv(RAW_DIR / f"orderly_{args.symbol}_klines_{stamp}.csv", kline_rows)
    write_funding_csv(RAW_DIR / f"orderly_{args.symbol}_funding_{stamp}.csv", funding_rows)
    write_spread_csv(RAW_DIR / "orderly_PERP_ETH_USDC_spread_samples.csv", top_of_book)

    print(f"Fetched {len(kline_rows)} kline rows for {args.symbol}.")
    print(f"Fetched {len(funding_rows)} funding rows for {args.symbol}.")
    print(f"Top-of-book spread: {top_of_book['spread_bps']:.4f} bps.")
    print(f"Output directory: {RAW_DIR}")


if __name__ == "__main__":
    main()
