#!/usr/bin/env python3
"""Fit a leaked per-instance dual center from observed P0 route trajectories.

This is an algorithmic-headroom diagnostic, not model training.  It consumes
only development rows collected with
``LUNAR_ICE_DUAL_CENTER_TRAJECTORY_COLLECTION=1`` and asks whether even a
perfect instance-specific center can improve matched end-to-end root CG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.pricing.dual_stabilization import (  # noqa: E402
    DevelopmentOracleDualCenter,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _unwrap_probe(payload: dict) -> dict:
    result = payload.get("result")
    return dict(result) if isinstance(result, dict) else payload


def _bound(row: dict) -> float | None:
    value = row.get("root_lp_bound")
    if value is None:
        value = row.get("node_lp_bound")
    return None if value is None else float(value)


def _trajectory_rows(
    history: list[dict],
    task_index: dict[str, int],
) -> tuple[list[list[float]], list[float], list[float], dict]:
    incidence: list[list[float]] = []
    objectives: list[float] = []
    values: list[float] = []
    useful_batch_count = 0
    observed_batch_count = 0
    for index, row in enumerate(history[:-1]):
        candidates = list(row.get("dual_center_route_candidates") or ())
        if not candidates:
            continue
        current_bound = _bound(row)
        next_bound = _bound(history[index + 1])
        if current_bound is None or next_bound is None:
            continue
        selected = [
            candidate
            for candidate in candidates
            if bool(candidate.get("selected_into_batch"))
        ]
        if not selected:
            continue
        observed_batch_count += 1
        # The root RMP is a minimization problem: adding useful columns lowers
        # its objective. Attribution remains at batch level because no
        # unsupported per-column Shapley value is fabricated.
        bound_gain = max(0.0, current_bound - next_bound)
        wall = max(1.0e-9, float(row.get("final_judge_wall_time") or 0.0))
        batch_value = bound_gain / wall
        if batch_value > 0.0:
            useful_batch_count += 1
        for candidate in selected:
            tasks = tuple(str(value) for value in candidate.get("task_ids") or ())
            if not tasks or any(task_id not in task_index for task_id in tasks):
                raise SystemExit("trajectory candidate task universe mismatch")
            vector = [0.0 for _ in task_index]
            for task_id in tasks:
                vector[task_index[task_id]] = 1.0
            incidence.append(vector)
            objectives.append(float(candidate["objective"]))
            values.append(float(batch_value))
    if useful_batch_count < 1:
        raise SystemExit(
            "no immediate measured root-bound-gain batch; trajectory oracle "
            "is not identifiable from this probe"
        )
    return incidence, objectives, values, {
        "observed_batch_count": observed_batch_count,
        "useful_batch_count": useful_batch_count,
        "observed_selected_route_count": len(incidence),
        "positive_value_route_count": sum(value > 0.0 for value in values),
        "unexplored_candidates_used_as_negative": False,
        "attribution_scope": "next_rmp_batch_bound_gain_per_pricing_second",
        "per_column_credit_fabricated": False,
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
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--face-regularizer", type=float, default=0.02)
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
        raise SystemExit("trajectory oracle accepts development instances only")

    outer = _load(probe_path)
    if str(outer.get("instance_content_hash") or data.instance_content_hash) != (
        data.instance_content_hash
    ):
        raise SystemExit("collected probe content hash mismatch")
    probe = _unwrap_probe(outer)
    if (
        str(probe.get("pricing_state") or "")
        != "CERTIFIED_NO_NEGATIVE"
        or not bool(probe.get("uses_true_dual_bpc_certificate"))
    ):
        raise SystemExit("collected P0 probe is not true-dual certified")
    history = [dict(row) for row in probe.get("history") or ()]
    if len(history) < 2:
        raise SystemExit("collected P0 probe has no usable root trajectory")
    if not any(
        bool(row.get("dual_center_trajectory_collection_enabled"))
        for row in history
    ):
        raise SystemExit("probe lacks dual-center trajectory collection rows")

    task_ids = tuple(data.task_ids)
    task_index = {
        task_id: index for index, task_id in enumerate(task_ids)
    }
    incidence, objectives, values, collection_audit = _trajectory_rows(
        history, task_index
    )
    dual_rows = []
    for row in history:
        task_duals = (row.get("dual_context") or {}).get("task_duals")
        if not isinstance(task_duals, dict):
            continue
        dual_rows.append(
            [float(task_duals[task_id]) for task_id in task_ids]
        )
    if len(dual_rows) < 2:
        raise SystemExit("probe has too few true-dual trajectory rows")

    # Torch is imported only inside this development-only command.
    import torch

    from lunar_ice_bpc.guidance.dual_center_training import (
        counterfactual_route_trajectory_loss,
        set_valued_dual_face_loss,
    )

    torch.set_num_threads(1)
    torch.manual_seed(0)
    incidence_tensor = torch.tensor(incidence, dtype=torch.float32)
    objective_tensor = torch.tensor(objectives, dtype=torch.float32)
    value_tensor = torch.tensor(values, dtype=torch.float32)
    observed_mask = torch.ones(len(values), dtype=torch.bool)
    initial = torch.tensor(dual_rows[0], dtype=torch.float32)
    face = torch.tensor(dual_rows[-min(8, len(dual_rows)):], dtype=torch.float32)
    trajectory_span = float(
        torch.max(torch.abs(face - initial[None, :])).detach()
    )
    residual_radius = max(0.05, min(1.0, 3.0 * trajectory_span))
    raw_residual = torch.zeros_like(initial, requires_grad=True)
    optimizer = torch.optim.Adam(
        [raw_residual], lr=float(args.learning_rate)
    )

    def current_center() -> torch.Tensor:
        return initial + residual_radius * torch.tanh(raw_residual)

    with torch.no_grad():
        initial_route_loss = counterfactual_route_trajectory_loss(
            initial,
            route_task_incidence=incidence_tensor,
            route_objective=objective_tensor,
            observed_route_value=value_tensor,
            observed_mask=observed_mask,
        )
    final_loss = None
    for _ in range(max(1, int(args.steps))):
        optimizer.zero_grad(set_to_none=True)
        center = current_center()
        route_loss = counterfactual_route_trajectory_loss(
            center,
            route_task_incidence=incidence_tensor,
            route_objective=objective_tensor,
            observed_route_value=value_tensor,
            observed_mask=observed_mask,
        )
        face_loss = set_valued_dual_face_loss(
            center,
            torch.zeros_like(center),
            admissible_dual_centers=face,
        )
        loss = route_loss + float(args.face_regularizer) * face_loss
        loss.backward()
        optimizer.step()
        final_loss = loss
    fitted = current_center().detach()
    fitted_route_loss = counterfactual_route_trajectory_loss(
        fitted,
        route_task_incidence=incidence_tensor,
        route_objective=objective_tensor,
        observed_route_value=value_tensor,
        observed_mask=observed_mask,
    )
    raw_task_priority = torch.zeros_like(initial, requires_grad=True)
    priority_optimizer = torch.optim.Adam(
        [raw_task_priority], lr=float(args.learning_rate)
    )
    zero_route_objective = torch.zeros_like(objective_tensor)
    for _ in range(max(1, int(args.steps))):
        priority_optimizer.zero_grad(set_to_none=True)
        priority = torch.tanh(raw_task_priority)
        priority_loss = counterfactual_route_trajectory_loss(
            priority,
            route_task_incidence=incidence_tensor,
            route_objective=zero_route_objective,
            observed_route_value=value_tensor,
            observed_mask=observed_mask,
        )
        (priority_loss + 1.0e-4 * torch.square(priority).mean()).backward()
        priority_optimizer.step()
    fitted_priority = torch.tanh(raw_task_priority).detach()
    fitted_priority = fitted_priority - fitted_priority.mean()
    maximum_priority = float(torch.max(torch.abs(fitted_priority)))
    if maximum_priority > 0.0:
        fitted_priority = fitted_priority / maximum_priority
    initial_priority_loss = counterfactual_route_trajectory_loss(
        torch.zeros_like(initial),
        route_task_incidence=incidence_tensor,
        route_objective=zero_route_objective,
        observed_route_value=value_tensor,
        observed_mask=observed_mask,
    )
    fitted_priority_loss = counterfactual_route_trajectory_loss(
        fitted_priority,
        route_task_incidence=incidence_tensor,
        route_objective=zero_route_objective,
        observed_route_value=value_tensor,
        observed_mask=observed_mask,
    )
    source_sha = hashlib.sha256(probe_path.read_bytes()).hexdigest()
    center = DevelopmentOracleDualCenter(
        instance_content_hash=data.instance_content_hash,
        task_dual_items=tuple(
            (task_id, float(fitted[index]))
            for index, task_id in enumerate(task_ids)
        ),
        source_rmp_iteration_id=(
            "development_trajectory_rc_oracle:"
            + str(
                (history[0].get("dual_context") or {}).get(
                    "rmp_iteration_id"
                )
                or "root-1"
            )
        ),
        source_artifact_sha256=source_sha,
        source_partition="development",
    )
    payload = {
        "schema_version": (
            "lunar_ice_bpc.development_trajectory_rc_dual_center_oracle.v1"
        ),
        "development_only": True,
        "deployable": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "oracle_center": center.to_payload(),
        "task_priority_oracle": {
            "schema_version": (
                "lunar_ice_bpc.development_trajectory_task_priority_oracle.v1"
            ),
            "source_partition": "development",
            "instance_content_hash": data.instance_content_hash,
            "source_artifact_sha256": source_sha,
            "task_priorities": {
                task_id: float(fitted_priority[index])
                for index, task_id in enumerate(task_ids)
            },
            "arc_priorities": {},
            "development_only": True,
            "deployable": False,
            "ordering_only": True,
            "can_filter": False,
            "can_certify": False,
        },
        "fit": {
            **collection_audit,
            "steps": max(1, int(args.steps)),
            "learning_rate": float(args.learning_rate),
            "face_regularizer": float(args.face_regularizer),
            "residual_radius": residual_radius,
            "initial_route_trajectory_loss": float(initial_route_loss),
            "fitted_route_trajectory_loss": float(fitted_route_loss),
            "initial_task_priority_loss": float(initial_priority_loss),
            "fitted_task_priority_loss": float(fitted_priority_loss),
            "total_final_loss": (
                None if final_loss is None else float(final_loss.detach())
            ),
            "route_loss_improved": bool(
                float(fitted_route_loss) < float(initial_route_loss)
            ),
            "checkpoint_selection_metric": (
                "matched_end_to_end_wall_time_not_coordinate_mse"
            ),
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
                "initial_route_trajectory_loss": float(initial_route_loss),
                "fitted_route_trajectory_loss": float(fitted_route_loss),
                **collection_audit,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
