# Data Warehouse Report
## Kesar Kasturi Pickle — Star Schema Analytics Platform

**Period:** June 2025 – August 2025  
**Submitted by:** Maitree  

---

## 1. Introduction

### 1.1 Business Context

Kesar Kasturi is a pickle manufacturing and retail business dealing in multiple product lines — Mango Pickle, Lemon Pickle, Mixed Pickle, Green Chilli Pickle, and Sweet Lemon Pickle — available in package sizes ranging from 100g to 5kg. The business records daily sales transactions spanning three summer months (June, July, August 2025).

The objective of this project is to design and implement a **Data Warehouse** that consolidates raw transactional Excel data into a structured, query-optimized database following the **Star Schema** model, enabling multi-dimensional analytics.

### 1.2 Objectives

- Design a Star Schema suitable for the pickle sales domain
- Build a Python ETL pipeline to extract, clean, and load data
- Implement OLAP-style analytical SQL queries
- Deliver an interactive web-based dashboard for visual exploration

---

## 2. Data Warehouse Architecture

### 2.1 Schema Design — Star Schema

The Star Schema was chosen over Snowflake Schema due to its simplicity and query performance advantages for OLAP operations. It consists of:

- **1 Central Fact Table**: `Fact_Sales`
- **3 Dimension Tables**: `Dim_Date`, `Dim_Product`, `Dim_Month`
- **2 Summary/Aggregate Tables**: `Summary_Monthly`, `Summary_Product`

### 2.2 Dimension Tables

#### Dim_Date
Stores all unique transaction dates with time intelligence attributes.

| Column | Type | Description |
|---|---|---|
| date_id | INTEGER PK | Surrogate key |
| full_date | TEXT | Calendar date (YYYY-MM-DD) |
| day | INTEGER | Day of month |
| month_num | INTEGER | Numeric month (6, 7, 8) |
| month_name | TEXT | Month name (June, July, August) |
| quarter | INTEGER | Calendar quarter (Q2, Q3) |
| year | INTEGER | Year (2025) |
| week_of_year | INTEGER | ISO week number |

**Total rows: 65** unique trading dates.

#### Dim_Product
Stores the product catalogue with SKU-level granularity.

| Column | Type | Description |
|---|---|---|
| product_id | INTEGER PK | Surrogate key |
| product_name | TEXT | Product variety name |
| package_size | TEXT | Size (100g, 200g, 500g, 1kg, 5kg) |
| category | TEXT | Product category (pickle) |

**Total rows: 29** unique SKUs (product × size combinations).

#### Dim_Month
Stores month-level time attributes for roll-up analysis.

| Column | Type | Description |
|---|---|---|
| month_id | INTEGER PK | Surrogate key |
| month_name | TEXT | June / July / August |
| month_key | TEXT | Lowercase key (june/july/august) |
| quarter | INTEGER | Q2 or Q3 |
| year | INTEGER | 2025 |

**Total rows: 3**.

### 2.3 Fact Table — Fact_Sales

The central fact table stores one row per individual sales transaction.

| Column | Type | Description |
|---|---|---|
| sales_id | INTEGER PK | Surrogate key |
| date_id | INTEGER FK | Reference to Dim_Date |
| product_id | INTEGER FK | Reference to Dim_Product |
| month_id | INTEGER FK | Reference to Dim_Month |
| quantity | REAL | Number of boxes sold |
| revenue | REAL | Total revenue (₹) |
| profit | REAL | Total profit (₹) |
| profit_margin | REAL | Profit margin as decimal |

**Total rows: 239** transactions.

### 2.4 Summary Tables

Pre-aggregated tables for faster dashboard rendering:

| Table | Granularity | Rows |
|---|---|---|
| Summary_Monthly | Per month | 3 |
| Summary_Product | Per product + size | 29 |

---

## 3. ETL Pipeline

### 3.1 Extract

The source data is an Excel workbook (`kesar kasturi.xlsx`) with the following sheets:

| Sheet | Description |
|---|---|
| `master_data` | Core transaction records (239 rows after clean) |
| `business overview` | Product catalogue with pricing |
| `june_month_sales` | June daily sales detail |
| `july_month_sales` | July daily sales detail |
| `august_month_sales` | August daily sales detail |
| `descriptive analysis` | Pre-computed summary statistics |

### 3.2 Transform

Data cleaning steps applied:

1. **Column standardization** — strip whitespace, lowercase, replace spaces with underscores
2. **Date parsing** — convert all date columns to `pandas.Timestamp`
3. **Type coercion** — convert revenue, profit, quantity to numeric, coerce errors to NaN
4. **Null removal** — drop rows missing critical fields (date, product_type, revenue, profit)
5. **Derived columns** — extract day, month_num, quarter, week_of_year from dates
6. **Surrogate key assignment** — integer sequences for all dimension PKs
7. **Category enrichment** — join product category from business overview sheet

