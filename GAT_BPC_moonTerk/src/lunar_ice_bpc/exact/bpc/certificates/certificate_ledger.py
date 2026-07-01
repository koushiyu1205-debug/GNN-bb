"""Certificate ledger tying algorithm status to certificate scope."""

from __future__ import annotations

from dataclasses import dataclass, field

from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.pricing.status import (
    AlgorithmStatus,
    BpcCertificateStatus,
    CertificateScope,
    PricingState,
    algorithm_status_value,
    certificate_scope_value,
)


@dataclass
class CertificateLedger:
    algorithm_status: AlgorithmStatus | str
    certificate_scope: CertificateScope | str
    pricing_state: PricingState | str = PricingState.NOT_PRICED
    uses_true_dual_bpc_certificate: bool = False
    issues: list[str] = field(default_factory=list)

    def validate(self, proof_debt_queue: ProofDebtQueue | None = None) -> dict:
        issues = list(self.issues)
        scope = certificate_scope_value(self.certificate_scope)
        status = algorithm_status_value(self.algorithm_status)
        if scope in {CertificateScope.BPC_NODE_LP_CERTIFIED.value, CertificateScope.BPC_TREE_OPTIMAL.value}:
            if not self.uses_true_dual_bpc_certificate:
                issues.append("bpc_scope_requires_true_dual_certificate")
        if scope == CertificateScope.DIRECT_DP_FIXED_GRAPH_OPTIMAL.value:
            if status != AlgorithmStatus.DIRECT_DP_BASELINE_OPTIMAL.value:
                issues.append("direct_dp_scope_requires_direct_dp_optimal_status")
        if proof_debt_queue is not None and proof_debt_queue.block_certificate_if_unreleased():
            issues.append("unreleased_true_rc_negative_proof_debt")
        certificate_status = (
            BpcCertificateStatus.BLOCKED_BY_PROOF_DEBT.value
            if "unreleased_true_rc_negative_proof_debt" in issues
            else (
                BpcCertificateStatus.CERTIFIED_NO_NEGATIVE.value
                if self.uses_true_dual_bpc_certificate and not issues
                else BpcCertificateStatus.NOT_PORTED_TRUE_DUAL_BPC.value
            )
        )
        return {
            "algorithm_status": status,
            "certificate_scope": scope,
            "pricing_state": str(self.pricing_state),
            "uses_true_dual_bpc_certificate": bool(self.uses_true_dual_bpc_certificate),
            "certificate_status": certificate_status,
            "issues": issues,
            "valid": not issues,
        }

