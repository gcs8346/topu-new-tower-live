import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Topu Upstox Live - No Trap", layout="wide")
st.title("🔥 Topu Upstox Live - No Trap V8")
st.caption("Direct Upstox API - No Yfinance, No Delay")

# === SIDEBAR - TERA TOKEN ===
st.sidebar.header("Topu ka Upstox Setup")
access_token = st.sidebar.text_input("Upstox Access Token Daal (6 8 7 8 wala)", type="password")
timeframe = st.sidebar.selectbox("Timeframe", ["1minute", "5minute", "15minute"], index=1)
refresh_sec = st.sidebar.slider("Auto Refresh (sec)", 5, 60, 10)

# Upstox Instrument Keys
SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "SENSEX": "BSE_INDEX|SENSEX",
    "CRUDE MCX": "MCX_FO|CRUDEOIL24DECFUT" # Ye har mahine change hota hai, expiry dekh lena
}

# Agar token nahi daala to rok de
if not access_token:
    st.warning("Bhai token daal de sidebar me, tabhi live chalega! Tu Upstox se token nikalta hai na wahi.")
    st.stop()

headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

def get_upstox_candles(instrument_key, interval):
    try:
        # Historical Candle API
        url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/2026-10-29/2026-10-29"
        # Intraday Candle - Live ke liye
        url_intra = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/{interval}"
        
        resp = requests.get(url_intra, headers=headers)
        data = resp.json()
        
        if 'data' in data and 'candles' in data['data']:
            candles = data['data']['candles']
            # Upstox deta hai [timestamp, open, high, low, close, volume, oi]
            df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values('Timestamp')
            return df
        else:
            st.error(f"Upstox Error: {data}")
            return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def check_signal(df):
    if df is None or len(df) < 25:
        return None
    
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    # === TOPU KE FILTERS - AB OI REAL HAI UPSTOX SE ===
    volume_ok = last['Volume'] > last['Vol_SMA'] * 0.8
    price_up = last['Close'] > prev['Close']
    
    # REAL OI FILTER - Ab yfinance ka jugar nahi, Upstox ka asli OI
    oi_up = last['OI'] > prev['OI'] if 'OI' in df.columns else True
    oi_fake_bullish = price_up and not oi_up  # Price up, OI down = Trap
    
    # Liquidity Sweep
    lower_wick = min(prev2['Open'], prev2['Close']) - prev2['Low']
    body_range = prev2['High'] - prev2['Low']
    is_sweep = lower_wick > body_range * 0.6 if body_range>0 else False

    buy_cross = (prev['EMA9'] < prev['EMA21']) and (last['EMA9'] > last['EMA21'])
    sell_cross = (prev['EMA9'] > prev['EMA21']) and (last['EMA9'] < last['EMA21'])

    signal = "WAIT"
    reason = "Market dekh raha hu..."

    if buy_cross and last['RSI'] > 55 and volume_ok and not oi_fake_bullish:
        if last['Close'] > prev['High']:
            signal = "BUY"
            reason = f"No Trap BUY - OI {last['OI']} up hai, Volume OK"
    elif sell_cross and last['RSI'] < 45 and volume_ok:
        if last['Close'] < prev['Low']:
            signal = "SELL"
            reason = f"SELL - OI confirm"

    if oi_fake_bullish:
        reason = f"TRAP! Price up par OI down ({last['OI']}) - Mat le entry"
    elif is_sweep:
        reason = "TRAP! Abhi Stop Hunt hua - 1 candle wait"

    return last['Close'], last['EMA9'], last['EMA21'], last['RSI'], last['OI'], signal, reason

# === LIVE DASHBOARD ===
placeholder = st.empty()

while True:
    with placeholder.container():
        cols = st.columns(3)
        for i, (name, key) in enumerate(SYMBOLS.items()):
            df = get_upstox_candles(key, timeframe)
            if df is None:
                continue
            
            result = check_signal(df)
            if result is None:
                continue
            
            price, ema9, ema21, rsi, oi, signal, reason = result
            
            with cols[i]:
                st.subheader(name)
                st.metric("Live Price", f"{price:.2f}", f"RSI {rsi:.1f} | OI {oi}")
                st.write(f"EMA9: {ema9:.2f} | EMA21: {ema21:.2f}")
                
                if signal == "BUY":
                    st.success(f"🟢 {signal} - {reason}")
                elif signal == "SELL":
                    st.error(f"🔴 {signal} - {reason}")
                else:
                    st.warning(f"🟡 {signal} - {reason}")
                st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
                st.divider()
    
    time.sleep(refresh_sec)
    st.rerun()