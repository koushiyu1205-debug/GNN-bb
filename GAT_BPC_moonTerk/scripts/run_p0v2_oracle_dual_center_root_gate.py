#!/usr/bin/env python3
"""Run one development-only root-CG oracle dual-center gate arm.

This is deliberately not wired into benchmark configs or deployment.  The
oracle is extracted from a completed true-dual root proof for the same
development instance and is therefore valid only as an algorithmic headroom
diagnostic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.pricing.dual_stabilization import (  # noqa: E402
    DevelopmentOracleDualCenter,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    B2B_R3_MODE,
    RELAXED_LABELING_WORKER,
    solve_b2_pricing_tail_baseline,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _diagnostic_b0_placeholder,
)


ARMS = (
    "p0_exact_first",
    "worker_moving_average",
    "oracle_center",
    "oracle_exact_harvest",
    "oracle_ascg_harvest",
    "oracle_ascg_adaptive",
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _development_hashes(path: Path) -> set[str]:
    manifest = _load_json(path)
    if not bool((manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    return {
        str(row["instance_content_hash"])
        for row in manifest.get("development", ())
    }


def _oracle_from_probe(
    data,
    *,
    probe_path: Path,
    probe: dict,
    center_target: str,
    tail_window: int,
) -> DevelopmentOracleDualCenter:
    if str(probe.get("instance_id") or "") != str(data.instance_id):
        raise SystemExit("source probe instance ID mismatch")
    if str(probe.get("pricing_state") or "") != "CERTIFIED_NO_NEGATIVE":
        raise SystemExit("source probe is not true-dual root certified")
    final_judge = probe.get("final_judge") or {}
    if not bool(final_judge.get("uses_true_dual_bpc_certificate")):
        raise SystemExit("source probe has no true-dual certificate")
    if not bool(final_judge.get("pricing_rc_audit_pass")):
        raise SystemExit("source probe pricing RC audit did not pass")
    history = list(probe.get("history") or ())
    if not history:
        raise SystemExit("source probe has no root trajectory")
    final_context = history[-1].get("dual_context") or {}
    final_task_duals = final_context.get("task_duals")
    if not isinstance(final_task_duals, dict):
        raise SystemExit("source probe final task duals are missing")
    if center_target == "tail_mean":
        tail_contexts = [
            dict(row.get("dual_context") or {})
            for row in history[-max(1, int(tail_window)) :]
        ]
        if any(
            set(context.get("task_duals") or {})
            != set(data.task_ids)
            for context in tail_contexts
        ):
            raise SystemExit("source probe tail dual universe mismatch")
        task_duals = {
            task_id: sum(
                float(context["task_duals"][task_id])
                for context in tail_contexts
            )
            / float(len(tail_contexts))
            for task_id in data.task_ids
        }
        source_iteration = (
            f"tail_mean_{len(tail_contexts)}:"
            f"{tail_contexts[0].get('rmp_iteration_id') or ''}:"
            f"{tail_contexts[-1].get('rmp_iteration_id') or ''}"
        )
    else:
        task_duals = final_task_duals
        source_iteration = str(
            final_context.get("rmp_iteration_id") or ""
        )
    center = DevelopmentOracleDualCenter(
        instance_content_hash=data.instance_content_hash,
        task_dual_items=tuple(
            (str(task_id), float(value))
            for task_id, value in task_duals.items()
        ),
        source_rmp_iteration_id=source_iteration,
        source_artifact_sha256=hashlib.sha256(
            probe_path.read_bytes()
        ).hexdigest(),
        source_partition="development",
    )
    center.validate_for(
        instance_content_hash=data.instance_content_hash,
        task_ids=list(data.task_ids),
    )
    return center


def _configure_environment(*, arm: str, scale: int) -> None:
    os.environ["LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST"] = (
        "1"
        if arm in {
            "p0_exact_first",
            "oracle_exact_harvest",
            "oracle_ascg_harvest",
            "oracle_ascg_adaptive",
        }
        else "0"
    )
    os.environ["LUNAR_ICE_SPPRC_EXACT_BACKEND"] = (
        "native_rcspp_host" if int(scale) >= 30 else "native_rcspp_inprocess"
    )
    os.environ["LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB"] = (
        "10" if int(scale) >= 30 else "8"
    )
    os.environ["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "1"
    os.environ["LUNAR_ICE_SPPRC_COMPLETION_BOUND"] = "0"
    os.environ["LUNAR_ICE_SPPRC_SUBSET_DOMINANCE"] = "1"
    os.environ["LUNAR_ICE_SPPRC_CUT_STATE"] = "1"
    os.environ["LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY"] = (
        "branch_adaptive_sparse_harvest_v1"
        if int(scale) >= 30
        else "harvest_then_proof"
    )


def _summarize(
    *,
    arm: str,
    data,
    center: DevelopmentOracleDualCenter,
    result: dict,
    elapsed_sec: float,
    inference_overhead_sec: float,
    include_result: bool,
) -> dict:
    history = list(result.get("history") or ())
    worker_wall = sum(
        float(row.get("worker_wall_time") or 0.0) for row in history
    )
    final_judge_wall = sum(
        float(row.get("final_judge_wall_time") or 0.0) for row in history
    )
    oracle_worker_rows = [
        row
        for row in history
        if str(row.get("development_oracle_dual_center_id") or "")
        == center.oracle_center_id
    ]
    oracle_harvest_rows = [
        row
        for row in history
        if str(row.get("harvest_discovery_oracle_center_id") or "")
        == center.oracle_center_id
    ]
    final_judge = result.get("final_judge") or {}
    exact_safe = bool(
        result.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and result.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and result.get("uses_true_dual_bpc_certificate")
        and final_judge.get("official_pricing_dual_source")
        == "current_true_rmp_dual"
        and final_judge.get("pricing_rc_audit_pass")
    )
    oracle_worker_safe = all(
        (
            not bool(
                (row.get("tail_dual_stabilization") or {}).get(
                    "can_certify_no_negative"
                )
            ),
            str(
                (row.get("tail_dual_stabilization") or {}).get(
                    "official_dual_source"
                )
                or ""
            )
            == "current_true_rmp_dual",
            not bool(row.get("development_oracle_deployable")),
        )
        for row in oracle_worker_rows
    )
    oracle_harvest_safe = all(
        (
            not bool(row.get("harvest_discovery_dual_can_certify")),
            bool(
                row.get(
                    "harvest_discovery_columns_reaudited_under_true_dual"
                )
            ),
        )
        for row in oracle_harvest_rows
    )
    summary = {
        "schema_version": (
            "lunar_ice_bpc.development_oracle_dual_center_root_gate_arm.v1"
        ),
        "arm": arm,
        "development_only": True,
        "deployable": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "oracle_center": center.to_payload(),
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "pricing_state": result.get("pricing_state"),
        "root_lp_bound": result.get("root_lp_bound"),
        "exact_safe": exact_safe,
        "oracle_worker_safe": (
            oracle_worker_safe and oracle_harvest_safe
        ),
        "oracle_harvest_safe": oracle_harvest_safe,
        "pricing_round_count": int(result.get("pricing_round_count") or 0),
        "final_judge_call_count": int(
            result.get("final_judge_call_count") or 0
        ),
        "added_to_master_count": int(
            result.get("added_to_master_count") or 0
        ),
        "candidate_negative_count": int(
            result.get("candidate_negative_count") or 0
        ),
        "worker_wall_sec": round(worker_wall, 6),
        "final_judge_wall_sec": round(final_judge_wall, 6),
        "measured_wall_sec": round(float(elapsed_sec), 6),
        "emulated_inference_overhead_sec": round(
            float(inference_overhead_sec), 6
        ),
        "net_wall_with_inference_sec": round(
            float(elapsed_sec) + float(inference_overhead_sec), 6
        ),
        "oracle_observed_round_count": (
            len(oracle_worker_rows) + len(oracle_harvest_rows)
        ),
        "oracle_worker_round_count": len(oracle_worker_rows),
        "oracle_harvest_round_count": len(oracle_harvest_rows),
        "oracle_active_round_count": sum(
            bool(row.get("development_oracle_dual_center_active"))
            for row in oracle_worker_rows
        )
        + sum(
            float(
                row.get("harvest_discovery_oracle_influence") or 0.0
            )
            > 0.0
            for row in oracle_harvest_rows
        ),
        "oracle_release_observed": any(
            bool(row.get("development_oracle_release_complete"))
            for row in oracle_worker_rows
        ),
        "exact_final_judge_first": arm in {
            "p0_exact_first",
            "oracle_exact_harvest",
            "oracle_ascg_harvest",
            "oracle_ascg_adaptive",
        },
    }
    if include_result:
        summary["result"] = result
    else:
        summary["result_omitted"] = True
        summary["result_sha256"] = hashlib.sha256(
            json.dumps(
                result,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--source-probe", required=True)
    parser.add_argument(
        "--oracle-center-target",
        choices=("final_true_dual", "tail_mean"),
        default="final_true_dual",
    )
    parser.add_argument("--oracle-tail-window", type=int, default=6)
    parser.add_argument(
        "--oracle-center-json",
        default="",
        help=(
            "Optional development-only fitted oracle center. When omitted, "
            "the source probe's final true dual is used."
        ),
    )
    parser.add_argument(
        "--split-manifest",
        default="data/gat_p0v2/p0v2_gat_split_manifest.json",
    )
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-rounds", type=int, default=0)
    parser.add_argument("--wall-time-limit-sec", type=float, default=0.0)
    parser.add_argument("--max-columns-per-round", type=int, default=0)
    parser.add_argument(
        "--initial-true-dual-weight", type=float, default=0.15
    )
    parser.add_argument("--release-round", type=int, default=8)
    parser.add_argument(
        "--l1-initial-penalty", type=float, default=1.0
    )
    parser.add_argument(
        "--l1-activation-round", type=int, default=2
    )
    parser.add_argument(
        "--emulated-inference-overhead-sec", type=float, default=0.02
    )
    parser.add_argument(
        "--include-result",
        action="store_true",
        help=(
            "Persist the full solver payload. The default stores only the "
            "bounded gate summary and a SHA256 of the omitted payload."
        ),
    )
    args = parser.parse_args()

    instance_path = (ROOT / args.instance).resolve()
    probe_path = (ROOT / args.source_probe).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    raw = _load_json(instance_path)
    data = load_lunar_ice_data(raw)
    if data.instance_content_hash not in _development_hashes(split_path):
        raise SystemExit("oracle gate accepts development instances only")
    probe = _load_json(probe_path)
    if args.oracle_center_json:
        center_path = (ROOT / args.oracle_center_json).resolve()
        center_payload = _load_json(center_path)
        center = DevelopmentOracleDualCenter.from_payload(
            center_payload.get("oracle_center") or center_payload
        )
        center.validate_for(
            instance_content_hash=data.instance_content_hash,
            task_ids=list(data.task_ids),
        )
    else:
        center = _oracle_from_probe(
            data,
            probe_path=probe_path,
            probe=probe,
            center_target=str(args.oracle_center_target),
            tail_window=max(1, int(args.oracle_tail_window)),
        )
    source_config = probe.get("config") or {}
    max_rounds = int(
        args.max_rounds
        or source_config.get("max_rounds")
        or max(16, int(data.scale) * 4)
    )
    wall_limit = float(
        args.wall_time_limit_sec
        or source_config.get("wall_time_limit_sec")
        or 300.0
    )
    max_columns = int(
        args.max_columns_per_round
        or source_config.get("max_columns_per_round")
        or 64
    )
    _configure_environment(arm=args.arm, scale=int(data.scale))
    started = perf_counter()
    result = solve_b2_pricing_tail_baseline(
        data,
        b0_direct=_diagnostic_b0_placeholder(data),
        max_direct_tasks=len(data.task_ids),
        max_rounds=max_rounds,
        wall_time_limit_sec=wall_limit,
        max_columns_per_round=max_columns,
        mode=B2B_R3_MODE,
        seed_mode=str(
            source_config.get("seed_mode")
            or "b0_incumbent_plus_singletons"
        ),
        tail_dual_stabilization_enabled=True,
        tail_dual_stabilization_alpha=float(
            source_config.get("tail_dual_stabilization_alpha") or 0.7
        ),
        tail_dual_stabilization_window=int(
            source_config.get("tail_dual_stabilization_window") or 5
        ),
        development_oracle_dual_center=(
            center
            if args.arm in {
                "oracle_center",
                "oracle_exact_harvest",
                "oracle_ascg_harvest",
                "oracle_ascg_adaptive",
            }
            else None
        ),
        development_oracle_initial_true_dual_weight=float(
            args.initial_true_dual_weight
        ),
        development_oracle_release_round=int(args.release_round),
        development_oracle_l1_sidecar_enabled=bool(
            args.arm in {
                "oracle_ascg_harvest",
                "oracle_ascg_adaptive",
            }
        ),
        development_oracle_l1_adaptive_penalty_enabled=bool(
            args.arm == "oracle_ascg_adaptive"
        ),
        development_oracle_l1_initial_penalty=float(
            args.l1_initial_penalty
        ),
        development_oracle_l1_activation_round=int(
            args.l1_activation_round
        ),
        worker_pricer_kind=RELAXED_LABELING_WORKER,
        labeling_final_judge_enabled=True,
        labeling_final_judge_max_exact_tasks=len(data.task_ids),
        labeling_final_judge_exact_harvest_target=max_columns,
    )
    elapsed = perf_counter() - started
    summary = _summarize(
        arm=args.arm,
        data=data,
        center=center,
        result=result,
        elapsed_sec=elapsed,
        inference_overhead_sec=(
            args.emulated_inference_overhead_sec
            if args.arm in {
                "oracle_center",
                "oracle_exact_harvest",
                "oracle_ascg_harvest",
                "oracle_ascg_adaptive",
            }
            else 0.0
        ),
        include_result=bool(args.include_result),
    )
    output_path = (ROOT / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "arm",
                    "algorithm_status",
                    "certificate_scope",
                    "pricing_state",
                    "exact_safe",
                    "pricing_round_count",
                    "final_judge_call_count",
                    "measured_wall_sec",
                    "net_wall_with_inference_sec",
                )
            },
            sort_keys=True,
        )
    )
    return 0 if summary["exact_safe"] and summary["oracle_worker_safe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
