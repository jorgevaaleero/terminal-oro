import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de Estética Profesional
st.set_page_config(page_title="Terminal Quant Pro - XAU/USD", layout="wide")
st.markdown("<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)

st.title("🥇 Terminal Quant Oro (XAU/USD)")

# --- MENU LATERAL ---
st.sidebar.header("⚙️ Parámetros de Élite")
intervalo = st.sidebar.selectbox("Temporalidad Operativa", ["5m", "15m", "1h"], index=1)
vol_sens = st.sidebar.slider("Sensibilidad Institucional", 1.5, 3.5, 2.2)
pips_dist = st.sidebar.number_input("Distancia de Reentrada (Pips)", value=30)

# --- MOTOR DE DATOS ---
def load_market_data():
    df = yf.download("GC=F", period="5d", interval=intervalo, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

data = load_market_data()

# --- CÁLCULOS CUANTITATIVOS ---
# VWAP Diario Corregido
data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
data['VWAP'] = (data['TP'] * data['Volume']).cumsum() / data['Volume'].cumsum()

# Filtro RSI para Fiabilidad
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

data['RSI'] = calc_rsi(data['Close'])
data['Vol_MA'] = data['Volume'].rolling(window=20).mean()

# Lógica de Diamantes de "Alta Fidelidad"
def logic_pro(row):
    cuerpo = row['High'] - row['Low']
    vol_extremo = row['Volume'] > (row['Vol_MA'] * vol_sens)
    if cuerpo == 0 or not vol_extremo: return None
    
    pos = (row['Close'] - row['Low']) / cuerpo
    # Filtro de Doble Confirmación (Volumen + Cierre + RSI)
    if pos > 0.85 and row['RSI'] < 60: return 'BUY'
    if pos < 0.15 and row['RSI'] > 40: return 'SELL'
    return None

data['Signal'] = data.apply(logic_pro, axis=1)

# --- VISUALIZACIÓN ---
fig = go.Figure()

# Velas
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], 
                             low=data['Low'], close=data['Close'], name='Oro'))

# VWAP (Línea de Equilibrio)
fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], 
                         line=dict(color='#00D4FF', width=2, dash='dot'), name='VWAP Diario'))

# Señales Diamantes
bulls = data[data['Signal'] == 'BUY']
bears = data[data['Signal'] == 'SELL']

fig.add_trace(go.Scatter(x=bulls.index, y=bulls['Low'], mode='markers', 
                         marker=dict(color='#00FFCC', size=14, symbol='diamond', line=dict(width=1, color='white')), name='Smart Buy'))

fig.add_trace(go.Scatter(x=bears.index, y=bears['High'], mode='markers', 
                         marker=dict(color='#FF3E3E', size=14, symbol='diamond', line=dict(width=1, color='white')), name='Smart Sell'))

# Marcador de Reentrada (Tu zona de 30 pips)
if not data[data['Signal'].notnull()].empty:
    last_sig = data[data['Signal'].notnull()].iloc[-1]
    reent_val = (pips_dist / 10) # 30 pips = 3 puntos
    p_reent = last_sig['Close'] - reent_val if last_sig['Signal'] == 'BUY' else last_sig['Close'] + reent_val
    fig.add_hline(y=p_reent, line_dash="dash", line_color="orange", annotation_text=f"ZONA REENTRADA ({pips_dist} Pips)")

fig.update_layout(template='plotly_dark', height=750, xaxis_rangeslider_visible=False,
                  margin=dict(l=20, r=20, t=30, b=20))

# --- DASHBOARD ---
c1, c2, c3 = st.columns(3)
with c1: st.metric("Precio Actual", f"${round(data['Close'].iloc[-1], 2)}")
with c2: st.metric("RSI (Filtro)", f"{round(data['RSI'].iloc[-1], 1)}")
with c3: st.write(f"**Última Act:** {datetime.now().strftime('%H:%M:%S')}")

st.plotly_chart(fig, use_container_width=True)
if st.button('🚀 Refrescar Mercado'): st.rerun()
