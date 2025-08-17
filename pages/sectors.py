import streamlit as st
import pandas as pd
from utils.data_processing import load_data, get_market_caps, preprocess_data
from utils.plotting import plot_top_20, plot_holder_composition

st.set_page_config(page_title="Tenedores Institucionales por Sector e Industria", layout="wide")

st.title("🏦 Tenedores Institucionales por Sector e Industria")

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
opcion = st.radio("📊 Seleccionar nivel de análisis:", ["Sector", "Industria"])
group_field = "Sector" if opcion == "Sector" else "Industry"

# === Calcular estadísticas por grupo ANTES de las tabs ===
group_stats = (
    merged_data.groupby(group_field)
    .agg({
        "Individual Holdings Value": "sum",
        "Percentage Owned": "mean",
        "Ticker": "nunique"
    })
    .rename(columns={
        "Individual Holdings Value": "Valor Total (USD millones)",
        "Percentage Owned": "Promedio % de Propiedad",
        "Ticker": "Número de Tickers"
    })
    .sort_values("Valor Total (USD millones)", ascending=False)
)

# === Crear tabs ===
tabs = st.tabs([
    f"📈 Estadísticas por {opcion}",
    f"🏆 Top {opcion}",
    f"🔎 Detalle por {opcion}",
    "📊 Composición de tenedor"
])

# === Tab 1: Estadísticas generales ===
with tabs[0]:
    st.subheader(f"📈 Estadísticas generales por {opcion}")
    st.dataframe(group_stats, use_container_width=True)

# === Tab 2, 3, 4 ... igual que antes

# === Tab 2: Top sectores / industrias por valor total ===
with tabs[1]:
    st.subheader(f"🏆 Principales {opcion} por Valor Total en manos de institucionales")
    plot_top_20(
        group_stats.reset_index(),
        x=group_field,
        y="Valor Total (USD millones)",
        title=f"Top {opcion} por Valor en manos institucionales",
        color="blue"
    )

# === Tab 3: Análisis detallado por sector/industria ===
with tabs[2]:
    st.subheader(f"🔎 Análisis detallado por {opcion}")
    selected = st.selectbox(f"Seleccionar {opcion}:", group_stats.index)

    if selected:
        filtered = merged_data[merged_data[group_field] == selected]

        # Top tenedores dentro del sector/industria
        top_holders = (
            filtered.groupby("Owner Name")
            .agg({
                "Individual Holdings Value": "sum",
                "Shares Held": "sum"
            })
            .rename(columns={
                "Individual Holdings Value": "Valor Total (USD millones)",
                "Shares Held": "Acciones Totales"
            })
            .sort_values("Valor Total (USD millones)", ascending=False)
        )

        st.write(f"### 🏦 Principales tenedores en {selected}")
        st.dataframe(top_holders.head(15), use_container_width=True)

        plot_top_20(
            top_holders.reset_index(),
            x="Owner Name",
            y="Valor Total (USD millones)",
            title=f"Top Tenedores en {selected}",
            color="green"
        )

# === Tab 4: Composición de un tenedor ===
with tabs[3]:
    st.subheader("📊 Composición de cartera de un tenedor")
    selected_holder = st.selectbox(
        "Seleccionar tenedor:",
        merged_data["Owner Name"].unique()
    )

    if selected_holder:
        plot_holder_composition(merged_data, selected_holder, group_field)
