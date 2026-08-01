#!/usr/bin/env python3
"""Run one fixed-budget sparse-tail replay suite from natural Exact traces.

This runner is deliberately a development pilot, not an oracle or certificate
producer.  It freezes a deterministic, instance-diverse set of already
persisted root pricing contexts before launching any action.  Each selected
context receives exactly one fresh-process S1 and S4 replay, subject to a hard
per-action wall limit.  Resume is hash checked and cannot expand the frozen
context registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import perf_counter
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "scripts" / "replay_p0v4_sparse_tail_deviation.py"
REGISTRY_SCHEMA = "lunar_ice_bpc.sparse_tail_replay_registry.v1"
SUITE_SCHEMA = "lunar_ice_bpc.sparse_tail_replay_suite.v1"
SUPPORTED_ACTIONS = ("S1", "S4")
SUPPORTED_SOURCE_STATES = frozenset(
    {"FOUND_NEGATIVE", "CERTIFIED_NO_NEGATIVE"}
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-probe",
        action="append",
        default=[],
        help="Natural V5 probe.json; repeat for multiple instances.",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--context-limit", type=int, default=12)
    parser.add_argument("--max-contexts-per-instance", type=int, default=2)
    parser.add_argument("--minimum-source-proof-sec", type=float, default=10.0)
    parser.add_argument("--per-action-cap-sec", type=float, default=60.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.0)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.source_probe:
        parser.error("at least one --source-probe is required")
    if int(args.context_limit) < 1:
        parser.error("--context-limit must be positive")
    if int(args.max_contexts_per_instance) < 1:
        parser.error("--max-contexts-per-instance must be positive")
    if float(args.per_action_cap_sec) <= 0.0:
        parser.error("--per-action-cap-sec must be positive")

    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    registry_path = output / "context_registry.json"
    suite_path = output / "suite_manifest.json"
    probe_paths = tuple(
        sorted({_resolve(value).resolve() for value in args.source_probe})
    )
    for path in probe_paths:
        if not path.is_file():
            parser.error(f"source probe is missing: {path}")

    requested_binding = {
        "schema_version": REGISTRY_SCHEMA,
        "source_probes": [
            {"path": str(path), "sha256": _sha256(path)}
            for path in probe_paths
        ],
        "context_limit": int(args.context_limit),
        "max_contexts_per_instance": int(args.max_contexts_per_instance),
        "minimum_source_proof_sec": float(args.minimum_source_proof_sec),
        "actions": list(SUPPORTED_ACTIONS),
        "per_action_cap_sec": float(args.per_action_cap_sec),
        "memory_limit_gb": float(args.memory_limit_gb),
        "replay_script": str(REPLAY.resolve()),
        "replay_script_sha256": _sha256(REPLAY),
        "selection_policy": (
            "state_balanced_instance_round_robin_then_source_proof_desc_v1"
        ),
        "certificate_authority": "none",
    }
    requested_binding_hash = _stable_hash(requested_binding)
    if registry_path.exists():
        if not bool(args.resume):
            raise SystemExit(
                "context registry exists; use --resume or a fresh output directory"
            )
        registry = _load_json(registry_path)
        if str(registry.get("binding_hash") or "") != requested_binding_hash:
            raise SystemExit("resume binding differs from frozen context registry")
    else:
        contexts = select_contexts(
            discover_contexts(
                probe_paths,
                minimum_source_proof_sec=float(args.minimum_source_proof_sec),
            ),
            context_limit=int(args.context_limit),
            max_contexts_per_instance=int(args.max_contexts_per_instance),
        )
        if not contexts:
            raise SystemExit("no eligible natural sparse-tail contexts")
        registry = {
            **requested_binding,
            "binding_hash": requested_binding_hash,
            "status": "FROZEN_BEFORE_ACTIONS",
            "context_count": len(contexts),
            "contexts": contexts,
            "runtime_eligible": False,
            "formal_training_authorized": False,
            "evaluation_authorized": False,
            "deployment_authorized": False,
        }
        _write_json(registry_path, registry)

    native_build_dir = _resolve(args.native_build_dir).resolve()
    env = dict(os.environ)
    python_paths = [str(ROOT / "src")]
    if native_build_dir.is_dir():
        python_paths.append(str(native_build_dir))
    if env.get("PYTHONPATH"):
        python_paths.append(str(env["PYTHONPATH"]))
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    rows = []
    failures = 0
    for context in registry["contexts"]:
        context_id = str(context["context_id"])
        for action in SUPPORTED_ACTIONS:
            target = output / "replays" / context_id / f"{action}.json"
            existing = _valid_existing_replay(
                target,
                context=context,
                action=action,
            )
            if existing is not None:
                rows.append(existing)
                continue
            command = [
                sys.executable,
                str(REPLAY),
                "--probe",
                str(context["source_probe"]),
                "--instance",
                str(context["instance"]),
                "--round",
                str(context["round"]),
                "--action",
                action,
                "--output",
                str(target),
                "--wall-time-limit-sec",
                str(float(args.per_action_cap_sec)),
                "--memory-limit-gb",
                str(float(args.memory_limit_gb)),
            ]
            if bool(args.dry_run):
                rows.append(
                    {
                        "context_id": context_id,
                        "action": action,
                        "status": "DRY_RUN",
                        "command": command,
                    }
                )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            observed = _run_process(
                command,
                env=env,
                timeout_sec=float(args.per_action_cap_sec) + 45.0,
            )
            row = {
                "context_id": context_id,
                "action": action,
                "command": command,
                **observed,
            }
            replay = _valid_existing_replay(
                target,
                context=context,
                action=action,
            )
            if replay is None:
                failures += 1
                row["status"] = "REPLAY_VALIDATION_FAILED"
            else:
                row.update(replay)
            rows.append(row)
            _write_suite(
                suite_path,
                registry_path=registry_path,
                registry=registry,
                rows=rows,
                dry_run=bool(args.dry_run),
                failures=failures,
            )

    suite = _write_suite(
        suite_path,
        registry_path=registry_path,
        registry=registry,
        rows=rows,
        dry_run=bool(args.dry_run),
        failures=failures,
    )
    print(json.dumps(suite, indent=2, sort_keys=True))
    return 0 if not failures else 2


def discover_contexts(
    probe_paths: Iterable[Path],
    *,
    minimum_source_proof_sec: float,
) -> list[dict]:
    rows = []
    seen = set()
    for probe_path in sorted(Path(value).resolve() for value in probe_paths):
        probe = _load_json(probe_path)
        instance_value = str(
            probe.get("instance_path") or probe.get("instance") or ""
        )
        if not instance_value:
            continue
        instance_path = Path(instance_value).resolve()
        if not instance_path.is_file():
            continue
        instance_sha = _sha256(instance_path)
        instance_hash = str(
            probe.get("instance_content_hash")
            or probe.get("instance_id")
            or instance_sha[:16]
        )
        for raw in probe.get("history") or ():
            row = dict(raw)
            state = str(row.get("pricing_state") or "")
            proof_wall = float(
                row.get("labeling_final_judge_proof_pass_wall_time") or 0.0
            )
            dual = dict(row.get("dual_context") or {})
            node_id = str(row.get("node_id") or "root")
            if (
                state not in SUPPORTED_SOURCE_STATES
                or proof_wall < float(minimum_source_proof_sec)
                or node_id not in {"root", "node_000"}
                or bool(row.get("branch_context_active"))
                or not dict(dual.get("task_duals") or {})
                or bool(dict(dual.get("cut_duals") or {}))
                or not bool(row.get("final_judge_called"))
                or not bool(
                    row.get("labeling_final_judge_harvest_pass_attempted")
                )
            ):
                continue
            round_index = int(row.get("round") or 0)
            logical = {
                "source_probe_sha256": _sha256(probe_path),
                "instance_sha256": instance_sha,
                "round": round_index,
                "dual_fingerprint": str(
                    dual.get("dual_fingerprint") or ""
                ),
                "source_state": state,
            }
            context_id = _stable_hash(logical)
            if context_id in seen:
                continue
            seen.add(context_id)
            rows.append(
                {
                    "context_id": context_id,
                    "source_probe": str(probe_path),
                    "source_probe_sha256": logical["source_probe_sha256"],
                    "instance": str(instance_path),
                    "instance_sha256": instance_sha,
                    "instance_content_hash": instance_hash,
                    "scale": int(
                        probe.get("scale")
                        or probe.get("task_count")
                        or len(dual.get("task_duals") or {})
                    ),
                    "round": round_index,
                    "dual_fingerprint": logical["dual_fingerprint"],
                    "source_state": state,
                    "source_proof_wall_sec": proof_wall,
                    "source_raw_unique_negative_count": int(
                        row.get("raw_unique_negative_count") or 0
                    ),
                    "source_selected_diverse_negative_count": int(
                        row.get("selected_diverse_negative_count") or 0
                    ),
                }
            )
    return rows


def select_contexts(
    contexts: Iterable[dict],
    *,
    context_limit: int,
    max_contexts_per_instance: int,
) -> list[dict]:
    """Freeze a deterministic state-balanced, instance-diverse prefix."""

    by_instance: dict[str, list[dict]] = {}
    for row in contexts:
        by_instance.setdefault(str(row["instance_content_hash"]), []).append(
            dict(row)
        )
    for values in by_instance.values():
        values.sort(
            key=lambda row: (
                0 if row["source_state"] == "FOUND_NEGATIVE" else 1,
                -float(row["source_proof_wall_sec"]),
                int(row["round"]),
                str(row["context_id"]),
            )
        )
    ordered_instances = sorted(
        by_instance,
        key=lambda key: (
            -max(
                float(row["source_proof_wall_sec"])
                for row in by_instance[key]
            ),
            key,
        ),
    )
    selected = []
    counts = {key: 0 for key in ordered_instances}
    state_turn = ("FOUND_NEGATIVE", "CERTIFIED_NO_NEGATIVE")
    while len(selected) < int(context_limit):
        progressed = False
        for wanted_state in state_turn:
            for instance in ordered_instances:
                if counts[instance] >= int(max_contexts_per_instance):
                    continue
                candidates = [
                    row
                    for row in by_instance[instance]
                    if row["source_state"] == wanted_state
                    and row not in selected
                ]
                if not candidates:
                    continue
                selected.append(candidates[0])
                counts[instance] += 1
                progressed = True
                if len(selected) >= int(context_limit):
                    break
            if len(selected) >= int(context_limit):
                break
        if not progressed:
            break
    return selected


def _valid_existing_replay(
    path: Path,
    *,
    context: dict,
    action: str,
) -> dict | None:
    if not path.is_file():
        return None
    try:
        payload = _load_json(path)
    except Exception:
        return None
    if (
        str(payload.get("status") or "") != "SAFE_REPLAY_COMPLETE"
        or str(payload.get("action") or "") != str(action)
        or str(payload.get("source_probe_sha256") or "")
        != str(context["source_probe_sha256"])
        or str(payload.get("instance_sha256") or "")
        != str(context["instance_sha256"])
        or int(payload.get("source_round") or -1) != int(context["round"])
        or list((payload.get("safety") or {}).get("issues") or ())
    ):
        return None
    return {
        "status": "COMPLETED",
        "replay": str(path.resolve()),
        "replay_sha256": _sha256(path),
        "fresh_process_wall_sec": float(
            payload.get("fresh_process_wall_sec") or 0.0
        ),
        "engine_status": str(payload.get("engine_status") or ""),
        "true_negative_column_count": int(payload.get("column_count") or 0),
        "negative_escape_triggered": bool(
            payload.get("negative_escape_triggered")
        ),
        "memory_adverse_event": bool(
            (payload.get("telemetry") or {}).get("memory_pressure_triggered")
        ),
    }


def _run_process(
    command: list[str],
    *,
    env: dict[str, str],
    timeout_sec: float,
) -> dict:
    started = perf_counter()
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=float(timeout_sec))
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=3.0)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
    return {
        "returncode": int(process.returncode or 0),
        "timed_out": timed_out,
        "process_wall_sec": perf_counter() - started,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }


def _write_suite(
    path: Path,
    *,
    registry_path: Path,
    registry: dict,
    rows: list[dict],
    dry_run: bool,
    failures: int,
) -> dict:
    expected = int(registry["context_count"]) * len(SUPPORTED_ACTIONS)
    complete = sum(row.get("status") == "COMPLETED" for row in rows)
    payload = {
        "schema_version": SUITE_SCHEMA,
        "status": (
            "DRY_RUN"
            if dry_run
            else "COMPLETE"
            if complete == expected and failures == 0
            else "INCOMPLETE"
        ),
        "context_registry": str(registry_path.resolve()),
        "context_registry_sha256": _sha256(registry_path),
        "context_binding_hash": str(registry["binding_hash"]),
        "context_count": int(registry["context_count"]),
        "expected_action_count": expected,
        "completed_action_count": complete,
        "failure_count": int(failures),
        "rows": rows,
        "source_role": "mathematical_context_only",
        "formal_training_authorized": False,
        "evaluation_authorized": False,
        "deployment_authorized": False,
        "certificate_authority": "none",
        "next_step": (
            "build_once_train_once_then_run_fixed_heldout_pilot"
            if complete == expected and failures == 0
            else "resume_same_frozen_registry_only"
        ),
    }
    _write_json(path, payload)
    return payload


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


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
