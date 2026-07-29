#!/usr/bin/env python3
"""Build development-only task-potential upper bounds for QG1.

These potentials deliberately use the completed QC0 replay and therefore are
future-leaked.  They are valid only for a reachability/headroom gate: if even
these optimistic task potentials cannot improve fresh QG1 replays, no learned
model should be trained for this landing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    canonical_arc_candidate_id,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


SCHEMA = "lunar_ice_bpc.p0v3_proof_queue_potential.v1"
METHODS = (
    "best_route_binary",
    "negative_route_reciprocal_rank",
    "negative_route_abs_rc",
    "cover_dual",
    "dominance_wins_log",
    "dominance_net_log",
    "dominance_leverage",
    "arc_dominance_wins_log",
    "arc_dominance_net_log",
    "arc_dominance_leverage",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_centered(
    values: dict[str, float],
    task_ids: tuple[str, ...],
) -> dict[str, float]:
    dense = {task_id: float(values.get(task_id, 0.0)) for task_id in task_ids}
    mean = sum(dense.values()) / max(1, len(dense))
    centered = {key: value - mean for key, value in dense.items()}
    maximum = max((abs(value) for value in centered.values()), default=0.0)
    if maximum <= 0.0:
        return {task_id: 0.0 for task_id in task_ids}
    return {
        task_id: round(centered[task_id] / maximum, 12)
        for task_id in task_ids
    }


def _route_rows(control: dict) -> list[dict]:
    rows = [
        dict(row)
        for row in control.get("route_rows") or ()
        if bool(row.get("accepted"))
        and row.get("python_manual_rc") is not None
    ]
    rows.sort(key=lambda row: float(row["python_manual_rc"]))
    return rows


def _raw_scores(
    *,
    method: str,
    task_ids: tuple[str, ...],
    snapshot: dict,
    control: dict,
) -> dict[str, float]:
    rows = _route_rows(control)
    score = {task_id: 0.0 for task_id in task_ids}
    if method.startswith("dominance_"):
        trace = list(
            (control.get("proof_telemetry") or {}).get(
                "proof_queue_potential_trace"
            )
            or ()
        )
        if len(trace) != len(task_ids) or not bool(
            (control.get("proof_telemetry") or {}).get(
                "proof_queue_potential_trace_enabled"
            )
        ):
            raise SystemExit(f"{method} requires a complete Native trace")
        for row in trace:
            task_id = str(row.get("task_id") or "")
            if task_id not in score:
                raise SystemExit("Native trace task universe mismatch")
            wins = float(row.get("existing_dominator_wins") or 0.0)
            wins += float(row.get("accepted_removed_existing") or 0.0)
            rejected = float(row.get("incoming_rejected") or 0.0)
            rejected += float(row.get("removed_as_existing") or 0.0)
            evaluated = float(row.get("incoming_evaluated") or 0.0)
            if method == "dominance_wins_log":
                value = math.log1p(wins)
            elif method == "dominance_net_log":
                value = math.log1p(wins) - math.log1p(rejected)
            elif method == "dominance_leverage":
                value = math.log1p(wins) / max(
                    1.0, math.log1p(evaluated)
                )
            else:  # pragma: no cover - guarded above
                raise SystemExit(f"unsupported method {method!r}")
            score[task_id] = value
        return score
    if method == "cover_dual":
        duals = dict((snapshot.get("true_duals") or {}).get("task_duals") or {})
        return {
            task_id: float(duals.get(task_id, 0.0))
            for task_id in task_ids
        }
    if not rows:
        raise SystemExit(f"{method} requires at least one accepted route")
    selected = rows[:1] if method == "best_route_binary" else rows
    for rank, row in enumerate(selected, start=1):
        if method == "best_route_binary":
            weight = 1.0
        elif method == "negative_route_reciprocal_rank":
            weight = 1.0 / float(rank)
        elif method == "negative_route_abs_rc":
            weight = max(0.0, -float(row["python_manual_rc"]))
        else:  # pragma: no cover - argparse protects this path
            raise SystemExit(f"unsupported method {method!r}")
        task_set = {
            str(task_id) for task_id in row.get("task_set") or ()
        }
        for task_id in task_set:
            if task_id not in score:
                raise SystemExit("control route task universe mismatch")
            score[task_id] += weight / max(1, len(task_set))
    return score


def _raw_arc_scores(
    *,
    method: str,
    legal_arc_ids: tuple[str, ...],
    control: dict,
) -> dict[str, float]:
    trace = list(
        (control.get("proof_telemetry") or {}).get(
            "proof_queue_arc_potential_trace"
        )
        or ()
    )
    if len(trace) != len(legal_arc_ids) or not bool(
        (control.get("proof_telemetry") or {}).get(
            "proof_queue_potential_trace_enabled"
        )
    ):
        raise SystemExit(f"{method} requires a complete Native arc trace")
    score = {arc_id: 0.0 for arc_id in legal_arc_ids}
    for row in trace:
        arc_id = canonical_arc_candidate_id(
            str(row.get("source") or ""),
            str(row.get("target") or ""),
            str(row.get("path_type") or ""),
        )
        if arc_id not in score:
            raise SystemExit("Native arc trace universe mismatch")
        wins = float(row.get("existing_dominator_wins") or 0.0)
        wins += float(row.get("accepted_removed_existing") or 0.0)
        rejected = float(row.get("incoming_rejected") or 0.0)
        rejected += float(row.get("removed_as_existing") or 0.0)
        evaluated = float(row.get("incoming_evaluated") or 0.0)
        if method == "arc_dominance_wins_log":
            value = math.log1p(wins)
        elif method == "arc_dominance_net_log":
            value = math.log1p(wins) - math.log1p(rejected)
        elif method == "arc_dominance_leverage":
            value = math.log1p(wins) / max(1.0, math.log1p(evaluated))
        else:  # pragma: no cover - argparse protects this path
            raise SystemExit(f"unsupported arc method {method!r}")
        score[arc_id] = value
    return score


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--control-replay", required=True)
    parser.add_argument("--method", choices=METHODS, required=True)
    parser.add_argument("--sign", choices=("forward", "reverse"), default="forward")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    instance_path = (ROOT / args.instance).resolve()
    snapshot_path = (ROOT / args.snapshot).resolve()
    control_path = (ROOT / args.control_replay).resolve()
    output_path = (ROOT / args.output).resolve()
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    control = _load(control_path)
    expected = data.instance_content_hash
    for payload, name in ((snapshot, "snapshot"), (control, "control")):
        if payload.get("instance_content_hash") != expected:
            raise SystemExit(f"{name} instance content hash mismatch")
    control_policy = str(control.get("policy") or "")
    if (
        "dominance_" in str(args.method)
        and control_policy not in {"QC0", "QD1"}
    ):
        raise SystemExit(
            "dominance potential oracle requires a QC0/QD1 control replay"
        )
    if (
        "dominance_" not in str(args.method)
        and control_policy != "QC0"
    ):
        raise SystemExit("route potential oracle requires a QC0 control replay")
    if control.get("source_state_hash") != snapshot.get("state_hash"):
        raise SystemExit("control/snapshot state hash mismatch")
    if (
        not bool(control.get("search_exhaustive"))
        or not bool(control.get("frontier_empty"))
        or bool(control.get("labels_dropped"))
    ):
        raise SystemExit("control replay is not exact and exhaustive")

    legal_arc_ids = tuple(
        canonical_arc_candidate_id(source, target, path_type)
        for (source, target), by_type in data.arcs.items()
        for path_type in by_type
    )
    arc_method = str(args.method).startswith("arc_")
    if arc_method:
        raw = _raw_arc_scores(
            method=str(args.method),
            legal_arc_ids=legal_arc_ids,
            control=control,
        )
        normalized = _normalized_centered(raw, legal_arc_ids)
        task_potentials = {
            task_id: 0.0 for task_id in data.task_ids
        }
        arc_potentials = normalized
    else:
        raw = _raw_scores(
            method=str(args.method),
            task_ids=data.task_ids,
            snapshot=snapshot,
            control=control,
        )
        normalized = _normalized_centered(raw, data.task_ids)
        task_potentials = normalized
        arc_potentials = {}
    if args.sign == "reverse":
        normalized = {
            key: -float(value) for key, value in normalized.items()
        }
        if arc_method:
            arc_potentials = normalized
        else:
            task_potentials = normalized
    identity_payload = {
        "instance_content_hash": expected,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_control_path": str(control_path),
        "method": str(args.method),
        "sign": str(args.sign),
        "task_potentials": task_potentials,
        "arc_potentials": arc_potentials,
    }
    potential_id = hashlib.sha256(
        json.dumps(
            identity_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_reduced_cost": False,
        "can_certify": False,
        "future_leakage": str(args.method) != "cover_dual",
        "valid_use": "oracle_headroom_gate_only",
        "source_kind": (
            "development_future_leaked_upper_bound"
            if str(args.method) != "cover_dual"
            else "development_current_context_heuristic"
        ),
        "instance_content_hash": expected,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_control_path": str(control_path),
        "method": str(args.method),
        "sign": str(args.sign),
        "feature_schema_version": "p0v3_task_potential_oracle.v1",
        "normalization_version": "centered_maxabs.v1",
        "ood_policy_version": "exact_state_hash_only.v1",
        "potential_id": potential_id,
        "task_potentials": task_potentials,
        "arc_potentials": arc_potentials,
        "audit": {
            "task_count": len(data.task_ids),
            "nonzero_task_count": sum(
                abs(value) > 0.0 for value in task_potentials.values()
            ),
            "arc_count": len(legal_arc_ids),
            "nonzero_arc_count": sum(
                abs(value) > 0.0 for value in arc_potentials.values()
            ),
            "minimum": min(normalized.values(), default=0.0),
            "maximum": max(normalized.values(), default=0.0),
            "mean": (
                sum(normalized.values()) / max(1, len(normalized))
            ),
            "unobserved_task_used_as_negative": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
