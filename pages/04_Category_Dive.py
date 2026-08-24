import pandas as pd
pd.set_option("styler.render.max_elements", 500000)
"""
Page 4 — Category Deep Dive
Drill into each of the 15 categories: food groups, energy, clothing etc.
Price levels, YoY/MoM trends, city comparisons within each category.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import (load_data, get_national_pivot, get_yoy, get_mom,
                         get_latest_snapshot, CATEGORIES, CATEGORY_COLORS, CITY_REGIONS)
from ui import (inject_css, inject_animation, page_header, section_header, kpi_row, sidebar_logo,
                disclaimer_bar, get_layout, ACCENT, UP, DOWN, MUTED,
                PALETTE, TEXT, CARD, BORDER, BG)

st.set_page_config(page_title="Category Deep Dive | Commodity Price Tracker", layout="wide", page_icon="🗂️")
inject_css()
inject_animation()
sidebar_logo()

df, canonical, short_map = load_data()
pivot = get_national_pivot()
yoy   = get_yoy()
mom   = get_mom()
snap, latest_month = get_latest_snapshot()
latest_str = latest_month.strftime("%B %Y")

page_header("🗂️ Category Deep Dive",
            f"Drill into each commodity group — prices, trends, city comparisons · {latest_str}")

# ── Category selector ─────────────────────────────────────────────────────────
cat_name = st.selectbox(
    "Select Category",
    list(CATEGORIES.keys()),
    index=0,
    format_func=lambda x: f"{x}  ({len(CATEGORIES[x])} items)"
)
cat_snos  = CATEGORIES[cat_name]
cat_color = CATEGORY_COLORS[cat_name]
cat_snap  = snap[snap["S. No"].isin(cat_snos)].copy()

st.markdown("---")

# ── KPI row for category ──────────────────────────────────────────────────────
avg_mom_cat = cat_snap["MoM%"].mean()
avg_yoy_cat = cat_snap["YoY%"].mean()
top_riser   = cat_snap.nlargest(1,"MoM%").iloc[0]
top_faller  = cat_snap.nsmallest(1,"MoM%").iloc[0]

kpi_row([
    {"label": "Items in Category",  "value": str(len(cat_snos))},
    {"label": "Avg MoM % Change",   "value": f"{avg_mom_cat:+.2f}%", "delta_up": avg_mom_cat>0},
    {"label": "Avg YoY % Change",   "value": f"{avg_yoy_cat:+.2f}%", "delta_up": avg_yoy_cat>0},
    {"label": "Biggest MoM Riser",  "value": top_riser["Short"][:22],
     "delta": f"+{top_riser['MoM%']:.1f}%", "delta_up": True},
    {"label": "Biggest MoM Faller", "value": top_faller["Short"][:22],
     "delta": f"{top_faller['MoM%']:.1f}%", "delta_up": False},
])

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "💰 Current Prices",
    "📈 Price Trends",
    "📊 YoY / MoM",
    "🏙️ City Breakdown",
])

# ── TAB 1: Current Prices ─────────────────────────────────────────────────────
with tab1:
    section_header(f"Current Prices — {cat_name} ({latest_str})")
    col1, col2 = st.columns(2)

    with col1:
        # Bar chart of current prices
        cat_snap_sorted = cat_snap.sort_values("Price", ascending=False)
        fig_p = go.Figure(go.Bar(
            x=cat_snap_sorted["Price"],
            y=cat_snap_sorted["Short"],
            orientation="h",
            marker_color=cat_color,
            text=[f"Rs {v:,.2f}" for v in cat_snap_sorted["Price"]],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=11),
            hovertemplate="<b>%{y}</b><br>Rs %{x:,.2f}<extra></extra>"
        ))
        lyt_p = get_layout(f"Current Prices — {cat_name}", height=max(280, len(cat_snos)*42))
        lyt_p["xaxis"]["title"] = "Price (Rs)"
        lyt_p["xaxis"]["range"] = [0, cat_snap_sorted["Price"].max() * 1.45]
        lyt_p["yaxis"]["autorange"] = "reversed"
        lyt_p["margin"]["r"] = 110
        fig_p.update_layout(lyt_p)
        st.plotly_chart(fig_p, use_container_width=True)

    with col2:
        # MoM % for each item
        fig_mom_cat = go.Figure(go.Bar(
            x=cat_snap["MoM%"],
            y=cat_snap["Short"],
            orientation="h",
            marker_color=[UP if v<0 else (DOWN if v>5 else "#F59E0B") for v in cat_snap["MoM%"]],
            text=[f"{v:+.2f}%" for v in cat_snap["MoM%"]],
            textposition="outside",
            cliponaxis=False,
        ))
        lyt_m = get_layout(f"MoM % Change — {cat_name}", height=max(280, len(cat_snos)*42))
        lyt_m["xaxis"]["title"] = "MoM %"
        _ma = cat_snap["MoM%"].abs().max()
        _neg = cat_snap["MoM%"].min() < 0
        _pos = cat_snap["MoM%"].max() > 0
        lyt_m["xaxis"]["range"] = [(-_ma*1.45 if _neg else -_ma*0.1), (_ma*1.45 if _pos else _ma*0.1)]
        lyt_m["yaxis"]["autorange"] = "reversed"
        lyt_m["margin"]["r"] = 90
        fig_mom_cat.update_layout(lyt_m)
        st.plotly_chart(fig_mom_cat, use_container_width=True)

    # Detailed table
    section_header("Item Detail Table")
    show_df = cat_snap[["S. No","Item","Price","Price_1Y","MoM%","YoY%","Cumulative%"]].copy()
    show_df.columns = ["#","Item","Price (Rs)","Price 1Y Ago","MoM %","YoY %","Since Jan'19 %"]
    st.dataframe(
        show_df.style
        .format({"Price (Rs)":"Rs {:,.2f}","Price 1Y Ago":"Rs {:,.2f}",
                 "MoM %":"{:+.2f}%","YoY %":"{:+.2f}%","Since Jan'19 %":"{:+.1f}%"})
        .map(lambda v: "color:#EF4444;font-weight:700" if isinstance(v,float) and v>10 else
                            ("color:#10B981;font-weight:600" if isinstance(v,float) and v<-5 else ""),
                  subset=["MoM %","YoY %"]),
        use_container_width=True
    )

# ── TAB 2: Price Trends ───────────────────────────────────────────────────────
with tab2:
    n_months = st.slider("Show last N months", 6, 84, 24, key="cat_months")
    pivot_cat = pivot[cat_snos].tail(n_months)

    section_header(f"Price Trend — {cat_name} (Last {n_months} months)")
    fig_tr = go.Figure()
    for i, sno in enumerate(cat_snos):
        if sno not in pivot_cat.columns:
            continue
        label = short_map.get(sno, f"Item {sno}")
        fig_tr.add_trace(go.Scatter(
            x=pivot_cat.index.strftime("%b %y"), y=pivot_cat[sno],
            name=label, mode="lines+markers",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: Rs %{{y:,.2f}}<extra></extra>"
        ))
    lyt_tr = get_layout(f"{cat_name} — Price Trend", height=420)
    lyt_tr["yaxis"]["title"] = "Price (Rs)"
    fig_tr.update_layout(lyt_tr)
    st.plotly_chart(fig_tr, use_container_width=True)

    # Indexed (Jan 2019 = 100)
    section_header("Indexed Price Trend (First Month = 100)")
    pivot_idx = pivot[cat_snos].copy()
    pivot_idx = pivot_idx / pivot_idx.iloc[0] * 100
    pivot_idx_f = pivot_idx.tail(n_months)

    fig_idx = go.Figure()
    for i, sno in enumerate(cat_snos):
        if sno not in pivot_idx_f.columns:
            continue
        label = short_map.get(sno, f"Item {sno}")
        fig_idx.add_trace(go.Scatter(
            x=pivot_idx_f.index.strftime("%b %y"), y=pivot_idx_f[sno],
            name=label, mode="lines",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
        ))
    fig_idx.add_hline(y=100, line_dash="dash", line_color=MUTED, line_width=1,
                      annotation_text="Baseline (Jan 2019)")
    lyt_idx = get_layout("Indexed Price (First Month = 100)", height=380)
    lyt_idx["yaxis"]["title"] = "Index"
    fig_idx.update_layout(lyt_idx)
    st.plotly_chart(fig_idx, use_container_width=True)

# ── TAB 3: YoY / MoM ─────────────────────────────────────────────────────────
with tab3:
    n_m3 = st.slider("Show last N months", 6, 84, 18, key="cat_yoy_months")
    yoy_cat = yoy[cat_snos].tail(n_m3)
    mom_cat = mom[cat_snos].tail(n_m3)

    section_header(f"YoY % Change — {cat_name}")
    fig_yoy = go.Figure()
    for i, sno in enumerate(cat_snos):
        if sno not in yoy_cat.columns:
            continue
        label = short_map.get(sno, f"Item {sno}")
        series = yoy_cat[sno].dropna()
        fig_yoy.add_trace(go.Scatter(
            x=series.index.strftime("%b %y"), y=series,
            name=label, mode="lines+markers",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
        ))
    fig_yoy.add_hline(y=0, line_dash="dash", line_color=MUTED)
    lyt_yoy = get_layout(f"YoY % — {cat_name}", height=380)
    fig_yoy.update_layout(lyt_yoy)
    st.plotly_chart(fig_yoy, use_container_width=True)

    section_header(f"MoM % Change Heatmap — {cat_name}")
    z_mom = mom_cat.values.T
    fig_hm = go.Figure(go.Heatmap(
        z=z_mom,
        x=mom_cat.index.strftime("%b %y").tolist(),
        y=[short_map.get(c,"")[:30] for c in mom_cat.columns],
        colorscale=[[0,"#10B981"],[0.45,"#E5E7EB"],[0.55,"#E5E7EB"],[1,"#EF4444"]],
        zmid=0,
        colorbar=dict(title="MoM %", tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}%<extra></extra>",
        xgap=1, ygap=1,
    ))
    lyt_hm = get_layout("", height=max(250, len(cat_snos)*40))
    lyt_hm["xaxis"]["tickangle"] = -45
    fig_hm.update_layout(lyt_hm)
    st.plotly_chart(fig_hm, use_container_width=True)

# ── TAB 4: City Breakdown ─────────────────────────────────────────────────────
with tab4:
    section_header(f"City-level Prices — {cat_name} ({latest_str})")
    latest_all = df[(df["Month"] == latest_month) & (df["S. No"].isin(cat_snos))]
    city_cat = latest_all.pivot_table(index="Cities", columns="S. No", values="Value")
    city_cat.columns = [short_map.get(c,"")[:25] for c in city_cat.columns]

    # Normalise
    city_cat_norm = city_cat.div(city_cat.mean()) * 100

    fig_cc = go.Figure(go.Heatmap(
        z=city_cat_norm.values,
        x=city_cat_norm.columns.tolist(),
        y=city_cat_norm.index.tolist(),
        colorscale=[[0,"#10B981"],[0.85,"#E5E7EB"],[1,"#EF4444"]],
        zmid=100,
        colorbar=dict(title="vs Item Avg", tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b> — %{x}<br>%{z:.1f}% of item avg<extra></extra>",
        xgap=1, ygap=1
    ))
    lyt_cc = get_layout(f"{cat_name} — City Prices vs Item Average", height=460)
    lyt_cc["xaxis"]["tickangle"] = -35
    fig_cc.update_layout(lyt_cc)
    st.plotly_chart(fig_cc, use_container_width=True)

    # Cheapest city per item
    section_header("Cheapest & Dearest City per Item")
    rows_cd = []
    for sno in cat_snos:
        sub = latest_all[latest_all["S. No"]==sno][["Cities","Value"]].dropna()
        if sub.empty: continue
        cheap = sub.nsmallest(1,"Value").iloc[0]
        dear  = sub.nlargest(1,"Value").iloc[0]
        rows_cd.append({
            "Item": short_map.get(sno,"")[:35],
            "Cheapest City": cheap["Cities"],
            "Cheapest Price": cheap["Value"],
            "Dearest City": dear["Cities"],
            "Dearest Price": dear["Value"],
            "Premium %": round((dear["Value"]-cheap["Value"])/cheap["Value"]*100,1)
        })
    df_cd = pd.DataFrame(rows_cd)
    st.dataframe(
        df_cd.style.format({"Cheapest Price":"Rs {:,.2f}","Dearest Price":"Rs {:,.2f}",
                            "Premium %":"{:.1f}%"}),
        use_container_width=True
    )

disclaimer_bar()
