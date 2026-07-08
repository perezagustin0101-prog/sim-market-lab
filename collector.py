from __future__ import annotations

import csv
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import requests

ROOT = Path(__file__).resolve().parent
HISTORY_PATH = ROOT / "historial_mercado.csv"
PHASE_PATH = ROOT / "fase_mercado_actual.csv"
SETTINGS_PATH = ROOT / "settings.json"
PRODUCTS_PATH = ROOT / "products.csv"

HISTORY_FIELDS = [
    "collected_at_utc",
    "kind",
    "name",
    "quality",
    "min_price",
    "quantity_at_min_price",
    "total_visible_quantity",
    "order_count",
]

PHASE_FIELDS = [
    "collected_at_utc",
    "kind",
    "name",
    "quality",
    "min_price",
    "points",
    "historical_min_price",
    "historical_max_price",
    "historical_avg_price",
    "percentile",
    "trend",
    "phase",
]


def load_settings() -> Dict[str, Any]:
    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_products() -> List[Dict[str, Any]]:
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError("No existe products.csv")
    products: List[Dict[str, Any]] = []
    with PRODUCTS_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                kind = int(row["kind"])
            except (KeyError, TypeError, ValueError):
                continue
            name = (row.get("name") or f"Producto {kind}").strip()
            products.append({"kind": kind, "name": name})
    if not products:
        raise RuntimeError("products.csv no tiene productos válidos")
    return products


def pick_product_for_this_run(products: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
    # Elegimos 1 producto por ejecución para no hacer muchas peticiones juntas.
    # Con GitHub Actions cada 6 minutos, rota por tiempo: 0, 1, 2, 3...
    window_seconds = int(settings.get("rotation_window_seconds", 360))
    index = int(time.time() // window_seconds) % len(products)
    return products[index]


def fetch_market_orders(settings: Dict[str, Any], kind: int) -> List[Dict[str, Any]]:
    url = settings["market_order_url_template"].format(
        realm_id=settings.get("realm_id", 0),
        kind=kind,
    )
    response = requests.get(
        url,
        timeout=settings.get("request_timeout_seconds", 30),
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError(f"Se esperaba una lista JSON, llegó {type(data).__name__}: {data!r}")
    return data


def summarize_orders(raw_orders: Iterable[Dict[str, Any]], product: Dict[str, Any], collected_at: str) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    requested_kind = int(product["kind"])
    name = str(product["name"])

    for item in raw_orders:
        try:
            kind = int(item.get("kind", requested_kind))
            quality = int(item.get("quality", 0))
            price = float(item.get("price"))
            quantity = int(float(item.get("quantity", 0)))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(price) or quantity <= 0:
            continue
        grouped.setdefault((kind, quality), []).append({"price": price, "quantity": quantity})

    rows: List[Dict[str, Any]] = []
    for (kind, quality), orders in grouped.items():
        min_price = min(o["price"] for o in orders)
        quantity_at_min = sum(o["quantity"] for o in orders if o["price"] == min_price)
        total_quantity = sum(o["quantity"] for o in orders)
        rows.append(
            {
                "collected_at_utc": collected_at,
                "kind": kind,
                "name": name,
                "quality": quality,
                "min_price": round(min_price, 6),
                "quantity_at_min_price": quantity_at_min,
                "total_visible_quantity": total_quantity,
                "order_count": len(orders),
            }
        )
    rows.sort(key=lambda r: (r["kind"], r["quality"]))
    return rows


def append_history(rows: List[Dict[str, Any]]) -> None:
    file_exists = HISTORY_PATH.exists() and HISTORY_PATH.stat().st_size > 0
    with HISTORY_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def load_history() -> List[Dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    out: List[Dict[str, Any]] = []
    with HISTORY_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                out.append(
                    {
                        "collected_at_utc": row["collected_at_utc"],
                        "kind": int(row["kind"]),
                        "name": row.get("name") or f"Producto {row['kind']}",
                        "quality": int(row["quality"]),
                        "min_price": float(row["min_price"]),
                        "quantity_at_min_price": int(float(row.get("quantity_at_min_price", 0))),
                        "total_visible_quantity": int(float(row.get("total_visible_quantity", 0))),
                        "order_count": int(float(row.get("order_count", 0))),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return out


def percentile_rank(values: List[float], current: float) -> float:
    if not values:
        return float("nan")
    below_or_equal = sum(1 for v in values if v <= current)
    return round(100 * below_or_equal / len(values), 2)


def calc_trend(prices: List[float], short_n: int, long_n: int) -> str:
    if len(prices) < max(3, short_n):
        return "sin datos"
    short_slice = prices[-short_n:]
    long_slice = prices[-min(long_n, len(prices)):]
    short_avg = sum(short_slice) / len(short_slice)
    long_avg = sum(long_slice) / len(long_slice)
    if short_avg > long_avg * 1.01:
        return "subiendo"
    if short_avg < long_avg * 0.99:
        return "bajando"
    return "lateral"


def classify_phase(percentile: float, trend: str, points: int, min_points: int) -> str:
    if points < min_points:
        return "sin historial suficiente"
    if percentile <= 20:
        return "barato / sobreoferta"
    if percentile <= 40:
        return "bajo-normal / recuperación" if trend == "subiendo" else "bajo-normal"
    if percentile <= 70:
        return "normal"
    if percentile <= 90:
        return "caro"
    return "pico / oportunidad de venta"


def build_latest_phase(history: List[Dict[str, Any]], settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    for row in history:
        grouped.setdefault((row["kind"], row["quality"]), []).append(row)

    latest_rows: List[Dict[str, Any]] = []
    min_points = int(settings.get("phase_min_points", 20))
    short_n = int(settings.get("short_window_points", 12))
    long_n = int(settings.get("long_window_points", 96))

    for (kind, quality), rows in grouped.items():
        rows = sorted(rows, key=lambda r: r["collected_at_utc"])
        prices = [float(r["min_price"]) for r in rows]
        latest = rows[-1]
        current = float(latest["min_price"])
        pctl = percentile_rank(prices, current)
        trend = calc_trend(prices, short_n, long_n)
        phase = classify_phase(pctl, trend, len(prices), min_points)
        latest_rows.append(
            {
                "collected_at_utc": latest["collected_at_utc"],
                "kind": kind,
                "name": latest.get("name") or f"Producto {kind}",
                "quality": quality,
                "min_price": round(current, 6),
                "points": len(prices),
                "historical_min_price": round(min(prices), 6),
                "historical_max_price": round(max(prices), 6),
                "historical_avg_price": round(sum(prices) / len(prices), 6),
                "percentile": pctl,
                "trend": trend,
                "phase": phase,
            }
        )
    latest_rows.sort(key=lambda r: (r["name"], r["quality"]))
    return latest_rows


def write_phase(rows: List[Dict[str, Any]]) -> None:
    with PHASE_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PHASE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    settings = load_settings()
    products = load_products()
    product = pick_product_for_this_run(products, settings)
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    raw_orders = fetch_market_orders(settings, int(product["kind"]))
    rows = summarize_orders(raw_orders, product, collected_at)
    if not rows:
        raise RuntimeError(f"No llegaron órdenes útiles para {product}")

    append_history(rows)
    history = load_history()
    phase_rows = build_latest_phase(history, settings)
    write_phase(phase_rows)

    print(f"Producto recolectado: {product['name']} ({product['kind']})")
    print(f"Filas agregadas: {len(rows)}")
    print(f"Historial total: {len(history)}")
    print(f"Fases actuales: {len(phase_rows)}")


if __name__ == "__main__":
    main()
