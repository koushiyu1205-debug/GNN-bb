#!/usr/bin/env python3
"""Freeze outcome-blind context selection and matched arm execution schedule."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    rotate_blocked_arm_order,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"
DEFAULT_INDEX = DEFAULT_RUN_ROOT / "context_snapshot_index.current.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--snapshot-index", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_freezes(run_root)
    config = _load(run_root / "config.freeze.json")
    source_freeze = _load(run_root / "source.freeze.json")
    split = _load(run_root / "instance_split.freeze.json")
    index_path = args.snapshot_index.resolve()
    index = _load(index_path)
    if not isinstance(index.get("rows"), list):
        raise SystemExit("snapshot index rows missing")
    assignments = dict(split["assignments"])
    instance_paths = {
        str(row["instance_content_hash"]): str(row["instance_path"])
        for row in split["rows"]
    }
    formal_blacklist = set(split["formal_benchmark_hash_blacklist"])

    by_instance: dict[str, list[dict]] = defaultdict(list)
    for raw in index["rows"]:
        row = dict(raw)
        instance_hash = str(row.get("instance_content_hash") or "")
        if instance_hash not in assignments:
            continue
        if instance_hash in formal_blacklist:
            _terminal(run_root, "INSTANCE_OR_FEATURE_LEAKAGE", {
                "instance_content_hash": instance_hash,
            })
            raise SystemExit("formal instance leaked into context index")
        _validate_index_row(row)
        by_instance[instance_hash].append(row)

    contexts = []
    maximum = int(config["context_coverage"]["maximum_per_instance"])
    for instance_hash, partition in sorted(assignments.items()):
        if partition == "development_e2e":
            continue
        candidates = by_instance.get(instance_hash, [])
        selected = _stratified_select(candidates, maximum)
        for ordinal, row in enumerate(selected):
            snapshot_path = Path(str(row["snapshot_path"])).resolve()
            if _sha256(snapshot_path) != str(row["snapshot_sha256"]):
                _terminal(run_root, "FREEZE_HASH_DRIFT", {
                    "snapshot_path": str(snapshot_path),
                })
                raise SystemExit("snapshot SHA-256 drift")
            snapshot = _load(snapshot_path)
            binding = _snapshot_binding(snapshot)
            if binding["state_hash"] != str(row["state_hash"]):
                raise SystemExit("snapshot/index state hash mismatch")
            for binding_key, index_key in (
                ("engine_hash", "source_engine_hash"),
                ("config_hash", "source_config_hash"),
                ("exact_action_policy_hash", "source_exact_action_policy_hash"),
            ):
                if binding[binding_key] != str(row[index_key]):
                    raise SystemExit(f"snapshot/index {binding_key} mismatch")
            if binding["engine_hash"] != str(source_freeze["exact_engine_hash"]):
                _terminal(run_root, "FREEZE_HASH_DRIFT", {
                    "snapshot_engine_hash": binding["engine_hash"],
                    "frozen_engine_hash": source_freeze["exact_engine_hash"],
                })
                raise SystemExit("snapshot is not from the frozen current engine")
            context_id = hashlib.sha256(
                f"portfolio-v1:{row['state_hash']}:{ordinal}".encode("utf-8")
            ).hexdigest()
            contexts.append({
                "context_id": context_id,
                "instance_content_hash": instance_hash,
                "instance_id": str(row["instance_id"]),
                "instance_path": instance_paths[instance_hash],
                "scale": int(row["scale"]),
                "partition": partition,
                "snapshot_path": str(snapshot_path),
                "snapshot_sha256": str(row["snapshot_sha256"]),
                "stratum": _stratum(row),
                "selection_ordinal_within_instance": ordinal,
                "selection_policy": "outcome_blind_stratum_round_robin.v1",
                **binding,
            })
    contexts.sort(key=lambda row: (
        row["scale"], row["partition"], row["instance_content_hash"],
        row["selection_ordinal_within_instance"],
    ))
    coverage = _coverage(contexts, config)
    corpus = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_corpus_freeze.v1",
        "status": "FROZEN_BEFORE_FRESH_ARM_OUTCOMES",
        "outcome_blind_selection": True,
        "maximum_contexts_per_instance": maximum,
        "snapshot_index": str(index_path),
        "snapshot_index_sha256": _sha256(index_path),
        "formal_benchmark_instances_used": False,
        "coverage": coverage,
        "rows": contexts,
    }
    corpus_path = run_root / "corpus.freeze.json"
    _write_once(corpus_path, corpus)
    milestone_schedule = _milestone_schedule(contexts, config)
    milestone_schedule.update({
        "corpus_freeze": str(corpus_path),
        "corpus_freeze_sha256": _sha256(corpus_path),
    })
    _write_once(
        run_root / "q0_milestone_execution.freeze.json",
        milestone_schedule,
    )
    schedule = _matched_schedule(contexts, config)
    schedule.update({
        "corpus_freeze": str(corpus_path),
        "corpus_freeze_sha256": _sha256(corpus_path),
    })
    _write_once(run_root / "matched_qd1_qb1_execution.freeze.json", schedule)
    _write_once(run_root / "coverage.decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_coverage_decision.v1",
        **coverage,
    })
    if not coverage["passed"]:
        _terminal(run_root, "INSUFFICIENT_CONTEXT_COVERAGE", coverage)
        _update_state(run_root, "TERMINAL", "FAIL", True, "INSUFFICIENT_CONTEXT_COVERAGE")
        return 2
    _update_state(run_root, "Q0_MILESTONE_FREEZE", "READY", False, None)
    print(json.dumps({
        "corpus_freeze": str(corpus_path),
        "context_count": len(contexts),
        "coverage": coverage,
        "next_stage": "Q0_MILESTONE_FREEZE",
    }, ensure_ascii=False, indent=2))
    return 0


def _stratified_select(rows: list[dict], maximum: int) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[_stratum(row)].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: (int(row.get("round") or 0), str(row["state_hash"])))
    selected = []
    strata = sorted(grouped, key=lambda value: hashlib.sha256(value.encode()).hexdigest())
    while len(selected) < maximum:
        progressed = False
        for stratum in strata:
            if grouped[stratum]:
                selected.append(grouped[stratum].pop(0))
                progressed = True
                if len(selected) == maximum:
                    break
        if not progressed:
            break
    return selected


def _stratum(row: dict) -> str:
    lifecycle = "root" if str(row.get("pricing_lifecycle_scope")) == "root_cg" else "tree"
    context = (
        "branch_cut" if int(row.get("branch_pair_count") or 0)
        or int(row.get("active_cut_count") or 0) else "plain"
    )
    round_index = int(row.get("round") or 0)
    round_band = "r0_9" if round_index < 10 else "r10_29" if round_index < 30 else "r30_plus"
    pressure = str(row.get("previous_q0_wall_stratum") or "missing")
    return f"{lifecycle}:{context}:{round_band}:{pressure}"


def _snapshot_binding(snapshot: dict) -> dict:
    required = ("engine_hash", "config_hash", "exact_action_policy_hash", "state_hash")
    if any(not str(snapshot.get(field) or "") for field in required):
        raise SystemExit("snapshot exact binding is incomplete")
    return {
        "engine_hash": str(snapshot["engine_hash"]),
        "config_hash": str(snapshot["config_hash"]),
        "exact_action_policy_hash": str(snapshot["exact_action_policy_hash"]),
        "state_hash": str(snapshot["state_hash"]),
        "dual_hash": _stable_hash(snapshot.get("true_duals") or {}),
        "branch_context_hash": _stable_hash(snapshot.get("branch_context") or {}),
        "cut_context_hash": _stable_hash(snapshot.get("cut_context") or {}),
        "cut_lineage_hash": str(
            dict(snapshot.get("cut_lineage") or {}).get("cut_lineage_hash") or ""
        ),
    }


def _matched_schedule(contexts: list[dict], config: dict) -> dict:
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    tasks = []
    for context in contexts:
        if context["partition"] not in {"train", "calibration"}:
            continue
        orders = rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QD1", "QB1"), repeats=repeats
        )
        for block, order in enumerate(orders):
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_content_hash": context["instance_content_hash"],
                    "scale": context["scale"],
                    "partition": context["partition"],
                    "snapshot_path": context["snapshot_path"],
                    "snapshot_sha256": context["snapshot_sha256"],
                    "state_hash": context["state_hash"],
                    "block": block,
                    "ordinal_in_block": ordinal,
                    "arm": arm,
                    "fresh_process": True,
                    "q0_historical_result_reuse": False,
                    "milestone_must_match_prefrozen_q0": True,
                    "target_milestone_registry": str(
                        Path(config["run_root"]) / "q0_milestone.freeze.json"
                    ),
                    "cap_sec": config["execution"]["replay_caps_sec"][str(context["scale"])],
                    "memory_limit_gb": config["execution"]["memory_limit_gb"],
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "status": "FROZEN_BEFORE_QD1_QB1_OUTCOMES",
        "single_native_process": True,
        "blocked_repeats": repeats,
        "arm_universe": ["Q0", "QD1", "QB1"],
        "task_count": len(tasks),
        "tasks": tasks,
    }


def _milestone_schedule(contexts: list[dict], config: dict) -> dict:
    tasks = []
    for context in contexts:
        if context["partition"] not in {"train", "calibration"}:
            continue
        tasks.append({
            "context_id": context["context_id"],
            "instance_content_hash": context["instance_content_hash"],
            "instance_path": context["instance_path"],
            "scale": context["scale"],
            "partition": context["partition"],
            "snapshot_path": context["snapshot_path"],
            "snapshot_sha256": context["snapshot_sha256"],
            "state_hash": context["state_hash"],
            "arm": "Q0",
            "purpose": "freeze_target_milestone_before_any_arm_outcome",
            "fresh_process": True,
            "cap_sec": config["execution"]["replay_caps_sec"][str(context["scale"])],
            "memory_limit_gb": config["execution"]["memory_limit_gb"],
        })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_q0_milestone_execution.v1",
        "status": "FROZEN_BEFORE_MILESTONE_Q0_RUNS",
        "single_native_process": True,
        "task_count": len(tasks),
        "tasks": tasks,
    }


def _coverage(contexts: list[dict], config: dict) -> dict:
    result = {}
    violations = []
    gates = dict(config["context_coverage"])
    for scale in (30, 50):
        scale_rows = [row for row in contexts if row["scale"] == scale]
        result[str(scale)] = {}
        for partition in ("train", "calibration", "selector_heldout"):
            rows = [row for row in scale_rows if row["partition"] == partition]
            instances = len({row["instance_content_hash"] for row in rows})
            gate = dict(gates[partition])
            passed = len(rows) >= int(gate["minimum_contexts"]) and instances >= int(gate["minimum_instances"])
            result[str(scale)][partition] = {
                "context_count": len(rows),
                "instance_count": instances,
                "target_contexts": int(gate["target_contexts"]),
                "minimum_contexts": int(gate["minimum_contexts"]),
                "minimum_instances": int(gate["minimum_instances"]),
                "passed": passed,
            }
            if not passed:
                violations.append(f"SCALE{scale}_{partition.upper()}_COVERAGE")
    return {"passed": not violations, "by_scale": result, "violations": violations}


def _validate_index_row(row: dict) -> None:
    required = (
        "snapshot_path", "snapshot_sha256", "state_hash", "source_config_hash",
        "source_engine_hash", "source_exact_action_policy_hash", "scale",
        "instance_id",
    )
    if any(not str(row.get(field) or "") for field in required):
        raise SystemExit("snapshot index row has incomplete exact binding")
    prohibited = {"wall_ratio", "selected_action", "winner", "arm_outcome"}
    if prohibited.intersection(row):
        raise SystemExit("outcome-bearing field found in pre-action corpus index")


def _verify_freezes(run_root: Path) -> None:
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        _terminal(run_root, "FREEZE_HASH_DRIFT", {"error": str(exc)})
        raise SystemExit(str(exc)) from exc


def _update_state(run_root, stage, status, terminal, decision):
    state = _load(run_root / "state.json")
    state.update({
        "current_stage": stage,
        "status": status,
        "terminal": bool(terminal),
        "terminal_decision": decision,
    })
    (run_root / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_terminal.v1",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "deployment_authorized": False, "production_switch_authorized": False,
    })


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_once(path: Path, payload) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable artifact drift: {path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
