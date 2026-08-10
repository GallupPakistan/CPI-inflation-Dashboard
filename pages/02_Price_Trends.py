"""Page 2 — Price Trends (improved: date slider, item deep-dive, volatility)"""
import pandas as pd
pd.set_option("styler.render.max_elements", 500000)

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from data_loader import load_data, get_national_pivot, get_yoy, get_mom, get_latest_snapshot, CATEGORIES, CATEGORY_COLORS
from ui import (inject_css, inject_animation, page_header, section_header, sidebar_logo,
                disclaimer_bar, get_layout, ACCENT, UP, DOWN, MUTED, PALETTE, TEXT, CARD, BORDER)

st.set_page_config(page_title="Price Trends | Commodity Price Tracker", layout="wide", page_icon="📈")
inject_css()
inject_animation()
sidebar_logo()

df, canonical, short_map = load_data()
pivot  = get_national_pivot()
yoy    = get_yoy()
mom_df = get_mom()
snap, latest_month = get_latest_snapshot()
latest_str = latest_month.strftime("%B %Y")

all_months = pivot.index.strftime("%b %Y").tolist()
all_items  = [(sno, short_map[sno]) for sno in range(1,52) if sno in pivot.columns]
item_opts  = [f"{sno}. {name}" for sno, name in all_items]

page_header("📈 Price Trends", f"Historical price charts — monthly national averages · up to {latest_str}")

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Item Selection")
selected_strs = st.sidebar.multiselect(
    "Select Items (max 8)", item_opts,
    default=[item_opts[6], item_opts[10], item_opts[0], item_opts[22]],
    max_selections=8
)
selected_snos = [int(s.split(".")[0]) for s in selected_strs] if selected_strs else [7,11,1,23]

st.sidebar.markdown("### Date Range")
range_sel = st.sidebar.select_slider(
    "From — To",
    options=all_months,
    value=(all_months[0], all_months[-1])
)
i0 = all_months.index(range_sel[0])
i1 = all_months.index(range_sel[1]) + 1
pivot_f = pivot.iloc[i0:i1]
yoy_f   = yoy.iloc[i0:i1]
mom_f   = mom_df.iloc[i0:i1]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Price Chart",
    "📉 YoY / MoM",
    "🔍 Item Deep Dive",
    "📅 Annual Averages",
    "🔥 MoM Heatmap",
])

