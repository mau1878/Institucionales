import pandas as pd
import yfinance as yf
import streamlit as st
import numpy as np

# Global ticker mapping for yfinance compatibility
TICKER_MAPPING = {
    'BRK.B': 'BRK-B',
    'BRK.A': 'BRK-A',
}

def color_percentage(val):
    try:
        if isinstance(val, str) and '%' in val:
            num = float(val.replace('%', ''))
            color = 'green' if num > 0 else 'red' if num < 0 else 'black'
        elif val == "N/A (Nueva posición)":
            color = 'black'
        else:
            color = 'black'
        return f'color: {color}'
    except (ValueError, TypeError):
        return 'color: black'

@st.cache_data
def load_data():
    try:
        institutional_holders = pd.read_parquet("institutional_holders.parquet", engine="pyarrow")
        general_data = pd.read_parquet("general_data.parquet", engine="pyarrow")
        return institutional_holders, general_data
    except Exception as e:
        raise FileNotFoundError(f"Error al cargar los archivos parquet: {str(e)}")

@st.cache_data
def get_market_caps(_tickers):
    mapped_tickers = [TICKER_MAPPING.get(ticker, ticker) for ticker in _tickers]
    market_caps = {}
    prices = {}
    null_price_tickers = []
    for original_ticker, yf_ticker in zip(_tickers, mapped_tickers):
        try:
            stock = yf.Ticker(yf_ticker)
            market_caps[original_ticker] = stock.info.get('marketCap', None)
            prices[original_ticker] = stock.info.get('regularMarketPrice', None)
            if prices[original_ticker] is None:
                null_price_tickers.append(original_ticker)
        except Exception as e:
            market_caps[original_ticker] = None
            prices[original_ticker] = None
            null_price_tickers.append(original_ticker)
            st.warning(f"No se pudo obtener datos para {original_ticker} (usando {yf_ticker}): {e}")
    if null_price_tickers:
        st.warning(f"Tickers con precios nulos: {', '.join(null_price_tickers)}")
    return market_caps, prices

@st.cache_data
def preprocess_data(institutional_holders, general_data, live_market_caps):
    try:
        # Ensure numeric columns
        for col in ['Shares Held', 'Total Shares Outstanding', 'Previous Shares']:
            if col in institutional_holders.columns:
                institutional_holders[col] = pd.to_numeric(institutional_holders[col], errors='coerce')
            if col in general_data.columns:
                general_data[col] = pd.to_numeric(general_data[col], errors='coerce')

        market_caps, prices = live_market_caps
        general_data['Price per Share'] = general_data['Ticker'].map(prices)
        general_data['Market Cap'] = general_data['Ticker'].map(market_caps)
        if general_data['Price per Share'].isna().any():
            null_price_tickers = general_data[general_data['Price per Share'].isna()]['Ticker'].tolist()
            st.warning(f"Algunos tickers tienen precios nulos: {', '.join(null_price_tickers)}. Los cálculos pueden ser inexactos. Rellenando con 0.")
            general_data['Price per Share'] = general_data['Price per Share'].fillna(0)
        if general_data['Market Cap'].isna().any():
            null_market_cap_tickers = general_data[general_data['Market Cap'].isna()]['Ticker'].tolist()
            st.warning(f"Algunos tickers tienen capitalización de mercado nula: {', '.join(null_market_cap_tickers)}. Rellenando con 0.")
            general_data['Market Cap'] = general_data['Market Cap'].fillna(0)
        merged_data = institutional_holders.merge(
            general_data[['Ticker', 'Total Shares Outstanding', 'Price per Share', 'Market Cap', 'Total Holdings Value', 'Institutional Ownership %']],
            on='Ticker', how='left'
        )
        if merged_data.empty:
            raise ValueError("Los datos combinados están vacíos.")
        merged_data['Percentage Owned'] = (merged_data['Shares Held'] / (merged_data['Total Shares Outstanding'] * 1e6)) * 100
        merged_data['Individual Holdings Value'] = (merged_data['Shares Held'] * merged_data['Price per Share'].fillna(0)) / 1e6
        merged_data['Previous Shares'] = merged_data.groupby(['Ticker', 'Owner Name'])['Shares Held'].shift(1)
        merged_data['Shares Change'] = merged_data['Shares Held'] - merged_data['Previous Shares'].fillna(0)
        merged_data['Shares Change %'] = merged_data['Shares Change'] / merged_data['Previous Shares'].replace(0, pd.NA) * 100
        merged_data['Shares Change %'] = merged_data['Shares Change %'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) and not np.isinf(x) else "N/A (Nueva posición)"
        )
        merged_data['Shares Change % num'] = pd.to_numeric(
            merged_data['Shares Change'] / merged_data['Previous Shares'].replace(0, pd.NA) * 100,
            errors='coerce'
        )
        merged_data['Change in Value'] = (merged_data['Shares Change'] * merged_data['Price per Share'].fillna(0)) / 1e6
        merged_data['Change as % of Market Cap'] = merged_data['Change in Value'] / merged_data['Market Cap'].replace(0, pd.NA) * 100
        tickers = general_data['Ticker'].unique()
        sector_data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(TICKER_MAPPING.get(ticker, ticker))
                sector_data[ticker] = stock.info.get('sector', 'Unknown')
            except Exception as e:
                sector_data[ticker] = 'Unknown'
                st.warning(f"No se pudo obtener el sector para {ticker}: {e}")
        merged_data['Sector'] = merged_data['Ticker'].map(sector_data)
        general_data['Sector'] = general_data['Ticker'].map(sector_data)
        merged_data_display = merged_data.copy()
        merged_data_display['Change in Value'] = merged_data_display['Change in Value'].apply(lambda x: f"${x:.2f}M")
        merged_data_display['Individual Holdings Value'] = merged_data_display['Individual Holdings Value'].apply(lambda x: f"${x:.2f}M")
        merged_data_display['Shares Held'] = merged_data_display['Shares Held'].apply(lambda x: f"{x:,.0f}")
        merged_data_display['Shares Change'] = merged_data_display['Shares Change'].apply(lambda x: f"{x:,.0f}")
        return merged_data, merged_data_display
    except Exception as e:
        raise ValueError(f"Error al procesar los datos: {str(e)}")