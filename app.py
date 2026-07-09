from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Market Lab — Estructura por Slots",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# Estilo visual
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
        font-size: 2.35rem;
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
    .hero-soft {
        background: linear-gradient(135deg, rgba(255, 209, 102, 0.14), rgba(91,141,255,0.09));
        border: 1px solid rgba(255,255,255,0.11);
        border-radius: 26px;
        padding: 20px 22px;
        box-shadow: 0 22px 50px rgba(0,0,0,0.22);
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
        font-size: 1.75rem;
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
    .slot-box {
        background: rgba(255,255,255,0.055);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 14px 16px;
        margin-bottom: 9px;
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
                    rows.append([row[0], row[1], row[3], row[4]])
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
# Sidebar: estructura real por bloques
# =============================
st.sidebar.markdown("# 🧱 Estructura real")
st.sidebar.caption("Cada bloque es un edificio real. El número del edificio es el NIVEL, no la cantidad de slots.")

if "slots_desbloqueados" not in st.session_state:
    st.session_state.slots_desbloqueados = 7

col_a, col_b = st.sidebar.columns([2, 1])
with col_a:
    slots_total = st.number_input("Slots desbloqueados", 3, 30, int(st.session_state.slots_desbloqueados), 1)
with col_b:
    st.write("")
    st.write("")
    if st.button("+ Slot", use_container_width=True):
        st.session_state.slots_desbloqueados = int(slots_total) + 1
        st.rerun()
slots_total = int(slots_total)
st.session_state.slots_desbloqueados = slots_total

st.sidebar.markdown("### Bloques actuales")
st.sidebar.markdown("**Soporte**")
central_level = st.sidebar.number_input("Central eléctrica — nivel", 0, 20, 1, 1)
embalse_level = st.sidebar.number_input("Embalse de agua — nivel", 0, 20, 1, 1)
semillera_count = st.sidebar.number_input("Granjas semilleras — cantidad", 0, 20, 1, 1)
semillera_level = st.sidebar.number_input("Nivel de cada granja semillera", 1, 20, 1, 1)

st.sidebar.markdown("**Producción para vender**")
venta_count = st.sidebar.number_input("Granjas de venta — cantidad", 0, 30, 3, 1)
venta_level = st.sidebar.number_input("Nivel de cada granja de venta", 1, 20, 1, 1)

with st.sidebar.expander("Opcional: Depósito de Embarque", expanded=False):
    deposito_count = st.number_input("Depósitos — cantidad", 0, 20, 0, 1)
    deposito_level = st.number_input("Nivel de cada depósito", 1, 20, 1, 1)

used_slots_now = int((1 if central_level > 0 else 0) + (1 if embalse_level > 0 else 0) + semillera_count + venta_count + deposito_count)
empty_slots = int(slots_total - used_slots_now)
if empty_slots < 0:
    st.sidebar.error(f"Te pasaste de slots: usás {used_slots_now} y tenés {slots_total}.")
    st.stop()
st.sidebar.info(f"Slots usados: {used_slots_now} · Slots vacíos: {empty_slots}")

st.sidebar.markdown("### Slot vacío")
slot_choice = "Nada por ahora"
if empty_slots > 0:
    slot_choice = st.sidebar.selectbox(
        "Qué querés probar en 1 slot vacío",
        ["Nada por ahora", "Granja de venta", "Granja semillera", "Embalse de agua", "Central eléctrica", "Depósito de Embarque"],
        index=0,
    )
else:
    st.sidebar.caption("No hay slot vacío para probar edificio nuevo.")

st.sidebar.markdown("### Venta")
sale_mode = st.sidebar.radio("Canal", ["Mercado", "Contrato", "Mejor automático"], index=0)
sell_surplus = st.sidebar.checkbox("Vender excedentes", value=True)

with st.sidebar.expander("Ajustes avanzados", expanded=False):
    fase = st.selectbox("Fase económica", ["Recesión", "Normal", "Boom"], index=1)
    production_mult = st.number_input("Multiplicador producción", 0.50, 1.50, 1.00, 0.01)
    salary_mult = st.number_input("Multiplicador salario", 0.50, 1.50, 1.00, 0.01)
    market_fee = st.slider("Comisión mercado", 0.0, 0.10, float(config.get("comision_mercado", 0.04)), 0.005)
    contract_discount = st.slider("Descuento contrato", 0.0, 0.10, float(config.get("descuento_contrato", 0.03)), 0.005)
    director_reduction = st.slider("Reducción admin por director", 0.0, 0.80, float(config.get("reduccion_admin_director", 0.0)), 0.01)

# =============================
# Motor de cálculo por niveles
# =============================
central_prod_base = float(central["produccion_h"]) * production_mult
embalse_prod_base = float(embalse["produccion_h"]) * production_mult
embalse_elec_need_base = float(embalse["electricidad_necesaria_h"]) * production_mult
seed_prod_base = float(seed_product["produccion_h"]) * production_mult
seed_water_need_base = float(seed_product["agua_necesaria_h"]) * production_mult
transport_market_price = float(latest_prices.get("Transporte", config.get("precio_transporte_default", 0.389)))
diesel_price = float(latest_prices.get("Diésel", config.get("precio_diesel_default", 40.75)))


def admin_from_levels(total_levels: float) -> float:
    return max(0.0, (float(total_levels) - 1.0) / 170.0) * (1.0 - director_reduction)


def total_levels_of(plan: dict) -> float:
    return (
        plan["central_level"]
        + plan["embalse_level"]
        + plan["semillera_count"] * plan["semillera_level"]
        + plan["venta_count"] * plan["venta_level"]
        + plan["deposito_count"] * plan["deposito_level"]
    )


def slots_of(plan: dict) -> int:
    return int(
        (1 if plan["central_level"] > 0 else 0)
        + (1 if plan["embalse_level"] > 0 else 0)
        + plan["semillera_count"]
        + plan["venta_count"]
        + plan["deposito_count"]
    )


def plan_unit_costs(plan: dict) -> dict:
    total_levels = total_levels_of(plan)
    admin = admin_from_levels(total_levels)
    central_salary = float(central["salario_h"]) * salary_mult * (1 + admin)
    embalse_salary = float(embalse["salario_h"]) * salary_mult * (1 + admin)
    granja_salary = float(granja["salario_h"]) * salary_mult * (1 + admin)
    deposito_salary = float(deposito["salario_h"]) * salary_mult * (1 + admin)

    electricity_unit_cost = safe_div(central_salary, central_prod_base)
    water_unit_cost = safe_div(embalse_salary + embalse_elec_need_base * electricity_unit_cost, embalse_prod_base)
    seed_unit_cost = safe_div(granja_salary + seed_water_need_base * water_unit_cost, seed_prod_base)

    transport_output = float(deposito["produccion_h"]) * production_mult
    transport_own_cost = safe_div(
        deposito_salary + transport_output * (1/95) * electricity_unit_cost + transport_output * (1/190) * diesel_price,
        transport_output,
    )
    return {
        "admin": admin,
        "total_levels": total_levels,
        "central_salary": central_salary,
        "embalse_salary": embalse_salary,
        "granja_salary": granja_salary,
        "deposito_salary": deposito_salary,
        "electricity_unit_cost": electricity_unit_cost,
        "water_unit_cost": water_unit_cost,
        "seed_unit_cost": seed_unit_cost,
        "transport_own_cost": transport_own_cost,
    }


def net_price_market(product_name: str, transport_unit_cost: float) -> float:
    price = float(latest_prices.get(product_name, 0) or 0)
    tr = float(get_product(product_name).get("transporte_mercado", 0) or 0)
    return price * (1 - market_fee) - tr * transport_unit_cost


def net_price_contract(product_name: str, transport_unit_cost: float) -> float:
    price = float(latest_prices.get(product_name, 0) or 0)
    tr = float(get_product(product_name).get("transporte_mercado", 0) or 0)
    return price * (1 - contract_discount) - (tr / 2) * transport_unit_cost


def chosen_net_price(product_name: str, transport_unit_cost: float) -> Tuple[str, float]:
    m = net_price_market(product_name, transport_unit_cost)
    c = net_price_contract(product_name, transport_unit_cost)
    if sale_mode == "Mercado":
        return "Mercado", m
    if sale_mode == "Contrato":
        return "Contrato", c
    return ("Contrato", c) if c > m else ("Mercado", m)


def physical_water_capacity(plan: dict) -> tuple[float, float, float, bool]:
    elec_total = plan["central_level"] * central_prod_base
    elec_for_embalse_full = plan["embalse_level"] * embalse_elec_need_base
    embalse_water_full = plan["embalse_level"] * embalse_prod_base
    elec_shortage = elec_for_embalse_full > elec_total + 1e-9
    if not elec_shortage:
        water = embalse_water_full
        elec_surplus = elec_total - elec_for_embalse_full
    else:
        water = safe_div(elec_total, embalse_elec_need_base) * embalse_prod_base
        elec_surplus = 0.0
    return water, elec_total, elec_surplus, elec_shortage


def product_unit_cost(crop_name: str, costs: dict) -> float:
    r = get_product(crop_name)
    prod = float(r.get("produccion_h", 0) or 0) * production_mult
    water_need = float(r.get("agua_necesaria_h", 0) or 0) * production_mult
    seed_need = float(r.get("semillas_necesarias_h", 0) or 0) * production_mult
    return safe_div(costs["granja_salary"] + water_need * costs["water_unit_cost"] + seed_need * costs["seed_unit_cost"], prod)


def simulate_plan(plan: dict, crop_name: str, etiqueta: str = "") -> dict:
    costs = plan_unit_costs(plan)
    transport_unit_cost = transport_market_price  # Por ahora se compra transporte.

    water_cap, elec_total, elec_surplus, elec_shortage = physical_water_capacity(plan)
    r = get_product(crop_name)

    crop_prod_per_level = float(r["produccion_h"]) * production_mult
    crop_water_per_level = float(r["agua_necesaria_h"]) * production_mult
    crop_seed_per_level = float(r["semillas_necesarias_h"]) * production_mult

    semillera_levels = plan["semillera_count"] * plan["semillera_level"]
    venta_levels = plan["venta_count"] * plan["venta_level"]

    seed_production = semillera_levels * seed_prod_base
    seed_water = semillera_levels * seed_water_need_base

    if seed_water > water_cap and seed_water > 0:
        seed_factor = water_cap / seed_water
        seed_production_real = seed_production * seed_factor
        water_left = 0.0
    else:
        seed_factor = 1.0
        seed_production_real = seed_production
        water_left = water_cap - seed_water

    crop_output_full = venta_levels * crop_prod_per_level
    crop_water_full = venta_levels * crop_water_per_level
    crop_seed_full = venta_levels * crop_seed_per_level

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

    channel, net_u = chosen_net_price(crop_name, transport_unit_cost)
    cost_u = product_unit_cost(crop_name, costs)
    profit_u = net_u - cost_u
    crop_profit_h = output * profit_u

    surplus_profit = 0.0
    surplus_items = []
    if sell_surplus:
        for pname, qty, unit_cost in [
            ("Electricidad", elec_surplus, costs["electricity_unit_cost"]),
            ("Agua", water_surplus, costs["water_unit_cost"]),
            ("Semillas", seeds_surplus, costs["seed_unit_cost"]),
        ]:
            if qty <= 1e-9:
                continue
            net_surplus = net_price_market(pname, transport_unit_cost)
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
    if elec_shortage:
        bottlenecks.append("electricidad")
    if not bottlenecks:
        bottlenecks.append("sin cuello fuerte")

    return {
        "Etiqueta": etiqueta,
        "Producto": crop_name,
        "Canal": channel,
        "Central nivel": plan["central_level"],
        "Embalse nivel": plan["embalse_level"],
        "Granjas semilleras": plan["semillera_count"],
        "Nivel semillera": plan["semillera_level"],
        "Granjas venta": plan["venta_count"],
        "Nivel granjas venta": plan["venta_level"],
        "Depósitos": plan["deposito_count"],
        "Slots usados": slots_of(plan),
        "Niveles totales": costs["total_levels"],
        "Admin": costs["admin"],
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


farm_crops = products[(products["edificio"] == "Granja") & (products["producto"] != "Semillas")]["producto"].tolist()

current_plan = {
    "central_level": int(central_level),
    "embalse_level": int(embalse_level),
    "semillera_count": int(semillera_count),
    "semillera_level": int(semillera_level),
    "venta_count": int(venta_count),
    "venta_level": int(venta_level),
    "deposito_count": int(deposito_count),
    "deposito_level": int(deposito_level),
}


def best_crop_for_plan(plan: dict, etiqueta: str = "Actual") -> pd.DataFrame:
    rows = [simulate_plan(plan, crop, etiqueta) for crop in farm_crops if plan["venta_count"] > 0]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Beneficio total/h", ascending=False).reset_index(drop=True)

current_plans = best_crop_for_plan(current_plan, "Actual")
if current_plans.empty:
    st.error("No hay granjas de venta cargadas. Agregá al menos 1 granja de venta para comparar cultivos.")
    st.stop()
current_best = current_plans.iloc[0].to_dict()

slot_plan = None
slot_best = None
slot_plans = pd.DataFrame()
if empty_slots > 0 and slot_choice != "Nada por ahora":
    slot_plan = dict(current_plan)
    if slot_choice == "Granja de venta":
        slot_plan["venta_count"] += 1
    elif slot_choice == "Granja semillera":
        slot_plan["semillera_count"] += 1
    elif slot_choice == "Embalse de agua":
        slot_plan["embalse_level"] += 1  # Nuevo embalse nivel 1: suma 1 nivel y 1 slot.
    elif slot_choice == "Central eléctrica":
        slot_plan["central_level"] += 1  # Nueva central nivel 1: suma 1 nivel y 1 slot.
    elif slot_choice == "Depósito de Embarque":
        slot_plan["deposito_count"] += 1
    slot_plans = best_crop_for_plan(slot_plan, f"+ {slot_choice}")
    if not slot_plans.empty:
        slot_best = slot_plans.iloc[0].to_dict()

# =============================
# UI principal
# =============================
st.markdown('<div class="title">🏭 Estructura simple por slots</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ahora la app separa edificios reales: 1 central, 1 embalse, 1 granja semillera y 3 granjas de venta. Si subís de nivel, cambiás el nivel del bloque; no se inventan slots nuevos.</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero">
        <div class="small">Tu estructura actual · <b>{used_slots_now} slots usados</b> · <b>{empty_slots} slot(s) vacío(s)</b></div>
        <div style="font-size:2.05rem;font-weight:950;margin-top:4px;">
            Mejor cultivo: {current_best['Producto']} · {money(current_best['Beneficio total/h'])}/h
        </div>
        <div style="margin-top:10px;">
            <span class="pill pill-blue">Central nivel {int(current_best['Central nivel'])}</span>
            <span class="pill pill-blue">Embalse nivel {int(current_best['Embalse nivel'])}</span>
            <span class="pill pill-good">{int(current_best['Granjas semilleras'])} semillera(s) N{int(current_best['Nivel semillera'])}</span>
            <span class="pill pill-good">{int(current_best['Granjas venta'])} granja(s) venta N{int(current_best['Nivel granjas venta'])}</span>
            <span class="pill pill-warn">Venta: {current_best['Canal']}</span>
            <span class="pill">Cuello: {current_best['Cuello']}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Beneficio total/h", money(current_best["Beneficio total/h"]))
c2.metric("Cultivo/h", money(current_best["Beneficio cultivo/h"]))
c3.metric("Excedentes/h", money(current_best["Beneficio excedentes/h"]))
c4.metric("Admin", pct(current_best["Admin"]))

st.markdown("### Bloques actuales")
b1, b2, b3, b4 = st.columns(4)
with b1:
    st.markdown(f'<div class="card"><h3>Central</h3><div class="big">Nivel {int(central_level)}</div><div class="small">1 slot. Si la subís a nivel 2, cambiás este número; no agregás otra central.</div></div>', unsafe_allow_html=True)
with b2:
    st.markdown(f'<div class="card"><h3>Embalse</h3><div class="big">Nivel {int(embalse_level)}</div><div class="small">1 slot. Produce agua usando electricidad propia.</div></div>', unsafe_allow_html=True)
with b3:
    st.markdown(f'<div class="card"><h3>Semillas</h3><div class="big good">{int(semillera_count)} granja(s)</div><div class="small">Nivel {int(semillera_level)} · {num(current_best["Semillas producidas/h"],1)} semillas/h.</div></div>', unsafe_allow_html=True)
with b4:
    st.markdown(f'<div class="card"><h3>Venta</h3><div class="big warn">{int(venta_count)} granja(s)</div><div class="small">Nivel {int(venta_level)} · fabrican el producto recomendado para vender.</div></div>', unsafe_allow_html=True)

if empty_slots > 0:
    st.markdown("### Slot vacío")
    if slot_choice == "Nada por ahora":
        st.info("Tenés slot libre. Elegí en la barra lateral qué edificio querés probar antes de construirlo.")
    elif slot_best is not None:
        mejora = slot_best["Beneficio total/h"] - current_best["Beneficio total/h"]
        st.markdown(
            f"""
            <div class="hero-soft">
                <div class="small">Simulación del slot vacío: <b>{slot_choice}</b> nivel 1. No destruye nada.</div>
                <div style="font-size:1.65rem;font-weight:950;margin-top:4px;">
                    Nuevo mejor cultivo: {slot_best['Producto']} · mejora {money(mejora)}/h
                </div>
                <div style="margin-top:10px;">
                    <span class="pill pill-blue">Central nivel total {int(slot_best['Central nivel'])}</span>
                    <span class="pill pill-blue">Embalse nivel total {int(slot_best['Embalse nivel'])}</span>
                    <span class="pill pill-good">{int(slot_best['Granjas semilleras'])} semillera(s)</span>
                    <span class="pill pill-good">{int(slot_best['Granjas venta'])} granja(s) venta</span>
                    <span class="pill">Cuello: {slot_best['Cuello']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["✅ Plan actual", "➕ Probar slot", "📊 Comparar cultivos", "⚙️ Datos"])

with tab1:
    st.markdown("### Saldos por hora")
    s1, s2, s3 = st.columns(3)
    s1.metric("Electricidad sobrante", num(current_best["Electricidad sobrante/h"], 1))
    s2.metric("Agua sobrante", num(current_best["Agua sobrante/h"], 1))
    s3.metric("Semillas sobrantes", num(current_best["Semillas sobrantes/h"], 1))

    if current_best["Excedentes"]:
        st.markdown("### Excedentes vendidos para caja")
        ex = pd.DataFrame(current_best["Excedentes"])
        ex_view = ex.copy()
        ex_view["Cantidad/h"] = ex_view["Cantidad/h"].map(lambda x: num(x, 1))
        ex_view["Beneficio/u"] = ex_view["Beneficio/u"].map(money)
        ex_view["Beneficio/h"] = ex_view["Beneficio/h"].map(money)
        st.dataframe(ex_view, hide_index=True, use_container_width=True)
    else:
        st.info("No hay excedentes vendibles relevantes, o desactivaste vender excedentes.")

    st.markdown("### Lectura rápida")
    if "agua" in str(current_best["Cuello"]):
        st.warning("Tu estructura está limitada por agua. Antes de sumar más granjas de venta, mirá si el embalse alcanza.")
    elif "semillas" in str(current_best["Cuello"]):
        st.warning("Tu estructura está limitada por semillas. La granja semillera no alcanza para alimentar todo el cultivo elegido.")
    elif "electricidad" in str(current_best["Cuello"]):
        st.warning("Tu estructura está limitada por electricidad. Recién ahí tiene sentido mirar central.")
    else:
        st.success("No aparece cuello fuerte. El foco es elegir el cultivo y vender excedentes.")

with tab2:
    st.markdown("### Probar un edificio nuevo en el slot vacío")
    st.caption("Esto no sube niveles. Esto solo prueba 1 edificio nuevo nivel 1 en un slot libre.")
    if empty_slots <= 0:
        st.info("No tenés slots vacíos.")
    elif slot_choice == "Nada por ahora":
        st.info("Elegí un edificio en la barra lateral para simular el slot libre.")
    elif slot_best is not None:
        df = slot_plans[["Producto", "Canal", "Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h", "Cuello"]].head(15).copy()
        for col in ["Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h"]:
            df[col] = df[col].map(money)
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.caption("Si querés subir la central de nivel, no uses esta pestaña: cambiá 'Central — nivel' en la barra lateral.")

with tab3:
    st.markdown("### Comparación de cultivos con tu estructura actual")
    view_cols = ["Producto", "Canal", "Producción vendible/h", "Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h", "Cuello"]
    top = current_plans[view_cols].head(30).copy()
    top["Producción vendible/h"] = top["Producción vendible/h"].map(lambda x: num(x, 1))
    for col in ["Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h"]:
        top[col] = top[col].map(money)
    st.dataframe(top, hide_index=True, use_container_width=True)
    st.caption("Esta tabla no cambia la cantidad de granjas. Solo cambia qué producen las granjas de venta.")

with tab4:
    st.markdown("### Resumen de estructura")
    estructura = pd.DataFrame([
        ["Central eléctrica", 1 if central_level > 0 else 0, int(central_level), "Soporte"],
        ["Embalse de agua", 1 if embalse_level > 0 else 0, int(embalse_level), "Soporte"],
        ["Granja semillera", int(semillera_count), int(semillera_level), "Semillas"],
        ["Granjas de venta", int(venta_count), int(venta_level), "Producto a vender"],
        ["Depósito de Embarque", int(deposito_count), int(deposito_level), "Opcional"],
    ], columns=["Bloque", "Cantidad de slots", "Nivel", "Rol"])
    st.dataframe(estructura, hide_index=True, use_container_width=True)

    st.markdown("### Costos base")
    costs_now = plan_unit_costs(current_plan)
    costs_df = pd.DataFrame([
        ["Niveles totales para admin", num(costs_now["total_levels"], 0)],
        ["Administración", pct(costs_now["admin"])],
        ["Electricidad propia", money(costs_now["electricity_unit_cost"])],
        ["Agua propia", money(costs_now["water_unit_cost"])],
        ["Semillas propias", money(costs_now["seed_unit_cost"])],
        ["Transporte comprado", money(transport_market_price)],
        ["Transporte fabricado estimado", money(costs_now["transport_own_cost"])],
        ["Diésel", money(diesel_price)],
    ], columns=["Dato", "Valor"])
    st.dataframe(costs_df, hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("V1.8: estructura por bloques. Nivel ≠ cantidad de edificios. Slot vacío ≠ upgrade de nivel.")
