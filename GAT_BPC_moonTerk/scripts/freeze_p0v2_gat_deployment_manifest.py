#!/usr/bin/env python3
"""Freeze an auditable, per-scale P0 V2 guidance deployment manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path

import torch

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.tensorization import (
    COMPOSITE_FEATURE_SCHEMA_V3,
    HARVEST_MODEL_CONTEXT_SCHEMA_V2,
)
from lunar_ice_bpc.guidance.deployment import (
    ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE,
    SUPPORTED_SCALES,
    DeploymentEligibilityManifest,
)
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--engine-hash",
        action="append",
        required=True,
        metavar="SCALE=HASH",
        help="Repeat once for every enabled scale.",
    )
    parser.add_argument("--online-scales", default="")
    parser.add_argument(
        "--shadow-scales",
        default="5,10,20,30,50,100",
    )
    parser.add_argument("--preimport-bypass-scales", default="")
    parser.add_argument(
        "--minimum-harvest-candidates",
        action="append",
        default=[],
        metavar="SCALE=COUNT",
        help=(
            "Cheap pre-import gate. Repeat for online scales; COUNT must be "
            "at least two."
        ),
    )
    parser.add_argument(
        "--minimum-harvest-negative-mass",
        action="append",
        default=[],
        metavar="SCALE=VALUE",
        help=(
            "Cheap pre-import pricing-pressure gate. Repeat for online scales."
        ),
    )
    parser.add_argument("--torch-num-threads", type=int, default=1)
    parser.add_argument(
        "--promotion-gate-report",
        default="",
        help="Required when any scale is online eligible.",
    )
    parser.add_argument(
        "--experimental-discovery-only",
        action="store_true",
        help=(
            "Allow held-out development-fold H/HA evidence collection before "
            "formal promotion. This manifest is never production eligible."
        ),
    )
    args = parser.parse_args()

    online = _parse_scales(args.online_scales)
    shadow = _parse_scales(args.shadow_scales)
    bypass = _parse_scales(args.preimport_bypass_scales)
    enabled = set(online).union(shadow)
    if not enabled:
        raise SystemExit("deployment manifest must enable at least one scale")
    engines = _parse_engine_rows(args.engine_hash)
    minimum_candidates = _parse_int_rows(
        args.minimum_harvest_candidates,
        field_name="minimum harvest candidates",
        minimum=2,
    )
    minimum_negative_mass = _parse_float_rows(
        args.minimum_harvest_negative_mass,
        field_name="minimum harvest negative mass",
        minimum=0.0,
    )
    missing = sorted(enabled.difference(engines))
    if missing:
        raise SystemExit(
            "engine hash missing for enabled scales: "
            + ",".join(str(value) for value in missing)
        )

    gate_hash = ""
    if online:
        missing_candidate_gates = sorted(
            set(online).difference(minimum_candidates)
        )
        missing_mass_gates = sorted(
            set(online).difference(minimum_negative_mass)
        )
        if (
            not args.experimental_discovery_only
            and (missing_candidate_gates or missing_mass_gates)
        ):
            raise SystemExit(
                "formal online scales require explicit cheap-gate thresholds; "
                f"missing candidate scales={missing_candidate_gates}, "
                f"missing pressure scales={missing_mass_gates}"
            )
        if (
            not args.experimental_discovery_only
            and not args.promotion_gate_report
        ):
            raise SystemExit(
                "online eligibility requires --promotion-gate-report"
            )
        if args.promotion_gate_report:
            gate_path = Path(args.promotion_gate_report).resolve()
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            if not bool(gate.get("passed")):
                raise SystemExit("promotion gate did not pass")
            if not args.experimental_discovery_only:
                if str(gate.get("training_objective") or "") != (
                    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                ):
                    raise SystemExit(
                        "formal promotion report has the wrong training "
                        "objective"
                    )
                if bool(gate.get("calibration_used")) or bool(
                    gate.get("protected_final_test_used")
                ):
                    raise SystemExit(
                        "formal promotion selection cannot use calibration "
                        "or protected test data"
                    )
                selected_decisions = [
                    row
                    for row in gate.get("decisions", ())
                    if bool(row.get("eligible"))
                    and str(row.get("model_kind") or "")
                    == str(gate.get("selected_model_kind") or "")
                ]
                required_gate_names = {
                    "p0_noop_calibration_gate",
                    "route_harvest_first_stage_gate",
                    "memory_resource_safety_gate",
                    "net_advantage_after_model_cost_gate",
                    "instance_snapshot_bootstrap_unit_gate",
                    "scale50_100_safety_only_gate",
                    "unbiased_sentinel_opportunity_density_gate",
                    "perfect_policy_net_benefit_gate",
                    "cheap_preimport_eligibility_gate",
                }
                decision_gates = (
                    {}
                    if len(selected_decisions) != 1
                    else dict(
                        selected_decisions[0].get(
                            "required_review_gates", {}
                        )
                    )
                )
                roi_eligible_scales = (
                    set()
                    if len(selected_decisions) != 1
                    else {
                        int(value)
                        for value in selected_decisions[0].get(
                            "opportunity_roi_eligible_scales", ()
                        )
                    }
                )
                if (
                    len(selected_decisions) != 1
                    or not required_gate_names.issubset(decision_gates)
                    or not all(
                        bool(decision_gates[name])
                        for name in required_gate_names
                    )
                    or not set(online).issubset(roi_eligible_scales)
                ):
                    raise SystemExit(
                        "formal promotion report lacks the reviewed route, "
                        "no-op, memory, bootstrap, per-scale opportunity, "
                        "or net-benefit gates"
                    )
            gate_hash = stable_payload_hash(gate)
    if args.experimental_discovery_only and args.promotion_gate_report:
        raise SystemExit(
            "discovery-only manifest cannot bind a formal promotion report"
        )
    if args.experimental_discovery_only and not online:
        raise SystemExit(
            "discovery-only manifest requires at least one online scale"
        )

    checkpoint_path = Path(args.checkpoint).resolve()
    checkpoint_sha256 = _sha256_file(checkpoint_path)
    payload = torch.load(
        checkpoint_path, map_location="cpu", weights_only=False
    )
    metadata = dict(payload.get("metadata") or {})
    required_metadata = (
        "checkpoint_id",
        "source_baseline_id",
        "feature_schema_version",
        "harvest_model_context_schema_version",
        "normalization_version",
        "ood_policy_version",
        "node_feature_mean",
        "node_feature_std",
        "edge_feature_mean",
        "edge_feature_std",
        "ood_max_abs_z",
        "training_objective",
        "counterfactual_main_scope",
        "p0_noop_trained",
        "trained_main_heads",
    )
    missing_metadata = [
        key for key in required_metadata if not metadata.get(key)
    ]
    if missing_metadata:
        raise SystemExit(
            "checkpoint metadata missing: " + ",".join(missing_metadata)
        )
    if str(metadata["feature_schema_version"]) != COMPOSITE_FEATURE_SCHEMA_V3:
        raise SystemExit("checkpoint composite feature schema is not deployable")
    if str(
        metadata["harvest_model_context_schema_version"]
    ) != HARVEST_MODEL_CONTEXT_SCHEMA_V2:
        raise SystemExit("checkpoint harvest model-context schema is not deployable")
    if str(metadata["training_objective"]) != (
        COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
    ):
        raise SystemExit(
            "deployment rejects legacy/non-counterfactual objectives"
        )
    if str(metadata["counterfactual_main_scope"]) != "harvest_only":
        raise SystemExit(
            "first-stage deployment requires harvest-only main training"
        )
    if not bool(metadata["p0_noop_trained"]):
        raise SystemExit(
            "first-stage deployment requires a trained P0_KEEP_ORDER action"
        )
    if "harvest" not in {
        str(value) for value in metadata["trained_main_heads"]
    }:
        raise SystemExit(
            "first-stage deployment requires a trained route-harvest head"
        )
    node_dim = int(payload["node_input_dim"])
    edge_dim = int(payload["edge_input_dim"])
    if any(
        len(metadata[key]) != expected
        for key, expected in (
            ("node_feature_mean", node_dim),
            ("node_feature_std", node_dim),
            ("edge_feature_mean", edge_dim),
            ("edge_feature_std", edge_dim),
        )
    ):
        raise SystemExit("checkpoint normalization width mismatch")
    numeric_metadata = [
        *metadata["node_feature_mean"],
        *metadata["node_feature_std"],
        *metadata["edge_feature_mean"],
        *metadata["edge_feature_std"],
        metadata["ood_max_abs_z"],
    ]
    if any(not isfinite(float(value)) for value in numeric_metadata):
        raise SystemExit("checkpoint normalization/OOD metadata is non-finite")
    if any(
        float(value) <= 0.0
        for key in ("node_feature_std", "edge_feature_std")
        for value in metadata[key]
    ):
        raise SystemExit("checkpoint normalization std must be positive")
    if not bool(metadata.get("ood_calibrated")):
        raise SystemExit(
            "runtime deployment requires calibrated OOD metadata"
        )
    ood_thresholds = dict(
        metadata.get("ood_max_abs_z_by_scale") or {}
    )
    missing_ood_scales = sorted(
        scale for scale in enabled if str(scale) not in ood_thresholds
    )
    if missing_ood_scales:
        raise SystemExit(
            "OOD calibration missing enabled scales: "
            + ",".join(str(scale) for scale in missing_ood_scales)
        )
    if any(
        not isfinite(float(ood_thresholds[str(scale)]))
        or float(ood_thresholds[str(scale)]) < 0.0
        for scale in enabled
    ):
        raise SystemExit("OOD calibration contains invalid thresholds")
    compatible = {
        str(value)
        for value in metadata.get("compatible_engine_hashes", ())
    }
    required_engines = {engines[scale] for scale in enabled}
    if compatible:
        absent = sorted(required_engines.difference(compatible))
        if absent:
            raise SystemExit(
                "checkpoint lacks compatible engine hashes: "
                + ",".join(absent)
            )
    elif len(required_engines) != 1 or str(
        metadata.get("engine_hash") or ""
    ) not in required_engines:
        raise SystemExit(
            "legacy single-engine checkpoint cannot cover this manifest"
        )
    discovery_validation_fold = None
    if args.experimental_discovery_only:
        try:
            discovery_validation_fold = int(metadata["fold"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(
                "discovery checkpoint must bind one integer validation fold"
            ) from exc
        if discovery_validation_fold not in range(5):
            raise SystemExit(
                "discovery checkpoint validation fold must be 0..4"
            )

    manifest = DeploymentEligibilityManifest(
        checkpoint_id=str(metadata["checkpoint_id"]),
        checkpoint_path=str(checkpoint_path),
        source_baseline_id=str(metadata["source_baseline_id"]),
        engine_hash=str(engines[min(enabled)]),
        model_kind=str(payload["model_kind"]),
        feature_schema_version=str(metadata["feature_schema_version"]),
        normalization_version=str(metadata["normalization_version"]),
        ood_policy_version=str(metadata["ood_policy_version"]),
        checkpoint_sha256=checkpoint_sha256,
        promotion_gate_report_hash=gate_hash,
        experimental_discovery_only=bool(
            args.experimental_discovery_only
        ),
        formal_promotion_eligible=bool(online and gate_hash),
        discovery_validation_fold=discovery_validation_fold,
        torch_num_threads=max(1, int(args.torch_num_threads)),
        deterministic_inference=True,
        guidance_action_scope=ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE,
        p0_noop_required=True,
        max_learned_promotions_per_context=1,
        engine_hash_by_scale=tuple(
            (scale, engines[scale]) for scale in sorted(enabled)
        ),
        eligible_online_scales=online,
        shadow_only_scales=shadow,
        preimport_bypass_scales=bypass,
        cheap_gate_policy_version="candidate_pressure_gate_v1",
        minimum_harvest_candidates_by_scale=tuple(
            sorted(minimum_candidates.items())
        ),
        minimum_harvest_negative_mass_by_scale=tuple(
            sorted(minimum_negative_mass.items())
        ),
    )
    output_payload = manifest.to_payload()
    output_payload["deployment_scope"] = (
        "held_out_development_fold_discovery_only"
        if args.experimental_discovery_only
        else "formal_promotion_or_shadow"
    )
    output_payload["manifest_hash"] = stable_payload_hash(output_payload)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            output_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


def _parse_scales(raw: str) -> tuple[int, ...]:
    values = tuple(
        sorted(
            {
                int(value)
                for value in str(raw).split(",")
                if value.strip()
            }
        )
    )
    unsupported = set(values).difference(SUPPORTED_SCALES)
    if unsupported:
        raise SystemExit(f"unsupported scales: {sorted(unsupported)}")
    return values


def _parse_engine_rows(rows: list[str]) -> dict[int, str]:
    parsed: dict[int, str] = {}
    for row in rows:
        scale_raw, separator, engine_hash = str(row).partition("=")
        if not separator or not scale_raw.strip() or not engine_hash.strip():
            raise SystemExit(f"invalid --engine-hash row {row!r}")
        scale = int(scale_raw)
        if scale not in SUPPORTED_SCALES:
            raise SystemExit(f"unsupported engine scale {scale}")
        if scale in parsed:
            raise SystemExit(f"duplicate engine hash for scale {scale}")
        parsed[scale] = engine_hash.strip()
    return parsed


def _parse_int_rows(
    rows: list[str],
    *,
    field_name: str,
    minimum: int,
) -> dict[int, int]:
    parsed: dict[int, int] = {}
    for row in rows:
        scale_raw, separator, value_raw = str(row).partition("=")
        if not separator:
            raise SystemExit(f"invalid {field_name} row {row!r}")
        scale = int(scale_raw)
        value = int(value_raw)
        if scale not in SUPPORTED_SCALES or value < minimum:
            raise SystemExit(f"invalid {field_name} row {row!r}")
        if scale in parsed:
            raise SystemExit(f"duplicate {field_name} scale {scale}")
        parsed[scale] = value
    return parsed


def _parse_float_rows(
    rows: list[str],
    *,
    field_name: str,
    minimum: float,
) -> dict[int, float]:
    parsed: dict[int, float] = {}
    for row in rows:
        scale_raw, separator, value_raw = str(row).partition("=")
        if not separator:
            raise SystemExit(f"invalid {field_name} row {row!r}")
        scale = int(scale_raw)
        value = float(value_raw)
        if (
            scale not in SUPPORTED_SCALES
            or not isfinite(value)
            or value < minimum
        ):
            raise SystemExit(f"invalid {field_name} row {row!r}")
        if scale in parsed:
            raise SystemExit(f"duplicate {field_name} scale {scale}")
        parsed[scale] = value
    return parsed


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
