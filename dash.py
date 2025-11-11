# frontend/app.py
import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import plotly.graph_objects as go

# ---------------- CONFIG ----------------
# Replace with your deployed backend URL on Render
BACKEND_URL = "https://all-hft.onrender.com"

# Path to same stocks.csv as backend
STOCKS_CSV = "stocks.csv"

# Refresh interval in seconds
DEFAULT_REFRESH = 60
# ---------------------------------------

@st.cache_data
def load_stock_list():
    try:
        df = pd.read_csv(STOCKS_CSV)
        return df['symbol'].tolist()
    except Exception as e:
        st.error(f"Failed to load stocks.csv: {e}")
        return []

def fetch_latest(symbol: str):
    try:
        r = requests.get(f"{BACKEND_URL}/api/latest/{symbol}", timeout=20)
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"No data yet for {symbol} (status {r.status_code})")
            return None
    except Exception as e:
        st.error(f"Error fetching latest data: {e}")
        return None

def fetch_history(symbol: str, limit: int = 200):
    try:
        r = requests.get(f"{BACKEND_URL}/api/history/{symbol}?limit={limit}", timeout=20)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return pd.DataFrame()

# ---- UI ----
st.set_page_config(page_title="IV Sentiment Dashboard", layout="wide")

st.title("📊 Multi-Stock IV & Sentiment Dashboard")
st.caption("Live data fetched from Render backend (Dhan API option chain)")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    symbol = st.selectbox("Select Stock / Index:", load_stock_list())
with col2:
    limit = st.number_input("History limit", min_value=50, max_value=1000, value=200, step=50)
with col3:
    refresh_interval = st.number_input("Auto-refresh (seconds)", min_value=30, max_value=300, value=DEFAULT_REFRESH, step=10)

placeholder = st.empty()

while True:
    with placeholder.container():
        if not symbol:
            st.warning("No symbol selected.")
            time.sleep(refresh_interval)
            continue

        st.subheader(f"📈 {symbol} — Live Option Chain Sentiment")

        # Fetch latest
        latest = fetch_latest(symbol)
        if latest:
            fetched_time = datetime.fromisoformat(latest["fetched_at"])
            st.markdown(f"**Last Update:** {fetched_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            st.json(latest["raw_json"]["data"] if "raw_json" in latest else latest)

        # Fetch historical data
        df = fetch_history(symbol, limit)
        if not df.empty:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"])
            df = df.sort_values("fetched_at")

            # ---- Plot ----
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["fetched_at"],
                y=df["last_price"],
                mode="lines+markers",
                name="Last Price",
                line=dict(width=2)
            ))
            fig.update_layout(
                title=f"Last Price History — {symbol}",
                xaxis_title="Time",
                yaxis_title="Last Price",
                template="plotly_dark",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No history data available yet.")

        st.markdown("---")
        st.caption("Auto-refreshes every few seconds.")
    time.sleep(refresh_interval)
