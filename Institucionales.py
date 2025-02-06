import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def convert_shares_to_millions(share_str):
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
    return df


def create_heatmap(df, selected_holders):
    # Group by Holder and Ticker to handle duplicates by taking the mean
    pivot_data = df[df['Holder'].isin(selected_holders)].groupby(['Holder', 'Ticker'])['% Out'].mean().reset_index()

    # Create pivot table after aggregation
    pivot_data = pivot_data.pivot(
        index='Holder',
        columns='Ticker',
        values='% Out'
    ).fillna(0)

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
        height=400 * len(selected_holders) // 4,
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

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Vista Individual", "Análisis Comparativo"])

    with tab1:
        # Original single-institution view
        selected_holder = st.sidebar.selectbox(
            "Seleccionar Institución",
            holders
        )

        holder_data = df[df['Holder'] == selected_holder].copy()
        holder_data_sorted = holder_data.sort_values('% Out', ascending=False)

        st.header(f"Análisis de Tenencias para {selected_holder}")

        # Original metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Número de Posiciones", len(holder_data))
        with col2:
            st.metric("% Promedio de Acciones en Circulación", f"{holder_data['% Out'].mean():.2f}%")
        with col3:
            st.metric("Valor Total", f"${holder_data['Value'].sum():,.0f}")

        # Add concentration metrics
        st.subheader("Métricas de Concentración")
        metrics = calculate_concentration_metrics(holder_data)
        metric_cols = st.columns(len(metrics))
        for col, (metric_name, value) in zip(metric_cols, metrics.items()):
            col.metric(metric_name, value)

        # Original bar plot
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

        # Original detailed data table
        st.subheader("Datos Detallados de Tenencias")
        display_df = pd.DataFrame({
            'Ticker': holder_data_sorted['Ticker'],
            'Acciones (M)': holder_data_sorted['Shares'],
            '% de Acciones en Circulación': holder_data_sorted['% Out'],
            'Valor ($)': holder_data_sorted['Value'],
            'Fecha Reportada': holder_data_sorted['Date Reported']
        })

        st.dataframe(
            display_df,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Acciones (M)": st.column_config.NumberColumn("Acciones (M)", format="%.2f M"),
                "% de Acciones en Circulación": st.column_config.NumberColumn("% de Acciones en Circulación",
                                                                              format="%.2f%%"),
                "Valor ($)": st.column_config.NumberColumn("Valor ($)", format="$%d"),
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )

    with tab2:
        # Multi-institution analysis
        selected_holders = st.multiselect(
            "Seleccionar Instituciones para Comparar (máx. 10)",
            holders,
            default=[holders[0]],
            max_selections=10
        )

        if selected_holders:
            # Heatmap
            st.subheader("Mapa de Calor de Participaciones")
            heatmap = create_heatmap(df, selected_holders)
            st.plotly_chart(heatmap, use_container_width=True)

            # Top 10 holdings for each selected institution
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

    # Download button
    st.subheader("Descargar Datos")
    csv = holder_data_sorted.to_csv(index=False)
    st.download_button(
        label="Descargar Datos en CSV",
        data=csv,
        file_name=f"{selected_holder}_tenencias.csv",
        mime="text/csv",
        help="Haga clic para descargar los datos filtrados en formato CSV"
    )


if __name__ == "__main__":
    main()
