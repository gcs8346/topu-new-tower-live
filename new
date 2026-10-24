import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Topu V28 FINAL")
st.title("🔥 Topu V28 FINAL LOCK - Index + Stock + Live Mid")

# --- ALL INDEXES + STOCKS ---
index_map = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "FIN NIFTY": "^CNXFINANCE",
    "SENSEX": "^BSESN",
    "MIDCAP NIFTY": "NIFTY_MID_SELECT.NS",
    "NIFTY IT": "^CNXIT"
}
selected_index = st.sidebar.selectbox("Index Chuno", list(index_map.keys()))
custom_stock = st.sidebar.text_input("Ya Stock Likhdo (RELIANCE, TCS)", "").strip().upper()
interval = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h","1d"], index=1)
period = st.sidebar.selectbox("Data Period", ["5d","10d","1mo","3mo"], index=1)

ticker = (custom_stock + ".NS" if ".NS" not in custom_stock and "^" not in custom_stock else custom_stock) if custom_stock else index_map[selected_index]

def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def rsi_calc(s, n=14):
    delta = s.diff()
    gain = delta.where(delta>0,0).rolling(n).mean()
    loss = -delta.where(delta<0,0).rolling(n).mean()
    return 100 - (100 / (1 + gain/loss))

@st.cache_data(ttl=120)
def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

df = load_data(ticker, period, interval)
df['EMA9'] = ema(df['Close'],9); df['EMA21'] = ema(df['Close'],21); df['EMA50'] = ema(df['Close'],50)
df['RSI'] = rsi_calc(df['Close'],14)
df['VWAP'] = (df['Close']*df['Volume']).cumsum() / df['Volume'].cumsum()
hl2 = (df['High']+df['Low'])/2; atr = (df['High']-df['Low']).rolling(10).mean()
df['ST_BULL'] = df['Close'] > (hl2 + 3*atr).shift(1) # simplified BULL check

# --- LIVE MID BECH MEIN ---
today_date = df.index[-1].date()
df_today = df[df.index.date == today_date]
today_high = df_today['High'].max() if len(df_today)>0 else df['High'].iloc[-20:].max()
today_low = df_today['Low'].min() if len(df_today)>0 else df['Low'].iloc[-20:].min()
today_mid = (today_high + today_low)/2
opening_mid = (df_today.head(3)['High'].max() + df_today.head(3)['Low'].min())/2 if len(df_today)>=3 else today_mid

# --- TERA 5 CHECKLIST - ENTRY ---
df['Cross'] = (df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1))
df['C1'] = df['EMA9'] > df['EMA21']
df['C2'] = df['Close'] > df['EMA9']
df['C3'] = (df['RSI'] >= 55) & (df['RSI'] <= 80)
df['C4'] = df['ST_BULL'] == True
df['C5'] = df['Close'] > df['EMA50']
df['ENTRY'] = df['Cross'] & df['C2'] & df['C3'] & df['C4'] & df['C5']

# --- EXIT RADAR 5 PATTERN ---
df['Green'] = df['Close'] > df['Open']; df['Red'] = df['Close'] < df['Open']
df['Exit1'] = df['Green'] & df['Green'].shift(1) & df['Green'].shift(2) & (df['Close'] > df['EMA21']*1.012)
df['Exit2'] = (df['Green'].shift(1)) & df['Red'] & (df['Open'] > df['Close'].shift(1))
df['Exit3'] = (df['High'] - df[['Open','Close']].max(axis=1) > 2*abs(df['Close']-df['Open']))
df['Exit4'] = df['Red'] & df['Red'].shift(1)
df['Exit5'] = (df['RSI'].shift(1) > 75) & (df['RSI'] < df['RSI'].shift(1))
df['EXIT'] = df['Exit1'] | df['Exit2'] | df['Exit3'] | df['Exit4'] | df['Exit5']

last = df.iloc[-1]
st.metric("Price", f"{last['Close']:.2f}"); st.metric("MID TODAY Live (Bech me)", f"{today_mid:.2f}", "UPAR" if last['Close']>today_mid else "NEECHE")
st.metric("Opening 15m Mid", f"{opening_mid:.2f}")

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], name="EMA9")); fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], name="EMA21")); fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="FIDI50"))
fig.add_hline(y=today_mid, line_dash="dash", line_color="orange", annotation_text=f"TODAY MID {today_mid:.1f}")
fig.add_hline(y=opening_mid, line_dash="dot", line_color="purple", annotation_text=f"OPEN MID {opening_mid:.1f}")
fig.add_trace(go.Scatter(x=df[df['ENTRY']].index, y=df[df['ENTRY']]['Low'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name="ENTRY"))
fig.add_trace(go.Scatter(x=df[df['EXIT']].index, y=df[df['EXIT']]['High'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name="EXIT"))
fig.update_layout(height=600, xaxis_rangeslider_visible=False); st.plotly_chart(fig, use_container_width=True)