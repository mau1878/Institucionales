"""
Manejo centralizado del período de datos (fechas de reporte 13-F).

Todas las páginas llaman a `setup_page()`, que:
  1. carga los datos si hace falta (también al entrar directo a una página),
  2. dibuja el selector de período en la barra lateral (igual en toda la app),
  3. devuelve los datos ya filtrados al período elegido.

Dos modos de agregación según el tipo de análisis:
  - mode="snapshot": una fila por (Ticker, Tenedor). Las variables de stock
    (acciones, valor, % propiedad) toman el último dato dentro del período y las
    de flujo (cambio en acciones / valor / % market cap) se acumulan en el período.
  - mode="events": una fila por (Ticker, Tenedor, Fecha). Sirve para rankings que
    cuentan eventos de cada trimestre (altas, bajas, aumentos, reducciones).
"""
import numpy as np
import pandas as pd
import streamlit as st

from utils.data_processing import load_data, get_market_caps, preprocess_data

_CANON_KEY = "period_range"        # valor canónico (inicio, fin); sobrevive al cambio de página
_START_KEY = "period_start_widget"  # estado de los widgets (se re-sincronizan en cada página)
_END_KEY = "period_end_widget"
_FLOW_COLS = ["Shares Change", "Change in Value", "Change as % of Market Cap"]


# ---------------------------------------------------------------- carga de datos
def ensure_data_loaded():
    """Carga los datos en session_state si todavía no están (cualquier página)."""
    if "merged_data" in st.session_state and "unique_dates" in st.session_state:
        return
    try:
        with st.spinner("Cargando datos..."):
            holders, general = load_data()
            if holders.empty or general.empty:
                raise ValueError("Uno o ambos archivos parquet están vacíos.")
            caps = get_market_caps(general["Ticker"].unique())
            merged, merged_display = preprocess_data(holders, general, caps)
            st.session_state.merged_data = merged
            st.session_state.merged_data_display = merged_display
            st.session_state.unique_dates = sorted(merged["Date"].dt.date.unique())
    except FileNotFoundError as e:
        st.error(
            "No se encontraron los archivos parquet. Asegúrate de que "
            f"'institutional_holders.parquet' y 'general_data_with_info.parquet' estén en el directorio raíz. Detalles: {e}"
        )
        st.stop()
    except Exception as e:  # noqa: BLE001
        st.error(f"Error al cargar los datos: {e}")
        st.stop()


# ------------------------------------------------------------- estado del período
def _fmt(d) -> str:
    return pd.Timestamp(d).strftime("%d/%m/%Y")


def _dates():
    return list(st.session_state.unique_dates)


def _coverage() -> pd.DataFrame:
    """Filas, tenedores y tickers por fecha de reporte (sobre datos sin filtrar)."""
    if "_coverage" not in st.session_state:
        df = st.session_state.merged_data
        cov = df.groupby(df["Date"].dt.date).agg(
            Registros=("Ticker", "size"),
            Tenedores=("Owner Name", "nunique"),
            Tickers=("Ticker", "nunique"),
        )
        st.session_state["_coverage"] = cov
    return st.session_state["_coverage"]


def get_period():
    """Devuelve (inicio, fin) como datetime.date del período activo."""
    dates = _dates()
    start, end = st.session_state.get(_CANON_KEY, (dates[0], dates[-1]))
    if start not in dates or end not in dates:  # los datos cambiaron
        start, end = dates[0], dates[-1]
    return start, end


def period_dates():
    start, end = get_period()
    return [d for d in _dates() if start <= d <= end]


def period_label() -> str:
    """Texto corto con el período activo, para títulos de gráficos y encabezados."""
    ds = period_dates()
    if len(ds) == 1:
        return f"Reporte al {_fmt(ds[0])}"
    return f"Reportes del {_fmt(ds[0])} al {_fmt(ds[-1])} ({len(ds)} fechas)"


def _set_period(start, end):
    st.session_state[_CANON_KEY] = (start, end)
    st.session_state[_START_KEY] = start
    st.session_state[_END_KEY] = end


def _on_start_change():
    start, end = st.session_state[_START_KEY], st.session_state[_END_KEY]
    _set_period(start, max(start, end))  # si el inicio pasa al fin, el fin lo sigue


def _on_end_change():
    start, end = st.session_state[_START_KEY], st.session_state[_END_KEY]
    _set_period(min(start, end), end)  # si el fin queda antes del inicio, el inicio lo sigue


