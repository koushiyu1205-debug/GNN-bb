"""Current-node RMP column view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import ColumnSemanticSignature


@dataclass
class MasterColumnView:
    signatures_by_node: dict[str, set[ColumnSemanticSignature]] = field(default_factory=dict)

    def contains_signature(self, sig: ColumnSemanticSignature, node_id: object = "root") -> bool:
        return sig in self.signatures_by_node.get(str(node_id), set())

    def add_from_pool(
        self,
        column: BpcColumn,
        node_context: Any = None,
        *,
        node_id: object = "root",
        pool: ColumnPool | None = None,
    ) -> bool:
        if pool is not None and not pool.contains_signature(column.signature):
            raise ValueError("column is not present in the supplied ColumnPool")
        key = str(node_id)
        signatures = self.signatures_by_node.setdefault(key, set())
        if column.signature in signatures:
            return False
        signatures.add(column.signature)
        return True

