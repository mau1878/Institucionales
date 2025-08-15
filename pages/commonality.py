import streamlit as st
import pandas as pd
import plotly.express as px

if 'merged_data' not in st.session_state:
    st.error("Datos no cargados. Por favor, revisa la página principal.")
    st.stop()

st.header("Análisis de Coincidencias")
st.write("""
**Cómo usar esta sección:**
- **Umbral de Coincidencia:** Define un porcentaje para filtrar los resultados. Sólo se mostrarán los tenedores o tickers que superan este umbral de coincidencia.
**Explicación de los datos:**
- **Tenedores Institucionales con más Tickers en Común:** Identifica cuáles tenedores tienen inversiones en una gran parte de las empresas (tickers) disponibles.
- **Tickers con más Tenedores Institucionales en Común:** Muestra qué empresas tienen el mayor número de tenedores institucionales.
**Calculación de Coincidencias:**
- **Para Tenedores:** Porcentaje de todos los tickers únicos en los que cada tenedor está invertido.
- **Para Tickers:** Porcentaje de todos los tenedores únicos que invierten en cada ticker.
""")

merged_data = st.session_state.merged_data
merged_data_display = st.session_state.merged_data_display

# Apply global date filter
if st.session_state.selected_date:
    merged_data = merged_data[merged_data['Date'] == st.session_state.selected_date]
    merged_data_display = merged_data_display[merged_data_display['Date'] == st.session_state.selected_date]

threshold = st.slider("Selecciona el umbral de coincidencia en porcentaje:", 0, 100, 50)

def commonality(data, group_by, common_entity):
    counts = data.groupby(group_by)['Ticker'].nunique() if common_entity == 'Ticker' else data.groupby(group_by)['Owner Name'].nunique()
    total = len(data[common_entity].unique())
    return ((counts / total) * 100).reset_index(name='Percentage')

st.subheader("Tenedores Institucionales con más Tickers en Común")
holder_commonality = commonality(merged_data, 'Owner Name', 'Ticker')
filtered_holders = holder_commonality[holder_commonality['Percentage'] >= threshold].sort_values('Percentage', ascending=False)
if not filtered_holders.empty:
    st.dataframe(filtered_holders)
    fig = px.bar(filtered_holders, x='Owner Name', y='Percentage',
                 title=f"Tenedores Institucionales con más de {threshold}% de Tickers en Común",
                 labels={'Percentage': f'Porcentaje de Tickers Comunes'})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write(f"No hay tenedores institucionales con más de {threshold}% de tickers en común.")

st.subheader("Tickers con más Tenedores Institucionales en Común")
ticker_commonality = commonality(merged_data, 'Ticker', 'Owner Name')
filtered_tickers = ticker_commonality[ticker_commonality['Percentage'] >= threshold].sort_values('Percentage', ascending=False)
if not filtered_tickers.empty:
    st.dataframe(filtered_tickers)
    fig = px.bar(filtered_tickers, x='Ticker', y='Percentage',
                 title=f"Tickers con más de {threshold}% de Tenedores Institucionales en Común",
                 labels={'Percentage': f'Porcentaje de Tenedores Comunes'})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write(f"No hay tickers con más de {threshold}% de tenedores institucionales en común.")