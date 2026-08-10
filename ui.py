"""
Shared chart layout, CSS, and UI components for SPI Dashboard.
"""
import plotly.graph_objects as go
import streamlit as st

# ── Design tokens ──────────────────────────────────────────────────────────────
BG        = "#0A0E1A"
CARD      = "#111827"
PANEL     = "#1F2937"
BORDER    = "#374151"
TEXT      = "#F9FAFB"
MUTED     = "#9CA3AF"
ACCENT    = "#E8A020"
UP        = "#10B981"
DOWN      = "#EF4444"
NEUTRAL   = "#6B7280"

PALETTE = ["#E8A020","#3B82F6","#10B981","#EF4444","#8B5CF6",
           "#F97316","#06B6D4","#EC4899","#84CC16","#F59E0B",
           "#A78BFA","#14B8A6","#CBD5E1","#94A3B8","#6B7280"]

def get_layout(title="", height=420, margin=None):
    m = margin or dict(l=20, r=20, t=48 if title else 20, b=20)
    return dict(
        title=dict(text=title, font=dict(color=TEXT, size=14), x=0),
        height=height,
        margin=m,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, sans-serif", size=12),
        legend=dict(bgcolor=CARD, bordercolor=BORDER, borderwidth=1,
                    font=dict(color=TEXT, size=11)),
        xaxis=dict(gridcolor=PANEL, linecolor=BORDER, tickcolor=BORDER,
                   tickfont=dict(color=MUTED, size=11)),
        yaxis=dict(gridcolor=PANEL, linecolor=BORDER, tickcolor=BORDER,
                   tickfont=dict(color=MUTED, size=11)),
        hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER,
                        font=dict(color=TEXT, size=12)),
    )

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .main { background: #0A0E1A !important; }
    section[data-testid="stSidebar"] { background: #060A14 !important; border-right: 1px solid #1F2937; }
    .stTabs [data-baseweb="tab-list"] { background: #111827; border-radius: 8px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 6px; color: #9CA3AF;
        font-size: 13px; font-weight: 500; padding: 6px 14px; }
    .stTabs [aria-selected="true"] { background: #1F2937 !important; color: #E8A020 !important; }
    div[data-testid="metric-container"] { background: #111827; border: 1px solid #1F2937;
        border-radius: 10px; padding: 12px 16px; }
    .stDataFrame { background: #111827 !important; }
    div[data-testid="stSelectbox"] > div, div[data-testid="stMultiSelect"] > div {
        background: #111827; border-color: #374151; }
    .stRadio > div { background: transparent; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #111827; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
    h1,h2,h3 { color: #F9FAFB !important; }
    .block-container { padding-top: 1.5rem; }

    /* ── Page-load fade-in animation ── */
    @keyframes fadeSlideIn {
      from { opacity: 0; transform: translateY(18px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .block-container > div > div > div { animation: fadeSlideIn 0.45s ease both; }
    .block-container > div > div > div:nth-child(1)  { animation-delay: 0.00s; }
    .block-container > div > div > div:nth-child(2)  { animation-delay: 0.06s; }
    .block-container > div > div > div:nth-child(3)  { animation-delay: 0.12s; }
    .block-container > div > div > div:nth-child(4)  { animation-delay: 0.18s; }
    .block-container > div > div > div:nth-child(5)  { animation-delay: 0.24s; }
    .block-container > div > div > div:nth-child(6)  { animation-delay: 0.30s; }
    .block-container > div > div > div:nth-child(n+7) { animation-delay: 0.36s; }

    /* ── Metric card hover lift ── */
    div[data-testid="metric-container"] {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(232,160,32,0.12);
    }

    /* ── Highlighted chat input glow ── */
    @keyframes glow-pulse {
      0%,100% { box-shadow: 0 0 0 0 rgba(232,160,32,0.0); }
      50%      { box-shadow: 0 0 0 3px rgba(232,160,32,0.25); }
    }
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInputTextArea"] {
        border: 1.5px solid #E8A020 !important;
        border-radius: 12px !important;
        animation: glow-pulse 2.5s ease-in-out infinite;
        background: #111827 !important;
    }

    /* ── Button hover accent ── */
    .stButton > button {
        transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #E8A020 !important;
        color: #E8A020 !important;
    }

    /* ── Plotly chart subtle fade-in ── */
    div[data-testid="stPlotlyChart"] {
        animation: fadeSlideIn 0.5s ease both;
        animation-delay: 0.1s;
    }

    /* ── Section header accent line animate ── */
    @keyframes expandLine {
      from { width: 0; }
      to   { width: 100%; }
    }
    </style>
    """, unsafe_allow_html=True)

def inject_animation():
    pass  # Animation removed — was causing double scrollbar


def page_header(title, subtitle=""):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#111827,#0A0E1A);
        border-left:4px solid #E8A020;border-radius:0 10px 10px 0;
        padding:16px 20px;margin-bottom:20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <div>
          <h2 style="color:#F9FAFB;margin:0;font-size:22px;font-weight:700;">{title}</h2>
          {"<p style='color:#9CA3AF;margin:4px 0 0 0;font-size:13px;'>"+subtitle+"</p>" if subtitle else ""}
        </div>
        <div style="text-align:right;">
          <img src="https://www.gallup.com.pk/Logo.png"
               style="height:40px;opacity:0.85;" onerror="this.style.display='none'">
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def section_header(text):
    st.markdown(f"""
    <p style="color:#E8A020;font-size:13px;font-weight:600;text-transform:uppercase;
       letter-spacing:0.08em;margin:16px 0 8px 0;border-bottom:1px solid #1F2937;
       padding-bottom:6px;">{text}</p>
    """, unsafe_allow_html=True)

def metric_card(label, value, delta=None, delta_up=None, note=""):
    delta_color = UP if delta_up else (DOWN if delta_up is False else MUTED)
    arrow = "▲" if delta_up else ("▼" if delta_up is False else "")
    delta_html = f"<p style='color:{delta_color};font-size:12px;margin:2px 0 0 0;'>{arrow} {delta}</p>" if delta else ""
    note_html = f"<p style='color:{MUTED};font-size:11px;margin:2px 0 0 0;'>{note}</p>" if note else ""
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1F2937;border-radius:10px;
        padding:14px 16px;height:100%;">
      <p style="color:#9CA3AF;font-size:11px;font-weight:600;text-transform:uppercase;
         letter-spacing:0.06em;margin:0;">{label}</p>
      <p style="color:#F9FAFB;font-size:22px;font-weight:700;margin:4px 0 0 0;">{value}</p>
      {delta_html}{note_html}
    </div>
    """, unsafe_allow_html=True)

def kpi_row(metrics: list):
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            metric_card(m["label"], m["value"],
                        m.get("delta"), m.get("delta_up"),
                        m.get("note",""))

def change_chip(val, suffix="%"):
    if val is None or (isinstance(val, float) and __import__("math").isnan(val)):
        return f"<span style='color:{MUTED}'>N/A</span>"
    color = UP if val > 0 else (DOWN if val < 0 else NEUTRAL)
    arrow = "▲" if val > 0 else ("▼" if val < 0 else "—")
    return f"<span style='color:{color};font-weight:600;'>{arrow} {abs(val):.2f}{suffix}</span>"

def sidebar_logo():
    st.sidebar.markdown("""
    <div style="text-align:center;padding:12px 0 8px 0;border-bottom:1px solid #1F2937;margin-bottom:12px;">
      <img src="https://www.gallup.com.pk/Logo.png"
           style="height:48px;margin-bottom:6px;" onerror="this.style.display='none'">
      <p style="color:#E8A020;font-size:13px;font-weight:700;margin:0;">Gallup Pakistan</p>
      <p style="color:#9CA3AF;font-size:11px;margin:2px 0 0 0;">Commodity Price Tracker</p>
    </div>
    """, unsafe_allow_html=True)

def disclaimer_bar():
    st.markdown("---")
    st.markdown("""
    <div style="background:#111827;border-radius:8px;padding:10px 16px;text-align:center;">
      <p style="color:#6B7280;font-size:11px;margin:0;">
      Source: Pakistan Bureau of Statistics (PBS) — <a href="https://www.pbs.gov.pk" style="color:#E8A020;">www.pbs.gov.pk</a>
      &nbsp;|&nbsp; Compiled & visualized by <strong style="color:#9CA3AF;">Gallup Pakistan Digital Analytics</strong>
      &nbsp;|&nbsp; Data covers SPI essential items across 17 cities
      </p>
    </div>
    """, unsafe_allow_html=True)

def fmt_price(v):
    return f"Rs {v:,.2f}"

def color_val_html(v, threshold_high=5, threshold_low=-5):
    if v > threshold_high:
        return f"<span style='color:{DOWN};font-weight:600;'>▲ {v:.2f}%</span>"
    elif v < threshold_low:
        return f"<span style='color:{UP};font-weight:600;'>▼ {abs(v):.2f}%</span>"
    elif v > 0:
        return f"<span style='color:#F59E0B;'>▲ {v:.2f}%</span>"
    elif v < 0:
        return f"<span style='color:{UP};'>▼ {abs(v):.2f}%</span>"
    return f"<span style='color:{NEUTRAL};'>— {v:.2f}%</span>"
