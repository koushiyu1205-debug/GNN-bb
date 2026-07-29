#!/usr/bin/env python3
"""Collect V3 state-local top-3 Ryan-Foster counterfactuals.

Each alternative arm shares one exact root source, follows P0 rank 0 to a
canonical branch path, changes only that path to rank 1 or rank 2, and then
returns to P0.  This is a development-only causal action-headroom experiment;
it is not a trained or deployable guidance policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID  # noqa: E402
from lunar_ice_bpc.guidance.branch_counterfactual_tree_solver import (  # noqa: E402
    solve_b3_branch_price_tree_baseline,
)
from lunar_ice_bpc.guidance.branch_tail_trigger import (  # noqa: E402
    TAIL_TRIGGER_POLICY_IDS,
    annotate_branch_tail_events,
)
from lunar_ice_bpc.exact.bpc.cuts.live_sri import LiveSriPolicy  # noqa: E402
from lunar_ice_bpc.exact.bpc.solver.live_sri_solver import (  # noqa: E402
    solve_node_pricing_with_live_sri,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    canonical_universe_hash,
)
from lunar_ice_bpc.exact.bpc.master.journey_master import (  # noqa: E402
    solve_root_journey_master,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    RELAXED_LABELING_WORKER,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.branching import BranchContext  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    CutContext,
    CutLineage,
    cut_context_from_payload,
    cut_lineage_from_payload,
)
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.exact.solver.branch_probe import (  # noqa: E402
    build_fractional_branch_probe,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _diagnostic_b0_placeholder,
)


PROFILE_BY_SCALE = {
    5: {
        "root_harvest_target": 8,
        "root_max_rounds": 20,
        "tree_max_nodes": 15,
        "tree_max_depth": 4,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 2,
    },
    10: {
        "root_harvest_target": 16,
        "root_max_rounds": 40,
        "tree_max_nodes": 63,
        "tree_max_depth": 6,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 4,
    },
    20: {
        "root_harvest_target": 32,
        "root_max_rounds": 80,
        "tree_max_nodes": 127,
        "tree_max_depth": 8,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 8,
    },
    30: {
        "root_harvest_target": 64,
        "root_max_rounds": 120,
        "tree_max_nodes": 255,
        "tree_max_depth": 12,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 10,
    },
}

BASELINE_ID = "FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3"
BASELINE_CONFIG_PATH = ROOT / "configs/native_live_sri_p0_pilot_v1.yaml"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


class _DevelopmentRoundSnapshotRecorder:
    """Write deduplicated pre-pricing root states for causal policy forks."""

    schema_version = "lunar_ice_bpc.p0v3_root_policy_state_snapshot.v1"
    manifest_schema_version = (
        "lunar_ice_bpc.p0v3_root_policy_state_snapshot_manifest.v1"
    )
    catalog_schema_version = (
        "lunar_ice_bpc.p0v3_root_policy_column_catalog.v1"
    )

    def __init__(
        self,
        *,
        output_dir: Path,
        data,
        solver_binding: dict,
        split_manifest_hash: str,
    ) -> None:
        self.output_dir = output_dir
        self.data = data
        self.solver_binding = dict(solver_binding)
        self.split_manifest_hash = str(split_manifest_hash)
        self.column_catalog: dict[str, dict] = {}
        self.snapshot_rows: list[dict] = []
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _dual_context(master) -> dict:
        context = master.reduced_cost_context
        return {
            "dual_source": "master.reduced_cost_context",
            "dual_fingerprint": str(
                getattr(context, "dual_fingerprint", "") or ""
            ),
            "rmp_iteration_id": str(
                getattr(context, "rmp_iteration_id", "") or ""
            ),
            "fleet_dual": float(
                getattr(context, "fleet_dual", 0.0)
            ),
            "task_duals": {
                str(key): float(value)
                for key, value in getattr(
                    context, "task_duals", {}
                ).items()
            },
            "cut_duals": {
                str(key): float(value)
                for key, value in getattr(
                    context, "cut_duals", {}
                ).items()
            },
        }

    @staticmethod
    def _trajectory_features(
        *,
        round_index: int,
        master,
        master_columns: tuple,
        prior_history: tuple,
        current_duals: dict,
        effective_harvest_target: int,
    ) -> dict:
        previous = dict(prior_history[-1]) if prior_history else {}
        penultimate = (
            dict(prior_history[-2])
            if len(prior_history) >= 2
            else {}
        )
        previous_duals = dict(
            (previous.get("dual_context") or {}).get(
                "task_duals"
            )
            or {}
        )
        current_task_duals = dict(
            current_duals.get("task_duals") or {}
        )
        dual_keys = sorted(
            set(previous_duals) | set(current_task_duals)
        )
        dual_deltas = [
            abs(
                float(current_task_duals.get(key, 0.0))
                - float(previous_duals.get(key, 0.0))
            )
            for key in dual_keys
        ]
        penultimate_duals = dict(
            (penultimate.get("dual_context") or {}).get(
                "task_duals"
            )
            or {}
        )
        penultimate_dual_keys = sorted(
            set(penultimate_duals) | set(current_task_duals)
        )
        penultimate_dual_deltas = [
            abs(
                float(current_task_duals.get(key, 0.0))
                - float(penultimate_duals.get(key, 0.0))
            )
            for key in penultimate_dual_keys
        ]
        previous_bound = previous.get("node_lp_bound")
        penultimate_bound = penultimate.get("node_lp_bound")
        current_bound = float(master.rmp.objective_bound)
        primal = tuple(master.rmp.primal_columns or tuple())
        fractional_primal_count = sum(
            1
            for row in primal
            if 1.0e-9
            < float(row.get("lambda_value") or 0.0)
            < 1.0 - 1.0e-9
        )
        return {
            "round": int(round_index),
            "active_column_count": len(master_columns),
            "active_task_set_count": len(
                {frozenset(column.task_set) for column in master_columns}
            ),
            "rmp_primal_nonzero_count": len(primal),
            "rmp_primal_fractional_count": int(
                fractional_primal_count
            ),
            "node_lp_bound": current_bound,
            "previous_node_lp_bound": previous_bound,
            "node_lp_bound_delta": (
                None
                if previous_bound is None
                else current_bound - float(previous_bound)
            ),
            "previous_final_judge_wall_time": (
                None
                if not previous
                else float(
                    previous.get("final_judge_wall_time")
                    or 0.0
                )
            ),
            "previous_harvest_pass_wall_time": (
                None
                if not previous
                else float(
                    previous.get(
                        "labeling_final_judge_harvest_pass_wall_time"
                    )
                    or 0.0
                )
            ),
            "previous_proof_pass_wall_time": (
                None
                if not previous
                else float(
                    previous.get(
                        "labeling_final_judge_proof_pass_wall_time"
                    )
                    or 0.0
                )
            ),
            "previous_harvest_column_count": (
                None
                if not previous
                else int(
                    previous.get(
                        "labeling_final_judge_harvest_pass_column_count"
                    )
                    or 0
                )
            ),
            "previous_harvest_processed_labels": (
                None
                if not previous
                else int(
                    previous.get(
                        "labeling_final_judge_harvest_pass_processed_labels"
                    )
                    or 0
                )
            ),
            "penultimate_harvest_column_count": (
                None
                if not penultimate
                else int(
                    penultimate.get(
                        "labeling_final_judge_harvest_pass_column_count"
                    )
                    or 0
                )
            ),
            "penultimate_harvest_processed_labels": (
                None
                if not penultimate
                else int(
                    penultimate.get(
                        "labeling_final_judge_harvest_pass_processed_labels"
                    )
                    or 0
                )
            ),
            "penultimate_best_true_rc": (
                None
                if not penultimate
                else penultimate.get("harvest_best_true_rc")
            ),
            "previous_added_column_count": (
                None
                if not previous
                else int(previous.get("added_column_count") or 0)
            ),
            "previous_best_true_rc": (
                None
                if not previous
                else previous.get("harvest_best_true_rc")
            ),
            "effective_harvest_target": int(
                effective_harvest_target
            ),
            "dual_l1_delta_from_previous": (
                None if not previous else sum(dual_deltas)
            ),
            "dual_linf_delta_from_previous": (
                None
                if not previous
                else max(dual_deltas, default=0.0)
            ),
            "dual_l1_delta_from_penultimate": (
                None
                if not penultimate
                else sum(penultimate_dual_deltas)
            ),
            "dual_linf_delta_from_penultimate": (
                None
                if not penultimate
                else max(
                    penultimate_dual_deltas,
                    default=0.0,
                )
            ),
            "node_lp_bound_delta_from_penultimate": (
                None
                if penultimate_bound is None
                else current_bound - float(penultimate_bound)
            ),
        }

    def __call__(self, state: dict) -> None:
        master = state["master"]
        master_columns = tuple(state["master_columns"])
        column_ids: list[str] = []
        for column in master_columns:
            column_payload = column.to_solution_payload(
                vehicle_id="snapshot_column"
            )
            column_id = _sha256_json(column_payload)
            self.column_catalog.setdefault(
                column_id, column_payload
            )
            column_ids.append(column_id)
        dual_context = self._dual_context(master)
        branch_payload = state["branch_context"].to_payload()
        cut_payload = state["cut_context"].to_payload()
        lineage_payload = state["cut_lineage"].to_payload()
        state_payload = {
            "schema_version": self.schema_version,
            "development_only": True,
            "deployable": False,
            "can_certify": False,
            "mutates_p0": False,
            "instance_id": self.data.instance_id,
            "instance_content_hash": (
                self.data.instance_content_hash
            ),
            "service_timing_policy_id": (
                self.data.service_timing_policy_id
            ),
            "split_manifest_hash": self.split_manifest_hash,
            "source_solver_binding_hash": self.solver_binding[
                "binding_hash"
            ],
            "node_id": str(state["node_id"]),
            "round": int(state["round"]),
            "source_pass_policy": str(state["pass_policy"]),
            "source_pass_strategy": str(
                state["pass_strategy"]
            ),
            "sparse_harvest_strike_count": int(
                state.get("sparse_harvest_strike_count") or 0
            ),
            "required_sparse_harvest_strikes": int(
                state.get("required_sparse_harvest_strikes") or 1
            ),
            "max_columns_per_round": int(
                state["max_columns_per_round"]
            ),
            "effective_harvest_target": int(
                state["effective_harvest_target"]
            ),
            "rmp_iteration_id": str(
                dual_context["rmp_iteration_id"]
            ),
            "node_lp_bound": float(
                master.rmp.objective_bound
            ),
            "rmp_primal": list(
                master.rmp.primal_columns or tuple()
            ),
            "true_duals": dual_context,
            "branch_context": branch_payload,
            "cut_context": cut_payload,
            "cut_lineage": lineage_payload,
            "live_cut_policy_hash": str(
                state["live_cut_policy_hash"]
            ),
            "separator_policy_version": str(
                state["separator_policy_version"]
            ),
            "active_column_ids": column_ids,
            "active_column_count": len(column_ids),
            "trajectory_features": self._trajectory_features(
                round_index=int(state["round"]),
                master=master,
                master_columns=master_columns,
                prior_history=tuple(
                    state.get("prior_history") or tuple()
                ),
                current_duals=dual_context,
                effective_harvest_target=int(
                    state["effective_harvest_target"]
                ),
            ),
        }
        state_payload["trajectory_features"][
            "sparse_harvest_strike_count"
        ] = int(state_payload["sparse_harvest_strike_count"])
        state_payload["trajectory_features"][
            "required_sparse_harvest_strikes"
        ] = int(state_payload["required_sparse_harvest_strikes"])
        state_hash = _sha256_json(state_payload)
        snapshot_path = (
            self.output_dir
            / f"round_{int(state['round']):04d}_{state_hash[:16]}.json"
        )
        _write_json(
            snapshot_path,
            {**state_payload, "state_hash": state_hash},
        )
        self.snapshot_rows.append(
            {
                "round": int(state["round"]),
                "state_hash": state_hash,
                "snapshot_path": str(snapshot_path.resolve()),
                "active_column_count": len(column_ids),
            }
        )

    def finalize(self) -> None:
        catalog_payload = {
            "schema_version": self.catalog_schema_version,
            "instance_id": self.data.instance_id,
            "instance_content_hash": (
                self.data.instance_content_hash
            ),
            "columns": self.column_catalog,
        }
        catalog_hash = _sha256_json(catalog_payload)
        catalog_path = self.output_dir / "column_catalog.json"
        _write_json(
            catalog_path,
            {**catalog_payload, "catalog_hash": catalog_hash},
        )
        manifest_payload = {
            "schema_version": self.manifest_schema_version,
            "development_only": True,
            "deployable": False,
            "can_certify": False,
            "instance_id": self.data.instance_id,
            "instance_content_hash": (
                self.data.instance_content_hash
            ),
            "source_solver_binding_hash": self.solver_binding[
                "binding_hash"
            ],
            "column_catalog_path": str(catalog_path.resolve()),
            "column_catalog_hash": catalog_hash,
            "snapshot_count": len(self.snapshot_rows),
            "snapshots": self.snapshot_rows,
        }
        _write_json(
            self.output_dir / "manifest.json",
            {
                **manifest_payload,
                "manifest_hash": _sha256_json(manifest_payload),
            },
        )


def _development_hashes(manifest: dict) -> set[str]:
    if not bool((manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    if (
        str(manifest.get("service_timing_policy_id") or "")
        != SERVICE_TIMING_POLICY_ID
    ):
        raise SystemExit("split manifest service-timing policy mismatch")
    if not bool(manifest.get("causal_oracle_collection_authorized")):
        raise SystemExit("split manifest does not authorize causal oracle collection")
    return {
        str(row["instance_content_hash"])
        for row in manifest.get("development", ())
    }


def _configure_environment(
    *,
    scale: int,
    profile: dict,
    subset_dominance_enabled: bool,
    final_judge_pass_policy: str,
    adaptive_harvest_cap_sec: float,
    adaptive_harvest_max_processed_labels: int,
) -> None:
    os.environ["LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST"] = "1"
    os.environ["LUNAR_ICE_SPPRC_EXACT_BACKEND"] = str(profile["backend"])
    os.environ["LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB"] = str(profile["memory_gb"])
    os.environ["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "1"
    os.environ["LUNAR_ICE_SPPRC_COMPLETION_BOUND"] = "0"
    os.environ["LUNAR_ICE_SPPRC_SUBSET_DOMINANCE"] = (
        "1" if subset_dominance_enabled else "0"
    )
    os.environ["LUNAR_ICE_SPPRC_CUT_STATE"] = "1"
    if final_judge_pass_policy == "p0":
        configured_pass_policy = (
            "branch_adaptive_sparse_harvest_v1"
            if int(scale) >= 30
            else "harvest_then_proof"
        )
    else:
        configured_pass_policy = str(final_judge_pass_policy)
    os.environ[
        "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY"
    ] = configured_pass_policy
    if (
        configured_pass_policy == "adaptive_sparse_harvest_v1"
        and int(adaptive_harvest_max_processed_labels) <= 0
    ):
        os.environ[
            "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC"
        ] = str(float(adaptive_harvest_cap_sec))
    else:
        os.environ.pop(
            "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC",
            None,
        )


def _solver_binding(
    *,
    data,
    profile: dict,
    tree_max_rounds: int,
    tree_max_columns_per_round: int,
    subset_dominance_enabled: bool,
    final_judge_pass_policy: str,
    adaptive_harvest_cap_sec: float,
    adaptive_harvest_max_processed_labels: int,
    sparse_harvest_strikes_before_proof: int,
) -> dict:
    configured_pass_policy = (
        (
            "branch_adaptive_sparse_harvest_v1"
            if int(data.scale) >= 30
            else "harvest_then_proof"
        )
        if final_judge_pass_policy == "p0"
        else str(final_judge_pass_policy)
    )
    payload = {
        "schema_version": (
            "lunar_ice_bpc.no_task_wait_v3_branch_solver_binding.v2"
        ),
        "baseline_id": BASELINE_ID,
        "instance_content_hash": data.instance_content_hash,
        "service_timing_policy_id": data.service_timing_policy_id,
        "baseline_config_path": str(BASELINE_CONFIG_PATH),
        "baseline_config_sha256": hashlib.sha256(
            BASELINE_CONFIG_PATH.read_bytes()
        ).hexdigest(),
        "backend": str(profile["backend"]),
        "engine_hash": spprc_engine_build_hash(str(profile["backend"])),
        "memory_limit_gb": float(profile["memory_gb"]),
        "subset_dominance_enabled": bool(
            subset_dominance_enabled
        ),
        "requested_final_judge_pass_policy": str(
            final_judge_pass_policy
        ),
        "live_sri_policy": "P0",
        "live_sri_policy_hash": LiveSriPolicy.named("P0").policy_hash,
        "root_max_rounds": int(profile["root_max_rounds"]),
        "root_harvest_target": int(profile["root_harvest_target"]),
        "tree_max_rounds": int(tree_max_rounds),
        "tree_max_columns_per_round": int(
            tree_max_columns_per_round
        ),
        "tree_max_nodes": int(profile["tree_max_nodes"]),
        "tree_max_depth": int(profile["tree_max_depth"]),
        "tail_dual_stabilization_enabled": True,
        "tail_dual_stabilization_alpha": 0.7,
        "tail_dual_stabilization_window": 5,
        "worker_pricer_kind": RELAXED_LABELING_WORKER,
        "final_judge_pass_policy": configured_pass_policy,
        "adaptive_harvest_cap_sec": (
            float(adaptive_harvest_cap_sec)
            if configured_pass_policy
            == "adaptive_sparse_harvest_v1"
            and int(adaptive_harvest_max_processed_labels) <= 0
            else None
        ),
        "adaptive_harvest_max_processed_labels": int(
            adaptive_harvest_max_processed_labels
        ),
        "sparse_harvest_strikes_before_proof": int(
            sparse_harvest_strikes_before_proof
        ),
    }
    return {**payload, "binding_hash": _sha256_json(payload)}


def _json_safe_top_level(payload: dict) -> dict:
    return {
        key: value
        for key, value in payload.items()
        if not str(key).startswith("_")
    }


def _node_primal_columns(payload: dict) -> tuple[dict, ...]:
    """Read the solved RMP primal from the solver's canonical master object."""

    master = payload.get("_master")
    if (
        master is not None
        and getattr(master, "rmp", None) is not None
    ):
        return tuple(master.rmp.primal_columns)
    return tuple(payload.get("primal_columns") or ())


