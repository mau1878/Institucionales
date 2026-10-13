import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import numpy as np                    # ← NECESARIO PARA np.isinf
from utils.data_processing import color_percentage
from utils.period import setup_page, show_chart, get_period_data, get_period

# Set custom page title for sidebar
st.set_page_config(page_title="Análisis Adicional", layout="wide")

st.header("Análisis Adicional")

# Datos del período activo (selector global en la barra lateral)
merged_data, merged_data_display = setup_page("snapshot")
general_data = st.session_state.merged_data  # sin filtrar: datos generales de la empresa y historial completo

# Market Cap Influence
st.subheader("Impacto de la Propiedad Institucional en la Capitalización de Mercado")
ticker_cap_list = sorted(merged_data['Ticker'].unique())
ticker = st.selectbox("Selecciona un Ticker para análisis de capitalización:", ticker_cap_list)
if ticker:
    ticker_data = merged_data[merged_data['Ticker'] == ticker]
    total_shares = general_data[general_data['Ticker'] == ticker]['Total Shares Outstanding'].iloc[0] * 1e6

    try:
        stock = yf.Ticker(ticker)
        price = stock.info['regularMarketPrice']
        market_cap = price * total_shares
        st.write(f"Precio actual de {ticker}: ${price:.2f}")
        st.write(f"Capitalización de Mercado de {ticker}: ${market_cap / 1e6:.2f} millones")
    except Exception as e:
        st.warning(f"No se pudo obtener el precio actual para {ticker} desde yfinance. Error: {e}")
        st.info(f"Usando precio aproximado de los datos cargados: ${general_data[general_data['Ticker'] == ticker]['Price per Share'].iloc[0]:.2f}")
        price = general_data[general_data['Ticker'] == ticker]['Price per Share'].iloc[0]
        market_cap = price * total_shares
        st.write(f"Capitalización de Mercado Aproximada de {ticker}: ${market_cap / 1e6:.2f} millones")

# Ownership Concentration
st.subheader("Concentración de Propiedad")
ticker_conc_list = sorted(merged_data['Ticker'].unique())
ticker_conc = st.selectbox("Selecciona un Ticker para análisis de concentración:", ticker_conc_list)
top_n = st.slider("Selecciona el número de principales tenedores:", 1, 20, 5)
if ticker_conc:
    ticker_data = merged_data[merged_data['Ticker'] == ticker_conc]
    total_shares = general_data[general_data['Ticker'] == ticker_conc]['Total Shares Outstanding'].iloc[0] * 1e6

    top_holders = ticker_data.sort_values('Shares Held', ascending=False).head(top_n)
    top_holders['Ownership Percentage'] = (top_holders['Shares Held'] / total_shares) * 100

    other_institutional_shares = ticker_data['Shares Held'].sum() - top_holders['Shares Held'].sum()
    other_institutional_percentage = (other_institutional_shares / total_shares) * 100

    other_holders_shares = total_shares - ticker_data['Shares Held'].sum()
    other_holders_percentage = (other_holders_shares / total_shares) * 100

    pie_data = top_holders[['Owner Name', 'Ownership Percentage']].rename(columns={'Ownership Percentage': 'Percentage'})
    pie_data = pd.concat([
        pie_data,
        pd.DataFrame({'Owner Name': ['Otros institucionales'], 'Percentage': [other_institutional_percentage]}),
        pd.DataFrame({'Owner Name': ['Otros tenedores'], 'Percentage': [other_holders_percentage]})
    ], ignore_index=True)

    fig = px.pie(pie_data, values='Percentage', names='Owner Name', title=f'Concentración de Propiedad para {ticker_conc}')
    show_chart(fig, use_container_width=True)

# Comparative Analysis Across Tickers
st.subheader("Comparación Entre Tickers")
tickers_comp_list = sorted(merged_data['Ticker'].unique())
tickers = st.multiselect("Selecciona los Tickers para comparar (Análisis Adicional):", tickers_comp_list)
if tickers:
    comparison_data = merged_data[merged_data['Ticker'].isin(tickers)]
    max_holders = st.slider("Selecciona el número máximo de tenedores a mostrar por ticker:", 1, 20, 5)
    simplified_data = pd.DataFrame()

    for ticker in tickers:
        ticker_subset = comparison_data[comparison_data['Ticker'] == ticker]
        top_holders = ticker_subset.sort_values('Shares Held', ascending=False).head(max_holders)
        others = ticker_subset.iloc[max_holders:]['Shares Held'].sum()
        if others > 0:
            others_row = pd.DataFrame({
                'Ticker': [ticker],
                'Owner Name': ['Otros institucionales'],
                'Shares Held': [others],
                'Percentage Owned': [others / (ticker_subset['Total Shares Outstanding'].iloc[0] * 1e6) * 100],
                'Individual Holdings Value': [others * ticker_subset['Price per Share'].iloc[0] / 1e6]
            })
            top_holders = pd.concat([top_holders, others_row], ignore_index=True)
        simplified_data = pd.concat([simplified_data, top_holders], ignore_index=True)

    category_order = [name for name in simplified_data['Owner Name'].unique() if name != 'Otros institucionales'] + ['Otros institucionales']

    st.write("### Comparación de Métricas por Ticker")
    for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
        fig = px.bar(simplified_data, x="Ticker", y=metric, color="Owner Name", barmode="stack",
                     category_orders={"Owner Name": category_order})
        fig.update_layout(title=f"Comparación de {metric} entre Tickers",
                          xaxis_title="Ticker", yaxis_title=metric, legend_title="Tenedores")
        show_chart(fig, use_container_width=True)

