import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import os
from datetime import datetime

@st.cache_data
def load_data():
    institutional_holders = pd.read_parquet("institutional_holders.parquet", engine="pyarrow")
    general_data = pd.read_parquet("general_data.parquet", engine="pyarrow")
    return institutional_holders, general_data


MARKET_CAP_CACHE = "market_caps_cache.parquet"

def load_market_caps_cache():
    """Carga cache de market caps si existe y es del día de hoy."""
    if os.path.exists(MARKET_CAP_CACHE):
        try:
            df = pd.read_parquet(MARKET_CAP_CACHE)
            cached_date = df.attrs.get("date_cached", "")
            today_str = datetime.today().strftime("%Y-%m-%d")
            if cached_date == today_str:
                # Convertir DataFrame a diccionario
                return dict(zip(df['Ticker'], df['Market Cap']))
        except Exception:
            pass
    return None

def save_market_caps_cache(market_caps):
    """Guarda market caps en disco con fecha de hoy."""
    df = pd.DataFrame(list(market_caps.items()), columns=['Ticker', 'Market Cap'])
    df.attrs["date_cached"] = datetime.today().strftime("%Y-%m-%d")
    df.to_parquet(MARKET_CAP_CACHE)

@st.cache_data(ttl=86400)  # máximo 1 día en memoria
def get_market_caps(tickers_list):
    """Obtiene market caps de Yahoo Finance usando cache diario en disco."""
    # Primero intentar cargar cache en disco
    cached_caps = load_market_caps_cache()
    if cached_caps:
        # Filtrar solo los tickers solicitados
        return {t: cached_caps[t] for t in tickers_list if t in cached_caps}

    # Si no hay cache válido, consultar Yahoo Finance
    market_caps = {}
    for ticker in tickers_list:
        try:
            stock = yf.Ticker(ticker)
            cap = stock.info.get('marketCap', None)
            if cap:
                market_caps[ticker] = cap
        except Exception:
            pass

    # Guardar cache en disco
    save_market_caps_cache(market_caps)
    return market_caps
@st.cache_data
def preprocess_data(institutional_holders, general_data, live_market_caps=None):
    """
    Preprocesa los datos combinando holders e información general.
    Calcula Price per Share, valores individuales, cambios y asegura Sector/Industry.
    """

    # 🔹 Calcular Price per Share aproximado
    general_data = general_data.copy()
    general_data["Price per Share"] = (general_data["Total Holdings Value"] * 1e6) / (
        general_data["Total Shares Outstanding"] * 1e6 * general_data["Institutional Ownership %"]
    )

    # 🔹 Merge de market caps en vivo si se proporcionan
    if live_market_caps:
        market_cap_df = pd.DataFrame(list(live_market_caps.items()), columns=['Ticker', 'Market Cap'])
        general_data = pd.merge(general_data, market_cap_df, on='Ticker', how='left')

    # 🔹 Asegurar columna Market Cap
    general_data['Market Cap'] = general_data.get(
        'Market Cap',
        general_data['Price per Share'] * general_data['Total Shares Outstanding'] * 1e6
    )
    general_data['Market Cap'].fillna(
        general_data['Price per Share'] * general_data['Total Shares Outstanding'] * 1e6,
        inplace=True
    )

    # 🔹 Merge final con holders
    merged_data = pd.merge(institutional_holders, general_data, on="Ticker", how="left")
    print(merged_data.head())
    print(merged_data.columns)

    # 🔹 Asegurarse de que existan las columnas Sector e Industry
    for col in ["Sector", "Industry"]:
        if col not in merged_data.columns:
            merged_data[col] = "Sin Datos"
        else:
            merged_data[col] = merged_data[col].fillna("Sin Datos")

    # 🔹 Cálculos adicionales
    merged_data["Percentage Owned"] = (merged_data["Shares Held"] / (merged_data["Total Shares Outstanding"] * 1e6)) * 100
    merged_data["Individual Holdings Value"] = merged_data["Shares Held"] * merged_data["Price per Share"] / 1e6
    merged_data['Date'] = pd.to_datetime(merged_data['Date'])
    merged_data["Change in Value"] = merged_data["Shares Change"] * merged_data["Price per Share"] / 1e6
    merged_data['Change as % of Market Cap'] = np.where(
        merged_data['Market Cap'] > 0,
        (merged_data['Change in Value'] * 1e6) / merged_data['Market Cap'] * 100,
        0
    )

    # 🔹 Porcentaje de cambio de shares
    merged_data["Previous Shares"] = merged_data["Shares Held"] - merged_data["Shares Change"]
    merged_data["Shares Change %"] = np.where(
        merged_data["Previous Shares"] != 0,
        (merged_data["Shares Change"] / merged_data["Previous Shares"]) * 100,
        np.inf
    )
    merged_data["Shares Change % num"] = merged_data["Shares Change %"]

    # 🔹 Preparar versión para display
    merged_data_display = merged_data.copy()
    merged_data_display["Shares Change %"] = merged_data_display["Shares Change %"].apply(
        lambda x: 'New Position' if np.isinf(x) else f"{x:.2f}%" if not np.isnan(x) else 'N/A'
    )

    return merged_data, merged_data_display






def color_percentage(val):
    if isinstance(val, str):
        if val == 'New Position':
            return 'color: green'
        elif val == 'N/A':
            return 'color: black'
        else:
            try:
                num_val = float(val.rstrip('%'))
                color = 'green' if num_val > 0 else 'red' if num_val < 0 else 'black'
                return f'color: {color}'
            except:
                return 'color: black'
    else:
        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {color}'
@st.cache_data
def aggregate_by_sector_industry(merged_data, level="Sector"):
    """Agrega estadísticas por Sector o Industria."""
    group_stats = (
        merged_data.groupby(level)
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
    return group_stats
