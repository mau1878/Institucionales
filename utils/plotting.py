import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3

# === Gráfico top 20 barras ===
def plot_top_20(df, x, y, title, color):
    df = df.sort_values(by=y, ascending=False)
    top_20 = df.head(20)
    others = df.iloc[20:][y].mean() if len(df) > 20 else None

    if others is not None:
        others_row = pd.DataFrame({x: ['Otros - Promedio'], y: [others]})
        top_20 = pd.concat([top_20, others_row], ignore_index=True)

    fig = px.bar(top_20, x=x, y=y, title=title, color_discrete_sequence=[color])
    fig.update_layout(xaxis_title=x, yaxis_title=y)
    st.plotly_chart(fig, use_container_width=True)

# === Gráfico de cambios ===
def plot_changes(df, x, y_num, title, is_percentage=False):
    plot_df = df[~np.isinf(df[y_num])].copy()
    plot_df = plot_df.sort_values(by=y_num, ascending=False)
    top_20 = plot_df.head(20)
    colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in top_20[y_num]]
    fig = go.Figure(data=[go.Bar(x=top_20[x], y=top_20[y_num], marker_color=colors)])
    fig.update_layout(title=title, xaxis_title=x, yaxis_title='Shares Change %' if is_percentage else 'Shares Change')
    st.plotly_chart(fig, use_container_width=True)

# === Diagrama tipo Venn con Plotly ===
def plot_venn_like_comparison(item_list, comparison_field, data):
    num_items = len(item_list)
    if not (2 <= num_items <= 3):
        st.warning("Seleccione 2 o 3 elementos para el diagrama de Venn.")
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
        n1, n2 = item_list
        common = s1 & s2
        unique1, unique2 = s1 - s2, s2 - s1
        c1, c2, c_common = len(unique1), len(unique2), len(common)

        if c1 == 0 and c2 == 0 and c_common == 0:
            st.write("No hay datos de coincidencia para mostrar.")
            return

        total1, total2 = len(s1), len(s2)
        max_total = max(total1, total2, 1)
        r1, r2 = math.sqrt(total1 / max_total), math.sqrt(total2 / max_total)
        x1, y1, x2, y2 = -r1/2, 0, r2/2, 0

        fig.add_shape(type="circle", x0=x1-r1, y0=y1-r1, x1=x1+r1, y1=y1+r1, fillcolor=colors[0], opacity=opacity, line_color=colors[0])
        fig.add_shape(type="circle", x0=x2-r2, y0=y2-r2, x1=x2+r2, y1=y2+r2, fillcolor=colors[1], opacity=opacity, line_color=colors[1])

        fig.add_annotation(x=x1, y=y1, text=f"<b>{c1}</b>", showarrow=False, font=dict(size=20, color="white"))
        fig.add_annotation(x=x2, y=y2, text=f"<b>{c2}</b>", showarrow=False, font=dict(size=20, color="white"))
        if c_common > 0:
            fig.add_annotation(x=(x1+x2)/2, y=(y1+y2)/2, text=f"<b>{c_common}</b>", showarrow=False, font=dict(size=20, color="white"))
        fig.add_annotation(x=x1, y=y1+r1+0.1, text=f"<b>{n1}</b>", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=x2, y=y2+r2+0.1, text=f"<b>{n2}</b>", showarrow=False, font=dict(size=14))

        with st.expander("Ver listas de entidades detalladas"):
            st.write(f"**Solo en {n1} ({c1}):** {', '.join(list(unique1)) if unique1 else 'Ninguno'}")
            st.write(f"**Solo en {n2} ({c2}):** {', '.join(list(unique2)) if unique2 else 'Ninguno'}")
            st.write(f"**En Común ({c_common}):** {', '.join(list(common)) if common else 'Ninguno'}")

    elif num_items == 3:
        s1, s2, s3 = sets
        n1, n2, n3 = item_list
        s1_only = s1 - s2 - s3
        s2_only = s2 - s1 - s3
        s3_only = s3 - s1 - s2
        s1_s2 = (s1 & s2) - s3
        s1_s3 = (s1 & s3) - s2
        s2_s3 = (s2 & s3) - s1
        s1_s2_s3 = s1 & s2 & s3
        counts = {'s1_only': len(s1_only), 's2_only': len(s2_only), 's3_only': len(s3_only),
                  's1_s2': len(s1_s2), 's1_s3': len(s1_s3), 's2_s3': len(s2_s3), 's1_s2_s3': len(s1_s2_s3)}

        r1 = math.sqrt(len(s1)/max(len(s1), len(s2), len(s3), 1))*0.8
        r2 = math.sqrt(len(s2)/max(len(s1), len(s2), len(s3), 1))*0.8
        r3 = math.sqrt(len(s3)/max(len(s1), len(s2), len(s3), 1))*0.8
        x1, y1, x2, y2, x3, y3 = 0, r1*0.6, -r2*0.5, -r2*0.3, r3*0.5, -r3*0.3
        fig.add_shape(type="circle", x0=x1-r1, y0=y1-r1, x1=x1+r1, y1=y1+r1, fillcolor=colors[0], opacity=opacity, line_color=colors[0])
        fig.add_shape(type="circle", x0=x2-r2, y0=y2-r2, x1=x2+r2, y1=y2+r2, fillcolor=colors[1], opacity=opacity, line_color=colors[1])
        fig.add_shape(type="circle", x0=x3-r3, y0=y3-r3, x1=x3+r3, y1=y3+r3, fillcolor=colors[2], opacity=opacity, line_color=colors[2])

        # Anotaciones contables
        fig.add_annotation(x=0, y=y1+r1/2, text=f"<b>{counts['s1_only']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=x2, y=y2, text=f"<b>{counts['s2_only']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=x3, y=y3, text=f"<b>{counts['s3_only']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=(x1+x2)/2, y=(y1+y2)/2, text=f"<b>{counts['s1_s2']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=(x1+x3)/2, y=(y1+y3)/2, text=f"<b>{counts['s1_s3']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=(x2+x3)/2, y=(y2+y3)/2, text=f"<b>{counts['s2_s3']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=0, y=0, text=f"<b>{counts['s1_s2_s3']}</b>", showarrow=False, font=dict(size=18,color="white"))
        fig.add_annotation(x=x1, y=y1+r1+0.1, text=f"<b>{n1}</b>", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=x2-r2-0.1, y=y2, text=f"<b>{n2}</b>", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=x3+r3+0.1, y=y3, text=f"<b>{n3}</b>", showarrow=False, font=dict(size=14))

        with st.expander("Ver listas de entidades detalladas"):
            st.write(f"**Solo en {n1} ({counts['s1_only']}):** {', '.join(list(s1_only)) if s1_only else 'Ninguno'}")
            st.write(f"**Solo en {n2} ({counts['s2_only']}):** {', '.join(list(s2_only)) if s2_only else 'Ninguno'}")
            st.write(f"**Solo en {n3} ({counts['s3_only']}):** {', '.join(list(s3_only)) if s3_only else 'Ninguno'}")
            st.write(f"**Común entre {n1} y {n2} ({counts['s1_s2']}):** {', '.join(list(s1_s2)) if s1_s2 else 'Ninguno'}")
            st.write(f"**Común entre {n1} y {n3} ({counts['s1_s3']}):** {', '.join(list(s1_s3)) if s1_s3 else 'Ninguno'}")
            st.write(f"**Común entre {n2} y {n3} ({counts['s2_s3']}):** {', '.join(list(s2_s3)) if s2_s3 else 'Ninguno'}")
            st.write(f"**Común entre los tres ({counts['s1_s2_s3']}):** {', '.join(list(s1_s2_s3)) if s1_s2_s3 else 'Ninguno'}")

    fig.update_layout(
        title_text=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2,2]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5,2]),
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=500,
        margin=dict(t=80,b=20,l=20,r=20)
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.add_annotation(text="M Taurus - X: @mtaurus_ok", xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=30,color="rgba(0,0,0,0.2)"), textangle=-30,
                       xanchor="center", yanchor="middle", opacity=0.2)
    st.plotly_chart(fig, use_container_width=True)

