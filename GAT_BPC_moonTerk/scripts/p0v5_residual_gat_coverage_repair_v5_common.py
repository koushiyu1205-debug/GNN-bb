#!/usr/bin/env python3
"""Shared immutable-import helpers for Residual-GAT Coverage-Repair V5."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


CONFIG = ROOT / "configs/experiments/p0v5_residual_gat_censor_aware_selector_v5.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v5_20260816"
SNAPSHOT_SCHEMA = "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
FORBIDDEN_OUTCOME_FIELDS = frozenset({
    "arm_outcome", "wall_ratio", "winner", "selected_action",
    "selected_arm", "arm_wall_sec", "q0_wall_sec",
})


def load(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_once(path: Path | str, payload: Any) -> None:
    target = Path(path)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable V5 artifact drift:{target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")


def write_mutable_json(path: Path | str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def copy_once(source: Path | str, target: Path | str) -> None:
    source_path = Path(source)
    target_path = Path(target)
    if target_path.exists():
        if sha256(source_path) != sha256(target_path):
            raise SystemExit(f"immutable V5 imported snapshot drift:{target_path}")
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = target_path.with_suffix(target_path.suffix + ".tmp")
    shutil.copyfile(source_path, temporary)
    temporary.replace(target_path)


def validate_v4_import(config: dict[str, Any]) -> dict[str, Any]:
    """Validate V4 terminal/source/snapshots without reading any arm outcome."""

    v4_root = (ROOT / str(config["v4_run_root"])).resolve()
    terminal_path = v4_root / "terminal_decision.json"
    source_path = v4_root / "source.freeze.json"
    prearm_path = v4_root / "prearm.freeze.registry.json"
    expected = {
        terminal_path: str(config["v4_expected_terminal_sha256"]),
        source_path: str(config["v4_expected_source_freeze_sha256"]),
        prearm_path: str(config["v4_expected_prearm_registry_sha256"]),
        (ROOT / str(config["native_differential"])).resolve(): str(
            config["native_differential_sha256"]
        ),
    }
    for path, digest in expected.items():
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"V5_PREACTION_IMPORT_HASH_DRIFT:{path}")

    terminal = load(terminal_path)
    if (
        terminal.get("decision") != "FAIL"
        or terminal.get("reason") != config["v4_expected_terminal_reason"]
        or terminal.get("detail") != [{
            "observed": 1, "partition": "selector_heldout",
            "required": 4, "scale": 30,
        }]
    ):
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_terminal_payload")
    state = load(v4_root / "state.json")
    if not bool(state.get("terminal")) or state.get("current_stage") != "TERMINAL":
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_state")
    # Root collection terminated before the performance freeze.  These files
    # would prove that an arm-producing stage had started and make reuse illegal.
    prohibited = (
        "freeze.registry.json", "corpus.freeze.json",
        "q0_milestone.freeze.json", "arm_execution.freeze.registry.json",
        "matched_qd1_rows.json", "matched_qd1_collapsed.json",
    )
    present = [name for name in prohibited if (v4_root / name).exists()]
    if present:
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_arm_stage_present:" + ",".join(present))

    source = load(source_path)
    for relative, digest in dict(source.get("source_sha256") or {}).items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"V5_PREACTION_IMPORT_HASH_DRIFT:V4_source:{relative}")
    native_binary = Path(str(source["native_binary"]))
    if (
        str(source.get("exact_engine_hash")) != str(config["expected_engine_hash"])
        or not native_binary.is_file()
        or sha256(native_binary) != str(config["expected_native_binary_sha256"])
    ):
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_native_binding")

    prearm = load(prearm_path)
    if int(prearm.get("arm_outcomes_present_at_freeze", -1)) != 0:
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_arm_outcomes")
    for relative, digest in dict(prearm["artifact_sha256"]).items():
        path = v4_root / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"V5_PREACTION_IMPORT_HASH_DRIFT:V4_artifact:{relative}")

    formal_payload = load(v4_root / "formal_blacklist.freeze.json")
    formal_hashes = frozenset(str(value) for value in formal_payload["content_hashes"])
    schedule = load(v4_root / "root_collection.execution.freeze.json")
    tasks = {
        str(row["instance_content_hash"]): dict(row)
        for row in schedule["tasks"]
    }
    if len(tasks) != 50:
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_task_count")

    snapshot_rows: list[dict[str, Any]] = []
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted((v4_root / "fresh_root_snapshots").glob("scale*/*/*.json")):
        payload = load(path)
        _validate_snapshot_payload(payload, tasks, formal_hashes, source)
        instance_hash = str(payload["instance_content_hash"])
        row = {
            "source_snapshot_path": str(path.resolve()),
            "source_snapshot_sha256": sha256(path),
            "instance_content_hash": instance_hash,
            "state_hash": str(payload["state_hash"]),
            "scale": int(payload["scale"]),
            "desired_partition": str(tasks[instance_hash]["desired_partition"]),
        }
        snapshot_rows.append(row)
        by_instance[instance_hash].append(row)
    if len(snapshot_rows) != 105:
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:V4_snapshot_count")

    fixed = [row for row in tasks.values() if row["desired_partition"] != "candidate_pool"]
    candidates = [row for row in tasks.values() if row["desired_partition"] == "candidate_pool"]
    fixed_snapshots = sum(len(by_instance[str(row["instance_content_hash"])]) for row in fixed)
    eligible_candidates = [
        row for row in candidates if by_instance[str(row["instance_content_hash"])]
    ]
    candidate_snapshots = sum(
        len(by_instance[str(row["instance_content_hash"])]) for row in eligible_candidates
    )
    ineligible_candidates = [
        row for row in candidates if not by_instance[str(row["instance_content_hash"])]
    ]
    observed = {
        "fixed_instances": len(fixed),
        "fixed_snapshots": fixed_snapshots,
        "eligible_candidate_instances": len(eligible_candidates),
        "eligible_candidate_snapshots": candidate_snapshots,
        "scale30_v4_eligible_instances": sum(
            int(row["scale"]) == 30 for row in eligible_candidates
        ),
        "scale50_v4_eligible_instances": sum(
            int(row["scale"]) == 50 for row in eligible_candidates
        ),
        "scale30_v4_screened_ineligible_instances": sum(
            int(row["scale"]) == 30 for row in ineligible_candidates
        ),
    }
    if observed != dict(config["required_import_counts"]):
        raise SystemExit(f"V5_PREACTION_IMPORT_HASH_DRIFT:counts:{observed}")
    partition_counts = Counter((int(row["scale"]), row["desired_partition"]) for row in fixed)
    expected_partitions = dict(config["final_partition_instances_per_scale"])
    for scale in (30, 50):
        for partition in ("train", "calibration", "development_e2e"):
            if partition_counts[(scale, partition)] != int(expected_partitions[partition]):
                raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:fixed_partition_counts")

    all_hashes = set(tasks)
    if all_hashes.intersection(formal_hashes):
        raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:formal_overlap")
    return {
        "v4_root": str(v4_root),
        "terminal_path": str(terminal_path),
        "source_freeze_path": str(source_path),
        "prearm_registry_path": str(prearm_path),
        "source": source,
        "formal_payload": formal_payload,
        "tasks": sorted(tasks.values(), key=lambda row: int(row["ordinal"])),
        "fixed_instances": sorted(fixed, key=_instance_order),
        "eligible_candidate_instances": sorted(eligible_candidates, key=_instance_order),
        "screened_ineligible_instances": sorted(ineligible_candidates, key=_instance_order),
        "snapshot_rows": sorted(
            snapshot_rows,
            key=lambda row: (row["scale"], row["instance_content_hash"], row["state_hash"]),
        ),
        "observed_counts": observed,
    }


def copy_imported_snapshots(
    run_root: Path, import_data: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for raw in import_data["snapshot_rows"]:
        row = dict(raw)
        target = (
            run_root / "imported_root_snapshots" / f"scale{int(row['scale'])}"
            / str(row["instance_content_hash"]) / f"{row['state_hash']}.json"
        )
        copy_once(row["source_snapshot_path"], target)
        row["snapshot_path"] = str(target.resolve())
        row["snapshot_sha256"] = sha256(target)
        rows.append(row)
    return rows


def verify_bootstrap(run_root: Path) -> None:
    registry = load(run_root / "prearm.freeze.registry.json")
    for relative, digest in dict(registry["artifact_sha256"]).items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    source = load(run_root / "source.freeze.json")
    for relative, digest in dict(source.get("source_sha256") or {}).items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    for label in ("selected_exact_config", "native_binary", "old_native_binary"):
        path_key = label
        digest_key = label + "_sha256"
        if source.get(path_key) and (
            not Path(str(source[path_key])).is_file()
            or sha256(Path(str(source[path_key]))) != str(source[digest_key])
        ):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{label}")
    differential = Path(str(source["old_new_native_differential_path"]))
    if (
        not differential.is_file()
        or sha256(differential) != str(source["old_new_native_differential_sha256"])
    ):
        raise SystemExit("FREEZE_HASH_DRIFT:old_new_native_differential")
    v4_import = load(run_root / "v4_preaction_import.freeze.json")
    for label in ("v4_terminal", "v4_source_freeze", "v4_prearm_registry"):
        path = Path(str(v4_import[label + "_path"]))
        if not path.is_file() or sha256(path) != str(v4_import[label + "_sha256"]):
            raise SystemExit(f"V5_PREACTION_IMPORT_HASH_DRIFT:{label}")


def assert_active(run_root: Path) -> None:
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V5 chain forbids artifact writers")


def terminal(run_root: Path, reason: str, detail: Any) -> None:
    path = run_root / "terminal_decision.json"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v5",
        "decision": "FAIL", "reason": str(reason), "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(path, payload)
    state_path = run_root / "state.json"
    state = load(state_path)
    state.update({
        "terminal": True, "terminal_decision": str(path.resolve()),
        "current_stage": "TERMINAL", "status": "FAIL",
    })
    write_mutable_json(state_path, state)


def update_state(run_root: Path, stage: str, status: str) -> None:
    path = run_root / "state.json"
    payload = load(path)
    payload.update({"current_stage": stage, "status": status})
    write_mutable_json(path, payload)


def validate_instance_file(
    path: Path, *, expected_scale: int, forbidden_hashes: set[str]
) -> dict[str, Any]:
    data = load_lunar_ice_data(load(path))
    if int(data.scale) != int(expected_scale):
        raise SystemExit(f"candidate scale mismatch:{path}")
    content_hash = str(data.instance_content_hash)
    if content_hash in forbidden_hashes:
        raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:candidate_hash_overlap")
    return {
        "scale": int(data.scale), "instance_content_hash": content_hash,
        "instance_id": str(data.instance_id), "instance_path": str(path.resolve()),
        "desired_partition": "candidate_pool",
        "source_cohort": "fresh_generated_v5_candidate",
    }


def _validate_snapshot_payload(
    payload: dict[str, Any], tasks: dict[str, dict[str, Any]],
    formal_hashes: frozenset[str], source: dict[str, Any],
) -> None:
    instance_hash = str(payload.get("instance_content_hash") or "")
    if instance_hash not in tasks or instance_hash in formal_hashes:
        raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:snapshot_instance")
    if FORBIDDEN_OUTCOME_FIELDS.intersection(payload):
        raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:arm_outcome_field")
    required = (
        "state_hash", "config_hash", "exact_action_policy_hash", "true_duals",
        "branch_context", "cut_context", "active_task_sets",
        "active_column_signature_hashes",
    )
    if any(payload.get(key) is None for key in required):
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:snapshot_binding_missing")
    if (
        payload.get("schema_version") != SNAPSHOT_SCHEMA
        or int(payload.get("scale") or 0) not in {30, 50}
        or str(payload.get("pricing_lifecycle_scope")) != "root_cg"
        or str(payload.get("pricing_mode")) != "exact_proof"
        or str(payload.get("objective_mode")) != "official"
        or not bool(payload.get("proof_tail_fallback_context"))
        or str(payload.get("base_proof_queue_policy_id")) != "Q0"
        or bool(payload.get("labels_dropped", False))
        or str(payload.get("engine_hash")) != str(source["exact_engine_hash"])
    ):
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:snapshot_contract")
    state_hash = str(payload["state_hash"])
    rebuilt = dict(payload)
    rebuilt.pop("state_hash", None)
    if stable_hash(rebuilt) != state_hash:
        raise SystemExit("V5_PREACTION_IMPORT_HASH_DRIFT:snapshot_state_hash")


def validate_candidate_snapshot(
    path: Path, task: dict[str, Any], source: dict[str, Any], formal_hashes: set[str]
) -> dict[str, Any]:
    payload = load(path)
    _validate_snapshot_payload(
        payload, {str(task["instance_content_hash"]): task},
        frozenset(formal_hashes), source,
    )
    if str(payload["instance_content_hash"]) != str(task["instance_content_hash"]):
        raise SystemExit("candidate snapshot instance binding mismatch")
    return payload


def _instance_order(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row["scale"]), str(row.get("desired_partition") or ""),
        str(row.get("instance_path") or ""), str(row["instance_content_hash"]),
    )
