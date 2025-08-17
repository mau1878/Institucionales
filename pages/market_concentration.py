import streamlit as st
from utils.data_processing import load_data, get_market_caps, preprocess_data
from utils.plotting import plot_market_concentration

st.set_page_config(page_title="Concentración de Mercado", layout="wide")
st.title("🏦 Concentración de mercado por sector/industria")

# === Cargar datos ===
institutional_holders, general_data = load_data()
live_market_caps = get_market_caps(general_data['Ticker'].unique())
merged_data, merged_data_display = preprocess_data(institutional_holders, general_data, live_market_caps)

# 🔹 Asegurarse de que las columnas existen y rellenar NaN
for col in ["Sector", "Industry"]:
    if col not in merged_data.columns:
        merged_data[col] = "Sin Datos"
    else:
        merged_data[col] = merged_data[col].fillna("Sin Datos")

# === Selección de nivel de análisis ===
group_field = st.radio("Seleccionar nivel de análisis:", ["Sector", "Industria"])

# 🔹 Filtro adicional si se quiere analizar industrias dentro de un sector
if group_field == "Industry":
    selected_sector = st.selectbox("Seleccionar sector para filtrar industrias:", merged_data["Sector"].unique())
    filtered_data = merged_data[merged_data["Sector"] == selected_sector]
else:
    filtered_data = merged_data

# === Top N tenedores ===
top_n = st.number_input("Mostrar top N tenedores por grupo:", min_value=1, max_value=50, value=5, step=1)

# === Botón para generar gráfico ===
if st.button("Generar concentración de mercado"):
    plot_market_concentration(filtered_data, group_field, top_n=top_n)
else:
    st.info("Selecciona opciones y presiona 'Generar concentración de mercado' para ver el gráfico.")
