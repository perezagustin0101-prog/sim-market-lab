from __future__ import annotations

import csv
import itertools
import json
import html
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"

import base64
from io import StringIO

FALLBACK_CSV_B64 = {
    "productos_v1.csv": "a2luZCxwcm9kdWN0byxlZGlmaWNpbyxwcm9kdWNjaW9uX2gsYWd1YV9uZWNlc2FyaWFfaCxzZW1pbGxhc19uZWNlc2FyaWFzX2gsZWxlY3RyaWNpZGFkX25lY2VzYXJpYV9oLGRpZXNlbF9uZWNlc2FyaW9faCx0cmFuc3BvcnRlX21lcmNhZG8scHJlY2lvX2RlZmF1bHQsY29zdG9fbWFudWFsDQoxMyxUcmFuc3BvcnRlLERlcMOzc2l0byBkZSBFbWJhcnF1ZSwzMjA2LjAxMSwwLDAsMzMuNzQ3NDg0LDE2Ljg3Mzc0MiwwLDAuMzg5LDANCjEsRWxlY3RyaWNpZGFkLENlbnRyYWwgZWzDqWN0cmljYSwyNTkyLjg3LDAsMCwwLDAsMCwwLjI3NywwDQoyLEFndWEsRW1iYWxzZSBkZSBhZ3VhLDE2NDIuODYsMCwwLDMyOC41NywwLDAsMC4zNzcsMA0KNjYsU2VtaWxsYXMsR3JhbmphLDg5OC42Miw4OS44NjE1LDAsMCwwLDAuMSwwLjI3LDANCjMsTWFuemFuYXMsR3JhbmphLDIwNC4yMyw2MTIuNjkzLDIwNC4yLDAsMCwxLDIuNywwDQo0LE5hcmFuamFzLEdyYW5qYSwxODcuOSw1NjMuNjc2LDE4Ny45LDAsMCwxLDIuNywwDQo1LFV2YXMsR3JhbmphLDE2My4zOSw2NTMuNTQsMTYzLjQsMCwwLDEsMy40LDANCjYsR3Jhbm8sR3JhbmphLDgxNi45Miw0MDguNDYxNSw4MTYuOSwwLDAsMC4xLDAuNzQ1LDANCjQwLEFsZ29kw7NuLEdyYW5qYSwyNjEuNDIsMjYxLjQsMjYxLjQsMCwwLDAuNSwxLjU3LDANCjcyLENhw7FhIGRlIGF6w7pjYXIsR3JhbmphLDYzNS41NCwxOTA2LjYxNCw2MzUuNSwwLDAsMC4xLDEuNzIsMA0KMTA2LE1hZGVyYSxHcmFuamEsNzcuNjEsMzEwLjQzMiw3Ny42LDAsMCwxLDQuMTUsMA0KMTE4LEdyYW5vcyBkZSBjYWbDqSxHcmFuamEsNDE2LjYzLDIwOC4zMTU1LDQxNi42LDAsMCwwLjEsMC44MDUsMA0KMTIwLFZlcmR1cmFzLEdyYW5qYSwyODUuOTIsNTcxLjg0NiwxNDI5LjYxNSwwLDAsMC4yLDIuNywwDQoxMzYsQ2FjYW8sR3JhbmphLDE3MS41NSwxNzEuNiwxNzEuNiwwLDAsMC4xLDEuNjgsMA0KMTIsRGnDqXNlbCwsMCwwLDAsMCwwLDAsNDAuNzUsMA0KMTE0LFJvYm90cywsMCwwLDAsMCwwLDAsMjYwLjAsMA0K",
    "edificios_v1.csv": "ZWRpZmljaW8scHJvZHVjdG9fcHJpbmNpcGFsLHNhbGFyaW9faCxwcm9kdWNjaW9uX2gsZWxlY3RyaWNpZGFkX25lY2VzYXJpYV9oLHZhbG9yX3JlZmVyZW5jaWFfbjEsY29zdG9fbjEsdGllbXBvX24xX2gsbm90YXMNCkNlbnRyYWwgZWzDqWN0cmljYSxFbGVjdHJpY2lkYWQsNDE0LDI1OTIuODcsMCw1MTc1MCw1Njc2MSwzLFByb2R1Y2UgZWxlY3RyaWNpZGFkOyBubyBjb25zdW1lIGluc3Vtb3MgZsOtc2ljb3MuDQpFbWJhbHNlIGRlIGFndWEsQWd1YSwzNDUsMTY0Mi44NiwzMjguNTcsMjA3MDAsMjI2NjYsMixQcm9kdWNlIGFndWEgdXNhbmRvIGVsZWN0cmljaWRhZCBwcm9waWEuDQpHcmFuamEsVmFyaW9zIGN1bHRpdm9zLDEwNCwwLDAsNjkwMCw3NTU1LDEsUHJvZHVjZSBjdWx0aXZvczsgY2FkYSBjdWx0aXZvIHRpZW5lIHByb2R1Y2Npw7NuIGUgaW5zdW1vcyBwcm9waW9zLg0KRGVww7NzaXRvIGRlIEVtYmFycXVlLFRyYW5zcG9ydGUsMzExLDMyMDYuMDExLDAsNTE3NTAsNTY3ODUsMyxQcm9kdWNlIHVuaWRhZGVzIGRlIHRyYW5zcG9ydGUgdXNhbmRvIGVsZWN0cmljaWRhZCB5IGRpw6lzZWwuDQo=",
}

