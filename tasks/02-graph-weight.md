# 02 — Graph + Weight engine

## Goal
Implement amount-dependent edge cost functions. No RPC.

## Inputs
- `architecture.mmd` Core/Weight Engine box.

## Outputs
- `src/bifrost/graph.py`: `Node(chain_id, symbol)`, `NodeId = "chain:symbol"`, `DirectedEdge{id, from, to, kind, venue, spot_rate, fee_bps, liquidity, model, gas_usd, latency_sec, risk_score}`, `Graph` (adjacency list, `edges_from(node)`).
- `src/bifrost/weight.py`:
  ```python
  def slippage_factor(x, liquidity, model) -> float
  def quote_edge(edge, x_in, price_out_usd) -> float
  ```
  Models: `cpmm -> 1/(1+x/reserve)`, `stable -> max(0, 1 - k*x)`, `fixed_variable -> max(0, 1 - var_fee) minus fixed fee in gas_usd`, `one_to_one -> 1.0` (wrap/unwrap).
  Formula: `y = x * spot * (1-fee) * slippage(x) - gas_usd/price_out_usd`, floored at 0.
- `tests/test_weight.py`: small vs large slippage, fee symmetry `A->B != B->A`, gas deduction, zero/negative guard.

## Acceptance
- All `test_weight.py` pass.
- `quote_edge` is pure/deterministic (no network, no time).
