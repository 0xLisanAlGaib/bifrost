"""Oracles: USD prices + gas. Offline defaults from registry; live via Chainlink/Pyth."""

# Re-export to keep a stable import path; files kept separate per tasks/06.
from .registry import PRICES_V1 as DEFAULT_PRICES_USD  # noqa: F401

GAS_DEFAULT_USD: dict[int, float] = {1: 3.0, 8453: 0.10}


def gas_usd(chain_id: int) -> float:
    # TODO(live): gas_units * gas_price * native_price.
    return GAS_DEFAULT_USD.get(chain_id, 1.0)
