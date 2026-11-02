import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🐋 WHALE + TRAP - RATE LIMIT FIXED")

UPSTOX_TOKEN = st.sidebar.text_input("Upstox Token", type="password").strip()
INSTRUMENT = st.sidebar.selectbox("Index", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX", "BSE_INDEX|BANKEX"])

# YE SABSE IMPORTANT HAI - 60 sec tak dobara API call nahi jayegi
@st.cache_data(ttl=60) 
def get_live_data(token, instrument):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    
    for attempt in range(3): # 3 baar try karega
        try:
            url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/1minute"
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code == 429 or r.status_code == 1015:
                st.warning(f"Rate limit lag gaya, {30*(attempt+1)} sec wait kar raha hu...")
                time.sleep(30 * (attempt+1)) # 30sec, 60sec, 90sec wait
                continue

            data = r.json()
            if r.status_code != 200:
                st.error(f"Upstox Error: {data}")
                return None
            if not data.get('data') or not data['data']['candles']:
                # Sunday hai to message
                if datetime.now().weekday() >= 5:
                    st.info("Sunday hai, isliye aaj ka candle nahi hai. Token sahi hai!")
                else:
                    st.warning("Market 9:15 pe khulega tab data ayega")
                return None

            df = pd.DataFrame(data['data']['candles'], columns=['time','open','high','low','close','volume','oi'])
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
            df.set_index('time', inplace=True)
            df = df.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna().reset_index()
            return df
        except Exception as e:
            time.sleep(5)
            continue
    return None

if not UPSTOX_TOKEN:
    st.warning("Token daal")
    st.stop()

# Ek hi baar button dabana, baar baar refresh mat karna
if st.sidebar.button("REFRESH DATA (1 min me 1 baar)"):
    st.cache_data.clear()

df = get_live_data(UPSTOX_TOKEN, INSTRUMENT)
if df is None:
    st.stop()

st.success(f"✅ LIVE! {len(df)} candles")
fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(df.tail(20))