# === Diagramas de Venn con matplotlib ===
def plot_matplotlib_venn(item_list, comparison_field, data):
    num_items = len(item_list)
    if not (2 <= num_items <= 3):
        st.warning("La comparación con diagramas de Venn solo admite 2 o 3 elementos.")
        return

    if comparison_field == 'Ticker':
        entity_field = 'Owner Name'
        title_entities = "Tenedores Institucionales"
    else:
        entity_field = 'Ticker'
        title_entities = "Tickers"

    title = f"Coincidencia Proporcional de {title_entities} entre {', '.join(item_list)}"
    sets = [set(data[data[comparison_field] == item][entity_field].unique()) for item in item_list]
    set_labels = item_list

    fig, ax = plt.subplots(figsize=(10,7))
    if num_items == 2:
        venn2(subsets=sets, set_labels=set_labels, ax=ax)
    elif num_items == 3:
        venn3(subsets=sets, set_labels=set_labels, ax=ax)
    ax.set_title(title)

    # Marca de agua
    ax.text(0.5,0.5,"M Taurus - X: @mtaurus_ok",transform=ax.transAxes,
            fontsize=30,color="gray",alpha=0.3,ha="center",va="center",rotation=30,zorder=10)
    st.pyplot(fig)

# === Sectores/industrias ===
def plot_sector_industry(df, group_field, value_field="Valor Total (USD millones)", color="blue"):
    plot_top_20(df.reset_index(), x=group_field, y=value_field, title=f"Top {group_field}", color=color)
    top_10 = df.head(10)
    others_value = df.iloc[10:][value_field].sum() if len(df) > 10 else 0
    pie_labels = list(top_10.index) + (["Otros"] if others_value>0 else [])
    pie_values = list(top_10[value_field]) + ([others_value] if others_value>0 else [])
    fig = px.pie(names=pie_labels, values=pie_values,
                 title=f"Distribución de {group_field} por Valor Total en holdings institucionales",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# === Composición de cartera de un tenedor ===
def plot_holder_composition(merged_data, holder_name, group_field="Sector"):
    holder_data = merged_data[merged_data["Owner Name"]==holder_name]
    if holder_data.empty:
        st.warning(f"No hay datos para el tenedor {holder_name}")
        return
    holder_group = holder_data.groupby(group_field)["Individual Holdings Value"].sum().reset_index().sort_values("Individual Holdings Value", ascending=False)
    fig = px.pie(holder_group, names=group_field, values="Individual Holdings Value", title=f"Composición de cartera de {holder_name} por {group_field}", hole=0.3)
    st.plotly_chart(fig, use_container_width=True)

# === Distribución de holdings por tenedor ===
def plot_holder_distribution(merged_data, group_field):
    """
    Gráfico de barras apiladas: porcentaje de holdings de cada tenedor por sector/industria
    """
    if merged_data.empty:
        st.warning("No hay datos disponibles para la distribución de tenedores.")
        return

    pivot = merged_data.pivot_table(
        index='Owner Name',
        columns=group_field,
        values='Individual Holdings Value',
        aggfunc='sum',
        fill_value=0
    )
    if pivot.empty:
        st.warning("No hay datos después de pivotar para la distribución de tenedores.")
        return

    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig = px.bar(
        pivot_pct,
        x=pivot_pct.index,
        y=pivot_pct.columns,
        title=f"Distribución de holdings por tenedor según {group_field}",
        labels={"value": "% del portafolio", "Owner Name": "Tenedor"},
        height=600
    )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig, use_container_width=True)
    st.write("✅ plot_holder_distribution ejecutada")

