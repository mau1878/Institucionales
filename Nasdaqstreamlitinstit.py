import streamlit as st
import pandas as pd
import plotly.express as px

# Loading and preprocessing data (as before)
institutional_holders = pd.read_csv("institutional_holders.csv")
general_data = pd.read_csv("general_data.csv")

institutional_holders["Shares Held"] = institutional_holders["Shares Held"].str.replace(",", "").astype(float)
institutional_holders["Shares Change"] = institutional_holders["Shares Change"].str.replace(",", "").astype(float)
general_data["Total Shares Outstanding"] = general_data["Total Shares Outstanding"].str.replace(",", "").astype(float)
general_data["Total Holdings Value"] = general_data["Total Holdings Value"].str.replace("$", "").str.replace(",",
                                                                                                             "").astype(
    float)

merged_data = pd.merge(institutional_holders, general_data, on="Ticker")
merged_data["Percentage Owned"] = (merged_data["Shares Held"] / (merged_data["Total Shares Outstanding"] * 1e6)) * 100

# Streamlit app
st.title("Análisis de Tenencias Institucionales")

# Sidebar for user input
st.sidebar.header("Entrada del Usuario")
option = st.sidebar.radio("Elige una opción:",
                          ["Análisis de Tenedor Institucional", "Análisis por Ticker", "Comparación",
                           "Análisis de Coincidencias"])


def plot_top_20(df, x, y, title, color):
    df = df.sort_values(by=y, ascending=False)
    top_20 = df.head(20)
    others = df.iloc[20:][y].mean() if len(df) > 20 else None

    if others is not None:
        others_row = pd.DataFrame({'x': ['Otros - Promedio'], y: [others]})
        others_row.columns = [x, y]
        top_20 = pd.concat([top_20, others_row], ignore_index=True)

    fig = px.bar(top_20, x=x, y=y, title=title, color_discrete_sequence=[color])
    fig.update_layout(xaxis_title=x, yaxis_title=y)
    st.plotly_chart(fig)


if option == "Análisis de Tenedor Institucional":
    st.header("Análisis de Tenedor Institucional")
    st.write("""
    **Cómo usar esta sección:**
    - **Selecciona un Tenedor Institucional:** Elige un tenedor para ver sus inversiones en diferentes empresas (tickers).
    - **Datos mostrados:** Verás las acciones mantenidas, el cambio en las acciones y el porcentaje de propiedad en cada empresa.

    **Explicación de los datos:**
    - **Acciones Mantenidas:** Número de acciones que el tenedor posee en cada empresa.
    - **Cambio en Acciones:** Diferencia en el número de acciones desde la última actualización.
    - **Porcentaje de Propiedad:** Porcentaje de las acciones totales de la empresa que posee el tenedor.
    """)

    institutional_holders_list = institutional_holders["Owner Name"].unique()
    selected_holder = st.selectbox("Selecciona un Tenedor Institucional:", institutional_holders_list)

    holder_data = merged_data[merged_data["Owner Name"] == selected_holder]

    if not holder_data.empty:
        st.write(f"### Tenencias de {selected_holder}")
        st.dataframe(holder_data[["Ticker", "Shares Held", "Shares Change", "Percentage Owned"]])

        # Plot for shares held
        st.write("### Acciones Mantenidas por Empresa")
        plot_top_20(holder_data, "Ticker", "Shares Held", f"Acciones Mantenidas por Empresa de {selected_holder}",
                    "skyblue")

        # Plot for percentage owned
        st.write("### Porcentaje de Acciones Propiedad por Empresa")
        plot_top_20(holder_data, "Ticker", "Percentage Owned",
                    f"Porcentaje de Acciones Propiedad por Empresa de {selected_holder}", "lightgreen")
    else:
        st.write("No hay datos disponibles para el tenedor institucional seleccionado.")

