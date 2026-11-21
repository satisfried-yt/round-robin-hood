"""Validated optional HA financial and PV sources; never used for switching."""
from __future__ import annotations
import math

# Normalization is intentionally strict: Wh is energy, W is power; tariff
# currency must match the RRH currency. Unknown/missing units are not guessed.
def normalize_unit(unit: str | None) -> str:
    return str(unit or "").replace(" ", "").lower()


def divisor_and_scale(kind: str, unit: str | None, currency: str = "EUR") -> float | None:
    """Return multiplicative conversion to kWp, currency/kWh, W or kWh."""
    unit = normalize_unit(unit)
    if kind == "capacity":
        return {"w": .001, "wp": .001, "kw": 1, "kwp": 1}.get(unit)
    if kind == "power":
        return {"w": 1, "kw": 1000}.get(unit)
    if kind == "energy":
        return {"wh": .001, "kwh": 1, "mwh": 1000}.get(unit)
    if kind != "price":
        return None
    price_units={
        "EUR": {"€/kwh":1, "eur/kwh":1, "euro/kwh":1, "ct/kwh":.01, "cent/kwh":.01, "c/kwh":.01, "€/mwh":.001, "eur/mwh":.001},
        "CHF": {"chf/kwh":1, "fr./kwh":1, "fr/kwh":1, "chf/mwh":.001},
        "USD": {"usd/kwh":1, "$/kwh":1, "usd/mwh":.001},
        "GBP": {"gbp/kwh":1, "£/kwh":1, "gbp/mwh":.001},
    }
    return price_units.get(currency,{}).get(unit)


def numeric_source_value(value, unit, kind: str, currency: str = "EUR") -> float:
    """Raise ValueError rather than displaying/billing invalid sensor readings."""
    if isinstance(value, bool):
        raise ValueError("boolean is not a measurement")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as err:
        raise ValueError("not numeric") from err
    scale = divisor_and_scale(kind, unit, currency)
    if scale is None:
        raise ValueError("incompatible or missing unit")
    if not math.isfinite(number) or number < 0 or number >= 1e10:
        raise ValueError("invalid value")
    result = number * scale
    if not math.isfinite(result):
        raise ValueError("invalid converted value")
    return result
