#!/usr/bin/env python3
"""Run every authorized one-deviation context serially and resumably."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_RUNNER = ROOT / "scripts/run_p0v4_one_deviation_oracle.py"
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.one_deviation_rollout import (  # noqa: E402
    selected_exact_runtime_binding,
)
from lunar_ice_bpc.guidance.route_admission import (  # noqa: E402
    validate_route_opportunity_census_binding,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action-manifest-root", required=True)
    parser.add_argument("--opportunity-census", required=True)
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument(
        "--instance-root", action="append", required=True
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--promotion-arm-count", type=int, default=2)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--scale30-context-limit", type=int, default=20)
    parser.add_argument("--scale50-context-limit", type=int, default=20)
    parser.add_argument(
        "--scale",
        action="append",
        type=int,
        choices=(30, 50),
        help="May be repeated; restrict scheduled contexts to these scales.",
    )
    parser.add_argument(
        "--engineering-smoke",
        action="store_true",
        help=(
            "Run a bounded, non-trainable scale-local signal check when the "
            "joint scale30/50 opportunity gate is not yet open."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    action_root = _resolve(args.action_manifest_root)
    census_path = _resolve(args.opportunity_census)
    fixed_path = _resolve(args.fixed_k_selection)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    census = _load_json(census_path)
    fixed = _load_json(fixed_path)
    requested_scales = (
        {int(value) for value in args.scale}
        if args.scale
        else None
    )
    try:
        execution_scope = _suite_authorization_scope(
            census,
            requested_scales=requested_scales,
            engineering_smoke=bool(args.engineering_smoke),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if str(fixed.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("oracle suite requires frozen fixed E_K")
    try:
        census_binding_hash = (
            validate_route_opportunity_census_binding(
                census,
                fixed_k_selection_sha256=_sha256(fixed_path),
            )
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    eligible_snapshot_index = _eligible_snapshot_index(census)
    exact_runtime_bindings = {
        str(scale): selected_exact_runtime_binding(fixed, scale=scale)
        for scale in sorted(
            {
                int(row["scale"])
                for row in eligible_snapshot_index.values()
            }
        )
    }
    native_build_dir = _native_build_dir_for_bindings(
        exact_runtime_bindings
    )
    instances = _instance_index(
        tuple(_resolve(value) for value in args.instance_root)
    )
    manifest_records = []
    ignored_manifests = []
    seen_snapshot_hashes: set[str] = set()
    for path in sorted(action_root.rglob("*.json")):
        try:
            payload = _load_json(path)
            if not payload.get("source_snapshot") or not payload.get(
                "actions"
            ):
                continue
            snapshot_hash = str(payload.get("snapshot_hash") or "")
            authorized = eligible_snapshot_index.get(snapshot_hash)
            if authorized is None:
                raise ValueError(
                    "action manifest snapshot is not census-authorized"
                )
            if (
                str(payload.get("fixed_k_selection_sha256"))
                != _sha256(fixed_path)
            ):
                raise ValueError("action manifest/fixed E_K mismatch")
            if (
                str(payload.get("census_content_binding_hash"))
                != census_binding_hash
            ):
                raise ValueError("stale action manifest census binding")
            if str(payload.get("source_snapshot_sha256")) != str(
                authorized["source_snapshot_sha256"]
            ):
                raise ValueError(
                    "action manifest snapshot digest differs from census"
                )
            if Path(str(payload["source_snapshot"])).resolve() != Path(
                str(authorized["source_snapshot"])
            ).resolve():
                raise ValueError(
                    "action manifest snapshot path differs from census"
                )
            if str(payload.get("instance_content_hash")) != str(
                authorized["instance_content_hash"]
            ):
                raise ValueError(
                    "action manifest instance differs from census"
                )
            if snapshot_hash in seen_snapshot_hashes:
                raise ValueError("duplicate action manifest snapshot")
            seen_snapshot_hashes.add(snapshot_hash)
            manifest_records.append(
                {
                    "path": path,
                    "scale": int(authorized["scale"]),
                    "instance_content_hash": str(
                        authorized["instance_content_hash"]
                    ),
                    "snapshot_hash": snapshot_hash,
                }
            )
        except Exception as exc:
            ignored_manifests.append(
                {"path": str(path.resolve()), "reason": repr(exc)}
            )
    if requested_scales is not None:
        manifest_records = [
            row
            for row in manifest_records
            if int(row["scale"]) in requested_scales
        ]
    authorized_manifest_count = len(manifest_records)
    available_context_count_by_scale = _count_records_by_scale(
        manifest_records
    )
    context_limits_by_scale = {
        30: max(0, int(args.scale30_context_limit)),
        50: max(0, int(args.scale50_context_limit)),
    }
    manifest_records = _stratified_manifest_records(
        manifest_records,
        limits_by_scale=context_limits_by_scale,
    )
    if args.limit:
        manifest_records = manifest_records[: max(0, int(args.limit))]
    manifests = [Path(record["path"]) for record in manifest_records]
    rows = []
    failures = 0
    for action_path in manifests:
        action = _load_json(action_path)
        snapshot_path = Path(str(action["source_snapshot"])).resolve()
        snapshot = _load_json(snapshot_path)
        instance_hash = str(snapshot["instance_content_hash"])
        instance_path = instances.get(instance_hash)
        if instance_path is None:
            rows.append(
                {
                    "action_manifest": str(action_path.resolve()),
                    "instance_content_hash": instance_hash,
                    "status": "INSTANCE_NOT_FOUND",
                }
            )
            failures += 1
            continue
        context_hash = str(snapshot["snapshot_hash"])
        context_output = output / f"scale_{int(snapshot['scale']):03d}" / context_hash
        package = context_output / "one_deviation_rollout_package.json"
        if args.resume and _rollout_package_reusable(
            package,
            census_sha256=_sha256(census_path),
            census_content_binding_hash=census_binding_hash,
            fixed_k_sha256=_sha256(fixed_path),
            source_snapshot_sha256=_sha256(snapshot_path),
            required_promotion_arm_count=max(
                2, int(args.promotion_arm_count)
            ),
            engineering_smoke=bool(args.engineering_smoke),
        ):
            rows.append(
                {
                    "action_manifest": str(action_path.resolve()),
                    "context_output": str(context_output.resolve()),
                    "package": str(package.resolve()),
                    "package_sha256": _sha256(package),
                    "status": "REUSED",
                }
            )
            continue
        command = [
            sys.executable,
            str(CONTEXT_RUNNER),
            "--action-manifest",
            str(action_path),
            "--opportunity-census",
            str(census_path),
            "--fixed-k-selection",
            str(fixed_path),
            "--instance",
            str(instance_path),
            "--output-dir",
            str(context_output),
            "--promotion-arm-count",
            str(max(2, int(args.promotion_arm_count))),
        ]
        if bool(args.engineering_smoke):
            command.append("--engineering-smoke")
        row = {
            "action_manifest": str(action_path.resolve()),
            "instance": str(instance_path.resolve()),
            "context_output": str(context_output.resolve()),
            "command": command,
            "status": "DRY_RUN" if args.dry_run else "RUNNING",
        }
        if not args.dry_run:
            budget = 300.0 if int(snapshot["scale"]) == 50 else 120.0
            arm_count = 1 + max(2, int(args.promotion_arm_count))
            row.update(
                _run_observed(
                    command,
                    context_output=context_output,
                    timeout_sec=(
                        3.0 * arm_count * (budget + 120.0) + 120.0
                    ),
                    native_build_dir=native_build_dir,
                )
            )
            if int(row["returncode"]) == 0 and package.is_file():
                row.update(
                    {
                        "status": "COMPLETED",
                        "package": str(package.resolve()),
                        "package_sha256": _sha256(package),
                    }
                )
            else:
                row["status"] = "FAILED"
                failures += 1
        rows.append(row)
        _write_json(output / "suite_rows.json", rows)
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_one_deviation_oracle_suite.v1"
        ),
        **execution_scope,
        "status": (
            "DRY_RUN"
            if args.dry_run
            else "COMPLETE" if failures == 0 else "COMPLETE_WITH_FAILURES"
        ),
        "opportunity_census": str(census_path.resolve()),
        "opportunity_census_sha256": _sha256(census_path),
        "fixed_k_selection": str(fixed_path.resolve()),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "context_count": len(rows),
        "failure_count": failures,
        "discovered_action_manifest_count": (
            authorized_manifest_count + len(ignored_manifests)
        ),
        "authorized_action_manifest_count": authorized_manifest_count,
        "scheduled_action_manifest_count": len(manifests),
        "promotion_arm_count_per_context": max(
            2, int(args.promotion_arm_count)
        ),
        "available_context_count_by_scale": (
            available_context_count_by_scale
        ),
        "scheduled_context_count_by_scale": _count_records_by_scale(
            manifest_records
        ),
        "context_limits_by_scale": {
            str(key): value
            for key, value in sorted(context_limits_by_scale.items())
        },
        "context_selection_policy": (
            "scale_then_instance_round_robin_snapshot_hash_v1"
        ),
        "requested_scales": (
            sorted(requested_scales)
            if requested_scales is not None
            else sorted(
                int(value)
                for value in available_context_count_by_scale
            )
        ),
        "ignored_action_manifests": ignored_manifests,
        "census_content_binding_hash": census_binding_hash,
        "large_scale_concurrency": 1,
        "fresh_process_per_arm": True,
        "native_build_dir": str(native_build_dir.resolve()),
        "exact_runtime_bindings": exact_runtime_bindings,
        "rows": rows,
    }
    _write_json(output / "suite_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if args.dry_run:
        return 0
    return 0 if failures == 0 and rows else 3


def _stratified_manifest_records(
    records: list[dict],
    *,
    limits_by_scale: dict[int, int],
) -> list[dict]:
    """Select contexts round-robin so prolific instances cannot dominate."""

    selected = []
    scales = sorted({int(record["scale"]) for record in records})
    for scale in scales:
        by_instance: dict[str, list[dict]] = {}
        for record in records:
            if int(record["scale"]) != scale:
                continue
            by_instance.setdefault(
                str(record["instance_content_hash"]), []
            ).append(record)
        for values in by_instance.values():
            values.sort(
                key=lambda value: (
                    str(value["snapshot_hash"]),
                    str(value["path"]),
                )
            )
        instance_hashes = sorted(by_instance)
        limit = int(limits_by_scale.get(scale, 0))
        available = sum(len(values) for values in by_instance.values())
        target = available if limit <= 0 else min(limit, available)
        scale_selected = []
        while len(scale_selected) < target:
            progress = False
            for instance_hash in instance_hashes:
                queue = by_instance[instance_hash]
                if not queue:
                    continue
                scale_selected.append(queue.pop(0))
                progress = True
                if len(scale_selected) >= target:
                    break
            if not progress:
                break
        selected.extend(scale_selected)
    return selected


def _suite_authorization_scope(
    census: dict,
    *,
    requested_scales: set[int] | None,
    engineering_smoke: bool,
) -> dict:
    joint_authorized = bool(census.get("expensive_oracle_authorized"))
    if joint_authorized and not engineering_smoke:
        return {
            "execution_scope": "formal_joint_scale_oracle",
            "engineering_smoke_only": False,
            "gat_training_authorized": True,
            "formal_claim_authorized": True,
        }
    if not engineering_smoke:
        raise ValueError("opportunity census did not authorize suite")
    scales = set(requested_scales or ())
    if not scales:
        raise ValueError(
            "engineering smoke requires at least one explicit --scale"
        )
    audit_scales = dict(
        dict(census.get("audit") or {}).get("scales") or {}
    )
    failed = [
        scale
        for scale in sorted(scales)
        if not bool(dict(audit_scales.get(str(scale)) or {}).get("gate_pass"))
    ]
    if failed:
        raise ValueError(
            "engineering smoke scale opportunity gate failed: "
            + ",".join(str(value) for value in failed)
        )
    return {
        "execution_scope": "engineering_smoke_scale_gate_only",
        "engineering_smoke_only": True,
        "gat_training_authorized": False,
        "formal_claim_authorized": False,
    }


def _count_records_by_scale(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(int(record["scale"]))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda value: int(value[0])))


def _rollout_package_reusable(
    path: Path,
    *,
    census_sha256: str,
    census_content_binding_hash: str,
    fixed_k_sha256: str,
    source_snapshot_sha256: str,
    required_promotion_arm_count: int,
    engineering_smoke: bool,
) -> bool:
    if not path.is_file():
        return False
    try:
        payload = _load_json(path)
    except Exception:
        return False
    return bool(
        str(payload.get("schema_version"))
        == "lunar_ice_bpc.one_deviation_rollout_package.v1"
        and str(payload.get("opportunity_census_sha256"))
        == str(census_sha256)
        and str(payload.get("census_content_binding_hash"))
        == str(census_content_binding_hash)
        and str(payload.get("fixed_k_selection_sha256"))
        == str(fixed_k_sha256)
        and str(payload.get("source_snapshot_sha256"))
        == str(source_snapshot_sha256)
        and len(tuple(payload.get("selected_action_ids") or ()))
        == 1 + max(2, int(required_promotion_arm_count))
        and bool(payload.get("engineering_smoke_only"))
        == bool(engineering_smoke)
        and bool(payload.get("gat_training_authorized"))
        == (not bool(engineering_smoke))
        and bool(
            dict(payload.get("validation") or {}).get(
                "validation_pass"
            )
        )
    )


def _eligible_snapshot_index(census: dict) -> dict[str, dict]:
    rows = [
        dict(value)
        for value in census.get("eligible_snapshots", ())
    ]
    result = {}
    for row in rows:
        snapshot_hash = str(row.get("snapshot_hash") or "")
        if (
            not snapshot_hash
            or not str(row.get("source_snapshot_sha256") or "")
            or not str(row.get("instance_content_hash") or "")
        ):
            raise SystemExit(
                "opportunity census has an incomplete snapshot index"
            )
        if snapshot_hash in result:
            raise SystemExit(
                "opportunity census has duplicate snapshot hashes"
            )
        result[snapshot_hash] = row
    if len(result) != int(census.get("eligible_snapshot_count") or 0):
        raise SystemExit(
            "opportunity census snapshot index count mismatch"
        )
    return result


def _instance_index(roots: tuple[Path, ...]) -> dict[str, Path]:
    result = {}
    for path in sorted(
        {
            value.resolve()
            for root in roots
            for value in root.rglob("instance_*_logical_graph.json")
        }
    ):
        try:
            data = load_lunar_ice_data(
                json.loads(path.read_text(encoding="utf-8"))
            )
        except Exception:
            continue
        current = result.setdefault(data.instance_content_hash, path)
        if current != path:
            raise SystemExit(
                "duplicate instance content hash at different paths"
            )
    return result


def _run_observed(
    command: list[str],
    *,
    context_output: Path,
    timeout_sec: float,
    native_build_dir: Path,
) -> dict:
    context_output.mkdir(parents=True, exist_ok=True)
    stdout_path = context_output / "suite_stdout.log"
    stderr_path = context_output / "suite_stderr.log"
    environment = dict(os.environ)
    pythonpath = [
        str(ROOT / "src"),
        str(native_build_dir.resolve()),
    ]
    if environment.get("PYTHONPATH"):
        pythonpath.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath)
    started = monotonic()
    peak_rss = 0
    termination_reason = ""
    with stdout_path.open("w", encoding="utf-8") as stdout, (
        stderr_path.open("w", encoding="utf-8")
    ) as stderr:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        while process.poll() is None:
            peak_rss = max(
                peak_rss, _process_tree_rss_bytes(process.pid)
            )
            if monotonic() - started >= timeout_sec:
                termination_reason = "ORACLE_SUITE_OUTER_DEADLINE"
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10.0)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5.0)
                break
            sleep(1.0)
        returncode = int(process.wait())
    return {
        "returncode": returncode,
        "wall_time_sec": monotonic() - started,
        "peak_process_tree_rss_gb": peak_rss / (1024.0**3),
        "termination_reason": termination_reason,
        "stdout": str(stdout_path.resolve()),
        "stderr": str(stderr_path.resolve()),
    }


def _native_build_dir_for_bindings(
    bindings: dict[str, dict],
) -> Path:
    backend_ids = {
        str(binding.get("backend_id") or "")
        for binding in bindings.values()
    }
    if not backend_ids or "" in backend_ids:
        raise SystemExit("oracle suite Exact backend binding is incomplete")
    build_dir = (
        ROOT / "build/native-spprc-bidirectional-feasibility-v1"
        if any("bidirectional" in value for value in backend_ids)
        else ROOT / "build/native-spprc-memory-opt-v2"
    )
    if not build_dir.is_dir() or not any(
        build_dir.glob("lunar_spprc_native*.so")
    ):
        raise SystemExit(
            f"oracle suite Native build is unavailable: {build_dir}"
        )
    return build_dir.resolve()


def _process_tree_rss_bytes(root_pid: int) -> int:
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            fields = (entry / "status").read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except OSError:
            continue
        parent = 0
        resident = 0
        for line in fields:
            if line.startswith("PPid:"):
                parent = int(line.split()[1])
            elif line.startswith("VmRSS:"):
                resident = int(line.split()[1]) * 1024
        children.setdefault(parent, []).append(pid)
        rss[pid] = resident
    total = 0
    stack = [int(root_pid)]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss.get(pid, 0)
        stack.extend(children.get(pid, ()))
    return total


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
