#!/usr/bin/env python3
"""Train the mandatory GAT candidate and freeze simple/topology controls."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.train_p0v5_context_queue_portfolio_selector as v1  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import geometric_mean  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (  # noqa: E402
    PORTFOLIO_ACTION_UNIVERSE,
    PORTFOLIO_ARMS,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v2 import assess_gat_calibration  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (  # noqa: E402
    INTERACTION_GAT_MANIFEST_SCHEMA_V1,
    INTERACTION_GAT_RUNTIME_POLICY_V2,
    QGR1_BUCKET_WIDTH,
    interaction_gat_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V1,
    INTERACTION_CONTEXT_FEATURES,
    INTERACTION_EDGE_FEATURES,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    INTERACTION_NODE_FEATURES,
    InteractionGATSelector,
    InteractionGraphFeatures,
    InteractionLinearControl,
    InteractionMLPControl,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_parameter_count,
    interaction_training_loss,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
DATASET_SCHEMA = "lunar_ice_bpc.p0v5_interaction_gat_training_dataset.v2"
MODEL_CLASSES = {
    "gat": InteractionGATSelector,
    "mlp": InteractionMLPControl,
    "linear": InteractionLinearControl,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--qgr1-ranker", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal chain forbids selector training")
    oracle = _load(run_root / "portfolio_oracle.decision.json")["decision"]
    if not bool(oracle.get("selector_training_authorized")):
        raise SystemExit("V2 portfolio oracle did not authorize GAT training")
    admission = _load(run_root / "qgr1_force_on.decision.json")["decision"]
    config = _load(run_root / "config.freeze.json")
    dataset_path = args.dataset.resolve()
    rows = _dataset_rows(_load(dataset_path))
    train_rows = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    if (
        len({row["instance_hash"] for row in train_rows}) != 24
        or len({row["instance_hash"] for row in calibration_rows}) != 8
    ):
        raise SystemExit("V2 selector requires 12+12 train and 4+4 calibration instances")
    normalization = fit_interaction_normalization([row["features"] for row in train_rows])
    envelope = fit_interaction_envelope([row["features"] for row in train_rows])
    allowed = _allowed_arms(admission)

    # Reuse the mature instance-balanced optimizer and reporting metrics while
    # replacing its model/loss globals with the V2 graph classes in this
    # process only.  No V1 source or artifact is modified.
    v1.MODEL_CLASSES = MODEL_CLASSES
    v1.portfolio_parameter_count = interaction_parameter_count
    v1.portfolio_training_loss = interaction_training_loss
    v1.PORTFOLIO_NODE_FEATURES = INTERACTION_NODE_FEATURES
    v1.PORTFOLIO_EDGE_FEATURES = INTERACTION_EDGE_FEATURES
    v1.PORTFOLIO_CONTEXT_FEATURES = INTERACTION_CONTEXT_FEATURES
    torch.set_num_threads(1)
    candidates = []
    output_dir = run_root / "selector_training"
    output_dir.mkdir(parents=True, exist_ok=True)
    for kind in ("gat", "mlp", "linear"):
        for seed in config["selector_training"]["seeds"]:
            candidate = v1._train_one(
                kind=kind, seed=int(seed), normalization=normalization,
                train_rows=train_rows, calibration_rows=calibration_rows,
                maximum_epochs=int(config["selector_training"]["maximum_epochs"]),
                patience=int(config["selector_training"]["patience"]),
            )
            candidate["probability_calibration"] = v1._fit_probability_calibration(
                candidate["model"], calibration_rows
            )
            candidate["metrics"] = {
                "train": v1._prediction_metrics(
                    candidate["model"], candidate["probability_calibration"], train_rows
                ),
                "calibration": v1._prediction_metrics(
                    candidate["model"], candidate["probability_calibration"], calibration_rows
                ),
            }
            thresholds = v1._threshold_results(
                candidate["model"], candidate["probability_calibration"],
                calibration_rows, config["threshold_grid"],
                allowed_arms_by_scale=allowed,
            )
            candidate["threshold_candidates"] = [
                {**row, **_activation_gate(candidate, row, calibration_rows, allowed)}
                for row in thresholds
            ]
            eligible = [
                row for row in candidate["threshold_candidates"]
                if (row["v2_eligible"] if kind == "gat" else row["eligible"])
            ]
            candidate["best_threshold"] = min(eligible, key=v1._threshold_key) if eligible else None
            candidates.append(candidate)

    gat_candidates = [row for row in candidates if row["kind"] == "gat" and row["best_threshold"]]
    if not gat_candidates:
        detail = {"reason": "NO_SAFE_GAT_CALIBRATION_THRESHOLD", "candidate_count": len(candidates)}
        _write_once(run_root / "selector_selection.decision.json", detail)
        _terminal(run_root, "NO_SAFE_GAT_CALIBRATION_THRESHOLD", detail)
        return 2

    gated = []
    for candidate in gat_candidates:
        topology = _topology_gate(candidate, calibration_rows, allowed)
        candidate["topology_gate"] = topology
        if topology["gate"]["passed"]:
            gated.append(candidate)
    if not gated:
        detail = {
            "reason": "NO_GAT_ADVANTAGE",
            "gat_candidates": [_summary(row) for row in gat_candidates],
        }
        _write_once(run_root / "selector_selection.decision.json", detail)
        _terminal(run_root, "NO_GAT_ADVANTAGE", detail)
        return 2

    selected = min(gated, key=v1._candidate_key)
    controls = {}
    for kind in ("mlp", "linear"):
        eligible = [row for row in candidates if row["kind"] == kind and row["best_threshold"]]
        controls[kind] = min(eligible, key=v1._candidate_key) if eligible else None
    if any(value is None for value in controls.values()):
        detail = {"reason": "CONTROL_FREEZE_FAILED"}
        _terminal(run_root, "NO_GAT_ADVANTAGE", detail)
        return 2

    # Freeze all checkpoints before selector-heldout is readable.
    for candidate in candidates:
        path = output_dir / f"{candidate['kind']}_seed{candidate['seed']}.pt"
        torch.save(_checkpoint(candidate, normalization, candidate_authorized=False), path)
        candidate["checkpoint_path"] = path
        candidate["checkpoint_sha256"] = _sha256(path)
        _write_once(output_dir / f"{candidate['kind']}_seed{candidate['seed']}.curve.json", {
            "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_training_curve.v2",
            "model_kind": candidate["kind"], "seed": candidate["seed"],
            "parameter_count": candidate["parameter_count"],
            "best_epoch": candidate["best_epoch"], "curve": candidate["curve"],
            "best_threshold": candidate["best_threshold"],
        })
    selected_checkpoint = run_root / "interaction_gat_selector_candidate.pt"
    torch.save(_checkpoint(selected, normalization, candidate_authorized=True), selected_checkpoint)
    manifest = _manifest(
        run_root, selected, selected_checkpoint, envelope, admission,
        args.qgr1_ranker,
    )
    manifest_path = run_root / "selector_heldout_candidate.manifest.json"
    _write_once(manifest_path, manifest)
    controls_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_controls_freeze.v2",
        "frozen_before_heldout": True,
        "controls_candidate_authorized": False,
        "controls": {
            kind: {
                "seed": row["seed"], "checkpoint_path": str(row["checkpoint_path"]),
                "checkpoint_sha256": row["checkpoint_sha256"],
                "threshold": row["best_threshold"]["thresholds"],
            }
            for kind, row in controls.items()
        },
        "topology_controls": ["no_message", "shuffled_topology"],
        "topology_controls_use_selected_gat_checkpoint": True,
    }
    _write_once(run_root / "selector_controls.freeze.json", controls_freeze)
    eligible_candidates = [row for row in candidates if row["best_threshold"]]
    attribution = v1._attribution(
        selected, calibration_rows, normalization,
        allowed_arms_by_scale=allowed,
    )
    _write_once(run_root / "selector_attribution.calibration.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_attribution.v2",
        "selected_model_kind": "gat",
        "selected_seed": selected["seed"],
        "heldout_outcomes_read": 0,
        **attribution,
    })
    _write_once(run_root / "selector_training_report.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_training_report.v2",
        "gat_is_only_candidate": True,
        "controls_candidate_authorized": False,
        "heldout_outcomes_read": 0,
        "formal_outcomes_read": 0,
        "seed_variance": v1._seed_variance(candidates),
        "calibration_action_disagreement": v1._candidate_disagreement(
            selected, eligible_candidates, calibration_rows,
            allowed_arms_by_scale=allowed,
        ),
        "candidates": [
            {
                "model_kind": row["kind"],
                "seed": row["seed"],
                "parameter_count": row["parameter_count"],
                "best_epoch": row["best_epoch"],
                "checkpoint_path": str(row["checkpoint_path"]),
                "checkpoint_sha256": row["checkpoint_sha256"],
                "best_threshold": row["best_threshold"],
                "metrics": row["metrics"],
                "topology_gate": row.get("topology_gate"),
            }
            for row in candidates
        ],
    })
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_model_selection.v2",
        "decision": "GAT_CANDIDATE_FROZEN",
        "gat_is_only_candidate": True,
        "simple_models_are_controls_only": True,
        "selected_model_kind": "gat",
        "selected_seed": selected["seed"],
        "selected_parameter_count": selected["parameter_count"],
        "selected_checkpoint": str(selected_checkpoint),
        "selected_checkpoint_sha256": _sha256(selected_checkpoint),
        "selected_threshold": selected["best_threshold"]["thresholds"],
        "selected_metrics": selected["metrics"],
        "topology_gate": selected["topology_gate"],
        "controls_freeze": str(run_root / "selector_controls.freeze.json"),
        "attribution": str(run_root / "selector_attribution.calibration.json"),
        "training_report": str(run_root / "selector_training_report.json"),
        "heldout_manifest": str(manifest_path),
        "heldout_outcomes_read": 0,
        "formal_outcomes_read": 0,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "selector_selection.decision.json", decision)
    _update_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _dataset_rows(payload):
    if payload.get("schema_version") != DATASET_SCHEMA:
        raise SystemExit("V2 interaction dataset schema mismatch")
    rows, seen = [], set()
    for raw in payload.get("rows") or ():
        partition = str(raw.get("partition") or "")
        if partition not in {"train", "calibration"}:
            continue
        identity = (partition, str(raw.get("context_id") or ""))
        if not all(identity) or identity in seen:
            raise SystemExit("V2 repeated or incomplete context row")
        seen.add(identity)
        feature = _features(raw["features"])
        targets = dict(raw.get("targets") or {})
        if set(targets) != set(PORTFOLIO_ARMS):
            raise SystemExit("V2 dataset arm target mismatch")
        if any(dict(targets[arm]).get("correctness_redlines") for arm in PORTFOLIO_ARMS):
            raise SystemExit("CORRECTNESS_REDLINE in V2 selector dataset")
        rows.append({
            "partition": partition, "context_id": identity[1],
            "instance_hash": str(raw["instance_hash"]),
            "scale": int(raw["scale"]), "features": feature, "targets": targets,
        })
    return rows


def _features(payload):
    row = InteractionGraphFeatures(
        instance_content_hash=str(payload["instance_content_hash"]),
        task_ids=tuple(payload["task_ids"]),
        node_features=tuple(tuple(map(float, values)) for values in payload["node_features"]),
        edge_index=tuple(tuple(map(int, values)) for values in payload["edge_index"]),
        edge_features=tuple(tuple(map(float, values)) for values in payload["edge_features"]),
        context_features=tuple(map(float, payload["context_features"])),
        graph_schema_version=str(payload["graph_schema_version"]),
        schema_version=str(payload["schema_version"]),
    )
    if row.schema_version != INTERACTION_FEATURE_SCHEMA_V2 or row.graph_schema_version != INTERACTION_GRAPH_SCHEMA_V1:
        raise SystemExit("V2 interaction feature/graph schema mismatch")
    return row


def _activation_gate(candidate, threshold, rows, allowed):
    if not threshold["eligible"]:
        return {"v2_eligible": False, "activation_instances_by_scale": {}}
    candidate["best_threshold"] = threshold
    actions = v1._candidate_actions(candidate, rows, allowed_arms_by_scale=allowed)
    by_context = {row["context_id"]: row for row in rows}
    instances = {}
    for scale in (30, 50):
        selected = [row for row in actions if by_context[row["context_id"]]["scale"] == scale]
        activated_instances = len({
            by_context[row["context_id"]]["instance_hash"]
            for row in selected if row["action"] != "Q0"
        })
        instances[str(scale)] = activated_instances
        if activated_instances < 2 or geometric_mean([row["ratio"] for row in selected]) >= 1.0:
            return {"v2_eligible": False, "activation_instances_by_scale": instances}
    return {"v2_eligible": True, "activation_instances_by_scale": instances}


def _topology_gate(candidate, rows, allowed):
    summaries = {}
    for variant in (None, "no_message", "shuffled_topology"):
        actions = v1._candidate_actions(
            candidate, rows, allowed_arms_by_scale=allowed, variant=variant
        )
        by_context = {row["context_id"]: row for row in rows}
        scales = {}
        for scale in (30, 50):
            selected = [row for row in actions if by_context[row["context_id"]]["scale"] == scale]
            scales[str(scale)] = {
                "activation_instances": len({
                    by_context[row["context_id"]]["instance_hash"]
                    for row in selected if row["action"] != "Q0"
                }),
                "selected_action_gm": geometric_mean([row["ratio"] for row in selected]),
            }
        key = "full" if variant is None else variant
        summaries[key] = {
            "scales": scales,
            "combined_gm": geometric_mean([row["ratio"] for row in actions]),
            "harmful_activations": sum(row["action"] != "Q0" and row["ratio"] >= 1.05 for row in actions),
            "rank_accuracy": _variant_rank_accuracy(candidate, rows, variant),
            "correctness_redlines": [],
            "action_counts": dict(Counter(row["action"] for row in actions)),
        }
    return {
        **summaries,
        "gate": assess_gat_calibration(
            full=summaries["full"], no_message=summaries["no_message"],
            shuffled_topology=summaries["shuffled_topology"],
        ),
    }


def _variant_rank_accuracy(candidate, rows, variant):
    hits = []
    for row in rows:
        output = v1._variant_output(candidate["model"], row["features"], variant)
        values = v1._calibrated_output(output, candidate["probability_calibration"])
        utility = {
            arm: values[arm]["benefit"] * values[arm]["gain"] - values[arm]["adverse"]
            for arm in PORTFOLIO_ARMS
        }
        for arm in PORTFOLIO_ARMS:
            target = row["targets"][arm]
            if target["determined"] and float(target["ratio"]) != 1.0:
                hits.append((utility[arm] > 0.0) == (float(target["ratio"]) < 1.0))
    return sum(map(float, hits)) / len(hits) if hits else 0.0


def _checkpoint(candidate, normalization, *, candidate_authorized):
    return {
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": candidate["kind"],
        "message_passing_required": candidate["kind"] == "gat",
        "controls_candidate_authorized": False,
        "candidate_authorized": bool(candidate_authorized and candidate["kind"] == "gat"),
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "normalization": normalization,
        "probability_calibration": candidate["probability_calibration"],
        "state_dict": candidate["model"].state_dict(),
        "parameter_count": candidate["parameter_count"],
        "seed": candidate["seed"],
        "activation_authority": False,
        "deployment_authorized": False,
    }


def _manifest(run_root, selected, checkpoint, envelope, admission, qgr1_ranker):
    corpus = _load(run_root / "corpus.freeze.json")
    source = _load(run_root / "source.freeze.json")
    mask = admission["arm_scale_mask"]
    manifest = {
        "schema_version": INTERACTION_GAT_MANIFEST_SCHEMA_V1,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V2,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "node_feature_names": list(INTERACTION_NODE_FEATURES),
        "edge_feature_names": list(INTERACTION_EDGE_FEATURES),
        "context_feature_names": list(INTERACTION_CONTEXT_FEATURES),
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "fallback_action": "Q0",
        "allowed_scales": [30, 50],
        "lifecycle_authority": ["root_cg"],
        "arm_scale_mask": mask,
        "forced_veto_arms": ["QGR1"] if not mask.get("QGR1") else [],
        "forced_veto_arms_by_scale": admission["forced_veto_arms_by_scale"],
        "model_kind": "gat",
        "message_passing_required": True,
        "controls_candidate_authorized": False,
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": _sha256(checkpoint),
        "feature_envelope": envelope,
        "thresholds": selected["best_threshold"]["thresholds"],
        "allowed_exact_engine_hashes": sorted({row["engine_hash"] for row in corpus["rows"]}),
        "allowed_exact_config_hashes": sorted({row["config_hash"] for row in corpus["rows"]}),
        "allowed_exact_action_policy_hashes": sorted({row["exact_action_policy_hash"] for row in corpus["rows"]}),
        "source_freeze_sha256": _sha256(run_root / "source.freeze.json"),
        "native_binary_sha256": source["native_binary_sha256"],
        "torch_num_threads": 1,
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "development_only": True,
        "production_switch_authorized": False,
    }
    if mask.get("QGR1"):
        if qgr1_ranker is None or not qgr1_ranker.resolve().is_file():
            raise SystemExit("admitted QGR1 requires the frozen V2 residual ranker")
        ranker = qgr1_ranker.resolve()
        manifest.update({
            "qgr1_ranker_checkpoint_path": str(ranker),
            "qgr1_ranker_checkpoint_sha256": _sha256(ranker),
            "qgr1_guidance_bucket_width": QGR1_BUCKET_WIDTH,
            "qgr1_label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        })
    return manifest


def _allowed_arms(admission):
    return {
        scale: [arm for arm, scales in admission["arm_scale_mask"].items() if scale in scales]
        for scale in (30, 50)
    }


def _summary(row):
    return {
        "model_kind": row["kind"], "seed": row["seed"],
        "best_threshold": row["best_threshold"],
        "topology_gate": row.get("topology_gate"),
    }


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v2",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    _update_state(run_root, "TERMINAL", "FAIL", terminal=True, reason=reason)


def _update_state(run_root, stage, status, terminal=False, reason=None):
    path = run_root / "state.json"
    state = _load(path)
    state.update({
        "current_stage": stage, "status": status,
        "terminal": bool(terminal), "terminal_decision": reason,
    })
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 selector artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
