#!/usr/bin/env python3
"""Execute one fresh-process arm of a P0V4 matched route rollout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.one_deviation_rollout import (  # noqa: E402
    execute_rollout_arm,
    matched_state_hashes,
    selected_exact_runtime_binding,
)
from lunar_ice_bpc.guidance.route_admission import (  # noqa: E402
    fixed_exact_admission_batch_size,
    validate_route_admission_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--action-manifest", required=True)
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--replicate-id", required=True)
    parser.add_argument("--budget-sec", type=float, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    snapshot_path = _resolve(args.snapshot)
    action_path = _resolve(args.action_manifest)
    instance_path = _resolve(args.instance)
    fixed_path = _resolve(args.fixed_k_selection)
    output = _resolve(args.output)
    snapshot = validate_route_admission_snapshot(
        _load_json(snapshot_path)
    )
    action_manifest = _load_json(action_path)
    fixed = _load_json(fixed_path)
    if str(fixed.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("arm execution requires a frozen fixed E_K")
    batch_size = fixed_exact_admission_batch_size(
        fixed, scale=int(snapshot["scale"])
    )
    if batch_size != int(snapshot["selection_limit"]):
        raise SystemExit("fixed E_K differs from route snapshot")
    actions = {
        str(row["action_id"]): dict(row)
        for row in action_manifest.get("actions", ())
    }
    action = actions.get(str(args.action_id))
    if action is None:
        raise SystemExit("requested action is absent from manifest")
    state_hashes = matched_state_hashes(
        snapshot,
        fixed_k_selection_hash=_sha256(fixed_path),
    )
    expected_budget = 300.0 if int(snapshot["scale"]) == 50 else 120.0
    if abs(float(args.budget_sec) - expected_budget) > 1.0e-9:
        raise SystemExit("arm budget differs from preregistered matched budget")
    if float(snapshot.get("remaining_solve_budget_sec") or 0.0) < (
        expected_budget
    ):
        raise SystemExit("snapshot lacks the matched rollout budget")
    exact_runtime = selected_exact_runtime_binding(
        fixed,
        scale=int(snapshot["scale"]),
    )
    backend = str(exact_runtime["backend_id"])
    if int(exact_runtime["admission_batch_size"]) != batch_size:
        raise SystemExit("selected Exact runtime differs from frozen E_K")
    actual_engine = spprc_engine_build_hash(backend)
    if actual_engine != state_hashes["exact_engine_hash"]:
        raise SystemExit(
            "fresh arm exact engine hash differs from source snapshot"
        )
    expected_source_config_hash = stable_payload_hash(
        {
            "schema_version": (
                "lunar_ice_bpc.harvest_guidance_config.v1"
            ),
            "source_phase": str(snapshot["source_phase"]),
            "negative_eps": 1.0e-6,
            "max_selected": batch_size,
            "backend_id": backend,
        }
    )
    if expected_source_config_hash != state_hashes["exact_config_hash"]:
        raise SystemExit(
            "fresh arm source configuration differs from snapshot"
        )
    thread_state = dict(
        snapshot["counterfactual_state"]["thread_state"]
    )
    for key, environment_key in (
        ("rmp_highs_threads", "LUNAR_ICE_RMP_HIGHS_THREADS"),
        ("omp_num_threads", "OMP_NUM_THREADS"),
    ):
        expected = int(thread_state.get(key) or 1)
        actual = int(os.getenv(environment_key, "1") or 1)
        if actual != expected:
            raise SystemExit(
                f"fresh arm thread state differs: {environment_key}"
            )
    data = load_lunar_ice_data(
        json.loads(instance_path.read_text(encoding="utf-8"))
    )
    if data.instance_content_hash != str(
        snapshot["instance_content_hash"]
    ):
        raise SystemExit("arm instance hash differs from snapshot")
    if int(data.scale) != int(snapshot["scale"]):
        raise SystemExit("arm instance scale differs from snapshot")
    result = execute_rollout_arm(
        data,
        snapshot,
        action,
        budget_sec=float(args.budget_sec),
        batch_size=batch_size,
        max_rounds=3,
        exact_backend=backend,
        exact_runtime_binding=exact_runtime,
        memory_limit_gb=float(
            snapshot.get("memory_limit_gb") or 0.0
        ),
    )
    payload = {
        **result,
        "replicate_id": str(args.replicate_id),
        "snapshot": str(snapshot_path),
        "snapshot_sha256": _sha256(snapshot_path),
        "action_manifest": str(action_path),
        "action_manifest_sha256": _sha256(action_path),
        "fixed_k_selection": str(fixed_path),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "instance": str(instance_path),
        "instance_sha256": _sha256(instance_path),
        "state_hashes": state_hashes,
        "exact_runtime_binding": exact_runtime,
        "exact_runtime_binding_hash": str(
            exact_runtime["runtime_binding_hash"]
        ),
        "fresh_process_arm": True,
    }
    _write_json(output, payload)
    return 0


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
