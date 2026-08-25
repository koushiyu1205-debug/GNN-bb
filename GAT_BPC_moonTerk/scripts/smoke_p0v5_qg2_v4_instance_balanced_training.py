#!/usr/bin/env python3
"""Run a bounded real-map Label-GAT smoke before the training freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
)


ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_smoke.v1"
WRAPPER = ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_rankers.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--instance-split", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--maximum-contexts-per-partition-scale", type=int, default=2)
    args = parser.parse_args()
    oracle_path = _resolve(args.oracle_summary)
    split_path = _resolve(args.instance_split)
    output_dir = _resolve(args.output_dir)
    output = _resolve(args.output)
    if output.is_file():
        _validate_existing(output, oracle_path=oracle_path, split_path=split_path)
        return 0
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit("instance-balanced smoke refuses partial output directory")
    oracle = _load(oracle_path)
    split = _load(split_path)
    if (
        oracle.get("schema_version") != ORACLE_SCHEMA
        or not bool(oracle.get("training_permitted"))
        or not bool(dict(oracle.get("oracle_gate") or {}).get("passed"))
    ):
        raise SystemExit("instance-balanced smoke requires authorized Oracle view")
    assignments = {
        str(key): str(value)
        for key, value in dict(split.get("assignments") or {}).items()
    }
    selected = _balanced_subset(
        oracle,
        assignments,
        maximum=max(1, int(args.maximum_contexts_per_partition_scale)),
    )
    selected_states = {str(row["state_hash"]) for row in selected}
    filtered = dict(oracle)
    filtered.update({
        "development_only": True,
        "deployable": False,
        "diagnostic_subset_only": True,
        "source_authorized_oracle_summary": str(oracle_path),
        "source_authorized_oracle_summary_sha256": _sha256(oracle_path),
        "initial_rows": [
            row for row in oracle.get("initial_rows") or ()
            if str(row.get("state_hash") or "") in selected_states
        ],
        "replicate_rows": [
            row for row in oracle.get("replicate_rows") or ()
            if str(row.get("state_hash") or "") in selected_states
        ],
        "context_rows": selected,
        "status": "INSTANCE_BALANCED_PRETRAINING_SMOKE_VIEW",
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    view = output_dir / "smoke_oracle_view.json"
    ranker_dir = output_dir / "ranker"
    _write(view, filtered)
    completed = subprocess.run([
        sys.executable,
        str(WRAPPER),
        "--oracle-summary", str(view),
        "--instance-split", str(split_path),
        "--output-dir", str(ranker_dir),
        "--models", "gat",
        "--epochs", "1",
        "--early-stopping-patience", "1",
        "--max-pairs-per-context", "256",
        "--seed", "20260807",
    ], cwd=ROOT, check=False)
    report_path = ranker_dir / "training_report.json"
    if completed.returncode != 0 or not report_path.is_file():
        raise SystemExit("instance-balanced Label-GAT smoke training failed")
    report = _load(report_path)
    models = [
        dict(row) for row in report.get("models") or ()
        if str(row.get("model_kind") or "") == "gat"
    ]
    if (
        len(models) != 1
        or str(report.get("instance_balancing_policy") or "")
        != INSTANCE_BALANCING_POLICY_V1
        or int(models[0].get("epochs_completed") or 0) != 1
    ):
        raise SystemExit("instance-balanced Label-GAT smoke report mismatch")
    import torch

    checkpoint = _resolve(models[0]["checkpoint_path"])
    stored = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if str(
        dict(stored.get("metadata") or {}).get("instance_balancing_policy")
        or stored.get("instance_balancing_policy")
        or ""
    ) != INSTANCE_BALANCING_POLICY_V1:
        raise SystemExit("instance-balanced smoke checkpoint lacks authority")
    payload = {
        "schema_version": SCHEMA,
        "passed": True,
        "development_only": True,
        "deployable": False,
        "source_authorized_oracle_summary": str(oracle_path),
        "source_authorized_oracle_summary_sha256": _sha256(oracle_path),
        "instance_split": str(split_path),
        "instance_split_sha256": _sha256(split_path),
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "selected_context_count": len(selected),
        "selected_instance_count": len({
            str(row["instance_hash"]) for row in selected
        }),
        "selected_state_hashes": sorted(selected_states),
        "smoke_oracle_view": str(view),
        "smoke_oracle_view_sha256": _sha256(view),
        "ranker_training_report": str(report_path),
        "ranker_training_report_sha256": _sha256(report_path),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "epoch_count": 1,
        "production_switch_authorized": False,
    }
    _write(output, payload)
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0


def _balanced_subset(oracle: dict, assignments: dict[str, str], *, maximum: int):
    initial = {
        str(row["state_hash"]): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    groups: dict[tuple[int, str], dict[str, list[dict]]] = {}
    for raw in oracle.get("context_rows") or ():
        row = dict(raw)
        state = str(row.get("state_hash") or "")
        instance = str(row.get("instance_hash") or "")
        partition = assignments.get(instance)
        scale = int(row.get("scale") or 0)
        if state not in initial or partition not in {
            "train", "calibration", "heldout"
        } or scale not in {30, 50}:
            continue
        groups.setdefault((scale, partition), {}).setdefault(
            instance, []
        ).append(row)
    selected = []
    for key in sorted(groups):
        if key[1] not in {"train", "calibration"}:
            continue
        instance_groups = groups[key]
        for rows in instance_groups.values():
            rows.sort(key=lambda row: str(row["state_hash"]))
        for instance in sorted(instance_groups)[:maximum]:
            selected.append(instance_groups[instance][0])
    required = {
        (scale, partition)
        for scale in (30, 50)
        for partition in ("train", "calibration")
    }
    observed = {
        (int(row["scale"]), assignments[str(row["instance_hash"])])
        for row in selected
    }
    if not required.issubset(observed):
        raise SystemExit("instance-balanced smoke lacks train/calibration coverage")
    return selected


def _validate_existing(path: Path, *, oracle_path: Path, split_path: Path) -> None:
    payload = _load(path)
    if (
        payload.get("schema_version") != SCHEMA
        or not bool(payload.get("passed"))
        or str(payload.get("source_authorized_oracle_summary_sha256") or "")
        != _sha256(oracle_path)
        or str(payload.get("instance_split_sha256") or "")
        != _sha256(split_path)
    ):
        raise SystemExit("instance-balanced smoke report drift")
    for key in (
        "smoke_oracle_view", "ranker_training_report", "checkpoint",
    ):
        source = _resolve(payload.get(key) or "")
        if not source.is_file() or _sha256(source) != str(
            payload.get(f"{key}_sha256") or ""
        ):
            raise SystemExit(f"instance-balanced smoke artifact drift:{key}")


def _resolve(value) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
