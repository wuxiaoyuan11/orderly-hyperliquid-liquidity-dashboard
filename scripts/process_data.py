from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SPREAD_WINDOW_HOURS = 72


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def latest(pattern: str) -> Path:
    files = sorted(RAW_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files match {RAW_DIR / pattern}")
    return files[-1]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[int(index)]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def funding_periods_per_day(timestamps: list[datetime]) -> float:
    if len(timestamps) < 2:
        return math.nan
    ordered = sorted(timestamps)
    deltas = [
        (ordered[i] - ordered[i - 1]).total_seconds() / 3600
        for i in range(1, len(ordered))
        if ordered[i] > ordered[i - 1]
    ]
    if not deltas:
        return math.nan
    median_hours = median(deltas)
    return 24 / median_hours


def normalize_volume_rows(rows: list[dict[str, str]], venue: str, symbol_key: str) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        timestamp = parse_iso(row["start_time"])
        normalized.append(
            {
                "exchange": venue,
                "market": row[symbol_key],
                "timestamp": timestamp.isoformat(),
                "date": timestamp.date().isoformat(),
                "volume_eth": float(row["volume_eth"]),
                "notional_volume_usd": float(row["notional_volume_usd"]),
                "close": float(row["close"]),
            }
        )
    return normalized


def normalize_funding_rows(rows: list[dict[str, str]], venue: str, symbol_key: str) -> list[dict[str, Any]]:
    timestamps = [parse_iso(row["timestamp"]) for row in rows]
    periods_per_day = funding_periods_per_day(timestamps)
    periods_per_year = periods_per_day * 365 if not math.isnan(periods_per_day) else math.nan

    normalized = []
    for row in rows:
        timestamp = parse_iso(row["timestamp"])
        funding_rate = float(row["funding_rate"])
        normalized.append(
            {
                "exchange": venue,
                "market": row[symbol_key],
                "timestamp": timestamp.isoformat(),
                "date": timestamp.date().isoformat(),
                "funding_rate": funding_rate,
                "funding_rate_pct": funding_rate * 100,
                "funding_rate_annualized_pct": funding_rate * periods_per_year * 100,
                "periods_per_day": periods_per_day,
            }
        )
    return normalized


def choose_spread_files() -> list[Path]:
    if (RAW_DIR / "spread_samples_1m_live.csv").exists():
        return [RAW_DIR / "spread_samples_1m_live.csv"]
    if (RAW_DIR / "spread_samples_1m.csv").exists():
        return [RAW_DIR / "spread_samples_1m.csv"]
    return [
        RAW_DIR / "hyperliquid_ETH_spread_samples.csv",
        RAW_DIR / "orderly_PERP_ETH_USDC_spread_samples.csv",
    ]


def load_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]], list[Path]]:
    hyper_volume = normalize_volume_rows(
        read_csv(latest("hyperliquid_ETH_candles_*.csv")),
        "Hyperliquid",
        "coin",
    )
    orderly_volume = normalize_volume_rows(
        read_csv(latest("orderly_PERP_ETH_USDC_klines_*.csv")),
        "Orderly",
        "symbol",
    )
    volume_rows = hyper_volume + orderly_volume

    hyper_funding = normalize_funding_rows(
        read_csv(latest("hyperliquid_ETH_funding_*.csv")),
        "Hyperliquid",
        "coin",
    )
    orderly_funding = normalize_funding_rows(
        read_csv(latest("orderly_PERP_ETH_USDC_funding_*.csv")),
        "Orderly",
        "symbol",
    )
    funding_rows = hyper_funding + orderly_funding

    spread_rows = []
    spread_files = choose_spread_files()

    seen_spread_keys: set[tuple[str, str, str]] = set()
    for path in spread_files:
        if path.exists():
            for row in read_csv(path):
                if row.get("status", "ok") == "ok":
                    if "market" in row and "coin" not in row and "symbol" not in row:
                        row["coin"] = row["market"] if row["exchange"] == "Hyperliquid" else ""
                        row["symbol"] = row["market"] if row["exchange"] == "Orderly" else ""
                    normalized = {
                        "exchange": row["exchange"],
                        "coin": row.get("coin", ""),
                        "symbol": row.get("symbol", ""),
                        "timestamp": row.get("timestamp") or row.get("observed_timestamp"),
                        "best_bid": row["best_bid"],
                        "best_ask": row["best_ask"],
                        "mid_price": row["mid_price"],
                        "spread_bps": row["spread_bps"],
                    }
                    key = (
                        normalized["exchange"],
                        normalized["timestamp"],
                        normalized["spread_bps"],
                    )
                    if key not in seen_spread_keys:
                        seen_spread_keys.add(key)
                        spread_rows.append(normalized)

    return volume_rows, funding_rows, spread_rows, spread_files


