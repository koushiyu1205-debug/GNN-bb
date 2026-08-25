#!/usr/bin/env python3
"""Run frozen four-arm full-BPC development/sealed Temporal-GAT evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.analyze_p0v5_qg2_paired_acceptance import _rows  # noqa: E402
from scripts.p0v5_temporal_gat_common import load_frozen_config  # noqa: E402


MANIFEST_ENV = "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_MANIFEST"
EVALUATION_ENV = "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_EVALUATION_MODE"
FORCE_ACTION_ENV = "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_FORCE_ACTION"
ARMS = ("Q0", "MODEL", "ALWAYS_CONTINUE", "BEST_CONTROL")


def _load(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_once(path: Path, payload: object) -> None:
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable full-BPC artifact drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")


def _evaluation_manifests(base_manifest: Path, output: Path, training_report):
    manifest = _load(base_manifest)
    bundle_path = (base_manifest.parent / manifest["portable_bundle_path"]).resolve()
    bundle = _load(bundle_path)
    selected = {
        str(row["name"]) for row in dict(training_report["control_audit"][
            "best_e2e_control_by_scale"
        ]).values() if str(row["family"]) == "simple"
    }
    paths = {}
    for kind in sorted(selected):
        controls = dict(bundle.get("evaluation_controls") or {})
        if kind not in controls:
            raise SystemExit(f"frozen simple control is missing:{kind}")
        control = dict(bundle)
        control["controller_kind"] = kind
        control["models"] = list(controls[kind]["models"])
        identity = {
            "benefit": {"kind": "platt", "a": 1.0, "b": 0.0},
            "adverse": {"kind": "platt", "a": 1.0, "b": 0.0},
            "gain_scale": 1.0,
        }
        control["calibration_by_scale"] = {
            "30": identity, "50": identity,
        }
        # This is the exact 0.5/0.5/positive-gain OOF policy used to select
        # the simple control.  It must not inherit the GAT's calibration-only
        # thresholds, otherwise the E2E "best control" would be a different
        # controller from the frozen OOF comparator.
        control_threshold = {
            "minimum_benefit_probability": 0.5,
            "maximum_adverse_probability": 0.5,
            "minimum_expected_gain": 0.0,
            "adverse_penalty": 0.0,
            "maximum_disagreement": 1.0,
        }
        control["thresholds_by_scale"] = {
            "30": control_threshold, "50": control_threshold,
        }
        unsigned = dict(control)
        unsigned.pop("bundle_sha256", None)
        control["bundle_sha256"] = hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode()).hexdigest()
        control_path = output / f"temporal_control.{kind}.bundle.json"
        _write_once(control_path, control)
        control_manifest = dict(manifest)
        control_manifest["portable_bundle_path"] = str(control_path)
        control_manifest["portable_bundle_file_sha256"] = _sha(control_path)
        manifest_path = output / f"temporal_control.{kind}.manifest.json"
        _write_once(manifest_path, control_manifest)
        paths[kind] = manifest_path
    return paths


def _mem_available_gb() -> float:
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return float(line.split()[1]) / (1024.0 * 1024.0)
    raise RuntimeError("MemAvailable is unavailable")


def _process_tree_rss_bytes(root_pid: int) -> int:
    """Return the sampled resident bytes of a live process and descendants.

    The scale30 in-process backend does not necessarily emit the host-backend
    ``host_peak_rss_bytes`` field.  Sampling the whole fresh-process tree gives
    both scales a common, conservative production-gate measurement without
    changing the solver or its memory-limit semantics.
    """
    parents: dict[int, int] = {}
    rss_bytes: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text(encoding="utf-8")
            tail = stat[stat.rfind(")") + 2:].split()
            if len(tail) < 2:
                continue
            pid = int(entry.name)
            parents[pid] = int(tail[1])
            rss_kib = 0
            for line in (entry / "status").read_text(
                encoding="utf-8"
            ).splitlines():
                if line.startswith("VmRSS:"):
                    rss_kib = int(line.split()[1])
                    break
            rss_bytes[pid] = rss_kib * 1024
        except (FileNotFoundError, ProcessLookupError, PermissionError,
                ValueError, OSError):
            continue
    selected = {int(root_pid)}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in selected and pid not in selected:
                selected.add(pid)
                changed = True
    return sum(rss_bytes.get(pid, 0) for pid in selected)


def _run_process_with_rss(command, *, environment, telemetry_path: Path) -> int:
    process = subprocess.Popen(
        command, cwd=ROOT, env=environment, start_new_session=True
    )
    peak = 0
    samples = 0
    interrupted = ""
    try:
        while True:
            peak = max(peak, _process_tree_rss_bytes(process.pid))
            samples += 1
            returncode = process.poll()
            if returncode is not None:
                break
            time.sleep(0.10)
    except BaseException as exc:
        interrupted = type(exc).__name__
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10.0)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        returncode = int(process.returncode or -signal.SIGTERM)
        _write_once(telemetry_path, {
            "schema_version": (
                "lunar_ice_bpc.temporal_gat_process_resource_telemetry.v1"
            ),
            "measurement": "sampled_sum_vmrss_process_tree_v1",
            "sample_period_seconds": 0.10,
            "sample_count": samples,
            "process_tree_peak_rss_bytes": peak,
            "returncode": returncode,
            "interrupted_by": interrupted,
        })
        raise
    _write_once(telemetry_path, {
        "schema_version": (
            "lunar_ice_bpc.temporal_gat_process_resource_telemetry.v1"
        ),
        "measurement": "sampled_sum_vmrss_process_tree_v1",
        "sample_period_seconds": 0.10,
        "sample_count": samples,
        "process_tree_peak_rss_bytes": peak,
        "returncode": int(returncode),
        "interrupted_by": interrupted,
    })
    return int(returncode)


def _environment(config, manifest: Path | None, force_action: str = ""):
    environment = dict(os.environ)
    for name in tuple(environment):
        if (
            name.startswith("LUNAR_ICE_P0V5_")
            or name.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or name.startswith("LUNAR_ICE_GAT_")
            or name == "LUNAR_ICE_PRODUCTION_POLICY_REGISTRY"
        ):
            environment.pop(name, None)
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()),
        str((ROOT / "src").resolve()),
    ))
    if manifest is not None:
        environment[MANIFEST_ENV] = str(manifest.resolve())
        environment[EVALUATION_ENV] = "1"
        if force_action:
            environment[FORCE_ACTION_ENV] = str(force_action)
    return environment


def _schedule(config, corpus, manifest, training_report, stage, control_manifests):
    selected = [
        dict(row) for row in corpus["rows"]
        if str(row["partition"]) == stage
    ]
    expected = int(config["split_counts_by_scale"][stage])
    counts = {
        scale: sum(int(row["scale"]) == scale for row in selected)
        for scale in (30, 50)
    }
    if counts != {30: expected, 50: expected}:
        raise SystemExit(f"{stage} corpus count drift:{counts}")
    best = dict(training_report["control_audit"][
        "best_e2e_control_by_scale"
    ])
    if set(best) != {"30", "50"} or any(
        str(row.get("family")) not in {"deterministic", "simple"}
        for row in best.values()
    ):
        raise SystemExit("best deterministic/simple control binding drift")
    tasks = []
    for row in sorted(selected, key=lambda value: (
        int(value["scale"]), str(value["instance_content_hash"])
    )):
        for repeat in range(3):
            ordered = sorted(ARMS, key=lambda arm: hashlib.sha256(
                f"{stage}:{row['instance_content_hash']}:{repeat}:{arm}".encode()
            ).hexdigest())
            for ordinal, arm in enumerate(ordered):
                identity = (
                    f"{stage}:{row['instance_content_hash']}:{repeat}:{arm}"
                )
                tasks.append({
                    "task_id": hashlib.sha256(identity.encode()).hexdigest()[:24],
                    "scale": int(row["scale"]),
                    "instance_hash": str(row["instance_content_hash"]),
                    "instance_path": str((ROOT / row["path"]).resolve()),
                    "instance_file_sha256": str(row["file_sha256"]),
                    "partition": stage, "repeat": repeat, "arm": arm,
                    "ordinal_in_block": ordinal,
                    "force_action": (
                        "CONTINUE_QD1" if arm == "ALWAYS_CONTINUE"
                        else str(best[str(row["scale"])]["force_action"])
                        if arm == "BEST_CONTROL" else ""
                    ),
                    "manifest": (
                        str(control_manifests[
                            str(best[str(row["scale"])]["name"])
                        ]) if arm == "BEST_CONTROL" and
                        best[str(row["scale"])]["family"] == "simple"
                        else str(manifest) if arm != "Q0" else ""
                    ),
                    "fresh_process": True,
                })
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_gat_full_bpc_execution.v1"
        ),
        "status": "FROZEN_BEFORE_FULL_BPC_OUTCOMES",
        "partition": stage,
        "single_host_instance": True,
        "fresh_process_per_task": True,
        "blocked_repeats": 3,
        "arm_order": "sha256_rotated_four_arm_block_v1",
        "best_deterministic_simple_control_by_scale": best,
        "manifest": str(manifest.resolve()),
        "manifest_sha256": _sha(manifest),
        "evaluation_control_manifest_sha256": {
            kind: _sha(path) for kind, path in sorted(control_manifests.items())
        },
        "task_count": len(tasks), "tasks": tasks,
    }


def _run_one(task, output, config, manifest=None):
    if output.exists():
        raise SystemExit(f"partial full-BPC task requires audit:{output}")
    arm = str(task["arm"])
    learned = arm != "Q0"
    selected_manifest = (
        Path(str(task.get("manifest"))).resolve()
        if learned and task.get("manifest") else manifest
    )
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str((ROOT / config["selected_exact_config"]).resolve()),
        "--scales", str(task["scale"]),
        "--instance", str(task["instance_path"]),
        "--limit", "1", "--output-dir", str(output), "--no-resume",
        "--effective-memory-cap-gb", str(
            config["execution"]["effective_native_memory_limit_gb"]
        ),
    ]
    returncode = _run_process_with_rss(
        command,
        environment=_environment(
            config, selected_manifest if learned else None,
            str(task.get("force_action") or ""),
        ),
        telemetry_path=output / "process_resource_telemetry.json",
    )
    if returncode not in {0, 1}:
        raise SystemExit(f"full-BPC task execution error:{task['task_id']}")


def _temporal_telemetry(payload):
    actions = {}
    inference_ms = []
    graph_wall = 0.0
    migration_wall = 0.0
    trial_wall = 0.0
    fail_closed = []
    runtime_reasons = []
    runtime_calls = 0
    tree_model_calls = 0
    peak_rss_bytes = 0
    seen_probes = set()

    def visit(value, *, in_tree=False):
        nonlocal graph_wall, migration_wall, trial_wall, runtime_calls
        nonlocal tree_model_calls, peak_rss_bytes
        if isinstance(value, dict):
            peak_rss_bytes = max(
                peak_rss_bytes, int(value.get("host_peak_rss_bytes") or 0)
            )
            if "proof_tail_frontier_runtime_action" in value:
                runtime_calls += int(bool(value.get(
                    "proof_tail_frontier_runtime_enabled"
                )))
                reason = str(value.get(
                    "proof_tail_frontier_runtime_reason"
                ) or "")
                if reason:
                    runtime_reasons.append(reason)
                if reason.startswith("non_root_lifecycle"):
                    in_tree = True
            probe = value.get("proof_queue_frontier_probe")
            if isinstance(probe, dict) and bool(probe.get("enabled")):
                probe_lifecycle = str(probe.get("pricing_lifecycle") or "")
                probe_scale = int(probe.get("problem_scale") or 0)
                probe_outside_authority = (
                    probe_lifecycle != "root_cg"
                    or probe_scale not in {30, 50}
                    or not bool(probe.get("require_root_cg"))
                )
                probe_identity = hashlib.sha256(json.dumps({
                    "mode": probe.get("mode"), "action": probe.get("action"),
                    "boundary": probe.get("boundary"),
                    "trial_pops": probe.get("trial_pops"),
                    "problem_scale": probe.get("problem_scale"),
                    "pricing_lifecycle": probe.get("pricing_lifecycle"),
                    "require_root_cg": probe.get("require_root_cg"),
                    "start": dict(probe.get("trial_start_snapshot") or {}).get(
                        "graph_hash"
                    ),
                    "end": dict(probe.get("trial_end_snapshot") or {}).get(
                        "graph_hash"
                    ),
                    "seed_outputs": probe.get("seed_outputs"),
                }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if probe_identity in seen_probes:
                    for child in value.values():
                        visit(child, in_tree=in_tree)
                    return
                seen_probes.add(probe_identity)
                action = str(probe.get("action") or "CONTINUE_Q0")
                actions[action] = actions.get(action, 0) + 1
                if bool(probe.get("model_called")):
                    inference_ms.append(
                        1000.0 * float(probe.get("inference_wall_seconds") or 0.0)
                    )
                    if in_tree or probe_outside_authority:
                        tree_model_calls += 1
                graph_wall += float(
                    probe.get("temporal_graph_build_wall_seconds")
                    or probe.get("graph_build_wall_seconds") or 0.0
                )
                migration_wall += float(probe.get("migration_wall_seconds") or 0.0)
                migration_wall += float(
                    probe.get("reverse_migration_wall_seconds") or 0.0
                )
                trial_wall += float(probe.get("trial_wall_seconds") or 0.0)
                if bool(probe.get("fail_closed")):
                    fail_closed.append(str(probe.get("decision_reason") or ""))
            for child in value.values():
                visit(child, in_tree=in_tree)
        elif isinstance(value, list):
            for child in value:
                visit(child, in_tree=in_tree)

    visit(payload)
    return {
        "selected_action_counts": dict(sorted(actions.items())),
        "inference_ms_values": inference_ms,
        "inference_ms": max(inference_ms, default=0.0),
        "graph_wall_seconds": graph_wall,
        "migration_wall_seconds": migration_wall,
        "trial_wall_seconds": trial_wall,
        "fail_closed_reasons": sorted(set(fail_closed)),
        "runtime_reasons": sorted(set(runtime_reasons)),
        "runtime_calls": runtime_calls,
        "tree_model_calls": tree_model_calls,
        "peak_rss_gb": peak_rss_bytes / float(1024 ** 3),
    }


def _parse_one(root, task):
    rows = _rows(root)
    if set(rows) != {task["instance_hash"]}:
        raise SystemExit("full-BPC acceptance output instance mismatch")
    row = dict(rows[task["instance_hash"]])
    tree = _load(Path(row["tree_result"])) if row.get("tree_result") else {}
    telemetry = _temporal_telemetry(tree)
    resource_path = root / "process_resource_telemetry.json"
    resource = _load(resource_path) if resource_path.is_file() else {}
    process_peak_rss_gb = float(
        resource.get("process_tree_peak_rss_bytes") or 0
    ) / float(1024 ** 3)
    telemetry["peak_rss_gb"] = max(
        float(telemetry.get("peak_rss_gb") or 0.0),
        process_peak_rss_gb,
    )
    exact = bool(row["exact"])
    redlines = [] if row["redlines_zero"] else ["solver_redline"]
    if telemetry["tree_model_calls"]:
        redlines.append("temporal_model_called_outside_root_cg")
    if task["arm"] == "Q0" and telemetry["runtime_calls"]:
        redlines.append("literal_q0_temporal_runtime_call")
    ledger = dict(tree.get("certificate_ledger") or {})
    semantics = {
        "algorithm_status": str(row["algorithm_status"]),
        "exact": exact,
        "exact_status": str(tree.get("exact_status") or ""),
        "certificate_scope": str(tree.get("certificate_scope") or ""),
        "all_certificate_ledgers_valid": bool(
            tree.get("all_certificate_ledgers_valid")
        ),
        "certificate_ledger_status": str(
            ledger.get("certificate_status") or ""
        ),
        "certificate_ledger_scope": str(
            ledger.get("certificate_scope") or ""
        ),
        "uses_true_dual_bpc_certificate": bool(
            ledger.get("uses_true_dual_bpc_certificate")
        ),
    }
    wall = float(row["wall_sec"])
    return {
        "task_id": task["task_id"], "scale": int(task["scale"]),
        "instance_hash": task["instance_hash"],
        "partition": task["partition"], "repeat": int(task["repeat"]),
        "arm": task["arm"], "status": "COMPLETE" if exact else "INCOMPLETE",
        "wall_seconds": wall, "resource_censor": not exact,
        "correctness_redlines": redlines,
        "exact_semantics_signature": hashlib.sha256(json.dumps(
            semantics, sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest(),
        "objective": row["objective"], "exact": exact,
        "certificate_semantics": semantics,
        "route_rc_reaudit_pass": bool(row["redlines_zero"]),
        "peak_rss_gb": telemetry["peak_rss_gb"],
        "process_tree_peak_rss_gb": process_peak_rss_gb,
        "process_tree_rss_sample_count": int(
            resource.get("sample_count") or 0
        ),
        "process_resource_telemetry": str(resource_path),
        "process_resource_telemetry_sha256": (
            _sha(resource_path) if resource_path.is_file() else ""
        ),
        "inference_ms": telemetry["inference_ms"],
        "inference_ms_values": telemetry["inference_ms_values"],
        "probe_overhead_ratio": 1.0 + telemetry["graph_wall_seconds"] /
            max(1.0e-9, wall),
        **{key: telemetry[key] for key in (
            "selected_action_counts", "graph_wall_seconds",
            "migration_wall_seconds", "trial_wall_seconds",
            "fail_closed_reasons", "runtime_reasons", "runtime_calls",
            "tree_model_calls",
        )},
        "tree_result": row.get("tree_result") or "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("development_e2e", "sealed_final"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--training-report", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    try:
        config, config_freeze = load_frozen_config(
            args.config, run_root=args.run_root
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    corpus = _load(args.corpus.resolve())
    manifest = args.manifest.resolve()
    training_report = _load(args.training_report.resolve())
    source_path = args.run_root.resolve() / "source.freeze.json"
    if not source_path.is_file():
        raise SystemExit("Temporal-GAT source freeze is missing")
    source = _load(source_path)
    selected_exact = (ROOT / config["selected_exact_config"]).resolve()
    native_binary = Path(str(source.get("native_binary") or ""))
    if (
        Path(str(source.get("corpus_manifest") or "")).resolve()
            != args.corpus.resolve()
        or str(source.get("corpus_manifest_sha256") or "")
            != _sha(args.corpus)
        or not selected_exact.is_file()
        or _sha(selected_exact)
            != str(source.get("selected_exact_config_sha256") or "")
        or not native_binary.is_file()
        or _sha(native_binary) != str(source.get("native_binary_sha256") or "")
    ):
        raise SystemExit("full-BPC source/corpus/config/native binding drift")
    for row in corpus.get("rows") or ():
        path = ROOT / str(row["path"])
        if not path.is_file() or _sha(path) != str(row["file_sha256"]):
            raise SystemExit("full-BPC frozen corpus row drift")
    if training_report.get("status") != "TRAINED_DEVELOPMENT_ONLY_NOT_PROMOTED":
        raise SystemExit("Temporal-GAT training gate is not complete")
    manifest_payload = _load(manifest)
    if not bool(manifest_payload.get("development_e2e_authorized")) or bool(
        manifest_payload.get("deployment_authorized")
    ):
        raise SystemExit("development runtime manifest authority drift")
    bundle_path = (
        manifest.parent / str(manifest_payload.get("portable_bundle_path") or "")
    ).resolve()
    if (
        manifest_payload.get("training_report_sha256")
            != _sha(args.training_report)
        or manifest_payload.get("selected_exact_config_sha256")
            != source.get("selected_exact_config_sha256")
        or manifest_payload.get("native_binary_sha256")
            != source.get("native_binary_sha256")
        or manifest_payload.get("source_freeze_sha256") != _sha(source_path)
        or manifest_payload.get("experiment_config_sha256")
            != _sha(config_freeze)
        or not bundle_path.is_file()
        or manifest_payload.get("portable_bundle_file_sha256")
            != _sha(bundle_path)
        or training_report.get("bundle_file_sha256") != _sha(bundle_path)
    ):
        raise SystemExit("full-BPC model/training/runtime binding drift")
    if args.stage == "sealed_final":
        development_audit_path = (
            args.run_root.resolve() / "full_bpc/development_e2e/audit.json"
        )
        development_outcomes_path = (
            args.run_root.resolve() / "full_bpc/development_e2e/outcomes.json"
        )
        if (
            not development_audit_path.is_file()
            or not development_outcomes_path.is_file()
        ):
            raise SystemExit("sealed final requires a completed development gate")
        development_audit = _load(development_audit_path)
        if (
            development_audit.get("decision") != "PASS"
            or development_audit.get("source_outcomes_sha256")
                != _sha(development_outcomes_path)
        ):
            raise SystemExit("sealed final development evidence binding drift")
    output = args.run_root.resolve() / "full_bpc" / args.stage
    schedule_path = output / "execution.freeze.json"
    control_manifests = _evaluation_manifests(
        manifest, output / "evaluation_controls", training_report
    )
    schedule = _schedule(
        config, corpus, manifest, training_report, args.stage,
        control_manifests,
    )
    schedule.update({
        "source_config_freeze_sha256": _sha(config_freeze),
        "source_freeze_sha256": _sha(source_path),
        "source_corpus_sha256": _sha(args.corpus),
        "source_training_report_sha256": _sha(args.training_report),
        "source_runtime_manifest_sha256": _sha(manifest),
        "source_bundle_sha256": _sha(bundle_path),
        "native_binary_sha256": _sha(native_binary),
    })
    _write_once(schedule_path, schedule)
    raw_root = output / "raw"
    launched = 0
    for task in schedule["tasks"]:
        task_root = raw_root / task["task_id"]
        row_path = task_root / "canonical_row.json"
        if row_path.is_file():
            continue
        if args.task_limit is not None and launched >= int(args.task_limit):
            break
        if _mem_available_gb() < float(
            config["execution"]["memavailable_reserve_gb"]
        ):
            raise SystemExit("MemAvailable reserve would be violated")
        _run_one(task, task_root, config, manifest)
        _write_once(row_path, _parse_one(task_root, task))
        launched += 1
    missing = [
        task for task in schedule["tasks"]
        if not (raw_root / task["task_id"] / "canonical_row.json").is_file()
    ]
    if missing:
        print(json.dumps({"status": "PARTIAL", "remaining": len(missing)}))
        return 0
    rows = [
        _load(raw_root / task["task_id"] / "canonical_row.json")
        for task in schedule["tasks"]
    ]
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_full_bpc_rows.v1",
        "partition": args.stage, "row_count": len(rows),
        "execution_freeze": str(schedule_path),
        "execution_freeze_sha256": _sha(schedule_path),
        "single_host_instance": True, "rows": rows,
    }
    _write_once(output / "outcomes.json", payload)
    print(json.dumps({
        "status": "COMPLETE", "partition": args.stage,
        "row_count": len(rows), "output": str(output / "outcomes.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