# ── TAB 1: Price Chart ────────────────────────────────────────────────────────
with tab1:
    section_header("National Average Price (Rs) — Monthly")
    col_opt1, col_opt2 = st.columns([3,1])
    with col_opt2:
        log_scale = st.checkbox("Log scale (Y)", value=False, key="log_y")
        show_band = st.checkbox("Show ±1 SD band", value=False, key="sd_band")

    fig = go.Figure()
    for i, sno in enumerate(selected_snos):
        if sno not in pivot_f.columns: continue
        label = short_map.get(sno, f"Item {sno}")
        y = pivot_f[sno]
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x=pivot_f.index.strftime("%b %y"), y=y,
            name=label, mode="lines+markers",
            line=dict(color=color, width=2),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: Rs %{{y:,.2f}}<extra></extra>"
        ))
        if show_band and len(y.dropna()) > 3:
            roll_mean = y.rolling(3, min_periods=1).mean()
            roll_std  = y.rolling(3, min_periods=1).std().fillna(0)
            xs = pivot_f.index.strftime("%b %y").tolist()
            fig.add_trace(go.Scatter(
                x=xs + xs[::-1],
                y=(roll_mean+roll_std).tolist() + (roll_mean-roll_std).tolist()[::-1],
                fill="toself", fillcolor=f"rgba{tuple(int(color.lstrip('#')[j:j+2],16) for j in (0,2,4))+(0.08,)}",
                line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
            ))

    lyt = get_layout("National Average Price (Rs)", height=460)
    lyt["yaxis"]["title"] = "Price (Rs)"
    if log_scale: lyt["yaxis"]["type"] = "log"
    fig.update_layout(lyt)
    st.plotly_chart(fig, use_container_width=True)

    # Stats row
    if selected_snos:
        section_header("Price Statistics — Selected Items & Date Range")
        cols = st.columns(min(len(selected_snos), 4))
        for col, sno in zip(cols, selected_snos[:4]):
            label = short_map.get(sno, f"Item {sno}")
            prices = pivot_f[sno].dropna() if sno in pivot_f.columns else pd.Series()
            if len(prices) == 0: continue
            cur = prices.iloc[-1]; mn = prices.min(); mx = prices.max(); avg = prices.mean()
            chg = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100 if prices.iloc[0] else 0
            col.markdown(f"""
            <div style='background:#111827;border:1px solid #1F2937;border-radius:8px;padding:12px;'>
              <p style='color:#E8A020;font-size:11px;font-weight:700;margin:0 0 4px 0;'>{label[:32]}</p>
              <p style='color:#F9FAFB;font-size:20px;font-weight:700;margin:0;'>Rs {cur:,.2f}</p>
              <p style='color:#9CA3AF;font-size:11px;margin:4px 0 0 0;'>
                Min Rs {mn:,.2f} · Max Rs {mx:,.2f}<br>
                Avg Rs {avg:,.2f} · Change <span style='color:{"#EF4444" if chg>0 else "#10B981"}'>{chg:+.1f}%</span>
              </p>
            </div>""", unsafe_allow_html=True)

# ── TAB 2: YoY / MoM ─────────────────────────────────────────────────────────
with tab2:
    section_header("Year-on-Year % Change Trend")
    fig_yoy = go.Figure()
    for i, sno in enumerate(selected_snos):
        if sno not in yoy_f.columns: continue
        label = short_map.get(sno, f"Item {sno}")
        s = yoy_f[sno].dropna()
        fig_yoy.add_trace(go.Scatter(
            x=s.index.strftime("%b %y"), y=s, name=label, mode="lines+markers",
            line=dict(color=PALETTE[i%len(PALETTE)], width=2),
        ))
    fig_yoy.add_hline(y=0, line_dash="dash", line_color=MUTED)
    lyt_y = get_layout("YoY % Change", height=400)
    lyt_y["yaxis"]["title"] = "YoY %"
    fig_yoy.update_layout(lyt_y)
    st.plotly_chart(fig_yoy, use_container_width=True)

    section_header("Month-on-Month % Change")
    fig_mom = go.Figure()
    for i, sno in enumerate(selected_snos):
        if sno not in mom_f.columns: continue
        label = short_map.get(sno, f"Item {sno}")
        s = mom_f[sno].dropna()
        fig_mom.add_trace(go.Bar(
            x=s.index.strftime("%b %y"), y=s, name=label,
            marker_color=PALETTE[i%len(PALETTE)],
        ))
    lyt_m = get_layout("MoM % Change", height=350)
    lyt_m["yaxis"]["title"] = "MoM %"
    lyt_m["barmode"] = "group"
    fig_mom.update_layout(lyt_m)
    st.plotly_chart(fig_mom, use_container_width=True)

