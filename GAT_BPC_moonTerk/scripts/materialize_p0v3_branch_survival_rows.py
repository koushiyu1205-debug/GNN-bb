#!/usr/bin/env python3
"""Materialize leak-free child-survival rows from matched P0 V3 probes."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite, log1p
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.branch_survival import (  # noqa: E402
    BRANCH_CHILD_SURVIVAL_RMST_OBJECTIVE_V1,
    BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2,
    BRANCH_NODE_FEATURE_SCHEMA_V2,
    BRANCH_PAIR_CONTEXT_SCHEMA_V1,
    validate_branch_survival_row,
)
from lunar_ice_bpc.guidance.branch_e2e_costs import (  # noqa: E402
    canonical_guided_e2e_costs,
)
from lunar_ice_bpc.guidance.tensorization import (  # noqa: E402
    STATIC_FEATURE_SCHEMA_V2,
    build_static_graph_features,
)


SCHEMA_VERSION = "lunar_ice_bpc.branch_survival_training_row.v2"
EXPECTED_REPORT_SCHEMA = (
    "lunar_ice_bpc.no_task_wait_v3_branch_child_trajectory.v2"
)
FORMAL_GUIDANCE_LIFECYCLE_OVERHEAD_SEC = 0.02


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _candidate_id(candidate: dict) -> str:
    left, right = sorted(
        (str(candidate["task_a"]), str(candidate["task_b"]))
    )
    return f"branch_pair:{left}|{right}"


def _latest_dual_context(node: dict) -> dict:
    for history in reversed(list(node.get("history") or ())):
        context = history.get("dual_context")
        if (
            isinstance(context, dict)
            and str(context.get("dual_source") or "")
            == "master.reduced_cost_context"
        ):
            return context
    raise ValueError("actionable node has no bound true-RMP dual context")


def _pair_context(candidate: dict) -> list[float]:
    same_count = max(0, int(candidate.get("same_child_column_count") or 0))
    different_count = max(
        0,
        int(candidate.get("different_child_column_count") or 0),
    )
    denominator = max(1, same_count + different_count)
    return [
        float(candidate["fractionality"]),
        float(candidate["same_fraction"]),
        log1p(max(0, int(candidate.get("support_column_count") or 0))),
        abs(same_count - different_count) / float(denominator),
    ]


def _branch_degrees(node: dict) -> tuple[dict[str, int], dict[str, int]]:
    same: dict[str, int] = {}
    different: dict[str, int] = {}
    for decision in (
        (node.get("branch_context") or {}).get("pair_decisions") or ()
    ):
        target = (
            same
            if str(decision.get("sense") or "") == "same_journey"
            else different
        )
        for key in ("task_a", "task_b"):
            task_id = str(decision.get(key) or "")
            if task_id:
                target[task_id] = target.get(task_id, 0) + 1
    return same, different


def _cut_dual_features(
    node: dict,
    dual_context: dict,
) -> tuple[dict[str, float], dict[str, float]]:
    signed: dict[str, float] = {}
    absolute: dict[str, float] = {}
    duals = {
        str(key): float(value)
        for key, value in (dual_context.get("cut_duals") or {}).items()
    }
    for cut in (node.get("cut_context") or {}).get("cuts") or ():
        value = float(duals.get(str(cut.get("cut_id") or ""), 0.0))
        for task_id in cut.get("tasks") or ():
            task = str(task_id)
            signed[task] = signed.get(task, 0.0) + value
            absolute[task] = absolute.get(task, 0.0) + abs(value)
    return signed, absolute


def _node_features(
    *,
    static,
    node: dict,
    scale: int,
    memory_limit_gb: float,
    horizon_sec: float,
    depth: int,
    node_lp_bound: float | None,
    incumbent_objective: float | None,
    processed_node_count: int,
    open_node_count: int,
    global_column_count: int,
) -> list[list[float]]:
    dual_context = _latest_dual_context(node)
    task_duals = {
        str(key): float(value)
        for key, value in (dual_context.get("task_duals") or {}).items()
    }
    cut_signed, cut_absolute = _cut_dual_features(node, dual_context)
    same_degree, different_degree = _branch_degrees(node)
    incumbent_available = bool(
        incumbent_objective is not None
        and isfinite(float(incumbent_objective))
    )
    normalized_incumbent_gap = (
        0.0
        if not incumbent_available
        or node_lp_bound is None
        or not isfinite(float(node_lp_bound))
        else max(
            0.0,
            float(incumbent_objective) - float(node_lp_bound),
        )
        / max(1.0e-8, abs(float(incumbent_objective)))
    )
    common = (
        log1p(float(scale)),
        log1p(max(0.0, float(memory_limit_gb)) * 1024.0**3),
        log1p(float(horizon_sec)),
        1.0,
        0.0,
        log1p(max(0, int(depth))),
        normalized_incumbent_gap,
        float(incumbent_available),
        log1p(max(0, int(processed_node_count))),
        log1p(max(0, int(open_node_count))),
        log1p(max(0, int(global_column_count))),
    )
    rows = []
    for node_id, values in zip(
        static.node_ids,
        static.node_features,
        strict=True,
    ):
        rows.append(
            [
                *map(float, values),
                float(task_duals.get(node_id, 0.0)),
                *common,
                float(cut_signed.get(node_id, 0.0)),
                float(cut_absolute.get(node_id, 0.0)),
                log1p(float(same_degree.get(node_id, 0))),
                log1p(float(different_degree.get(node_id, 0))),
            ]
        )
    return rows


def _child_arrays(
    *,
    pair_reports: list[dict],
    horizon_sec: float,
) -> tuple[list[list[float]], list[list[float]], list[list[float]]]:
    times = []
    events = []
    masks = []
    for pair in pair_reports:
        by_sense = {
            str(child.get("branch_sense") or ""): child
            for child in pair.get("children") or ()
        }
        candidate_times = []
        candidate_events = []
        candidate_masks = []
        for sense in ("same_journey", "different_journey"):
            child = by_sense.get(sense)
            observed = bool(
                child is not None
                and str(child.get("node_status") or "") != "NOT_RUN"
            )
            available_budget = (
                0.0
                if child is None
                else float(child.get("budget_sec") or 0.0)
            )
            wall = 0.0 if child is None else float(
                child.get("observed_wall_sec") or 0.0
            )
            raw_event = bool(
                observed and child.get("event_observed")
            )
            if observed and (
                available_budget + 1.0e-6 < horizon_sec
                or (
                    not raw_event
                    and wall + 1.0e-6 < horizon_sec
                )
            ):
                raise ValueError(
                    "formal child-survival rows require matched, non-raced "
                    "coverage through the target horizon"
                )
            event = bool(raw_event and wall <= horizon_sec)
            fraction = (
                min(
                    1.0,
                    max(
                        1.0e-9,
                        wall / horizon_sec if event else 1.0,
                    ),
                )
                if observed
                else 0.0
            )
            candidate_times.append(fraction)
            candidate_events.append(float(event))
            candidate_masks.append(float(observed))
        times.append(candidate_times)
        events.append(candidate_events)
        masks.append(candidate_masks)
    return times, events, masks


def _control_tree_map(paths: list[Path]) -> dict[str, dict]:
    result = {}
    for path in paths:
        tree_path = (
            path / "control_rank0_tree.json"
            if path.is_dir()
            else path
        )
        tree = _load_json(tree_path)
        digest = _sha256_json(tree)
        if digest in result:
            raise ValueError(f"duplicate control tree hash {digest}")
        result[digest] = tree
    return result


def _e2e_gold_report_map(paths: list[Path]) -> dict[str, dict]:
    result: dict[str, dict[str, dict]] = {}
    for path in paths:
        report_path = (
            path / "state_oracle_report.json"
            if path.is_dir()
            else path
        )
        report = _load_json(report_path)
        content_hash = str(report.get("instance_content_hash") or "")
        if not content_hash:
            raise ValueError("E2E oracle report has no instance hash")
        state_paths = {
            str(row.get("path_hash") or "")
            for row in report.get("state_reports") or ()
        }
        if not state_paths or "" in state_paths:
            raise ValueError("E2E oracle report has no bound state path")
        by_path = result.setdefault(content_hash, {})
        overlap = state_paths.intersection(by_path)
        if overlap:
            raise ValueError(
                "duplicate E2E oracle instance-state "
                + ",".join(sorted(overlap))
            )
        for path_hash in state_paths:
            by_path[path_hash] = report
    return result


def _external_e2e_gold_label(
    *,
    oracle: dict | None,
    state: dict,
    candidate_ids: list[str],
    parent_source_sha256: str,
) -> dict | None:
    if oracle is None:
        return None
    if (
        str(oracle.get("schema_version") or "")
        != "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
        or str(oracle.get("root_source_sha256") or "")
        != str(parent_source_sha256)
        or not bool(oracle.get("control_universe_safe"))
    ):
        raise ValueError("external E2E oracle binding/exactness mismatch")
    matches = [
        row
        for row in oracle.get("state_reports") or ()
        if str(row.get("path_hash") or "")
        == str(state.get("path_hash") or "")
    ]
    if len(matches) != 1:
        raise ValueError("external E2E oracle state binding mismatch")
    row = matches[0]
    if not bool(row.get("complete_matched_e2e_gold")):
        return None
    arms = list(row.get("arms") or ())
    if (
        not bool(oracle.get("control_exact_safe"))
        or list(row.get("top3_candidate_ids") or ())
        != list(candidate_ids)
        or int(row.get("eligible_alternative_count") or 0) != 2
        or len(arms) != 2
        or any(
            not bool(arm.get("exact_safe"))
            or not bool(
                arm.get(
                    "counterfactual_universe_matches_control"
                )
            )
            for arm in arms
        )
    ):
        raise ValueError("external E2E oracle is not complete matched gold")
    control = oracle.get("control") or {}
    arm_by_rank = {0: control}
    for arm in arms:
        rank = int(arm["requested_rank_index"])
        if rank not in {1, 2} or rank in arm_by_rank:
            raise ValueError("external E2E oracle arm rank mismatch")
        arm_by_rank[rank] = arm
    costs = canonical_guided_e2e_costs(
        arm_by_rank=arm_by_rank,
        guidance_lifecycle_overhead_sec=(
            FORMAL_GUIDANCE_LIFECYCLE_OVERHEAD_SEC
        ),
    )
    return {
        "schema_version": str(oracle["schema_version"]),
        "oracle_selected_rank_index": int(
            costs["oracle_selected_rank_index"]
        ),
        "oracle_net_gain_sec": float(costs["oracle_net_gain_sec"]),
        "oracle_net_gain_ratio": (
            float(costs["oracle_net_gain_sec"])
            / float(costs["p0_control_wall_sec"])
        ),
        "p0_control_wall_sec": float(costs["p0_control_wall_sec"]),
        "guidance_lifecycle_overhead_sec": float(
            costs["guidance_lifecycle_overhead_sec"]
        ),
        "cost_semantics": costs["cost_semantics"],
        "matched_end_to_end_wall_sec_by_rank": (
            costs["guided_action_wall_sec_by_rank"]
        ),
        "source_report_sha256": _sha256_json(oracle),
        "same_parent_snapshot_bound": True,
    }


def _external_e2e_pairwise_preferences(
    *,
    oracle: dict | None,
    state: dict,
    candidate_ids: list[str],
    parent_source_sha256: str,
) -> list[list[int]]:
    if oracle is None:
        return []
    if (
        str(oracle.get("schema_version") or "")
        != "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
        or str(oracle.get("root_source_sha256") or "")
        != str(parent_source_sha256)
        or not bool(oracle.get("control_universe_safe"))
    ):
        raise ValueError(
            "external censored E2E binding/exactness mismatch"
        )
    matches = [
        row
        for row in oracle.get("state_reports") or ()
        if str(row.get("path_hash") or "")
        == str(state.get("path_hash") or "")
    ]
    if len(matches) != 1:
        raise ValueError(
            "external censored E2E state binding mismatch"
        )
    row = matches[0]
    if list(row.get("top3_candidate_ids") or ()) != list(
        candidate_ids
    ):
        raise ValueError(
            "external censored E2E top-3 binding mismatch"
        )
    observed = {
        int(value)
        for value in row.get("observed_rank_indices") or ()
    }
    arm_by_rank = {
        0: dict(oracle.get("control") or {}),
        **{
            int(arm["requested_rank_index"]): dict(arm)
            for arm in row.get("arms") or ()
        },
    }
    preferences = []
    directed = set()
    for item in (
        row.get("trusted_censored_pairwise_preferences") or ()
    ):
        if (
            "winner_rank_index" not in item
            or "loser_rank_index" not in item
        ):
            raise ValueError(
                "external censored E2E preference has no ranks"
            )
        winner = int(item["winner_rank_index"])
        loser = int(item["loser_rank_index"])
        winner_arm = arm_by_rank.get(winner) or {}
        loser_arm = arm_by_rank.get(loser) or {}
        winner_wall = winner_arm.get(
            "matched_end_to_end_wall_sec"
        )
        loser_wall = loser_arm.get(
            "matched_end_to_end_wall_sec"
        )
        evidence = str(item.get("evidence") or "")
        evidence_valid = bool(
            winner_wall is not None
            and loser_wall is not None
            and isfinite(float(winner_wall))
            and isfinite(float(loser_wall))
            and 0.0 < float(winner_wall) < float(loser_wall)
            and (
                (
                    evidence == "BOTH_EXACT_OBJECTIVE_MATCH"
                    and winner_arm.get("exact_safe") is True
                    and loser_arm.get("exact_safe") is True
                    and winner_arm.get("objective") is not None
                    and loser_arm.get("objective") is not None
                    and abs(
                        float(winner_arm["objective"])
                        - float(loser_arm["objective"])
                    )
                    <= 5.0e-6
                )
                or (
                    evidence
                    == "EXACT_BEFORE_OTHER_CENSOR_HORIZON"
                    and winner_arm.get("exact_safe") is True
                    and loser_arm.get("exact_safe") is False
                )
            )
        )
        if (
            winner == loser
            or winner not in observed
            or loser not in observed
            or item.get("same_parent_snapshot") is not True
            or item.get("unexplored_arm_used_as_negative") is not False
            or not evidence_valid
            or (winner, loser) in directed
            or (loser, winner) in directed
        ):
            raise ValueError(
                "external censored E2E preference is invalid"
            )
        directed.add((winner, loser))
        preferences.append([winner, loser])
    return preferences


def _materialize(
    *,
    report: dict,
    control: dict,
    manifest_row: dict,
    external_e2e_oracle: dict | None = None,
) -> list[dict]:
    if str(report.get("schema_version") or "") != EXPECTED_REPORT_SCHEMA:
        raise ValueError("child trajectory report schema mismatch")
    if bool(report.get("legacy_normalized_cost_present")) or bool(
        report.get("legacy_four_coefficient_cost_present")
    ):
        raise ValueError("legacy branch cost present in child report")
    if int(report.get("guidance_branch_pair_drop_count") or 0) != 0:
        raise ValueError("child report dropped legal branch pairs")
    if (
        report.get("continuation_source_report_sha256") is not None
        or bool(report.get("continuation_reuses_columns_only"))
        or report.get("formal_one_shot_survival_label") is False
    ):
        raise ValueError(
            "continuation is horizon discovery only; formal survival rows "
            "require one uninterrupted child probe from the parent snapshot"
        )
    instance_path = Path(str(manifest_row["instance_path"]))
    data = load_lunar_ice_data(_load_json(instance_path))
    if data.instance_content_hash != str(
        report["instance_content_hash"]
    ):
        raise ValueError("instance content hash mismatch")
    static = build_static_graph_features(data)
    node_index = {
        node_id: index for index, node_id in enumerate(static.node_ids)
    }
    nodes = {
        str(node["node_id"]): node for node in control.get("nodes") or ()
    }
    binding = report.get("solver_binding") or {}
    horizon_sec = float(report["probe_budget_sec"])
    if not isfinite(horizon_sec) or horizon_sec <= 0.0:
        raise ValueError("probe horizon must be finite and positive")
    rows = []
    for state in report.get("state_reports") or ():
        if not bool(state.get("parent_state_reconstructed")):
            raise ValueError(
                "formal row requires an exact reconstructed parent snapshot"
            )
        depth = int(state.get("depth") or 0)
        parent_snapshot = state.get("parent_snapshot") or {}
        if (
            depth != 0
            and str(parent_snapshot.get("snapshot_origin") or "")
            != "exact_p0_deep_parent_snapshot"
        ):
            raise ValueError(
                "deeper formal state requires an exact node-specific P0 "
                "parent snapshot"
            )
        node = nodes.get(str(state["node_id"]))
        if node is None:
            raise ValueError("state node absent from bound control tree")
        fresh_shortlist = bool(
            state.get("fresh_reconstructed_shortlist_bound")
        )
        candidates = list(
            (
                parent_snapshot.get("reconstructed_top3_candidates")
                if fresh_shortlist
                else (
                    node.get("fractional_branch_probe") or {}
                ).get("candidates")
            )
            or ()
        )[:3]
        pair_reports = sorted(
            list(state.get("pair_reports") or ()),
            key=lambda row: int(row["rank_index"]),
        )
        if len(candidates) != 3 or len(pair_reports) != 3:
            raise ValueError("formal row requires three P0 candidates")
        candidate_ids = [_candidate_id(candidate) for candidate in candidates]
        if candidate_ids != [
            str(pair["candidate_id"]) for pair in pair_reports
        ]:
            raise ValueError("child report candidate order mismatch")
        times, events, masks = _child_arrays(
            pair_reports=pair_reports,
            horizon_sec=horizon_sec,
        )
        embedded_gold = state.get("gold_end_to_end_label")
        state_external_oracle = external_e2e_oracle
        if (
            external_e2e_oracle is not None
            and "schema_version" not in external_e2e_oracle
        ):
            state_external_oracle = external_e2e_oracle.get(
                str(state.get("path_hash") or "")
            )
        external_gold = _external_e2e_gold_label(
            oracle=state_external_oracle,
            state=state,
            candidate_ids=candidate_ids,
            parent_source_sha256=str(
                report.get("p0_parent_source_sha256") or ""
            ),
        )
        external_pairwise = _external_e2e_pairwise_preferences(
            oracle=state_external_oracle,
            state=state,
            candidate_ids=candidate_ids,
            parent_source_sha256=str(
                report.get("p0_parent_source_sha256") or ""
            ),
        )
        if embedded_gold is not None and external_gold is not None:
            raise ValueError("duplicate embedded and external E2E gold")
        gold = embedded_gold or external_gold
        if fresh_shortlist and embedded_gold is not None:
            raise ValueError(
                "fresh reconstructed shortlist cannot reuse historical gold"
            )
        row = {
            "schema_version": SCHEMA_VERSION,
            "branch_training_objective": (
                BRANCH_CHILD_SURVIVAL_RMST_OBJECTIVE_V1
            ),
            "branch_primary_training_objective": (
                BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2
            ),
            "branch_node_feature_schema": (
                BRANCH_NODE_FEATURE_SCHEMA_V2
            ),
            "branch_pair_context_schema": (
                BRANCH_PAIR_CONTEXT_SCHEMA_V1
            ),
            "static_feature_schema": STATIC_FEATURE_SCHEMA_V2,
            "baseline_id": report["baseline_id"],
            "engine_hash": binding.get("engine_hash"),
            "instance_id": report["instance_id"],
            "instance_content_hash": report["instance_content_hash"],
            "instance_generator_domain": str(
                manifest_row.get("instance_generator_domain") or ""
            ),
            "scale": int(report["scale"]),
            "node_id": state["node_id"],
            "node_phase": (
                "root_fractional_exact_node"
                if depth == 0
                else "deep_fractional_exact_node"
            ),
            "parent_snapshot_origin": str(
                parent_snapshot.get("snapshot_origin")
                or "exact_p0_parent_source"
            ),
            "rmp_context_hash": _sha256_json(
                {
                    "instance": report["instance_content_hash"],
                    "node": state["node_id"],
                    "path": state["path_hash"],
                    "dual": parent_snapshot.get(
                        "true_dual_context"
                    ),
                    "cuts": node.get("cut_context") or {},
                    "branch": node.get("branch_context") or {},
                }
            ),
            "path_hash": state["path_hash"],
            "tree_context": {
                "depth": depth,
                "node_lp_bound": node.get("node_lp_bound"),
                "incumbent_objective": (
                    parent_snapshot.get("incumbent_objective")
                    if parent_snapshot.get("incumbent_objective")
                    is not None
                    else control.get("objective")
                ),
                "processed_node_count": int(
                    parent_snapshot.get("processed_node_count")
                    or 0
                ),
                "open_node_count": int(
                    parent_snapshot.get("open_node_count") or 0
                ),
                "global_column_count": int(
                    parent_snapshot.get("global_column_count")
                    or parent_snapshot.get("active_column_count")
                    or 0
                ),
                "decision_time_only": True,
            },
            "node_features": _node_features(
                static=static,
                node={
                    **node,
                    "history": [
                        {
                            "dual_context": parent_snapshot.get(
                                "true_dual_context"
                            )
                        }
                    ],
                },
                scale=int(report["scale"]),
                memory_limit_gb=float(
                    binding.get("memory_limit_gb") or 0.0
                ),
                horizon_sec=horizon_sec,
                depth=depth,
                node_lp_bound=node.get("node_lp_bound"),
                incumbent_objective=(
                    parent_snapshot.get("incumbent_objective")
                    if parent_snapshot.get("incumbent_objective")
                    is not None
                    else control.get("objective")
                ),
                processed_node_count=int(
                    parent_snapshot.get("processed_node_count")
                    or 0
                ),
                open_node_count=int(
                    parent_snapshot.get("open_node_count") or 0
                ),
                global_column_count=int(
                    parent_snapshot.get("global_column_count")
                    or parent_snapshot.get("active_column_count")
                    or 0
                ),
            ),
            "edge_features": [
                list(map(float, values))
                for values in static.arc_features
            ],
            "edge_index": [
                list(static.arc_sources),
                list(static.arc_targets),
            ],
            "branch_pairs": [
                [
                    node_index[str(candidate["task_a"])],
                    node_index[str(candidate["task_b"])],
                ]
                for candidate in candidates
            ],
            "branch_candidate_ids": candidate_ids,
            "branch_context": [
                _pair_context(candidate) for candidate in candidates
            ],
            "branch_child_observed_time_fractions": times,
            "branch_child_event_observed": events,
            "branch_child_observed_mask": masks,
            "branch_probe_horizon_sec": horizon_sec,
            "branch_e2e_gold_rank_index": (
                None
                if gold is None
                else int(gold["oracle_selected_rank_index"])
            ),
            "branch_e2e_gold_net_gain_sec": (
                None if gold is None else float(gold["oracle_net_gain_sec"])
            ),
            "branch_e2e_p0_control_wall_sec": (
                None
                if gold is None
                else float(gold["p0_control_wall_sec"])
            ),
            "branch_guidance_lifecycle_overhead_sec": (
                None
                if gold is None
                else float(gold["guidance_lifecycle_overhead_sec"])
            ),
            "branch_e2e_cost_semantics": (
                None if gold is None else str(gold["cost_semantics"])
            ),
            "branch_e2e_wall_sec_by_rank": (
                None
                if gold is None
                else {
                    str(key): float(value)
                    for key, value in (
                        gold.get(
                            "matched_end_to_end_wall_sec_by_rank"
                        )
                        or {}
                    ).items()
                }
            ),
            "branch_e2e_trusted_pairwise_preferences": (
                [] if gold is not None else external_pairwise
            ),
            "legal_branch_shortlist_hash_before_sort": state[
                "legal_branch_shortlist_hash_before_sort"
            ],
            "legal_branch_shortlist_hash_after_sort": state[
                "legal_branch_shortlist_hash_after_sort"
            ],
            "guidance_branch_pair_drop_count": 0,
            "guidance_filter_count": 0,
            "unexplored_candidate_negative": False,
            "calibration_used": False,
            "protected_final_test_used": False,
            "fresh_reconstructed_shortlist_bound": fresh_shortlist,
            "historical_end_to_end_gold_binding_valid": (
                embedded_gold is not None and not fresh_shortlist
            ),
            "same_snapshot_e2e_gold_binding_valid": (
                external_gold is not None
            ),
            "same_snapshot_e2e_censored_pairwise_binding_valid": (
                bool(external_pairwise)
            ),
        }
        validate_branch_survival_row(row)
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child-report", action="append", required=True)
    parser.add_argument(
        "--oracle-dir",
        action="append",
        required=True,
        help="Directory containing control_rank0_tree.json, or that file.",
    )
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument(
        "--e2e-oracle-report",
        action="append",
        default=[],
        help=(
            "Optional exact matched E2E state-oracle report (or directory). "
            "It must bind the same certified parent snapshot and top-3."
        ),
    )
    parser.add_argument(
        "--target-horizon-sec",
        type=float,
        default=None,
        help=(
            "Optional common horizon no larger than every supplied probe. "
            "Later events are replayed as right-censored at this horizon."
        ),
    )
    args = parser.parse_args()

    manifest = _load_json(Path(args.split_manifest))
    authorized_collection_manifest_hashes = {
        str(value)
        for value in (
            manifest.get("authorized_collection_manifest_hashes")
            or (
                manifest.get("source_content_manifest_hash")
                or manifest.get("manifest_hash"),
            )
        )
        if value
    }
    if not authorized_collection_manifest_hashes:
        raise SystemExit(
            "split manifest has no authorized collection binding"
        )
    development = {
        str(row["instance_content_hash"]): row
        for row in manifest.get("development") or ()
    }
    forbidden = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in manifest.get(partition) or ()
    }
    trees = _control_tree_map(
        [Path(value) for value in args.oracle_dir]
    )
    e2e_gold = _e2e_gold_report_map(
        [Path(value) for value in args.e2e_oracle_report]
    )
    rows = []
    for value in args.child_report:
        report = _load_json(Path(value))
        if str(report.get("split_manifest_hash") or "") not in (
            authorized_collection_manifest_hashes
        ):
            raise SystemExit(
                "child report collection split binding mismatch"
            )
        if args.target_horizon_sec is not None:
            target = float(args.target_horizon_sec)
            if (
                not isfinite(target)
                or target <= 0.0
                or target > float(report["probe_budget_sec"]) + 1.0e-6
            ):
                raise SystemExit(
                    "target horizon must be positive and no larger than "
                    "the collected probe horizon"
                )
            report = {
                **report,
                "probe_budget_sec": target,
            }
        content_hash = str(report["instance_content_hash"])
        if content_hash in forbidden or content_hash not in development:
            raise SystemExit("non-development child report rejected")
        control_hash = str(report.get("control_tree_sha256") or "")
        if control_hash not in trees:
            raise SystemExit(
                f"bound control tree not supplied for {content_hash}"
            )
        rows.extend(
            _materialize(
                report=report,
                control=trees[control_hash],
                manifest_row=development[content_hash],
                external_e2e_oracle=e2e_gold.get(content_hash),
            )
        )
    destination = Path(args.output_jsonl)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    temporary.replace(destination)
    print(
        json.dumps(
            {
                "output_jsonl": str(destination),
                "row_count": len(rows),
                "instance_count": len(
                    {row["instance_content_hash"] for row in rows}
                ),
                "survival_observation_count": sum(
                    int(value)
                    for row in rows
                    for pair in row["branch_child_observed_mask"]
                    for value in pair
                ),
                "e2e_gold_count": sum(
                    row["branch_e2e_gold_rank_index"] is not None
                    for row in rows
                ),
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
