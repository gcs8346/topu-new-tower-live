import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="WHALE DETECTOR")
st.title("🐋 WHALE + TRAP - RATE LIMIT FIXED")

UPSTOX_TOKEN = st.sidebar.text_input("Upstox Token", type="password").strip()
INSTRUMENT = st.sidebar.selectbox("Index", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX"])
TIMEFRAME = st.sidebar.selectbox("TimeFrame", ["1minute", "5minute"], index=0)
AUTO_REFRESH = st.sidebar.checkbox("Auto Refresh (60 sec)", value=False)

# Tera wala hi rate limit fix, isko mat cherna
@st.cache_data(ttl=60) 
def get_live_data(token, instrument, tf):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    for attempt in range(3):
        try:
            url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/{tf}"
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code in [429, 1015]:
                st.warning(f"Rate limit! {30*(attempt+1)} sec wait...")
                time.sleep(30 * (attempt+1))
                continue

            data = r.json()
            if r.status_code != 200:
                st.error(f"Upstox Error: {data}")
                return None
            if not data.get('data') or not data['data'].get('candles'):
                if datetime.now().weekday() >= 5:
                    st.info("Sunday hai, token sahi hai!")
                else:
                    st.warning("Market 9:15 pe khulega")
                return None

            df = pd.DataFrame(data['data']['candles'], columns=['time','open','high','low','close','volume','oi'])
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
            return df
        except Exception as e:
            time.sleep(5)
            continue
    return None

def detect_whale_trap(df):
    df['body'] = abs(df['close'] - df['open'])
    df['wick_up'] = df['high'] - df[['open','close']].max(axis=1)
    df['wick_down'] = df[['open','close']].min(axis=1) - df['low']
    df['avg_vol'] = df['volume'].rolling(20).mean()
    
    last = df.iloc[-1]
    signal = "NO TRADE - RANGE"
    
    # WHALE LOGIC - Volume 2.5x se zyada
    if last['volume'] > last['avg_vol'] * 2.5:
        if last['wick_up'] > last['body'] * 2:
            signal = f"🔴 WHALE SELL TRAP @ {last['high']} - Bade log bech ke gaye!"
        elif last['wick_down'] > last['body'] * 2:
            signal = f"🟢 WHALE BUY TRAP @ {last['low']} - Bade log kharid ke gaye!"
        elif last['close'] > last['open']:
            signal = f"🟢 WHALE BUYING - Volume tez!"
        else:
            signal = f"🔴 WHALE SELLING - Volume tez!"
    
    # Tere liye 1.5 point wala scalping signal
    if "NO TRADE" in signal and len(df) > 5:
        if df['close'].iloc[-1] > df['close'].iloc[-3:].max():
            signal = f"⚡ SCALP BUY - 1.5 point ke liye ready"
        elif df['close'].iloc[-1] < df['close'].iloc[-3:].min():
            signal = f"⚡ SCALP SELL - 1.5 point ke liye ready"

    return signal, last

if not UPSTOX_TOKEN:
    st.warning("Token daal bhai")
    st.stop()

if st.sidebar.button("REFRESH DATA (1 min me 1 baar)"):
    st.cache_data.clear()

df = get_live_data(UPSTOX_TOKEN, INSTRUMENT, TIMEFRAME)
if df is None or df.empty:
    st.stop()

signal, last = detect_whale_trap(df)

# --- SIGNAL BOARD ---
if "SELL TRAP" in signal or "SELLING" in signal:
    st.error(f"## {signal}")
elif "BUY" in signal:
    st.success(f"## {signal}")
else:
    st.info(f"## {signal}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("LTP", f"{last['close']}")
col2.metric("Volume", f"{int(last['volume'])}")
col3.metric("Avg 20 Vol", f"{int(last['avg_vol']) if pd.notna(last['avg_vol']) else 0}")
col4.metric("Candles", f"{len(df)}")

st.success(f"✅ LIVE! {len(df)} candles | TimeFrame: {TIMEFRAME}")

fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
# Whale wali candle ko mark karega
fig.add_trace(go.Bar(x=df['time'], y=df['volume'], name="Volume", yaxis="y2", opacity=0.3))
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, yaxis2=dict(overlaying='y', side='right', showgrid=False), height=500)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df.tail(20).sort_values('time', ascending=False))

if AUTO_REFRESH:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()