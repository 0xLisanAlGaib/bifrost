# 05 — Adapter interfaces + mocks

## Goal
Pluggable venue quoters behind one interface; deterministic mocks for tests/eval.

## Outputs
- `src/bifrost/adapters/base.py`: `BaseQuoter(venue, kind)`, `fetch_edges() -> list[DirectedEdge]`, `refresh(edge) -> DirectedEdge` (TTL hook, mocked v1).
- `src/bifrost/adapters/mock.py`: `MockQuoter(edges: list[DirectedEdge])` for fixtures.
- `src/bifrost/adapters/registry.py`: `build_v1_mock_graph() -> (Graph, prices)` with the 12 v1 nodes and representative edges (Uniswap/Aerodrome/Curve/Across/Stargate/native/wrap).
- Tests use only mocks (no network).

## Acceptance
- `build_v1_mock_graph()` returns graph with both chains, wrap edges, ≥1 bridge per stable.
- Pathfinder + toggles run end-to-end on mock graph.
