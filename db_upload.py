"""
Step 3: db_upload.py
Uploads cleaned_stock_data.csv into a MySQL database.
Creates tables: stock_prices, sector_mapping.

Usage:
    python db_upload.py

Edit DB_CONFIG below to match your MySQL credentials.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

# ── MySQL credentials — EDIT THESE ────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",          # your MySQL username
    "password": "mohan",          # your MySQL password
    "database": "nifty50_db",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
CLEAN_CSV  = os.path.join(DATA_DIR, "cleaned_stock_data.csv")
SECTOR_CSV = os.path.join(DATA_DIR, "nifty50_sectors.csv")

# ── create engine & database ───────────────────────────────────────────────────
engine_root = create_engine(
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
)

with engine_root.connect() as conn:
    conn.execute(text(
        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    ))
    conn.commit()
print(f"✅  Database '{DB_CONFIG['database']}' ready.")

engine = create_engine(
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# ── upload stock_prices ────────────────────────────────────────────────────────
df = pd.read_csv(CLEAN_CSV, parse_dates=["date"])

# Keep only the columns we want
cols = ["ticker", "date", "open", "close", "high", "low", "volume",
        "daily_return", "price_change", "intraday_range",
        "year", "month", "month_num", "month_name", "Company", "Sector"]
df = df[[c for c in cols if c in df.columns]]

from sqlalchemy import types

df.to_sql(
    "stock_prices",
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=5000,
    dtype={
        "ticker": types.VARCHAR(20),
        "Company": types.VARCHAR(100),
        "Sector": types.VARCHAR(50),
    }
)
print(f"✅  Uploaded {len(df)} rows → table 'stock_prices'")

# ── upload sector_mapping ──────────────────────────────────────────────────────
sectors = pd.read_csv(SECTOR_CSV)
sectors.columns = sectors.columns.str.lower()
sectors.to_sql("sector_mapping", con=engine, if_exists="replace", index=False)
print(f"✅  Uploaded {len(sectors)} rows → table 'sector_mapping'")

# ── create useful indexes ──────────────────────────────────────────────────────
with engine.connect() as conn:
    conn.execute(text(
        "ALTER TABLE stock_prices ADD INDEX idx_ticker (ticker),"
        " ADD INDEX idx_date (date)"
    ))
    conn.commit()

print("✅  Indexes created. DB upload complete.")
