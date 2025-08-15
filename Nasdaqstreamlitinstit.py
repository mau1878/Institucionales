import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3

# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    institutional_holders = pd.read_parquet("institutional_holders.parquet", engine="pyarrow")
    general_data = pd.read_parquet("general_data.parquet", engine="pyarrow")
    return institutional_holders, general_data

@st.cache_data
def get_market_caps(tickers_list):
    """
    Fetches current market capitalization for a list of tickers using yfinance.
    Includes error handling for tickers that might fail.
    """
    market_caps = {}
    for ticker in tickers_list:
        try:
            stock = yf.Ticker(ticker)
            # Use 'marketCap' as it's the most common key for market capitalization
            cap = stock.info.get('marketCap', None)
            if cap:
                market_caps[ticker] = cap
        except Exception:
            # Silently fail for tickers that can't be found
            pass
    return market_caps

# --- Main App Logic ---
institutional_holders, general_data = load_data()


# Calculate approximate price per share (in dollars)
general_data["Price per Share"] = (general_data["Total Holdings Value"] * 1e6) / (general_data["Total Shares Outstanding"] * 1e6 * general_data["Institutional Ownership %"])

# --- NEW: Fetch and Merge Live Market Cap Data ---
with st.spinner('Obteniendo datos de capitalización de mercado en tiempo real...'):
    unique_tickers = general_data['Ticker'].unique()
    live_market_caps = get_market_caps(unique_tickers)

    if live_market_caps:
        market_cap_df = pd.DataFrame(list(live_market_caps.items()), columns=['Ticker', 'Market Cap'])
        general_data = pd.merge(general_data, market_cap_df, on='Ticker', how='left')
        st.success('Datos de capitalización de mercado obtenidos con éxito.')
    else:
        st.warning('No se pudieron obtener los datos de capitalización de mercado en tiempo real. Se usarán valores aproximados.')

# Use approximate market cap as a fallback
general_data['Market Cap'] = general_data.get('Market Cap', general_data['Price per Share'] * general_data['Total Shares Outstanding'] * 1e6)
general_data['Market Cap'].fillna(general_data['Price per Share'] * general_data['Total Shares Outstanding'] * 1e6, inplace=True)


# Merge data
merged_data = pd.merge(institutional_holders, general_data, on="Ticker")
merged_data["Percentage Owned"] = (merged_data["Shares Held"] / (merged_data["Total Shares Outstanding"] * 1e6)) * 100
merged_data["Individual Holdings Value"] = merged_data["Shares Held"] * merged_data["Price per Share"] / 1e6  # In millions
merged_data['Date'] = pd.to_datetime(merged_data['Date'])

# Calculate change in value (in millions USD)
merged_data["Change in Value"] = merged_data["Shares Change"] * merged_data["Price per Share"] / 1e6  # In millions USD

# --- NEW: Calculate Change as % of Market Cap ---
# Ensure Market Cap is not zero to avoid division errors
merged_data['Change as % of Market Cap'] = np.where(
    merged_data['Market Cap'] > 0,
    (merged_data['Change in Value'] * 1e6) / merged_data['Market Cap'] * 100,
    0
)

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


# Global date filter
st.sidebar.header("Filtro por Fecha")
unique_dates = sorted(merged_data['Date'].dt.date.unique())
selected_date = st.sidebar.selectbox("Selecciona una Fecha (opcional):", [None] + unique_dates)

if selected_date:
    selected_date = pd.to_datetime(selected_date)
    merged_data = merged_data[merged_data['Date'] == selected_date]
    merged_data_display = merged_data_display[merged_data_display['Date'] == selected_date]

# Streamlit app
st.title("Análisis de Tenencias Institucionales")

# Sidebar for user input
st.sidebar.header("Entrada del Usuario")
option = st.sidebar.radio("Elige una opción:",
                          ["Análisis de Tenedor Institucional", "Análisis por Ticker", "Comparación",
                           "Análisis de Coincidencias", "Rankings de Mercado", "Análisis Adicional"])


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


def plot_changes(df, x, y_num, title, is_percentage=False):
    # Filter out inf for plotting
    plot_df = df[~np.isinf(df[y_num])].copy()
    plot_df = plot_df.sort_values(by=y_num, ascending=False)
    top_20 = plot_df.head(20)

    # Define colors based on sign
    colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in top_20[y_num]]

    fig = go.Figure(data=[go.Bar(x=top_20[x], y=top_20[y_num], marker_color=colors)])
    fig.update_layout(title=title, xaxis_title=x, yaxis_title='Shares Change %' if is_percentage else 'Shares Change')
    st.plotly_chart(fig)


