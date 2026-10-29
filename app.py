import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="V101 MCX FIRE", layout="wide")
st.title("V101 - MCX FIRE ON ✅ Coddu Sharma")

token_input = st.text_input("Upstox Token (Roz Naya)", type="password")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()

token = st.session_state.get("tok", "")
if not token or len(token) < 50:
    st.warning("Pehle Upstox ka Token daal - Roz naya lena padta hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

INSTRUMENTS = {
    "SENSEX": "BSE_INDEX|SENSEX",
    "BANKEX": "BSE_INDEX|BANKEX",
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "GOLD": "MCX_FO|495213",
    "CRUDEOIL": "MCX_FO|573422",
    "SILVER": "MCX_FO|495214",
}

def ema(s, p): return s.ewm(span=p, adjust=False).mean()
def rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0).rolling(p).mean()
    l = -d.where(d < 0, 0).rolling(p).mean()
    rs = g / l.replace(0, 0.001)
    return 100 - (100 / (1 + rs))
def atr(df, p=10):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(p).mean()
def supertrend_v96(df):
    df = df.copy()
    df["atr"] = atr(df, 10)
    hl2 = (df["high"] + df["low"]) / 2
    df["upper"] = hl2 + (3 * df["atr"])
    df["lower"] = hl2 - (3 * df["atr"])
    df["st"] = np.where(df["close"] > df["upper"].shift(), df["lower"], df["upper"])
    return df["close"].iloc[-1] > df["st"].iloc[-1]

def get_df_v101(key):
    try:
        url = f"https://api.upstox.com/v3/historical-candle/intraday/{key}/5minute"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            c = r.json().get("data", {}).get("candles", [])
            if c and len(c) > 20:
                df = pd.DataFrame(c, columns=["ts","open","high","low","close","volume","oi"])
                return df.iloc[::-1].reset_index(drop=True)
    except: pass
    return None

def get_ltp_batch(all_keys):
    try:
        url = "https://api.upstox.com/v3/market-quote/ltp"
        params = {"instrument_key": ",".join(all_keys)}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get("data", {})
        return {}
    except: return {}

st.caption(f"TIME: {datetime.now().strftime('%H:%M:%S')} | MCX OPEN 9AM-11:55PM")

@st.fragment(run_every=2)
def live_board():
    all_keys_list = list(INSTRUMENTS.values())
    ltp_data = get_ltp_batch(all_keys_list)
    if not ltp_data:
        st.error("LTP nahi aaya - Token check kar")
        return

    for name, pipe_key in INSTRUMENTS.items():
        colon_key = pipe_key.replace("|", ":")
        q = ltp_data.get(colon_key) or ltp_data.get(pipe_key) or {}
        if not q:
            for v in ltp_data.values():
                if v.get("instrument_token") == pipe_key:
                    q = v
                    break
        ltp = q.get("last_price", 0) if q else 0
        df = get_df_v101(pipe_key)

        if df is None or len(df) < 10:
            if ltp:
                st.markdown(f"### {name} - Rs.{ltp:.1f} - 💤 Closed / WAIT Candle")
            else:
                st.markdown(f"### {name} - WAIT")
            continue

        close = df["close"]
        high = df["high"]
        low = df["low"]
        e9 = ema(close, 9).iloc[-1]
        e21 = ema(close, 21).iloc[-1]
        e50 = ema(close, 50).iloc[-1]
        r_val = rsi(close).iloc[-1]
        live_price = ltp if ltp and ltp > 0 else close.iloc[-1]

        if df["volume"].sum() > 0:
            tp = (df["high"] + df["low"] + df["close"]) / 3
            vwap = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
            vwap_check = live_price > vwap.iloc[-1]
        else: vwap_check = True

        try: st_check = supertrend_v96(df)
        except: st_check = live_price > e50
        bos_check = live_price > high.iloc[-11:-1].max()

        checks = {"EMA9>21": e9>e21, "Close>EMA9": live_price>e9, "RSI 50+": r_val>50, "Supertrend": st_check, "EMA50": live_price>e50, "BOS": bos_check, "SAFE": abs(live_price-e9)/live_price < 0.008, "FVG": low.iloc[-1] > high.iloc[-2], "VWAP": vwap_check, "TIME": True}
        score = sum(checks.values())
        color = "#00ff88" if score>=7 else "#ffaa00" if score>=4 else "#ff4444"
        tag = "🔥 FIRE" if score>=7 else "⚠️ SETUP" if score>=4 else "💤 WAIT"
        st.markdown(f"### {name} - Rs.{live_price:.1f} - <span style='color:{color}'>{score}/10 {tag}</span> - RSI:{r_val:.0f}", unsafe_allow_html=True)
        if score < 10:
            failed = [k for k,v in checks.items() if not v]
            st.caption(f"Fail: {', '.join(failed)}")

live_board()
st.caption("V101 FINAL | Copy done = Century Done 💯")