from __future__ import annotations

import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT
CONFIG_DIR = ROOT
HISTORY_PATH = ROOT / "historial_mercado.csv"
PHASE_PATH = ROOT / "fase_mercado_actual.csv"
SETTINGS_PATH = ROOT / "settings.json"
PRODUCTS_PATH = ROOT / "products.csv"

HISTORY_FIELDS = [
    "collected_at_utc",
    "kind",
    "quality",
    "price",
]

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


def now_iso_for_url() -> str:
    # Sim Companies ticker examples use ISO-like timestamps.
    # Keeping milliseconds and Z avoids locale issues.
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def fetch_market_ticker(settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = settings["market_ticker_url_template"].format(timestamp=now_iso_for_url())
    response = requests.get(url, timeout=settings.get("request_timeout_seconds", 30))
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError(f"Expected list from market ticker, got {type(data).__name__}: {data!r}")
    return data


def normalize_rows(raw_rows: Iterable[Dict[str, Any]], collected_at: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in raw_rows:
        # Market ticker payloads historically contain kind, quality and price.
        # We intentionally ignore account/private fields and do not use cookies/auth.
        try:
            kind = int(item.get("kind"))
            quality = int(item.get("quality", 0))
            price = float(item.get("price"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(price):
            continue
        rows.append(
            {
                "collected_at_utc": collected_at,
                "kind": kind,
                "quality": quality,
                "price": price,
            }
        )
    return rows


def append_history(rows: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = HISTORY_PATH.exists() and HISTORY_PATH.stat().st_size > 0
    with HISTORY_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def load_history() -> List[Dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        out = []
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
    with PRODUCTS_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        names = {}
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


def build_latest_phase(history: List[Dict[str, Any]], settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    names = load_product_names()
    grouped: Dict[tuple[int, int], List[Dict[str, Any]]] = {}
    for row in history:
        key = (row["kind"], row["quality"])
        grouped.setdefault(key, []).append(row)

    latest_rows: List[Dict[str, Any]] = []
    min_points = int(settings.get("phase_min_points", 20))
    short_n = int(settings.get("short_window_points", 12))
    long_n = int(settings.get("long_window_points", 96))

    for (kind, quality), rows in grouped.items():
        rows = sorted(rows, key=lambda r: r["collected_at_utc"])
        prices = [r["price"] for r in rows]
        latest = rows[-1]
        current = latest["price"]
        pctl = percentile_rank(prices, current)
        trend = calc_trend(prices, short_n, long_n)
        phase = classify_phase(pctl, trend, len(prices), min_points)
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
                "percentile": pctl,
                "trend": trend,
                "phase": phase,
            }
        )

    latest_rows.sort(key=lambda r: (r["name"], r["quality"]))
    return latest_rows


def write_phase(rows: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PHASE_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PHASE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    settings = load_settings()
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    raw = fetch_market_ticker(settings)
    rows = normalize_rows(raw, collected_at)
    if not rows:
        raise RuntimeError("Market ticker returned no usable rows")
    append_history(rows)
    history = load_history()
    phase_rows = build_latest_phase(history, settings)
    write_phase(phase_rows)
    print(f"Collected {len(rows)} ticker rows at {collected_at}")
    print(f"History rows: {len(history)}")
    print(f"Phase rows: {len(phase_rows)}")


if __name__ == "__main__":
    main()