def _fallback_csv(name: str) -> pd.DataFrame:
    raw = FALLBACK_CSV_B64.get(name)
    if not raw:
        return pd.DataFrame()
    return pd.read_csv(StringIO(base64.b64decode(raw).decode("utf-8")))


st.set_page_config(
    page_title="Sim Companies Business Simulator V2.20 estable visual",
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
    /* Compacto sin romper textos: no tocamos agresivamente line-height global ni gaps internos. */
    .block-container {padding-top: 1.6rem; padding-bottom: 1.2rem; max-width: 96vw;}
    h1 {line-height: 1.22 !important; margin-top: .25rem !important; margin-bottom: .45rem !important; padding-top: .15rem !important;}
    h2, h3 {line-height: 1.25 !important;}
    div[data-testid="stMetric"] {background: rgba(250,250,250,.025); border: 1px solid rgba(128,128,128,.18); padding: .55rem .70rem; border-radius: .70rem; min-height: 4.1rem;}
    div[data-testid="stMetricLabel"] {font-size: .88rem; line-height: 1.2;}
    div[data-testid="stMetricValue"] {font-size: 1.40rem; line-height: 1.25;}
    label, .stSelectbox label, .stNumberInput label, .stMultiSelect label, .stCheckbox label {font-size: .86rem !important; line-height: 1.25 !important; margin-bottom: .18rem !important;}
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: .70rem; padding-top: .55rem; padding-bottom: .55rem;}
    div[data-testid="column"] {padding-left: .28rem !important; padding-right: .28rem !important;}
    .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div, .stNumberInput input {min-height: 2.45rem !important; font-size: .94rem !important;}
    .stButton button {min-height: 2.35rem !important; padding: .25rem .75rem !important; font-size: .92rem !important;}
    .module-title {font-size: 1.18rem; font-weight: 800; margin: .18rem 0 .45rem 0; line-height:1.30; clear:both;}
    .module-sub {font-size: .88rem; color: #8a8f98; margin: .10rem 0 .55rem 0; line-height:1.35;}
    .soft-card {border: 1px solid rgba(128,128,128,.22); border-radius: .75rem; padding: .70rem; margin-bottom: .55rem;}
    .line-card {border: 1px solid rgba(128,128,128,.20); border-radius: .75rem; padding: .60rem .75rem; margin-bottom: .45rem;}
    .small-note {font-size: .84rem; color: #8a8f98; line-height:1.30;}
    .inline-kpis {display:grid; grid-template-columns: repeat(6, minmax(8.2rem, 1fr)); gap:.28rem; margin-top:.35rem; margin-bottom:.12rem;}
    .inline-kpi {border:1px solid rgba(128,128,128,.18); border-radius:.48rem; padding:.32rem .48rem; background:rgba(250,250,250,.018); min-width: 0;}
    .inline-label {font-size:.78rem; color:#8a8f98; line-height:1.20; white-space:nowrap;}
    .inline-value {font-size:1.00rem; font-weight:700; line-height:1.25; margin-top:.06rem; white-space:nowrap;}
    .req-line {font-size:.82rem; color:#8a8f98; margin-top:.18rem; line-height:1.30;}
    .line-title {font-weight:800; margin:.10rem 0 .35rem 0; line-height:1.25;}
    .summary-strip {display:grid; grid-template-columns: repeat(4, minmax(8rem, 1fr)); gap:.35rem; margin-top:.35rem;}
    .summary-chip {border:1px solid rgba(128,128,128,.18); border-radius:.55rem; padding:.45rem .65rem; min-width: 0; background:rgba(250,250,250,.015);}
    @media (max-width: 1200px) {
      .inline-kpis {grid-template-columns: repeat(3, minmax(8rem, 1fr));}
      .summary-strip {grid-template-columns: repeat(2, minmax(8rem, 1fr));}
    }
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


def safe_rerun() -> None:
    rerun_fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if rerun_fn is not None:
        rerun_fn()


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    """Carga CSV del repo. Si GitHub/Upload lo dejó roto (una sola línea o sin filas), usa fallback embebido."""
    for path in [ROOT / name, DATA / name]:
        if path.exists():
            try:
                df = pd.read_csv(path)
                # Si el CSV quedó pegado en una sola línea, pandas suele devolver 0 filas o columnas raras.
                if name in {"productos_v1.csv", "edificios_v1.csv"}:
                    min_cols = {"productos_v1.csv": {"kind", "producto", "edificio"}, "edificios_v1.csv": {"edificio", "salario_h"}}[name]
                    if (not df.empty) and min_cols.issubset(set(df.columns)):
                        return df
                else:
                    return df
            except Exception:
                pass
    fb = _fallback_csv(name)
    return fb if not fb.empty else pd.DataFrame()


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
DIRECTOR_EFFECT_COLUMNS = ["Reducción admin %", "Mejora contable $", "Aumento ventas %", "Patentes +pp"]
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
    if "Mejora contable $" not in out.columns:
        if "Mejora contable $M" in out.columns:
            out["Mejora contable $"] = pd.to_numeric(out["Mejora contable $M"], errors="coerce").fillna(0) * 1_000_000.0
        elif "Lift contable $M" in out.columns:
            out["Mejora contable $"] = pd.to_numeric(out["Lift contable $M"], errors="coerce").fillna(0) * 1_000_000.0
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
    out["Mejora contable $"] = [round_half_up(v * 1_000_000.0, 0) for v in accounting_vals]
    out["Aumento ventas %"] = [round_half_up(v, 1) for v in sales_vals]
    out["Patentes +pp"] = [round_half_up(v, 1) for v in science_vals]

    # Limpieza de columnas viejas que venían de versiones anteriores.
    for old_col in [
        "Perfil", "Puesto asignado", "Puesto asignado ", "Lift contable $M", "Mejora contable $M", "Puesto viejo",
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
st.title("Sim Companies Business Simulator V2.20")
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
        source_data_bonus_pct = st.number_input(
            "Bonus incluido en datos cargados (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(config_raw.get("bonus_incluido_datos_pct", 1.0)),
            step=1.0,
            format="%.2f",
            help="Si los valores cargados fueron copiados desde tu juego con bonus activo, la app los divide por este porcentaje para reconstruir la base.",
        )

    market_fee = market_fee_pct / 100.0
    contract_discount = contract_discount_pct / 100.0

    st.markdown("**Directores**")
    directores_base = add_director_effects(st.session_state["directores"]).copy()
    editor_cols = DIRECTOR_INPUT_COLUMNS
    directores_inputs = directores_base[editor_cols].copy()

    with st.form("form_directores_v29", clear_on_submit=False):
        directores_editados = st.data_editor(
            directores_inputs,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Activo": st.column_config.CheckboxColumn("Activo"),
                "Nombre": st.column_config.TextColumn("Nombre"),
                "Puesto": st.column_config.SelectboxColumn("Puesto", options=DIRECTOR_ROLE_OPTIONS),
                "Management": st.column_config.NumberColumn("Gestión", min_value=0, max_value=999, step=1),
                "Accounting": st.column_config.NumberColumn("Contabilidad", min_value=0, max_value=999, step=1),
                "Communication": st.column_config.NumberColumn("Comunicación", min_value=0, max_value=999, step=1),
                "Science": st.column_config.NumberColumn("Ciencia", min_value=0, max_value=999, step=1),
                "Salario diario": st.column_config.NumberColumn("Salario diario", min_value=0.0, step=100.0, format="$%.1f"),
            },
            key="directores_v29_editor",
        )
        aplicar_directores = st.form_submit_button("Aplicar directores", use_container_width=False)

    if aplicar_directores:
        st.session_state["directores"] = add_director_effects(directores_editados).copy()
        safe_rerun()

    directores_df = add_director_effects(st.session_state["directores"]).copy()

    active_directors = directores_df[directores_df["Activo"]] if (not directores_df.empty and "Activo" in directores_df.columns) else pd.DataFrame()
    total_director_salary_day = float(active_directors["Salario diario"].sum()) if not active_directors.empty else 0.0
    total_director_salary_h = total_director_salary_day / 24.0

    director_reduction_pct_total = float(active_directors["Reducción admin %"].sum()) if not active_directors.empty else 0.0
    director_sales_pct_total = float(active_directors["Aumento ventas %"].sum()) if not active_directors.empty else 0.0
    director_accounting_effect = float(active_directors["Mejora contable $"].sum()) if not active_directors.empty else 0.0
    director_science_pct_total = float(active_directors["Patentes +pp"].sum()) if not active_directors.empty else 0.0

    # Tabla de resultados separada del editor: evita errores de Streamlit con columnas calculadas/formateadas.
    rendimiento_directores = directores_df[[
        "Activo", "Nombre", "Puesto", "Reducción admin %", "Mejora contable $", "Aumento ventas %", "Patentes +pp"
    ]].copy()
    rendimiento_directores = rendimiento_directores.rename(columns={
        "Reducción admin %": "Reducción administrativa",
        "Mejora contable $": "Mejora contable",
        "Aumento ventas %": "Aumento de ventas",
        "Patentes +pp": "Probabilidad de patente",
    })
    rendimiento_directores["Reducción administrativa"] = rendimiento_directores["Reducción administrativa"].map(lambda v: pct_plain(v, 1))
    rendimiento_directores["Mejora contable"] = rendimiento_directores["Mejora contable"].map(money)
    rendimiento_directores["Aumento de ventas"] = rendimiento_directores["Aumento de ventas"].map(lambda v: pct_plain(v, 1))
    rendimiento_directores["Probabilidad de patente"] = rendimiento_directores["Probabilidad de patente"].map(lambda v: pct_plain(v, 1))

    with st.expander("Ver rendimiento estimado por director", expanded=False):
        st.dataframe(rendimiento_directores, hide_index=True, use_container_width=True)

    director_reduction = max(0.0, min(0.95, director_reduction_pct_total / 100.0))
    production_bonus_pct_total = production_bonus_pct_manual
    retail_bonus_pct_total = retail_bonus_pct_manual + director_sales_pct_total
    production_mult = max(0.10, 1.0 + production_bonus_pct_total / 100.0)
    source_data_mult = max(0.10, 1.0 + source_data_bonus_pct / 100.0)

    def base_rate(row: Any, col: str) -> float:
        try:
            return float(row.get(col, 0) or 0) / source_data_mult
        except Exception:
            return 0.0

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

# Admin estimada usada por la vista rápida de cada línea. Se recalcula con las líneas activas antes de mostrar métricas.
admin_pct = 0.0

# ============================================================
# 2. Línea de producción
# ============================================================
def _line_uid() -> str:
    st.session_state["line_uid_counter"] = int(st.session_state.get("line_uid_counter", 0)) + 1
    return f"linea_{st.session_state['line_uid_counter']}"


def all_building_options(products: pd.DataFrame, buildings: pd.DataFrame) -> List[str]:
    opts = []
    if not buildings.empty and "edificio" in buildings.columns:
        opts += buildings["edificio"].dropna().astype(str).tolist()
    if not products.empty and "edificio" in products.columns:
        opts += products["edificio"].dropna().astype(str).tolist()
    clean = []
    for x in opts:
        if x and x not in clean:
            clean.append(x)
    return clean or ["Granja"]


def product_options_for_line(products: pd.DataFrame, edificio: str) -> List[str]:
    opts = products[(products["edificio"].astype(str) == str(edificio)) & (products["produccion_h"] > 0)]["producto"].dropna().astype(str).tolist()
    if not opts:
        opts = products[products["produccion_h"] > 0]["producto"].dropna().astype(str).tolist()
    opts = [x for x in opts if x]
    return opts or ["Simular opciones"]


def make_empty_line(building: str | None = None, product: str | None = None) -> dict:
    b_opts = all_building_options(products, buildings)
    b = building or (b_opts[0] if b_opts else "Granja")
    p_opts = product_options_for_line(products, b)
    p = product or (p_opts[0] if p_opts else "Simular opciones")
    return {
        "uid": _line_uid(),
        "activo": True,
        "edificio": b,
        "producto": p,
        "nivel_total": 1,
        "fuentes": {},
        "sobrante": "Vender en mercado",
    }


def ensure_production_lines() -> None:
    if "production_lines" not in st.session_state:
        st.session_state["production_lines"] = []
    fixed = []
    for line in st.session_state.get("production_lines", []):
        if not isinstance(line, dict):
            continue
        line.setdefault("uid", _line_uid())
        line.setdefault("activo", True)
        line.setdefault("edificio", "Granja")
        line.setdefault("producto", "Simular opciones")
        line.setdefault("nivel_total", 1)
        # Migración: en versiones anteriores el proveedor elegía a qué línea abastecía.
        # Desde V2.16 cada línea consumidora elige de dónde se abastece.
        line.setdefault("fuentes", {})
        if not isinstance(line.get("fuentes"), dict):
            line["fuentes"] = {}
        line.setdefault("sobrante", "Vender en mercado")
        fixed.append(line)
    st.session_state["production_lines"] = fixed


def line_label(line: dict, idx: int) -> str:
    return f"Línea {idx + 1}: {line.get('edificio', '')} → {line.get('producto', '')}"


def safe_product_row_for_line(producto: str) -> pd.Series:
    try:
        return get_product_row(products, str(producto))
    except Exception:
        return pd.Series(dtype=object)


def _line_output_unit_cost(line: dict, all_lines: List[dict], stack: Tuple[str, ...] = ()) -> float:
    """Costo unitario integrado de una línea.

    Si un insumo está abastecido por otra línea, usa el costo unitario de esa línea.
    Si no está abastecido por ninguna línea activa, usa precio de mercado.
    Esto corrige el caso de algodón: no cuesta igual usar agua propia que agua comprada.
    """
    uid = str(line.get("uid", ""))
    if uid and uid in stack:
        return 0.0
    s = line_physical_summary(line, all_lines, stack=stack)
    return float(s.get("costo_u", 0.0) or 0.0)


def _input_unit_cost(input_name: str, current_uid: str, all_lines: List[dict], stack: Tuple[str, ...] = ()) -> Tuple[float, str]:
    """Costo del insumo elegido por la línea consumidora.

    Desde V2.16 NO se toma automáticamente producción propia.
    Cada línea decide en su campo "Se abastece de" si compra en mercado
    o si usa otra línea que produce ese insumo.
    """
    current = None
    for line in all_lines:
        if str(line.get("uid", "")) == str(current_uid):
            current = line
            break

    chosen = "Mercado"
    if isinstance(current, dict):
        fuentes = current.get("fuentes", {})
        if isinstance(fuentes, dict):
            chosen = str(fuentes.get(input_name, "Mercado") or "Mercado")

    if chosen not in {"", "Mercado"}:
        supplier = None
        for other in all_lines:
            if not bool(other.get("activo", True)):
                continue
            if str(other.get("uid", "")) != chosen:
                continue
            if str(other.get("producto", "")) != str(input_name):
                continue
            supplier = other
            break
        if supplier is not None:
            suid = str(supplier.get("uid", ""))
            if not (suid and suid in stack):
                sc = _line_output_unit_cost(supplier, all_lines, stack=stack + (str(current_uid),))
                return float(sc), "Propio"

    return price_of(input_name, market_stats, price_mode), "Mercado"


def _line_production_h(line: dict) -> float:
    prod_name = str(line.get("producto", ""))
    levels = float(line.get("nivel_total", 0) or 0)
    pr = safe_product_row_for_line(prod_name)
    if pr.empty:
        return 0.0
    return levels * base_rate(pr, "produccion_h") * production_mult


def line_physical_summary(line: dict, all_lines: List[dict] | None = None, stack: Tuple[str, ...] = ()) -> dict:
    """Resumen rápido visual por línea.

    Usa costo integrado cuando el insumo viene de otra línea que abastece a esta.
    Si no hay abastecimiento propio, usa precio de mercado.
    """
    if all_lines is None:
        all_lines = []
    prod_name = str(line.get("producto", ""))
    edificio = str(line.get("edificio", ""))
    uid = str(line.get("uid", ""))
    levels = float(line.get("nivel_total", 0) or 0)
    pr = safe_product_row_for_line(prod_name)
    br = get_building_row(buildings, edificio)

    prod_base_h = 0.0 if pr.empty else levels * base_rate(pr, "produccion_h")
    prod_eff_h = prod_base_h * production_mult

    salary_level_h = 0.0 if br.empty else float(br.get("salario_h", 0) or 0) * (1 + admin_pct)
    salary_h = salary_level_h * levels

    reqs = {}
    req_sources = {}
    input_cost_h = 0.0
    if not pr.empty:
        for input_name, col in REQ_MAP.items():
            req_h = levels * base_rate(pr, col) * production_mult
            reqs[input_name] = req_h
            if req_h > 0:
                unit_cost, source = _input_unit_cost(input_name, uid, all_lines, stack=stack + ((uid,) if uid else tuple()))
                req_sources[input_name] = source
                input_cost_h += req_h * unit_cost

    total_cost_h = salary_h + input_cost_h
    cost_u = safe_div(total_cost_h, prod_eff_h)
    price_u = price_of(prod_name, market_stats, price_mode)

    transport_need = 0.0 if pr.empty else float(pr.get("transporte_mercado", 0) or 0)
    transport_price = price_of("Transporte", market_stats, price_mode)
    action = str(line.get("sobrante", "Vender en mercado"))
    if action == "Vender por contrato":
        net_u = price_u * (1 - contract_discount) - transport_need * transport_price * CONTRACT_TRANSPORT_FACTOR
    elif action == "Almacenar":
        net_u = 0.0
    else:
        net_u = price_u * (1 - market_fee) - transport_need * transport_price

    return {
        "produccion_base_h": prod_base_h,
        "produccion_h": prod_eff_h,
        "requisitos_h": reqs,
        "fuentes_requisitos": req_sources,
        "salario_h": salary_h,
        "insumos_h": input_cost_h,
        "costo_h": total_cost_h,
        "costo_u": cost_u,
        "precio_u": price_u,
        "neto_u": net_u,
        "beneficio_u_aprox": net_u - cost_u if action != "Almacenar" else 0.0,
    }

def line_needs_input(target_line: dict, input_product: str) -> float:
    col = REQ_MAP.get(str(input_product))
    if not col:
        return 0.0
    pr = safe_product_row_for_line(str(target_line.get("producto", "")))
    if pr.empty:
        return 0.0
    levels = float(target_line.get("nivel_total", 0) or 0)
    return levels * base_rate(pr, col) * production_mult


def line_supply_summary(line: dict, all_lines: List[dict]) -> dict:
    own = line_physical_summary(line, all_lines)
    prod_name = str(line.get("producto", ""))
    uid = str(line.get("uid", ""))
    demanda_asignada_h = 0.0

    # Una línea abastece solamente si otra línea la eligió explícitamente en "Se abastece de".
    # Se usan las líneas YA actualizadas de la pantalla actual; esto evita que el sobrante se calcule
    # con niveles viejos cuando editás una línea de abajo.
    for other in all_lines:
        if not bool(other.get("activo", True)):
            continue
        fuentes = other.get("fuentes", {})
        if not isinstance(fuentes, dict):
            continue
        if str(fuentes.get(prod_name, "")) == uid:
            demanda_asignada_h += line_needs_input(other, prod_name)

    # Para tomar decisiones interesa ver el balance: producción - demanda asignada.
    # Si da negativo, no hay sobrante: hay faltante. Lo dejamos negativo para que sea visible.
    sobrante_h = own["produccion_h"] - demanda_asignada_h
    action = str(line.get("sobrante", "Vender en mercado"))
    valor_sobrante_h = 0.0
    if sobrante_h > 0 and action != "Almacenar":
        valor_sobrante_h = sobrante_h * max(own["neto_u"] - own["costo_u"], 0.0)
    own.update({
        "abastece_h": demanda_asignada_h,
        "sobrante_h": sobrante_h,
        "valor_sobrante_h": valor_sobrante_h,
    })
    return own


def render_line_metrics(line: dict, all_lines: List[dict]) -> None:
    s = line_supply_summary(line, all_lines)
    reqs = {k: v for k, v in s.get("requisitos_h", {}).items() if abs(float(v or 0)) > 0.0001}
    req_sources = s.get("fuentes_requisitos", {}) or {}
    req_text = "Sin insumos" if not reqs else " · ".join([f"{k}: {num(v, 1)}/h ({req_sources.get(k, 'Mercado')})" for k, v in reqs.items()])
    items = [
        ("Producción/h", num(s["produccion_h"], 1)),
        ("Costo/h", money1(s["costo_h"])),
        ("Costo/u", money(s["costo_u"])),
        ("Abastece/h", num(s["abastece_h"], 1)),
        ("Sobrante/h", num(s["sobrante_h"], 1)),
        ("Valor sobrante/h", money1(s["valor_sobrante_h"])),
    ]
    cards = "".join([
        f'<div class="inline-kpi"><div class="inline-label">{html.escape(label)}</div><div class="inline-value">{html.escape(str(value))}</div></div>'
        for label, value in items
    ])
    st.markdown(
        f'<div class="inline-kpis">{cards}</div><div class="req-line">Requiere/h: {html.escape(req_text)}</div>',
        unsafe_allow_html=True,
    )


ensure_production_lines()

with st.container(border=True):
    st.markdown('<div class="module-title">2. Línea de producción</div>', unsafe_allow_html=True)
    btn1, btn2, spacer = st.columns([1, 1, 3])
    with btn1:
        if st.button("Agregar línea", use_container_width=True):
            st.session_state["production_lines"].append(make_empty_line())
            safe_rerun()
    with btn2:
        if st.button("Vaciar empresa", use_container_width=True):
            st.session_state["production_lines"] = []
            safe_rerun()

    building_options = all_building_options(products, buildings)
    lines = st.session_state["production_lines"]

    if not lines:
        st.info("La empresa está vacía. Agregá una línea para empezar a simular.")

    labels_by_uid = {line.get("uid", f"linea_{i}"): line_label(line, i) for i, line in enumerate(lines)}
    updated_lines = []
    metric_slots = []
    metric_lines = []
    remove_uid = None

    for i, line in enumerate(lines):
        uid = line.get("uid", f"linea_{i}")
        with st.container(border=True):
            st.markdown(f'<div class="line-title">{html.escape(line_label(line, i))}</div>', unsafe_allow_html=True)
            c0, c1, c2, c3, c4, c5 = st.columns([0.55, 1.55, 1.55, 0.75, 1.35, 0.65])
            with c0:
                activo = st.checkbox("Activa", value=bool(line.get("activo", True)), key=f"activo_{uid}")
            with c1:
                current_building = str(line.get("edificio", building_options[0] if building_options else "Granja"))
                if current_building not in building_options:
                    building_options = [current_building] + building_options
                edificio = st.selectbox("Edificio", building_options, index=building_options.index(current_building), key=f"edificio_{uid}")
            with c2:
                p_opts = product_options_for_line(products, edificio)
                current_product = str(line.get("producto", p_opts[0] if p_opts else "Simular opciones"))
                if current_product not in p_opts:
                    current_product = p_opts[0] if p_opts else "Simular opciones"
                producto = st.selectbox("Produce", p_opts, index=p_opts.index(current_product), key=f"producto_{uid}")
            with c3:
                nivel = st.number_input("Nivel", min_value=0, max_value=999, value=int(line.get("nivel_total", 1) or 0), step=1, key=f"nivel_{uid}")
            with c4:
                sob_options = ["Vender en mercado", "Vender por contrato", "Almacenar"]
                current_sob = str(line.get("sobrante", "Vender en mercado"))
                if current_sob not in sob_options:
                    current_sob = "Vender en mercado"
                sobrante = st.selectbox("Sobrante", sob_options, index=sob_options.index(current_sob), key=f"sobrante_{uid}")
            with c5:
                if st.button("Quitar", key=f"quitar_{uid}", use_container_width=True):
                    remove_uid = uid

            # Fuentes de insumos físicas. No toma producción propia automáticamente:
            # si querés usar tu central/embalse/semillera, hay que elegir esa línea acá.
            pr_for_sources = safe_product_row_for_line(producto)
            current_sources = line.get("fuentes", {}) if isinstance(line.get("fuentes", {}), dict) else {}
            fuentes = {}
            req_inputs = []
            if not pr_for_sources.empty:
                for input_name, col in REQ_MAP.items():
                    need_h_tmp = float(nivel or 0) * base_rate(pr_for_sources, col) * production_mult
                    if need_h_tmp > 0:
                        req_inputs.append(input_name)

            if req_inputs:
                source_cols = st.columns(min(len(req_inputs), 4))
                for j, input_name in enumerate(req_inputs):
                    provider_options = ["Mercado"]
                    for other in lines:
                        if str(other.get("uid", "")) == str(uid):
                            continue
                        if not bool(other.get("activo", True)):
                            continue
                        if str(other.get("producto", "")) == str(input_name):
                            provider_options.append(str(other.get("uid", "")))
                    current_source = str(current_sources.get(input_name, "Mercado") or "Mercado")
                    if current_source not in provider_options:
                        current_source = "Mercado"
                    with source_cols[j % len(source_cols)]:
                        fuentes[input_name] = st.selectbox(
                            f"Se abastece de · {input_name}",
                            provider_options,
                            index=provider_options.index(current_source),
                            format_func=lambda x, _input=input_name: "Mercado" if x == "Mercado" else labels_by_uid.get(x, str(x)),
                            key=f"fuente_{uid}_{input_name}",
                        )
            else:
                st.markdown('<div class="req-line">Se abastece de: solo dinero / sin insumos físicos</div>', unsafe_allow_html=True)

            current_line_data = {
                "uid": uid,
                "activo": bool(activo),
                "edificio": edificio,
                "producto": producto,
                "nivel_total": int(nivel),
                "fuentes": fuentes,
                "sobrante": sobrante,
            }
            # La vista rápida se dibuja después de leer TODAS las líneas visibles.
            # Así el sobrante de una línea usa los niveles/fuentes actuales de las líneas siguientes,
            # no los valores viejos guardados en sesión.
            metric_slots.append(st.empty())
            metric_lines.append(current_line_data)
            updated_lines.append(current_line_data)

    if remove_uid:
        st.session_state["production_lines"] = [x for x in updated_lines if x.get("uid") != remove_uid]
        safe_rerun()
    else:
        st.session_state["production_lines"] = updated_lines

    # Recalcular administración y métricas visuales con TODAS las líneas ya actualizadas.
    try:
        display_total_levels = sum(
            int(x.get("nivel_total", 0) or 0)
            for x in updated_lines
            if bool(x.get("activo", True))
        )
        admin_pct = max(0.0, (display_total_levels - 1) / 170.0) * (1 - director_reduction)
    except Exception:
        admin_pct = 0.0

    for slot, line_data in zip(metric_slots, metric_lines):
        with slot.container():
            render_line_metrics(line_data, updated_lines)

    scenario_rows = []
    for line in st.session_state["production_lines"]:
        action = str(line.get("sobrante", "Vender en mercado"))
        scenario_rows.append({
            "Activo": bool(line.get("activo", True)),
            "Edificio": str(line.get("edificio", "")),
            "Producto": str(line.get("producto", "")),
            "Nivel total": int(line.get("nivel_total", 0) or 0),
            "Vender salida": action in ["Vender en mercado", "Vender por contrato"],
            "Sobrante": action,
            "Fuentes": dict(line.get("fuentes", {})) if isinstance(line.get("fuentes", {}), dict) else {},
        })
    scenario = {"rows": scenario_rows}
    st.session_state["active_company"] = scenario
    if "scenarios" in st.session_state:
        st.session_state["scenarios"]["Mi empresa actual"] = {"tipo": "Real", "descripcion": "Empresa cargada en líneas", "cash": 0, "deuda": 0, "rows": scenario_rows}

    active_buildings_df = pd.DataFrame(scenario_rows)
    if not active_buildings_df.empty:
        active_mask = active_buildings_df["Activo"].fillna(False).astype(bool) & (pd.to_numeric(active_buildings_df["Nivel total"], errors="coerce").fillna(0) > 0)
        active_buildings_df = active_buildings_df[active_mask].copy()
    total_levels = int(pd.to_numeric(active_buildings_df.get("Nivel total", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not active_buildings_df.empty else 0
    used_building_rows = int(len(active_buildings_df)) if not active_buildings_df.empty else 0
    products_to_sell = int(active_buildings_df.get("Vender salida", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if not active_buildings_df.empty else 0
    stored_outputs = int((active_buildings_df.get("Sobrante", pd.Series(dtype=str)).astype(str) == "Almacenar").sum()) if not active_buildings_df.empty else 0
    admin_pct = max(0.0, (total_levels - 1) / 170.0) * (1 - director_reduction)

    st.markdown(
        '<div class="summary-strip">'
        f'<div class="summary-chip"><div class="inline-label">Niveles totales</div><div class="inline-value">{total_levels}</div></div>'
        f'<div class="summary-chip"><div class="inline-label">Líneas activas</div><div class="inline-value">{used_building_rows}</div></div>'
        f'<div class="summary-chip"><div class="inline-label">Salidas a vender</div><div class="inline-value">{products_to_sell}</div></div>'
        f'<div class="summary-chip"><div class="inline-label">Salidas a almacenar</div><div class="inline-value">{stored_outputs}</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# 3. Productos / recetas
# ============================================================
# ============================================================
# 3. Productos / recetas
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">3. Productos / recetas</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-sub">Base editable de producción y requisitos. La app corrige el bonus incluido en datos cargados y muestra base vs efectivo.</div>', unsafe_allow_html=True)

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
                    prod_base = niveles * base_rate(prr, "produccion_h")
                    agua_base = niveles * base_rate(prr, "agua_necesaria_h")
                    semillas_base = niveles * base_rate(prr, "semillas_necesarias_h")
                    electricidad_base = niveles * base_rate(prr, "electricidad_necesaria_h")
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
        st.caption("Base corregida = dato cargado ÷ bonus incluido. Efectiva = base corregida × bonus de producción cargado.")
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
# 4. Fuente de insumos
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">4. Fuente de insumos</div>', unsafe_allow_html=True)
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
        qty = float(r.get("Nivel total", 0) or 0) * base_rate(pr, "produccion_h") * production_mult
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
        if pr.empty or base_rate(pr, "produccion_h") <= 0:
            price = market_buy_price(producto, market_stats)
            return {"Producto": producto, "Costo/u": price, "Salario/u": 0.0, "Insumos/u": price, "Detalle": "sin receta -> mercado"}

        edificio = str(pr.get("edificio", ""))
        prod_h = base_rate(pr, "produccion_h") * production_mult
        sal_u = safe_div(salary_per_level(edificio), prod_h)
        ins_u = 0.0
        details = []
        for input_name, col in REQ_MAP.items():
            need_h = base_rate(pr, col) * production_mult
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


def net_sale_price(producto: str, unit_costs: Dict[str, dict], rows: List[dict], action: str | None = None) -> Tuple[str, float, float, float]:
    pr = get_product_row(products, producto)
    price = market_buy_price(producto, market_stats)
    tr_need = float(pr.get("transporte_mercado", 0) or 0) if not pr.empty else 0.0
    tr_u = transport_unit_cost(rows, unit_costs, market_stats, fuente_df)
    market_net = price * (1 - market_fee) - tr_need * tr_u
    contract_net = price * (1 - contract_discount) - tr_need * tr_u * CONTRACT_TRANSPORT_FACTOR
    mode = sale_mode
    if action == "Vender en mercado":
        mode = "Mercado"
    elif action == "Vender por contrato":
        mode = "Contrato"
    elif action == "Almacenar":
        return "Almacenar", 0.0, price, 0.0
    if mode == "Mercado":
        return "Mercado", market_net, price, tr_need * tr_u
    if mode == "Contrato":
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
        qty_base = levels * base_rate(pr, "produccion_h")
        qty = qty_base * production_mult
        outputs[prod_name] = outputs.get(prod_name, 0.0) + qty
        for input_name, col in REQ_MAP.items():
            needs[input_name] = needs.get(input_name, 0.0) + levels * base_rate(pr, col) * production_mult

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
        qty_base = levels * base_rate(pr, "produccion_h")
        qty = qty_base * production_mult
        channel, net_u, gross_u, transport_cost_u = net_sale_price(prod_name, unit_costs, rows, str(r.get("Sobrante", "")))
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
# 5. Mercado / historial de precios
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">5. Mercado / historial de precios</div>', unsafe_allow_html=True)
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
# 6/7/8 Detalle de la empresa activa
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
    st.markdown('<div class="module-title">6. Beneficio real</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="module-title">7. Sobrantes / faltantes</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="module-title">8. Costos reales</div>', unsafe_allow_html=True)
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
# 9. Comparador de escenarios
# ============================================================
with st.container(border=True):
    st.markdown('<div class="module-title">9. Comparador de escenarios</div>', unsafe_allow_html=True)
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
    "V2.19: línea de producción compacta sin achicar la letra, métricas en una sola franja y fuentes por línea. "
    "El capital base aproximado usa costo N1 × niveles como proxy; los upgrades exactos quedan para una versión posterior."
)
