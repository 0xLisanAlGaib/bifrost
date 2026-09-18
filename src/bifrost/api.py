"""Framework-free quote API: top-3 routes with full breakdown."""
from __future__ import annotations

from dataclasses import dataclass

from .graph import Graph, Node
from .pathfinder import PathResult, find_k_paths, find_split, simulate_baseline
from .toggles import Preference, passes_filter, score_route


@dataclass
class Route:
    legs: list[str]  # edge ids
    venues: list[str]
    nodes: list[str]
    expected_out: float
    min_out: float
    gas_usd: float
    eta_sec: float
    risk: float
    impact_bps: float
    score: float


@dataclass
class QuoteResponse:
    routes: list[Route]
    split_expected_out: float
    split_allocations: list[dict]


def _to_route(p: PathResult, prices: dict[str, float], amount_in: float, pref: Preference, slippage_tol: float = 0.005) -> Route:
    out_usd = p.expected_out * prices.get(p.nodes[-1].id, 0.0)
    baseline = simulate_baseline(p.edges, amount_in)
    impact = ((baseline - p.expected_out) / baseline * 10_000) if baseline > 0 else 0.0
    return Route(
        legs=list(p.edge_ids),
        venues=[e.venue for e in p.edges],
        nodes=[n.id for n in p.nodes],
        expected_out=p.expected_out,
        min_out=p.expected_out * (1 - slippage_tol),
        gas_usd=p.gas_usd,
        eta_sec=p.eta_sec,
        risk=p.risk,
        impact_bps=max(impact, 0.0),
        score=score_route(out_usd, p.gas_usd, p.eta_sec, p.risk, pref),
    )


def quote(
    graph: Graph,
    prices: dict[str, float],
    source: Node,
    dest: Node,
    amount_in: float,
    preference: Preference = Preference.MAX_OUTPUT,
    k: int = 3,
    slippage_tol: float = 0.005,
) -> QuoteResponse:
    paths = find_k_paths(graph, source, dest, amount_in, prices, k=k)
    routes = [_to_route(p, prices, amount_in, preference, slippage_tol) for p in paths]
    routes = [r for r in routes if passes_filter(r.eta_sec, preference)]
    routes.sort(key=lambda r: r.score, reverse=True)
    routes = routes[:3]

    split = find_split(graph, source, dest, amount_in, prices, k=k)
    allocs = [
        {"legs": [e.id for e in a.edges], "amount_in": a.amount_in, "expected_out": a.expected_out}
        for a in split.allocations
    ]
    return QuoteResponse(routes=routes, split_expected_out=split.expected_out, split_allocations=allocs)
