import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de Interfaz Limpia
st.set_page_config(page_title="Quant Signal Pro", layout="wide")
st.markdown("<style>div.block-container{padding-top:1.5rem;}</style>", unsafe_allow_html=True)

# --- MOTOR DE DATOS ---
def load_data():
    df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

data = load_data()

# --- CÁLCULOS (VWAP, RSI, VOLUMEN) ---
data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
data['VWAP'] = (data['TP'] * data['Volume']).cumsum() / data['Volume'].cumsum()

def get_rsi(series, p=14):
    delta = series.diff()
    g = (delta.where(delta > 0, 0)).rolling(p).mean()
    l = (-delta.where(delta < 0, 0)).rolling(p).mean()
    return 100 - (100 / (1 + (g/l)))

data['RSI'] = get_rsi(data['Close'])
data['Vol_MA'] = data['Volume'].rolling(20).mean()

# --- LÓGICA DE DECISIÓN AUTOMÁTICA ---
ultima_vela = data.iloc[-1]
vol_ok = ultima_vela['Volume'] > (ultima_vela['Vol_MA'] * 2.2)
cuerpo = ultima_vela['High'] - ultima_vela['Low']
pos = (ultima_vela['Close'] - ultima_vela['Low']) / cuerpo if cuerpo != 0 else 0.5

# Evaluación de condiciones
decision = "ESPERA ⏳"
color_box = "#31333F" # Gris neutro

if vol_ok:
    # Condición de COMPRA: Volumen fuerte + Cierre arriba + RSI bajo + Bajo el VWAP
    if pos > 0.85 and ultima_vela['RSI'] < 55 and ultima_vela['Close'] < ultima_vela['VWAP']:
        decision = "COMPRA 🚀"
        color_box = "#00FFCC"
    # Condición de VENTA: Volumen fuerte + Cierre abajo + RSI alto + Sobre el VWAP
    elif pos < 0.15 and ultima_vela['RSI'] > 45 and ultima_vela['Close'] > ultima_vela['VWAP']:
        decision = "VENTA 📉"
        color_box = "#FF3E3E"

# --- INTERFAZ VISUAL ---
st.title("🥇 Terminal de Señales XAU/USD")

# Cuadro de Decisión Gigante
st.markdown(f"""
    <div style="background-color:{color_box}; padding:20px; border-radius:10px; text-align:center;">
        <h1 style="color:black; margin:0;">{decision}</h1>
        <p style="color:black; font-weight:bold; margin:0;">Basado en Confluencia Quant (VWAP + RSI + Vol)</p>
    </div>
    """, unsafe_allow_html=True)

st.write("") # Espacio

# Dashboard de métricas
c1, c2, c3, c4 = st.columns(4)
c1.metric("Precio", f"${round(ultima_vela['Close'], 2)}")
c2.metric("RSI", f"{round(ultima_vela['RSI'], 1)}")
c3.metric("VWAP", f"${round(ultima_vela['VWAP'], 2)}")
c4.metric("Volumen vs Media", f"{round(ultima_vela['Volume']/ultima_vela['Vol_MA'], 1)}x")

# Gráfico
fig = go.Figure()
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Precio'))
fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], line=dict(color='#00D4FF', width=2), name='VWAP'))
fig.update_layout(template='plotly_dark', height=500, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

if st.button('Actualizar Ahora'): st.rerun()
