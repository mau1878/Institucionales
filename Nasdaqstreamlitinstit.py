import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import numpy as np

# Loading and preprocessing data
institutional_holders = pd.read_csv("institutional_holders.csv")
general_data = pd.read_csv("general_data.csv")

# Preprocess institutional_holders
institutional_holders["Shares Held"] = institutional_holders["Shares Held"].str.replace(",", "").astype(float)
institutional_holders["Shares Change"] = institutional_holders["Shares Change"].str.replace(",", "").astype(float)

# Preprocess general_data
general_data["Total Shares Outstanding"] = general_data["Total Shares Outstanding"].str.replace(",", "").astype(float)
general_data["Total Holdings Value"] = general_data["Total Holdings Value"].str.replace("$", "").str.replace(",", "").astype(float)
general_data["Institutional Ownership %"] = general_data["Institutional Ownership %"].str.replace("%", "").astype(float) / 100

# Calculate approximate price per share (in dollars)
general_data["Price per Share"] = (general_data["Total Holdings Value"] * 1e6) / (general_data["Total Shares Outstanding"] * 1e6 * general_data["Institutional Ownership %"])

# Merge data
merged_data = pd.merge(institutional_holders, general_data, on="Ticker")
merged_data["Percentage Owned"] = (merged_data["Shares Held"] / (merged_data["Total Shares Outstanding"] * 1e6)) * 100
merged_data["Individual Holdings Value"] = merged_data["Shares Held"] * merged_data["Price per Share"] / 1e6  # In millions
merged_data['Date'] = pd.to_datetime(merged_data['Date'])

# Add percentage change calculation
merged_data["Previous Shares"] = merged_data["Shares Held"] - merged_data["Shares Change"]
merged_data["Shares Change %"] = np.where(
    merged_data["Previous Shares"] != 0,
    (merged_data["Shares Change"] / merged_data["Previous Shares"]) * 100,
    np.inf
)
merged_data["Shares Change % num"] = merged_data["Shares Change %"]

# For display purposes, replace inf with 'New Position'
merged_data_display = merged_data.copy()
merged_data_display["Shares Change %"] = merged_data_display["Shares Change %"].apply(
    lambda x: 'New Position' if np.isinf(x) else f"{x:.2f}%" if not np.isnan(x) else 'N/A'
)

# Function to color percentage changes
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

# Streamlit app
st.title("Análisis de Tenencias Institucionales")

# Sidebar for user input
st.sidebar.header("Entrada del Usuario")
option = st.sidebar.radio("Elige una opción:", ["Análisis de Tenedor Institucional", "Análisis por Ticker", "Comparación", "Análisis de Coincidencias", "Análisis Adicional"])

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

