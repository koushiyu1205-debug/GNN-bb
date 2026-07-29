#!/usr/bin/env python3
"""Build paired cost-to-closure labels for the P0 V3 proof-pass gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics


ROOT = Path(__file__).resolve().parents[1]
FORK_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_fork.v1"
SNAPSHOT_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_state_snapshot.v1"
OUTPUT_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_fork_labels.v1"
ACTIONS = ("harvest_then_proof", "proof_only")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
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


def _input_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = (ROOT / value).resolve()
        if path.is_dir():
            paths.extend(sorted(path.glob("*.json")))
        else:
            paths.append(path)
    return paths


def _validated_fork(path: Path) -> dict:
    payload = _load_json(path)
    if payload.get("schema_version") != FORK_SCHEMA:
        raise SystemExit(f"fork schema mismatch: {path}")
    recorded_hash = str(payload.get("fork_hash") or "")
    unhashed = dict(payload)
    unhashed.pop("fork_hash", None)
    if recorded_hash != _sha256_json(unhashed):
        raise SystemExit(f"fork hash mismatch: {path}")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or bool(payload.get("can_certify_source_solve"))
    ):
        raise SystemExit(f"fork is not development-only: {path}")
    if not (
        bool(payload.get("state_rebuild_match"))
        and bool(payload.get("fork_exact_safe"))
        and bool(payload.get("fork_universe_safe"))
    ):
        raise SystemExit(f"unsafe or unmatched fork: {path}")
    action = str(
        payload.get("requested_first_pass_strategy") or ""
    )
    if action not in ACTIONS:
        raise SystemExit(f"fork has no one-step action label: {path}")
    return payload


def _validated_snapshot(path: Path, *, state_hash: str) -> dict:
    payload = _load_json(path)
    if payload.get("schema_version") != SNAPSHOT_SCHEMA:
        raise SystemExit(f"snapshot schema mismatch: {path}")
    if str(payload.get("state_hash") or "") != str(state_hash):
        raise SystemExit(f"fork/snapshot state hash mismatch: {path}")
    unhashed = dict(payload)
    recorded_hash = str(unhashed.pop("state_hash", ""))
    if recorded_hash != _sha256_json(unhashed):
        raise SystemExit(f"snapshot hash mismatch: {path}")
    return payload


def _median(values: list[float]) -> float:
    if not values:
        raise ValueError("median requires observations")
    return float(statistics.median(values))


def _bootstrap_mean_interval(
    values: list[float],
    *,
    state_hashes: list[str],
    sample_count: int = 20_000,
) -> dict:
    if not values:
        return {
            "sample_count": 0,
            "mean_sec": None,
            "two_sided_95_lower_sec": None,
            "two_sided_95_upper_sec": None,
            "one_sided_95_lower_sec": None,
            "one_sided_95_upper_sec": None,
        }
    seed_payload = "|".join(sorted(state_hashes)).encode("utf-8")
    seed = int(
        hashlib.sha256(seed_payload).hexdigest()[:16],
        16,
    )
    generator = random.Random(seed)
    observation_count = len(values)
    means = sorted(
        sum(
            generator.choice(values)
            for _ in range(observation_count)
        )
        / observation_count
        for _ in range(max(1, int(sample_count)))
    )

    def quantile(probability: float) -> float:
        index = min(
            len(means) - 1,
            max(0, math.ceil(probability * len(means)) - 1),
        )
        return float(means[index])

    return {
        "sample_count": len(means),
        "seed": seed,
        "mean_sec": float(statistics.mean(values)),
        "two_sided_95_lower_sec": quantile(0.025),
        "two_sided_95_upper_sec": quantile(0.975),
        "one_sided_95_lower_sec": quantile(0.05),
        "one_sided_95_upper_sec": quantile(0.95),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Fork JSON file or directory; repeat for more sources.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--inference-overhead-sec",
        type=float,
        default=0.02,
    )
    parser.add_argument(
        "--absolute-deadband-sec",
        type=float,
        default=0.05,
    )
    parser.add_argument(
        "--relative-deadband",
        type=float,
        default=0.05,
    )
    parser.add_argument(
        "--bound-match-tolerance",
        type=float,
        default=1.1e-6,
        help=(
            "Maximum absolute delta between paired terminal RMP bounds. "
            "The RMP stores its objective rounded to six decimal places."
        ),
    )
    args = parser.parse_args()
    for value, name in (
        (args.inference_overhead_sec, "inference overhead"),
        (args.absolute_deadband_sec, "absolute deadband"),
        (args.relative_deadband, "relative deadband"),
        (args.bound_match_tolerance, "bound match tolerance"),
    ):
        if not math.isfinite(float(value)) or float(value) < 0.0:
            raise SystemExit(f"{name} must be finite and nonnegative")

    grouped: dict[tuple[str, str], dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for path in _input_paths(list(args.input)):
        payload = _validated_fork(path)
        key = (
            str(payload["instance_content_hash"]),
            str(payload["source_state_hash"]),
        )
        action = str(payload["requested_first_pass_strategy"])
        grouped[key][action].append({**payload, "_path": str(path)})

    rows: list[dict] = []
    missing_pairs: list[dict] = []
    for (instance_hash, state_hash), by_action in sorted(
        grouped.items()
    ):
        missing = [action for action in ACTIONS if not by_action[action]]
        if missing:
            missing_pairs.append(
                {
                    "instance_content_hash": instance_hash,
                    "source_state_hash": state_hash,
                    "missing_actions": missing,
                }
            )
            continue
        observations = {
            action: [
                float(row["fork_wall_sec"])
                for row in by_action[action]
            ]
            for action in ACTIONS
        }
        costs = {
            action: _median(observations[action])
            for action in ACTIONS
        }
        exemplars = {
            action: by_action[action][0] for action in ACTIONS
        }
        bounds = [
            float(exemplars[action]["fork_node_lp_bound"])
            for action in ACTIONS
        ]
        bound_abs_delta = abs(bounds[0] - bounds[1])
        if bound_abs_delta > float(args.bound_match_tolerance):
            raise SystemExit(
                "paired forks closed to different exact root bounds: "
                f"{state_hash} (delta={bound_abs_delta:.12g}, "
                f"tolerance={float(args.bound_match_tolerance):.12g})"
            )
        source_path = Path(
            exemplars[ACTIONS[0]]["source_snapshot_path"]
        )
        snapshot = _validated_snapshot(
            source_path, state_hash=state_hash
        )
        source_action = str(
            snapshot.get("source_pass_strategy") or ""
        )
        if source_action not in ACTIONS:
            raise SystemExit(
                f"snapshot has unsupported source action: {source_path}"
            )
        harvest_cost = costs["harvest_then_proof"]
        proof_cost = costs["proof_only"]
        proof_advantage_sec = harvest_cost - proof_cost
        deadband_sec = max(
            float(args.absolute_deadband_sec),
            float(args.relative_deadband)
            * min(harvest_cost, proof_cost),
        )
        best_action = (
            "proof_only"
            if proof_advantage_sec > deadband_sec
            else "harvest_then_proof"
            if proof_advantage_sec < -deadband_sec
            else "indistinguishable"
        )
        source_cost = costs[source_action]
        oracle_cost = min(costs.values())
        oracle_gain_before_overhead = source_cost - oracle_cost
        net_oracle_gain = (
            oracle_gain_before_overhead
            - float(args.inference_overhead_sec)
        )
        override_action = (
            min(costs, key=costs.get)
            if net_oracle_gain > deadband_sec
            else "abstain"
        )
        rows.append(
            {
                "instance_id": exemplars[ACTIONS[0]][
                    "instance_id"
                ],
                "scale": len(
                    (snapshot.get("true_duals") or {}).get(
                        "task_duals"
                    )
                    or {}
                ),
                "instance_content_hash": instance_hash,
                "source_state_hash": state_hash,
                "source_round": int(snapshot["round"]),
                "source_pass_policy": str(
                    snapshot.get("source_pass_policy") or ""
                ),
                "source_pass_strategy": source_action,
                "trajectory_features": dict(
                    snapshot.get("trajectory_features") or {}
                ),
                "harvest_cost_to_closure_sec": harvest_cost,
                "proof_cost_to_closure_sec": proof_cost,
                "proof_advantage_sec": proof_advantage_sec,
                "proof_advantage_ratio": (
                    proof_advantage_sec / harvest_cost
                    if harvest_cost > 0.0
                    else 0.0
                ),
                "deadband_sec": deadband_sec,
                "best_action_outside_deadband": best_action,
                "source_action_cost_sec": source_cost,
                "oracle_cost_sec": oracle_cost,
                "oracle_gain_before_overhead_sec": (
                    oracle_gain_before_overhead
                ),
                "inference_overhead_sec": float(
                    args.inference_overhead_sec
                ),
                "net_oracle_gain_sec": net_oracle_gain,
                "override_or_abstain_target": override_action,
                "fork_node_lp_bound": bounds[0],
                "paired_fork_node_lp_bounds": {
                    action: bounds[index]
                    for index, action in enumerate(ACTIONS)
                },
                "paired_bound_abs_delta": bound_abs_delta,
                "observation_count_by_action": {
                    action: len(observations[action])
                    for action in ACTIONS
                },
                "fork_paths_by_action": {
                    action: [
                        row["_path"] for row in by_action[action]
                    ]
                    for action in ACTIONS
                },
            }
        )

    proof_best_count = sum(
        row["best_action_outside_deadband"] == "proof_only"
        for row in rows
    )
    harvest_best_count = sum(
        row["best_action_outside_deadband"]
        == "harvest_then_proof"
        for row in rows
    )
    indistinguishable_count = sum(
        row["best_action_outside_deadband"] == "indistinguishable"
        for row in rows
    )
    override_rows = [
        row
        for row in rows
        if row["override_or_abstain_target"] != "abstain"
    ]
    by_scale = {}
    for scale in sorted(
        {int(row["scale"]) for row in rows}
    ):
        scale_rows = [
            row for row in rows if int(row["scale"]) == scale
        ]
        by_scale[str(scale)] = {
            "paired_state_count": len(scale_rows),
            "override_target_count": sum(
                row["override_or_abstain_target"] != "abstain"
                for row in scale_rows
            ),
            "total_oracle_gain_before_overhead_sec": sum(
                float(row["oracle_gain_before_overhead_sec"])
                for row in scale_rows
            ),
            "total_inference_overhead_sec": (
                len(scale_rows)
                * float(args.inference_overhead_sec)
            ),
            "total_net_oracle_gain_sec": sum(
                float(row["net_oracle_gain_sec"])
                for row in scale_rows
            ),
            "net_oracle_gain_mean_bootstrap": (
                _bootstrap_mean_interval(
                    [
                        float(row["net_oracle_gain_sec"])
                        for row in scale_rows
                    ],
                    state_hashes=[
                        str(row["source_state_hash"])
                        for row in scale_rows
                    ],
                )
            ),
        }
    summary = {
        "paired_state_count": len(rows),
        "assumed_guidance_call_count": len(rows),
        "missing_pair_count": len(missing_pairs),
        "proof_best_count": proof_best_count,
        "harvest_best_count": harvest_best_count,
        "indistinguishable_count": indistinguishable_count,
        "override_target_count": len(override_rows),
        "abstain_target_count": len(rows) - len(override_rows),
        "total_net_oracle_gain_sec": sum(
            float(row["net_oracle_gain_sec"]) for row in rows
        ),
        "total_oracle_gain_before_overhead_sec": sum(
            float(row["oracle_gain_before_overhead_sec"])
            for row in rows
        ),
        "total_inference_overhead_sec": (
            len(rows) * float(args.inference_overhead_sec)
        ),
        "positive_net_oracle_gain_count": sum(
            float(row["net_oracle_gain_sec"]) > 0.0
            for row in rows
        ),
        "net_oracle_gain_mean_bootstrap": (
            _bootstrap_mean_interval(
                [
                    float(row["net_oracle_gain_sec"])
                    for row in rows
                ],
                state_hashes=[
                    str(row["source_state_hash"])
                    for row in rows
                ],
            )
        ),
        "by_scale": by_scale,
        "action_label_density": (
            (proof_best_count + harvest_best_count) / len(rows)
            if rows
            else 0.0
        ),
        "override_label_density": (
            len(override_rows) / len(rows) if rows else 0.0
        ),
        "training_authorized": False,
        "training_blocker": (
            "PILOT_ONLY_REQUIRES_MORE_INSTANCES_AND_REPEATED_FORKS"
        ),
    }
    output = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "can_certify": False,
        "objective": (
            "paired_exact_cost_to_closure_one_step_action_regret"
        ),
        "inference_overhead_sec": float(
            args.inference_overhead_sec
        ),
        "absolute_deadband_sec": float(
            args.absolute_deadband_sec
        ),
        "relative_deadband": float(args.relative_deadband),
        "bound_match_tolerance": float(
            args.bound_match_tolerance
        ),
        "summary": summary,
        "missing_pairs": missing_pairs,
        "rows": rows,
    }
    _write_json(
        (ROOT / args.output).resolve(),
        {**output, "artifact_hash": _sha256_json(output)},
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
