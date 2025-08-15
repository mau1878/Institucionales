import streamlit as st
import pandas as pd
from utils.data_processing import load_data, get_market_caps, preprocess_data

st.set_page_config(page_title="Análisis de Tenencias Institucionales", layout="wide")
st.header("POR FAVOR ESPERAR A QUE SE CARGUEN LOS DATOS Y SE DIGA QUE SE CARGARON CON ÉXITO!!!")
# Initialize session state for data
if 'merged_data' not in st.session_state:
    try:
        with st.spinner('Cargando datos...'):
            institutional_holders, general_data = load_data()
            if institutional_holders.empty or general_data.empty:
                raise ValueError("Uno o ambos archivos parquet están vacíos.")
            live_market_caps = get_market_caps(general_data['Ticker'].unique())
            merged_data, merged_data_display = preprocess_data(institutional_holders, general_data, live_market_caps)
            st.session_state.merged_data = merged_data
            st.session_state.merged_data_display = merged_data_display
            st.session_state.unique_dates = sorted(merged_data['Date'].dt.date.unique())
            st.success("Datos cargados con éxito.")
    except FileNotFoundError as e:
        st.error(f"Error: No se encontraron los archivos parquet. Asegúrate de que 'institutional_holders.parquet' y 'general_data.parquet' estén en el directorio raíz. Detalles: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        st.stop()

# Global date filter
try:
    st.sidebar.header("Filtro por Fecha")
    selected_date = st.sidebar.selectbox(
        "Selecciona una Fecha (opcional):",
        [None] + st.session_state.unique_dates,
        key='global_date_filter'
    )
    st.session_state.selected_date = pd.to_datetime(selected_date) if selected_date else None
except KeyError:
    st.error("No se pudieron cargar las fechas únicas. Los datos no están inicializados correctamente.")
    st.stop()

st.title("Análisis de Tenencias Institucionales")
st.write("Selecciona una página desde la barra lateral para continuar.")