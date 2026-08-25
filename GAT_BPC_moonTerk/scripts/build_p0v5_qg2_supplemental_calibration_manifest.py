#!/usr/bin/env python3
"""Build a leakage-safe supplemental QG2 calibration context manifest.

The bounded Oracle may provide enough action-reachable supervision to fit the
three model classes while its instance-level 20% calibration partition still
contains fewer than the 52 independent contexts required by the declared
one-sided harmful-rate gate.  This read-only builder fills that *evaluation*
shortfall from the already frozen snapshot index.  It never adds a context to
model training and never starts Native.

Instances already present in the trainer split retain their frozen assignment.
Previously unseen instances receive a deterministic 60/20/20 assignment from
their content hash.  Only calibration and heldout assignments are emitted.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SPLIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_instance_split.v1"
INDEX_SCHEMAS = {
    "lunar_ice_bpc.p0v5_qg2_fallback_snapshot_index.v1",
    "lunar_ice_bpc.p0v5_qg2_fallback_snapshot_index.v2",
}
MANIFEST_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_manifest.v1"
)
PARTITIONS = ("train", "calibration", "heldout")
SCALES = (30, 50)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-report", required=True)
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--state-index", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-calibration-contexts", type=int, default=52)
    parser.add_argument(
        "--minimum-calibration-contexts-per-scale", type=int, default=20
    )
    parser.add_argument(
        "--minimum-heldout-contexts-per-scale", type=int, default=10
    )
    args = parser.parse_args()

    output = _resolve(args.output)
    payload = build_manifest(
        training_path=_resolve(args.training_report),
        oracle_path=_resolve(args.oracle_summary),
        state_index_path=_resolve(args.state_index),
        minimum_calibration=max(1, int(args.minimum_calibration_contexts)),
        minimum_calibration_per_scale=max(
            1, int(args.minimum_calibration_contexts_per_scale)
        ),
        minimum_heldout_per_scale=max(
            1, int(args.minimum_heldout_contexts_per_scale)
        ),
    )
    _write(output, payload)
    print(json.dumps({
        "status": payload["status"],
        "supplemental_context_count": len(payload["rows"]),
        "output": str(output),
    }, sort_keys=True), flush=True)
    return 0 if payload["sufficient"] else 2


def build_manifest(
    *,
    training_path: Path,
    oracle_path: Path,
    state_index_path: Path,
    minimum_calibration: int,
    minimum_calibration_per_scale: int,
    minimum_heldout_per_scale: int,
) -> dict[str, Any]:
    training = _load(training_path)
    oracle = _load(oracle_path)
    index = _load(state_index_path)
    errors = _contract_errors(
        training=training,
        training_path=training_path,
        oracle=oracle,
        oracle_path=oracle_path,
        index=index,
        state_index_path=state_index_path,
    )
    if errors:
        raise ValueError("supplemental calibration contract failed: " + ",".join(errors))

    split_path = _resolve(training["split_path"])
    split_payload = _load(split_path)
    frozen_assignments = {
        str(key): str(value)
        for key, value in dict(split_payload["assignments"]).items()
    }
    if any(value not in PARTITIONS for value in frozen_assignments.values()):
        raise ValueError("supplemental calibration split assignment is invalid")

    oracle_rows = [dict(row) for row in oracle.get("context_rows") or ()]
    base_rows = [
        {
            **row,
            "partition": frozen_assignments[
                str(row.get("instance_hash") or "")
            ],
        }
        for row in oracle_rows
        if frozen_assignments.get(str(row.get("instance_hash") or ""))
        in {"calibration", "heldout"}
    ]
    base_states = {str(row.get("state_hash") or "") for row in oracle_rows}
    allowed_engines = {
        str(row.get("source_engine_hash") or "")
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context") and row.get("source_engine_hash")
    }
    allowed_action_policies = {
        str(row.get("source_exact_action_policy_hash") or "")
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
        and row.get("source_exact_action_policy_hash")
    }
    allowed_backends = {
        str(row.get("source_backend_id") or "")
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context") and row.get("source_backend_id")
    }
    candidates = []
    assignments = dict(frozen_assignments)
    for raw in index.get("rows") or ():
        row = _normalized_index_row(raw)
        if row is None or row["state_hash"] in base_states:
            continue
        partition = assignments.get(row["instance_hash"])
        if partition is None:
            partition = _stable_partition(
                scale=row["scale"], instance_hash=row["instance_hash"]
            )
            assignments[row["instance_hash"]] = partition
        if partition not in {"calibration", "heldout"}:
            continue
        if allowed_engines and row["source_engine_hash"] not in allowed_engines:
            continue
        if (
            allowed_action_policies
            and row["source_exact_action_policy_hash"]
            not in allowed_action_policies
        ):
            continue
        if allowed_backends and row["source_backend_id"] not in allowed_backends:
            continue
        candidates.append({**row, "partition": partition})

    selected = _select_supplement(
        base_rows=base_rows,
        candidates=candidates,
        minimum_calibration=minimum_calibration,
        minimum_calibration_per_scale=minimum_calibration_per_scale,
        minimum_heldout_per_scale=minimum_heldout_per_scale,
    )
    combined = [
        {
            "scale": int(row["scale"]),
            "instance_hash": str(row["instance_hash"]),
            "state_hash": str(row["state_hash"]),
            "partition": str(row["partition"]),
        }
        for row in base_rows
    ] + [dict(row) for row in selected]
    counts = _counts(combined)
    sufficient = bool(
        counts["calibration_context_count"] >= minimum_calibration
        and all(
            counts[f"scale{scale}_calibration_context_count"]
            >= minimum_calibration_per_scale
            and counts[f"scale{scale}_heldout_context_count"]
            >= minimum_heldout_per_scale
            for scale in SCALES
        )
    )
    return {
        "schema_version": MANIFEST_SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "deployable": False,
        "starts_solver_process": False,
        "training_authority": False,
        "training_rows_added": 0,
        "instance_isolation_unit": "instance_content_hash",
        "known_instance_assignment": "frozen_trainer_split",
        "unseen_instance_assignment": "sha256_60_20_20_v1",
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "state_index": str(state_index_path),
        "state_index_sha256": _sha256(state_index_path),
        "split_path": str(split_path),
        "split_sha256": _sha256(split_path),
        "requirements": {
            "minimum_calibration_contexts": int(minimum_calibration),
            "minimum_calibration_contexts_per_scale": int(
                minimum_calibration_per_scale
            ),
            "minimum_heldout_contexts_per_scale": int(
                minimum_heldout_per_scale
            ),
        },
        "base_counts": _counts([
            {
                "scale": int(row["scale"]),
                "instance_hash": str(row["instance_hash"]),
                "state_hash": str(row["state_hash"]),
                "partition": str(row["partition"]),
            }
            for row in base_rows
        ]),
        "candidate_count": len(candidates),
        "rows": selected,
        "combined_counts": counts,
        "sufficient": sufficient,
        "status": (
            "READY_FOR_FRESH_PROCESS_CALIBRATION"
            if sufficient
            else "INSUFFICIENT_LEAKAGE_SAFE_EVALUATION_CONTEXTS"
        ),
    }


def _contract_errors(
    *,
    training: dict,
    training_path: Path,
    oracle: dict,
    oracle_path: Path,
    index: dict,
    state_index_path: Path,
) -> list[str]:
    errors = []
    if training.get("schema_version") != TRAINING_SCHEMA:
        errors.append("training_schema_mismatch")
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        errors.append("oracle_schema_mismatch")
    if not bool(training.get("oracle_gate_passed")):
        errors.append("training_not_oracle_authorized")
    if not bool((oracle.get("oracle_gate") or {}).get("passed")):
        errors.append("oracle_gate_not_passed")
    if str(training.get("oracle_summary_sha256") or "") != _sha256(oracle_path):
        errors.append("training_oracle_hash_mismatch")
    split_raw = str(training.get("split_path") or "")
    if not split_raw:
        errors.append("split_path_missing")
    else:
        split_path = _resolve(split_raw)
        if not split_path.is_file():
            errors.append("split_missing")
        else:
            split = _load(split_path)
            if split.get("schema_version") != SPLIT_SCHEMA:
                errors.append("split_schema_mismatch")
            if str(training.get("split_sha256") or "") != _sha256(split_path):
                errors.append("split_hash_mismatch")
    if str(oracle.get("source_state_index_sha256") or "") != _sha256(
        state_index_path
    ):
        errors.append("oracle_state_index_hash_mismatch")
    if str(index.get("schema_version") or "") not in INDEX_SCHEMAS:
        errors.append("state_index_schema_mismatch")
    if bool(training.get("deployable")) or bool(oracle.get("deployable")):
        errors.append("development_safety_mismatch")
    if not training_path.is_file() or not oracle_path.is_file():
        errors.append("source_file_missing")
    return errors


def _normalized_index_row(raw: dict) -> dict[str, Any] | None:
    scale = int(raw.get("scale") or 0)
    instance_hash = str(
        raw.get("instance_content_hash") or raw.get("instance_hash") or ""
    )
    state_hash = str(raw.get("source_state_hash") or raw.get("state_hash") or "")
    instance_path = str(raw.get("instance_path") or "")
    snapshot_path = str(
        raw.get("snapshot_path") or raw.get("source_snapshot_path") or ""
    )
    if (
        scale not in SCALES
        or not instance_hash
        or not state_hash
        or not instance_path
        or not snapshot_path
    ):
        return None
    if not _resolve(instance_path).is_file() or not _resolve(snapshot_path).is_file():
        return None
    return {
        "scale": scale,
        "instance_id": str(raw.get("instance_id") or ""),
        "instance_hash": instance_hash,
        "state_hash": state_hash,
        "instance_path": str(_resolve(instance_path)),
        "snapshot_path": str(_resolve(snapshot_path)),
        "source_backend_id": str(raw.get("source_backend_id") or ""),
        "source_engine_hash": str(raw.get("source_engine_hash") or ""),
        "source_config_hash": str(raw.get("source_config_hash") or ""),
        "source_exact_action_policy_hash": str(
            raw.get("source_exact_action_policy_hash") or ""
        ),
        "preaction_stratum": _preaction_stratum(raw),
    }


def _stable_partition(*, scale: int, instance_hash: str) -> str:
    digest = hashlib.sha256(
        f"p0v5-qg2-instance-split-v1:{int(scale)}:{instance_hash}".encode()
    ).digest()
    fraction = int.from_bytes(digest, "big") / float(1 << 256)
    return (
        "train" if fraction < 0.60
        else "calibration" if fraction < 0.80
        else "heldout"
    )


def _select_supplement(
    *,
    base_rows: list[dict],
    candidates: list[dict],
    minimum_calibration: int,
    minimum_calibration_per_scale: int,
    minimum_heldout_per_scale: int,
) -> list[dict]:
    selected = []
    selected_states: set[str] = set()
    counts = _counts([
        {
            "scale": int(row["scale"]),
            "instance_hash": str(row["instance_hash"]),
            "state_hash": str(row["state_hash"]),
            "partition": str(row["partition"]),
        }
        for row in base_rows
    ])
    queues = {
        (partition, scale): _round_robin_instances(
            row for row in candidates
            if row["partition"] == partition and row["scale"] == scale
        )
        for partition in ("calibration", "heldout")
        for scale in SCALES
    }

    def take(partition: str, scale: int) -> bool:
        queue = queues[(partition, scale)]
        while queue:
            row = queue.pop(0)
            if row["state_hash"] in selected_states:
                continue
            selected.append(row)
            selected_states.add(row["state_hash"])
            counts[f"{partition}_context_count"] += 1
            counts[f"scale{scale}_{partition}_context_count"] += 1
            return True
        return False

    for scale in SCALES:
        while (
            counts[f"scale{scale}_calibration_context_count"]
            < minimum_calibration_per_scale
            and take("calibration", scale)
        ):
            pass
        while (
            counts[f"scale{scale}_heldout_context_count"]
            < minimum_heldout_per_scale
            and take("heldout", scale)
        ):
            pass
    cursor = 0
    while counts["calibration_context_count"] < minimum_calibration:
        scale = SCALES[cursor % len(SCALES)]
        cursor += 1
        if take("calibration", scale):
            continue
        other = 50 if scale == 30 else 30
        if not take("calibration", other):
            break
    return selected


def _round_robin_instances(rows: Iterable[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(str(row["preaction_stratum"]), str(row["instance_hash"]))].append(
            dict(row)
        )
    for values in groups.values():
        values.sort(key=lambda row: str(row["state_hash"]))
    result = []
    while groups:
        for key in sorted(tuple(groups)):
            result.append(groups[key].pop(0))
            if not groups[key]:
                groups.pop(key)
    return result


def _counts(rows: list[dict]) -> dict[str, int]:
    result = {
        "calibration_context_count": 0,
        "heldout_context_count": 0,
    }
    for scale in SCALES:
        for partition in ("calibration", "heldout"):
            result[f"scale{scale}_{partition}_context_count"] = 0
    for row in rows:
        partition = str(row.get("partition") or "")
        scale = int(row.get("scale") or 0)
        if partition not in {"calibration", "heldout"} or scale not in SCALES:
            continue
        result[f"{partition}_context_count"] += 1
        result[f"scale{scale}_{partition}_context_count"] += 1
    return result


def _preaction_stratum(row: dict) -> str:
    scope = (
        "root"
        if str(row.get("pricing_lifecycle_scope") or "") == "root_cg"
        else "tree"
    )
    structural = (
        "branch_cut"
        if int(row.get("branch_pair_count") or 0) > 0
        or int(row.get("active_cut_count") or 0) > 0
        else "plain"
    )
    round_index = int(row.get("round") or 0)
    round_bucket = (
        "r0_9" if round_index < 10
        else "r10_29" if round_index < 30
        else "r30_plus"
    )
    return (
        f"{scope}:{structural}:{round_bucket}:"
        f"{str(row.get('previous_q0_wall_stratum') or 'missing')}"
    )


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
