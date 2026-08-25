#!/usr/bin/env python3
"""Fit one future-leaked QO2 label-state ranker from a completed Q0 trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import torch
from torch.nn import functional as F


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scenario import PATH_TYPES  # noqa: E402
from lunar_ice_bpc.exact.bpc.guidance.contracts import canonical_arc_candidate_id  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
    build_admission_aware_preference_pairs,
)


INPUT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
OUTPUT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--q0-trace", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--max-generated-pairs", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260801)
    args = parser.parse_args()

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(int(args.seed))
    data = load_lunar_ice_data(_load(_resolve(args.instance)))
    replay_path = _resolve(args.q0_trace)
    replay = _load(replay_path)
    if replay.get("schema_version") != INPUT_SCHEMA or replay.get("policy") != "Q0":
        raise SystemExit("QO2 requires a Q0 QG2-trace replay")
    if replay.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("QO2 trace instance mismatch")
    telemetry = dict(replay.get("proof_telemetry") or {})
    rows = [dict(row) for row in telemetry.get("proof_queue_label_state_trace") or ()]
    if not rows:
        raise SystemExit("QO2 trace has no label-state rows")
    by_id = {int(row["label_id"]): row for row in rows}
    if len(by_id) != len(rows):
        raise SystemExit("QO2 trace contains duplicate label ids")

    arc_ids = tuple(
        canonical_arc_candidate_id(source, target, path_type)
        for (source, target), by_type in sorted(data.arcs.items())
        for path_type in PATH_TYPES
        if path_type in by_type
    )
    dimension = len(data.task_ids) + len(arc_ids) + 15
    feature_cache: dict[int, torch.Tensor] = {}

    def label_features(label_id: int) -> torch.Tensor:
        if label_id in feature_cache:
            return feature_cache[label_id]
        row = by_id[label_id]
        vector = torch.zeros(dimension, dtype=torch.float32)
        parent_id = int(row.get("parent_label_id", 2**64 - 1))
        if parent_id in by_id and parent_id != label_id:
            vector.copy_(label_features(parent_id))
        node_id = int(row.get("node_id", 0))
        task_index = node_id - 1
        if 0 <= task_index < len(data.task_ids):
            vector[: len(data.task_ids)].zero_()
            vector[task_index] = 1.0
        else:
            vector[: len(data.task_ids)].zero_()
        arc_index = int(row.get("incoming_arc_index", 2**64 - 1))
        if 0 <= arc_index < len(arc_ids):
            vector[len(data.task_ids) + arc_index] += 1.0
        raw_state = tuple(float(value) for value in row.get("features") or ())
        if len(raw_state) != 15:
            raise SystemExit("QO2 label-state feature dimension mismatch")
        vector[-15:] = torch.tensor(raw_state, dtype=torch.float32)
        feature_cache[label_id] = vector
        return vector

    maximum = max(1, min(50_000, int(args.max_generated_pairs)))
    try:
        pairs, supervision = build_admission_aware_preference_pairs(
            replay,
            by_id,
            seed=int(args.seed),
            maximum=maximum,
        )
    except ValueError as exc:
        raise SystemExit(f"QO2 admission supervision failed closed: {exc}")
    if (
        supervision.get("supervision_schema_version")
        != QG2_SUPERVISION_SCHEMA_V2
        or supervision.get("queue_action_surface")
        != QG2_QUEUE_ACTION_SURFACE_V1
        or int(supervision.get("action_reachable_pair_count") or 0)
        != len(pairs)
    ):
        raise SystemExit("QO2 supervision/action-surface contract mismatch")
    if len(pairs) < 10:
        raise SystemExit("QO2 has fewer than ten reachable preference pairs")

    differences = torch.stack(
        [label_features(winner) - label_features(loser) for winner, loser, _ in pairs]
    )
    weights = torch.zeros(dimension, requires_grad=True)
    optimizer = torch.optim.Adam([weights], lr=float(args.learning_rate))
    for _epoch in range(max(1, int(args.epochs))):
        optimizer.zero_grad()
        margins = differences @ weights
        loss = F.softplus(-margins).mean() + 1.0e-4 * weights.square().mean()
        loss.backward()
        optimizer.step()
    with torch.inference_mode():
        margins = differences @ weights
        accuracy = float((margins > 0.0).float().mean())
    values = weights.detach()
    normalized = _normalize(values)
    task = normalized[: len(data.task_ids)]
    arc = normalized[
        len(data.task_ids) : len(data.task_ids) + len(arc_ids)
    ]
    state = normalized[-15:]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "future_leakage": True,
        "source_kind": "QO2_LEAKED_admission_aware_label_state_ranker",
        "valid_use": "bounded_oracle_fresh_process_replay_only",
        "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "instance_content_hash": data.instance_content_hash,
        "source_state_hash": replay["source_state_hash"],
        "source_engine_hash": str(replay["source_engine_hash"]),
        "source_config_hash": str(replay["source_config_hash"]),
        "source_exact_action_policy_hash": str(
            replay["source_exact_action_policy_hash"]
        ),
        "source_q0_trace": str(replay_path),
        "source_q0_trace_sha256": _sha256(replay_path),
        "feature_schema_version": "lunar_ice_bpc.p0v5_qg2_features.v1",
        "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        "normalization_version": "global_maxabs_rank_preserving.v2",
        "task_potentials": {
            task_id: float(value)
            for task_id, value in zip(data.task_ids, task.tolist(), strict=True)
        },
        "arc_potentials": {
            arc_id: float(value)
            for arc_id, value in zip(arc_ids, arc.tolist(), strict=True)
        },
        "label_state_coefficients": [float(value) for value in state.tolist()],
        "training_pair_count": len(pairs),
        "training_pair_kind_counts": _counts(kind for _, _, kind in pairs),
        "supervision": supervision,
        "training_pair_accuracy": accuracy,
        "label_trace_row_count": len(rows),
        "label_trace_truncated": bool(
            telemetry.get("proof_queue_label_trace_truncated")
        ),
    }
    payload["potential_id"] = _hash(payload)
    target = _resolve(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "potential": str(target),
        "pairs": len(pairs),
        "accuracy": accuracy,
    }, sort_keys=True))
    return 0


def _normalize(values: torch.Tensor) -> torch.Tensor:
    maximum = values.abs().max()
    if float(maximum) <= 1.0e-12:
        return torch.zeros_like(values)
    return values / maximum


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
