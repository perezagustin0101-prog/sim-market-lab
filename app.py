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
    page_title="Market Lab — Slots reales",
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
        font-size: 2.4rem;
        line-height: 1.05;
        font-weight: 950;
        letter-spacing: -0.05em;
        margin-bottom: 0.1rem;
    }
    .subtitle { color: #aab7d4; font-size: 1.02rem; margin-bottom: 1.1rem; }
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
    .card h3 { color:#aab7d4; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; margin:0 0 8px 0; }
    .big { font-size:1.85rem; font-weight:950; color:white; margin:0; }
    .small { color:#b8c4dc; font-size:.93rem; }
    .good { color:#59e68b !important; }
    .warn { color:#ffd166 !important; }
    .bad { color:#ff6b6b !important; }
    .muted { color:#aab7d4 !important; }
    .pill {
        display:inline-block; border-radius:999px; padding:6px 11px; margin:4px 5px 4px 0;
        font-size:.80rem; font-weight:850; border:1px solid rgba(255,255,255,.14); background:rgba(255,255,255,.07);
    }
    .pill-good { background: rgba(89,230,139,.15); color:#59e68b; border-color: rgba(89,230,139,.32); }
    .pill-warn { background: rgba(255,209,102,.16); color:#ffd166; border-color: rgba(255,209,102,.32); }
    .pill-blue { background: rgba(91,141,255,.17); color:#8eb0ff; border-color: rgba(91,141,255,.32); }
    div[data-testid="stMetric"] { background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.10); padding:14px 16px; border-radius:18px; }
    .stDataFrame { border-radius:18px; overflow:hidden; }
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
    return f"{float(x)*100:.1f}%".replace(".", ",")


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
                # Soporta historial viejo de profundidad y ticker nuevo.
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
farm_crops = products[(products["edificio"] == "Granja") & (products["producto"] != "Semillas")]["producto"].tolist()

# =============================
# Estado inicial de slots
# =============================
def default_slot(i: int) -> dict:
    if i == 1:
        return {"tipo": "Central eléctrica", "nivel": 1, "rol": "Soporte"}
    if i == 2:
        return {"tipo": "Embalse de agua", "nivel": 1, "rol": "Soporte"}
    if i == 3:
        return {"tipo": "Granja", "nivel": 1, "rol": "Semillera"}
    if i in (4, 5, 6):
        return {"tipo": "Granja", "nivel": 1, "rol": "Venta"}
    return {"tipo": "Vacío", "nivel": 1, "rol": "Vacío"}


if "slots_desbloqueados" not in st.session_state:
    st.session_state["slots_desbloqueados"] = 7
if "slots" not in st.session_state:
    st.session_state["slots"] = [default_slot(i) for i in range(1, st.session_state["slots_desbloqueados"] + 1)]

# =============================
# Sidebar: configuración simple por slot
# =============================
st.sidebar.markdown("# 🧱 Slots reales")
st.sidebar.caption("Cada slot es un edificio separado. El nivel se carga en ese slot, no como promedio.")

b1, b2 = st.sidebar.columns(2)
if b1.button("+ Desbloquear slot", use_container_width=True):
    st.session_state["slots_desbloqueados"] += 1
    st.session_state["slots"].append(default_slot(st.session_state["slots_desbloqueados"]))
if b2.button("↺ Reset actual", use_container_width=True):
    st.session_state["slots_desbloqueados"] = 7
    st.session_state["slots"] = [default_slot(i) for i in range(1, 8)]

slot_count = st.sidebar.number_input(
    "Slots desbloqueados",
    min_value=1,
    max_value=30,
    value=int(st.session_state["slots_desbloqueados"]),
    step=1,
)
if slot_count != st.session_state["slots_desbloqueados"]:
    old = st.session_state["slots_desbloqueados"]
    st.session_state["slots_desbloqueados"] = int(slot_count)
    if slot_count > old:
        for i in range(old + 1, int(slot_count) + 1):
            st.session_state["slots"].append(default_slot(i))
    else:
        st.session_state["slots"] = st.session_state["slots"][: int(slot_count)]
    st.rerun()

st.sidebar.markdown("### Qué hay en cada slot")
slot_options = ["Vacío", "Central eléctrica", "Embalse de agua", "Granja", "Depósito de Embarque"]
role_options = ["Semillera", "Venta"]

for idx in range(st.session_state["slots_desbloqueados"]):
    slot = st.session_state["slots"][idx]
    with st.sidebar.expander(f"Slot {idx+1}: {slot.get('tipo', 'Vacío')}" + (f" N{slot.get('nivel', 1)}" if slot.get("tipo") != "Vacío" else ""), expanded=(idx < 7)):
        tipo_actual = slot.get("tipo", "Vacío")
        tipo = st.selectbox(
            "Edificio",
            slot_options,
            index=slot_options.index(tipo_actual) if tipo_actual in slot_options else 0,
            key=f"slot_{idx}_tipo",
        )
        slot["tipo"] = tipo
        if tipo == "Vacío":
            slot["nivel"] = 1
            slot["rol"] = "Vacío"
            st.caption("Este slot está libre. Cuando construyas algo, elegilo acá.")
        else:
            slot["nivel"] = int(st.number_input("Nivel de ESTE edificio", min_value=1, max_value=20, value=int(slot.get("nivel", 1)), step=1, key=f"slot_{idx}_nivel"))
            if tipo == "Granja":
                rol_actual = slot.get("rol", "Venta")
                if rol_actual not in role_options:
                    rol_actual = "Venta"
                slot["rol"] = st.radio("Uso de ESTA granja", role_options, index=role_options.index(rol_actual), horizontal=True, key=f"slot_{idx}_rol")
            else:
                slot["rol"] = "Soporte"

st.sidebar.markdown("---")
st.sidebar.markdown("### Venta y cálculo")
product_mode = st.sidebar.radio("Producto de las granjas de venta", ["Automático", "Elegir yo"], index=0)
manual_crop = st.sidebar.selectbox("Producto elegido", farm_crops, index=farm_crops.index("Grano") if "Grano" in farm_crops else 0, disabled=(product_mode == "Automático"))
sale_mode = st.sidebar.radio("Canal de venta", ["Mercado", "Contrato", "Mejor automático"], index=0)
sell_surplus = st.sidebar.checkbox("Vender excedentes en mercado", value=True)

st.sidebar.markdown("### Fase y ajustes")
fase = st.sidebar.selectbox("Fase económica", ["Recesión", "Normal", "Boom"], index=1)
with st.sidebar.expander("Ajustes avanzados", expanded=False):
    production_mult = st.number_input("Multiplicador producción", 0.50, 1.50, 1.00, 0.01)
    salary_mult = st.number_input("Multiplicador salario", 0.50, 1.50, 1.00, 0.01)
    market_fee = st.slider("Comisión mercado", 0.0, 0.10, float(config.get("comision_mercado", 0.04)), 0.005)
    contract_discount = st.slider("Descuento contrato", 0.0, 0.10, float(config.get("descuento_contrato", 0.03)), 0.005)
    director_reduction = st.slider("Reducción administración director", 0.0, 0.80, float(config.get("reduccion_admin_director", 0.0)), 0.01)

# =============================
# Cálculos por slots
# =============================
slots = st.session_state["slots"]
slots_used = sum(1 for s in slots if s.get("tipo") != "Vacío")
empty_slots = st.session_state["slots_desbloqueados"] - slots_used

def slot_levels(tipo: str, rol: str | None = None) -> int:
    total = 0
    for s in slots:
        if s.get("tipo") != tipo:
            continue
        if rol is not None and s.get("rol") != rol:
            continue
        total += int(s.get("nivel", 1))
    return total

central_levels = slot_levels("Central eléctrica")
embalse_levels = slot_levels("Embalse de agua")
seed_levels = slot_levels("Granja", "Semillera")
crop_levels = slot_levels("Granja", "Venta")
depot_levels = slot_levels("Depósito de Embarque")
total_levels = sum(int(s.get("nivel", 1)) for s in slots if s.get("tipo") != "Vacío")

st.sidebar.info(f"Slots usados: {slots_used} · vacíos: {empty_slots} · niveles totales: {total_levels}")

# Base por nivel
central_prod_base = float(central["produccion_h"]) * production_mult
embalse_prod_base = float(embalse["produccion_h"]) * production_mult
embalse_elec_need_base = float(embalse["electricidad_necesaria_h"]) * production_mult
seed_prod_base = float(seed_product["produccion_h"]) * production_mult
seed_water_need_base = float(seed_product["agua_necesaria_h"]) * production_mult
transport_market_price = float(latest_prices.get("Transporte", config.get("precio_transporte_default", 0.389)))
diesel_price = float(latest_prices.get("Diésel", config.get("precio_diesel_default", 40.75)))


def admin_pct(levels_total: int) -> float:
    return max(0.0, (int(levels_total) - 1) / 170.0) * (1 - director_reduction)


def unit_costs(levels_total: int) -> dict:
    admin = admin_pct(levels_total)
    central_salary_lvl = float(central["salario_h"]) * salary_mult * (1 + admin)
    embalse_salary_lvl = float(embalse["salario_h"]) * salary_mult * (1 + admin)
    granja_salary_lvl = float(granja["salario_h"]) * salary_mult * (1 + admin)
    deposito_salary_lvl = float(deposito["salario_h"]) * salary_mult * (1 + admin)

    electricity_unit_cost = safe_div(central_salary_lvl, central_prod_base)
    water_unit_cost = safe_div(embalse_salary_lvl + embalse_elec_need_base * electricity_unit_cost, embalse_prod_base)
    seed_unit_cost = safe_div(granja_salary_lvl + seed_water_need_base * water_unit_cost, seed_prod_base)

    transport_output = float(deposito["produccion_h"]) * production_mult
    transport_own_cost = safe_div(
        deposito_salary_lvl + transport_output * (1 / 95) * electricity_unit_cost + transport_output * (1 / 190) * diesel_price,
        transport_output,
    )
    return {
        "admin": admin,
        "central_salary_lvl": central_salary_lvl,
        "embalse_salary_lvl": embalse_salary_lvl,
        "granja_salary_lvl": granja_salary_lvl,
        "deposito_salary_lvl": deposito_salary_lvl,
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


def physical_water_capacity(central_lvls: int, embalse_lvls: int) -> tuple[float, float, float, bool]:
    elec_total = central_lvls * central_prod_base
    elec_for_embalse_full = embalse_lvls * embalse_elec_need_base
    embalse_water_full = embalse_lvls * embalse_prod_base
    elec_shortage = elec_for_embalse_full > elec_total + 1e-9
    if not elec_shortage:
        water = embalse_water_full
        elec_surplus = elec_total - elec_for_embalse_full
    else:
        water = safe_div(elec_total, embalse_elec_need_base) * embalse_prod_base
        elec_surplus = 0.0
    return water, elec_total, elec_surplus, elec_shortage


def crop_unit_cost(crop_name: str, costs: dict) -> float:
    r = get_product(crop_name)
    prod = float(r.get("produccion_h", 0) or 0) * production_mult
    water_need = float(r.get("agua_necesaria_h", 0) or 0) * production_mult
    seed_need = float(r.get("semillas_necesarias_h", 0) or 0) * production_mult
    return safe_div(costs["granja_salary_lvl"] + water_need * costs["water_unit_cost"] + seed_need * costs["seed_unit_cost"], prod)


def simulate(crop_name: str) -> dict:
    costs = unit_costs(total_levels)
    transport_unit_cost = transport_market_price  # V1: por defecto se compra transporte.

    water_cap, elec_total, elec_surplus, elec_shortage = physical_water_capacity(central_levels, embalse_levels)
    r = get_product(crop_name)

    crop_prod_per_level = float(r["produccion_h"]) * production_mult
    crop_water_per_level = float(r["agua_necesaria_h"]) * production_mult
    crop_seed_per_level = float(r["semillas_necesarias_h"]) * production_mult

    seed_production_full = seed_levels * seed_prod_base
    seed_water_full = seed_levels * seed_water_need_base

    # Primero se abastece el bloque semillero.
    if seed_water_full > water_cap and seed_water_full > 0:
        seed_factor = water_cap / seed_water_full
        seed_production_real = seed_production_full * seed_factor
        water_left = 0.0
    else:
        seed_factor = 1.0
        seed_production_real = seed_production_full
        water_left = water_cap - seed_water_full

    crop_output_full = crop_levels * crop_prod_per_level
    crop_water_full = crop_levels * crop_water_per_level
    crop_seed_full = crop_levels * crop_seed_per_level

    factor_by_water = 1.0 if crop_water_full <= 0 else min(1.0, safe_div(water_left, crop_water_full))
    factor_by_seed = 1.0 if crop_seed_full <= 0 else min(1.0, safe_div(seed_production_real, crop_seed_full))
    crop_factor = min(factor_by_water, factor_by_seed)

    output = crop_output_full * crop_factor
    seeds_used = crop_seed_full * crop_factor
    water_used_crop = crop_water_full * crop_factor
    water_used = min(seed_water_full, water_cap) + water_used_crop

    seeds_surplus = max(0.0, seed_production_real - seeds_used)
    water_surplus = max(0.0, water_cap - water_used)
    elec_surplus = max(0.0, elec_surplus)

    channel, net_u = chosen_net_price(crop_name, transport_unit_cost)
    cost_u = crop_unit_cost(crop_name, costs)
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
        "Producto": crop_name,
        "Canal": channel,
        "Central nivel total": central_levels,
        "Embalse nivel total": embalse_levels,
        "Semillera nivel total": seed_levels,
        "Venta nivel total": crop_levels,
        "Depósito nivel total": depot_levels,
        "Slots usados": slots_used,
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
        "Costos": costs,
    }


if crop_levels <= 0:
    st.warning("No tenés ninguna granja marcada como 'Venta'. Marcá al menos un slot de Granja como Venta para simular producto principal.")
    st.stop()

if product_mode == "Automático":
    all_plans = pd.DataFrame([simulate(crop) for crop in farm_crops]).sort_values("Beneficio total/h", ascending=False).reset_index(drop=True)
    best = all_plans.iloc[0].to_dict()
else:
    best = simulate(manual_crop)
    all_plans = pd.DataFrame([simulate(crop) for crop in farm_crops]).sort_values("Beneficio total/h", ascending=False).reset_index(drop=True)

# =============================
# UI principal
# =============================
st.markdown('<div class="title">🏭 Plan por slots reales</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Cada slot es un edificio individual. Si una granja es nivel 3, se carga en ese slot. Si tenés dos granjas con niveles distintos, son dos slots separados.</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero">
        <div class="small">Empresa cargada: <b>{slots_used} slots usados</b> · <b>{empty_slots} vacío(s)</b> · <b>{total_levels} niveles totales</b></div>
        <div style="font-size:2.05rem;font-weight:950;margin-top:4px;">{best['Producto']} · {money(best['Beneficio total/h'])}/h</div>
        <div style="margin-top:10px;">
            <span class="pill pill-blue">Central nivel total {central_levels}</span>
            <span class="pill pill-blue">Embalse nivel total {embalse_levels}</span>
            <span class="pill pill-good">Semillera nivel total {seed_levels}</span>
            <span class="pill pill-good">Venta nivel total {crop_levels}</span>
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

if empty_slots > 0:
    st.info("Tenés slot vacío. No se recomienda nada raro automáticamente: elegí vos en el slot vacío si querés probar una Granja, Embalse, Central o Depósito.")

st.markdown("### Bloques reales")
b1, b2, b3 = st.columns(3)
with b1:
    st.markdown(f"""<div class="card"><h3>Soporte</h3><div class="big">Central {central_levels} · Embalse {embalse_levels}</div><div class="small">Suma de niveles reales cargados en slots individuales.</div></div>""", unsafe_allow_html=True)
with b2:
    st.markdown(f"""<div class="card"><h3>Semillas</h3><div class="big good">Nivel total {seed_levels}</div><div class="small">Produce {num(best['Semillas producidas/h'],1)} semillas/h · usa {num(best['Semillas usadas/h'],1)} · sobra {num(best['Semillas sobrantes/h'],1)}</div></div>""", unsafe_allow_html=True)
with b3:
    st.markdown(f"""<div class="card"><h3>Venta</h3><div class="big warn">Nivel total {crop_levels}</div><div class="small">Granjas marcadas como Venta fabrican {best['Producto']}.</div></div>""", unsafe_allow_html=True)

st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["✅ Plan actual", "🧱 Slots", "📊 Comparar productos", "⚙️ Costos"])

with tab1:
    st.markdown("### Saldos por hora")
    s1, s2, s3 = st.columns(3)
    s1.metric("Electricidad sobrante", num(best["Electricidad sobrante/h"], 1))
    s2.metric("Agua sobrante", num(best["Agua sobrante/h"], 1))
    s3.metric("Semillas sobrantes", num(best["Semillas sobrantes/h"], 1))

    if best["Excedentes"]:
        st.markdown("### Excedentes vendidos para flujo de caja")
        ex = pd.DataFrame(best["Excedentes"])
        ex_view = ex.copy()
        ex_view["Cantidad/h"] = ex_view["Cantidad/h"].map(lambda x: num(x, 1))
        ex_view["Beneficio/u"] = ex_view["Beneficio/u"].map(money)
        ex_view["Beneficio/h"] = ex_view["Beneficio/h"].map(money)
        st.dataframe(ex_view, hide_index=True, use_container_width=True)
    else:
        st.info("No hay excedentes vendibles relevantes, o desactivaste vender excedentes.")

    st.markdown("### Lectura rápida")
    if "agua" in str(best["Cuello"]):
        st.warning("Este plan está limitado por agua.")
    elif "semillas" in str(best["Cuello"]):
        st.warning("Este plan está limitado por semillas.")
    elif "electricidad" in str(best["Cuello"]):
        st.warning("Este plan está limitado por electricidad.")
    else:
        st.success("No aparece un cuello fuerte con los slots cargados.")

with tab2:
    st.markdown("### Cada slot cargado")
    rows = []
    for i, s in enumerate(slots, start=1):
        rows.append({
            "Slot": i,
            "Edificio": s.get("tipo", "Vacío"),
            "Nivel": "—" if s.get("tipo") == "Vacío" else int(s.get("nivel", 1)),
            "Uso": s.get("rol", "—"),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("Ejemplo correcto: si el Slot 3 es Granja nivel 3, es UNA granja nivel 3. Si el Slot 4 es Granja nivel 1, es otra granja distinta.")

with tab3:
    st.markdown("### Productos posibles con los mismos slots")
    view_cols = ["Producto", "Canal", "Producción vendible/h", "Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h", "Cuello"]
    top = all_plans[view_cols].head(30).copy()
    top["Producción vendible/h"] = top["Producción vendible/h"].map(lambda x: num(x, 1))
    for col in ["Beneficio cultivo/h", "Beneficio excedentes/h", "Beneficio total/h"]:
        top[col] = top[col].map(money)
    st.dataframe(top, hide_index=True, use_container_width=True)
    st.caption("Esta tabla no cambia tus slots. Solo compara qué fabricar en las granjas marcadas como Venta.")

with tab4:
    st.markdown("### Costos usados")
    costs_now = best["Costos"]
    costs_df = pd.DataFrame([
        ["Administración por niveles", pct(costs_now["admin"])],
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
st.caption("V1.9: slots individuales. Nada de nivel promedio. Cada edificio tiene su propio nivel y su propio uso.")
