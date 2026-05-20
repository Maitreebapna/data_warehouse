"""
Exports all warehouse data to JSON for the HTML dashboard.
"""
import sqlite3, json, os

DB_PATH  = "data_warehouse.db"
OUT_FILE = "dashboard_data.json"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def q(sql):
    return [dict(r) for r in conn.execute(sql).fetchall()]

data = {
    "dim_date"    : q("SELECT * FROM Dim_Date ORDER BY date_id"),
    "dim_product" : q("SELECT * FROM Dim_Product ORDER BY product_id"),
    "dim_month"   : q("SELECT * FROM Dim_Month ORDER BY month_id"),
    "fact_sales"  : q("SELECT * FROM Fact_Sales ORDER BY sales_id"),
    "summary_monthly" : q("SELECT * FROM Summary_Monthly ORDER BY month_id"),
    "summary_product" : q("SELECT * FROM Summary_Product ORDER BY total_revenue DESC"),

    # KPI aggregates
    "kpis": q("""
        SELECT
            SUM(revenue)            AS total_revenue,
            SUM(profit)             AS total_profit,
            SUM(quantity)           AS total_quantity,
            AVG(profit_margin)*100  AS avg_margin_pct,
            COUNT(*)                AS total_transactions
        FROM Fact_Sales
    """)[0],

    # Revenue by product type (rollup)
    "revenue_by_product_type": q("""
        SELECT dp.product_name, SUM(fs.revenue) AS revenue, SUM(fs.profit) AS profit
        FROM Fact_Sales fs JOIN Dim_Product dp ON fs.product_id=dp.product_id
        GROUP BY dp.product_name ORDER BY revenue DESC
    """),

    # Revenue by package size
    "revenue_by_size": q("""
        SELECT dp.package_size, SUM(fs.revenue) AS revenue
        FROM Fact_Sales fs JOIN Dim_Product dp ON fs.product_id=dp.product_id
        GROUP BY dp.package_size ORDER BY revenue DESC
    """),

    # Daily sales trend
    "daily_trend": q("""
        SELECT dd.full_date AS date, dd.month_name, SUM(fs.revenue) AS revenue,
               SUM(fs.profit) AS profit, SUM(fs.quantity) AS quantity
        FROM Fact_Sales fs JOIN Dim_Date dd ON fs.date_id=dd.date_id
        GROUP BY dd.full_date ORDER BY dd.full_date
    """),

    # Top 10 records
    "top_records": q("""
        SELECT fs.sales_id, dd.full_date AS date, dm.month_name AS month,
               dp.product_name, dp.package_size, fs.quantity,
               fs.revenue, fs.profit,
               ROUND(fs.profit_margin*100,2) AS margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Date dd    ON fs.date_id    = dd.date_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        JOIN Dim_Month dm   ON fs.month_id   = dm.month_id
        ORDER BY fs.revenue DESC LIMIT 50
    """),
}

conn.close()
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print(f"Exported -> {OUT_FILE}")
