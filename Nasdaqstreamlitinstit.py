import streamlit as st
import pandas as pd
import plotly.express as px

# Loading and preprocessing data (same as before)
institutional_holders = pd.read_csv("institutional_holders.csv")
general_data = pd.read_csv("general_data.csv")

institutional_holders["Shares Held"] = institutional_holders["Shares Held"].str.replace(",", "").astype(float)
institutional_holders["Shares Change"] = institutional_holders["Shares Change"].str.replace(",", "").astype(float)
general_data["Total Shares Outstanding"] = general_data["Total Shares Outstanding"].str.replace(",", "").astype(float)
general_data["Total Holdings Value"] = general_data["Total Holdings Value"].str.replace("$", "").str.replace(",", "").astype(float)

merged_data = pd.merge(institutional_holders, general_data, on="Ticker")
merged_data["Percentage Owned"] = (merged_data["Shares Held"] / (merged_data["Total Shares Outstanding"] * 1e6)) * 100

# Streamlit app
st.title("Análisis de Tenencias Institucionales")

# Sidebar for user input
st.sidebar.header("Entrada del Usuario")
option = st.sidebar.radio("Elige una opción:", ["Análisis de Tenedor Institucional", "Análisis por Ticker"])

def plot_top_20(df, x, y, title, color):
    # Sort the DataFrame by 'y' in descending order
    df = df.sort_values(by=y, ascending=False)

    # Take the top 20 and calculate mean for others
    top_20 = df.head(20)
    others = df.iloc[20:][y].mean() if len(df) > 20 else None

    # Add 'Others' to top_20 if there are more than 20 items
    if others is not None:
        others_row = pd.DataFrame({'x': ['Otros - Promedio'], y: [others]})
        others_row.columns = [x, y]
        top_20 = pd.concat([top_20, others_row], ignore_index=True)

    # Plot with Plotly
    fig = px.bar(top_20, x=x, y=y, title=title, color_discrete_sequence=[color])
    fig.update_layout(xaxis_title=x, yaxis_title=y)
    st.plotly_chart(fig)


if option == "Análisis de Tenedor Institucional":
    st.header("Análisis de Tenedor Institucional")

    institutional_holders_list = institutional_holders["Owner Name"].unique()
    selected_holder = st.selectbox("Selecciona un Tenedor Institucional:", institutional_holders_list)

    holder_data = merged_data[merged_data["Owner Name"] == selected_holder]

    if not holder_data.empty:
        st.write(f"### Tenencias de {selected_holder}")
        st.dataframe(holder_data[["Ticker", "Shares Held", "Shares Change", "Percentage Owned"]])

        # Plot for shares held
        st.write("### Acciones Mantenidas por Empresa")
        plot_top_20(holder_data, "Ticker", "Shares Held", f"Acciones Mantenidas por Empresa de {selected_holder}", "skyblue")

        # Plot for percentage owned
        st.write("### Porcentaje de Acciones Propiedad por Empresa")
        plot_top_20(holder_data, "Ticker", "Percentage Owned",
                    f"Porcentaje de Acciones Propiedad por Empresa de {selected_holder}", "lightgreen")
    else:
        st.write("No hay datos disponibles para el tenedor institucional seleccionado.")

elif option == "Análisis por Ticker":
    st.header("Análisis por Ticker")

    tickers_list = general_data["Ticker"].unique()
    selected_ticker = st.selectbox("Selecciona un Ticker:", tickers_list)

    ticker_data = merged_data[merged_data["Ticker"] == selected_ticker]
    general_ticker_data = general_data[general_data["Ticker"] == selected_ticker]

    if not ticker_data.empty:
        st.write(f"### Datos Generales para {selected_ticker}")
        st.write(f"Acciones Totales Emitidas: {general_ticker_data['Total Shares Outstanding'].values[0]:,.0f} millones")
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