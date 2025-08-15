import streamlit as st
import pandas as pd
import plotly.express as px
from utils.plotting import plot_venn_like_comparison, plot_matplotlib_venn
from utils.data_processing import color_percentage

# Set custom page title for sidebar
st.set_page_config(page_title="Comparación", layout="wide")

if 'merged_data' not in st.session_state:
    st.error("Datos no cargados. Por favor, revisa la página principal.")
    st.stop()

st.header("Comparación")
st.write("""
**Cómo usar esta sección:**
- **Elige el tipo de comparación:** Puedes comparar tickers o tenedores institucionales.
- **Selecciona 2 o 3 items:** Elige varios tickers o tenedores para comparar sus datos.
- **Gráfico de Coincidencias:** Aparecerá un diagrama mostrando las coincidencias entre los items seleccionados.
""")

merged_data = st.session_state.merged_data
merged_data_display = st.session_state.merged_data_display
general_data = st.session_state.merged_data

# Apply global date filter
# Apply global date filter safely
if 'selected_date' in st.session_state and st.session_state.selected_date is not None:
    merged_data = merged_data[merged_data['Date'] == st.session_state.selected_date]
    merged_data_display = merged_data_display[merged_data_display['Date'] == st.session_state.selected_date]

# Ensure 'Shares Change % num' is numeric
merged_data['Shares Change % num'] = pd.to_numeric(merged_data['Shares Change % num'], errors='coerce')

comparison_type = st.radio("Elige el tipo de comparación:", ["Tickers", "Tenedores Institucionales"])

if comparison_type == "Tickers":
    tickers = st.multiselect("Selecciona los Tickers para comparar:", sorted(general_data["Ticker"].unique()))
    if tickers:
        if len(tickers) in [2, 3]:
            st.subheader("Gráfico de Coincidencias de Tenedores")
            chart_type = st.radio(
                "Elige el tipo de gráfico:",
                ('Burbujas (Interactivo)', 'Venn (Proporcional y Preciso)'),
                key='ticker_chart_choice',
                help="El gráfico de Burbujas es interactivo. El gráfico de Venn es una representación matemática precisa de las superposiciones."
            )
            if chart_type == 'Burbujas (Interactivo)':
                st.write("Este diagrama de burbujas muestra los tenedores únicos para cada ticker y las coincidencias.")
                plot_venn_like_comparison(tickers, 'Ticker', merged_data)
            else:
                st.write("Este diagrama de Venn muestra las proporciones exactas de tenedores únicos y compartidos.")
                plot_matplotlib_venn(tickers, 'Ticker', merged_data)

        comparison_data = merged_data[merged_data['Ticker'].isin(tickers)]
        comparison_data_display = merged_data_display[merged_data_display['Ticker'].isin(tickers)]
        comparison_data_display = comparison_data_display.sort_values(by='Shares Change % num', ascending=False)
        st.write("### Tabla de Comparación de Tickers")
        display_cols = ["Date", "Ticker", "Owner Name", "Shares Held", "Shares Change", "Shares Change %",
                        "Percentage Owned", "Individual Holdings Value", "Change as % of Market Cap"]
        styled_df = comparison_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format(
            {'Change as % of Market Cap': '{:.4f}%'}
        )
        st.dataframe(styled_df)

        for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
            fig = px.bar(comparison_data, x="Ticker", y=metric, color="Owner Name", barmode="group")
            fig.update_layout(title=f"Comparación de {metric} por Ticker", xaxis_title="Ticker", yaxis_title=metric)
            st.plotly_chart(fig, use_container_width=True)

elif comparison_type == "Tenedores Institucionales":
    holders = st.multiselect("Selecciona los Tenedores Institucionales para comparar:",
                            sorted(merged_data["Owner Name"].unique()))
    if holders:
        if len(holders) in [2, 3]:
            st.subheader("Gráfico de Coincidencias de Tickers")
            chart_type = st.radio(
                "Elige el tipo de gráfico:",
                ('Burbujas (Interactivo)', 'Venn (Proporcional y Preciso)'),
                key='holder_chart_choice',
                help="El gráfico de Burbujas es interactivo. El gráfico de Venn es una representación matemática precisa de las superposiciones."
            )
            if chart_type == 'Burbujas (Interactivo)':
                st.write("Este diagrama de burbujas muestra los tickers únicos en la cartera de cada tenedor y las coincidencias.")
                plot_venn_like_comparison(holders, 'Owner Name', merged_data)
            else:
                st.write("Este diagrama de Venn muestra las proporciones exactas de tickers únicos y compartidos.")
                plot_matplotlib_venn(holders, 'Owner Name', merged_data)

        comparison_data = merged_data[merged_data['Owner Name'].isin(holders)]
        comparison_data_display = merged_data_display[merged_data_display['Owner Name'].isin(holders)]
        comparison_data_display = comparison_data_display.sort_values(by='Shares Change % num', ascending=False)
        st.write("### Tabla de Comparación de Tenedores Institucionales")
        display_cols = ["Date", "Owner Name", "Ticker", "Shares Held", "Shares Change", "Shares Change %",
                        "Percentage Owned", "Individual Holdings Value", "Change as % of Market Cap"]
        styled_df = comparison_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format(
            {'Change as % of Market Cap': '{:.4f}%'}
        )
        st.dataframe(styled_df)

        for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
            fig = px.bar(comparison_data, x="Owner Name", y=metric, color="Ticker", barmode="group")
            fig.update_layout(title=f"Comparación de {metric} por Tenedor Institucional",
                              xaxis_title="Tenedor Institucional", yaxis_title=metric)
            st.plotly_chart(fig, use_container_width=True)