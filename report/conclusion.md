# Orderly vs Hyperliquid ETH Perp Liquidity Comparison

**Historical snapshot:** June 1, 2026  
**Volume & funding window:** trailing 14 days ending June 1, 2026  
**Spread sample:** 72 hours of 1-minute top-of-book snapshots from June 1, 2026 11:49 UTC to June 4, 2026 11:49 UTC

## Executive Conclusion

Hyperliquid is the stronger venue on **market activity**, while Orderly looks stronger on **typical sampled top-of-book execution friction**. Hyperliquid generated approximately **$10.64B** of ETH perp notional volume over the 14-day historical window, versus **$249.36M** on Orderly, or about **42.7x** higher turnover. This is a clear signal of broader participation and deeper historical trading activity.

Orderly's strongest result is quoted tightness: in the Jun 1-4 72-hour sample, its median top-of-book spread is approximately **0.053 bps**, versus **0.531 bps** on Hyperliquid. This suggests meaningfully lower small-order taker friction at the best bid/ask during the sampled period. The key caveat is that top-of-book spread does not prove deeper liquidity for larger orders; that would require depth and slippage analysis.

The liquidity profile is therefore mixed rather than one-sided: **Hyperliquid leads on flow scale**, while **Orderly leads on typical sampled quote tightness**. Funding was positive on both venues, with Orderly showing steadier positive carry pressure. This conclusion treats volume, funding, and spread as complementary market-quality signals rather than interchangeable measures of "liquidity."

## Market Quality Read

**Scale favors Hyperliquid.**  
Hyperliquid's much larger 14-day turnover indicates a more active ETH perp market and likely stronger organic flow. This is the clearest area where Hyperliquid leads.

**Top-of-book tightness favors Orderly in the Jun 1-4 sample.**  
Orderly's median sampled spread is roughly **90% lower** than Hyperliquid's. For small taker orders, this points to lower immediate execution friction on Orderly during the observed period.

**Funding shows positive ETH long-side pressure on both venues.**  
Orderly's mean annualized funding is approximately **12.10%**, compared with **7.99%** on Hyperliquid. Orderly funding was positive in all observed intervals, while Hyperliquid was positive in about **88.7%** of intervals and occasionally turned negative. Annualized funding standard deviation was approximately **2.77%** on Orderly versus **5.21%** on Hyperliquid, suggesting Orderly had steadier positive carry pressure while Hyperliquid's long/short pressure was more variable. Funding is venue-specific but market-driven, so it is best read as carry pressure rather than a direct liquidity-depth ranking.

**Tail behavior needs to be separated from typical conditions.**  
Both venues showed brief spread-widening events. Median and p90 spread are therefore better indicators of normal execution quality than max spread. Orderly's normal spread is much tighter, but its p99 tail is wider relative to its own median, so rare quote-widening events should be reviewed separately from typical execution conditions. Hyperliquid's typical spread is higher, but its p99 is less extreme relative to its own median.

Spread-widening events are defined using a venue-specific **median + 3 x scaled MAD** threshold. This is preferred over a mean + 3 standard deviation threshold because spread data is spike-heavy and non-normal; median and MAD are more robust to extreme values. Scaled MAD multiplies median absolute deviation by **1.4826**, making it comparable to standard deviation under a roughly normal distribution while remaining less distorted by outliers.

## Implication for Orderly

The most compelling Orderly angle is not that it has more ETH perp activity than Hyperliquid; it does not. The stronger message is that Orderly appears competitive on **market quality at the top of book**, with very tight typical quoted spreads during the Jun 1-4 sampled period. For a liquidity/product narrative, this suggests Orderly can position itself around efficient small-order execution quality while continuing to grow volume and broader market participation.

## Limitations and Analytical Extension

Volume and funding are historical 14-day metrics anchored to the case assignment date. Spread is based on the finalized Jun 1-4 72-hour live 1-minute sample because comparable public historical top-of-book data was not available through the same collection path. Historical spread backfills would require historical best bid/ask or order-book snapshots. The next analytical extension would be simulated price impact for representative ETH perp taker order sizes such as **USD 50k**, **USD 100k**, and **USD 500k**, to test whether Orderly's tight top-of-book quote scales into deeper executable liquidity.
