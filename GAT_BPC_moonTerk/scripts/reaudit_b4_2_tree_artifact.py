#!/usr/bin/env python3
"""Re-audit an existing B4.2 tree artifact without rerunning the solver.

The original state and summary files remain immutable.  This command writes an
independent, hash-bound report using the current worker/final-judge field-scope
rules from ``run_lunar_ice_b4_2_cold_exact.py``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
B4_2_RUNNER = PROJECT_ROOT / "scripts" / "run_lunar_ice_b4_2_cold_exact.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "b4_2_cold_exact_reaudit",
        B4_2_RUNNER,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load B4.2 runner: {B4_2_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _single_path(paths: list[Path], label: str) -> Path:
    if len(paths) != 1:
        raise ValueError(
            f"expected exactly one {label}, found {len(paths)}"
        )
    return paths[0]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def reaudit(run_dir: Path) -> dict:
    run_dir = run_dir.resolve()
    state_path = run_dir / "b4_2_cold_exact_state.json"
    summary_path = run_dir / "b4_2_cold_exact_summary.json"
    tree_path = _single_path(
        sorted(run_dir.rglob("tree_closure_001.json")),
        "tree closure result",
    )
    b4_1_path = _single_path(
        sorted(run_dir.rglob("b4_1_summary.json")),
        "B4.1 summary",
    )
    state = _load_json(state_path)
    original_summary = _load_json(summary_path)
    tree = _load_json(tree_path)
    b4_1 = _load_json(b4_1_path)
    rows = state.get("rows")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("re-audit currently requires exactly one B4.2 row")
    original_row = rows[0]

    runner = _load_runner()
    worker_payload = runner._last_worker_payload_from_tree_raw(tree)
    safety = runner._worker_safety_redline_fields(
        worker_payload,
        tail_dual_stabilization_enabled=bool(
            tree.get(
                "tail_dual_stabilization_enabled",
                original_row.get(
                    "tree_closure_tail_dual_stabilization_enabled"
                ),
            )
        ),
    )
    b4_1_redlines = (
        b4_1.get("redlines")
        if isinstance(b4_1.get("redlines"), dict)
        else {}
    )
    redlines = {
        "b4_1_certificate_leak_count": _int(
            b4_1_redlines.get("certificate_leak_count")
        ),
        "b4_1_manual_rc_fail_count": _int(
            b4_1_redlines.get("manual_rc_fail_count")
        ),
        "b4_1_pricing_rc_fail_count": _int(
            b4_1_redlines.get("pricing_rc_fail_count")
        ),
        "b4_1_tail_dual_certificate_leak_count": _int(
            b4_1_redlines.get("tail_dual_certificate_leak_count")
        ),
        "root_pool_worker_certificate_leak_count": _int(
            original_row.get("root_pool_worker_certificate_leak_count")
        ),
        "root_pool_tail_dual_certificate_leak_count": _int(
            original_row.get(
                "root_pool_tail_dual_certificate_leak_count"
            )
        ),
        "root_pool_true_dual_rc_recompute_missing_count": _int(
            original_row.get(
                "root_pool_true_dual_rc_recompute_missing_count"
            )
        ),
        "tree_worker_certificate_leak_count": int(
            bool(safety["worker_certificate_leak"])
        ),
        "tree_tail_dual_certificate_leak_count": int(
            bool(safety["tail_dual_certificate_leak"])
        ),
        "tree_true_dual_rc_recompute_missing_count": int(
            bool(safety["true_dual_rc_recompute_missing"])
        ),
    }
    redline_total = sum(redlines.values())

    nodes = tree.get("nodes") if isinstance(tree.get("nodes"), list) else []
    root_node = nodes[0] if nodes and isinstance(nodes[0], dict) else {}
    final_judge = (
        root_node.get("final_judge")
        if isinstance(root_node.get("final_judge"), dict)
        else {}
    )
    algorithm_status = str(
        tree.get("algorithm_status")
        or root_node.get("algorithm_status")
        or ""
    )
    certificate_scope = str(
        tree.get("certificate_scope")
        or root_node.get("certificate_scope")
        or ""
    )
    pricing_state = str(
        root_node.get("pricing_state")
        or final_judge.get("pricing_state")
        or tree.get("pricing_state")
        or ""
    )
    underlying_exact = bool(
        algorithm_status == "BPC_OPTIMAL"
        and certificate_scope == "BPC_TREE_OPTIMAL"
        and pricing_state == "CERTIFIED_NO_NEGATIVE"
    )
    corrected_exact = bool(underlying_exact and redline_total == 0)
    backend_result = (
        final_judge.get("native_backend_result")
        if isinstance(final_judge.get("native_backend_result"), dict)
        else {}
    )
    backend_telemetry = (
        backend_result.get("telemetry")
        if isinstance(backend_result.get("telemetry"), dict)
        else {}
    )
    request_bindings = (
        backend_telemetry.get("request_bindings")
        if isinstance(backend_telemetry.get("request_bindings"), dict)
        else {}
    )
    canonical_binding = (
        request_bindings.get("canonical_solve_binding_v2")
        if isinstance(
            request_bindings.get("canonical_solve_binding_v2"),
            dict,
        )
        else request_bindings
    )
    state_config = (
        state.get("config")
        if isinstance(state.get("config"), dict)
        else {}
    )
    native_runtime_binding = (
        state_config.get("native_runtime_binding")
        if isinstance(
            state_config.get("native_runtime_binding"),
            dict,
        )
        else {}
    )

    source_paths = (
        state_path,
        summary_path,
        tree_path,
        b4_1_path,
        B4_2_RUNNER,
        Path(__file__).resolve(),
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_2_existing_tree_reaudit.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reaudit_policy": (
            "source_scoped_worker_and_exact_final_judge_fields_v1"
        ),
        "original_artifacts_mutated": False,
        "source_files": [
            {
                "path": str(path),
                "sha256": _sha256(path),
            }
            for path in source_paths
        ],
        "binding": {
            "b4_2_config_hash": str(
                original_row.get("config_hash") or ""
            ),
            "solve_config_hash": str(
                canonical_binding.get("config_hash") or ""
            ),
            "engine_hash": str(
                canonical_binding.get("engine_hash")
                or native_runtime_binding.get("engine_build_hash")
                or ""
            ),
            "instance_hash": str(
                canonical_binding.get("instance_hash") or ""
            ),
            "instance_path": str(
                original_row.get("instance_path") or ""
            ),
        },
        "original_b4_2_classification": {
            "algorithm_status": str(
                original_row.get("algorithm_status") or ""
            ),
            "certificate_scope": str(
                original_row.get("certificate_scope") or ""
            ),
            "pricing_state": str(
                original_row.get("pricing_state") or ""
            ),
            "exact_certificate": bool(
                original_row.get("exact_certificate")
            ),
            "worker_certificate_leak": _int(
                original_row.get("worker_certificate_leak")
            ),
            "tail_dual_certificate_leak": _int(
                original_row.get("tail_dual_certificate_leak")
            ),
            "summary_redlines": original_summary.get("redlines")
            if isinstance(original_summary.get("redlines"), dict)
            else {},
        },
        "underlying_tree_classification": {
            "algorithm_status": algorithm_status,
            "certificate_scope": certificate_scope,
            "pricing_state": pricing_state,
            "underlying_exact": underlying_exact,
        },
        "source_scoped_worker_safety": safety,
        "corrected_redlines": redlines,
        "corrected_redline_total": redline_total,
        "corrected_classification": {
            "algorithm_status": (
                "BPC_OPTIMAL"
                if corrected_exact
                else "BPC_INCOMPLETE_PRICING"
            ),
            "certificate_scope": (
                "BPC_TREE_OPTIMAL"
                if corrected_exact
                else "DIAGNOSTIC_PRICING_FRONTIER"
            ),
            "pricing_state": (
                "CERTIFIED_NO_NEGATIVE"
                if corrected_exact
                else "INCOMPLETE_LIMIT"
            ),
            "exact_certificate": corrected_exact,
            "posthoc_reaudit_pass": corrected_exact,
        },
        "timing_sec": {
            "root_cg": original_row.get("root_cg_sec"),
            "tree": original_row.get("tree_sec"),
            "cold_start_total": original_row.get(
                "cold_start_total_sec"
            ),
        },
        "diagnosis": (
            "The original B4.2 reporter treated the flattened exact "
            "final-judge can_certify_no_negative field as a relaxed-worker "
            "certificate claim. Explicit worker and tail-dual certificate "
            "fields are false; the underlying tree result is unchanged."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    output = args.output
    if output is None:
        output = (
            args.run_dir
            / "posthoc_b4_2_reporting_reaudit_v1.json"
        )
    payload = reaudit(args.run_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
