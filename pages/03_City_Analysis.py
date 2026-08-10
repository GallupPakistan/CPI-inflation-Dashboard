import pandas as pd
pd.set_option("styler.render.max_elements", 500000)
"""
Page 3 — City Analysis
Compare prices across 17 cities for any item.
Which city is cheapest/dearest? How do cities track over time?
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import (load_data, get_city_pivot, get_latest_snapshot,
                         CITY_REGIONS, CATEGORY_COLORS, CATEGORIES)
from ui import (inject_css, inject_animation, page_header, section_header, sidebar_logo,
                disclaimer_bar, get_layout, ACCENT, UP, DOWN, MUTED,
                PALETTE, TEXT, CARD, BORDER, PANEL, BG)

st.set_page_config(page_title="City Analysis | Commodity Price Tracker", layout="wide", page_icon="🏙️")
inject_css()
inject_animation()
sidebar_logo()

df, canonical, short_map = load_data()
snap, latest_month = get_latest_snapshot()
latest_str = latest_month.strftime("%B %Y")

CITIES = sorted(df["Cities"].unique().tolist())
REGION_COLORS = {
    "Punjab/Federal": "#3B82F6",
    "Sindh":          "#10B981",
    "KPK":            "#F59E0B",
    "Balochistan":    "#EF4444",
}

page_header("🏙️ City Price Analysis",
            f"Compare prices across 17 cities — cheapest vs dearest — {latest_str}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Item Selection")
item_options = [f"{sno}. {short_map[sno]}" for sno in range(1,52) if sno in canonical]
selected_str = st.sidebar.selectbox("Select Item", item_options, index=6)
selected_sno = int(selected_str.split(".")[0])
selected_label = short_map[selected_sno]

n_months_trend = st.sidebar.slider("Trend: Last N months", 6, 84, 24)

tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ City Price Ranking",
    "📊 City Trend Over Time",
    "🌡️ City × Item Heatmap",
    "📐 Price Spread Analysis",
])

# ── TAB 1: City Ranking ───────────────────────────────────────────────────────
with tab1:
    section_header(f"City Price Ranking — {selected_label} ({latest_str})")
    city_piv = get_city_pivot(selected_sno)
    if city_piv.empty or latest_month not in city_piv.index:
        st.warning("No city data for this item/month.")
    else:
        latest_city = city_piv.loc[latest_month].sort_values(ascending=False).reset_index()
        latest_city.columns = ["City","Price"]
        latest_city["Region"] = latest_city["City"].map(CITY_REGIONS)
        latest_city["Color"]  = latest_city["Region"].map(REGION_COLORS)
        nat_avg = snap[snap["S. No"] == selected_sno]["Price"].values
        nat_avg = nat_avg[0] if len(nat_avg) else None

        col1, col2 = st.columns([3,1])
        with col1:
            fig = go.Figure(go.Bar(
                x=latest_city["Price"], y=latest_city["City"],
                orientation="h",
                marker_color=latest_city["Color"].tolist(),
                text=[f"Rs {v:,.2f}" for v in latest_city["Price"]],
                textposition="outside",
            cliponaxis=False,
                textfont=dict(size=11),
                customdata=latest_city["Region"].values,
                hovertemplate="<b>%{y}</b> (%{customdata})<br>Rs %{x:,.2f}<extra></extra>"
            ))
            if nat_avg:
                fig.add_vline(x=nat_avg, line_dash="dash", line_color=ACCENT,
                              annotation_text=f"National Avg: Rs {nat_avg:,.2f}",
                              annotation_font_color=ACCENT)
            lyt = get_layout(f"{selected_label} — City Prices ({latest_str})", height=480)
            lyt["xaxis"]["title"] = "Price (Rs)"
            lyt["yaxis"]["autorange"] = "reversed"
            fig.update_layout(lyt)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Stats
            cheapest = latest_city.iloc[-1]
            dearest  = latest_city.iloc[0]
            spread   = dearest["Price"] - cheapest["Price"]
            spread_pct = spread / cheapest["Price"] * 100
            st.markdown(f"""
            <div style='background:#111827;border:1px solid #1F2937;border-radius:10px;padding:16px;'>
            <p style='color:#E8A020;font-size:12px;font-weight:700;margin:0 0 12px 0;'>CITY STATS</p>
            <p style='color:#9CA3AF;font-size:11px;margin:0;'>DEAREST CITY</p>
            <p style='color:#EF4444;font-size:16px;font-weight:700;margin:2px 0 10px 0;'>
              {dearest["City"]}<br><span style='font-size:13px;'>Rs {dearest["Price"]:,.2f}</span></p>
            <p style='color:#9CA3AF;font-size:11px;margin:0;'>CHEAPEST CITY</p>
            <p style='color:#10B981;font-size:16px;font-weight:700;margin:2px 0 10px 0;'>
              {cheapest["City"]}<br><span style='font-size:13px;'>Rs {cheapest["Price"]:,.2f}</span></p>
            <p style='color:#9CA3AF;font-size:11px;margin:0;'>PRICE SPREAD</p>
            <p style='color:#F9FAFB;font-size:16px;font-weight:700;margin:2px 0 10px 0;'>
              Rs {spread:,.2f}<br><span style='font-size:13px;color:#F59E0B;'>+{spread_pct:.1f}% premium</span></p>
            {"<p style='color:#9CA3AF;font-size:11px;margin:0;'>NATIONAL AVG</p><p style='color:#E8A020;font-size:16px;font-weight:700;margin:2px 0 0 0;'>Rs "+f"{nat_avg:,.2f}</p>" if nat_avg else ""}
            </div>
            """, unsafe_allow_html=True)

            # Region legend
            st.markdown("<br>", unsafe_allow_html=True)
            for region, color in REGION_COLORS.items():
                cities_in = [c for c, r in CITY_REGIONS.items() if r == region]
                st.markdown(f"""
                <div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>
                  <div style='width:12px;height:12px;border-radius:2px;background:{color};'></div>
                  <span style='color:#9CA3AF;font-size:11px;'>{region} ({len(cities_in)})</span>
                </div>""", unsafe_allow_html=True)

    # City rankings for ALL items latest month
    st.markdown("---")
    section_header(f"All-City Price Comparison — Select Item ({latest_str})")
    # City pivot for all items
    latest_all = df[df["Month"] == latest_month].copy()
    city_item_pivot = latest_all.pivot_table(index="Cities", columns="S. No", values="Value")

    # Normalise to national avg = 100
    nat_avgs = snap.set_index("S. No")["Price"]
    city_norm = city_item_pivot.div(nat_avgs, axis=1) * 100

    fig_norm = go.Figure(go.Heatmap(
        z=city_norm.values,
        x=[short_map.get(c, str(c))[:25] for c in city_norm.columns],
        y=city_norm.index.tolist(),
        colorscale=[[0,"#10B981"],[0.85,"#1F2937"],[1,"#EF4444"]],
        zmid=100,
        colorbar=dict(title=dict(text="Title", font=dict(color=MUTED)), tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b> — %{x}<br>%{z:.1f}% of national avg<extra></extra>",
        xgap=1, ygap=1,
    ))
    lyt_n = get_layout("City Prices vs National Average (100 = national avg)", height=460)
    lyt_n["xaxis"]["tickangle"] = -45
    lyt_n["xaxis"]["tickfont"]  = dict(size=9, color=MUTED)
    fig_norm.update_layout(lyt_n)
    st.plotly_chart(fig_norm, use_container_width=True)

# ── TAB 2: City Trend ─────────────────────────────────────────────────────────
with tab2:
    section_header(f"City Price Trend — {selected_label}")
    city_piv = get_city_pivot(selected_sno)
    if city_piv.empty:
        st.warning("No city data available.")
    else:
        city_piv_f = city_piv.tail(n_months_trend)
        selected_cities = st.multiselect(
            "Select Cities", CITIES,
            default=["Karachi","Lahore","Islamabad","Peshawar","Quetta"],
            key="city_trend_sel"
        )
        fig_ct = go.Figure()
        for city in selected_cities:
            if city not in city_piv_f.columns:
                continue
            color = REGION_COLORS.get(CITY_REGIONS.get(city,""), ACCENT)
            fig_ct.add_trace(go.Scatter(
                x=city_piv_f.index.strftime("%b %y"),
                y=city_piv_f[city],
                name=city, mode="lines+markers",
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{city}</b><br>%{{x}}: Rs %{{y:,.2f}}<extra></extra>"
            ))
        # National avg line
        nat_piv = df[df["S. No"]==selected_sno].drop_duplicates("Month").set_index("Month")["Average Price"].sort_index()
        nat_piv_f = nat_piv.tail(n_months_trend)
        fig_ct.add_trace(go.Scatter(
            x=nat_piv_f.index.strftime("%b %y"),
            y=nat_piv_f,
            name="National Avg",
            line=dict(color=ACCENT, width=2.5, dash="dash"),
            mode="lines",
        ))
        lyt_ct = get_layout(f"{selected_label} — City Price Trend", height=440)
        lyt_ct["yaxis"]["title"] = "Price (Rs)"
        fig_ct.update_layout(lyt_ct)
        st.plotly_chart(fig_ct, use_container_width=True)

# ── TAB 3: City × Item Heatmap ────────────────────────────────────────────────
with tab3:
    section_header(f"City × Item Price Heatmap — {latest_str}")
    cat_sel = st.selectbox("Filter by Category", ["All"] + list(CATEGORIES.keys()), key="ci_cat")

    latest_all = df[df["Month"] == latest_month]
    if cat_sel != "All":
        snos_in_cat = CATEGORIES[cat_sel]
        latest_all = latest_all[latest_all["S. No"].isin(snos_in_cat)]

    city_item = latest_all.pivot_table(index="Cities", columns="S. No", values="Value")
    # Normalise each item to mean = 100 across cities
    city_item_norm = city_item.div(city_item.mean()) * 100
    x_labels_ci = [short_map.get(c,"")[:22] for c in city_item_norm.columns]

    fig_ci = go.Figure(go.Heatmap(
        z=city_item_norm.values,
        x=x_labels_ci,
        y=city_item_norm.index.tolist(),
        colorscale=[[0,"#10B981"],[0.85,"#1F2937"],[1,"#EF4444"]],
        zmid=100,
        colorbar=dict(title=dict(text="Title", font=dict(color=MUTED)), tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b> — %{x}<br>%{z:.1f}% of item avg<extra></extra>",
        xgap=1, ygap=1
    ))
    lyt_ci = get_layout("City × Item — Normalised to Item Mean (100 = avg across cities)", height=500)
    lyt_ci["xaxis"]["tickangle"] = -45
    lyt_ci["xaxis"]["tickfont"]  = dict(size=9, color=MUTED)
    fig_ci.update_layout(lyt_ci)
    st.plotly_chart(fig_ci, use_container_width=True)

# ── TAB 4: Price Spread ───────────────────────────────────────────────────────
with tab4:
    section_header(f"Price Spread (Max − Min across Cities) — {latest_str}")
    latest_all = df[df["Month"] == latest_month]
    city_spread = latest_all.groupby("S. No")["Value"].agg(
        Max="max", Min="min", Mean="mean", Std="std"
    ).reset_index()
    city_spread["Spread"] = city_spread["Max"] - city_spread["Min"]
    city_spread["Spread%"] = (city_spread["Spread"] / city_spread["Min"] * 100).round(1)
    city_spread["Item"] = city_spread["S. No"].map(short_map)
    city_spread = city_spread.sort_values("Spread%", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig_sp = go.Figure(go.Bar(
            x=city_spread["Spread%"].head(20),
            y=city_spread["Item"].head(20),
            orientation="h",
            marker_color=ACCENT,
            text=[f"{v:.1f}%" for v in city_spread["Spread%"].head(20)],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=11),
            hovertemplate="<b>%{y}</b><br>Spread: %{x:.1f}% above cheapest city<extra></extra>"
        ))
        lyt_sp = get_layout("Top 20 Items by Price Spread % (Dearest vs Cheapest City)", height=480)
        lyt_sp["xaxis"]["title"] = "Spread %"
        lyt_sp["yaxis"]["autorange"] = "reversed"
        fig_sp.update_layout(lyt_sp)
        st.plotly_chart(fig_sp, use_container_width=True)

    with col2:
        section_header("Price Spread Table — All Items")
        display_sp = city_spread[["Item","Min","Max","Mean","Spread","Spread%"]].copy()
        display_sp.columns = ["Item","Min (Rs)","Max (Rs)","Mean (Rs)","Spread (Rs)","Spread %"]
        st.dataframe(
            display_sp.style
            .format({"Min (Rs)":"Rs {:,.2f}","Max (Rs)":"Rs {:,.2f}",
                     "Mean (Rs)":"Rs {:,.2f}","Spread (Rs)":"Rs {:,.2f}",
                     "Spread %":"{:.1f}%"})
            .map(lambda v: f"color:#EF4444;font-weight:700" if isinstance(v,float) and v>50 else "",
                      subset=["Spread %"]),
            use_container_width=True, height=480
        )

disclaimer_bar()
