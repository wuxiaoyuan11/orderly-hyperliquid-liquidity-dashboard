from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

ANALYSIS_SNAPSHOT = "2026-06-01"
HISTORICAL_WINDOW = "Trailing 14 days ending on 2026-06-01"


st.set_page_config(
    page_title="Orderly vs Hyperliquid ETH Liquidity",
    page_icon="",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background: transparent; }
    .insight-card {
        border: 1px solid #e6e8ef;
        border-radius: 8px;
        padding: 18px 18px 16px 18px;
        min-height: 150px;
        background: #ffffff;
    }
    .insight-label {
        font-size: 0.88rem;
        color: #73788a;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .insight-value {
        font-size: 2.6rem;
        line-height: 1.05;
        color: #2f3140;
        font-weight: 650;
        margin-bottom: 10px;
    }
    .insight-note {
        font-size: 0.96rem;
        color: #4f5568;
        line-height: 1.35;
    }
    .takeaway {
        border-left: 4px solid #2f6fed;
        background: #f6f8fc;
        padding: 12px 16px;
        border-radius: 6px;
        color: #32384a;
        margin: 10px 0 20px 0;
        line-height: 1.45;
    }
    .scope-note {
        border-left: 3px solid #9aa3b7;
        background: #fafbfe;
        padding: 10px 14px;
        border-radius: 6px;
        color: #565d70;
        margin: 4px 0 18px 0;
        line-height: 1.42;
        font-size: 0.94rem;
    }
    .score-row {
        border: 1px solid #e6e8ef;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        background: #ffffff;
    }
    .score-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #303344;
        margin-bottom: 4px;
    }
    .score-body {
        font-size: 0.96rem;
        color: #555b6e;
        line-height: 1.4;
    }
    .comparison-row {
        border: 1px solid #e6e8ef;
        border-radius: 8px;
        padding: 16px 18px;
        margin-bottom: 12px;
        background: #ffffff;
    }
    .comparison-title {
        font-size: 1.08rem;
        font-weight: 750;
        color: #303344;
        margin-bottom: 8px;
    }
    .comparison-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1.5fr;
        gap: 14px;
        align-items: start;
    }
    .comparison-label {
        font-size: 0.78rem;
        color: #73788a;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        margin-bottom: 3px;
    }
    .comparison-value {
        font-size: 1.28rem;
        color: #2f3140;
        font-weight: 750;
    }
    .comparison-note {
        color: #555b6e;
        line-height: 1.4;
    }
    .winner-card {
        border: 1px solid #e6e8ef;
        border-radius: 8px;
        padding: 16px 18px;
        min-height: 132px;
        background: #ffffff;
    }
    .winner-label {
        font-size: 0.78rem;
        color: #73788a;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        margin-bottom: 6px;
    }
    .winner-name {
        font-size: 1.8rem;
        line-height: 1.1;
        color: #2f3140;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .winner-read {
        font-size: 0.94rem;
        color: #555b6e;
        line-height: 1.35;
    }
    .winner-bars {
        margin-top: 12px;
    }
    .bar-row {
        display: grid;
        grid-template-columns: 90px 1fr 88px;
        gap: 10px;
        align-items: center;
        margin-top: 7px;
    }
    .bar-label {
        font-size: 0.82rem;
        color: #555b6e;
        font-weight: 700;
    }
    .bar-track {
        height: 9px;
        background: #eef1f7;
        border-radius: 999px;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        background: #2f6fed;
        border-radius: 999px;
    }
    .bar-fill.secondary {
        background: #80c7ff;
    }
    .bar-value {
        font-size: 0.82rem;
        color: #555b6e;
        font-weight: 700;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name
    return pd.read_csv(path)


def format_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def format_pct(value: float) -> str:
    return f"{value:.2f}%"


def format_bps(value: float) -> str:
    return f"{value:.3f} bps"


def format_ratio(value: float) -> str:
    return f"{value:.2f}x"


def insight_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-label">{label}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def takeaway(text: str) -> None:
    st.markdown(f'<div class="takeaway"><strong>Takeaway:</strong> {text}</div>', unsafe_allow_html=True)


def scope_note(text: str) -> None:
    st.markdown(f'<div class="scope-note"><strong>Scope note:</strong> {text}</div>', unsafe_allow_html=True)


def comparison_row(title: str, orderly_value: str, hyper_value: str, read: str) -> None:
    st.markdown(
        f"""
        <div class="comparison-row">
            <div class="comparison-title">{title}</div>
            <div class="comparison-grid">
                <div>
                    <div class="comparison-label">Orderly</div>
                    <div class="comparison-value">{orderly_value}</div>
                </div>
                <div>
                    <div class="comparison-label">Hyperliquid</div>
                    <div class="comparison-value">{hyper_value}</div>
                </div>
                <div>
                    <div class="comparison-label">Read</div>
                    <div class="comparison-note">{read}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def winner_bar_card(
    label: str,
    winner: str,
    read: str,
    orderly_value: str,
    hyper_value: str,
    orderly_width: float,
    hyper_width: float,
) -> None:
    st.markdown(
        f"""
        <div class="winner-card">
            <div class="winner-label">{label}</div>
            <div class="winner-name">{winner}</div>
            <div class="winner-read">{read}</div>
            <div class="winner-bars">
                <div class="bar-row">
                    <div class="bar-label">Orderly</div>
                    <div class="bar-track"><div class="bar-fill secondary" style="width: {orderly_width:.1f}%;"></div></div>
                    <div class="bar-value">{orderly_value}</div>
                </div>
                <div class="bar-row">
                    <div class="bar-label">Hyperliquid</div>
                    <div class="bar-track"><div class="bar-fill" style="width: {hyper_width:.1f}%;"></div></div>
                    <div class="bar-value">{hyper_value}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def spread_quality_row(venue: str, typical: str, tail: str, cost: str, read: str) -> None:
    st.markdown(
        f"""
        <div class="comparison-row">
            <div class="comparison-title">{venue}</div>
            <div class="comparison-grid">
                <div>
                    <div class="comparison-label">Typical</div>
                    <div class="comparison-value">{typical}</div>
                </div>
                <div>
                    <div class="comparison-label">P99 Tail</div>
                    <div class="comparison-value">{tail}</div>
                </div>
                <div>
                    <div class="comparison-label">Execution Read</div>
                    <div class="comparison-note">{read} Estimated half-spread cost per $100k: <strong>{cost}</strong>.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_style(fig):
    fig.update_layout(
        margin=dict(l=20, r=20, t=55, b=30),
        legend_title_text="",
        hovermode="x unified",
    )
    return fig


def build_spread_events(spread_frame: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    events = []
    for exchange, group in spread_frame.sort_values("timestamp").groupby("exchange"):
        threshold = thresholds[exchange]
        current = []
        previous_ts = None

        for row in group.itertuples():
            is_wide = row.spread_bps > threshold
            is_consecutive = (
                previous_ts is not None
                and (row.timestamp - previous_ts).total_seconds() <= 90
            )

            if is_wide and (not current or is_consecutive):
                current.append(row)
            else:
                if current:
                    events.append(
                        {
                            "Exchange": exchange,
                            "Start": current[0].timestamp,
                            "End": current[-1].timestamp,
                            "Duration (min)": len(current),
                            "Max spread (bps)": max(item.spread_bps for item in current),
                            "Avg spread (bps)": sum(item.spread_bps for item in current) / len(current),
                            "Threshold (bps)": threshold,
                        }
                    )
                    current = []
                if is_wide:
                    current = [row]
            previous_ts = row.timestamp

        if current:
            events.append(
                {
                    "Exchange": exchange,
                    "Start": current[0].timestamp,
                    "End": current[-1].timestamp,
                    "Duration (min)": len(current),
                    "Max spread (bps)": max(item.spread_bps for item in current),
                    "Avg spread (bps)": sum(item.spread_bps for item in current) / len(current),
                    "Threshold (bps)": threshold,
                }
            )

    return pd.DataFrame(events)


def spread_thresholds(spread_frame: pd.DataFrame, method: str) -> dict[str, float]:
    thresholds = {}
    for exchange, group in spread_frame.groupby("exchange"):
        series = group["spread_bps"]
        if method == "mean_std":
            thresholds[exchange] = series.mean() + 3 * series.std()
        elif method == "scaled_mad":
            median = series.median()
            mad = (series - median).abs().median()
            thresholds[exchange] = median + 3 * 1.4826 * mad
        else:
            raise ValueError(f"Unknown threshold method: {method}")
    return thresholds


def spread_event_summary(spread_events: pd.DataFrame) -> pd.DataFrame:
    duration_summary = (
        spread_events.groupby("Exchange")
        .agg(
            events=("Duration (min)", "count"),
            samples_above_threshold=("Duration (min)", "sum"),
            one_minute_event_share=("Duration (min)", lambda series: (series == 1).mean()),
            max_duration_min=("Duration (min)", "max"),
            max_spread_bps=("Max spread (bps)", "max"),
            threshold_bps=("Threshold (bps)", "first"),
        )
        .reset_index()
    )
    duration_summary["one_minute_event_share"] = duration_summary[
        "one_minute_event_share"
    ].map(lambda value: format_pct(value * 100))
    duration_summary["max_spread_bps"] = duration_summary["max_spread_bps"].map(format_bps)
    duration_summary["threshold_bps"] = duration_summary["threshold_bps"].map(format_bps)
    return duration_summary.rename(
        columns={
            "events": "Widening events",
            "samples_above_threshold": "Samples above threshold",
            "one_minute_event_share": "One-minute event share",
            "max_duration_min": "Max duration (min)",
            "max_spread_bps": "Max spread",
            "threshold_bps": "Threshold",
        }
    )


summary = load_csv("summary_metrics.csv")
volume_daily = load_csv("volume_daily.csv")
volume_hourly = load_csv("volume_hourly.csv")
funding = load_csv("funding.csv")
funding_daily = load_csv("funding_daily.csv")
spread = load_csv("spread_samples.csv")
spread_quality = load_csv("spread_sampling_quality.csv")

volume_daily["date"] = pd.to_datetime(volume_daily["date"], format="mixed")
volume_hourly["timestamp"] = pd.to_datetime(volume_hourly["timestamp"], format="mixed", utc=True)
funding["timestamp"] = pd.to_datetime(funding["timestamp"], format="mixed", utc=True)
funding_daily["date"] = pd.to_datetime(funding_daily["date"], format="mixed")
spread["timestamp"] = pd.to_datetime(spread["timestamp"], format="mixed", utc=True)
spread_quality["sample_window_start"] = pd.to_datetime(
    spread_quality["sample_window_start"], format="mixed", utc=True
)
spread_quality["sample_window_end"] = pd.to_datetime(
    spread_quality["sample_window_end"], format="mixed", utc=True
)

daily_volume_stats = volume_daily.groupby("exchange")["notional_volume_usd"].agg(
    avg_daily="mean",
    std_daily="std",
    max_daily="max",
    total="sum",
)
daily_volume_stats["cv"] = daily_volume_stats["std_daily"] / daily_volume_stats["avg_daily"]
daily_volume_stats["top_day_share"] = daily_volume_stats["max_daily"] / daily_volume_stats["total"]

funding_deep_stats = funding.groupby("exchange")["funding_rate_annualized_pct"].agg(
    mean="mean",
    std="std",
    median="median",
    minimum="min",
    maximum="max",
)

spread_deep_stats = spread.groupby("exchange")["spread_bps"].agg(
    samples="count",
    median="median",
    p90=lambda series: series.quantile(0.90),
    p95=lambda series: series.quantile(0.95),
    p99=lambda series: series.quantile(0.99),
    maximum="max",
)
spread_deep_stats["p99_to_median"] = spread_deep_stats["p99"] / spread_deep_stats["median"]
spread_deep_stats["share_under_0_1_bps"] = spread.groupby("exchange")["spread_bps"].apply(
    lambda series: (series <= 0.1).mean()
)
spread_deep_stats["share_under_0_6_bps"] = spread.groupby("exchange")["spread_bps"].apply(
    lambda series: (series <= 0.6).mean()
)

spread_start = spread["timestamp"].min()
spread_end = spread["timestamp"].max()
spread_hours = (spread_end - spread_start).total_seconds() / 3600
spread_window_exact = f"{spread_start:%b %-d, %Y %H:%M UTC} to {spread_end:%b %-d, %Y %H:%M UTC}"
SPREAD_WINDOW = f"{spread_hours:.1f}-hour 1-minute top-of-book sample: {spread_window_exact}"
expected_minute_samples = max(1, round(spread_hours * 60))
spread_quality_display = spread_quality.copy()
spread_quality_display["expected_minute_samples"] = expected_minute_samples
spread_quality_display["minute_coverage"] = (
    spread_quality_display["successful_samples"] / expected_minute_samples
)


st.title("Orderly vs Hyperliquid ETH Perp Liquidity")
st.caption(
    f"Snapshot: {ANALYSIS_SNAPSHOT} | Volume & funding: {HISTORICAL_WINDOW} | "
    f"Spread: {SPREAD_WINDOW}"
)

with st.sidebar:
    st.header("Data")
    st.caption("Dashboard reads the processed CSV files included with this project.")

tabs = st.tabs(["Overview", "Market Quality", "Volume", "Funding", "Top-of-book spread", "Methodology"])


with tabs[0]:
    st.subheader("Executive Summary")

    orderly = summary.loc[summary["exchange"] == "Orderly"].iloc[0]
    hyper = summary.loc[summary["exchange"] == "Hyperliquid"].iloc[0]
    volume_ratio = hyper["total_notional_volume_usd"] / orderly["total_notional_volume_usd"]
    spread_reduction = (1 - orderly["median_spread_bps"] / hyper["median_spread_bps"]) * 100
    funding_gap = orderly["mean_funding_annualized_pct"] - hyper["mean_funding_annualized_pct"]
    orderly_funding_vol = funding_deep_stats.loc["Orderly", "std"]
    hyper_funding_vol = funding_deep_stats.loc["Hyperliquid", "std"]

    volume_max = max(orderly["total_notional_volume_usd"], hyper["total_notional_volume_usd"])
    spread_max = max(orderly["median_spread_bps"], hyper["median_spread_bps"])
    funding_vol_max = max(orderly_funding_vol, hyper_funding_vol)

    col1, col2, col3 = st.columns(3)
    with col1:
        winner_bar_card(
            "Activity / flow scale",
            "Hyperliquid leads",
            f"{volume_ratio:.1f}x higher 14-day notional volume.",
            format_usd(orderly["total_notional_volume_usd"]),
            format_usd(hyper["total_notional_volume_usd"]),
            orderly["total_notional_volume_usd"] / volume_max * 100,
            hyper["total_notional_volume_usd"] / volume_max * 100,
        )
    with col2:
        winner_bar_card(
            "Quoted execution cost",
            "Orderly leads",
            f"{spread_reduction:.1f}% lower median spread in the 72.0h sample; lower is better.",
            format_bps(orderly["median_spread_bps"]),
            format_bps(hyper["median_spread_bps"]),
            orderly["median_spread_bps"] / spread_max * 100,
            hyper["median_spread_bps"] / spread_max * 100,
        )
    with col3:
        winner_bar_card(
            "Funding stability",
            "Orderly leads",
            "Lower annualized funding standard deviation; lower is steadier.",
            format_pct(orderly_funding_vol),
            format_pct(hyper_funding_vol),
            orderly_funding_vol / funding_vol_max * 100,
            hyper_funding_vol / funding_vol_max * 100,
        )

    takeaway(
        "Hyperliquid leads on historical activity, while Orderly looks stronger on the 72.0h sampled top-of-book "
        "tightness. Funding is positive on both venues, with Orderly more consistently positive."
    )

    st.markdown("**Final Read**")
    st.markdown(
        f"""
        <div class="score-row">
            <div class="score-title">Hyperliquid is the activity leader</div>
            <div class="score-body">14-day notional volume was <strong>{format_usd(hyper['total_notional_volume_usd'])}</strong> on Hyperliquid versus <strong>{format_usd(orderly['total_notional_volume_usd'])}</strong> on Orderly. This points to a much larger active ETH perp trading base on Hyperliquid.</div>
        </div>
        <div class="score-row">
            <div class="score-title">Orderly is the sampled top-of-book tightness leader</div>
            <div class="score-body">In the 72.0h sample from {spread_window_exact}, median top-of-book spread was <strong>{format_bps(orderly['median_spread_bps'])}</strong> on Orderly versus <strong>{format_bps(hyper['median_spread_bps'])}</strong> on Hyperliquid. This suggests lower sampled small-order taker friction on Orderly, subject to the spread sampling caveat.</div>
        </div>
        <div class="score-row">
            <div class="score-title">Funding shows persistent positive ETH long-side pressure</div>
            <div class="score-body">Mean annualized funding was <strong>{format_pct(orderly['mean_funding_annualized_pct'])}</strong> on Orderly and <strong>{format_pct(hyper['mean_funding_annualized_pct'])}</strong> on Hyperliquid. Orderly was positive in all observed funding intervals; Hyperliquid was positive in about <strong>{hyper['positive_funding_share'] * 100:.1f}%</strong>.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Technical diagnostics"):
        diagnostic = summary[
            [
                "exchange",
                "hourly_volume_rows",
                "funding_rows",
                "spread_samples",
                "positive_funding_share",
                "p90_abs_funding_annualized_pct",
                "p90_spread_bps",
            ]
        ].copy()
        diagnostic["positive_funding_share"] = (diagnostic["positive_funding_share"] * 100).map(format_pct)
        diagnostic["p90_abs_funding_annualized_pct"] = diagnostic[
            "p90_abs_funding_annualized_pct"
        ].map(format_pct)
        diagnostic["p90_spread_bps"] = diagnostic["p90_spread_bps"].map(format_bps)
        st.dataframe(diagnostic, use_container_width=True, hide_index=True)
        st.dataframe(spread_quality_display, use_container_width=True, hide_index=True)


with tabs[1]:
    st.subheader("Liquidity Assessment")
    st.caption("A diagnostic view of scale, stability, execution cost, and tail behavior.")

    h_vol = daily_volume_stats.loc["Hyperliquid"]
    o_vol = daily_volume_stats.loc["Orderly"]
    h_funding = funding_deep_stats.loc["Hyperliquid"]
    o_funding = funding_deep_stats.loc["Orderly"]
    h_spread = spread_deep_stats.loc["Hyperliquid"]
    o_spread = spread_deep_stats.loc["Orderly"]

    takeaway(
        "The liquidity picture is mixed: Hyperliquid has stronger market activity, while Orderly has "
        "better 72.0h sampled top-of-book tightness. The diagnostic checks below test whether those advantages "
        "are broad-based or fragile."
    )

    st.markdown("**Diagnostics by Dimension**")
    comparison_row(
        "1. Scale: market participation",
        format_usd(o_vol["total"]),
        format_usd(h_vol["total"]),
        f"Hyperliquid is {volume_ratio:.1f}x larger by 14-day notional volume, so it clearly leads historical activity.",
    )
    comparison_row(
        "2. Activity stability: top-day concentration",
        format_pct(o_vol["top_day_share"] * 100),
        format_pct(h_vol["top_day_share"] * 100),
        "Both venues are similar, so the volume comparison is not just one abnormal day dominating the sample.",
    )
    comparison_row(
        "3. Carry stability: annualized funding standard deviation",
        format_pct(o_funding["std"]),
        format_pct(h_funding["std"]),
        "Funding is venue-specific but market-driven. Hyperliquid funding moved more, while Orderly funding was steadier and more persistently positive.",
    )
    comparison_row(
        "4. Typical execution friction: 72.0h median top-of-book spread",
        format_bps(o_spread["median"]),
        format_bps(h_spread["median"]),
        "Orderly has the tighter sampled top-of-book quote, which is favorable for small taker orders.",
    )
    comparison_row(
        "5. Tail behavior: p99 / median spread",
        format_ratio(o_spread["p99_to_median"]),
        format_ratio(h_spread["p99_to_median"]),
        "Orderly's normal spread is much tighter, but its p99 / median ratio shows rare tail widening. Hyperliquid's typical spread is higher but its p99 is less extreme relative to its own median.",
    )

    with st.expander("Framework note"):
        st.write(
            "Institutional liquidity dashboards typically separate activity, execution cost, and resilience. "
            "This page follows that structure so the venue comparison does not collapse into a simple "
            "volume leaderboard. Volume, funding, and top-of-book spread are treated as complementary signals; "
            "full depth and large-order slippage would require additional order-book analysis."
        )


with tabs[2]:
    st.subheader("Volume")
    st.caption("Question answered: which venue had more ETH perp activity over the historical window?")

    v1, v2, v3 = st.columns(3)
    with v1:
        insight_card("Hyperliquid 14d Volume", format_usd(hyper["total_notional_volume_usd"]), "Higher turnover indicates broader historical market participation.")
    with v2:
        insight_card("Orderly 14d Volume", format_usd(orderly["total_notional_volume_usd"]), "Orderly is smaller by turnover in this ETH perp window.")
    with v3:
        insight_card("Volume Gap", f"{volume_ratio:.1f}x", "Hyperliquid's ETH perp turnover was materially larger.")

    takeaway("Hyperliquid is the clear leader on activity. This is the strongest evidence that its ETH perp market has deeper historical participation.")

    fig_daily = px.bar(
        volume_daily,
        x="date",
        y="notional_volume_usd",
        color="exchange",
        barmode="group",
        labels={"date": "Date", "notional_volume_usd": "Daily notional volume (USD)", "exchange": "Exchange"},
        title="Daily ETH perp notional volume",
    )
    st.plotly_chart(apply_chart_style(fig_daily), use_container_width=True)

    cumulative = volume_daily.sort_values(["exchange", "date"]).copy()
    cumulative["cumulative_notional_volume_usd"] = cumulative.groupby("exchange")[
        "notional_volume_usd"
    ].cumsum()

    fig_cumulative = px.line(
        cumulative,
        x="date",
        y="cumulative_notional_volume_usd",
        color="exchange",
        markers=True,
        labels={
            "date": "Date",
            "cumulative_notional_volume_usd": "Cumulative notional volume (USD)",
            "exchange": "Exchange",
        },
        title="Cumulative notional volume",
    )
    st.plotly_chart(apply_chart_style(fig_cumulative), use_container_width=True)


with tabs[3]:
    st.subheader("Funding")
    st.caption("Question answered: how persistent and volatile was long/short pressure?")

    f1, f2, f3 = st.columns(3)
    with f1:
        insight_card("Orderly Mean Annualized", format_pct(orderly["mean_funding_annualized_pct"]), "Consistently positive across observed intervals.")
    with f2:
        insight_card("Hyperliquid Mean Annualized", format_pct(hyper["mean_funding_annualized_pct"]), "Positive on average but more variable.")
    with f3:
        insight_card("Positive Funding Share", f"{orderly['positive_funding_share'] * 100:.1f}% / {hyper['positive_funding_share'] * 100:.1f}%", "Orderly / Hyperliquid share of intervals with positive funding.")

    takeaway("Both venues showed positive ETH long-side pressure. Orderly was more consistently positive, while Hyperliquid had more frequent negative or low-funding episodes.")

    fig_funding = px.line(
        funding,
        x="timestamp",
        y="funding_rate_annualized_pct",
        color="exchange",
        labels={
            "timestamp": "Timestamp",
            "funding_rate_annualized_pct": "Annualized funding (%)",
            "exchange": "Exchange",
        },
        title="Funding rate, annualized",
    )
    fig_funding.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(apply_chart_style(fig_funding), use_container_width=True)

    fig_daily_funding = px.bar(
        funding_daily,
        x="date",
        y="daily_cumulative_funding_pct",
        color="exchange",
        barmode="group",
        labels={
            "date": "Date",
            "daily_cumulative_funding_pct": "Daily cumulative funding (%)",
            "exchange": "Exchange",
        },
        title="Daily cumulative funding",
    )
    st.plotly_chart(apply_chart_style(fig_daily_funding), use_container_width=True)

    with st.expander("Funding metric note"):
        st.write(
            "Daily cumulative funding approximates the daily carry paid or received by a trader who "
            "held a perp position through that day's funding intervals."
        )


with tabs[4]:
    st.subheader("Top-of-book Spread")
    st.caption(f"Question answered: what was small-order execution friction during the 72.0h top-of-book sample from {spread_window_exact}?")

    s1, s2, s3 = st.columns(3)
    with s1:
        insight_card("Orderly Median Spread", format_bps(orderly["median_spread_bps"]), "Tighter best bid/ask during the live sample.")
    with s2:
        insight_card("Hyperliquid Median Spread", format_bps(hyper["median_spread_bps"]), "Wider typical top-of-book spread in the sample.")
    with s3:
        insight_card("Orderly Median Advantage", f"{spread_reduction:.1f}% lower", "Lower spread implies lower small-order taker friction.")

    takeaway("Orderly's 72.0h sampled top-of-book was materially tighter on a typical basis, but this should not be overstated as full-depth liquidity or large-order slippage.")

    fig_spread = px.line(
        spread,
        x="timestamp",
        y="spread_bps",
        color="exchange",
        labels={"timestamp": "Timestamp", "spread_bps": "Spread (bps)", "exchange": "Exchange"},
        title=f"Top-of-book spread over 72.0h sampled window ({spread_start:%b %-d} to {spread_end:%b %-d}, 2026 UTC)",
    )
    st.plotly_chart(apply_chart_style(fig_spread), use_container_width=True)

    st.caption(
        "Short spikes represent moments when best bid/ask widened. Median and p90 are more useful "
        "than max for typical execution quality."
    )

    st.markdown("**Spike Duration Summary**")
    scope_note(
        "Widening events use a robust threshold: median + 3 x scaled MAD for each venue's 72.0h spread distribution. MAD means median absolute deviation; scaled MAD multiplies MAD by 1.4826 so it is comparable to standard deviation under a roughly normal distribution. This threshold is preferred over mean + 3 standard deviations because spread data is spike-heavy and non-normal, so mean and standard deviation can be distorted by extreme values."
    )
    method_thresholds = spread_thresholds(spread, "scaled_mad")
    method_events = build_spread_events(spread, method_thresholds)
    st.dataframe(spread_event_summary(method_events), use_container_width=True, hide_index=True)
    fig_events = px.scatter(
        method_events,
        x="Start",
        y="Max spread (bps)",
        color="Exchange",
        size="Duration (min)",
        hover_data=["End", "Duration (min)", "Avg spread (bps)", "Threshold (bps)"],
        labels={"Start": "Event start", "Max spread (bps)": "Max spread (bps)"},
        title="Spread-widening events: median + 3 scaled MAD threshold",
    )
    st.plotly_chart(apply_chart_style(fig_events), use_container_width=True)
    st.caption(
        "Each dot is a grouped spread-widening event above the robust threshold, not a single raw minute. "
        "The line chart shows every sampled minute; this event chart compresses consecutive widened minutes "
        "into one dot, where y-axis is the event's maximum spread and dot size is event duration in minutes."
    )

    st.markdown("**Spread Percentiles**")
    percentile_rows = []
    for exchange, group in spread.groupby("exchange"):
        for label, quantile in [("Median", 0.50), ("P90", 0.90), ("P95", 0.95), ("P99", 0.99)]:
            percentile_rows.append(
                {
                    "Exchange": exchange,
                    "Percentile": label,
                    "Spread (bps)": group["spread_bps"].quantile(quantile),
                }
            )
    spread_percentiles = pd.DataFrame(percentile_rows)
    fig_percentiles = px.bar(
        spread_percentiles,
        x="Percentile",
        y="Spread (bps)",
        color="Exchange",
        barmode="group",
        text=spread_percentiles["Spread (bps)"].map(format_bps),
        title=f"Spread percentiles over 72.0h sample ({spread_start:%b %-d} to {spread_end:%b %-d}, 2026 UTC)",
    )
    fig_percentiles.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(apply_chart_style(fig_percentiles), use_container_width=True)

    spread_stats = (
        spread.groupby("exchange")["spread_bps"]
        .agg(
            samples="count",
            median="median",
            mean="mean",
            p90=lambda series: series.quantile(0.90),
            p95=lambda series: series.quantile(0.95),
            p99=lambda series: series.quantile(0.99),
            maximum="max",
        )
        .reset_index()
    )
    spread_stats["estimated_cost_per_100k_usd"] = (
        spread.groupby("exchange")["spread_bps"].median().values / 2 / 10_000 * 100_000
    )
    for column in ["median", "mean", "p90", "p95", "p99", "maximum"]:
        spread_stats[column] = spread_stats[column].map(format_bps)
    spread_stats["estimated_cost_per_100k_usd"] = spread_stats[
        "estimated_cost_per_100k_usd"
    ].map(lambda value: f"${value:.2f}")
    spread_stats = spread_stats.rename(
        columns={
            "exchange": "Exchange",
            "samples": "Samples",
            "median": "Median",
            "mean": "Mean",
            "p90": "P90",
            "p95": "P95",
            "p99": "P99",
            "maximum": "Max",
            "estimated_cost_per_100k_usd": "Half-spread cost per $100k",
        }
    )
    st.markdown("**Spread quality read**")
    for _, row in spread_stats.iterrows():
        if row["Exchange"] == "Orderly":
            read = "Typical quoted cost is very low, but the p99 tail shows rare widening events that should be reviewed separately from normal conditions."
        else:
            read = "Typical quoted cost is higher, while tail widening is less extreme relative to its own median than Orderly's rare spike events."
        spread_quality_row(
            row["Exchange"],
            row["Median"],
            row["P99"],
            row["Half-spread cost per $100k"],
            read,
        )

    with st.expander("Spread statistics table"):
        st.dataframe(spread_stats, use_container_width=True, hide_index=True)

    outlier_thresholds = spread.groupby("exchange")["spread_bps"].quantile(0.99).to_dict()
    outliers = spread[
        spread.apply(lambda row: row["spread_bps"] >= outlier_thresholds[row["exchange"]], axis=1)
    ].sort_values("spread_bps", ascending=False)
    with st.expander("Largest observed spread events"):
        st.dataframe(
            outliers[["timestamp", "exchange", "best_bid", "best_ask", "mid_price", "spread_bps"]]
            .head(10),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Sampling coverage"):
        q1, q2, q3 = st.columns(3)
        sample_hours = spread_quality["sample_window_hours"].max()
        total_success = int(spread_quality["successful_samples"].sum())
        avg_minute_coverage = spread_quality_display["minute_coverage"].mean()
        with q1:
            insight_card("Sample Window", f"{sample_hours:.1f}h", f"{spread_start:%Y-%m-%d %H:%M UTC} to {spread_end:%Y-%m-%d %H:%M UTC}.")
        with q2:
            insight_card("Successful Samples", f"{total_success:,}", "Successful top-of-book observations across both venues.")
        with q3:
            insight_card("Avg Minute Coverage", format_pct(avg_minute_coverage * 100), "Observed snapshots divided by expected 1-minute slots; missing minutes are excluded from spread stats.")
        st.dataframe(spread_quality_display, use_container_width=True, hide_index=True)


with tabs[5]:
    st.subheader("Data & Assumptions")
    st.markdown(
        """
        **Scope**

        This dashboard compares Orderly `PERP_ETH_USDC` and Hyperliquid `ETH` perpetual markets using
        the three requested liquidity metrics: volume, funding, and top-of-book spread.

        **Time windows**

        - Volume and funding use the trailing 14-day window ending on **2026-06-01**, the case assignment date.
        - Top-of-book spread uses 1-minute live snapshots from **2026-06-01 12:17 UTC** to **2026-06-04 12:17 UTC**.
        - Spread statistics include observed snapshots only; missing minute slots are excluded.

        **Volume**

        Volume is measured as estimated USD notional turnover from hourly candles:
        `ETH volume * close price`. This is used as the activity/participation measure.

        **Funding**

        Funding is annualized so venues with different funding intervals can be compared. Hyperliquid
        funding is observed hourly; Orderly funding is observed roughly every 8 hours. Funding is venue-specific
        but market-driven: each exchange defines the mechanism, while trader positioning and perp-index premium
        determine the realized rate. It is interpreted as directional pressure/carry, not as a simple
        "higher is better" liquidity metric.

        **Top-of-book spread**

        Spread is calculated from best bid and best ask:

        `spread_bps = (best_ask - best_bid) / ((best_ask + best_bid) / 2) * 10000`

        Lower spread means lower immediate execution cost for small taker orders. The half-spread cost
        estimates the cost of crossing half the bid/ask spread for a given notional size. Historical spread
        backfills require historical best bid/ask or order-book snapshots; those were not available through
        the same public data path used for volume and funding.

        **Analytical framing**

        The dashboard follows institutional liquidity-analysis logic: volume alone is not enough.
        Activity, execution friction, carry pressure, and tail behavior are assessed separately.

        **Limitation and next step**

        This case directly measures volume, funding, and the 72.0h sampled top-of-book spread. It does not
        measure full order book depth or simulated slippage for larger orders because the processed spread
        dataset contains best bid/ask observations rather than full order-book levels. A deeper liquidity
        assessment would require 0.1% and 0.5% depth plus price-impact analysis for representative ETH perp
        taker order sizes such as USD 50k, USD 100k, and USD 500k.
        """
    )
