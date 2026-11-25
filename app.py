import json
import os
import urllib.request
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Bitcoin - Evidencia 03.01",
    page_icon="📈",
    layout="wide",
)

# Paleta oficial de la materia
COLOR_BASE = "#B9C3D1"
COLOR_DESTACADO = "#1C4C9A"
PALETA = ["#E69F00", "#56B4E9", "#009E73", "#0072B2"]


# 1. Función de carga con caché de Streamlit y respaldo local
@st.cache_data(ttl=3600)
def cargar_datos():
  json_file = "respuesta.json"
  if not os.path.exists(json_file):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&interval=daily"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
      with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
        with open(json_file, "w", encoding="utf-8") as f:
          json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
      st.error(f"Error al conectar con la API de CoinGecko: {e}")
      st.stop()
  else:
    with open(json_file, "r", encoding="utf-8") as f:
      data = json.load(f)

  df_prices = pd.DataFrame(data["prices"], columns=["timestamp", "precio_usd"])
  df_volumes = pd.DataFrame(
      data["total_volumes"], columns=["timestamp", "volumen_usd"]
  )
  df = pd.merge(df_prices, df_volumes, on="timestamp").dropna()
  df["fecha"] = pd.to_datetime(df["timestamp"], unit="ms")
  df["trimestre"] = df["fecha"].dt.to_period("Q").astype(str)
  return df


df = cargar_datos()

# 2. Encabezado y Barra Lateral (Filtros Interactivos)
st.title("📊 Análisis Histórico de Bitcoin (CoinGecko API)")
st.markdown(
    "Dashboard interactivo generado a partir de los datos de mercado (últimos"
    " 365 días)."
)

st.sidebar.header("Filtros del Dashboard")
trimestres_disponibles = sorted(df["trimestre"].unique())
trimestres_sel = st.sidebar.multiselect(
    "Selecciona los trimestres a visualizar:",
    options=trimestres_disponibles,
    default=trimestres_disponibles,
)

bins_hist = st.sidebar.slider(
    "Intervalos del histograma (Bins):", min_value=10, max_value=40, value=20
)

# Filtrado dinámico
df_filtrado = df[df["trimestre"].isin(trimestres_sel)]

if df_filtrado.empty:
  st.warning(
      "Selecciona al menos un trimestre en el menú lateral para visualizar los"
      " datos."
  )
  st.stop()

# 3. Tarjetas de Métricas (KPIs)
col1, col2, col3, col4 = st.columns(4)
precio_actual = df_filtrado["precio_usd"].iloc[-1]
precio_max = df_filtrado["precio_usd"].max()
precio_min = df_filtrado["precio_usd"].min()
vol_promedio = df_filtrado["volumen_usd"].mean() / 1e9

col1.metric("Último Precio (Periodo)", f"${precio_actual:,.2f} USD")
col2.metric("Precio Máximo", f"${precio_max:,.2f} USD")
col3.metric("Precio Mínimo", f"${precio_min:,.2f} USD")
col4.metric("Volumen Diario Promedio", f"${vol_promedio:,.2f} B")

st.divider()

# 4. Cuadrícula de las 4 Visualizaciones
fila1_col1, fila1_col2 = st.columns(2)

with fila1_col1:
  st.subheader("1. Evolución del Precio")
  fig1, ax1 = plt.subplots(figsize=(8, 4))
  ax1.plot(
      df_filtrado["fecha"],
      df_filtrado["precio_usd"],
      color=COLOR_DESTACADO,
      linewidth=1.8,
  )
  ax1.set_title("Tendencia de cotización en USD", fontsize=10, fontweight="bold")
  ax1.set_xlabel("Fecha")
  ax1.set_ylabel("Precio (USD)")
  ax1.grid(True, linestyle="--", alpha=0.5)
  st.pyplot(fig1)
  st.caption(
      "**Lectura:** Muestra la trayectoria diaria del activo dentro de los"
      " trimestres seleccionados."
  )

with fila1_col2:
  st.subheader("2. Distribución de Precios")
  fig2, ax2 = plt.subplots(figsize=(8, 4))
  ax2.hist(
      df_filtrado["precio_usd"],
      bins=bins_hist,
      color=COLOR_BASE,
      edgecolor="white",
  )
  ax2.set_title(
      "Frecuencia de niveles de cotización", fontsize=10, fontweight="bold"
  )
  ax2.set_xlabel("Precio (USD)")
  ax2.set_ylabel("Frecuencia (Días)")
  st.pyplot(fig2)
  st.caption(
      "**Lectura:** Identifica los rangos de precio donde el mercado operó con"
      " mayor frecuencia."
  )

fila2_col1, fila2_col2 = st.columns(2)

with fila2_col1:
  st.subheader("3. Relación Volumen vs. Precio")
  fig3, ax3 = plt.subplots(figsize=(8, 4))
  ax3.scatter(
      df_filtrado["volumen_usd"] / 1e9,
      df_filtrado["precio_usd"],
      color=COLOR_DESTACADO,
      alpha=0.6,
  )
  ax3.set_title(
      "Correlación entre volumen operado y precio",
      fontsize=10,
      fontweight="bold",
  )
  ax3.set_xlabel("Volumen Diario (Miles de Millones USD)")
  ax3.set_ylabel("Precio (USD)")
  ax3.grid(True, linestyle="--", alpha=0.5)
  st.pyplot(fig3)
  st.caption(
      "**Lectura:** Evalúa si los días de mayor flujo de capital coinciden con"
      " precios más altos."
  )

with fila2_col2:
  st.subheader("4. Comparativa por Trimestre")
  fig4, ax4 = plt.subplots(figsize=(8, 4))
  trims_ordenados = sorted(df_filtrado["trimestre"].unique())
  datos_box = [
      df_filtrado[df_filtrado["trimestre"] == t]["precio_usd"]
      for t in trims_ordenados
  ]

box = ax4.boxplot(
       datos_box, tick_labels=trims_ordenados, patch_artist=True
   )
  for patch, color in zip(box["boxes"], PALETA * 2):
    patch.set_facecolor(color)

  ax4.set_title(
      "Dispersión y mediana por periodo trimestral",
      fontsize=10,
      fontweight="bold",
  )
  ax4.set_xlabel("Trimestre")
  ax4.set_ylabel("Precio (USD)")
  st.pyplot(fig4)
  st.caption(
      "**Lectura:** Compara la estabilidad (ancho de caja) y la mediana entre"
      " los distintos periodos."
  )

# 5. Sección de Preguntas Descartadas y Tabla de Datos
st.divider()
with st.expander("📋 Ver alcance de datos y preguntas no viables"):
  st.markdown("""
    * **Predicción a futuro:** No es viable con esta API, ya que solo entrega registros históricos.
    * **Impacto macroeconómico:** No se incluyen tasas de interés ni índices de inflación en el JSON.
    * **Cálculo de rendimiento personal:** Se requieren los montos y fechas exactas de inversión individual.
    """)

with st.expander("🗄️ Explorar tabla de datos limpios"):
  st.dataframe(
      df_filtrado[["fecha", "trimestre", "precio_usd", "volumen_usd"]],
      use_container_width=True,
  )
