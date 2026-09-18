"""Aerodrome quoter (Base). Same offline-degradation pattern as Uniswap."""
from __future__ import annotations

import os

from ..graph import DirectedEdge
from .base import BaseQuoter
from .registry import build_v1_mock_graph


class AerodromeQuoter(BaseQuoter):
    venue = "aerodrome"
    kind = "dex"

    def __init__(self, rpc_url: str | None = None) -> None:
        self.rpc_url = rpc_url or os.getenv("BASE_RPC_URL")

    def fetch_edges(self) -> list[DirectedEdge]:
        g, _ = build_v1_mock_graph()
        edges = [e for e in g.edges() if e.venue == "aerodrome"]
        if not self.rpc_url:
            for e in edges:
                e.stale = True
        # TODO(live): read volatile/stable pool reserves.
        return edges
