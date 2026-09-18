"""Bifrost explorer: Streamlit + Pyvis over the v1 mock graph.

Run:  pip install -e ".[viz]" && streamlit run dashboard/app.py
Fully offline (mock graph, no RPC).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from bifrost.adapters.registry import build_v1_mock_graph
from bifrost.api import quote
from bifrost.graph import Graph, parse_node_id
from bifrost.toggles import Preference
from bifrost.viz import filter_edges, graph_to_mermaid, graph_to_vis, quote_to_vis

CHAIN_NAMES = {1: "Ethereum", 8453: "Base"}
CHAIN_COLORS = {1: "#4C8DFF", 8453: "#2ECC71"}
KIND_COLORS = {"dex": "#95A5A6", "bridge": "#E67E22", "wrap": "#9B59B6"}


def _chain_label(chain_id: int) -> str:
    name = CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")
    return f"{name} ({chain_id})"


def _default_index(options: list, preferred, fallback: int = 0) -> int:
    try:
        return options.index(preferred)
    except ValueError:
        return min(fallback, len(options) - 1) if options else 0


def _humanize_eta(sec: float) -> str:
    if sec < 60:
        return f"{sec:.0f}s"
    if sec < 3600:
        return f"{sec / 60:.1f}min"
    if sec < 86400:
        return f"{sec / 3600:.1f}h"
    return f"{sec / 86400:.1f}d"


@st.cache_data
def _load():
    g, prices = build_v1_mock_graph()
    node_ids = sorted(n.id for n in g.nodes())
    venues = sorted({e.venue for e in g.edges()})
    chains = sorted({n.chain_id for n in g.nodes()})
    assets_by_chain = {
        c: sorted(n.symbol for n in g.nodes() if n.chain_id == c) for c in chains
    }
    return g, prices, node_ids, venues, chains, assets_by_chain


def _build_pyvis_html(
    vis_nodes: list[dict],
    vis_edges: list[dict],
    best_legs: set[str],
    other_legs: set[str],
) -> str:
    net = Network(height="600px", width="100%", directed=True)
    net.toggle_physics(True)
    for n in vis_nodes:
        net.add_node(
            n["id"],
            label=n["label"],
            color=CHAIN_COLORS.get(n["chain"], "#7F8C8D"),
            title=f"{n['id']}",
        )
    for i, e in enumerate(vis_edges):
        if e["id"] in best_legs:
            color, width = "#E74C3C", 5
        elif e["id"] in other_legs:
            color, width = "#F39C12", 2
        else:
            color, width = KIND_COLORS.get(e["kind"], "#BDC3C7"), 1
        net.add_edge(
            e["from"],
            e["to"],
            label=e["venue"],
            title=e["title"],
            color=color,
            width=width,
            arrows="to",
            smooth={"type": "curvedCW", "roundness": 0.15 * (i % 4)},
        )
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "graph.html")
        net.write_html(path, open_browser=False)
        return Path(path).read_text()


def main() -> None:
    st.set_page_config(page_title="Bifrost Explorer", layout="wide")
    st.title("Bifrost — route explorer (Eth + Base, v1 mock)")
    g, prices, _node_ids, venues, chains, assets_by_chain = _load()

    with st.sidebar:
        st.header("Quote")
        src_chain = st.selectbox(
            "Source chain", chains, index=_default_index(chains, 1), format_func=_chain_label
        )
        src_asset = st.selectbox(
            "Source asset",
            assets_by_chain[src_chain],
            index=_default_index(assets_by_chain[src_chain], "USDC"),
        )
        dst_chain = st.selectbox(
            "Destination chain",
            chains,
            index=_default_index(chains, 8453),
            format_func=_chain_label,
        )
        dst_asset = st.selectbox(
            "Destination asset",
            assets_by_chain[dst_chain],
            index=_default_index(assets_by_chain[dst_chain], "USDC"),
        )
        src_id = f"{src_chain}:{src_asset}"
        dst_id = f"{dst_chain}:{dst_asset}"
        st.caption(f"Routing **{src_id} → {dst_id}**")
        amount = st.number_input("Amount in", min_value=0.0, value=10_000.0, step=100.0)
        pref_label = st.radio("Preference", ["max_output", "fastest", "cheapest"], index=0)
        k = st.slider("k paths", 1, 5, 3)
        st.header("Filters")
        kinds = st.multiselect("Kinds", ["dex", "bridge", "wrap"], default=["dex", "bridge", "wrap"])
        sel_venues = st.multiselect("Venues", venues, default=venues)
        hide_native = st.checkbox("Hide native bridge (7d)", value=True)

    pref = Preference(pref_label)
    kept = filter_edges(
        g.edges(), kinds=set(kinds), venues=set(sel_venues), hide_native_bridge=hide_native
    )
    fg = Graph()
    for e in kept:
        fg.add_edge(e)
    # Keep isolated src/dst visible even with no out-edges.
    for nid in (src_id, dst_id):
        fg._adj.setdefault(parse_node_id(nid), [])

    src, dst = parse_node_id(src_id), parse_node_id(dst_id)
    resp = quote(fg, prices, src, dst, amount, pref, k=k)
    if not resp.routes:
        st.warning("No route found with current filters. Widen venues/kinds.")
        return
    qvis = quote_to_vis(resp, fg, prices, amount)
    best_legs = set(resp.routes[0].legs)
    other_legs = set().union(*[set(r.legs) for r in resp.routes[1:]]) if len(resp.routes) > 1 else set()

    vis_nodes, vis_edges = graph_to_vis(fg, prices, amount)
    html = _build_pyvis_html(vis_nodes, vis_edges, best_legs, other_legs)
    st.subheader("Graph (red = best route, orange = runner-ups)")
    components.html(html, height=650, scrolling=True)

    st.subheader(f"Top-{len(resp.routes)} routes ({pref_label})")
    for i, (r, vr) in enumerate(zip(resp.routes, qvis["routes"])):
        badge = "BEST" if i == 0 else f"#{i + 1}"
        with st.expander(f"{badge}: {' → '.join(r.nodes)}  |  out={r.expected_out:,.2f}", expanded=(i == 0)):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Expected out", f"{r.expected_out:,.2f}")
            c2.metric("Min out", f"{r.min_out:,.2f}")
            c3.metric("Gas USD", f"${r.gas_usd:,.2f}")
            c4.metric("ETA", _humanize_eta(r.eta_sec))
            c1.metric("Risk", f"{r.risk:.2f}")
            c2.metric("Impact", f"{r.impact_bps:.1f} bps")
            c3.metric("Score", f"{r.score:,.2f}")
            c4.metric("Venues", ", ".join(r.venues) if r.venues else "—")
            st.table(
                [
                    {
                        "leg": h["edge"],
                        "venue": h["venue"],
                        "hop": f"{h['from']} → {h['to']}",
                        "in": round(h["in"], 4),
                        "out": round(h["out"], 4),
                    }
                    for h in vr["hops"]
                ]
            )

    st.subheader("Split execution")
    st.write(f"Split expected out: **{resp.split_expected_out:,.2f}** (best single: {resp.routes[0].expected_out:,.2f})")
    if resp.split_allocations:
        total = sum(a["amount_in"] for a in resp.split_allocations) or 1.0
        st.table(
            [
                {
                    "legs": " + ".join(a["legs"]),
                    "amount_in": round(a["amount_in"], 2),
                    "share_%": round(100 * a["amount_in"] / total, 1),
                    "expected_out": round(a["expected_out"], 2),
                }
                for a in resp.split_allocations
            ]
        )

    with st.expander("Mermaid (paste into docs)"):
        st.code(graph_to_mermaid(fg, best_legs), language="mermaid")


if __name__ == "__main__":
    main()
