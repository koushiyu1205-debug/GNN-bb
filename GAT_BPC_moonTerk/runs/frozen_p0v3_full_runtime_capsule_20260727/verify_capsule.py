#!/usr/bin/env python3
"""Verify and optionally smoke-test the immutable P0 V3 runtime capsule."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile


DEFAULT_CAPSULE_DIR = (
    Path(__file__).resolve().parents[1]
    / "runs"
    / "frozen_p0v3_full_runtime_capsule_20260727"
)
INNER_MANIFEST = (
    "GAT_BPC_moonTerk/metadata/capsule_manifest.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capsule-dir", type=Path, default=DEFAULT_CAPSULE_DIR
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    capsule = args.capsule_dir.resolve()
    manifest_path = capsule / "capsule_manifest.json"
    issues: list[str] = []
    if not manifest_path.is_file():
        raise SystemExit(f"missing manifest: {manifest_path}")
    outer = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive = capsule / str((outer.get("archive") or {}).get("path") or "")
    if not archive.is_file():
        issues.append("archive_missing")
        archive_sha = ""
    else:
        archive_sha = sha256_file(archive)
        if archive_sha != (outer.get("archive") or {}).get("sha256"):
            issues.append("archive_sha256_mismatch")

    inner: dict = {}
    archive_rows: dict[str, dict] = {}
    if archive.is_file():
        inner, archive_rows, archive_issues = audit_archive(archive)
        issues.extend(archive_issues)
        if inner.get("capsule_id") != outer.get("capsule_id"):
            issues.append("inner_outer_capsule_id_mismatch")
        if inner.get("content_bundle_hash") != outer.get(
            "content_bundle_hash"
        ):
            issues.append("inner_outer_content_hash_mismatch")

    smoke_result: dict = {"executed": False}
    if args.smoke and not issues:
        smoke_result, smoke_issues = run_smoke(archive, inner)
        issues.extend(smoke_issues)
    result = {
        "schema_version": (
            "lunar_ice_bpc.p0v3_runtime_capsule.v1.verification"
        ),
        "capsule_id": outer.get("capsule_id"),
        "valid": not issues,
        "issues": sorted(set(issues)),
        "archive_sha256": archive_sha,
        "content_file_count": len(archive_rows),
        "smoke": smoke_result,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not issues else 1


def audit_archive(
    archive: Path,
) -> tuple[dict, dict[str, dict], list[str]]:
    issues: list[str] = []
    payloads: dict[str, bytes] = {}
    seen: set[str] = set()
    with tarfile.open(archive, mode="r:gz") as handle:
        for member in handle.getmembers():
            name = member.name
            path = PurePosixPath(name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or name in seen
                or not member.isfile()
            ):
                issues.append(f"unsafe_or_duplicate_member:{name}")
                continue
            seen.add(name)
            extracted = handle.extractfile(member)
            if extracted is None:
                issues.append(f"member_unreadable:{name}")
                continue
            payloads[name] = extracted.read()
    if INNER_MANIFEST not in payloads:
        return {}, {}, issues + ["inner_manifest_missing"]
    inner = json.loads(payloads[INNER_MANIFEST].decode("utf-8"))
    expected_rows = {
        str(row["path"]): dict(row)
        for row in inner.get("content_files") or []
    }
    actual_content = {
        name: payload
        for name, payload in payloads.items()
        if name != INNER_MANIFEST
    }
    if set(expected_rows) != set(actual_content):
        missing = sorted(set(expected_rows) - set(actual_content))
        extra = sorted(set(actual_content) - set(expected_rows))
        issues.extend(f"content_missing:{name}" for name in missing)
        issues.extend(f"content_extra:{name}" for name in extra)
    for name, row in expected_rows.items():
        payload = actual_content.get(name)
        if payload is None:
            continue
        if sha256_bytes(payload) != row.get("sha256"):
            issues.append(f"content_sha256_mismatch:{name}")
        expected_size = row.get("size_bytes")
        if expected_size is None or len(payload) != int(expected_size):
            issues.append(f"content_size_mismatch:{name}")
    if stable_payload_hash(list(inner.get("content_files") or [])) != inner.get(
        "content_bundle_hash"
    ):
        issues.append("inner_content_bundle_hash_mismatch")
    return inner, expected_rows, issues


def run_smoke(archive: Path, inner: dict) -> tuple[dict, list[str]]:
    issues: list[str] = []
    expected = dict(inner.get("smoke") or {})
    with tempfile.TemporaryDirectory(prefix="p0v3-capsule-verify-") as raw:
        base = Path(raw)
        with tarfile.open(archive, mode="r:gz") as handle:
            handle.extractall(base, filter="data")
        project = base / str(inner["project_prefix"])
        output = base / "smoke_output"
        frozen_native = (
            project
            / "runs"
            / "frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725"
            / "native"
        )
        command = [
            sys.executable,
            str(
                project
                / "scripts"
                / "run_lunar_ice_native_spprc_acceptance.py"
            ),
            "--config",
            str(project / "configs" / "native_live_sri_p0_full120_v1.yaml"),
            "--scales",
            "5",
            "--instance",
            str(project / "data" / "instances" / "lunar_ice_sp50_005"
                / "instance_001_logical_graph.json"),
            "--output-dir",
            str(output),
            "--no-resume",
        ]
        environment = sanitized_environment()
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(project / "src"), str(frozen_native))
        )
        completed = subprocess.run(
            command,
            cwd=project,
            env=environment,
            text=True,
            capture_output=True,
            timeout=120.0,
            check=False,
        )
        if completed.returncode != 0:
            issues.append(f"smoke_returncode:{completed.returncode}")
        summary_path = output / "native_spprc_acceptance_summary.json"
        state_path = output / "scale_005" / "b4_2_cold_exact_state.json"
        if not summary_path.is_file():
            issues.append("smoke_summary_missing")
            summary = {}
        else:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not state_path.is_file():
            issues.append("smoke_state_missing")
            row = {}
        else:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            rows = list(state.get("rows") or [])
            row = rows[0] if len(rows) == 1 else {}
            if len(rows) != 1:
                issues.append(f"smoke_row_count:{len(rows)}")
        if row.get("algorithm_status") != expected.get(
            "expected_algorithm_status"
        ):
            issues.append("smoke_algorithm_status_mismatch")
        if row.get("certificate_scope") != expected.get(
            "expected_certificate_scope"
        ):
            issues.append("smoke_certificate_scope_mismatch")
        if row.get("exact_certificate") is not True:
            issues.append("smoke_exact_certificate_false")
        if row.get("no_cheat_pass") is not True:
            issues.append("smoke_no_cheat_failed")
        tree_path = Path(str(row.get("tree_result_json") or ""))
        if not tree_path.is_file():
            issues.append("smoke_tree_result_missing")
            tree = {}
        else:
            tree = json.loads(tree_path.read_text(encoding="utf-8"))
        if tree.get("exact_status") != expected.get("expected_exact_status"):
            issues.append("smoke_exact_status_mismatch")
        objective = tree.get("incumbent_objective")
        target = expected.get("expected_objective")
        tolerance = float(expected.get("objective_tolerance") or 0.0)
        if (
            objective is None
            or target is None
            or abs(float(objective) - float(target)) > tolerance
        ):
            issues.append("smoke_objective_mismatch")
        return {
            "executed": True,
            "returncode": completed.returncode,
            "acceptance_row_status": (
                ((summary.get("rows") or [{}])[0]).get("status")
            ),
            "algorithm_status": row.get("algorithm_status"),
            "exact_status": tree.get("exact_status"),
            "certificate_scope": row.get("certificate_scope"),
            "objective": objective,
            "stdout_tail": completed.stdout[-1000:],
            "stderr_tail": completed.stderr[-1000:],
        }, issues


def sanitized_environment() -> dict[str, str]:
    blocked = {
        "LUNAR_ICE_ADAPTIVE_TAIL_HARVEST_MAX",
        "LUNAR_ICE_ADAPTIVE_TAIL_HARVEST_TRIGGER_SEC",
        "LUNAR_ICE_DEVELOPMENT_ORACLE_TASK_PRIORITY_JSON",
        "LUNAR_ICE_DUAL_CENTER_TRAJECTORY_COLLECTION",
        "LUNAR_ICE_EXPERIMENTAL_PROOF_QUEUE_POLICY",
        "LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE",
    }
    return {
        key: value
        for key, value in os.environ.items()
        if key not in blocked and not key.startswith("LUNAR_ICE_GAT_")
    }


def stable_payload_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
