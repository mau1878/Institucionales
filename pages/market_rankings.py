import streamlit as st
from utils.period import setup_page, show_chart
import pandas as pd
import plotly.express as px
import numpy as np  # Add this import

# Set custom page title for sidebar
st.set_page_config(page_title="Rankings de Mercado", layout="wide")

st.header("Rankings de Mercado")
st.write("""
Esta sección clasifica los tickers según la actividad de compra y venta de los tenedores institucionales.
- **Términos Absolutos:** Número de tenedores que realizaron una acción (abrir, aumentar, disminuir, cerrar posición).
- **Términos Relativos (Valor):** Valor total en USD del movimiento.
- **Términos Relativos (% Market Cap):** Valor del movimiento como porcentaje de la capitalización de mercado total.
""")

# Datos del período activo (selector global): un registro por tenedor/ticker/fecha de reporte
merged_data, merged_data_display = setup_page("events")

# New Positions
st.subheader("🏆 Top Tickers por Apertura de Nuevas Posiciones")
new_positions_df = merged_data[np.isinf(merged_data['Shares Change % num'])]

st.markdown("#### Por Número de Tenedores (Absoluto)")
new_abs = new_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Nuevas Posiciones')
top_new_abs = new_abs.sort_values('Número de Nuevas Posiciones', ascending=False).head(20)
fig_new_abs = px.bar(top_new_abs, x='Ticker', y='Número de Nuevas Posiciones', title="Top 20 Tickers por Nuevas Posiciones Abiertas")
show_chart(fig_new_abs, use_container_width=True)
with st.expander("Ver datos de nuevas posiciones (absoluto)"):
    st.dataframe(top_new_abs)

st.markdown("#### Por Valor de las Nuevas Posiciones (Relativo - USD)")
new_val = new_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total (Millones USD)')
top_new_val = new_val.sort_values('Valor Total (Millones USD)', ascending=False).head(20)
fig_new_val = px.bar(top_new_val, x='Ticker', y='Valor Total (Millones USD)', title="Top 20 Tickers por Valor de Nuevas Posiciones")
show_chart(fig_new_val, use_container_width=True)
with st.expander("Ver datos de nuevas posiciones (valor)"):
    st.dataframe(top_new_val)

