"""
Page 7 — AI Price Analyst
GROQ (free) or Anthropic-powered chatbot for inflation & price analysis.
Set GROQ_API_KEY or ANTHROPIC_API_KEY in Hugging Face Space secrets.
"""
import pandas as pd
pd.set_option("styler.render.max_elements", 500000)

import streamlit as st
import os
import json
import requests
from data_loader import (load_data, get_national_pivot, get_yoy,
                         get_latest_snapshot, CATEGORIES, CATEGORY_COLORS)
from ui import inject_css, inject_animation, page_header, section_header, sidebar_logo, disclaimer_bar, ACCENT, DOWN, UP, MUTED

st.set_page_config(page_title="AI Analyst | Commodity Price Tracker", layout="wide", page_icon="🤖")
inject_css()
inject_animation()
sidebar_logo()

df, canonical, short_map = load_data()
pivot  = get_national_pivot()
yoy    = get_yoy()
snap, latest_month = get_latest_snapshot()
latest_str = latest_month.strftime("%B %Y")

page_header("🤖 AI Price Analyst",
    f"Ask questions about Pakistan's essential commodity prices · Powered by AI · Data: {latest_str}")

# ── Build COMPACT data context (~800 tokens max) ─────────────────────────────
@st.cache_data(show_spinner=False)
def build_context():
    s = snap.copy()
    lm_df = df[df["Month"] == latest_month]

    # --- Items table as compact CSV string (Item|Price|MoM%|YoY%|Category) ---
    lines = ["Item|Price_Rs|MoM%|YoY%|Category"]
    for _, row in s.iterrows():
        yoy = f"{row['YoY%']:.1f}" if pd.notna(row["YoY%"]) else "N/A"
        lines.append(f"{row['Short'][:30]}|{row['Price']:.0f}|{row['MoM%']:.1f}|{yoy}|{row['Category']}")
    items_table = "\n".join(lines)

    # --- City prices for 8 key items only ---
    city_lines = []
    for sno, label in [(7,"Chicken"),(11,"Eggs"),(1,"Wheat Flour"),(23,"Tomatoes"),
                       (47,"Petrol"),(49,"LPG"),(22,"Onions"),(24,"Sugar")]:
        sub = lm_df[lm_df["S. No"]==sno][["Cities","Value"]].dropna()
        if not sub.empty:
            mn  = sub.nsmallest(1,"Value").iloc[0]
            mx  = sub.nlargest(1,"Value").iloc[0]
            avg = sub["Value"].mean()
            city_lines.append(f"{label}: avg Rs{avg:.0f}, cheapest {mn['Cities']} Rs{mn['Value']:.0f}, dearest {mx['Cities']} Rs{mx['Value']:.0f}")
    city_summary = "\n".join(city_lines)

    # --- Annual avg for 6 key items ---
    ann = df[df["S. No"].between(1,51)].drop_duplicates(["Month","S. No"]).copy()
    ann["Year"] = ann["Month"].dt.year
    ann_avg = ann.groupby(["Year","S. No"])["Average Price"].mean()
    key_snos = {1:"WheatFlour",7:"Chicken",11:"Eggs",23:"Tomatoes",47:"Petrol",49:"LPG"}
    ann_lines = ["Item|2022|2023|2024|2025"]
    for sno, lbl in key_snos.items():
        vals = []
        for yr in [2022,2023,2024,2025]:
            try:
                vals.append(f"Rs{ann_avg[yr][sno]:.0f}")
            except:
                vals.append("N/A")
        ann_lines.append(f"{lbl}|" + "|".join(vals))
    ann_table = "\n".join(ann_lines)

    # --- Summary stats ---
    top3_rise = s.nlargest(3,"MoM%")[["Short","MoM%","YoY%"]].values.tolist()
    top3_fall = s.nsmallest(3,"MoM%")[["Short","MoM%","YoY%"]].values.tolist()
    cat_mom   = s.groupby("Category")["MoM%"].mean().sort_values(ascending=False)

    summary = f"""DATASET: PBS SPI | {latest_str} | 51 items | 17 cities | Jan 2019-{latest_str}
OVERALL: {int((s["MoM%"]>0).sum())} items rising MoM, {int((s["MoM%"]<0).sum())} falling | Avg MoM: {s["MoM%"].mean():.2f}% | Avg YoY: {s["YoY%"].mean():.2f}%
TOP 3 RISERS (MoM): {", ".join([f"{r[0][:20]} +{r[1]:.1f}% (YoY {r[2]:.1f}%)" for r in top3_rise])}
TOP 3 FALLERS (MoM): {", ".join([f"{r[0][:20]} {r[1]:.1f}% (YoY {r[2]:.1f}%)" for r in top3_fall])}
CATEGORY AVG MoM: {" | ".join([f"{k}: {v:+.1f}%" for k,v in cat_mom.items()])}"""

    return summary, items_table, city_summary, ann_table

_summary, _items_table, _city_summary, _ann_table = build_context()

# System prompt is kept short — context in compact table format
data_context = f"{_summary}\n\nITEMS:\n{_items_table}\n\nCITY PRICES (key items):\n{_city_summary}\n\nANNUAL AVG (key items):\n{_ann_table}"

SYSTEM_PROMPT = f"""You are a Pakistan commodity price analyst for Gallup Pakistan Digital Analytics.
Data: PBS SPI — 51 essential items, 17 cities, Jan 2019–{latest_str}.

{data_context}

Rules:
- Cite prices in Rs. MoM = month-on-month, YoY = year-on-year.
- This is SPI (essential items), not CPI.
- Be concise: max 4 sentences per point.
- Pakistan inflation context: ~28% in 2022, ~38% in 2023, moderated to ~5-7% in 2025-26.
- If item not in dataset, say so."""

