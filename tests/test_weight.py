"""Weight engine tests: slippage, spread asymmetry, gas, guards."""
from bifrost.graph import DirectedEdge, Node
from bifrost.weight import quote_edge, slippage_factor


def _edge(**kw):
    base = {
        "id": "t", "from_node": Node(1, "A"), "to_node": Node(1, "B"),
        "kind": "dex", "venue": "test", "spot_rate": 1.0, "fee_bps": 0.0,
        "liquidity": 1_000_000.0, "model": "cpmm", "gas_usd": 0.0,
        "latency_sec": 0.0, "risk_score": 0.0,
    }
    base.update(kw)
    return DirectedEdge(**base)


def test_cpmm_slippage_grows_with_size():
    e = _edge()
    small = quote_edge(e, 1_000, 1.0)
    large = quote_edge(e, 500_000, 1.0)
    # Effective rate (out/in) must degrade with size.
    assert small / 1_000 > large / 500_000


def test_stable_less_impact_than_cpmm():
    cpmm = _edge(model="cpmm")
    stable = _edge(model="stable")
    x = 500_000
    assert quote_edge(stable, x, 1.0) > quote_edge(cpmm, x, 1.0)


def test_spread_asymmetry():
    fwd = _edge(id="fwd", fee_bps=10)
    rev = _edge(id="rev", fee_bps=30)
    assert quote_edge(fwd, 10_000, 1.0) != quote_edge(rev, 10_000, 1.0)


def test_gas_deduction_and_floor():
    e = _edge(gas_usd=5.0)
    assert quote_edge(e, 10_000, 1.0) == 10_000 * slippage_factor(10_000, 1_000_000, "cpmm") - 5.0
    dust = _edge(gas_usd=50.0)
    assert quote_edge(dust, 1.0, 1.0) == 0.0  # floored, never negative


def test_guards():
    e = _edge()
    assert quote_edge(e, 0, 1.0) == 0.0
    assert quote_edge(e, -5, 1.0) == 0.0
    assert slippage_factor(999_999, 0, "cpmm") == 1.0
