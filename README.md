# 📈 Data-Driven Stock Analysis — Nifty 50 Dashboard

A full end-to-end data analytics project:  
**YAML → CSV → MySQL → Streamlit Dashboard**

---

## 📁 Project Structure

```
stock_analysis/
│
├── extract_yaml_to_csv.py   # Step 1: Reads YAML files → 50 CSVs + master CSV
├── clean_data.py            # Step 2: Cleans data, adds computed columns
├── db_upload.py             # Step 3: Uploads to MySQL via SQLAlchemy
│
├── data/
│   ├── csv/                 # 50 per-symbol CSV files (auto-generated)
│   ├── master_stock_data.csv     (auto-generated)
│   ├── cleaned_stock_data.csv    (auto-generated)
│   └── nifty50_sectors.csv  # Sector mapping for all 50 stocks
│
├── app/
│   └── app.py               # Streamlit dashboard (8 visualizations)
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Execution

### 1. Install dependencies
```bash
cd stock_analysis
pip install -r requirements.txt
```

### 2. Configure MySQL
Open `db_upload.py` and edit the `DB_CONFIG` block:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",       # your MySQL username
    "password": "your_pass",  # your MySQL password
    "database": "nifty50_db",
}
```

### 3. Run the pipeline
```bash
# Step 1 — Extract YAML → CSVs
python extract_yaml_to_csv.py

# Step 2 — Clean & enrich data
python clean_data.py

# Step 3 — Upload to MySQL
python db_upload.py

# Step 4 — Launch dashboard
streamlit run app/app.py
```

---

## 📊 Dashboard Visualizations

| # | Chart | Description |
|---|-------|-------------|
| 1 | KPI Cards | Green/Red stock count, avg price, avg volume, best/worst return |
| 2 | Top 10 Green & Red | Horizontal bar charts of yearly gainers and losers |
| 3 | Volatility Analysis | Top 10 most volatile stocks by std dev of daily returns |
| 4 | Cumulative Return | Line chart of top 5 performers over the full year |
| 5 | Sector-wise Performance | Average yearly return grouped by sector |
| 6 | Correlation Heatmap | Stock price correlation matrix |
| 7 | Monthly Gainers/Losers | 12 bar charts showing top 5 up/down stocks each month |
| 8 | Candlestick + Volume | Interactive per-stock OHLCV chart with range slider |

---

## 🛠️ Tech Stack
- **Language:** Python 3.10+
- **Database:** MySQL (via SQLAlchemy + PyMySQL)
- **Dashboard:** Streamlit + Plotly
- **Libraries:** Pandas, NumPy, PyYAML

---

## 📌 Notes
- The YAML files live in the monthly folders (`2023-10/`, `2023-11/`, ...) one level above `stock_analysis/`.
- The pipeline auto-discovers all `20*/` folders so adding new months requires no code changes.
- All file paths are computed relative to script location — works on any OS.