def _warm_start_from_root_source(
    *,
    path: Path,
    data,
    split_manifest_hash: str,
    solver_binding: dict,
) -> tuple[tuple, dict]:
    source = _load_json(path)
    source_binding = source.get("solver_binding") or {}
    if (
        source.get("instance_content_hash")
        != data.instance_content_hash
        or str(source.get("split_manifest_hash") or "")
        != str(split_manifest_hash)
        or str(source_binding.get("baseline_id") or "") != BASELINE_ID
        or str(source_binding.get("engine_hash") or "")
        != str(solver_binding.get("engine_hash") or "")
        or str(source_binding.get("service_timing_policy_id") or "")
        != data.service_timing_policy_id
    ):
        raise SystemExit("root warm-start source binding mismatch")
    source_result = source.get("result") or {}
    columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in source_result.get("active_columns") or ()
    )
    if not columns:
        raise SystemExit("root warm-start source contains no active columns")
    metadata = {
        "source_path": str(path),
        "source_sha256": _sha256_json(source),
        "source_root_wall_sec": float(source.get("root_wall_sec") or 0.0),
        "source_collection_wall_sec": (
            float(source.get("root_wall_sec") or 0.0)
            + float(
                (source.get("root_warm_start") or {}).get(
                    "source_collection_wall_sec"
                )
                or (source.get("root_warm_start") or {}).get(
                    "source_root_wall_sec"
                )
                or 0.0
            )
        ),
        "source_root_exact_safe": bool(source.get("root_exact_safe")),
        "source_pricing_state": source_result.get("pricing_state"),
        "source_certificate_scope": source_result.get(
            "certificate_scope"
        ),
        "active_column_count": len(columns),
        "certificate_reused": False,
        "columns_only": True,
    }
    return columns, metadata


