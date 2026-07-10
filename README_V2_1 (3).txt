from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Sim Companies Business Simulator V2.8",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# Estilo
# ============================================================
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {background: rgba(250,250,250,.04); border: 1px solid rgba(128,128,128,.22); padding: .8rem; border-radius: .9rem;}
    .module-title {font-size: 1.15rem; font-weight: 800; margin: .35rem 0 .35rem 0;}
    .module-sub {font-size: .88rem; color: #8a8f98; margin-bottom: .65rem;}
    .soft-card {border: 1px solid rgba(128,128,128,.25); border-radius: 1rem; padding: 1rem; margin-bottom: .75rem;}
    .small-note {font-size: .82rem; color: #8a8f98;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Helpers
# ============================================================
def money(x: Any) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        x = float(x)
    except Exception:
        return "—"
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1000:
        return sign + f"${x:,.0f}".replace(",", ".")
    if x >= 10:
        return sign + f"${x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return sign + f"${x:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")



def money1(x: Any) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        x = float(x)
    except Exception:
        return "—"
    sign = "-" if x < 0 else ""
    x = abs(x)
    return sign + f"${x:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct_plain(x: Any, dec: int = 1) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        return f"{float(x):,.{dec}f}%".replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return "—"

def num(x: Any, dec: int = 1) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        return f"{float(x):,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return "—"


def pct(x: Any) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        return f"{float(x)*100:.1f}%".replace(".", ",")
    except Exception:
        return "—"


def safe_div(a: float, b: float) -> float:
    try:
        b = float(b)
        if abs(b) < 1e-12:
            return 0.0
        return float(a) / b
    except Exception:
        return 0.0


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    for path in [ROOT / name, DATA / name]:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_json(name: str) -> dict:
    for path in [ROOT / name, DATA / name]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


@st.cache_data(show_spinner=False)
def parse_market_history() -> pd.DataFrame:
    """Soporta historial_mercado.csv viejo o nuevo.

    Formato esperado mínimo:
    fecha/kind/quality/price o variantes generadas por collector.py.
    """
    for path in [ROOT / "historial_mercado.csv", DATA / "historial_mercado.csv", ROOT / "market_ticks.csv", DATA / "market_ticks.csv"]:
        if path.exists():
            break
    else:
        return pd.DataFrame(columns=["fecha", "kind", "quality", "price"])

    rows = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                first = str(row[0]).strip().lower()
                if first in {"collected_at_utc", "recopilado_en_utc", "fecha", "timestamp"}:
                    continue
                # Variante vieja: fecha, kind, ... quality, price
                if len(row) >= 8 and not str(row[2]).replace(".", "", 1).isdigit():
                    rows.append([row[0], row[1], row[3], row[4]])
                # Variante simple: fecha, kind, quality, price
                elif len(row) >= 4:
                    rows.append([row[0], row[1], row[2], row[3]])
    except Exception:
        return pd.DataFrame(columns=["fecha", "kind", "quality", "price"])

    df = pd.DataFrame(rows, columns=["fecha", "kind", "quality", "price"])
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", utc=True)
    df["kind"] = pd.to_numeric(df["kind"], errors="coerce")
    df["quality"] = pd.to_numeric(df["quality"], errors="coerce").fillna(0).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["fecha", "kind", "price"])
    df["kind"] = df["kind"].astype(int)
    return df.sort_values("fecha")


REQ_MAP = {
    "Electricidad": "electricidad_necesaria_h",
    "Agua": "agua_necesaria_h",
    "Semillas": "semillas_necesarias_h",
    "Diésel": "diesel_necesario_h",
}

SOURCE_OPTIONS = ["Propia", "Mercado", "Contrato", "Mixta"]
SALE_OPTIONS = ["Mercado", "Contrato", "Mejor automático"]
PRICE_OPTIONS = ["Último", "Promedio", "Mínimo", "Máximo", "Manual/default"]
CONTRACT_TRANSPORT_FACTOR = 0.50  # Regla del juego: contratos usan la mitad del transporte de mercado.


# ============================================================
# Carga de datos base
# ============================================================
products_raw = load_csv("productos_v1.csv")
buildings_raw = load_csv("edificios_v1.csv")
config_raw = load_json("configuracion_v1.json")
hist = parse_market_history()

if products_raw.empty or buildings_raw.empty:
    st.error("Faltan productos_v1.csv o edificios_v1.csv en la carpeta raíz del repo.")
    st.stop()

# Normalización defensiva
for col in ["kind", "produccion_h", "agua_necesaria_h", "semillas_necesarias_h", "electricidad_necesaria_h", "diesel_necesario_h", "transporte_mercado", "precio_default", "costo_manual"]:
    if col in products_raw.columns:
        products_raw[col] = pd.to_numeric(products_raw[col], errors="coerce").fillna(0)
for col in ["salario_h", "produccion_h", "electricidad_necesaria_h", "valor_referencia_n1", "costo_n1", "tiempo_n1_h"]:
    if col in buildings_raw.columns:
        buildings_raw[col] = pd.to_numeric(buildings_raw[col], errors="coerce").fillna(0)

# Estado editable de productos/recetas
if "productos_editados" not in st.session_state:
    st.session_state["productos_editados"] = products_raw.copy()

# ============================================================
# Market stats
# ============================================================
def build_market_stats(products: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    base = products[["kind", "producto", "precio_default"]].copy()
    base["kind"] = base["kind"].astype(int)
    if history.empty:
        out = base.copy()
        out["Último"] = out["precio_default"]
        out["Mínimo"] = out["precio_default"]
        out["Promedio"] = out["precio_default"]
        out["Máximo"] = out["precio_default"]
        out["Puntos"] = 0
        return out[["producto", "Último", "Mínimo", "Promedio", "Máximo", "Puntos", "precio_default"]]

    h0 = history[history["quality"] == 0].copy()
    if h0.empty:
        h0 = history.copy()
    agg = h0.groupby("kind").agg(
        Último=("price", lambda s: s.iloc[-1]),
        Mínimo=("price", "min"),
        Promedio=("price", "mean"),
        Máximo=("price", "max"),
        Puntos=("price", "count"),
    ).reset_index()
    out = base.merge(agg, on="kind", how="left")
    for col in ["Último", "Mínimo", "Promedio", "Máximo"]:
        out[col] = out[col].fillna(out["precio_default"])
    out["Puntos"] = out["Puntos"].fillna(0).astype(int)
    return out[["producto", "Último", "Mínimo", "Promedio", "Máximo", "Puntos", "precio_default"]]


def fmt_df_money(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].map(money)
    return out


def get_building_row(buildings: pd.DataFrame, edificio: str) -> pd.Series:
    m = buildings[buildings["edificio"] == edificio]
    if m.empty:
        return pd.Series(dtype="object")
    return m.iloc[0]


def get_product_row(products: pd.DataFrame, producto: str) -> pd.Series:
    m = products[products["producto"] == producto]
    if m.empty:
        return pd.Series(dtype="object")
    return m.iloc[0]


def price_of(producto: str, market_stats: pd.DataFrame, mode: str) -> float:
    row = market_stats[market_stats["producto"] == producto]
    if row.empty:
        return 0.0
    r = row.iloc[0]
    key = mode if mode in ["Último", "Promedio", "Mínimo", "Máximo"] else "precio_default"
    return float(r.get(key, 0) or 0)

# ============================================================
# Escenarios por defecto
# ============================================================
def default_scenarios() -> Dict[str, dict]:
    return {
        "Mi empresa actual": {
            "tipo": "Real",
            "descripcion": "Tu empresa cargada: central N1, embalse N1, granja semillera N2, 3 granjas comunes N1.",
            "cash": 146000,
            "deuda": 0,
            "rows": [
                {"Activo": True, "Edificio": "Central eléctrica", "Producto": "Electricidad", "Nivel total": 1, "Vender salida": False},
                {"Activo": True, "Edificio": "Embalse de agua", "Producto": "Agua", "Nivel total": 1, "Vender salida": False},
                {"Activo": True, "Edificio": "Granja", "Producto": "Semillas", "Nivel total": 2, "Vender salida": False},
                {"Activo": True, "Edificio": "Granja", "Producto": "Simular opciones", "Nivel total": 3, "Vender salida": True},
            ],
        },
        "Agricultura integrada ejemplo": {
            "tipo": "Simulada",
            "descripcion": "Ejemplo para probar agricultura integrada con más niveles.",
            "cash": 0,
            "deuda": 0,
            "rows": [
                {"Activo": True, "Edificio": "Central eléctrica", "Producto": "Electricidad", "Nivel total": 2, "Vender salida": False},
                {"Activo": True, "Edificio": "Embalse de agua", "Producto": "Agua", "Nivel total": 3, "Vender salida": False},
                {"Activo": True, "Edificio": "Granja", "Producto": "Semillas", "Nivel total": 3, "Vender salida": False},
                {"Activo": True, "Edificio": "Granja", "Producto": "Simular opciones", "Nivel total": 5, "Vender salida": True},
            ],
        },
        "Solo comprar insumos y producir": {
            "tipo": "Simulada",
            "descripcion": "Ejemplo de producción sin cadena propia: compra electricidad/agua/semillas/insumos al mercado.",
            "cash": 0,
            "deuda": 0,
            "rows": [
                {"Activo": True, "Edificio": "Granja", "Producto": "Simular opciones", "Nivel total": 6, "Vender salida": True},
            ],
        },
    }


if "scenarios" not in st.session_state:
    st.session_state["scenarios"] = default_scenarios()
if "scenario_name" not in st.session_state:
    st.session_state["scenario_name"] = "Mi empresa actual"
if "fuentes_insumos" not in st.session_state:
    st.session_state["fuentes_insumos"] = pd.DataFrame([
        {"Insumo": "Electricidad", "Fuente": "Propia", "% propio si Mixta": 50},
        {"Insumo": "Agua", "Fuente": "Propia", "% propio si Mixta": 50},
        {"Insumo": "Semillas", "Fuente": "Propia", "% propio si Mixta": 50},
        {"Insumo": "Diésel", "Fuente": "Mercado", "% propio si Mixta": 0},
        {"Insumo": "Transporte", "Fuente": "Mercado", "% propio si Mixta": 0},
    ])
DIRECTOR_INPUT_COLUMNS = ["Activo", "Nombre", "Puesto", "Management", "Accounting", "Communication", "Science", "Salario diario"]
DIRECTOR_EFFECT_COLUMNS = ["Reducción admin %", "Mejora contable $M", "Aumento ventas %", "Patentes +pp"]
DIRECTOR_COLUMNS = DIRECTOR_INPUT_COLUMNS + DIRECTOR_EFFECT_COLUMNS
DIRECTOR_ROLE_OPTIONS = ["COO", "CFO", "CMO", "CTO", "Staff"]


def round_half_up(value: float, decimals: int = 1) -> float:
    """Redondeo decimal consistente entre tabla y tarjetas."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal("1") if decimals == 0 else Decimal("1." + ("0" * decimals))
    return float(Decimal(str(float(value))).quantize(q, rounding=ROUND_HALF_UP))


def _director_role_weight(puesto: str, target_role: str) -> float:
    """Peso del puesto asignado para estimar aportes cruzados.

    En Sim Companies importan los puntos/habilidades del director y el puesto donde está asignado.
    El puesto asociado al efecto cuenta completo; los otros puestos aportan parcialmente.
    Staff no aplica beneficios directos, pero sirve para entrenar habilidades.
    """
    puesto = str(puesto or "").strip()
    if puesto == "Staff" or puesto == "":
        return 0.0
    if puesto == target_role:
        return 1.0
    return 0.25


def add_director_effects(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Migración desde versiones anteriores.
    if "Puesto" not in out.columns:
        if "Puesto asignado" in out.columns:
            out["Puesto"] = out["Puesto asignado"]
        elif "Perfil" in out.columns:
            out["Puesto"] = out["Perfil"]
        else:
            out["Puesto"] = "COO"
    if "Mejora contable $M" not in out.columns and "Lift contable $M" in out.columns:
        out["Mejora contable $M"] = out["Lift contable $M"]
    if "Aumento ventas %" not in out.columns and "Aumento venta %" in out.columns:
        out["Aumento ventas %"] = out["Aumento venta %"]
    if "Patentes +pp" not in out.columns and "Impacto ciencia %" in out.columns:
        out["Patentes +pp"] = out["Impacto ciencia %"]

    for col in DIRECTOR_INPUT_COLUMNS:
        if col not in out.columns:
            if col == "Nombre":
                out[col] = ""
            elif col == "Puesto":
                out[col] = "COO"
            elif col == "Activo":
                out[col] = False
            else:
                out[col] = 0

    for col in ["Management", "Accounting", "Communication", "Science", "Salario diario"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    out["Nombre"] = out["Nombre"].fillna("").astype(str)
    out["Puesto"] = out["Puesto"].fillna("Staff").astype(str)

    # Para evitar cargar datos y olvidarse el check: si una fila tiene nombre, skills o salario,
    # la activamos automáticamente. Las filas vacías quedan apagadas.
    has_data = (
        out["Nombre"].str.strip().ne("")
        | (out[["Management", "Accounting", "Communication", "Science", "Salario diario"]].abs().sum(axis=1) > 0)
    )
    out["Activo"] = out["Activo"].fillna(False).astype(bool) | has_data
    active_mult = out["Activo"].astype(float)

    # Fórmulas iniciales. Se muestran redondeadas a 1 decimal para que tabla y tarjetas coincidan.
    admin_vals = active_mult * out.apply(
        lambda r: float(r["Management"]) * _director_role_weight(r.get("Puesto"), "COO"), axis=1
    )
    accounting_vals = active_mult * out.apply(
        lambda r: (float(r["Accounting"]) * _director_role_weight(r.get("Puesto"), "CFO")) / 2.0, axis=1
    )
    sales_vals = active_mult * out.apply(
        lambda r: (float(r["Communication"]) * _director_role_weight(r.get("Puesto"), "CMO")) / 12.0, axis=1
    )
    science_vals = active_mult * out.apply(
        lambda r: (float(r["Science"]) * _director_role_weight(r.get("Puesto"), "CTO")) * 0.125, axis=1
    )

    out["Reducción admin %"] = [round_half_up(v, 1) for v in admin_vals]
    out["Mejora contable $M"] = [round_half_up(v, 1) for v in accounting_vals]
    out["Aumento ventas %"] = [round_half_up(v, 1) for v in sales_vals]
    out["Patentes +pp"] = [round_half_up(v, 1) for v in science_vals]

    # Limpieza de columnas viejas que venían de versiones anteriores.
    for old_col in [
        "Perfil", "Puesto asignado", "Puesto asignado ", "Lift contable $M", "Puesto viejo",
        "Aumento venta %", "Impacto ciencia %", "Reducción admin % viejo", "Bono producción %", "Bono venta retail %"
    ]:
        if old_col in out.columns and old_col not in DIRECTOR_COLUMNS:
            out = out.drop(columns=[old_col])

    return out[DIRECTOR_COLUMNS].copy()


if "directores" not in st.session_state:
    st.session_state["directores"] = pd.DataFrame([
        {"Activo": False, "Nombre": "", "Puesto": "COO", "Management": 0, "Accounting": 0, "Communication": 0, "Science": 0, "Salario diario": 0.0},
        {"Activo": False, "Nombre": "", "Puesto": "CFO", "Management": 0, "Accounting": 0, "Communication": 0, "Science": 0, "Salario diario": 0.0},
        {"Activo": False, "Nombre": "", "Puesto": "CMO", "Management": 0, "Accounting": 0, "Communication": 0, "Science": 0, "Salario diario": 0.0},
        {"Activo": False, "Nombre": "", "Puesto": "CTO", "Management": 0, "Accounting": 0, "Communication": 0, "Science": 0, "Salario diario": 0.0},
    ])
st.session_state["directores"] = add_director_effects(st.session_state["directores"])

# ============================================================
# Configuración global
# ============================================================
st.title("Sim Companies Business Simulator V2.8")
st.caption("Una pantalla modular para simular tu empresa real, probar empresas nuevas y comparar costos/precios/beneficio real.")

with st.container(border=True):
    st.markdown('<div class="module-title">1. Configuración global</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        price_mode = st.selectbox("Precio usado", PRICE_OPTIONS, index=0)
        analysis_hours = st.number_input("Horas simuladas", min_value=1, max_value=24*30, value=24, step=1)
    with c2:
        market_fee_pct = st.number_input(
            "Comisión venta mercado (%)",
            min_value=0.0,
            max_value=25.0,
            value=float(config_raw.get("comision_mercado", 0.03)) * 100,
            step=0.1,
            format="%.2f",
        )
        contract_discount_pct = st.number_input(
            "Descuento venta contrato (%)",
            min_value=0.0,
            max_value=50.0,
            value=float(config_raw.get("descuento_contrato", 0.03)) * 100,
            step=0.1,
            format="%.2f",
        )
    with c3:
        sale_mode = st.selectbox("Canal de venta", SALE_OPTIONS, index=0)
        sell_surplus = st.checkbox("Vender excedentes", value=True)
    with c4:
        production_bonus_pct_manual = st.number_input(
            "Bonus de producción (%)",
            min_value=-90.0,
            max_value=300.0,
            value=float(config_raw.get("bono_produccion_pct", 0.0)),
            step=1.0,
            format="%.2f",
            help="Cargá solamente el bonus extra que tengas en el juego.",
        )
        retail_bonus_pct_manual = st.number_input(
            "Bonus de venta retail (%)",
            min_value=-90.0,
            max_value=300.0,
            value=float(config_raw.get("bono_venta_retail_pct", 0.0)),
            step=1.0,
            format="%.2f",
            help="Cargá solamente el bonus extra de venta retail que tengas en el juego.",
        )

    market_fee = market_fee_pct / 100.0
    contract_discount = contract_discount_pct / 100.0

    st.markdown("**Directores**")
    directores_base = add_director_effects(st.session_state["directores"]).copy()

    with st.form("form_directores_v28", clear_on_submit=False):
        directores_editados = st.data_editor(
            directores_base,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=DIRECTOR_EFFECT_COLUMNS,
            column_config={
                "Activo": st.column_config.CheckboxColumn("Activo"),
                "Puesto": st.column_config.SelectboxColumn("Puesto", options=DIRECTOR_ROLE_OPTIONS),
                "Management": st.column_config.NumberColumn("Gestión", min_value=0, max_value=999, step=1),
                "Accounting": st.column_config.NumberColumn("Contabilidad", min_value=0, max_value=999, step=1),
                "Communication": st.column_config.NumberColumn("Comunicación", min_value=0, max_value=999, step=1),
                "Science": st.column_config.NumberColumn("Ciencia", min_value=0, max_value=999, step=1),
                "Salario diario": st.column_config.NumberColumn("Salario diario", min_value=0.0, step=100.0, format="$%.1f"),
                "Reducción admin %": st.column_config.NumberColumn("Reducción administrativa", format="%.1f%%"),
                "Mejora contable $M": st.column_config.NumberColumn("Mejora contable", format="$%.1fM", help="Efecto estimado del director en la parte contable. No es beneficio directo."),
                "Aumento ventas %": st.column_config.NumberColumn("Aumento de ventas", format="%.1f%%"),
                "Patentes +pp": st.column_config.NumberColumn("Probabilidad de patente", format="%.1f%%"),
            },
            key="directores_v28_editor",
        )
        aplicar_directores = st.form_submit_button("Aplicar directores", use_container_width=False)

    if aplicar_directores:
        st.session_state["directores"] = add_director_effects(directores_editados).copy()
        st.rerun()

    directores_df = add_director_effects(st.session_state["directores"]).copy()

    active_directors = directores_df[directores_df["Activo"]] if (not directores_df.empty and "Activo" in directores_df.columns) else pd.DataFrame()
    total_director_salary_day = float(active_directors["Salario diario"].sum()) if not active_directors.empty else 0.0
    total_director_salary_h = total_director_salary_day / 24.0

    director_reduction_pct_total = float(active_directors["Reducción admin %"].sum()) if not active_directors.empty else 0.0
    director_sales_pct_total = float(active_directors["Aumento ventas %"].sum()) if not active_directors.empty else 0.0
    director_accounting_lift_m = float(active_directors["Mejora contable $M"].sum()) if not active_directors.empty else 0.0
    director_science_pct_total = float(active_directors["Patentes +pp"].sum()) if not active_directors.empty else 0.0

    director_reduction = max(0.0, min(0.95, director_reduction_pct_total / 100.0))
    production_bonus_pct_total = production_bonus_pct_manual
    retail_bonus_pct_total = retail_bonus_pct_manual + director_sales_pct_total
    production_mult = max(0.10, 1.0 + production_bonus_pct_total / 100.0)

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Costo directores/día", money1(total_director_salary_day))
    d2.metric("Costo directores/h", money1(total_director_salary_h))
    d3.metric("Reducción administrativa", pct_plain(director_reduction_pct_total, 1))
    d4.metric("Mejora contable", money(director_accounting_effect))
    d5.metric("Aumento de ventas", pct_plain(director_sales_pct_total, 1))
    d6.metric("Probabilidad de patente", pct_plain(director_science_pct_total, 1))

# Productos editables
products = st.session_state["productos_editados"].copy()
buildings = buildings_raw.copy()
market_stats = build_market_stats(products, hist)

# ============================================================
# 2. Empresas / escenarios
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">2. Empresas / escenarios</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Elegí tu empresa real o un escenario simulado. Podés duplicar, crear y modificar sin tocar el juego.</div>', unsafe_allow_html=True)

    names = list(st.session_state["scenarios"].keys())
    if st.session_state["scenario_name"] not in names:
        st.session_state["scenario_name"] = names[0]

    a, b, c, d = st.columns([2.2, 1.2, 1.2, 1.2])
    with a:
        scenario_name = st.selectbox("Empresa / escenario activo", names, index=names.index(st.session_state["scenario_name"]))
        st.session_state["scenario_name"] = scenario_name
    with b:
        if st.button("Duplicar escenario", use_container_width=True):
            base = st.session_state["scenarios"][scenario_name]
            new_name = f"{scenario_name} copia"
            i = 2
            while new_name in st.session_state["scenarios"]:
                new_name = f"{scenario_name} copia {i}"
                i += 1
            st.session_state["scenarios"][new_name] = json.loads(json.dumps(base))
            st.session_state["scenarios"][new_name]["tipo"] = "Simulada"
            st.session_state["scenario_name"] = new_name
            st.rerun()
    with c:
        if st.button("Nuevo vacío", use_container_width=True):
            new_name = "Empresa nueva"
            i = 2
            while new_name in st.session_state["scenarios"]:
                new_name = f"Empresa nueva {i}"
                i += 1
            st.session_state["scenarios"][new_name] = {
                "tipo": "Simulada",
                "descripcion": "Escenario vacío para armar desde cero.",
                "cash": 0,
                "deuda": 0,
                "rows": [],
            }
            st.session_state["scenario_name"] = new_name
            st.rerun()
    with d:
        if st.button("Reset V2", use_container_width=True):
            st.session_state["scenarios"] = default_scenarios()
            st.session_state["scenario_name"] = "Mi empresa actual"
            st.rerun()

    scenario = st.session_state["scenarios"][st.session_state["scenario_name"]]
    m1, m2, m3, m4 = st.columns(4)
    scenario["tipo"] = m1.selectbox("Tipo", ["Real", "Simulada"], index=0 if scenario.get("tipo") == "Real" else 1)
    scenario["cash"] = m2.number_input("Cash / capital", value=float(scenario.get("cash", 0)), step=1000.0)
    scenario["deuda"] = m3.number_input("Deuda", value=float(scenario.get("deuda", 0)), step=1000.0)
    scenario["descripcion"] = m4.text_input("Descripción corta", value=str(scenario.get("descripcion", "")))

# ============================================================
# 3. Edificios
# ============================================================
def scenario_rows_df(scenario: dict) -> pd.DataFrame:
    rows = scenario.get("rows", [])
    if not rows:
        rows = [{"Activo": True, "Edificio": buildings_raw["edificio"].iloc[0], "Producto": "Simular opciones", "Nivel total": 1, "Vender salida": True}]
    df = pd.DataFrame(rows)
    for col, default in [("Activo", True), ("Edificio", "Granja"), ("Producto", "Simular opciones"), ("Nivel total", 1), ("Vender salida", True)]:
        if col not in df.columns:
            df[col] = default
    return df[["Activo", "Edificio", "Producto", "Nivel total", "Vender salida"]]


with st.container(border=True):
    st.markdown('<div class="module-title">3. Edificios de la empresa seleccionada</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Cargá niveles totales por tipo de edificio/uso. No hace falta cargar slot por slot.</div>', unsafe_allow_html=True)
    building_options = buildings["edificio"].dropna().astype(str).tolist()
    product_options = ["Simular opciones"] + products["producto"].dropna().astype(str).tolist()
    edited_rows = st.data_editor(
        scenario_rows_df(scenario),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Activo": st.column_config.CheckboxColumn("Activo"),
            "Edificio": st.column_config.SelectboxColumn("Edificio", options=building_options),
            "Producto": st.column_config.SelectboxColumn("Producto", options=product_options),
            "Nivel total": st.column_config.NumberColumn("Nivel total", min_value=0, max_value=100, step=1),
            "Vender salida": st.column_config.CheckboxColumn("Vender salida", help="Si está apagado, la producción se usa como insumo interno y solo se vende el excedente si activaste vender excedentes."),
        },
        key=f"rows_editor_{st.session_state['scenario_name']}",
    )
    edited_rows["Nivel total"] = pd.to_numeric(edited_rows["Nivel total"], errors="coerce").fillna(0).astype(int)
    scenario["rows"] = edited_rows.to_dict(orient="records")

    total_levels = int(edited_rows.loc[edited_rows["Activo"], "Nivel total"].sum()) if not edited_rows.empty else 0
    used_building_rows = int((edited_rows["Activo"] & (edited_rows["Nivel total"] > 0)).sum()) if not edited_rows.empty else 0
    admin_pct = max(0.0, (total_levels - 1) / 170.0) * (1 - director_reduction)
    mm1, mm2, mm3, mm4 = st.columns(4)
    mm1.metric("Niveles totales", total_levels)
    mm2.metric("Bloques activos", used_building_rows)
    mm3.metric("Administración estimada", pct(admin_pct))
    mm4.metric("Cash neto", money(float(scenario.get("cash", 0)) - float(scenario.get("deuda", 0))))

# ============================================================
# 4. Productos / recetas
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">4. Productos / recetas</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Base editable de producción y requisitos. La app muestra base vs efectivo para detectar doble conteo.</div>', unsafe_allow_html=True)

    # Vista rápida: valores base del CSV vs valores efectivos con bonos aplicados
    preview_rows = []
    try:
        scen_df = pd.DataFrame(scenario.get("rows", []))
        if not scen_df.empty:
            scen_df["Activo"] = scen_df.get("Activo", True).astype(bool)
            scen_df["Nivel total"] = pd.to_numeric(scen_df.get("Nivel total", 0), errors="coerce").fillna(0)
            scen_df = scen_df[(scen_df["Activo"]) & (scen_df["Nivel total"] > 0)]
            for _, rr in scen_df.iterrows():
                edificio_sel = str(rr.get("Edificio", ""))
                prod_sel = str(rr.get("Producto", ""))
                niveles = float(rr.get("Nivel total", 0) or 0)
                if prod_sel == "Simular opciones":
                    prod_rows = products[(products["edificio"] == edificio_sel) & (products["produccion_h"] > 0)].copy()
                else:
                    prod_rows = products[products["producto"] == prod_sel].copy()
                for _, prr in prod_rows.iterrows():
                    prod_base = niveles * float(prr.get("produccion_h", 0) or 0)
                    agua_base = niveles * float(prr.get("agua_necesaria_h", 0) or 0)
                    semillas_base = niveles * float(prr.get("semillas_necesarias_h", 0) or 0)
                    electricidad_base = niveles * float(prr.get("electricidad_necesaria_h", 0) or 0)
                    preview_rows.append({
                        "Edificio": edificio_sel,
                        "Producto": prr.get("producto", ""),
                        "Niveles": int(niveles),
                        "Producción base/h": prod_base,
                        "Producción efectiva/h": prod_base * production_mult,
                        "Agua base/h": agua_base,
                        "Agua efectiva/h": agua_base * production_mult,
                        "Semillas base/h": semillas_base,
                        "Semillas efectiva/h": semillas_base * production_mult,
                        "Electricidad base/h": electricidad_base,
                        "Electricidad efectiva/h": electricidad_base * production_mult,
                    })
    except Exception:
        preview_rows = []

    if preview_rows:
        st.markdown("**Control base vs efectivo**")
        st.caption("Si Producción base/h ya coincide con lo que te muestra el juego con bonus, entonces el CSV está bonificado y habría doble conteo. La columna efectiva es base × bonus total.")
        st.dataframe(
            pd.DataFrame(preview_rows).head(80).style.format({
                "Producción base/h": "{:.2f}",
                "Producción efectiva/h": "{:.2f}",
                "Agua base/h": "{:.2f}",
                "Agua efectiva/h": "{:.2f}",
                "Semillas base/h": "{:.2f}",
                "Semillas efectiva/h": "{:.2f}",
                "Electricidad base/h": "{:.2f}",
                "Electricidad efectiva/h": "{:.2f}",
            }),
            hide_index=True,
            use_container_width=True,
        )

    with st.expander("Ver / editar recetas y requisitos BASE", expanded=False):
        editable_cols = [
            "kind", "producto", "edificio", "produccion_h", "agua_necesaria_h", "semillas_necesarias_h",
            "electricidad_necesaria_h", "diesel_necesario_h", "transporte_mercado", "precio_default", "costo_manual"
        ]
        edited_products = st.data_editor(
            products[editable_cols],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="productos_v2_editor",
        )
        st.session_state["productos_editados"] = edited_products.copy()
        products = edited_products.copy()
        market_stats = build_market_stats(products, hist)
        st.download_button(
            "Descargar productos_v1.csv editado",
            data=edited_products.to_csv(index=False).encode("utf-8"),
            file_name="productos_v1_editado.csv",
            mime="text/csv",
        )

# ============================================================
# 5. Fuente de insumos
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">5. Fuente de insumos</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Define si cada insumo se valora como producción propia, mercado, contrato o mixto.</div>', unsafe_allow_html=True)
    fuente_df = st.data_editor(
        st.session_state["fuentes_insumos"],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Insumo": st.column_config.SelectboxColumn("Insumo", options=sorted(set(list(REQ_MAP.keys()) + ["Transporte"] + products["producto"].astype(str).tolist()))),
            "Fuente": st.column_config.SelectboxColumn("Fuente", options=SOURCE_OPTIONS),
            "% propio si Mixta": st.column_config.NumberColumn("% propio si Mixta", min_value=0, max_value=100, step=5),
        },
        key="fuentes_v2_editor",
    )
    fuente_df["% propio si Mixta"] = pd.to_numeric(fuente_df["% propio si Mixta"], errors="coerce").fillna(0).clip(0, 100)
    st.session_state["fuentes_insumos"] = fuente_df.copy()

# ============================================================
# Motor de simulación
# ============================================================
def fuente_config(fuente_df: pd.DataFrame) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for _, r in fuente_df.iterrows():
        out[str(r.get("Insumo", ""))] = {
            "Fuente": str(r.get("Fuente", "Mercado")),
            "pct_propio": float(r.get("% propio si Mixta", 0) or 0) / 100.0,
        }
    return out


def active_rows_for_scenario(scenario: dict) -> List[dict]:
    df = pd.DataFrame(scenario.get("rows", []))
    if df.empty:
        return []
    df["Activo"] = df.get("Activo", True).astype(bool)
    df["Nivel total"] = pd.to_numeric(df.get("Nivel total", 0), errors="coerce").fillna(0).astype(int)
    df = df[(df["Activo"]) & (df["Nivel total"] > 0)]
    return df.to_dict(orient="records")


def product_options_for_building(products: pd.DataFrame, edificio: str) -> List[str]:
    opts = products[(products["edificio"] == edificio) & (products["produccion_h"] > 0)]["producto"].dropna().astype(str).tolist()
    return opts or products[products["produccion_h"] > 0]["producto"].dropna().astype(str).tolist()


def expand_variants(rows: List[dict], products: pd.DataFrame, max_variants: int = 250) -> List[Tuple[str, List[dict]]]:
    sim_positions = [i for i, r in enumerate(rows) if str(r.get("Producto")) == "Simular opciones"]
    if not sim_positions:
        name = " + ".join(str(r.get("Producto")) for r in rows if bool(r.get("Vender salida", False))) or "Escenario"
        return [(name, rows)]

    options_by_pos = []
    for pos in sim_positions:
        edificio = str(rows[pos].get("Edificio", ""))
        options_by_pos.append(product_options_for_building(products, edificio))

    variants = []
    for combo in itertools.product(*options_by_pos):
        new_rows = [dict(r) for r in rows]
        for pos, prod_name in zip(sim_positions, combo):
            new_rows[pos]["Producto"] = prod_name
        label_parts = []
        for r in new_rows:
            if bool(r.get("Vender salida", False)):
                label_parts.append(f"{r.get('Producto')} N{r.get('Nivel total')}")
        variants.append((" + ".join(label_parts) or "Escenario", new_rows))
        if len(variants) >= max_variants:
            break
    return variants


def scenario_output_capacity(rows: List[dict], products: pd.DataFrame) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for r in rows:
        prod_name = str(r.get("Producto", ""))
        pr = get_product_row(products, prod_name)
        if pr.empty:
            continue
        qty = float(r.get("Nivel total", 0) or 0) * float(pr.get("produccion_h", 0) or 0) * production_mult
        out[prod_name] = out.get(prod_name, 0.0) + qty
    return out


def salary_per_level(edificio: str) -> float:
    br = get_building_row(buildings, edificio)
    if br.empty:
        return 0.0
    return float(br.get("salario_h", 0) or 0) * (1 + admin_pct)


def product_building(producto: str, products: pd.DataFrame) -> str:
    r = get_product_row(products, producto)
    return "" if r.empty else str(r.get("edificio", ""))


def market_buy_price(producto: str, market_stats: pd.DataFrame) -> float:
    return price_of(producto, market_stats, price_mode)


def own_possible(producto: str, rows: List[dict], products: pd.DataFrame) -> bool:
    return any(str(r.get("Producto")) == producto and float(r.get("Nivel total", 0) or 0) > 0 for r in rows)


def calculate_unit_costs(rows: List[dict], products: pd.DataFrame, market_stats: pd.DataFrame, fuente_df: pd.DataFrame) -> Dict[str, dict]:
    fcfg = fuente_config(fuente_df)
    memo: Dict[str, dict] = {}

    def input_unit_price(input_name: str, stack: Tuple[str, ...]) -> float:
        cfg = fcfg.get(input_name, {"Fuente": "Mercado", "pct_propio": 0})
        source = cfg.get("Fuente", "Mercado")
        market_price = market_buy_price(input_name, market_stats)
        if source == "Mercado":
            return market_price
        if source == "Contrato":
            # Supuesto simple: contrato de compra con el mismo descuento cargado.
            return market_price * (1 - contract_discount)
        if source in {"Propia", "Mixta"} and own_possible(input_name, rows, products):
            own = unit_cost(input_name, stack + (input_name,)).get("Costo/u", market_price)
            if source == "Propia":
                return own
            pct_own = float(cfg.get("pct_propio", 0) or 0)
            return pct_own * own + (1 - pct_own) * market_price
        return market_price

    def unit_cost(producto: str, stack: Tuple[str, ...] = ()) -> dict:
        if producto in memo:
            return memo[producto]
        if producto in stack:
            # Evita ciclos raros si se editan recetas.
            price = market_buy_price(producto, market_stats)
            return {"Producto": producto, "Costo/u": price, "Salario/u": 0.0, "Insumos/u": price, "Detalle": "ciclo -> mercado"}
        pr = get_product_row(products, producto)
        if pr.empty or float(pr.get("produccion_h", 0) or 0) <= 0:
            price = market_buy_price(producto, market_stats)
            return {"Producto": producto, "Costo/u": price, "Salario/u": 0.0, "Insumos/u": price, "Detalle": "sin receta -> mercado"}

        edificio = str(pr.get("edificio", ""))
        prod_h = float(pr.get("produccion_h", 0) or 0) * production_mult
        sal_u = safe_div(salary_per_level(edificio), prod_h)
        ins_u = 0.0
        details = []
        for input_name, col in REQ_MAP.items():
            need_h = float(pr.get(col, 0) or 0) * production_mult
            if need_h <= 0:
                continue
            need_u = safe_div(need_h, prod_h)
            in_price = input_unit_price(input_name, stack)
            ins_u += need_u * in_price
            details.append(f"{input_name}: {num(need_u, 4)}u × {money(in_price)}")
        result = {
            "Producto": producto,
            "Costo/u": sal_u + ins_u,
            "Salario/u": sal_u,
            "Insumos/u": ins_u,
            "Detalle": "; ".join(details),
        }
        memo[producto] = result
        return result

    # Calcula para todos los productos con receta y para los productos presentes en filas.
    for p in products[products["produccion_h"] > 0]["producto"].dropna().astype(str).tolist():
        unit_cost(p, ())
    return memo


def transport_unit_cost(rows: List[dict], unit_costs: Dict[str, dict], market_stats: pd.DataFrame, fuente_df: pd.DataFrame) -> float:
    fcfg = fuente_config(fuente_df)
    cfg = fcfg.get("Transporte", {"Fuente": "Mercado", "pct_propio": 0})
    market_price = market_buy_price("Transporte", market_stats)
    source = cfg.get("Fuente", "Mercado")
    if source == "Mercado":
        return market_price
    if source == "Contrato":
        return market_price * (1 - contract_discount)
    own = unit_costs.get("Transporte", {}).get("Costo/u", market_price)
    if source == "Propia" and own_possible("Transporte", rows, products):
        return own
    if source == "Mixta" and own_possible("Transporte", rows, products):
        pct_own = float(cfg.get("pct_propio", 0) or 0)
        return pct_own * own + (1 - pct_own) * market_price
    return market_price


def net_sale_price(producto: str, unit_costs: Dict[str, dict], rows: List[dict]) -> Tuple[str, float, float, float]:
    pr = get_product_row(products, producto)
    price = market_buy_price(producto, market_stats)
    tr_need = float(pr.get("transporte_mercado", 0) or 0) if not pr.empty else 0.0
    tr_u = transport_unit_cost(rows, unit_costs, market_stats, fuente_df)
    market_net = price * (1 - market_fee) - tr_need * tr_u
    contract_net = price * (1 - contract_discount) - tr_need * tr_u * CONTRACT_TRANSPORT_FACTOR
    if sale_mode == "Mercado":
        return "Mercado", market_net, price, tr_need * tr_u
    if sale_mode == "Contrato":
        return "Contrato", contract_net, price, tr_need * tr_u * CONTRACT_TRANSPORT_FACTOR
    if contract_net > market_net:
        return "Contrato", contract_net, price, tr_need * tr_u * CONTRACT_TRANSPORT_FACTOR
    return "Mercado", market_net, price, tr_need * tr_u


def simulate_variant(label: str, rows: List[dict], products: pd.DataFrame, market_stats: pd.DataFrame, fuente_df: pd.DataFrame) -> dict:
    outputs: Dict[str, float] = {}
    needs: Dict[str, float] = {k: 0.0 for k in REQ_MAP.keys()}
    unit_costs = calculate_unit_costs(rows, products, market_stats, fuente_df)

    # Producción y consumo físico por hora
    for r in rows:
        prod_name = str(r.get("Producto", ""))
        pr = get_product_row(products, prod_name)
        if pr.empty:
            continue
        levels = float(r.get("Nivel total", 0) or 0)
        qty_base = levels * float(pr.get("produccion_h", 0) or 0)
        qty = qty_base * production_mult
        outputs[prod_name] = outputs.get(prod_name, 0.0) + qty
        for input_name, col in REQ_MAP.items():
            needs[input_name] = needs.get(input_name, 0.0) + levels * float(pr.get(col, 0) or 0) * production_mult

    # Beneficio por producción marcada como vendible
    sell_rows = []
    total_revenue_h = 0.0
    total_cost_h = 0.0
    total_profit_h = 0.0
    for r in rows:
        if not bool(r.get("Vender salida", False)):
            continue
        prod_name = str(r.get("Producto", ""))
        pr = get_product_row(products, prod_name)
        if pr.empty:
            continue
        levels = float(r.get("Nivel total", 0) or 0)
        qty_base = levels * float(pr.get("produccion_h", 0) or 0)
        qty = qty_base * production_mult
        channel, net_u, gross_u, transport_cost_u = net_sale_price(prod_name, unit_costs, rows)
        cost_u = float(unit_costs.get(prod_name, {}).get("Costo/u", market_buy_price(prod_name, market_stats)))
        revenue_h = qty * net_u
        cost_h = qty * cost_u
        profit_h = revenue_h - cost_h
        total_revenue_h += revenue_h
        total_cost_h += cost_h
        total_profit_h += profit_h
        sell_rows.append({
            "Producto": prod_name,
            "Nivel total": int(levels),
            "Producción base/h": qty_base,
            "Producción efectiva/h": qty,
            "Canal": channel,
            "Precio bruto/u": gross_u,
            "Transporte/u": transport_cost_u,
            "Precio neto/u": net_u,
            "Costo/u": cost_u,
            "Beneficio/u": net_u - cost_u,
            "Beneficio/h": profit_h,
        })

    # Sobrantes/faltantes físicos
    balances = []
    surplus_profit_h = 0.0
    for input_name in sorted(set(list(outputs.keys()) + list(needs.keys()))):
        produced = float(outputs.get(input_name, 0.0))
        needed = float(needs.get(input_name, 0.0))
        balance = produced - needed
        uc = float(unit_costs.get(input_name, {}).get("Costo/u", market_buy_price(input_name, market_stats)))
        channel, net_u, _, _ = net_sale_price(input_name, unit_costs, rows)
        surplus_profit = 0.0
        if sell_surplus and balance > 0 and input_name not in [s["Producto"] for s in sell_rows]:
            # Vende solo excedentes de productos que no fueron vendidos como salida principal.
            surplus_profit = balance * (net_u - uc)
            surplus_profit_h += surplus_profit
        balances.append({
            "Producto/Insumo": input_name,
            "Producido/h": produced,
            "Necesario/h": needed,
            "Sobra/Falta/h": balance,
            "Costo propio/u": uc,
            "Precio neto venta/u": net_u,
            "Beneficio excedente/h": surplus_profit,
        })

    fixed_director_cost_h = float(total_director_salary_h)
    total_cost_h += fixed_director_cost_h
    total_profit_h = total_profit_h + surplus_profit_h - fixed_director_cost_h

    # Capital base aproximado: costo_n1 * niveles. No es upgrade exacto, solo proxy.
    cap_base = 0.0
    for r in rows:
        br = get_building_row(buildings, str(r.get("Edificio", "")))
        if br.empty:
            continue
        cap_base += float(br.get("costo_n1", 0) or 0) * float(r.get("Nivel total", 0) or 0)

    return {
        "Variante": label,
        "Filas": rows,
        "Ventas": sell_rows,
        "Balances": balances,
        "UnitCosts": unit_costs,
        "Ingreso neto/h": total_revenue_h,
        "Costo total/h": total_cost_h,
        "Costo directores/h": fixed_director_cost_h,
        "Beneficio principal/h": total_revenue_h - total_cost_h,
        "Beneficio excedentes/h": surplus_profit_h,
        "Beneficio real/h": total_profit_h,
        "Beneficio simulado": total_profit_h * float(analysis_hours),
        "Capital base aprox": cap_base,
        "ROI horas aprox": safe_div(cap_base, max(total_profit_h, 0.000001)) if total_profit_h > 0 else None,
        "Niveles totales": sum(int(r.get("Nivel total", 0) or 0) for r in rows),
    }


def simulate_scenario(scenario: dict, max_variants: int = 250) -> List[dict]:
    rows = active_rows_for_scenario(scenario)
    variants = expand_variants(rows, products, max_variants=max_variants)
    results = [simulate_variant(label, vrows, products, market_stats, fuente_df) for label, vrows in variants]
    return sorted(results, key=lambda r: r["Beneficio real/h"], reverse=True)

# Cálculos del escenario activo
results = simulate_scenario(scenario, max_variants=250)
if not results:
    st.warning("El escenario activo no tiene filas válidas para simular.")
    st.stop()

# ============================================================
# 6. Mercado / historial de precios
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">6. Mercado / historial de precios</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Precios públicos leídos del historial. La app usa la columna elegida en Configuración global.</div>', unsafe_allow_html=True)
    show_products = sorted(set(
        [str(r.get("Producto")) for r in active_rows_for_scenario(scenario) if str(r.get("Producto")) != "Simular opciones"]
        + list(REQ_MAP.keys()) + ["Transporte"]
        + products[products["edificio"].isin([str(r.get("Edificio")) for r in active_rows_for_scenario(scenario)])]["producto"].astype(str).tolist()
    ))
    market_view = market_stats[market_stats["producto"].isin(show_products)].copy()
    market_view = market_view.sort_values("producto")
    if market_view.empty:
        st.info("No hay productos de mercado para mostrar todavía.")
    else:
        st.dataframe(
            fmt_df_money(market_view, ["Último", "Mínimo", "Promedio", "Máximo", "precio_default"]),
            hide_index=True,
            use_container_width=True,
        )
        if not hist.empty:
            first = hist["fecha"].min()
            last = hist["fecha"].max()
            st.caption(f"Historial leído: {len(hist)} filas · desde {first} hasta {last}.")
        else:
            st.caption("No se encontró historial_mercado.csv. Se usan precios default/manuales.")

# ============================================================
# 7/8/9 Detalle del escenario activo
# ============================================================
summary_rows = []
for r in results:
    summary_rows.append({
        "Variante": r["Variante"],
        "Ingreso neto/h": r["Ingreso neto/h"],
        "Costo total/h": r["Costo total/h"],
        "Costo directores/h": r["Costo directores/h"],
        "Beneficio principal/h": r["Beneficio principal/h"],
        "Beneficio excedentes/h": r["Beneficio excedentes/h"],
        "Beneficio real/h": r["Beneficio real/h"],
        f"Beneficio {int(analysis_hours)}h": r["Beneficio simulado"],
        "Capital base aprox": r["Capital base aprox"],
        "ROI horas aprox": r["ROI horas aprox"],
    })
summary_df = pd.DataFrame(summary_rows)

with st.container(border=True):
    st.markdown('<div class="module-title">7. Beneficio real</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Ranking numérico de variantes del escenario activo. No decide por vos: solo muestra ingreso, costo y beneficio real.</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    best = results[0]
    k1.metric("Mayor beneficio/h", money(best["Beneficio real/h"]))
    k2.metric(f"Beneficio {int(analysis_hours)}h", money(best["Beneficio simulado"]))
    k3.metric("Ingreso neto/h", money(best["Ingreso neto/h"]))
    k4.metric("Costo total/h", money(best["Costo total/h"]))
    formatted_summary = fmt_df_money(summary_df, ["Ingreso neto/h", "Costo total/h", "Costo directores/h", "Beneficio principal/h", "Beneficio excedentes/h", "Beneficio real/h", f"Beneficio {int(analysis_hours)}h", "Capital base aprox", "ROI horas aprox"])
    st.dataframe(formatted_summary, hide_index=True, use_container_width=True, height=min(520, 120 + len(formatted_summary) * 35))

with st.container(border=True):
    st.markdown('<div class="module-title">8. Sobrantes / faltantes</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Balance físico por producto/insumo para la variante que selecciones.</div>', unsafe_allow_html=True)
    variant_names = [r["Variante"] for r in results]
    selected_variant_name = st.selectbox("Variante para ver detalle", variant_names, index=0)
    detail = next(r for r in results if r["Variante"] == selected_variant_name)
    bal_df = pd.DataFrame(detail["Balances"])
    if not bal_df.empty:
        st.dataframe(
            fmt_df_money(bal_df, ["Costo propio/u", "Precio neto venta/u", "Beneficio excedente/h"]),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Sin balances para mostrar.")

with st.container(border=True):
    st.markdown('<div class="module-title">9. Costos reales</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Desglose de costo unitario y venta para la variante seleccionada.</div>', unsafe_allow_html=True)
    vdf = pd.DataFrame(detail["Ventas"])
    if not vdf.empty:
        st.dataframe(
            fmt_df_money(vdf, ["Precio bruto/u", "Transporte/u", "Precio neto/u", "Costo/u", "Beneficio/u", "Beneficio/h"]),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No hay productos marcados como 'Vender salida'.")

    costs_table = pd.DataFrame(detail["UnitCosts"].values())
    if not costs_table.empty:
        show_costs = costs_table[costs_table["Producto"].isin(show_products + [str(v.get("Producto")) for v in detail["Ventas"]])].copy()
        if show_costs.empty:
            show_costs = costs_table.head(25).copy()
        st.markdown("**Costos unitarios calculados**")
        st.dataframe(
            fmt_df_money(show_costs, ["Costo/u", "Salario/u", "Insumos/u"]),
            hide_index=True,
            use_container_width=True,
        )

# ============================================================
# 10. Comparador de escenarios
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">10. Comparador de escenarios</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Compara empresas reales o simuladas. Muestra el mejor resultado calculado por cada escenario, sin recomendación automática.</div>', unsafe_allow_html=True)
    compare_rows = []
    for name, sc in st.session_state["scenarios"].items():
        try:
            sc_results = simulate_scenario(sc, max_variants=120)
            if not sc_results:
                continue
            r = sc_results[0]
            compare_rows.append({
                "Empresa / escenario": name,
                "Tipo": sc.get("tipo", "Simulada"),
                "Variante mostrada": r["Variante"],
                "Niveles": r["Niveles totales"],
                "Beneficio/h": r["Beneficio real/h"],
                f"Beneficio {int(analysis_hours)}h": r["Beneficio simulado"],
                "Capital base aprox": r["Capital base aprox"],
                "ROI horas aprox": r["ROI horas aprox"],
            })
        except Exception as e:
            compare_rows.append({
                "Empresa / escenario": name,
                "Tipo": sc.get("tipo", "Simulada"),
                "Variante mostrada": f"Error: {e}",
                "Niveles": 0,
                "Beneficio/h": 0,
                f"Beneficio {int(analysis_hours)}h": 0,
                "Capital base aprox": 0,
                "ROI horas aprox": None,
            })
    comp_df = pd.DataFrame(compare_rows)
    if not comp_df.empty:
        comp_df = comp_df.sort_values("Beneficio/h", ascending=False)
        st.dataframe(
            fmt_df_money(comp_df, ["Beneficio/h", f"Beneficio {int(analysis_hours)}h", "Capital base aprox", "ROI horas aprox"]),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No hay escenarios comparables.")

st.caption(
    "V2.4 modular: configuración global · escenarios · edificios · recetas base vs efectivo · fuentes de insumos · mercado · sobrantes/faltantes · costos · beneficio · comparador. "
    "El capital base aproximado usa costo N1 × niveles como proxy; los upgrades exactos quedan para una versión posterior."
)
