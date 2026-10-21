import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOPU TOWER - NO.1 SIGNAL", layout="wide")
st.title("👑 TOPU TOWER - WORLD NO.1 SIGNAL")

# ========= 1. YEARLY TOKEN CHECK =========
def check_yearly_token(token):
    try:
        curr_year = datetime.now().year
        token_year = int(token.split('-')[1]) if '-' in token else 2026
        return curr_year <= token_year
    except:
        return True # Testing ke liye abhi open rakha hai

token = st.text_input("🔑 Yearly Token (TOPU-2026-XXXX)", value="TOPU-2026-TEST")
if not check_yearly_token(token):
    st.error("TOKEN EXPIRE - NAYA DALO")
    st.stop()

# ========= 2. NO.1 LOGIC =========
st.subheader("SENSEX / NIFTY - Live Signal Tower")

# Yaha tera Upstox Live Data ayega
# close, ema, supertrend, OI data
# Main structure de raha hu

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("FIDI EMA", "✅ BULLISH", "Trend Up")
col2.metric("EMA 9>21", "✅ BULLISH", "Speed Tez")
col3.metric("SuperTrend", "✅ BUY", "Dir -1")
col4.metric("Smart Money", "✅ BOS", "Order Block Hold")
col5.metric("Option Chain", "✅ OI BUILDUP", "PCR 1.2 - Call Writing Kam")

st.divider()

# FINAL CONFLUENCE
fidi = True
ema = True
stt = True
smc = True
oi = True

if fidi and ema and stt and smc and oi:
    st.success("🚀 SIGNAL NO.1 - PERFECT BUY - AB MANUAL EXECUTE KAR TOPU BHAI")
    st.balloons()
    st.write("**Option Chain:** Nifty 25500 CE pe OI kam ho raha hai, PE pe add ho raha hai + Smart Money Order Block se bounce")
else:
    st.warning("⏳ WAIT - 5 ka Jod Nahi Mila, Perfect ka Intezaar Kar")

# Manual Execution Note
st.info("💡 Execution: Tu bas signal dekh ke Upstox App me jaake manually BUY/SELL maar dega. Tower order nahi marega.")