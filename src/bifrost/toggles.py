"""User preference toggles: scalarized multi-objective scoring."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Preference(str, Enum):
    MAX_OUTPUT = "max_output"
    FASTEST = "fastest"
    CHEAPEST = "cheapest"


@dataclass(frozen=True)
class Preset:
    w_gas: float  # USD penalty per $1 gas
    w_time: float  # USD penalty per second of ETA
    w_risk: float  # fractional haircut of out_usd per unit risk
    max_eta_sec: float | None = None


PRESETS: dict[Preference, Preset] = {
    Preference.MAX_OUTPUT: Preset(w_gas=1.0, w_time=0.001, w_risk=0.05),
    Preference.FASTEST: Preset(w_gas=1.0, w_time=0.05, w_risk=0.05, max_eta_sec=300),
    Preference.CHEAPEST: Preset(w_gas=2.0, w_time=0.0005, w_risk=0.02),
}


def score_route(
    out_usd: float, gas_usd: float, eta_sec: float, risk: float, pref: Preference
) -> float:
    p = PRESETS[pref]
    return out_usd - p.w_gas * gas_usd - p.w_time * eta_sec - p.w_risk * risk * out_usd


def passes_filter(eta_sec: float, pref: Preference) -> bool:
    p = PRESETS[pref]
    return not (p.max_eta_sec is not None and eta_sec > p.max_eta_sec)