def plot_changes(df, x, y, title, is_percentage=False):
    # Filter out inf for plotting
    plot_df = df[~np.isinf(df[y])].copy()
    plot_df = plot_df.sort_values(by=y, ascending=False)
    top_20 = plot_df.head(20)

    # Define colors based on sign
    colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in top_20[y]]

    fig = go.Figure(data=[go.Bar(x=top_20[x], y=top_20[y], marker_color=colors)])
    fig.update_layout(title=title, xaxis_title=x, yaxis_title=y + (' %' if is_percentage else ''))
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
    - **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
    """)

    institutional_holders_list = institutional_holders["Owner Name"].unique()
    selected_holder = st.selectbox("Selecciona un Tenedor Institucional:", institutional_holders_list)

    holder_data = merged_data[merged_data["Owner Name"] == selected_holder]
    holder_data_display = merged_data_display[merged_data_display["Owner Name"] == selected_holder]
    holder_data_display = holder_data_display.sort_values(by='Shares Change % num', ascending=False)

    if not holder_data.empty:
        st.write(f"### Tenencias de {selected_holder}")
        styled_df = holder_data_display[["Ticker", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value"]].style.applymap(color_percentage, subset=["Shares Change %"])
        st.dataframe(styled_df)

        # Plot for shares held
        st.write("### Acciones Mantenidas por Empresa")
        plot_top_20(holder_data, "Ticker", "Shares Held", f"Acciones Mantenidas por Empresa de {selected_holder}", "skyblue")

        # Plot for percentage owned
        st.write("### Porcentaje de Acciones Propiedad por Empresa")
        plot_top_20(holder_data, "Ticker", "Percentage Owned", f"Porcentaje de Acciones Propiedad por Empresa de {selected_holder}", "lightgreen")

        # New plot for shares change
        st.write("### Cambio en Acciones por Empresa")
        plot_changes(holder_data, "Ticker", "Shares Change", f"Cambio en Acciones por Empresa de {selected_holder}")

        # New plot for shares change %
        st.write("### Cambio en Acciones % por Empresa")
        plot_changes(holder_data, "Ticker", "Shares Change %", f"Cambio en Acciones % por Empresa de {selected_holder}", is_percentage=True)
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
    - **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
    """)

    tickers_list = general_data["Ticker"].unique()
    selected_ticker = st.selectbox("Selecciona un Ticker:", tickers_list)

    ticker_data = merged_data[merged_data["Ticker"] == selected_ticker]
    ticker_data_display = merged_data_display[merged_data_display["Ticker"] == selected_ticker]
    ticker_data_display = ticker_data_display.sort_values(by='Shares Change % num', ascending=False)
    general_ticker_data = general_data[general_data["Ticker"] == selected_ticker]

    if not ticker_data.empty:
        st.write(f"### Datos Generales para {selected_ticker}")
        st.write(f"Acciones Totales Emitidas: {general_ticker_data['Total Shares Outstanding'].values[0]:,.0f} millones")
        st.write(f"Propiedad Institucional: {general_ticker_data['Institutional Ownership %'].values[0] * 100:.2f}%")
        st.write(f"Valor Total de Tenencias: ${general_ticker_data['Total Holdings Value'].values[0]:,.0f} millones")

        st.write(f"### Tenedores Institucionales para {selected_ticker}")
        styled_df = ticker_data_display[["Owner Name", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value"]].style.applymap(color_percentage, subset=["Shares Change %"])
        st.dataframe(styled_df)

        # Plot for shares held by institutional holders
        st.write("### Acciones Mantenidas por Tenedores Institucionales")
        plot_top_20(ticker_data, "Owner Name", "Shares Held", f"Acciones Mantenidas por Tenedores Institucionales para {selected_ticker}", "orange")

        # Plot for percentage owned by institutional holders
        st.write("### Porcentaje de Acciones Propiedad por Tenedores Institucionales")
        plot_top_20(ticker_data, "Owner Name", "Percentage Owned", f"Porcentaje de Acciones Propiedad por Tenedores Institucionales para {selected_ticker}", "purple")

        # New plot for shares change
        st.write("### Cambio en Acciones por Tenedores Institucionales")
        plot_changes(ticker_data, "Owner Name", "Shares Change", f"Cambio en Acciones por Tenedores Institucionales para {selected_ticker}")

        # New plot for shares change %
        st.write("### Cambio en Acciones % por Tenedores Institucionales")
        plot_changes(ticker_data, "Owner Name", "Shares Change %", f"Cambio en Acciones % por Tenedores Institucionales para {selected_ticker}", is_percentage=True)
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
    - **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
    """)

    comparison_type = st.radio("Elige el tipo de comparación:", ["Tickers", "Tenedores Institucionales"])

    if comparison_type == "Tickers":
        tickers = st.multiselect("Selecciona los Tickers para comparar:", general_data["Ticker"].unique())
        if tickers:
            comparison_data = merged_data[merged_data['Ticker'].isin(tickers)]
            comparison_data_display = merged_data_display[merged_data_display['Ticker'].isin(tickers)]
            comparison_data_display = comparison_data_display.sort_values(by='Shares Change % num', ascending=False)
            st.write("### Comparación de Tickers")
            styled_df = comparison_data_display[["Ticker", "Owner Name", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value"]].style.applymap(color_percentage, subset=["Shares Change %"])
            st.dataframe(styled_df)

            # Plotting
            for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
                fig = px.bar(comparison_data, x="Ticker", y=metric, color="Owner Name", barmode="group")
                fig.update_layout(title=f"Comparación de {metric} por Ticker", xaxis_title="Ticker", yaxis_title=metric)
                st.plotly_chart(fig)

            # New plots for changes
            st.write("### Comparación de Cambio en Acciones por Ticker")
            colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in comparison_data["Shares Change"]]
            fig = go.Figure(data=[go.Bar(x=comparison_data["Ticker"] + ' - ' + comparison_data["Owner Name"], y=comparison_data["Shares Change"], marker_color=colors)])
            fig.update_layout(title="Comparación de Cambio en Acciones por Ticker", xaxis_title="Ticker - Owner", yaxis_title="Cambio en Acciones")
            st.plotly_chart(fig)

            st.write("### Comparación de Cambio en Acciones % por Ticker")
            plot_comparison_data = comparison_data[~np.isinf(comparison_data["Shares Change %"])]
            colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in plot_comparison_data["Shares Change %"]]
            fig = go.Figure(data=[go.Bar(x=plot_comparison_data["Ticker"] + ' - ' + plot_comparison_data["Owner Name"], y=plot_comparison_data["Shares Change %"], marker_color=colors)])
            fig.update_layout(title="Comparación de Cambio en Acciones % por Ticker", xaxis_title="Ticker - Owner", yaxis_title="Cambio en Acciones %")
            st.plotly_chart(fig)

    elif comparison_type == "Tenedores Institucionales":
        holders = st.multiselect("Selecciona los Tenedores Institucionales para comparar:", institutional_holders["Owner Name"].unique())
        if holders:
            comparison_data = merged_data[merged_data['Owner Name'].isin(holders)]
            comparison_data_display = merged_data_display[merged_data_display['Owner Name'].isin(holders)]
            comparison_data_display = comparison_data_display.sort_values(by='Shares Change % num', ascending=False)
            st.write("### Comparación de Tenedores Institucionales")
            styled_df = comparison_data_display[["Owner Name", "Ticker", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value"]].style.applymap(color_percentage, subset=["Shares Change %"])
            st.dataframe(styled_df)

            # Plotting
            for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
                fig = px.bar(comparison_data, x="Owner Name", y=metric, color="Ticker", barmode="group")
                fig.update_layout(title=f"Comparación de {metric} por Tenedor Institucional", xaxis_title="Tenedor Institucional", yaxis_title=metric)
                st.plotly_chart(fig)

            # New plots for changes
            st.write("### Comparación de Cambio en Acciones por Tenedor Institucional")
            colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in comparison_data["Shares Change"]]
            fig = go.Figure(data=[go.Bar(x=comparison_data["Owner Name"] + ' - ' + comparison_data["Ticker"], y=comparison_data["Shares Change"], marker_color=colors)])
            fig.update_layout(title="Comparación de Cambio en Acciones por Tenedor Institucional", xaxis_title="Owner - Ticker", yaxis_title="Cambio en Acciones")
            st.plotly_chart(fig)

            st.write("### Comparación de Cambio en Acciones % por Tenedor Institucional")
            plot_comparison_data = comparison_data[~np.isinf(comparison_data["Shares Change %"])]
            colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in plot_comparison_data["Shares Change %"]]
            fig = go.Figure(data=[go.Bar(x=plot_comparison_data["Owner Name"] + ' - ' + plot_comparison_data["Ticker"], y=plot_comparison_data["Shares Change %"], marker_color=colors)])
            fig.update_layout(title="Comparación de Cambio en Acciones % por Tenedor Institucional", xaxis_title="Owner - Ticker", yaxis_title="Cambio en Acciones %")
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
        counts = data.groupby(group_by)['Ticker'].nunique() if common_entity == 'Ticker' else data.groupby(group_by)['Owner Name'].nunique()
        total = len(data[common_entity].unique())
        return ((counts / total) * 100).reset_index(name='Percentage')

    # Institutional Holders with most common tickers
    st.subheader("Tenedores Institucionales con más Tickers en Común")
    holder_commonality = commonality(merged_data, 'Owner Name', 'Ticker')
    filtered_holders = holder_commonality[holder_commonality['Percentage'] >= threshold].sort_values('Percentage', ascending=False)
    if not filtered_holders.empty:
        st.dataframe(filtered_holders)
        fig = px.bar(filtered_holders, x='Owner Name', y='Percentage', title=f"Tenedores Institucionales con más de {threshold}% de Tickers en Común", labels={'Percentage': f'Porcentaje de Tickers Comunes'})
        st.plotly_chart(fig)
    else:
        st.write(f"No hay tenedores institucionales con más de {threshold}% de tickers en común.")

    # Tickers with most common institutional holders
    st.subheader("Tickers con más Tenedores Institucionales en Común")
    ticker_commonality = commonality(merged_data, 'Ticker', 'Owner Name')
    filtered_tickers = ticker_commonality[ticker_commonality['Percentage'] >= threshold].sort_values('Percentage', ascending=False)
    if not filtered_tickers.empty:
        st.dataframe(filtered_tickers)
        fig = px.bar(filtered_tickers, x='Ticker', y='Percentage', title=f"Tickers con más de {threshold}% de Tenedores Institucionales en Común", labels={'Percentage': f'Porcentaje de Tenedores Comunes'})
        st.plotly_chart(fig)
    else:
        st.write(f"No hay tickers con más de {threshold}% de tenedores institucionales en común.")

elif option == "Análisis Adicional":
    st.header("Análisis Adicional")

    # 2. Market Cap Influence
    st.subheader("Impacto de la Propiedad Institucional en la Capitalización de Mercado")
    ticker = st.selectbox("Selecciona un Ticker para análisis de capitalización:", general_data['Ticker'])
    ticker_data = merged_data[merged_data['Ticker'] == ticker]
    total_shares = general_data[general_data['Ticker'] == ticker]['Total Shares Outstanding'].iloc[0] * 1e6

    # Use yfinance to get current stock price
    try:
        stock = yf.Ticker(ticker)
        price = stock.info['regularMarketPrice']
        market_cap = price * total_shares
        st.write(f"Precio actual de {ticker}: ${price:.2f}")
        st.write(f"Capitalización de Mercado de {ticker}: ${market_cap / 1e6:.2f} millones")
    except:
        st.write(f"No se pudo obtener el precio actual para {ticker}. Capitalización aproximada no disponible.")
        st.write(f"Capitalización de Mercado Aproximada de {ticker}: ${total_shares * 100:.2f} millones (asumiendo $100 por acción como ejemplo)")

    # Ownership concentration
    st.subheader("Concentración de Propiedad")
    top_n = st.slider("Selecciona el número de principales tenedores:", 1, 20, 5)
    ticker = st.selectbox("Selecciona un Ticker para análisis de concentración:", general_data['Ticker'])
    ticker_data = merged_data[merged_data['Ticker'] == ticker]
    total_shares = general_data[general_data['Ticker'] == ticker]['Total Shares Outstanding'].iloc[0] * 1e6

    # Get top N holders
    top_holders = ticker_data.sort_values('Shares Held', ascending=False).head(top_n)
    top_holders['Ownership Percentage'] = (top_holders['Shares Held'] / total_shares) * 100

    # Calculate shares held by other institutional holders
    other_institutional_shares = ticker_data['Shares Held'].sum() - top_holders['Shares Held'].sum()
    other_institutional_percentage = (other_institutional_shares / total_shares) * 100

    # Calculate shares held by other holders (non-institutional)
    other_holders_shares = total_shares - ticker_data['Shares Held'].sum()
    other_holders_percentage = (other_holders_shares / total_shares) * 100

    # Prepare data for pie chart
    pie_data = top_holders[['Owner Name', 'Ownership Percentage']].rename(columns={'Ownership Percentage': 'Percentage'})
    pie_data = pd.concat([pie_data, 
                          pd.DataFrame({'Owner Name': ['Otros institucionales'], 'Percentage': [other_institutional_percentage]}),
                          pd.DataFrame({'Owner Name': ['Otros tenedores'], 'Percentage': [other_holders_percentage]})], 
                         ignore_index=True)

    # Create pie chart
    fig = px.pie(pie_data, values='Percentage', names='Owner Name', title=f'Concentración de Propiedad para {ticker}')
    st.plotly_chart(fig)

    # 4. Comparative Analysis Across Tickers
    st.subheader("Comparación Entre Tickers")
    tickers = st.multiselect("Selecciona los Tickers para comparar:", general_data['Ticker'].unique())
    if tickers:
        comparison_data = merged_data[merged_data['Ticker'].isin(tickers)]

        # Option to limit the number of holders shown
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

        # Sort 'Otros institucionales' to the bottom
        category_order = [name for name in simplified_data['Owner Name'].unique() if name != 'Otros institucionales'] + ['Otros institucionales']

        st.write("### Comparación de Métricas por Ticker")
        for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
            fig = px.bar(simplified_data, x="Ticker", y=metric, color="Owner Name", barmode="stack",
                         category_orders={"Owner Name": category_order})

            # Custom color for 'Otros institucionales'
            colors = ['grey' if c == 'Otros institucionales' else px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
                      for i, c in enumerate(simplified_data['Owner Name'].unique())]
            fig.for_each_trace(lambda t: t.update(marker_color=colors[category_order.index(t.name)]))

            fig.update_layout(title=f"Comparación de {metric} entre Tickers",
                              xaxis_title="Ticker",
                              yaxis_title=metric,
                              legend_title="Tenedores")
            st.plotly_chart(fig, use_container_width=True)

        # Scatter plot for Individual Holdings Value
        fig = px.scatter(simplified_data, x="Ticker", y="Individual Holdings Value", color="Owner Name",
                         size="Shares Held",
                         hover_data=['Percentage Owned'],
                         title="Comparación de Valor Total de Tenencias por Ticker")
        for i, d in enumerate(fig.data):
            if d.name == 'Otros institucionales':
                fig.data[i].marker.color = 'grey'
        fig.update_layout(xaxis_title="Ticker", yaxis_title="Valor Total de Tenencias (en millones $)")
        st.plotly_chart(fig, use_container_width=True)

    # 5. Sector Analysis (Note: Sector mapping not available in current data)
    st.subheader("Análisis por Sector")
    st.write("Nota: Este análisis requiere información sobre sectores, que no está presente en los datos actuales.")

    # 8. Interactive Data Exploration
    st.subheader("Exploración Interactiva de Datos")
    min_date = merged_data['Date'].min().date()
    max_date = merged_data['Date'].max().date()
    date_range = st.slider("Selecciona un rango de fechas:", 
                           min_value=min_date, max_value=max_date, 
                           value=(min_date, max_date))

    date_range_pandas = pd.to_datetime(date_range)
    filtered_data = merged_data[(merged_data['Date'] >= date_range_pandas[0]) & (merged_data['Date'] <= date_range_pandas[1])]
    filtered_data_display = merged_data_display[(merged_data_display['Date'] >= date_range_pandas[0]) & (merged_data_display['Date'] <= date_range_pandas[1])]
    filtered_data_display = filtered_data_display.sort_values(by='Shares Change % num', ascending=False)
    styled_df = filtered_data_display[['Ticker', 'Owner Name', 'Date', 'Shares Held', 'Shares Change', 'Shares Change %', 'Individual Holdings Value']].style.applymap(color_percentage, subset=["Shares Change %"])
    st.dataframe(styled_df)

    # 9. Portfolio Analysis for Holders
    st.subheader("Análisis de Cartera para Tenedores")
    holder = st.selectbox("Selecciona un Tenedor para análisis de diversificación:", institutional_holders['Owner Name'].unique())
    holder_portfolio = merged_data[merged_data['Owner Name'] == holder]
    st.write(f"### Diversificación de {holder}")
    st.write(f"Número de Tickers Únicos: {holder_portfolio['Ticker'].nunique()}")

    # Calculate total holdings value using individual holdings
    total_holdings_value = holder_portfolio['Individual Holdings Value'].sum()  # In millions

    # Format the value for display
    if total_holdings_value >= 1e3:  # Billions
        formatted_value = f"${total_holdings_value / 1e3:.2f} mil millones"
    elif total_holdings_value >= 1:  # Millions
        formatted_value = f"${total_holdings_value:.2f} millones"
    else:
        formatted_value = f"${total_holdings_value * 1e6:.2f}"

    st.write(f"Valor Total de Tenencias: {formatted_value}")

    # 10. Sentiment Indicator
    st.subheader("Indicador de Sentimiento a través de Tenencias")
    holder = st.selectbox("Selecciona un Tenedor para análisis de sentimiento:", institutional_holders['Owner Name'].unique())
    holder_sentiment = merged_data[merged_data['Owner Name'] == holder].sort_values('Date')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=holder_sentiment['Date'], y=holder_sentiment['Shares Change'],
                             mode='lines+markers',
                             marker=dict(color=['green' if x > 0 else 'red' for x in holder_sentiment['Shares Change']])))
    fig.update_layout(title=f'Sentimiento de {holder} a través de Cambios en Tenencias', xaxis_title='Fecha', yaxis_title='Cambio en Acciones')
    st.plotly_chart(fig)

    # New: Sentiment with % change
    st.subheader("Indicador de Sentimiento a través de Cambios % en Tenencias")
    holder_sentiment_noinf = holder_sentiment[~np.isinf(holder_sentiment['Shares Change %'])]
    fig_percent = go.Figure()
    fig_percent.add_trace(go.Scatter(x=holder_sentiment_noinf['Date'], y=holder_sentiment_noinf['Shares Change %'],
                                     mode='lines+markers',
                                     marker=dict(color=['green' if x > 0 else 'red' for x in holder_sentiment_noinf['Shares Change %']])))
    fig_percent.update_layout(title=f'Sentimiento de {holder} a través de Cambios % en Tenencias', xaxis_title='Fecha', yaxis_title='Cambio en Acciones %')
    st.plotly_chart(fig_percent)
