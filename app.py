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
    page_title="Market Lab — Plan Real",
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
# Sidebar realista
# =============================
st.sidebar.markdown("# ⚙️ Tu empresa real")
st.sidebar.caption("Modo conservador: no destruye edificios ni inventa una empresa nueva.")

empresa_cfg = config.get("empresa_actual", {})
slots_total = st.sidebar.number_input("Slots desbloqueados", min_value=3, max_value=30, value=7, step=1)
st.sidebar.markdown("### Edificios que YA tenés")
current_central = st.sidebar.number_input("Central eléctrica", 0, 20, int(empresa_cfg.get("Central eléctrica", {}).get("cantidad", 1)), 1)
current_embalse = st.sidebar.number_input("Embalse de agua", 0, 20, int(empresa_cfg.get("Embalse de agua", {}).get("cantidad", 1)), 1)
current_granja = st.sidebar.number_input("Granja", 0, 30, int(empresa_cfg.get("Granja", {}).get("cantidad", 4)), 1)
current_deposito = st.sidebar.number_input("Depósito de Embarque", 0, 20, int(empresa_cfg.get("Depósito de Embarque", {}).get("cantidad", 0)), 1)

used_slots_now = int(current_central + current_embalse + current_granja + current_deposito)
empty_slots = int(slots_total - used_slots_now)
if empty_slots < 0:
    st.sidebar.error("Tenés más edificios cargados que slots desbloqueados. Corregí los números.")
    st.stop()
st.sidebar.info(f"Slots usados: {used_slots_now} · Slots vacíos: {empty_slots}")

st.sidebar.markdown("### Decisión")
sale_mode = st.sidebar.radio("Canal de venta", ["Mercado", "Contrato", "Mejor automático"], index=0)
sell_surplus = st.sidebar.checkbox("Vender excedentes", value=True, help="Vende electricidad, agua o semillas sobrantes para flujo de caja.")
real_mode = st.sidebar.checkbox("Modo real: NO destruir ni reemplazar edificios", value=True)
use_empty_slots = st.sidebar.checkbox("Evaluar qué poner en slots vacíos", value=True)
allow_extra_power_business = st.sidebar.checkbox(
    "Permitir central extra solo para vender electricidad",
    value=False,
    help="Apagado por defecto. Si ya te sobra electricidad, no recomienda otra central como negocio aparte.",
)
consider_depot = st.sidebar.checkbox("Considerar Depósito de Embarque", value=False, help="Apagado por defecto porque ocupa un slot y hoy probablemente no compense.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Fase")
fase = st.sidebar.selectbox("Fase económica", ["Recesión", "Normal", "Boom"], index=1)
with st.sidebar.expander("Ajustes avanzados", expanded=False):
    production_mult = st.number_input("Multiplicador producción", 0.50, 1.50, 1.00, 0.01)
    salary_mult = st.number_input("Multiplicador salario", 0.50, 1.50, 1.00, 0.01)
    market_fee = st.slider("Comisión mercado", 0.0, 0.10, float(config.get("comision_mercado", 0.04)), 0.005)
    contract_discount = st.slider("Descuento contrato", 0.0, 0.10, float(config.get("descuento_contrato", 0.03)), 0.005)
    director_reduction = st.slider("Reducción administración director", 0.0, 0.80, float(config.get("reduccion_admin_director", 0.0)), 0.01)

# =============================
# Constantes base
# =============================
central_prod_base = float(central["produccion_h"]) * production_mult
embalse_prod_base = float(embalse["produccion_h"]) * production_mult
embalse_elec_need_base = float(embalse["electricidad_necesaria_h"]) * production_mult
seed_prod_base = float(seed_product["produccion_h"]) * production_mult
seed_water_need_base = float(seed_product["agua_necesaria_h"]) * production_mult
transport_market_price = float(latest_prices.get("Transporte", config.get("precio_transporte_default", 0.389)))
diesel_price = float(latest_prices.get("Diésel", config.get("precio_diesel_default", 40.75)))


