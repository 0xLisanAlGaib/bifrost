"""Exporter-only tests (no Streamlit, no network)."""
from bifrost.adapters.registry import build_v1_mock_graph
from bifrost.api import quote
from bifrost.graph import Node
from bifrost.toggles import Preference
from bifrost.viz import filter_edges, graph_to_mermaid, graph_to_vis, quote_to_vis


def test_filter_hides_native_bridge_by_default():
    g, _ = build_v1_mock_graph()
    all_edges = g.edges()
    assert any(e.venue == "native-bridge" for e in all_edges)
    filtered = filter_edges(all_edges)
    assert all(e.venue != "native-bridge" for e in filtered)
    kept = filter_edges(all_edges, hide_native_bridge=False)
    assert len(kept) == len(all_edges)


def test_filter_by_kind_and_venue():
    g, _ = build_v1_mock_graph()
    dex_only = filter_edges(g.edges(), kinds={"dex"}, hide_native_bridge=False)
    assert dex_only and all(e.kind == "dex" for e in dex_only)
    across = filter_edges(g.edges(), venues={"across"})
    assert across and all(e.venue == "across" for e in across)


def test_effective_rate_reflects_slippage():
    g, prices = build_v1_mock_graph()
    _, small = graph_to_vis(g, prices, 100.0)
    _, large = graph_to_vis(g, prices, 5_000_000.0)
    by_id_small = {e["id"]: e for e in small}
    by_id_large = {e["id"]: e for e in large}
    # Deep cpmm edge degrades with size (slippage); fixed-fee bridge edge
    # amortizes gas so its effective rate rises slightly with size.
    assert by_id_large["uni-eth-WETH-USDC"]["effective_rate"] < by_id_small["uni-eth-WETH-USDC"]["effective_rate"]
    assert by_id_large["across-eth-base-USDC"]["effective_rate"] > by_id_small["across-eth-base-USDC"]["effective_rate"]


def test_quote_to_vis_hops_reconcile():
    g, prices = build_v1_mock_graph()
    resp = quote(g, prices, Node(1, "USDC"), Node(8453, "USDC"), 10_000.0, Preference.MAX_OUTPUT)
    vis = quote_to_vis(resp, g, prices, 10_000.0)
    assert len(vis["routes"]) == len(resp.routes)
    for vr, r in zip(vis["routes"], resp.routes):
        assert vr["hops"][0]["in"] == 10_000.0
        assert abs(vr["hops"][-1]["out"] - r.expected_out) < 1e-6
        assert abs(vr["expected_out"] - r.expected_out) < 1e-9


def test_mermaid_highlights_best_route():
    g, prices = build_v1_mock_graph()
    resp = quote(g, prices, Node(1, "USDC"), Node(8453, "USDC"), 10_000.0, Preference.MAX_OUTPUT)
    best = set(resp.routes[0].legs)
    mm = graph_to_mermaid(g, best)
    assert mm.startswith("flowchart LR")
    assert "linkStyle" in mm  # highlight applied
    plain = graph_to_mermaid(g)
    assert "linkStyle" not in plain