# ── API helper ────────────────────────────────────────────────────────────────
def _get_secret(name):
    val = os.environ.get(name, "")
    if not val:
        try:
            val = st.secrets.get(name, "")
        except Exception:
            pass
    return str(val).strip()

def call_ai(messages_history):
    anthropic_key = _get_secret("ANTHROPIC_API_KEY")
    groq_key      = _get_secret("GROQ_API_KEY")

    # Keep only last 6 messages to prevent token accumulation
    payload = [{"role": m["role"], "content": m["content"]} for m in messages_history[-6:]]

    if anthropic_key:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json",
                     "x-api-key": anthropic_key,
                     "anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-5","max_tokens":1500,
                  "system": SYSTEM_PROMPT, "messages": payload},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["content"][0]["text"]
        return f"⚠️ Anthropic error {resp.status_code}: {resp.text[:200]}"

    elif groq_key:
        groq_msgs = [{"role":"system","content":SYSTEM_PROMPT}] + payload
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Content-Type":"application/json",
                     "Authorization":f"Bearer {groq_key}"},
            json={"model":"llama-3.1-8b-instant","messages":groq_msgs,
                  "max_tokens":1500,"temperature":0.4},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"⚠️ Groq error {resp.status_code}: {resp.text[:200]}"

    else:
        return (
            "⚠️ **No AI API key configured.**\n\n"
            "**Option A — Groq (FREE ✅ — recommended)**\n"
            "1. Sign up free at [console.groq.com](https://console.groq.com) (no credit card)\n"
            "2. Create an API key\n"
            "3. In your Hugging Face Space → **Settings → Repository Secrets**\n"
            "4. Add secret name: `GROQ_API_KEY` · Value: your key\n"
            "5. Restart the Space\n\n"
            "**Option B — Anthropic Claude (Paid, ~$5 minimum)**\n"
            "1. Sign up at [console.anthropic.com](https://console.anthropic.com)\n"
            "2. Add $5 credit → Create API key\n"
            "3. Add secret: `ANTHROPIC_API_KEY` in HF Space secrets\n\n"
            "_Keys are stored as secrets and never visible to users._"
        )

# ── Session state init ────────────────────────────────────────────────────────
if "chat_history"       not in st.session_state: st.session_state.chat_history = []
if "pending_question"   not in st.session_state: st.session_state.pending_question = None

# ── Suggested questions (populate input, not auto-send) ──────────────────────
section_header("💡 Suggested Questions — Click to copy to prompt")
suggestions = [
    f"Which items rose the most in price in {latest_str}?",
    "Compare chicken prices across cities",
    "Why did petrol and LPG prices surge recently?",
    "Which food items are cheapest in Karachi vs Lahore?",
    "How much has wheat flour price changed since 2019?",
    "What is the overall inflation trend for essential goods?",
    "Which city has the highest cost of living based on this data?",
    "Explain the seasonal pattern in tomato and potato prices",
    "Compare energy costs now vs 2022",
    "Which items show deflation in the latest month?",
    "What are the 5 most volatile items by monthly price swings?",
    f"Give a complete inflation summary for {latest_str}",
]

rows = [suggestions[i:i+3] for i in range(0, len(suggestions), 3)]
for row in rows:
    cols = st.columns(3)
    for col, sq in zip(cols, row):
        if col.button(sq, key=f"sq_{sq[:20]}", use_container_width=True):
            # Store as pending — will be picked up by chat_input below
            st.session_state.pending_question = sq
            st.rerun()

st.markdown("---")

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"]=="user" else "🤖"):
        st.markdown(msg["content"])

# ── Highlighted prompt area hint ─────────────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("""
    <div style="background:linear-gradient(90deg,rgba(232,160,32,0.08),rgba(232,160,32,0.03));
        border:1.5px solid rgba(232,160,32,0.5);border-radius:12px;
        padding:14px 20px;margin:16px 0 8px 0;text-align:center;
        animation:pulse-border 2s ease-in-out infinite;">
      <p style="color:#E8A020;font-size:14px;font-weight:600;margin:0;">
        ⬇️ Type your question in the chat box below or click a suggestion above
      </p>
      <p style="color:#9CA3AF;font-size:12px;margin:4px 0 0 0;">
        Ask about prices, trends, city comparisons, inflation drivers — anything about Pakistan's essential commodities
      </p>
    </div>
    <style>
    @keyframes pulse-border {
      0%,100% { border-color: rgba(232,160,32,0.4); box-shadow: 0 0 0 0 rgba(232,160,32,0); }
      50%      { border-color: rgba(232,160,32,0.9); box-shadow: 0 0 12px 2px rgba(232,160,32,0.15); }
    }
    </style>
    """, unsafe_allow_html=True)

# ── Chat input — pre-fill with pending question if set ───────────────────────
default_val = st.session_state.pending_question or ""
user_input = st.chat_input(
    f"Ask anything about Pakistan commodity prices ({latest_str} data)...",
    key="chat_input_main"
)

# If a suggestion was clicked, treat it as user input this run
if st.session_state.pending_question and not user_input:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

if user_input:
    st.session_state.chat_history.append({"role":"user","content":user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analysing price data..."):
            reply = call_ai(st.session_state.chat_history)
        st.markdown(reply)
    st.session_state.chat_history.append({"role":"assistant","content":reply})
    st.session_state.pending_question = None

# ── Clear chat ────────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

with st.expander("🔍 View Data Context Sent to AI (first 3000 chars)"):
    st.code(data_context[:2000] + "\n... [truncated]", language="text")

disclaimer_bar()
