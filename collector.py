from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

ROOT = Path(__file__).resolve().parent
HISTORY_PATH = ROOT / "historial_mercado.csv"
PHASE_PATH = ROOT / "fase_mercado_actual.csv"
SETTINGS_PATH = ROOT / "settings.json"
PRODUCTS_PATH = ROOT / "products.csv"

HISTORY_FIELDS = ["collected_at_utc", "kind", "quality", "price"]
PHASE_FIELDS = [
    "collected_at_utc",
    "kind",
    "name",
    "quality",
    "price",
    "points",
    "min_price",
    "max_price",
    "avg_price",
    "percentile",
    "trend",
    "phase",
]


def load_settings() -> Dict[str, Any]:
    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_market_ticker(settings: Dict[str, Any]) -> Any:
    # Endpoint global detectado en el navegador:
    # https://www.simcompanies.com/api/v3/market-ticker/0/
    url = settings.get("market_ticker_url") or settings.get("market_ticker_url_template")
    if not url:
        raise RuntimeError("settings.json no tiene market_ticker_url")
    response = requests.get(url, timeout=settings.get("request_timeout_seconds", 30))
    response.raise_for_status()
    return response.json()


def _try_add_row(rows: List[Dict[str, Any]], collected_at: str, kind: Any, quality: Any, price: Any) -> None:
    try:
        k = int(kind)
        q = int(quality if quality is not None else 0)
        p = float(price)
    except (TypeError, ValueError):
        return
    if not math.isfinite(p):
        return
    rows.append({"collected_at_utc": collected_at, "kind": k, "quality": q, "price": p})


def normalize_rows(payload: Any, collected_at: str) -> List[Dict[str, Any]]:
    """Acepta varias formas posibles del ticker.

    Esperado típico: lista de objetos con kind, quality y price.
    También soporta dicts que contengan listas en keys comunes o mapas kind->price.
    """
    rows: List[Dict[str, Any]] = []

    if isinstance(payload, dict):
        # Caso: {"data": [...]} / {"resources": [...]} / etc.
        for key in ("data", "results", "resources", "items", "ticker"):
            if isinstance(payload.get(key), list):
                return normalize_rows(payload[key], collected_at)

        # Caso: {"1": 0.27, "2": 0.38} o {"1": {"0": 0.27}}
        for kind, value in payload.items():
            if isinstance(value, dict):
                for quality, price in value.items():
                    _try_add_row(rows, collected_at, kind, quality, price)
            else:
                _try_add_row(rows, collected_at, kind, 0, value)
        return rows

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind") or item.get("resource") or item.get("resourceId") or item.get("id")
            quality = item.get("quality", 0)
            price = item.get("price") or item.get("marketPrice") or item.get("lowestPrice") or item.get("minPrice")
            _try_add_row(rows, collected_at, kind, quality, price)
        return rows

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
                        "quality": int(row["quality"]),
                        "price": float(row["price"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return out


def load_product_names() -> Dict[int, str]:
    if not PRODUCTS_PATH.exists():
        return {}
    names: Dict[int, str] = {}
    with PRODUCTS_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                names[int(row["kind"])] = row["name"]
            except (KeyError, TypeError, ValueError):
                continue
    return names


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
    names = load_product_names()
    grouped: Dict[tuple[int, int], List[Dict[str, Any]]] = {}
    for row in history:
        grouped.setdefault((row["kind"], row["quality"]), []).append(row)

    min_points = int(settings.get("phase_min_points", 20))
    short_n = int(settings.get("short_window_points", 12))
    long_n = int(settings.get("long_window_points", 96))
    latest_rows: List[Dict[str, Any]] = []

    for (kind, quality), rows in grouped.items():
        rows = sorted(rows, key=lambda r: r["collected_at_utc"])
        prices = [r["price"] for r in rows]
        latest = rows[-1]
        current = latest["price"]
        percentile = percentile_rank(prices, current)
        trend = calc_trend(prices, short_n, long_n)
        latest_rows.append(
            {
                "collected_at_utc": latest["collected_at_utc"],
                "kind": kind,
                "name": names.get(kind, f"Producto {kind}"),
                "quality": quality,
                "price": round(current, 6),
                "points": len(prices),
                "min_price": round(min(prices), 6),
                "max_price": round(max(prices), 6),
                "avg_price": round(sum(prices) / len(prices), 6),
                "percentile": percentile,
                "trend": trend,
                "phase": classify_phase(percentile, trend, len(prices), min_points),
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
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload = fetch_market_ticker(settings)
    rows = normalize_rows(payload, collected_at)
    if not rows:
        raise RuntimeError(f"El ticker no devolvió filas utilizables. Payload ejemplo: {str(payload)[:500]}")
    append_history(rows)
    history = load_history()
    phase_rows = build_latest_phase(history, settings)
    write_phase(phase_rows)
    print(f"Collected {len(rows)} ticker rows at {collected_at}")
    print(f"History rows: {len(history)}")
    print(f"Phase rows: {len(phase_rows)}")


if __name__ == "__main__":
    main()
