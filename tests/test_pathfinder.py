"""Pathfinder tests: optimality, amount-dependent flip, unreachable, wrap."""
from bifrost.adapters.registry import build_v1_mock_graph
from bifrost.graph import DirectedEdge, Graph, Node
from bifrost.pathfinder import find_best_path, find_k_paths, find_split
from bifrost.weight import quote_edge


def _tiny_graph() -> tuple[Graph, dict[str, float]]:
    g = Graph()
    a, b, c = Node(1, "A"), Node(1, "B"), Node(1, "C")
    prices = {"1:A": 1.0, "1:B": 1.0, "1:C": 1.0}
    # Direct weak edge.
    g.add_edge(DirectedEdge("direct", a, c, "dex", "weak", 0.90, 0, 10**9, "cpmm", 0, 0, 0))
    # Two-hop strong route.
    g.add_edge(DirectedEdge("ab", a, b, "dex", "good", 1.0, 0, 10**9, "cpmm", 0, 0, 0))
    g.add_edge(DirectedEdge("bc", b, c, "dex", "good", 1.0, 0, 10**9, "cpmm", 0, 0, 0))
    return g, prices


def test_two_hop_beats_direct():
    g, prices = _tiny_graph()
    r = find_best_path(g, Node(1, "A"), Node(1, "C"), 100.0, prices)
    assert r is not None
    assert r.edge_ids == ("ab", "bc")
    assert r.expected_out > 90.0


def test_amount_dependent_flip():
    # Same pair, two venues: high-rate shallow vs lower-rate deep.
    g = Graph()
    a, b = Node(1, "A"), Node(1, "B")
    prices = {"1:A": 1.0, "1:B": 1.0}
    g.add_edge(DirectedEdge("shallow", a, b, "dex", "hot", 1.00, 0, 10_000, "cpmm", 0, 0, 0))
    g.add_edge(DirectedEdge("deep", a, b, "dex", "deep", 0.99, 0, 100_000_000, "cpmm", 0, 0, 0))
    small = find_best_path(g, a, b, 100.0, prices)
    large = find_best_path(g, a, b, 5_000_000.0, prices)
    assert small is not None and large is not None
    assert small.edge_ids == ("shallow",)
    assert large.edge_ids == ("deep",)


def test_unreachable_returns_none():
    g, prices = _tiny_graph()
    assert find_best_path(g, Node(1, "C"), Node(1, "A"), 100.0, prices) is None


def test_wrap_edge_is_one_to_one_minus_gas():
    g, prices = build_v1_mock_graph()
    r = find_best_path(g, Node(1, "ETH"), Node(1, "WETH"), 10.0, prices)
    assert r is not None and r.edge_ids == ("wrap-1",)
    assert r.expected_out == 10.0 - 0.50 / prices["1:WETH"]


def test_k_paths_and_split_beats_single():
    g, prices = build_v1_mock_graph()
    src, dst = Node(1, "USDC"), Node(8453, "USDC")
    single = find_best_path(g, src, dst, 1_000_000.0, prices)
    assert single is not None
    paths = find_k_paths(g, src, dst, 1_000_000.0, prices, k=3)
    assert len(paths) >= 2  # Across vs Stargate vs native
    split = find_split(g, src, dst, 1_000_000.0, prices, k=3)
    assert split.expected_out >= single.expected_out - 1e-9


def test_quote_edge_monotone_fifo():
    g, _prices = build_v1_mock_graph()
    e = g.get_edge("uni-eth-WETH-USDC")
    assert e is not None
    assert quote_edge(e, 2000, 1.0) >= quote_edge(e, 1000, 1.0)
