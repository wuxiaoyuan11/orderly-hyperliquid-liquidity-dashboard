# Orderly vs Hyperliquid ETH Perp Liquidity Case

This repository is a case-task dashboard comparing ETH perpetual market quality on **Orderly** and **Hyperliquid**. The analysis focuses on three requested liquidity dimensions: **volume**, **funding**, and **top-of-book spread**.

**Dashboard:** https://orderly-hyperliquid-liquidity.streamlit.app

## Case Objective

The goal is to evaluate where each venue appears stronger from available public market data:

- **Activity scale:** which venue has more ETH perp trading activity?
- **Carry pressure:** how persistent and volatile is funding?
- **Execution friction:** which venue has tighter top-of-book quotes for small taker orders?
- **Tail behavior:** how often do quoted spreads widen beyond normal conditions?

## Key Findings

- **Hyperliquid leads on activity scale.** It generated about **$10.64B** of 14-day ETH perp notional volume versus about **$249.36M** on Orderly.
- **Orderly leads on typical sampled top-of-book tightness.** In the Jun 1-4 spread sample, Orderly's median top-of-book spread was about **0.053 bps**, versus about **0.531 bps** on Hyperliquid.
- **Funding was positive on both venues.** Orderly showed steadier positive carry pressure, while Hyperliquid funding was more variable.
- **The liquidity profile is mixed.** Hyperliquid has stronger flow scale, while Orderly appears competitive on sampled small-order execution quality.

## Data Windows

- Historical snapshot date: **2026-06-01**
- Volume and funding window: trailing 14 days ending on **2026-06-01**
- Spread sample: 1-minute top-of-book snapshots from **2026-06-01 11:49 UTC** to **2026-06-04 11:49 UTC**

Volume and funding use historical API data. Spread uses a live sampled top-of-book window because comparable historical best bid/ask snapshots were not available through the same public data path.

## Methodology

### Volume

Volume is measured as estimated USD notional turnover from hourly candles:

```text
notional volume = ETH volume * close price
```

This is used as the market activity and flow scale measure.

### Funding

Funding is annualized so venues with different funding intervals can be compared.

- Hyperliquid funding is observed hourly.
- Orderly funding is observed roughly every 8 hours.

Funding is interpreted as directional pressure and carry stability, not as a direct liquidity-depth ranking.

### Top-of-book Spread

Top-of-book spread measures the immediate cost of crossing the best bid and best ask:

```text
mid_price = (best_ask + best_bid) / 2
spread_bps = (best_ask - best_bid) / mid_price * 10000
```

Lower spread indicates lower immediate execution friction for small taker orders. It does not prove full order-book depth or large-order slippage.

### Spread-Widening Events

Spread-widening events use a venue-specific **median + 3 x scaled MAD** threshold:

```text
threshold = median(spread) + 3 * 1.4826 * MAD(spread)
```

MAD means median absolute deviation. This robust threshold is used because spread data is spike-heavy and non-normal; median and MAD are less distorted by extreme values than mean and standard deviation.

## Dashboard Structure

The Streamlit dashboard is organized around:

- **Overview:** headline read on activity, spread tightness, and funding stability.
- **Market Quality:** side-by-side diagnostic checks by liquidity dimension.
- **Volume:** historical activity and cumulative volume.
- **Funding:** annualized funding and daily cumulative funding.
- **Top-of-book Spread:** spread time series, widening events, percentiles, and execution-cost read.
- **Methodology:** data windows, metric definitions, assumptions, and limitations.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

The dashboard reads the processed CSV files in `data/processed/`.

## Repository Structure

```text
dashboard/app.py          Streamlit dashboard
data/processed/           Processed CSV files used by the dashboard
report/conclusion.md      Written conclusion
scripts/                  Data collection and processing scripts
requirements.txt          Python dependencies
```

## Analytical Limitation

This case directly measures volume, funding, and sampled top-of-book spread. It does not measure full order-book depth or simulated price impact for larger orders. A deeper liquidity assessment would require historical order-book depth and slippage analysis for representative taker sizes.
