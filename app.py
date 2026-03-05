import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página Web
st.set_page_config(page_title="Quant XAU/USD Terminal", layout="wide")
st.title("🚀 Terminal Cuantitativa: XAU/USD (Gold)")

# --- MENU LATERAL ---
st.sidebar.header("Configuración de Estrategia")
symbol = "GC=F"
intervalo = st.sidebar.selectbox("Temporalidad", ["5m", "15m", "1h"], index=0)
vol_mult = st.sidebar.slider("Sensibilidad Volumen (Multiplicador)", 1.5, 4.0, 2.5)
reentrada_pips = st.sidebar.number_input("Distancia Reentrada (Pips)", value=30)

# --- MOTOR DE DATOS ---
def get_data():
    df = yf.download(symbol, period="2d", interval=intervalo, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

data = get_data()

# --- LÓGICA CUANTITATIVA ---
v, p = data['Volume'], (data['High'] + data['Low'] + data['Close']) / 3
data['VWAP'] = (p * v).cumsum() / v.cumsum()
data['Vol_MA'] = data['Volume'].rolling(window=20).mean()

def detect_sig(row):
    cuerpo = row['High'] - row['Low']
    if cuerpo == 0 or row['Volume'] < (row['Vol_MA'] * vol_mult): return None
    pos = (row['Close'] - row['Low']) / cuerpo
    if pos > 0.85: return 'BULL'
    if pos < 0.15: return 'BEAR'
    return None

data['Sig'] = data.apply(detect_sig, axis=1)

# --- GRÁFICO INTERACTIVO ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], 
                             low=data['Low'], close=data['Close'], name='Precio'))
fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], line=dict(color='white', width=1, dash='dot'), name='VWAP'))

# Señales
bulls = data[data['Sig'] == 'BULL']
bears = data[data['Sig'] == 'BEAR']
fig.add_trace(go.Scatter(x=bulls.index, y=bulls['Low'], mode='markers', marker=dict(color='#00FFCC', size=12, symbol='diamond')))
fig.add_trace(go.Scatter(x=bears.index, y=bears['High'], mode='markers', marker=dict(color='#FF3E3E', size=12, symbol='diamond')))

fig.update_layout(template='plotly_dark', height=700, xaxis_rangeslider_visible=False)

# --- DASHBOARD DE ESTADO ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Precio Actual", f"${round(data['Close'].iloc[-1], 2)}")
with col2:
    diff_vwap = round(data['Close'].iloc[-1] - data['VWAP'].iloc[-1], 2)
    st.metric("Distancia al VWAP", f"{diff_vwap} pts")
with col3:
    st.write(f"**Última Act:** {datetime.now().strftime('%H:%M:%S')}")

st.plotly_chart(fig, use_container_width=True)

# Botón de refresco manual (Streamlit Cloud actualiza al interactuar)
if st.button('Actualizar Mercado'):
    st.rerun()