### 3.3 Load

- Old database deleted before each run (full refresh)
- Tables created with `PRAGMA foreign_keys = ON`
- Data loaded via `pandas.DataFrame.to_sql()` with `if_exists='append'`
- Transaction committed and connection closed

---

## 4. Key Performance Indicators

| KPI | Value |
|---|---|
| Total Revenue | ₹17,92,382 |
| Total Profit | ₹7,51,038.76 |
| Total Units Sold (Boxes) | 884 |
| Total Transactions | 239 |
| Average Profit Margin | 42.6% |

### 4.1 Monthly Breakdown

| Month | Revenue (₹) | Profit (₹) | Units | Transactions | Avg Margin |
|---|---|---|---|---|---|
| June | 6,35,876 | 2,54,882.90 | 301 | 82 | 41.03% |
| July | 6,67,207 | 2,75,971.34 | 347 | 99 | 42.29% |
| August | 4,89,299 | 2,20,184.52 | 236 | 58 | 45.19% |

> **Observation:** July had the highest revenue and transaction count. August had the lowest volume but the highest average margin (45.19%), suggesting better product mix or pricing in that month.

### 4.2 Revenue by Product

| Product | Revenue (₹) | Share |
|---|---|---|
| Mango Pickle | 5,58,544 | 31.2% |
| Mixed Pickle | 4,13,217 | 23.1% |
| Lemon Pickle | 3,26,128 | 18.2% |
| Green Chilli Pickle | 2,70,155 | 15.1% |
| Sweet Lemon Pickle | 2,24,338 | 12.5% |

> **Observation:** Mango Pickle is the top revenue contributor at 31.2%, followed by Mixed Pickle. Sweet Lemon Pickle has the lowest share.

---

## 5. OLAP Operations

The data warehouse supports standard OLAP operations through SQL queries:

### 5.1 Roll-Up (Detail → Summary)
Aggregate daily sales up to monthly totals:
```sql
SELECT dm.month_name,
       SUM(fs.revenue) AS total_revenue,
       SUM(fs.profit)  AS total_profit
FROM Fact_Sales fs
JOIN Dim_Month dm ON fs.month_id = dm.month_id
GROUP BY dm.month_name;
```
**Result:** 3 rows — one per month.

### 5.2 Drill-Down (Summary → Detail)
Break monthly totals down to daily level:
```sql
SELECT dd.full_date, dd.month_name,
       SUM(fs.revenue)  AS daily_revenue,
       SUM(fs.quantity) AS units
FROM Fact_Sales fs
JOIN Dim_Date dd ON fs.date_id = dd.date_id
GROUP BY dd.full_date
ORDER BY dd.full_date;
```
**Result:** 65 rows — one per trading day.

### 5.3 Slice (Filter single dimension)
Isolate only July transactions:
```sql
SELECT fs.sales_id, dp.product_name, dp.package_size,
       fs.quantity, fs.revenue, fs.profit
FROM Fact_Sales fs
JOIN Dim_Month dm  ON fs.month_id   = dm.month_id
JOIN Dim_Product dp ON fs.product_id = dp.product_id
WHERE dm.month_name = 'July';
```

### 5.4 Dice (Filter multiple dimensions)
Mango Pickle, 500g, in June and July only:
```sql
SELECT dd.full_date, dm.month_name,
       fs.quantity, fs.revenue
FROM Fact_Sales fs
JOIN Dim_Date    dd ON fs.date_id    = dd.date_id
JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
JOIN Dim_Product dp ON fs.product_id = dp.product_id
WHERE dp.product_name = 'mango pickle'
  AND dp.package_size = '500g'
  AND dm.month_name IN ('June','July');
```

### 5.5 Pivot — Margin by Product and Month
```sql
SELECT dp.product_name,
       ROUND(AVG(CASE WHEN dm.month_name='June'
                 THEN fs.profit_margin END)*100,2) AS june_margin,
       ROUND(AVG(CASE WHEN dm.month_name='July'
                 THEN fs.profit_margin END)*100,2) AS july_margin,
       ROUND(AVG(CASE WHEN dm.month_name='August'
                 THEN fs.profit_margin END)*100,2) AS aug_margin
FROM Fact_Sales fs
JOIN Dim_Product dp ON fs.product_id = dp.product_id
JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
GROUP BY dp.product_name;
```

---

## 6. Analytical SQL Queries & Results

### Query 1 — Revenue by Month
```sql
SELECT dm.month_name,
       SUM(fs.revenue) AS revenue,
       SUM(fs.profit)  AS profit
FROM Fact_Sales fs
JOIN Dim_Month dm ON fs.month_id = dm.month_id
GROUP BY dm.month_name;
```
| month_name | revenue | profit |
|---|---|---|
| June | 635876.0 | 254882.9 |
| July | 667207.0 | 275971.34 |
| August | 489299.0 | 220184.52 |