elif option == "Análisis por Ticker":
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
    """)

    tickers_list = general_data["Ticker"].unique()
    selected_ticker = st.selectbox("Selecciona un Ticker:", tickers_list)

    ticker_data = merged_data[merged_data["Ticker"] == selected_ticker]
    general_ticker_data = general_data[general_data["Ticker"] == selected_ticker]

    if not ticker_data.empty:
        st.write(f"### Datos Generales para {selected_ticker}")
        st.write(
            f"Acciones Totales Emitidas: {general_ticker_data['Total Shares Outstanding'].values[0]:,.0f} millones")
        st.write(f"Propiedad Institucional: {general_ticker_data['Institutional Ownership %'].values[0]}")
        st.write(f"Valor Total de Tenencias: ${general_ticker_data['Total Holdings Value'].values[0]:,.0f} millones")

        st.write(f"### Tenedores Institucionales para {selected_ticker}")
        st.dataframe(ticker_data[["Owner Name", "Shares Held", "Shares Change", "Percentage Owned"]])

        # Plot for shares held by institutional holders
        st.write("### Acciones Mantenidas por Tenedores Institucionales")
        plot_top_20(ticker_data, "Owner Name", "Shares Held",
                    f"Acciones Mantenidas por Tenedores Institucionales para {selected_ticker}", "orange")

        # Plot for percentage owned by institutional holders
        st.write("### Porcentaje de Acciones Propiedad por Tenedores Institucionales")
        plot_top_20(ticker_data, "Owner Name", "Percentage Owned",
                    f"Porcentaje de Acciones Propiedad por Tenedores Institucionales para {selected_ticker}", "purple")
    else:
        st.write("No hay datos disponibles para el ticker seleccionado.")

elif option == "Comparación":
    st.header("Comparación")
    st.write("""
    **Cómo usar esta sección:**
    - **Elige el tipo de comparación:** Puedes comparar tickers o tenedores institucionales.
    - **Selecciona múltiples items:** Elige varios tickers o tenedores para comparar sus datos.

    **Explicación de los datos:**
    - **Comparación de Tickers:** Verás cómo se distribuyen las tenencias institucionales entre diferentes empresas.
    - **Comparación de Tenedores Institucionales:** Observa cómo un mismo tenedor invierte en diferentes empresas.
    """)

    comparison_type = st.radio("Elige el tipo de comparación:", ["Tickers", "Tenedores Institucionales"])

    if comparison_type == "Tickers":
        tickers = st.multiselect("Selecciona los Tickers para comparar:", general_data["Ticker"].unique())
        if tickers:
            comparison_data = merged_data[merged_data['Ticker'].isin(tickers)]
            st.write("### Comparación de Tickers")
            st.dataframe(comparison_data[["Ticker", "Owner Name", "Shares Held", "Shares Change", "Percentage Owned"]])

            # Plotting
            for metric in ["Shares Held", "Percentage Owned"]:
                fig = px.bar(comparison_data, x="Ticker", y=metric, color="Owner Name", barmode="group")
                fig.update_layout(title=f"Comparación de {metric} por Ticker", xaxis_title="Ticker", yaxis_title=metric)
                st.plotly_chart(fig)

    elif comparison_type == "Tenedores Institucionales":
        holders = st.multiselect("Selecciona los Tenedores Institucionales para comparar:",
                                 institutional_holders["Owner Name"].unique())
        if holders:
            comparison_data = merged_data[merged_data['Owner Name'].isin(holders)]
            st.write("### Comparación de Tenedores Institucionales")
            st.dataframe(comparison_data[["Owner Name", "Ticker", "Shares Held", "Shares Change", "Percentage Owned"]])

            # Plotting
            for metric in ["Shares Held", "Percentage Owned"]:
                fig = px.bar(comparison_data, x="Owner Name", y=metric, color="Ticker", barmode="group")
                fig.update_layout(title=f"Comparación de {metric} por Tenedor Institucional",
                                  xaxis_title="Tenedor Institucional", yaxis_title=metric)
                st.plotly_chart(fig)

elif option == "Análisis de Coincidencias":
    st.header("Análisis de Coincidencias")
    st.write("""
    **Cómo usar esta sección:**
    - **Umbral de Coincidencia:** Define un porcentaje para filtrar los resultados. Sólo se mostrarán los tenedores o tickers que superan este umbral de coincidencia.

    **Explicación de los datos:**
    - **Tenedores Institucionales con más Tickers en Común:** Identifica cuáles tenedores tienen inversiones en una gran parte de las empresas (tickers) disponibles. Esto puede indicar una estrategia de inversión diversificada o influencia significativa en el mercado.
    - **Tickers con más Tenedores Institucionales en Común:** Muestra qué empresas tienen el mayor número de tenedores institucionales, lo que podría señalar un fuerte interés o respaldo institucional hacia esas empresas.

    **Calculación de Coincidencias:**
    - **Para Tenedores:** Se calcula el porcentaje de todos los tickers únicos en los que cada tenedor está invertido. 
    - **Para Tickers:** Se calcula el porcentaje de todos los tenedores únicos que invierten en cada ticker. 
    - El porcentaje se obtiene dividiendo el número de tickers/tenedores únicos asociados por el total de tickers/tenedores únicos en el conjunto de datos, multiplicado por 100.
    """)

    # User-defined threshold
    threshold = st.slider("Selecciona el umbral de coincidencia en porcentaje:", 0, 100, 50)


    # Function to calculate commonality
    def commonality(data, group_by, common_entity):
        counts = data.groupby(group_by)['Ticker'].nunique() if common_entity == 'Ticker' else data.groupby(group_by)[
            'Owner Name'].nunique()
        total = len(data[common_entity].unique())
        return ((counts / total) * 100).reset_index(name='Percentage')


    # Institutional Holders with most common tickers
    st.subheader("Tenedores Institucionales con más Tickers en Común")
    holder_commonality = commonality(merged_data, 'Owner Name', 'Ticker')
    filtered_holders = holder_commonality[holder_commonality['Percentage'] >= threshold].sort_values('Percentage',
                                                                                                     ascending=False)
    if not filtered_holders.empty:
        st.dataframe(filtered_holders)
        fig = px.bar(filtered_holders, x='Owner Name', y='Percentage',
                     title=f"Tenedores Institucionales con más de {threshold}% de Tickers en Común",
                     labels={'Percentage': f'Porcentaje de Tickers Comunes'})
        st.plotly_chart(fig)
    else:
        st.write(f"No hay tenedores institucionales con más de {threshold}% de tickers en común.")

    # Tickers with most common institutional holders
    st.subheader("Tickers con más Tenedores Institucionales en Común")
    ticker_commonality = commonality(merged_data, 'Ticker', 'Owner Name')
    filtered_tickers = ticker_commonality[ticker_commonality['Percentage'] >= threshold].sort_values('Percentage',
                                                                                                     ascending=False)
    if not filtered_tickers.empty:
        st.dataframe(filtered_tickers)
        fig = px.bar(filtered_tickers, x='Ticker', y='Percentage',
                     title=f"Tickers con más de {threshold}% de Tenedores Institucionales en Común",
                     labels={'Percentage': f'Porcentaje de Tenedores Comunes'})
        st.plotly_chart(fig)
    else:
        st.write(f"No hay tickers con más de {threshold}% de tenedores institucionales en común.")
