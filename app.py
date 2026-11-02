import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide", page_title="WHALE FINAL")
st.title("🐋 WHALE + TRAP - FULL CODE (FIXED)")

# --- AUTO REFRESH HAR 60 SEC ---
st_autorefresh(interval=60 * 1000, key="whale_final_auto")

UPSTOX_TOKEN = st.sidebar.text_input("Upstox Token", type="password").strip()
INSTRUMENT = st.sidebar.selectbox("Index", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX", "BSE_INDEX|BANKEX"])

def get_fast_ltp(token, instrument):
    try:
        headers = {'Authorization': f'Bearer {token}'}
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument}"
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        if r.status_code == 200:
            return list(data['data'].values())[0]['last_price']
    except: return None
    return None

def get_candles(token, instrument):
    try:
        headers = {'Authorization': f'Bearer {token}'}
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/1minute"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        df = pd.DataFrame(data['data']['candles'], columns=['time','open','high','low','close','volume','oi'])
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        return df
    except: return None

def detect_whale_trap(df):
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    wick_up = last['high'] - max(last['open'], last['close'])
    wick_down = min(last['open'], last['close']) - last['low']
    
    new_signal = None
    entry = 0
    target = 0
    
    # Logic thoda easy kiya, jaldi signal ayega
    if wick_up > body * 1.2 and body > 1:
        entry = last['high']
        target = entry - 1.5
        new_signal = f"🔴 PERFECT SELL TRAP @ {entry:.1f}"
    elif wick_down > body * 1.2 and body > 1:
        entry = last['low']
        target = entry + 1.5
        new_signal = f"🟢 PERFECT BUY TRAP @ {entry:.1f}"
        
    if 'last_trap' not in st.session_state:
        st.session_state.last_trap = "⚪ WAIT - Beech me hai"
        st.session_state.trap_count = 0
        st.session_state.target = 0

    if new_signal:
        st.session_state.last_trap = new_signal
        st.session_state.target = target
        st.session_state.trap_count = 0
    else:
        st.session_state.trap_count += 1

    final = st.session_state.last_trap
    if "TRAP" in final:
        if st.session_state.trap_count == 0:
            final += f" | TARGET: {st.session_state.target:.1f} (1.5 pt kaat le)"
        else:
            final += f" (Hold {st.session_state.trap_count} candle pehle) | TARGET: {st.session_state.target:.1f}"
    return final, last

if not UPSTOX_TOKEN: 
    st.warning("Pehle Upstox Token daal sidebar me")
    st.stop()

fast_ltp = get_fast_ltp(UPSTOX_TOKEN, INSTRUMENT)
df = get_candles(UPSTOX_TOKEN, INSTRUMENT)

if df is None: 
    st.error("Data nahi aaya, token expire?")
    st.stop()

signal, last_candle = detect_whale_trap(df)

# Time upar dikhega
st.info(f"⏰ Last Update: {datetime.now().strftime('%H:%M:%S')} | Auto refresh: 60 sec")

if "SELL" in signal: st.error(f"## {signal}")
elif "BUY" in signal: st.success(f"## {signal}")
else: st.info(f"## {signal}")

c1,c2,c3,c4 = st.columns(4)
display_ltp = fast_ltp if fast_ltp else last_candle['close']
body_size = abs(last_candle['close'] - last_candle['open'])

c1.metric("LTP", f"{display_ltp:.1f}")
c2.metric("Body", f"{body_size:.1f}") # Volume ki jagah Body
c3.metric("Range", f"{(last_candle['high']-last_candle['low']):.1f}")
c4.metric("Candles", f"{len(df)}")

st.success(f"✅ LIVE! {len(df)} candles | {INSTRUMENT}")

fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
st.plotly_chart(fig, use_container_width=True)