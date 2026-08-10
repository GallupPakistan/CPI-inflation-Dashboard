"""
SPI Price Dashboard — Data Loader
Reads DATAFILE.csv and exposes clean DataFrames for all pages.
To update: replace DATAFILE.csv and restart the app.
"""
import pandas as pd
import numpy as np
import streamlit as st

DATA_FILE = "DATAFILE.csv"

# ── Item categories ────────────────────────────────────────────────────────────
CATEGORIES = {
    "Grains & Bread":     [1, 2, 3, 4],
    "Meat & Poultry":     [5, 6, 7],
    "Dairy & Eggs":       [8, 9, 10, 11],
    "Oils & Fats":        [12, 13, 14, 15],
    "Fresh Produce":      [16, 21, 22, 23, 28],
    "Pulses":             [17, 18, 19, 20],
    "Sugar & Spices":     [24, 25, 26, 27],
    "Beverages & Tea":    [29, 32],
    "Cooked Food":        [30, 31],
    "Tobacco":            [33],
    "Clothing":           [34, 35, 36, 37],
    "Footwear":           [38, 39, 40],
    "Energy & Utilities": [41, 42, 43, 44, 47, 48, 49],
    "Household":          [45, 46, 51],
    "Communication":      [50],
}

SNO_TO_CAT = {sno: cat for cat, snos in CATEGORIES.items() for sno in snos}

CATEGORY_COLORS = {
    "Grains & Bread":     "#F59E0B",
    "Meat & Poultry":     "#EF4444",
    "Dairy & Eggs":       "#06B6D4",
    "Oils & Fats":        "#8B5CF6",
    "Fresh Produce":      "#10B981",
    "Pulses":             "#F97316",
    "Sugar & Spices":     "#EC4899",
    "Beverages & Tea":    "#84CC16",
    "Cooked Food":        "#A78BFA",
    "Tobacco":            "#6B7280",
    "Clothing":           "#3B82F6",
    "Footwear":           "#14B8A6",
    "Energy & Utilities": "#E8A020",
    "Household":          "#94A3B8",
    "Communication":      "#CBD5E1",
}

CITY_REGIONS = {
    "Islamabad":  "Punjab/Federal",
    "Rawalpindi": "Punjab/Federal",
    "Lahore":     "Punjab/Federal",
    "Faisalabad": "Punjab/Federal",
    "Gujranwala": "Punjab/Federal",
    "Sialkot":    "Punjab/Federal",
    "Sargodha":   "Punjab/Federal",
    "Multan":     "Punjab/Federal",
    "Bahawalpur": "Punjab/Federal",
    "Karachi":    "Sindh",
    "Hyderabad":  "Sindh",
    "Sukkur":     "Sindh",
    "Larkana":    "Sindh",
    "Peshawar":   "KPK",
    "Bannu":      "KPK",
    "Quetta":     "Balochistan",
    "Khuzdar":    "Balochistan",
}

@st.cache_data(show_spinner="Loading price data...")
def load_data():
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df["Month"] = pd.to_datetime(df["Month"])
    df.columns = df.columns.str.strip()

    # Keep only clean S.No 1-51
    df = df[df["S. No"].between(1, 51)].copy()

    # Build canonical item names from the latest month
    latest_month = df["Month"].max()
    canonical = (
        df[df["Month"] == latest_month]
        .drop_duplicates("S. No")
        .set_index("S. No")["Description"]
        .to_dict()
    )
    df["Item"] = df["S. No"].map(canonical)
    df["Category"] = df["S. No"].map(SNO_TO_CAT)
    df["Region"] = df["Cities"].map(CITY_REGIONS)

    # Short labels (strip units for display)
    short_map = {}
    for sno, name in canonical.items():
        s = name.split("(")[0].split(",")[0].strip()
        s = s.replace(" Per ", " ").replace(" per ", " ")
        short_map[sno] = s[:38]
    df["Short"] = df["S. No"].map(short_map)

    return df, canonical, short_map


@st.cache_data(show_spinner=False)
def get_national_pivot():
    """Monthly national average price pivot: index=Month, columns=S.No"""
    df, _, _ = load_data()
    pivot = (
        df.drop_duplicates(["Month", "S. No"])
        .pivot(index="Month", columns="S. No", values="Average Price")
        .sort_index()
    )
    return pivot


@st.cache_data(show_spinner=False)
def get_yoy():
    """YoY % change for all items, all months"""
    return get_national_pivot().pct_change(12) * 100


@st.cache_data(show_spinner=False)
def get_mom():
    """MoM % change for all items, all months (from raw % Change column)"""
    df, _, _ = load_data()
    mom = (
        df.drop_duplicates(["Month", "S. No"])
        .pivot(index="Month", columns="S. No", values="% Change")
        .sort_index()
    )
    return mom


@st.cache_data(show_spinner=False)
def get_city_pivot(sno):
    """City-level price pivot for a specific item: index=Month, columns=Cities"""
    df, _, _ = load_data()
    sub = df[df["S. No"] == sno].copy()
    pivot = sub.pivot_table(index="Month", columns="Cities", values="Value").sort_index()
    return pivot


@st.cache_data(show_spinner=False)
def get_latest_snapshot():
    """All 51 items latest month with prices, MoM%, YoY%, category"""
    df, canonical, short_map = load_data()
    pivot = get_national_pivot()
    yoy = get_yoy()
    latest_month = pivot.index[-1]

    rows = []
    for sno in range(1, 52):
        if sno not in pivot.columns:
            continue
        price = pivot.loc[latest_month, sno]
        mom_val = df[(df["Month"] == latest_month) & (df["S. No"] == sno)]["% Change"].values
        mom_val = mom_val[0] if len(mom_val) else np.nan
        yoy_val = yoy.loc[latest_month, sno] if sno in yoy.columns else np.nan
        # Price 1 year ago
        if len(pivot) >= 13:
            price_1y = pivot.iloc[-13][sno] if sno in pivot.columns else np.nan
        else:
            price_1y = np.nan
        # Price at series start
        price_start = pivot.iloc[0][sno] if sno in pivot.columns else np.nan
        cumulative = (price - price_start) / price_start * 100 if price_start else np.nan

        rows.append({
            "S. No": sno,
            "Item": canonical.get(sno, f"Item {sno}"),
            "Short": short_map.get(sno, f"Item {sno}"),
            "Category": SNO_TO_CAT.get(sno, "Other"),
            "Price": round(price, 2),
            "Price_1Y": round(price_1y, 2) if not np.isnan(price_1y) else np.nan,
            "MoM%": round(mom_val, 2),
            "YoY%": round(yoy_val, 2) if not np.isnan(yoy_val) else np.nan,
            "Cumulative%": round(cumulative, 1) if not np.isnan(cumulative) else np.nan,
        })
    return pd.DataFrame(rows), latest_month


def get_meta():
    df, _, _ = load_data()
    return {
        "latest_month": df["Month"].max(),
        "first_month": df["Month"].min(),
        "n_months": df["Month"].nunique(),
        "n_items": df["S. No"].nunique(),
        "n_cities": df["Cities"].nunique(),
        "cities": sorted(df["Cities"].unique().tolist()),
        "categories": list(CATEGORIES.keys()),
    }
