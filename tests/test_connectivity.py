"""Connectivity: every asset must resolve cross-chain, even bridgeless ones.

Bridgeless assets (rETH, AAVE, UNI — absent from NEW_BRIDGES) prove the core
thesis: with no direct bridge edge, the pathfinder must compose
swap -> bridge (intermediate) -> swap legs.
"""
from collections import deque

from bifrost.adapters.registry import NEW_BRIDGES, build_v1_mock_graph
from bifrost.api import quote
from bifrost.graph import Node
from bifrost.toggles import Preference

BRIDGELESS = ("rETH", "AAVE", "UNI")


def _reachable(g, source):
    seen = {source}
    dq = deque([source])
    while dq:
        node = dq.popleft()
        for e in g.edges_from(node):
            if e.to_node not in seen:
                seen.add(e.to_node)
                dq.append(e.to_node)
    return seen


def test_all_pairs_reachable():
    g, _ = build_v1_mock_graph()
    nodes = g.nodes()
    assert len(nodes) >= 30  # 17 assets x 2 chains
    for src in nodes:
        reached = _reachable(g, src)
        missing = [n.id for n in nodes if n not in reached]
        assert not missing, f"{src.id} cannot reach {missing}"


def test_bridgeless_assets_route_via_intermediates():
    g, prices = build_v1_mock_graph()
    for sym in BRIDGELESS:
        for venue, syms in NEW_BRIDGES.items():
            assert sym not in syms, f"{sym} unexpectedly bridged by {venue}"
        resp = quote(g, prices, Node(1, sym), Node(8453, sym), 100.0, Preference.MAX_OUTPUT)
        assert resp.routes, f"no route for bridgeless {sym}"
        legs = resp.routes[0].legs
        assert len(legs) >= 3, f"{sym} should need >=3 hops, got {legs}"
        for leg_id in legs:
            e = g.get_edge(leg_id)
            assert e is not None
            if e.kind == "bridge":
                # Bridge legs must carry an intermediate, never the asset itself.
                assert e.from_node.symbol != sym, f"{sym} rode a direct bridge: {leg_id}"
