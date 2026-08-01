#!/usr/bin/env python3
"""Run fresh-runtime, content-bound P0/DSSR V2 paired validation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
from time import monotonic
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SRC = ROOT / "src"
for path in (SCRIPTS, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_dssr_all_scale_full100_validation import run_observed  # noqa: E402
from run_live_sri_paired_promotion import (  # noqa: E402
    atomic_write_json,
    config_profile,
    read_run_result,
    sha256_file,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


SCHEMA_VERSION = "lunar_ice_bpc.dssr_v2_paired_validation.v1"
POLICY_VERSION = "multi_sortie_counterexample_pressure_refinement_v2"
SCALES = (5, 10, 20, 30, 50, 100)
CONTROL_BACKEND = {
    scale: (
        "native_rcspp_inprocess"
        if scale <= 30
        else "native_rcspp_host"
    )
    for scale in SCALES
}
CANDIDATE_BACKEND = {
    scale: (
        "native_rcspp_dssr_v2_inprocess"
        if scale <= 30
        else "native_rcspp_dssr_v2_host"
    )
    for scale in SCALES
}
DEFAULT_CONFIG = ROOT / "configs" / "dssr_v2_candidate_base.yaml"
DEFAULT_SPLIT = (
    ROOT
    / "data"
    / "manifests"
    / "dssr_v2_validation_split_manifest.json"
)
DEFAULT_GRID = (
    ROOT
    / "runs"
    / "dssr_v2_development_20260729"
    / "sentinel_grid"
    / "summary.json"
)
ACCEPTANCE = (
    ROOT / "scripts" / "run_lunar_ice_native_spprc_acceptance.py"
)
LOCKED_RECEIPT = (
    ROOT / "runs" / "dssr_v2_locked_test_single_use_receipt.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--partition",
        choices=("development", "locked_test"),
        default="development",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--grid-summary", type=Path, default=DEFAULT_GRID)
    parser.add_argument(
        "--native-build",
        type=Path,
        default=ROOT / "build" / "native-spprc-dssr-v2",
    )
    parser.add_argument("--candidate-freeze", type=Path)
    parser.add_argument("--scales", type=int, nargs="+", default=list(SCALES))
    parser.add_argument("--limit-per-scale", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-pregrid-smoke",
        action="store_true",
        help="development-only partial smoke; can never pass a gate",
    )
    parser.add_argument("--heartbeat-interval-sec", type=float, default=30.0)
    parser.add_argument("--outer-timeout-grace-sec", type=float, default=300.0)
    args = parser.parse_args()

    scales = tuple(int(scale) for scale in args.scales)
    if (
        len(scales) != len(set(scales))
        or any(scale not in SCALES for scale in scales)
    ):
        raise SystemExit(f"scales must be unique members of {SCALES}")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.config.resolve()
    split_path = args.split_manifest.resolve()
    grid_path = args.grid_summary.resolve()
    native_build = args.native_build.resolve()
    manifest = _read_json(split_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    issues = _preflight_issues(
        manifest=manifest,
        config=config,
        grid_path=grid_path,
        partition=args.partition,
        candidate_freeze=args.candidate_freeze,
        allow_pregrid_smoke=bool(args.allow_pregrid_smoke),
        limit_per_scale=max(0, int(args.limit_per_scale)),
        dry_run=bool(args.dry_run),
    )
    if issues:
        atomic_write_json(
            output / "preflight.json",
            {
                "schema_version": f"{SCHEMA_VERSION}.preflight",
                "status": "FAILED",
                "issues": issues,
            },
        )
        raise SystemExit("preflight failed: " + ",".join(issues))

    native_modules = sorted(native_build.glob("lunar_spprc_native*.so"))
    if len(native_modules) != 1:
        raise SystemExit("isolated native build must contain exactly one module")
    if str(native_build) not in sys.path:
        sys.path.insert(0, str(native_build))
    expected_engine_hashes = {
        backend: spprc_engine_build_hash(backend)
        for backend in (
            *CONTROL_BACKEND.values(),
            *CANDIDATE_BACKEND.values(),
        )
    }
    selected = _selected_rows(
        manifest,
        partition=args.partition,
        scales=scales,
        limit_per_scale=max(0, int(args.limit_per_scale)),
    )
    _validate_instance_bindings(selected)
    freeze_hash = (
        sha256_file(args.candidate_freeze.resolve())
        if args.candidate_freeze
        else ""
    )
    if args.partition == "locked_test" and not args.dry_run:
        _claim_locked_test_once(
            output=output,
            candidate_freeze_hash=freeze_hash,
            resume=bool(args.resume),
        )

    environment = _solver_environment(native_build)
    schedule_hash = _stable_hash(
        [
            {
                "scale": row["scale"],
                "instance_content_hash": row["instance_content_hash"],
                "path": row["path"],
            }
            for row in selected
        ]
    )
    execution_hash = _stable_hash(
        {
            "config_sha256": sha256_file(config_path),
            "native_module_sha256": sha256_file(native_modules[0]),
            "split_manifest_sha256": sha256_file(split_path),
            "grid_summary_sha256": (
                sha256_file(grid_path) if grid_path.is_file() else ""
            ),
            "candidate_freeze_sha256": freeze_hash,
            "schedule_hash": schedule_hash,
            "partition": args.partition,
        }
    )
    preflight = {
        "schema_version": f"{SCHEMA_VERSION}.preflight",
        "status": "PASS",
        "partition": args.partition,
        "scales": list(scales),
        "selected_instance_count": len(selected),
        "schedule_hash": schedule_hash,
        "execution_hash": execution_hash,
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "native_module_path": str(native_modules[0]),
        "native_module_sha256": sha256_file(native_modules[0]),
        "split_manifest_path": str(split_path),
        "split_manifest_sha256": sha256_file(split_path),
        "grid_summary_path": str(grid_path),
        "grid_summary_sha256": (
            sha256_file(grid_path) if grid_path.is_file() else ""
        ),
        "fresh_python_native_runtime_per_arm": True,
        "same_config_both_arms": True,
        "control_backend_by_scale": {
            str(scale): CONTROL_BACKEND[scale] for scale in scales
        },
        "candidate_backend_by_scale": {
            str(scale): CANDIDATE_BACKEND[scale] for scale in scales
        },
        "tree_max_rounds": {
            str(scale): int(config["profiles"][str(scale)]["tree_max_rounds"])
            for scale in scales
        },
        "guidance_disabled": True,
        "production_default_unchanged": "no_cut",
    }
    atomic_write_json(output / "preflight.json", preflight)
    atomic_write_json(output / "schedule.json", selected)

    rows_path = output / "rows.json"
    rows = _read_json(rows_path) if rows_path.is_file() else []
    if rows and not args.resume:
        raise SystemExit("rows.json exists; use --resume or a new output")
    recovered = {
        str(row["pair_id"]): row
        for row in rows
        if row.get("execution_hash") == execution_hash
    }
    if len(recovered) != len(rows):
        raise SystemExit("recovered row binding mismatch")

    started = monotonic()
    for spec in selected:
        pair_id = _pair_id(spec)
        if pair_id in recovered:
            continue
        pair_dir = (
            output
            / "slots"
            / f"scale_{int(spec['scale']):03d}"
            / str(spec["instance_content_hash"])
        )
        if pair_dir.exists():
            raise SystemExit(f"unbound existing pair directory: {pair_dir}")
        arms: dict[str, dict] = {}
        for arm, backend in (
            ("control", CONTROL_BACKEND[int(spec["scale"])]),
            ("candidate", CANDIDATE_BACKEND[int(spec["scale"])]),
        ):
            run_dir = pair_dir / arm
            run_dir.mkdir(parents=True, exist_ok=False)
            command = [
                sys.executable,
                str(ACCEPTANCE),
                "--config",
                str(config_path),
                "--scales",
                str(spec["scale"]),
                "--backend",
                backend,
                "--instance",
                str((ROOT / spec["path"]).resolve()),
                "--output-dir",
                str(run_dir),
                "--no-resume",
            ]
            print(f"[START] {pair_id} arm={arm} backend={backend}", flush=True)
            if args.dry_run:
                observed = {
                    "returncode": 0,
                    "launcher_wall_time_sec": 0.0,
                    "peak_process_tree_rss_gb": 0.0,
                    "launcher_termination_reason": "",
                }
                result = {
                    "status": "DRY_RUN",
                    "exact": False,
                    "redlines_zero": True,
                }
            else:
                profile = config_profile(
                    config_path, int(spec["scale"])
                )
                observed = run_observed(
                    command,
                    cwd=ROOT,
                    environment=environment,
                    stdout_path=run_dir / "launcher_stdout.txt",
                    stderr_path=run_dir / "launcher_stderr.txt",
                    heartbeat_path=output / "resource_heartbeat.csv",
                    slot_id=f"{pair_id}:{arm}",
                    timeout_sec=(
                        float(profile["row_time_limit_sec"])
                        + max(0.0, float(args.outer_timeout_grace_sec))
                    ),
                    heartbeat_interval_sec=max(
                        1.0, float(args.heartbeat_interval_sec)
                    ),
                )
                result = read_run_result(
                    run_dir,
                    scale=int(spec["scale"]),
                    returncode=int(observed["returncode"]),
                )
                result.update(_root_closure_fields(run_dir))
            arms[arm] = {
                "backend_id": backend,
                "expected_engine_hash": expected_engine_hashes[backend],
                "command": command,
                **result,
                **observed,
            }
            print(
                f"[DONE] {pair_id} arm={arm} "
                f"status={result.get('status')} "
                f"sec={result.get('cold_start_total_sec')}",
                flush=True,
            )
        row = _paired_row(
            spec,
            arms=arms,
            execution_hash=execution_hash,
        )
        rows.append(row)
        recovered[pair_id] = row
        atomic_write_json(rows_path, rows)

    summary = _summarize(
        rows,
        expected=selected,
        partition=args.partition,
        full_design=bool(
            not args.limit_per_scale
            and set(scales) == set(SCALES)
        ),
        elapsed_sec=monotonic() - started,
        pregrid_smoke=bool(args.allow_pregrid_smoke),
    )
    atomic_write_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] in {"PASS", "DRY_RUN"} else 1


def _preflight_issues(
    *,
    manifest: Mapping,
    config: Mapping,
    grid_path: Path,
    partition: str,
    candidate_freeze: Path | None,
    allow_pregrid_smoke: bool,
    limit_per_scale: int,
    dry_run: bool,
) -> list[str]:
    issues: list[str] = []
    if manifest.get("status") != "LOCKED":
        issues.append("split_manifest_not_locked")
    audit = dict(manifest.get("audit") or {})
    if audit.get("development_locked_overlap_count") != 0:
        issues.append("split_overlap")
    if audit.get("formal_or_prior_protected_overlap_count") != 0:
        issues.append("protected_overlap")
    if config.get("dssr_policy_version") != POLICY_VERSION:
        issues.append("wrong_dssr_policy")
    if any(
        int(profile.get("tree_max_rounds") or 0) != 16
        for profile in dict(config.get("profiles") or {}).values()
    ):
        issues.append("tree_round_cap_changed")
    grid = _read_json(grid_path) if grid_path.is_file() else {}
    grid_allowed = bool(grid.get("freeze_allowed"))
    if not grid_allowed and not (
        partition == "development"
        and allow_pregrid_smoke
        and (limit_per_scale or dry_run)
    ):
        issues.append("sentinel_grid_not_passed")
    if grid_allowed:
        selected = dict(grid.get("selected_configuration") or {})
        if int(config.get("dssr_pressure_max_bucket_size") or 0) != int(
            selected.get("bucket_limit") or -1
        ):
            issues.append("config_bucket_not_grid_selected")
        if int(
            config.get("dssr_pressure_max_candidate_checks") or 0
        ) != int(selected.get("candidate_check_limit") or -1):
            issues.append("config_checks_not_grid_selected")
    if partition == "locked_test":
        if candidate_freeze is None or not candidate_freeze.is_file():
            issues.append("locked_test_requires_candidate_freeze")
        elif not _valid_candidate_freeze(candidate_freeze):
            issues.append("candidate_freeze_invalid")
    return sorted(set(issues))


def _valid_candidate_freeze(path: Path) -> bool:
    payload = _read_json(path)
    return bool(
        payload.get("candidate_id") == "DSSR_V2_DETERMINISTIC_CANDIDATE"
        and payload.get("promotion_status") == "LOCKED_TEST_AUTHORIZED"
        and payload.get("production_default_unchanged") == "no_cut"
    )


def _selected_rows(
    manifest: Mapping,
    *,
    partition: str,
    scales: Iterable[int],
    limit_per_scale: int,
) -> list[dict]:
    selected: list[dict] = []
    allowed = set(map(int, scales))
    for scale in sorted(allowed):
        rows = [
            dict(row)
            for row in manifest.get(partition, ())
            if int(row["scale"]) == scale
        ]
        if limit_per_scale:
            rows = rows[:limit_per_scale]
        selected.extend(rows)
    return selected


def _validate_instance_bindings(rows: Iterable[Mapping]) -> None:
    for row in rows:
        path = (ROOT / str(row["path"])).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        data = load_lunar_ice_data(_read_json(path))
        if (
            data.instance_content_hash != row["instance_content_hash"]
            or data.instance_id != row["instance_id"]
            or int(data.scale) != int(row["scale"])
        ):
            raise ValueError(f"instance binding mismatch: {path}")


def _solver_environment(native_build: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not (
            key.startswith("LUNAR_ICE_SPPRC_DSSR_")
            or key.startswith("LUNAR_ICE_GAT_")
        )
    }
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(SRC), str(native_build))
    )
    environment["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "0"
    return environment


def _claim_locked_test_once(
    *,
    output: Path,
    candidate_freeze_hash: str,
    resume: bool,
) -> None:
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.locked_test_receipt",
        "candidate_freeze_sha256": candidate_freeze_hash,
        "output_dir": str(output),
    }
    if LOCKED_RECEIPT.exists():
        existing = _read_json(LOCKED_RECEIPT)
        if not (
            resume
            and existing.get("candidate_freeze_sha256")
            == candidate_freeze_hash
            and existing.get("output_dir") == str(output)
        ):
            raise SystemExit("locked test has already been claimed")
        return
    LOCKED_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    with LOCKED_RECEIPT.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _root_closure_fields(run_dir: Path) -> dict:
    trees = sorted(run_dir.glob("**/tree_closure_001.json"))
    if not trees:
        return {"root_exact_closed": False}
    tree = _read_json(trees[-1])
    nodes = list(tree.get("nodes") or [])
    root = next(
        (
            node
            for node in nodes
            if str(node.get("node_id") or "") == "root"
            or node.get("parent_node_id") in {None, ""}
        ),
        {},
    )
    return {
        "root_exact_closed": bool(
            tree.get("root_lp_bound_official")
            and root.get("node_lp_bound_official")
            and root.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
            and root.get("uses_true_dual_bpc_certificate")
        ),
        "root_pricing_proof_kind": root.get("pricing_proof_kind"),
        "root_node_status": tree.get("root_node_status"),
    }


def _paired_row(
    spec: Mapping,
    *,
    arms: Mapping[str, Mapping],
    execution_hash: str,
) -> dict:
    control = arms["control"]
    candidate = arms["candidate"]
    control_wall = control.get("cold_start_total_sec")
    candidate_wall = candidate.get("cold_start_total_sec")
    ratio = (
        float(candidate_wall) / float(control_wall)
        if control.get("exact")
        and candidate.get("exact")
        and control_wall
        and candidate_wall
        else None
    )
    objective_match = (
        math.isclose(
            float(control["objective"]),
            float(candidate["objective"]),
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
        if control.get("exact")
        and candidate.get("exact")
        and control.get("objective") is not None
        and candidate.get("objective") is not None
        else None
    )
    issues = [
        f"{arm}:{issue}"
        for arm, payload in arms.items()
        for issue in _arm_safety_issues(payload)
    ]
    if objective_match is False:
        issues.append("objective_mismatch")
    return {
        **dict(spec),
        "pair_id": _pair_id(spec),
        "execution_hash": execution_hash,
        "control": dict(control),
        "candidate": dict(candidate),
        "control_exact": bool(control.get("exact")),
        "candidate_exact": bool(candidate.get("exact")),
        "extra_incomplete": bool(
            control.get("exact") and not candidate.get("exact")
        ),
        "objective_match": objective_match,
        "wall_ratio": ratio,
        "safety_issues": sorted(set(issues)),
        "safety_pass": not issues,
    }


def _arm_safety_issues(payload: Mapping) -> list[str]:
    if payload.get("status") == "DRY_RUN":
        return []
    issues: list[str] = []
    if payload.get("launcher_termination_reason"):
        issues.append("outer_launcher_terminated")
    for field in ("redlines_zero", "engine_hash_valid", "no_cheat_pass"):
        if payload.get(field) is not True:
            issues.append(f"{field}_false")
    if str(payload.get("engine_build_hash") or "") != str(
        payload.get("expected_engine_hash") or ""
    ):
        issues.append("isolated_engine_hash_mismatch")
    for field in ("certificate_leak", "pricing_rc_fail", "manual_rc_fail"):
        if int(payload.get(field) or 0):
            issues.append(f"{field}_nonzero")
    return issues


def _summarize(
    rows: list[dict],
    *,
    expected: list[dict],
    partition: str,
    full_design: bool,
    elapsed_sec: float,
    pregrid_smoke: bool,
) -> dict:
    dry_run = bool(rows) and all(
        row["control"].get("status") == "DRY_RUN"
        and row["candidate"].get("status") == "DRY_RUN"
        for row in rows
    )
    expected_ids = {_pair_id(row) for row in expected}
    observed_ids = {str(row["pair_id"]) for row in rows}
    schedule_complete = expected_ids == observed_ids
    scale_summary: dict[str, dict] = {}
    all_scale_gates = True
    for scale in SCALES:
        scale_rows = [
            row for row in rows if int(row["scale"]) == scale
        ]
        if not scale_rows:
            continue
        ratios = [
            float(row["wall_ratio"])
            for row in scale_rows
            if row.get("wall_ratio") is not None
        ]
        candidate_walls = [
            float(row["candidate"]["cold_start_total_sec"])
            for row in scale_rows
            if row["candidate"].get("cold_start_total_sec") is not None
        ]
        candidate_rss = [
            float(row["candidate"]["peak_process_tree_rss_gb"])
            for row in scale_rows
            if row["candidate"].get("peak_process_tree_rss_gb") is not None
        ]
        safety = all(row.get("safety_pass") for row in scale_rows)
        extra_incomplete = sum(
            bool(row.get("extra_incomplete")) for row in scale_rows
        )
        p50 = statistics.median(ratios) if ratios else None
        mean = statistics.mean(ratios) if ratios else None
        geomean = _geomean(ratios)
        if scale in {5, 10}:
            performance = bool(
                ratios
                and p50 is not None
                and p50 <= 1.02
                and mean is not None
                and mean <= 1.03
            )
        elif scale in {20, 30}:
            performance = bool(
                not extra_incomplete
                and ratios
                and geomean is not None
                and geomean <= 1.0
                and mean is not None
                and mean <= 1.0
            )
        else:
            performance = bool(
                partition != "locked_test"
                or (
                    all(
                        row["candidate"].get("root_exact_closed")
                        for row in scale_rows
                    )
                    and candidate_walls
                    and max(candidate_walls) <= 3600.0
                    and candidate_rss
                    and max(candidate_rss) < 8.0
                )
            )
        gate = bool(
            safety
            and not extra_incomplete
            and all(row.get("objective_match") is not False for row in scale_rows)
            and performance
        )
        all_scale_gates = all_scale_gates and gate
        scale_summary[str(scale)] = {
            "row_count": len(scale_rows),
            "safety_pass": safety,
            "extra_incomplete_count": extra_incomplete,
            "paired_exact_count": len(ratios),
            "p50_wall_ratio": p50,
            "mean_wall_ratio": mean,
            "geometric_mean_wall_ratio": geomean,
            "candidate_max_wall_sec": max(candidate_walls, default=None),
            "candidate_max_peak_rss_gb": max(candidate_rss, default=None),
            "performance_gate": performance,
            "scale_gate": gate,
        }
    pass_gate = bool(
        not dry_run
        and not pregrid_smoke
        and full_design
        and schedule_complete
        and set(map(int, scale_summary)) == set(SCALES)
        and all_scale_gates
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "DRY_RUN"
            if dry_run
            else "PASS"
            if pass_gate
            else "FAIL"
        ),
        "partition": partition,
        "full_design": full_design,
        "schedule_complete": schedule_complete,
        "expected_pair_count": len(expected),
        "completed_pair_count": len(rows),
        "scale_summary": scale_summary,
        "safety_pass": all(
            row.get("safety_pass") for row in rows
        ),
        "zero_extra_incomplete": not any(
            row.get("extra_incomplete") for row in rows
        ),
        "freeze_allowed": bool(
            partition == "development" and pass_gate
        ),
        "promotion_allowed": bool(
            partition == "locked_test" and pass_gate
        ),
        "gat_oracle_allowed": bool(
            partition == "locked_test" and pass_gate
        ),
        "elapsed_sec": elapsed_sec,
    }


def _pair_id(row: Mapping) -> str:
    return (
        f"s{int(row['scale']):03d}_"
        f"{str(row['instance_content_hash'])}"
    )


def _geomean(values: list[float]) -> float | None:
    if not values or any(value <= 0.0 for value in values):
        return None
    return math.exp(statistics.mean(math.log(value) for value in values))


def _stable_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
