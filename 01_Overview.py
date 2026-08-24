"""Page 1 — Overview"""
import pandas as pd
pd.set_option("styler.render.max_elements", 500000)

import streamlit as st
import plotly.graph_objects as go
from data_loader import get_latest_snapshot, get_national_pivot, get_meta, CATEGORIES, CATEGORY_COLORS
from ui import (inject_css, inject_animation, page_header, section_header, kpi_row,
                sidebar_logo, disclaimer_bar, get_layout,
                ACCENT, UP, DOWN, MUTED, PALETTE, TEXT)

st.set_page_config(page_title="Overview | Commodity Price Tracker", layout="wide", page_icon="🏠")
inject_css()
inject_animation()
sidebar_logo()

snap, latest_month = get_latest_snapshot()
meta  = get_meta()
pivot = get_national_pivot()
latest_str = latest_month.strftime("%B %Y")
first_str  = meta["first_month"].strftime("%b %Y")

# ── Gallup Pakistan Branding Hero ────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0D1220,#FFFFFF,#FFFFFF);
    border-radius:16px;padding:28px 32px;margin-bottom:24px;
    border:1px solid #E5E7EB;position:relative;overflow:hidden;">
  <!-- Decorative glow -->
  <div style="position:absolute;top:-60px;right:-60px;width:220px;height:220px;
      background:radial-gradient(circle,rgba(232,160,32,0.08),transparent 70%);
      border-radius:50%;pointer-events:none;"></div>
  <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
    <div>
      <img src="https://www.gallup.com.pk/Logo.png"
           style="height:52px;filter:brightness(1.1);"
           onerror="this.style.display='none'">
    </div>
    <div style="flex:1;min-width:200px;">
      <p style="color:#4B5563;font-size:11px;font-weight:600;text-transform:uppercase;
         letter-spacing:0.1em;margin:0 0 4px 0;">Gallup Pakistan Digital Analytics</p>
      <h1 style="color:#111827;font-size:26px;font-weight:800;margin:0;line-height:1.2;">
        Pakistan Commodity Price Tracker</h1>
      <p style="color:#4B5563;font-size:13px;margin:6px 0 0 0;">
        Sensitive Price Indicator · {meta['n_items']} essential items · {meta['n_cities']} cities ·
        <span style="color:#E8A020;">Latest: {latest_str}</span> ·
        Coverage: {first_str} – {latest_str}
      </p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

rising   = int((snap["MoM%"] > 0).sum())
falling  = int((snap["MoM%"] < 0).sum())
top_riser  = snap.nlargest(1,"MoM%").iloc[0]
top_faller = snap.nsmallest(1,"MoM%").iloc[0]
avg_mom  = snap["MoM%"].mean()
avg_yoy  = snap["YoY%"].mean()

kpi_row([
    {"label": "Items Rising (MoM)",  "value": str(rising),  "delta": f"of {meta['n_items']} tracked", "delta_up": True},
    {"label": "Items Falling (MoM)", "value": str(falling), "delta": f"of {meta['n_items']} tracked", "delta_up": False},
    {"label": "Biggest MoM Surge",   "value": top_riser["Short"][:22],  "delta": f"+{top_riser['MoM%']:.1f}%",  "delta_up": True},
    {"label": "Biggest MoM Drop",    "value": top_faller["Short"][:22], "delta": f"{top_faller['MoM%']:.1f}%", "delta_up": False},
    {"label": "Avg MoM Change",      "value": f"{avg_mom:+.2f}%", "delta_up": avg_mom > 0},
    {"label": "Avg YoY Change",      "value": f"{avg_yoy:+.2f}%", "delta_up": avg_yoy > 0},
])
st.markdown("---")