# --- UPGRADED VENN DIAGRAM FUNCTION (Proportional and 2/3-way) ---
def plot_venn_like_comparison(item_list, comparison_field, data):
    """
    Generates a proportional Venn diagram for two or three items.
    The circle sizes are proportional to the total number of entities in each set.
    """
    num_items = len(item_list)
    if not (2 <= num_items <= 3):
        st.warning("Please select 2 or 3 items for Venn diagram comparison.")
        return

    if comparison_field == 'Ticker':
        entity_field = 'Owner Name'
        title_entities = "Tenedores"
    else:
        entity_field = 'Ticker'
        title_entities = "Tickers"

    title = f"Coincidencia de {title_entities} entre {', '.join(item_list)}"
    sets = [set(data[data[comparison_field] == item][entity_field].unique()) for item in item_list]
    fig = go.Figure()
    opacity = 0.6
    colors = ["#636EFA", "#EF553B", "#00CC96"]

    if num_items == 2:
        s1, s2 = sets[0], sets[1]
        n1, n2 = item_list[0], item_list[1]

        # Calculate segments
        common = s1.intersection(s2)
        unique1 = s1.difference(s2)
        unique2 = s2.difference(s1)
        c1, c2, c_common = len(unique1), len(unique2), len(common)

        if c1 == 0 and c2 == 0 and c_common == 0:
            st.write("No hay datos de coincidencia para mostrar.")
            return

        # Proportional radius
        total1, total2 = len(s1), len(s2)
        max_total = max(total1, total2, 1)
        r1 = math.sqrt(total1 / max_total)
        r2 = math.sqrt(total2 / max_total)

        # Position circles
        x1, y1 = -r1 / 2, 0
        x2, y2 = r2 / 2, 0

        fig.add_shape(type="circle", xref="x", yref="y", x0=x1 - r1, y0=y1 - r1, x1=x1 + r1, y1=y1 + r1,
                      fillcolor=colors[0], opacity=opacity, line_color=colors[0])
        fig.add_shape(type="circle", xref="x", yref="y", x0=x2 - r2, y0=y2 - r2, x1=x2 + r2, y1=y2 + r2,
                      fillcolor=colors[1], opacity=opacity, line_color=colors[1])

        # Add annotations
        fig.add_annotation(x=x1, y=y1, text=f"<b>{c1}</b>", showarrow=False, font=dict(size=20, color="white"))
        fig.add_annotation(x=x2, y=y2, text=f"<b>{c2}</b>", showarrow=False, font=dict(size=20, color="white"))
        if c_common > 0:
            fig.add_annotation(x=(x1 + x2) / 2, y=(y1 + y2) / 2, text=f"<b>{c_common}</b>", showarrow=False,
                               font=dict(size=20, color="white"))

        fig.add_annotation(x=x1, y=y1 + r1 + 0.1, text=f"<b>{n1}</b>", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=x2, y=y2 + r2 + 0.1, text=f"<b>{n2}</b>", showarrow=False, font=dict(size=14))

        with st.expander("Ver listas de entidades detalladas"):
            st.write(f"**Solo en {n1} ({c1}):** {', '.join(list(unique1)) if unique1 else 'Ninguno'}")
            st.write(f"**Solo en {n2} ({c2}):** {', '.join(list(unique2)) if unique2 else 'Ninguno'}")
            st.write(f"**En Común ({c_common}):** {', '.join(list(common)) if common else 'Ninguno'}")

    elif num_items == 3:
        s1, s2, s3 = sets[0], sets[1], sets[2]
        n1, n2, n3 = item_list[0], item_list[1], item_list[2]

        # Calculate segments
        s1_only = s1 - s2 - s3
        s2_only = s2 - s1 - s3
        s3_only = s3 - s1 - s2
        s1_s2 = (s1 & s2) - s3
        s1_s3 = (s1 & s3) - s2
        s2_s3 = (s2 & s3) - s1
        s1_s2_s3 = s1 & s2 & s3

        counts = {k: len(v) for k, v in locals().items() if k.startswith('s')}

        # Proportional radius
        total1, total2, total3 = len(s1), len(s2), len(s3)
        max_total = max(total1, total2, total3, 1)
        r1 = math.sqrt(total1 / max_total) * 0.8
        r2 = math.sqrt(total2 / max_total) * 0.8
        r3 = math.sqrt(total3 / max_total) * 0.8

        # Position circles
        x1, y1 = 0, r1 * 0.6
        x2, y2 = -r2 * 0.5, -r2 * 0.3
        x3, y3 = r3 * 0.5, -r3 * 0.3

        fig.add_shape(type="circle", x0=x1 - r1, y0=y1 - r1, x1=x1 + r1, y1=y1 + r1, fillcolor=colors[0],
                      opacity=opacity, line_color=colors[0])
        fig.add_shape(type="circle", x0=x2 - r2, y0=y2 - r2, x1=x2 + r2, y1=y2 + r2, fillcolor=colors[1],
                      opacity=opacity, line_color=colors[1])
        fig.add_shape(type="circle", x0=x3 - r3, y0=y3 - r3, x1=x3 + r3, y1=y3 + r3, fillcolor=colors[2],
                      opacity=opacity, line_color=colors[2])

        # Add annotations (simplified positioning)
        fig.add_annotation(x=0, y=y1 + r1 / 2, text=f"<b>{counts['s1_only']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))
        fig.add_annotation(x=x2, y=y2, text=f"<b>{counts['s2_only']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))
        fig.add_annotation(x=x3, y=y3, text=f"<b>{counts['s3_only']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))
        fig.add_annotation(x=(x1 + x2) / 2, y=(y1 + y2) / 2, text=f"<b>{counts['s1_s2']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))
        fig.add_annotation(x=(x1 + x3) / 2, y=(y1 + y3) / 2, text=f"<b>{counts['s1_s3']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))
        fig.add_annotation(x=(x2 + x3) / 2, y=(y2 + y3) / 2, text=f"<b>{counts['s2_s3']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))
        fig.add_annotation(x=0, y=0, text=f"<b>{counts['s1_s2_s3']}</b>", showarrow=False,
                           font=dict(size=18, color="white"))

        fig.add_annotation(x=x1, y=y1 + r1 + 0.1, text=f"<b>{n1}</b>", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=x2 - r2 - 0.1, y=y2, text=f"<b>{n2}</b>", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=x3 + r3 + 0.1, y=y3, text=f"<b>{n3}</b>", showarrow=False, font=dict(size=14))

        with st.expander("Ver listas de entidades detalladas"):
            st.write(f"**Solo en {n1} ({counts['s1_only']}):** {', '.join(list(s1_only)) if s1_only else 'Ninguno'}")
            st.write(f"**Solo en {n2} ({counts['s2_only']}):** {', '.join(list(s2_only)) if s2_only else 'Ninguno'}")
            st.write(f"**Solo en {n3} ({counts['s3_only']}):** {', '.join(list(s3_only)) if s3_only else 'Ninguno'}")
            st.write(
                f"**Común entre {n1} y {n2} ({counts['s1_s2']}):** {', '.join(list(s1_s2)) if s1_s2 else 'Ninguno'}")
            st.write(
                f"**Común entre {n1} y {n3} ({counts['s1_s3']}):** {', '.join(list(s1_s3)) if s1_s3 else 'Ninguno'}")
            st.write(
                f"**Común entre {n2} y {n3} ({counts['s2_s3']}):** {', '.join(list(s2_s3)) if s2_s3 else 'Ninguno'}")
            st.write(
                f"**Común entre los tres ({counts['s1_s2_s3']}):** {', '.join(list(s1_s2_s3)) if s1_s2_s3 else 'Ninguno'}")

    fig.update_layout(
        title_text=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2, 2]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5, 2]),
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=500,
        margin=dict(t=80, b=20, l=20, r=20)
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    st.plotly_chart(fig, use_container_width=True)


def plot_matplotlib_venn(item_list, comparison_field, data):
    """
    Generates a true proportional Venn diagram using the matplotlib-venn library.
    NOTE: This function requires you to run 'pip install matplotlib-venn' in your environment.
    """
    num_items = len(item_list)
    if not (2 <= num_items <= 3):
        # This check is important as the library supports 2 or 3 sets.
        st.warning("La comparación con diagramas de Venn proporcionales solo admite 2 o 3 elementos.")
        return

    # Determine the entity to compare (Holders or Tickers)
    if comparison_field == 'Ticker':
        entity_field = 'Owner Name'
        title_entities = "Tenedores Institucionales"
    else:
        entity_field = 'Ticker'
        title_entities = "Tickers"

    title = f"Coincidencia Proporcional de {title_entities} entre {', '.join(item_list)}"

    # Create the sets for the diagram
    sets = [set(data[data[comparison_field] == item][entity_field].unique()) for item in item_list]
    set_labels = item_list

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 7))  # Create a matplotlib figure and axes
    if num_items == 2:
        venn2(subsets=sets, set_labels=set_labels, ax=ax)
    elif num_items == 3:
        venn3(subsets=sets, set_labels=set_labels, ax=ax)

    ax.set_title(title)
    st.pyplot(fig)  # Display the matplotlib figure in Streamlit
if option == "Análisis de Tenedor Institucional":
    st.header("Análisis de Tenedor Institucional")
    st.write("""
    **Cómo usar esta sección:**
    - **Selecciona un Tenedor Institucional:** Elige un tenedor para ver sus inversiones en diferentes empresas (tickers).
    - **Datos mostrados:** Verás las acciones mantenidas, el cambio en las acciones y el porcentaje de propiedad en cada empresa.**Explicación de los datos:**
- **Acciones Mantenidas:** Número de acciones que el tenedor posee en cada empresa.
- **Cambio en Acciones:** Diferencia en el número de acciones desde la última actualización.
- **Porcentaje de Propiedad:** Porcentaje de las acciones totales de la empresa que posee el tenedor.
- **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
""")

    institutional_holders_list = sorted(institutional_holders["Owner Name"].unique())
    selected_holder = st.selectbox("Selecciona un Tenedor Institucional:", institutional_holders_list)

    holder_data = merged_data[merged_data["Owner Name"] == selected_holder]
    holder_data_display = merged_data_display[merged_data_display["Owner Name"] == selected_holder]
    holder_data_display = holder_data_display.sort_values(by='Shares Change % num', ascending=False)

    if not holder_data.empty:
        st.write(f"### Tenencias de {selected_holder}")
        display_cols = ["Date", "Ticker", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value", "Change as % of Market Cap"]
        styled_df = holder_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format({'Change as % of Market Cap': '{:.4f}%'})
        st.dataframe(styled_df)

        # Plot for shares held
        st.write("### Acciones Mantenidas por Empresa")
        plot_top_20(holder_data, "Ticker", "Shares Held", f"Acciones Mantenidas por Empresa de {selected_holder}",
                    "skyblue")

        # Plot for percentage owned
        st.write("### Porcentaje de Acciones Propiedad por Empresa")
        plot_top_20(holder_data, "Ticker", "Percentage Owned",
                    f"Porcentaje de Acciones Propiedad por Empresa de {selected_holder}", "lightgreen")

        # New plot for shares change
        st.write("### Cambio en Acciones por Empresa")
        plot_changes(holder_data, "Ticker", "Shares Change", f"Cambio en Acciones por Empresa de {selected_holder}")

        # New plot for shares change %
        st.write("### Cambio en Acciones % por Empresa")
        plot_changes(holder_data, "Ticker", "Shares Change % num",
                     f"Cambio en Acciones % por Empresa de {selected_holder}", is_percentage=True)

        # New: Rank of most valuable holdings
        st.write("### Rank de Tenencias Más Valiosas (por Valor Total)")
        holder_val_sorted = holder_data.sort_values(by="Individual Holdings Value", ascending=False).head(20)
        fig_val = px.bar(holder_val_sorted, x="Ticker", y="Individual Holdings Value",
                         title=f"Tenencias Más Valiosas de {selected_holder} (en millones USD)",
                         color_discrete_sequence=["blue"])
        fig_val.update_layout(xaxis_title="Ticker", yaxis_title="Valor Total (millones USD)")
        st.plotly_chart(fig_val)

        # New: Rank of most valuable changes in positions
        st.write("### Rank de Cambios en Posiciones Más Valiosos (por USD)")
        holder_change_sorted = holder_data.sort_values(by="Change in Value", ascending=False).head(20)
        colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in
                  holder_change_sorted["Change in Value"]]
        fig_change = go.Figure(data=[
            go.Bar(x=holder_change_sorted["Ticker"], y=holder_change_sorted["Change in Value"], marker_color=colors)])
        fig_change.update_layout(title=f"Cambios Más Valiosos en Posiciones de {selected_holder} (en millones USD)",
                                 xaxis_title="Ticker", yaxis_title="Cambio en Valor (millones USD)")
        st.plotly_chart(fig_change)
    else:
        st.write("No hay datos disponibles para el tenedor institucional seleccionado.")

elif option == "Análisis por Ticker":
    st.header("Análisis por Ticker")
    st.write("""
    **Cómo usar esta sección:**
    - **Selecciona un Ticker:** Elige una empresa para ver quiénes son sus principales tenedores institucionales.
    - **Datos mostrados:** Información general sobre la empresa y detalles de los tenedores institucionales.**Explicación de los datos:**
- **Acciones Totales Emitidas:** Total de acciones en circulación de la empresa.
- **Propiedad Institucional:** Porcentaje del total de acciones que son propiedad de instituciones.
- **Valor Total de Tenencias:** Valor total de las acciones mantenidas por instituciones.
- **Tenedores Institucionales:** Lista de los principales tenedores con sus acciones mantenidas y cambios.
- **Cambio en Acciones %:** Porcentaje de cambio en las acciones mantenidas (verde para aumentos, rojo para disminuciones).
""")

    tickers_list = sorted(general_data["Ticker"].unique())
    selected_ticker = st.selectbox("Selecciona un Ticker:", tickers_list)

    ticker_data = merged_data[merged_data["Ticker"] == selected_ticker]
    ticker_data_display = merged_data_display[merged_data_display["Ticker"] == selected_ticker]
    ticker_data_display = ticker_data_display.sort_values(by='Shares Change % num', ascending=False)
    general_ticker_data = general_data[general_data["Ticker"] == selected_ticker]

    if not ticker_data.empty:
        st.write(f"### Datos Generales para {selected_ticker}")
        st.write(
            f"Acciones Totales Emitidas: {general_ticker_data['Total Shares Outstanding'].values[0]:,.0f} millones")
        st.write(f"Propiedad Institucional: {general_ticker_data['Institutional Ownership %'].values[0] * 100:.2f}%")
        st.write(f"Valor Total de Tenencias: ${general_ticker_data['Total Holdings Value'].values[0]:,.0f} millones")
        st.write(f"Capitalización de Mercado (Market Cap): ${general_ticker_data['Market Cap'].values[0] / 1e9:,.2f} mil millones")


        st.write(f"### Tenedores Institucionales para {selected_ticker}")
        display_cols = ["Date", "Owner Name", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value", "Change as % of Market Cap"]
        styled_df = ticker_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format({'Change as % of Market Cap': '{:.4f}%'})
        st.dataframe(styled_df)

        # Plot for shares held by institutional holders
        st.write("### Acciones Mantenidas por Tenedores Institucionales")
        plot_top_20(ticker_data, "Owner Name", "Shares Held",
                    f"Acciones Mantenidas por Tenedores Institucionales para {selected_ticker}", "orange")

        # Plot for percentage owned by institutional holders
        st.write("### Porcentaje de Acciones Propiedad por Tenedores Institucionales")
        plot_top_20(ticker_data, "Owner Name", "Percentage Owned",
                    f"Porcentaje de Acciones Propiedad por Tenedores Institucionales para {selected_ticker}", "purple")

        # New plot for shares change
        st.write("### Cambio en Acciones por Tenedores Institucionales")
        plot_changes(ticker_data, "Owner Name", "Shares Change",
                     f"Cambio en Acciones por Tenedores Institucionales para {selected_ticker}")

        # New plot for shares change %
        st.write("### Cambio en Acciones % por Tenedores Institucionales")
        plot_changes(ticker_data, "Owner Name", "Shares Change % num",
                     f"Cambio en Acciones % por Tenedores Institucionales para {selected_ticker}", is_percentage=True)

        # New: Rank of most valuable holdings (by holders for this ticker)
        st.write("### Rank de Tenencias Más Valiosas (por Valor Total)")
        ticker_val_sorted = ticker_data.sort_values(by="Individual Holdings Value", ascending=False).head(20)
        fig_val = px.bar(ticker_val_sorted, x="Owner Name", y="Individual Holdings Value",
                         title=f"Tenencias Más Valiosas en {selected_ticker} (en millones USD)",
                         color_discrete_sequence=["blue"])
        fig_val.update_layout(xaxis_title="Tenedor Institucional", yaxis_title="Valor Total (millones USD)")
        st.plotly_chart(fig_val)

        # New: Rank de most valuable changes in positions (by holders for this ticker)
        st.write("### Rank de Cambios en Posiciones Más Valiosos (por USD)")
        ticker_change_sorted = ticker_data.sort_values(by="Change in Value", ascending=False).head(20)
        colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in
                  ticker_change_sorted["Change in Value"]]
        fig_change = go.Figure(data=[
            go.Bar(x=ticker_change_sorted["Owner Name"], y=ticker_change_sorted["Change in Value"],
                   marker_color=colors)])
        fig_change.update_layout(title=f"Cambios Más Valiosos en Posiciones para {selected_ticker} (en millones USD)",
                                 xaxis_title="Tenedor Institucional", yaxis_title="Cambio en Valor (millones USD)")
        st.plotly_chart(fig_change)
    else:
        st.write("No hay datos disponibles para el ticker seleccionado.")

# --- CORRECTED SECTION ---
# --- UPDATED SECTION ---
elif option == "Comparación":
    st.header("Comparación")
    st.write("""
    **Cómo usar esta sección:**
    - **Elige el tipo de comparación:** Puedes comparar tickers o tenedores institucionales.
    - **Selecciona 2 o 3 items:** Elige varios tickers o tenedores para comparar sus datos.
    - **Gráfico de Coincidencias:** Aparecerá un diagrama mostrando las coincidencias entre los items seleccionados.
    """)

    comparison_type = st.radio("Elige el tipo de comparación:", ["Tickers", "Tenedores Institucionales"])

    if comparison_type == "Tickers":
        tickers = st.multiselect("Selecciona los Tickers para comparar:", sorted(general_data["Ticker"].unique()))
        if tickers:
            # Logic for plotting Venn diagrams
            if len(tickers) in [2, 3]:
                st.subheader("Gráfico de Coincidencias de Tenedores")

                # ADDED: Let the user choose the chart type
                chart_type = st.radio(
                    "Elige el tipo de gráfico:",
                    ('Burbujas (Interactivo)', 'Venn (Proporcional y Preciso)'),
                    key='ticker_chart_choice',
                    help="El gráfico de Burbujas es interactivo. El gráfico de Venn es una representación matemática precisa de las superposiciones."
                )

                if chart_type == 'Burbujas (Interactivo)':
                    st.write(
                        "Este diagrama de burbujas muestra los tenedores únicos para cada ticker y las coincidencias. El tamaño de las burbujas es proporcional al total de tenedores.")
                    plot_venn_like_comparison(tickers, 'Ticker', merged_data)
                else:
                    st.write(
                        "Este diagrama de Venn muestra las proporciones exactas de tenedores únicos y compartidos.")
                    plot_matplotlib_venn(tickers, 'Ticker', merged_data)

            # The rest of the comparison logic remains the same
            comparison_data = merged_data[merged_data['Ticker'].isin(tickers)]
            comparison_data_display = merged_data_display[merged_data_display['Ticker'].isin(tickers)]
            comparison_data_display = comparison_data_display.sort_values(by='Shares Change % num', ascending=False)
            st.write("### Tabla de Comparación de Tickers")
            display_cols = ["Date", "Ticker", "Owner Name", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value", "Change as % of Market Cap"]
            styled_df = comparison_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format({'Change as % of Market Cap': '{:.4f}%'})
            st.dataframe(styled_df)

            for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
                fig = px.bar(comparison_data, x="Ticker", y=metric, color="Owner Name", barmode="group")
                fig.update_layout(title=f"Comparación de {metric} por Ticker", xaxis_title="Ticker", yaxis_title=metric)
                st.plotly_chart(fig)

    elif comparison_type == "Tenedores Institucionales":
        holders = st.multiselect("Selecciona los Tenedores Institucionales para comparar:",
                                 sorted(institutional_holders["Owner Name"].unique()))
        if holders:
            # Logic for plotting Venn diagrams
            if len(holders) in [2, 3]:
                st.subheader("Gráfico de Coincidencias de Tickers")

                # ADDED: Let the user choose the chart type
                chart_type = st.radio(
                    "Elige el tipo de gráfico:",
                    ('Burbujas (Interactivo)', 'Venn (Proporcional y Preciso)'),
                    key='holder_chart_choice',
                    help="El gráfico de Burbujas es interactivo. El gráfico de Venn es una representación matemática precisa de las superposiciones."
                )

                if chart_type == 'Burbujas (Interactivo)':
                    st.write(
                        "Este diagrama de burbujas muestra los tickers únicos en la cartera de cada tenedor y las coincidencias. El tamaño de las burbujas es proporcional al total de tickers.")
                    plot_venn_like_comparison(holders, 'Owner Name', merged_data)
                else:
                    st.write("Este diagrama de Venn muestra las proporciones exactas de tickers únicos y compartidos.")
                    plot_matplotlib_venn(holders, 'Owner Name', merged_data)

            # The rest of the comparison logic remains the same
            comparison_data = merged_data[merged_data['Owner Name'].isin(holders)]
            comparison_data_display = merged_data_display[merged_data_display['Owner Name'].isin(holders)]
            comparison_data_display = comparison_data_display.sort_values(by='Shares Change % num', ascending=False)
            st.write("### Tabla de Comparación de Tenedores Institucionales")
            display_cols = ["Date", "Owner Name", "Ticker", "Shares Held", "Shares Change", "Shares Change %", "Percentage Owned", "Individual Holdings Value", "Change as % of Market Cap"]
            styled_df = comparison_data_display[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format({'Change as % of Market Cap': '{:.4f}%'})
            st.dataframe(styled_df)

            for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
                fig = px.bar(comparison_data, x="Owner Name", y=metric, color="Ticker", barmode="group")
                fig.update_layout(title=f"Comparación de {metric} por Tenedor Institucional",
                                  xaxis_title="Tenedor Institucional", yaxis_title=metric)
                st.plotly_chart(fig)

elif option == "Análisis de Coincidencias":
    st.header("Análisis de Coincidencias")
    st.write("""
    **Cómo usar esta sección:**
    - **Umbral de Coincidencia:** Define un porcentaje para filtrar los resultados. Sólo se mostrarán los tenedores o tickers que superan este umbral de coincidencia.**Explicación de los datos:**
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

# --- NEW SECTION: Market Rankings ---
elif option == "Rankings de Mercado":
    st.header("Rankings de Mercado")
    st.write("""
    Esta sección clasifica los tickers según la actividad de compra y venta de los tenedores institucionales.
    - **Términos Absolutos:** Se refiere al número de tenedores que realizaron una acción (abrir, aumentar, disminuir, cerrar posición).
    - **Términos Relativos (Valor):** Se refiere al valor total en USD del movimiento.
    - **Términos Relativos (% Market Cap):** Mide el valor del movimiento como un porcentaje de la capitalización de mercado total de la empresa, indicando la magnitud del impacto.
    """)

    # --- 1. New Positions ---
    st.subheader("🏆 Top Tickers por Apertura de Nuevas Posiciones")
    new_positions_df = merged_data[np.isinf(merged_data['Shares Change % num'])]

    # Absolute
    st.markdown("#### Por Número de Tenedores (Absoluto)")
    new_abs = new_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Nuevas Posiciones')
    top_new_abs = new_abs.sort_values('Número de Nuevas Posiciones', ascending=False).head(20)
    fig_new_abs = px.bar(top_new_abs, x='Ticker', y='Número de Nuevas Posiciones', title="Top 20 Tickers por Nuevas Posiciones Abiertas")
    st.plotly_chart(fig_new_abs)
    with st.expander("Ver datos de nuevas posiciones (absoluto)"):
        st.dataframe(top_new_abs)

    # Relative (Value)
    st.markdown("#### Por Valor de las Nuevas Posiciones (Relativo - USD)")
    new_val = new_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total (Millones USD)')
    top_new_val = new_val.sort_values('Valor Total (Millones USD)', ascending=False).head(20)
    fig_new_val = px.bar(top_new_val, x='Ticker', y='Valor Total (Millones USD)', title="Top 20 Tickers por Valor de Nuevas Posiciones")
    st.plotly_chart(fig_new_val)
    with st.expander("Ver datos de nuevas posiciones (valor)"):
        st.dataframe(top_new_val)

    # Relative (% Market Cap)
    st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
    new_mc = new_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
    top_new_mc = new_mc.sort_values('% del Market Cap', ascending=False).head(20)
    fig_new_mc = px.bar(top_new_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Nuevas Posiciones en Market Cap")
    fig_new_mc.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig_new_mc)
    with st.expander("Ver datos de nuevas posiciones (% market cap)"):
        st.dataframe(top_new_mc.style.format({'% del Market Cap': '{:.4f}%'}))


    # --- 2. Increased Positions ---
    st.subheader("📈 Top Tickers por Aumento de Posiciones Existentes")
    increased_positions_df = merged_data[(merged_data['Shares Change'] > 0) & (merged_data['Previous Shares'] > 0)]

    # Absolute
    st.markdown("#### Por Número de Tenedores (Absoluto)")
    inc_abs = increased_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Posiciones Aumentadas')
    top_inc_abs = inc_abs.sort_values('Número de Posiciones Aumentadas', ascending=False).head(20)
    fig_inc_abs = px.bar(top_inc_abs, x='Ticker', y='Número de Posiciones Aumentadas', title="Top 20 Tickers por Aumento de Posiciones")
    st.plotly_chart(fig_inc_abs)
    with st.expander("Ver datos de posiciones aumentadas (absoluto)"):
        st.dataframe(top_inc_abs)

    # Relative (Value)
    st.markdown("#### Por Valor del Aumento (Relativo - USD)")
    inc_val = increased_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total del Aumento (Millones USD)')
    top_inc_val = inc_val.sort_values('Valor Total del Aumento (Millones USD)', ascending=False).head(20)
    fig_inc_val = px.bar(top_inc_val, x='Ticker', y='Valor Total del Aumento (Millones USD)', title="Top 20 Tickers por Valor de Aumento de Posiciones")
    st.plotly_chart(fig_inc_val)
    with st.expander("Ver datos de posiciones aumentadas (valor)"):
        st.dataframe(top_inc_val)

    # Relative (% Market Cap)
    st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
    inc_mc = increased_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
    top_inc_mc = inc_mc.sort_values('% del Market Cap', ascending=False).head(20)
    fig_inc_mc = px.bar(top_inc_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Aumento de Posiciones en Market Cap")
    fig_inc_mc.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig_inc_mc)
    with st.expander("Ver datos de posiciones aumentadas (% market cap)"):
        st.dataframe(top_inc_mc.style.format({'% del Market Cap': '{:.4f}%'}))


    # --- 3. Decreased Positions ---
    st.subheader("📉 Top Tickers por Reducción de Posiciones Existentes")
    decreased_positions_df = merged_data[(merged_data['Shares Change'] < 0) & (merged_data['Shares Held'] > 0)]

    # Absolute
    st.markdown("#### Por Número de Tenedores (Absoluto)")
    dec_abs = decreased_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Posiciones Reducidas')
    top_dec_abs = dec_abs.sort_values('Número de Posiciones Reducidas', ascending=False).head(20)
    fig_dec_abs = px.bar(top_dec_abs, x='Ticker', y='Número de Posiciones Reducidas', title="Top 20 Tickers por Reducción de Posiciones", color_discrete_sequence=['#EF553B'])
    st.plotly_chart(fig_dec_abs)
    with st.expander("Ver datos de posiciones reducidas (absoluto)"):
        st.dataframe(top_dec_abs)

    # Relative (Value)
    st.markdown("#### Por Valor de la Reducción (Relativo - USD)")
    dec_val = decreased_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de la Reducción (Millones USD)')
    top_dec_val = dec_val.sort_values('Valor Total de la Reducción (Millones USD)', ascending=True).head(20)
    fig_dec_val = px.bar(top_dec_val, x='Ticker', y='Valor Total de la Reducción (Millones USD)', title="Top 20 Tickers por Valor de Reducción de Posiciones", color_discrete_sequence=['#EF553B'])
    st.plotly_chart(fig_dec_val)
    with st.expander("Ver datos de posiciones reducidas (valor)"):
        st.dataframe(top_dec_val)

    # Relative (% Market Cap)
    st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
    dec_mc = decreased_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
    top_dec_mc = dec_mc.sort_values('% del Market Cap', ascending=True).head(20)
    fig_dec_mc = px.bar(top_dec_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Reducción de Posiciones en Market Cap", color_discrete_sequence=['#EF553B'])
    fig_dec_mc.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig_dec_mc)
    with st.expander("Ver datos de posiciones reducidas (% market cap)"):
        st.dataframe(top_dec_mc.style.format({'% del Market Cap': '{:.4f}%'}))


    # --- 4. Closed Positions ---
    st.subheader("❌ Top Tickers por Cierre Total de Posiciones")
    closed_positions_df = merged_data[(merged_data['Shares Held'] == 0) & (merged_data['Previous Shares'] > 0)]

    # Absolute
    st.markdown("#### Por Número de Tenedores (Absoluto)")
    closed_abs = closed_positions_df.groupby('Ticker')['Owner Name'].nunique().reset_index(name='Número de Posiciones Cerradas')
    top_closed_abs = closed_abs.sort_values('Número de Posiciones Cerradas', ascending=False).head(20)
    fig_closed_abs = px.bar(top_closed_abs, x='Ticker', y='Número de Posiciones Cerradas', title="Top 20 Tickers por Cierre de Posiciones", color_discrete_sequence=['#d62728'])
    st.plotly_chart(fig_closed_abs)
    with st.expander("Ver datos de posiciones cerradas (absoluto)"):
        st.dataframe(top_closed_abs)

    # Relative (Value)
    st.markdown("#### Por Valor de la Posición Cerrada (Relativo - USD)")
    closed_val = closed_positions_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de Posiciones Cerradas (Millones USD)')
    top_closed_val = closed_val.sort_values('Valor Total de Posiciones Cerradas (Millones USD)', ascending=True).head(20)
    fig_closed_val = px.bar(top_closed_val, x='Ticker', y='Valor Total de Posiciones Cerradas (Millones USD)', title="Top 20 Tickers por Valor de Posiciones Cerradas", color_discrete_sequence=['#d62728'])
    st.plotly_chart(fig_closed_val)
    with st.expander("Ver datos de posiciones cerradas (valor)"):
        st.dataframe(top_closed_val)

    # Relative (% Market Cap)
    st.markdown("#### Por % de Capitalización de Mercado (Relativo - % del Total)")
    closed_mc = closed_positions_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
    top_closed_mc = closed_mc.sort_values('% del Market Cap', ascending=True).head(20)
    fig_closed_mc = px.bar(top_closed_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Impacto de Cierre de Posiciones en Market Cap", color_discrete_sequence=['#d62728'])
    fig_closed_mc.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig_closed_mc)
    with st.expander("Ver datos de posiciones cerradas (% market cap)"):
        st.dataframe(top_closed_mc.style.format({'% del Market Cap': '{:.4f}%'}))



    # --- 5. Cumulative Positive Flow (Buying Pressure) ---
    st.subheader("🟩 Flujo Acumulado Positivo (Presión de Compra)")
    positive_flow_df = merged_data[merged_data['Shares Change'] > 0]

    # By Value
    st.markdown("#### Por Valor Total (USD)")
    pos_flow_val = positive_flow_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de Compra (Millones USD)')
    top_pos_flow_val = pos_flow_val.sort_values('Valor Total de Compra (Millones USD)', ascending=False).head(20)
    fig_pos_flow_val = px.bar(top_pos_flow_val, x='Ticker', y='Valor Total de Compra (Millones USD)', title="Top 20 Tickers por Presión de Compra (Valor)")
    st.plotly_chart(fig_pos_flow_val)
    with st.expander("Ver datos de presión de compra (valor)"):
        st.dataframe(top_pos_flow_val)

    # By % of Market Cap
    st.markdown("#### Por % de Capitalización de Mercado")
    pos_flow_mc = positive_flow_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
    top_pos_flow_mc = pos_flow_mc.sort_values('% del Market Cap', ascending=False).head(20)
    fig_pos_flow_mc = px.bar(top_pos_flow_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Presión de Compra (% Market Cap)")
    fig_pos_flow_mc.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig_pos_flow_mc)
    with st.expander("Ver datos de presión de compra (% market cap)"):
        st.dataframe(top_pos_flow_mc.style.format({'% del Market Cap': '{:.4f}%'}))


    # --- 6. Cumulative Negative Flow (Selling Pressure) ---
    st.subheader("🟥 Flujo Acumulado Negativo (Presión de Venta)")
    negative_flow_df = merged_data[merged_data['Shares Change'] < 0]

    # By Value
    st.markdown("#### Por Valor Total (USD)")
    neg_flow_val = negative_flow_df.groupby('Ticker')['Change in Value'].sum().reset_index(name='Valor Total de Venta (Millones USD)')
    top_neg_flow_val = neg_flow_val.sort_values('Valor Total de Venta (Millones USD)', ascending=True).head(20)
    fig_neg_flow_val = px.bar(top_neg_flow_val, x='Ticker', y='Valor Total de Venta (Millones USD)', title="Top 20 Tickers por Presión de Venta (Valor)", color_discrete_sequence=['#EF553B'])
    st.plotly_chart(fig_neg_flow_val)
    with st.expander("Ver datos de presión de venta (valor)"):
        st.dataframe(top_neg_flow_val)

    # By % of Market Cap
    st.markdown("#### Por % de Capitalización de Mercado")
    neg_flow_mc = negative_flow_df.groupby('Ticker')['Change as % of Market Cap'].sum().reset_index(name='% del Market Cap')
    top_neg_flow_mc = neg_flow_mc.sort_values('% del Market Cap', ascending=True).head(20)
    fig_neg_flow_mc = px.bar(top_neg_flow_mc, x='Ticker', y='% del Market Cap', title="Top 20 Tickers por Presión de Venta (% Market Cap)", color_discrete_sequence=['#EF553B'])
    fig_neg_flow_mc.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig_neg_flow_mc)
    with st.expander("Ver datos de presión de venta (% market cap)"):
        st.dataframe(top_neg_flow_mc.style.format({'% del Market Cap': '{:.4f}%'}))


    # --- 7. Net Institutional Flow ---
    st.subheader("📊 Flujo Neto Institucional (Compra Neta vs. Venta Neta)")
    net_flow_df = merged_data.groupby('Ticker').agg(
        Net_Change_Value=('Change in Value', 'sum'),
        Net_Change_MC=('Change as % of Market Cap', 'sum')
    ).reset_index()

    # Top by Positive Net Flow
    st.markdown("#### Top Tickers por Flujo Neto Positivo (Mayor Entrada de Capital)")
    top_net_positive = net_flow_df.sort_values('Net_Change_Value', ascending=False).head(20)
    fig_net_pos_val = px.bar(top_net_positive, x='Ticker', y='Net_Change_Value', title="Top 20 Tickers por Flujo Neto Positivo (Valor)", color_discrete_sequence=['#00CC96'])
    fig_net_pos_val.update_layout(yaxis_title="Flujo Neto (Millones USD)")
    st.plotly_chart(fig_net_pos_val)
    with st.expander("Ver datos de flujo neto positivo (valor)"):
        st.dataframe(top_net_positive)

    top_net_positive_mc = net_flow_df.sort_values('Net_Change_MC', ascending=False).head(20)
    fig_net_pos_mc = px.bar(top_net_positive_mc, x='Ticker', y='Net_Change_MC', title="Top 20 Tickers por Flujo Neto Positivo (% Market Cap)", color_discrete_sequence=['#00CC96'])
    fig_net_pos_mc.update_layout(yaxis_title="Flujo Neto (% Market Cap)", yaxis_ticksuffix="%")
    st.plotly_chart(fig_net_pos_mc)
    with st.expander("Ver datos de flujo neto positivo (% market cap)"):
        st.dataframe(top_net_positive_mc.style.format({'Net_Change_MC': '{:.4f}%'}))

    # Top by Negative Net Flow
    st.markdown("#### Top Tickers por Flujo Neto Negativo (Mayor Salida de Capital)")
    top_net_negative = net_flow_df.sort_values('Net_Change_Value', ascending=True).head(20)
    fig_net_neg_val = px.bar(top_net_negative, x='Ticker', y='Net_Change_Value', title="Top 20 Tickers por Flujo Neto Negativo (Valor)", color_discrete_sequence=['#d62728'])
    fig_net_neg_val.update_layout(yaxis_title="Flujo Neto (Millones USD)")
    st.plotly_chart(fig_net_neg_val)
    with st.expander("Ver datos de flujo neto negativo (valor)"):
        st.dataframe(top_net_negative)

    top_net_negative_mc = net_flow_df.sort_values('Net_Change_MC', ascending=True).head(20)
    fig_net_neg_mc = px.bar(top_net_negative_mc, x='Ticker', y='Net_Change_MC', title="Top 20 Tickers por Flujo Neto Negativo (% Market Cap)", color_discrete_sequence=['#d62728'])
    fig_net_neg_mc.update_layout(yaxis_title="Flujo Neto (% Market Cap)", yaxis_ticksuffix="%")
    st.plotly_chart(fig_net_neg_mc)
    with st.expander("Ver datos de flujo neto negativo (% market cap)"):
        st.dataframe(top_net_negative_mc.style.format({'Net_Change_MC': '{:.4f}%'}))

elif option == "Análisis Adicional":
    st.header("Análisis Adicional")
    # ... (rest of the code remains the same) ...
    # 2. Market Cap Influence
    st.subheader("Impacto de la Propiedad Institucional en la Capitalización de Mercado")
    ticker_cap_list = sorted(general_data['Ticker'].unique())
    ticker = st.selectbox("Selecciona un Ticker para análisis de capitalización:", ticker_cap_list)
    if ticker:
        ticker_data = merged_data[merged_data['Ticker'] == ticker]
        total_shares = general_data[general_data['Ticker'] == ticker]['Total Shares Outstanding'].iloc[0] * 1e6

        # Use yfinance to get current stock price
        try:
            stock = yf.Ticker(ticker)
            price = stock.info['regularMarketPrice']
            market_cap = price * total_shares
            st.write(f"Precio actual de {ticker}: ${price:.2f}")
            st.write(f"Capitalización de Mercado de {ticker}: ${market_cap / 1e6:.2f} millones")
        except Exception as e:
            st.warning(f"No se pudo obtener el precio actual para {ticker} desde yfinance. Error: {e}")
            st.info(
                f"Usando precio aproximado de los datos cargados: ${general_data[general_data['Ticker'] == ticker]['Price per Share'].iloc[0]:.2f}")
            price = general_data[general_data['Ticker'] == ticker]['Price per Share'].iloc[0]
            market_cap = price * total_shares
            st.write(f"Capitalización de Mercado Aproximada de {ticker}: ${market_cap / 1e6:.2f} millones")

    # Ownership concentration
    st.subheader("Concentración de Propiedad")
    ticker_conc_list = sorted(general_data['Ticker'].unique())
    ticker_conc = st.selectbox("Selecciona un Ticker para análisis de concentración:", ticker_conc_list)
    top_n = st.slider("Selecciona el número de principales tenedores:", 1, 20, 5)
    if ticker_conc:
        ticker_data = merged_data[merged_data['Ticker'] == ticker_conc]
        total_shares = general_data[general_data['Ticker'] == ticker_conc]['Total Shares Outstanding'].iloc[0] * 1e6

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
        pie_data = top_holders[['Owner Name', 'Ownership Percentage']].rename(
            columns={'Ownership Percentage': 'Percentage'})
        pie_data = pd.concat([pie_data,
                              pd.DataFrame({'Owner Name': ['Otros institucionales'],
                                            'Percentage': [other_institutional_percentage]}),
                              pd.DataFrame(
                                  {'Owner Name': ['Otros tenedores'], 'Percentage': [other_holders_percentage]})],
                             ignore_index=True)

        # Create pie chart
        fig = px.pie(pie_data, values='Percentage', names='Owner Name',
                     title=f'Concentración de Propiedad para {ticker_conc}')
        st.plotly_chart(fig)

    # 4. Comparative Analysis Across Tickers
    st.subheader("Comparación Entre Tickers")
    tickers_comp_list = sorted(general_data['Ticker'].unique())
    tickers = st.multiselect("Selecciona los Tickers para comparar (Análisis Adicional):", tickers_comp_list)
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
        category_order = [name for name in simplified_data['Owner Name'].unique() if
                          name != 'Otros institucionales'] + ['Otros institucionales']

        st.write("### Comparación de Métricas por Ticker")
        for metric in ["Shares Held", "Percentage Owned", "Individual Holdings Value"]:
            fig = px.bar(simplified_data, x="Ticker", y=metric, color="Owner Name", barmode="stack",
                         category_orders={"Owner Name": category_order})

            fig.update_layout(title=f"Comparación de {metric} entre Tickers",
                              xaxis_title="Ticker",
                              yaxis_title=metric,
                              legend_title="Tenedores")
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
    filtered_data = merged_data[
        (merged_data['Date'] >= date_range_pandas[0]) & (merged_data['Date'] <= date_range_pandas[1])]
    filtered_data_display = merged_data_display[
        (merged_data_display['Date'] >= date_range_pandas[0]) & (merged_data_display['Date'] <= date_range_pandas[1])]
    filtered_data_display = filtered_data_display.sort_values(by='Shares Change % num', ascending=False)

    num_rows = st.slider("Número de filas a mostrar:", 1, min(1000, len(filtered_data_display)), 100)
    display_df = filtered_data_display.head(num_rows)
    display_cols = ['Date', 'Ticker', 'Owner Name', 'Shares Held', 'Shares Change', 'Shares Change %', 'Individual Holdings Value', 'Change as % of Market Cap']
    styled_df = display_df[display_cols].style.map(color_percentage, subset=["Shares Change %"]).format({'Change as % of Market Cap': '{:.4f}%'})
    st.dataframe(styled_df)

    # 9. Portfolio Analysis for Holders
    st.subheader("Análisis de Cartera para Tenedores")
    holder_port_list = sorted(institutional_holders['Owner Name'].unique())
    holder = st.selectbox("Selecciona un Tenedor para análisis de diversificación:", holder_port_list)
    if holder:
        holder_portfolio = merged_data[merged_data['Owner Name'] == holder]
        st.write(f"### Diversificación de {holder}")
        st.write(f"Número de Tickers Únicos: {holder_portfolio['Ticker'].nunique()}")

        total_holdings_value = holder_portfolio['Individual Holdings Value'].sum()

        if total_holdings_value >= 1e3:
            formatted_value = f"${total_holdings_value / 1e3:.2f} mil millones"
        else:
            formatted_value = f"${total_holdings_value:.2f} millones"

        st.write(f"Valor Total de Tenencias: {formatted_value}")

    # 10. Sentiment Indicator
    st.subheader("Indicador de Sentimiento a través de Tenencias")
    holder_sent_list = sorted(institutional_holders['Owner Name'].unique())
    holder = st.selectbox("Selecciona un Tenedor para análisis de sentimiento:", holder_sent_list)
    if holder:
        holder_sentiment = merged_data[merged_data['Owner Name'] == holder].sort_values('Date')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=holder_sentiment['Date'], y=holder_sentiment['Shares Change'],
                                 mode='lines+markers',
                                 marker=dict(
                                     color=['green' if x > 0 else 'red' for x in holder_sentiment['Shares Change']])))
        fig.update_layout(title=f'Sentimiento de {holder} a través de Cambios en Tenencias', xaxis_title='Fecha',
                          yaxis_title='Cambio en Acciones')
        st.plotly_chart(fig)

        # New: Sentiment with % change
        st.subheader("Indicador de Sentimiento a través de Cambios % en Tenencias")
        holder_sentiment_noinf = holder_sentiment[~np.isinf(holder_sentiment['Shares Change % num'])]
        fig_percent = go.Figure()
        fig_percent.add_trace(
            go.Scatter(x=holder_sentiment_noinf['Date'], y=holder_sentiment_noinf['Shares Change % num'],
                       mode='lines+markers',
                       marker=dict(
                           color=['green' if x > 0 else 'red' for x in holder_sentiment_noinf['Shares Change % num']])))
        fig_percent.update_layout(title=f'Sentimiento de {holder} a través de Cambios % en Tenencias',
                                  xaxis_title='Fecha', yaxis_title='Cambio en Acciones %')
        st.plotly_chart(fig_percent)