"""Curve stable quoter (Eth; Base if deployed)."""
from __future__ import annotations

import os

from ..graph import DirectedEdge
from .base import BaseQuoter
from .registry import build_v1_mock_graph


class CurveQuoter(BaseQuoter):
    venue = "curve-stable"
    kind = "dex"

    def __init__(self, chain_id: int = 1, rpc_url: str | None = None) -> None:
        self.chain_id = chain_id
        self.rpc_url = rpc_url or os.getenv("RPC_URL")

    def fetch_edges(self) -> list[DirectedEdge]:
        g, _ = build_v1_mock_graph()
        edges = [e for e in g.edges() if e.venue == "curve-stable" and e.from_node.chain_id == self.chain_id]
        if not self.rpc_url:
            for e in edges:
                e.stale = True
        # TODO(live): call get_dy per stable pair.
        return edges
