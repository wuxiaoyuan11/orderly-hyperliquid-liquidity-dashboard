# Orderly vs Hyperliquid ETH Perp Liquidity Dashboard

This project compares ETH perpetual market quality on Orderly and Hyperliquid using volume, funding, and top-of-book spread data.

## Dashboard

Run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

The dashboard reads the processed CSV files in `data/processed/`.

## Analysis Window

- Historical snapshot date: **2026-06-01**
- Volume and funding window: trailing 14 days ending on **2026-06-01**
- Spread sample: 1-minute top-of-book snapshots from **2026-06-01 11:49 UTC** to **2026-06-04 11:49 UTC**

Volume and funding use historical API data. Spread uses a live sampled top-of-book window because comparable historical best bid/ask snapshots were not available through the same public data path.

## Metrics

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

### Top-of-book spread

Top-of-book spread measures the immediate cost of crossing the best bid and best ask:

```text
mid_price = (best_ask + best_bid) / 2
spread_bps = (best_ask - best_bid) / mid_price * 10000
```

Lower spread indicates lower immediate execution friction for small taker orders. It does not prove full order-book depth or large-order slippage.

## Analysis Framework

The dashboard separates liquidity into complementary market-quality dimensions:

- **Activity scale:** notional volume and participation.
- **Carry pressure:** funding direction, magnitude, and stability.
- **Execution friction:** median and percentile top-of-book spread.
- **Tail behavior:** spread-widening events and p99 spread behavior.

Spread-widening events use a venue-specific **median + 3 x scaled MAD** threshold. This robust threshold is used because spread data is spike-heavy and non-normal; median and MAD are less distorted by extreme values than mean and standard deviation.

## Key Read

Hyperliquid leads on historical activity scale, with much higher 14-day ETH perp notional volume. Orderly leads on typical sampled top-of-book tightness, with materially lower median spread in the sampled window. Funding was positive on both venues, with Orderly showing steadier positive carry pressure.

The overall liquidity profile is mixed: Hyperliquid has stronger flow scale, while Orderly appears competitive on sampled small-order execution quality.

## Project Structure

```text
dashboard/app.py          Streamlit dashboard
data/processed/           Processed CSV files used by the dashboard
report/conclusion.md      Written conclusion
scripts/                  Data collection and processing scripts
requirements.txt          Python dependencies
```
