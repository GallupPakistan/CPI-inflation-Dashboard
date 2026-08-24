import pandas as pd
pd.set_option("styler.render.max_elements", 500000)
"""
Page 5 — Inflation Tracker
Computes inflation metrics directly from the raw price data:
- Unweighted avg YoY across all items
- Category-level inflation
- High-inflation alerts
- Food vs energy vs other breakdown
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import (load_data, get_national_pivot, get_yoy, get_mom,
                         get_latest_snapshot, CATEGORIES, CATEGORY_COLORS)
from ui import (inject_css, inject_animation, page_header, section_header, kpi_row, sidebar_logo,
                disclaimer_bar, get_layout, ACCENT, UP, DOWN, MUTED,
                PALETTE, TEXT, CARD, BORDER, BG, PANEL)

st.set_page_config(page_title="Inflation Tracker | Commodity Price Tracker", layout="wide", page_icon="📉")
inject_css()
inject_animation()
sidebar_logo()

df, canonical, short_map = load_data()
pivot = get_national_pivot()
yoy   = get_yoy()
mom_df = get_mom()
snap, latest_month = get_latest_snapshot()
latest_str = latest_month.strftime("%B %Y")
prev_month_str = (latest_month - pd.DateOffset(months=1)).strftime("%B %Y")
ly_str = (latest_month - pd.DateOffset(months=12)).strftime("%B %Y")

page_header("📉 Inflation Tracker",
            f"Price inflation computed from raw SPI data · {latest_str}")

# ── Compute summary stats ─────────────────────────────────────────────────────
avg_yoy_now  = snap["YoY%"].mean()
avg_mom_now  = snap["MoM%"].mean()
rising_yoy   = (snap["YoY%"] > 0).sum()
falling_yoy  = (snap["YoY%"] < 0).sum()
double_digit = (snap["YoY%"] > 10).sum()

kpi_row([
    {"label": "Avg YoY % (all items)",   "value": f"{avg_yoy_now:+.2f}%",
     "delta_up": avg_yoy_now>0, "note": latest_str},
    {"label": "Avg MoM % (all items)",   "value": f"{avg_mom_now:+.2f}%",
     "delta_up": avg_mom_now>0, "note": f"vs {prev_month_str}"},
    {"label": "Items with +ve YoY",      "value": str(rising_yoy),
     "delta": "prices higher vs last year", "delta_up": True},
    {"label": "Items with −ve YoY",      "value": str(falling_yoy),
     "delta": "prices lower vs last year", "delta_up": False},
    {"label": "Double-digit YoY (>10%)", "value": str(double_digit),
     "delta": "items surging", "delta_up": True},
])

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Unweighted Inflation",
    "🗂️ Category Inflation",
    "⚡ Alert: High Inflation",
    "🍞 Food vs Energy",
    "📆 Year-on-Year History",
])

# ── TAB 1: Unweighted avg inflation trend ─────────────────────────────────────
with tab1:
    section_header("Unweighted Average YoY % — All 51 Items (Monthly Trend)")
    avg_yoy_series = yoy.mean(axis=1).dropna()
    avg_mom_series = mom_df.mean(axis=1)

    col1, col2 = st.columns(2)
    with col1:
        fig_ay = go.Figure()
        fig_ay.add_trace(go.Scatter(
            x=avg_yoy_series.index.strftime("%b %y"),
            y=avg_yoy_series,
            name="Avg YoY %",
            mode="lines+markers",
            line=dict(color=ACCENT, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(232,160,32,0.08)",
            hovertemplate="%{x}: %{y:.2f}%<extra></extra>"
        ))
        fig_ay.add_hline(y=0, line_dash="dash", line_color=MUTED)
        lyt_ay = get_layout("Avg YoY % — All Items (Unweighted)", height=380)
        lyt_ay["yaxis"]["title"] = "Avg YoY %"
        fig_ay.update_layout(lyt_ay)
        st.plotly_chart(fig_ay, use_container_width=True)

    with col2:
        fig_am = go.Figure(go.Bar(
            x=avg_mom_series.index.strftime("%b %y"),
            y=avg_mom_series,
            marker_color=[UP if v<0 else (DOWN if v>3 else "#F59E0B") for v in avg_mom_series],
            hovertemplate="%{x}: %{y:.2f}%<extra></extra>"
        ))
        lyt_am = get_layout("Avg MoM % — All Items (Unweighted)", height=380)
        lyt_am["yaxis"]["title"] = "Avg MoM %"
        fig_am.update_layout(lyt_am)
        st.plotly_chart(fig_am, use_container_width=True)

    # Distribution of YoY changes
    section_header(f"Distribution of YoY % Changes — {latest_str}")
    yoy_latest = snap["YoY%"].dropna()
    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=yoy_latest, nbinsx=20,
        marker_color=ACCENT, opacity=0.8,
        hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>"
    ))
    fig_dist.add_vline(x=0, line_dash="solid", line_color=MUTED)
    fig_dist.add_vline(x=yoy_latest.mean(), line_dash="dash", line_color=UP,
                       annotation_text=f"Mean: {yoy_latest.mean():.1f}%", annotation_font_color=UP)
    lyt_dist = get_layout(f"YoY % Distribution — {latest_str}", height=320)
    lyt_dist["xaxis"]["title"] = "YoY %"
    lyt_dist["yaxis"]["title"] = "No. of Items"
    fig_dist.update_layout(lyt_dist)
    st.plotly_chart(fig_dist, use_container_width=True)

# ── TAB 2: Category Inflation ─────────────────────────────────────────────────
with tab2:
    section_header(f"Average YoY % by Category — {latest_str}")
    cat_yoy = snap.groupby("Category")["YoY%"].mean().sort_values(ascending=False).reset_index()
    cat_mom = snap.groupby("Category")["MoM%"].mean().sort_values(ascending=False).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig_cy = go.Figure(go.Bar(
            x=cat_yoy["YoY%"], y=cat_yoy["Category"],
            orientation="h",
            marker_color=[CATEGORY_COLORS.get(c, ACCENT) for c in cat_yoy["Category"]],
            text=[f"{v:+.2f}%" for v in cat_yoy["YoY%"]],
            textposition="outside",
            cliponaxis=False,
        ))
        lyt_cy = get_layout("Avg YoY % by Category", height=420)
        lyt_cy["yaxis"]["autorange"] = "reversed"
        fig_cy.update_layout(lyt_cy)
        st.plotly_chart(fig_cy, use_container_width=True)

    with col2:
        fig_cm = go.Figure(go.Bar(
            x=cat_mom["MoM%"], y=cat_mom["Category"],
            orientation="h",
            marker_color=[UP if v<0 else (DOWN if v>3 else "#F59E0B") for v in cat_mom["MoM%"]],
            text=[f"{v:+.2f}%" for v in cat_mom["MoM%"]],
            textposition="outside",
            cliponaxis=False,
        ))
        lyt_cm = get_layout("Avg MoM % by Category", height=420)
        lyt_cm["yaxis"]["autorange"] = "reversed"
        fig_cm.update_layout(lyt_cm)
        st.plotly_chart(fig_cm, use_container_width=True)

    # Category inflation over time
    section_header("Category Average YoY % — Over Time (Heatmap)")
    n_m = st.slider("Last N months", 6, 60, 24, key="cat_inf_months")
    # Compute category avg YoY per month
    yoy_T = yoy.copy()
    yoy_T.columns = [short_map.get(c,"") for c in yoy_T.columns]

    cat_yoy_ts = {}
    for cat, snos in CATEGORIES.items():
        snos_present = [s for s in snos if s in yoy.columns]
        if snos_present:
            cat_yoy_ts[cat] = yoy[snos_present].mean(axis=1)
    cat_yoy_df = pd.DataFrame(cat_yoy_ts).tail(n_m)

    fig_cat_hm = go.Figure(go.Heatmap(
        z=cat_yoy_df.values.T,
        x=cat_yoy_df.index.strftime("%b %y").tolist(),
        y=cat_yoy_df.columns.tolist(),
        colorscale=[[0,"#10B981"],[0.35,"#E5E7EB"],[0.5,"#E5E7EB"],[1,"#EF4444"]],
        zmid=0,
        colorbar=dict(title="Avg YoY %", tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}%<extra></extra>",
        xgap=1, ygap=1,
    ))
    lyt_cat_hm = get_layout("Category × Month YoY % Heatmap", height=480)
    lyt_cat_hm["xaxis"]["tickangle"] = -45
    fig_cat_hm.update_layout(lyt_cat_hm)
    st.plotly_chart(fig_cat_hm, use_container_width=True)

# ── TAB 3: High Inflation Alerts ─────────────────────────────────────────────
with tab3:
    threshold = st.slider("YoY % Alert Threshold", 5, 50, 10, key="alert_thresh")
    section_header(f"Items with YoY > {threshold}% — {latest_str}")

    alerts = snap[snap["YoY%"] > threshold].sort_values("YoY%", ascending=False)
    if alerts.empty:
        st.success(f"No items with YoY above {threshold}%.")
    else:
        for _, row in alerts.iterrows():
            color = DOWN if row["YoY%"] > 20 else "#F59E0B"
            st.markdown(f"""
            <div style='background:#FFFFFF;border-left:4px solid {color};border-radius:0 8px 8px 0;
                padding:10px 16px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;'>
              <div>
                <p style='color:#111827;font-size:14px;font-weight:600;margin:0;'>{row["Short"]}</p>
                <p style='color:#4B5563;font-size:11px;margin:2px 0 0 0;'>{row["Category"]} &nbsp;|&nbsp; Rs {row["Price"]:,.2f}</p>
              </div>
              <div style='text-align:right;'>
                <p style='color:{color};font-size:18px;font-weight:700;margin:0;'>▲ {row["YoY%"]:.1f}%</p>
                <p style='color:#4B5563;font-size:11px;margin:2px 0 0 0;'>MoM: {row["MoM%"]:+.2f}%</p>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    section_header(f"Items with YoY < −{threshold//2}% (Deflation) — {latest_str}")
    deflation = snap[snap["YoY%"] < -(threshold//2)].sort_values("YoY%")
    if deflation.empty:
        st.success("No items showing significant deflation.")
    else:
        for _, row in deflation.iterrows():
            st.markdown(f"""
            <div style='background:#FFFFFF;border-left:4px solid #10B981;border-radius:0 8px 8px 0;
                padding:10px 16px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;'>
              <div>
                <p style='color:#111827;font-size:14px;font-weight:600;margin:0;'>{row["Short"]}</p>
                <p style='color:#4B5563;font-size:11px;margin:2px 0 0 0;'>{row["Category"]} &nbsp;|&nbsp; Rs {row["Price"]:,.2f}</p>
              </div>
              <div style='text-align:right;'>
                <p style='color:#10B981;font-size:18px;font-weight:700;margin:0;'>▼ {abs(row["YoY%"]):.1f}%</p>
                <p style='color:#4B5563;font-size:11px;margin:2px 0 0 0;'>MoM: {row["MoM%"]:+.2f}%</p>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ── TAB 4: Food vs Energy ─────────────────────────────────────────────────────
with tab4:
    FOOD_SNOS   = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32]
    ENERGY_SNOS = [41,42,43,44,47,48,49]
    OTHER_SNOS  = [sno for sno in range(1,52) if sno not in FOOD_SNOS and sno not in ENERGY_SNOS]

    food_yoy   = yoy[[s for s in FOOD_SNOS if s in yoy.columns]].mean(axis=1)
    energy_yoy = yoy[[s for s in ENERGY_SNOS if s in yoy.columns]].mean(axis=1)
    other_yoy  = yoy[[s for s in OTHER_SNOS if s in yoy.columns]].mean(axis=1)

    section_header("Food vs Energy vs Other — Avg YoY % Trend")
    fig_fe = go.Figure()
    fig_fe.add_trace(go.Scatter(x=food_yoy.dropna().index.strftime("%b %y"),
        y=food_yoy.dropna(), name="Food & Beverages",
        line=dict(color="#3B82F6", width=2.5), mode="lines"))
    fig_fe.add_trace(go.Scatter(x=energy_yoy.dropna().index.strftime("%b %y"),
        y=energy_yoy.dropna(), name="Energy & Utilities",
        line=dict(color=ACCENT, width=2.5), mode="lines"))
    fig_fe.add_trace(go.Scatter(x=other_yoy.dropna().index.strftime("%b %y"),
        y=other_yoy.dropna(), name="Other",
        line=dict(color="#8B5CF6", width=2, dash="dot"), mode="lines"))
    fig_fe.add_hline(y=0, line_dash="dash", line_color=MUTED)
    lyt_fe = get_layout("Food vs Energy vs Other — Avg YoY %", height=420)
    lyt_fe["yaxis"]["title"] = "Avg YoY %"
    fig_fe.update_layout(lyt_fe)
    st.plotly_chart(fig_fe, use_container_width=True)

    # Latest month comparison
    col1, col2, col3 = st.columns(3)
    for col, label, snos, color in [
        (col1, "Food Items", FOOD_SNOS, "#3B82F6"),
        (col2, "Energy Items", ENERGY_SNOS, ACCENT),
        (col3, "Other Items", OTHER_SNOS, "#8B5CF6"),
    ]:
        with col:
            sub = snap[snap["S. No"].isin(snos)]
            avg = sub["YoY%"].mean()
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:16px;text-align:center;'>
              <p style='color:{color};font-size:12px;font-weight:700;margin:0 0 6px 0;'>{label}</p>
              <p style='color:#111827;font-size:26px;font-weight:700;margin:0;'>{avg:+.1f}%</p>
              <p style='color:#4B5563;font-size:11px;margin:4px 0 0 0;'>Avg YoY · {len(sub)} items</p>
            </div>
            """, unsafe_allow_html=True)

# ── TAB 5: Year-on-Year History ───────────────────────────────────────────────
with tab5:
    section_header("Historical Annual Average Price Change (year-over-year)")
    ann = df[df["S. No"].between(1,51)].drop_duplicates(["Month","S. No"]).copy()
    ann["Year"] = ann["Month"].dt.year
    ann_avg = ann.groupby(["Year","S. No"])["Average Price"].mean().unstack()
    ann_yoy = ann_avg.pct_change() * 100

    # Avg across all items per year
    ann_yoy_avg = ann_yoy.mean(axis=1).dropna()
    fig_ann = go.Figure(go.Bar(
        x=ann_yoy_avg.index.astype(str),
        y=ann_yoy_avg,
        marker_color=[DOWN if v>10 else (UP if v<0 else "#F59E0B") for v in ann_yoy_avg],
        text=[f"{v:+.1f}%" for v in ann_yoy_avg], textposition="outside",
            cliponaxis=False,
        textfont=dict(size=11),
        hovertemplate="%{x}: %{y:.2f}%<extra></extra>"
    ))
    fig_ann.add_hline(y=0, line_dash="dash", line_color=MUTED)
    lyt_ann = get_layout("Annual Average Price Change — All Items (Unweighted Avg YoY %)", height=360)
    lyt_ann["yaxis"]["title"] = "Avg YoY %"
    fig_ann.update_layout(lyt_ann)
    st.plotly_chart(fig_ann, use_container_width=True)

    section_header("Annual YoY % by Category — Heatmap")
    cat_ann = {}
    for cat, snos in CATEGORIES.items():
        snos_p = [s for s in snos if s in ann_yoy.columns]
        if snos_p:
            cat_ann[cat] = ann_yoy[snos_p].mean(axis=1)
    cat_ann_df = pd.DataFrame(cat_ann).dropna(how="all")

    fig_cann = go.Figure(go.Heatmap(
        z=cat_ann_df.values.T,
        x=cat_ann_df.index.astype(str).tolist(),
        y=cat_ann_df.columns.tolist(),
        colorscale=[[0,"#10B981"],[0.3,"#E5E7EB"],[0.5,"#E5E7EB"],[1,"#EF4444"]],
        zmid=0,
        colorbar=dict(title="Avg YoY %", tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>",
        xgap=2, ygap=1,
    ))
    lyt_cann = get_layout("Category × Year Average YoY % Heatmap", height=460)
    fig_cann.update_layout(lyt_cann)
    st.plotly_chart(fig_cann, use_container_width=True)

disclaimer_bar()
