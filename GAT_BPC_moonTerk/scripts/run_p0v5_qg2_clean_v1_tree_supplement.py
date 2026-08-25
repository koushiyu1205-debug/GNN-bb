#!/usr/bin/env python3
"""Run the pre-frozen, bounded real-tree QG2 snapshot supplement."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
PLAN = RUN_ROOT / "qg2_clean_v1_tree_supplement_freeze.json"
COLLECTION_FREEZE = RUN_ROOT / "qg2_clean_v1_collection_freeze.json"
SNAPSHOT_DIR = RUN_ROOT / "fallback_snapshots_qg2_clean_v1"
INDEX = RUN_ROOT / "qg2_clean_v1_live_snapshot_index.json"
STATE = RUN_ROOT / "qg2_clean_v1_tree_supplement_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    plan = _load(PLAN)
    _validate_plan(plan)
    commands = [
        _acceptance_command(
            scale=scale,
            instances=tuple(_resolve(value) for value in plan["selected_instances"][str(scale)]),
        )
        for scale in (30, 50)
    ]
    if args.dry_run:
        print(json.dumps({
            "status": "DRY_RUN_VALIDATED",
            "plan": str(PLAN),
            "commands": commands,
        }, sort_keys=True))
        return 0
    active = _active_pricing_or_collection_pids()
    if active:
        raise SystemExit(
            "tree supplement requires an idle single-Native machine; "
            f"active_pids={active}"
        )
    for scale, command in zip((30, 50), commands, strict=True):
        output_dir = _output_dir(scale)
        if output_dir.exists():
            raise SystemExit(
                f"tree supplement refuses implicit resume: {output_dir}"
            )
        _state("RUNNING", scale=scale)
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=_environment(),
            check=False,
        )
        if completed.returncode not in {0, 1}:
            _state("EXECUTION_ERROR", scale=scale, returncode=completed.returncode)
            return completed.returncode
        coverage = _build_index()
        _state("SCALE_COMPLETED", scale=scale, coverage=coverage)
    coverage = _build_index()
    branch_cut = sum(
        int((coverage.get(str(scale)) or {}).get("branch_or_cut_context_count") or 0)
        for scale in (30, 50)
    )
    status = "COMPLETED_WITH_BRANCH_CUT_CONTEXT" if branch_cut >= 1 else (
        "COMPLETED_NATURAL_BRANCH_CUT_OPPORTUNITY_ABSENT"
    )
    _state(status, coverage=coverage, expansion_permitted=False)
    return 0 if branch_cut >= 1 else 2


def _acceptance_command(*, scale: int, instances: tuple[Path, ...]) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config",
        str(ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"),
        "--scales",
        str(scale),
    ]
    for path in instances:
        command.extend(("--instance", str(path)))
    command.extend((
        "--limit", str(len(instances)),
        "--output-dir", str(_output_dir(scale)),
        "--no-resume",
    ))
    return command


def _output_dir(scale: int) -> Path:
    return RUN_ROOT / f"snapshot_collection_qg2_clean_v1_tree_scale{scale}"


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    # The supplement records the literal Q0 control trajectory.  Never inherit
    # a caller's deployment/evaluation manifest into collection.
    env.pop("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", None)
    env.pop("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", None)
    env.update({
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE": "15",
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR": str(SNAPSHOT_DIR),
        "PYTHONPATH": f"{ROOT / 'src'}:{BUILD}",
    })
    return env


def _build_index() -> dict:
    command = [
        sys.executable,
        str(ROOT / "scripts/build_p0v5_qg2_fallback_snapshot_index.py"),
        "--snapshot-dir", str(SNAPSHOT_DIR),
        "--instance-root", str(ROOT / "data/p0v5_qg2_oracle_development_v3"),
        "--output", str(INDEX),
        "--collection-freeze", str(COLLECTION_FREEZE),
        "--require-exact-action-policy-hash",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(), check=False
    )
    if completed.returncode != 0:
        raise SystemExit("tree supplement strict index validation failed")
    payload = _load(INDEX)
    if int(payload.get("excluded_count") or 0) != 0:
        raise SystemExit("tree supplement produced excluded snapshots")
    return dict(payload.get("coverage") or {})


def _validate_plan(plan: dict) -> None:
    schema = str(plan.get("schema_version") or "")
    if schema not in {
        "lunar_ice_bpc.p0v5_qg2_tree_supplement_freeze.v1",
        "lunar_ice_bpc.p0v5_qg2_tree_supplement_freeze.v2",
    }:
        raise SystemExit("tree supplement freeze schema mismatch")
    if not bool(plan.get("development_only")) or bool(plan.get("deployable")):
        raise SystemExit("tree supplement safety contract mismatch")
    expected = (
        (plan["selected_exact_config"], plan["selected_exact_config_sha256"]),
        (plan["development_corpus_manifest"], plan["development_corpus_manifest_sha256"]),
    )
    for raw_path, digest in expected:
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(digest):
            raise SystemExit(f"tree supplement frozen file drift: {path}")
    selected = plan.get("selected_instances") or {}
    if any(len(selected.get(str(scale)) or ()) != 5 for scale in (30, 50)):
        raise SystemExit("tree supplement requires exactly five frozen instances per scale")
    for scale in (30, 50):
        for value in selected[str(scale)]:
            path = _resolve(value)
            if not path.is_file() or f"scale_{scale:03d}" not in str(path):
                raise SystemExit(f"invalid frozen tree supplement instance: {path}")
    if schema.endswith(".v2"):
        collection_path = _resolve(plan.get("collection_freeze") or "")
        if (
            collection_path != COLLECTION_FREEZE.resolve()
            or not collection_path.is_file()
            or _sha256(collection_path)
            != str(plan.get("collection_freeze_sha256") or "")
        ):
            raise SystemExit("tree supplement collection freeze drift")
        collection = _load(collection_path)
        required = dict(
            plan.get("required_exact_action_policy_hashes_by_scale") or {}
        )
        if required != dict(collection.get(
            "required_exact_action_policy_hashes_by_scale"
        ) or {}):
            raise SystemExit(
                "tree supplement scale-aware action-policy mapping mismatch"
            )


def _active_pricing_or_collection_pids() -> list[int]:
    patterns = (
        "continue_p0v5_qg2_admission_v4_collection.py",
        "run_lunar_ice_compact_pricing_batch_probe.py",
        "run_lunar_ice_b4_2_cold_exact.py",
    )
    result = []
    own_pid = os.getpid()
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        pid = int(path.parent.name)
        if pid == own_pid:
            continue
        try:
            command = path.read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(pattern in command for pattern in patterns):
            result.append(pid)
    return sorted(result)


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_tree_supplement_state.v1",
        "status": status,
        "plan": str(PLAN),
        **extra,
    }
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