def plot_holders_heatmap(merged_data, group_field):
    """
    Heatmap: filas = tenedores, columnas = sector/industria, valores = % de holdings
    """
    if merged_data.empty:
        st.warning("No hay datos disponibles para el heatmap de tenedores.")
        return

    pivot = merged_data.pivot_table(
        index='Owner Name',
        columns=group_field,
        values='Individual Holdings Value',
        aggfunc='sum',
        fill_value=0
    )
    if pivot.empty:
        st.warning("No hay datos después de pivotar para el heatmap de tenedores.")
        return

    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig = px.imshow(
        pivot_pct,
        labels=dict(x=group_field, y="Tenedor", color="% Holdings"),
        x=pivot_pct.columns,
        y=pivot_pct.index,
        aspect="auto",
        color_continuous_scale="RdYlGn"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.write("✅ plot_holders_heatmap ejecutada")

def plot_market_concentration(merged_data, group_field, top_n=5):
    """
    Muestra top N tenedores que concentran más del X% de cada sector/industria
    """
    if merged_data.empty:
        st.warning("No hay datos disponibles para concentración de mercado.")
        return

    df = merged_data.copy()
    df["Pct of Group"] = df.groupby(group_field)["Individual Holdings Value"].transform(
        lambda x: x / x.sum() * 100 if x.sum() != 0 else 0
    )

    top_holders = df.groupby([group_field, "Owner Name"])["Pct of Group"].sum().reset_index()
    if top_holders.empty:
        st.warning("No hay datos para top holders después de agrupar.")
        return

    top_holders = top_holders.sort_values(["Pct of Group"], ascending=False)
    fig = px.bar(
        top_holders.head(top_n*len(top_holders[group_field].unique())),
        x="Owner Name",
        y="Pct of Group",
        color=group_field,
        title=f"Top {top_n} tenedores por {group_field} (concentración de mercado)"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.write("✅ plot_market_concentration ejecutada")

def plot_multiple_holders_comparison(merged_data, selected_holders, group_field):
    """
    Comparación sectorial entre varios tenedores
    """
    if merged_data.empty:
        st.warning("No hay datos disponibles para comparar tenedores.")
        return

    df = merged_data[merged_data["Owner Name"].isin(selected_holders)]
    if df.empty:
        st.warning("No hay datos para los tenedores seleccionados.")
        return

    pivot = df.pivot_table(
        index="Owner Name",
        columns=group_field,
        values="Individual Holdings Value",
        aggfunc='sum',
        fill_value=0
    )
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    fig = px.bar(
        pivot_pct,
        x=pivot_pct.index,
        y=pivot_pct.columns,
        title="Comparación sectorial entre tenedores",
        labels={"value": "% del portafolio", "Owner Name": "Tenedor"},
        height=600
    )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig, use_container_width=True)
    st.write("✅ plot_multiple_holders_comparison ejecutada")
