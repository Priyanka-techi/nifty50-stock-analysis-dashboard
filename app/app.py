"""
app/app.py  —  Nifty 50 Stock Performance Dashboard
Run:  streamlit run app/app.py
"""

import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty 50 Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── load data ─────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "cleaned_stock_data.csv")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    
    # Calculate daily_return if missing
    if "daily_return" not in df.columns:
        df = df.sort_values(["ticker", "date"])
        df["daily_return"] = df.groupby("ticker")["close"].pct_change() * 100
        df["daily_return"] = df["daily_return"].fillna(0)
    
    # Create month columns if missing
    if "month" not in df.columns:
        df["month"] = df["date"].dt.month
        df["month_name"] = df["date"].dt.strftime("%B")
        df["month_num"] = df["date"].dt.month
    
    # Ensure numeric columns are properly typed
    numeric_cols = ["open", "high", "low", "close", "volume", "daily_return"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df

df = load_data()

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #1a237e, #0d47a1);
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        margin-bottom: 16px;
    ">
        <span style="font-size: 2rem;">📈</span><br>
        <span style="color: #ffffff; font-size: 1.1rem; font-weight: 700; letter-spacing: 1px;">
            NIFTY 50
        </span><br>
        <span style="color: #90caf9; font-size: 0.75rem; letter-spacing: 2px;">
            STOCK DASHBOARD
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Debug info in sidebar
st.sidebar.markdown("---")
st.sidebar.caption(f"📊 Total records: {len(df):,}")
st.sidebar.caption(f"📈 Unique stocks: {df['ticker'].nunique()}")
st.sidebar.caption(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")

st.sidebar.title("Filters")

all_sectors = sorted(df["Sector"].dropna().unique())
if len(all_sectors) == 0:
    st.error("No sectors found in data. Please check your CSV file.")
    st.stop()

sel_sectors = st.sidebar.multiselect("Sector", all_sectors, default=all_sectors)

if len(sel_sectors) == 0:
    st.warning("Please select at least one sector.")
    st.stop()

all_tickers = sorted(df[df["Sector"].isin(sel_sectors)]["ticker"].unique())
sel_tickers = st.sidebar.multiselect("Stock (for detail views)", all_tickers,
                                     default=all_tickers[:min(5, len(all_tickers))])

date_min = df["date"].min().date()
date_max = df["date"].max().date()
date_range = st.sidebar.date_input("Date Range",
                                    value=(date_min, date_max),
                                    min_value=date_min,
                                    max_value=date_max)

# Apply filters
if len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = df["date"].min(), df["date"].max()

dff = df[
    df["Sector"].isin(sel_sectors) &
    (df["date"] >= start_date) &
    (df["date"] <= end_date)
].copy()

# Check if data exists after filtering
if len(dff) == 0:
    st.error("⚠️ No data available for the selected filters. Please check:")
    st.error(f"- Sectors selected: {sel_sectors}")
    st.error(f"- Date range: {start_date.date()} to {end_date.date()}")
    st.error(f"- Available dates in data: {df['date'].min().date()} to {df['date'].max().date()}")
    st.stop()

# ── title ──────────────────────────────────────────────────────────────────────
st.title("📈 Nifty 50 Stock Performance Dashboard")
st.caption(f"Data: {start_date.date()} → {end_date.date()}  |  "
           f"{dff['ticker'].nunique()} stocks  |  {len(dff):,} trading records")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — KPI SUMMARY CARDS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📊 Market Summary")

# Yearly return per stock
first_last = (
    dff.groupby("ticker")
       .agg(first_close=("close", "first"), last_close=("close", "last"))
       .reset_index()
)
first_last["yearly_return"] = (
    (first_last["last_close"] - first_last["first_close"])
    / first_last["first_close"] * 100
)

green_stocks = (first_last["yearly_return"] > 0).sum()
red_stocks   = (first_last["yearly_return"] <= 0).sum()
avg_price    = dff["close"].mean()
avg_volume   = dff["volume"].mean()
best_return  = first_last["yearly_return"].max() if len(first_last) > 0 else 0
worst_return = first_last["yearly_return"].min() if len(first_last) > 0 else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("🟢 Green Stocks",  f"{green_stocks}")
c2.metric("🔴 Red Stocks",    f"{red_stocks}")
c3.metric("Avg Close Price",  f"₹{avg_price:,.2f}")
c4.metric("Avg Daily Volume", f"{avg_volume:,.0f}")
c5.metric("Best Return",      f"{best_return:.1f}%")
c6.metric("Worst Return",     f"{worst_return:.1f}%")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — TOP 10 GREEN / RED
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🏆 Top 10 Green vs Red Stocks (Yearly Return)")

if len(first_last) > 0:
    top10_green = first_last.nlargest(10, "yearly_return")
    top10_red   = first_last.nsmallest(10, "yearly_return")

    col_g, col_r = st.columns(2)

    with col_g:
        if len(top10_green) > 0:
            fig_green = px.bar(
                top10_green.sort_values("yearly_return"),
                x="yearly_return", y="ticker", orientation="h",
                color="yearly_return",
                color_continuous_scale=["#00c853", "#1b5e20"],
                labels={"yearly_return": "Return (%)", "ticker": "Stock"},
                title="Top 10 Gainers",
                text=top10_green.sort_values("yearly_return")["yearly_return"].map(lambda x: f"{x:.1f}%"),
            )
            fig_green.update_layout(coloraxis_showscale=False, height=400)
            st.plotly_chart(fig_green, use_container_width=True)
        else:
            st.info("No gainers data available")

    with col_r:
        if len(top10_red) > 0:
            fig_red = px.bar(
                top10_red.sort_values("yearly_return", ascending=False),
                x="yearly_return", y="ticker", orientation="h",
                color="yearly_return",
                color_continuous_scale=["#b71c1c", "#ef9a9a"],
                labels={"yearly_return": "Return (%)", "ticker": "Stock"},
                title="Top 10 Losers",
                text=top10_red.sort_values("yearly_return", ascending=False)["yearly_return"].map(lambda x: f"{x:.1f}%"),
            )
            fig_red.update_layout(coloraxis_showscale=False, height=400)
            st.plotly_chart(fig_red, use_container_width=True)
        else:
            st.info("No losers data available")
else:
    st.warning("No data available for return calculations")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — VOLATILITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚡ Volatility Analysis (Top 10 Most Volatile Stocks)")

if "daily_return" in dff.columns and len(dff) > 0:
    volatility = (
        dff.groupby("ticker")["daily_return"]
           .std()
           .reset_index()
           .rename(columns={"daily_return": "volatility"})
           .dropna()
    )
    
    if len(volatility) > 0:
        top10_vol = volatility.nlargest(10, "volatility").sort_values("volatility")
        
        fig_vol = px.bar(
            top10_vol, x="ticker", y="volatility",
            color="volatility",
            color_continuous_scale="OrRd",
            labels={"volatility": "Std Dev of Daily Returns (%)", "ticker": "Stock"},
            title="Top 10 Most Volatile Nifty 50 Stocks",
            text=top10_vol["volatility"].map(lambda x: f"{x:.2f}%"),
        )
        fig_vol.update_traces(textposition="outside")
        fig_vol.update_layout(coloraxis_showscale=False, height=420)
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No volatility data available")
else:
    st.info("Daily return data not available for volatility calculation")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CUMULATIVE RETURN (Top 5)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📈 Cumulative Return — Top 5 Performing Stocks")

if len(first_last) > 0:
    top5_tickers = first_last.nlargest(5, "yearly_return")["ticker"].tolist()
    cum_df = dff[dff["ticker"].isin(top5_tickers)].copy()
    
    if len(cum_df) > 0:
        cum_df.sort_values(["ticker", "date"], inplace=True)
        
        def calc_cumulative_return(grp):
            grp = grp.copy()
            grp["cum_return"] = (1 + grp["daily_return"].fillna(0) / 100).cumprod() - 1
            grp["cum_return"] *= 100
            return grp
        
        cum_df = cum_df.groupby("ticker", group_keys=False).apply(calc_cumulative_return)
        
        fig_cum = px.line(
            cum_df, x="date", y="cum_return", color="ticker",
            labels={"cum_return": "Cumulative Return (%)", "date": "Date", "ticker": "Stock"},
            title="Cumulative Return of Top 5 Stocks",
        )
        fig_cum.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig_cum, use_container_width=True)
    else:
        st.info("No cumulative return data available")
else:
    st.info("No performance data available")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — SECTOR-WISE PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🏭 Sector-wise Average Yearly Return")

if len(first_last) > 0 and "Sector" in dff.columns:
    sector_perf = (
        first_last
        .merge(dff[["ticker", "Sector"]].drop_duplicates(), on="ticker", how="left")
        .groupby("Sector")["yearly_return"]
        .mean()
        .reset_index()
        .sort_values("yearly_return", ascending=False)
    )
    
    if len(sector_perf) > 0:
        sector_perf["color"] = sector_perf["yearly_return"].apply(
            lambda x: "#00c853" if x >= 0 else "#d50000"
        )
        
        fig_sec = px.bar(
            sector_perf, x="Sector", y="yearly_return",
            color="yearly_return",
            color_continuous_scale=["#d50000", "#ffab40", "#00c853"],
            labels={"yearly_return": "Avg Yearly Return (%)", "Sector": "Sector"},
            title="Average Yearly Return by Sector",
            text=sector_perf["yearly_return"].map(lambda x: f"{x:.1f}%"),
        )
        fig_sec.update_traces(textposition="outside")
        fig_sec.update_layout(coloraxis_showscale=False, height=430, xaxis_tickangle=-30)
        st.plotly_chart(fig_sec, use_container_width=True)
    else:
        st.info("No sector performance data available")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — CORRELATION HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🔗 Stock Price Correlation Heatmap")
st.caption("Based on daily closing prices. Use sidebar ticker filter to select stocks.")

heat_tickers = sel_tickers if len(sel_tickers) >= 2 else all_tickers[:min(15, len(all_tickers))]

if len(heat_tickers) >= 2:
    pivot = (
        dff[dff["ticker"].isin(heat_tickers)]
        .pivot_table(index="date", columns="ticker", values="close")
        .dropna()
    )
    
    if len(pivot) > 0 and len(pivot.columns) >= 2:
        corr = pivot.corr()
        
        fig_heat = px.imshow(
            corr,
            color_continuous_scale="RdYlGn",
            zmin=-1, zmax=1,
            title="Correlation Matrix of Closing Prices",
            aspect="auto",
            text_auto=".2f",
        )
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.warning("Insufficient data for correlation heatmap. Try selecting different stocks or date range.")
else:
    st.info("Select at least 2 stocks in the sidebar to see correlation heatmap.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — TOP 5 GAINERS & LOSERS (MONTH-WISE)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📅 Monthly Top 5 Gainers & Losers")

if "month" in dff.columns and len(dff) > 0:
    monthly_return = (
        dff.groupby(["ticker", "month", "month_name", "month_num"])
           .agg(first_close=("close", "first"), last_close=("close", "last"))
           .reset_index()
    )
    monthly_return["monthly_return"] = (
        (monthly_return["last_close"] - monthly_return["first_close"])
        / monthly_return["first_close"] * 100
    )
    
    months_sorted = (
        monthly_return[["month", "month_name", "month_num"]]
        .drop_duplicates()
        .sort_values(["month_num"])
        ["month"].tolist()
    )
    
    # 2 columns layout
    for i in range(0, len(months_sorted), 2):
        cols = st.columns(2)
        for j, month_key in enumerate(months_sorted[i:i+2]):
            month_df = monthly_return[monthly_return["month"] == month_key]
            if len(month_df) > 0:
                month_label = month_df["month_name"].iloc[0]
                top5    = month_df.nlargest(5, "monthly_return")
                bottom5 = month_df.nsmallest(5, "monthly_return")
                combined = pd.concat([top5, bottom5])
                combined["color"] = combined["monthly_return"].apply(
                    lambda x: "Gainer" if x >= 0 else "Loser"
                )
                fig_m = px.bar(
                    combined.sort_values("monthly_return"),
                    x="monthly_return", y="ticker", orientation="h",
                    color="color",
                    color_discrete_map={"Gainer": "#00c853", "Loser": "#d50000"},
                    labels={"monthly_return": "Return (%)", "ticker": ""},
                    title=f"{month_label}",
                    text=combined.sort_values("monthly_return")["monthly_return"].map(
                        lambda x: f"{x:.1f}%"
                    ),
                )
                fig_m.update_traces(textposition="outside")
                fig_m.update_layout(height=380, showlegend=False,
                                    margin=dict(l=10, r=30, t=40, b=10))
                with cols[j]:
                    st.plotly_chart(fig_m, use_container_width=True)
            else:
                with cols[j]:
                    st.info(f"No data for month {month_key}")
else:
    st.info("Monthly data not available")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — INDIVIDUAL STOCK CANDLESTICK
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🕯️ Individual Stock — Candlestick Chart")

if len(dff["ticker"].unique()) > 0:
    selected_stock = st.selectbox("Choose a stock", sorted(dff["ticker"].unique()))
    stock_df = dff[dff["ticker"] == selected_stock].sort_values("date")
    
    if len(stock_df) > 0:
        fig_candle = go.Figure(data=[go.Candlestick(
            x=stock_df["date"],
            open=stock_df["open"],
            high=stock_df["high"],
            low=stock_df["low"],
            close=stock_df["close"],
            name=selected_stock,
        )])
        fig_candle.update_layout(
            title=f"{selected_stock} — Candlestick Chart",
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            height=500,
            xaxis_rangeslider_visible=True,
        )
        st.plotly_chart(fig_candle, use_container_width=True)
        
        # volume bar below
        fig_vol_bar = px.bar(stock_df, x="date", y="volume",
                             title=f"{selected_stock} — Daily Volume",
                             labels={"volume": "Volume", "date": "Date"})
        fig_vol_bar.update_layout(height=250)
        st.plotly_chart(fig_vol_bar, use_container_width=True)
    else:
        st.warning(f"No data available for {selected_stock}")
else:
    st.warning("No stock data available")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption("Nifty 50 Stock Analysis Dashboard · Built with Streamlit & Plotly")
