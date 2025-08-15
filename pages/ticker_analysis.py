import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.plotting import plot_top_20, plot_changes
from utils.data_processing import color_percentage, TICKER_MAPPING
import numpy as np
import yfinance as yf

st.write(f"Debug: Page title set to 'Análisis por Ticker'")

if 'merged_data' not in st.session_state or 'general_data' not in st.session_state:
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

try:
    merged_data = st.session_state.merged_data
    merged_data_display = st.session_state.merged_data_display
    general_data = st.session_state.general_data

    # Apply global date filter safely
    if 'selected_date' in st.session_state and st.session_state.selected_date is not None:
        merged_data = merged_data[merged_data['Date'] == st.session_state.selected_date]
        merged_data_display = merged_data_display[merged_data_display['Date'] == st.session_state.selected_date]

    # Ensure 'Shares Change % num' is numeric
    merged_data['Shares Change % num'] = pd.to_numeric(merged_data['Shares Change % num'], errors='coerce')

    tickers_list = sorted(merged_data["Ticker"].unique())
    selected_ticker = st.selectbox("Selecciona un Ticker:", tickers_list)

    ticker_data = merged_data[merged_data["Ticker"] == selected_ticker]
    ticker_data_display = merged_data_display[merged_data_display["Ticker"] == selected_ticker]

    # Ensure 'Shares Change % num' is numeric in ticker_data
    ticker_data['Shares Change % num'] = pd.to_numeric(ticker_data['Shares Change % num'], errors='coerce')
    ticker_data_display['Shares Change % num'] = pd.to_numeric(ticker_data_display['Shares Change % num'], errors='coerce')

    ticker_data_display = ticker_data_display.sort_values(by='Shares Change % num', ascending=False)
    general_ticker_data = general_data[general_data["Ticker"] == selected_ticker]

    if not ticker_data.empty and not general_ticker_data.empty:
        st.write(f"### Datos Generales para {selected_ticker}")
        try:
            total_shares = general_ticker_data['Total Shares Outstanding'].iloc[0]
            st.write(f"Acciones Totales Emitidas: {total_shares:,.0f} millones")
        except IndexError:
            st.warning(f"No se encontraron datos de acciones en circulación para {selected_ticker}.")
            total_shares = 0
        try:
            institutional_ownership = general_ticker_data['Institutional Ownership %'].iloc[0] * 100
            st.write(f"Propiedad Institucional: {institutional_ownership:.2f}%")
        except IndexError:
            st.warning(f"No se encontraron datos de propiedad institucional para {selected_ticker}.")
            institutional_ownership = 0
        try:
            total_holdings_value = general_ticker_data['Total Holdings Value'].iloc[0]
            st.write(f"Valor Total de Tenencias: ${total_holdings_value:,.0f} millones")
        except IndexError:
            st.warning(f"No se encontraron datos de valor total de tenencias para {selected_ticker}.")
            total_holdings_value = 0
        try:
            market_cap = general_ticker_data['Market Cap'].iloc[0]
            if pd.isna(market_cap) or market_cap == 0:
                st.warning(f"Capitalización de mercado no disponible para {selected_ticker}. Intentando obtener desde yfinance.")
                stock = yf.Ticker(TICKER_MAPPING.get(selected_ticker, selected_ticker))
                market_cap = stock.info.get('marketCap', 0)
            st.write(f"Capitalización de Mercado (Market Cap): ${market_cap / 1e9:,.2f} mil millones")
        except IndexError:
            st.warning(f"No se encontraron datos de capitalización de mercado para {selected_ticker}.")
            market_cap = 0

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
        st.warning(f"No hay datos disponibles para el ticker {selected_ticker}.")
except Exception as e:
    st.error(f"Error en la página de Análisis por Ticker: {str(e)}")