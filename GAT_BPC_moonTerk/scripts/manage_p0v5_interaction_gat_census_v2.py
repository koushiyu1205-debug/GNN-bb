#!/usr/bin/env python3
"""Evaluate the outcome-blind root census and freeze the V2 split/corpus."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import rotate_blocked_arm_order  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("evaluate", "finalize"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--exhausted", action="store_true")
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    _assert_active(run_root)
    config = _load(run_root / "config.freeze.json")
    formal = set(_load(run_root / "formal_blacklist.freeze.json")["content_hashes"])
    protected = set(_load(
        run_root / "candidate_protected_blacklist.freeze.json"
    )["content_hashes"])
    rows, instance_meta = _merged_rows(run_root, config, formal, protected)
    eligible = _eligible(rows, instance_meta)
    coverage = {
        str(scale): {
            "eligible_instances": len(eligible[scale]),
            "target": 23,
            "eligible_contexts": sum(len(value) for value in eligible[scale].values()),
        }
        for scale in (30, 50)
    }
    enough = all(coverage[str(scale)]["eligible_instances"] >= 23 for scale in (30, 50))
    generated = _generated_counts(config)
    status = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_census_status.v2",
        "outcome_blind": True,
        "coverage": coverage,
        "generated_instances_by_scale": generated,
        "maximum_generated_instances_per_scale": 30,
        "target_reached": enough,
        "arm_outcomes_read": 0,
    }
    status_path = run_root / "candidate_census.status.json"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.mode == "evaluate":
        if enough:
            print(json.dumps({**status, "next": "finalize"}, ensure_ascii=False, indent=2))
            return 0
        exhausted = args.exhausted or all(generated[str(scale)] >= 30 for scale in (30, 50))
        if exhausted:
            _terminal(run_root, "INSUFFICIENT_ROOT_GAT_COVERAGE", status)
            return 2
        next_target = {
            str(scale): min(30, generated[str(scale)] + 5)
            for scale in (30, 50)
            if coverage[str(scale)]["eligible_instances"] < 23
        }
        request = {
            "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_candidate_generation_request.v2",
            "outcome_blind": True,
            "next_per_scale_target": next_target,
            "seed_base": 260807000,
            "maximum_per_scale": 30,
        }
        path = run_root / f"candidate_generation_request_{max(next_target.values(), default=0):02d}.json"
        _write_once(path, request)
        print(json.dumps({**status, "next_generation_request": str(path)}, ensure_ascii=False, indent=2))
        return 3
    if not enough:
        raise SystemExit("cannot finalize census before 23 eligible instances per scale")
    _freeze_corpus(run_root, config, formal, eligible, instance_meta)
    print(json.dumps({
        "coverage": coverage,
        "instance_split": str(run_root / "instance_split.freeze.json"),
        "corpus": str(run_root / "corpus.freeze.json"),
        "next_stage": "Q0_MILESTONE_FREEZE",
    }, ensure_ascii=False, indent=2))
    return 0


def _merged_rows(run_root, config, formal, protected):
    rows = []
    instance_meta = {}
    initial = _load(run_root / "candidate_census.initial.freeze.json")
    for row in initial["instances"]:
        instance_meta[str(row["instance_content_hash"])] = dict(row)
    imported = _load(run_root / "r1_preaction_import.freeze.json")
    for raw in imported["rows"]:
        row = dict(raw)
        row["source_cohort"] = "r1_imported_root_q0"
        rows.append(row)
    index = run_root / "root_screen_snapshot_index.current.json"
    if index.is_file():
        for raw in _load(index).get("rows") or ():
            row = dict(raw)
            rows.append(row)
            instance_meta[str(row["instance_content_hash"])] = {
                "scale": int(row["scale"]),
                "instance_content_hash": str(row["instance_content_hash"]),
                "instance_id": str(row["instance_id"]),
                "instance_path": str(row["instance_path"]),
                "source_cohort": str(row["source_cohort"]),
            }
    deduped = {}
    for row in rows:
        _validate_preaction_row(row, config, formal, protected)
        key = (str(row["instance_content_hash"]), str(row["state_hash"]))
        deduped.setdefault(key, row)
    return list(deduped.values()), instance_meta


def _validate_preaction_row(row, config, formal, protected):
    prohibited = {"wall_ratio", "selected_action", "winner", "arm_outcome"}
    if prohibited.intersection(row):
        raise SystemExit("outcome-bearing field leaked into V2 census")
    if str(row.get("pricing_lifecycle_scope")) != "root_cg":
        raise SystemExit("non-root context leaked into V2 census")
    if int(row.get("scale") or 0) not in {30, 50}:
        raise SystemExit("V2 census scale invalid")
    if str(row.get("source_engine_hash")) != config["r1_expected_engine_hash"]:
        raise SystemExit("V2 census engine hash drift")
    if str(row["instance_content_hash"]) in formal:
        raise SystemExit("formal content hash leaked into V2 census")
    if (
        str(row.get("source_cohort") or "") == "generated_v2_candidate"
        and str(row["instance_content_hash"]) in protected
    ):
        raise SystemExit("generated V2 candidate overlaps protected content")
    snapshot = Path(row["snapshot_path"]).resolve()
    if not snapshot.is_file() or _sha256(snapshot) != str(row["snapshot_sha256"]):
        raise SystemExit("V2 census snapshot hash drift")
    payload = _load(snapshot)
    if str(payload.get("state_hash")) != str(row["state_hash"]):
        raise SystemExit("V2 census state hash drift")


def _eligible(rows, instance_meta):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(int(row["scale"]), str(row["instance_content_hash"]))].append(row)
    result = {30: {}, 50: {}}
    for (scale, instance_hash), values in grouped.items():
        if len(values) >= 2 and instance_hash in instance_meta:
            result[scale][instance_hash] = sorted(values, key=lambda row: str(row["state_hash"]))
    return result


def _freeze_corpus(run_root, config, formal, eligible, instance_meta):
    selected_instances = {}
    split_rows = []
    assignments = {}
    contexts = []
    partitions = (("train", 12), ("calibration", 4), ("selector_heldout", 4), ("development_e2e", 3))
    for scale in (30, 50):
        chosen = _select_eligible_instances(scale, eligible[scale], instance_meta, 23)
        selected_instances[str(scale)] = chosen
        cursor = 0
        for partition, count in partitions:
            for instance_hash in chosen[cursor:cursor + count]:
                meta = dict(instance_meta[instance_hash])
                assignments[instance_hash] = partition
                split_rows.append({
                    **meta, "partition": partition, "scale": scale,
                    "selection_stratum": _instance_stratum(eligible[scale][instance_hash], meta),
                })
                if partition != "development_e2e":
                    selected_contexts = _select_two_contexts(eligible[scale][instance_hash], scale)
                    if len(selected_contexts) != 2:
                        raise SystemExit("eligible instance lost two-context guarantee")
                    for ordinal, row in enumerate(selected_contexts):
                        contexts.append(_context_row(row, meta, partition, ordinal))
            cursor += count
        if cursor != 23:
            raise SystemExit("V2 split quota does not sum to 23")
    split = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_instance_split.v2",
        "unit": "instance_content_hash", "outcome_blind": True,
        "formal_blacklist": sorted(formal), "development_formal_overlap": [],
        "partition_counts_per_scale": {name: count for name, count in partitions},
        "selected_instances_by_scale": selected_instances,
        "assignments": dict(sorted(assignments.items())),
        "rows": sorted(split_rows, key=lambda row: (row["scale"], row["partition"], row["instance_content_hash"])),
    }
    contexts.sort(key=lambda row: (
        row["scale"], row["partition"], row["instance_content_hash"],
        row["selection_ordinal_within_instance"],
    ))
    corpus = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v2",
        "status": "FROZEN_BEFORE_ANY_FRESH_ARM_OUTCOME",
        "root_only": True, "outcome_blind": True,
        "exactly_two_contexts_per_train_calibration_heldout_instance": True,
        "tree_contexts": 0, "arm_outcomes_used": False,
        "rows": contexts,
    }
    _write_once(run_root / "instance_split.freeze.json", split)
    _write_once(run_root / "corpus.freeze.json", corpus)
    _write_once(run_root / "q0_milestone_execution.freeze.json", _milestone_schedule(contexts, config))
    _write_once(run_root / "matched_qd1_qb1_execution.freeze.json", _matrix_schedule(contexts, config))
    _write_once(run_root / "candidate_census.decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_census_decision.v2",
        "passed": True, "eligible_instances_per_scale": 23,
        "context_counts": {
            str(scale): {
                partition: sum(row["scale"] == scale and row["partition"] == partition for row in contexts)
                for partition in ("train", "calibration", "selector_heldout")
            }
            for scale in (30, 50)
        },
        "arm_outcomes_read": 0,
    })
    _update_state(run_root, "Q0_MILESTONE_FREEZE", "READY")


def _select_eligible_instances(scale, eligible, instance_meta, count):
    grouped = defaultdict(list)
    for instance_hash, rows in eligible.items():
        meta = instance_meta[instance_hash]
        grouped[_instance_stratum(rows, meta)].append(instance_hash)
    for stratum, values in grouped.items():
        values.sort(key=lambda value: hashlib.sha256(
            f"61635:{scale}:{stratum}:{value}".encode()
        ).hexdigest())
    strata = sorted(grouped, key=lambda value: hashlib.sha256(f"{scale}:{value}".encode()).hexdigest())
    result = []
    while len(result) < count:
        progressed = False
        for stratum in strata:
            if grouped[stratum]:
                result.append(grouped[stratum].pop(0))
                progressed = True
                if len(result) == count:
                    break
        if not progressed:
            break
    if len(result) != count:
        raise SystemExit(f"scale{scale} cannot select 23 eligible instances")
    return result


def _instance_stratum(rows, meta):
    rounds = sorted(int(row.get("round") or 0) for row in rows)
    round_band = "early" if rounds[len(rounds) // 2] < 10 else "middle" if rounds[len(rounds) // 2] < 30 else "late"
    density = sum(int(row.get("active_task_set_count") or 0) for row in rows) / len(rows)
    density_band = "low" if density < 500 else "medium" if density < 1500 else "high"
    cohort = str(meta.get("source_cohort") or rows[0].get("source_cohort") or "unknown")
    return f"{cohort}:{round_band}:{density_band}"


def _select_two_contexts(rows, scale):
    grouped = defaultdict(list)
    for row in rows:
        grouped[_context_stratum(row, scale)].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: (int(row.get("round") or 0), str(row["state_hash"])))
    strata = sorted(grouped, key=lambda value: hashlib.sha256(value.encode()).hexdigest())
    selected = []
    while len(selected) < 2:
        progressed = False
        for stratum in strata:
            if grouped[stratum]:
                selected.append(grouped[stratum].pop(0))
                progressed = True
                if len(selected) == 2:
                    break
        if not progressed:
            break
    return selected


def _context_stratum(row, scale):
    round_index = int(row.get("round") or 0)
    band = "r0_9" if round_index < 10 else "r10_29" if round_index < 30 else "r30_plus"
    pressure = str(row.get("previous_q0_wall_stratum") or "missing")
    density = int(row.get("active_task_set_count") or 0) / max(1, scale)
    density_band = "low" if density < 20 else "medium" if density < 50 else "high"
    return f"{band}:{pressure}:{density_band}"


def _context_row(row, meta, partition, ordinal):
    snapshot = _load(Path(row["snapshot_path"]))
    context_id = hashlib.sha256(f"interaction-gat-v2:{row['state_hash']}:{ordinal}".encode()).hexdigest()
    return {
        "context_id": context_id,
        "instance_content_hash": str(row["instance_content_hash"]),
        "instance_id": str(meta["instance_id"]),
        "instance_path": str(meta["instance_path"]),
        "scale": int(row["scale"]), "partition": partition,
        "snapshot_path": str(row["snapshot_path"]),
        "snapshot_sha256": str(row["snapshot_sha256"]),
        "state_hash": str(row["state_hash"]),
        "engine_hash": str(snapshot["engine_hash"]),
        "config_hash": str(snapshot["config_hash"]),
        "exact_action_policy_hash": str(snapshot["exact_action_policy_hash"]),
        "dual_hash": _stable_hash(snapshot.get("true_duals") or {}),
        "branch_context_hash": _stable_hash(snapshot.get("branch_context") or {}),
        "cut_context_hash": _stable_hash(snapshot.get("cut_context") or {}),
        "cut_lineage_hash": str(dict(snapshot.get("cut_lineage") or {}).get("cut_lineage_hash") or ""),
        "pricing_lifecycle_scope": "root_cg",
        "selection_ordinal_within_instance": ordinal,
        "selection_stratum": _context_stratum(row, int(row["scale"])),
        "selection_policy": "round_pressure_active_density_round_robin.v2",
    }


def _milestone_schedule(contexts, config):
    tasks = [{
        "context_id": row["context_id"], "instance_content_hash": row["instance_content_hash"],
        "instance_path": row["instance_path"], "scale": row["scale"],
        "partition": row["partition"], "snapshot_path": row["snapshot_path"],
        "snapshot_sha256": row["snapshot_sha256"], "state_hash": row["state_hash"],
        "arm": "Q0", "purpose": "freeze_target_milestone_before_any_arm_outcome",
        "fresh_process": True,
        "cap_sec": config["execution"]["replay_caps_sec"][str(row["scale"])],
        "memory_limit_gb": config["execution"]["memory_limit_gb"],
    } for row in contexts if row["partition"] in {"train", "calibration"}]
    return {
        # Kept compatible with the already-audited fresh replay runner.
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_q0_milestone_execution.v1",
        "v2_experiment_schema": "lunar_ice_bpc.p0v5_interaction_gat_q0_milestone_execution.v2",
        "status": "FROZEN_BEFORE_MILESTONE_Q0_RUNS",
        "single_native_process": True, "task_count": len(tasks), "tasks": tasks,
    }


def _matrix_schedule(contexts, config):
    tasks = []
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    for row in contexts:
        if row["partition"] not in {"train", "calibration"}:
            continue
        for block, order in enumerate(rotate_blocked_arm_order(
            row["state_hash"], arms=("Q0", "QD1", "QB1"), repeats=repeats
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": row["context_id"],
                    "instance_content_hash": row["instance_content_hash"],
                    "scale": row["scale"], "partition": row["partition"],
                    "snapshot_path": row["snapshot_path"], "snapshot_sha256": row["snapshot_sha256"],
                    "state_hash": row["state_hash"], "block": block,
                    "ordinal_in_block": ordinal, "arm": arm,
                    "fresh_process": True, "q0_historical_result_reuse": False,
                    "milestone_must_match_prefrozen_q0": True,
                    "cap_sec": config["execution"]["replay_caps_sec"][str(row["scale"])],
                    "memory_limit_gb": config["execution"]["memory_limit_gb"],
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "v2_experiment_schema": "lunar_ice_bpc.p0v5_interaction_gat_matched_execution.v2",
        "status": "FROZEN_BEFORE_QD1_QB1_OUTCOMES",
        "single_native_process": True, "blocked_repeats": repeats,
        "arm_universe": ["Q0", "QD1", "QB1"],
        "task_count": len(tasks), "tasks": tasks,
    }


def _generated_counts(config):
    root = (ROOT / config["candidate_instance_root"]).resolve()
    result = {}
    for scale in (30, 50):
        values = [] if not root.is_dir() else [
            path for path in root.rglob("instance_*_logical_graph.json")
            if f"_{scale:03d}" in str(path.parent) or int(load_lunar_ice_data(_load(path)).scale) == scale
        ]
        result[str(scale)] = len(values)
    return result


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v2",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    _update_state(run_root, "TERMINAL", "FAIL", terminal=True, reason=reason)


def _assert_active(run_root):
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids census writer")


def _update_state(run_root, stage, status, terminal=False, reason=None):
    path = run_root / "state.json"
    state = _load(path)
    state.update({"current_stage": stage, "status": status, "terminal": terminal, "terminal_decision": reason})
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 census artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
