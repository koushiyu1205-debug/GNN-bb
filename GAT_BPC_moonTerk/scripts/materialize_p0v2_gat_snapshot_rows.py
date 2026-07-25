#!/usr/bin/env python3
"""Materialize masked pricing-ranking rows from immutable replay snapshots."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from math import log1p
from pathlib import Path

from lunar_ice_bpc.exact.bpc.guidance.replay import load_pricing_snapshot
from lunar_ice_bpc.exact.bpc.pricing.backends import BackendPricingRequest
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.tensorization import (
    NODE_STATIC_FEATURES,
    build_static_graph_features,
    dynamic_node_features,
    encode_queue_policy_id,
)
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
    materialize_counterfactual_targets,
    pre_action_feature_hash,
    validate_counterfactual_trajectory_record,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--harvest-row-dir", default="")
    parser.add_argument(
        "--counterfactual-records-jsonl",
        action="append",
        default=[],
        help=(
            "Repeat for independently collected scale/kind intervention "
            "files. Duplicate context-kind records are rejected."
        ),
    )
    parser.add_argument(
        "--training-objective",
        choices=(
            COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
            "legacy_graded_listwise",
        ),
        default=COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
    )
    parser.add_argument(
        "--static-cache-dir",
        default="data/gat_p0v2/static_tensor_cache",
    )
    parser.add_argument(
        "--partition",
        choices=("development", "calibration"),
        default="development",
    )
    parser.add_argument("--output-jsonl", required=True)
    args = parser.parse_args()
    development_manifest = json.loads(
        Path(args.development_manifest).read_text(encoding="utf-8")
    )
    instance_paths = {
        str(row["instance_content_hash"]): Path(row["path"])
        for row in development_manifest.get("instances", ())
    }
    split_manifest = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((split_manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    selected_hashes = {
        str(row["instance_content_hash"])
        for row in split_manifest.get(args.partition, ())
    }
    output = Path(args.output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    static_cache_dir = Path(args.static_cache_dir)
    static_cache_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped_unobserved = 0
    skipped_non_development = 0
    seen_contexts = set()
    static_payloads: dict[str, dict] = {}
    data_by_hash = {}
    counterfactual_records = _load_counterfactual_records(
        tuple(
            Path(value)
            for value in args.counterfactual_records_jsonl
            if str(value).strip()
        )
    )
    if (
        args.partition == "development"
        and args.training_objective
        == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
        and not counterfactual_records
    ):
        raise SystemExit(
            "counterfactual trajectory training requires "
            "--counterfactual-records-jsonl"
        )
    skipped_missing_counterfactual = 0
    with output.open("w", encoding="utf-8") as handle:
        for snapshot_path in sorted(Path(args.snapshot_dir).rglob("*.json")):
            snapshot = load_pricing_snapshot(snapshot_path)
            instance_path = instance_paths.get(snapshot.instance_content_hash)
            if (
                instance_path is None
                or snapshot.instance_content_hash not in selected_hashes
            ):
                skipped_non_development += 1
                continue
            context_key = (
                snapshot.instance_content_hash,
                snapshot.binding.binding_hash,
            )
            if context_key in seen_contexts:
                continue
            seen_contexts.add(context_key)
            data = load_lunar_ice_data(
                json.loads(instance_path.read_text(encoding="utf-8"))
            )
            data_by_hash[data.instance_content_hash] = data
            request = BackendPricingRequest(
                data=data,
                true_duals=JourneyDuals(
                    cover=dict(snapshot.true_duals.get("cover") or {}),
                    fleet_limit=_optional_float_default(
                        snapshot.true_duals.get("fleet_limit"), 0.0
                    ),
                    cuts=dict(snapshot.true_duals.get("cuts") or {}),
                ),
                mode=snapshot.pricing_mode,
                objective_mode=snapshot.objective_mode,
                branch_context=branch_context_from_payload(
                    snapshot.branch_context
                ),
                cut_context=cut_context_from_payload(
                    snapshot.full_cut_context
                ),
                wall_time_limit_sec=snapshot.wall_time_budget_sec,
                memory_limit_gb=snapshot.memory_limit_gb,
                instance_hash=snapshot.binding.instance_hash,
                config_hash=snapshot.binding.config_hash,
                engine_hash=snapshot.binding.engine_hash,
                dual_binding_hash=snapshot.binding.mathematical_dual_hash,
                cut_lineage_hash=snapshot.binding.cut_lineage_hash,
                live_cut_policy_hash=snapshot.binding.live_cut_policy_hash,
                rmp_iteration_id=snapshot.binding.rmp_iteration_id,
                separator_policy_version=(
                    snapshot.binding.separator_policy_version
                ),
            )
            if (
                args.partition == "development"
                and args.training_objective
                == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            ):
                try:
                    model_budget = _counterfactual_model_budget(
                        {
                            "instance_content_hash": (
                                snapshot.instance_content_hash
                            ),
                            "rmp_context_hash": (
                                snapshot.binding.binding_hash
                            ),
                        },
                        records=counterfactual_records,
                        candidate_kinds=("task", "arc"),
                    )
                except KeyError:
                    skipped_missing_counterfactual += 1
                    continue
                request = replace(
                    request, wall_time_limit_sec=model_budget
                )
            static = build_static_graph_features(data)
            dynamic = dynamic_node_features(request)
            static_payload = _ensure_static_sidecar(
                static,
                cache_dir=static_cache_dir,
                existing=static_payloads,
            )
            by_id = {
                str(row["candidate_id"]): row
                for row in snapshot.candidate_rows
            }
            task_rows = [by_id[task_id] for task_id in data.task_ids]
            arc_rows = [
                by_id[candidate_id]
                for candidate_id in static.arc_candidate_ids
            ]
            task_mask = [
                bool(row.get("training_observed")) for row in task_rows
            ]
            arc_mask = [
                bool(row.get("training_observed")) for row in arc_rows
            ]
            if (
                args.partition == "development"
                and sum(task_mask) < 2
                and sum(arc_mask) < 2
            ):
                skipped_unobserved += 1
                continue
            row = {
                "schema_version": (
                    "lunar_ice_bpc.gat_pricing_training_row.v1"
                ),
                "head": (
                    "exact_pricing"
                    if args.partition == "development"
                    else "ood"
                ),
                "scale": data.scale,
                "instance_content_hash": data.instance_content_hash,
                "node_phase": snapshot.binding.phase,
                "rmp_context_hash": snapshot.binding.binding_hash,
                "candidate_id": "context",
                "snapshot_hash": snapshot.snapshot_hash,
                "censored": snapshot.censored,
                "static_tensor_cache_key": data.instance_content_hash,
                "static_tensor_cache_hash": static_payload[
                    "static_tensor_cache_hash"
                ],
                "dynamic_node_features": [
                    list(values) for values in dynamic
                ],
                "task_candidate_ids": list(data.task_ids),
                "arc_candidate_ids": list(static.arc_candidate_ids),
                "task_grades": [
                    float(row.get("training_grade") or 0.0)
                    for row in task_rows
                ],
                "task_observed_mask": task_mask,
                "arc_grades": [
                    float(row.get("training_grade") or 0.0)
                    for row in arc_rows
                ],
                "arc_observed_mask": arc_mask,
                "resource_context": [
                    log1p(
                        max(0.0, snapshot.memory_limit_gb) * (1024.0**3)
                    ),
                    log1p(
                        0.0
                        if snapshot.wall_time_budget_sec is None
                        else max(0.0, snapshot.wall_time_budget_sec)
                    ),
                    1.0 if snapshot.pricing_mode == "exact_proof" else 0.0,
                    encode_queue_policy_id(snapshot.queue_policy_id),
                ],
            }
            if (
                args.partition == "development"
                and args.training_objective
                == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            ):
                model_budget = _counterfactual_model_budget(
                    row,
                    records=counterfactual_records,
                    candidate_kinds=("task", "arc"),
                )
                row["resource_context"][1] = log1p(model_budget)
            row["pre_action_feature_hash"] = pre_action_feature_hash(
                binding_hash=snapshot.binding.binding_hash,
                static_tensor_cache_hash=static_payload[
                    "static_tensor_cache_hash"
                ],
                dynamic_node_features=row["dynamic_node_features"],
                resource_context=row["resource_context"],
            )
            if (
                args.partition == "development"
                and args.training_objective
                == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            ):
                try:
                    row = _attach_counterfactual_targets(
                        row,
                        records=counterfactual_records,
                        candidate_kinds=("task", "arc"),
                    )
                except KeyError:
                    skipped_missing_counterfactual += 1
                    continue
            elif args.partition == "development":
                row["training_objective"] = "legacy_graded_listwise"
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )
            written += 1
        if args.harvest_row_dir and args.partition == "development":
            for row_path in sorted(
                Path(args.harvest_row_dir).rglob("*.json")
            ):
                row = json.loads(row_path.read_text(encoding="utf-8"))
                row = _apply_pricing_grade_contract(row)
                content_hash = str(row["instance_content_hash"])
                if content_hash not in selected_hashes:
                    skipped_non_development += 1
                    continue
                context_key = (
                    content_hash,
                    str(row["rmp_context_hash"]),
                    str(row["head"]),
                )
                if context_key in seen_contexts:
                    continue
                seen_contexts.add(context_key)
                data = data_by_hash.get(content_hash)
                if data is None:
                    instance_path = instance_paths.get(content_hash)
                    if instance_path is None:
                        raise ValueError(
                            f"instance path missing for {content_hash}"
                        )
                    data = load_lunar_ice_data(
                        json.loads(
                            instance_path.read_text(encoding="utf-8")
                        )
                    )
                    data_by_hash[content_hash] = data
                static_payload = _ensure_static_sidecar(
                    build_static_graph_features(data),
                    cache_dir=static_cache_dir,
                    existing=static_payloads,
                )
                row = _compact_materialized_row(
                    row, static_payload=static_payload
                )
                row.setdefault(
                    "harvest_candidate_ids",
                    [
                        f"harvest:legacy-index:{index}"
                        for index, _ in enumerate(
                            row.get("harvest_grades", ())
                        )
                    ],
                )
                if (
                    args.training_objective
                    == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                ):
                    try:
                        model_budget = _counterfactual_model_budget(
                            row,
                            records=counterfactual_records,
                            candidate_kinds=("harvest",),
                        )
                    except KeyError:
                        skipped_missing_counterfactual += 1
                        continue
                    row["resource_context"][1] = log1p(model_budget)
                row["pre_action_feature_hash"] = pre_action_feature_hash(
                    binding_hash=str(row["rmp_context_hash"]),
                    static_tensor_cache_hash=static_payload[
                        "static_tensor_cache_hash"
                    ],
                    dynamic_node_features=row[
                        "dynamic_node_features"
                    ],
                    resource_context=row["resource_context"],
                )
                if (
                    args.training_objective
                    == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                ):
                    try:
                        row = _attach_counterfactual_targets(
                            row,
                            records=counterfactual_records,
                            candidate_kinds=("harvest",),
                        )
                    except KeyError:
                        skipped_missing_counterfactual += 1
                        continue
                else:
                    row["training_objective"] = (
                        "legacy_graded_listwise"
                    )
                handle.write(
                    json.dumps(row, ensure_ascii=False, sort_keys=True)
                    + "\n"
                )
                written += 1
    report = {
        "schema_version": (
            "lunar_ice_bpc.gat_snapshot_materialization.v2"
        ),
        "snapshot_dir": str(Path(args.snapshot_dir).resolve()),
        "output_jsonl": str(output.resolve()),
        "split_manifest_hash": split_manifest.get("manifest_hash"),
        "partition": args.partition,
        "written_context_count": written,
        "skipped_unobserved_context_count": skipped_unobserved,
        "skipped_non_development_count": skipped_non_development,
        "skipped_missing_counterfactual_count": (
            skipped_missing_counterfactual
        ),
        "training_objective": str(args.training_objective),
        "counterfactual_record_count": len(counterfactual_records),
        "unexplored_candidates_used_as_negative": False,
        "compact_static_tensor_cache": True,
        "static_tensor_cache_dir": str(static_cache_dir.resolve()),
        "static_tensor_cache_entry_count": len(static_payloads),
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _load_counterfactual_records(
    paths: tuple[Path, ...],
) -> dict[tuple[str, str, str], dict]:
    if not paths:
        return {}
    indexed: dict[tuple[str, str, str], dict] = {}
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = validate_counterfactual_trajectory_record(
                        json.loads(line)
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid counterfactual row "
                        f"{path}:{line_number}: {exc}"
                    ) from exc
                key = (
                    str(row["instance_content_hash"]),
                    str(row["rmp_context_hash"]),
                    str(row["candidate_kind"]),
                )
                if key in indexed:
                    raise ValueError(
                        "duplicate counterfactual context/candidate-kind "
                        f"record: {key}"
                    )
                indexed[key] = row
    return indexed


def _attach_counterfactual_targets(
    row: dict,
    *,
    records: dict[tuple[str, str, str], dict],
    candidate_kinds: tuple[str, ...],
) -> dict:
    materialized = dict(row)
    for kind in candidate_kinds:
        key = (
            str(materialized["instance_content_hash"]),
            str(materialized["rmp_context_hash"]),
            kind,
        )
        counterfactual = records[key]
        if str(counterfactual["pre_action_feature_hash"]) != str(
            materialized["pre_action_feature_hash"]
        ):
            raise ValueError(
                f"{kind} counterfactual pre-action feature hash mismatch"
            )
        candidate_ids = materialized[f"{kind}_candidate_ids"]
        targets = materialize_counterfactual_targets(
            counterfactual,
            candidate_ids=candidate_ids,
        )
        for target_key, value in targets.items():
            if target_key in {
                "training_objective",
                "unexplored_candidates_used_as_negative",
                "p0_control_used_as_model_candidate",
                "post_action_features_exposed_to_model",
            }:
                previous = materialized.get(target_key)
                if previous is not None and previous != value:
                    raise ValueError(
                        f"counterfactual target contract mismatch: {target_key}"
                    )
                materialized[target_key] = value
            else:
                materialized[f"{kind}_{target_key}"] = value
    return materialized


def _counterfactual_model_budget(
    row: dict,
    *,
    records: dict[tuple[str, str, str], dict],
    candidate_kinds: tuple[str, ...],
) -> float:
    values = []
    for kind in candidate_kinds:
        record = records[
            (
                str(row["instance_content_hash"]),
                str(row["rmp_context_hash"]),
                kind,
            )
        ]
        value = float(
            record.get("model_wall_time_budget_sec")
            or record["budget_sec"]
        )
        if value <= 0.0:
            raise ValueError("counterfactual model budget must be positive")
        values.append(value)
    if any(abs(value - values[0]) > 1.0e-12 for value in values[1:]):
        raise ValueError(
            "task/arc counterfactual model budgets must match"
        )
    return values[0]


def _optional_float_default(value, default: float) -> float:
    return float(default) if value is None else float(value)


def _ensure_static_sidecar(static, *, cache_dir: Path, existing: dict) -> dict:
    content_hash = str(static.instance_content_hash)
    cached = existing.get(content_hash)
    if cached is not None:
        return cached
    payload = {
        "schema_version": "lunar_ice_bpc.gat_static_tensor_sidecar.v1",
        "instance_content_hash": content_hash,
        "feature_schema_version": str(static.schema_version),
        "node_static_features": [
            list(values) for values in static.node_features
        ],
        "edge_features": [
            list(values) for values in static.arc_features
        ],
        "edge_index": [
            list(static.arc_sources),
            list(static.arc_targets),
        ],
        "task_node_indices": list(range(1, len(static.node_ids))),
    }
    payload["static_tensor_cache_hash"] = stable_payload_hash(payload)
    target = cache_dir / f"{content_hash}.json"
    if target.exists():
        observed = json.loads(target.read_text(encoding="utf-8"))
        if observed != payload:
            raise ValueError(
                f"stale static tensor sidecar rejected for {content_hash}"
            )
    else:
        target.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
    existing[content_hash] = payload
    return payload


def _compact_materialized_row(row: dict, *, static_payload: dict) -> dict:
    compact = dict(row)
    raw_node = list(compact.pop("node_features"))
    static_node = list(static_payload["node_static_features"])
    if len(raw_node) != len(static_node):
        raise ValueError("static/dynamic node count mismatch")
    static_width = len(NODE_STATIC_FEATURES)
    dynamic = []
    for raw_values, static_values in zip(
        raw_node, static_node, strict=True
    ):
        if len(raw_values) < static_width:
            raise ValueError("node feature width is smaller than static schema")
        if any(
            abs(float(left) - float(right)) > 1.0e-12
            for left, right in zip(
                raw_values[:static_width],
                static_values,
                strict=True,
            )
        ):
            raise ValueError("stale static tensor payload rejected")
        dynamic.append(
            [float(value) for value in raw_values[static_width:]]
        )
    compact.pop("edge_features", None)
    compact.pop("edge_index", None)
    compact.pop("task_node_indices", None)
    compact.update(
        {
            "static_tensor_cache_key": str(
                static_payload["instance_content_hash"]
            ),
            "static_tensor_cache_hash": str(
                static_payload["static_tensor_cache_hash"]
            ),
            "dynamic_node_features": dynamic,
        }
    )
    return compact


def _apply_pricing_grade_contract(row: dict) -> dict:
    """Upgrade raw observations to the frozen graded-ranking contract.

    The exact collector records factual addability/support flags.  Translating
    those observations into learning grades belongs here, outside the exact
    engine identity.  Optional hidden-negative masks are produced only by
    paired offline replay; absent masks never fabricate labels.
    """

    materialized = dict(row)
    if str(materialized.get("head") or "") == "harvest":
        grades = [
            float(value) for value in materialized.get("harvest_grades", ())
        ]
        contexts = list(materialized.get("harvest_context") or ())
        if len(grades) != len(contexts):
            raise ValueError("harvest grade/context length mismatch")
        for index, context in enumerate(contexts):
            would_change_active_support = (
                len(context) > 1 and float(context[1]) > 0.5
            )
            # The raw factual grade already says whether the candidate is
            # addable.  Context position 2 was ``would_enter_master`` in v1
            # and is ``is_new_task_set`` in v2, so it must not participate in
            # the useful-negative grade translation.
            if grades[index] >= 3.0 and would_change_active_support:
                grades[index] = 4.0
        materialized["harvest_grades"] = grades
        hidden_key = "harvest_hidden_negative_mask"
        grade_key = "harvest_grades"
    elif str(materialized.get("head") or "") == "exact_pricing":
        for prefix in ("task", "arc"):
            grades = [
                float(value)
                for value in materialized.get(f"{prefix}_grades", ())
            ]
            hidden = list(
                materialized.get(f"{prefix}_hidden_negative_mask") or ()
            )
            if hidden:
                if len(hidden) != len(grades):
                    raise ValueError(
                        f"{prefix} hidden-negative mask length mismatch"
                    )
                materialized[f"{prefix}_grades"] = [
                    min(4.0, grade + (1.0 if bool(flag) else 0.0))
                    for grade, flag in zip(grades, hidden, strict=True)
                ]
        return materialized
    else:
        return materialized

    hidden = list(materialized.get(hidden_key) or ())
    if hidden:
        grades = [
            float(value) for value in materialized.get(grade_key, ())
        ]
        if len(hidden) != len(grades):
            raise ValueError("harvest hidden-negative mask length mismatch")
        materialized[grade_key] = [
            min(4.0, grade + (1.0 if bool(flag) else 0.0))
            for grade, flag in zip(grades, hidden, strict=True)
        ]
    return materialized


if __name__ == "__main__":
    raise SystemExit(main())