# ── TAB 3: Item Deep Dive ─────────────────────────────────────────────────────
with tab3:
    section_header("Single-Item Deep Dive")
    col_sel, col_range = st.columns([2,2])
    with col_sel:
        item_dd = st.selectbox("Select Item", item_opts, index=6, key="dd_item")
    sno_dd = int(item_dd.split(".")[0])
    label_dd = short_map.get(sno_dd, "")

    prices_dd = pivot[sno_dd].dropna() if sno_dd in pivot.columns else pd.Series()
    if len(prices_dd) == 0:
        st.warning("No data for this item.")
    else:
        # Date slider using actual month indices
        months_dd = prices_dd.index.strftime("%b %Y").tolist()
        date_range_dd = st.select_slider(
            "Date Range", options=months_dd,
            value=(months_dd[0], months_dd[-1]), key="dd_range"
        )
        i0_dd = months_dd.index(date_range_dd[0])
        i1_dd = months_dd.index(date_range_dd[1]) + 1
        prices_sel = prices_dd.iloc[i0_dd:i1_dd]
        mom_sel    = mom_df[sno_dd].iloc[i0_dd:i1_dd] if sno_dd in mom_df.columns else pd.Series()
        yoy_sel    = yoy[sno_dd].iloc[i0_dd:i1_dd] if sno_dd in yoy.columns else pd.Series()

        # KPIs
        cur_p = prices_sel.iloc[-1]; start_p = prices_sel.iloc[0]
        total_chg = (cur_p - start_p)/start_p*100
        vol = prices_sel.pct_change().std()*100
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Current Price", f"Rs {cur_p:,.2f}")
        c2.metric("Period Start", f"Rs {start_p:,.2f}")
        c3.metric("Total Change", f"{total_chg:+.1f}%")
        c4.metric("Monthly Volatility", f"{vol:.1f}%")

        # Price + MoM combo
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=prices_sel.index.strftime("%b %y"), y=prices_sel,
            name="Price (Rs)", mode="lines+markers",
            line=dict(color=ACCENT, width=2.5),
            hovertemplate="Rs %{y:,.2f}<extra></extra>", yaxis="y1"
        ))
        if len(mom_sel.dropna()) > 0:
            fig_dd.add_trace(go.Bar(
                x=mom_sel.dropna().index.strftime("%b %y"), y=mom_sel.dropna(),
                name="MoM %",
                marker_color=[UP if v<0 else DOWN for v in mom_sel.dropna()],
                opacity=0.5, yaxis="y2",
                hovertemplate="MoM: %{y:.2f}%<extra></extra>"
            ))
        lyt_dd = get_layout(f"{label_dd} — Price & MoM %", height=420)
        lyt_dd["yaxis"]  = dict(**lyt_dd["yaxis"], title="Price (Rs)")
        lyt_dd["yaxis2"] = dict(title="MoM %", overlaying="y", side="right",
                                 gridcolor="rgba(0,0,0,0)", tickfont=dict(color=MUTED, size=10))
        lyt_dd["barmode"] = "overlay"
        fig_dd.update_layout(lyt_dd)
        st.plotly_chart(fig_dd, use_container_width=True)

        # YoY trend
        if len(yoy_sel.dropna()) > 0:
            fig_yy = go.Figure(go.Scatter(
                x=yoy_sel.dropna().index.strftime("%b %y"), y=yoy_sel.dropna(),
                mode="lines+markers", fill="tozeroy",
                line=dict(color=ACCENT, width=2),
                fillcolor="rgba(232,160,32,0.1)",
                hovertemplate="YoY: %{y:.2f}%<extra></extra>"
            ))
            fig_yy.add_hline(y=0, line_dash="dash", line_color=MUTED)
            lyt_yy = get_layout(f"{label_dd} — YoY % Trend", height=300)
            lyt_yy["yaxis"]["title"] = "YoY %"
            fig_yy.update_layout(lyt_yy)
            st.plotly_chart(fig_yy, use_container_width=True)

        # Min/Max city prices for latest month
        st.markdown("---")
        section_header(f"City Prices — {label_dd} ({latest_str})")
        city_latest = df[(df["S. No"]==sno_dd) & (df["Month"]==latest_month)][["Cities","Value"]].sort_values("Value", ascending=False)
        if not city_latest.empty:
            fig_c = go.Figure(go.Bar(
                x=city_latest["Value"], y=city_latest["Cities"], orientation="h",
                marker_color=ACCENT,
                text=[f"Rs {v:,.2f}" for v in city_latest["Value"]],
                textposition="outside", textfont=dict(size=10),
            ))
            nat = snap[snap["S. No"]==sno_dd]["Price"].values
            if len(nat): fig_c.add_vline(x=nat[0], line_dash="dash", line_color="#10B981",
                annotation_text=f"Nat. Avg: Rs {nat[0]:,.2f}", annotation_font_color="#10B981")
            lyt_c = get_layout("", height=400)
            lyt_c["xaxis"]["title"] = "Price (Rs)"
            lyt_c["xaxis"]["range"] = [0, city_latest["Value"].max()*1.25]
            lyt_c["yaxis"]["autorange"] = "reversed"
            lyt_c["margin"]["r"] = 120
            fig_c.update_layout(lyt_c)
            st.plotly_chart(fig_c, use_container_width=True)

