import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.plotting import plot_top_20, plot_changes
from utils.data_processing import color_percentage

# Set custom page title for sidebar
st.set_page_config(page_title="Análisis de Tenedores", layout="wide")

if 'merged_data' not in st.session_state:
    st.error("Datos no cargados. Por favor, revisa la página principal.")
    st.stop()

st.header("Análisis de Tenedor Institucional")
st.write("""
**Cómo usar esta sección:**
- **Selecciona un Tenedor Institucional:** Elige un tenedor para ver sus inversiones en diferentes empresas (tickers).
- **Datos mostrados:** Verás las acciones mantenidas, el cambio en las acciones y el porcentaje de propiedad en cada empresa.
**Explicación de los datos:**
- **Acciones Mantenidas:** Número de acciones que el tenedor posee en cada empresa.
- **Cambio en Acciones:** Diferencia en el número de acciones desde la última actualización.
- **Porcentaje de Propiedad:** Porcentaje de las acciones totales de la empresa que posee el tenedor.
- **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
""")

merged_data = st.session_state.merged_data
merged_data_display = st.session_state.merged_data_display

# Apply global date filter
if st.session_state.selected_date:
    merged_data = merged_data[merged_data['Date'] == st.session_state.selected_date]
    merged_data_display = merged_data_display[merged_data_display['Date'] == st.session_state.selected_date]

institutional_holders_list = sorted(merged_data["Owner Name"].unique())
selected_holder = st.selectbox("Selecciona un Tenedor Institucional:", institutional_holders_list)

holder_data = merged_data[merged_data["Owner Name"] == selected_holder]
holder_data_display = merged_data_display[merged_data_display["Owner Name"] == selected_holder]
holder_data_display = holder_data_display.sort_values(by='Shares Change % num', ascending=False)

if not holder_data.empty:
    st.write(f"### Tenencias de {selected_holder}")
    display_cols = ["Date", "Ticker", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned",
                    "Individual Holdings Value", "Change as % of Market Cap"]
    styled_df = holder_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format(
        {'Change as % of Market Cap': '{:.4f}%'}
    )
    st.dataframe(styled_df)

    st.write("### Acciones Mantenidas por Empresa")
    plot_top_20(holder_data, "Ticker", "Shares Held", f"Acciones Mantenidas por Empresa de {selected_holder}", "skyblue")

    st.write("### Porcentaje de Acciones Propiedad por Empresa")
    plot_top_20(holder_data, "Ticker", "Percentage Owned",
                f"Porcentaje de Acciones Propiedad por Empresa de {selected_holder}", "lightgreen")

    st.write("### Cambio en Acciones por Empresa")
    plot_changes(holder_data, "Ticker", "Shares Change", f"Cambio en Acciones por Empresa de {selected_holder}")

    st.write("### Cambio en Acciones % por Empresa")
    plot_changes(holder_data, "Ticker", "Shares Change % num",
                 f"Cambio en Acciones % por Empresa de {selected_holder}", is_percentage=True)

    st.write("### Rank de Tenencias Más Valiosas (por Valor Total)")
    holder_val_sorted = holder_data.sort_values(by="Individual Holdings Value", ascending=False).head(20)
    fig_val = px.bar(holder_val_sorted, x="Ticker", y="Individual Holdings Value",
                     title=f"Tenencias Más Valiosas de {selected_holder} (en millones USD)",
                     color_discrete_sequence=["blue"])
    fig_val.update_layout(xaxis_title="Ticker", yaxis_title="Valor Total (millones USD)")
    st.plotly_chart(fig_val, use_container_width=True)

    st.write("### Rank de Cambios en Posiciones Más Valiosos (por USD)")
    holder_change_sorted = holder_data.sort_values(by="Change in Value", ascending=False).head(20)
    colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in holder_change_sorted["Change in Value"]]
    fig_change = go.Figure(data=[
        go.Bar(x=holder_change_sorted["Ticker"], y=holder_change_sorted["Change in Value"], marker_color=colors)
    ])
    fig_change.update_layout(
        title=f"Cambios Más Valiosos en Posiciones de {selected_holder} (en millones USD)",
        xaxis_title="Ticker", yaxis_title="Cambio en Valor (millones USD)"
    )
    st.plotly_chart(fig_change, use_container_width=True)
else:
    st.write("No hay datos disponibles para el tenedor institucional seleccionado.")