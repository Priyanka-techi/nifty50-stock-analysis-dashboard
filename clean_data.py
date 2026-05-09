"""
Step 2: clean_data.py
Reads master_stock_data.csv, cleans it, adds computed columns,
and writes cleaned_stock_data.csv.
"""

import os
import pandas as pd
import numpy as np

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")

RAW_CSV     = os.path.join(DATA_DIR, "master_stock_data.csv")
CLEAN_CSV   = os.path.join(DATA_DIR, "cleaned_stock_data.csv")
SECTOR_CSV  = os.path.join(DATA_DIR, "nifty50_sectors.csv")

# ── load ───────────────────────────────────────────────────────────────────────
df = pd.read_csv(RAW_CSV, parse_dates=["date"])
print(f"Raw rows: {len(df)}")

# ── basic cleaning ─────────────────────────────────────────────────────────────
df.dropna(subset=["ticker", "date", "open", "close", "high", "low", "volume"],
          inplace=True)
df.drop_duplicates(subset=["ticker", "date"], inplace=True)
df.sort_values(["ticker", "date"], inplace=True)
df.reset_index(drop=True, inplace=True)

# Validate OHLCV sanity
df = df[(df["open"] > 0) & (df["close"] > 0) &
        (df["high"] >= df["low"]) & (df["volume"] >= 0)]

# ── derived columns ────────────────────────────────────────────────────────────
# Daily return (%)
df["daily_return"] = df.groupby("ticker")["close"].pct_change() * 100

# Price change (close - open)
df["price_change"] = df["close"] - df["open"]

# Intraday range
df["intraday_range"] = df["high"] - df["low"]

# Year and Month columns for grouping
df["year"]       = df["date"].dt.year
df["month"]      = df["date"].dt.to_period("M").astype(str)
df["month_num"]  = df["date"].dt.month
df["month_name"] = df["date"].dt.strftime("%b %Y")

# ── merge sector info ──────────────────────────────────────────────────────────
sectors = pd.read_csv(SECTOR_CSV)
df = df.merge(sectors[["Ticker", "Company", "Sector"]],
              left_on="ticker", right_on="Ticker", how="left")
df.drop(columns=["Ticker"], inplace=True)

# ── save ───────────────────────────────────────────────────────────────────────
df.to_csv(CLEAN_CSV, index=False)
print(f"✅  Cleaned data saved: {CLEAN_CSV}")
print(f"   Final rows: {len(df)}  |  Tickers: {df['ticker'].nunique()}")
print(df.dtypes)
