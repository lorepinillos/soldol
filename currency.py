# exchange_dashboard_enhanced.py
"""
💱 USD→PEN FX Dashboard – Fixed Y-axis 3.4–4.0 & Cognitive Design Enhancements
Author: Lorena + ChatGPT
Optimized for Peruvians living abroad who frequently convert USD↔PEN.
"""

import datetime as dt
import time

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf

# ──────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG & STYLE
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="USD ↔ PEN Exchange Dashboard",
    page_icon="💱",
    layout="wide"
)

# Inject minimal CSS for colored KPI cards & sidebar sections
st.markdown("""
<style>
.kpi-card {
    background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
}
.sidebar-section {
    background-color: #fafafa;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("💱 USD → PEN Exchange Dashboard")
st.markdown(
    "_Real-time USD→PEN tracking with historical averages, buy/wait guidance and adjustable chart._"
)

# ──────────────────────────────────────────────────────────────────────────────
# 2. DATA HELPERS (yfinance)
# ──────────────────────────────────────────────────────────────────────────────
TICKER = "PEN=X"  # Yahoo symbol for USD→PEN

@st.cache_data(ttl=15 * 60)
def fetch_latest_rate() -> dict:
    """Fetch the latest USD→PEN quote and timestamp (15-min delayed)."""
    df = yf.download(TICKER, period="1d", interval="1m", progress=False)
    if df.empty:
        df = yf.download(TICKER, period="1d", progress=False)
    rate = float(df["Close"].dropna().iloc[-1])
    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return {"rate": rate, "timestamp": timestamp}

@st.cache_data(ttl=60 * 60)
def fetch_history(days: int) -> pd.Series:
    """Return a Series of daily closes for USD→PEN over the past <days> days."""
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    df = yf.download(TICKER, start=start, end=end, progress=False)
    ser = df["Close"].dropna()
    ser.name = "Rate"
    return ser

# ──────────────────────────────────────────────────────────────────────────────
# 3. SIDEBAR – CONVERTER, REFRESH & PRINCIPLES
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.header("Options")
    usd_amount = st.number_input("Amount (USD)", min_value=0.01, value=100.0, step=10.0)
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)
    if st.button("Refresh now"):
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# 4. LOAD / REFRESH DATA
# ──────────────────────────────────────────────────────────────────────────────
if auto_refresh or "fx" not in st.session_state:
    st.session_state["fx"] = fetch_latest_rate()
    st.session_state["loaded_at"] = dt.datetime.utcnow()

fx = st.session_state["fx"]
current_rate = float(fx["rate"])
last_updated = fx["timestamp"]

# ──────────────────────────────────────────────────────────────────────────────
# 5. CURRENT RATE & QUICK CONVERSION
# ──────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("### Current Exchange Rate")
    st.markdown(
        f"<div style='font-size:2rem;' class='kpi-card'><b>S/. {current_rate:.4f}</b> per USD</div>",
        unsafe_allow_html=True
    )
    st.markdown(f"_Last updated: {last_updated}_")
with col2:
    converted = usd_amount * current_rate
    st.markdown("### Quick Conversion")
    st.markdown(
        f"<div style='font-size:1.5rem;' class='kpi-card'>{usd_amount:.2f} USD → {converted:.2f} PEN</div>",
        unsafe_allow_html=True
    )

# ──────────────────────────────────────────────────────────────────────────────
# 6. ADJUSTABLE HISTORICAL CHART
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Adjustable History")

# Time-window selector
window = st.selectbox(
    "History Window",
    options=[("7 days", 7), ("30 days", 30), ("365 days", 365)],
    format_func=lambda x: x[0],
    index=2,
)
days = window[1]

series = fetch_history(days)
if not series.empty:
    df_hist = series.reset_index()
    df_hist.columns = ["Date", "Rate"]

    base_line = (
        alt.Chart(df_hist)
        .mark_line(color="#1f77b4", strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y(
                "Rate:Q",
                title="Exchange Rate (PEN per USD)",
                scale=alt.Scale(domain=[3.4, 4.0])  # fixed Y-axis
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Rate:Q", title="Rate", format=".4f"),
            ],
        )
        .properties(height=350)
        .interactive()
    )

    current_rule = (
        alt.Chart(pd.DataFrame({"Rate": [current_rate]}))
        .mark_rule(color="red", strokeDash=[4, 4])
        .encode(
            y=alt.Y("Rate:Q", scale=alt.Scale(domain=[3.4, 4.0]))
        )
    )

    st.altair_chart(base_line + current_rule, use_container_width=True)
    st.markdown("_Dashed red line = current rate_")
else:
    st.error("No historical data available for this window.")

# ──────────────────────────────────────────────────────────────────────────────
# 7. AVERAGES & BUY/WAIT GUIDANCE
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Averages & Guidance")

hist365 = fetch_history(365)
avg7   = float(hist365[-7:].mean())   if len(hist365) >= 7 else current_rate
avg30  = float(hist365[-30:].mean())  if len(hist365) >= 30 else current_rate
avg365 = float(hist365.mean())        if len(hist365) >= 1  else current_rate

k1, k2, k3, k4 = st.columns(4)
k1.metric("Now",            f"S/. {current_rate:.4f}")
k2.metric("7-day avg",      f"S/. {avg7:.4f}",   delta=f"{(current_rate-avg7):+.4f}")
k3.metric("30-day avg",     f"S/. {avg30:.4f}",  delta=f"{(current_rate-avg30):+.4f}")
k4.metric("365-day avg",    f"S/. {avg365:.4f}", delta=f"{(current_rate-avg365):+.4f}")

score = 0.0
if current_rate < avg365: score += 0.30
if current_rate < avg30:  score += 0.50
if current_rate < avg7:   score += 0.20

st.subheader("Recommendation")
if score > 0.5:
    st.success(f"BUY 🟢  (score {score:.2f} > 0.50)")
else:
    st.warning(f"WAIT / SELL 🟠  (score {score:.2f} ≤ 0.50)")

# ──────────────────────────────────────────────────────────────────────────────
# 8. AUTO-REFRESH TIMER
# ──────────────────────────────────────────────────────────────────────────────
if auto_refresh:
    elapsed   = (dt.datetime.utcnow() - st.session_state["loaded_at"]).total_seconds()
    remaining = max(0, 60 - elapsed)
    st.sidebar.progress((60-remaining)/60, text=f"{int(remaining)}s until refresh")
    if remaining < 1:
        time.sleep(1)
        st.experimental_rerun()

# ──────────────────────────────────────────────────────────────────────────────
# 9. FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; font-size:0.8rem; color:#666;'>"
    f"Optimized for Peruvians abroad • Data via Yahoo Finance (15 min delay) • Last updated {last_updated}"
    f"</div>",
    unsafe_allow_html=True,
)
