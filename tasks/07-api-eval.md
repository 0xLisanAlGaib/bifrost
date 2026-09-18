# 07 — API /quote + eval harness

## Goal
Serve top-3 routes + prove split >= direct.

## Outputs
- `src/bifrost/api.py`: `quote(graph, prices, source, dest, amount, preference) -> QuoteResponse{routes: [Route{legs, venues, expected_out, min_out, gas_usd, eta_sec, risk, impact_bps}]}`. `min_out = expected*(1-slippage_tol)`, `impact_bps` vs infinite-liquidity baseline.
- `tests/test_quote_e2e.py`: end-to-end on `build_v1_mock_graph()` across sizes `[100, 10_000, 1_000_000]` USD-notional; asserts split>=single, response schema valid, Fastest eta ordering.
- Future (FastAPI wiring) out of scope for core lib; `api.py` stays framework-free.

## Acceptance
- `pytest tests/test_quote_e2e.py` passes offline.
- Eval prints comparison table (direct vs split) for manual review.
