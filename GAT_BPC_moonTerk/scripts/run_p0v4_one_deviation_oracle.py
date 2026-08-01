#!/usr/bin/env python3
"""Generate matched one-deviation rollout packages in fresh arm processes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.one_deviation_oracle import (  # noqa: E402
    validate_one_deviation_rollouts,
)
from lunar_ice_bpc.guidance.one_deviation_rollout import (  # noqa: E402
    build_matched_rollout_context,
    materialize_matched_rollout_rows,
    selected_exact_runtime_binding,
    training_row_from_harvest,
)
from lunar_ice_bpc.guidance.route_admission import (  # noqa: E402
    ONE_DEVIATION_NOOP_ACTION_ID,
    validate_route_admission_snapshot,
    validate_route_opportunity_census_binding,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402


ARM_RUNNER = ROOT / "scripts/run_p0v4_one_deviation_arm.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action-manifest", required=True)
    parser.add_argument("--opportunity-census", required=True)
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--promotion-arm-count", type=int, default=2)
    parser.add_argument(
        "--engineering-smoke",
        action="store_true",
        help=(
            "Allow one diagnostic context when its own scale passed the "
            "opportunity gate but the joint scale30/50 census did not. "
            "The resulting package is explicitly barred from training and "
            "formal claims."
        ),
    )
    args = parser.parse_args()
    action_path = _resolve(args.action_manifest)
    census_path = _resolve(args.opportunity_census)
    fixed_path = _resolve(args.fixed_k_selection)
    instance_path = _resolve(args.instance)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_manifest = _load_json(action_path)
    census = _load_json(census_path)
    fixed = _load_json(fixed_path)
    if str(fixed.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("matched rollout requires frozen E_K")
    fixed_k_sha256 = _sha256(fixed_path)
    try:
        census_binding_hash = (
            validate_route_opportunity_census_binding(
                census,
                fixed_k_selection_sha256=fixed_k_sha256,
            )
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if str(source_manifest.get("fixed_k_selection_sha256")) != _sha256(
        fixed_path
    ):
        raise SystemExit("action manifest/fixed E_K hash mismatch")
    if (
        str(source_manifest.get("census_content_binding_hash"))
        != census_binding_hash
    ):
        raise SystemExit("action manifest/opportunity census mismatch")
    snapshot_path = Path(str(source_manifest["source_snapshot"]))
    if _sha256(snapshot_path) != str(
        source_manifest["source_snapshot_sha256"]
    ):
        raise SystemExit("route snapshot hash drift")
    snapshot = validate_route_admission_snapshot(
        _load_json(snapshot_path)
    )
    try:
        rollout_scope = _rollout_authorization_scope(
            census,
            scale=int(snapshot["scale"]),
            engineering_smoke=bool(args.engineering_smoke),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    exact_runtime_binding = selected_exact_runtime_binding(
        fixed,
        scale=int(snapshot["scale"]),
    )
    native_build_dir = _native_build_dir(exact_runtime_binding)
    authorized_snapshot = _authorized_snapshot_record(
        census, snapshot_hash=str(snapshot["snapshot_hash"])
    )
    if snapshot_path.resolve() != Path(
        str(authorized_snapshot["source_snapshot"])
    ).resolve():
        raise SystemExit("route snapshot path differs from census")
    if str(authorized_snapshot["source_snapshot_sha256"]) != _sha256(
        snapshot_path
    ):
        raise SystemExit("route snapshot is not the census-bound artifact")
    if str(authorized_snapshot["instance_content_hash"]) != str(
        snapshot["instance_content_hash"]
    ):
        raise SystemExit("route snapshot instance differs from census")
    expected_split = str(authorized_snapshot["instance_split"])
    if str(source_manifest.get("instance_split")) != expected_split:
        raise SystemExit("action manifest instance split differs from census")
    selected_manifest = _select_actions(
        source_manifest,
        promotion_count=max(2, int(args.promotion_arm_count)),
    )
    selected_path = output / "selected_action_manifest.json"
    _write_json(selected_path, selected_manifest)
    context = build_matched_rollout_context(
        snapshot,
        selected_manifest,
        fixed_k_selection_hash=fixed_k_sha256,
    )
    _write_json(output / "oracle_context.json", context)
    pre_action_feature_row = _training_row(
        snapshot_path,
        snapshot,
        selected_manifest,
        census,
    )
    thread_state = dict(
        snapshot["counterfactual_state"]["thread_state"]
    )
    thread_environment = {
        "LUNAR_ICE_RMP_HIGHS_THREADS": str(
            int(thread_state.get("rmp_highs_threads") or 1)
        ),
        "OMP_NUM_THREADS": str(
            int(thread_state.get("omp_num_threads") or 1)
        ),
    }
    actions = [
        dict(value) for value in selected_manifest["actions"]
    ]
    raw_by_replicate: dict[str, list[dict]] = {}
    execution_rows = []
    for replicate_index in range(3):
        replicate_id = f"blocked_{replicate_index + 1:02d}"
        ordered_actions = _rotated(actions, replicate_index)
        raw_rows = []
        for action in ordered_actions:
            action_id = str(action["action_id"])
            arm_output = (
                output
                / "raw_arms"
                / replicate_id
                / f"{action_id}.json"
            )
            command = [
                sys.executable,
                str(ARM_RUNNER),
                "--snapshot",
                str(snapshot_path),
                "--action-manifest",
                str(selected_path),
                "--action-id",
                action_id,
                "--instance",
                str(instance_path),
                "--fixed-k-selection",
                str(fixed_path),
                "--replicate-id",
                replicate_id,
                "--budget-sec",
                str(context["matched_rollout_budget_sec"]),
                "--output",
                str(arm_output),
            ]
            observed = _run_observed(
                command,
                output=arm_output,
                timeout_sec=(
                    float(context["matched_rollout_budget_sec"])
                    + 120.0
                ),
                native_build_dir=native_build_dir,
                environment_overrides=thread_environment,
            )
            execution_rows.append(
                {
                    "replicate_id": replicate_id,
                    "action_id": action_id,
                    "command": command,
                    **observed,
                }
            )
            _write_json(
                output / "rollout_execution_rows.json",
                execution_rows,
            )
            if int(observed["returncode"]) != 0 or not arm_output.is_file():
                raise SystemExit(
                    f"matched arm failed {replicate_id}/{action_id}"
                )
            raw = _load_json(arm_output)
            raw["peak_process_tree_rss_gb"] = float(
                observed["peak_process_tree_rss_gb"]
            )
            raw["memory_adverse_event"] = bool(
                raw.get("memory_adverse_event")
                or observed.get("termination_reason")
                or (
                    float(snapshot.get("memory_limit_gb") or 0.0)
                    > 0.0
                    and float(observed["peak_process_tree_rss_gb"])
                    > float(snapshot["memory_limit_gb"])
                )
            )
            raw_rows.append(raw)
        raw_by_replicate[replicate_id] = raw_rows
    rollout_rows = materialize_matched_rollout_rows(
        context, raw_by_replicate
    )
    validation = validate_one_deviation_rollouts(
        context, rollout_rows
    )
    all_raw = [
        row for rows in raw_by_replicate.values() for row in rows
    ]
    selected_action_manifest_sha256 = _sha256(selected_path)
    raw_binding_redline_count = sum(
        int(str(row.get("snapshot_sha256")) != _sha256(snapshot_path))
        + int(
            str(row.get("action_manifest_sha256"))
            != selected_action_manifest_sha256
        )
        + int(
            str(row.get("fixed_k_selection_sha256"))
            != fixed_k_sha256
        )
        + int(
            str(row.get("exact_runtime_binding_hash"))
            != str(exact_runtime_binding["runtime_binding_hash"])
        )
        + int(
            dict(row.get("exact_runtime_binding") or {})
            != exact_runtime_binding
        )
        for row in all_raw
    )
    package = {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_rollout_package.v1"
        ),
        "context": context,
        "rollouts": rollout_rows,
        "training_row": (
            None
            if bool(rollout_scope["engineering_smoke_only"])
            else pre_action_feature_row
        ),
        "diagnostic_feature_row": (
            pre_action_feature_row
            if bool(rollout_scope["engineering_smoke_only"])
            else None
        ),
        **rollout_scope,
        "legacy_empty_cut_lineage_reconstructed": (
            _legacy_empty_cut_lineage_reconstructed(snapshot)
        ),
        "validation": validation,
        "correctness_redline_count": sum(
            int(row.get("correctness_redline_count") or 0)
            for row in all_raw
        ),
        "hash_redline_count": sum(
            int(dict(row.get("state_hashes") or {}) != context["state_hashes"])
            for row in all_raw
        )
        + raw_binding_redline_count,
        "leakage_redline_count": 0,
        "candidate_filter_redline_count": 0,
        "certificate_redline_count": sum(
            int(bool(row.get("certificate_paths_mutated")))
            for row in all_raw
        ),
        "source_snapshot": str(snapshot_path.resolve()),
        "source_snapshot_sha256": _sha256(snapshot_path),
        "selected_action_manifest": str(selected_path.resolve()),
        "selected_action_manifest_sha256": (
            selected_action_manifest_sha256
        ),
        "selected_action_manifest_hash": stable_payload_hash(
            selected_manifest
        ),
        "selected_action_ids": [
            str(value["action_id"])
            for value in selected_manifest["actions"]
        ],
        "opportunity_census": str(census_path.resolve()),
        "opportunity_census_sha256": _sha256(census_path),
        "census_content_binding_hash": census_binding_hash,
        "fixed_k_selection": str(fixed_path.resolve()),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "exact_runtime_binding": exact_runtime_binding,
        "exact_runtime_binding_hash": str(
            exact_runtime_binding["runtime_binding_hash"]
        ),
        "native_build_dir": str(native_build_dir.resolve()),
        "instance": str(instance_path.resolve()),
        "instance_sha256": _sha256(instance_path),
        "fresh_process_per_arm": True,
        "blocked_action_order_rotated": True,
        "p0v4_deterministic_score_control_action_id": str(
            selected_manifest[
                "p0v4_deterministic_score_control_action_id"
            ]
        ),
        "perfect_oracle_control_materialized_by_auditor": True,
    }
    target = output / "one_deviation_rollout_package.json"
    _write_json(target, package)
    print(json.dumps(package["validation"], indent=2, sort_keys=True))
    return 0


def _rollout_authorization_scope(
    census: dict,
    *,
    scale: int,
    engineering_smoke: bool,
) -> dict:
    """Keep early signal checks separate from the formal oracle gate."""

    joint_authorized = bool(census.get("expensive_oracle_authorized"))
    if joint_authorized and not engineering_smoke:
        return {
            "execution_scope": "formal_joint_scale_oracle",
            "formal_joint_scale_census_authorized": True,
            "engineering_smoke_only": False,
            "gat_training_authorized": True,
            "formal_claim_authorized": True,
        }
    if not engineering_smoke:
        raise ValueError("opportunity census did not authorize rollouts")
    scale_row = dict(
        dict(census.get("audit") or {}).get("scales") or {}
    ).get(str(int(scale)))
    if not isinstance(scale_row, dict) or not bool(
        scale_row.get("gate_pass")
    ):
        raise ValueError(
            "engineering smoke requires its scale opportunity gate to pass"
        )
    return {
        "execution_scope": "engineering_smoke_scale_gate_only",
        "formal_joint_scale_census_authorized": joint_authorized,
        "engineering_smoke_only": True,
        "gat_training_authorized": False,
        "formal_claim_authorized": False,
    }


def _legacy_empty_cut_lineage_reconstructed(snapshot: dict) -> bool:
    return bool(
        not str(
            dict(snapshot.get("canonical_solve_binding") or {}).get(
                "cut_lineage_hash"
            )
            or ""
        )
        and not list(
            dict(snapshot.get("full_cut_context") or {}).get("cuts")
            or ()
        )
    )


def _select_actions(manifest: dict, *, promotion_count: int) -> dict:
    actions = [dict(value) for value in manifest.get("actions", ())]
    action_ids = [str(value.get("action_id") or "") for value in actions]
    if (
        any(not value for value in action_ids)
        or len(action_ids) != len(set(action_ids))
    ):
        raise SystemExit("action manifest contains duplicate identities")
    controls = [
        value
        for value in actions
        if str(value["action_id"]) == ONE_DEVIATION_NOOP_ACTION_ID
    ]
    promotions = [
        value
        for value in actions
        if str(value["action_id"]) != ONE_DEVIATION_NOOP_ACTION_ID
    ]
    promotions.sort(
        key=lambda value: (
            int(value.get("promoted_from_rank") or 0),
            str(value["action_id"]),
        )
    )
    if len(controls) != 1 or len(promotions) < 2:
        raise SystemExit(
            "action manifest requires one no-op and two promotions"
        )
    count = min(len(promotions), max(2, int(promotion_count)))
    if count == len(promotions):
        selected = promotions
    else:
        selected = [
            promotions[
                round(index * (len(promotions) - 1) / (count - 1))
            ]
            for index in range(count)
        ]
    if len({str(value["action_id"]) for value in selected}) != count:
        raise SystemExit("promotion-arm sampling produced duplicates")
    return {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_selected_action_manifest.v1"
        ),
        "snapshot_hash": str(manifest["snapshot_hash"]),
        "node_id": "root",
        "p0_batch_size": int(manifest["p0_batch_size"]),
        "omitted_window": int(manifest["omitted_window"]),
        "actions": [controls[0], *selected],
        "p0v4_deterministic_score_control_action_id": str(
            selected[0]["action_id"]
        ),
        "promotion_arm_sampling_policy": (
            "include_rank_k_plus_1_then_evenly_spaced_through_k_plus_32"
        ),
        "intervention_count_limit_per_root": 1,
        "next_round_policy": "restore_frozen_exact_p0_order",
        "guidance_filter_count": 0,
        "permanent_drop_count": 0,
        "can_certify": False,
    }


def _training_row(
    snapshot_path: Path,
    snapshot: dict,
    selected_manifest: dict,
    census: dict,
) -> dict:
    harvest_path = snapshot_path.parent / "harvest.json"
    if not harvest_path.is_file():
        raise ValueError(
            "matched rollout requires the pre-action harvest features"
        )
    instance_hash = str(snapshot["instance_content_hash"])
    split = str(
        dict(census.get("instance_split_by_hash") or {}).get(
            instance_hash
        )
        or ""
    )
    if split not in {"train", "calibration"}:
        raise ValueError(
            "opportunity census lacks a pre-outcome instance split"
        )
    return training_row_from_harvest(
        _load_json(harvest_path),
        selected_manifest,
        instance_content_hash=instance_hash,
        split=split,
    )


def _authorized_snapshot_record(
    census: dict,
    *,
    snapshot_hash: str,
) -> dict:
    matches = [
        dict(value)
        for value in census.get("eligible_snapshots", ())
        if str(dict(value).get("snapshot_hash") or "")
        == str(snapshot_hash)
    ]
    if len(matches) != 1:
        raise SystemExit(
            "route snapshot is not uniquely authorized by the census"
        )
    record = matches[0]
    instance_hash = str(record.get("instance_content_hash") or "")
    split = str(
        dict(census.get("instance_split_by_hash") or {}).get(
            instance_hash
        )
        or ""
    )
    if split not in {"train", "calibration"} or split != str(
        record.get("instance_split") or ""
    ):
        raise SystemExit("census instance split binding is invalid")
    return record


def _rotated(rows: list[dict], offset: int) -> list[dict]:
    if not rows:
        return []
    shift = int(offset) % len(rows)
    return rows[shift:] + rows[:shift]


def _run_observed(
    command: list[str],
    *,
    output: Path,
    timeout_sec: float,
    native_build_dir: Path,
    environment_overrides: dict[str, str] | None = None,
) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = output.with_suffix(".stdout.log")
    stderr_path = output.with_suffix(".stderr.log")
    started = monotonic()
    peak_rss = 0
    termination_reason = ""
    environment = dict(os.environ)
    paths = [
        str(ROOT / "src"),
        str(native_build_dir.resolve()),
    ]
    if environment.get("PYTHONPATH"):
        paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    environment.update(environment_overrides or {})
    with stdout_path.open("w", encoding="utf-8") as stdout, (
        stderr_path.open("w", encoding="utf-8")
    ) as stderr:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        while process.poll() is None:
            peak_rss = max(
                peak_rss, _process_tree_rss_bytes(process.pid)
            )
            if monotonic() - started >= timeout_sec:
                termination_reason = "MATCHED_ARM_OUTER_DEADLINE"
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10.0)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5.0)
                break
            sleep(0.25)
        returncode = int(process.wait())
    return {
        "returncode": returncode,
        "launcher_wall_time_sec": monotonic() - started,
        "peak_process_tree_rss_gb": (
            peak_rss / (1024.0**3)
        ),
        "termination_reason": termination_reason,
        "stdout": str(stdout_path.resolve()),
        "stderr": str(stderr_path.resolve()),
    }


def _native_build_dir(exact_runtime_binding: dict) -> Path:
    backend = str(exact_runtime_binding.get("backend_id") or "")
    if not backend:
        raise SystemExit("matched rollout Exact backend is missing")
    result = (
        ROOT / "build/native-spprc-bidirectional-feasibility-v1"
        if "bidirectional" in backend
        else ROOT / "build/native-spprc-memory-opt-v2"
    )
    if not result.is_dir() or not any(result.glob("lunar_spprc_native*.so")):
        raise SystemExit(f"matched rollout Native build is missing: {result}")
    return result.resolve()


def _process_tree_rss_bytes(root_pid: int) -> int:
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            fields = (entry / "status").read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except OSError:
            continue
        parent = 0
        resident = 0
        for line in fields:
            if line.startswith("PPid:"):
                parent = int(line.split()[1])
            elif line.startswith("VmRSS:"):
                resident = int(line.split()[1]) * 1024
        children.setdefault(parent, []).append(pid)
        rss[pid] = resident
    total = 0
    stack = [int(root_pid)]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss.get(pid, 0)
        stack.extend(children.get(pid, ()))
    return total


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
