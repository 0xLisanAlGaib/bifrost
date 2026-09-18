"""Deterministic mock quoter for tests and offline eval."""
from __future__ import annotations

from ..graph import DirectedEdge
from .base import BaseQuoter


class MockQuoter(BaseQuoter):
    def __init__(self, venue: str, kind: str, edges: list[DirectedEdge]) -> None:
        self.venue = venue
        self.kind = kind
        self._edges = edges

    def fetch_edges(self) -> list[DirectedEdge]:
        return list(self._edges)
