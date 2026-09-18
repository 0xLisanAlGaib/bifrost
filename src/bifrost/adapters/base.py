"""Adapter interface: every venue quoter yields DirectedEdges."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..graph import DirectedEdge


class BaseQuoter(ABC):
    venue: str = "base"
    kind: str = "dex"  # 'dex' | 'bridge' | 'wrap'

    @abstractmethod
    def fetch_edges(self) -> list[DirectedEdge]:
        """Return a fresh snapshot of directed edges. May set edge.stale=True."""
        raise NotImplementedError
