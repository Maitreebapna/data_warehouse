# Kesar Kasturi Pickle — Data Warehouse (OLAP Analytics)

A complete **Data Warehouse + OLAP Analytics** project built for a pickle manufacturing business.

- **Company:** Shri Nakoda Food Industries
- **Brand:** Kesar Kasturi Pickle
- **Database:** SQLite (Star Schema)
- **ETL:** Python (pandas + sqlite3)
- **Dashboard:** Interactive HTML + Chart.js

---

# Features

- Real business dataset (pickle sales — June to August 2025)
- Star Schema (1 Fact table + 3 Dimension tables)
- Python ETL pipeline (Extract, Transform, Load)
- 8 OLAP queries (Roll-Up, Drill-Down, Slice, Dice, Pivot)
- Interactive browser-based dashboard with KPIs and charts
- Full academic report in `report/README.md`

---

# Dataset

Source: Excel workbook with daily sales data from a pickle manufacturing unit.

Sheets included:
- `master_data` — 239 transaction records
- `business overview` — product catalogue with pricing
- `june_month_sales`, `july_month_sales`, `august_month_sales` — monthly detail

> Dataset file is not included in this repo (private business data). Place it at:
> `proof of originality/kesar kasturi.xlsx`

---

# Setup Instructions

## Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/data-warehouse-project
cd data-warehouse-project
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# How to Run

## Step 1 — Run ETL Pipeline

```bash
python etl_pipeline.py
```

This reads the Excel source, cleans the data, builds the Star Schema, and loads everything into `data_warehouse.db`.

## Step 2 — Export Data for Dashboard

```bash
python export_json.py
python run_queries.py
```

## Step 3 — View Dashboard

```bash
python -m http.server 8080
```

Or on Windows, run:

```bat
.\start_server.bat
```

Open in browser:

```
http://localhost:8080/dashboard.html
```

This dashboard now renders a 3D OLAP cube instead of tables.

> Note: Run the server command from the project root so the browser can load `dashboard.html` and `query_results.json` correctly.

---

# How It Works

## Architecture Overview

```
Excel Workbook (Source)
        |
   ETL Pipeline (Python)
        |
SQLite Data Warehouse (Star Schema)
        |
   OLAP SQL Queries
        |
 HTML Dashboard + JSON
```

---

# Data Warehouse Design

## Star Schema

### Fact Table

- `Fact_Sales` — quantity, revenue, profit, profit_margin per transaction

### Dimension Tables

- `Dim_Date` — full_date, day, month, quarter, year, week
- `Dim_Product` — product_name, package_size, category
- `Dim_Month` — month_name, quarter, year

### Summary Tables

- `Summary_Monthly` — pre-aggregated monthly totals
- `Summary_Product` — pre-aggregated per-product totals

---

# ETL Pipeline

Implemented in `etl_pipeline.py`

## Extract

- Read all sheets from Excel using pandas

## Transform

- Normalize column names
- Parse and validate dates
- Coerce numeric types, drop null rows
- Assign surrogate keys to all dimension tables
- Enrich product categories from business overview sheet

## Load

- Drop existing database, recreate schema with foreign key constraints
- Load all 6 tables via `DataFrame.to_sql()`

---

# OLAP Operations

The warehouse supports:

## Roll-Up

```sql
SELECT dm.month_name, SUM(fs.revenue) AS revenue
FROM Fact_Sales fs JOIN Dim_Month dm ON fs.month_id = dm.month_id
GROUP BY dm.month_name;
```

## Drill-Down

```sql
SELECT dd.full_date, SUM(fs.revenue) AS daily_revenue
FROM Fact_Sales fs JOIN Dim_Date dd ON fs.date_id = dd.date_id
GROUP BY dd.full_date ORDER BY dd.full_date;
```

## Slice

```sql
SELECT * FROM Fact_Sales fs
JOIN Dim_Month dm ON fs.month_id = dm.month_id
WHERE dm.month_name = 'July';
```

## Dice

```sql
SELECT * FROM Fact_Sales fs
JOIN Dim_Product dp ON fs.product_id = dp.product_id
JOIN Dim_Month dm ON fs.month_id = dm.month_id
WHERE dp.product_name = 'mango pickle'
  AND dm.month_name IN ('June', 'July');
```

---

# Dashboard Features

## KPIs

- Total Revenue
- Total Profit
- Units Sold
- Total Transactions
- Average Profit Margin

## Charts

### 1. Monthly Revenue vs Profit
- Bar chart comparing revenue and profit month by month

### 2. Revenue by Product
- Doughnut chart showing each product's revenue share

### 3. Revenue by Package Size
- Horizontal bar chart across all package sizes

### 4. Profit Margin Trend
- Line chart showing margin improvement over 3 months

## Page 2 — SQL Queries
- 8 analytical queries shown with actual result tables

---

# Key Results

| Metric | Value |
|---|---|
| Total Revenue | Rs. 17,92,382 |
| Total Profit | Rs. 7,51,038 |
| Units Sold | 884 boxes |
| Transactions | 239 |
| Avg Profit Margin | 42.6% |
| Best Month (Revenue) | July 2025 |
| Best Month (Margin) | August 2025 (45.19%) |
| Top Revenue Product | Mango Pickle (31.2%) |
| Top Profit Product | Lemon Pickle (32.9%) |

---

# Important Notes

- The Excel source file is not included (private business data)
- Run `etl_pipeline.py` first before launching the dashboard
- The dashboard reads from JSON files — always regenerate them after ETL

---

# Technologies Used

- Python 3
- pandas
- openpyxl
- sqlite3
- Chart.js
- HTML / CSS / JavaScript

---

# Learning Outcomes

This project demonstrates:

- Data Warehouse design with Star Schema
- ETL Pipeline development in Python
- OLAP querying (Roll-Up, Drill-Down, Slice, Dice)
- Interactive data visualization
- Business intelligence from raw transactional data

---

**Submitted by:** Maitree Bapna
**Project:** Academic Data Warehouse Project — 2025
