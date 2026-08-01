#!/usr/bin/env python3
"""Bind the measured V5 Exact candidate for GAT development.

This is deliberately not a formal Exact promotion.  It records the user's
decision to treat V5/E128 as the fixed development baseline, verifies the
available all-small and scale-50 evidence, and emits an immutable selected
config plus a fixed-K binding consumable by the opportunity/oracle runners.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)


SCHEMA_VERSION = "lunar_ice_bpc.p0v4_v5_gat_exact_binding.v1"
BACKEND_ID = "native_rcspp_bidirectional_root_partial_hybrid_v3"
EXPECTED_ENGINE_HASH = "a3be48f74fb8ec8a"
ADMISSION_BATCH_SIZE_BY_SCALE = {
    "5": 8,
    "10": 16,
    "20": 32,
    "30": 64,
    "50": 128,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=(
            "configs/experiments/"
            "p0v4_bidirectional_sri_group_screen_all_scale_candidate_v5.yaml"
        ),
    )
    parser.add_argument(
        "--small80-run",
        default=(
            "runs/"
            "p0v4_bidirectional_sri_group_screen_candidate_v5_"
            "full_small80_20260731"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="runs/p0v4_v5_exact_gat_binding_20260731",
    )
    parser.add_argument(
        "--scale50-evidence-run",
        action="append",
        default=[],
    )
    args = parser.parse_args()

    config_path = _resolve(args.config)
    small80 = _resolve(args.small80_run)
    output = _resolve(args.output_dir)
    evidence_runs = tuple(
        _resolve(value)
        for value in (
            args.scale50_evidence_run
            or (
                "runs/p0v4_bidirectional_sri_group_screen_candidate_"
                "v5_scale50_005_probe_20260731",
                "runs/p0v4_bidirectional_sri_group_screen_candidate_"
                "v5_scale50_006_probe_20260731",
                "runs/p0v4_bidirectional_sri_group_screen_candidate_"
                "v5_scale50_010_probe_20260731",
            )
        )
    )
    config = _read_yaml(config_path)
    _validate_config(config)
    small_evidence = _audit_small80(small80)
    scale50_evidence = _audit_scale50(evidence_runs)
    engine_hash = spprc_engine_build_hash(BACKEND_ID)
    if engine_hash != EXPECTED_ENGINE_HASH:
        raise SystemExit(
            "V5 Native engine hash mismatch: "
            f"{engine_hash} != {EXPECTED_ENGINE_HASH}"
        )

    output.mkdir(parents=True, exist_ok=True)
    selected_config = output / "selected_exact_v5.yaml"
    shutil.copy2(config_path, selected_config)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "FIXED_K_SELECTED",
        "selection_authority": (
            "user_assumed_v5_plus_p0v4_for_gat_development_20260731"
        ),
        "selection_basis": (
            "measured_v5_small80_plus_targeted_scale50_evidence"
        ),
        "formal_e64_e128_e256_development_oracle_complete": False,
        "formal_exact_promotion_authorized": False,
        "gat_opportunity_and_oracle_development_authorized": True,
        "selected_arm": "V5_E128",
        "selected_batch_size": 128,
        "selected_raw_negative_pool_size": 512,
        "admission_batch_size_by_scale": ADMISSION_BATCH_SIZE_BY_SCALE,
        "raw_negative_pool_size_by_scale": {
            key: 4 * value
            for key, value in ADMISSION_BATCH_SIZE_BY_SCALE.items()
        },
        "selected_config": str(selected_config.resolve()),
        "selected_config_sha256": _sha256(selected_config),
        "source_config": str(config_path.resolve()),
        "source_config_sha256": _sha256(config_path),
        "backend_id": BACKEND_ID,
        "engine_build_hash": engine_hash,
        "small80_evidence": small_evidence,
        "scale50_targeted_evidence": scale50_evidence,
        "correctness_redline_count": 0,
        "candidate_manufacturing_used": False,
        "production_default_changed": False,
        "note": (
            "This binding fixes V5/E128 only for GAT opportunity, oracle, "
            "training, and calibration development. Formal Exact promotion "
            "remains gated by the registered full acceptance protocol."
        ),
    }
    target = output / "fixed_k_selection.json"
    _write_json(target, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _validate_config(config: dict) -> None:
    if str(config.get("live_sri_policy")) != "P0_GROUP_SCREEN_V1":
        raise SystemExit("selected config is not V5 group screening")
    if not bool(config.get("exact_negative_escape_enabled")):
        raise SystemExit("selected config disabled diverse negative escape")
    if not bool(config.get("batch_master_admission_enabled")):
        raise SystemExit("selected config disabled batch admission")
    if int(config.get("exact_raw_negative_pool_multiplier") or 0) != 4:
        raise SystemExit("selected config raw-negative multiplier is not four")
    profiles = dict(config.get("profiles") or {})
    for scale, expected in ADMISSION_BATCH_SIZE_BY_SCALE.items():
        row = dict(profiles.get(scale) or profiles.get(int(scale)) or {})
        if int(row.get("harvest_target") or 0) != expected:
            raise SystemExit(f"scale{scale} admission batch mismatch")
        if str(row.get("backend_id") or "") != BACKEND_ID:
            raise SystemExit(f"scale{scale} backend mismatch")


def _audit_small80(run_root: Path) -> dict:
    rows = {}
    for scale in (5, 10, 20, 30):
        summary_path = (
            run_root / f"scale_{scale:03d}" / "b4_2_cold_exact_summary.json"
        )
        summary = _read_json(summary_path)
        by_scale = dict(summary.get("by_scale") or {}).get(str(scale), {})
        if int(summary.get("row_count") or 0) != 20:
            raise SystemExit(f"scale{scale} V5 evidence is not full20")
        if int(by_scale.get("exact_count") or 0) != 20:
            raise SystemExit(f"scale{scale} V5 evidence is not 20/20 exact")
        if not bool((summary.get("acceptance") or {}).get("redlines_zero")):
            raise SystemExit(f"scale{scale} V5 evidence has a redline")
        rows[str(scale)] = {
            "summary": str(summary_path.resolve()),
            "summary_sha256": _sha256(summary_path),
            "row_count": 20,
            "exact_count": 20,
            "mean_cold_start_total_sec": float(
                by_scale["mean_cold_start_total_sec"]
            ),
            "max_cold_start_total_sec": float(
                by_scale["max_cold_start_total_sec"]
            ),
            "redlines_zero": True,
        }
    return rows


def _audit_scale50(run_roots: tuple[Path, ...]) -> dict:
    rows = []
    for run_root in run_roots:
        summary_path = run_root / "native_spprc_acceptance_summary.json"
        summary = _read_json(summary_path)
        acceptance_rows = tuple(summary.get("rows") or ())
        if len(acceptance_rows) != 1:
            raise SystemExit(f"invalid targeted scale50 evidence: {run_root}")
        row = dict(acceptance_rows[0])
        if int(row.get("exact_count") or 0) != 1:
            raise SystemExit(f"targeted scale50 evidence is not exact: {run_root}")
        if not bool(row.get("redlines_zero")):
            raise SystemExit(f"targeted scale50 evidence has redline: {run_root}")
        state_paths = tuple(run_root.rglob("b4_2_cold_exact_rows.csv"))
        if len(state_paths) != 1:
            raise SystemExit(f"targeted scale50 row ledger missing: {run_root}")
        with state_paths[0].open(newline="", encoding="utf-8") as handle:
            ledger = tuple(csv.DictReader(handle))
        if len(ledger) != 1:
            raise SystemExit(f"targeted scale50 ledger is not singleton: {run_root}")
        rows.append(
            {
                "instance_key": str(ledger[0]["instance_key"]),
                "algorithm_status": str(ledger[0]["algorithm_status"]),
                "cold_start_total_sec": float(
                    ledger[0]["cold_start_total_sec"]
                ),
                "summary": str(summary_path.resolve()),
                "summary_sha256": _sha256(summary_path),
            }
        )
    return {
        "row_count": len(rows),
        "exact_count": len(rows),
        "redlines_zero": True,
        "rows": rows,
    }


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _read_yaml(path: Path) -> dict:
    return dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _read_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