# ── Top 10 Risers / Fallers ──────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    section_header(f"Top 10 Price Risers — MoM % ({latest_str})")
    t10 = snap.nlargest(10,"MoM%")
    mx  = t10["MoM%"].max()
    fig = go.Figure(go.Bar(
        x=t10["MoM%"], y=t10["Short"], orientation="h",
        marker_color=[CATEGORY_COLORS.get(c,ACCENT) for c in t10["Category"]],
        text=[f"+{v:.1f}%" for v in t10["MoM%"]],
        textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        customdata=t10[["YoY%","Price"]].values,
        hovertemplate="<b>%{y}</b><br>MoM: +%{x:.2f}%<br>YoY: %{customdata[0]:.2f}%<br>Rs %{customdata[1]:,.2f}<extra></extra>"
    ))
    lyt = get_layout("", height=440)
    lyt["xaxis"]["range"]  = [0, mx * 1.35]
    lyt["xaxis"]["title"]  = "MoM % Change"
    lyt["yaxis"]["autorange"] = "reversed"
    lyt["margin"]["r"] = 90
    fig.update_layout(lyt); st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header(f"Top 10 Price Fallers — MoM % ({latest_str})")
    b10 = snap.nsmallest(10,"MoM%")
    mf  = abs(b10["MoM%"].min())
    fig2 = go.Figure(go.Bar(
        x=b10["MoM%"], y=b10["Short"], orientation="h",
        marker_color=DOWN,
        text=[f"{v:.1f}%" for v in b10["MoM%"]],
        textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        customdata=b10[["YoY%","Price"]].values,
        hovertemplate="<b>%{y}</b><br>MoM: %{x:.2f}%<br>YoY: %{customdata[0]:.2f}%<br>Rs %{customdata[1]:,.2f}<extra></extra>"
    ))
    lyt2 = get_layout("", height=440)
    lyt2["xaxis"]["range"]  = [-(mf * 1.35), 0]
    lyt2["xaxis"]["title"]  = "MoM % Change"
    lyt2["yaxis"]["autorange"] = "reversed"
    lyt2["margin"]["l"] = 170
    fig2.update_layout(lyt2); st.plotly_chart(fig2, use_container_width=True)

# ── YoY Top Risers + Category Summary ────────────────────────────────────────
col3, col4 = st.columns(2)
with col3:
    section_header(f"Top 10 YoY % ({latest_str} vs {(latest_month - pd.DateOffset(months=12)).strftime('%b %Y')})")
    ty = snap.dropna(subset=["YoY%"]).nlargest(10,"YoY%")
    my = ty["YoY%"].max()
    fig3 = go.Figure(go.Bar(
        x=ty["YoY%"], y=ty["Short"], orientation="h",
        marker_color=ACCENT,
        text=[f"{v:+.1f}%" for v in ty["YoY%"]],
        textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>YoY: %{x:.2f}%<extra></extra>"
    ))
    lyt3 = get_layout("", height=440)
    lyt3["xaxis"]["range"]  = [0, my * 1.35]
    lyt3["xaxis"]["title"]  = "YoY % Change"
    lyt3["yaxis"]["autorange"] = "reversed"
    lyt3["margin"]["r"] = 90
    fig3.update_layout(lyt3); st.plotly_chart(fig3, use_container_width=True)

with col4:
    section_header("Average MoM % Change by Category")
    cm = snap.groupby("Category")["MoM%"].mean().sort_values(ascending=False).reset_index()
    ma = cm["MoM%"].abs().max()
    fig4 = go.Figure(go.Bar(
        x=cm["MoM%"], y=cm["Category"], orientation="h",
        marker_color=[CATEGORY_COLORS.get(c,ACCENT) for c in cm["Category"]],
        text=[f"{v:+.2f}%" for v in cm["MoM%"]],
        textposition="outside", textfont=dict(size=10, color=TEXT),
            cliponaxis=False,
    ))
    lyt4 = get_layout("", height=440)
    lyt4["xaxis"]["range"]  = [-(ma*0.3), ma*1.4]
    lyt4["xaxis"]["title"]  = "Avg MoM %"
    lyt4["yaxis"]["autorange"] = "reversed"
    lyt4["margin"]["r"] = 90
    fig4.update_layout(lyt4); st.plotly_chart(fig4, use_container_width=True)

# ── All 51 Items — horizontal bar (replaces broken treemap) ──────────────────
section_header("All Items — MoM % Change (colour-coded)")
snap_s = snap.sort_values("MoM%", ascending=False).copy()
bar_colors = []
for v in snap_s["MoM%"]:
    if v > 10:    bar_colors.append("#EF4444")
    elif v > 0:   bar_colors.append("#F59E0B")
    elif v > -10: bar_colors.append("#34D399")
    else:         bar_colors.append("#10B981")

