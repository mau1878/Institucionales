import streamlit as st
import pandas as pd
from utils.data_processing import preprocess_data
from utils.period import ensure_data_loaded, render_period_selector, render_period_banner, _coverage, _fmt

st.set_page_config(page_title="Análisis de Tenencias Institucionales", layout="wide")

# Carga de datos (se hace una sola vez por sesión; las demás páginas lo reutilizan)
ensure_data_loaded()

# Selector de período global (también se muestra en todas las páginas)
render_period_selector()

st.title("Análisis de Tenencias Institucionales")
st.write("Selecciona una página desde la barra lateral para continuar.")
render_period_banner("snapshot")


# Función para limpiar cache
def clear_preprocess_cache():
    """Borra forzosamente el cache de preprocess_data."""
    preprocess_data.clear()
    for key in ("merged_data", "merged_data_display", "unique_dates", "_coverage"):
        st.session_state.pop(key, None)
    st.success("Cache de datos forzadamente borrado. Los datos se regenerarán al recargar.")


# Botón para limpiar cache
if st.button("Regenerar datos"):
    clear_preprocess_cache()

st.subheader("Fechas de reporte disponibles")
st.write(
    "Cada fecha corresponde al cierre de un trimestre. El 13-F se presenta hasta 45 días después, "
    "por lo que las fechas más recientes pueden estar incompletas."
)
cov = _coverage().rename_axis("Fecha de reporte").reset_index()
cov["Fecha de reporte"] = cov["Fecha de reporte"].map(_fmt)
st.dataframe(cov, hide_index=True, use_container_width=True)
