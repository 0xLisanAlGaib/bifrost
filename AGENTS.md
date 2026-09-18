# Bifrost — AGENTS.md

Bifrost is a cross-chain best-route router. Assets are nodes `(chain_id, symbol)`
in a directed weighted multigraph; swap routes and bridges are directed edges
(spread means `A->B != B->A`). v1 scope: Ethereum (1) + Base (8453), 17 assets,
direct non-custodial execution. See `architecture.mmd` and `tasks/00-overview.md`.

## Layout

- `src/bifrost/graph.py` — `Node`, `DirectedEdge`, `Graph` (adjacency list, parallel edges allowed)
- `src/bifrost/weight.py` — `quote_edge(e, x, price_out_usd)`; slippage models `cpmm | stable | fixed_variable | one_to_one`
- `src/bifrost/pathfinder.py` — max-output Dijkstra + Yen k-paths + greedy split allocator
- `src/bifrost/toggles.py` — `MAX_OUTPUT | FASTEST | CHEAPEST` scoring presets
- `src/bifrost/api.py` — framework-free `quote()` returning top-3 `Route`s + split
- `src/bifrost/viz.py` — pure exporter (graph/quote -> JSON + mermaid). **No Streamlit import here.**
- `src/bifrost/adapters/` — `base.py` (`BaseQuoter`), `mock.py`, `registry.py` (mock graph + USD prices, source of truth offline), per-venue live quoters, `oracles.py`
- `dashboard/app.py` — Streamlit + Pyvis explorer (UI only, consumes `viz.py` + `api.py`)
- `tests/` — offline unit/e2e tests; `tasks/` — one spec doc per build step; `docs/intent-model-B.md` — deferred v2 design, **doc-only, do not implement**

## Environment (important)

- Python >= 3.12. **Always use `.venv` binaries** — system pip is PEP 668 blocked:
  `./.venv/bin/pytest`, `./.venv/bin/ruff`, `./.venv/bin/streamlit`, `./.venv/bin/pip`
- Install: `./.venv/bin/pip install -e ".[dev]"` (+ `.[viz]` for `streamlit`, `pyvis`)
- Dashboard: `./.venv/bin/streamlit run dashboard/app.py` (first run may ask for an email — pre-write `~/.streamlit/credentials.toml` with `[general] email = ""`)

## Verify (in this order)

1. `./.venv/bin/ruff check src tests dashboard`
2. `./.venv/bin/pytest -q` (must stay fully offline; live-adapter tests are skipped without `RPC_URL`)

## Core invariants — do not break

- Edge weights are **amount-dependent** `w_e(x)`. Never precompute static weights or use networkx.
- `quote_edge` is non-decreasing in `x` (FIFO) — that is what makes the modified Dijkstra optimal. Keep it monotone; the `test_quote_edge_monotone_fifo` test guards this.
- Adapters behind `BaseQuoter.fetch_edges()`; live quoters must degrade to `stale=True` edges when RPC/API is missing.
- Mock graph changes go in `adapters/registry.py` (nodes, prices, venues together). To add an asset: `ASSET_PRICES` + one `DEX_PAIRS` row per liquid pair (+ `NEW_BRIDGES` entry only if a bridge supports it — bridgeless assets route via intermediates, guarded by `tests/test_connectivity.py`). Dashboard asset lists derive from the graph — no hardcoded asset lists in UI.
- `filter_edges(..., hide_native_bridge=True)` by default; the 7-day native bridge drowns layouts.
- For new skills, load the `skill-creator` skill (`.opencode/skills/skill-creator/SKILL.md`).
