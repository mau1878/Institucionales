import streamlit as st
from utils.data_processing import load_data, get_market_caps, preprocess_data
from utils.plotting import plot_market_concentration

st.set_page_config(page_title="Concentración de Mercado", layout="wide")
st.title("🏛️ Concentración de Mercado por Sector / Industria")

# === Cargar datos ===
institutional_holders, general_data = load_data()
live_market_caps = get_market_caps(general_data['Ticker'].unique())
merged_data, _ = preprocess_data(institutional_holders, general_data, live_market_caps)

# 🔹 Asegurarse de que las columnas existen y rellenar NaN
for col in ["Sector", "Industry"]:
    if col not in merged_data.columns:
        merged_data[col] = "Sin Datos"
    else:
        merged_data[col] = merged_data[col].fillna("Sin Datos")

# === Selección de nivel de análisis ===
nivel_radio = st.radio("📊 Nivel de análisis:", ["Sector", "Industria"])
group_field = "Sector" if nivel_radio == "Sector" else "Industry"

# === Filtros adicionales ===
filtered_data = merged_data.copy()
if group_field == "Industry":
    selected_sector = st.selectbox("Filtrar por Sector:", merged_data["Sector"].unique())
    filtered_data = filtered_data[filtered_data["Sector"] == selected_sector]

top_bottom_option = st.radio("Mostrar:", ["Top N", "Bottom N"])
top_n = st.number_input("N:", min_value=1, max_value=50, value=5, step=1)

# === Validación antes de graficar ===
if filtered_data.empty:
    st.warning("No hay datos disponibles para la selección actual.")
else:
    plot_market_concentration(filtered_data, group_field, top_n=top_n, top_bottom=top_bottom_option)
