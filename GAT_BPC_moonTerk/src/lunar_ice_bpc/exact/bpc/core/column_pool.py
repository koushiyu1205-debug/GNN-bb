"""Column pool distinct from the current RMP column view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lunar_ice_bpc.exact.bpc.core.column_signature import ColumnSemanticSignature


@dataclass(frozen=True)
class BpcColumn:
    signature: ColumnSemanticSignature
    objective: float
    payload: Any = None


@dataclass(frozen=True)
class AddabilityReport:
    addable: bool
    reason: str
    signature: ColumnSemanticSignature
    is_new_signature: bool = True
    is_forbidden_signature: bool = False
    is_allowed_by_branch: bool = True
    is_allowed_by_cut_context: bool = True
    cut_coefficients: dict[str, float] = field(default_factory=dict)
    branch_signature: tuple[str, ...] = tuple()
    dominance_key: tuple = tuple()
    would_replace_existing: bool = False
    would_change_active_support: bool = True
    would_enter_master: bool = True
    reject_reason: str = ""
    current_master_contains_signature: bool = False
    pool_contains_signature: bool = False


@dataclass(frozen=True)
class AddResult:
    added: bool
    reason: str
    signature: ColumnSemanticSignature
    addability_report: AddabilityReport | None = None


@dataclass
class ColumnPool:
    columns_by_signature: dict[ColumnSemanticSignature, BpcColumn] = field(default_factory=dict)

    def contains_signature(self, sig: ColumnSemanticSignature) -> bool:
        return sig in self.columns_by_signature

    def addability_check(self, column: BpcColumn, node_context: Any = None) -> AddabilityReport:
        context = node_context if isinstance(node_context, dict) else {}
        signature = column.signature
        pool_contains = self.contains_signature(signature)
        master_view = context.get("master_view")
        node_id = context.get("node_id", "root")
        current_master_contains = bool(
            master_view is not None
            and hasattr(master_view, "contains_signature")
            and master_view.contains_signature(signature, node_id=node_id)
        )
        forbidden = signature in set(context.get("forbidden_signatures") or set())
        branch_allowed = bool(context.get("is_allowed_by_branch", True))
        cut_allowed = bool(context.get("is_allowed_by_cut_context", True))
        cut_coefficients = {
            str(key): float(value)
            for key, value in (context.get("cut_coefficients") or {}).items()
        }
        branch_signature = tuple(str(item) for item in (context.get("branch_signature") or tuple()))
        dominance_key = tuple(context.get("dominance_key") or tuple(signature.task_set))
        active_task_sets = {
            frozenset(str(task_id) for task_id in row)
            for row in (context.get("active_task_sets") or set())
        }
        task_set = frozenset(signature.task_set)
        would_change_active_support = bool(task_set not in active_task_sets)
        if forbidden:
            reject_reason = "forbidden_signature"
        elif not branch_allowed:
            reject_reason = "branch_infeasible"
        elif not cut_allowed:
            reject_reason = "cut_infeasible"
        elif current_master_contains:
            reject_reason = "duplicate_in_current_master"
        else:
            reject_reason = ""
        would_enter_master = not bool(reject_reason)
        if reject_reason:
            reason = reject_reason
        elif pool_contains:
            reason = "in_pool_not_master"
        else:
            reason = "addable_to_pool_and_master"
        return AddabilityReport(
            addable=would_enter_master,
            reason=reason,
            signature=signature,
            is_new_signature=not pool_contains,
            is_forbidden_signature=forbidden,
            is_allowed_by_branch=branch_allowed,
            is_allowed_by_cut_context=cut_allowed,
            cut_coefficients=cut_coefficients,
            branch_signature=branch_signature,
            dominance_key=dominance_key,
            would_replace_existing=bool(pool_contains and not current_master_contains),
            would_change_active_support=would_change_active_support,
            would_enter_master=would_enter_master,
            reject_reason=reject_reason,
            current_master_contains_signature=current_master_contains,
            pool_contains_signature=pool_contains,
        )

    def add(self, column: BpcColumn, node_context: Any = None) -> AddResult:
        report = self.addability_check(column, node_context)
        if report.pool_contains_signature or not report.addable:
            return AddResult(False, report.reason, column.signature, report)
        self.columns_by_signature[column.signature] = column
        return AddResult(True, "added_to_pool", column.signature, report)

    def get(self, sig: ColumnSemanticSignature) -> BpcColumn | None:
        return self.columns_by_signature.get(sig)
