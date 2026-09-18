"""Graph model: directed weighted multigraph.

Node = (chain_id, symbol). Edge weights are amount-dependent via
`weight.quote_edge`, so the graph stores quotable edges, not static scalars.
Reverse edges (spread) are stored explicitly with different params.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    chain_id: int
    symbol: str

    @property
    def id(self) -> str:
        return f"{self.chain_id}:{self.symbol}"

    def __str__(self) -> str:  # pragma: no cover
        return self.id


NodeId = str


def node_id(chain_id: int, symbol: str) -> NodeId:
    return f"{chain_id}:{symbol}"


def parse_node_id(nid: NodeId) -> Node:
    chain, _, symbol = nid.partition(":")
    return Node(chain_id=int(chain), symbol=symbol)


# Edge kinds. 'wrap' = ETH<->WETH 1:1. 'dex' | 'bridge' otherwise.
EdgeKind = str
# Slippage models: cpmm | stable | fixed_variable | one_to_one
SlippageModel = str


@dataclass
class DirectedEdge:
    id: str
    from_node: Node
    to_node: Node
    kind: EdgeKind  # 'dex' | 'bridge' | 'wrap'
    venue: str  # e.g. 'uniswapv3-5bps', 'across', 'native-bridge'
    spot_rate: float  # units of to-asset per 1 unit of from-asset (pre-fee, zero-impact)
    fee_bps: float = 0.0  # proportional fee (protocol + LP + bridge variable)
    liquidity: float = 0.0  # depth in from-asset units; <=0 means unknown -> no slippage est
    model: SlippageModel = "cpmm"
    gas_usd: float = 0.0  # fixed execution cost for this leg, in USD
    latency_sec: float = 0.0
    risk_score: float = 0.0  # 0.0 (safest) .. 1.0 (riskiest)
    stale: bool = False  # True if quoter failed to refresh (live degradation)

    def __post_init__(self) -> None:
        if self.spot_rate <= 0:
            raise ValueError("spot_rate must be > 0")
        if self.fee_bps < 0:
            raise ValueError("fee_bps must be >= 0")
        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError("risk_score must be in [0, 1]")


@dataclass
class Graph:
    """Adjacency-list directed multigraph. Parallel edges allowed."""

    _adj: dict[Node, list[DirectedEdge]] = field(default_factory=dict)

    def add_edge(self, edge: DirectedEdge) -> None:
        self._adj.setdefault(edge.from_node, []).append(edge)
        # Ensure destination node exists in map (even with no out-edges).
        self._adj.setdefault(edge.to_node, [])

    def add_bidirectional(
        self,
        id_fwd: str,
        id_rev: str,
        a: Node,
        b: Node,
        kind: EdgeKind,
        venue: str,
        spot_fwd: float,
        spot_rev: float,
        **kwargs,
    ) -> tuple[DirectedEdge, DirectedEdge]:
        fwd = DirectedEdge(id_fwd, a, b, kind, venue, spot_fwd, **kwargs)
        rev = DirectedEdge(id_rev, b, a, kind, venue, spot_rev, **kwargs)
        self.add_edge(fwd)
        self.add_edge(rev)
        return fwd, rev

    def nodes(self) -> list[Node]:
        return list(self._adj.keys())

    def edges(self) -> list[DirectedEdge]:
        out: list[DirectedEdge] = []
        for lst in self._adj.values():
            out.extend(lst)
        return out

    def edges_from(self, node: Node) -> list[DirectedEdge]:
        return list(self._adj.get(node, []))

    def get_edge(self, edge_id: str) -> DirectedEdge | None:
        for e in self.edges():
            if e.id == edge_id:
                return e
        return None

    def __len__(self) -> int:
        return len(self._adj)