def plan_admin(total_buildings: int) -> float:
    return max(0.0, (int(total_buildings) - 1) / 170.0) * (1 - director_reduction)


def plan_unit_costs(total_buildings: int) -> dict:
    admin = plan_admin(total_buildings)
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


def physical_water_capacity(central_slots: int, embalse_slots: int) -> tuple[float, float, float, bool]:
    elec_total = central_slots * central_prod_base
    elec_for_embalse_full = embalse_slots * embalse_elec_need_base
    embalse_water_full = embalse_slots * embalse_prod_base
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


def simulate_plan(central_slots: int, embalse_slots: int, seed_farms: int, crop_farms: int, depot_slots: int, crop_name: str, etiqueta: str = "") -> dict:
    total_buildings = central_slots + embalse_slots + seed_farms + crop_farms + depot_slots
    costs = plan_unit_costs(total_buildings)
    transport_unit_cost = transport_market_price  # V1: por defecto se compra transporte.

    water_cap, elec_total, elec_surplus, elec_shortage = physical_water_capacity(central_slots, embalse_slots)
    r = get_product(crop_name)

    crop_prod_per_farm = float(r["produccion_h"]) * production_mult
    crop_water_per_farm = float(r["agua_necesaria_h"]) * production_mult
    crop_seed_per_farm = float(r["semillas_necesarias_h"]) * production_mult

    seed_production = seed_farms * seed_prod_base
    seed_water = seed_farms * seed_water_need_base

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
        "Central": central_slots,
        "Embalse": embalse_slots,
        "Granja semillas": seed_farms,
        "Granja venta": crop_farms,
        "Depósito": depot_slots,
        "Slots usados": total_buildings,
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


def best_split_for_fixed_buildings(c: int, e: int, g_total: int, d: int, etiqueta: str = "") -> pd.DataFrame:
    plans: List[dict] = []
    if g_total <= 0:
        return pd.DataFrame()
    for seed_f in range(0, g_total + 1):
        crop_f = g_total - seed_f
        if crop_f < 1:
            continue
        for crop in farm_crops:
            plans.append(simulate_plan(c, e, seed_f, crop_f, d, crop, etiqueta=etiqueta))
    if not plans:
        return pd.DataFrame()
    return pd.DataFrame(plans).sort_values("Beneficio total/h", ascending=False).reset_index(drop=True)


current_plans = best_split_for_fixed_buildings(current_central, current_embalse, current_granja, current_deposito, "Actual")
if current_plans.empty:
    st.error("Con los edificios actuales no se pudo simular un plan. Revisá que tengas al menos 1 granja.")
    st.stop()
current_best = current_plans.iloc[0].to_dict()

future_plans: List[dict] = []
if use_empty_slots and empty_slots > 0:
    # En modo real no se reemplaza nada: solo se agregan edificios al slot vacío.
    # Por defecto se comparan opciones de 1 edificio nuevo, no se inventa una empresa desde cero.
    candidates = ["Granja", "Embalse de agua"]
    if consider_depot:
        candidates.append("Depósito de Embarque")
    current_has_electricity_bottleneck = "electricidad" in str(current_best.get("Cuello", ""))
    if allow_extra_power_business or current_has_electricity_bottleneck:
        candidates.append("Central eléctrica")

    for new_building in candidates:
        c, e, g, d = current_central, current_embalse, current_granja, current_deposito
        if new_building == "Central eléctrica":
            c += 1
        elif new_building == "Embalse de agua":
            e += 1
        elif new_building == "Granja":
            g += 1
        elif new_building == "Depósito de Embarque":
            d += 1
        df = best_split_for_fixed_buildings(c, e, g, d, f"Agregar {new_building}")
        if not df.empty:
            best_candidate = df.iloc[0].to_dict()
            best_candidate["Nuevo edificio"] = new_building
            best_candidate["Mejora vs actual/h"] = best_candidate["Beneficio total/h"] - current_best["Beneficio total/h"]
            future_plans.append(best_candidate)

