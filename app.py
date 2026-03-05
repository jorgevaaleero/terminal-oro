import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. CONFIGURACIÓN Y AUTO-REFRESCO (Cada 10 segundos)
st.set_page_config(page_title="Live Quant Signal", layout="wide")
st_autorefresh(interval=10 * 1000, key="data_refresh") # 10000ms = 10s

st.markdown("<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)

# --- MOTOR DE DATOS ---
def load_data():
    # Pedimos 2 días para tener suficiente histórico para el VWAP
    df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

data = load_data()

# --- CÁLCULOS CUANTITATIVOS ---
data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
data['VWAP'] = (data['TP'] * data['Volume']).cumsum() / data['Volume'].cumsum()

def get_rsi(series, p=14):
    delta = series.diff()
    g = (delta.where(delta > 0, 0)).rolling(p).mean()
    l = (-delta.where(delta < 0, 0)).rolling(p).mean()
    rs = g / l
    return 100 - (100 / (1 + rs))

data['RSI'] = get_rsi(data['Close'])
data['Vol_MA'] = data['Volume'].rolling(20).mean()

# --- LÓGICA DE DECISIÓN (Última vela cerrada) ---
# Usamos la penúltima vela si la actual aún no tiene volumen suficiente
vela = data.iloc[-1] 
vol_ok = vela['Volume'] > (vela['Vol_MA'] * 2.2)
cuerpo = vela['High'] - vela['Low']
pos = (vela['Close'] - vela['Low']) / cuerpo if cuerpo != 0 else 0.5

decision = "ESPERA ⏳"
color_box = "#E0E0E0" # Gris claro

# Condición COMPRA: Volumen + Cierre Arriba + RSI bajo + Bajo VWAP
if vol_ok and pos > 0.85 and vela['RSI'] < 55 and vela['Close'] < vela['VWAP']:
    decision = "COMPRA 🚀"
    color_box = "#00FFCC"
# Condición VENTA: Volumen + Cierre Abajo + RSI alto + Sobre VWAP
elif vol_ok and pos < 0.15 and vela['RSI'] > 45 and vela['Close'] > vela['VWAP']:
    decision = "VENTA 📉"
    color_box = "#FF3E3E"

# --- INTERFAZ VISUAL ---
st.title("🥇 Monitor Real-Time XAU/USD")

# Semáforo Gigante
st.markdown(f"""
    <div style="background-color:{color_box}; padding:30px; border-radius:15px; text-align:center; border: 2px solid #333;">
        <h1 style="color:black; font-size: 60px; margin:0;">{decision}</h1>
        <p style="color:black; font-size: 20px; font-weight:bold; opacity: 0.8;">
            Actualizado: {datetime.now().strftime('%H:%M:%S')}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.write("") 

# Gráfico de apoyo
fig = go.Figure()
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Oro'))
fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], line=dict(color='#00D4FF', width=2), name='VWAP'))
fig.update_layout(template='plotly_dark', height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# Métricas rápidas abajo
c1, c2, c3 = st.columns(3)
c1.metric("Precio Actual", f"${round(vela['Close'], 2)}")
c2.metric("Fuerza RSI", f"{round(vela['RSI'], 1)}")
c3.metric("Distancia VWAP", f"{round(vela['Close'] - vela['VWAP'], 2)} pts")