# Sector Analysis
st.subheader("Análisis por Sector")
st.write("Nota: Este análisis requiere información sobre sectores, que no está presente en los datos actuales.")

# Interactive Data Exploration
st.subheader("Exploración Interactiva de Datos")
st.caption("Un registro por tenedor, ticker y fecha de reporte dentro del período activo "
           "(se cambia desde la barra lateral).")
_, events_display = get_period_data("events")
filtered_data_display = events_display.sort_values(by='Shares Change % num', ascending=False)

if filtered_data_display.empty:
    st.info("No hay registros en el período seleccionado.")
else:
    num_rows = st.slider("Número de filas a mostrar:", 1, min(1000, len(filtered_data_display)),
                         min(100, len(filtered_data_display)))
    display_df = filtered_data_display.head(num_rows)
    display_cols = ['Date', 'Ticker', 'Owner Name', 'Shares Held', 'Shares Change', 'Shares Change %',
                    'Individual Holdings Value', 'Change as % of Market Cap']
    styled_df = display_df[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format(
        {'Change as % of Market Cap': '{:.4f}%'}
    )
    st.dataframe(styled_df)

# Portfolio Analysis for Holders
st.subheader("Análisis de Cartera para Tenedores")
holder_port_list = sorted(merged_data['Owner Name'].unique())
holder = st.selectbox("Selecciona un Tenedor para análisis de diversificación:", holder_port_list)
if holder:
    holder_portfolio = merged_data[merged_data['Owner Name'] == holder]
    st.write(f"### Diversificación de {holder}")
    st.write(f"Número de Tickers Únicos: {holder_portfolio['Ticker'].nunique()}")
    total_holdings_value = holder_portfolio['Individual Holdings Value'].sum()
    formatted_value = f"${total_holdings_value / 1e3:.2f} mil millones" if total_holdings_value >= 1e3 else f"${total_holdings_value:.2f} millones"
    st.write(f"Valor Total de Tenencias: {formatted_value}")

# Sentiment Indicator
st.subheader("Indicador de Sentimiento a través de Tenencias")
holder_sent_list = sorted(merged_data['Owner Name'].unique())
holder = st.selectbox("Selecciona un Tenedor para análisis de sentimiento:", holder_sent_list)
if holder:
    # Serie temporal: se muestra TODO el historial y se resalta el período activo
    holder_sentiment = general_data[general_data['Owner Name'] == holder].sort_values('Date')
    _p_start, _p_end = get_period()
    st.caption("Historial completo de fechas de reporte; la franja sombreada marca el período activo.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=holder_sentiment['Date'], y=holder_sentiment['Shares Change'],
                             mode='lines+markers',
                             marker=dict(color=['green' if x > 0 else 'red' for x in holder_sentiment['Shares Change']])))
    fig.add_vrect(x0=pd.Timestamp(_p_start), x1=pd.Timestamp(_p_end), fillcolor="royalblue", opacity=0.12, line_width=0)
    fig.update_layout(title=f'Sentimiento de {holder} a través de Cambios en Tenencias',
                      xaxis_title='Fecha', yaxis_title='Cambio en Acciones')
    show_chart(fig, use_container_width=True)

    st.subheader("Indicador de Sentimiento a través de Cambios % en Tenencias")
    holder_sentiment_noinf = holder_sentiment[~np.isinf(holder_sentiment['Shares Change % num'])]
    fig_percent = go.Figure()
    fig_percent.add_trace(
        go.Scatter(x=holder_sentiment_noinf['Date'], y=holder_sentiment_noinf['Shares Change % num'],
                   mode='lines+markers',
                   marker=dict(color=['green' if x > 0 else 'red' for x in holder_sentiment_noinf['Shares Change % num']])))
    fig_percent.add_vrect(x0=pd.Timestamp(_p_start), x1=pd.Timestamp(_p_end), fillcolor="royalblue", opacity=0.12, line_width=0)
    fig_percent.update_layout(title=f'Sentimiento de {holder} a través de Cambios % en Tenencias',
                              xaxis_title='Fecha', yaxis_title='Cambio en Acciones %')
    show_chart(fig_percent, use_container_width=True)
