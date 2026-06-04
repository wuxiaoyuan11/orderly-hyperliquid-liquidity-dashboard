from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import request


BASE_URL = "https://api.hyperliquid.xyz/info"
DEFAULT_COIN = "ETH"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def utc_now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def ms_to_iso(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()


def post_info(payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        BASE_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_candles(coin: str, start_ms: int, end_ms: int, interval: str) -> list[dict[str, Any]]:
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
        },
    }
    return post_info(payload)


def fetch_funding_history(coin: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    payload = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": start_ms,
        "endTime": end_ms,
    }
    return post_info(payload)


def fetch_top_of_book(coin: str) -> dict[str, Any]:
    payload = {
        "type": "l2Book",
        "coin": coin,
    }
    book = post_info(payload)
    levels = book.get("levels", [])
    if len(levels) < 2 or not levels[0] or not levels[1]:
        raise ValueError(f"Unexpected l2Book response shape: {book}")

    best_bid = float(levels[0][0]["px"])
    best_ask = float(levels[1][0]["px"])
    mid = (best_bid + best_ask) / 2
    spread_bps = (best_ask - best_bid) / mid * 10_000

    return {
        "exchange": "Hyperliquid",
        "coin": coin,
        "timestamp_ms": utc_now_ms(),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid,
        "spread_bps": spread_bps,
        "raw": book,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def write_candles_csv(path: Path, candles: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "exchange",
        "coin",
        "interval",
        "start_time",
        "end_time",
        "open",
        "high",
        "low",
        "close",
        "volume_eth",
        "notional_volume_usd",
        "trades",
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in candles:
            close = float(row["c"])
            volume_eth = float(row["v"])
            writer.writerow(
                {
                    "exchange": "Hyperliquid",
                    "coin": row.get("s", DEFAULT_COIN),
                    "interval": row.get("i"),
                    "start_time": ms_to_iso(int(row["t"])),
                    "end_time": ms_to_iso(int(row["T"])),
                    "open": row["o"],
                    "high": row["h"],
                    "low": row["l"],
                    "close": row["c"],
                    "volume_eth": volume_eth,
                    "notional_volume_usd": volume_eth * close,
                    "trades": row.get("n"),
                }
            )


def write_funding_csv(path: Path, funding_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["exchange", "coin", "timestamp", "funding_rate", "premium"]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in funding_rows:
            writer.writerow(
                {
                    "exchange": "Hyperliquid",
                    "coin": row.get("coin", DEFAULT_COIN),
                    "timestamp": ms_to_iso(int(row["time"])),
                    "funding_rate": row["fundingRate"],
                    "premium": row.get("premium"),
                }
            )


def write_spread_csv(path: Path, top_of_book: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "exchange",
        "coin",
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
                "coin": top_of_book["coin"],
                "timestamp": ms_to_iso(top_of_book["timestamp_ms"]),
                "best_bid": top_of_book["best_bid"],
                "best_ask": top_of_book["best_ask"],
                "mid_price": top_of_book["mid_price"],
                "spread_bps": top_of_book["spread_bps"],
            }
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Hyperliquid ETH perp market data.")
    parser.add_argument("--coin", default=DEFAULT_COIN)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--interval", default="1h")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    end_ms = utc_now_ms()
    start_ms = int((datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp() * 1000)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    candles = fetch_candles(args.coin, start_ms, end_ms, args.interval)
    funding = fetch_funding_history(args.coin, start_ms, end_ms)
    top_of_book = fetch_top_of_book(args.coin)

    write_json(RAW_DIR / f"hyperliquid_{args.coin}_candles_{stamp}.json", candles)
    write_json(RAW_DIR / f"hyperliquid_{args.coin}_funding_{stamp}.json", funding)
    write_json(RAW_DIR / f"hyperliquid_{args.coin}_l2book_{stamp}.json", top_of_book["raw"])

    write_candles_csv(RAW_DIR / f"hyperliquid_{args.coin}_candles_{stamp}.csv", candles)
    write_funding_csv(RAW_DIR / f"hyperliquid_{args.coin}_funding_{stamp}.csv", funding)
    write_spread_csv(RAW_DIR / "hyperliquid_ETH_spread_samples.csv", top_of_book)

    print(f"Fetched {len(candles)} candle rows for {args.coin}.")
    print(f"Fetched {len(funding)} funding rows for {args.coin}.")
    print(f"Top-of-book spread: {top_of_book['spread_bps']:.4f} bps.")
    print(f"Output directory: {RAW_DIR}")


if __name__ == "__main__":
    main()