st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
new_mc = new_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
top_new_mc = new_mc.sort_values('% del Market Cap', ascending=False).head(20)
fig_new_mc = px.bar(top_new_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Nuevas Posiciones en Market Cap")
fig_new_mc.update_layout(yaxis_ticksuffix="%")
show_chart(fig_new_mc, use_container_width=True)
with st.expander("Ver datos de nuevas posiciones (% market cap)"):
    st.dataframe(top_new_mc.style.format({'% del Market Cap': '{:.4f}%'}))

# Increased Positions
st.subheader("📈 Top Tickers por Aumento de Posiciones Existentes")
increased_positions_df = merged_data[(merged_data['Shares Change'] > 0) & (merged_data['Previous Shares'] > 0)]

st.markdown("#### Por Número de Tenedores (Absoluto)")
inc_abs = increased_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Posiciones Aumentadas')
top_inc_abs = inc_abs.sort_values('Número de Posiciones Aumentadas', ascending=False).head(20)
fig_inc_abs = px.bar(top_inc_abs, x='Ticker', y='Número de Posiciones Aumentadas', title="Top 20 Tickers por Aumento de Posiciones")
show_chart(fig_inc_abs, use_container_width=True)
with st.expander("Ver datos de posiciones aumentadas (absoluto)"):
    st.dataframe(top_inc_abs)

st.markdown("#### Por Valor del Aumento (Relativo - USD)")
inc_val = increased_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total del Aumento (Millones USD)')
top_inc_val = inc_val.sort_values('Valor Total del Aumento (Millones USD)', ascending=False).head(20)
fig_inc_val = px.bar(top_inc_val, x='Ticker', y='Valor Total del Aumento (Millones USD)', title="Top 20 Tickers por Valor de Aumento de Posiciones")
show_chart(fig_inc_val, use_container_width=True)
with st.expander("Ver datos de posiciones aumentadas (valor)"):
    st.dataframe(top_inc_val)

st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
inc_mc = increased_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
top_inc_mc = inc_mc.sort_values('% del Market Cap', ascending=False).head(20)
fig_inc_mc = px.bar(top_inc_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Aumento de Posiciones en Market Cap")
fig_inc_mc.update_layout(yaxis_ticksuffix="%")
show_chart(fig_inc_mc, use_container_width=True)
with st.expander("Ver datos de posiciones aumentadas (% market cap)"):
    st.dataframe(top_inc_mc.style.format({'% del Market Cap': '{:.4f}%'}))

# Decreased Positions
st.subheader("📉 Top Tickers por Reducción de Posiciones Existentes")
decreased_positions_df = merged_data[(merged_data['Shares Change'] < 0) & (merged_data['Shares Held'] > 0)]

st.markdown("#### Por Número de Tenedores (Absoluto)")
dec_abs = decreased_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Posiciones Reducidas')
top_dec_abs = dec_abs.sort_values('Número de Posiciones Reducidas', ascending=False).head(20)
fig_dec_abs = px.bar(top_dec_abs, x='Ticker', y='Número de Posiciones Reducidas', title="Top 20 Tickers por Reducción de Posiciones", color_discrete_sequence=['#EF553B'])
show_chart(fig_dec_abs, use_container_width=True)
with st.expander("Ver datos de posiciones reducidas (absoluto)"):
    st.dataframe(top_dec_abs)

st.markdown("#### Por Valor de la Reducción (Relativo - USD)")
dec_val = decreased_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de la Reducción (Millones USD)')
top_dec_val = dec_val.sort_values('Valor Total de la Reducción (Millones USD)', ascending=True).head(20)
fig_dec_val = px.bar(top_dec_val, x='Ticker', y='Valor Total de la Reducción (Millones USD)', title="Top 20 Tickers por Valor de Reducción de Posiciones", color_discrete_sequence=['#EF553B'])
show_chart(fig_dec_val, use_container_width=True)
with st.expander("Ver datos de posiciones reducidas (valor)"):
    st.dataframe(top_dec_val)

st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
dec_mc = decreased_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
top_dec_mc = dec_mc.sort_values('% del Market Cap', ascending=True).head(20)
fig_dec_mc = px.bar(top_dec_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Reducción de Posiciones en Market Cap", color_discrete_sequence=['#EF553B'])
fig_dec_mc.update_layout(yaxis_ticksuffix="%")
show_chart(fig_dec_mc, use_container_width=True)
with st.expander("Ver datos de posiciones reducidas (% market cap)"):
    st.dataframe(top_dec_mc.style.format({'% del Market Cap': '{:.4f}%'}))

# Closed Positions
st.subheader("❌ Top Tickers por Cierre Total de Posiciones")
closed_positions_df = merged_data[(merged_data['Shares Held'] == 0) & (merged_data['Previous Shares'] > 0)]

st.markdown("#### Por Número de Tenedores (Absoluto)")
closed_abs = closed_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Posiciones Cerradas')
top_closed_abs = closed_abs.sort_values('Número de Posiciones Cerradas', ascending=False).head(20)
fig_closed_abs = px.bar(top_closed_abs, x='Ticker', y='Número de Posiciones Cerradas', title="Top 20 Tickers por Cierre de Posiciones", color_discrete_sequence=['#d62728'])
show_chart(fig_closed_abs, use_container_width=True)
with st.expander("Ver datos de posiciones cerradas (absoluto)"):
    st.dataframe(top_closed_abs)

st.markdown("#### Por Valor de la Posición Cerrada (Relativo - USD)")
closed_val = closed_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de Posiciones Cerradas (Millones USD)')
top_closed_val = closed_val.sort_values('Valor Total de Posiciones Cerradas (Millones USD)', ascending=True).head(20)
fig_closed_val = px.bar(top_closed_val, x='Ticker', y='Valor Total de Posiciones Cerradas (Millones USD)', title="Top 20 Tickers por Valor de Posiciones Cerradas", color_discrete_sequence=['#d62728'])
show_chart(fig_closed_val, use_container_width=True)
with st.expander("Ver datos de posiciones cerradas (valor)"):
    st.dataframe(top_closed_val)

st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
closed_mc = closed_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
top_closed_mc = closed_mc.sort_values('% del Market Cap', ascending=True).head(20)
fig_closed_mc = px.bar(top_closed_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Cierre de Posiciones en Market Cap", color_discrete_sequence=['#d62728'])
fig_closed_mc.update_layout(yaxis_ticksuffix="%")
show_chart(fig_closed_mc, use_container_width=True)
with st.expander("Ver datos de posiciones cerradas (% market cap)"):
    st.dataframe(top_closed_mc.style.format({'% del Market Cap': '{:.4f}%'}))

# Cumulative Positive Flow
st.subheader("🟩 Flujo Acumulado Positivo (Presión de Compra)")
positive_flow_df = merged_data[merged_data['Shares Change'] > 0]

st.markdown("#### Por Valor Total (USD)")
pos_flow_val = positive_flow_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de Compra (Millones USD)')
top_pos_flow_val = pos_flow_val.sort_values('Valor Total de Compra (Millones USD)', ascending=False).head(20)
fig_pos_flow_val = px.bar(top_pos_flow_val, x='Ticker', y='Valor Total de Compra (Millones USD)', title="Top 20 Tickers por Presión de Compra (Valor)")
show_chart(fig_pos_flow_val, use_container_width=True)
with st.expander("Ver datos de presión de compra (valor)"):
    st.dataframe(top_pos_flow_val)

st.markdown("#### Por % de Capitalización de Mercado")
pos_flow_mc = positive_flow_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
top_pos_flow_mc = pos_flow_mc.sort_values('% del Market Cap', ascending=False).head(20)
fig_pos_flow_mc = px.bar(top_pos_flow_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Presión de Compra (% Market Cap)")
fig_pos_flow_mc.update_layout(yaxis_ticksuffix="%")
show_chart(fig_pos_flow_mc, use_container_width=True)
with st.expander("Ver datos de presión de compra (% market cap)"):
    st.dataframe(top_pos_flow_mc.style.format({'% del Market Cap': '{:.4f}%'}))

# Cumulative Negative Flow
st.subheader("🟥 Flujo Acumulado Negativo (Presión de Venta)")
negative_flow_df = merged_data[merged_data['Shares Change'] < 0]

st.markdown("#### Por Valor Total (USD)")
neg_flow_val = negative_flow_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de Venta (Millones USD)')
top_neg_flow_val = neg_flow_val.sort_values('Valor Total de Venta (Millones USD)', ascending=True).head(20)
fig_neg_flow_val = px.bar(top_neg_flow_val, x='Ticker', y='Valor Total de Venta (Millones USD)', title="Top 20 Tickers por Presión de Venta (Valor)", color_discrete_sequence=['#EF553B'])
show_chart(fig_neg_flow_val, use_container_width=True)
with st.expander("Ver datos de presión de venta (valor)"):
    st.dataframe(top_neg_flow_val)

st.markdown("#### Por % de Capitalización de Mercado")
neg_flow_mc = negative_flow_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
top_neg_flow_mc = neg_flow_mc.sort_values('% del Market Cap', ascending=True).head(20)
fig_neg_flow_mc = px.bar(top_neg_flow_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Presión de Venta (% Market Cap)", color_discrete_sequence=['#EF553B'])
fig_neg_flow_mc.update_layout(yaxis_ticksuffix="%")
show_chart(fig_neg_flow_mc, use_container_width=True)
with st.expander("Ver datos de presión de venta (% market cap)"):
    st.dataframe(top_neg_flow_mc.style.format({'% del Market Cap': '{:.4f}%'}))

# Net Institutional Flow
st.subheader("📊 Flujo Neto Institucional (Compra Neta vs. Venta Neta)")
net_flow_df = merged_data.groupby('Ticker').agg(
    Net_Change_Value=('Change in Value', 'sum'),
    Net_Change_MC=('Change as % of Market Cap', 'sum')
).reset_index()

st.markdown("#### Top Tickers por Flujo Neto Positivo (Mayor Entrada de Capital)")
top_net_positive = net_flow_df.sort_values('Net_Change_Value', ascending=False).head(20)
fig_net_pos_val = px.bar(top_net_positive, x='Ticker', y='Net_Change_Value', title="Top 20 Tickers por Flujo Neto Positivo (Valor)", color_discrete_sequence=['#00CC96'])
fig_net_pos_val.update_layout(yaxis_title="Flujo Neto (Millones USD)")
show_chart(fig_net_pos_val, use_container_width=True)
with st.expander("Ver datos de flujo neto positivo (valor)"):
    st.dataframe(top_net_positive)

top_net_positive_mc = net_flow_df.sort_values('Net_Change_MC', ascending=False).head(20)
fig_net_pos_mc = px.bar(top_net_positive_mc, x='Ticker', y='Net_Change_MC', title="Top 20 Tickers por Flujo Neto Positivo (% Market Cap)", color_discrete_sequence=['#00CC96'])
fig_net_pos_mc.update_layout(yaxis_title="Flujo Neto (% Market Cap)", yaxis_ticksuffix="%")
show_chart(fig_net_pos_mc, use_container_width=True)
with st.expander("Ver datos de flujo neto positivo (% market cap)"):
    st.dataframe(top_net_positive_mc.style.format({'Net_Change_MC': '{:.4f}%'}))

st.markdown("#### Top Tickers por Flujo Neto Negativo (Mayor Salida de Capital)")
top_net_negative = net_flow_df.sort_values('Net_Change_Value', ascending=True).head(20)
fig_net_neg_val = px.bar(top_net_negative, x='Ticker', y='Net_Change_Value', title="Top 20 Tickers por Flujo Neto Negativo (Valor)", color_discrete_sequence=['#d62728'])
fig_net_neg_val.update_layout(yaxis_title="Flujo Neto (Millones USD)")
show_chart(fig_net_neg_val, use_container_width=True)
with st.expander("Ver datos de flujo neto negativo (valor)"):
    st.dataframe(top_net_negative)

top_net_negative_mc = net_flow_df.sort_values('Net_Change_MC', ascending=True).head(20)
fig_net_neg_mc = px.bar(top_net_negative_mc, x='Ticker', y='Net_Change_MC', title="Top 20 Tickers por Flujo Neto Negativo (% Market Cap)", color_discrete_sequence=['#d62728'])
fig_net_neg_mc.update_layout(yaxis_title="Flujo Neto (% Market Cap)", yaxis_ticksuffix="%")
show_chart(fig_net_neg_mc, use_container_width=True)
with st.expander("Ver datos de flujo neto negativo (% market cap)"):
    st.dataframe(top_net_negative_mc.style.format({'Net_Change_MC': '{:.4f}%'}))