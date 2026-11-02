import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="WHALE DETECTOR")
st.title("🐋 WHALE + TRAP - RATE LIMIT FIXED")

UPSTOX_TOKEN = st.sidebar.text_input("Upstox Token", type="password").strip()
INSTRUMENT = st.sidebar.selectbox("Index", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX", "BSE_INDEX|BANKEX"])
TIMEFRAME = st.sidebar.selectbox("TimeFrame", ["1m", "5m", "15m", "30m"], index=0)
AUTO_REFRESH = st.sidebar.checkbox("Auto Refresh (60 sec)", value=False)

@st.cache_data(ttl=60) 
def get_live_data(token, instrument, tf_label):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    api_tf = "1minute"
    for attempt in range(3):
        try:
            url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/{api_tf}"
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
            df.set_index('time', inplace=True)

            if tf_label == "5m":
                df = df.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
            elif tf_label == "15m":
                df = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
            elif tf_label == "30m":
                df = df.resample('30min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
            
            df = df.reset_index()
            return df
        except Exception as e:
            st.error(f"Error: {e}")
            time.sleep(5)
            continue
    return None

def detect_whale_trap(df):
    df['body'] = abs(df['close'] - df['open'])
    df['range'] = df['high'] - df['low']
    df['wick_up'] = df['high'] - df[['open','close']].max(axis=1)
    df['wick_down'] = df[['open','close']].min(axis=1) - df['low']
    df['avg_range'] = df['range'].rolling(20).mean()
    
    last = df.iloc[-1]
    
    # Volume 0 fix for INDEX
    if last['volume'] == 0:
        avg_r = last['avg_range'] if pd.notna(last['avg_range']) else last['range']
        if last['wick_up'] > last['body'] * 2.5 and last['range'] > avg_r * 1.5:
            signal = f"🔴 WHALE SELL TRAP @ {last['high']:.1f}"
        elif last['wick_down'] > last['body'] * 2.5 and last['range'] > avg_r * 1.5:
            signal = f"🟢 WHALE BUY TRAP @ {last['low']:.1f}"
        elif last['range'] > avg_r * 2:
            if last['close'] > last['open']:
                signal = f"🟢 TEZ BUY - 1.5 point scalp ready"
            else:
                signal = f"🔴 TEZ SELL - 1.5 point scalp ready"
        else:
            signal = f"⚪ NO TRADE - RANGE"
    else:
        df['avg_vol'] = df['volume'].rolling(20).mean()
        if last['volume'] > last['avg_vol'] * 2.5:
            signal = f"🟢 WHALE VOLUME TEZ @ {last['close']:.1f}"
        else:
            signal = f"⚪ NO TRADE - RANGE"
            
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

if "SELL" in signal:
    st.error(f"## {signal}")
elif "BUY" in signal:
    st.success(f"## {signal}")
else:
    st.info(f"## {signal}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("LTP", f"{last['close']:.1f}")
c2.metric("Volume", f"{int(last['volume'])}")
c3.metric("Range", f"{last['range']:.1f}")
c4.metric("Candles", f"{len(df)}")

st.success(f"✅ LIVE! {len(df)} candles | TimeFrame: {TIMEFRAME}")

fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=550)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(df.tail(20).sort_values('time', ascending=False))

if AUTO_REFRESH:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()