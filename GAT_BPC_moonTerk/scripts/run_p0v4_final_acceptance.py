#!/usr/bin/env python3
"""Execute and gate the frozen Exact and one-deviation P0V4 candidates."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import ceil, exp, log
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT / "configs/experiments/p0v4_final_acceptance_v1.yaml"
)
ACCEPTANCE_RUNNER = (
    ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--output-dir",
        default="runs/p0v4_final_acceptance_v1",
    )
    parser.add_argument(
        "--stage",
        choices=(
            "prepare",
            "representative",
            "exact-small30",
            "exact-scale50-heldout",
            "exact-scale50-001",
            "gat-small30",
            "gat-scale50-heldout",
            "gat-scale50-001",
            "scale100",
            "summarize",
            "freeze",
        ),
        default="prepare",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = _resolve(args.config)
    experiment = _read_yaml(config_path)
    _validate_experiment(experiment)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    exact_config, gat_config = _materialize_configs(
        experiment, output, require_gat=False
    )

    if args.stage == "prepare":
        payload = _prepare_manifest(
            experiment,
            config_path=config_path,
            exact_config=exact_config,
            gat_config=gat_config,
        )
        _write_json(output / "prepare_manifest.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.stage == "representative":
        return _run_acceptance_allow_fail_closed(
            exact_config,
            output / "representative" / "Exact",
            scales=(30, 50),
            instances=tuple(
                _resolve(value)
                for value in experiment["representative_instances"]
            ),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=4,
        )
    if args.stage == "exact-small30":
        return _run_acceptance_allow_fail_closed(
            exact_config,
            output / "official" / "Exact" / "small30",
            scales=(5, 10, 20, 30),
            instances=tuple(),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=80,
        )
    if args.stage == "exact-scale50-heldout":
        return _run_acceptance_allow_fail_closed(
            exact_config,
            output / "official" / "Exact" / "scale50_heldout",
            scales=(50,),
            instances=_indexed_instances(
                experiment["official_scale50_held_out"]
            ),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=19,
        )
    if args.stage == "exact-scale50-001":
        return _run_acceptance_allow_fail_closed(
            exact_config,
            output / "official" / "Exact" / "scale50_001",
            scales=(50,),
            instances=tuple(
                _resolve(value)
                for value in experiment[
                    "official_scale50_final_non_held_out"
                ]
            ),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=1,
        )

    gat_branch = _one_deviation_branch_state(experiment)
    if args.stage.startswith("gat-") and gat_branch["mode"] == "stopped":
        payload = {
            "schema_version": (
                "lunar_ice_bpc.p0v4_gat_acceptance_not_applicable.v1"
            ),
            "stage": args.stage,
            "status": "NOT_APPLICABLE_STOPPED_BY_PREDECLARED_GATES",
            "terminal_decision": gat_branch["terminal_decision"],
            "terminal_decision_sha256": gat_branch[
                "terminal_decision_sha256"
            ],
            "gat_performance_claim_authorized": False,
            "exact_acceptance_unblocked": True,
        }
        path = output / "gat_not_applicable" / f"{args.stage}.json"
        _write_json(path, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    exact_config, gat_config = _materialize_configs(
        experiment,
        output,
        require_gat=bool(gat_branch["mode"] == "actionful"),
    )
    if args.stage == "gat-small30":
        return _run_acceptance_allow_fail_closed(
            gat_config,
            output / "official" / "GAT" / "small30",
            scales=(5, 10, 20, 30),
            instances=tuple(),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=80,
        )
    if args.stage == "gat-scale50-heldout":
        return _run_acceptance_allow_fail_closed(
            gat_config,
            output / "official" / "GAT" / "scale50_heldout",
            scales=(50,),
            instances=_indexed_instances(
                experiment["official_scale50_held_out"]
            ),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=19,
        )
    if args.stage == "gat-scale50-001":
        return _run_acceptance_allow_fail_closed(
            gat_config,
            output / "official" / "GAT" / "scale50_001",
            scales=(50,),
            instances=tuple(
                _resolve(value)
                for value in experiment[
                    "official_scale50_final_non_held_out"
                ]
            ),
            resume=args.resume,
            dry_run=args.dry_run,
            expected=1,
        )
    if args.stage == "scale100":
        instances = _indexed_instances(
            experiment["scale100_diagnostic"]
        )
        p0v4_config = output / "configs" / "P0V4.yaml"
        p0v4_code = _run_acceptance(
            p0v4_config,
            output / "diagnostic" / "scale100" / "P0V4",
            scales=(100,),
            instances=instances,
            resume=args.resume,
            dry_run=args.dry_run,
        )
        if p0v4_code != 0 and not _has_complete_state(
            output / "diagnostic" / "scale100" / "P0V4",
            expected=len(instances),
        ):
            return p0v4_code
        final_large_config = (
            exact_config
            if gat_branch["mode"] == "stopped"
            else gat_config
        )
        return _run_acceptance_allow_fail_closed(
            final_large_config,
            output
            / "diagnostic"
            / "scale100"
            / "FinalCandidate",
            scales=(100,),
            instances=instances,
            resume=args.resume,
            dry_run=args.dry_run,
            expected=len(instances),
        )
    summary = _summarize(experiment, output)
    _write_json(output / "final_acceptance_summary.json", summary)
    if args.stage == "summarize":
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["all_required_evidence_available"] else 3
    return _freeze_candidate(
        experiment,
        output,
        summary=summary,
        exact_config=exact_config,
        gat_config=gat_config,
    )


def _materialize_configs(
    experiment: Mapping[str, object],
    output: Path,
    *,
    require_gat: bool,
) -> tuple[Path, Path]:
    _verify_frozen_p0v4(experiment)
    fixed_path = _resolve(experiment["fixed_k_selection"])
    if not fixed_path.is_file():
        raise SystemExit("fixed-K selection is missing")
    fixed = _read_json(fixed_path)
    if str(fixed.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("fixed-K selection has not passed the 7/10 gate")
    selected_config = Path(str(fixed["selected_config"])).resolve()
    if (
        not selected_config.is_file()
        or _sha256(selected_config)
        != str(fixed["selected_config_sha256"])
    ):
        raise SystemExit("selected Exact config hash mismatch")
    exact = _read_yaml(selected_config)
    exact["model_id"] = "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
    exact["final_candidate"] = True
    exact["fixed_k_selection"] = str(fixed_path.resolve())
    exact["fixed_k_selection_sha256"] = _sha256(fixed_path)
    exact["production_default"] = False
    exact["one_deviation_gat_deployment_manifest"] = ""
    exact["one_deviation_gat_evaluation_mode"] = False
    exact_path = output / "configs" / "Exact.yaml"
    exact_path.parent.mkdir(parents=True, exist_ok=True)
    exact_path.write_text(
        yaml.safe_dump(exact, sort_keys=False), encoding="utf-8"
    )

    gat = json.loads(json.dumps(exact))
    gat["model_id"] = (
        "P0V4_V5_BIDIRECTIONAL_ONE_DEVIATION_GAT_FINAL_CANDIDATE"
    )
    gat["one_deviation_gat_evaluation_mode"] = False
    manifest_path = _one_deviation_manifest_path(experiment)
    gat_branch = _one_deviation_branch_state(experiment)
    if manifest_path.is_file():
        manifest = _read_json(manifest_path)
        if (
            require_gat
            and not bool(manifest.get("deployment_authorized"))
        ):
            raise SystemExit(
                "one-deviation training manifest did not authorize deployment"
            )
        if bool(manifest.get("deployment_authorized")):
            gat["one_deviation_gat_deployment_manifest"] = str(
                manifest_path.resolve()
            )
            gat["one_deviation_gat_deployment_manifest_sha256"] = (
                _sha256(manifest_path)
            )
    elif require_gat:
        raise SystemExit(
            "GAT acceptance is blocked until an authorized deployment "
            "manifest exists"
        )
    if gat_branch["mode"] == "stopped":
        gat["one_deviation_gat_deployment_manifest"] = ""
        gat["one_deviation_gat_evaluation_mode"] = False
        gat["one_deviation_gat_stopped_by_gate"] = True
        gat["one_deviation_terminal_decision"] = gat_branch[
            "terminal_decision"
        ]
        gat["one_deviation_terminal_decision_sha256"] = gat_branch[
            "terminal_decision_sha256"
        ]
    gat_path = output / "configs" / "GAT.yaml"
    gat_path.write_text(
        yaml.safe_dump(gat, sort_keys=False), encoding="utf-8"
    )
    _materialize_paper_ablation_configs(
        experiment,
        output,
        fixed_path=fixed_path,
        exact_path=exact_path,
        gat_path=gat_path,
    )
    return exact_path, gat_path


def _materialize_paper_ablation_configs(
    experiment: Mapping[str, object],
    output: Path,
    *,
    fixed_path: Path,
    exact_path: Path,
    gat_path: Path,
) -> Path:
    """Materialize core configurations plus any triggered Exact fallback."""

    gat_branch = _one_deviation_branch_state(experiment)
    frozen_path = _resolve(experiment["frozen_p0v4_config"])
    if (
        not frozen_path.is_file()
        or _sha256(frozen_path)
        != str(experiment["frozen_p0v4_config_sha256"])
    ):
        raise SystemExit("frozen P0V4 config hash mismatch")
    config_dir = output / "configs"
    p0v4 = _read_yaml(frozen_path)
    p0v4.update(
        {
            "model_id": "P0V4_PAPER_CONTROL",
            "exact_negative_escape_enabled": False,
            "batch_master_admission_enabled": False,
            "one_deviation_gat_deployment_manifest": "",
            "production_default": False,
            "paper_ablation_id": "P0V4",
        }
    )
    p0v4_path = config_dir / "P0V4.yaml"
    p0v4_path.write_text(
        yaml.safe_dump(p0v4, sort_keys=False), encoding="utf-8"
    )

    batch_only = json.loads(json.dumps(p0v4))
    batch_only.update(
        {
            "model_id": "P0V4_BATCH_ADMISSION_ONLY",
            "batch_master_admission_enabled": True,
            "paper_ablation_id": "P0V4_BATCH_ADMISSION",
        }
    )
    batch_only_path = config_dir / "BatchAdmissionOnly.yaml"
    batch_only_path.write_text(
        yaml.safe_dump(batch_only, sort_keys=False), encoding="utf-8"
    )

    selected_exact = _read_yaml(exact_path)
    bidirectional_included = any(
        "bidirectional" in str(dict(profile).get("backend_id") or "")
        for profile in dict(selected_exact.get("profiles") or {}).values()
    )
    escape_batch = json.loads(json.dumps(p0v4))
    for key in (
        "exact_admission_batch_size_policy",
        "exact_raw_negative_pool_multiplier",
        "exact_negative_escape_policy_id",
    ):
        if key in selected_exact:
            escape_batch[key] = selected_exact[key]
    escape_batch.update(
        {
            "model_id": "P0V4_DIVERSE_ESCAPE_BATCH_UNIDIRECTIONAL",
            "exact_negative_escape_enabled": True,
            "batch_master_admission_enabled": True,
            "one_deviation_gat_deployment_manifest": "",
            "paper_ablation_id": "P0V4_ESCAPE_BATCH",
        }
    )
    selected_profiles = dict(selected_exact.get("profiles") or {})
    for scale, profile in dict(escape_batch.get("profiles") or {}).items():
        selected_profile = dict(selected_profiles.get(str(scale)) or {})
        for key in ("harvest_target", "raw_negative_pool_size"):
            if key in selected_profile:
                profile[key] = selected_profile[key]
    escape_batch_path = config_dir / "EscapeBatchUnidirectional.yaml"
    escape_batch_path.write_text(
        yaml.safe_dump(escape_batch, sort_keys=False), encoding="utf-8"
    )

    escape_only = json.loads(json.dumps(escape_batch))
    escape_only.update(
        {
            "model_id": "P0V4_DIVERSE_NEGATIVE_ESCAPE_ONLY",
            "batch_master_admission_enabled": False,
            "one_deviation_gat_deployment_manifest": "",
            "paper_ablation_id": "P0V4_DIVERSE_NEGATIVE_ESCAPE",
        }
    )
    escape_only_path = config_dir / "DiverseEscapeOnly.yaml"
    escape_only_path.write_text(
        yaml.safe_dump(escape_only, sort_keys=False), encoding="utf-8"
    )

    specifications = [
            ("P0V4", p0v4_path, tuple()),
            (
                "P0V4_BATCH_ADMISSION",
                batch_only_path,
                ("batch_admission",),
            ),
            (
                "P0V4_DIVERSE_NEGATIVE_ESCAPE",
                escape_only_path,
                ("diverse_negative_escape",),
            ),
            (
                "P0V4_ESCAPE_BATCH",
                escape_batch_path,
                ("diverse_negative_escape", "batch_admission"),
            ),
    ]
    exact_components = ["diverse_negative_escape", "batch_admission"]
    if bidirectional_included:
        exact_components.extend(
            ("bidirectional_pricing", "live_sri_group_screen")
        )
        specifications.append(
            (
                "P0V4_ESCAPE_BATCH_V5_BIDIRECTIONAL",
                exact_path,
                tuple(exact_components),
            )
        )
    specifications.append(
        (
            "P0V4_ESCAPE_BATCH_ONE_DEVIATION_GAT",
            gat_path,
            (*exact_components, "one_deviation_gat"),
        )
    )
    entries = []
    for order, (ablation_id, path, components) in enumerate(
        specifications, start=1
    ):
        entries.append(
            {
                "order": order,
                "ablation_id": ablation_id,
                "components": list(components),
                "config_path": str(path.resolve()),
                "config_sha256": _sha256(path),
                "requires_authorized_gat": bool(
                    "one_deviation_gat" in components
                ),
                "included_in_formal_acceptance": bool(
                    "one_deviation_gat" not in components
                    or gat_branch["mode"] == "actionful"
                ),
                "terminally_stopped_by_gate": bool(
                    "one_deviation_gat" in components
                    and gat_branch["mode"] == "stopped"
                ),
            }
        )
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_paper_ablation_manifest.v1"
        ),
        "status": (
            "CORE_PLUS_TRIGGERED_BIDIRECTIONAL_MATERIALIZED"
            if bidirectional_included
            else "FIVE_CORE_CONFIGS_MATERIALIZED"
        ),
        "fixed_k_selection": str(fixed_path.resolve()),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "configuration_count": len(entries),
        "configurations": entries,
        "bidirectional_included": bidirectional_included,
        "bidirectional_inclusion_policy": (
            "only_if_fallback_is_actually_triggered"
        ),
        "one_deviation_branch_mode": gat_branch["mode"],
        "one_deviation_terminal_decision": gat_branch[
            "terminal_decision"
        ],
        "one_deviation_terminal_decision_sha256": gat_branch[
            "terminal_decision_sha256"
        ],
        "production_default_changed": False,
    }
    path = config_dir / "paper_ablation_manifest.json"
    _write_json(path, manifest)
    return path


def _run_acceptance(
    config: Path,
    output: Path,
    *,
    scales: tuple[int, ...],
    instances: tuple[Path, ...] = tuple(),
    resume: bool,
    dry_run: bool,
) -> int:
    implementation_before = _implementation_binding()
    native_build_dir = _native_build_dir_for_config(config)
    command = [
        sys.executable,
        str(ACCEPTANCE_RUNNER),
        "--config",
        str(config),
        "--scales",
        *(str(scale) for scale in scales),
        "--output-dir",
        str(output),
        "--resume" if resume else "--no-resume",
    ]
    for instance in instances:
        if not instance.is_file():
            raise SystemExit(f"acceptance instance is missing: {instance}")
        command.extend(("--instance", str(instance)))
    if dry_run:
        command.append("--dry-run")
    output.mkdir(parents=True, exist_ok=True)
    launch = {
        "schema_version": "lunar_ice_bpc.p0v4_acceptance_launch.v1",
        "command": command,
        "config": str(config.resolve()),
        "config_sha256": _sha256(config),
        "scales": list(scales),
        "instances": [str(value.resolve()) for value in instances],
        "large_scale_concurrency": 1,
        "implementation_binding_hash_before": str(
            implementation_before["binding_hash"]
        ),
        "native_build_dir": str(native_build_dir.resolve()),
        "native_module_sha256": _sha256(
            _sole_native_module(native_build_dir)
        ),
    }
    environment = dict(os.environ)
    pythonpath = [str(ROOT / "src"), str(native_build_dir.resolve())]
    if environment.get("PYTHONPATH"):
        pythonpath.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        text=True,
    )
    implementation_after = _implementation_binding()
    launch["returncode"] = int(completed.returncode)
    launch["implementation_binding_hash_after"] = str(
        implementation_after["binding_hash"]
    )
    launch["implementation_stable_during_launch"] = bool(
        implementation_before["binding_hash"]
        == implementation_after["binding_hash"]
    )
    launch["evidence_usable"] = bool(
        launch["implementation_stable_during_launch"]
    )
    _write_json(output / "p0v4_launch_manifest.json", launch)
    if not bool(launch["evidence_usable"]):
        return 4
    return int(completed.returncode)


def _run_acceptance_allow_fail_closed(
    config: Path,
    output: Path,
    *,
    scales: tuple[int, ...],
    instances: tuple[Path, ...],
    resume: bool,
    dry_run: bool,
    expected: int,
) -> int:
    code = _run_acceptance(
        config,
        output,
        scales=scales,
        instances=instances,
        resume=resume,
        dry_run=dry_run,
    )
    if dry_run:
        return code
    if code == 4:
        return code
    return (
        0
        if _has_complete_state(output, expected=expected)
        else code
    )


def _summarize(
    experiment: Mapping[str, object], output: Path
) -> dict:
    expected_formal_keys = _expected_formal_keys(experiment)
    gat_branch = _one_deviation_branch_state(experiment)
    gat_required = bool(gat_branch["mode"] == "actionful")
    exact_rows, exact_state_audit = _state_evidence_audit(
        output / "official" / "Exact",
        expected_keys=expected_formal_keys,
        expected_model_id=(
            "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
        ),
    )
    gat_rows, gat_state_audit = _state_evidence_audit(
        output / "official" / "GAT",
        expected_keys=expected_formal_keys if gat_required else set(),
        expected_model_id=(
            "P0V4_V5_BIDIRECTIONAL_ONE_DEVIATION_GAT_"
            "FINAL_CANDIDATE"
        ),
    )
    implementation_audit = _formal_implementation_audit(output)
    prepared_implementation_hash = str(
        implementation_audit.get("prepared_binding_hash") or ""
    )
    exact_launch_audit = _candidate_launch_audit(
        experiment,
        output,
        label="Exact",
        config_path=output / "configs" / "Exact.yaml",
        implementation_binding_hash=prepared_implementation_hash,
    )
    gat_launch_audit = (
        _candidate_launch_audit(
            experiment,
            output,
            label="GAT",
            config_path=output / "configs" / "GAT.yaml",
            implementation_binding_hash=prepared_implementation_hash,
        )
        if gat_required
        else {
            "pass": True,
            "label": "GAT",
            "issues": [],
            "launches": [],
            "not_applicable": True,
            "reason": "stopped_by_predeclared_gates",
        }
    )
    exact_runtime_audit = _one_deviation_runtime_audit(
        exact_rows, allowed_scales=set()
    )
    gat_config = _read_yaml(output / "configs" / "GAT.yaml")
    gat_runtime_audit = _one_deviation_runtime_audit(
        gat_rows,
        allowed_scales={30, 50} if gat_required else set(),
        expected_manifest_sha256=str(
            gat_config.get(
                "one_deviation_gat_deployment_manifest_sha256"
            )
            or ""
        ),
        require_at_least_one_execution=gat_required,
    )
    baseline_rows, baseline_audit = _baseline_rows(experiment)
    exact = _candidate_metrics(exact_rows, baseline_rows)
    gat = _gat_metrics(gat_rows, exact_rows)
    gates = dict(experiment["gates"])
    exact_gate = _exact_gate(exact, gates)
    gat_gate = (
        _gat_gate(
            gat,
            gates,
            _one_deviation_manifest_path(experiment),
        )
        if gat_required
        else {
            "pass": True,
            "not_applicable": True,
            "performance_claim_authorized": False,
            "reason": "stopped_by_predeclared_gates",
            "issues": [],
        }
    )
    expected_scale100_keys = {
        (100, f"instance_{index:03d}") for index in range(1, 6)
    }
    scale100_p0v4_rows, scale100_p0v4_state_audit = (
        _state_evidence_audit(
            output / "diagnostic" / "scale100" / "P0V4",
            expected_keys=expected_scale100_keys,
            expected_model_id="P0V4_PAPER_CONTROL",
        )
    )
    scale100_final_rows, scale100_final_state_audit = (
        _state_evidence_audit(
            output
            / "diagnostic"
            / "scale100"
            / "FinalCandidate",
            expected_keys=expected_scale100_keys,
            expected_model_id=(
                "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
                if not gat_required
                else (
                    "P0V4_V5_BIDIRECTIONAL_ONE_DEVIATION_GAT_"
                    "FINAL_CANDIDATE"
                )
            ),
        )
    )
    scale100_launch_audit = _scale100_launch_audit(
        experiment,
        output,
        implementation_binding_hash=prepared_implementation_hash,
        final_config_name="GAT.yaml" if gat_required else "Exact.yaml",
    )
    scale100_p0v4_runtime_audit = _one_deviation_runtime_audit(
        scale100_p0v4_rows, allowed_scales=set()
    )
    scale100_final_runtime_audit = _one_deviation_runtime_audit(
        scale100_final_rows, allowed_scales=set()
    )
    scale100_diagnostic_complete = bool(
        scale100_p0v4_state_audit["pass"]
        and scale100_final_state_audit["pass"]
        and scale100_launch_audit["pass"]
        and scale100_p0v4_runtime_audit["pass"]
        and scale100_final_runtime_audit["pass"]
    )
    required_exact_count = 100
    required_gat_count = 100 if gat_required else 0
    evidence_available = bool(
        exact_state_audit["pass"]
        and (gat_state_audit["pass"] if gat_required else True)
        and implementation_audit["pass"]
        and exact_launch_audit["pass"]
        and (gat_launch_audit["pass"] if gat_required else True)
        and exact_runtime_audit["pass"]
        and (gat_runtime_audit["pass"] if gat_required else True)
        and baseline_audit["pass"]
        and scale100_diagnostic_complete
    )
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v4_final_acceptance_summary.v1"
        ),
        "all_required_evidence_available": evidence_available,
        "expected_row_count_per_candidate": required_exact_count,
        "expected_gat_row_count": required_gat_count,
        "one_deviation_branch": gat_branch,
        "exact": exact,
        "gat_increment": gat,
        "exact_gate": exact_gate,
        "gat_gate": gat_gate,
        "formal_evidence_audit": {
            "implementation": implementation_audit,
            "exact_states": exact_state_audit,
            "gat_states": gat_state_audit,
            "exact_launches": exact_launch_audit,
            "gat_launches": gat_launch_audit,
            "exact_one_deviation_runtime": exact_runtime_audit,
            "gat_one_deviation_runtime": gat_runtime_audit,
            "paired_p0v4_baseline": baseline_audit,
        },
        "scale100_diagnostic": {
            "p0v4_row_count": len(scale100_p0v4_rows),
            "final_candidate_row_count": len(
                scale100_final_rows
            ),
            "expected_row_count_per_candidate": 5,
            "complete": scale100_diagnostic_complete,
            "p0v4_state_audit": scale100_p0v4_state_audit,
            "final_candidate_state_audit": (
                scale100_final_state_audit
            ),
            "launch_audit": scale100_launch_audit,
            "p0v4_one_deviation_runtime": (
                scale100_p0v4_runtime_audit
            ),
            "final_candidate_one_deviation_runtime": (
                scale100_final_runtime_audit
            ),
            "gating_role": "required_completeness_diagnostic_only",
        },
        "final_candidate_gate_pass": bool(
            evidence_available
            and exact_gate["pass"]
            and (gat_gate["pass"] if gat_required else True)
        ),
        "gat_performance_claim_authorized": bool(
            gat_required and gat_gate["pass"]
        ),
        "scale100_is_diagnostic_only": True,
        "p0v4_overwritten": False,
        "production_default_changed": False,
    }


def _formal_rows(output: Path, label: str) -> list[dict]:
    rows, audit = _state_evidence_audit(
        output / "official" / label,
        expected_keys=None,
        expected_model_id=None,
    )
    if not bool(audit["pass"]):
        raise ValueError(
            f"formal {label} rows failed uniqueness/identity audit"
        )
    return rows


def _state_rows_under(root: Path) -> list[dict]:
    rows, audit = _state_evidence_audit(
        root,
        expected_keys=None,
        expected_model_id=None,
    )
    if not bool(audit["pass"]):
        raise ValueError("state rows failed uniqueness/identity audit")
    return rows


def _state_evidence_audit(
    root: Path,
    *,
    expected_keys: set[tuple[int, str]] | None,
    expected_model_id: str | None,
) -> tuple[list[dict], dict]:
    rows = []
    invalid_rows = []
    invalid_probes = []
    duplicate_keys = []
    by_key: dict[tuple[int, str], dict] = {}
    for path in sorted(root.rglob("b4_2_cold_exact_state.json")):
        try:
            payload = _read_json(path)
        except Exception as exc:
            invalid_rows.append(
                {"path": str(path.resolve()), "reason": repr(exc)}
            )
            continue
        state_rows = payload.get("rows", ())
        if not isinstance(state_rows, list):
            invalid_rows.append(
                {
                    "path": str(path.resolve()),
                    "reason": "state rows are not a list",
                }
            )
            continue
        for value in state_rows:
            row = dict(value)
            scale = int(row.get("scale") or 0)
            instance_key = str(row.get("instance_key") or "")
            key = (scale, instance_key)
            if scale <= 0 or not instance_key:
                invalid_rows.append(
                    {
                        "path": str(path.resolve()),
                        "reason": "row lacks scale/instance identity",
                    }
                )
                continue
            row["_state_path"] = str(path.resolve())
            probe_value = str(
                row.get("root_pool_latest_probe_json")
                or row.get("source_probe_json")
                or ""
            )
            probe_path = (
                _resolve(probe_value) if probe_value else Path()
            )
            if not probe_value or not probe_path.is_file():
                invalid_probes.append(
                    {
                        "scale": scale,
                        "instance_key": instance_key,
                        "reason": "source probe is missing",
                    }
                )
                row["_probe"] = {}
            else:
                try:
                    row["_probe"] = _read_json(probe_path)
                    row["_probe_path"] = str(probe_path.resolve())
                    row["_probe_sha256"] = _sha256(probe_path)
                except Exception as exc:
                    invalid_probes.append(
                        {
                            "scale": scale,
                            "instance_key": instance_key,
                            "reason": repr(exc),
                        }
                    )
                    row["_probe"] = {}
            previous = by_key.get(key)
            if previous is not None:
                duplicate_keys.append(
                    {
                        "scale": scale,
                        "instance_key": instance_key,
                        "first_path": previous["_state_path"],
                        "duplicate_path": str(path.resolve()),
                    }
                )
                continue
            by_key[key] = row
            rows.append(row)
    observed_keys = set(by_key)
    missing = (
        set()
        if expected_keys is None
        else set(expected_keys) - observed_keys
    )
    unexpected = (
        set()
        if expected_keys is None
        else observed_keys - set(expected_keys)
    )
    model_mismatches = [
        {
            "scale": int(row["scale"]),
            "instance_key": str(row["instance_key"]),
            "observed_model_id": str(row.get("model_id") or ""),
        }
        for row in rows
        if expected_model_id is not None
        and not (
            str(row.get("model_id") or "") == expected_model_id
            or str(row.get("model_id") or "").startswith(
                expected_model_id + "_S"
            )
        )
    ]
    nonterminal_rows = [
        {
            "scale": int(row["scale"]),
            "instance_key": str(row["instance_key"]),
        }
        for row in rows
        if not bool(row.get("row_terminal"))
    ]
    issues = []
    if invalid_rows:
        issues.append("invalid_state_rows")
    if invalid_probes:
        issues.append("invalid_source_probes")
    if duplicate_keys:
        issues.append("duplicate_scale_instance_rows")
    if missing:
        issues.append("missing_expected_scale_instance_rows")
    if unexpected:
        issues.append("unexpected_scale_instance_rows")
    if model_mismatches:
        issues.append("model_id_mismatch")
    if nonterminal_rows:
        issues.append("nonterminal_rows")
    return rows, {
        "pass": not issues,
        "root": str(root.resolve()),
        "row_count": len(rows),
        "expected_row_count": (
            None if expected_keys is None else len(expected_keys)
        ),
        "issues": issues,
        "invalid_rows": invalid_rows,
        "invalid_probes": invalid_probes,
        "duplicate_keys": duplicate_keys,
        "missing_keys": [
            {"scale": scale, "instance_key": instance}
            for scale, instance in sorted(missing)
        ],
        "unexpected_keys": [
            {"scale": scale, "instance_key": instance}
            for scale, instance in sorted(unexpected)
        ],
        "model_mismatches": model_mismatches,
        "nonterminal_rows": nonterminal_rows,
    }


def _expected_formal_keys(
    experiment: Mapping[str, object],
) -> set[tuple[int, str]]:
    gates = dict(experiment["gates"])
    exact_counts = dict(gates["exact_count_by_scale"])
    keys = {
        (scale, f"instance_{index:03d}")
        for scale in (5, 10, 20, 30)
        for index in range(
            1, int(exact_counts[str(scale)]) + 1
        )
    }
    scale50_paths = (
        *_indexed_instances(experiment["official_scale50_held_out"]),
        *(
            _resolve(value)
            for value in experiment[
                "official_scale50_final_non_held_out"
            ]
        ),
    )
    keys.update(
        (50, _instance_key_from_path(path))
        for path in scale50_paths
    )
    if len(keys) != 100:
        raise SystemExit(
            "formal expected corpus must contain exactly 100 identities"
        )
    return keys


def _instance_key_from_path(path: Path) -> str:
    suffix = "_logical_graph"
    stem = path.stem
    return stem[: -len(suffix)] if stem.endswith(suffix) else stem


def _formal_implementation_audit(output: Path) -> dict:
    issues = []
    prepare_path = output / "prepare_manifest.json"
    prepared_hash = ""
    if not prepare_path.is_file():
        issues.append("prepare_manifest_missing")
        prepare = {}
    else:
        prepare = _read_json(prepare_path)
        binding = dict(prepare.get("implementation_binding") or {})
        prepared_hash = str(
            prepare.get("implementation_binding_hash") or ""
        )
        binding_core = {
            key: value
            for key, value in binding.items()
            if key != "binding_hash"
        }
        if (
            not prepared_hash
            or str(binding.get("binding_hash") or "") != prepared_hash
            or _payload_sha256(binding_core) != prepared_hash
        ):
            issues.append("prepare_implementation_binding_invalid")
    current = _implementation_binding()
    current_hash = str(current["binding_hash"])
    if prepared_hash and current_hash != prepared_hash:
        issues.append("implementation_changed_after_prepare")
    return {
        "pass": not issues,
        "issues": issues,
        "prepare_manifest": str(prepare_path.resolve()),
        "prepared_binding_hash": prepared_hash,
        "current_binding_hash": current_hash,
    }


def _candidate_launch_audit(
    experiment: Mapping[str, object],
    output: Path,
    *,
    label: str,
    config_path: Path,
    implementation_binding_hash: str,
) -> dict:
    expected = (
        (
            "small30",
            (5, 10, 20, 30),
            tuple(),
        ),
        (
            "scale50_heldout",
            (50,),
            _indexed_instances(
                experiment["official_scale50_held_out"]
            ),
        ),
        (
            "scale50_001",
            (50,),
            tuple(
                _resolve(value)
                for value in experiment[
                    "official_scale50_final_non_held_out"
                ]
            ),
        ),
    )
    rows = []
    issues = []
    for directory, scales, instances in expected:
        path = (
            output
            / "official"
            / label
            / directory
            / "p0v4_launch_manifest.json"
        )
        row_issues = _launch_manifest_issues(
            path,
            config_path=config_path,
            expected_scales=scales,
            expected_instances=instances,
            implementation_binding_hash=(
                implementation_binding_hash
            ),
        )
        rows.append(
            {
                "path": str(path.resolve()),
                "issues": row_issues,
            }
        )
        issues.extend(
            f"{directory}:{issue}" for issue in row_issues
        )
    return {
        "pass": not issues,
        "label": label,
        "issues": issues,
        "launches": rows,
    }


def _scale100_launch_audit(
    experiment: Mapping[str, object],
    output: Path,
    *,
    implementation_binding_hash: str,
    final_config_name: str = "GAT.yaml",
) -> dict:
    instances = _indexed_instances(
        experiment["scale100_diagnostic"]
    )
    rows = []
    issues = []
    for directory, config_name in (
        ("P0V4", "P0V4.yaml"),
        ("FinalCandidate", final_config_name),
    ):
        path = (
            output
            / "diagnostic"
            / "scale100"
            / directory
            / "p0v4_launch_manifest.json"
        )
        row_issues = _launch_manifest_issues(
            path,
            config_path=output / "configs" / config_name,
            expected_scales=(100,),
            expected_instances=instances,
            implementation_binding_hash=(
                implementation_binding_hash
            ),
        )
        rows.append(
            {"path": str(path.resolve()), "issues": row_issues}
        )
        issues.extend(
            f"{directory}:{issue}" for issue in row_issues
        )
    return {"pass": not issues, "issues": issues, "launches": rows}


def _launch_manifest_issues(
    path: Path,
    *,
    config_path: Path,
    expected_scales: tuple[int, ...],
    expected_instances: tuple[Path, ...],
    implementation_binding_hash: str,
) -> list[str]:
    if not path.is_file():
        return ["launch_manifest_missing"]
    try:
        row = _read_json(path)
    except Exception:
        return ["launch_manifest_invalid_json"]
    issues = []
    if (
        str(row.get("schema_version") or "")
        != "lunar_ice_bpc.p0v4_acceptance_launch.v1"
    ):
        issues.append("launch_schema_mismatch")
    if (
        not config_path.is_file()
        or Path(str(row.get("config") or "")).resolve()
        != config_path.resolve()
        or str(row.get("config_sha256") or "")
        != _sha256(config_path)
    ):
        issues.append("launch_config_binding_mismatch")
    if tuple(int(value) for value in row.get("scales", ())) != tuple(
        int(value) for value in expected_scales
    ):
        issues.append("launch_scale_set_mismatch")
    if tuple(
        Path(str(value)).resolve()
        for value in row.get("instances", ())
    ) != tuple(value.resolve() for value in expected_instances):
        issues.append("launch_instance_set_mismatch")
    if int(row.get("large_scale_concurrency") or 0) != 1:
        issues.append("launch_concurrency_mismatch")
    before = str(
        row.get("implementation_binding_hash_before") or ""
    )
    after = str(
        row.get("implementation_binding_hash_after") or ""
    )
    if (
        not implementation_binding_hash
        or before != implementation_binding_hash
        or after != implementation_binding_hash
        or not bool(row.get("implementation_stable_during_launch"))
        or not bool(row.get("evidence_usable"))
    ):
        issues.append("launch_implementation_binding_mismatch")
    if int(row.get("returncode") or 0) not in {0, 1}:
        issues.append("launch_returncode_invalid")
    return issues


def _one_deviation_runtime_audit(
    rows: list[dict],
    *,
    allowed_scales: set[int],
    expected_manifest_sha256: str = "",
    require_at_least_one_execution: bool = False,
    maximum_inference_p99_ms: float = 10.0,
) -> dict:
    issues = []
    execution_rows = []
    runtime_call_count = 0
    runtime_error_count = 0
    fallback_count = 0
    ood_noop_count = 0
    inference_latencies_ms = []
    for row in rows:
        scale = int(row.get("scale") or 0)
        row_instrumented = False
        history = [
            dict(value)
            for value in dict(row.get("_probe") or {}).get(
                "history", ()
            )
        ]
        for round_row in history:
            instrumented = (
                "one_deviation_executed" in round_row
            )
            row_instrumented = row_instrumented or instrumented
            runtime_enabled = bool(
                round_row.get("one_deviation_runtime_enabled")
            )
            fallback = bool(
                round_row.get("one_deviation_fallback_to_noop")
            )
            runtime_error = str(
                round_row.get("one_deviation_runtime_error") or ""
            )
            requested = bool(
                round_row.get("one_deviation_requested")
            )
            executed = bool(
                round_row.get("one_deviation_executed")
            )
            intervention_count = int(
                round_row.get(
                    "one_deviation_intervention_count_this_root"
                )
                or 0
            )
            decision_reason = str(
                round_row.get("one_deviation_decision_reason")
                or round_row.get("one_deviation_reject_reason")
                or ""
            )
            runtime_call_count += int(
                runtime_enabled or fallback or bool(runtime_error)
            )
            fallback_count += int(fallback)
            runtime_error_count += int(bool(runtime_error))
            ood_noop_count += int(
                bool(round_row.get("one_deviation_ood"))
                and not executed
            )
            identity = (
                f"scale{scale}/{row.get('instance_key')}/"
                f"round{round_row.get('round')}"
            )
            if scale not in allowed_scales:
                if any(
                    (
                        runtime_enabled,
                        fallback,
                        bool(runtime_error),
                        requested,
                        executed,
                        intervention_count != 0,
                    )
                ):
                    issues.append(
                        identity + ":runtime_active_outside_allowlist"
                    )
                continue
            if not instrumented:
                issues.append(
                    identity + ":runtime_telemetry_missing"
                )
                continue
            if runtime_enabled:
                latency = round_row.get(
                    "one_deviation_inference_wall_ms"
                )
                if latency is None or float(latency) < 0.0:
                    issues.append(
                        identity + ":one_deviation_inference_latency_missing"
                    )
                else:
                    inference_latencies_ms.append(float(latency))
                if bool(
                    round_row.get("one_deviation_evaluation_mode")
                ):
                    issues.append(
                        identity + ":evaluation_mode_active_in_formal_run"
                    )
                if not str(
                    round_row.get(
                        "one_deviation_exact_runtime_binding_hash"
                    )
                    or ""
                ):
                    issues.append(
                        identity
                        + ":one_deviation_exact_runtime_binding_hash_missing"
                    )
                if (
                    expected_manifest_sha256
                    and str(
                        round_row.get(
                            "one_deviation_manifest_sha256"
                        )
                        or ""
                    )
                    != expected_manifest_sha256
                ):
                    issues.append(
                        identity + ":deployment_manifest_hash_mismatch"
                    )
            if runtime_error and (not fallback or executed):
                issues.append(
                    identity + ":runtime_error_did_not_fail_noop"
                )
            if runtime_error:
                issues.append(identity + ":runtime_error_observed")
            if bool(round_row.get("one_deviation_ood")) and (
                executed or decision_reason != "context_ood"
            ):
                issues.append(
                    identity + ":ood_did_not_fail_noop"
                )
            if decision_reason in {
                "memory_adverse_event_veto",
                "no_candidate_passed_thresholds",
                "root_intervention_already_used",
                "calibration_gate_failed",
                "context_hash_mismatch",
                "model_hash_mismatch",
                "invalid_model_output",
            } and executed:
                issues.append(
                    identity + ":safety_veto_executed_promotion"
                )
            if executed:
                execution_rows.append(
                    {
                        "scale": scale,
                        "instance_key": str(row["instance_key"]),
                        "round": int(round_row.get("round") or 0),
                    }
                )
                if (
                    not requested
                    or intervention_count != 1
                    or str(
                        round_row.get(
                            "one_deviation_next_round_policy"
                        )
                        or ""
                    )
                    != "restore_frozen_exact_p0_order"
                ):
                    issues.append(
                        identity + ":promotion_contract_mismatch"
                    )
                for key in (
                    "one_deviation_manifest_sha256",
                    "one_deviation_checkpoint_sha256",
                    "one_deviation_input_hash",
                    "one_deviation_exact_engine_hash",
                    "one_deviation_exact_runtime_binding_hash",
                    "one_deviation_request_config_hash",
                ):
                    if not str(round_row.get(key) or ""):
                        issues.append(
                            identity + f":{key}_missing"
                        )
        if scale in allowed_scales and not row_instrumented:
            issues.append(
                f"scale{scale}/{row.get('instance_key')}:"
                "runtime_telemetry_absent_for_root"
            )
    execution_count_by_root: dict[tuple[int, str], int] = {}
    for value in execution_rows:
        key = (int(value["scale"]), str(value["instance_key"]))
        execution_count_by_root[key] = (
            execution_count_by_root.get(key, 0) + 1
        )
    repeated_roots = [
        {
            "scale": scale,
            "instance_key": instance,
            "execution_count": count,
        }
        for (scale, instance), count in sorted(
            execution_count_by_root.items()
        )
        if count > 1
    ]
    if repeated_roots:
        issues.append("more_than_one_promotion_per_root")
    if require_at_least_one_execution and not execution_rows:
        issues.append("no_formal_promotion_executed")
    ordered_latencies = sorted(inference_latencies_ms)
    inference_p99_ms = (
        None
        if not ordered_latencies
        else ordered_latencies[
            max(
                0,
                min(
                    len(ordered_latencies) - 1,
                    ceil(0.99 * len(ordered_latencies)) - 1,
                ),
            )
        ]
    )
    if (
        inference_p99_ms is not None
        and inference_p99_ms > float(maximum_inference_p99_ms)
    ):
        issues.append("formal_inference_p99_gate_failed")
    return {
        "pass": not issues,
        "allowed_scales": sorted(allowed_scales),
        "issues": issues,
        "runtime_call_count": runtime_call_count,
        "runtime_error_count": runtime_error_count,
        "fallback_to_noop_count": fallback_count,
        "ood_noop_count": ood_noop_count,
        "inference_p99_ms": inference_p99_ms,
        "inference_latency_sample_count": len(ordered_latencies),
        "maximum_inference_p99_ms": float(maximum_inference_p99_ms),
        "promotion_execution_count": len(execution_rows),
        "promotion_executions": execution_rows,
        "roots_with_multiple_promotions": repeated_roots,
    }


def _baseline_rows(
    experiment: Mapping[str, object],
) -> tuple[list[dict], dict]:
    expected_keys = {
        (scale, f"instance_{index:03d}")
        for scale in (5, 10, 20, 30)
        for index in range(1, 21)
    }
    rows = []
    source_files = []
    invalid_sources = []
    duplicate_keys = []
    by_key: dict[tuple[int, str], dict] = {}
    evidence = dict(experiment["baseline_evidence"])
    for key in ("small_scale_current_engine", "scale30_frozen"):
        summary_path = _resolve(evidence[key])
        if not summary_path.is_file():
            invalid_sources.append(
                {"source": key, "reason": "summary_missing"}
            )
            continue
        try:
            summary = _read_json(summary_path)
        except Exception as exc:
            invalid_sources.append(
                {"source": key, "reason": repr(exc)}
            )
            continue
        source_files.append(
            {
                "role": key,
                "path": str(summary_path.resolve()),
                "sha256": _sha256(summary_path),
            }
        )
        for scale_row in summary.get("rows", ()):
            output_dir = Path(str(scale_row.get("output_dir") or ""))
            state = output_dir / "b4_2_cold_exact_state.json"
            if not state.is_file():
                invalid_sources.append(
                    {
                        "source": key,
                        "scale": int(scale_row.get("scale") or 0),
                        "reason": "state_missing",
                        "path": str(state.resolve()),
                    }
                )
                continue
            try:
                state_payload = _read_json(state)
            except Exception as exc:
                invalid_sources.append(
                    {
                        "source": key,
                        "reason": repr(exc),
                        "path": str(state.resolve()),
                    }
                )
                continue
            source_files.append(
                {
                    "role": f"{key}_state",
                    "path": str(state.resolve()),
                    "sha256": _sha256(state),
                }
            )
            for value in state_payload.get("rows", ()):
                row = dict(value)
                identity = (
                    int(row.get("scale") or 0),
                    str(row.get("instance_key") or ""),
                )
                if identity[0] <= 0 or not identity[1]:
                    invalid_sources.append(
                        {
                            "source": key,
                            "reason": "row_identity_missing",
                            "path": str(state.resolve()),
                        }
                    )
                    continue
                if identity in by_key:
                    duplicate_keys.append(
                        {
                            "scale": identity[0],
                            "instance_key": identity[1],
                        }
                    )
                    continue
                row["_state_path"] = str(state.resolve())
                by_key[identity] = row
                rows.append(row)
    observed_keys = set(by_key)
    missing = expected_keys - observed_keys
    unexpected = observed_keys - expected_keys
    nonexact = [
        {
            "scale": scale,
            "instance_key": instance,
        }
        for (scale, instance), row in sorted(by_key.items())
        if not _is_exact(row)
    ]
    redline_rows = [
        {
            "scale": scale,
            "instance_key": instance,
            "redline_count": _row_redlines(row),
        }
        for (scale, instance), row in sorted(by_key.items())
        if _row_redlines(row) > 0
    ]
    issues = []
    if invalid_sources:
        issues.append("baseline_source_invalid")
    if duplicate_keys:
        issues.append("baseline_duplicate_scale_instance_rows")
    if missing:
        issues.append("baseline_missing_expected_rows")
    if unexpected:
        issues.append("baseline_unexpected_rows")
    if nonexact:
        issues.append("baseline_nonexact_rows")
    if redline_rows:
        issues.append("baseline_correctness_redline")
    return rows, {
        "pass": not issues,
        "issues": issues,
        "expected_row_count": len(expected_keys),
        "observed_row_count": len(rows),
        "source_files": source_files,
        "invalid_sources": invalid_sources,
        "duplicate_keys": duplicate_keys,
        "missing_keys": [
            {"scale": scale, "instance_key": instance}
            for scale, instance in sorted(missing)
        ],
        "unexpected_keys": [
            {"scale": scale, "instance_key": instance}
            for scale, instance in sorted(unexpected)
        ],
        "nonexact_rows": nonexact,
        "redline_rows": redline_rows,
    }


def _candidate_metrics(
    rows: list[dict], baseline_rows: list[dict]
) -> dict:
    by_scale = {}
    baseline_by_key = {
        (int(row.get("scale") or 0), str(row.get("instance_key"))): row
        for row in baseline_rows
    }
    ratios_by_scale: dict[int, list[float]] = {}
    redlines = 0
    for row in rows:
        scale = int(row.get("scale") or 0)
        bucket = by_scale.setdefault(
            str(scale),
            {"row_count": 0, "exact_count": 0, "wall_time_sec": 0.0},
        )
        bucket["row_count"] += 1
        exact = _is_exact(row)
        bucket["exact_count"] += int(exact)
        wall = float(row.get("cold_start_total_sec") or 0.0)
        bucket["wall_time_sec"] += wall
        redlines += _row_redlines(row)
        control = baseline_by_key.get(
            (scale, str(row.get("instance_key")))
        )
        if exact and control is not None and _is_exact(control):
            control_wall = float(
                control.get("cold_start_total_sec") or 0.0
            )
            if wall > 0.0 and control_wall > 0.0:
                ratios_by_scale.setdefault(scale, []).append(
                    wall / control_wall
                )
    geometric_ratio_by_scale = {
        str(scale): _geometric_mean(values)
        for scale, values in ratios_by_scale.items()
    }
    paired_exact_count_by_scale = {
        str(scale): len(ratios_by_scale.get(scale, ()))
        for scale in (5, 10, 20, 30)
    }
    return {
        "row_count": len(rows),
        "by_scale": by_scale,
        "paired_exact_count_by_scale": paired_exact_count_by_scale,
        "paired_geometric_mean_ratio_by_scale": (
            geometric_ratio_by_scale
        ),
        "scale20_30_combined_ratio": _geometric_mean(
            [
                value
                for scale in (20, 30)
                for value in ratios_by_scale.get(scale, ())
            ]
        ),
        "scale5_30_combined_ratio": _geometric_mean(
            [
                value
                for scale in (5, 10, 20, 30)
                for value in ratios_by_scale.get(scale, ())
            ]
        ),
        "correctness_redline_count": redlines,
        "scale50_held_out_exact_count": sum(
            _is_exact(row)
            for row in rows
            if int(row.get("scale") or 0) == 50
            and int(row.get("instance_index") or 0) >= 2
        ),
    }


def _gat_metrics(
    gat_rows: list[dict], exact_rows: list[dict]
) -> dict:
    exact_by_key = {
        (int(row.get("scale") or 0), str(row.get("instance_key"))): row
        for row in exact_rows
    }
    ratios = []
    ratios_by_scale: dict[int, list[float]] = {}
    exact_count = 0
    exact_only_count = 0
    redlines = 0
    for row in gat_rows:
        key = (
            int(row.get("scale") or 0),
            str(row.get("instance_key")),
        )
        control = exact_by_key.get(key)
        gat_exact = _is_exact(row)
        exact_count += int(gat_exact)
        redlines += _row_redlines(row)
        if control is not None and _is_exact(control):
            exact_only_count += 1
            if gat_exact:
                left = float(row.get("cold_start_total_sec") or 0.0)
                right = float(
                    control.get("cold_start_total_sec") or 0.0
                )
                if left > 0.0 and right > 0.0:
                    ratio = left / right
                    ratios.append(ratio)
                    ratios_by_scale.setdefault(key[0], []).append(ratio)
    scale50_extra = sum(
        _is_exact(row)
        and not _is_exact(exact_by_key.get(
            (50, str(row.get("instance_key"))), {}
        ))
        for row in gat_rows
        if int(row.get("scale") or 0) == 50
    )
    return {
        "row_count": len(gat_rows),
        "exact_count": exact_count,
        "exact_candidate_count": sum(
            _is_exact(row) for row in exact_rows
        ),
        "exact_only_common_reference_count": exact_only_count,
        "commonly_exact_paired_geometric_mean_ratio": (
            _geometric_mean(ratios)
        ),
        "paired_geometric_mean_ratio_by_scale": {
            str(scale): _geometric_mean(values)
            for scale, values in sorted(ratios_by_scale.items())
        },
        "commonly_exact_count_by_scale": {
            str(scale): len(values)
            for scale, values in sorted(ratios_by_scale.items())
        },
        "scale50_extra_exact_closure_count": scale50_extra,
        "correctness_redline_count": redlines,
    }


def _exact_gate(metrics: Mapping[str, object], gates: Mapping[str, object]) -> dict:
    issues = []
    by_scale = dict(metrics["by_scale"])
    for scale, required in dict(gates["exact_count_by_scale"]).items():
        observed = int(dict(by_scale.get(str(scale), {})).get("exact_count") or 0)
        if observed < int(required):
            issues.append(f"scale{scale}_exact_{observed}_lt_{required}")
    heldout = int(metrics["scale50_held_out_exact_count"])
    if heldout < int(gates["scale50_held_out_min_exact"]):
        issues.append("scale50_heldout_exact_gate_failed")
    paired_exact_counts = dict(
        metrics.get("paired_exact_count_by_scale") or {}
    )
    for scale, maximum in dict(gates["scale_small_ratio_max"]).items():
        paired_count = int(
            paired_exact_counts.get(str(scale), 0)
        )
        if paired_count != 20:
            issues.append(
                f"scale{scale}_paired_control_count_{paired_count}_ne_20"
            )
        ratio = dict(
            metrics["paired_geometric_mean_ratio_by_scale"]
        ).get(str(scale))
        if ratio is None or float(ratio) > float(maximum):
            issues.append(f"scale{scale}_time_ratio_gate_failed")
    if float(metrics["scale20_30_combined_ratio"]) > (
        1.0 - float(gates["scale20_30_combined_speedup_min"])
    ):
        issues.append("scale20_30_combined_speedup_gate_failed")
    if float(metrics["scale5_30_combined_ratio"]) > (
        1.0 - float(gates["scale5_30_combined_speedup_min"])
    ):
        issues.append("scale5_30_combined_speedup_gate_failed")
    if int(metrics["correctness_redline_count"]) > int(
        gates["correctness_redline_max"]
    ):
        issues.append("correctness_redline_gate_failed")
    return {"pass": not issues, "issues": issues}


def _gat_gate(
    metrics: Mapping[str, object],
    gates: Mapping[str, object],
    manifest_path: Path,
) -> dict:
    issues = []
    if not manifest_path.is_file():
        issues.append("deployment_manifest_missing")
        return {"pass": False, "issues": issues}
    manifest = _read_json(manifest_path)
    if not bool(manifest.get("deployment_authorized")):
        issues.append("deployment_not_authorized")
    p99 = float(
        dict(manifest.get("latency") or {}).get("p99_ms")
        or manifest.get("inference_p99_ms")
        or 1.0e12
    )
    if p99 > float(gates["inference_p99_ms_max"]):
        issues.append("inference_p99_gate_failed")
    ratios_by_scale = dict(
        metrics.get("paired_geometric_mean_ratio_by_scale") or {}
    )
    counts_by_scale = dict(
        metrics.get("commonly_exact_count_by_scale") or {}
    )
    for scale in (30, 50):
        ratio = ratios_by_scale.get(str(scale))
        if int(counts_by_scale.get(str(scale), 0)) <= 0:
            issues.append(f"gat_scale{scale}_common_exact_missing")
        if (
            ratio is None
            or float(ratio)
            > 1.0 - float(gates["gat_common_exact_speedup_min"])
        ):
            issues.append(f"gat_scale{scale}_speedup_gate_failed")
    if int(metrics["exact_count"]) < int(
        metrics["exact_candidate_count"]
    ):
        issues.append("gat_exact_count_regressed")
    if int(metrics["correctness_redline_count"]) > int(
        gates["correctness_redline_max"]
    ):
        issues.append("gat_correctness_redline_gate_failed")
    return {
        "pass": not issues,
        "issues": issues,
        "inference_p99_ms": p99,
    }


def _freeze_candidate(
    experiment: Mapping[str, object],
    output: Path,
    *,
    summary: Mapping[str, object],
    exact_config: Path,
    gat_config: Path,
) -> int:
    if not bool(summary.get("final_candidate_gate_pass")):
        raise SystemExit(
            "final candidate cannot be frozen before every formal gate passes"
        )
    freeze_dir = (
        output / "frozen_final_candidate"
    )
    if freeze_dir.exists():
        raise SystemExit(
            f"independent final freeze already exists: {freeze_dir}"
        )
    freeze_dir.mkdir(parents=True)
    gat_branch = _one_deviation_branch_state(experiment)
    branch_artifact = (
        _resolve(gat_branch["terminal_decision"])
        if gat_branch["mode"] == "stopped"
        else _one_deviation_manifest_path(experiment)
    )
    artifacts = (
        exact_config.parent / "P0V4.yaml",
        exact_config.parent / "BatchAdmissionOnly.yaml",
        exact_config.parent / "DiverseEscapeOnly.yaml",
        exact_config.parent / "EscapeBatchUnidirectional.yaml",
        exact_config,
        gat_config,
        exact_config.parent / "paper_ablation_manifest.json",
        output / "prepare_manifest.json",
        output / "final_acceptance_summary.json",
        _resolve(experiment["fixed_k_selection"]),
        branch_artifact,
    )
    copied = {}
    for source in artifacts:
        target = freeze_dir / source.name
        shutil.copy2(source, target)
        copied[target.name] = {
            "sha256": _sha256(target),
            "size_bytes": target.stat().st_size,
        }
    prepare = _read_json(output / "prepare_manifest.json")
    implementation_binding_path = (
        freeze_dir / "formal_implementation_binding.json"
    )
    _write_json(
        implementation_binding_path,
        dict(prepare["implementation_binding"]),
    )
    copied[implementation_binding_path.name] = {
        "sha256": _sha256(implementation_binding_path),
        "size_bytes": implementation_binding_path.stat().st_size,
    }
    evidence_capsule_path = (
        freeze_dir / "formal_evidence_capsule.json"
    )
    _write_json(
        evidence_capsule_path,
        _formal_evidence_capsule(experiment, output),
    )
    copied[evidence_capsule_path.name] = {
        "sha256": _sha256(evidence_capsule_path),
        "size_bytes": evidence_capsule_path.stat().st_size,
    }
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_final_candidate_freeze.v1"
        ),
        "freeze_id": (
            "FROZEN_P0V4_V5_EXACT_GAT_STOPPED_V1"
            if gat_branch["mode"] == "stopped"
            else "FROZEN_P0V4_V5_ONE_DEVIATION_GAT_V1"
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": copied,
        "formal_gate_pass": True,
        "one_deviation_branch_mode": gat_branch["mode"],
        "gat_performance_claim_authorized": bool(
            gat_branch["mode"] == "actionful"
        ),
        "historical_p0v4_preserved": True,
        "historical_p0v3_preserved": True,
        "production_no_cut_preserved": True,
    }
    _write_json(freeze_dir / "freeze_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _formal_evidence_capsule(
    experiment: Mapping[str, object],
    output: Path,
) -> dict:
    """Bind every formal launch, state, and source probe by content hash."""

    gat_branch = _one_deviation_branch_state(experiment)
    branch_artifact = (
        _resolve(gat_branch["terminal_decision"])
        if gat_branch["mode"] == "stopped"
        else _one_deviation_manifest_path(experiment)
    )
    files = {
        output / "prepare_manifest.json",
        output / "final_acceptance_summary.json",
        _resolve(experiment["fixed_k_selection"]),
        branch_artifact,
    }
    files.update(
        _resolve(value)
        for value in dict(experiment["baseline_evidence"]).values()
    )
    for root in (
        output / "official",
        output / "diagnostic" / "scale100",
    ):
        files.update(root.rglob("p0v4_launch_manifest.json"))
        for state in root.rglob("b4_2_cold_exact_state.json"):
            files.add(state)
            payload = _read_json(state)
            for value in payload.get("rows", ()):
                row = dict(value)
                probe_value = str(
                    row.get("root_pool_latest_probe_json")
                    or row.get("source_probe_json")
                    or ""
                )
                if probe_value:
                    files.add(_resolve(probe_value))
    missing = [
        str(path.resolve())
        for path in files
        if not path.is_file()
    ]
    if missing:
        raise SystemExit(
            "formal evidence capsule has missing files: "
            + ", ".join(sorted(missing))
        )
    entries = [
        {
            "path": (
                str(path.resolve().relative_to(ROOT))
                if path.resolve().is_relative_to(ROOT)
                else str(path.resolve())
            ),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(files, key=lambda value: str(value.resolve()))
    ]
    core = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_formal_evidence_capsule.v1"
        ),
        "entry_count": len(entries),
        "entries": entries,
    }
    return {**core, "binding_hash": _payload_sha256(core)}


def _prepare_manifest(
    experiment: Mapping[str, object],
    *,
    config_path: Path,
    exact_config: Path,
    gat_config: Path,
) -> dict:
    fixed_path = _resolve(experiment["fixed_k_selection"])
    fixed = _read_json(fixed_path)
    gat_manifest = _one_deviation_manifest_path(experiment)
    gat_branch = _one_deviation_branch_state(experiment)
    gat_ready = bool(
        gat_manifest.is_file()
        and _read_json(gat_manifest).get("deployment_authorized")
    )
    implementation = _implementation_binding()
    return {
        "schema_version": "lunar_ice_bpc.p0v4_final_prepare.v1",
        "status": (
            "EXACT_READY_GAT_STOPPED_BY_GATE"
            if gat_branch["mode"] == "stopped"
            else (
                "EXACT_READY_GAT_PENDING"
                if not gat_ready
                else "EXACT_AND_GAT_READY"
            )
        ),
        "experiment_config": str(config_path.resolve()),
        "experiment_config_sha256": _sha256(config_path),
        "fixed_k_selection": str(fixed_path.resolve()),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "selected_arm": fixed["selected_arm"],
        "exact_config": str(exact_config.resolve()),
        "exact_config_sha256": _sha256(exact_config),
        "gat_config": str(gat_config.resolve()),
        "gat_config_sha256": _sha256(gat_config),
        "one_deviation_branch": gat_branch,
        "paper_ablation_manifest": str(
            (
                exact_config.parent
                / "paper_ablation_manifest.json"
            ).resolve()
        ),
        "paper_ablation_manifest_sha256": _sha256(
            exact_config.parent / "paper_ablation_manifest.json"
        ),
        "implementation_binding": implementation,
        "implementation_binding_hash": str(
            implementation["binding_hash"]
        ),
        "frozen_p0v4_verified": True,
        "production_default_changed": False,
    }


def _verify_frozen_p0v4(
    experiment: Mapping[str, object],
) -> None:
    verifier = _resolve(experiment["frozen_p0v4_verifier"])
    completed = subprocess.run(
        [sys.executable, str(verifier)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "frozen P0V4 verification failed: " + completed.stderr
        )


def _indexed_instances(
    row: Mapping[str, object],
) -> tuple[Path, ...]:
    directory = _resolve(row["instance_dir"])
    return tuple(
        directory / f"instance_{index:03d}_logical_graph.json"
        for index in range(
            int(row["first_index"]), int(row["last_index"]) + 1
        )
    )


def _has_complete_state(root: Path, *, expected: int) -> bool:
    rows, audit = _state_evidence_audit(
        root,
        expected_keys=None,
        expected_model_id=None,
    )
    return bool(audit["pass"]) and len(rows) == int(expected)


def _is_exact(row: Mapping[str, object]) -> bool:
    return bool(
        row.get("bpc_tree_optimal")
        or str(row.get("algorithm_status")) == "BPC_OPTIMAL"
    )


def _row_redlines(row: Mapping[str, object]) -> int:
    keys = (
        "certificate_leak",
        "manual_rc_fail",
        "pricing_rc_fail",
        "true_dual_rc_recompute_missing",
        "worker_certificate_leak",
        "tail_dual_certificate_leak",
        "root_pool_large_task_direct_worker_certificate_leak_count",
        "root_pool_support_continuation_certificate_leak_count",
        "root_pool_tail_dual_certificate_leak_count",
        "root_pool_true_dual_rc_recompute_missing_count",
        "root_pool_worker_certificate_leak_count",
    )
    return sum(int(row.get(key) or 0) for key in keys) + int(
        not bool(row.get("no_cheat_pass", True))
    )


def _implementation_binding() -> dict:
    """Hash every source/binary component used by formal candidate runs."""

    native_candidates = tuple(
        _sole_native_module(ROOT / directory)
        for directory in (
            "build/native-spprc-memory-opt-v2",
            "build/native-spprc-bidirectional-feasibility-v1",
        )
    )
    explicit = (
        ROOT / "scripts/run_p0v4_final_acceptance.py",
        ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py",
        ROOT / "scripts/run_lunar_ice_b4_2_cold_exact.py",
        *native_candidates,
    )
    for path in explicit:
        if not path.is_file():
            raise SystemExit(
                f"formal implementation component is missing: {path}"
            )
    files = set(explicit)
    for root in (
        ROOT / "src/lunar_ice_bpc/exact",
        ROOT / "src/lunar_ice_bpc/guidance",
        ROOT / "native/lunar_spprc",
    ):
        files.update(
            path
            for path in root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix
            in {
                ".py",
                ".cpp",
                ".hpp",
                ".h",
                ".cc",
                ".cmake",
                ".txt",
            }
        )
    entries = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(files)
    ]
    core = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_formal_implementation_binding.v1"
        ),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": sys.version,
        "component_count": len(entries),
        "components": entries,
    }
    return {
        **core,
        "binding_hash": _payload_sha256(core),
    }


def _native_build_dir_for_config(config_path: Path) -> Path:
    config = _read_yaml(config_path)
    backends = {
        str(dict(value).get("backend_id") or "")
        for value in dict(config.get("profiles") or {}).values()
    }
    directory = (
        ROOT / "build/native-spprc-bidirectional-feasibility-v1"
        if any("bidirectional" in backend for backend in backends)
        else ROOT / "build/native-spprc-memory-opt-v2"
    )
    _sole_native_module(directory)
    return directory.resolve()


def _sole_native_module(directory: Path) -> Path:
    candidates = tuple(sorted(directory.glob("lunar_spprc_native*.so")))
    if len(candidates) != 1:
        raise SystemExit(
            "formal implementation binding requires one Native module in "
            f"{directory}"
        )
    return candidates[0].resolve()


def _geometric_mean(values: Iterable[float]) -> float:
    rows = [max(1.0e-12, float(value)) for value in values]
    if not rows:
        return 1.0e12
    return exp(sum(log(value) for value in rows) / len(rows))


def _payload_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _validate_experiment(row: Mapping[str, object]) -> None:
    if (
        str(row.get("schema_version"))
        != "lunar_ice_bpc.p0v4_final_acceptance.v1"
    ):
        raise SystemExit("P0V4 final acceptance schema mismatch")
    if int(dict(row["execution"])["large_scale_concurrency"]) != 1:
        raise SystemExit("scale50/100 acceptance must be serial")


def _read_yaml(path: Path) -> dict:
    return dict(yaml.safe_load(path.read_text(encoding="utf-8")))


def _read_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _one_deviation_manifest_path(
    experiment: Mapping[str, object],
) -> Path:
    value = (
        experiment.get("one_deviation_deployment_manifest")
        or experiment.get("one_deviation_training_manifest")
    )
    if not value:
        raise SystemExit("one-deviation deployment manifest is unspecified")
    return _resolve(value)


def _one_deviation_terminal_decision_path(
    experiment: Mapping[str, object],
) -> Path | None:
    value = experiment.get("one_deviation_terminal_decision")
    return None if not value else _resolve(value)


def _one_deviation_branch_state(
    experiment: Mapping[str, object],
) -> dict[str, object]:
    manifest_path = _one_deviation_manifest_path(experiment)
    manifest_authorized = bool(
        manifest_path.is_file()
        and _read_json(manifest_path).get("deployment_authorized")
    )
    terminal_path = _one_deviation_terminal_decision_path(experiment)
    terminal_valid = False
    terminal_issues: list[str] = []
    if terminal_path is not None and terminal_path.is_file():
        terminal = _read_json(terminal_path)
        if str(terminal.get("schema_version") or "") != (
            "lunar_ice_bpc.p0v4_one_deviation_terminal_decision.v1"
        ):
            terminal_issues.append("terminal_schema_mismatch")
        if str(terminal.get("status") or "") != (
            "STOPPED_BY_PREDECLARED_GATES"
        ):
            terminal_issues.append("terminal_status_mismatch")
        if not bool(terminal.get("terminal_decision_valid")):
            terminal_issues.append("terminal_decision_not_valid")
        if not bool(terminal.get("exact_acceptance_may_proceed_without_gat")):
            terminal_issues.append("terminal_does_not_unblock_exact")
        if bool(terminal.get("gat_performance_claim_authorized")):
            terminal_issues.append("terminal_authorizes_gat_claim")
        if str(terminal.get("certificate_or_bound_role") or "") != "none":
            terminal_issues.append("terminal_has_certificate_role")
        if bool(terminal.get("baseline_mutated")):
            terminal_issues.append("terminal_mutated_baseline")
        for artifact in terminal.get("artifacts") or ():
            artifact_path = Path(str(dict(artifact).get("path") or "")).resolve()
            artifact_sha = str(dict(artifact).get("sha256") or "")
            if (
                not artifact_path.is_file()
                or not artifact_sha
                or _sha256(artifact_path) != artifact_sha
            ):
                terminal_issues.append(
                    "terminal_source_artifact_hash_mismatch:"
                    + str(artifact_path)
                )
        terminal_valid = not terminal_issues
    if manifest_authorized and terminal_valid:
        raise SystemExit(
            "one-deviation branch cannot be both deployment-authorized and "
            "terminally stopped"
        )
    if manifest_authorized:
        return {
            "mode": "actionful",
            "deployment_manifest": str(manifest_path.resolve()),
            "deployment_manifest_sha256": _sha256(manifest_path),
            "terminal_decision": "",
            "terminal_decision_sha256": "",
            "issues": [],
        }
    if terminal_valid and terminal_path is not None:
        return {
            "mode": "stopped",
            "deployment_manifest": "",
            "deployment_manifest_sha256": "",
            "terminal_decision": str(terminal_path.resolve()),
            "terminal_decision_sha256": _sha256(terminal_path),
            "issues": [],
        }
    return {
        "mode": "pending",
        "deployment_manifest": (
            str(manifest_path.resolve()) if manifest_path.is_file() else ""
        ),
        "deployment_manifest_sha256": (
            _sha256(manifest_path) if manifest_path.is_file() else ""
        ),
        "terminal_decision": (
            "" if terminal_path is None else str(terminal_path.resolve())
        ),
        "terminal_decision_sha256": (
            ""
            if terminal_path is None or not terminal_path.is_file()
            else _sha256(terminal_path)
        ),
        "issues": terminal_issues or [
            "neither_authorized_deployment_nor_valid_terminal_stop"
        ],
    }


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
