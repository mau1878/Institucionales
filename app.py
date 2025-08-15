import streamlit as st
from utils.data_processing import load_data, get_market_caps, preprocess_data

# Set page configuration
st.set_page_config(page_title="Análisis de Tenencias Institucionales", layout="wide")

# Initialize session state for data
if 'merged_data' not in st.session_state:
    with st.spinner('Cargando datos...'):
        institutional_holders, general_data = load_data()
        live_market_caps = get_market_caps(general_data['Ticker'].unique())
        merged_data, merged_data_display = preprocess_data(institutional_holders, general_data, live_market_caps)
        st.session_state.merged_data = merged_data
        st.session_state.merged_data_display = merged_data_display
        st.session_state.unique_dates = sorted(merged_data['Date'].dt.date.unique())

# Global date filter
st.sidebar.header("Filtro por Fecha")
selected_date = st.sidebar.selectbox(
    "Selecciona una Fecha (opcional):",
    [None] + st.session_state.unique_dates,
    key='global_date_filter'
)
st.session_state.selected_date = pd.to_datetime(selected_date) if selected_date else None

st.title("Análisis de Tenencias Institucionales")
st.write("Selecciona una página desde la barra lateral para continuar.")