#!/usr/bin/env python3
"""Validate matched rollout packages and open or close the GAT training gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from statistics import mean
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402
from lunar_ice_bpc.guidance.one_deviation_oracle import (  # noqa: E402
    audit_one_deviation_oracle,
    materialize_one_deviation_time_labels,
)
from lunar_ice_bpc.guidance.one_deviation_rollout import (  # noqa: E402
    selected_exact_runtime_binding,
)
from lunar_ice_bpc.guidance.route_admission import (  # noqa: E402
    fixed_exact_admission_batch_size,
    validate_route_admission_snapshot,
    validate_route_opportunity_census_binding,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollout-root", required=True)
    parser.add_argument("--opportunity-census", required=True)
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    rollout_root = _resolve(args.rollout_root)
    census_path = _resolve(args.opportunity_census)
    fixed_k_path = _resolve(args.fixed_k_selection)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    census = _load_json(census_path)
    fixed_k = _load_json(fixed_k_path)
    if not bool(census.get("expensive_oracle_authorized")):
        raise SystemExit("opportunity census did not authorize rollouts")
    if str(fixed_k.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("oracle requires a frozen fixed E_K")
    fixed_k_hash = _sha256(fixed_k_path)
    census_sha256 = _sha256(census_path)
    try:
        census_binding_hash = (
            validate_route_opportunity_census_binding(
                census,
                fixed_k_selection_sha256=fixed_k_hash,
            )
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    eligible_snapshot_index = _eligible_snapshot_index(census)
    context_rows = []
    label_rows = []
    training_rows = []
    rejected = []
    seen_context_hashes: set[str] = set()
    package_paths = sorted(
        rollout_root.rglob("one_deviation_rollout_package.json")
    )
    if not package_paths:
        raise SystemExit(
            "no one_deviation_rollout_package.json found under rollout root"
        )
    for path in package_paths:
        try:
            package = _load_json(path)
            if (
                str(package.get("schema_version") or "")
                != "lunar_ice_bpc.one_deviation_rollout_package.v1"
            ):
                raise ValueError("rollout package schema mismatch")
            if str(package.get("opportunity_census_sha256")) != (
                census_sha256
            ):
                raise ValueError(
                    "rollout package/opportunity census hash mismatch"
                )
            if str(package.get("census_content_binding_hash")) != (
                census_binding_hash
            ):
                raise ValueError(
                    "rollout package census content binding mismatch"
                )
            if str(package.get("fixed_k_selection_sha256")) != (
                fixed_k_hash
            ):
                raise ValueError("rollout package/fixed E_K mismatch")
            context = dict(package["context"])
            expected_exact_runtime = selected_exact_runtime_binding(
                fixed_k,
                scale=int(context["scale"]),
            )
            if dict(package.get("exact_runtime_binding") or {}) != (
                expected_exact_runtime
            ):
                raise ValueError(
                    "rollout package selected Exact runtime mismatch"
                )
            if str(package.get("exact_runtime_binding_hash") or "") != str(
                expected_exact_runtime["runtime_binding_hash"]
            ):
                raise ValueError(
                    "rollout package selected Exact runtime hash mismatch"
                )
            rollouts = tuple(package["rollouts"])
            context_hash = str(context.get("context_hash") or "")
            if not context_hash:
                raise ValueError("rollout package lacks a context hash")
            if context_hash in seen_context_hashes:
                raise ValueError("duplicate rollout context package")
            seen_context_hashes.add(context_hash)
            if (
                str(context["state_hashes"]["fixed_k_selection_hash"])
                != fixed_k_hash
            ):
                raise ValueError("rollout/fixed E_K hash mismatch")
            if int(context["batch_size"]) != (
                fixed_exact_admission_batch_size(
                    fixed_k, scale=int(context["scale"])
                )
            ):
                raise ValueError("rollout/fixed E_K batch mismatch")
            source_snapshot_path = Path(
                str(package["source_snapshot"])
            ).resolve()
            if _sha256(source_snapshot_path) != str(
                package["source_snapshot_sha256"]
            ):
                raise ValueError("rollout source snapshot hash drift")
            source_snapshot = validate_route_admission_snapshot(
                _load_json(source_snapshot_path)
            )
            authorized_snapshot = eligible_snapshot_index.get(
                str(source_snapshot["snapshot_hash"])
            )
            if authorized_snapshot is None:
                raise ValueError(
                    "rollout source snapshot is not census-authorized"
                )
            if str(authorized_snapshot["source_snapshot_sha256"]) != str(
                package["source_snapshot_sha256"]
            ):
                raise ValueError(
                    "rollout source snapshot differs from census"
                )
            if (
                str(context["instance_content_hash"])
                != str(source_snapshot["instance_content_hash"])
                or int(context["scale"]) != int(source_snapshot["scale"])
            ):
                raise ValueError(
                    "rollout context differs from source snapshot"
                )
            selected_manifest_path = Path(
                str(package["selected_action_manifest"])
            ).resolve()
            if _sha256(selected_manifest_path) != str(
                package["selected_action_manifest_sha256"]
            ):
                raise ValueError(
                    "selected action manifest hash drift"
                )
            selected_manifest = _load_json(selected_manifest_path)
            selected_manifest_hash = stable_payload_hash(
                selected_manifest
            )
            if (
                selected_manifest_hash
                != str(package["selected_action_manifest_hash"])
                or selected_manifest_hash
                != str(context["action_manifest_hash"])
            ):
                raise ValueError(
                    "selected action manifest/context binding mismatch"
                )
            selected_action_ids = [
                str(value["action_id"])
                for value in selected_manifest.get("actions", ())
            ]
            if selected_action_ids != [
                str(value)
                for value in package.get("selected_action_ids", ())
            ]:
                raise ValueError(
                    "selected action identity binding mismatch"
                )
            redline_count = sum(
                int(package.get(key) or 0)
                for key in (
                    "correctness_redline_count",
                    "hash_redline_count",
                    "leakage_redline_count",
                    "candidate_filter_redline_count",
                    "certificate_redline_count",
                )
            )
            labels = materialize_one_deviation_time_labels(
                context, rollouts
            )
            control_times = [
                float(row["milestone_time_sec"])
                for row in rollouts
                if str(row.get("action_kind")) == "noop"
                and not bool(row.get("right_censored"))
            ]
            observed_relative_gains = [
                float(row["relative_time_gain"])
                for row in labels["labels"]
                if row["relative_time_gain"] is not None
                and int(row["observed_replicate_count"]) == 3
                and int(row["right_censored_replicate_count"]) == 0
                and not bool(row.get("memory_adverse_event"))
            ]
            if not control_times:
                raise ValueError("oracle package lacks observed P0 control")
            oracle_gain_fraction = max(
                0.0,
                max(observed_relative_gains, default=0.0),
            )
            deterministic_action_id = str(
                package.get(
                    "p0v4_deterministic_score_control_action_id"
                )
                or ""
            )
            deterministic_label = next(
                (
                    row
                    for row in labels["labels"]
                    if str(row["action_id"])
                    == deterministic_action_id
                ),
                None,
            )
            deterministic_gain_fraction = (
                0.0
                if deterministic_label is None
                or deterministic_label.get("relative_time_gain") is None
                or int(
                    deterministic_label["observed_replicate_count"]
                )
                != 3
                or int(
                    deterministic_label[
                        "right_censored_replicate_count"
                    ]
                )
                != 0
                or bool(
                    deterministic_label.get("memory_adverse_event")
                )
                else float(deterministic_label["relative_time_gain"])
            )
            context_rows.append(
                {
                    "scale": int(context["scale"]),
                    "instance_content_hash": str(
                        context["instance_content_hash"]
                    ),
                    "oracle_gain_fraction": oracle_gain_fraction,
                    "p0v4_deterministic_score_gain_fraction": (
                        deterministic_gain_fraction
                    ),
                    "redline_count": redline_count,
                }
            )
            label_rows.append(
                {
                    "source": str(path.resolve()),
                    "source_sha256": _sha256(path),
                    "context": context,
                    "oracle_gain_fraction": oracle_gain_fraction,
                    **labels,
                }
            )
            if package.get("training_row") is None:
                raise ValueError(
                    "rollout package lacks pre-action training features"
                )
            expected_split = str(
                authorized_snapshot["instance_split"]
            )
            training_rows.append(
                _bind_training_row(
                    dict(package["training_row"]),
                    labels["labels"],
                    context_hash=context_hash,
                    fixed_k_hash=fixed_k_hash,
                    state_hashes=dict(
                        context["state_hashes"]
                    ),
                    expected_instance_hash=str(
                        context["instance_content_hash"]
                    ),
                    expected_scale=int(context["scale"]),
                    expected_split=expected_split,
                    exact_runtime_binding=expected_exact_runtime,
                )
            )
        except Exception as exc:
            rejected.append(
                {"path": str(path.resolve()), "reason": repr(exc)}
            )
    gate = audit_one_deviation_oracle(context_rows)
    gate["pilot_oracle_gate_pass"] = bool(gate["gate_pass"])
    final_targets = {30: 100, 50: 60}
    final_instance_target = 10
    final_scale_reports = {}
    final_data_gate = True
    for scale, target in final_targets.items():
        scale_rows = [
            row for row in context_rows if int(row["scale"]) == scale
        ]
        instance_count = len(
            {
                str(row["instance_content_hash"])
                for row in scale_rows
            }
        )
        scale_pass = bool(
            len(scale_rows) >= target
            and instance_count >= final_instance_target
        )
        final_data_gate = final_data_gate and scale_pass
        final_scale_reports[str(scale)] = {
            "context_count": len(scale_rows),
            "required_context_count": target,
            "instance_count": instance_count,
            "required_instance_count": final_instance_target,
            "gate_pass": scale_pass,
        }
    gate["final_training_data_gate"] = {
        "gate_pass": final_data_gate,
        "scales": final_scale_reports,
    }
    gate["pilot_expansion_authorized"] = bool(gate["gate_pass"])
    gate["gat_training_authorized"] = bool(
        gate["gate_pass"] and final_data_gate
    )
    gate["perfect_oracle_mean_gain_fraction"] = (
        0.0
        if not context_rows
        else mean(
            [
                float(row["oracle_gain_fraction"])
                for row in context_rows
            ]
        )
    )
    gate["p0v4_deterministic_score_mean_gain_fraction"] = (
        0.0
        if not context_rows
        else mean(
            [
                float(
                    row[
                        "p0v4_deterministic_score_gain_fraction"
                    ]
                )
                for row in context_rows
            ]
        )
    )
    gate["package_validation_redline_count"] = len(rejected)
    if rejected:
        gate["gate_pass"] = False
        gate["pilot_oracle_gate_pass"] = False
        gate["pilot_expansion_authorized"] = False
        gate["gat_training_authorized"] = False
    gate.update(
        {
            "opportunity_census": str(census_path),
            "opportunity_census_sha256": census_sha256,
            "census_content_binding_hash": census_binding_hash,
            "fixed_k_selection": str(fixed_k_path),
            "fixed_k_selection_sha256": fixed_k_hash,
            "valid_context_count": len(context_rows),
            "rejected_packages": rejected,
            "rollout_root": str(rollout_root),
        }
    )
    _write_json(output / "oracle_gate.json", gate)
    _write_jsonl(output / "oracle_labels.jsonl", label_rows)
    _write_jsonl(output / "one_deviation_dataset.jsonl", training_rows)
    print(json.dumps(gate, indent=2, sort_keys=True))
    return 0 if bool(gate["pilot_expansion_authorized"]) else 3


def _bind_training_row(
    row: dict,
    labels: list[dict],
    *,
    context_hash: str,
    fixed_k_hash: str,
    state_hashes: dict,
    expected_instance_hash: str,
    expected_scale: int,
    expected_split: str,
    exact_runtime_binding: dict,
) -> dict:
    if str(row.get("instance_content_hash") or "") != str(
        expected_instance_hash
    ):
        raise ValueError("training row instance binding mismatch")
    if int(row.get("scale") or 0) != int(expected_scale):
        raise ValueError("training row scale binding mismatch")
    if str(row.get("split") or "") != str(expected_split):
        raise ValueError("training row pre-outcome split mismatch")
    runtime = dict(exact_runtime_binding)
    runtime_hash = str(runtime.get("runtime_binding_hash") or "")
    unsigned_runtime = {
        key: value
        for key, value in runtime.items()
        if key != "runtime_binding_hash"
    }
    if (
        not runtime_hash
        or stable_payload_hash(unsigned_runtime) != runtime_hash
        or int(runtime.get("scale") or 0) != int(expected_scale)
    ):
        raise ValueError("training row exact runtime binding is invalid")
    action_ids = tuple(str(value) for value in row["action_ids"])
    by_action = {str(value["action_id"]): value for value in labels}
    if set(action_ids) != set(by_action):
        raise ValueError("training candidates differ from rollout actions")
    ordered = [by_action[action_id] for action_id in action_ids]
    feature_payload = {
        key: row[key]
        for key in (
            "node_features",
            "edge_index",
            "edge_features",
            "candidate_task_masks",
            "candidate_context",
            "global_context",
        )
    }
    row.update(
        {
            "context_hash": str(context_hash),
            "beneficial": [value["beneficial"] is True for value in ordered],
            "observed_mask": [
                bool(value["probability_head_mask"]) for value in ordered
            ],
            "positive_gain_sec": [
                max(0.0, float(value["delta_time_sec"] or 0.0))
                for value in ordered
            ],
            "positive_relative_gain": [
                max(0.0, float(value["relative_time_gain"] or 0.0))
                for value in ordered
            ],
            "delta_time_sec": [
                float(value["delta_time_sec"] or 0.0)
                for value in ordered
            ],
            "relative_time_gain": [
                float(value["relative_time_gain"] or 0.0)
                for value in ordered
            ],
            "right_censored_positive_mask": [
                bool(value["survival_mask"]) for value in ordered
            ],
            "memory_adverse_event": [
                bool(value["memory_adverse_event"]) for value in ordered
            ],
            "censor_lower_bound_sec": [
                float(value.get("censor_lower_bound_sec") or 0.0)
                for value in ordered
            ],
            "censor_lower_bound_relative": [
                float(
                    value.get("censor_lower_bound_relative") or 0.0
                )
                for value in ordered
            ],
            "fixed_k_selection_hash": fixed_k_hash,
            "exact_binary_hash": str(
                state_hashes["exact_binary_hash"]
            ),
            "exact_config_hash": str(
                state_hashes["exact_config_hash"]
            ),
            "exact_engine_hash": str(
                state_hashes["exact_engine_hash"]
            ),
            "exact_runtime_binding": runtime,
            "exact_runtime_binding_hash": runtime_hash,
            "pre_action_feature_hash": stable_payload_hash(
                feature_payload
            ),
            "post_action_features_exposed_to_model": False,
            "certificate_paths_mutated": False,
        }
    )
    return row


def _eligible_snapshot_index(census: dict) -> dict[str, dict]:
    result = {}
    split_by_hash = dict(
        census.get("instance_split_by_hash") or {}
    )
    for value in census.get("eligible_snapshots", ()):
        row = dict(value)
        snapshot_hash = str(row.get("snapshot_hash") or "")
        instance_hash = str(row.get("instance_content_hash") or "")
        split = str(row.get("instance_split") or "")
        if (
            not snapshot_hash
            or not instance_hash
            or not str(row.get("source_snapshot_sha256") or "")
            or split not in {"train", "calibration"}
            or split != str(split_by_hash.get(instance_hash) or "")
        ):
            raise SystemExit(
                "opportunity census has an invalid snapshot index"
            )
        if snapshot_hash in result:
            raise SystemExit(
                "opportunity census has duplicate snapshot hashes"
            )
        result[snapshot_hash] = row
    if len(result) != int(census.get("eligible_snapshot_count") or 0):
        raise SystemExit(
            "opportunity census snapshot index count mismatch"
        )
    return result


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