def _root_exact_safe(payload: dict) -> bool:
    final_judge = payload.get("final_judge") or {}
    return bool(
        payload.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and payload.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and (
            payload.get("uses_true_dual_bpc_certificate")
            or final_judge.get("uses_true_dual_bpc_certificate")
        )
        and (
            payload.get("pricing_rc_audit_pass")
            or final_judge.get("pricing_rc_audit_pass")
        )
    )


def _tree_exact_safe(payload: dict) -> bool:
    return bool(
        payload.get("algorithm_status") == "BPC_OPTIMAL"
        and payload.get("certificate_scope") == "BPC_TREE_OPTIMAL"
        and payload.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and payload.get("uses_true_dual_bpc_certificate")
        and payload.get("all_certificate_ledgers_valid")
        and int(payload.get("incomplete_node_count") or 0) == 0
        and not bool(payload.get("tree_deadline_hit"))
    )


def _node_lp_exact_safe(payload: dict) -> bool:
    return bool(
        payload.get("requested_node_status") == "NODE_LP_CERTIFIED"
        and payload.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and payload.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and payload.get("node_lp_bound_official")
        and payload.get("uses_true_dual_bpc_certificate")
        and payload.get("manual_rc_audit_pass")
        and payload.get("pricing_rc_audit_pass")
        and payload.get("final_judge_certifying_proof_kind")
        and (payload.get("certificate_ledger") or {}).get("valid")
    )


def _universe_safe(payload: dict) -> bool:
    branch_nodes = [
        node
        for node in payload.get("nodes", ())
        if node.get("node_status") == "BRANCHED"
    ]
    return all(
        node.get("legal_branch_shortlist_hash_before_sort")
        == node.get("legal_branch_shortlist_hash_after_sort")
        and int(node.get("guidance_branch_pair_drop_count") or 0) == 0
        for node in branch_nodes
    )


def _candidate_id(candidate: dict) -> str:
    left, right = sorted(
        (str(candidate["task_a"]), str(candidate["task_b"]))
    )
    return f"branch_pair:{left}|{right}"


