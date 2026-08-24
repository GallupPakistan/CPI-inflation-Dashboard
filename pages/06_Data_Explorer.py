"""Page 6 — Data Explorer & Export"""
import pandas as pd
pd.set_option("styler.render.max_elements", 500000)

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from data_loader import (load_data, get_national_pivot, get_yoy, get_mom,
                         get_latest_snapshot, CATEGORIES, CATEGORY_COLORS)
from ui import (inject_css, inject_animation, page_header, section_header, sidebar_logo,
                disclaimer_bar, get_layout, ACCENT, UP, DOWN, MUTED, TEXT)

st.set_page_config(page_title="Data Explorer | Commodity Price Tracker", layout="wide", page_icon="📋")
inject_css()
inject_animation()
sidebar_logo()

df, canonical, short_map = load_data()
pivot  = get_national_pivot()
yoy    = get_yoy()
mom_df = get_mom()
snap, latest_month = get_latest_snapshot()
latest_str = latest_month.strftime("%B %Y")

page_header("📋 Data Explorer & Export",
            "Browse, filter and download raw SPI price data")

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Raw Data",
    "📊 National Averages",
    "📐 Computed Metrics",
    "📈 MoM Spotlight",
])

# ── TAB 1: Raw Data ───────────────────────────────────────────────────────────
with tab1:
    section_header("Filter Raw Data")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cat_sel = st.selectbox("Category", ["All"] + list(CATEGORIES.keys()), key="exp_cat")
    with col2:
        cities_list = sorted(df["Cities"].unique().tolist())
        city_sel = st.multiselect("Cities", cities_list, default=cities_list[:5], key="exp_city")
    with col3:
        months_list = df["Month"].dt.strftime("%b %Y").unique().tolist()
        month_from  = st.selectbox("From Month", months_list, index=0, key="exp_from")
        month_to    = st.selectbox("To Month",   months_list, index=len(months_list)-1, key="exp_to")
    with col4:
        sort_col = st.selectbox("Sort by", ["Month","S. No","Average Price","% Change","Value"], key="exp_sort")
        sort_asc = st.checkbox("Ascending", value=True, key="exp_asc")

    df_exp = df.copy()
    if cat_sel != "All":
        df_exp = df_exp[df_exp["S. No"].isin(CATEGORIES[cat_sel])]
    if city_sel:
        df_exp = df_exp[df_exp["Cities"].isin(city_sel)]
    from_dt = pd.to_datetime(month_from, format="%b %Y")
    to_dt   = pd.to_datetime(month_to,   format="%b %Y")
    df_exp  = df_exp[(df_exp["Month"] >= from_dt) & (df_exp["Month"] <= to_dt)]
    df_exp  = df_exp.sort_values(sort_col, ascending=sort_asc)

    st.caption(f"Showing {len(df_exp):,} rows")
    display_cols = ["Month","S. No","Short","Category","Cities","Region","Value","Average Price","% Change"]
    display_cols = [c for c in display_cols if c in df_exp.columns]
    # Plain dataframe (no Styler) for large filtered data to avoid max_elements crash
    out = df_exp[display_cols].rename(columns={
        "Short":"Item","% Change":"MoM %","Average Price":"Nat. Avg Price","Value":"City Price"
    }).copy()
    out["Month"] = out["Month"].dt.strftime("%b %Y")
    out["Nat. Avg Price"] = out["Nat. Avg Price"].round(2)
    out["City Price"]     = out["City Price"].round(2)
    out["MoM %"]          = out["MoM %"].round(2)
    st.dataframe(out, use_container_width=True, height=500)
    st.download_button("⬇️ Download Filtered Data (CSV)", df_exp[display_cols].to_csv(index=False),
                       file_name="spi_filtered_data.csv", mime="text/csv")

