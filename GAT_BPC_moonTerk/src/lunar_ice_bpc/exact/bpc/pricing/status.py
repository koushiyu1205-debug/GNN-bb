"""Enum status taxonomy for exact-safe BPC artifacts."""

from __future__ import annotations

from enum import Enum


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class AlgorithmStatus(_StringEnum):
    DIRECT_DP_BASELINE_OPTIMAL = "DIRECT_DP_BASELINE_OPTIMAL"
    DIRECT_DP_NO_COVER = "DIRECT_DP_NO_COVER"
    DIRECT_DP_TIME_LIMIT = "DIRECT_DP_TIME_LIMIT"
    CANONICAL_DP_BASELINE_OPTIMAL = "CANONICAL_DP_BASELINE_OPTIMAL"
    SKIPPED_TOO_LARGE_FOR_DIRECT_DP_BASELINE = "SKIPPED_TOO_LARGE_FOR_DIRECT_DP_BASELINE"
    SKIPPED_TOO_LARGE_FOR_ENUM_BASELINE = "SKIPPED_TOO_LARGE_FOR_ENUM_BASELINE"
    NO_COLUMN_COVER_IN_CANONICAL_UNIVERSE = "NO_COLUMN_COVER_IN_CANONICAL_UNIVERSE"
    BPC_OPTIMAL = "BPC_OPTIMAL"
    BPC_TIME_LIMIT = "BPC_TIME_LIMIT"
    BPC_INCOMPLETE_PRICING = "BPC_INCOMPLETE_PRICING"
    BPC_GAP_AVAILABLE = "BPC_GAP_AVAILABLE"
    BPC_INFEASIBLE = "BPC_INFEASIBLE"


class CertificateScope(_StringEnum):
    DIRECT_DP_FIXED_GRAPH_OPTIMAL = "DIRECT_DP_FIXED_GRAPH_OPTIMAL"
    DIRECT_DP_NO_COVER = "DIRECT_DP_NO_COVER"
    BPC_NODE_LP_CERTIFIED = "BPC_NODE_LP_CERTIFIED"
    BPC_TREE_OPTIMAL = "BPC_TREE_OPTIMAL"
    BPC_INFEASIBLE_CERTIFIED = "BPC_INFEASIBLE_CERTIFIED"
    DIAGNOSTIC_RMP_BOUND = "DIAGNOSTIC_RMP_BOUND"
    DIAGNOSTIC_PRICING_FRONTIER = "DIAGNOSTIC_PRICING_FRONTIER"
    FEASIBLE_INCUMBENT_ONLY = "FEASIBLE_INCUMBENT_ONLY"


class PricingState(_StringEnum):
    FOUND_NEGATIVE = "FOUND_NEGATIVE"
    LOCAL_NO_COLUMN_UNCERTIFIED = "LOCAL_NO_COLUMN_UNCERTIFIED"
    CERTIFIED_NO_NEGATIVE = "CERTIFIED_NO_NEGATIVE"
    INCOMPLETE_LIMIT = "INCOMPLETE_LIMIT"
    DUPLICATE_ONLY = "DUPLICATE_ONLY"
    NOT_PRICED = "NOT_PRICED"


class BpcCertificateStatus(_StringEnum):
    CERTIFIED_NO_NEGATIVE = "CERTIFIED_NO_NEGATIVE"
    NOT_PORTED_TRUE_DUAL_BPC = "NOT_PORTED_TRUE_DUAL_BPC"
    WAITING_TRUE_DUAL_PRICING_PROOF = "WAITING_TRUE_DUAL_PRICING_PROOF"
    BLOCKED_BY_PROOF_DEBT = "BLOCKED_BY_PROOF_DEBT"
    INVALID_CERTIFICATE_SCOPE = "INVALID_CERTIFICATE_SCOPE"


DIRECT_DP_TIME_LIMIT_STATUSES = frozenset(
    {
        AlgorithmStatus.DIRECT_DP_TIME_LIMIT.value,
        "DIRECT_DP_BASELINE_TIME_LIMIT",
    }
)


def algorithm_status_value(status: AlgorithmStatus | str) -> str:
    return status.value if isinstance(status, AlgorithmStatus) else str(status)


def certificate_scope_value(scope: CertificateScope | str) -> str:
    return scope.value if isinstance(scope, CertificateScope) else str(scope)


def certificate_scope_for_algorithm_status(status: AlgorithmStatus | str) -> CertificateScope:
    value = algorithm_status_value(status)
    if value == AlgorithmStatus.DIRECT_DP_BASELINE_OPTIMAL.value:
        return CertificateScope.DIRECT_DP_FIXED_GRAPH_OPTIMAL
    if value == AlgorithmStatus.DIRECT_DP_NO_COVER.value or value == "NO_COLUMN_COVER_IN_DIRECT_DP_UNIVERSE":
        return CertificateScope.DIRECT_DP_NO_COVER
    return CertificateScope.FEASIBLE_INCUMBENT_ONLY


def is_direct_dp_time_limit_status(status: AlgorithmStatus | str) -> bool:
    return algorithm_status_value(status) in DIRECT_DP_TIME_LIMIT_STATUSES

