from __future__ import annotations

import argparse
import signal
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from collect_spread_samples import (
    DEFAULT_HYPERLIQUID_COIN,
    DEFAULT_ORDERLY_SYMBOL,
    PROJECT_ROOT,
    ensure_output_header,
    sample_once,
)


DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_START = "2026-06-05T00:00:00"
DEFAULT_END = "2026-06-08T00:00:00"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "spread_samples_20260605_0000_to_20260608_0000_shanghai.csv"
)

SHOULD_STOP = False


def handle_stop_signal(signum: int, frame: Any) -> None:
    global SHOULD_STOP
    SHOULD_STOP = True


signal.signal(signal.SIGINT, handle_stop_signal)
signal.signal(signal.SIGTERM, handle_stop_signal)


def parse_local_datetime(value: str, timezone_name: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed.astimezone(timezone.utc)


def sleep_until(target: datetime) -> None:
    while not SHOULD_STOP:
        remaining = (target - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(30, remaining))


def next_scheduled_time(start: datetime, interval_seconds: int, now: datetime) -> datetime:
    if now <= start:
        return start
    elapsed = (now - start).total_seconds()
    intervals_elapsed = int(elapsed // interval_seconds) + 1
    return start + timedelta(seconds=intervals_elapsed * interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect 1-minute top-of-book spread samples for a fixed wall-clock window."
    )
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--hyperliquid-coin", default=DEFAULT_HYPERLIQUID_COIN)
    parser.add_argument("--orderly-symbol", default=DEFAULT_ORDERLY_SYMBOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mirror-output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_utc = parse_local_datetime(args.start, args.timezone)
    end_utc = parse_local_datetime(args.end, args.timezone)

    if end_utc <= start_utc:
        raise ValueError("--end must be later than --start")

    ensure_output_header(args.output)
    local_tz = ZoneInfo(args.timezone)
    print(f"Spread window sampler output: {args.output}")
    print(f"Window start: {start_utc.astimezone(local_tz).isoformat()} ({start_utc.isoformat()} UTC)")
    print(f"Window end:   {end_utc.astimezone(local_tz).isoformat()} ({end_utc.isoformat()} UTC)")

    now = datetime.now(timezone.utc)
    if now < start_utc:
        print("Waiting for scheduled start...")
        sleep_until(start_utc)
    elif now >= end_utc:
        print("Scheduled window has already ended; nothing to collect.")
        return
    else:
        print("Scheduled window is already in progress; starting at the next interval.")

    scheduled_timestamp = next_scheduled_time(start_utc, args.interval_seconds, datetime.now(timezone.utc))
    sample_id = int((scheduled_timestamp - start_utc).total_seconds() // args.interval_seconds) + 1

    while not SHOULD_STOP and scheduled_timestamp < end_utc:
        sleep_until(scheduled_timestamp)
        if SHOULD_STOP:
            break

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

        scheduled_timestamp += timedelta(seconds=args.interval_seconds)
        sample_id += 1

    print("Window spread sampler stopped.")


if __name__ == "__main__":
    main()