# ── TAB 2: National Averages Pivot ────────────────────────────────────────────
with tab2:
    section_header("National Average Price — Pivot Table (Months × Items)")
    n_months_show = st.slider("Show last N months", 6, 84, 24, key="pivot_months")
    pivot_show = pivot.tail(n_months_show).copy()
    pivot_show.index = pivot_show.index.strftime("%b %Y")
    # Prefix S.No to guarantee unique column names
    pivot_show.columns = [f"{int(c)}. {short_map.get(c,'')[:18]}" for c in pivot_show.columns]
    pivot_show = pivot_show.round(2)
    st.dataframe(pivot_show, use_container_width=True, height=500)
    st.download_button("⬇️ Download National Avg Pivot (CSV)", pivot_show.to_csv(),
                       file_name="spi_national_avg_pivot.csv", mime="text/csv")

# ── TAB 3: Computed Metrics ───────────────────────────────────────────────────
with tab3:
    section_header("All Items — Latest Month Full Metrics")
    full_snap = snap[["S. No","Item","Category","Price","Price_1Y","MoM%","YoY%","Cumulative%"]].copy()
    full_snap.columns = ["#","Item","Category","Price (Rs)","Price 1Y Ago (Rs)","MoM %","YoY %","Cumul. Since Jan'19 %"]

    def _sp(v):
        if not isinstance(v,(int,float)): return ""
        if v>10:  return "color:#EF4444;font-weight:700"
        if v<-5:  return "color:#10B981;font-weight:600"
        return ""

    st.dataframe(
        full_snap.style
            .map(_sp, subset=["MoM %","YoY %"])
            .format({"Price (Rs)":"Rs {:,.2f}","Price 1Y Ago (Rs)":"Rs {:,.2f}",
                     "MoM %":"{:+.2f}%","YoY %":"{:+.2f}%","Cumul. Since Jan'19 %":"{:+.1f}%"}),
        use_container_width=True, height=500
    )
    st.download_button("⬇️ Download Latest Snapshot (CSV)", full_snap.to_csv(index=False),
                       file_name="spi_latest_snapshot.csv", mime="text/csv")

    st.markdown("---")
    section_header("YoY % — All Items × All Months (Last 24)")
    yoy_show = yoy.tail(24).copy()
    yoy_show.index = yoy_show.index.strftime("%b %Y")
    # Unique column names with S.No prefix
    yoy_show.columns = [f"{int(c)}. {short_map.get(c,'')[:15]}" for c in yoy_show.columns]

    def _sy(v):
        if not isinstance(v,(int,float)): return ""
        if v>10:  return "color:#EF4444"
        if v<-5:  return "color:#10B981"
        return "color:#111827"

    st.dataframe(
        yoy_show.style.map(_sy).format("{:+.2f}%"),
        use_container_width=True, height=420
    )
    st.download_button("⬇️ Download YoY % Table (CSV)", yoy_show.to_csv(),
                       file_name="spi_yoy_table.csv", mime="text/csv")

    st.markdown("---")
    section_header("MoM % — All Items × All Months (Last 24)")
    mom_show = mom_df.tail(24).copy()
    mom_show.index = mom_show.index.strftime("%b %Y")
    mom_show.columns = [f"{int(c)}. {short_map.get(c,'')[:15]}" for c in mom_show.columns]
    mom_show = mom_show.round(2)
    st.dataframe(mom_show, use_container_width=True, height=420)
    st.download_button("⬇️ Download MoM % Table (CSV)", mom_show.to_csv(),
                       file_name="spi_mom_table.csv", mime="text/csv")

