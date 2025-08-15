import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from utils.data_processing import color_percentage, TICKER_MAPPING
import numpy as np

st.write(f"Debug: Page title set to 'Análisis Adicional'")

if 'merged_data' not in st.session_state or 'general_data' not in st.session_state:
    st.error("Datos no cargados. Por favor, revisa la página principal.")
    st.stop()

st.header("Análisis Adicional")

try:
    merged_data = st.session_state.merged_data
    merged_data_display = st.session_state.merged_data_display
    general_data = st.session_state.general_data

    # Apply global date filter
    if 'selected_date' in st.session_state and st.session_state.selected_date is not None:
        merged_data = merged_data[merged_data['Date'] == st.session_state.selected_date]
        merged_data_display = merged_data_display[merged_data_display['Date'] == st.session_state.selected_date]

    # Ensure 'Shares Change % num' is numeric
    merged_data['Shares Change % num'] = pd.to_numeric(merged_data['Shares Change % num'], errors='coerce')

    # Add sector data if not already present
    if 'Sector' not in merged_data.columns:
        tickers = merged_data['Ticker'].unique()
        sector_data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(TICKER_MAPPING.get(ticker, ticker))
                sector_data[ticker] = stock.info.get('sector', 'Unknown')
            except Exception as e:
                sector_data[ticker] = 'Unknown'
                st.warning(f"No se pudo obtener el sector para {ticker}: {e}")
        merged_data['Sector'] = merged_data['Ticker'].map(sector_data)
        merged_data_display['Sector'] = merged_data_display['Ticker'].map(sector_data)

    # Market Cap Influence
    st.subheader("Impacto de la Propiedad Institucional en la Capitalización de Mercado")
    ticker_cap_list = sorted(merged_data['Ticker'].unique())
    ticker = st.selectbox("Selecciona un Ticker para análisis de capitalización:", ticker_cap_list)
    if ticker:
        ticker_data = merged_data[merged_data['Ticker'] == ticker]
        try:
            general_ticker_data = general_data[general_data['Ticker'] == ticker]
            if general_ticker_data.empty:
                raise IndexError(f"No se encontraron datos para {ticker}.")
            total_shares = general_ticker_data['Total Shares Outstanding'].iloc[0] * 1e6
            market_cap = general_ticker_data['Market Cap'].iloc[0]
            price = general_ticker_data['Price per Share'].iloc[0]
            if pd.isna(market_cap) or market_cap == 0:
                st.warning(f"Capitalización de mercado no disponible para {ticker}. Intentando obtener desde yfinance.")
                stock = yf.Ticker(TICKER_MAPPING.get(ticker, ticker))
                market_cap = stock.info.get('marketCap', 0)
            if pd.isna(price) or price == 0:
                st.warning(f"Precio no disponible para {ticker}. Intentando obtener desde yfinance.")
                stock = yf.Ticker(TICKER_MAPPING.get(ticker, ticker))
                price = stock.info.get('regularMarketPrice', 0)
            st.write(f"Precio actual de {ticker}: ${price:.2f}")
            st.write(f"Capitalización de Mercado de {ticker}: ${market_cap / 1e6:.2f} millones")
        except IndexError as e:
            st.error(f"Error: {str(e)}")
            market_cap = 0
            price = 0
        else:
            st.write(f"Precio actual de {ticker}: ${price:.2f}")

        market_cap = price * total_shares
        if market_cap > 0:
            st.write(f"Capitalización de Mercado de {ticker}: ${market_cap / 1e6:.2f} millones")
        else:
            st.warning(f"No se pudo calcular la capitalización de mercado para {ticker} debido a precio no disponible.")

    # Ownership Concentration
    st.subheader("Concentración de Propiedad")
    ticker_conc_list = sorted(merged_data['Ticker'].unique())
    ticker_conc = st.selectbox("Selecciona un Ticker para análisis de concentración:", ticker_conc_list)
    top_n = st.slider("Selecciona el número de principales tenedores:", 1, 20, 5)
    if ticker_conc:
        ticker_data = merged_data[merged_data['Ticker'] == ticker_conc]
        try:
            total_shares = general_data[general_data['Ticker'] == ticker_conc]['Total Shares Outstanding'].iloc[0] * 1e6
        except IndexError:
            st.error(f"No se encontraron datos de acciones en circulación para {ticker_conc}.")
            total_shares = 0

        top_holders = ticker_data.sort_values('Shares Held', ascending=False).head(top_n)
        top_holders['Ownership Percentage'] = (top_holders['Shares Held'] / total_shares) * 100 if total_shares > 0 else 0

        other_institutional_shares = ticker_data['Shares Held'].sum() - top_holders['Shares Held'].sum()
        other_institutional_percentage = (other_institutional_shares / total_shares) * 100 if total_shares > 0 else 0

        other_holders_shares = total_shares - ticker_data['Shares Held'].sum() if total_shares > 0 else 0
        other_holders_percentage = (other_holders_shares / total_shares) * 100 if total_shares > 0 else 0

        pie_data = top_holders[['Owner Name', 'Ownership Percentage']].rename(columns={'Ownership Percentage': 'Percentage'})
        pie_data = pd.concat([
            pie_data,
            pd.DataFrame({'Owner Name': ['Otros institucionales'], 'Percentage': [other_institutional_percentage]}),
            pd.DataFrame({'Owner Name': ['Otros tenedores'], 'Percentage': [other_holders_percentage]})
        ], ignore_index=True)

        fig = px.pie(pie_data, values='Percentage', names='Owner Name', title=f'Concentración de Propiedad para {ticker_conc}')
        st.plotly_chart(fig, use_container_width=True)

    # Sector Analysis
    st.subheader("Análisis por Sector")
    sectors = sorted(merged_data['Sector'].unique())
    selected_sector = st.selectbox("Selecciona un Sector:", sectors)
    if selected_sector:
        sector_data = merged_data[merged_data['Sector'] == selected_sector]
        sector_data_display = merged_data_display[merged_data_display['Sector'] == selected_sector]

        st.write(f"### Propiedad Institucional Total en {selected_sector}")
        total_shares_held = sector_data['Shares Held'].sum()
        total_market_cap = (sector_data['Total Shares Outstanding'] * sector_data['Price per Share'].fillna(0)).sum() / 1e6
        institutional_percentage = (total_shares_held / (sector_data['Total Shares Outstanding'] * 1e6).sum()) * 100 if sector_data['Total Shares Outstanding'].sum() > 0 else 0
        st.write(f"Acciones Totales Mantenidas por Instituciones: {total_shares_held:,.0f}")
        st.write(f"Porcentaje de Propiedad Institucional: {institutional_percentage:.2f}%")
        st.write(f"Valor Total de Tenencias: ${sector_data['Individual Holdings Value'].sum():.2f} millones")

        st.write(f"### Principales Tickers en {selected_sector} por Propiedad Institucional")
        sector_tickers = sector_data.groupby('Ticker').agg({
            'Shares Held': 'sum',
            'Total Shares Outstanding': 'first',
            'Individual Holdings Value': 'sum'
        }).reset_index()
        sector_tickers['Ownership Percentage'] = (sector_tickers['Shares Held'] / (sector_tickers['Total Shares Outstanding'] * 1e6)) * 100
        top_tickers = sector_tickers.sort_values('Ownership Percentage', ascending=False).head(10)
        fig_tickers = px.bar(top_tickers, x='Ticker', y='Ownership Percentage',
                             title=f"Top 10 Tickers en {selected_sector} por % de Propiedad Institucional",
                             labels={'Ownership Percentage': '% de Propiedad'})
        fig_tickers.update_layout(yaxis_ticksuffix="%")
        st.plotly_chart(fig_tickers, use_container_width=True)

        st.write(f"### Principales Tenedores Institucionales en {selected_sector}")
        top_holders = sector_data.groupby('Owner Name').agg({
            'Shares Held': 'sum',
            'Individual Holdings Value': 'sum'
        }).reset_index()
        top_holders = top_holders.sort_values('Individual Holdings Value', ascending=False).head(10)
        fig_holders = px.bar(top_holders, x='Owner Name', y='Individual Holdings Value',
                             title=f"Top 10 Tenedores en {selected_sector} por Valor de Tenencias",
                             labels={'Individual Holdings Value': 'Valor (Millones USD)'})
        st.plotly_chart(fig_holders, use_container_width=True)

        with st.expander("Ver datos detallados"):
            display_cols = ['Date', 'Ticker', 'Owner Name', 'Shares Held', 'Shares Change', 'Shares Change %',
                            'Individual Holdings Value', 'Change as % of Market Cap']
            styled_df = sector_data_display[display_cols].style.applymap(color_percentage, subset=["Shares Change %"]).format(
                {'Change as % of Market Cap': '{:.4f}%'}
            )
            st.dataframe(styled_df)

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
                try:
                    total_shares = ticker_subset['Total Shares Outstanding'].iloc[0] * 1e6
                    price = ticker_subset['Price per Share'].iloc[0]
                    if pd.isna(price) or price == 0:
                        st.warning(f"Precio no disponible para {ticker}. Usando 0 para cálculos de 'Otros institucionales'.")
                        price = 0
                except IndexError:
                    st.error(f"No se encontraron datos de acciones en circulación para {ticker}.")
                    total_shares = 0
                    price = 0
                others_row = pd.DataFrame({
                    'Ticker': [ticker],
                    'Owner Name': ['Otros institucionales'],
                    'Shares Held': [others],
                    'Percentage Owned': [others / total_shares * 100 if total_shares > 0 else 0],
                    'Individual Holdings Value': [others * price / 1e6 if total_shares > 0 else 0]
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
            st.plotly_chart(fig, use_container_width=True)

    # Interactive Data Exploration
    st.subheader("Exploración Interactiva de Datos")
    min_date = merged_data['Date'].min().date() if not merged_data['Date'].empty else None
    max_date = merged_data['Date'].max().date() if not merged_data['Date'].empty else None
    if min_date and max_date:
        date_range = st.slider("Selecciona un rango de fechas:",
                               min_value=min_date, max_value=max_date,
                               value=(min_date, max_date))
        date_range_pandas = pd.to_datetime(date_range)
        filtered_data = merged_data[
            (merged_data['Date'] >= date_range_pandas[0]) & (merged_data['Date'] <= date_range_pandas[1])
        ]
        filtered_data_display = merged_data_display[
            (merged_data_display['Date'] >= date_range_pandas[0]) & (merged_data_display['Date'] <= date_range_pandas[1])
        ]
        filtered_data_display = filtered_data_display.sort_values(by='Shares Change % num', ascending=False)

        num_rows = st.slider("Número de filas a mostrar:", 1, min(1000, len(filtered_data_display)), 100)
        display_df = filtered_data_display.head(num_rows)
        display_cols = ['Date', 'Ticker', 'Owner Name', 'Shares Held', 'Shares Change', 'Shares Change %',
                        'Individual Holdings Value', 'Change as % of Market Cap']
        styled_df = display_df[display_cols].style.applymap(color_percentage, subset=["Shares Change %"]).format(
            {'Change as % of Market Cap': '{:.4f}%'}
        )
        st.dataframe(styled_df)
    else:
        st.warning("No hay datos de fechas disponibles para el filtro interactivo.")

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
        holder_sentiment = merged_data[merged_data['Owner Name'] == holder].sort_values('Date')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=holder_sentiment['Date'], y=holder_sentiment['Shares Change'],
                                 mode='lines+markers',
                                 marker=dict(color=['green' if x > 0 else 'red' for x in holder_sentiment['Shares Change']])))
        fig.update_layout(title=f'Sentimiento de {holder} a través de Cambios en Tenencias',
                          xaxis_title='Fecha', yaxis_title='Cambio en Acciones')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Indicador de Sentimiento a través de Cambios % en Tenencias")
        holder_sentiment_noinf = holder_sentiment[~np.isinf(holder_sentiment['Shares Change % num'])]
        fig_percent = go.Figure()
        fig_percent.add_trace(
            go.Scatter(x=holder_sentiment_noinf['Date'], y=holder_sentiment_noinf['Shares Change % num'],
                       mode='lines+markers',
                       marker=dict(color=['green' if x > 0 else 'red' for x in holder_sentiment_noinf['Shares Change % num']])))
        fig_percent.update_layout(title=f'Sentimiento de {holder} a través de Cambios % en Tenencias',
                                  xaxis_title='Fecha', yaxis_title='Cambio en Acciones %')
        st.plotly_chart(fig_percent, use_container_width=True)

except Exception as e:
    st.error(f"Error en la página de Análisis Adicional: {str(e)}")