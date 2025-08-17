import streamlit as st
from utils.data_processing import load_data, get_market_caps, preprocess_data
from utils.plotting import plot_holder_distribution, plot_holders_heatmap

st.set_page_config(page_title="Distribución de holdings por tenedor", layout="wide")
st.title("📊 Distribución de holdings por tenedor")

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

# === Selección de categoría ===
group_field = st.radio("Seleccionar categoría para filtrar:", ["Sector", "Industry"])

# === Filtrado opcional por categorías específicas ===
categories = merged_data[group_field].unique()
selected_categories = st.multiselect(f"Filtrar {group_field} específicos (opcional):", categories)

if selected_categories:
    filtered_data = merged_data[merged_data[group_field].isin(selected_categories)]
else:
    filtered_data = merged_data

# === Filtro top/bottom N tenedores ===
n_filter = st.number_input("Mostrar solo top/bottom N tenedores por valor total:", min_value=1, max_value=100, value=20, step=1)
top_bottom_option = st.radio("Top o Bottom:", ["Top", "Bottom"])

# Aplicar filtro por valor total
holder_totals = filtered_data.groupby("Owner Name")["Individual Holdings Value"].sum().reset_index()
holder_totals = holder_totals.sort_values("Individual Holdings Value", ascending=(top_bottom_option=="Bottom"))
top_bottom_holders = holder_totals.head(n_filter)["Owner Name"]
filtered_data = filtered_data[filtered_data["Owner Name"].isin(top_bottom_holders)]

# === Botón para generar gráficos ===
if st.button("Generar gráficos"):
    st.subheader("📊 Distribución de holdings por tenedor")
    plot_holder_distribution(filtered_data, group_field)

    st.subheader("💹 Heatmap de holdings por tenedor")
    plot_holders_heatmap(filtered_data, group_field)
else:
    st.info("Selecciona categoría(s), top/bottom N y presiona 'Generar gráficos' para ver los plots.")
