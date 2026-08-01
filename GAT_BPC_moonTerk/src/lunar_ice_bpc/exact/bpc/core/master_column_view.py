"""Current-node RMP column view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from lunar_ice_bpc.exact.bpc.core.column_pool import (
    AddResult,
    BpcColumn,
    ColumnPool,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import ColumnSemanticSignature


@dataclass
class MasterColumnView:
    signatures_by_node: dict[str, set[ColumnSemanticSignature]] = field(default_factory=dict)

    def contains_signature(self, sig: ColumnSemanticSignature, node_id: object = "root") -> bool:
        return sig in self.signatures_by_node.get(str(node_id), set())

    def remove_signature(self, sig: ColumnSemanticSignature, node_id: object = "root") -> bool:
        signatures = self.signatures_by_node.get(str(node_id), set())
        if sig not in signatures:
            return False
        signatures.remove(sig)
        return True

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

    def add_many_from_pool(
        self,
        columns: tuple[BpcColumn, ...] | list[BpcColumn],
        *,
        node_id: object = "root",
        pool: ColumnPool,
    ) -> tuple[bool, ...]:
        """Atomically activate an ordered batch already present in ``pool``."""

        ordered_columns = tuple(columns)
        missing = [
            column.signature
            for column in ordered_columns
            if not pool.contains_signature(column.signature)
        ]
        if missing:
            raise ValueError(
                "one or more columns are not present in the supplied ColumnPool"
            )
        if not ordered_columns:
            return tuple()
        key = str(node_id)
        scratch = set(self.signatures_by_node.get(key, set()))
        decisions = []
        for column in ordered_columns:
            added = column.signature not in scratch
            decisions.append(added)
            if added:
                scratch.add(column.signature)
        self.signatures_by_node[key] = scratch
        return tuple(decisions)

    def admit_many_atomically(
        self,
        columns: tuple[BpcColumn, ...] | list[BpcColumn],
        *,
        node_contexts: tuple[Any, ...] | list[Any] | None = None,
        node_id: object = "root",
        pool: ColumnPool,
        activate: Callable[
            [ColumnPool, "MasterColumnView", BpcColumn, object], bool
        ]
        | None = None,
    ) -> tuple[tuple[AddResult, ...], tuple[bool, ...]]:
        """Apply ordered pool and node-view admission as one transaction.

        Each decision observes all earlier decisions in the batch, exactly as
        repeated scalar ``pool.add`` plus ``view.add_from_pool`` calls would.
        The live pool and view are committed only after the full batch
        succeeds.
        """

        ordered_columns = tuple(columns)
        contexts = (
            tuple({} for _column in ordered_columns)
            if node_contexts is None
            else tuple(node_contexts)
        )
        if len(contexts) != len(ordered_columns):
            raise ValueError("node_contexts must have one entry per column")
        scratch_pool = ColumnPool(dict(pool.columns_by_signature))
        scratch_view = MasterColumnView(
            {
                str(key): set(signatures)
                for key, signatures in self.signatures_by_node.items()
            }
        )
        add_results: list[AddResult] = []
        activation_results: list[bool] = []
        for column, raw_context in zip(
            ordered_columns, contexts, strict=True
        ):
            context = dict(
                raw_context if isinstance(raw_context, dict) else {}
            )
            context["master_view"] = scratch_view
            context["node_id"] = node_id
            add_results.append(scratch_pool.add(column, context))
            stored = scratch_pool.get(column.signature)
            if stored is None:
                activation_results.append(False)
                continue
            if activate is None:
                activated = scratch_view.add_from_pool(
                    stored,
                    node_id=node_id,
                    pool=scratch_pool,
                )
            else:
                activated = activate(
                    scratch_pool,
                    scratch_view,
                    stored,
                    node_id,
                )
            activation_results.append(bool(activated))
        pool.columns_by_signature = scratch_pool.columns_by_signature
        self.signatures_by_node = scratch_view.signatures_by_node
        return tuple(add_results), tuple(activation_results)
