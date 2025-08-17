import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3

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
    st.plotly_chart(fig, use_container_width=True)

def plot_changes(df, x, y_num, title, is_percentage=False):
    plot_df = df[~np.isinf(df[y_num])].copy()
    plot_df = plot_df.sort_values(by=y_num, ascending=False)
    top_20 = plot_df.head(20)

    colors = ['green' if val > 0 else 'red' if val < 0 else 'grey' for val in top_20[y_num]]

    fig = go.Figure(data=[go.Bar(x=top_20[x], y=top_20[y_num], marker_color=colors)])
    fig.update_layout(title=title, xaxis_title=x, yaxis_title='Shares Change %' if is_percentage else 'Shares Change')
    st.plotly_chart(fig, use_container_width=True)

def plot_venn_like_comparison(item_list, comparison_field, data):
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
        common = s1.intersection(s2)
        unique1 = s1.difference(s2)
        unique2 = s2.difference(s1)
        c1, c2, c_common = len(unique1), len(unique2), len(common)

        if c1 == 0 and c2 == 0 and c_common == 0:
            st.write("No hay datos de coincidencia para mostrar.")
            return

        total1, total2 = len(s1), len(s2)
        max_total = max(total1, total2, 1)
        r1 = math.sqrt(total1 / max_total)
        r2 = math.sqrt(total2 / max_total)

        x1, y1 = -r1 / 2, 0
        x2, y2 = r2 / 2, 0

        fig.add_shape(type="circle", xref="x", yref="y", x0=x1 - r1, y0=y1 - r1, x1=x1 + r1, y1=y1 + r1,
                      fillcolor=colors[0], opacity=opacity, line_color=colors[0])
        fig.add_shape(type="circle", xref="x", yref="y", x0=x2 - r2, y0=y2 - r2, x1=x2 + r2, y1=y2 + r2,
                      fillcolor=colors[1], opacity=opacity, line_color=colors[1])

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

        s1_only = s1 - s2 - s3
        s2_only = s2 - s1 - s3
        s3_only = s3 - s1 - s2
        s1_s2 = (s1 & s2) - s3
        s1_s3 = (s1 & s3) - s2
        s2_s3 = (s2 & s3) - s1
        s1_s2_s3 = s1 & s2 & s3

        counts = {k: len(v) for k, v in locals().items() if k.startswith('s')}

        total1, total2, total3 = len(s1), len(s2), len(s3)
        max_total = max(total1, total2, total3, 1)
        r1 = math.sqrt(total1 / max_total) * 0.8
        r2 = math.sqrt(total2 / max_total) * 0.8
        r3 = math.sqrt(total3 / max_total) * 0.8

        x1, y1 = 0, r1 * 0.6
        x2, y2 = -r2 * 0.5, -r2 * 0.3
        x3, y3 = r3 * 0.5, -r3 * 0.3

        fig.add_shape(type="circle", x0=x1 - r1, y0=y1 - r1, x1=x1 + r1, y1=y1 + r1, fillcolor=colors[0],
                      opacity=opacity, line_color=colors[0])
        fig.add_shape(type="circle", x0=x2 - r2, y0=y2 - r2, x1=x2 + r2, y1=y2 + r2, fillcolor=colors[1],
                      opacity=opacity, line_color=colors[1])
        fig.add_shape(type="circle", x0=x3 - r3, y0=y3 - r3, x1=x3 + r3, y1=y3 + r3, fillcolor=colors[2],
                      opacity=opacity, line_color=colors[2])

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
            st.write(f"**Común entre {n1} y {n2} ({counts['s1_s2']}):** {', '.join(list(s1_s2)) if s1_s2 else 'Ninguno'}")
            st.write(f"**Común entre {n1} y {n3} ({counts['s1_s3']}):** {', '.join(list(s1_s3)) if s1_s3 else 'Ninguno'}")
            st.write(f"**Común entre {n2} y {n3} ({counts['s2_s3']}):** {', '.join(list(s2_s3)) if s2_s3 else 'Ninguno'}")
            st.write(f"**Común entre los tres ({counts['s1_s2_s3']}):** {', '.join(list(s1_s2_s3)) if s1_s2_s3 else 'Ninguno'}")

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
    fig.add_annotation(
        text="M Taurus - X: @mtaurus_ok",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=30, color="rgba(0,0,0,0.2)"),
        textangle=-30,
        xanchor="center",
        yanchor="middle",
        opacity=0.2
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_matplotlib_venn(item_list, comparison_field, data):
    num_items = len(item_list)
    if not (2 <= num_items <= 3):
        st.warning("La comparación con diagramas de Venn proporcionales solo admite 2 o 3 elementos.")
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

    fig, ax = plt.subplots(figsize=(10, 7))
    if num_items == 2:
        venn2(subsets=sets, set_labels=set_labels, ax=ax)
    elif num_items == 3:
        venn3(subsets=sets, set_labels=set_labels, ax=ax)

    ax.set_title(title)

    # 🔹 Add diagonal watermark
    ax.text(
        0.5, 0.5, "M Taurus - X: @mtaurus_ok",
        transform=ax.transAxes,
        fontsize=30,
        color="gray",
        alpha=0.3,
        ha="center",
        va="center",
        rotation=30,
        zorder=10
    )

    st.pyplot(fig)
