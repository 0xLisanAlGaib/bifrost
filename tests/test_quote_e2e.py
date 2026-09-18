"""End-to-end quote tests on the v1 mock graph (offline)."""
from bifrost.adapters.registry import build_v1_mock_graph
from bifrost.api import quote
from bifrost.graph import Node
from bifrost.toggles import Preference


def test_quote_schema_and_split_guarantee():
    g, prices = build_v1_mock_graph()
    for size in (100.0, 10_000.0, 1_000_000.0):
        resp = quote(g, prices, Node(1, "USDC"), Node(8453, "USDC"), size, Preference.MAX_OUTPUT)
        assert resp.routes, f"no routes for size {size}"
        r = resp.routes[0]
        assert r.expected_out > 0 and r.min_out <= r.expected_out
        assert r.gas_usd >= 0 and r.eta_sec > 0
        assert 0.0 <= r.risk <= 1.0 and r.impact_bps >= 0
        assert resp.split_expected_out >= r.expected_out - 1e-9


def test_fastest_prefers_low_eta_bridge():
    g, prices = build_v1_mock_graph()
    resp = quote(g, prices, Node(1, "USDC"), Node(8453, "USDC"), 10_000.0, Preference.FASTEST)
    assert resp.routes
    assert all(r.eta_sec <= 300 for r in resp.routes)
    assert "across" in resp.routes[0].venues  # fastest bridge wins despite fee


def test_cross_asset_eth_usdc_to_base_weth():
    g, prices = build_v1_mock_graph()
    resp = quote(g, prices, Node(1, "USDC"), Node(8453, "WETH"), 10_000.0, Preference.MAX_OUTPUT)
    assert resp.routes
    assert resp.routes[0].nodes[-1] == "8453:WETH"
    assert len(resp.routes[0].legs) >= 2  # at least bridge + swap


def test_new_assets_routable():
    g, prices = build_v1_mock_graph()
    # cbBTC cross-chain via new bridge edges.
    resp = quote(g, prices, Node(1, "cbBTC"), Node(8453, "cbBTC"), 1.0, Preference.MAX_OUTPUT)
    assert resp.routes and resp.routes[0].expected_out > 0
    # LST swap on Eth (WETH -> wstETH) and Base WBTC tradable (previously isolated).
    r2 = quote(g, prices, Node(1, "WETH"), Node(1, "wstETH"), 10.0, Preference.MAX_OUTPUT)
    assert r2.routes and r2.routes[0].expected_out > 0
    r3 = quote(g, prices, Node(8453, "WBTC"), Node(8453, "USDC"), 0.5, Preference.MAX_OUTPUT)
    assert r3.routes and r3.routes[0].expected_out > 0


def test_eval_table(capsys):
    # Manual-review helper: prints direct vs split across sizes. Always passes.
    g, prices = build_v1_mock_graph()
    for size in (100.0, 10_000.0, 1_000_000.0):
        resp = quote(g, prices, Node(1, "USDC"), Node(8453, "USDC"), size, Preference.MAX_OUTPUT)
        print(f"size={size:>10.0f} best={resp.routes[0].expected_out:>12.2f} split={resp.split_expected_out:>12.2f} via={resp.routes[0].venues}")
    out = capsys.readouterr().out
    assert "size=" in out
