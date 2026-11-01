import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import datetime

st.set_page_config(page_title="WHALE + TRAP FINAL", layout="wide")
st.title("🐋 WHALE + TRAP DETECTOR - FINAL")

# --- SUNDAY CHECK - Tera wala issue fix ---
today = datetime.datetime.now().weekday() # 6 = Sunday
if today == 6:
    st.warning("⚠️ Aaj Sunday hai, Upstox / Exchange band hai")
    st.info("Isliye 'Data nahi aaya' dikh raha hai. App sahi hai, Kal Monday se live data auto ayega.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Setting")
UPSTOX_TOKEN = st.sidebar.text_input("Upstox Access Token daal", type="password")
INSTRUMENT = st.sidebar.selectbox("Index", ["BSE_INDEX|SENSEX", "BSE_INDEX|BANKEX", "NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank"])
EMA_CHOICE = st.sidebar.selectbox("EMA Logic", ["9x21 (Tera wala)", "8x10 (Fast)", "10x20 (Slow)"])

if EMA_CHOICE == "8x10 (Fast)": FAST, SLOW = 8, 10
elif EMA_CHOICE == "10x20 (Slow)": FAST, SLOW = 10, 20
else: FAST, SLOW = 9, 21

def get_live_data(token, instrument):
    url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/5minute"
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.get(url, headers=headers).json()
    if 'data' not in r or not r['data']['candles']: return None
    df = pd.DataFrame(r['data']['candles'], columns=['time','open','high','low','close','volume','oi'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    return df

if not UPSTOX_TOKEN:
    st.warning("Pehle Upstox Token daal sidebar me")
    st.stop()

df = get_live_data(UPSTOX_TOKEN, INSTRUMENT)
if df is None:
    st.error("Data nahi aaya, token expire hai kya? Ya aaj market band hai.")
    st.stop()

# --- CALCULATIONS ---
df[f'EMA_{FAST}'] = df['close'].ewm(span=FAST).mean()
df[f'EMA_{SLOW}'] = df['close'].ewm(span=SLOW).mean()
df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
df['CVD'] = (df['close'].diff() * df['volume']).cumsum()
df['CVD_MA'] = df['CVD'].ewm(span=20).mean()
df['OI_CHG'] = df['oi'].diff()

# --- SIGNALS ---
df['FINAL_BUY'] = (df['close'] > df['VWAP']) & (df['CVD'] > df['CVD_MA']) & (df['OI_CHG'] > 0)
df['FINAL_SELL'] = (df['close'] < df['VWAP']) & (df['CVD'] < df['CVD_MA']) & (df['OI_CHG'] < 0)
# TRAP LOGIC - Tera 22995 wala case
df['TRAP_BUY'] = (df['close'] < df[f'EMA_{SLOW}'] - 50) & (df['CVD'] > df['CVD_MA'])

# --- CHART ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price"))
fig.add_trace(go.Scatter(x=df['time'], y=df[f'EMA_{FAST}'], name=f"EMA {FAST}", line=dict(color='blue')))
fig.add_trace(go.Scatter(x=df['time'], y=df[f'EMA_{SLOW}'], name=f"EMA {SLOW}", line=dict(color='red')))
fig.add_trace(go.Scatter(x=df['time'], y=df['VWAP'], name="VWAP", line=dict(color='orange', dash='dash')))

# Signal markers
buy_df = df[df['FINAL_BUY']]
fig.add_trace(go.Scatter(x=buy_df['time'], y=buy_df['low']-20, mode='markers', marker=dict(color='green', size=12, symbol='triangle-up'), name='FINAL BUY'))

trap_df = df[df['TRAP_BUY']]
fig.add_trace(go.Scatter(x=trap_df['time'], y=trap_df['low']-40, mode='markers', marker=dict(color='yellow', size=14, symbol='star'), name='TRAP BUY'))

st.plotly_chart(fig, use_container_width=True)

# --- STATUS ---
last = df.iloc[-1]
st.metric("Last Price", last['close'])
if last['TRAP_BUY']: st.success("⚠️ TRAP BUY ACTIVE - Whale neeche maal bhar raha hai")
elif last['FINAL_BUY']: st.success("✅ FINAL BUY")
elif last['FINAL_SELL']: st.error("❌ FINAL SELL")
else: st.info("WAIT - Koi solid signal nahi")
st.dataframe(df.tail(10))