# ── TAB 4: MoM Spotlight ─────────────────────────────────────────────────────
with tab4:
    section_header(f"MoM % Spotlight — Top Movers ({latest_str})")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<p style='color:#10B981;font-weight:600;font-size:13px;'>▲ TOP 15 INCREASED (MoM)</p>", unsafe_allow_html=True)
        top15_rise = snap.nlargest(15,"MoM%")[["Short","MoM%","Category"]].copy()
        max_r = top15_rise["MoM%"].max()
        fig_rise = go.Figure(go.Bar(
            x=top15_rise["MoM%"], y=top15_rise["Short"], orientation="h",
            marker_color=[CATEGORY_COLORS.get(c, ACCENT) for c in top15_rise["Category"]],
            text=[f"+{v:.1f}%" for v in top15_rise["MoM%"]],
            textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        ))
        lyt_r = get_layout("", height=480)
        lyt_r["xaxis"]["range"]  = [0, max_r * 1.35]
        lyt_r["xaxis"]["title"]  = "MoM %"
        lyt_r["yaxis"]["autorange"] = "reversed"
        lyt_r["margin"]["r"] = 90
        fig_rise.update_layout(lyt_r)
        st.plotly_chart(fig_rise, use_container_width=True)

    with col2:
        st.markdown(f"<p style='color:#EF4444;font-weight:600;font-size:13px;'>▼ TOP 15 DECREASED (MoM)</p>", unsafe_allow_html=True)
        top15_fall = snap.nsmallest(15,"MoM%")[["Short","MoM%","Category"]].copy()
        max_f = abs(top15_fall["MoM%"].min())
        fig_fall = go.Figure(go.Bar(
            x=top15_fall["MoM%"], y=top15_fall["Short"], orientation="h",
            marker_color=DOWN,
            text=[f"{v:.1f}%" for v in top15_fall["MoM%"]],
            textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        ))
        lyt_f = get_layout("", height=480)
        lyt_f["xaxis"]["range"]  = [-(max_f * 1.35), 0]
        lyt_f["xaxis"]["title"]  = "MoM %"
        lyt_f["yaxis"]["autorange"] = "reversed"
        lyt_f["margin"]["l"] = 170
        fig_fall.update_layout(lyt_f)
        st.plotly_chart(fig_fall, use_container_width=True)

    st.markdown("---")
    section_header(f"YoY % Spotlight — Top 15 Risers & Fallers ({latest_str})")
    col3, col4 = st.columns(2)

    with col3:
        top15_yoy = snap.dropna(subset=["YoY%"]).nlargest(15,"YoY%")[["Short","YoY%","Category"]]
        max_y = top15_yoy["YoY%"].max()
        fig_yrise = go.Figure(go.Bar(
            x=top15_yoy["YoY%"], y=top15_yoy["Short"], orientation="h",
            marker_color=ACCENT,
            text=[f"+{v:.1f}%" for v in top15_yoy["YoY%"]],
            textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        ))
        lyt_yr = get_layout("Top 15 YoY Risers", height=480)
        lyt_yr["xaxis"]["range"]  = [0, max_y * 1.35]
        lyt_yr["xaxis"]["title"]  = "YoY %"
        lyt_yr["yaxis"]["autorange"] = "reversed"
        lyt_yr["margin"]["r"] = 90
        fig_yrise.update_layout(lyt_yr)
        st.plotly_chart(fig_yrise, use_container_width=True)

    with col4:
        bot15_yoy = snap.dropna(subset=["YoY%"]).nsmallest(15,"YoY%")[["Short","YoY%","Category"]]
        max_yf = abs(bot15_yoy["YoY%"].min())
        fig_yfall = go.Figure(go.Bar(
            x=bot15_yoy["YoY%"], y=bot15_yoy["Short"], orientation="h",
            marker_color=UP,
            text=[f"{v:.1f}%" for v in bot15_yoy["YoY%"]],
            textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        ))
        lyt_yf = get_layout("Top 15 YoY Fallers (Deflation)", height=480)
        lyt_yf["xaxis"]["range"]  = [-(max_yf * 1.35), 0]
        lyt_yf["xaxis"]["title"]  = "YoY %"
        lyt_yf["yaxis"]["autorange"] = "reversed"
        lyt_yf["margin"]["l"] = 170
        fig_yfall.update_layout(lyt_yf)
        st.plotly_chart(fig_yfall, use_container_width=True)

disclaimer_bar()
