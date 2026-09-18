"""UniswapV3 quoter (Eth + Base).

Live refresh (TODO behind RPC_URL): read pool slot0 + liquidity per fee tier,
derive spot_rate + depth, return DirectedEdges. Offline: returns representative
static edges with stale=True so routing still works.
"""
from __future__ import annotations

import os

from ..graph import DirectedEdge
from .base import BaseQuoter
from .registry import build_v1_mock_graph


class UniswapQuoter(BaseQuoter):
    venue = "uniswapv3-5bps"
    kind = "dex"

    def __init__(self, chain_id: int, rpc_url: str | None = None) -> None:
        self.chain_id = chain_id
        self.rpc_url = rpc_url or os.getenv("RPC_URL")

    def fetch_edges(self) -> list[DirectedEdge]:
        g, _ = build_v1_mock_graph()
        edges = [e for e in g.edges() if e.venue == "uniswapv3-5bps" and e.from_node.chain_id == self.chain_id]
        if not self.rpc_url:
            for e in edges:
                e.stale = True  # last-known params, not freshly quoted
        # TODO(live): eth_call slot0/liquidity per pool, recompute spot_rate/liquidity.
        return edges
