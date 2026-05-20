"""
Runs all analytical SQL queries against the data warehouse
and exports results to query_results.json for the dashboard.
"""
import sqlite3, json

DB_PATH  = "data_warehouse.db"
OUT_FILE = "query_results.json"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def run(sql):
    return [dict(r) for r in conn.execute(sql).fetchall()]

queries = [
    {
        "title": "Revenue by Month",
        "description": "Total revenue and profit grouped by each month.",
        "sql": (
            "SELECT dm.month_name,\n"
            "       SUM(fs.revenue) AS revenue,\n"
            "       SUM(fs.profit)  AS profit\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Month dm\n"
            "  ON fs.month_id = dm.month_id\n"
            "GROUP BY dm.month_name;"
        ),
        "results": run("""
            SELECT dm.month_name,
                   ROUND(SUM(fs.revenue),2) AS revenue,
                   ROUND(SUM(fs.profit),2)  AS profit
            FROM Fact_Sales fs
            JOIN Dim_Month dm ON fs.month_id = dm.month_id
            GROUP BY dm.month_id
        """)
    },
    {
        "title": "Top Products by Revenue",
        "description": "Products ranked by total revenue across all months.",
        "sql": (
            "SELECT dp.product_name,\n"
            "       SUM(fs.revenue) AS total_rev\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Product dp\n"
            "  ON fs.product_id = dp.product_id\n"
            "GROUP BY dp.product_name\n"
            "ORDER BY total_rev DESC;"
        ),
        "results": run("""
            SELECT dp.product_name,
                   ROUND(SUM(fs.revenue),2) AS total_rev
            FROM Fact_Sales fs
            JOIN Dim_Product dp ON fs.product_id = dp.product_id
            GROUP BY dp.product_name
            ORDER BY total_rev DESC
        """)
    },
    {
        "title": "Daily Sales Trend",
        "description": "Revenue and units sold per day across all months.",
        "sql": (
            "SELECT dd.full_date,\n"
            "       SUM(fs.revenue)  AS rev,\n"
            "       SUM(fs.quantity) AS units\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Date dd\n"
            "  ON fs.date_id = dd.date_id\n"
            "GROUP BY dd.full_date\n"
            "ORDER BY dd.full_date;"
        ),
        "results": run("""
            SELECT dd.full_date,
                   ROUND(SUM(fs.revenue),2)  AS rev,
                   CAST(SUM(fs.quantity) AS INTEGER) AS units
            FROM Fact_Sales fs
            JOIN Dim_Date dd ON fs.date_id = dd.date_id
            GROUP BY dd.full_date
            ORDER BY dd.full_date
            LIMIT 20
        """)
    },
    {
        "title": "Avg Margin by Package Size",
        "description": "Average profit margin percentage for each package size.",
        "sql": (
            "SELECT dp.package_size,\n"
            "       ROUND(AVG(fs.profit_margin)*100,2)\n"
            "         AS avg_margin_pct\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Product dp\n"
            "  ON fs.product_id = dp.product_id\n"
            "GROUP BY dp.package_size\n"
            "ORDER BY avg_margin_pct DESC;"
        ),
        "results": run("""
            SELECT dp.package_size,
                   ROUND(AVG(fs.profit_margin)*100,2) AS avg_margin_pct
            FROM Fact_Sales fs
            JOIN Dim_Product dp ON fs.product_id = dp.product_id
            GROUP BY dp.package_size
            ORDER BY avg_margin_pct DESC
        """)
    },
    {
        "title": "Monthly Profit Margin Trend",
        "description": "Average profit margin and transaction count per month.",
        "sql": (
            "SELECT dm.month_name,\n"
            "       ROUND(AVG(fs.profit_margin)*100,2)\n"
            "         AS avg_margin_pct,\n"
            "       COUNT(*) AS transactions\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Month dm\n"
            "  ON fs.month_id = dm.month_id\n"
            "GROUP BY dm.month_name\n"
            "ORDER BY dm.month_id;"
        ),
        "results": run("""
            SELECT dm.month_name,
                   ROUND(AVG(fs.profit_margin)*100,2) AS avg_margin_pct,
                   COUNT(*) AS transactions
            FROM Fact_Sales fs
            JOIN Dim_Month dm ON fs.month_id = dm.month_id
            GROUP BY dm.month_name
            ORDER BY dm.month_id
        """)
    },
    {
        "title": "Revenue by Category and Size",
        "description": "Revenue and units sold broken down by product category and package size.",
        "sql": (
            "SELECT dp.category,\n"
            "       dp.package_size,\n"
            "       SUM(fs.revenue)  AS revenue,\n"
            "       SUM(fs.quantity) AS units\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Product dp\n"
            "  ON fs.product_id = dp.product_id\n"
            "GROUP BY dp.category, dp.package_size\n"
            "ORDER BY revenue DESC;"
        ),
        "results": run("""
            SELECT dp.category,
                   dp.package_size,
                   ROUND(SUM(fs.revenue),2)  AS revenue,
                   CAST(SUM(fs.quantity) AS INTEGER) AS units
            FROM Fact_Sales fs
            JOIN Dim_Product dp ON fs.product_id = dp.product_id
            GROUP BY dp.category, dp.package_size
            ORDER BY revenue DESC
        """)
    },
    {
        "title": "Best Selling Days (Top 10)",
        "description": "Top 10 days by revenue across the entire period.",
        "sql": (
            "SELECT dm.month_name,\n"
            "       dd.full_date,\n"
            "       SUM(fs.revenue) AS daily_rev\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Date dd  ON fs.date_id  = dd.date_id\n"
            "JOIN Dim_Month dm ON fs.month_id = dm.month_id\n"
            "GROUP BY dm.month_name, dd.full_date\n"
            "ORDER BY daily_rev DESC\n"
            "LIMIT 10;"
        ),
        "results": run("""
            SELECT dm.month_name,
                   dd.full_date,
                   ROUND(SUM(fs.revenue),2) AS daily_rev
            FROM Fact_Sales fs
            JOIN Dim_Date dd  ON fs.date_id  = dd.date_id
            JOIN Dim_Month dm ON fs.month_id = dm.month_id
            GROUP BY dm.month_name, dd.full_date
            ORDER BY daily_rev DESC
            LIMIT 10
        """)
    },
    {
        "title": "Profit Contribution by Product",
        "description": "Each product's share of total profit across all sales.",
        "sql": (
            "SELECT dp.product_name,\n"
            "       SUM(fs.profit) AS total_profit,\n"
            "       ROUND(SUM(fs.profit)*100.0 /\n"
            "         (SELECT SUM(profit) FROM Fact_Sales),2)\n"
            "         AS profit_share_pct\n"
            "FROM Fact_Sales fs\n"
            "JOIN Dim_Product dp\n"
            "  ON fs.product_id = dp.product_id\n"
            "GROUP BY dp.product_name\n"
            "ORDER BY total_profit DESC;"
        ),
        "results": run("""
            SELECT dp.product_name,
                   ROUND(SUM(fs.profit),2) AS total_profit,
                   ROUND(SUM(fs.profit)*100.0 /
                     (SELECT SUM(profit) FROM Fact_Sales),2) AS profit_share_pct
            FROM Fact_Sales fs
            JOIN Dim_Product dp ON fs.product_id = dp.product_id
            GROUP BY dp.product_name
            ORDER BY total_profit DESC
        """)
    },
]

conn.close()

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(queries, f, indent=2)

print(f"[OK] Exported {len(queries)} queries with results -> {OUT_FILE}")
for q in queries:
    print(f"     {q['title']}: {len(q['results'])} rows")