def render_period_selector():
    """Selector de período en la barra lateral. Se muestra igual en todas las páginas."""
    dates = _dates()
    if _CANON_KEY not in st.session_state:
        st.session_state[_CANON_KEY] = (dates[0], dates[-1])
    # Re-sincroniza los widgets con el valor canónico (pierden estado al cambiar de página)
    start, end = get_period()
    st.session_state[_START_KEY] = start
    st.session_state[_END_KEY] = end

    sb = st.sidebar
    sb.header("📅 Período de datos")
    c_from, c_to = sb.columns(2)
    c_from.selectbox("Desde:", dates, key=_START_KEY, format_func=_fmt, on_change=_on_start_change,
                     help="Primera fecha de reporte (13-F) a incluir. Para ver una sola fecha, elegí la misma en Desde y Hasta.")
    c_to.selectbox("Hasta:", dates, key=_END_KEY, format_func=_fmt, on_change=_on_end_change,
                   help="Última fecha de reporte (13-F) a incluir. El período se aplica a todas las secciones de la app.")
    b1, b2 = sb.columns(2)
    b1.button("Último", use_container_width=True, on_click=_set_period, args=(dates[-1], dates[-1]),
              help="Solo la fecha de reporte más reciente")
    b2.button("Todo", use_container_width=True, on_click=_set_period, args=(dates[0], dates[-1]),
              help="Todas las fechas de reporte disponibles")

    sb.caption(f"**Mostrando:** {period_label()}")
    with sb.expander("Cobertura por fecha de reporte"):
        st.dataframe(
            _coverage().rename_axis("Fecha").reset_index().assign(
                Fecha=lambda d: d["Fecha"].map(_fmt)
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Algunas fechas tienen muchos menos tenedores que otras (p. ej. las más recientes, "
                   "porque los fondos presentan el 13-F hasta 45 días después del cierre del trimestre).")


# ------------------------------------------------------------------- agregación
def _format_change_pct(x):
    if np.isinf(x):
        return "New Position"
    return f"{x:.2f}%" if not np.isnan(x) else "N/A"


def _filter_dates(df: pd.DataFrame, start, end) -> pd.DataFrame:
    d = df["Date"].dt.date
    return df[(d >= start) & (d <= end)]


@st.cache_data(show_spinner=False)
def _collapse(_df: pd.DataFrame, start, end, data_key):
    """Una fila por (Ticker, Tenedor): stock = último dato del período; flujo = suma en el período."""
    sub = _filter_dates(_df, start, end).sort_values("Date")
    keys = ["Ticker", "Owner Name"]
    out = sub.groupby(keys, sort=False).tail(1).set_index(keys)
    g = sub.groupby(keys, sort=False)
    for col in _FLOW_COLS:
        out[col] = g[col].sum()
    first = g.head(1).set_index(keys)
    out["Previous Shares"] = first["Shares Held"] - first["Shares Change"]
    out["First Date"] = first["Date"]
    out = out.reset_index()
    out["Shares Change %"] = np.where(
        out["Previous Shares"] != 0, out["Shares Change"] / out["Previous Shares"] * 100, np.inf
    )
    out["Shares Change % num"] = out["Shares Change %"]
    display = out.copy()
    display["Shares Change %"] = display["Shares Change %"].apply(_format_change_pct)
    return out, display


def get_period_data(mode: str = "snapshot"):
    """(merged_data, merged_data_display) del período activo. Ver docstring del módulo."""
    start, end = get_period()
    md = st.session_state.merged_data
    mdd = st.session_state.merged_data_display
    if mode == "events":
        return _filter_dates(md, start, end), _filter_dates(mdd, start, end)
    key = (len(md), str(md["Date"].max()))
    return _collapse(md, start, end, key)


# ---------------------------------------------------------------------- UI helpers
def render_period_banner(mode: str = "snapshot", extra: str | None = None):
    """Aviso visible al comienzo de cada sección con las fechas que se están mostrando."""
    ds = period_dates()
    cov = _coverage()
    if len(ds) == 1:
        head = f"📅 **Datos mostrados:** reporte 13-F al **{_fmt(ds[0])}**."
    else:
        head = (f"📅 **Datos mostrados:** reportes 13-F del **{_fmt(ds[0])}** al **{_fmt(ds[-1])}** "
                f"({len(ds)} fechas: {', '.join(_fmt(d) for d in ds)}).")
    if mode == "events":
        how = ("Los eventos (aperturas, aumentos, reducciones, cierres y flujos) de **cada fecha de reporte** "
               "dentro del período se suman.")
    else:
        how = ("Las tenencias (acciones, valor, % de propiedad) corresponden a la **última fecha del período**; "
               "los cambios se **acumulan** dentro del período.")
    st.info(" ".join([head, how] + ([extra] if extra else [])) + " Podés cambiar el período en la barra lateral.")

    # Aviso de cobertura parcial (fechas con muchos menos tenedores que el máximo histórico)
    max_h = cov["Tenedores"].max()
    partial = [d for d in ds if cov.loc[d, "Tenedores"] < 0.25 * max_h]
    if partial:
        st.warning(
            "⚠️ Cobertura parcial en: "
            + ", ".join(f"{_fmt(d)} ({int(cov.loc[d, 'Tenedores'])} tenedores vs. máx. {int(max_h)})" for d in partial)
            + ". Los resultados para esas fechas pueden no ser representativos."
        )


def show_chart(fig, **kwargs):
    """st.plotly_chart que agrega el período activo como subtítulo del gráfico."""
    kwargs.setdefault("use_container_width", True)
    try:
        title = fig.layout.title.text
        label = period_label()
        if title and label not in title:
            fig.update_layout(title_text=f"{title}<br><sup>📅 {label}</sup>")
    except Exception:  # noqa: BLE001
        pass
    st.plotly_chart(fig, **kwargs)


def setup_page(mode: str = "snapshot", extra: str | None = None):
    """Arranque común de cada página. Devuelve (merged_data, merged_data_display) del período."""
    ensure_data_loaded()
    render_period_selector()
    render_period_banner(mode, extra)
    return get_period_data(mode)