fig_all = go.Figure(go.Bar(
    x=snap_s["MoM%"], y=snap_s["Short"], orientation="h",
    marker_color=bar_colors,
    text=[f"{v:+.1f}%" for v in snap_s["MoM%"]],
    textposition="outside", textfont=dict(size=9, color=TEXT),
            cliponaxis=False,
    customdata=snap_s[["YoY%","Price","Category"]].values,
    hovertemplate="<b>%{y}</b><br>%{customdata[2]}<br>MoM: %{x:+.2f}%<br>YoY: %{customdata[0]:+.2f}%<br>Rs %{customdata[1]:,.2f}<extra></extra>",
))
# Symmetric range based on actual min/max so both +ve and -ve labels are visible
_max_pos = snap_s["MoM%"].max()   # e.g. +19.8 (Petrol)
_max_neg = snap_s["MoM%"].min()   # e.g. -23.9 (Tomatoes)
_pad_r   = _max_pos * 1.25        # 25% breathing room on right
_pad_l   = _max_neg * 1.25        # 25% breathing room on left (negative × 1.25 = more left)
lyt_all = get_layout(f"All 51 Items — MoM % Change ({latest_str})", height=1100)
lyt_all["xaxis"]["range"]    = [_pad_l, _pad_r]
lyt_all["xaxis"]["title"]    = "MoM % Change"
lyt_all["yaxis"]["autorange"] = "reversed"
lyt_all["yaxis"]["tickfont"]  = dict(size=10, color=MUTED)
lyt_all["margin"]["r"] = 110
lyt_all["margin"]["l"] = 210
fig_all.add_vline(x=0, line_dash="solid", line_color=MUTED, line_width=1)
fig_all.update_layout(lyt_all)
st.plotly_chart(fig_all, use_container_width=True)

# ── Key item price trends — last 12 months ────────────────────────────────────
section_header("Key Item Price Trends — Last 12 Months (National Average, Rs)")
KEY_ITEMS = {7:"Chicken",11:"Eggs",23:"Tomatoes",21:"Potatoes",
             1:"Wheat Flour",47:"Petrol",49:"LPG",24:"Sugar"}
last12 = pivot.tail(12)
fig_tr = go.Figure()
for i,(sno,label) in enumerate(KEY_ITEMS.items()):
    if sno in last12.columns:
        fig_tr.add_trace(go.Scatter(
            x=last12.index.strftime("%b %y"), y=last12[sno],
            name=label, mode="lines+markers",
            line=dict(width=2, color=PALETTE[i%len(PALETTE)]),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: Rs %{{y:,.2f}}<extra></extra>"
        ))
lyt_t = get_layout("Price Trend — Last 12 Months", height=460)
lyt_t["yaxis"]["title"] = "Price (Rs)"
fig_tr.update_layout(lyt_t)
st.plotly_chart(fig_tr, use_container_width=True)

# ── Complete price snapshot table ─────────────────────────────────────────────
section_header("Complete Price Snapshot — All 51 Items")
col_a, col_b, col_c = st.columns([2,1,1])
with col_b:
    cat_filter = st.selectbox("Filter Category", ["All"]+list(CATEGORIES.keys()), key="ov_cat")
with col_c:
    sort_by = st.selectbox("Sort by", ["MoM%","YoY%","Price","S. No"], key="ov_sort")

df_show = snap if cat_filter=="All" else snap[snap["Category"]==cat_filter]
df_show = df_show.sort_values(sort_by, ascending=(sort_by=="S. No"))
disp = df_show[["S. No","Short","Category","Price","MoM%","YoY%","Cumulative%"]].copy()
disp.columns = ["#","Item","Category","Price (Rs)","MoM %","YoY %","Since Jan 2019 %"]

def _sp(v):
    if not isinstance(v,(int,float)): return ""
    if v>10:  return "color:#EF4444;font-weight:700"
    if v>0:   return "color:#F59E0B"
    if v<-10: return "color:#10B981;font-weight:700"
    if v<0:   return "color:#10B981"
    return ""

st.dataframe(
    disp.style
        .map(_sp, subset=["MoM %","YoY %","Since Jan 2019 %"])
        .format({"Price (Rs)":"Rs {:,.2f}","MoM %":"{:+.2f}%","YoY %":"{:+.2f}%","Since Jan 2019 %":"{:+.1f}%"}),
    use_container_width=True, height=420
)
disclaimer_bar()
