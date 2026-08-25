#!/usr/bin/env python3
"""Shared immutable-evidence helpers for Minimal Interaction-GAT V6."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from math import exp, log
from pathlib import Path
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONFIG = ROOT / "configs/experiments/p0v5_minimal_interaction_gat_qd1_selector_v6.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817"
V5_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v5_20260816"


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
            raise SystemExit(f"immutable V6 artifact drift:{target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")


def write_mutable(path: Path | str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def copy_once(source: Path | str, target: Path | str) -> None:
    source_path, target_path = Path(source), Path(target)
    if target_path.exists():
        if sha256(source_path) != sha256(target_path):
            raise SystemExit(f"immutable V6 copied snapshot drift:{target_path}")
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = target_path.with_suffix(target_path.suffix + ".tmp")
    shutil.copyfile(source_path, temporary)
    temporary.replace(target_path)


def geometric_mean(values) -> float:
    values = tuple(float(value) for value in values)
    if not values or any(value <= 0.0 for value in values):
        raise ValueError("geometric mean requires positive values")
    return exp(sum(log(value) for value in values) / len(values))


def validate_v5_import(config: dict[str, Any]) -> dict[str, Any]:
    v5_root = (ROOT / str(config["v5_run_root"])).resolve()
    expected = dict(config["expected_v5_artifact_sha256"])
    for relative, digest in expected.items():
        path = v5_root / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"V6_V5_EVIDENCE_IMPORT_DRIFT:{relative}")
    differential = (ROOT / str(config["native_differential"])).resolve()
    if (
        not differential.is_file()
        or sha256(differential) != str(config["native_differential_sha256"])
    ):
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:native_differential")

    # V5's own source/prearm registries remain the first-level immutable audit.
    from scripts.p0v5_residual_gat_coverage_repair_v5_common import verify_bootstrap
    verify_bootstrap(v5_root)

    terminal_payload = load(v5_root / "terminal_decision.json")
    if (
        terminal_payload.get("decision") != "FAIL"
        or terminal_payload.get("reason")
        != "QGR1_TRACE_MANDATORY_WITNESS_INCOMPLETE"
        or bool(terminal_payload.get("deployment_authorized"))
        or bool(terminal_payload.get("production_switch_authorized"))
    ):
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:terminal_contract")
    state = load(v5_root / "state.json")
    if not bool(state.get("terminal")) or state.get("current_stage") != "TERMINAL":
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:terminal_state")

    prohibited = (
        "interaction_gat_selector_candidate.pt",
        "selector_selection.decision.json",
        "selector_heldout_candidate.manifest.json",
        "selector_heldout.decision.json",
        "development_e2e.decision.json",
        "formal_full100.decision.json",
        "qgr1_force_on.decision.json",
        "qgr1_ranker.pt",
    )
    present = [name for name in prohibited if (v5_root / name).exists()]
    if present:
        raise SystemExit(
            "V6_V5_EVIDENCE_IMPORT_DRIFT:post_qd1_artifact:" + ",".join(present)
        )

    source = load(v5_root / "source.freeze.json")
    native_binary = Path(str(source["native_binary"]))
    if (
        source.get("exact_engine_hash") != config["expected_engine_hash"]
        or not native_binary.is_file()
        or sha256(native_binary) != config["expected_native_binary_sha256"]
    ):
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:native_binding")

    raw = load(v5_root / "matched_qd1_rows.json")
    collapsed = load(v5_root / "matched_qd1_collapsed.json")
    if len(raw.get("rows") or ()) != int(config["expected_counts"]["raw_matched_tasks"]):
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:raw_task_count")
    rows = [dict(row) for row in collapsed.get("rows") or ()]
    if len(rows) != int(config["expected_counts"]["collapsed_outcomes"]):
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:collapsed_count")
    if any(
        row.get("arm") != "QD1" or not bool(row.get("determined"))
        or row.get("correctness_redlines")
        for row in rows
    ):
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:collapsed_contract")
    resource_failures = [
        row for row in rows if bool(row.get("resource_censor_positive"))
    ]
    if (
        len(resource_failures) != int(
            config["expected_counts"][
                "resource_failure_rows_folded_into_adverse"
            ]
        )
        or any(
            not bool(row.get("adverse"))
            or int(row.get("q0_complete_arm_censored_blocks") or 0) <= 0
            for row in resource_failures
        )
    ):
        raise SystemExit(
            "V6_V5_EVIDENCE_IMPORT_DRIFT:resource_failure_adverse_contract"
        )

    corpus = load(v5_root / "corpus.freeze.json")
    milestone = load(v5_root / "q0_milestone.freeze.json")["by_context"]
    expected_counts = dict(config["expected_counts"])
    by_partition = defaultdict(lambda: {"contexts": 0, "instances": set()})
    for row in corpus["rows"]:
        partition = str(row["partition"])
        if partition in {"train", "calibration"}:
            marker = milestone.get(str(row["context_id"]))
            if not marker or not bool(marker.get("replay_eligible")):
                continue
        key = (partition, str(int(row["scale"])))
        by_partition[key]["contexts"] += 1
        by_partition[key]["instances"].add(str(row["instance_content_hash"]))
    for partition in ("train", "calibration", "selector_heldout", "development_e2e"):
        for scale in ("30", "50"):
            expected_row = expected_counts[partition][scale]
            actual = by_partition[(partition, scale)]
            if (
                actual["contexts"] != int(expected_row["contexts"])
                or len(actual["instances"]) != int(expected_row["instances"])
            ):
                raise SystemExit(
                    f"V6_V5_EVIDENCE_IMPORT_DRIFT:{partition}:{scale}:counts"
                )

    outcome_contexts = {str(row["context_id"]) for row in rows}
    legal_outcome_contexts = {
        str(row["context_id"]) for row in corpus["rows"]
        if row["partition"] in {"train", "calibration"}
        and bool(milestone[str(row["context_id"])]["replay_eligible"])
    }
    if outcome_contexts != legal_outcome_contexts:
        raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:outcome_partition_leakage")

    formal = load(v5_root / "formal_blacklist.freeze.json")
    formal_hashes = {str(value) for value in formal["content_hashes"]}
    corpus_hashes = {str(row["instance_content_hash"]) for row in corpus["rows"]}
    if formal_hashes.intersection(corpus_hashes):
        raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:formal_overlap")

    train_oracle = load(v5_root / "qd1_base_oracle.decision.json")
    for scale in (30, 50):
        observed = float(train_oracle["scales"][str(scale)]["instance_weighted_gm"])
        if abs(observed - float(config["expected_train_oracle_gm"][str(scale)])) > 1e-12:
            raise SystemExit(f"V6_V5_EVIDENCE_IMPORT_DRIFT:train_oracle:{scale}")
        if int(train_oracle["scales"][str(scale)]["non_q0_winner_instances"]) < 5:
            raise SystemExit(f"NO_Q0_QD1_GAT_HEADROOM:{scale}:winners")
    calibration = _calibration_oracle(rows)
    for scale in (30, 50):
        observed = float(calibration[str(scale)]["instance_weighted_gm"])
        expected_gm = float(config["expected_calibration_oracle_gm"][str(scale)])
        if abs(observed - expected_gm) > 1e-12:
            raise SystemExit(f"V6_V5_EVIDENCE_IMPORT_DRIFT:calibration_oracle:{scale}")
        if int(calibration[str(scale)]["beneficial_instances"]) < 2:
            raise SystemExit(f"NO_Q0_QD1_GAT_HEADROOM:{scale}:calibration")
    return {
        "v5_root": str(v5_root), "source": source,
        "terminal": terminal_payload, "raw": raw, "collapsed": collapsed,
        "corpus": corpus, "milestone": milestone,
        "split": load(v5_root / "instance_split.freeze.json"),
        "folds": load(v5_root / "grouped_cv_folds.freeze.json"),
        "graph": load(v5_root / "graph.freeze.json"),
        "interface": load(v5_root / "interface.freeze.json"),
        "formal": formal, "train_oracle": train_oracle,
        "calibration_oracle": calibration,
        "native_differential_path": str(differential),
    }


def _calibration_oracle(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for scale in (30, 50):
        selected = [
            row for row in rows
            if row["partition"] == "calibration" and int(row["scale"]) == scale
        ]
        by_instance = defaultdict(list)
        beneficial_instances = set()
        for row in selected:
            ratio = float(row["ratio"])
            by_instance[str(row["instance_hash"])].append(min(1.0, ratio))
            if ratio <= 0.98:
                beneficial_instances.add(str(row["instance_hash"]))
        folded = {
            instance: geometric_mean(values) for instance, values in by_instance.items()
        }
        result[str(scale)] = {
            "context_count": len(selected), "instance_count": len(by_instance),
            "beneficial_instances": len(beneficial_instances),
            "instance_ratios": folded,
            "instance_weighted_gm": geometric_mean(folded.values()),
        }
    return result


def copied_corpus(run_root: Path, imported: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for raw in imported["corpus"]["rows"]:
        row = dict(raw)
        source = Path(str(row["snapshot_path"]))
        if not source.is_file() or sha256(source) != str(row["snapshot_sha256"]):
            raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:snapshot_hash")
        target = (
            run_root / "imported_preaction_snapshots" / f"scale{int(row['scale'])}"
            / str(row["instance_content_hash"]) / f"{row['state_hash']}.json"
        )
        copy_once(source, target)
        row["v5_snapshot_path"] = str(source.resolve())
        row["v5_snapshot_sha256"] = str(row["snapshot_sha256"])
        row["snapshot_path"] = str(target.resolve())
        row["snapshot_sha256"] = sha256(target)
        rows.append(row)
    return {
        **{key: value for key, value in imported["corpus"].items() if key != "rows"},
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_corpus_freeze.v1",
        "source_v5_corpus_sha256": sha256(
            Path(imported["v5_root"]) / "corpus.freeze.json"
        ),
        "arm_outcomes_in_corpus": 0,
        "rows": rows,
    }


def assert_active(run_root: Path) -> None:
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V6 chain forbids artifact writers")


def verify_freezes(run_root: Path) -> None:
    registry = load(run_root / "freeze.registry.json")
    for relative, digest in dict(registry["artifact_sha256"]).items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    source = load(run_root / "source.freeze.json")
    for relative, digest in dict(source["source_sha256"]).items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    evidence = load(run_root / "v5_qd1_evidence_import.freeze.json")
    for relative, digest in dict(evidence["v5_artifact_sha256"]).items():
        path = Path(str(evidence["v5_run_root"])) / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"V6_V5_EVIDENCE_IMPORT_DRIFT:{relative}")


def update_state(run_root: Path, stage: str, status: str) -> None:
    state = load(run_root / "state.json")
    state.update({"current_stage": str(stage), "status": str(status)})
    write_mutable(run_root / "state.json", state)


def terminal(run_root: Path, reason: str, detail: Any) -> int:
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_terminal.v6",
        "decision": "FAIL", "reason": str(reason), "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "terminal_decision.json", decision)
    state = load(run_root / "state.json")
    state.update({
        "current_stage": "TERMINAL", "status": "FAIL", "terminal": True,
        "terminal_decision": str((run_root / "terminal_decision.json").resolve()),
    })
    write_mutable(run_root / "state.json", state)
    return 2