def _path_hash(path: tuple[str, ...]) -> str:
    return hashlib.sha256(
        json.dumps(
            path,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _actionable_states(control: dict) -> list[dict]:
    states = []
    for node in control.get("nodes", ()):
        probe = node.get("fractional_branch_probe") or {}
        candidates = list(probe.get("candidates") or ())
        path = tuple(
            str(value)
            for value in node.get("development_branch_path_signature") or ()
        )
        if (
            node.get("node_status") != "BRANCHED"
            or len(candidates) < 3
            or node.get("legal_branch_shortlist_hash_before_sort")
            != node.get("legal_branch_shortlist_hash_after_sort")
            or int(node.get("guidance_branch_pair_drop_count") or 0) != 0
            or int(node.get("development_branch_selected_rank_index") or 0)
            != 0
        ):
            continue
        states.append(
            {
                "node_id": str(node["node_id"]),
                "path_signature": list(path),
                "path_hash": _path_hash(path),
                "depth": int(node.get("depth") or 0),
                "candidate_count": int(probe.get("candidate_count") or 0),
                "top3_candidate_ids": [
                    _candidate_id(candidate) for candidate in candidates[:3]
                ],
                "legal_branch_shortlist_hash_before_sort": str(
                    node.get(
                        "legal_branch_shortlist_hash_before_sort"
                    )
                    or ""
                ),
                "legal_branch_shortlist_hash_after_sort": str(
                    node.get(
                        "legal_branch_shortlist_hash_after_sort"
                    )
                    or ""
                ),
                "control_tree_elapsed_sec_at_exit": float(
                    node.get("tree_elapsed_sec_at_exit") or 0.0
                ),
            }
        )
    return sorted(
        states,
        key=lambda row: (
            int(row["depth"]),
            float(row["control_tree_elapsed_sec_at_exit"]),
            str(row["node_id"]),
        ),
    )


def _tree_call(
    *,
    data,
    active_columns: tuple,
    profile: dict,
    wall_time_limit_sec: float,
    max_rounds: int,
    max_columns_per_round: int,
    rank_by_path: dict[tuple[str, ...], int] | None = None,
    max_tree_nodes: int | None = None,
    max_branch_depth: int | None = None,
    certified_root_node: dict | None = None,
    certified_tree_state: dict | None = None,
    branch_snapshot_callback=None,
) -> tuple[dict, float]:
    started = perf_counter()
    result = solve_b3_branch_price_tree_baseline(
        data,
        initial_columns=active_columns,
        max_direct_tasks=len(data.task_ids),
        max_rounds_per_node=int(max_rounds),
        wall_time_limit_sec=float(wall_time_limit_sec),
        max_columns_per_round=int(max_columns_per_round),
        max_tree_nodes=int(
            profile["tree_max_nodes"]
            if max_tree_nodes is None
            else max_tree_nodes
        ),
        max_branch_depth=int(
            profile["tree_max_depth"]
            if max_branch_depth is None
            else max_branch_depth
        ),
        use_complete_universe_audit=False,
        run_b2_root_diagnostic=False,
        solve_b0_direct_first=False,
        tail_dual_stabilization_enabled=True,
        tail_dual_stabilization_alpha=0.7,
        tail_dual_stabilization_window=5,
        worker_pricer_kind=RELAXED_LABELING_WORKER,
        labeling_final_judge_enabled=True,
        labeling_final_judge_max_exact_tasks=len(data.task_ids),
        labeling_final_judge_exact_harvest_target=int(
            profile["root_harvest_target"]
        ),
        live_sri_policy="P0",
        development_branch_rank_index=0,
        development_branch_rank_by_path=rank_by_path,
        development_certified_root_node=certified_root_node,
        development_certified_tree_state=certified_tree_state,
        development_branch_snapshot_callback=(
            branch_snapshot_callback
        ),
    )
    return result, perf_counter() - started


def _opportunity_control_from_raw(
    *,
    data,
    raw: dict,
    initial_column_count: int,
    wall_sec: float,
) -> dict:
    """Build the one-node opportunity view from an exact parent payload."""

    active_columns = tuple(raw.get("_active_columns") or ())
    if not active_columns:
        active_columns = tuple(
            journey_column_from_solution_payload(data, row)
            for row in raw.get("active_columns") or ()
        )
    primal_columns = _node_primal_columns(raw)
    # ``_master`` is intentionally omitted from persisted JSON.  Preserve its
    # actual primal rows explicitly so replay does not interpret a solved
    # fractional parent as an empty primal.
    raw["primal_columns"] = primal_columns
    probe = (
        {"status": "NO_ACTIVE_COLUMNS", "candidates": []}
        if not active_columns
        else build_fractional_branch_probe(
            data.task_ids,
            primal_columns,
            active_columns,
            max_candidates=3,
        )
    )
    node = {
        **_json_safe_top_level(raw),
        "node_id": "node_000",
        "parent_node_id": None,
        "depth": 0,
        "branch_context": (raw.get("branch_context") or {}),
        "fractional_branch_probe": probe,
        "fractional_branch_probe_status": probe.get("status"),
        "development_branch_path_signature": [],
        "tree_global_column_count_at_entry": int(initial_column_count),
        "tree_global_column_count_at_exit": len(active_columns),
        "tree_globally_shared_new_column_count": max(
            0,
            len(active_columns) - int(initial_column_count),
        ),
        "tree_node_wall_time_sec": round(float(wall_sec), 6),
        "tree_elapsed_sec_at_exit": round(float(wall_sec), 6),
    }
    exact_parent = _opportunity_parent_exact_safe(node)
    return {
        "schema_version": (
            "lunar_ice_bpc.opportunity_parent_control.v1"
        ),
        "algorithm_status": "BPC_INCOMPLETE_PRICING",
        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
        "pricing_state": "INCOMPLETE_LIMIT",
        "uses_true_dual_bpc_certificate": False,
        "tree_closed": False,
        "tree_deadline_hit": not exact_parent,
        "incomplete_node_count": 0 if exact_parent else 1,
        "node_count": 1,
        "expanded_node_count": 1,
        "incumbent_objective": None,
        "global_lower_bound": None,
        "nodes": [node],
        "opportunity_parent_only": True,
        "tree_result_is_exact_bpc": False,
        "guidance_filter_count": 0,
    }


def _opportunity_parent_call(
    *,
    data,
    initial_columns: tuple,
    profile: dict,
    wall_time_limit_sec: float,
    max_rounds: int,
    max_columns_per_round: int,
) -> tuple[dict, dict, float]:
    """Close only the P0 parent node and retain its active columns."""

    started = perf_counter()
    raw = solve_node_pricing_with_live_sri(
        data,
        policy=LiveSriPolicy.named("P0"),
        depth=0,
        branch_context=BranchContext(),
        cut_context=CutContext(),
        cut_lineage=CutLineage(
            policy_version=LiveSriPolicy.named("P0").version
        ),
        node_id="node_000",
        ancestor_path=tuple(),
        initial_columns=initial_columns,
        incumbent_objective=None,
        max_direct_tasks=len(data.task_ids),
        max_rounds=int(max_rounds),
        wall_time_limit_sec=float(wall_time_limit_sec),
        max_columns_per_round=int(max_columns_per_round),
        b0_direct=_diagnostic_b0_placeholder(data),
        tail_dual_stabilization_enabled=True,
        tail_dual_stabilization_alpha=0.7,
        tail_dual_stabilization_window=5,
        worker_pricer_kind=RELAXED_LABELING_WORKER,
        labeling_final_judge_enabled=True,
        labeling_final_judge_max_exact_tasks=len(data.task_ids),
        labeling_final_judge_exact_harvest_target=int(
            profile["root_harvest_target"]
        ),
    )
    wall_sec = perf_counter() - started
    control = _opportunity_control_from_raw(
        data=data,
        raw=raw,
        initial_column_count=len(initial_columns),
        wall_sec=wall_sec,
    )
    return raw, control, wall_sec


def _opportunity_parent_exact_safe(node: dict) -> bool:
    return bool(
        node.get("node_status") == "NODE_LP_CERTIFIED"
        and node.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and node.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and node.get("node_lp_bound_official")
        and node.get("uses_true_dual_bpc_certificate")
        and node.get("manual_rc_audit_pass")
        and node.get("pricing_rc_audit_pass")
        and node.get("final_judge_certifying_proof_kind")
        and node.get("branch_pricing_audit_pass")
        and node.get("cut_pricing_audit_pass")
        and (node.get("certificate_ledger") or {}).get("valid")
    )


def _replay_exact_opportunity_parent_source(
    *,
    data,
    source: dict,
) -> tuple[dict, dict, float]:
    """Restore omitted primal rows without rerunning exact pricing."""

    raw = dict(source.get("result") or {})
    if not _opportunity_parent_exact_safe(raw):
        raise ValueError("persisted P0 parent source is not exact-safe")
    active_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in raw.get("active_columns") or ()
    )
    if not active_columns:
        raise ValueError("persisted P0 parent source has no active columns")
    cut_context = cut_context_from_payload(raw.get("cut_context"))
    cut_lineage = cut_lineage_from_payload(raw.get("cut_lineage"))
    if (
        cut_context.active_cut_context_hash
        != str(raw.get("active_cut_context_hash") or "")
        or cut_lineage.cut_lineage_hash
        != str(raw.get("cut_lineage_hash") or "")
    ):
        raise ValueError("persisted P0 parent cut binding mismatch")
    master = solve_root_journey_master(
        data,
        active_columns,
        rmp_iteration_id=(
            "v3_branch_opportunity_parent_snapshot_replay:"
            f"{data.instance_content_hash}"
        ),
        branch_context=BranchContext(),
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        live_cut_policy_hash=str(raw.get("live_cut_policy_hash") or ""),
        separator_policy_version=str(
            raw.get("separator_policy_version") or ""
        ),
    )
    if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
        raise ValueError("persisted P0 parent restricted replay failed")
    expected_bound = raw.get("node_lp_bound")
    observed_bound = master.rmp.objective_bound
    if (
        expected_bound is None
        or observed_bound is None
        or abs(float(expected_bound) - float(observed_bound)) > 1.0e-6
    ):
        raise ValueError("persisted P0 parent replay bound mismatch")
    raw["_active_columns"] = active_columns
    raw["_master"] = master
    raw["primal_columns"] = tuple(master.rmp.primal_columns)
    raw["parent_snapshot_replayed_from_exact_source"] = True
    wall_sec = float(source.get("root_wall_sec") or 0.0)
    control = _opportunity_control_from_raw(
        data=data,
        raw=raw,
        initial_column_count=int(
            raw.get("loaded_column_count") or len(active_columns)
        ),
        wall_sec=wall_sec,
    )
    control["parent_snapshot_replayed_from_exact_source"] = True
    control["parent_snapshot_replay_ran_pricing"] = False
    return raw, control, wall_sec


def _arm_summary(
    *,
    result: dict,
    tree_wall_sec: float,
    root_wall_sec: float,
    lifecycle_overhead_sec: float,
    target_path: tuple[str, ...] | None,
    requested_rank: int,
) -> dict:
    target_rows = [
        node
        for node in result.get("nodes", ())
        if (
            "development_branch_path_signature" in node
            and tuple(
                node.get("development_branch_path_signature") or ()
            )
            == tuple(target_path or ())
        )
    ]
    target = target_rows[0] if len(target_rows) == 1 else {}
    target_candidates = list(
        (target.get("fractional_branch_probe") or {}).get("candidates")
        or ()
    )[:3]
    target_candidate_ids = [
        _candidate_id(candidate) for candidate in target_candidates
    ]
    selected_rank = target.get(
        "development_branch_selected_rank_index"
    )
    selected_candidate_id = (
        target_candidate_ids[int(selected_rank)]
        if (
            selected_rank is not None
            and 0 <= int(selected_rank) < len(target_candidate_ids)
        )
        else None
    )
    return {
        "requested_rank_index": int(requested_rank),
        "target_path_signature": list(target_path or ()),
        "target_path_hash": _path_hash(tuple(target_path or ())),
        "target_path_reached_once": len(target_rows) == 1,
        "target_node_id": target.get("node_id"),
        "target_selected_rank_index": target.get(
            "development_branch_selected_rank_index"
        ),
        "target_selected_candidate_id": selected_candidate_id,
        "target_top3_candidate_ids": target_candidate_ids,
        "target_legal_branch_shortlist_hash_before_sort": target.get(
            "legal_branch_shortlist_hash_before_sort"
        ),
        "target_legal_branch_shortlist_hash_after_sort": target.get(
            "legal_branch_shortlist_hash_after_sort"
        ),
        "target_fallback_to_p0": bool(
            target.get("development_branch_rank_fallback_to_p0")
        ),
        "tree_wall_sec": round(float(tree_wall_sec), 6),
        "root_wall_sec": round(float(root_wall_sec), 6),
        "guidance_lifecycle_overhead_sec": round(
            float(lifecycle_overhead_sec), 6
        ),
        "matched_end_to_end_wall_sec": round(
            float(root_wall_sec)
            + float(tree_wall_sec)
            + float(lifecycle_overhead_sec),
            6,
        ),
        "exact_safe": _tree_exact_safe(result),
        "universe_safe": _universe_safe(result),
        "objective": result.get("incumbent_objective"),
        "global_lower_bound": result.get("global_lower_bound"),
        "node_count": int(result.get("node_count") or 0),
        "expanded_node_count": int(result.get("expanded_node_count") or 0),
        "incomplete_node_count": int(result.get("incomplete_node_count") or 0),
        "tree_result_sha256": _sha256_json(result),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument(
        "--split-manifest",
        default=(
            "data/gat_p0v2/"
            "p0_no_task_wait_v3_gat_split_rebind_manifest.json"
        ),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--root-wall-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--tree-wall-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--tree-max-rounds", type=int, default=16)
    parser.add_argument("--tree-max-columns-per-round", type=int, default=128)
    parser.add_argument("--max-states", type=int, default=1)
    parser.add_argument(
        "--subset-dominance",
        choices=("on", "off"),
        default="on",
        help=(
            "Development-only exact policy arm. Both choices preserve the "
            "legal label universe; the default matches P0."
        ),
    )
    parser.add_argument(
        "--final-judge-pass-policy",
        choices=("p0", "adaptive_sparse_harvest_v1", "proof_only"),
        default="p0",
        help=(
            "Development-only exact pass-mode arm. p0 preserves the frozen "
            "scale policy; adaptive switches a sparse harvest tail to an "
            "explicit exact proof on the next dual; proof_only is an "
            "oracle-headroom control and is never a deployment default."
        ),
    )
    parser.add_argument(
        "--adaptive-harvest-cap-sec",
        type=float,
        default=2.0,
        help=(
            "Development-only wall cap for each adaptive harvest pass. "
            "It is ignored by p0 and proof_only."
        ),
    )
    parser.add_argument(
        "--adaptive-harvest-max-processed-labels",
        type=int,
        default=0,
        help=(
            "Development-only deterministic harvest work budget. Positive "
            "values replace the soft wall cap; zero preserves wall-cap mode."
        ),
    )
    parser.add_argument(
        "--adaptive-sparse-harvest-strikes-before-proof",
        type=int,
        default=1,
        help=(
            "Development-only deterministic control. Require this many "
            "consecutive sparse work-budget harvest passes before scheduling "
            "proof_only. One preserves adaptive_sparse_harvest_v1."
        ),
    )
    parser.add_argument(
        "--tail-trigger-policy",
        choices=TAIL_TRIGGER_POLICY_IDS,
        default=None,
        help=(
            "Development-only Torch-free admission rule. When set, only "
            "the first qualifying tail state can receive counterfactual arms."
        ),
    )
    parser.add_argument(
        "--root-warm-start-source",
        default=None,
        help=(
            "Development-only root_source.json whose bound columns may seed "
            "the new solve. No certificate or exact status is reused."
        ),
    )
    parser.add_argument(
        "--p0-parent-warm-start-source",
        default=None,
        help=(
            "Opportunity-only P0 parent source whose columns may seed a "
            "longer parent closure. Certificates are never reused."
        ),
    )
    parser.add_argument(
        "--opportunity-only",
        action="store_true",
        help=(
            "Close only the P0 root node LP and record whether its legal "
            "shortlist has at least three candidates. The intentionally "
            "truncated tree is never treated as an exact BPC result."
        ),
    )
    parser.add_argument(
        "--root-source-only",
        action="store_true",
        help=(
            "Stop after the independently certified root source. This is "
            "used for matched exact root-policy action gates."
        ),
    )
    parser.add_argument(
        "--round-snapshot-dir",
        default=None,
        help=(
            "Development-only directory for deduplicated pre-pricing root "
            "state snapshots. Existing non-empty directories are rejected."
        ),
    )
    parser.add_argument(
        "--opportunity-use-bound-root-columns",
        action="store_true",
        help=(
            "For opportunity collection only, use the columns from "
            "--root-warm-start-source directly as a seed for an independently "
            "certified P0 parent. The source root certificate is not reused."
        ),
    )
    parser.add_argument(
        "--emulated-guidance-lifecycle-overhead-sec",
        type=float,
        default=0.02,
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.opportunity_use_bound_root_columns and (
        not args.opportunity_only
        or not args.root_warm_start_source
    ):
        raise SystemExit(
            "bound root columns require --opportunity-only and "
            "--root-warm-start-source"
        )
    if args.round_snapshot_dir and args.resume:
        raise SystemExit(
            "--round-snapshot-dir cannot be combined with --resume"
        )

    instance_path = (ROOT / args.instance).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_lunar_ice_data(_load_json(instance_path))
    split_manifest = _load_json(split_path)
    split_manifest_hash = str(
        split_manifest.get("manifest_hash") or _sha256_json(split_manifest)
    )
    if data.instance_content_hash not in _development_hashes(split_manifest):
        raise SystemExit("state oracle accepts V3 development instances only")
    if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise SystemExit("instance service-timing policy mismatch")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit("state oracle currently accepts scale5/10/20/30 only")
    subset_dominance_enabled = args.subset_dominance == "on"
    if (
        not math.isfinite(float(args.adaptive_harvest_cap_sec))
        or float(args.adaptive_harvest_cap_sec) <= 0.0
    ):
        raise SystemExit("--adaptive-harvest-cap-sec must be finite and positive")
    if int(args.adaptive_harvest_max_processed_labels) < 0:
        raise SystemExit(
            "--adaptive-harvest-max-processed-labels must be nonnegative"
        )
    if int(args.adaptive_sparse_harvest_strikes_before_proof) < 1:
        raise SystemExit(
            "--adaptive-sparse-harvest-strikes-before-proof "
            "must be at least one"
        )
    _configure_environment(
        scale=int(data.scale),
        profile=profile,
        subset_dominance_enabled=subset_dominance_enabled,
        final_judge_pass_policy=str(
            args.final_judge_pass_policy
        ),
        adaptive_harvest_cap_sec=float(
            args.adaptive_harvest_cap_sec
        ),
        adaptive_harvest_max_processed_labels=int(
            args.adaptive_harvest_max_processed_labels
        ),
    )
    solver_binding = _solver_binding(
        data=data,
        profile=profile,
        tree_max_rounds=int(args.tree_max_rounds),
        tree_max_columns_per_round=int(
            args.tree_max_columns_per_round
        ),
        subset_dominance_enabled=subset_dominance_enabled,
        final_judge_pass_policy=str(
            args.final_judge_pass_policy
        ),
        adaptive_harvest_cap_sec=float(
            args.adaptive_harvest_cap_sec
        ),
        adaptive_harvest_max_processed_labels=int(
            args.adaptive_harvest_max_processed_labels
        ),
        sparse_harvest_strikes_before_proof=int(
            args.adaptive_sparse_harvest_strikes_before_proof
        ),
    )
    round_snapshot_recorder = None
    if args.round_snapshot_dir:
        round_snapshot_dir = (
            ROOT / args.round_snapshot_dir
        ).resolve()
        if round_snapshot_dir.is_dir() and any(
            round_snapshot_dir.iterdir()
        ):
            raise SystemExit(
                "round snapshot directory already exists and is non-empty"
            )
        round_snapshot_recorder = (
            _DevelopmentRoundSnapshotRecorder(
                output_dir=round_snapshot_dir,
                data=data,
                solver_binding=solver_binding,
                split_manifest_hash=split_manifest_hash,
            )
        )
    warm_start_columns: tuple = tuple()
    warm_start_metadata: dict | None = None
    if args.root_warm_start_source:
        warm_start_path = (ROOT / args.root_warm_start_source).resolve()
        warm_start_columns, warm_start_metadata = (
            _warm_start_from_root_source(
                path=warm_start_path,
                data=data,
                split_manifest_hash=split_manifest_hash,
                solver_binding=solver_binding,
            )
        )

    root_path = output_dir / "root_source.json"
    if args.resume and root_path.is_file():
        root_payload = _load_json(root_path)
        if (
            root_payload.get("instance_content_hash")
            != data.instance_content_hash
        ):
            raise SystemExit("persisted root source instance hash mismatch")
        persisted_binding = root_payload.get("solver_binding") or {}
        if (
            persisted_binding.get("binding_hash")
            != solver_binding["binding_hash"]
        ):
            raise SystemExit("persisted root source solver binding mismatch")
        if (
            str(root_payload.get("split_manifest_hash") or "")
            != split_manifest_hash
        ):
            raise SystemExit("persisted root source split manifest mismatch")
        root_result = dict(root_payload["result"])
        root_wall = float(root_payload["root_wall_sec"])
    else:
        if args.opportunity_use_bound_root_columns:
            source = _load_json(
                (ROOT / args.root_warm_start_source).resolve()
            )
            root_result = {
                "schema_version": (
                    "lunar_ice_bpc.opportunity_column_seed.v1"
                ),
                "certificate_scope": "NONE",
                "pricing_state": "COLUMN_SEED_ONLY",
                "uses_true_dual_bpc_certificate": False,
                "active_columns": list(
                    (source.get("result") or {}).get(
                        "active_columns"
                    )
                    or ()
                ),
            }
            root_wall = 0.0
        else:
            started = perf_counter()
            root_result = solve_node_pricing_with_b2b_r3(
                data,
                node_id="root",
                initial_columns=warm_start_columns or None,
                max_direct_tasks=len(data.task_ids),
                max_rounds=int(profile["root_max_rounds"]),
                wall_time_limit_sec=float(args.root_wall_time_limit_sec),
                max_columns_per_round=int(
                    profile["root_harvest_target"]
                ),
                b0_direct=_diagnostic_b0_placeholder(data),
                tail_dual_stabilization_enabled=True,
                tail_dual_stabilization_alpha=0.7,
                tail_dual_stabilization_window=5,
                worker_pricer_kind=RELAXED_LABELING_WORKER,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=len(data.task_ids),
                labeling_final_judge_exact_harvest_target=int(
                    profile["root_harvest_target"]
                ),
                labeling_final_judge_harvest_max_processed_labels=int(
                    args.adaptive_harvest_max_processed_labels
                ),
                return_active_columns_payload=True,
                development_round_snapshot_callback=(
                    round_snapshot_recorder
                ),
                development_sparse_harvest_strikes_before_proof=int(
                    args.adaptive_sparse_harvest_strikes_before_proof
                ),
            )
            root_wall = perf_counter() - started
            if round_snapshot_recorder is not None:
                round_snapshot_recorder.finalize()
        root_payload = {
            "schema_version": (
                "lunar_ice_bpc.no_task_wait_v3_branch_root_source.v1"
            ),
            "development_only": True,
            "deployable": False,
            "instance_path": str(instance_path),
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "service_timing_policy_id": data.service_timing_policy_id,
            "split_manifest_hash": split_manifest_hash,
            "solver_binding": solver_binding,
            "root_wall_time_limit_sec": float(
                args.root_wall_time_limit_sec
            ),
            "root_wall_sec": round(float(root_wall), 6),
            "root_exact_safe": _root_exact_safe(root_result),
            "root_column_seed_only": bool(
                args.opportunity_use_bound_root_columns
            ),
            "root_warm_start": warm_start_metadata,
            "root_warm_start_certificate_reused": False,
            "result": _json_safe_top_level(root_result),
        }
        _write_json(root_path, root_payload)
    if (
        not args.opportunity_use_bound_root_columns
        and not _root_exact_safe(root_result)
    ):
        raise SystemExit("common root source did not close exactly")
    if args.root_source_only:
        print(
            json.dumps(
                {
                    "instance_id": data.instance_id,
                    "root_exact_safe": True,
                    "root_wall_sec": round(float(root_wall), 6),
                    "subset_dominance_enabled": (
                        subset_dominance_enabled
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    active_payload = root_result.get("active_columns") or ()
    active_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in active_payload
    )
    if not active_columns:
        raise SystemExit("common root source contains no active columns")
    parent_initial_columns = active_columns
    parent_warm_metadata = None
    if args.p0_parent_warm_start_source:
        parent_warm_path = (
            ROOT / args.p0_parent_warm_start_source
        ).resolve()
        parent_initial_columns, parent_warm_metadata = (
            _warm_start_from_root_source(
                path=parent_warm_path,
                data=data,
                split_manifest_hash=split_manifest_hash,
                solver_binding=solver_binding,
            )
        )

    control_path = output_dir / "control_rank0_tree.json"
    control_summary_path = output_dir / "control_rank0_summary.json"
    if (
        args.resume
        and control_path.is_file()
        and control_summary_path.is_file()
    ):
        persisted_control = _load_json(control_path)
        persisted_control_summary = _load_json(control_summary_path)
        if (
            _tree_exact_safe(persisted_control)
            and _universe_safe(persisted_control)
            and bool(persisted_control_summary.get("exact_safe"))
        ):
            control = persisted_control
            control_summary = persisted_control_summary
            control_wall = float(control_summary["tree_wall_sec"])
        else:
            control = None
    else:
        control = None
    replayed_parent_source = False
    parent_snapshot_source_path = output_dir / "p0_parent_source.json"
    if control is None:
        if args.opportunity_only:
            persisted_parent_path = output_dir / "p0_parent_source.json"
            if args.resume and persisted_parent_path.is_file():
                persisted_parent = _load_json(persisted_parent_path)
                persisted_binding = (
                    persisted_parent.get("solver_binding") or {}
                )
                if (
                    str(
                        persisted_parent.get("instance_content_hash")
                        or ""
                    )
                    != data.instance_content_hash
                    or str(
                        persisted_parent.get("split_manifest_hash")
                        or ""
                    )
                    != split_manifest_hash
                    or str(
                        persisted_binding.get("binding_hash")
                        or ""
                    )
                    != solver_binding["binding_hash"]
                ):
                    raise SystemExit(
                        "persisted P0 parent source binding mismatch"
                    )
                raw_parent, control, control_wall = (
                    _replay_exact_opportunity_parent_source(
                        data=data,
                        source=persisted_parent,
                    )
                )
                replayed_parent_source = True
                parent_snapshot_source_path = (
                    output_dir / "p0_parent_snapshot_replay.json"
                )
                _write_json(
                    parent_snapshot_source_path,
                    {
                        **persisted_parent,
                        "schema_version": (
                            "lunar_ice_bpc.p0_parent_snapshot_replay.v1"
                        ),
                        "training_authorized": False,
                        "deployable": False,
                        "source_parent_sha256": _sha256_json(
                            persisted_parent
                        ),
                        "parent_snapshot_replay_ran_pricing": False,
                        "certificate_reused_for_pricing": False,
                        "result": _json_safe_top_level(raw_parent),
                    },
                )
            else:
                raw_parent, control, control_wall = _opportunity_parent_call(
                    data=data,
                    initial_columns=parent_initial_columns,
                    profile=profile,
                    wall_time_limit_sec=float(
                        args.tree_wall_time_limit_sec
                    ),
                    max_rounds=int(args.tree_max_rounds),
                    max_columns_per_round=int(
                        args.tree_max_columns_per_round
                    ),
                )
            if not replayed_parent_source:
                _write_json(
                    output_dir / "p0_parent_source.json",
                    {
                        "schema_version": (
                            "lunar_ice_bpc.p0_parent_source.v1"
                        ),
                        "development_only": True,
                        "deployable": False,
                        "training_authorized": False,
                        "instance_id": data.instance_id,
                        "instance_content_hash": (
                            data.instance_content_hash
                        ),
                        "service_timing_policy_id": (
                            data.service_timing_policy_id
                        ),
                        "split_manifest_hash": split_manifest_hash,
                        "solver_binding": solver_binding,
                        "root_wall_sec": round(
                            float(control_wall),
                            6,
                        ),
                        "root_exact_safe": (
                            _opportunity_parent_exact_safe(
                                control["nodes"][0]
                            )
                        ),
                        "root_warm_start": parent_warm_metadata,
                        "certificate_reused": False,
                        "columns_only_warm_start": True,
                        "result": _json_safe_top_level(raw_parent),
                    },
                )
        else:
            control, control_wall = _tree_call(
                data=data,
                active_columns=active_columns,
                profile=profile,
                wall_time_limit_sec=float(args.tree_wall_time_limit_sec),
                max_rounds=int(args.tree_max_rounds),
                max_columns_per_round=int(args.tree_max_columns_per_round),
            )
        _write_json(control_path, control)
        control_summary = _arm_summary(
            result=control,
            tree_wall_sec=control_wall,
            root_wall_sec=root_wall,
            lifecycle_overhead_sec=0.0,
            target_path=None,
            requested_rank=0,
        )
        _write_json(control_summary_path, control_summary)
    if args.opportunity_only:
        nodes = list(control.get("nodes") or ())
        root_node = nodes[0] if nodes else {}
        root_node_exact_safe = (
            _opportunity_parent_exact_safe(root_node)
            if bool(control.get("opportunity_parent_only"))
            else _node_lp_exact_safe(root_node)
        )
        candidates = list(
            (root_node.get("fractional_branch_probe") or {}).get(
                "candidates"
            )
            or ()
        )
        candidate_ids = [_candidate_id(row) for row in candidates]
        universe_hash = canonical_universe_hash(
            candidate_ids,
            universe_kind="p0_branch_shortlist",
        )
        parent_snapshot_eligible = bool(
            root_node_exact_safe and len(candidates) >= 3
        )
        if parent_snapshot_eligible:
            root_node.update(
                {
                    "development_branch_path_signature": [],
                    "development_branch_requested_rank_index": 0,
                    "development_branch_selected_rank_index": 0,
                    "development_branch_rank_fallback_to_p0": False,
                    "legal_branch_shortlist_hash_before_sort": (
                        universe_hash
                    ),
                    "legal_branch_shortlist_hash_after_sort": (
                        universe_hash
                    ),
                    "guidance_branch_pair_drop_count": 0,
                    "opportunity_parent_snapshot_eligible": True,
                }
            )
            control["nodes"][0] = root_node
            _write_json(control_path, control)
        opportunity_status = (
            "EXACT_ACTIONABLE_ROOT"
            if root_node_exact_safe and len(candidates) >= 3
            else (
                "EXACT_NONACTIONABLE_ROOT"
                if root_node_exact_safe
                else "TREE_ROOT_CENSORED"
            )
        )
        opportunity_report = {
            "schema_version": (
                "lunar_ice_bpc.no_task_wait_v3_branch_opportunity.v2"
            ),
            "development_only": True,
            "deployable": False,
            "training_authorized": False,
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "service_timing_policy_id": data.service_timing_policy_id,
            "split_manifest_hash": split_manifest_hash,
            "solver_binding": solver_binding,
            "root_source_exact_safe": _root_exact_safe(root_result),
            "p0_root_node_exact_safe": root_node_exact_safe,
            "opportunity_status": opportunity_status,
            "candidate_count": len(candidates),
            "top3_candidate_ids": candidate_ids[:3],
            "legal_branch_shortlist_hash_before_sort": universe_hash,
            "legal_branch_shortlist_hash_after_sort": universe_hash,
            "guidance_branch_pair_drop_count": 0,
            "guidance_filter_count": 0,
            "opportunity_parent_snapshot_eligible": (
                parent_snapshot_eligible
            ),
            "root_wall_sec": round(float(root_wall), 6),
            "p0_root_node_wall_sec": round(float(control_wall), 6),
            "root_warm_start": root_payload.get("root_warm_start"),
            "p0_parent_warm_start": parent_warm_metadata,
            "p0_parent_source_path": str(
                parent_snapshot_source_path
            ),
            "matched_end_to_end_wall_sec": round(
                float(root_wall) + float(control_wall),
                6,
            ),
            "matched_collection_wall_including_warm_source_sec": round(
                float(root_wall)
                + float(control_wall)
                + float(
                    (
                        root_payload.get("root_warm_start")
                        or {}
                    ).get("source_collection_wall_sec")
                    or 0.0
                )
                + float(
                    (parent_warm_metadata or {}).get(
                        "source_collection_wall_sec"
                    )
                    or (parent_warm_metadata or {}).get(
                        "source_root_wall_sec"
                    )
                    or 0.0
                ),
                6,
            ),
            "tree_truncation_is_intentional": True,
            "tree_truncation_reason": "OPPORTUNITY_ONLY_NODE_LIMIT",
            "opportunity_parent_solver": (
                "exact_parent_snapshot_replay_no_pricing_v1"
                if replayed_parent_source
                else (
                    "direct_live_sri_parent_with_active_columns_v1"
                    if bool(control.get("opportunity_parent_only"))
                    else "legacy_truncated_tree"
                )
            ),
            "parent_snapshot_replayed_from_exact_source": (
                replayed_parent_source
            ),
            "tree_result_is_exact_bpc": False,
            "tree_result_sha256": _sha256_json(control),
        }
        _write_json(
            output_dir / "branch_opportunity_report.json",
            opportunity_report,
        )
        print(
            json.dumps(
                {
                    "instance_id": data.instance_id,
                    "scale": int(data.scale),
                    "opportunity_status": opportunity_status,
                    "candidate_count": len(candidates),
                    "p0_root_node_exact_safe": root_node_exact_safe,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if root_node_exact_safe else 1
    if not _tree_exact_safe(control) or not _universe_safe(control):
        raise SystemExit("P0 control tree did not close exact-safe")

    states = _actionable_states(control)
    tail_annotations: list[dict] = []
    tail_triggered_states = states
    if args.tail_trigger_policy is not None:
        tail_annotations = annotate_branch_tail_events(
            nodes=list(control.get("nodes") or ()),
            root_wall_sec=float(root_wall),
            scale=int(data.scale),
            policy_id=str(args.tail_trigger_policy),
        )
        annotation_by_node = {
            str(row["node_id"]): row for row in tail_annotations
        }
        states = [
            {
                **state,
                **annotation_by_node[str(state["node_id"])],
            }
            for state in states
        ]
        tail_triggered_states = [
            state for state in states if state["tail_triggered"] is True
        ]
        if len(tail_triggered_states) > 1:
            raise SystemExit("one-shot tail trigger selected multiple states")
    selected_states = tail_triggered_states[
        : max(0, int(args.max_states))
    ]
    state_reports = []
    for state_index, state in enumerate(selected_states):
        path = tuple(state["path_signature"])
        arms = []
        for rank in (1, 2):
            arm_path = (
                output_dir
                / f"state_{state_index:03d}_{state['path_hash'][:12]}"
                / f"rank_{rank}_tree.json"
            )
            arm_summary_path = arm_path.with_name(f"rank_{rank}_summary.json")
            if (
                args.resume
                and arm_path.is_file()
            ):
                persisted_result = _load_json(arm_path)
                persisted_summary = (
                    _load_json(arm_summary_path)
                    if arm_summary_path.is_file()
                    else {}
                )
                persisted_arm = _arm_summary(
                    result=persisted_result,
                    tree_wall_sec=float(
                        persisted_summary.get("tree_wall_sec")
                        or persisted_result.get("tree_wall_time_sec")
                        or 0.0
                    ),
                    root_wall_sec=root_wall,
                    lifecycle_overhead_sec=float(
                        args.emulated_guidance_lifecycle_overhead_sec
                    ),
                    target_path=path,
                    requested_rank=rank,
                )
                if (
                    bool(persisted_arm.get("exact_safe"))
                    and bool(persisted_arm.get("universe_safe"))
                    and bool(persisted_arm.get("target_path_reached_once"))
                    and not bool(persisted_arm.get("target_fallback_to_p0"))
                    and int(
                        persisted_arm.get("target_selected_rank_index") or -1
                    )
                    == int(rank)
                    and persisted_arm.get(
                        "target_top3_candidate_ids"
                    )
                    == state["top3_candidate_ids"]
                    and str(
                        persisted_arm.get(
                            "target_legal_branch_shortlist_hash_before_sort"
                        )
                        or ""
                    )
                    == str(
                        state[
                            "legal_branch_shortlist_hash_before_sort"
                        ]
                    )
                ):
                    arm = persisted_arm
                    _write_json(arm_summary_path, arm)
                else:
                    arm = None
            else:
                arm = None
            if arm is None:
                result, tree_wall = _tree_call(
                    data=data,
                    active_columns=active_columns,
                    profile=profile,
                    wall_time_limit_sec=float(
                        args.tree_wall_time_limit_sec
                    ),
                    max_rounds=int(args.tree_max_rounds),
                    max_columns_per_round=int(
                        args.tree_max_columns_per_round
                    ),
                    rank_by_path={path: rank},
                )
                _write_json(arm_path, result)
                arm = _arm_summary(
                    result=result,
                    tree_wall_sec=tree_wall,
                    root_wall_sec=root_wall,
                    lifecycle_overhead_sec=float(
                        args.emulated_guidance_lifecycle_overhead_sec
                    ),
                    target_path=path,
                    requested_rank=rank,
                )
                _write_json(arm_summary_path, arm)
            arms.append(arm)

        control_e2e = float(control_summary["matched_end_to_end_wall_sec"])
        for arm in arms:
            arm["counterfactual_universe_matches_control"] = bool(
                arm.get("target_top3_candidate_ids")
                == state["top3_candidate_ids"]
                and str(
                    arm.get(
                        "target_legal_branch_shortlist_hash_before_sort"
                    )
                    or ""
                )
                == str(
                    state["legal_branch_shortlist_hash_before_sort"]
                )
            )
        eligible = [
            arm
            for arm in arms
            if (
                arm["exact_safe"]
                and arm["universe_safe"]
                and arm["target_path_reached_once"]
                and not arm["target_fallback_to_p0"]
                and int(arm["target_selected_rank_index"]) == int(
                    arm["requested_rank_index"]
                )
                and arm["objective"] == control_summary["objective"]
                and arm[
                    "counterfactual_universe_matches_control"
                ]
            )
        ]
        complete_gold = len(eligible) == 2
        best = min(
            eligible,
            key=lambda row: float(row["matched_end_to_end_wall_sec"]),
            default=None,
        )
        best_wall = (
            control_e2e
            if best is None or not complete_gold
            else min(
                control_e2e,
                float(best["matched_end_to_end_wall_sec"]),
            )
        )
        state_reports.append(
            {
                **state,
                "arms": arms,
                "eligible_alternative_count": len(eligible),
                "complete_matched_e2e_gold": complete_gold,
                "counterfactual_universe_binding_required": True,
                "oracle_selected_rank_index": (
                    None
                    if not complete_gold
                    else 0
                    if best is None
                    or float(best["matched_end_to_end_wall_sec"])
                    >= control_e2e
                    else int(best["requested_rank_index"])
                ),
                "oracle_net_gain_sec": (
                    None
                    if not complete_gold
                    else round(
                        max(0.0, control_e2e - best_wall), 6
                    )
                ),
                "oracle_net_gain_ratio": (
                    None
                    if not complete_gold
                    else round(
                        max(0.0, control_e2e - best_wall)
                        / control_e2e
                        if control_e2e > 0.0
                        else 0.0,
                        9,
                    )
                ),
            }
        )

    report = {
        "schema_version": (
            "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
        ),
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "service_timing_policy_id": data.service_timing_policy_id,
        "solver_binding": solver_binding,
        "root_wall_time_limit_sec": float(args.root_wall_time_limit_sec),
        "tree_wall_time_limit_sec": float(args.tree_wall_time_limit_sec),
        "scale": int(data.scale),
        "split_manifest_hash": split_manifest_hash,
        "root_source_sha256": _sha256_json(root_payload),
        "root_warm_start": root_payload.get("root_warm_start"),
        "root_exact_safe": _root_exact_safe(root_result),
        "control": control_summary,
        "control_exact_safe": _tree_exact_safe(control),
        "control_universe_safe": _universe_safe(control),
        "actionable_state_count": len(states),
        "tail_trigger_policy_id": args.tail_trigger_policy,
        "tail_trigger_call_count": (
            0
            if args.tail_trigger_policy is None
            else len(tail_triggered_states)
        ),
        "tail_trigger_annotations": tail_annotations,
        "tail_triggered_states": (
            []
            if args.tail_trigger_policy is None
            else tail_triggered_states
        ),
        "torch_imported_before_tail_trigger": False,
        "checkpoint_loaded_before_tail_trigger": False,
        "selected_state_count": len(selected_states),
        "state_reports": state_reports,
        "one_deviation_only": True,
        "post_deviation_policy": "p0_rank0",
        "guidance_filter_count": 0,
    }
    _write_json(output_dir / "state_oracle_report.json", report)
    print(
        json.dumps(
            {
                "instance_id": report["instance_id"],
                "scale": report["scale"],
                "root_exact_safe": report["root_exact_safe"],
                "control_exact_safe": report["control_exact_safe"],
                "actionable_state_count": report["actionable_state_count"],
                "selected_state_count": report["selected_state_count"],
                "positive_state_count": sum(
                    float(row["oracle_net_gain_sec"]) > 0.0
                    for row in state_reports
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
