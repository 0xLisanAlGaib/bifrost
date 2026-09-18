# 03 — Pathfinder (single best path)

## Goal
Modified Dijkstra maximizing output, propagating real amounts forward.

## Inputs
- `graph.py`, `weight.py`.

## Outputs
- `src/bifrost/pathfinder.py`: `find_best_path(graph, source, dest, amount_in, price_usd: dict, edge_filter=None) -> PathResult{path, edges, expected_out}`.
- Algorithm: max-heap on `best_out[node]`; relax via `quote_edge`; track predecessors; skip non-improving relaxations. `O(E log V)`. Optional `edge_filter(edge)->bool` for latency/risk pruning.
- `tests/test_pathfinder.py`: direct vs 2-hop wins, amount-dependent flip (small amount picks high-rate/low-depth edge, large amount picks deep edge), unreachable -> `None`, wrap edge 1:1 minus gas.

## Acceptance
- All pathfinder single-path tests pass.
- No use of static precomputed weights; proof: test with same graph, two amounts, different winners.