future_df = pd.DataFrame(future_plans)
if not future_df.empty:
    future_df = future_df.sort_values("Mejora vs actual/h", ascending=False).reset_index(drop=True)
    future_best = future_df.iloc[0].to_dict()
else:
    future_best = None

# =============================
# UI principal
# =============================
st.markdown('<div class="title">🏭 Plan real de producción</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Primero respeta lo que ya construiste. No recomienda destruir edificios ni inventar 3 centrales de la nada.</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero">
        <div class="small">Plan actual usando tus edificios reales: <b>{used_slots_now} usados</b> · <b>{empty_slots} vacío(s)</b></div>
        <div style="font-size:2.15rem;font-weight:950;margin-top:4px;">
            {current_best['Producto']} · {money(current_best['Beneficio total/h'])}/h
        </div>
        <div style="margin-top:10px;">
            <span class="pill pill-blue">{int(current_best['Central'])} Central real</span>
            <span class="pill pill-blue">{int(current_best['Embalse'])} Embalse real</span>
            <span class="pill pill-good">{int(current_best['Granja semillas'])} Granja semillas</span>
            <span class="pill pill-good">{int(current_best['Granja venta'])} Granja venta</span>
            <span class="pill pill-warn">Venta: {current_best['Canal']}</span>
            <span class="pill">Cuello: {current_best['Cuello']}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Beneficio actual/h", money(current_best["Beneficio total/h"]))
c2.metric("Cultivo/h", money(current_best["Beneficio cultivo/h"]))
c3.metric("Excedentes/h", money(current_best["Beneficio excedentes/h"]))
c4.metric("Producción vendible/h", num(current_best["Producción vendible/h"], 1))

if future_best is not None:
    st.markdown(
        f"""
        <div class="hero-soft">
            <div class="small">Cuando tengas dinero para usar el slot vacío, sin destruir nada:</div>
            <div style="font-size:1.7rem;font-weight:950;margin-top:4px;">
                Agregar {future_best['Nuevo edificio']} · mejora estimada {money(future_best['Mejora vs actual/h'])}/h
            </div>
            <div style="margin-top:10px;">
                <span class="pill pill-blue">Quedaría: {int(future_best['Central'])} Central</span>
                <span class="pill pill-blue">{int(future_best['Embalse'])} Embalse</span>
                <span class="pill pill-good">{int(future_best['Granja semillas'])} Granja semillas</span>
                <span class="pill pill-good">{int(future_best['Granja venta'])} Granja venta</span>
                <span class="pill pill-warn">Producto: {future_best['Producto']}</span>
                <span class="pill">Cuello: {future_best['Cuello']}</span>
            </div>
            <div class="small" style="margin-top:8px;">Esto NO significa construir ahora mismo. Es solo la opción futura cuando tengas capital y quieras usar el slot vacío.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif empty_slots > 0:
    st.info("Tenés slot vacío, pero no hay recomendación futura activa. Activá 'Evaluar qué poner en slots vacíos' o permití más tipos de edificio.")
else:
    st.info("No tenés slots vacíos. La app solo optimiza cómo usar tus edificios actuales.")

st.markdown("### Qué hace cada bloque actual")
b1, b2, b3 = st.columns(3)
with b1:
    st.markdown(
        f"""
        <div class="card">
            <h3>Soporte fijo</h3>
            <div class="big">{int(current_best['Central'])} + {int(current_best['Embalse'])}</div>
            <div class="small">Son los edificios que ya tenés. No se reemplazan. La electricidad sobrante se vende si está activado.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with b2:
    st.markdown(
        f"""
        <div class="card">
            <h3>Semillas</h3>
            <div class="big good">{int(current_best['Granja semillas'])} granja(s)</div>
            <div class="small">Produce {num(current_best['Semillas producidas/h'],1)} semillas/h · usa {num(current_best['Semillas usadas/h'],1)} · sobra {num(current_best['Semillas sobrantes/h'],1)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with b3:
    st.markdown(
        f"""
        <div class="card">
            <h3>Producto de caja</h3>
            <div class="big warn">{int(current_best['Granja venta'])} granja(s)</div>
            <div class="small">Fabrican {current_best['Producto']} y venden por {current_best['Canal']}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["✅ Plan actual", "🧱 Slot vacío", "📊 Comparar cultivos", "⚙️ Datos"])

with tab1:
    st.markdown("### Saldos por hora con lo que ya tenés")
    s1, s2, s3 = st.columns(3)
    s1.metric("Electricidad sobrante", num(current_best["Electricidad sobrante/h"], 1))
    s2.metric("Agua sobrante", num(current_best["Agua sobrante/h"], 1))
    s3.metric("Semillas sobrantes", num(current_best["Semillas sobrantes/h"], 1))

    if current_best["Excedentes"]:
        st.markdown("### Excedentes vendidos para flujo de caja")
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
        st.warning("Tu plan actual está limitado por agua. Sumar una granja puede no servir si no agregás más agua.")
    elif "semillas" in str(current_best["Cuello"]):
        st.warning("Tu plan actual está limitado por semillas. La app asignó granjas a semillas para sostener el cultivo.")
    elif "electricidad" in str(current_best["Cuello"]):
        st.warning("Tu plan actual está limitado por electricidad. Recién ahí tendría sentido mirar otra central.")
    else:
        st.success("Con tus edificios actuales no aparece un cuello fuerte. El foco es elegir el mejor cultivo y vender excedentes.")

with tab2:
    st.markdown("### Opciones para el slot vacío")
    if future_df.empty:
        st.info("No hay opciones calculadas. Si el slot está vacío pero no tenés dinero, está perfecto: usá esta sección solo para planificar.")
    else:
        fv = future_df[["Nuevo edificio", "Producto", "Central", "Embalse", "Granja semillas", "Granja venta", "Beneficio total/h", "Mejora vs actual/h", "Cuello"]].copy()
        for col in ["Beneficio total/h", "Mejora vs actual/h"]:
            fv[col] = fv[col].map(money)
        st.dataframe(fv, hide_index=True, use_container_width=True)
        st.caption("Estas opciones solo agregan edificios al slot vacío. No borran ni reemplazan los edificios que ya tenés.")

with tab3:
    st.markdown("### Mejor uso de tus 4 granjas actuales")
    view_cols = ["Producto", "Granja semillas", "Granja venta", "Canal", "Producción vendible/h", "Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h", "Cuello"]
    top = current_plans[view_cols].head(25).copy()
    top["Producción vendible/h"] = top["Producción vendible/h"].map(lambda x: num(x, 1))
    for col in ["Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h"]:
        top[col] = top[col].map(money)
    st.dataframe(top, hide_index=True, use_container_width=True)
    st.caption("Esta tabla solo cambia el reparto interno de tus granjas: cuántas a semillas y cuántas al producto de venta.")

with tab4:
    st.markdown("### Costos base actuales")
    costs_now = plan_unit_costs(used_slots_now)
    costs_df = pd.DataFrame([
        ["Administración actual", pct(costs_now["admin"])],
        ["Electricidad propia", money(costs_now["electricity_unit_cost"])],
        ["Agua propia", money(costs_now["water_unit_cost"])],
        ["Semillas propias", money(costs_now["seed_unit_cost"])],
        ["Transporte comprado", money(transport_market_price)],
        ["Transporte fabricado estimado", money(costs_now["transport_own_cost"])],
        ["Diésel", money(diesel_price)],
    ], columns=["Dato", "Valor"])
    st.dataframe(costs_df, hide_index=True, use_container_width=True)

    st.markdown("### Precios actuales leídos")
    simple_prices = []
    for p in ["Electricidad", "Agua", "Semillas", "Grano", "Caña de azúcar", "Verduras", "Algodón", "Madera", "Transporte", "Diésel"]:
        simple_prices.append([p, money(latest_prices.get(p, 0))])
    st.dataframe(pd.DataFrame(simple_prices, columns=["Producto", "Precio"]), hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("V1.6 real: respeta tus edificios existentes. La recomendación principal es cómo usar lo que ya tenés; el slot vacío se evalúa aparte y solo como planificación futura.")