def filter_to_last_14_days(rows: list[dict[str, Any]], timestamp_key: str) -> list[dict[str, Any]]:
    timestamps = [parse_iso(str(row[timestamp_key])) for row in rows]
    end_time = max(timestamps)
    start_time = end_time - timedelta(days=14)
    return [
        row for row in rows
        if start_time <= parse_iso(str(row[timestamp_key])) <= end_time
    ]


def filter_to_last_hours(
    rows: list[dict[str, Any]],
    timestamp_key: str,
    hours: int,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    timestamps = [parse_iso(str(row[timestamp_key])) for row in rows]
    end_time = max(timestamps)
    start_time = end_time - timedelta(hours=hours)
    return [
        row for row in rows
        if start_time <= parse_iso(str(row[timestamp_key])) <= end_time
    ]


def daily_volume(volume_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in volume_rows:
        key = (row["exchange"], row["date"])
        if key not in grouped:
            grouped[key] = {
                "exchange": row["exchange"],
                "date": row["date"],
                "volume_eth": 0.0,
                "notional_volume_usd": 0.0,
            }
        grouped[key]["volume_eth"] += row["volume_eth"]
        grouped[key]["notional_volume_usd"] += row["notional_volume_usd"]
    return sorted(grouped.values(), key=lambda row: (row["date"], row["exchange"]))


def daily_funding(funding_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in funding_rows:
        grouped[(row["exchange"], row["date"])].append(row["funding_rate"])

    rows = []
    for (exchange, date), rates in grouped.items():
        rows.append(
            {
                "exchange": exchange,
                "date": date,
                "funding_observations": len(rates),
                "daily_cumulative_funding_pct": sum(rates) * 100,
                "avg_funding_rate_pct": mean(rates) * 100,
            }
        )
    return sorted(rows, key=lambda row: (row["date"], row["exchange"]))


def summary_metrics(
    volume_rows: list[dict[str, Any]],
    funding_rows: list[dict[str, Any]],
    spread_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    exchanges = sorted({row["exchange"] for row in volume_rows + funding_rows})
    rows = []
    for exchange in exchanges:
        exchange_volume = [row for row in volume_rows if row["exchange"] == exchange]
        exchange_funding = [row for row in funding_rows if row["exchange"] == exchange]
        exchange_spread = [
            float(row["spread_bps"]) for row in spread_rows if row["exchange"] == exchange
        ]
        rates = [row["funding_rate"] for row in exchange_funding]
        annualized = [row["funding_rate_annualized_pct"] for row in exchange_funding]

        rows.append(
            {
                "exchange": exchange,
                "hourly_volume_rows": len(exchange_volume),
                "funding_rows": len(exchange_funding),
                "spread_samples": len(exchange_spread),
                "total_notional_volume_usd": sum(row["notional_volume_usd"] for row in exchange_volume),
                "avg_hourly_notional_volume_usd": mean(
                    [row["notional_volume_usd"] for row in exchange_volume]
                ) if exchange_volume else math.nan,
                "mean_funding_rate_pct": mean(rates) * 100 if rates else math.nan,
                "median_funding_rate_pct": median(rates) * 100 if rates else math.nan,
                "mean_funding_annualized_pct": mean(annualized) if annualized else math.nan,
                "p90_abs_funding_annualized_pct": percentile([abs(value) for value in annualized], 0.9),
                "positive_funding_share": (
                    sum(1 for value in rates if value > 0) / len(rates)
                    if rates else math.nan
                ),
                "median_spread_bps": median(exchange_spread) if exchange_spread else math.nan,
                "p90_spread_bps": percentile(exchange_spread, 0.9),
            }
        )
    return rows


def spread_sampling_quality(spread_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not spread_rows:
        return []

    timestamps = [parse_iso(str(row["timestamp"])) for row in spread_rows]
    start_time = min(timestamps)
    end_time = max(timestamps)
    window_hours = (end_time - start_time).total_seconds() / 3600

    exchanges = sorted({row.get("exchange", "") for row in spread_rows if row.get("exchange")})
    quality_rows = []
    for exchange in exchanges:
        exchange_rows = [row for row in spread_rows if row.get("exchange") == exchange]
        quality_rows.append(
            {
                "exchange": exchange,
                "sample_window_start": start_time.isoformat(),
                "sample_window_end": end_time.isoformat(),
                "sample_window_hours": window_hours,
                "total_rows": len(exchange_rows),
                "successful_samples": len(exchange_rows),
                "error_rows": 0,
                "success_rate": 1.0 if exchange_rows else math.nan,
            }
        )
    return quality_rows


def main() -> None:
    volume_rows, funding_rows, spread_rows, spread_files = load_inputs()
    volume_rows = filter_to_last_14_days(volume_rows, "timestamp")
    funding_rows = filter_to_last_14_days(funding_rows, "timestamp")
    spread_rows = filter_to_last_hours(spread_rows, "timestamp", SPREAD_WINDOW_HOURS)

    write_csv(
        PROCESSED_DIR / "volume_hourly.csv",
        sorted(volume_rows, key=lambda row: (row["timestamp"], row["exchange"])),
        ["exchange", "market", "timestamp", "date", "volume_eth", "notional_volume_usd", "close"],
    )
    write_csv(
        PROCESSED_DIR / "volume_daily.csv",
        daily_volume(volume_rows),
        ["exchange", "date", "volume_eth", "notional_volume_usd"],
    )
    write_csv(
        PROCESSED_DIR / "funding.csv",
        sorted(funding_rows, key=lambda row: (row["timestamp"], row["exchange"])),
        [
            "exchange",
            "market",
            "timestamp",
            "date",
            "funding_rate",
            "funding_rate_pct",
            "funding_rate_annualized_pct",
            "periods_per_day",
        ],
    )
    write_csv(
        PROCESSED_DIR / "funding_daily.csv",
        daily_funding(funding_rows),
        ["exchange", "date", "funding_observations", "daily_cumulative_funding_pct", "avg_funding_rate_pct"],
    )
    write_csv(
        PROCESSED_DIR / "spread_samples.csv",
        spread_rows,
        ["exchange", "coin", "symbol", "timestamp", "best_bid", "best_ask", "mid_price", "spread_bps"],
    )
    write_csv(
        PROCESSED_DIR / "summary_metrics.csv",
        summary_metrics(volume_rows, funding_rows, spread_rows),
        [
            "exchange",
            "hourly_volume_rows",
            "funding_rows",
            "spread_samples",
            "total_notional_volume_usd",
            "avg_hourly_notional_volume_usd",
            "mean_funding_rate_pct",
            "median_funding_rate_pct",
            "mean_funding_annualized_pct",
            "p90_abs_funding_annualized_pct",
            "positive_funding_share",
            "median_spread_bps",
            "p90_spread_bps",
        ],
    )
    write_csv(
        PROCESSED_DIR / "spread_sampling_quality.csv",
        spread_sampling_quality(spread_rows),
        [
            "exchange",
            "sample_window_start",
            "sample_window_end",
            "sample_window_hours",
            "total_rows",
            "successful_samples",
            "error_rows",
            "success_rate",
        ],
    )

    print(f"Wrote processed tables to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
