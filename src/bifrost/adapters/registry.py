"""v1 mock graph: Eth (1) + Base (8453), 17 assets, representative venues.

How to add an asset (scales to 50+):
1. Add `symbol: price_usd` to ASSET_PRICES (nodes appear on both chains).
2. Add one DEX_PAIRS row per liquid pair (spot rates derive from prices).
3. Optionally add it to NEW_BRIDGES (absence = no direct bridge; the
   pathfinder routes via a bridged intermediate — see connectivity test).
HYPE deferred to v2.
Prices (USD): ETH/WETH 3000, stables 1, WBTC/cbBTC 65000,
wstETH 3450, cbETH 3050, weETH 3200, ezETH 3100, rETH 3300,
LINK 18, AAVE 150, UNI 9.
"""
from __future__ import annotations

from ..graph import DirectedEdge, Graph, Node

ETH = 1
BASE = 8453

ASSET_PRICES: dict[str, float] = {
    "ETH": 3000.0,
    "WETH": 3000.0,
    "USDC": 1.0,
    "USDT": 1.0,
    "DAI": 1.0,
    "WBTC": 65000.0,
    "cbBTC": 65000.0,
    "wstETH": 3450.0,
    "cbETH": 3050.0,
    "weETH": 3200.0,
    "ezETH": 3100.0,
    "rETH": 3300.0,
    "LINK": 18.0,
    "AAVE": 150.0,
    "UNI": 9.0,
    "USDe": 1.0,
    "FRAX": 1.0,
}

PRICES_V1: dict[str, float] = {
    f"{c}:{s}": p for c in (ETH, BASE) for s, p in ASSET_PRICES.items()
}

_CHAIN_NAME = {ETH: "eth", BASE: "base"}
# Default per-chain DEX leg params: (gas_usd, latency_sec, risk_score).
_DEX_DEFAULTS = {ETH: (3.0, 15, 0.05), BASE: (0.10, 3, 0.08)}

# New-asset DEX pairs: (id_prefix, chain, sym_a, sym_b, venue, fee_bps,
#                      liq_a, liq_b, model). Spots derive from ASSET_PRICES.
DEX_PAIRS: list[tuple] = [
    ("uni", ETH, "WETH", "weETH", "uniswapv3-5bps", 5, 20_000, 18_000, "cpmm"),
    ("uni", ETH, "WETH", "ezETH", "uniswapv3-5bps", 5, 15_000, 14_000, "cpmm"),
    ("uni", ETH, "WETH", "rETH", "uniswapv3-5bps", 5, 25_000, 22_000, "cpmm"),
    ("uni30", ETH, "WETH", "LINK", "uniswapv3-30bps", 30, 8_000, 1_300_000, "cpmm"),
    ("uni30", ETH, "WETH", "AAVE", "uniswapv3-30bps", 30, 6_000, 120_000, "cpmm"),
    ("uni30", ETH, "WETH", "UNI", "uniswapv3-30bps", 30, 7_000, 2_300_000, "cpmm"),
    ("curve", ETH, "USDC", "USDe", "curve-stable", 1, 50_000_000, 50_000_000, "stable"),
    ("curve", ETH, "USDC", "FRAX", "curve-stable", 1, 50_000_000, 50_000_000, "stable"),
    ("curve", ETH, "FRAX", "DAI", "curve-stable", 1, 30_000_000, 30_000_000, "stable"),
    ("aero", BASE, "WETH", "weETH", "aerodrome", 5, 9_000, 8_500, "cpmm"),
    ("aero", BASE, "WETH", "ezETH", "aerodrome", 5, 7_000, 6_800, "cpmm"),
    ("aero", BASE, "WETH", "rETH", "aerodrome", 5, 9_000, 8_000, "cpmm"),
    ("aero", BASE, "WETH", "LINK", "aerodrome", 5, 5_000, 800_000, "cpmm"),
    ("aero", BASE, "WETH", "AAVE", "aerodrome", 5, 4_000, 80_000, "cpmm"),
    ("aero", BASE, "WETH", "UNI", "aerodrome", 5, 5_000, 1_600_000, "cpmm"),
    ("aero", BASE, "USDC", "USDe", "aerodrome", 1, 6_000_000, 6_000_000, "stable"),
    ("aero", BASE, "USDC", "FRAX", "aerodrome", 1, 6_000_000, 6_000_000, "stable"),
]

