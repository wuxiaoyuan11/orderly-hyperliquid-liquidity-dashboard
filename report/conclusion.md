# Orderly vs Hyperliquid ETH Perp Liquidity Comparison

**Historical snapshot:** June 1, 2026  
**Volume & funding window:** trailing 14 days ending June 1, 2026  
**Spread sample:** 72.0 hours of 1-minute top-of-book snapshots from June 1, 2026 12:17 UTC to June 4, 2026 12:17 UTC

## Executive Conclusion

Hyperliquid is the stronger venue on **market activity**, while Orderly looks stronger on **typical sampled top-of-book execution friction**. Hyperliquid generated approximately **$10.64B** of ETH perp notional volume over the 14-day historical window, versus **$249.36M** on Orderly, or about **42.7x** higher turnover. This is a clear signal of broader participation and deeper historical trading activity.

Orderly's strongest result is quoted tightness: in the 72.0-hour sample from June 1, 2026 12:17 UTC to June 4, 2026 12:17 UTC, its median top-of-book spread is approximately **0.053 bps**, versus **0.531 bps** on Hyperliquid. This suggests meaningfully lower small-order taker friction at the best bid/ask during the sampled period. The key caveat is that top-of-book spread does not prove deeper liquidity for larger orders; that would require depth and slippage analysis.

The liquidity profile is therefore mixed rather than one-sided: **Hyperliquid is the stronger venue for demonstrated market activity**, while **Orderly's advantage is narrower but still meaningful: tighter observed top-of-book quoting for small orders during the sampled window**. Funding was positive on both venues, with Orderly showing steadier positive carry pressure. This conclusion treats volume, funding, and spread as complementary market-quality signals rather than interchangeable measures of "liquidity."

## Market Quality Read

**Scale favors Hyperliquid.**  
Hyperliquid's much larger 14-day turnover indicates a more active ETH perp market and likely stronger organic flow. This is the clearest area where Hyperliquid leads.

**Top-of-book tightness favors Orderly in the 72.0-hour sample.**  
Orderly's median sampled spread is roughly **90% lower** than Hyperliquid's. For small taker orders, this points to lower immediate execution friction on Orderly during the observed period.

**Funding shows positive ETH long-side pressure on both venues.**  
Orderly's mean annualized funding is approximately **12.10%**, compared with **7.99%** on Hyperliquid. Orderly funding was positive in all observed intervals, while Hyperliquid was positive in about **88.7%** of intervals and occasionally turned negative. Annualized funding standard deviation was approximately **2.77%** on Orderly versus **5.21%** on Hyperliquid, suggesting Orderly had steadier positive carry pressure while Hyperliquid's long/short pressure was more variable. Funding is venue-specific but market-driven, so it is best read as carry pressure rather than a direct liquidity-depth ranking.

Orderly's persistently positive funding should not be interpreted as a clean risk-free arbitrage opportunity. A positive funding rate can invite short-perp/long-spot basis trades, but that trade is constrained by funding-rate uncertainty, execution cost, spread, margin usage, liquidation risk, venue risk, and limited capacity on a lower-volume market. The persistence of positive funding is therefore more consistent with sustained long-side carry pressure and imperfect arbitrage capacity than with a free return left unexploited.

**Tail behavior needs to be separated from typical conditions.**  
Both venues showed brief spread-widening events. Median and p90 spread are therefore better indicators of normal execution quality than max spread. Orderly's normal spread is much tighter, but its p99 tail is wider relative to its own median, so rare quote-widening events should be reviewed separately from typical execution conditions. Hyperliquid's typical spread is higher, but its p99 is less extreme relative to its own median.

Spread-widening events are defined using a venue-specific **median + 3 x scaled MAD** threshold. This is preferred over a mean + 3 standard deviation threshold because spread data is spike-heavy and non-normal; median and MAD are more robust to extreme values. Scaled MAD multiplies median absolute deviation by **1.4826**, making it comparable to standard deviation under a roughly normal distribution while remaining less distorted by outliers. Therefore, the spread conclusion should rely primarily on median and p90 conditions, while treating rare spikes as a resilience risk rather than normal execution cost.

## Implication for Orderly

The most compelling Orderly angle is not that it has more ETH perp activity than Hyperliquid; it does not. The stronger message is that Orderly appears competitive on **market quality at the top of book**, with very tight typical quoted spreads during the 72.0-hour sampled period. The product implication is that Orderly should not yet frame the ETH perp comparison as a headline-volume contest against Hyperliquid. Its stronger narrative is quote efficiency, small-order execution quality, and market-maker performance at the top of book, while continuing to grow volume and broader market participation.

## Limitations and Analytical Extension

Volume and funding are historical 14-day metrics anchored to the case assignment date. Spread is based on the finalized 72.0-hour live 1-minute sample from June 1, 2026 12:17 UTC to June 4, 2026 12:17 UTC because comparable public historical top-of-book data was not available through the same collection path. Historical spread backfills would require historical best bid/ask or order-book snapshots. The current processed spread dataset contains only best bid and best ask, so it cannot show how much size is available behind those quotes or simulate how quickly execution cost rises for larger orders. As a result, large-order slippage cannot be calculated rigorously from the existing data. A deeper liquidity assessment would require 0.1% and 0.5% order-book depth plus simulated price impact for representative ETH perp taker order sizes such as **USD 50k**, **USD 100k**, and **USD 500k**.
