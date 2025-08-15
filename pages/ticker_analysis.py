import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.plotting import plot_top_20, plot_changes
from utils.data_processing import color_percentage

# Set custom page title for sidebar
st.set_page_config(page_title="Análisis por Ticker", layout="wide")
st.write(f"Debug: Page title set to 'Análisis por Ticker'")  # Debug message

if 'merged_data' not in st.session_state:
    st.error("Datos no cargados. Por favor, revisa la página principal.")
    st.stop()

st.header("Análisis por Ticker")
st.write("""
**Cómo usar esta sección:**
- **Selecciona un Ticker:** Elige una empresa para ver quiénes son sus principales tenedores institucionales.
- **Datos mostrados:** Información general sobre la empresa y detalles de los tenedores institucionales.
**Explicación de los datos:**
- **Acciones Totales Emitidas:** Total de acciones en circulación de la empresa.
- **Propiedad Institucional:** Porcentaje del total de acciones que son propiedad de instituciones.
- **Valor Total de Tenencias:** Valor total de las acciones mantenidas por instituciones.
- **Tenedores Institucionales:** Lista de los principales tenedores con sus acciones mantenidas y cambios.
- **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
""")

merged_data = st.session_state.merged_data
merged_data_display = st.session_state.merged_data_display
general_data = st.session_state.merged_data  # Note: general_data is part of merged_data

# Apply global date filter
if st.session_state.selected_date:
    merged_data = merged_data[merged_data['Date'] == st.session_state.selected_date]
    merged_data_display = merged_data_display[merged_data_display['Date'] == st.session_state.selected_date]

tickers_list = sorted(general_data["Ticker"].unique())
selected_ticker = st.selectbox("Selecciona un Ticker:", tickers_list)

ticker_data = merged_data[merged_data["Ticker"] == selected_ticker]
ticker_data_display = merged_data_display[merged_data_display["Ticker"] == selected_ticker]
ticker_data_display = ticker_data_display.sort_values(by='Shares Change % num', ascending=False)
general_ticker_data = general_data[general_data["Ticker"] == selected_ticker]

if not ticker_data.empty:
    st.write(f"### Datos Generales para {selected_ticker}")
    st.write(f"Acciones Totales Emitidas: {general_ticker_data['Total Shares Outstanding'].values[0]:,.0f} millones")
    st.write(f"Propiedad Institucional: {general_ticker_data['Institutional Ownership %'].values[0] * 100:.2f}%")
    st.write(f"Valor Total de Tenencias: ${general_ticker_data['Total Holdings Value'].values[0]:,.0f} millones")
    st.write(f"Capitalización de Mercado (Market Cap): ${general_ticker_data['Market Cap'].values[0] / 1e9:,.2f} mil millones")

    st.write(f"### Tenedores Institucionales para {selected_ticker}")
    display_cols = ["Date", "Owner Name", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned",
                    "Individual Holdings Value", "Change as % of Market Cap"]
    styled_df = ticker_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format(
        {'Change as % of Market Cap': '{:.4f}%'}
    )
    st.dataframe(styled_df)

    st.write("### Acciones Mantenidas por Tenedores Institucionales")
    plot_top_20(ticker_data, "Owner Name", "Shares Held",
                f"Acciones Mantenidas por Tenedores Institucionales para {selected_ticker}", "orange")

    st.write("### Porcentaje de Acciones Propiedad por Tenedores Institucionales")
    plot_top_20(ticker_data, "Owner Name", "Percentage Owned",
                f"Porcentaje de Acciones Propiedad por Tenedores Institucionales para {selected_ticker}", "purple")

    st.write("### Cambio en Acciones por Tenedores Institucionales")
    plot_changes(ticker_data, "Owner Name", "Shares Change",
                 f"Cambio en Acciones por Tenedores Institucionales para {selected_ticker}")

    st.write("### Cambio en Acciones % por Tenedores Institucionales")
    plot_changes(ticker_data, "Owner Name", "Shares Change % num",
                 f"Cambio en Acciones % por Tenedores Institucionales para {selected_ticker}", is_percentage=True)

    st.write("### Rank de Tenencias Más Valiosas (por Valor Total)")
    ticker_val_sorted = ticker_data.sort_values(by="Individual Holdings Value", ascending=False).head(20)
    fig_val = px.bar(ticker_val_sorted, x="Owner Name", y="Individual Holdings Value",
                     title=f"Tenencias Más Valiosas en {selected_ticker} (en millones USD)",
                     color_discrete_sequence=["blue"])
    fig_val.update_layout(xaxis_title="Tenedor Institucional", yaxis_title="Valor Total (millones USD)")
    st.plotly_chart(fig_val, use_container_width=True)

    st.write("### Rank de Cambios en Posiciones Más Valiosos (por USD)")
    ticker_change_sorted = ticker_data.sort_values(by="Change in Value", ascending=False).head(20)
    colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in ticker_change_sorted["Change in Value"]]
    fig_change = go.Figure(data=[
        go.Bar(x=ticker_change_sorted["Owner Name"], y=ticker_change_sorted["Change in Value"], marker_color=colors)
    ])
    fig_change.update_layout(
        title=f"Cambios Más Valiosos en Posiciones para {selected_ticker} (en millones USD)",
        xaxis_title="Tenedor Institucional", yaxis_title="Cambio en Valor (millones USD)"
    )
    st.plotly_chart(fig_change, use_container_width=True)
else:
    st.write("No hay datos disponibles para el ticker seleccionado.")