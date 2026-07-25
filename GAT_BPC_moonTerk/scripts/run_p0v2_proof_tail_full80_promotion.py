#!/usr/bin/env python3
"""Run the protected full80 P0/Q0 versus dynamic-QD1 paired promotion.

The protected set is resolved only from the audited split and historical
instance-hash manifests.  Every slot is a fresh subprocess; completed slots
are persisted and may be recovered by relaunching this harness, while solver
resume remains disabled.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import statistics
import sys
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_p0v2_gat_b0_development import _run_one  # noqa: E402

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


EXPECTED_SCHEMA = (
    "lunar_ice_bpc.proof_tail_full80_promotion_manifest.v1"
)
EXPECTED_SCALES = (5, 10, 20, 30)
BOOTSTRAP_SEED = 20260724
BOOTSTRAP_REPLICATES = 20_000
RUNTIME_SOURCE_GLOBS = (
    "src/lunar_ice_bpc/**/*.py",
    "native/lunar_spprc/CMakeLists.txt",
    "native/lunar_spprc/include/**/*",
    "native/lunar_spprc/src/**/*",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/run_lunar_ice_b4_2_cold_exact.py",
    "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py",
    "scripts/run_p0v2_gat_b0_development.py",
    "scripts/run_p0v2_proof_tail_full80_promotion.py",
    "build/native-spprc/lunar_spprc_native*.so",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"invalid YAML object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _runtime_source_bundle() -> dict[str, Any]:
    files: set[Path] = set()
    for pattern in RUNTIME_SOURCE_GLOBS:
        files.update(
            path
            for path in ROOT.glob(pattern)
            if path.is_file()
        )
    rows = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": _sha256(path),
        }
        for path in sorted(files)
    ]
    if not rows:
        raise SystemExit("runtime source bundle is empty")
    return {
        "schema_version": (
            "lunar_ice_bpc.proof_tail_runtime_source_bundle.v1"
        ),
        "file_count": len(rows),
        "files": rows,
        "sha256": _stable_hash(rows),
    }


def _validate_runtime_source_bundle(
    expected: dict[str, Any],
) -> None:
    current = _runtime_source_bundle()
    if (
        current.get("sha256") != expected.get("sha256")
        or current.get("file_count") != expected.get("file_count")
    ):
        raise SystemExit("runtime source/native bundle drifted")


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * float(probability)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + weight * (
        ordered[upper] - ordered[lower]
    )


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _instance_row(
    *,
    scale: int,
    index: int,
    relative_path: str,
    expected_file_hash: str,
    protected_by_hash: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    path = ROOT / relative_path
    if not path.is_file():
        raise SystemExit(f"frozen instance is missing: {relative_path}")
    if _sha256(path) != expected_file_hash:
        raise SystemExit(f"frozen instance hash drift: {relative_path}")
    raw = _load_json(path)
    data = load_lunar_ice_data(raw)
    if int(data.scale) != int(scale):
        raise SystemExit(f"frozen instance scale mismatch: {relative_path}")
    protected = protected_by_hash.get(data.instance_content_hash)
    if protected is None:
        raise SystemExit(
            f"instance is absent from protected split: {relative_path}"
        )
    if str(protected.get("instance_id")) != str(data.instance_id):
        raise SystemExit(
            f"protected instance ID mismatch: {relative_path}"
        )
    if str(protected.get("source_role")) != "full80_exact_test":
        raise SystemExit(
            f"protected instance has wrong source role: {relative_path}"
        )
    return {
        "scale": int(scale),
        "index": int(index),
        "path": relative_path,
        "instance_id": str(data.instance_id),
        "instance_content_hash": str(data.instance_content_hash),
        "instance_file_sha256": expected_file_hash,
    }


def _validate_manifest(
    manifest_path: Path,
) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != EXPECTED_SCHEMA:
        raise SystemExit("unsupported full80 promotion manifest schema")
    if tuple(int(value) for value in manifest.get("scales", ())) != (
        EXPECTED_SCALES
    ):
        raise SystemExit("formal full80 scales must be 5/10/20/30")
    if (
        bool(manifest.get("development_used_in_formal_rows"))
        or bool(manifest.get("calibration_used_in_formal_rows"))
        or not bool(manifest.get("protected_final_test_used"))
    ):
        raise SystemExit("formal rows must use protected full80 only")
    if not bool(manifest.get("candidate_frozen_before_protected_test")):
        raise SystemExit("candidate was not frozen before protected test")
    if int(manifest.get("workers") or 0) != 1:
        raise SystemExit("formal full80 promotion must use one worker")
    if (
        int(manifest.get("instances_per_scale") or 0) != 20
        or int(manifest.get("instance_count") or 0) != 80
        or int(manifest.get("slot_count") or 0) != 160
        or int(manifest.get("repeats_per_instance_per_mode") or 0)
        != 1
    ):
        raise SystemExit("formal full80 cardinality is not 80/160")
    if (
        not bool(manifest.get("strict_cold_start"))
        or not bool(manifest.get("fresh_python_native_runtime_per_slot"))
        or bool(manifest.get("solver_resume"))
    ):
        raise SystemExit("formal full80 cold-start contract is invalid")

    evidence_path = ROOT / str(
        manifest["candidate_selection_evidence"]
    )
    if _sha256(evidence_path) != str(
        manifest["candidate_selection_evidence_sha256"]
    ):
        raise SystemExit("candidate-selection evidence hash mismatch")
    evidence = _load_json(evidence_path)
    if not bool(evidence.get("promotion_passed")):
        raise SystemExit("held-out candidate-selection gate did not pass")
    if bool(evidence.get("protected_final_test_used")):
        raise SystemExit("candidate selection used protected final test")

    control_path = ROOT / str(manifest["control_config"])
    candidate_path = ROOT / str(manifest["candidate_config"])
    control = _load_yaml(control_path)
    candidate = _load_yaml(candidate_path)
    allowed_differences = {
        "model_id",
        "native_proof_queue_experiment_policy",
    }
    unexpected = [
        key
        for key in sorted(set(control) | set(candidate))
        if key not in allowed_differences
        and control.get(key) != candidate.get(key)
    ]
    if unexpected:
        raise SystemExit(
            "control/candidate differ outside queue policy: "
            + ",".join(unexpected)
        )
    if control.get("native_proof_queue_experiment_policy") != "off":
        raise SystemExit("formal control is not Q0")
    if candidate.get("native_proof_queue_experiment_policy") != str(
        manifest["candidate_rule"]
    ):
        raise SystemExit("formal candidate rule/config mismatch")

    frozen_p0_manifest = _load_json(
        ROOT
        / "runs/frozen_native_live_sri_p0_optimized_baseline_v2_20260723"
        / "baseline_freeze_manifest.json"
    )
    if frozen_p0_manifest.get("freeze_id") != str(
        manifest["control_baseline_id"]
    ):
        raise SystemExit("control baseline ID mismatch")
    frozen_config_path = ROOT / str(
        (frozen_p0_manifest.get("config_snapshot") or {}).get("path")
    )
    frozen_control = _load_yaml(frozen_config_path)
    frozen_keys = set(frozen_control) | set(control)
    unexpected_control = [
        key
        for key in sorted(frozen_keys)
        if key not in allowed_differences
        and frozen_control.get(key) != control.get(key)
    ]
    if unexpected_control:
        raise SystemExit(
            "formal Q0 control drifted from P0 V2: "
            + ",".join(unexpected_control)
        )

    split_path = ROOT / str(manifest["split_manifest"])
    split = _load_json(split_path)
    if (
        not bool((split.get("audit") or {}).get("passed"))
        or split.get("manifest_hash") != manifest.get(
            "split_manifest_hash"
        )
    ):
        raise SystemExit("protected split manifest audit/hash mismatch")
    protected_rows = [
        row
        for row in split.get("protected_final_test", ())
        if int(row.get("scale") or 0) in EXPECTED_SCALES
        and str(row.get("source_role")) == "full80_exact_test"
    ]
    if len(protected_rows) != 80:
        raise SystemExit("protected split does not contain full80")
    protected_by_hash = {
        str(row["instance_content_hash"]): row
        for row in protected_rows
    }

    instance_manifest_path = ROOT / str(
        manifest["instance_hash_manifest"]
    )
    if _sha256(instance_manifest_path) != str(
        manifest["instance_hash_manifest_sha256"]
    ):
        raise SystemExit("historical instance-hash manifest drift")
    instance_manifest = _load_json(instance_manifest_path)
    if (
        instance_manifest.get("freeze_id")
        != "FROZEN_NATIVE_NO_CUT_BASELINE_V1"
    ):
        raise SystemExit("unexpected historical instance freeze")

    instances: list[dict[str, Any]] = []
    for scale in EXPECTED_SCALES:
        rows = list(
            (instance_manifest.get("instances") or {}).get(
                str(scale), ()
            )
        )
        if len(rows) != 20:
            raise SystemExit(f"scale{scale} frozen count is not 20")
        for index, row in enumerate(rows, start=1):
            instances.append(
                _instance_row(
                    scale=scale,
                    index=index,
                    relative_path=str(row["path"]),
                    expected_file_hash=str(row["sha256"]),
                    protected_by_hash=protected_by_hash,
                )
            )
    if (
        len(instances) != 80
        or len(
            {
                str(row["instance_content_hash"])
                for row in instances
            }
        )
        != 80
    ):
        raise SystemExit("formal full80 instance identity is not unique")

    manifest_hash = _sha256(manifest_path)
    return manifest, manifest_hash, instances


def _build_schedule(
    manifest: dict[str, Any],
    instances: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    schedule: list[dict[str, Any]] = []
    for row in instances:
        scale = int(row["scale"])
        index = int(row["index"])
        order = (
            ("control", "candidate")
            if (scale + index) % 2 == 0
            else ("candidate", "control")
        )
        pair_id = f"scale{scale:02d}_instance{index:03d}"
        for order_index, arm in enumerate(order, start=1):
            schedule.append(
                {
                    **row,
                    "pair_id": pair_id,
                    "slot_id": (
                        f"s{scale:03d}:i{index:03d}:"
                        f"o{order_index}:{arm}"
                    ),
                    "arm": arm,
                    "order": "/".join(order),
                    "order_index": order_index,
                    "config": str(manifest[f"{arm}_config"]),
                }
            )
    if len(schedule) != 160:
        raise SystemExit("formal full80 schedule is not 160 slots")
    return schedule


def _policy_and_certificate_metrics(target: Path) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    tree: dict[str, Any] = {}
    paths = sorted(
        {
            *target.rglob("probe.json"),
            *target.rglob("tree_closure_*.json"),
        }
    )
    for path in paths:
        try:
            payload = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if path.name.startswith("tree_closure_"):
            tree = payload
        for dictionary in _walk_dicts(payload):
            policy = dictionary.get("proof_queue_policy_id")
            if policy is not None:
                counts[str(policy)] += 1
    summary_path = target / "native_spprc_acceptance_summary.json"
    configured_selector = ""
    if summary_path.is_file():
        summary = _load_json(summary_path)
        acceptance_row = (summary.get("rows") or [{}])[0]
        configured_selector = str(
            acceptance_row.get("proof_queue_experiment_policy") or ""
        )
    ledger = tree.get("certificate_ledger") or {}
    return {
        "proof_queue_policy_observation_counts": dict(
            sorted(counts.items())
        ),
        "configured_proof_queue_experiment_policy": (
            configured_selector
        ),
        "certificate_scope": str(
            tree.get("certificate_scope") or ""
        ),
        "exact_status": str(tree.get("exact_status") or ""),
        "global_lower_bound": tree.get("global_lower_bound"),
        "all_certificate_ledgers_valid": bool(
            tree.get("all_certificate_ledgers_valid")
        ),
        "all_node_lower_bounds_official": bool(
            tree.get("all_node_lower_bounds_official")
        ),
        "all_node_pricing_proofs_certifying": bool(
            tree.get("all_node_pricing_proofs_certifying")
        ),
        "tree_certificate_gate_issues": list(
            tree.get("tree_certificate_gate_issues") or ()
        ),
        "uses_true_dual_bpc_certificate": bool(
            tree.get("uses_true_dual_bpc_certificate")
        ),
        "certificate_ledger_valid": bool(ledger.get("valid")),
    }


def _safety_passed(row: dict[str, Any]) -> bool:
    safety = row.get("stage_b_safety") or {}
    return bool(
        row.get("redlines_zero")
        and int(safety.get("binding_mismatch_accepted") or 0) == 0
        and int(safety.get("guidance_induced_permanent_drop") or 0)
        == 0
        and int(safety.get("legal_universe_hash_mismatch") or 0)
        == 0
        and int(safety.get("nonfinite_hint_accepted") or 0) == 0
        and not bool(safety.get("labels_dropped"))
    )


def _exact_passed(row: dict[str, Any]) -> bool:
    return bool(
        row.get("algorithm_status") == "BPC_OPTIMAL"
        and row.get("bpc_tree_optimal")
        and row.get("row_terminal")
        and not row.get("row_budget_exhausted")
        and not row.get("outer_timeout")
        and int(row.get("subprocess_returncode") or 0) == 0
        and _safety_passed(row)
        and row.get("certificate_scope") == "BPC_TREE_OPTIMAL"
        and row.get("exact_status") == "BPC_TREE_OPTIMAL"
        and row.get("all_certificate_ledgers_valid")
        and row.get("all_node_lower_bounds_official")
        and row.get("all_node_pricing_proofs_certifying")
        and not row.get("tree_certificate_gate_issues")
        and row.get("uses_true_dual_bpc_certificate")
        and row.get("certificate_ledger_valid")
    )


def _bootstrap_log_mean_ci(
    log_ratios: list[float],
) -> tuple[float | None, float | None]:
    if not log_ratios:
        return None, None
    generator = random.Random(BOOTSTRAP_SEED)
    means = sorted(
        statistics.fmean(
            generator.choice(log_ratios)
            for _ in range(len(log_ratios))
        )
        for _ in range(BOOTSTRAP_REPLICATES)
    )
    return _quantile(means, 0.025), _quantile(means, 0.975)


def _build_audit(
    manifest: dict[str, Any],
    manifest_hash: str,
    schedule: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_slot = {str(row["slot_id"]): row for row in rows}
    pair_specs: dict[str, list[dict[str, Any]]] = {}
    for spec in schedule:
        pair_specs.setdefault(str(spec["pair_id"]), []).append(spec)

    pair_rows: list[dict[str, Any]] = []
    extra_incomplete = 0
    safety_failure_count = 0
    rss_ratios: list[float] = []
    candidate_rss_max = 0
    candidate_qd1_by_scale: dict[str, int] = {
        str(scale): 0 for scale in EXPECTED_SCALES
    }
    all_complete = True
    all_exact_equal = True

    for pair_id, specs in sorted(
        pair_specs.items(),
        key=lambda item: (
            int(item[1][0]["scale"]),
            int(item[1][0]["index"]),
        ),
    ):
        arms = {
            str(spec["arm"]): by_slot.get(str(spec["slot_id"]))
            for spec in specs
        }
        control = arms.get("control")
        candidate = arms.get("candidate")
        complete = control is not None and candidate is not None
        all_complete = all_complete and complete
        base = {
            "pair_id": pair_id,
            "scale": int(specs[0]["scale"]),
            "index": int(specs[0]["index"]),
            "instance_id": str(specs[0]["instance_id"]),
            "instance_content_hash": str(
                specs[0]["instance_content_hash"]
            ),
            "arms_complete": complete,
        }
        if not complete:
            all_exact_equal = False
            pair_rows.append(base)
            continue
        assert control is not None and candidate is not None
        control_exact = _exact_passed(control)
        candidate_exact = _exact_passed(candidate)
        objective_equal = bool(
            control_exact
            and candidate_exact
            and control.get("global_ub") is not None
            and candidate.get("global_ub") is not None
            and math.isclose(
                float(control["global_ub"]),
                float(candidate["global_ub"]),
                rel_tol=0.0,
                abs_tol=1.0e-9,
            )
            and control.get("global_lower_bound") is not None
            and candidate.get("global_lower_bound") is not None
            and math.isclose(
                float(control["global_lower_bound"]),
                float(candidate["global_lower_bound"]),
                rel_tol=0.0,
                abs_tol=1.0e-9,
            )
        )
        all_exact_equal = all_exact_equal and objective_equal
        if control_exact and not candidate_exact:
            extra_incomplete += 1
        safety_failure_count += int(not _safety_passed(control))
        safety_failure_count += int(not _safety_passed(candidate))

        control_wall = float(control["cold_start_total_sec"])
        candidate_wall = float(candidate["cold_start_total_sec"])
        ratio = candidate_wall / control_wall
        control_rss = int(
            control.get("process_tree_rss_peak_bytes") or 0
        )
        candidate_rss = int(
            candidate.get("process_tree_rss_peak_bytes") or 0
        )
        candidate_rss_max = max(candidate_rss_max, candidate_rss)
        if control_rss > 0:
            rss_ratios.append(candidate_rss / control_rss)
        scale_key = str(base["scale"])
        candidate_counts = (
            candidate.get("proof_queue_policy_observation_counts") or {}
        )
        candidate_qd1_by_scale[scale_key] += int(
            candidate_counts.get("QD1") or 0
        )
        base.update(
            {
                "control_exact": control_exact,
                "candidate_exact": candidate_exact,
                "exact_objective_and_certificate_equal": (
                    objective_equal
                ),
                "global_ub_control": control.get("global_ub"),
                "global_ub_candidate": candidate.get("global_ub"),
                "control_wall_sec": control_wall,
                "candidate_wall_sec": candidate_wall,
                "candidate_over_control_wall_ratio": ratio,
                "control_peak_rss_bytes": control_rss,
                "candidate_peak_rss_bytes": candidate_rss,
                "candidate_over_control_peak_rss_ratio": (
                    None
                    if control_rss <= 0
                    else candidate_rss / control_rss
                ),
                "control_safety_passed": _safety_passed(control),
                "candidate_safety_passed": _safety_passed(
                    candidate
                ),
                "candidate_proof_queue_policy_counts": (
                    candidate_counts
                ),
            }
        )
        pair_rows.append(base)

    per_scale: dict[str, dict[str, Any]] = {}
    scale_checks: dict[str, bool] = {}
    gate_by_scale = manifest["primary_gate"]["per_scale"]
    for scale in EXPECTED_SCALES:
        scale_key = str(scale)
        pairs = [
            row
            for row in pair_rows
            if int(row["scale"]) == scale
            and bool(
                row.get("exact_objective_and_certificate_equal")
            )
        ]
        ratios = [
            float(row["candidate_over_control_wall_ratio"])
            for row in pairs
        ]
        logs = [math.log(value) for value in ratios]
        control_times = [
            float(row["control_wall_sec"]) for row in pairs
        ]
        candidate_times = [
            float(row["candidate_wall_sec"]) for row in pairs
        ]
        lcb, ucb = _bootstrap_log_mean_ci(logs)
        geometric = (
            None if not logs else math.exp(statistics.fmean(logs))
        )
        median = None if not ratios else statistics.median(ratios)
        mean_ratio = (
            None
            if not control_times
            else statistics.fmean(candidate_times)
            / statistics.fmean(control_times)
        )
        worst = None if not ratios else max(ratios)
        limits = gate_by_scale[scale_key]
        checks = {
            "complete_exact_20": len(pairs) == 20,
            "geometric_mean_passed": geometric is not None
            and geometric
            <= float(
                limits["paired_geometric_mean_wall_ratio_max"]
            ),
            "median_passed": median is not None
            and median
            <= float(limits["paired_median_wall_ratio_max"]),
            "arithmetic_mean_passed": mean_ratio is not None
            and mean_ratio
            <= float(limits["arithmetic_mean_wall_ratio_max"]),
        }
        if "paired_log_ratio_bootstrap_ucb95_max" in limits:
            checks["bootstrap_ucb_passed"] = ucb is not None and ucb <= float(
                limits["paired_log_ratio_bootstrap_ucb95_max"]
            )
        if "worst_instance_wall_ratio_max" in limits:
            checks["worst_instance_passed"] = (
                worst is not None
                and worst
                <= float(limits["worst_instance_wall_ratio_max"])
            )
        scale_checks[scale_key] = all(checks.values())
        per_scale[scale_key] = {
            "completed_exact_pair_count": len(pairs),
            "paired_geometric_mean_wall_ratio": geometric,
            "paired_median_wall_ratio": median,
            "arithmetic_mean_wall_ratio": mean_ratio,
            "paired_worst_wall_ratio": worst,
            "paired_log_ratio_bootstrap_lcb95": lcb,
            "paired_log_ratio_bootstrap_ucb95": ucb,
            "candidate_qd1_observation_count": (
                candidate_qd1_by_scale[scale_key]
            ),
            "gate_checks": checks,
            "promotion_passed": all(checks.values()),
        }

    gate = manifest["primary_gate"]
    non_scale30_qd1 = sum(
        candidate_qd1_by_scale[str(scale)]
        for scale in (5, 10, 20)
    )
    rss_ratio_p90 = (
        None if not rss_ratios else _quantile(rss_ratios, 0.90)
    )
    global_checks = {
        "all_arms_complete": (
            all_complete and len(rows) == len(schedule) == 160
        ),
        "exact_objective_and_certificate_equal": all_exact_equal,
        "extra_incomplete_passed": extra_incomplete
        <= int(gate["extra_incomplete_allowed"]),
        "safety_passed": safety_failure_count
        <= int(gate["safety_redline_count_max"]),
        "rss_ratio_p90_passed": rss_ratio_p90 is not None
        and rss_ratio_p90
        <= float(gate["candidate_peak_rss_ratio_p90_max"]),
        "rss_absolute_passed": candidate_rss_max
        <= int(gate["candidate_peak_rss_absolute_max_bytes"]),
        "non_scale30_qd1_zero": non_scale30_qd1
        <= int(gate["candidate_qd1_count_non_scale30_max"]),
        "scale30_qd1_observed": candidate_qd1_by_scale["30"]
        >= int(gate["candidate_qd1_count_scale30_min"]),
        "all_scale_gates_passed": all(scale_checks.values()),
    }
    evaluable = bool(
        len(rows) == len(schedule)
        and all_complete
        and all(
            int(row["completed_exact_pair_count"]) == 20
            for row in per_scale.values()
        )
    )
    promotion_passed = evaluable and all(global_checks.values())
    return {
        "schema_version": (
            "lunar_ice_bpc.proof_tail_full80_promotion_audit.v1"
        ),
        "experiment_id": manifest["experiment_id"],
        "manifest_sha256": manifest_hash,
        "evidence_scope": manifest["evidence_scope"],
        "control_baseline_id": manifest["control_baseline_id"],
        "runtime_source_bundle_sha256": manifest.get(
            "_runtime_source_bundle_sha256"
        ),
        "production_default_switch_authorized": False,
        "expected_slot_count": len(schedule),
        "completed_slot_count": len(rows),
        "completed_pair_count": sum(
            bool(row.get("arms_complete")) for row in pair_rows
        ),
        "extra_incomplete_count": extra_incomplete,
        "safety_failure_count": safety_failure_count,
        "candidate_qd1_observation_count_by_scale": (
            candidate_qd1_by_scale
        ),
        "candidate_peak_rss_ratio_p90": rss_ratio_p90,
        "candidate_peak_rss_absolute_max_bytes": candidate_rss_max,
        "per_scale": per_scale,
        "global_gate_checks": global_checks,
        "promotion_evaluable": evaluable,
        "promotion_passed": promotion_passed,
        "status": (
            "PROMOTED_ACTIVE_EXPERIMENT_BASELINE"
            if promotion_passed
            else "NOT_PROMOTED"
            if evaluable
            else "IN_PROGRESS"
        ),
        "pairs": pair_rows,
    }


def _validate_input_hashes(
    manifest_path: Path,
    manifest_hash: str,
    manifest: dict[str, Any],
) -> None:
    if _sha256(manifest_path) != manifest_hash:
        raise SystemExit("promotion manifest drifted during run")
    evidence_path = ROOT / str(
        manifest["candidate_selection_evidence"]
    )
    if _sha256(evidence_path) != str(
        manifest["candidate_selection_evidence_sha256"]
    ):
        raise SystemExit("candidate-selection evidence drifted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    manifest_path = (ROOT / args.manifest).resolve()
    output_root = (ROOT / args.output_dir).resolve()
    manifest, manifest_hash, instances = _validate_manifest(
        manifest_path
    )
    schedule = _build_schedule(manifest, instances)
    schedule_hash = _stable_hash(schedule)
    current_runtime_bundle = _runtime_source_bundle()
    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "VALID",
                    "manifest_sha256": manifest_hash,
                    "schedule_sha256": schedule_hash,
                    "runtime_source_bundle_sha256": (
                        current_runtime_bundle["sha256"]
                    ),
                    "runtime_source_bundle_file_count": (
                        current_runtime_bundle["file_count"]
                    ),
                    "instance_count": len(instances),
                    "slot_count": len(schedule),
                },
                sort_keys=True,
            )
        )
        return 0

    output_root.mkdir(parents=True, exist_ok=True)
    frozen_dir = output_root / "frozen_inputs"
    frozen_dir.mkdir(parents=True, exist_ok=True)
    runtime_bundle_path = (
        frozen_dir / "runtime_source_bundle.json"
    )
    if runtime_bundle_path.exists():
        frozen_runtime_bundle = _load_json(runtime_bundle_path)
        _validate_runtime_source_bundle(frozen_runtime_bundle)
    else:
        frozen_runtime_bundle = current_runtime_bundle
        _atomic_write_json(
            runtime_bundle_path, frozen_runtime_bundle
        )
    manifest["_runtime_source_bundle_sha256"] = (
        frozen_runtime_bundle["sha256"]
    )
    frozen_manifest = frozen_dir / "promotion_manifest.json"
    if frozen_manifest.exists():
        if _sha256(frozen_manifest) != manifest_hash:
            raise SystemExit(
                "output directory is bound to another promotion manifest"
            )
    else:
        shutil.copy2(manifest_path, frozen_manifest)
        shutil.copy2(
            ROOT / str(manifest["control_config"]),
            frozen_dir / "control_config.yaml",
        )
        shutil.copy2(
            ROOT / str(manifest["candidate_config"]),
            frozen_dir / "candidate_config.yaml",
        )
    frozen_configs = {
        "control": frozen_dir / "control_config.yaml",
        "candidate": frozen_dir / "candidate_config.yaml",
    }
    if not all(path.is_file() for path in frozen_configs.values()):
        raise SystemExit("frozen promotion config copy is missing")
    frozen_config_hashes = {
        arm: _sha256(path)
        for arm, path in frozen_configs.items()
    }
    _atomic_write_json(
        output_root / "promotion_preflight.json",
        {
            "schema_version": (
                "lunar_ice_bpc.proof_tail_full80_preflight.v1"
            ),
            "passed": True,
            "manifest_sha256": manifest_hash,
            "schedule_sha256": schedule_hash,
            "runtime_source_bundle_sha256": (
                frozen_runtime_bundle["sha256"]
            ),
            "runtime_source_bundle_file_count": (
                frozen_runtime_bundle["file_count"]
            ),
            "frozen_config_hashes": frozen_config_hashes,
            "instance_count": len(instances),
            "slot_count": len(schedule),
            "protected_final_test_used": True,
            "development_used_in_formal_rows": False,
            "calibration_used_in_formal_rows": False,
        },
    )
    _atomic_write_json(
        output_root / "promotion_schedule.json",
        {
            "schema_version": (
                "lunar_ice_bpc.proof_tail_full80_schedule.v1"
            ),
            "manifest_sha256": manifest_hash,
            "schedule_sha256": schedule_hash,
            "strict_cold_start": True,
            "solver_resume": False,
            "fresh_python_native_runtime_per_slot": True,
            "slots": schedule,
        },
    )

    rows_path = output_root / "promotion_rows.json"
    rows = (
        list(_load_json(rows_path)) if rows_path.exists() else []
    )
    completed = {str(row["slot_id"]): row for row in rows}
    if len(completed) != len(rows):
        raise SystemExit("duplicate slot IDs in persisted promotion rows")

    audit = _build_audit(
        manifest, manifest_hash, schedule, rows
    )
    _atomic_write_json(output_root / "promotion_audit.json", audit)
    for slot_number, spec in enumerate(schedule, start=1):
        slot_id = str(spec["slot_id"])
        if slot_id in completed:
            continue
        _validate_input_hashes(
            manifest_path, manifest_hash, manifest
        )
        _validate_runtime_source_bundle(frozen_runtime_bundle)
        arm = str(spec["arm"])
        config_path = frozen_configs[arm]
        if _sha256(config_path) != frozen_config_hashes[arm]:
            raise SystemExit("frozen promotion config drifted")
        slot_root = (
            output_root / "raw" / str(spec["pair_id"]) / arm
        )
        print(
            f"START [{slot_number:03d}/{len(schedule):03d}] "
            f"{spec['pair_id']} arm={arm}",
            flush=True,
        )
        result = _run_one(
            spec,
            config=config_path,
            output_root=slot_root,
            snapshot_max_per_instance=1,
            outer_timeout_sec=float(
                manifest["outer_time_limit_sec"]
            ),
            resume=False,
            collect_training=False,
            deployment_manifest=None,
            guidance_mode="off",
            experiment_variant=(
                "P0_Q0_FULL80_CONTROL"
                if arm == "control"
                else "P0_DYNAMIC_QD1_FULL80_CANDIDATE"
            ),
        )
        target = (
            slot_root
            / f"scale_{int(spec['scale']):03d}"
            / f"instance_{int(spec['index']):03d}"
        )
        result.update(_policy_and_certificate_metrics(target))
        result.update(
            {
                "slot_id": slot_id,
                "pair_id": str(spec["pair_id"]),
                "arm": arm,
                "order": str(spec["order"]),
                "order_index": int(spec["order_index"]),
                "instance_file_sha256": str(
                    spec["instance_file_sha256"]
                ),
                "manifest_sha256": manifest_hash,
                "schedule_sha256": schedule_hash,
                "runtime_source_bundle_sha256": (
                    frozen_runtime_bundle["sha256"]
                ),
                "strict_cold_start": True,
                "solver_resume": False,
                "protected_final_test": True,
            }
        )
        rows.append(result)
        completed[slot_id] = result
        _atomic_write_json(rows_path, rows)
        audit = _build_audit(
            manifest, manifest_hash, schedule, rows
        )
        _atomic_write_json(
            output_root / "promotion_audit.json", audit
        )
        print(
            f"DONE [{slot_number:03d}/{len(schedule):03d}] "
            f"{spec['pair_id']} arm={arm} "
            f"status={result.get('algorithm_status')} "
            f"wall={float(result.get('cold_start_total_sec') or 0.0):.6f} "
            f"exact={_exact_passed(result)}",
            flush=True,
        )
        if not _safety_passed(result):
            print(
                f"STOP safety failure at {slot_id}",
                flush=True,
            )
            return 4

    _validate_input_hashes(manifest_path, manifest_hash, manifest)
    _validate_runtime_source_bundle(frozen_runtime_bundle)
    final_audit = _build_audit(
        manifest, manifest_hash, schedule, rows
    )
    _atomic_write_json(
        output_root / "promotion_audit.json", final_audit
    )
    print(
        json.dumps(final_audit, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return 0 if final_audit.get("promotion_passed") else 3


if __name__ == "__main__":
    raise SystemExit(main())
