# 06 — Live adapters (Eth + Base)

## Goal
Replace mock params with live RPC/API reads. Same `BaseQuoter` interface.

## Outputs
- `uniswap.py` (Eth+Base UniswapV3: pool `slot0` + liquidity -> spot + depth; fee tier per edge).
- `aerodrome.py` (Base: volatile/stable pools).
- `curve.py` (Eth stables; Base if deployed else skip).
- `across.py`, `stargate.py`, `native_bridge.py` (quote APIs -> spot≈1-fee, latency/risk presets: Across ~120s/low, Stargate ~300s/medium, native ~7d/high-latency but cheap).
- `oracles.py` (Chainlink/Pyth spot USD + gas oracle -> `gas_usd`, `prices` dict).
- Each adapter degrades to last-known + `stale=True` flag on RPC failure.

## Acceptance (deferred to live env)
- Each adapter has a `fetch_edges()` integration test marked `live` (skipped without `RPC_URL`).
- Stale-flag path unit-tested with mocked transport.
- v1 ships usable with mocks + 1 live adapter (Uniswap) if RPC is available.
