"""
============================================================
KESAR KASTURI PICKLE – DATA WAREHOUSE ETL PIPELINE
============================================================
Architecture : Star Schema
  Dimensions : Dim_Date, Dim_Product, Dim_Size, Dim_Month
  Fact Table  : Fact_Sales
  Summary     : Summary_Monthly, Summary_ProductRevenue
============================================================
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
from pathlib import Path

DEFAULT_EXCEL = Path(r"proof of originality/kesar kasturi.xlsx")
FALLBACK_EXCEL = Path(r"kesar kasturi.xlsx")
EXCEL_PATH = DEFAULT_EXCEL if DEFAULT_EXCEL.exists() else FALLBACK_EXCEL

if not EXCEL_PATH.exists():
    raise FileNotFoundError(
        f"Could not find Excel source file. Checked:\n"
        f"  - {DEFAULT_EXCEL}\n"
        f"  - {FALLBACK_EXCEL}\n"
        f"Please place the workbook in one of these locations."
    )

DB_PATH     = "data_warehouse.db"

# ---------------------------------------------------------
# STEP 1 – EXTRACT
# ---------------------------------------------------------
print("="*60)
print(" KESAR KASTURI – DATA WAREHOUSE ETL")
print("="*60)

xls = pd.ExcelFile(EXCEL_PATH)
print(f"\n[EXTRACT] Sheets found: {xls.sheet_names}")

# -- Master data (core transactions) ----------------------
raw_master = pd.read_excel(xls, sheet_name="master_data")
print(f"[EXTRACT] master_data rows (raw): {len(raw_master)}")

# -- Business overview (product catalogue) ----------------
raw_biz = pd.read_excel(xls, sheet_name="business overview ", header=1)

# -- Monthly sales sheets ----------------------------------
def load_monthly(sheet):
    df = pd.read_excel(xls, sheet_name=sheet, header=2)
    df.columns = ["date","product_type","size_g","quantity_sold_box",
                  "pieces_per_box","selling_price_per_piece","revenue",
                  "cost_per_piece","total_cost","profit","margin_pct"]
    df = df.dropna(subset=["date"])
    # Keep only rows where 'date' is actually a date-like object (not header text)
    df = df[df["date"].apply(lambda x: isinstance(x, (pd.Timestamp, float)) or
                              (isinstance(x, str) and x not in ["date","date ","Date"]))]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["month_source"] = sheet.replace("_month_sales","").replace("_"," ").title()
    return df

june_df   = load_monthly("june_month_sales")
july_df   = load_monthly("july_month_sales")
august_df = load_monthly("august_month_sales")
all_monthly = pd.concat([june_df, july_df, august_df], ignore_index=True)
print(f"[EXTRACT] Combined monthly sales rows: {len(all_monthly)}")

# -- Descriptive summary -----------------------------------
raw_desc = pd.read_excel(xls, sheet_name="descriptive analysis")

# ---------------------------------------------------------
# STEP 2 – TRANSFORM
# ---------------------------------------------------------
print("\n[TRANSFORM] Cleaning data …")

# -- Clean master_data -------------------------------------
master = raw_master.copy()
master.columns = [c.strip().lower().replace(" ","_") for c in master.columns]
master.rename(columns={"revenue_":"revenue","profit_":"profit",
                        "unit_size_":"unit_size","profit_margin":"profit_margin"}, inplace=True)
master.dropna(subset=["date","product_type"], inplace=True)
master["date"] = pd.to_datetime(master["date"])
master["month"] = master["month"].str.strip().str.lower()
master["product_type"] = master["product_type"].str.strip().str.lower()
master["unit_size"] = master["unit_size"].str.strip().str.lower()
master["quantity"] = pd.to_numeric(master["quantity"], errors="coerce")
master["revenue"]  = pd.to_numeric(master["revenue"], errors="coerce")
master["profit"]   = pd.to_numeric(master["profit"], errors="coerce")
master["profit_margin"] = pd.to_numeric(master["profit_margin"], errors="coerce")
master.dropna(subset=["quantity","revenue","profit"], inplace=True)
print(f"  master rows after clean: {len(master)}")

# -- Clean business overview -------------------------------
biz = raw_biz.copy()
biz.columns = ["product_type","size","pieces_per_box","sell_price_per_piece",
               "sell_price_per_box","shelf_life","category"]
biz.dropna(subset=["product_type"], inplace=True)
biz["product_type"] = biz["product_type"].str.strip().str.lower()
biz["category"]     = biz["category"].str.strip().str.lower()
print(f"  business overview rows after clean: {len(biz)}")

# -- Clean detailed monthly data ---------------------------
monthly = all_monthly.copy()
monthly["date"] = pd.to_datetime(monthly["date"])
monthly["product_type"] = monthly["product_type"].str.strip().str.lower()
monthly.dropna(subset=["date","product_type","revenue"], inplace=True)
print(f"  monthly detail rows after clean: {len(monthly)}")

# ---------------------------------------------------------
# BUILD DIMENSION TABLES
# ---------------------------------------------------------

# -- Dim_Date ----------------------------------------------
all_dates = master["date"].drop_duplicates().sort_values()
dim_date = pd.DataFrame({
    "date_id"    : range(1, len(all_dates)+1),
    "full_date"  : all_dates.values,
    "day"        : all_dates.dt.day.values,
    "month_num"  : all_dates.dt.month.values,
    "month_name" : all_dates.dt.strftime("%B").values,
    "quarter"    : all_dates.dt.quarter.values,
    "year"       : all_dates.dt.year.values,
    "week_of_year": all_dates.dt.isocalendar().week.values
})
date_map = {d: i for i, d in zip(dim_date["date_id"], dim_date["full_date"])}

# -- Dim_Product -------------------------------------------
prod_pairs = master[["product_type","unit_size"]].drop_duplicates().sort_values("product_type")
# Merge with category from biz overview
cat_map = biz.groupby("product_type")["category"].first().to_dict()
prod_pairs = prod_pairs.copy()
prod_pairs["category"] = prod_pairs["product_type"].map(cat_map).fillna("pickle")
prod_pairs = prod_pairs.reset_index(drop=True)
prod_pairs.insert(0, "product_id", range(1, len(prod_pairs)+1))
prod_pairs.rename(columns={"product_type":"product_name","unit_size":"package_size"}, inplace=True)
dim_product = prod_pairs.copy()
product_map = {(row.product_name, row.package_size): row.product_id
               for row in dim_product.itertuples()}

# -- Dim_Month ---------------------------------------------
months = ["june","july","august"]
dim_month = pd.DataFrame({
    "month_id"    : [1,2,3],
    "month_name"  : ["June","July","August"],
    "month_key"   : months,
    "quarter"     : [2,3,3],
    "year"        : [2025,2025,2025]
})
month_map = {"june":1,"july":2,"august":3}

# ---------------------------------------------------------
# BUILD FACT TABLE
# ---------------------------------------------------------
fact = master.copy()
fact["date_id"]    = fact["date"].map(date_map)
fact["product_id"] = fact.apply(
    lambda r: product_map.get((r["product_type"], r["unit_size"])), axis=1)
fact["month_id"]   = fact["month"].map(month_map)

fact_sales = fact[[
    "date_id","product_id","month_id",
    "quantity","revenue","profit","profit_margin"
]].copy()
fact_sales.insert(0, "sales_id", range(1, len(fact_sales)+1))
fact_sales["revenue"]  = fact_sales["revenue"].round(2)
fact_sales["profit"]   = fact_sales["profit"].round(2)
fact_sales["profit_margin"] = fact_sales["profit_margin"].round(4)
print(f"\n[TRANSFORM] Fact_Sales rows: {len(fact_sales)}")

# ---------------------------------------------------------
# SUMMARY / AGGREGATE TABLES
# ---------------------------------------------------------
summary_monthly = (fact_sales
    .merge(dim_month[["month_id","month_name","year"]], on="month_id")
    .groupby(["month_id","month_name","year"])
    .agg(total_revenue=("revenue","sum"),
         total_profit=("profit","sum"),
         total_quantity=("quantity","sum"),
         avg_margin=("profit_margin","mean"),
         num_transactions=("sales_id","count"))
    .reset_index()
)
summary_monthly["total_revenue"]  = summary_monthly["total_revenue"].round(2)
summary_monthly["total_profit"]   = summary_monthly["total_profit"].round(2)
summary_monthly["avg_margin"]     = summary_monthly["avg_margin"].round(4)

summary_product = (fact_sales
    .merge(dim_product, on="product_id")
    .groupby(["product_id","product_name","package_size","category"])
    .agg(total_revenue=("revenue","sum"),
         total_profit=("profit","sum"),
         total_quantity=("quantity","sum"),
         avg_margin=("profit_margin","mean"),
         num_transactions=("sales_id","count"))
    .reset_index()
)
summary_product["total_revenue"] = summary_product["total_revenue"].round(2)
summary_product["total_profit"]  = summary_product["total_profit"].round(2)
summary_product["avg_margin"]    = summary_product["avg_margin"].round(4)

# ---------------------------------------------------------
# STEP 3 – LOAD INTO SQLITE
# ---------------------------------------------------------
print("\n[LOAD] Writing to SQLite …")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

cur.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Dim_Date (
    date_id      INTEGER PRIMARY KEY,
    full_date    TEXT NOT NULL,
    day          INTEGER,
    month_num    INTEGER,
    month_name   TEXT,
    quarter      INTEGER,
    year         INTEGER,
    week_of_year INTEGER
);

CREATE TABLE IF NOT EXISTS Dim_Product (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    package_size TEXT,
    category     TEXT
);

CREATE TABLE IF NOT EXISTS Dim_Month (
    month_id   INTEGER PRIMARY KEY,
    month_name TEXT NOT NULL,
    month_key  TEXT,
    quarter    INTEGER,
    year       INTEGER
);

CREATE TABLE IF NOT EXISTS Fact_Sales (
    sales_id      INTEGER PRIMARY KEY,
    date_id       INTEGER REFERENCES Dim_Date(date_id),
    product_id    INTEGER REFERENCES Dim_Product(product_id),
    month_id      INTEGER REFERENCES Dim_Month(month_id),
    quantity      REAL,
    revenue       REAL,
    profit        REAL,
    profit_margin REAL
);

CREATE TABLE IF NOT EXISTS Summary_Monthly (
    month_id         INTEGER REFERENCES Dim_Month(month_id),
    month_name       TEXT,
    year             INTEGER,
    total_revenue    REAL,
    total_profit     REAL,
    total_quantity   REAL,
    avg_margin       REAL,
    num_transactions INTEGER
);

CREATE TABLE IF NOT EXISTS Summary_Product (
    product_id       INTEGER REFERENCES Dim_Product(product_id),
    product_name     TEXT,
    package_size     TEXT,
    category         TEXT,
    total_revenue    REAL,
    total_profit     REAL,
    total_quantity   REAL,
    avg_margin       REAL,
    num_transactions INTEGER
);
""")

dim_date["full_date"] = dim_date["full_date"].astype(str)
dim_date.to_sql("Dim_Date",      conn, if_exists="append", index=False)
dim_product.to_sql("Dim_Product", conn, if_exists="append", index=False)
dim_month.to_sql("Dim_Month",    conn, if_exists="append", index=False)
fact_sales.to_sql("Fact_Sales",  conn, if_exists="append", index=False)
summary_monthly.to_sql("Summary_Monthly", conn, if_exists="append", index=False)
summary_product.to_sql("Summary_Product", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print(f"  [OK] Database saved -> {DB_PATH}")
print(f"\n{'='*60}")
print("  DATA WAREHOUSE CREATION COMPLETE")
print(f"{'='*60}")
print(f"  Dim_Date     : {len(dim_date)} rows")
print(f"  Dim_Product  : {len(dim_product)} rows")
print(f"  Dim_Month    : {len(dim_month)} rows")
print(f"  Fact_Sales   : {len(fact_sales)} rows")
print(f"  Summary_Monthly : {len(summary_monthly)} rows")
print(f"  Summary_Product : {len(summary_product)} rows")
print(f"{'='*60}")
