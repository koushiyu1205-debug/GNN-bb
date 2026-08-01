#!/usr/bin/env python3
"""Freeze the fixed sparse-tail replay suite as a two-head GAT pilot dataset.

The labels in this dataset measure local mathematical discovery headroom only.
They are not end-to-end solve-time labels and therefore cannot authorize
evaluation or deployment.  The instance-disjoint split is derived exclusively
from the registry binding and instance file hash, never from replay outcomes.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_p0v4_sparse_tail_gat_smoke_dataset import (  # noqa: E402
    _history_row,
    _offline_context,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402
from lunar_ice_bpc.guidance.sparse_tail_action import (  # noqa: E402
    SPARSE_TAIL_ACTIONS,
    build_sparse_tail_action_features,
    sparse_tail_feature_schema,
)


DATASET_SCHEMA = "lunar_ice_bpc.sparse_tail_gat_fixed_pilot_dataset.v1"
SUITE_SCHEMA = "lunar_ice_bpc.sparse_tail_replay_suite.v1"
REGISTRY_SCHEMA = "lunar_ice_bpc.sparse_tail_replay_registry.v1"
REPLAY_SCHEMA = "lunar_ice_bpc.p0v4_sparse_tail_deviation_replay.v1"
SPLIT_POLICY = "sha256_registry_binding_and_instance_sha_mod3_v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = build_dataset(
        suite_manifest_path=_resolve(args.suite_manifest),
        output_dir=_resolve(args.output_dir),
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def build_dataset(*, suite_manifest_path: Path, output_dir: Path) -> dict:
    suite_manifest_path = suite_manifest_path.resolve()
    suite = _load_json(suite_manifest_path)
    if suite.get("schema_version") != SUITE_SCHEMA:
        raise SystemExit("unexpected sparse-tail suite schema")
    if suite.get("status") != "COMPLETE":
        raise SystemExit("sparse-tail replay suite is not complete")
    if int(suite.get("failure_count") or 0) != 0:
        raise SystemExit("sparse-tail replay suite contains failures")
    if bool(suite.get("evaluation_authorized")) or bool(
        suite.get("deployment_authorized")
    ):
        raise SystemExit("development replay suite has invalid authority")

    registry_path = Path(str(suite.get("context_registry") or "")).resolve()
    if not registry_path.is_file():
        raise SystemExit("frozen context registry is missing")
    if _sha256(registry_path) != str(
        suite.get("context_registry_sha256") or ""
    ):
        raise SystemExit("frozen context registry hash mismatch")
    registry = _load_json(registry_path)
    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise SystemExit("unexpected sparse-tail registry schema")
    binding_hash = str(registry.get("binding_hash") or "")
    if not binding_hash or binding_hash != str(
        suite.get("context_binding_hash") or ""
    ):
        raise SystemExit("suite and registry binding mismatch")

    contexts = [dict(value) for value in registry.get("contexts") or ()]
    if len(contexts) != int(registry.get("context_count") or -1):
        raise SystemExit("registry context count mismatch")
    if len(contexts) != int(suite.get("context_count") or -1):
        raise SystemExit("suite context count mismatch")
    context_by_id = {
        str(context.get("context_id") or ""): context
        for context in contexts
    }
    if "" in context_by_id or len(context_by_id) != len(contexts):
        raise SystemExit("registry contains duplicate or empty context IDs")

    replay_rows = _index_suite_rows(suite, context_by_id)
    rows = []
    split_instances: dict[str, set[str]] = {
        "train": set(),
        "calibration": set(),
    }
    for context in contexts:
        context_id = str(context["context_id"])
        instance_path = Path(str(context.get("instance") or "")).resolve()
        source_probe_path = Path(
            str(context.get("source_probe") or "")
        ).resolve()
        _verify_source_artifacts(
            context,
            instance_path=instance_path,
            source_probe_path=source_probe_path,
        )
        source_probe = _load_json(source_probe_path)
        history, round_row = _history_row(
            source_probe, int(context["round"])
        )
        offline_context = _offline_context(
            instance_path=instance_path,
            probe=source_probe,
            history=history,
            round_row=round_row,
            source_key={
                "suite_manifest_sha256": _sha256(suite_manifest_path),
                "registry_binding_hash": binding_hash,
                "context_id": context_id,
                "source_probe_sha256": _sha256(source_probe_path),
                "round": int(context["round"]),
                "label_role": "local_discovery_headroom_only",
            },
            runtime_eligible=False,
        )
        features = build_sparse_tail_action_features(offline_context)
        instance_sha = str(context.get("instance_sha256") or "")
        split = split_for_instance(
            binding_hash=binding_hash,
            instance_sha256=instance_sha,
        )
        split_instances[split].add(instance_sha)

        labels = []
        for action in SPARSE_TAIL_ACTIONS:
            labels.append(
                _action_label(
                    context=context,
                    action=str(action),
                    suite_row=replay_rows[(context_id, str(action))],
                )
            )
        rows.append(
            _dataset_row(
                features=features,
                context=context,
                split=split,
                labels=labels,
                suite_manifest_path=suite_manifest_path,
                registry_path=registry_path,
            )
        )

    if split_instances["train"] & split_instances["calibration"]:
        raise SystemExit("instance leakage across train/calibration split")
    if not split_instances["train"] or not split_instances["calibration"]:
        raise SystemExit("deterministic split lacks train or calibration instances")

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / "sparse_tail_gat_fixed_pilot.jsonl"
    dataset_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    positive_action_count = sum(
        sum(int(value) for value in row["beneficial"]) for row in rows
    )
    calibration_positive_action_count = sum(
        sum(int(value) for value in row["beneficial"])
        for row in rows
        if row["split"] == "calibration"
    )
    executable_partial_action_count = sum(
        sum(int(value) for value in row["executable_partial_return"])
        for row in rows
    )
    blockers = [
        "labels_measure_local_discovery_headroom_not_end_to_end_solve_time",
        "all_contexts_are_mathematical_replays_not_runtime_paired_rollouts",
    ]
    if calibration_positive_action_count == 0:
        blockers.append("calibration_split_has_zero_beneficial_actions")
    manifest = {
        "schema_version": DATASET_SCHEMA,
        "status": "FIXED_PILOT_DATASET_SHADOW_ONLY",
        "dataset": str(dataset_path.resolve()),
        "dataset_sha256": _sha256(dataset_path),
        "suite_manifest": str(suite_manifest_path),
        "suite_manifest_sha256": _sha256(suite_manifest_path),
        "context_registry": str(registry_path),
        "context_registry_sha256": _sha256(registry_path),
        "context_binding_hash": binding_hash,
        "feature_schema": sparse_tail_feature_schema(),
        "feature_schema_hash": stable_payload_hash(
            sparse_tail_feature_schema()
        ),
        "label_semantics": "local_discovery_headroom_not_end_to_end",
        "split_policy": SPLIT_POLICY,
        "split_uses_outcomes": False,
        "instance_disjoint_split": True,
        "row_count": len(rows),
        "observed_action_count": len(rows) * len(SPARSE_TAIL_ACTIONS),
        "executable_partial_action_count": executable_partial_action_count,
        "beneficial_action_count": positive_action_count,
        "calibration_beneficial_action_count": (
            calibration_positive_action_count
        ),
        "runtime_eligible_row_count": 0,
        "mathematical_context_only_row_count": len(rows),
        "train_instance_sha256": sorted(split_instances["train"]),
        "calibration_instance_sha256": sorted(
            split_instances["calibration"]
        ),
        "action_ids": list(SPARSE_TAIL_ACTIONS),
        "formal_training_authorized": False,
        "evaluation_authorized": False,
        "deployment_authorized": False,
        "certificate_authority": "none",
        "blockers": blockers,
        "rows": [
            {
                "context_id": row["context_id"],
                "scale": row["scale"],
                "split": row["split"],
                "instance_content_hash": row["instance_content_hash"],
                "instance_sha256": row["instance_sha256"],
                "beneficial": row["beneficial"],
                "executable_partial_return": row[
                    "executable_partial_return"
                ],
                "feature_hash": row["feature_hash"],
            }
            for row in rows
        ],
    }
    manifest_path = output_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def split_for_instance(*, binding_hash: str, instance_sha256: str) -> str:
    if not binding_hash or not instance_sha256:
        raise ValueError("split binding and instance SHA must be non-empty")
    digest = sha256(
        f"{binding_hash}:{instance_sha256}".encode("utf-8")
    ).hexdigest()
    return "calibration" if int(digest, 16) % 3 == 0 else "train"


def _index_suite_rows(
    suite: dict, context_by_id: dict[str, dict]
) -> dict[tuple[str, str], dict]:
    expected = {
        (context_id, str(action))
        for context_id in context_by_id
        for action in SPARSE_TAIL_ACTIONS
    }
    indexed = {}
    for row_value in suite.get("rows") or ():
        row = dict(row_value)
        key = (str(row.get("context_id") or ""), str(row.get("action") or ""))
        if key in indexed:
            raise SystemExit("duplicate suite context/action row")
        indexed[key] = row
    if set(indexed) != expected:
        raise SystemExit("suite does not contain exactly one row per fixed action")
    if int(suite.get("completed_action_count") or -1) != len(expected):
        raise SystemExit("suite completed action count mismatch")
    if int(suite.get("expected_action_count") or -1) != len(expected):
        raise SystemExit("suite expected action count mismatch")
    return indexed


def _verify_source_artifacts(
    context: dict, *, instance_path: Path, source_probe_path: Path
) -> None:
    if not instance_path.is_file() or not source_probe_path.is_file():
        raise SystemExit("fixed pilot source artifact is missing")
    if _sha256(instance_path) != str(context.get("instance_sha256") or ""):
        raise SystemExit("fixed pilot instance SHA mismatch")
    if _sha256(source_probe_path) != str(
        context.get("source_probe_sha256") or ""
    ):
        raise SystemExit("fixed pilot source probe SHA mismatch")


def _action_label(*, context: dict, action: str, suite_row: dict) -> dict:
    if suite_row.get("status") != "COMPLETED":
        raise SystemExit("fixed pilot action was not completed")
    replay_path = Path(str(suite_row.get("replay") or "")).resolve()
    if not replay_path.is_file():
        raise SystemExit("fixed pilot replay is missing")
    if _sha256(replay_path) != str(suite_row.get("replay_sha256") or ""):
        raise SystemExit("fixed pilot replay SHA mismatch")
    replay = _load_json(replay_path)
    if replay.get("schema_version") != REPLAY_SCHEMA:
        raise SystemExit("unexpected sparse-tail replay schema")
    if replay.get("status") != "SAFE_REPLAY_COMPLETE":
        raise SystemExit("sparse-tail replay did not pass safety audit")
    if str(replay.get("action") or "") != action:
        raise SystemExit("sparse-tail replay action mismatch")
    if int(replay.get("source_round") or -1) != int(context["round"]):
        raise SystemExit("sparse-tail replay round mismatch")
    if str(replay.get("source_probe_sha256") or "") != str(
        context.get("source_probe_sha256") or ""
    ):
        raise SystemExit("sparse-tail replay source probe mismatch")
    if str(replay.get("instance_sha256") or "") != str(
        context.get("instance_sha256") or ""
    ):
        raise SystemExit("sparse-tail replay instance mismatch")
    safety = dict(replay.get("safety") or {})
    safety_issues = tuple(str(value) for value in safety.get("issues") or ())
    if safety_issues:
        raise SystemExit(f"sparse-tail replay safety issues: {safety_issues}")
    if safety.get("replay_certificate_authority") != "none":
        raise SystemExit("sparse-tail replay has certificate authority")

    true_negative_count = int(
        (replay.get("reconstruction_audit") or {}).get(
            "true_negative_column_count"
        )
        or suite_row.get("true_negative_column_count")
        or 0
    )
    executable_partial = bool(
        replay.get("engine_status") == "FOUND_NEGATIVE_PARTIAL"
        and replay.get("negative_escape_triggered") is True
        and replay.get("partial_columns_valid") is True
        and int(replay.get("column_count") or 0) > 0
        and true_negative_count > 0
    )
    source_wall = float(context.get("source_proof_wall_sec") or 0.0)
    action_wall = float(replay.get("fresh_process_wall_sec") or 0.0)
    if source_wall <= 0.0 or action_wall < 0.0:
        raise SystemExit("invalid sparse-tail replay wall time")
    if executable_partial:
        delta_time_sec = source_wall - action_wall
    else:
        # A miss cannot certify.  Frozen V5 must still run its official proof,
        # so the sparse action is pure overhead relative to the source round.
        delta_time_sec = -action_wall
    beneficial = bool(executable_partial and delta_time_sec > 0.0)
    return {
        "action": action,
        "beneficial": beneficial,
        "observed": True,
        "positive_relative_gain": (
            delta_time_sec / source_wall if beneficial else 0.0
        ),
        "delta_time_sec": delta_time_sec,
        "relative_time_gain": delta_time_sec / source_wall,
        "memory_adverse_event": bool(
            suite_row.get("memory_adverse_event")
            or replay.get("memory_adverse_event")
            or replay.get("engine_status") == "MEMORY_LIMIT"
        ),
        "executable_partial_return": executable_partial,
        "engine_status": str(replay.get("engine_status") or ""),
        "true_negative_column_count": true_negative_count,
        "replay": str(replay_path),
        "replay_sha256": _sha256(replay_path),
    }


def _dataset_row(
    *,
    features,
    context: dict,
    split: str,
    labels: list[dict],
    suite_manifest_path: Path,
    registry_path: Path,
) -> dict:
    feature_payload = features.payload()
    feature_schema_version = str(feature_payload.pop("schema_version"))
    return {
        "schema_version": DATASET_SCHEMA,
        "feature_schema_version": feature_schema_version,
        "context_id": str(context["context_id"]),
        "split": split,
        "source_role": "mathematical_context_only",
        "label_semantics": "local_discovery_headroom_not_end_to_end",
        "runtime_eligible": False,
        **feature_payload,
        "instance_sha256": str(context["instance_sha256"]),
        "source_state": str(context["source_state"]),
        "source_proof_wall_sec": float(context["source_proof_wall_sec"]),
        "feature_hash": features.feature_hash,
        "beneficial": [bool(label["beneficial"]) for label in labels],
        "observed_mask": [bool(label["observed"]) for label in labels],
        "positive_relative_gain": [
            float(label["positive_relative_gain"]) for label in labels
        ],
        "delta_time_sec": [float(label["delta_time_sec"]) for label in labels],
        "relative_time_gain": [
            float(label["relative_time_gain"]) for label in labels
        ],
        "memory_adverse_event": [
            bool(label["memory_adverse_event"]) for label in labels
        ],
        "executable_partial_return": [
            bool(label["executable_partial_return"]) for label in labels
        ],
        "engine_status": [str(label["engine_status"]) for label in labels],
        "true_negative_column_count": [
            int(label["true_negative_column_count"]) for label in labels
        ],
        "replay_artifacts": [str(label["replay"]) for label in labels],
        "replay_artifact_sha256": [
            str(label["replay_sha256"]) for label in labels
        ],
        "source_artifacts": [
            str(suite_manifest_path),
            str(registry_path),
            str(Path(str(context["source_probe"])).resolve()),
            str(Path(str(context["instance"])).resolve()),
        ],
        "source_artifact_sha256": [
            _sha256(suite_manifest_path),
            _sha256(registry_path),
            str(context["source_probe_sha256"]),
            str(context["instance_sha256"]),
        ],
        "safety_issues": [],
        "certificate_authority": "none",
        "post_action_features_exposed_to_model": False,
    }


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
