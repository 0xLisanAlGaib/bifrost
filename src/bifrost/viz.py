"""Viz exporter (pure): graph -> JSON/mermaid for the Streamlit+Pyvis dashboard.

No Streamlit import here. Amount-dependent weights are evaluated at the routed
amount via `quote_edge` — never static spot labels.
"""
from __future__ import annotations

from .api import QuoteResponse
from .graph import DirectedEdge, Graph
from .weight import quote_edge

NATIVE_BRIDGE_VENUE = "native-bridge"


def _sanitize(nid: str) -> str:
    return "C" + nid.replace(":", "_")


def filter_edges(
    edges: list[DirectedEdge],
    kinds: set[str] | None = None,
    venues: set[str] | None = None,
    hide_native_bridge: bool = True,
) -> list[DirectedEdge]:
    out: list[DirectedEdge] = []
    for e in edges:
        if hide_native_bridge and e.venue == NATIVE_BRIDGE_VENUE:
            continue
        if kinds is not None and e.kind not in kinds:
            continue
        if venues is not None and e.venue not in venues:
            continue
        out.append(e)
    return out


def graph_to_vis(
    graph: Graph, prices: dict[str, float], amount: float
) -> tuple[list[dict], list[dict]]:
    """Return (nodes, edges) JSON-serializable dicts for Pyvis."""
    nodes = [
        {"id": n.id, "label": f"{n.symbol}\n{n.chain_id}", "chain": n.chain_id, "symbol": n.symbol}
        for n in sorted(graph.nodes(), key=lambda n: n.id)
    ]
    edges: list[dict] = []
    for e in graph.edges():
        price_out = prices.get(e.to_node.id, 0.0)
        out = quote_edge(e, amount, price_out) if amount > 0 else 0.0
        eff = (out / amount) if amount > 0 else e.spot_rate * (1.0 - e.fee_bps / 10_000.0)
        edges.append(
            {
                "id": e.id,
                "from": e.from_node.id,
                "to": e.to_node.id,
                "venue": e.venue,
                "kind": e.kind,
                "fee_bps": e.fee_bps,
                "liquidity": e.liquidity,
                "gas_usd": e.gas_usd,
                "eta_sec": e.latency_sec,
                "risk": e.risk_score,
                "stale": e.stale,
                "effective_rate": eff,
                "title": (
                    f"{e.id}<br>venue={e.venue} kind={e.kind}<br>"
                    f"fee={e.fee_bps}bps liq={e.liquidity:g}<br>"
                    f"gas=${e.gas_usd:g} eta={e.latency_sec:g}s risk={e.risk_score:g}"
                ),
            }
        )
    return nodes, edges


def quote_to_vis(
    response: QuoteResponse, graph: Graph, prices: dict[str, float], amount_in: float
) -> dict:
    """Expand each route into per-hop in/out amounts (forward simulation)."""
    routes: list[dict] = []
    for r in response.routes:
        hops: list[dict] = []
        amt = amount_in
        for leg_id in r.legs:
            e = graph.get_edge(leg_id)
            if e is None:
                hops.append({"edge": leg_id, "in": amt, "out": 0.0})
                amt = 0.0
                continue
            nxt = quote_edge(e, amt, prices.get(e.to_node.id, 0.0))
            hops.append(
                {
                    "edge": e.id,
                    "venue": e.venue,
                    "kind": e.kind,
                    "from": e.from_node.id,
                    "to": e.to_node.id,
                    "in": amt,
                    "out": nxt,
                }
            )
            amt = nxt
        routes.append(
            {
                "legs": list(r.legs),
                "venues": list(r.venues),
                "nodes": list(r.nodes),
                "hops": hops,
                "expected_out": r.expected_out,
                "min_out": r.min_out,
                "gas_usd": r.gas_usd,
                "eta_sec": r.eta_sec,
                "risk": r.risk,
                "impact_bps": r.impact_bps,
                "score": r.score,
            }
        )
    return {"routes": routes, "split": list(response.split_allocations)}


def graph_to_mermaid(graph: Graph, highlight_ids: frozenset[str] | set[str] = frozenset()) -> str:
    """Minimal flowchart for docs. Highlighted edges get orange linkStyle."""
    lines = ["flowchart LR"]
    for n in sorted(graph.nodes(), key=lambda n: n.id):
        lines.append(f'    {_sanitize(n.id)}["{n.id}"]')
    link_idx: list[int] = []
    for idx, e in enumerate(graph.edges()):
        lines.append(f"    {_sanitize(e.from_node.id)} -->|{e.venue}| {_sanitize(e.to_node.id)}")
        if e.id in highlight_ids:
            link_idx.append(idx)
    for i in link_idx:
        lines.append(f"    linkStyle {i} stroke:orange,stroke-width:4px")
    return "\n".join(lines)
