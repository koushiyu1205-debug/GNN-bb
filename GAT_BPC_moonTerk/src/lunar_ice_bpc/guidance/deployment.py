"""Framework-free deployment gates for P0 V2 guidance.

This module must remain safe to import in a fresh small-scale process.  In
particular it deliberately does not import torch or any model implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path
from typing import Any


SUPPORTED_SCALES = (5, 10, 20, 30, 50, 100)
DEPLOYMENT_ELIGIBILITY_SCHEMA_V2 = (
    "lunar_ice_bpc.deployment_eligibility_manifest.v2"
)
DEPLOYMENT_ELIGIBILITY_SCHEMA_V1 = DEPLOYMENT_ELIGIBILITY_SCHEMA_V2
ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE = (
    "route_harvest_single_promotion"
)


@dataclass(frozen=True)
class DeploymentEligibilityManifest:
    checkpoint_id: str
    checkpoint_path: str
    source_baseline_id: str
    engine_hash: str
    model_kind: str
    feature_schema_version: str
    normalization_version: str
    ood_policy_version: str
    checkpoint_sha256: str = ""
    promotion_gate_report_hash: str = ""
    experimental_discovery_only: bool = False
    formal_promotion_eligible: bool = False
    discovery_validation_fold: int | None = None
    torch_num_threads: int = 1
    deterministic_inference: bool = True
    guidance_action_scope: str = ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE
    p0_noop_required: bool = True
    max_learned_promotions_per_context: int = 1
    engine_hash_by_scale: tuple[tuple[int, str], ...] = tuple()
    eligible_online_scales: tuple[int, ...] = tuple()
    shadow_only_scales: tuple[int, ...] = SUPPORTED_SCALES
    preimport_bypass_scales: tuple[int, ...] = tuple()
    cheap_gate_policy_version: str = "candidate_pressure_gate_v1"
    minimum_harvest_candidates_by_scale: tuple[
        tuple[int, int], ...
    ] = tuple()
    minimum_harvest_negative_mass_by_scale: tuple[
        tuple[int, float], ...
    ] = tuple()
    frozen: bool = True
    schema_version: str = DEPLOYMENT_ELIGIBILITY_SCHEMA_V1

    def __post_init__(self) -> None:
        for field_name in (
            "eligible_online_scales",
            "shadow_only_scales",
            "preimport_bypass_scales",
        ):
            values = tuple(
                sorted({int(value) for value in getattr(self, field_name)})
            )
            unsupported = set(values).difference(SUPPORTED_SCALES)
            if unsupported:
                raise ValueError(
                    f"{field_name} contains unsupported scales {sorted(unsupported)}"
                )
            object.__setattr__(self, field_name, values)
        engine_rows = tuple(
            sorted(
                (
                    (int(scale), str(engine_hash))
                    for scale, engine_hash in self.engine_hash_by_scale
                ),
                key=lambda row: row[0],
            )
        )
        if len({scale for scale, _ in engine_rows}) != len(engine_rows):
            raise ValueError("engine_hash_by_scale contains duplicate scales")
        if any(
            scale not in SUPPORTED_SCALES or not engine_hash
            for scale, engine_hash in engine_rows
        ):
            raise ValueError("engine_hash_by_scale contains invalid rows")
        object.__setattr__(self, "engine_hash_by_scale", engine_rows)
        candidate_rows = tuple(
            sorted(
                (
                    (int(scale), int(count))
                    for scale, count in (
                        self.minimum_harvest_candidates_by_scale
                    )
                ),
                key=lambda row: row[0],
            )
        )
        mass_rows = tuple(
            sorted(
                (
                    (int(scale), float(value))
                    for scale, value in (
                        self.minimum_harvest_negative_mass_by_scale
                    )
                ),
                key=lambda row: row[0],
            )
        )
        if len({scale for scale, _ in candidate_rows}) != len(candidate_rows):
            raise ValueError(
                "minimum_harvest_candidates_by_scale has duplicate scales"
            )
        if len({scale for scale, _ in mass_rows}) != len(mass_rows):
            raise ValueError(
                "minimum_harvest_negative_mass_by_scale has duplicate scales"
            )
        if any(
            scale not in SUPPORTED_SCALES or count < 2
            for scale, count in candidate_rows
        ):
            raise ValueError(
                "harvest candidate gate requires supported scales and count>=2"
            )
        if any(
            scale not in SUPPORTED_SCALES
            or not isfinite(value)
            or value < 0.0
            for scale, value in mass_rows
        ):
            raise ValueError(
                "harvest pressure gate requires supported scales and mass>=0"
            )
        object.__setattr__(
            self, "minimum_harvest_candidates_by_scale", candidate_rows
        )
        object.__setattr__(
            self, "minimum_harvest_negative_mass_by_scale", mass_rows
        )
        if set(self.eligible_online_scales).intersection(
            self.preimport_bypass_scales
        ):
            raise ValueError("an online-eligible scale cannot be pre-import bypassed")
        if not self.checkpoint_id:
            raise ValueError("checkpoint_id must be non-empty")
        if not self.source_baseline_id:
            raise ValueError("source_baseline_id must be non-empty")
        if not self.engine_hash:
            raise ValueError("engine_hash must be non-empty")
        if not self.frozen:
            raise ValueError("deployment manifest must be frozen before use")
        if self.cheap_gate_policy_version != "candidate_pressure_gate_v1":
            raise ValueError("unsupported pre-import cheap gate policy")
        if int(self.torch_num_threads) < 1:
            raise ValueError("torch_num_threads must be positive")
        object.__setattr__(
            self, "torch_num_threads", int(self.torch_num_threads)
        )
        if not self.deterministic_inference:
            raise ValueError(
                "P0 V2 deployment requires deterministic inference"
            )
        if self.guidance_action_scope != (
            ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE
        ):
            raise ValueError(
                "first-stage deployment only supports one route-level "
                "harvest promotion"
            )
        if not self.p0_noop_required:
            raise ValueError("P0_KEEP_ORDER must remain a deployable action")
        if int(self.max_learned_promotions_per_context) != 1:
            raise ValueError(
                "first-stage deployment permits exactly one learned "
                "promotion per context"
            )
        object.__setattr__(
            self,
            "max_learned_promotions_per_context",
            1,
        )
        if self.experimental_discovery_only and self.formal_promotion_eligible:
            raise ValueError(
                "discovery-only manifest cannot be formally promoted"
            )
        if (
            self.experimental_discovery_only
            and self.promotion_gate_report_hash
        ):
            raise ValueError(
                "discovery-only manifest cannot bind a promotion report"
            )
        if (
            self.formal_promotion_eligible
            and not self.promotion_gate_report_hash
        ):
            raise ValueError(
                "formal promotion requires a gate report hash"
            )
        if self.experimental_discovery_only:
            if self.discovery_validation_fold is None:
                raise ValueError(
                    "discovery-only manifest requires a validation fold"
                )
            if int(self.discovery_validation_fold) not in range(5):
                raise ValueError("discovery validation fold must be 0..4")
            object.__setattr__(
                self,
                "discovery_validation_fold",
                int(self.discovery_validation_fold),
            )

    @classmethod
    def from_payload(
        cls, payload: dict[str, Any]
    ) -> "DeploymentEligibilityManifest":
        return cls(
            checkpoint_id=str(payload["checkpoint_id"]),
            checkpoint_path=str(payload.get("checkpoint_path") or ""),
            source_baseline_id=str(payload["source_baseline_id"]),
            engine_hash=str(payload["engine_hash"]),
            model_kind=str(payload["model_kind"]),
            feature_schema_version=str(payload["feature_schema_version"]),
            normalization_version=str(payload["normalization_version"]),
            ood_policy_version=str(payload["ood_policy_version"]),
            checkpoint_sha256=str(payload.get("checkpoint_sha256") or ""),
            promotion_gate_report_hash=str(
                payload.get("promotion_gate_report_hash") or ""
            ),
            experimental_discovery_only=bool(
                payload.get("experimental_discovery_only", False)
            ),
            formal_promotion_eligible=bool(
                payload.get("formal_promotion_eligible", False)
            ),
            discovery_validation_fold=(
                None
                if payload.get("discovery_validation_fold") is None
                else int(payload["discovery_validation_fold"])
            ),
            torch_num_threads=int(payload.get("torch_num_threads") or 1),
            deterministic_inference=bool(
                payload.get("deterministic_inference", True)
            ),
            guidance_action_scope=str(
                payload.get(
                    "guidance_action_scope",
                    ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE,
                )
            ),
            p0_noop_required=bool(
                payload.get("p0_noop_required", True)
            ),
            max_learned_promotions_per_context=int(
                payload.get("max_learned_promotions_per_context", 1)
            ),
            engine_hash_by_scale=tuple(
                (int(scale), str(engine_hash))
                for scale, engine_hash in payload.get(
                    "engine_hash_by_scale", ()
                )
            ),
            eligible_online_scales=tuple(
                int(value)
                for value in payload.get("eligible_online_scales", ())
            ),
            shadow_only_scales=tuple(
                int(value)
                for value in payload.get("shadow_only_scales", SUPPORTED_SCALES)
            ),
            preimport_bypass_scales=tuple(
                int(value)
                for value in payload.get("preimport_bypass_scales", ())
            ),
            cheap_gate_policy_version=str(
                payload.get(
                    "cheap_gate_policy_version",
                    "candidate_pressure_gate_v1",
                )
            ),
            minimum_harvest_candidates_by_scale=tuple(
                (int(scale), int(count))
                for scale, count in payload.get(
                    "minimum_harvest_candidates_by_scale", ()
                )
            ),
            minimum_harvest_negative_mass_by_scale=tuple(
                (int(scale), float(value))
                for scale, value in payload.get(
                    "minimum_harvest_negative_mass_by_scale", ()
                )
            ),
            frozen=bool(payload.get("frozen", True)),
            schema_version=str(
                payload.get(
                    "schema_version", DEPLOYMENT_ELIGIBILITY_SCHEMA_V1
                )
            ),
        )

    @classmethod
    def load(cls, path: str | Path) -> "DeploymentEligibilityManifest":
        return cls.from_payload(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_path": self.checkpoint_path,
            "source_baseline_id": self.source_baseline_id,
            "engine_hash": self.engine_hash,
            "model_kind": self.model_kind,
            "feature_schema_version": self.feature_schema_version,
            "normalization_version": self.normalization_version,
            "ood_policy_version": self.ood_policy_version,
            "checkpoint_sha256": self.checkpoint_sha256,
            "promotion_gate_report_hash": self.promotion_gate_report_hash,
            "experimental_discovery_only": self.experimental_discovery_only,
            "formal_promotion_eligible": self.formal_promotion_eligible,
            "discovery_validation_fold": self.discovery_validation_fold,
            "torch_num_threads": self.torch_num_threads,
            "deterministic_inference": self.deterministic_inference,
            "guidance_action_scope": self.guidance_action_scope,
            "p0_noop_required": self.p0_noop_required,
            "max_learned_promotions_per_context": (
                self.max_learned_promotions_per_context
            ),
            "engine_hash_by_scale": [
                [scale, engine_hash]
                for scale, engine_hash in self.engine_hash_by_scale
            ],
            "eligible_online_scales": list(self.eligible_online_scales),
            "shadow_only_scales": list(self.shadow_only_scales),
            "preimport_bypass_scales": list(self.preimport_bypass_scales),
            "cheap_gate_policy_version": self.cheap_gate_policy_version,
            "minimum_harvest_candidates_by_scale": [
                [scale, count]
                for scale, count in (
                    self.minimum_harvest_candidates_by_scale
                )
            ],
            "minimum_harvest_negative_mass_by_scale": [
                [scale, value]
                for scale, value in (
                    self.minimum_harvest_negative_mass_by_scale
                )
            ],
            "frozen": self.frozen,
        }

    def expected_engine_hash(self, scale: int) -> str:
        return str(
            dict(self.engine_hash_by_scale).get(int(scale), self.engine_hash)
        )

    def minimum_harvest_candidates(self, scale: int) -> int:
        return int(
            dict(self.minimum_harvest_candidates_by_scale).get(
                int(scale), 2
            )
        )

    def minimum_harvest_negative_mass(self, scale: int) -> float:
        return float(
            dict(self.minimum_harvest_negative_mass_by_scale).get(
                int(scale), 0.0
            )
        )


@dataclass(frozen=True)
class GuidanceEntryDecision:
    status: str
    requested_mode: str
    effective_mode: str
    scale: int
    import_learning_runtime: bool
    reason: str

    @property
    def bypassed_before_import(self) -> bool:
        return not self.import_learning_runtime


def decide_guidance_entry(
    manifest: DeploymentEligibilityManifest,
    *,
    scale: int,
    requested_mode: str,
) -> GuidanceEntryDecision:
    """Make the full eligibility decision without importing torch."""

    normalized_scale = int(scale)
    mode = str(requested_mode)
    if mode == "off":
        return GuidanceEntryDecision(
            status="GUIDANCE_DISABLED",
            requested_mode=mode,
            effective_mode="off",
            scale=normalized_scale,
            import_learning_runtime=False,
            reason="guidance_mode_off",
        )
    if normalized_scale not in SUPPORTED_SCALES:
        return GuidanceEntryDecision(
            status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
            requested_mode=mode,
            effective_mode="off",
            scale=normalized_scale,
            import_learning_runtime=False,
            reason="unsupported_scale",
        )
    if mode == "task_arc":
        return GuidanceEntryDecision(
            status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
            requested_mode=mode,
            effective_mode="off",
            scale=normalized_scale,
            import_learning_runtime=False,
            reason="task_arc_not_in_first_stage_online_scope",
        )
    if normalized_scale in manifest.preimport_bypass_scales:
        return GuidanceEntryDecision(
            status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
            requested_mode=mode,
            effective_mode="off",
            scale=normalized_scale,
            import_learning_runtime=False,
            reason="scale_frozen_to_preimport_bypass",
        )
    if mode in {"harvest", "task_arc"}:
        eligible = normalized_scale in manifest.eligible_online_scales
        if not eligible:
            return GuidanceEntryDecision(
                status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
                requested_mode=mode,
                effective_mode="off",
                scale=normalized_scale,
                import_learning_runtime=False,
                reason="scale_not_online_eligible",
            )
    if normalized_scale not in set(manifest.shadow_only_scales).union(
        manifest.eligible_online_scales
    ):
        return GuidanceEntryDecision(
            status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
            requested_mode=mode,
            effective_mode="off",
            scale=normalized_scale,
            import_learning_runtime=False,
            reason="scale_not_manifest_enabled",
        )
    if not manifest.checkpoint_path:
        return GuidanceEntryDecision(
            status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
            requested_mode=mode,
            effective_mode="off",
            scale=normalized_scale,
            import_learning_runtime=False,
            reason="checkpoint_path_missing",
        )
    return GuidanceEntryDecision(
        status="GUIDANCE_RUNTIME_ELIGIBLE",
        requested_mode=mode,
        effective_mode=mode,
        scale=normalized_scale,
        import_learning_runtime=True,
        reason="manifest_gate_passed",
    )
