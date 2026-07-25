#!/usr/bin/env python3
"""Collect resumable fresh-process QC0/QD1 proof-tail pairs.

The input is a preselected context manifest.  Pair order is frozen from a
stable hash before either arm runs.  Repetitions estimate timing noise and
never increase the independent-context count.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from lunar_ice_bpc.exact.bpc.guidance.replay import (
    load_pricing_snapshot,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.proof_tail_gate import (
    audit_static_proof_tail_scale_rule,
    build_proof_tail_gate_dataset,
    build_proof_tail_policy_pair,
    validate_proof_tail_arm,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLAY_SCRIPT = (
    PROJECT_ROOT / "scripts/replay_p0v2_gat_proof_tail_snapshot.py"
)
CONTEXT_CONFIG_SCHEMA_V1 = (
    "lunar_ice_bpc.proof_tail_context_config.v1"
)
FROZEN_CONTEXT_MANIFEST_SCHEMA_V1 = (
    "lunar_ice_bpc.proof_tail_context_manifest.v1"
)
COLLECTION_REPORT_SCHEMA_V1 = (
    "lunar_ice_bpc.proof_tail_pair_collection.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--gate-wall-sec-upper-bound",
        type=float,
        default=0.001,
    )
    parser.add_argument(
        "--promotion-margin-sec",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--limit-contexts",
        type=int,
        default=0,
    )
    args = parser.parse_args()

    if args.repeats <= 0:
        raise SystemExit("--repeats must be positive")
    if args.gate_wall_sec_upper_bound < 0.0:
        raise SystemExit("gate wall upper bound must be nonnegative")
    if args.promotion_margin_sec < 0.0:
        raise SystemExit("promotion margin must be nonnegative")

    config_path = Path(args.context_config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if str(config.get("schema_version") or "") != (
        CONTEXT_CONFIG_SCHEMA_V1
    ):
        raise SystemExit("proof-tail context config schema mismatch")
    configured_hash = str(config.get("config_hash") or "")
    if configured_hash:
        actual_config_hash = stable_payload_hash(
            {
                key: value
                for key, value in config.items()
                if key != "config_hash"
            }
        )
        if configured_hash != actual_config_hash:
            raise SystemExit("proof-tail context config hash mismatch")
    split_path = _resolve_path(
        config.get("split_manifest"), config_path=config_path
    )
    split_manifest = json.loads(
        split_path.read_text(encoding="utf-8")
    )
    if str(split_manifest.get("schema_version") or "") != (
        "lunar_ice_bpc.gat_split_manifest.v1"
    ):
        raise SystemExit("proof-tail split manifest schema mismatch")
    recorded_split_hash = str(
        split_manifest.get("manifest_hash") or ""
    )
    actual_split_hash = stable_payload_hash(
        {
            key: value
            for key, value in split_manifest.items()
            if key != "manifest_hash"
        }
    )
    if recorded_split_hash != actual_split_hash:
        raise SystemExit("proof-tail split manifest hash mismatch")
    configured_split_hash = str(
        config.get("split_manifest_hash") or ""
    )
    if (
        configured_split_hash
        and configured_split_hash != recorded_split_hash
    ):
        raise SystemExit(
            "proof-tail context config binds another split manifest"
        )
    partition_by_hash = {
        str(row["instance_content_hash"]): str(row["partition"])
        for partition in (
            "development",
            "calibration",
            "protected_final_test",
        )
        for row in split_manifest.get(partition, ())
    }
    allowed_partitions = {
        str(value)
        for value in config.get(
            "allowed_partitions", ("development",)
        )
    }
    if not allowed_partitions or not allowed_partitions.issubset(
        {"development", "calibration"}
    ):
        raise SystemExit("invalid proof-tail allowed partitions")
    resolved_rows = _resolve_contexts(
        config,
        config_path=config_path,
        partition_by_hash=partition_by_hash,
        allowed_partitions=allowed_partitions,
    )
    if args.limit_contexts > 0:
        resolved_rows = resolved_rows[: int(args.limit_contexts)]
    if not resolved_rows:
        raise SystemExit("proof-tail context config is empty")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_manifest = {
        "schema_version": FROZEN_CONTEXT_MANIFEST_SCHEMA_V1,
        "source_config": str(config_path),
        "selection_frozen_before_outcome": True,
        "selection_stream": str(
            config.get("selection_stream") or "targeted_pilot"
        ),
        "selection_salt": str(
            config.get("selection_salt") or "proof-tail-pairs-v1"
        ),
        "selection_uses_qc0_qd1_outcomes": bool(
            config.get("selection_uses_qc0_qd1_outcomes", False)
        ),
        "selection_fields": list(config.get("selection_fields") or ()),
        "source_config_hash": configured_hash,
        "split_manifest": str(split_path),
        "split_manifest_hash": recorded_split_hash,
        "allowed_partitions": sorted(allowed_partitions),
        "contexts": resolved_rows,
    }
    frozen_manifest["manifest_hash"] = stable_payload_hash(
        frozen_manifest
    )
    frozen_path = output_dir / "frozen_context_manifest.json"
    _write_or_verify_json(frozen_path, frozen_manifest)

    pair_rows = []
    rejected_rows = []
    selection_salt = str(frozen_manifest["selection_salt"])
    for context in resolved_rows:
        context_dir = output_dir / str(context["context_id"])
        for repeat_index in range(int(args.repeats)):
            replicate_id = f"replicate_{repeat_index + 1:03d}"
            replicate_dir = context_dir / replicate_id
            replicate_dir.mkdir(parents=True, exist_ok=True)
            order = _pair_order(
                selection_salt=selection_salt,
                context_id=str(context["context_id"]),
                replicate_id=replicate_id,
            )
            arm_payloads: dict[str, dict[str, Any]] = {}
            for policy in order:
                target = replicate_dir / f"{policy.lower()}.json"
                if target.exists():
                    arm = json.loads(target.read_text(encoding="utf-8"))
                else:
                    _run_arm(
                        context,
                        policy_id=policy,
                        output=target,
                    )
                    arm = json.loads(target.read_text(encoding="utf-8"))
                arm_payloads[policy] = arm
            try:
                pair = build_proof_tail_policy_pair(
                    arm_payloads["QC0"],
                    arm_payloads["QD1"],
                    replicate_id=replicate_id,
                    pair_run_order=f"{order[0]}_THEN_{order[1]}",
                    gate_wall_sec_upper_bound=float(
                        args.gate_wall_sec_upper_bound
                    ),
                    promotion_margin_sec=float(
                        args.promotion_margin_sec
                    ),
                )
            except ValueError as exc:
                rejection = {
                    "schema_version": (
                        "lunar_ice_bpc.proof_tail_pair_rejection.v1"
                    ),
                    "selection_manifest_hash": frozen_manifest[
                        "manifest_hash"
                    ],
                    "configured_context_id": str(
                        context["context_id"]
                    ),
                    "replicate_id": replicate_id,
                    "pair_run_order": f"{order[0]}_THEN_{order[1]}",
                    "reason": str(exc),
                    "arms": {
                        policy: _arm_rejection_summary(
                            arm_payloads[policy]
                        )
                        for policy in ("QC0", "QD1")
                    },
                    "usable_as_complete_pair": False,
                    "production_policy_changed": False,
                }
                rejection["rejection_hash"] = stable_payload_hash(
                    rejection
                )
                _write_or_verify_json(
                    replicate_dir / "rejected_pair.json",
                    rejection,
                )
                rejected_rows.append(rejection)
                continue
            pair.update(
                {
                    "selection_manifest_hash": frozen_manifest[
                        "manifest_hash"
                    ],
                    "configured_context_id": str(
                        context["context_id"]
                    ),
                    "selection_stream": str(
                        frozen_manifest["selection_stream"]
                    ),
                }
            )
            pair["pair_hash"] = stable_payload_hash(
                {
                    key: value
                    for key, value in pair.items()
                    if key != "pair_hash"
                }
            )
            _write_or_verify_json(replicate_dir / "pair.json", pair)
            pair_rows.append(pair)

    if not pair_rows:
        raise SystemExit(
            "proof-tail collection produced no valid complete pairs"
        )
    dataset = build_proof_tail_gate_dataset(pair_rows)
    dataset.update(
        {
            "selection_manifest_hash": frozen_manifest["manifest_hash"],
            "selection_stream": frozen_manifest["selection_stream"],
            "gate_wall_sec_upper_bound": float(
                args.gate_wall_sec_upper_bound
            ),
            "promotion_margin_sec": float(args.promotion_margin_sec),
        }
    )
    dataset["dataset_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in dataset.items()
            if key != "dataset_hash"
        }
    )
    _write_json(output_dir / "proof_tail_gate_dataset.json", dataset)
    static_rule_audit = audit_static_proof_tail_scale_rule(dataset)
    _write_json(
        output_dir / "static_scale_rule_audit.json",
        static_rule_audit,
    )
    by_scale: dict[str, dict[str, int]] = {}
    for row in dataset["contexts"]:
        scale = str(int(row["context"]["scale"]))
        bucket = by_scale.setdefault(
            scale,
            {"context_count": 0, "qd1_target_count": 0},
        )
        bucket["context_count"] += 1
        bucket["qd1_target_count"] += int(
            row["target_policy_id"] == "QD1"
        )
    report = {
        "schema_version": COLLECTION_REPORT_SCHEMA_V1,
        "status": "COMPLETE",
        "selection_manifest_hash": frozen_manifest["manifest_hash"],
        "selection_stream": frozen_manifest["selection_stream"],
        "pair_count": dataset["pair_count"],
        "rejected_pair_count": len(rejected_rows),
        "rejected_context_count": len(
            {
                row["configured_context_id"]
                for row in rejected_rows
            }
        ),
        "requested_context_count": len(resolved_rows),
        "independent_context_count": dataset[
            "independent_context_count"
        ],
        "by_scale": by_scale,
        "dataset_path": str(
            (output_dir / "proof_tail_gate_dataset.json").resolve()
        ),
        "static_scale_rule_audit_path": str(
            (output_dir / "static_scale_rule_audit.json").resolve()
        ),
        "static_scale_rule_promotion_evaluable": bool(
            static_rule_audit["promotion_evaluable"]
        ),
        "static_scale_rule_promotion_passed": bool(
            static_rule_audit["promotion_passed"]
        ),
        "production_policy_changed": False,
        "model_training_allowed": False,
        "note": (
            "Pilot collection validates the paired data path only. "
            "Training remains blocked until the independent multi-instance "
            "context quota and oracle net-benefit gate pass."
        ),
    }
    _write_json(output_dir / "collection_report.json", report)
    print(
        str((output_dir / "collection_report.json").resolve())
    )
    return 0


def _resolve_contexts(
    config: dict[str, Any],
    *,
    config_path: Path,
    partition_by_hash: dict[str, str],
    allowed_partitions: set[str],
) -> list[dict[str, Any]]:
    rows = []
    seen_ids: set[str] = set()
    seen_mathematical_contexts: set[str] = set()
    for raw in config.get("contexts", ()):
        row = dict(raw)
        context_id = str(row.get("context_id") or "")
        if not context_id or context_id in seen_ids:
            raise SystemExit("context IDs must be non-empty and unique")
        seen_ids.add(context_id)
        instance = _resolve_path(
            row.get("instance"), config_path=config_path
        )
        snapshot_path = _resolve_path(
            row.get("snapshot"), config_path=config_path
        )
        snapshot = load_pricing_snapshot(snapshot_path)
        partition = partition_by_hash.get(
            str(snapshot.instance_content_hash)
        )
        if partition is None:
            raise SystemExit(
                f"context is absent from split manifest: {context_id}"
            )
        if partition == "protected_final_test":
            raise SystemExit(
                f"protected final-test context is forbidden: {context_id}"
            )
        if partition not in allowed_partitions:
            raise SystemExit(
                "context partition is outside the allowed development "
                f"scope: {context_id}/{partition}"
            )
        scale = int(row.get("scale") or 0)
        if scale not in {5, 10, 20, 30, 50, 100}:
            raise SystemExit(f"unsupported context scale: {context_id}")
        if snapshot.objective_mode != "official":
            raise SystemExit(
                f"non-official proof-tail context: {context_id}"
            )
        source_role = str(
            row.get("source_role") or "mathematical_context"
        )
        if source_role not in {"exact_control", "mathematical_context"}:
            raise SystemExit(f"invalid source role: {context_id}")
        if (
            source_role == "exact_control"
            and snapshot.pricing_mode != "exact_proof"
        ):
            raise SystemExit(
                f"exact-control context has no exact snapshot: {context_id}"
            )
        identity = stable_payload_hash(
            {
                "instance_content_hash": snapshot.instance_content_hash,
                "objective_mode": snapshot.objective_mode,
                "phase": snapshot.binding.phase,
                "mathematical_dual_hash": (
                    snapshot.binding.mathematical_dual_hash
                ),
                "branch_context_hash": (
                    snapshot.binding.branch_context_hash
                ),
                "full_cut_context_hash": (
                    snapshot.binding.full_cut_context_hash
                ),
                "projected_pricing_cut_context_hash": (
                    snapshot.binding.projected_pricing_cut_context_hash
                ),
                "completion_bound": str(
                    row.get("completion_bound") or "off"
                ),
                "subset_dominance": str(
                    row.get("subset_dominance") or "off"
                ),
                "negative_eps": abs(
                    float(row.get("negative_eps") or 1.0e-6)
                ),
                "dominance_eps": abs(
                    float(row.get("dominance_eps") or 1.0e-12)
                ),
                "resource_eps": abs(
                    float(row.get("resource_eps") or 1.0e-9)
                ),
                "wall_time_limit_sec": float(
                    row.get("wall_time_limit_sec") or 120.0
                ),
                "memory_limit_gb": float(snapshot.memory_limit_gb),
            }
        )
        if identity in seen_mathematical_contexts:
            raise SystemExit(
                "duplicate mathematical proof-tail context in config: "
                f"{context_id}"
            )
        seen_mathematical_contexts.add(identity)
        rows.append(
            {
                "context_id": context_id,
                "pre_outcome_context_identity": identity,
                "scale": scale,
                "instance": str(instance),
                "snapshot": str(snapshot_path),
                "source_role": source_role,
                "completion_bound": str(
                    row.get("completion_bound") or "off"
                ),
                "subset_dominance": str(
                    row.get("subset_dominance") or "off"
                ),
                "wall_time_limit_sec": float(
                    row.get("wall_time_limit_sec") or 120.0
                ),
                "negative_eps": abs(
                    float(row.get("negative_eps") or 1.0e-6)
                ),
                "dominance_eps": abs(
                    float(row.get("dominance_eps") or 1.0e-12)
                ),
                "resource_eps": abs(
                    float(row.get("resource_eps") or 1.0e-9)
                ),
                "selection_reason": str(
                    row.get("selection_reason") or "targeted_pilot"
                ),
                "split_partition": partition,
            }
        )
    return rows


def _run_arm(
    context: dict[str, Any],
    *,
    policy_id: str,
    output: Path,
) -> None:
    command = [
        sys.executable,
        str(REPLAY_SCRIPT),
        "--source-role",
        str(context["source_role"]),
        "--instance",
        str(context["instance"]),
        "--snapshot",
        str(context["snapshot"]),
        "--output",
        str(output),
        "--proof-queue-policy",
        str(policy_id),
        "--completion-bound",
        str(context["completion_bound"]),
        "--subset-dominance",
        str(context["subset_dominance"]),
        "--wall-time-limit-sec",
        str(context["wall_time_limit_sec"]),
        "--negative-eps",
        str(context["negative_eps"]),
        "--dominance-eps",
        str(context["dominance_eps"]),
        "--resource-eps",
        str(context["resource_eps"]),
    ]
    environment = dict(os.environ)
    existing_pythonpath = str(environment.get("PYTHONPATH") or "")
    required = [
        str(PROJECT_ROOT / "src"),
        str(PROJECT_ROOT / "build/native-spprc"),
    ]
    environment["PYTHONPATH"] = os.pathsep.join(
        required + ([existing_pythonpath] if existing_pythonpath else [])
    )
    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )


def _arm_rejection_summary(arm: dict[str, Any]) -> dict[str, Any]:
    telemetry = dict(arm.get("proof_telemetry") or {})
    return {
        "proof_queue_policy_id": str(
            arm.get("proof_queue_policy_id") or ""
        ),
        "engine_status": str(arm.get("engine_status") or ""),
        "search_exhaustive": bool(arm.get("search_exhaustive")),
        "frontier_empty": bool(arm.get("frontier_empty")),
        "labels_dropped": bool(arm.get("labels_dropped")),
        "certificate_blockers": list(
            arm.get("certificate_blockers") or ()
        ),
        "host_timed_out": bool(telemetry.get("host_timed_out")),
        "host_memory_killed": bool(
            telemetry.get("host_memory_killed")
        ),
        "wall_time_seconds": telemetry.get("wall_time_seconds"),
        "total_fresh_process_wall_sec": arm.get(
            "total_fresh_process_wall_sec"
        ),
    }


def _pair_order(
    *,
    selection_salt: str,
    context_id: str,
    replicate_id: str,
) -> tuple[str, str]:
    value = int(
        stable_payload_hash(
            {
                "selection_salt": selection_salt,
                "context_id": context_id,
                "replicate_id": replicate_id,
            }
        )[:8],
        16,
    )
    return (
        ("QC0", "QD1")
        if value % 2 == 0
        else ("QD1", "QC0")
    )


def _resolve_path(value: Any, *, config_path: Path) -> Path:
    path = Path(str(value or ""))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if not path.exists():
        raise SystemExit(f"proof-tail source path does not exist: {path}")
    return path


def _write_or_verify_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous != payload:
            raise SystemExit(
                f"resume artifact differs from frozen payload: {path}"
            )
        return
    _write_json(path, payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
