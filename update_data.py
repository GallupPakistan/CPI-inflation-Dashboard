"""
Monthly Data Updater — Pakistan Commodity Price Tracker
=========================================================
Run this script each month when PBS releases new data:

    python3 update_data.py "SPI-Monthly-Prices-Annex-4_Items_1-51_.csv"

It reads the new PBS monthly CSV, converts it to the long-format
required by DATAFILE.csv, appends the new month (if not already present),
and saves back to DATAFILE.csv.

PBS CSV format (from Annex-4):
  Row 0 : Title  "Average Monthly Prices of 51 Essential Items for the month of [Month Year]"
  Row 1 : Headers — S.No, Description, Unit, [17 cities], AvgMar26, AvgFeb26, AvgMar25, MoM%, YoY%
  Rows 2-52 : 51 items
  Cols 3-19 : City prices (17 cities)
  Col 20    : Average price current month
  Col 23    : MoM % change
  Col 24    : YoY % change
"""

import pandas as pd
import numpy as np
import sys
import re
from pathlib import Path

DATAFILE = "DATAFILE.csv"

CITIES = [
    "Islamabad","Rawalpindi","Gujranwala","Sialkot","Lahore","Faisalabad",
    "Sargodha","Multan","Bahawalpur","Karachi","Hyderabad","Sukkur",
    "Larkana","Peshawar","Bannu","Quetta","Khuzdar"
]

def parse_monthly_csv(filepath):
    """Parse PBS monthly Annex-4 CSV → long-format DataFrame"""
    df_raw = pd.read_csv(filepath, header=None, encoding="utf-8-sig")

    # Extract month/year from title row
    title = str(df_raw.iloc[0, 0])
    match = re.search(r"month of (\w+)\s+(\d{4})", title, re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot extract month/year from title: {title}")
    month_str = match.group(1)
    year_str  = match.group(2)
    month_dt  = pd.to_datetime(f"1 {month_str} {year_str}", dayfirst=True)
    print(f"  Detected month: {month_dt.strftime('%B %Y')} ({month_dt.date()})")

    # Data rows 2-52
    data = df_raw.iloc[2:53].copy().reset_index(drop=True)
    data.columns = range(data.shape[1])

    rows = []
    for _, row in data.iterrows():
        sno  = row[0]
        desc = str(row[1]).strip() + " " + str(row[2]).strip()
        desc = desc.strip()
        avg_price = float(row[20]) if pd.notna(row[20]) else np.nan
        mom_pct   = float(row[23]) if pd.notna(row[23]) else np.nan

        # National average row
        rows.append({
            "S. No":       int(sno),
            "Description": desc,
            "Average Price": avg_price,
            "% Change":    mom_pct,
            "Cities":      "National",
            "Value":       avg_price,
            "Month":       month_dt,
        })

        # City rows (cols 3-19)
        for city_idx, city in enumerate(CITIES):
            val = row[3 + city_idx]
            if pd.notna(val) and str(val).strip() not in ("", "nan"):
                try:
                    city_price = float(val)
                    rows.append({
                        "S. No":       int(sno),
                        "Description": desc,
                        "Average Price": avg_price,
                        "% Change":    mom_pct,
                        "Cities":      city,
                        "Value":       city_price,
                        "Month":       month_dt,
                    })
                except (ValueError, TypeError):
                    pass

    df_new = pd.DataFrame(rows)
    df_new["Month"] = df_new["Month"].dt.strftime("%-m/%-d/%Y")
    # Filter out National rows (DATAFILE only has city rows + one avg row per item)
    df_new = df_new[df_new["Cities"] != "National"].copy()
    return df_new, month_dt

def update_datafile(new_csv_path):
    print(f"\nReading new PBS CSV: {new_csv_path}")
    df_new, month_dt = parse_monthly_csv(new_csv_path)

    print(f"  New data rows: {len(df_new):,}")

    print(f"\nLoading existing {DATAFILE}...")
    df_existing = pd.read_csv(DATAFILE, encoding="utf-8-sig")
    df_existing["Month_dt"] = pd.to_datetime(df_existing["Month"])
    print(f"  Existing rows: {len(df_existing):,}")
    print(f"  Existing latest: {df_existing['Month_dt'].max().strftime('%B %Y')}")

    # Check if month already exists
    if month_dt in df_existing["Month_dt"].values:
        print(f"\n  ⚠️  {month_dt.strftime('%B %Y')} already exists in DATAFILE.csv")
        overwrite = input("  Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("  Aborted.")
            return
        df_existing = df_existing[df_existing["Month_dt"] != month_dt]
        print(f"  Removed existing {month_dt.strftime('%B %Y')} rows")

    df_existing = df_existing.drop(columns=["Month_dt"])

    # Append new data
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_csv(DATAFILE, index=False)

    print(f"\n✅ DATAFILE.csv updated successfully!")
    print(f"  Total rows: {len(df_combined):,}")
    print(f"  New month added: {month_dt.strftime('%B %Y')}")
    print(f"\n  Restart your Streamlit app to see the new data.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 update_data.py <path-to-new-pbs-csv>")
        print("Example: python3 update_data.py 'SPI-Monthly-Prices-Annex-4_Items_1-51_.csv'")
        sys.exit(1)
    update_datafile(sys.argv[1])