### Query 2 — Top Products by Revenue
```sql
SELECT dp.product_name, SUM(fs.revenue) AS total_rev
FROM Fact_Sales fs
JOIN Dim_Product dp ON fs.product_id = dp.product_id
GROUP BY dp.product_name
ORDER BY total_rev DESC;
```
| product_name | total_rev |
|---|---|
| mango pickle | 558544.0 |
| mixed pickle | 413217.0 |
| lemon pickle | 326128.0 |
| green chilli pickle | 270155.0 |
| sweet lemon pickle | 224338.0 |

### Query 3 — Avg Margin by Package Size
```sql
SELECT dp.package_size,
       ROUND(AVG(fs.profit_margin)*100,2) AS avg_margin_pct
FROM Fact_Sales fs
JOIN Dim_Product dp ON fs.product_id = dp.product_id
GROUP BY dp.package_size
ORDER BY avg_margin_pct DESC;
```
| package_size | avg_margin_pct |
|---|---|
| 200g | 61.35 |
| 100g | 56.90 |
| other | 49.20 |
| 500g | 37.80 |
| 5kg | 37.04 |
| 1kg | 33.20 |

### Query 4 — Profit Contribution by Product
```sql
SELECT dp.product_name,
       ROUND(SUM(fs.profit),2) AS total_profit,
       ROUND(SUM(fs.profit)*100.0/(SELECT SUM(profit) FROM Fact_Sales),2)
         AS profit_share_pct
FROM Fact_Sales fs
JOIN Dim_Product dp ON fs.product_id = dp.product_id
GROUP BY dp.product_name
ORDER BY total_profit DESC;
```
| product_name | total_profit | profit_share_pct |
|---|---|---|
| lemon pickle | 247318.5 | 32.93% |
| mango pickle | 182166.5 | 24.25% |
| green chilli pickle | 166956.8 | 22.23% |
| mixed pickle | 153082.6 | 20.38% |
| sweet lemon pickle | 1514.4 | 0.20% |

---

## 7. Dashboard

The interactive dashboard (`dashboard.html`) is a single-file web application requiring no backend server (except a static file server for JSON loading).

### Page 1 — Dashboard
- **5 KPI cards**: Revenue, Profit, Units, Transactions, Avg Margin
- **4 Charts**: Monthly Revenue vs Profit (bar), Revenue by Product (doughnut), Revenue by Package Size (horizontal bar), Profit Margin Trend (line)
- **Star Schema diagram**: Visual layout of all tables with PK/FK indicators
- **Warehouse Tables** (tabs): Summary Monthly, Summary Product, Fact Sales, Dimensions

### Page 2 — SQL Queries
- 8 analytical SQL queries displayed with their actual results fetched live from `query_results.json`
- Queries cover: revenue roll-up, product ranking, daily trends, margin analysis, contribution analysis

### Technology Stack
- **Chart.js 4.4** — interactive canvas charts
- **Vanilla HTML/CSS/JS** — no framework dependency
- **fetch() API** — loads `query_results.json` dynamically

---

## 8. Key Findings & Insights

1. **July is peak month**: Highest revenue (₹6,67,207) and most transactions (99), indicating a seasonal demand spike.

2. **August efficiency**: Despite lowest volume (236 units, 58 transactions), August achieved the highest average margin (45.19%), suggesting better sales mix or lower cost products sold.

3. **Mango Pickle dominates revenue** (31.2%) but **Lemon Pickle leads in profit contribution** (32.93%) due to significantly higher margins (62.28% for 200g).

4. **Small packages are more profitable**: 200g and 100g sizes have margins of 61.35% and 56.90% respectively, compared to just 33.20% for 1kg. Bulk sizes trade margin for volume.

5. **Sweet Lemon Pickle underperforms**: Only 0.20% profit share despite being one of 5 product lines — warrants a strategic review.

6. **29 unique SKUs** across 5 product types × 6 size variants shows strong product diversification.

---

## 9. Conclusion

This data warehouse successfully consolidates 3 months of Kesar Kasturi Pickle sales data into a normalized Star Schema, enabling efficient multi-dimensional analysis. The ETL pipeline ensures repeatable, clean data loading from the source Excel workbook. The analytical SQL queries and interactive dashboard provide actionable business intelligence — identifying peak periods, high-margin products, and underperforming lines.

The architecture is designed to scale: adding new months requires only re-running `etl_pipeline.py` with updated source data, and the dashboard automatically reflects the new data after re-running `export_json.py` and `run_queries.py`.

---

*Report generated for Kesar Kasturi Pickle Data Warehouse Project — 2025*
