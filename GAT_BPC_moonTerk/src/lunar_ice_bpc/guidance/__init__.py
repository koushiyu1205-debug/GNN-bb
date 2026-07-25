"""Exact-safe learning-to-order components.

This package entry point remains framework-free.  Torch is imported only by
``models`` after ``deployment.decide_guidance_entry`` admits the scale.
Guidance artifacts cannot certify no-negative pricing, official lower bounds,
pruning, or optimality.
"""

from lunar_ice_bpc.guidance.deployment import (
    DeploymentEligibilityManifest,
    GuidanceEntryDecision,
    decide_guidance_entry,
)
from lunar_ice_bpc.guidance.identity import (
    EXPERIMENT_LIVE_SRI_POLICY,
    GAT_EXPERIMENT_FAMILY_ID,
    P0V2_BINDING_V2_B0_CONTROL_ID,
    P0V2_EXPERIMENT_CONTROL_ID,
    PRODUCTION_DEFAULT_LIVE_SRI_POLICY,
)
from lunar_ice_bpc.guidance.opportunity_gate import (
    attach_matched_end_to_end_benefit,
    audit_opportunity_roi,
    validate_opportunity_observation,
)

__all__ = [
    "DeploymentEligibilityManifest",
    "GuidanceEntryDecision",
    "decide_guidance_entry",
    "EXPERIMENT_LIVE_SRI_POLICY",
    "GAT_EXPERIMENT_FAMILY_ID",
    "P0V2_BINDING_V2_B0_CONTROL_ID",
    "P0V2_EXPERIMENT_CONTROL_ID",
    "PRODUCTION_DEFAULT_LIVE_SRI_POLICY",
    "audit_opportunity_roi",
    "attach_matched_end_to_end_benefit",
    "validate_opportunity_observation",
]
