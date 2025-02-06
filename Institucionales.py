import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

#########################################
# Helper Functions
#########################################

def abbreviate_number_py(num):
    """
    Convert a number to a string using abbreviations for thousand (K), million (M), and billion (B).
    """
    abs_num = abs(num)
    if abs_num >= 1e9:
        return f"{num/1e9:.1f}B"
    elif abs_num >= 1e6:
        return f"{num/1e6:.1f}M"
    elif abs_num >= 1e3:
        return f"{num/1e3:.1f}K"
    else:
        return f"{num:.0f}"

def convert_shares_to_millions(share_str):
    """
    Converts a share string to numeric value in millions.
    """
    if isinstance(share_str, (int, float)):
        return share_str
    share_str = share_str.strip()
    if 'B' in share_str:
        return float(share_str.replace('B', '')) * 1000
    elif 'M' in share_str:
        return float(share_str.replace('M', ''))
    elif 'k' in share_str:
        return float(share_str.replace('k', '')) / 1000
    else:
        return float(share_str)

def load_and_prepare_data():
    df = pd.read_csv('institutional_holders_all_20250205_215655.csv')
    df['Shares'] = df['Shares'].apply(convert_shares_to_millions)
    df['% Out'] = df['% Out'].str.replace('%', '').astype(float)
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    return df

