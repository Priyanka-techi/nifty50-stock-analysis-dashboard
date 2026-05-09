"""
Step 1: extract_yaml_to_csv.py
Reads all YAML files from the monthly folders and produces
one CSV per stock ticker under data/csv/.
"""

import os
import glob
import yaml
import pandas as pd

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT  = os.path.join(BASE_DIR, "..")          # parent = project root
CSV_DIR    = os.path.join(BASE_DIR, "data", "csv")
os.makedirs(CSV_DIR, exist_ok=True)

# ── collect every yaml file across all monthly folders ────────────────────────
yaml_files = sorted(glob.glob(os.path.join(DATA_ROOT, "20*", "*.yaml")))
print(f"Found {len(yaml_files)} YAML files.")

all_records = []

for fpath in yaml_files:
    with open(fpath, "r", encoding="utf-8") as f:
        records = yaml.safe_load(f)
    if records:
        all_records.extend(records)

print(f"Total records loaded: {len(all_records)}")

# ── build master dataframe ─────────────────────────────────────────────────────
df = pd.DataFrame(all_records)
df.rename(columns={"Ticker": "ticker"}, inplace=True)
df["date"] = pd.to_datetime(df["date"])
df.sort_values(["ticker", "date"], inplace=True)
df.reset_index(drop=True, inplace=True)

# ── split into per-symbol CSVs ─────────────────────────────────────────────────
tickers = df["ticker"].unique()
print(f"Unique tickers found: {len(tickers)}")

for ticker in tickers:
    symbol_df = df[df["ticker"] == ticker].copy()
    out_path   = os.path.join(CSV_DIR, f"{ticker}.csv")
    symbol_df.to_csv(out_path, index=False)

print(f"✅  Saved {len(tickers)} CSV files to: {CSV_DIR}")

# ── also save a combined master CSV for convenience ───────────────────────────
master_path = os.path.join(BASE_DIR, "data", "master_stock_data.csv")
df.to_csv(master_path, index=False)
print(f"✅  Master CSV saved to: {master_path}")
