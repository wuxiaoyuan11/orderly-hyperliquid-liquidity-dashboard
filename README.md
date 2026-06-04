# Orderly vs Hyperliquid ETH Liquidity Case

This project compares ETH perpetual liquidity on Orderly and Hyperliquid over the last 14 days.

## Deliverables

- Dashboard: visual comparison of volume, funding, and top-of-book spread.
- One-page conclusion: concise interpretation of which venue looks stronger by metric.

## Project Structure

```text
data/
  raw/          API responses or lightly normalized raw pulls.
  processed/    Clean tables used by the dashboard and report.
scripts/
  fetch_hyperliquid.py
  fetch_orderly.py
  process_data.py
dashboard/
  app.py
report/
  conclusion.md
```

## Metrics

## Analysis Window

This case uses **Option A**: the historical window is anchored to the case assignment date.

- Data snapshot date: 2026-06-01.
- Volume and funding window: trailing 14 days ending on 2026-06-01.
- Spread sampling window: 1-minute top-of-book snapshots collected after the case was assigned.

This avoids changing the historical analysis every day during the case preparation period. The spread window is documented separately because accessible public APIs provide real-time top-of-book data, not a full historical top-of-book archive.

### Volume

Volume measures trading activity. For comparison, we prefer notional volume in USD terms rather than ETH units, because notional volume reflects actual market turnover.

### Funding

Funding is the recurring payment between long and short perpetual futures traders. Positive funding usually means longs pay shorts, while negative funding means shorts pay longs. Stable and moderate funding can indicate a healthier, less one-sided market.

### Top-of-book spread

Top-of-book spread measures the immediate cost of crossing the best bid and best ask:

```text
spread_bps = (best_ask - best_bid) / mid_price * 10000
mid_price = (best_ask + best_bid) / 2
```

Lower spread means lower immediate execution cost for a small taker order.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Dashboard

Refresh processed data before opening the dashboard:

```bash
python scripts/process_data.py
streamlit run dashboard/app.py
```

For GitHub and link-style deployment steps, see [DEPLOYMENT.md](DEPLOYMENT.md).

## First Data Pull

```bash
python scripts/fetch_hyperliquid.py
python scripts/fetch_orderly.py
python scripts/process_data.py
```

The processed comparison tables are written to `data/processed/`.

## Spread Sampling

Top-of-book spread is real-time order book data, so the project includes a sampler that appends one row per venue on every interval:

```bash
python scripts/collect_spread_samples.py
```

By default it samples every 60 seconds and writes to `data/raw/spread_samples_1m.csv`.

In the current macOS background setup, the live LaunchAgent writes to:

```text
/private/tmp/orderly-spread-sampler/spread_samples_1m.csv
```

To copy the live file back into the project folder:

```bash
python scripts/sync_spread_samples.py
```

This creates:

```text
data/raw/spread_samples_1m_live.csv
```

For a short test:

```bash
python scripts/collect_spread_samples.py --duration-minutes 5
```

For the final fixed 72-hour window from **2026-06-05 00:00** to **2026-06-08 00:00 Asia/Shanghai**, use:

```bash
python scripts/collect_spread_window.py
```

This writes:

```text
data/raw/spread_samples_20260605_0000_to_20260608_0000_shanghai.csv
```

After collecting samples, refresh the processed tables:

```bash
python scripts/process_data.py
```

## Current Data Notes

- Hyperliquid funding is hourly, so annualized funding uses about 24 funding periods per day.
- Orderly funding is 8-hourly, so annualized funding uses about 3 funding periods per day.
- Current spread samples are point-in-time snapshots. For a stronger final case, collect more spread samples over the next few days and describe the sampling window in the methodology.

## Analysis Framework

The dashboard uses a market quality framework inspired by institutional crypto liquidity analytics:

- **Scale:** notional volume and turnover.
- **Carry pressure:** funding direction, magnitude, and stability.
- **Execution friction:** top-of-book spread and estimated half-spread cost.
- **Resilience:** p90/p99 spread and brief spread-widening events.

This structure is informed by public frameworks from Kaiko exchange ranking, Amberdata liquidity analytics, and Coin Metrics/CoinMarketCap liquidity methodology. The case directly measures volume, funding, and top-of-book spread; larger-order depth and slippage are listed as the next analytical extension.
