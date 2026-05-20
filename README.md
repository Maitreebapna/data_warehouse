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


---



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