def create_heatmap(df, selected_holders):
    pivot_data = (
        df[df['Holder'].isin(selected_holders)]
        .groupby(['Holder', 'Ticker'])['% Out']
        .mean()
        .reset_index()
    )
    pivot_data = pivot_data.pivot(index='Holder', columns='Ticker', values='% Out').fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        text=np.round(pivot_data.values, 2),
        texttemplate='%{text}%',
        textfont={"size": 10},
        hoverongaps=False
    ))
    fig.update_layout(
        title='Mapa de Calor de Participaciones por Institución',
        height=400 * max(len(selected_holders) // 4, 1),
        yaxis_title='Institución',
        xaxis_title='Ticker',
        xaxis_tickangle=-45
    )
    return fig

def calculate_concentration_metrics(holder_data):
    total_value = holder_data['Value'].sum()
    sorted_positions = holder_data.sort_values('Value', ascending=False)
    metrics = {
        'Top 5 Concentración': f"{(sorted_positions['Value'].head(5).sum() / total_value * 100):.2f}%",
        'Top 10 Concentración': f"{(sorted_positions['Value'].head(10).sum() / total_value * 100):.2f}%",
        'HHI': f"{((holder_data['Value'] / total_value * 100) ** 2).sum():.2f}",
        'Posiciones >5%': len(holder_data[holder_data['% Out'] > 5]),
        'Posiciones >10%': len(holder_data[holder_data['% Out'] > 10])
    }
    return metrics

#########################################
# Main App
#########################################

def main():
    st.set_page_config(page_title="Análisis de Tenencias Institucionales", page_icon="📊", layout="wide")
    st.markdown("""
    <div style='text-align: right; color: gray; padding-bottom: 20px;'>
        Desarrollado por <a href='https://twitter.com/MTaurus_ok' target='_blank'>MTaurus</a> (@MTaurus_ok)
    </div>
    """, unsafe_allow_html=True)
    st.title("Análisis de Tenencias Institucionales")

    df = load_and_prepare_data()
    holders = sorted(df['Holder'].unique())
    tickers = sorted(df['Ticker'].unique())

    tab1, tab2, tab3, tab4 = st.tabs([
        "Vista Individual",
        "Análisis Comparativo",
        "Ranking Institucional",
        "Análisis por Ticker"
    ])

    #### Tab 1: Vista Individual ####
    with tab1:
        selected_holder = st.sidebar.selectbox("Seleccionar Institución", holders)
        holder_data = df[df['Holder'] == selected_holder].copy()
        holder_data_sorted = holder_data.sort_values('% Out', ascending=False)

        st.header(f"Análisis de Tenencias para {selected_holder}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Número de Posiciones", len(holder_data))
        with col2:
            st.metric("% Promedio de Acciones en Circulación", f"{holder_data['% Out'].mean():.2f}%")
        with col3:
            st.metric("Valor Total", f"${holder_data['Value'].sum():,.0f}")

        st.subheader("Métricas de Concentración")
        metrics = calculate_concentration_metrics(holder_data)
        for metric_name, value in metrics.items():
            st.write(f"**{metric_name}:** {value}")

        # Simple bar chart
        fig = px.bar(
            holder_data_sorted,
            x='Ticker',
            y='% Out',
            title=f'Participaciones de {selected_holder}',
            labels={'% Out': '% de Acciones en Circulación', 'Ticker': 'Empresa', 'Value': 'Valor ($)'},
            color='Value',
            color_continuous_scale='Viridis',
            height=500
        )
        fig.add_annotation(
            text="MTaurus: X: @MTaurus_ok",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="rgba(150,150,150,0.2)"),
            textangle=-30
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=True,
            coloraxis_colorbar_title="Valor ($)"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Tabla Interactiva de Tenencias (AgGrid)")
        display_df = pd.DataFrame({
            'Ticker': holder_data_sorted['Ticker'],
            'Acciones (M)': holder_data_sorted['Shares'],
            '% de Acciones en Circulación': holder_data_sorted['% Out'],
            'Valor ($)': holder_data_sorted['Value'],
            'Fecha Reportada': holder_data_sorted['Date Reported']
        })

        # Build AgGrid options with custom renderers
        gb = GridOptionsBuilder.from_dataframe(display_df)
        renderer_value = JsCode("""
        function(params) {
            let value = params.value;
            if (Math.abs(value) >= 1e9) {
                return (value / 1e9).toFixed(1) + 'B';
            } else if (Math.abs(value) >= 1e6) {
                return (value / 1e6).toFixed(1) + 'M';
            } else if (Math.abs(value) >= 1e3) {
                return (value / 1e3).toFixed(1) + 'K';
            } else {
                return value;
            }
        }
        """)
        renderer_shares = JsCode("""
        function(params) {
            let value = params.value;
            return Number(value).toFixed(2) + 'M';
        }
        """)
        gb.configure_column("Valor ($)", cellRenderer=renderer_value, sortable=True)
        gb.configure_column("Acciones (M)", cellRenderer=renderer_shares, sortable=True)
        gridOptions = gb.build()

        AgGrid(
            display_df,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=400,
            fit_columns_on_grid_load=True
        )

        st.markdown("___")
        # Option to download the filtered holder data
        csv = holder_data_sorted.to_csv(index=False)
        st.download_button(
            label="Descargar Datos en CSV",
            data=csv,
            file_name=f"{selected_holder}_tenencias.csv",
            mime="text/csv",
            help="Descarga los datos en formato CSV"
        )

    #### Tab 2: Análisis Comparativo ####
    with tab2:
        selected_holders = st.multiselect(
            "Seleccionar Instituciones para Comparar (máx. 10)",
            holders,
            default=[holders[0]],
            max_selections=10)
        if selected_holders:
            st.subheader("Mapa de Calor de Participaciones")
            heatmap = create_heatmap(df, selected_holders)
            st.plotly_chart(heatmap, use_container_width=True)
            st.subheader("Top 10 Holdings por Institución")
            for holder in selected_holders:
                holder_data = df[df['Holder'] == holder].sort_values('Value', ascending=False).head(10)
                fig = px.bar(
                    holder_data,
                    x='Ticker',
                    y='Value',
                    title=f'Top 10 Holdings - {holder}',
                    labels={'Value': 'Valor ($)', 'Ticker': 'Empresa'},
                    color='% Out'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Por favor, seleccione al menos una institución para el análisis comparativo.")

    #### Tab 3: Ranking Institucional ####
    with tab3:
        st.header("Ranking de Instituciones")
        inst_metrics = df.groupby('Holder').agg({
            'Ticker': 'count',
            'Value': 'sum'
        }).reset_index()
        inst_metrics.columns = ['Institución', 'Número de Empresas', 'Valor Total']
        inst_metrics['Tamaño Promedio de Posición'] = inst_metrics['Valor Total'] / inst_metrics['Número de Empresas']

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Por Número de Empresas")
            companies_ranking = inst_metrics.sort_values('Número de Empresas', ascending=False).head(20)
            fig = px.bar(
                companies_ranking,
                x='Institución',
                y='Número de Empresas',
                title='Top 20 Instituciones por Número de Empresas',
                height=500
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Por Valor Total")
            value_ranking = inst_metrics.sort_values('Valor Total', ascending=False).head(20)
            fig = px.bar(
                value_ranking,
                x='Institución',
                y='Valor Total',
                title='Top 20 Instituciones por Valor Total',
                height=500
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Tabla Completa de Instituciones")
        # Build AgGrid table for the ranking data
        gb_inst = GridOptionsBuilder.from_dataframe(inst_metrics)
        renderer_val_total = JsCode("""
        function(params) {
            let value = params.value;
            if (Math.abs(value) >= 1e9) {
                return (value / 1e9).toFixed(1) + 'B';
            } else if (Math.abs(value) >= 1e6) {
                return (value / 1e6).toFixed(1) + 'M';
            } else if (Math.abs(value) >= 1e3) {
                return (value / 1e3).toFixed(1) + 'K';
            } else {
                return value;
            }
        }
        """)
        renderer_avg = JsCode("""
        function(params) {
            let value = params.value;
            if (Math.abs(value) >= 1e9) {
                return (value / 1e9).toFixed(1) + 'B';
            } else if (Math.abs(value) >= 1e6) {
                return (value / 1e6).toFixed(1) + 'M';
            } else if (Math.abs(value) >= 1e3) {
                return (value / 1e3).toFixed(1) + 'K';
            } else {
                return value;
            }
        }
        """)
        gb_inst.configure_column("Valor Total", cellRenderer=renderer_val_total, sortable=True)
        gb_inst.configure_column("Tamaño Promedio de Posición", cellRenderer=renderer_avg, sortable=True)
        gridOptions_inst = gb_inst.build()

        AgGrid(
            inst_metrics,
            gridOptions=gridOptions_inst,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=500,
            fit_columns_on_grid_load=True
        )

        download_df = inst_metrics.copy()
        download_df['Valor Total'] = download_df['Valor Total'].apply(lambda x: f"${x:,.0f}")
        download_df['Tamaño Promedio de Posición'] = download_df['Tamaño Promedio de Posición'].apply(lambda x: f"${x:,.0f}")
        csv_inst = download_df.to_csv(index=False)
        st.download_button(
            label="Descargar Ranking Completo en CSV",
            data=csv_inst,
            file_name="ranking_institucional.csv",
            mime="text/csv",
            help="Descarga el ranking completo en CSV"
        )

    #### Tab 4: Análisis por Ticker ####
    with tab4:
        st.header("Análisis por Ticker")
        selected_ticker = st.selectbox("Seleccionar Ticker", tickers)
        ticker_data = df[df['Ticker'] == selected_ticker].sort_values('Value', ascending=False)
        st.subheader(f"Top Inversores Institucionales en {selected_ticker}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Número de Inversores", len(ticker_data))
        with col2:
            st.metric("Valor Total de Participaciones", f"${ticker_data['Value'].sum():,.0f}")

        fig = px.bar(
            ticker_data.head(15),
            x='Holder',
            y='% Out',
            title=f'Top 15 Inversores en {selected_ticker}',
            labels={'% Out': '% de Acciones en Circulación', 'Holder': 'Institución'},
            color='Value',
            height=500
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Datos Detallados")
        ticker_display_df = pd.DataFrame({
            'Institución': ticker_data['Holder'],
            'Acciones (M)': ticker_data['Shares'],
            '% de Acciones en Circulación': ticker_data['% Out'],
            'Valor ($)': ticker_data['Value'],
            'Fecha Reportada': ticker_data['Date Reported']
        })
        gb_ticker = GridOptionsBuilder.from_dataframe(ticker_display_df)
        gb_ticker.configure_column("Valor ($)", cellRenderer=renderer_value, sortable=True)
        gb_ticker.configure_column("Acciones (M)", cellRenderer=renderer_shares, sortable=True)
        gridOptions_ticker = gb_ticker.build()

        AgGrid(
            ticker_display_df,
            gridOptions=gridOptions_ticker,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=400,
            fit_columns_on_grid_load=True
        )

if __name__ == "__main__":
    main()
