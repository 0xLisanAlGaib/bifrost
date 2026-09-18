# 00 — Overview (v1 locked)

## Decisions
- Execution **A (direct, non-custodial)**. User signs each hop. `Execution Router` exposes a `DirectExecutor` interface kept forward-compatible with intents (see `docs/intent-model-B.md`).
- Chains: **Ethereum Mainnet (1) + Base (8453)** only.
- Assets v1: `ETH, WETH, USDC, USDT, WBTC, DAI, cbBTC, wstETH, cbETH, weETH, ezETH, rETH, LINK, AAVE, UNI, USDe, FRAX` (see `ASSET_PRICES` in `adapters/registry.py`). `ETH<->WETH` = wrap/unwrap edge (1:1, gas only). `HYPE` deferred to v2 + Model B (HyperEVM).
- Pathfinder: **Python**. Custom heap-based search (NOT networkx static weights) because edge weights are amount-dependent `w_e(x)`.
- Toggles: `MaxOutput | Fastest | Cheapest`, implemented as scalarized scoring in `toggles.py`.

## Graph model
- Node = `(chain_id, symbol)` e.g. `(1, USDC)`, `(8453, WETH)`. ~34 nodes v1.
- Directed edge `A->B` with `quote(x)` function: `spot_rate * (1-fee) * slippage(x) - gas`. Reverse edge `B->A` has different weight (spread).
- Multigraph: parallel edges per venue (UniswapV3, Aerodrome, Curve, Across, Stargate, native bridge).

## Venue matrix v1
- Eth: UniswapV3, Curve (stables), 1inch API fallback (optional).
- Base: UniswapV3, Aerodrome, Curve (if deployed, else mock).
- Bridges: Across (fast), Stargate, Base native bridge (slow/cheap baseline).

## Global acceptance
- `split-route output >= best single-path output` on eval sizes.
- Small sizes prefer low-gas/fast venues; large sizes prefer deep-liquidity venues (amount-dependent flip covered by tests).
- `POST /quote` returns top-3 routes with legs, expectedOut, minOut, gasUsd, etaSec, risk, impactBps.
