from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Market Lab — Plan Simple",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# Estilo
# =============================
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #17213a 0, #0b1020 42%, #070a10 100%);
        color: #eef3ff;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #090d16 100%);
        border-right: 1px solid rgba(255,255,255,0.09);
    }
    .title {
        font-size: 2.45rem;
        line-height: 1.05;
        font-weight: 950;
        letter-spacing: -0.05em;
        margin-bottom: 0.15rem;
    }
    .subtitle {
        color: #aab7d4;
        font-size: 1.02rem;
        margin-bottom: 1.15rem;
    }
    .hero {
        background: linear-gradient(135deg, rgba(55, 111, 255, 0.18), rgba(30, 207, 129, 0.10));
        border: 1px solid rgba(255,255,255,0.11);
        border-radius: 26px;
        padding: 22px 24px;
        box-shadow: 0 22px 50px rgba(0,0,0,0.28);
        margin-bottom: 18px;
    }
    .card {
        background: rgba(255,255,255,0.065);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 22px;
        padding: 17px 18px;
        min-height: 112px;
        box-shadow: 0 18px 42px rgba(0,0,0,0.23);
    }
    .card h3 {
        color: #aab7d4;
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin: 0 0 8px 0;
    }
    .big {
        font-size: 1.85rem;
        font-weight: 950;
        color: white;
        margin: 0;
    }
    .small { color: #b8c4dc; font-size: .93rem; }
    .good { color: #59e68b !important; }
    .warn { color: #ffd166 !important; }
    .bad { color: #ff6b6b !important; }
    .muted { color: #aab7d4 !important; }
    .pill {
        display:inline-block;
        border-radius: 999px;
        padding: 6px 11px;
        margin: 4px 5px 4px 0;
        font-size: .80rem;
        font-weight: 850;
        border: 1px solid rgba(255,255,255,.14);
        background: rgba(255,255,255,.07);
    }
    .pill-good { background: rgba(89,230,139,.15); color:#59e68b; border-color: rgba(89,230,139,.32); }
    .pill-warn { background: rgba(255,209,102,.16); color:#ffd166; border-color: rgba(255,209,102,.32); }
    .pill-blue { background: rgba(91,141,255,.17); color:#8eb0ff; border-color: rgba(91,141,255,.32); }
    .section-title {
        font-size: 1.35rem;
        font-weight: 900;
        margin-top: .2rem;
        margin-bottom: .55rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        padding: 14px 16px;
        border-radius: 18px;
    }
    .stDataFrame { border-radius: 18px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Utilidades
# =============================
def money(x) -> str:
    if x is None or pd.isna(x):
        return "—"
    x = float(x)
    if abs(x) >= 1000:
        return f"${x:,.0f}".replace(",", ".")
    if abs(x) >= 10:
        return f"${x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"${x:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")


def num(x, dec=1) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{float(x):,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{float(x) * 100:.1f}%".replace(".", ",")


def safe_div(a: float, b: float) -> float:
    return 0.0 if abs(float(b)) < 1e-12 else float(a) / float(b)


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
    path = ROOT / "historial_mercado.csv"
    if not path.exists():
        return pd.DataFrame(columns=["fecha", "kind", "quality", "price"])

    rows = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                if row[0].strip().lower() in {"collected_at_utc", "recopilado_en_utc"}:
                    continue
                if len(row) >= 8 and not str(row[2]).replace(".", "", 1).isdigit():
                    # Formato antiguo de profundidad: fecha,kind,name,quality,min_price,...
                    rows.append([row[0], row[1], row[3], row[4]])
                elif len(row) >= 4:
                    # Ticker nuevo: fecha,kind,quality,price
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


products = load_csv("productos_v1.csv")
buildings = load_csv("edificios_v1.csv")
config = load_json("configuracion_v1.json")
hist = parse_market_history()

if products.empty or buildings.empty:
    st.error("Faltan productos_v1.csv o edificios_v1.csv. Subilos al repo junto con app.py.")
    st.stop()

name_by_kind = dict(zip(products["kind"], products["producto"]))
latest_prices: Dict[str, float] = {}
if not hist.empty:
    latest = hist[hist["quality"] == 0].sort_values("fecha").groupby("kind", as_index=False).tail(1)
    for _, r in latest.iterrows():
        name = name_by_kind.get(int(r["kind"]))
        if name:
            latest_prices[name] = float(r["price"])
for _, r in products.iterrows():
    latest_prices.setdefault(str(r["producto"]), float(r.get("precio_default", 0) or 0))

# Historial resumido
hist_stats = {}
if not hist.empty:
    q0 = hist[hist["quality"] == 0]
    for kind, g in q0.groupby("kind"):
        ps = g["price"].dropna()
        if len(ps) >= 3:
            hist_stats[int(kind)] = {
                "p20": float(ps.quantile(0.20)),
                "p50": float(ps.quantile(0.50)),
                "p80": float(ps.quantile(0.80)),
                "n": int(len(ps)),
            }


def get_building(name: str) -> pd.Series:
    m = buildings[buildings["edificio"] == name]
    return m.iloc[0] if not m.empty else pd.Series(dtype="object")


def get_product(name: str) -> pd.Series:
    m = products[products["producto"] == name]
    return m.iloc[0] if not m.empty else pd.Series(dtype="object")

central = get_building("Central eléctrica")
embalse = get_building("Embalse de agua")
granja = get_building("Granja")
deposito = get_building("Depósito de Embarque")
seed_product = get_product("Semillas")

# =============================
# Sidebar simple
# =============================
st.sidebar.markdown("# ⚙️ Plan simple")
st.sidebar.caption("Sin nivel promedio, sin mil ajustes. Primero: slots y venta en mercado.")

slots = st.sidebar.number_input("Cantidad de slots disponibles", min_value=3, max_value=30, value=int(config.get("slots_actuales", 6)), step=1)
sale_mode = st.sidebar.radio("Canal de venta", ["Mercado", "Contrato", "Mejor automático"], index=0)
consider_depot = st.sidebar.checkbox("Permitir Depósito de Embarque", value=False, help="Por ahora lo dejo apagado porque ocupa un slot. Sirve solo si consumís muchísimo transporte.")
sell_surplus = st.sidebar.checkbox("Vender excedentes", value=True, help="Vende electricidad, agua o semillas sobrantes para flujo de caja.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Fase")
fase = st.sidebar.selectbox("Fase económica", ["Recesión", "Normal", "Boom"], index=1)
st.sidebar.caption("Por ahora dejá los multiplicadores en 1 si no tenés el dato exacto de la fase.")
with st.sidebar.expander("Ajustes avanzados", expanded=False):
    production_mult = st.number_input("Multiplicador producción", 0.50, 1.50, 1.00, 0.01)
    salary_mult = st.number_input("Multiplicador salario", 0.50, 1.50, 1.00, 0.01)
    market_fee = st.slider("Comisión mercado", 0.0, 0.10, float(config.get("comision_mercado", 0.04)), 0.005)
    contract_discount = st.slider("Descuento contrato", 0.0, 0.10, float(config.get("descuento_contrato", 0.03)), 0.005)
    director_reduction = st.slider("Reducción administración director", 0.0, 0.80, float(config.get("reduccion_admin_director", 0.0)), 0.01)

# =============================
# Modelo económico simple: todos nivel 1
# =============================
admin_base = max(0.0, (slots - 1) / 170.0)
admin_final = admin_base * (1 - director_reduction)

central_salary = float(central["salario_h"]) * salary_mult * (1 + admin_final)
embalse_salary = float(embalse["salario_h"]) * salary_mult * (1 + admin_final)
granja_salary = float(granja["salario_h"]) * salary_mult * (1 + admin_final)
deposito_salary = float(deposito["salario_h"]) * salary_mult * (1 + admin_final)

central_prod = float(central["produccion_h"]) * production_mult
embalse_prod = float(embalse["produccion_h"]) * production_mult
embalse_elec_need = float(embalse["electricidad_necesaria_h"]) * production_mult
seed_prod = float(seed_product["produccion_h"]) * production_mult
seed_water_need = float(seed_product["agua_necesaria_h"]) * production_mult

electricity_unit_cost = safe_div(central_salary, central_prod)
water_unit_cost = safe_div(embalse_salary + embalse_elec_need * electricity_unit_cost, embalse_prod)
seed_unit_cost = safe_div(granja_salary + seed_water_need * water_unit_cost, seed_prod)

diesel_price = float(latest_prices.get("Diésel", config.get("precio_diesel_default", 40.75)))
transport_market_price = float(latest_prices.get("Transporte", config.get("precio_transporte_default", 0.389)))
transport_output = float(deposito["produccion_h"]) * production_mult
transport_own_cost = safe_div(
    deposito_salary + transport_output * (1/95) * electricity_unit_cost + transport_output * (1/190) * diesel_price,
    transport_output,
)
transport_unit_cost = transport_market_price  # V1 simple: se compra. El depósito se compara aparte.


def net_price_market(product_name: str) -> float:
    price = float(latest_prices.get(product_name, 0) or 0)
    tr = float(get_product(product_name).get("transporte_mercado", 0) or 0)
    return price * (1 - market_fee) - tr * transport_unit_cost


def net_price_contract(product_name: str) -> float:
    price = float(latest_prices.get(product_name, 0) or 0)
    tr = float(get_product(product_name).get("transporte_mercado", 0) or 0)
    return price * (1 - contract_discount) - (tr / 2) * transport_unit_cost


def chosen_net_price(product_name: str) -> tuple[str, float]:
    m = net_price_market(product_name)
    c = net_price_contract(product_name)
    if sale_mode == "Mercado":
        return "Mercado", m
    if sale_mode == "Contrato":
        return "Contrato", c
    return ("Contrato", c) if c > m else ("Mercado", m)


def physical_water_capacity(central_slots: int, embalse_slots: int) -> tuple[float, float, float]:
    """Devuelve agua real/h, electricidad total/h, electricidad sobrante/h."""
    elec_total = central_slots * central_prod
    elec_for_embalse_full = embalse_slots * embalse_elec_need
    embalse_water_full = embalse_slots * embalse_prod
    if elec_for_embalse_full <= elec_total:
        water = embalse_water_full
        elec_surplus = elec_total - elec_for_embalse_full
    else:
        water = safe_div(elec_total, embalse_elec_need) * embalse_prod
        elec_surplus = 0.0
    return water, elec_total, elec_surplus


def product_unit_cost(crop_name: str) -> float:
    r = get_product(crop_name)
    prod = float(r.get("produccion_h", 0) or 0) * production_mult
    water_need = float(r.get("agua_necesaria_h", 0) or 0) * production_mult
    seed_need = float(r.get("semillas_necesarias_h", 0) or 0) * production_mult
    return safe_div(granja_salary + water_need * water_unit_cost + seed_need * seed_unit_cost, prod)


def simulate_plan(central_slots: int, embalse_slots: int, seed_farms: int, crop_farms: int, depot_slots: int, crop_name: str) -> dict:
    water_cap, elec_total, elec_surplus = physical_water_capacity(central_slots, embalse_slots)
    r = get_product(crop_name)

    crop_prod_per_farm = float(r["produccion_h"]) * production_mult
    crop_water_per_farm = float(r["agua_necesaria_h"]) * production_mult
    crop_seed_per_farm = float(r["semillas_necesarias_h"]) * production_mult

    seed_production = seed_farms * seed_prod
    seed_water = seed_farms * seed_water_need

    # Primero se alimenta el bloque de semillas.
    if seed_water > water_cap and seed_water > 0:
        seed_factor = water_cap / seed_water
        seed_production_real = seed_production * seed_factor
        water_left = 0.0
    else:
        seed_factor = 1.0
        seed_production_real = seed_production
        water_left = water_cap - seed_water

    crop_output_full = crop_farms * crop_prod_per_farm
    crop_water_full = crop_farms * crop_water_per_farm
    crop_seed_full = crop_farms * crop_seed_per_farm

    factor_by_water = 1.0 if crop_water_full <= 0 else min(1.0, safe_div(water_left, crop_water_full))
    factor_by_seed = 1.0 if crop_seed_full <= 0 else min(1.0, safe_div(seed_production_real, crop_seed_full))
    crop_factor = min(factor_by_water, factor_by_seed)

    output = crop_output_full * crop_factor
    seeds_used = crop_seed_full * crop_factor
    water_used_crop = crop_water_full * crop_factor
    water_used = min(seed_water, water_cap) + water_used_crop

    seeds_surplus = max(0.0, seed_production_real - seeds_used)
    water_surplus = max(0.0, water_cap - water_used)
    elec_surplus = max(0.0, elec_surplus)

    channel, net_u = chosen_net_price(crop_name)
    cost_u = product_unit_cost(crop_name)
    profit_u = net_u - cost_u
    crop_profit_h = output * profit_u

    surplus_profit = 0.0
    surplus_items = []
    if sell_surplus:
        for pname, qty, unit_cost in [
            ("Electricidad", elec_surplus, electricity_unit_cost),
            ("Agua", water_surplus, water_unit_cost),
            ("Semillas", seeds_surplus, seed_unit_cost),
        ]:
            if qty <= 1e-9:
                continue
            surplus_channel, net_surplus = ("Mercado", net_price_market(pname))
            profit_surplus_u = net_surplus - unit_cost
            profit_surplus_h = qty * profit_surplus_u
            surplus_profit += profit_surplus_h
            surplus_items.append({
                "Producto": pname,
                "Cantidad/h": qty,
                "Beneficio/u": profit_surplus_u,
                "Beneficio/h": profit_surplus_h,
            })

    bottlenecks = []
    if factor_by_seed < 0.999:
        bottlenecks.append("semillas")
    if factor_by_water < 0.999 or seed_factor < 0.999:
        bottlenecks.append("agua")
    if embalse_slots > 0 and elec_total < embalse_slots * embalse_elec_need - 1e-9:
        bottlenecks.append("electricidad")
    if not bottlenecks:
        bottlenecks.append("sin cuello fuerte")

    return {
        "Producto": crop_name,
        "Canal": channel,
        "Central": central_slots,
        "Embalse": embalse_slots,
        "Granja semillas": seed_farms,
        "Granja venta": crop_farms,
        "Depósito": depot_slots,
        "Slots usados": central_slots + embalse_slots + seed_farms + crop_farms + depot_slots,
        "Producción vendible/h": output,
        "Beneficio cultivo/h": crop_profit_h,
        "Beneficio excedentes/h": surplus_profit,
        "Beneficio total/h": crop_profit_h + surplus_profit,
        "Beneficio/u cultivo": profit_u,
        "Semillas producidas/h": seed_production_real,
        "Semillas usadas/h": seeds_used,
        "Semillas sobrantes/h": seeds_surplus,
        "Agua producida/h": water_cap,
        "Agua usada/h": water_used,
        "Agua sobrante/h": water_surplus,
        "Electricidad producida/h": elec_total,
        "Electricidad sobrante/h": elec_surplus,
        "Cuello": ", ".join(dict.fromkeys(bottlenecks)),
        "Excedentes": surplus_items,
    }


# =============================
# Enumeración automática de planes
# =============================
farm_crops = products[(products["edificio"] == "Granja") & (products["producto"] != "Semillas")]["producto"].tolist()
plans: List[dict] = []
max_depots = 1 if consider_depot else 0

for c in range(1, min(3, slots) + 1):
    for e in range(1, min(4, slots - c) + 1):
        for d in range(0, max_depots + 1):
            remaining = slots - c - e - d
            if remaining < 1:
                continue
            for seed_f in range(0, remaining + 1):
                crop_f = remaining - seed_f
                if crop_f < 1:
                    continue
                for crop in farm_crops:
                    plan = simulate_plan(c, e, seed_f, crop_f, d, crop)
                    plans.append(plan)

plans_df = pd.DataFrame(plans)
if plans_df.empty:
    st.error("No se pudo armar ningún plan con esa cantidad de slots.")
    st.stop()

# Filtro: planes que realmente producen algo y no tienen pérdida enorme.
plans_df = plans_df.sort_values("Beneficio total/h", ascending=False).reset_index(drop=True)
best = plans_df.iloc[0].to_dict()

# =============================
# UI principal
# =============================
st.markdown('<div class="title">🏭 Plan simple de producción</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Vos ponés los slots. La app arma la mejor combinación simple: central, embalse, granjas de semillas, granjas de venta y excedentes.</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero">
        <div class="small">Plan recomendado para <b>{int(slots)} slots</b></div>
        <div style="font-size:2.15rem;font-weight:950;margin-top:4px;">
            {best['Producto']} · {money(best['Beneficio total/h'])}/h
        </div>
        <div style="margin-top:10px;">
            <span class="pill pill-blue">{int(best['Central'])} Central</span>
            <span class="pill pill-blue">{int(best['Embalse'])} Embalse</span>
            <span class="pill pill-good">{int(best['Granja semillas'])} Granja semillas</span>
            <span class="pill pill-good">{int(best['Granja venta'])} Granja venta</span>
            <span class="pill pill-warn">Venta: {best['Canal']}</span>
            <span class="pill">Cuello: {best['Cuello']}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Beneficio total/h", money(best["Beneficio total/h"]))
c2.metric("Cultivo/h", money(best["Beneficio cultivo/h"]))
c3.metric("Excedentes/h", money(best["Beneficio excedentes/h"]))
c4.metric("Producción vendible/h", num(best["Producción vendible/h"], 1))

st.markdown("### Qué hace cada bloque")
b1, b2, b3 = st.columns(3)
with b1:
    st.markdown(
        f"""
        <div class="card">
            <h3>Soporte básico</h3>
            <div class="big">{int(best['Central'])} + {int(best['Embalse'])}</div>
            <div class="small">Central para electricidad · embalse para agua. La electricidad sobrante se vende si está activado.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with b2:
    st.markdown(
        f"""
        <div class="card">
            <h3>Semillas</h3>
            <div class="big good">{int(best['Granja semillas'])} granja(s)</div>
            <div class="small">Produce {num(best['Semillas producidas/h'],1)} semillas/h · usa {num(best['Semillas usadas/h'],1)} · sobra {num(best['Semillas sobrantes/h'],1)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with b3:
    st.markdown(
        f"""
        <div class="card">
            <h3>Producto de venta</h3>
            <div class="big warn">{int(best['Granja venta'])} granja(s)</div>
            <div class="small">Fabrican {best['Producto']} y venden por {best['Canal']}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["✅ Resumen claro", "📊 Comparar planes", "⚙️ Datos simples"])

with tab1:
    st.markdown("### Saldos por hora")
    s1, s2, s3 = st.columns(3)
    s1.metric("Electricidad sobrante", num(best["Electricidad sobrante/h"], 1))
    s2.metric("Agua sobrante", num(best["Agua sobrante/h"], 1))
    s3.metric("Semillas sobrantes", num(best["Semillas sobrantes/h"], 1))

    if best["Excedentes"]:
        st.markdown("### Excedentes que se venden para caja")
        ex = pd.DataFrame(best["Excedentes"])
        ex_view = ex.copy()
        ex_view["Cantidad/h"] = ex_view["Cantidad/h"].map(lambda x: num(x, 1))
        ex_view["Beneficio/u"] = ex_view["Beneficio/u"].map(money)
        ex_view["Beneficio/h"] = ex_view["Beneficio/h"].map(money)
        st.dataframe(ex_view, hide_index=True, use_container_width=True)
    else:
        st.info("Este plan no deja excedentes vendibles relevantes, o tenés desactivada la venta de excedentes.")

    st.markdown("### Lectura rápida")
    if "agua" in str(best["Cuello"]):
        st.warning("El plan está sensible al agua. Si agregás más granjas, probablemente también necesites más embalse.")
    elif "semillas" in str(best["Cuello"]):
        st.warning("El plan está sensible a semillas. Te falta soporte o el cultivo elegido consume demasiadas semillas.")
    elif "electricidad" in str(best["Cuello"]):
        st.warning("El plan está sensible a electricidad. Más embalses podrían requerir más central.")
    else:
        st.success("No aparece un cuello fuerte con esta combinación. Es un plan simple y balanceado.")

with tab2:
    st.markdown("### Top combinaciones automáticas")
    view_cols = [
        "Producto", "Central", "Embalse", "Granja semillas", "Granja venta", "Canal", "Producción vendible/h", "Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h", "Cuello",
    ]
    top = plans_df[view_cols].head(25).copy()
    for col in ["Producción vendible/h"]:
        top[col] = top[col].map(lambda x: num(x, 1))
    for col in ["Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h"]:
        top[col] = top[col].map(money)
    st.dataframe(top, hide_index=True, use_container_width=True)

    st.caption("Esto ya no usa ‘nivel promedio’. Está comparando edificios enteros de nivel 1 según la cantidad de slots que pusiste.")

with tab3:
    st.markdown("### Costos base que está usando")
    costs = pd.DataFrame([
        ["Administración", pct(admin_final)],
        ["Electricidad propia", money(electricity_unit_cost)],
        ["Agua propia", money(water_unit_cost)],
        ["Semillas propias", money(seed_unit_cost)],
        ["Transporte comprado", money(transport_market_price)],
        ["Transporte fabricado estimado", money(transport_own_cost)],
        ["Diésel", money(diesel_price)],
    ], columns=["Dato", "Valor"])
    st.dataframe(costs, hide_index=True, use_container_width=True)

    st.markdown("### Precios actuales leídos")
    simple_prices = []
    for p in ["Electricidad", "Agua", "Semillas", "Grano", "Caña de azúcar", "Verduras", "Algodón", "Madera", "Transporte", "Diésel"]:
        simple_prices.append([p, money(latest_prices.get(p, 0))])
    st.dataframe(pd.DataFrame(simple_prices, columns=["Producto", "Precio"]), hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("V1.5 simple: la decisión principal se basa en cantidad de slots. No usa nivel promedio. Los niveles, robots, directores y otros edificios vuelven después, en una pantalla avanzada separada.")
