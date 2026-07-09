from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Market Lab - Producción",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Estilo visual
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #182338 0, #0c111b 38%, #080b10 100%);
        color: #eaf0ff;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #121a29 0%, #0b1018 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #aebbd4;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }
    .card {
        background: rgba(255,255,255,0.065);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 22px;
        padding: 18px 18px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.25);
        min-height: 116px;
    }
    .card h3 {
        color: #aebbd4;
        font-size: 0.83rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin: 0 0 8px 0;
    }
    .card .big {
        font-size: 1.75rem;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .card .small {
        color: #b8c2d9;
        font-size: 0.92rem;
    }
    .good { color: #55e68a !important; }
    .warn { color: #ffd166 !important; }
    .bad { color: #ff6b6b !important; }
    .muted { color: #aebbd4 !important; }
    .pill {
        display:inline-block;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 0.78rem;
        font-weight: 800;
        margin-right: 6px;
    }
    .pill-good { background: rgba(85,230,138,0.16); color: #55e68a; border: 1px solid rgba(85,230,138,0.30); }
    .pill-warn { background: rgba(255,209,102,0.16); color: #ffd166; border: 1px solid rgba(255,209,102,0.30); }
    .pill-bad { background: rgba(255,107,107,0.16); color: #ff6b6b; border: 1px solid rgba(255,107,107,0.30); }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        padding: 14px 16px;
        border-radius: 18px;
    }
    .dataframe tbody tr:hover { background: rgba(255,255,255,0.08); }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Utilidades
# -----------------------------

def money(x: float | int | None) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        x = float(x)
    except Exception:
        return "—"
    if abs(x) >= 1000:
        return f"${x:,.0f}".replace(",", ".")
    if abs(x) >= 10:
        return f"${x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"${x:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x: float | int | None) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{float(x)*100:.1f}%".replace(".", ",")


def num(x: float | int | None, dec: int = 2) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{float(x):,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def safe_div(a: float, b: float) -> float:
    return 0.0 if b == 0 else a / b


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    # Soporta dos formas de subida en GitHub:
    # 1) /data/archivo.csv (ideal)
    # 2) archivo.csv en la raíz del repo (por si GitHub aplana la subida)
    for path in [DATA / name, ROOT / name]:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_json(name: str) -> dict:
    for path in [DATA / name, ROOT / name]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


@st.cache_data(show_spinner=False)
def parse_market_history(path_str: str = "historial_mercado.csv") -> pd.DataFrame:
    """Lee historial aunque venga mezclado por versiones anteriores.

    Formatos soportados:
    - ticker nuevo: collected_at_utc,kind,quality,price
    - ticker sin header mezclado: fecha,kind,quality,price
    - profundidad antigua: fecha,kind,name,quality,min_price,...
    """
    path = ROOT / path_str
    if not path.exists():
        return pd.DataFrame(columns=["collected_at_utc", "kind", "quality", "price"])

    rows = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                if row[0].strip().lower() in {"collected_at_utc", "recopilado_en_utc"}:
                    continue
                # Formato ticker: fecha,kind,quality,price
                if len(row) >= 4:
                    # profundidad vieja: fecha,kind,name,quality,min_price,...
                    if len(row) >= 8 and not str(row[2]).replace(".", "", 1).isdigit():
                        fecha, kind, _name, quality, min_price = row[0], row[1], row[2], row[3], row[4]
                        rows.append([fecha, kind, quality, min_price])
                    else:
                        rows.append([row[0], row[1], row[2], row[3]])
    except Exception:
        return pd.DataFrame(columns=["collected_at_utc", "kind", "quality", "price"])

    df = pd.DataFrame(rows, columns=["collected_at_utc", "kind", "quality", "price"])
    if df.empty:
        return df
    df["collected_at_utc"] = pd.to_datetime(df["collected_at_utc"], errors="coerce", utc=True)
    df["kind"] = pd.to_numeric(df["kind"], errors="coerce")
    df["quality"] = pd.to_numeric(df["quality"], errors="coerce").fillna(0).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["collected_at_utc", "kind", "price"])
    df["kind"] = df["kind"].astype(int)
    return df.sort_values("collected_at_utc")


products = load_csv("productos_v1.csv")
buildings = load_csv("edificios_v1.csv")
robots_req = load_csv("robots_requeridos.csv")
config = load_json("configuracion_v1.json")
hist = parse_market_history()

product_name_by_kind = dict(zip(products["kind"], products["producto"])) if not products.empty else {}
kind_by_product = dict(zip(products["producto"], products["kind"])) if not products.empty else {}

# Últimos precios del historial o defaults del CSV
latest_prices: Dict[str, float] = {}
if not hist.empty:
    latest = hist.sort_values("collected_at_utc").groupby(["kind", "quality"], as_index=False).tail(1)
    latest_q0 = latest[latest["quality"] == 0]
    for _, r in latest_q0.iterrows():
        name = product_name_by_kind.get(int(r["kind"]))
        if name:
            latest_prices[name] = float(r["price"])

for _, r in products.iterrows():
    if r["producto"] not in latest_prices and not pd.isna(r.get("precio_default", math.nan)):
        latest_prices[r["producto"]] = float(r["precio_default"])

# Históricos por producto
hist_stats = {}
if not hist.empty:
    q0 = hist[hist["quality"] == 0].copy()
    if not q0.empty:
        for kind, g in q0.groupby("kind"):
            prices = g["price"].dropna()
            if len(prices) >= 3:
                hist_stats[int(kind)] = {
                    "p20": float(prices.quantile(0.20)),
                    "p50": float(prices.quantile(0.50)),
                    "p80": float(prices.quantile(0.80)),
                    "n": int(len(prices)),
                }

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## ⚙️ Mi empresa")
st.sidebar.caption("V1: Central + Embalse + Granja + Depósito de Embarque")

st.sidebar.markdown("## 🌍 Fase económica")
fase_options = ["Recesión", "Normal", "Boom"]
fase_default = config.get("fase_actual", "Normal")
if fase_default not in fase_options:
    fase_default = "Normal"
fase_actual = st.sidebar.selectbox("Fase actual del juego", fase_options, index=fase_options.index(fase_default))
mults = config.get("multiplicadores_fase", {})
phase_defaults = mults.get(fase_actual, {"produccion": 1.0, "salario": 1.0})
production_phase_mult = st.sidebar.number_input(
    "Multiplicador producción/h",
    min_value=0.50,
    max_value=1.50,
    value=float(phase_defaults.get("produccion", 1.0)),
    step=0.01,
    help="La fase cambia la velocidad/volumen de producción. Si no sabemos el número exacto, dejalo editable y lo calibramos contra tu juego.",
)
salary_phase_mult = st.sidebar.number_input(
    "Multiplicador salario/h",
    min_value=0.50,
    max_value=1.50,
    value=float(phase_defaults.get("salario", 1.0)),
    step=0.01,
    help="Según varias referencias, el salario base/h suele mantenerse; si tu interfaz lo muestra cambiado, ajustalo acá.",
)
st.sidebar.caption("Importante: las recetas por unidad no cambian; si cambia la producción/h, también escala el consumo/h de insumos.")

build_inputs = {}
for b in ["Central eléctrica", "Embalse de agua", "Granja", "Depósito de Embarque"]:
    default_qty = int(config.get("empresa_actual", {}).get(b, {}).get("cantidad", 0))
    default_lvl = int(config.get("empresa_actual", {}).get(b, {}).get("nivel", 1))
    with st.sidebar.expander(b, expanded=(b in ["Central eléctrica", "Embalse de agua", "Granja"])):
        qty = st.number_input(f"Cantidad - {b}", min_value=0, max_value=30, value=default_qty, step=1, key=f"qty_{b}")
        lvl = st.number_input(f"Nivel promedio - {b}", min_value=1, max_value=20, value=default_lvl, step=1, key=f"lvl_{b}")
        build_inputs[b] = {"cantidad": int(qty), "nivel": int(lvl), "niveles_totales": int(qty) * int(lvl)}

st.sidebar.markdown("---")
st.sidebar.markdown("## 🧾 Parámetros")
fee_market = st.sidebar.slider("Comisión mercado", 0.0, 0.10, float(config.get("comision_mercado", 0.04)), 0.005)
contract_discount = st.sidebar.slider("Descuento contrato", 0.0, 0.10, float(config.get("descuento_contrato", 0.03)), 0.005)
director_admin_reduction = st.sidebar.slider("Reducción administración por director", 0.0, 0.80, float(config.get("reduccion_admin_director", 0.0)), 0.01)

transport_mode = st.sidebar.radio(
    "Transporte para cálculos",
    ["Comprar en mercado", "Simular fabricación propia"],
    index=0,
    help="Aunque fabricarlo sea más barato, ocupa un slot. La app muestra la comparación.",
)

# Total de niveles y administración
sum_levels = sum(v["niveles_totales"] for v in build_inputs.values())
admin_base = max(0.0, (sum_levels - 1) / 170.0)
admin_final = admin_base * (1 - director_admin_reduction)

# Base building access
def b_row(name: str) -> pd.Series:
    m = buildings[buildings["edificio"] == name]
    if m.empty:
        return pd.Series(dtype="object")
    return m.iloc[0]

central = b_row("Central eléctrica")
embalse = b_row("Embalse de agua")
granja = b_row("Granja")
deposito = b_row("Depósito de Embarque")

central_levels = build_inputs["Central eléctrica"]["niveles_totales"]
embalse_levels = build_inputs["Embalse de agua"]["niveles_totales"]
granja_levels = build_inputs["Granja"]["niveles_totales"]
deposito_levels = build_inputs["Depósito de Embarque"]["niveles_totales"]

# Costos base propios
def salary_with_admin(row: pd.Series) -> float:
    if row.empty:
        return 0.0
    return float(row["salario_h"]) * salary_phase_mult * (1 + admin_final)

central_salary = salary_with_admin(central)
embalse_salary = salary_with_admin(embalse)
granja_salary = salary_with_admin(granja)
deposito_salary = salary_with_admin(deposito)

# Costos unitarios: asumimos producción y salarios lineales por nivel. En costo unitario, el nivel se cancela.
electricity_prod_h = float(central.get("produccion_h", 0) or 0) * production_phase_mult
electricity_cost = safe_div(central_salary, electricity_prod_h)

water_prod_h = float(embalse.get("produccion_h", 0) or 0) * production_phase_mult
water_electricity_need = float(embalse.get("electricidad_necesaria_h", 0) or 0) * production_phase_mult
water_cost = safe_div(embalse_salary + water_electricity_need * electricity_cost, water_prod_h)

seed_row = products[products["producto"] == "Semillas"].iloc[0]
seed_prod_h_phase = float(seed_row["produccion_h"]) * production_phase_mult
seed_water_h_phase = float(seed_row["agua_necesaria_h"]) * production_phase_mult
seed_cost = safe_div(
    granja_salary + seed_water_h_phase * water_cost,
    seed_prod_h_phase,
)

diesel_price = float(latest_prices.get("Diésel", config.get("precio_diesel_default", 40.75)))
transport_market_price = float(latest_prices.get("Transporte", config.get("precio_transporte_default", 0.389)))
transport_output_h = float(deposito.get("produccion_h", 0) or 0) * production_phase_mult
transport_cost_own = safe_div(
    deposito_salary
    + transport_output_h * (1 / 95) * electricity_cost
    + transport_output_h * (1 / 190) * diesel_price,
    transport_output_h,
)
transport_cost_used = transport_cost_own if transport_mode == "Simular fabricación propia" else transport_market_price

# -----------------------------
# Cálculos de productos
# -----------------------------
product_rows = []
for _, r in products.iterrows():
    p = r["producto"]
    kind = int(r["kind"])
    building = r.get("edificio", "")
    prod_h = float(r.get("produccion_h", 0) or 0) * production_phase_mult
    water_need = float(r.get("agua_necesaria_h", 0) or 0) * production_phase_mult
    seed_need = float(r.get("semillas_necesarias_h", 0) or 0) * production_phase_mult
    elec_need = float(r.get("electricidad_necesaria_h", 0) or 0) * production_phase_mult
    diesel_need = float(r.get("diesel_necesario_h", 0) or 0) * production_phase_mult
    transport_units = float(r.get("transporte_mercado", 0) or 0)
    price = float(latest_prices.get(p, r.get("precio_default", 0) or 0))

    if p == "Electricidad":
        cost = electricity_cost
        prod_h = electricity_prod_h
    elif p == "Agua":
        cost = water_cost
        prod_h = water_prod_h
    elif p == "Transporte":
        cost = transport_cost_own
        prod_h = transport_output_h
    elif building == "Granja":
        cost = safe_div(granja_salary + water_need * water_cost + seed_need * seed_cost, prod_h)
    elif building == "Depósito de Embarque":
        cost = safe_div(deposito_salary + elec_need * electricity_cost + diesel_need * diesel_price, prod_h)
    else:
        cost = float(r.get("costo_manual", 0) or 0)

    market_profit_u = price * (1 - fee_market) - cost - transport_units * transport_cost_used
    contract_price = price * (1 - contract_discount)
    contract_profit_u = contract_price - cost - (transport_units / 2) * transport_cost_used
    best_channel = "Contrato" if contract_profit_u > market_profit_u else "Mercado"
    best_profit_u = max(market_profit_u, contract_profit_u)
    best_profit_h = best_profit_u * prod_h

    stats = hist_stats.get(kind, {})
    p20 = stats.get("p20")
    p50 = stats.get("p50")
    p80 = stats.get("p80")
    n_points = stats.get("n", 0)
    if p20 is None:
        estado = "sin historial"
    elif price <= p20:
        estado = "barato"
    elif price >= p80:
        estado = "caro"
    else:
        estado = "normal"

    product_rows.append(
        {
            "Producto": p,
            "ID": kind,
            "Edificio": building,
            "Producción/h": prod_h,
            "Costo propio": cost,
            "Precio actual": price,
            "P20": p20,
            "Mediana": p50,
            "P80": p80,
            "Estado precio": estado,
            "Transp. mercado": transport_units,
            "Beneficio/u mercado": market_profit_u,
            "Beneficio/h mercado": market_profit_u * prod_h,
            "Beneficio/u contrato": contract_profit_u,
            "Beneficio/h contrato": contract_profit_u * prod_h,
            "Mejor canal": best_channel,
            "Beneficio/h mejor": best_profit_h,
            "Puntos hist.": n_points,
        }
    )

prod_df = pd.DataFrame(product_rows)

# Solo productos actuales de interés
farm_products = prod_df[prod_df["Edificio"].isin(["Granja", "Central eléctrica", "Embalse de agua", "Depósito de Embarque"])].copy()

# -----------------------------
# Simulación de combinaciones
# -----------------------------

def effective_water_capacity(central_lv: int, embalse_lv: int) -> Tuple[float, str]:
    elec_cap = central_lv * electricity_prod_h
    embalse_water_cap = embalse_lv * water_prod_h
    if water_electricity_need <= 0:
        return embalse_water_cap, "agua"
    water_cap_by_elec = safe_div(elec_cap, water_electricity_need) * water_prod_h
    if water_cap_by_elec < embalse_water_cap:
        return water_cap_by_elec, "electricidad"
    return embalse_water_cap, "agua"


def simulate_scenario(central_lv: int, embalse_lv: int, granja_lv: int) -> pd.DataFrame:
    rows = []
    water_cap, water_bottleneck = effective_water_capacity(central_lv, embalse_lv)
    seed_prod = float(seed_row["produccion_h"]) * production_phase_mult
    seed_water = float(seed_row["agua_necesaria_h"]) * production_phase_mult

    for _, r in products[products["edificio"] == "Granja"].iterrows():
        p = r["producto"]
        prod_h = float(r["produccion_h"]) * production_phase_mult
        water_direct = float(r["agua_necesaria_h"]) * production_phase_mult
        seeds_need = float(r["semillas_necesarias_h"]) * production_phase_mult

        if p == "Semillas":
            max_crop_lv_by_farm = granja_lv
            max_crop_lv_by_water = safe_div(water_cap, water_direct) if water_direct else granja_lv
            crop_lv = min(max_crop_lv_by_farm, max_crop_lv_by_water)
            seed_lv = 0.0
        else:
            seed_lv_per_crop_lv = safe_div(seeds_need, seed_prod)
            water_per_crop_lv_with_seeds = water_direct + seed_lv_per_crop_lv * seed_water
            max_crop_lv_by_farm = safe_div(granja_lv, 1 + seed_lv_per_crop_lv)
            max_crop_lv_by_water = safe_div(water_cap, water_per_crop_lv_with_seeds) if water_per_crop_lv_with_seeds else max_crop_lv_by_farm
            crop_lv = min(max_crop_lv_by_farm, max_crop_lv_by_water)
            seed_lv = crop_lv * seed_lv_per_crop_lv

        output = crop_lv * prod_h
        pr = prod_df[prod_df["Producto"] == p].iloc[0]
        best_profit_u = max(float(pr["Beneficio/u mercado"]), float(pr["Beneficio/u contrato"]))
        best_channel = pr["Mejor canal"]
        total_profit = output * best_profit_u
        limiting = "slots/granjas"
        if crop_lv < max_crop_lv_by_farm - 1e-6:
            limiting = water_bottleneck

        rows.append(
            {
                "Cultivo": p,
                "Canal": best_channel,
                "Granjas cultivo": crop_lv,
                "Granjas semillas": seed_lv,
                "Output/h": output,
                "Beneficio/h": total_profit,
                "Cuello de botella": limiting,
            }
        )
    return pd.DataFrame(rows).sort_values("Beneficio/h", ascending=False)

current_sim = simulate_scenario(central_levels, embalse_levels, granja_levels)

scenarios = []
scenario_defs = [
    ("Actual", central_levels, embalse_levels, granja_levels, deposito_levels),
    ("+ 1 Granja", central_levels, embalse_levels, granja_levels + 1, deposito_levels),
    ("+ 1 Embalse", central_levels, embalse_levels + 1, granja_levels, deposito_levels),
    ("+ 1 Central", central_levels + 1, embalse_levels, granja_levels, deposito_levels),
    ("+ 1 Depósito", central_levels, embalse_levels, granja_levels, deposito_levels + 1),
]
for name, c_lv, e_lv, g_lv, d_lv in scenario_defs:
    sim = simulate_scenario(c_lv, e_lv, g_lv)
    if not sim.empty:
        best = sim.iloc[0]
        scenarios.append(
            {
                "Escenario": name,
                "Mejor cultivo": best["Cultivo"],
                "Canal": best["Canal"],
                "Beneficio/h estimado": float(best["Beneficio/h"]),
                "Output/h": float(best["Output/h"]),
                "Cuello": best["Cuello de botella"],
            }
        )
scenario_df = pd.DataFrame(scenarios)

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">🏭 Market Lab — Producción & Edificios</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Dashboard visual para decidir qué fabricar, qué vender, y qué edificio sumar sin regalar mercadería ni comprar caro.</div>',
    unsafe_allow_html=True,
)

# Top cards
best_prod = prod_df.sort_values("Beneficio/h mejor", ascending=False).iloc[0] if not prod_df.empty else None
best_scenario = scenario_df.sort_values("Beneficio/h estimado", ascending=False).iloc[0] if not scenario_df.empty else None
water_cap, water_limit_type = effective_water_capacity(central_levels, embalse_levels)
transport_saving = transport_market_price - transport_cost_own

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""
        <div class="card">
            <h3>Fase + administración</h3>
            <div class="big">{fase_actual}</div>
            <div class="small">Admin {pct(admin_final)} · prod x{production_phase_mult:.2f} · salario x{salary_phase_mult:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="card">
            <h3>Mejor producto directo</h3>
            <div class="big good">{best_prod['Producto'] if best_prod is not None else '—'}</div>
            <div class="small">{money(best_prod['Beneficio/h mejor']) + '/h' if best_prod is not None else '—'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
        <div class="card">
            <h3>Próximo slot</h3>
            <div class="big warn">{best_scenario['Escenario'] if best_scenario is not None else '—'}</div>
            <div class="small">{best_scenario['Mejor cultivo'] if best_scenario is not None else '—'} · {money(best_scenario['Beneficio/h estimado']) + '/h' if best_scenario is not None else '—'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""
        <div class="card">
            <h3>Transporte</h3>
            <div class="big {'good' if transport_saving > 0 else 'warn'}">{money(transport_cost_used)}</div>
            <div class="small">Mercado {money(transport_market_price)} · propio {money(transport_cost_own)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📌 Resumen", "🌾 Productos", "⚙️ Simulador", "🏗️ Próximo edificio", "🤖 Robots", "📚 Datos que faltan"]
)

with tab1:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Diagnóstico rápido")
        if current_sim.empty:
            st.warning("No hay datos suficientes para simular.")
        else:
            b = current_sim.iloc[0]
            st.markdown(
                f"""
                <div class="card">
                <h3>Mejor uso de tus granjas actuales</h3>
                <div class="big good">{b['Cultivo']}</div>
                <div class="small">Canal recomendado: <b>{b['Canal']}</b> · Beneficio estimado: <b>{money(b['Beneficio/h'])}/h</b></div>
                <br>
                <span class="pill pill-warn">Cuello: {b['Cuello de botella']}</span>
                <span class="pill pill-good">Output: {num(b['Output/h'], 1)}/h</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("### Costos internos calculados")
        cost_cards = pd.DataFrame(
            [
                ["Electricidad propia", money(electricity_cost)],
                ["Agua propia", money(water_cost)],
                ["Semillas propias", money(seed_cost)],
                ["Transporte mercado", money(transport_market_price)],
                ["Transporte propio", money(transport_cost_own)],
                ["Diésel mercado", money(diesel_price)],
            ],
            columns=["Concepto", "Costo unitario"],
        )
        st.dataframe(cost_cards, hide_index=True, use_container_width=True)

    with right:
        st.subheader("Capacidades")
        st.metric("Electricidad/h", num(central_levels * electricity_prod_h, 1))
        st.metric("Agua efectiva/h", num(water_cap, 1), help="Limitada por embalses o por electricidad disponible")
        st.metric("Granjas nivel-equivalente", num(granja_levels, 0))
        st.metric("Administración final", pct(admin_final))

with tab2:
    st.subheader("Ranking de productos")
    view = prod_df.copy()
    view["Costo propio"] = view["Costo propio"].map(money)
    view["Precio actual"] = view["Precio actual"].map(money)
    view["Beneficio/h mercado"] = view["Beneficio/h mercado"].map(money)
    view["Beneficio/h contrato"] = view["Beneficio/h contrato"].map(money)
    view["Beneficio/h mejor"] = view["Beneficio/h mejor"].map(money)
    view["P20"] = view["P20"].map(money)
    view["Mediana"] = view["Mediana"].map(money)
    view["P80"] = view["P80"].map(money)
    cols = [
        "Producto", "Precio actual", "Estado precio", "Costo propio", "Mejor canal",
        "Beneficio/h mercado", "Beneficio/h contrato", "Beneficio/h mejor", "P20", "Mediana", "P80", "Puntos hist."
    ]
    st.dataframe(view[cols], hide_index=True, use_container_width=True)
    st.caption("Estado precio usa P20/P80 si ya hay historial suficiente. Al principio puede aparecer 'sin historial'.")

with tab3:
    st.subheader("Simulador de producción con semillas propias")
    st.caption("Calcula cuántas granjas de cultivo y cuántas granjas de semillas harían falta para sostener cada producto usando tus embalses y centrales.")
    sim_view = current_sim.copy()
    sim_view["Beneficio/h"] = sim_view["Beneficio/h"].map(money)
    for c in ["Granjas cultivo", "Granjas semillas", "Output/h"]:
        sim_view[c] = sim_view[c].map(lambda x: num(x, 2))
    st.dataframe(sim_view, hide_index=True, use_container_width=True)

    selected_crop = st.selectbox("Ver detalle de cultivo", current_sim["Cultivo"].tolist() if not current_sim.empty else [])
    if selected_crop:
        det = current_sim[current_sim["Cultivo"] == selected_crop].iloc[0]
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Granjas cultivo", num(det["Granjas cultivo"], 2))
        d2.metric("Granjas semillas", num(det["Granjas semillas"], 2))
        d3.metric("Output/h", num(det["Output/h"], 1))
        d4.metric("Beneficio/h", money(det["Beneficio/h"]))

with tab4:
    st.subheader("Comparador del próximo edificio")
    st.caption("Compara el próximo slot contra tu situación actual. La opción ganadora no siempre es la más obvia: puede depender del cuello de botella.")
    if not scenario_df.empty:
        sc = scenario_df.copy()
        sc["Beneficio/h estimado"] = sc["Beneficio/h estimado"].map(money)
        sc["Output/h"] = sc["Output/h"].map(lambda x: num(x, 1))
        st.dataframe(sc, hide_index=True, use_container_width=True)
        chart_df = scenario_df.set_index("Escenario")[["Beneficio/h estimado"]]
        st.bar_chart(chart_df)
    else:
        st.warning("No se pudieron simular escenarios.")

    st.markdown("### Transporte: comprar vs producir")
    t1, t2, t3 = st.columns(3)
    t1.metric("Comprar transporte", money(transport_market_price))
    t2.metric("Fabricar transporte", money(transport_cost_own))
    t3.metric("Ahorro por unidad", money(transport_saving))
    st.info("Aunque fabricar transporte salga más barato por unidad, ocupa un slot. La decisión correcta es comparar el ahorro/h contra lo que generaría ese slot como granja, embalse u otro edificio.")

with tab5:
    st.subheader("Robots y especialización")
    st.markdown(
        """
        Los robots no se tratan como una mejora automática. En esta V1 los usamos como análisis de **payback**:
        si instalar robots te ahorra X por hora, ¿cuántas horas tardás en recuperar el costo?
        """
    )
    selected_building = st.selectbox("Edificio", robots_req["edificio"].unique().tolist() if not robots_req.empty else [])
    if selected_building:
        rview = robots_req[robots_req["edificio"] == selected_building].copy()
        st.dataframe(rview, hide_index=True, use_container_width=True)

    st.markdown("### Calculadora simple de payback")
    rb1, rb2, rb3 = st.columns(3)
    with rb1:
        robot_count = st.number_input("Cantidad de robots", min_value=0, value=1, step=1)
    with rb2:
        robot_price = st.number_input("Precio por robot", min_value=0.0, value=float(latest_prices.get("Robots", 260.0)), step=1.0)
    with rb3:
        extra_profit_h = st.number_input("Ganancia extra/h esperada", min_value=0.0, value=10.0, step=1.0)
    total_robot_cost = robot_count * robot_price
    payback_hours = safe_div(total_robot_cost, extra_profit_h)
    st.metric("Costo robots", money(total_robot_cost))
    st.metric("Payback", f"{num(payback_hours, 1)} horas" if payback_hours else "—")
    st.warning("Regla práctica: si vas a subir de nivel o destruir/cambiar ese edificio pronto, no instales robots todavía.")

with tab6:
    st.subheader("Datos que faltan para expandir a otros mercados")
    st.markdown(
        """
        Para agregar otros edificios sin inventar números, necesito cargar sus recetas. La app ya está preparada para crecer, pero cada edificio/producto nuevo debe tener estos campos.
        """
    )
    needed = pd.DataFrame(
        [
            ["Producto", "Nombre exacto del producto"],
            ["ID/kind", "ID del recurso en el ticker"],
            ["Edificio", "Qué edificio lo fabrica"],
            ["Producción/h", "Unidades por hora por nivel/building base"],
            ["Insumos", "Qué consume por hora o por unidad"],
            ["Transporte mercado", "Unidades de transporte para vender en mercado"],
            ["Salario edificio", "Salario/h sin administración"],
            ["Construcción/mejora", "Costo, materiales y tiempo si vamos a planificar edificios"],
            ["Robots", "Cantidad y calidad requerida por nivel"],
        ],
        columns=["Dato", "Para qué sirve"],
    )
    st.dataframe(needed, hide_index=True, use_container_width=True)
    st.info("Para la cadena actual ya están cargadas Central, Embalse, Granja y Depósito. Para otros edificios conviene ir agregándolos de a uno o por cadena completa.")

st.markdown("---")
st.caption("V1.1 — Modelo inicial con fase económica editable. Producción y consumo/h escalan por fase; salarios/h quedan editables porque deben calibrarse contra tu interfaz del juego.")
