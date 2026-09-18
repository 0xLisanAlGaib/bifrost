# 04 — Split routing + toggles

## Goal
Multi-path splits for whales + user-facing preference toggles.

## Inputs
- `pathfinder.py` single-path.

## Outputs
- `src/bifrost/pathfinder.py` (+): `find_k_paths(...)` (Yen-style: iteratively forbid one edge of best path, re-run, dedupe, k=3) and `find_split(graph, source, dest, amount, k=3, chunk_frac=0.05) -> SplitResult{allocations: [(edges, amount)], expected_out}` via greedy marginal-gain: allocate chunks to path with best incremental `dOut/dIn` until no gain.
- Constraint: max 2 bridge-kind edges per split leg (each split adds fixed bridge fee + tx); enforce in scoring.
- `src/bifrost/toggles.py`: `Preference = MaxOutput | Fastest | Cheapest`; `score_route(out_usd, gas_usd, eta_sec, risk) -> float` with preset weights; `filter_by_preference(routes, pref)` (e.g. Fastest drops `eta>300s`).
- Tests: split >= best single on deep+shallow pool pair; Fastest prefers Across-like edge over higher-output slow edge.

## Acceptance
- `split.expected_out >= best_single.expected_out - 1e-9` on all fixtures.
- Toggle test: same graph, different preference -> different winner.
