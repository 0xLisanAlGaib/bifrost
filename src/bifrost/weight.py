"""Weight engine: amount-dependent edge cost functions.

Effective output for input x on edge e:
    y = x * spot * (1 - fee) * slippage(x, L, model) - gas_usd / price_out_usd

Slippage models (deterministic, offline):
- cpmm:           1 / (1 + x / L)
- stable:         1 / (1 + 0.05 * x / L)   (~20x less impact than cpmm)
- fixed_variable: 1.0  (variable fee in fee_bps, fixed fee in gas_usd)
- one_to_one:     1.0  (wrap/unwrap)

Unknown depth (L <= 0) -> factor 1.0 (no slippage estimate).
"""
from __future__ import annotations

from .graph import DirectedEdge


def slippage_factor(x_in: float, liquidity: float, model: str) -> float:
    if x_in <= 0:
        return 1.0
    if liquidity is None or liquidity <= 0:
        return 1.0
    ratio = x_in / liquidity
    if model == "cpmm":
        return 1.0 / (1.0 + ratio)
    if model == "stable":
        return 1.0 / (1.0 + 0.05 * ratio)
    if model in ("fixed_variable", "one_to_one"):
        return 1.0
    raise ValueError(f"unknown slippage model: {model}")


def quote_edge(edge: DirectedEdge, x_in: float, price_out_usd: float) -> float:
    """Simulate output amount of `to`-asset for input `x_in` of `from`-asset."""
    if x_in <= 0:
        return 0.0
    gross = x_in * edge.spot_rate * (1.0 - edge.fee_bps / 10_000.0)
    gross *= slippage_factor(x_in, edge.liquidity, edge.model)
    gas_in_output = 0.0
    if edge.gas_usd > 0 and price_out_usd and price_out_usd > 0:
        gas_in_output = edge.gas_usd / price_out_usd
    return max(gross - gas_in_output, 0.0)


def baseline_edge(edge: DirectedEdge, x_in: float) -> float:
    """Infinite-liquidity, zero-gas baseline for price-impact measurement."""
    if x_in <= 0:
        return 0.0
    return x_in * edge.spot_rate * (1.0 - edge.fee_bps / 10_000.0)
