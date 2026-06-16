import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analytics import get_global_stats, get_figure_stats, get_all_data
from figures import FIGURES

st.set_page_config(page_title="Museo Digital - Analytics", page_icon="\U0001f3db", layout="wide")

st.markdown("""
<style>
    .main { background: #0B0B0F; }
    .stMetric { background: #13131A; border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1rem; }
    .stMetric label { color: #8A8490 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #C9953C !important; }
    h1, h2, h3 { color: #F0EDE8 !important; }
    .stTabs [data-baseweb="tab"] { color: #8A8490; }
    .stTabs [aria-selected="true"] { color: #C9953C !important; }
</style>
""", unsafe_allow_html=True)

st.title("\U0001f3db Museo Digital - Dashboard")
st.markdown("---")

global_stats = get_global_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Conversaciones", global_stats["total_conversations"])
with col2:
    st.metric("Hoy", global_stats["today_count"])
with col3:
    st.metric("Personajes Activos", len(global_stats["figures_used"]))
with col4:
    most = global_stats["most_active"] or "N/A"
    emoji = FIGURES.get(most, {}).get("emoji", "")
    st.metric("Mas Consultado", f"{emoji} {most}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Por Personaje", "Actividad", "Preguntas"])

with tab1:
    fig_names = list(FIGURES.keys())
    selected = st.selectbox("Seleccionar personaje", fig_names)

    stats = get_figure_stats(selected)
    fig_data = FIGURES[selected]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Conversaciones", stats["total"])
    with c2:
        st.metric("Tiempo Respuesta (ms)", stats["avg_response_time"])
    with c3:
        st.metric("Palabras/Pregunta", stats["avg_question_length"])
    with c4:
        st.metric("Caracteres/Respuesta", stats["avg_response_length"])

    if stats["by_date"]:
        df_date = pd.DataFrame(list(stats["by_date"].items()), columns=["Fecha", "Conversaciones"])
        df_date["Fecha"] = pd.to_datetime(df_date["Fecha"])
        df_date = df_date.sort_values("Fecha")

        fig_bar = px.bar(
            df_date, x="Fecha", y="Conversaciones",
            title=f"Conversaciones por da - {selected}",
            color_discrete_sequence=["#C9953C"],
        )
        fig_bar.update_layout(
            plot_bgcolor="#13131A", paper_bgcolor="#0B0B0F",
            font_color="#F0EDE8", title_font_color="#C9953C",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    if stats["by_hour"]:
        df_hour = pd.DataFrame(list(stats["by_hour"].items()), columns=["Hora", "Conversaciones"])
        df_hour = df_hour.sort_values("Hora")

        fig_hour = px.line(
            df_hour, x="Hora", y="Conversaciones",
            title=f"Actividad por hora - {selected}",
            markers=True,
            color_discrete_sequence=["#C9953C"],
        )
        fig_hour.update_layout(
            plot_bgcolor="#13131A", paper_bgcolor="#0B0B0F",
            font_color="#F0EDE8", title_font_color="#C9953C",
        )
        st.plotly_chart(fig_hour, use_container_width=True)

with tab2:
    if global_stats["figures_used"]:
        df_fig = pd.DataFrame(
            list(global_stats["figures_used"].items()),
            columns=["Personaje", "Conversaciones"]
        )
        df_fig["emoji"] = df_fig["Personaje"].apply(lambda n: FIGURES.get(n, {}).get("emoji", ""))
        df_fig["Label"] = df_fig["emoji"] + " " + df_fig["Personaje"]

        col_a, col_b = st.columns(2)
        with col_a:
            fig_pie = px.pie(
                df_fig, values="Conversaciones", names="Label",
                title="Distribucion por Personaje",
                color_discrete_sequence=["#C9953C", "#3B82F6", "#059669"],
            )
            fig_pie.update_layout(
                plot_bgcolor="#13131A", paper_bgcolor="#0B0B0F",
                font_color="#F0EDE8", title_font_color="#C9953C",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            fig_bar2 = px.bar(
                df_fig, x="Label", y="Conversaciones",
                title="Ranking de Personajes",
                color="Conversaciones",
                color_continuous_scale=["#1A1A24", "#C9953C"],
            )
            fig_bar2.update_layout(
                plot_bgcolor="#13131A", paper_bgcolor="#0B0B0F",
                font_color="#F0EDE8", title_font_color="#C9953C",
            )
            st.plotly_chart(fig_bar2, use_container_width=True)

        all_data = get_all_data()
        if all_data["conversations"]:
            df_all = pd.DataFrame(all_data["conversations"])
            df_all["timestamp"] = pd.to_datetime(df_all["timestamp"])
            df_all["date"] = df_all["timestamp"].dt.date

            daily = df_all.groupby("date").size().reset_index(name="Conversaciones")
            daily.columns = ["Fecha", "Conversaciones"]

            fig_timeline = px.area(
                daily, x="Fecha", y="Conversaciones",
                title="Timeline de Actividad Global",
                color_discrete_sequence=["#C9953C"],
            )
            fig_timeline.update_layout(
                plot_bgcolor="#13131A", paper_bgcolor="#0B0B0F",
                font_color="#F0EDE8", title_font_color="#C9953C",
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No hay datos de conversaciones aun. Chatea con los personajes para generar datos.")

with tab3:
    st.subheader("Ultimas Preguntas por Personaje")
    for name in FIGURES.keys():
        s = get_figure_stats(name)
        if s["questions"]:
            emoji = FIGURES[name]["emoji"]
            with st.expander(f"{emoji} {name} ({len(s['questions'])} preguntas)"):
                recent = list(reversed(s["questions"]))[:10]
                for i, q in enumerate(recent, 1):
                    st.write(f"{i}. {q}")
