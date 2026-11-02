import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import datetime

st.set_page_config(page_title="WHALE + TRAP FINAL", layout="wide")
st.title("🐋 WHALE + TRAP DETECTOR - FINAL FIXED")

st.sidebar.header("Setting")
UPSTOX_TOKEN = st.sidebar.text_input("Upstox Access Token daal", type="password").strip()
INSTRUMENT = st.sidebar.selectbox("Index", ["BSE_INDEX|SENSEX", "BSE_INDEX|BANKEX", "NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank"])
EMA_CHOICE = st.sidebar.selectbox("EMA Logic", ["9x21 (Tera wala)", "8x10 (Fast)", "10x20 (Slow)"])

if EMA_CHOICE == "8x10 (Fast)": FAST, SLOW = 8, 10
elif EMA_CHOICE == "10x20 (Slow)": FAST, SLOW = 10, 20
else: FAST, SLOW = 9, 21

def get_live_data(token, instrument):
    # Upstox ne 5min band kia, isliye 1min se 5min banayenge
    url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/1minute"
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        if r.status_code != 200:
            st.error(f"Upstox Error: {data}")
            return None
        if 'data' not in data or not data['data']['candles'] or len(data['data']['candles']) == 0:
            st.warning(f"No candles for {instrument} - Sunday hai isliye Market band")
            return None
        df = pd.DataFrame(data['data']['candles'], columns=['time','open','high','low','close','volume','oi'])
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        df.set_index('time', inplace=True)
        df_5min = df.resample('5min').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum', 'oi': 'last'
        }).dropna().reset_index()
        return df_5min
    except Exception as e:
        st.error(f"API Fail: {e}")
        return None

if not UPSTOX_TOKEN:
    st.warning("Pehle Upstox Token daal sidebar me")
    st.stop()

df = get_live_data(UPSTOX_TOKEN, INSTRUMENT)
if df is None:
    st.error("Data nahi aaya, Token expire hai kya? Naya token lele.")
    st.info("Aaj Sunday hai to Friday ka last data bhi kabhi-kabhi nahi aata, Kal Monday live chalega")
    st.stop()

df[f'EMA_{FAST}'] = df['close'].ewm(span=FAST).mean()
df[f'EMA_{SLOW}'] = df['close'].ewm(span=SLOW).mean()
df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
df['CVD'] = (df['close'].diff() * df['volume']).cumsum()
df['CVD_MA'] = df['CVD'].ewm(span=20).mean()
df['oi'] = pd.to_numeric(df['oi'], errors='coerce').fillna(0)
df['OI_CHG'] = df['oi'].diff().fillna(0)

if "INDEX" in INSTRUMENT:
    df['FINAL_BUY'] = (df['close'] > df['VWAP']) & (df['CVD'] > df['CVD_MA'])
    df['FINAL_SELL'] = (df['close'] < df['VWAP']) & (df['CVD'] < df['CVD_MA'])
else:
    df['FINAL_BUY'] = (df['close'] > df['VWAP']) & (df['CVD'] > df['CVD_MA']) & (df['OI_CHG'] > 0)
    df['FINAL_SELL'] = (df['close'] < df['VWAP']) & (df['CVD'] < df['CVD_MA']) & (df['OI_CHG'] < 0)

df['TRAP_BUY'] = (df['close'] < df[f'EMA_{SLOW}'] - 50) & (df['CVD'] > df['CVD_MA'])

fig = go.Figure()
fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price"))
fig.add_trace(go.Scatter(x=df['time'], y=df[f'EMA_{FAST}'], name=f"EMA {FAST}", line=dict(color='cyan')))
fig.add_trace(go.Scatter(x=df['time'], y=df[f'EMA_{SLOW}'], name=f"EMA {SLOW}", line=dict(color='red')))
fig.add_trace(go.Scatter(x=df['time'], y=df['VWAP'], name="VWAP", line=dict(color='orange', dash='dash')))
buy_df = df[df['FINAL_BUY']]
fig.add_trace(go.Scatter(x=buy_df['time'], y=buy_df['low']-20, mode='markers', marker=dict(color='green', size=12, symbol='triangle-up'), name='FINAL BUY'))
trap_df = df[df['TRAP_BUY']]
fig.add_trace(go.Scatter(x=trap_df['time'], y=trap_df['low']-40, mode='markers', marker=dict(color='yellow', size=14, symbol='star'), name='TRAP BUY'))
fig.update_layout(xaxis_rangeslider_visible=False, height=650, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

last = df.iloc[-1]
c1,c2,c3 = st.columns(3)
c1.metric("Last Price", f"{last['close']}")
c2.metric("CVD Trend", "BULL" if last['CVD'] > last['CVD_MA'] else "BEAR")
c3.metric("VWAP", "UPAR" if last['close'] > last['VWAP'] else "NEECHE")

if last['TRAP_BUY']: st.success("⚠️ TRAP BUY ACTIVE - Whale neeche maal bhar raha hai")
elif last['FINAL_BUY']: st.success("✅ FINAL BUY")
elif last['FINAL_SELL']: st.error("❌ FINAL SELL")
else: st.info("WAIT - Koi solid signal nahi")
st.dataframe(df.tail(15), use_container_width=True)