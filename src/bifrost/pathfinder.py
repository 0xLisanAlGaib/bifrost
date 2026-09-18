"""Pathfinder: modified Dijkstra over amount-dependent weights + splits.

`quote_edge` is non-decreasing in x (FIFO property), so expanding the node
with the best output seen so far first yields the optimal single path, and
the first pop of the destination is optimal.
"""
from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field

from .graph import DirectedEdge, Graph, Node
from .weight import baseline_edge, quote_edge

EdgeFilter = Callable[[DirectedEdge], bool]


@dataclass
class PathResult:
    nodes: list[Node]
    edges: list[DirectedEdge]
    expected_out: float
    gas_usd: float = 0.0
    eta_sec: float = 0.0
    risk: float = 0.0  # max leg risk (conservative)

    @property
    def edge_ids(self) -> tuple[str, ...]:
        return tuple(e.id for e in self.edges)


@dataclass
class SplitAllocation:
    edges: list[DirectedEdge]
    amount_in: float
    expected_out: float


@dataclass
class SplitResult:
    allocations: list[SplitAllocation] = field(default_factory=list)
    expected_out: float = 0.0


def simulate_path(
    edges: list[DirectedEdge], amount_in: float, prices: dict[str, float]
) -> float:
    """Forward-propagate amount through an edge list."""
    amt = amount_in
    for e in edges:
        amt = quote_edge(e, amt, prices.get(e.to_node.id, 0.0))
        if amt <= 0:
            return 0.0
    return amt


def simulate_baseline(edges: list[DirectedEdge], amount_in: float) -> float:
    amt = amount_in
    for e in edges:
        amt = baseline_edge(e, amt)
    return amt


def _summarize(nodes: list[Node], edges: list[DirectedEdge], out: float) -> PathResult:
    return PathResult(
        nodes=nodes,
        edges=edges,
        expected_out=out,
        gas_usd=sum(e.gas_usd for e in edges),
        eta_sec=sum(e.latency_sec for e in edges),
        risk=max((e.risk_score for e in edges), default=0.0),
    )


def find_best_path(
    graph: Graph,
    source: Node,
    dest: Node,
    amount_in: float,
    prices: dict[str, float],
    edge_filter: EdgeFilter | None = None,
    forbidden_edge_ids: frozenset[str] | None = None,
) -> PathResult | None:
    if amount_in <= 0:
        return None
    forbidden = forbidden_edge_ids or frozenset()
    best: dict[Node, float] = {source: amount_in}
    prev: dict[Node, tuple[Node, DirectedEdge]] = {}
    heap: list[tuple[float, int, Node]] = [(-amount_in, 0, source)]
    counter = 0
    settled: set[Node] = set()

    while heap:
        neg_out, _, node = heapq.heappop(heap)
        out = -neg_out
        if node in settled:
            continue
        if out < best.get(node, 0.0) - 1e-12:
            continue
        settled.add(node)
        if node == dest:
            break
        for e in graph.edges_from(node):
            if e.id in forbidden:
                continue
            if edge_filter is not None and not edge_filter(e):
                continue
            nxt = quote_edge(e, out, prices.get(e.to_node.id, 0.0))
            if nxt <= best.get(e.to_node, 0.0) + 1e-12:
                continue
            best[e.to_node] = nxt
            prev[e.to_node] = (node, e)
            counter += 1
            heapq.heappush(heap, (-nxt, counter, e.to_node))

    if dest not in prev and source != dest:
        return None
    if source == dest:
        return _summarize([source], [], amount_in)

    # Reconstruct.
    nodes: list[Node] = [dest]
    edges: list[DirectedEdge] = []
    cur = dest
    while cur != source:
        p, e = prev[cur]
        edges.append(e)
        nodes.append(p)
        cur = p
    nodes.reverse()
    edges.reverse()
    return _summarize(nodes, edges, best[dest])


def find_k_paths(
    graph: Graph,
    source: Node,
    dest: Node,
    amount_in: float,
    prices: dict[str, float],
    k: int = 3,
    edge_filter: EdgeFilter | None = None,
) -> list[PathResult]:
    """Yen-style: forbid each edge of the best path in turn, re-search, dedupe."""
    best = find_best_path(graph, source, dest, amount_in, prices, edge_filter)
    if best is None:
        return []
    paths = [best]
    seen = {best.edge_ids}
    candidates: list[PathResult] = []
    for e in best.edges:
        alt = find_best_path(
            graph, source, dest, amount_in, prices, edge_filter, frozenset({e.id})
        )
        if alt is not None and alt.edge_ids not in seen:
            seen.add(alt.edge_ids)
            candidates.append(alt)
    candidates.sort(key=lambda p: p.expected_out, reverse=True)
    paths.extend(candidates[: max(0, k - 1)])
    return paths


def _count_bridge_legs(edges: list[DirectedEdge]) -> int:
    return sum(1 for e in edges if e.kind == "bridge")


def find_split(
    graph: Graph,
    source: Node,
    dest: Node,
    amount_in: float,
    prices: dict[str, float],
    k: int = 3,
    chunk_frac: float = 0.05,
    max_bridge_legs: int = 2,
    edge_filter: EdgeFilter | None = None,
) -> SplitResult:
    """Greedy marginal-gain splitter over top-k paths.

    Splits source-side DEX liquidity while capping bridge fan-out (each extra
    bridge leg adds fixed fee + tx). Allocates `chunk_frac` slices to the path
    with the best incremental output until the full amount is placed.
    """
    if amount_in <= 0:
        return SplitResult()
    paths = find_k_paths(graph, source, dest, amount_in, prices, k, edge_filter)
    paths = [p for p in paths if _count_bridge_legs(p.edges) <= max_bridge_legs]
    if not paths:
        single = find_best_path(graph, source, dest, amount_in, prices, edge_filter)
        if single is None:
            return SplitResult()
        paths = [single]

    n_chunks = max(1, round(1.0 / chunk_frac))
    chunk = amount_in / n_chunks
    allocs = [0.0] * len(paths)
    # Incremental simulation: out(path, a) each time (paths are short; k<=3).
    for _ in range(n_chunks):
        best_gain = -1.0
        best_i = -1
        for i, p in enumerate(paths):
            cur_out = simulate_path(p.edges, allocs[i], prices) if allocs[i] > 0 else 0.0
            new_out = simulate_path(p.edges, allocs[i] + chunk, prices)
            gain = new_out - cur_out
            if gain > best_gain:
                best_gain = gain
                best_i = i
        if best_i < 0 or best_gain <= 0:
            break
        allocs[best_i] += chunk

    result = SplitResult()
    for p, a in zip(paths, allocs):
        if a <= 0:
            continue
        out = simulate_path(p.edges, a, prices)
        result.allocations.append(SplitAllocation(list(p.edges), a, out))
        result.expected_out += out
    return result
