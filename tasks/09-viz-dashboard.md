# 09 — Pyvis + Streamlit Explorer (route + legs)

## Goal
Interactive local dashboard to visualize the v1 directed multigraph and
per-quote routing decisions. Stack locked: **Streamlit + Pyvis**. Depth locked:
**route + legs only** (no Dijkstra debug trace).

## Inputs
- `src/bifrost/graph.py` (`Graph`, `DirectedEdge`, `Node`)
- `src/bifrost/weight.py` (`quote_edge`)
- `src/bifrost/api.py` (`quote() -> QuoteResponse`)
- `src/bifrost/adapters/registry.py` (`build_v1_mock_graph()`)

## Outputs
- `src/bifrost/viz.py` (pure, NO streamlit import):
  - `graph_to_vis(graph, prices, amount) -> (nodes, edges)` — edge dicts carry
    effective rate at routed amount (amount-dependent weights; never static spot).
  - `quote_to_vis(response, graph, prices, amount_in)` — per-route per-hop
    propagated amounts for leg-by-leg display.
  - `graph_to_mermaid(graph, highlight_ids) -> str` — docs paste-up.
  - `filter_edges(edges, kinds, venues, hide_native_bridge=True)`.
- `dashboard/app.py` (Streamlit + Pyvis only): sidebar controls
  (source/dest/amount/preference/venue+kind filters) -> `quote()` -> canvas +
  top-3 route cards + split bar. Fully offline.
- `tests/test_viz.py`: exporter only (filters, highlight set, per-hop sums).
- `pyproject.toml`: `[viz]` extra (`streamlit`, `pyvis`). Core stays dep-free.

## Acceptance
- `.venv/bin/pytest tests/test_viz.py` passes; full `pytest` green; `ruff` clean.
- `streamlit run dashboard/app.py` renders 12 v1 nodes offline;
  `1:USDC -> 8453:USDC, 10k, Fastest` highlights Across, ETA <= 300s.
- Eval parity: split >= single on 100 / 10k / 1M sizes.
