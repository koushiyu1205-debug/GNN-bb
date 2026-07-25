#!/usr/bin/env python3
"""Build a development-only positive-unlabeled Native prefix oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    canonical_arc_candidate_id,
)
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _route_actions(sorties: list[dict]) -> tuple[set[str], set[str]]:
    tasks: set[str] = set()
    arcs: set[str] = set()
    for sortie in sorties:
        route_tasks = [
            str(task_id) for task_id in sortie.get("tasks") or ()
        ]
        path_types = [
            str(path_type)
            for path_type in sortie.get("path_types") or ()
        ]
        if not route_tasks or len(path_types) != len(route_tasks) + 1:
            raise SystemExit("prefix route has an incomplete sortie")
        source = "depot"
        for task_id, path_type in zip(route_tasks, path_types):
            tasks.add(task_id)
            arcs.add(
                canonical_arc_candidate_id(
                    source, task_id, path_type
                )
            )
            source = task_id
        arcs.add(
            canonical_arc_candidate_id(
                source, "depot", path_types[-1]
            )
        )
    return tasks, arcs


def _normalize_positive(values: dict[str, float]) -> dict[str, float]:
    maximum = max(values.values(), default=0.0)
    if maximum <= 0.0:
        return {}
    return {
        key: round(float(value) / float(maximum), 9)
        for key, value in sorted(values.items())
        if value > 0.0
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--collected-probe", required=True)
    parser.add_argument(
        "--split-manifest",
        default="data/gat_p0v2/p0v2_gat_split_manifest.json",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-round", type=int, default=1)
    parser.add_argument("--maximum-round", type=int, default=2**31 - 1)
    parser.add_argument(
        "--context-selection",
        choices=(
            "exact_dual_hash_only",
            "exact_dual_hash_else_nearest_normalized_cover_dual",
        ),
        default="exact_dual_hash_else_nearest_normalized_cover_dual",
    )
    args = parser.parse_args()

    instance_path = (ROOT / args.instance).resolve()
    probe_path = (ROOT / args.collected_probe).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_path = (ROOT / args.output).resolve()
    data = load_lunar_ice_data(_load(instance_path))
    split = _load(split_path)
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    development_hashes = {
        str(row["instance_content_hash"])
        for row in split.get("development", ())
    }
    if data.instance_content_hash not in development_hashes:
        raise SystemExit("prefix oracle accepts development instances only")

    outer = _load(probe_path)
    probe = (
        dict(outer["result"])
        if isinstance(outer.get("result"), dict)
        else outer
    )
    if (
        str(probe.get("pricing_state") or "")
        != "CERTIFIED_NO_NEGATIVE"
        or not bool(probe.get("uses_true_dual_bpc_certificate"))
    ):
        raise SystemExit("collected probe is not true-dual certified")
    contexts = []
    total_events = 0
    total_positive_tasks = 0
    total_positive_arcs = 0
    for row in probe.get("history") or ():
        round_index = int(row.get("round") or 0)
        if not (
            int(args.minimum_round)
            <= round_index
            <= int(args.maximum_round)
        ):
            continue
        if not bool(row.get("dual_center_native_prefix_trace_usable")):
            continue
        events = list(
            row.get("dual_center_native_prefix_trace_events") or ()
        )
        if not events:
            continue
        task_weight: dict[str, float] = {}
        arc_weight: dict[str, float] = {}
        for event_rank, event in enumerate(events):
            # Ordinal reciprocal-rank credit avoids combining seconds, label
            # counts, and RC through arbitrary physical-unit coefficients.
            rank_weight = 1.0 / float(event_rank + 1)
            tasks, arcs = _route_actions(list(event.get("sorties") or ()))
            if not tasks or not arcs:
                continue
            per_task = rank_weight / float(len(tasks))
            per_arc = rank_weight / float(len(arcs))
            for task_id in tasks:
                task_weight[task_id] = (
                    task_weight.get(task_id, 0.0) + per_task
                )
            for arc_id in arcs:
                arc_weight[arc_id] = (
                    arc_weight.get(arc_id, 0.0) + per_arc
                )
        task_priorities = _normalize_positive(task_weight)
        arc_priorities = _normalize_positive(arc_weight)
        if not task_priorities or not arc_priorities:
            continue
        dual_context = dict(row.get("dual_context") or {})
        task_duals = dict(dual_context.get("task_duals") or {})
        if set(task_duals) != set(data.task_ids):
            raise SystemExit("prefix context task-dual universe mismatch")
        fleet_dual = float(dual_context.get("fleet_dual") or 0.0)
        cut_duals = dict(dual_context.get("cut_duals") or {})
        values = [
            *task_priorities.values(),
            *arc_priorities.values(),
            *[float(value) for value in task_duals.values()],
            fleet_dual,
            *[float(value) for value in cut_duals.values()],
        ]
        if any(not isfinite(value) for value in values):
            raise SystemExit("prefix oracle contains NaN/Inf")
        contexts.append(
            {
                "rmp_iteration_id": str(
                    dual_context.get("rmp_iteration_id") or ""
                ),
                "round_index": round_index,
                "mathematical_dual_hash": true_dual_binding_hash(
                    task_duals,
                    fleet_limit=fleet_dual,
                    cuts=cut_duals,
                ),
                "task_duals": {
                    str(key): float(value)
                    for key, value in sorted(task_duals.items())
                },
                "fleet_dual": fleet_dual,
                "cut_duals": {
                    str(key): float(value)
                    for key, value in sorted(cut_duals.items())
                },
                "task_priorities": task_priorities,
                "arc_priorities": arc_priorities,
                "observed_best_rc_event_count": len(events),
                "first_event_extended_labels": int(
                    events[0].get("extended_labels") or 0
                ),
                "last_event_extended_labels": int(
                    events[-1].get("extended_labels") or 0
                ),
                "unobserved_actions_used_as_negative": False,
            }
        )
        total_events += len(events)
        total_positive_tasks += len(task_priorities)
        total_positive_arcs += len(arc_priorities)
    if not contexts:
        raise SystemExit("no usable Native prefix contexts")
    source_sha = hashlib.sha256(probe_path.read_bytes()).hexdigest()
    payload = {
        "schema_version": (
            "lunar_ice_bpc.development_native_prefix_priority_oracle.v1"
        ),
        "source_partition": "development",
        "instance_content_hash": data.instance_content_hash,
        "source_artifact_sha256": source_sha,
        "contexts": contexts,
        "context_selection": str(args.context_selection),
        "task_priorities": {},
        "arc_priorities": {},
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "can_filter": False,
        "can_certify": False,
        "unobserved_actions_used_as_negative": False,
        "audit": {
            "passed": True,
            "context_count": len(contexts),
            "best_rc_event_count": total_events,
            "mean_positive_task_count": (
                total_positive_tasks / len(contexts)
            ),
            "mean_positive_arc_count": (
                total_positive_arcs / len(contexts)
            ),
            "target_kind": (
                "positive_unlabeled_best_rc_prefix_reciprocal_rank"
            ),
            "mixed_physical_unit_cost_formula_used": False,
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
    print(
        json.dumps(
            {
                "instance_id": data.instance_id,
                **payload["audit"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
