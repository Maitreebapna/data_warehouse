"""
olap_cube.py
============
Builds a multi-dimensional OLAP Cube for the Kesar Kasturi Pickle
Data Warehouse and exports it to olap_cube.json.

Cube Dimensions:
  - Month    (Dim_Month)
  - Product  (Dim_Product.product_name)
  - Size     (Dim_Product.package_size)

Cube Measures:
  - total_revenue
  - total_profit
  - total_units
  - total_transactions
  - avg_margin_pct

OLAP Operations included:
  1. Full Cube      → Month x Product x Size (3-D)
  2. Roll-Up 1      → Month x Product        (2-D, size rolled up)
  3. Roll-Up 2      → Month x Size           (2-D, product rolled up)
  4. Roll-Up 3      → Product x Size         (2-D, month rolled up)
  5. Roll-Up 4      → Month only             (1-D)
  6. Roll-Up 5      → Product only           (1-D)
  7. Roll-Up 6      → Size only              (1-D)
  8. Grand Total    → (0-D)
"""

import sqlite3
import json
import os

DB_PATH = "data_warehouse.db"
OUT_PATH = "olap_cube.json"

def run_query(conn, sql):
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]

def build_cube():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] {DB_PATH} not found. Run etl_pipeline.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    cube = {}

    # 1. Full 3-D Cube: Month x Product x Size
    cube["full_cube"] = run_query(conn, """
        SELECT
            dm.month_name,
            dp.product_name,
            dp.package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dm.month_name, dp.product_name, dp.package_size
        ORDER BY dm.month_name, dp.product_name, dp.package_size
    """)

    # 2. Roll-Up: Month x Product (size rolled up)
    cube["rollup_month_product"] = run_query(conn, """
        SELECT
            dm.month_name,
            dp.product_name,
            'All'                           AS package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dm.month_name, dp.product_name
        ORDER BY dm.month_name, dp.product_name
    """)

    # 3. Roll-Up: Month x Size (product rolled up)
    cube["rollup_month_size"] = run_query(conn, """
        SELECT
            dm.month_name,
            'All'                           AS product_name,
            dp.package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dm.month_name, dp.package_size
        ORDER BY dm.month_name, dp.package_size
    """)

    # 4. Roll-Up: Product x Size (month rolled up)
    cube["rollup_product_size"] = run_query(conn, """
        SELECT
            'All'                           AS month_name,
            dp.product_name,
            dp.package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dp.product_name, dp.package_size
        ORDER BY dp.product_name, dp.package_size
    """)

    # 5. Roll-Up: Month only
    cube["rollup_month"] = run_query(conn, """
        SELECT
            dm.month_name,
            'All'                           AS product_name,
            'All'                           AS package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dm.month_name
        ORDER BY dm.month_name
    """)

    # 6. Roll-Up: Product only
    cube["rollup_product"] = run_query(conn, """
        SELECT
            'All'                           AS month_name,
            dp.product_name,
            'All'                           AS package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dp.product_name
        ORDER BY total_revenue DESC
    """)

    # 7. Roll-Up: Size only
    cube["rollup_size"] = run_query(conn, """
        SELECT
            'All'                           AS month_name,
            'All'                           AS product_name,
            dp.package_size,
            ROUND(SUM(fs.revenue), 2)       AS total_revenue,
            ROUND(SUM(fs.profit), 2)        AS total_profit,
            ROUND(SUM(fs.quantity), 0)      AS total_units,
            COUNT(fs.sales_id)              AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
        JOIN Dim_Month   dm ON fs.month_id   = dm.month_id
        JOIN Dim_Product dp ON fs.product_id = dp.product_id
        GROUP BY dp.package_size
        ORDER BY total_revenue DESC
    """)

    # 8. Grand Total (0-D)
    cube["grand_total"] = run_query(conn, """
        SELECT
            'All'                           AS month_name,
            'All'                           AS product_name,
            'All'                           AS package_size,
            ROUND(SUM(fs.revenue), 2)           AS total_revenue,
            ROUND(SUM(fs.profit), 2)            AS total_profit,
            ROUND(SUM(fs.quantity), 0)          AS total_units,
            COUNT(fs.sales_id)                  AS total_transactions,
            ROUND(AVG(fs.profit_margin)*100, 2) AS avg_margin_pct
        FROM Fact_Sales fs
    """)

    conn.close()

    # Add metadata
    result = {
        "metadata": {
            "cube_name": "Kesar Kasturi Pickle OLAP Cube",
            "company": "Shri Nakoda Food Industries",
            "dimensions": ["Month", "Product", "Package Size"],
            "measures": ["total_revenue", "total_profit", "total_units",
                         "total_transactions", "avg_margin_pct"],
            "period": "June - August 2025",
            "total_cells": len(cube["full_cube"])
        },
        "slices": cube
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("=" * 55)
    print("  OLAP CUBE BUILT SUCCESSFULLY")
    print("=" * 55)
    print(f"  Full Cube cells      : {len(cube['full_cube'])}")
    print(f"  Month x Product      : {len(cube['rollup_month_product'])}")
    print(f"  Month x Size         : {len(cube['rollup_month_size'])}")
    print(f"  Product x Size       : {len(cube['rollup_product_size'])}")
    print(f"  Month roll-up        : {len(cube['rollup_month'])}")
    print(f"  Product roll-up      : {len(cube['rollup_product'])}")
    print(f"  Size roll-up         : {len(cube['rollup_size'])}")
    print(f"  Output               : {OUT_PATH}")
    print("=" * 55)

if __name__ == "__main__":
    build_cube()
