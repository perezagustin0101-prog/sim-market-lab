from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
HISTORY_PATH = ROOT / "historial_mercado.csv"
PHASE_PATH = ROOT / "fase_mercado_actual.csv"
PRODUCTS_PATH = ROOT / "products.csv"

st.set_page_config(page_title="Market Lab", layout="wide")
st.title("Market Lab")
st.caption("Historial de precios mínimos del mercado y detector de fases por producto/calidad.")


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


history = load_csv(HISTORY_PATH)
phase = load_csv(PHASE_PATH)

if history.empty:
    st.warning("Todavía no hay historial. Ejecutá el recolector o esperá a que corra GitHub Actions.")
    st.stop()

history["collected_at_utc"] = pd.to_datetime(history["collected_at_utc"], errors="coerce")
history = history.dropna(subset=["collected_at_utc"])

col1, col2, col3 = st.columns(3)
with col1:
    selected_name = st.selectbox("Producto", sorted(history["name"].astype(str).unique()))
with col2:
    q_options = sorted(history.loc[history["name"] == selected_name, "quality"].unique())
    selected_q = st.selectbox("Calidad", q_options)
with col3:
    st.metric("Registros históricos", len(history))

filtered = history[(history["name"] == selected_name) & (history["quality"] == selected_q)].copy()
filtered = filtered.sort_values("collected_at_utc")

st.subheader(f"Historial: {selected_name} Q{selected_q}")
if len(filtered) < 2:
    st.info("Se necesitan más registros para ver tendencia.")
else:
    chart = (
        alt.Chart(filtered)
        .mark_line(point=True)
        .encode(
            x=alt.X("collected_at_utc:T", title="Fecha/hora UTC"),
            y=alt.Y("min_price:Q", title="Precio mínimo mercado"),
            tooltip=[
                "collected_at_utc:T",
                "name:N",
                "quality:Q",
                "min_price:Q",
                "quantity_at_min_price:Q",
                "total_visible_quantity:Q",
                "order_count:Q",
            ],
        )
        .properties(height=360)
    )
    st.altair_chart(chart, use_container_width=True)

st.subheader("Fases actuales")
if phase.empty:
    st.info("Todavía no se generó fase_mercado_actual.csv.")
else:
    st.dataframe(phase, use_container_width=True, hide_index=True)

st.subheader("Historial crudo")
st.dataframe(history.sort_values("collected_at_utc", ascending=False).head(500), use_container_width=True, hide_index=True)