# New-asset bridge support: venue -> {symbol: extra_fee_bps}.
# Symbols absent here (rETH, AAVE, UNI) have NO direct bridge and must route
# via a bridged intermediate — the connectivity test proves they still resolve.
NEW_BRIDGES: dict[str, dict[str, float]] = {
    "across": {"weETH": 2, "LINK": 4, "USDe": 2},
    "stargate": {"ezETH": 2, "USDe": 2, "FRAX": 2},
}


def _e(
    eid: str,
    c1: int,
    s1: str,
    c2: int,
    s2: str,
    kind: str,
    venue: str,
    spot: float,
    fee_bps: float = 0.0,
    liquidity: float = 0.0,
    model: str = "cpmm",
    gas_usd: float = 0.0,
    latency_sec: float = 0.0,
    risk_score: float = 0.0,
) -> DirectedEdge:
    return DirectedEdge(
        eid,
        Node(c1, s1),
        Node(c2, s2),
        kind,
        venue,
        spot,
        fee_bps,
        liquidity,
        model,
        gas_usd,
        latency_sec,
        risk_score,
    )


def build_v1_mock_graph() -> tuple[Graph, dict[str, float]]:
    g = Graph()
    for c in (ETH, BASE):
        # Wrap / unwrap (1:1, gas only).
        g.add_edge(_e(f"wrap-{c}", c, "ETH", c, "WETH", "wrap", "native-wrap", 1.0, 0, 0, "one_to_one", 0.50, 2, 0.0))
        g.add_edge(_e(f"unwrap-{c}", c, "WETH", c, "ETH", "wrap", "native-wrap", 1.0, 0, 0, "one_to_one", 0.50, 2, 0.0))

    # --- Eth excep DEX ---
    # UniswapV3 WETH<->USDC (5bps, deep cpmm).
    g.add_edge(_e("uni-eth-WETH-USDC", ETH, "WETH", ETH, "USDC", "dex", "uniswapv3-5bps", 3000.0, 5, 5_000_000, "cpmm", 3.0, 15, 0.05))
    g.add_edge(_e("uni-eth-USDC-WETH", ETH, "USDC", ETH, "WETH", "dex", "uniswapv3-5bps", 1 / 3000.0, 5, 15_000_000, "cpmm", 3.0, 15, 0.05))
    # Curve stables USDC<->USDT / USDC<->DAI (1bp, stable model, very deep).
    for a, b in (("USDC", "USDT"), ("USDT", "USDC"), ("USDC", "DAI"), ("DAI", "USDC")):
        g.add_edge(_e(f"curve-eth-{a}-{b}", ETH, a, ETH, b, "dex", "curve-stable", 1.0, 1, 50_000_000, "stable", 2.0, 15, 0.05))
    # Uniswap WBTC<->WETH.
    g.add_edge(_e("uni-eth-WBTC-WETH", ETH, "WBTC", ETH, "WETH", "dex", "uniswapv3-30bps", 65000 / 3000, 30, 500, "cpmm", 3.0, 15, 0.05))
    g.add_edge(_e("uni-eth-WETH-WBTC", ETH, "WETH", ETH, "WBTC", "dex", "uniswapv3-30bps", 3000 / 65000, 30, 10_000, "cpmm", 3.0, 15, 0.05))
    # Uniswap LSTs: WETH<->wstETH (1bp tier) and WETH<->cbETH.
    g.add_edge(_e("uni-eth-WETH-wstETH", ETH, "WETH", ETH, "wstETH", "dex", "uniswapv3-1bp", 3000 / 3450, 1, 50_000, "cpmm", 3.0, 15, 0.05))
    g.add_edge(_e("uni-eth-wstETH-WETH", ETH, "wstETH", ETH, "WETH", "dex", "uniswapv3-1bp", 3450 / 3000, 1, 40_000, "cpmm", 3.0, 15, 0.05))
    g.add_edge(_e("uni-eth-WETH-cbETH", ETH, "WETH", ETH, "cbETH", "dex", "uniswapv3-5bps", 3000 / 3050, 5, 30_000, "cpmm", 3.0, 15, 0.05))
    g.add_edge(_e("uni-eth-cbETH-WETH", ETH, "cbETH", ETH, "WETH", "dex", "uniswapv3-5bps", 3050 / 3000, 5, 30_000, "cpmm", 3.0, 15, 0.05))
    # WBTC<->cbBTC pegged pair (stable model).
    g.add_edge(_e("uni-eth-WBTC-cbBTC", ETH, "WBTC", ETH, "cbBTC", "dex", "uniswapv3-1bp", 1.0, 1, 2_000, "stable", 3.0, 15, 0.05))
    g.add_edge(_e("uni-eth-cbBTC-WBTC", ETH, "cbBTC", ETH, "WBTC", "dex", "uniswapv3-1bp", 1.0, 1, 2_000, "stable", 3.0, 15, 0.05))

    # --- Base DEX ---
    g.add_edge(_e("aero-base-WETH-USDC", BASE, "WETH", BASE, "USDC", "dex", "aerodrome", 3000.0, 5, 2_000_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-USDC-WETH", BASE, "USDC", BASE, "WETH", "dex", "aerodrome", 1 / 3000.0, 5, 6_000_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("uni-base-WETH-USDC", BASE, "WETH", BASE, "USDC", "dex", "uniswapv3-5bps", 2999.0, 5, 1_000_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("uni-base-USDC-WETH", BASE, "USDC", BASE, "WETH", "dex", "uniswapv3-5bps", 1 / 2999.0, 5, 3_000_000, "cpmm", 0.10, 3, 0.08))
    # Base BTC: cbBTC<->USDC on two venues + WBTC<->USDC + pegged WBTC<->cbBTC.
    g.add_edge(_e("aero-base-cbBTC-USDC", BASE, "cbBTC", BASE, "USDC", "dex", "aerodrome", 65000.0, 5, 200, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-USDC-cbBTC", BASE, "USDC", BASE, "cbBTC", "dex", "aerodrome", 1 / 65000.0, 5, 13_000_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("uni-base-cbBTC-USDC", BASE, "cbBTC", BASE, "USDC", "dex", "uniswapv3-5bps", 64980.0, 5, 100, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("uni-base-USDC-cbBTC", BASE, "USDC", BASE, "cbBTC", "dex", "uniswapv3-5bps", 1 / 64980.0, 5, 6_500_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-WBTC-USDC", BASE, "WBTC", BASE, "USDC", "dex", "aerodrome", 65000.0, 5, 80, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-USDC-WBTC", BASE, "USDC", BASE, "WBTC", "dex", "aerodrome", 1 / 65000.0, 5, 5_000_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-WBTC-cbBTC", BASE, "WBTC", BASE, "cbBTC", "dex", "aerodrome", 1.0, 1, 300, "stable", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-cbBTC-WBTC", BASE, "cbBTC", BASE, "WBTC", "dex", "aerodrome", 1.0, 1, 300, "stable", 0.10, 3, 0.08))
    # Base LSTs: wstETH<->WETH and cbETH<->WETH.
    g.add_edge(_e("aero-base-wstETH-WETH", BASE, "wstETH", BASE, "WETH", "dex", "aerodrome", 3450 / 3000, 5, 8_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-WETH-wstETH", BASE, "WETH", BASE, "wstETH", "dex", "aerodrome", 3000 / 3450, 5, 9_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-cbETH-WETH", BASE, "cbETH", BASE, "WETH", "dex", "aerodrome", 3050 / 3000, 5, 20_000, "cpmm", 0.10, 3, 0.08))
    g.add_edge(_e("aero-base-WETH-cbETH", BASE, "WETH", BASE, "cbETH", "dex", "aerodrome", 3000 / 3050, 5, 20_000, "cpmm", 0.10, 3, 0.08))

    # --- Bridges (each stable; Across fast, Stargate medium, native slow/cheap) ---
    bridges = [
        ("across", 6, 120, 0.10, "fixed_variable"),
        ("stargate", 8, 300, 0.20, "fixed_variable"),
        ("native-bridge", 2, 604800, 0.35, "fixed_variable"),
    ]
    for venue, fee, eta, risk, model in bridges:
        for sym in ("USDC", "USDT", "DAI"):
            g.add_edge(_e(f"{venue}-eth-base-{sym}", ETH, sym, BASE, sym, "bridge", venue, 1.0, fee, 0, model, 1.50 if venue != "native-bridge" else 0.50, eta, risk))
            # Return direction (higher latency, same fee) for spread realism.
            g.add_edge(_e(f"{venue}-base-eth-{sym}", BASE, sym, ETH, sym, "bridge", venue, 1.0, fee + 1, 0, model, 1.50, eta * 1.2, min(1.0, risk + 0.05)))
    # WETH + WBTC bridges (Across/Stargate only).
    for venue, fee, eta, risk, model in bridges[:2]:
        g.add_edge(_e(f"{venue}-eth-base-WETH", ETH, "WETH", BASE, "WETH", "bridge", venue, 1.0, fee, 0, model, 2.0, eta, risk))
        g.add_edge(_e(f"{venue}-eth-base-WBTC", ETH, "WBTC", BASE, "WBTC", "bridge", venue, 1.0, fee + 4, 0, model, 2.0, eta, risk))
    # New-asset bridges (Across/Stargate, both directions with spread).
    for venue, fee, eta, risk, model in bridges[:2]:
        for sym, extra in (("cbBTC", 4), ("wstETH", 2), ("cbETH", 2)):
            g.add_edge(_e(f"{venue}-eth-base-{sym}", ETH, sym, BASE, sym, "bridge", venue, 1.0, fee + extra, 0, model, 2.0, eta, risk))
            g.add_edge(_e(f"{venue}-base-eth-{sym}", BASE, sym, ETH, sym, "bridge", venue, 1.0, fee + extra + 1, 0, model, 2.0, eta * 1.2, min(1.0, risk + 0.05)))

    # --- Table-driven pairs + bridges (batch 2+; spot rates from ASSET_PRICES) ---
    for prefix, chain, a, b, venue, fee_bps, liq_a, liq_b, model in DEX_PAIRS:
        gas, eta, risk = _DEX_DEFAULTS[chain]
        tag = _CHAIN_NAME[chain]
        g.add_edge(_e(f"{prefix}-{tag}-{a}-{b}", chain, a, chain, b, "dex", venue, ASSET_PRICES[a] / ASSET_PRICES[b], fee_bps, liq_a, model, gas, eta, risk))
        g.add_edge(_e(f"{prefix}-{tag}-{b}-{a}", chain, b, chain, a, "dex", venue, ASSET_PRICES[b] / ASSET_PRICES[a], fee_bps, liq_b, model, gas, eta, risk))
    _venue_params = {v: (fee, eta, risk) for v, fee, eta, risk, _ in bridges}
    for venue, syms in NEW_BRIDGES.items():
        fee, eta, risk = _venue_params[venue]
        for sym, extra in syms.items():
            g.add_edge(_e(f"{venue}-eth-base-{sym}", ETH, sym, BASE, sym, "bridge", venue, 1.0, fee + extra, 0, "fixed_variable", 2.0, eta, risk))
            g.add_edge(_e(f"{venue}-base-eth-{sym}", BASE, sym, ETH, sym, "bridge", venue, 1.0, fee + extra + 1, 0, "fixed_variable", 2.0, eta * 1.2, min(1.0, risk + 0.05)))
    return g, dict(PRICES_V1)