# ── TAB 4: Annual Averages ────────────────────────────────────────────────────
with tab4:
    section_header("Annual Average Price — All Years")
    ann = df[df["S. No"].between(1,51)].drop_duplicates(["Month","S. No"]).copy()
    ann["Year"] = ann["Month"].dt.year
    ann_avg = ann.groupby(["Year","S. No"])["Average Price"].mean().unstack()

    fig_ann = go.Figure()
    for i, sno in enumerate(selected_snos):
        if sno not in ann_avg.columns: continue
        label = short_map.get(sno, f"Item {sno}")
        fig_ann.add_trace(go.Scatter(
            x=ann_avg.index.astype(str), y=ann_avg[sno],
            name=label, mode="lines+markers",
            line=dict(color=PALETTE[i%len(PALETTE)], width=2.5),
            marker=dict(size=8),
        ))
    lyt_ann = get_layout("Annual Average Price (Rs)", height=420)
    lyt_ann["yaxis"]["title"] = "Price (Rs)"
    fig_ann.update_layout(lyt_ann)
    st.plotly_chart(fig_ann, use_container_width=True)

    section_header("Annual YoY % Change")
    ann_yoy = ann_avg.pct_change() * 100
    fig_ay = go.Figure()
    for i, sno in enumerate(selected_snos):
        if sno not in ann_yoy.columns: continue
        label = short_map.get(sno, f"Item {sno}")
        vals = ann_yoy[sno].dropna()
        fig_ay.add_trace(go.Bar(
            x=vals.index.astype(str), y=vals, name=label,
            marker_color=PALETTE[i%len(PALETTE)],
        ))
    lyt_ay = get_layout("Annual YoY % Change", height=360)
    lyt_ay["barmode"] = "group"
    fig_ay.update_layout(lyt_ay)
    st.plotly_chart(fig_ay, use_container_width=True)

# ── TAB 5: MoM Heatmap ───────────────────────────────────────────────────────
with tab5:
    section_header("MoM % Change Heatmap — All Items × All Months")
    n_hm = st.slider("Show last N months", 6, 84, 24, key="hm_months")
    mom_sub = mom_df.tail(n_hm)
    fig_hm = go.Figure(go.Heatmap(
        z=mom_sub.values.T,
        x=mom_sub.index.strftime("%b %y").tolist(),
        y=[short_map.get(c,"")[:30] for c in mom_sub.columns],
        colorscale=[[0,"#10B981"],[0.4,"#1F2937"],[0.5,"#1F2937"],[1,"#EF4444"]],
        zmid=0,
        colorbar=dict(title=dict(text="MoM %", font=dict(color=MUTED)), tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}%<extra></extra>",
        xgap=1, ygap=1,
    ))
    lyt_hm = get_layout("", height=max(600, len(mom_sub.columns)*14))
    lyt_hm["xaxis"]["tickangle"] = -45
    lyt_hm["yaxis"]["tickfont"] = dict(size=10, color=MUTED)
    fig_hm.update_layout(lyt_hm)
    st.plotly_chart(fig_hm, use_container_width=True)

disclaimer_bar()
