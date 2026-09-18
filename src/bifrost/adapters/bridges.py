"""Bridge quoters: Across (fast), Stargate (medium), native (slow/cheap).

Live: query each bridge's quote API (fee + ETA). Offline: static params.
"""
from __future__ import annotations

import os

from ..graph import DirectedEdge
from .base import BaseQuoter
from .registry import build_v1_mock_graph


class _BridgeQuoter(BaseQuoter):
    _venue = ""
    kind = "bridge"

    def fetch_edges(self) -> list[DirectedEdge]:
        g, _ = build_v1_mock_graph()
        edges = [e for e in g.edges() if e.venue == self._venue]
        if not os.getenv("BRIDGE_API"):
            for e in edges:
                e.stale = True
        # TODO(live): refresh fee_bps/gas_usd/latency_sec from bridge API.
        return edges


class AcrossQuoter(_BridgeQuoter):
    venue = "across"
    _venue = "across"


class StargateQuoter(_BridgeQuoter):
    venue = "stargate"
    _venue = "stargate"


class NativeBridgeQuoter(_BridgeQuoter):
    venue = "native-bridge"
    _venue = "native-bridge"
