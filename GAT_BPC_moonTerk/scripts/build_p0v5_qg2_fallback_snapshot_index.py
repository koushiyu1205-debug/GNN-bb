#!/usr/bin/env python3
"""Validate and index bounded P0V5 fallback snapshots for QG2 oracle replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    qg2_exact_action_policy_hash_from_snapshot,
)


SNAPSHOT_SCHEMA = "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
INDEX_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fallback_snapshot_index.v2"
TRAJECTORY_FEATURE_SEMANTICS = (
    "p0v5_qg2_preaction_trajectory_missingness.v2"
)
DEFAULT_SOURCE_BACKEND_ID = (
    "native_rcspp_bidirectional_root_partial_hybrid_v3"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--instance-root", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    parser.add_argument(
        "--source-backend-id",
        default=DEFAULT_SOURCE_BACKEND_ID,
    )
    parser.add_argument("--collection-freeze")
    parser.add_argument(
        "--require-exact-action-policy-hash",
        action="store_true",
    )
    args = parser.parse_args()

    snapshot_root = _resolve(args.snapshot_dir)
    output = _resolve(args.output)
    native_build_dir = _resolve(args.native_build_dir)
    sys.path.insert(0, str(native_build_dir))
    expected_engine_hash = spprc_engine_build_hash(
        str(args.source_backend_id)
    )
    collection_freeze = None
    collection_freeze_path = None
    if args.collection_freeze:
        collection_freeze_path = _resolve(args.collection_freeze)
        collection_freeze = _load(collection_freeze_path)
        _validate_collection_freeze(
            collection_freeze,
            snapshot_root=snapshot_root,
            native_build_dir=native_build_dir,
            source_backend_id=str(args.source_backend_id),
            expected_engine_hash=expected_engine_hash,
        )
    expected_exact_action_policy_hashes_by_scale = (
        _expected_exact_action_policy_hashes_by_scale(
            collection_freeze or {}
        )
    )
    exclusions = []
    validated = []
    for path in sorted(snapshot_root.glob("scale*/*/*.json")):
        try:
            payload = _load(path)
            scale = int(payload.get("scale") or 0)
            reason = _snapshot_exclusion(
                payload,
                expected_engine_hash=expected_engine_hash,
                require_exact_action_policy_hash=bool(
                    args.require_exact_action_policy_hash
                ),
                expected_exact_action_policy_hash=(
                    expected_exact_action_policy_hashes_by_scale.get(
                        scale, ""
                    )
                ),
            )
            if reason:
                exclusions.append({"path": str(path), "reason": reason})
                continue
            recorded_state = str(payload.get("state_hash") or "")
            unhashed = dict(payload)
            unhashed.pop("state_hash", None)
            if _stable_hash(unhashed) != recorded_state:
                raise ValueError("state_hash_mismatch")
            validated.append((path, payload))
        except Exception as exc:
            exclusions.append({
                "path": str(path),
                "reason": f"invalid_snapshot:{exc}",
            })
    target_instance_ids = {
        str(payload["instance_id"]) for _path, payload in validated
    }
    instance_index, duplicate_instance_paths = _instance_index(
        tuple(_resolve(value) for value in args.instance_root),
        target_instance_ids=target_instance_ids,
    )
    rows = []
    seen_states: dict[str, Path] = {}
    for path, payload in validated:
        try:
            recorded_state = str(payload.get("state_hash") or "")
            if recorded_state in seen_states:
                exclusions.append({
                    "path": str(path),
                    "reason": "duplicate_state_hash",
                    "first_path": str(seen_states[recorded_state]),
                })
                continue
            instance_hash = str(payload["instance_content_hash"])
            candidates = instance_index.get(instance_hash, ())
            if not candidates:
                raise ValueError("instance_content_hash_not_found")
            instance_path = candidates[0]
            seen_states[recorded_state] = path
            branch = dict(payload.get("branch_context") or {})
            cut = dict(payload.get("cut_context") or {})
            trajectory = dict(payload.get("trajectory_features") or {})
            scale = int(payload["scale"])
            escape_binding_explicit = all(
                key in payload
                for key in (
                    "exact_negative_escape_enabled",
                    "exact_admission_batch_size",
                    "exact_raw_negative_pool_size",
                    "exact_negative_escape_policy_id",
                )
            )
            admission_target = int(
                payload.get("exact_admission_batch_size")
                or (64 if scale == 30 else 128)
            )
            active_task_sets = tuple(
                tuple(str(task_id) for task_id in task_set)
                for task_set in payload.get("active_task_sets") or ()
            )
            active_signature_hashes = tuple(
                str(value)
                for value in payload.get(
                    "active_column_signature_hashes"
                ) or ()
            )
            exact_action_policy_hash = (
                qg2_exact_action_policy_hash_from_snapshot(payload)
            )
            recorded_action_policy_hash = str(
                payload.get("exact_action_policy_hash") or ""
            )
            if (
                recorded_action_policy_hash
                and recorded_action_policy_hash != exact_action_policy_hash
            ):
                raise ValueError("exact_action_policy_hash_mismatch")
            rows.append({
                "scale": scale,
                "instance_id": str(payload["instance_id"]),
                "instance_content_hash": instance_hash,
                "instance_hash": instance_hash,
                "instance_path": str(instance_path),
                "snapshot_path": str(path.resolve()),
                "snapshot_sha256": _sha256(path),
                "source_backend_id": str(args.source_backend_id),
                "source_engine_hash": str(payload["engine_hash"]),
                "source_config_hash": str(payload["config_hash"]),
                "source_exact_action_policy_hash": (
                    exact_action_policy_hash
                ),
                "source_state_hash": recorded_state,
                "state_hash": recorded_state,
                "round": payload.get("round"),
                "pricing_lifecycle_scope": str(
                    payload.get("pricing_lifecycle_scope") or ""
                ),
                "branch_pair_count": len(
                    tuple(branch.get("pair_decisions") or ())
                ),
                "active_cut_count": len(tuple(cut.get("cuts") or ())),
                "active_task_set_count": len(active_task_sets),
                "active_task_coverage_count": len({
                    task_id
                    for task_set in active_task_sets
                    for task_id in task_set
                }),
                "active_column_signature_count": len(
                    active_signature_hashes
                ),
                "admission_binding_complete": True,
                "v5_midpoint_reason": str(
                    payload.get("bidirectional_midpoint_fallback_reason")
                    or ""
                ),
                "previous_q0_wall_stratum": _wall_stratum(
                    trajectory.get("previous_proof_pass_wall_time")
                ),
                "negative_escape_binding_source": (
                    "snapshot_explicit"
                    if escape_binding_explicit
                    else "frozen_scale_compatible_inference"
                ),
                "exact_negative_escape_enabled": bool(
                    payload.get("exact_negative_escape_enabled", True)
                ),
                "exact_admission_batch_size": admission_target,
                "exact_raw_negative_pool_size": int(
                    payload.get("exact_raw_negative_pool_size")
                    or 4 * admission_target
                ),
                "exact_negative_escape_policy_id": str(
                    payload.get("exact_negative_escape_policy_id")
                    or "diverse_raw_4x_then_p0v4_selector_v1"
                ),
            })
        except Exception as exc:
            exclusions.append({
                "path": str(path),
                "reason": f"invalid_snapshot:{exc}",
            })

    rows.sort(
        key=lambda row: (
            int(row["scale"]),
            str(row["instance_content_hash"]),
            str(row["state_hash"]),
        )
    )
    coverage = {
        str(scale): {
            "context_count": sum(row["scale"] == scale for row in rows),
            "instance_count": len({
                row["instance_content_hash"]
                for row in rows if row["scale"] == scale
            }),
            "root_context_count": sum(
                row["scale"] == scale
                and row["pricing_lifecycle_scope"] == "root_cg"
                for row in rows
            ),
            "branch_or_cut_context_count": sum(
                row["scale"] == scale
                and (
                    row["branch_pair_count"] > 0
                    or row["active_cut_count"] > 0
                )
                for row in rows
            ),
        }
        for scale in (30, 50)
    }
    payload = {
        "schema_version": INDEX_SCHEMA,
        "development_only": True,
        "deployable": False,
        "bounded_oracle_context_limit": 300,
        "bounded_oracle_context_limit_per_scale": 150,
        "snapshot_dir": str(snapshot_root),
        "native_build_dir": str(native_build_dir),
        "source_backend_id": str(args.source_backend_id),
        "expected_engine_hash": expected_engine_hash,
        "collection_freeze": (
            None
            if collection_freeze_path is None
            else str(collection_freeze_path)
        ),
        "collection_freeze_sha256": (
            None
            if collection_freeze_path is None
            else _sha256(collection_freeze_path)
        ),
        "exact_action_policy_hash_required": bool(
            args.require_exact_action_policy_hash
        ),
        "expected_exact_action_policy_hashes_by_scale": {
            str(scale): digest
            for scale, digest in sorted(
                expected_exact_action_policy_hashes_by_scale.items()
            )
        },
        "observed_config_hashes": sorted({
            row["source_config_hash"] for row in rows
        }),
        "observed_exact_action_policy_hashes": sorted({
            row["source_exact_action_policy_hash"] for row in rows
        }),
        "instance_roots": [str(_resolve(value)) for value in args.instance_root],
        "coverage": coverage,
        "oracle_preflight_ready": all(
            coverage[str(scale)]["context_count"] >= 20
            and coverage[str(scale)]["instance_count"] >= 10
            for scale in (30, 50)
        ),
        "rows": rows,
        "excluded_count": len(exclusions),
        "exclusions": exclusions,
        "legacy_compatible_escape_binding_count": sum(
            row["negative_escape_binding_source"]
            == "frozen_scale_compatible_inference"
            for row in rows
        ),
        "duplicate_instance_paths": duplicate_instance_paths,
    }
    _write(output, payload)
    print(json.dumps({
        "coverage": coverage,
        "oracle_preflight_ready": payload["oracle_preflight_ready"],
        "output": str(output),
    }, sort_keys=True))
    return 0


def _snapshot_exclusion(
    payload: dict,
    *,
    expected_engine_hash: str = "",
    require_exact_action_policy_hash: bool = False,
    expected_exact_action_policy_hash: str = "",
) -> str:
    if str(payload.get("schema_version") or "") != SNAPSHOT_SCHEMA:
        return "schema_mismatch"
    if not bool(payload.get("development_only")) or bool(payload.get("deployable")):
        return "snapshot_not_development_only"
    if bool(payload.get("can_certify")) or bool(payload.get("mutates_p0")):
        return "snapshot_safety_contract_mismatch"
    if not bool(payload.get("proof_tail_fallback_context")):
        return "not_v5_fallback_context"
    if str(payload.get("trajectory_feature_semantics_version") or "") != (
        TRAJECTORY_FEATURE_SEMANTICS
    ):
        return "trajectory_feature_semantics_mismatch"
    if expected_engine_hash and str(payload.get("engine_hash") or "") != str(
        expected_engine_hash
    ):
        return "engine_hash_mismatch"
    if payload.get("active_task_sets") is None:
        return "active_task_sets_missing"
    if payload.get("active_column_signature_hashes") is None:
        return "active_column_signatures_missing"
    if len(payload.get("active_column_signature_hashes") or ()) != int(
        payload.get("active_column_count") or 0
    ):
        return "active_column_signature_count_mismatch"
    if int(payload.get("scale") or 0) not in {30, 50}:
        return "scale_outside_qg2"
    if str(payload.get("pricing_mode") or "") != "exact_proof":
        return "not_exact_proof"
    if str(payload.get("objective_mode") or "") != "official":
        return "nonofficial_objective"
    if require_exact_action_policy_hash:
        if str(payload.get("base_proof_queue_policy_id") or "") != "Q0":
            return "base_proof_queue_policy_not_explicit_q0"
        if not str(payload.get("exact_action_policy_hash") or ""):
            return "exact_action_policy_hash_missing"
    if expected_exact_action_policy_hash and str(
        payload.get("exact_action_policy_hash") or ""
    ) != expected_exact_action_policy_hash:
        return "exact_action_policy_hash_not_frozen_value"
    return ""


def _expected_exact_action_policy_hashes_by_scale(
    payload: dict,
) -> dict[int, str]:
    """Return the frozen exact-action contract for each QG2 scale.

    QG2 intentionally binds the admission milestone, so scale30
    ``(K=64,Q=256)`` and scale50 ``(K=128,Q=512)`` have different policy
    hashes.  The legacy scalar remains readable only for old single-policy
    collections; new two-scale freezes must provide the explicit mapping.
    """

    raw = dict(
        payload.get("required_exact_action_policy_hashes_by_scale") or {}
    )
    values = {
        int(scale): str(digest)
        for scale, digest in raw.items()
        if str(digest)
    }
    if values:
        return values
    legacy = str(payload.get("required_exact_action_policy_hash") or "")
    return {scale: legacy for scale in (30, 50)} if legacy else {}


def _validate_collection_freeze(
    payload: dict,
    *,
    snapshot_root: Path,
    native_build_dir: Path,
    source_backend_id: str,
    expected_engine_hash: str,
) -> None:
    if payload.get("schema_version") not in {
        "lunar_ice_bpc.p0v5_qg2_clean_collection_freeze.v1",
        "lunar_ice_bpc.p0v5_qg2_clean_collection_freeze.v2",
        "lunar_ice_bpc.p0v5_qg2_clean_collection_freeze.v3",
    }:
        raise SystemExit("QG2 collection freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("QG2 collection freeze safety contract mismatch")
    frozen_snapshot_dir = _resolve(str(payload.get("snapshot_dir") or ""))
    if frozen_snapshot_dir != snapshot_root:
        raise SystemExit("QG2 collection freeze snapshot directory mismatch")
    if str(payload.get("source_backend_id") or "") != source_backend_id:
        raise SystemExit("QG2 collection freeze source backend mismatch")
    if str(payload.get("source_engine_hash") or "") != expected_engine_hash:
        raise SystemExit("QG2 collection freeze source engine drift")

    frozen_files = (
        (
            ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py",
            "qg2_runtime_source_sha256",
        ),
        (
            ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py",
            "qg2_model_source_sha256",
        ),
        (
            _resolve(str(payload.get("selected_exact_config") or "")),
            "selected_exact_config_sha256",
        ),
        (
            _resolve(str(payload.get("development_corpus_manifest") or "")),
            "development_corpus_manifest_sha256",
        ),
    )
    for path, key in frozen_files:
        if not path.is_file() or _sha256(path) != str(payload.get(key) or ""):
            raise SystemExit(f"QG2 collection freeze file drift: {key}")
    native_extensions = tuple(sorted(
        native_build_dir.glob("lunar_spprc_native*.so")
    ))
    if len(native_extensions) != 1 or _sha256(native_extensions[0]) != str(
        payload.get("native_extension_sha256") or ""
    ):
        raise SystemExit("QG2 collection freeze Native extension drift")

    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
        qg2_runtime_implementation_hash,
    )

    if qg2_runtime_implementation_hash() != str(
        payload.get("qg2_runtime_implementation_hash") or ""
    ):
        raise SystemExit("QG2 collection freeze runtime implementation drift")


def _instance_index(
    roots: tuple[Path, ...],
    *,
    target_instance_ids: set[str],
):
    by_hash: dict[str, list[Path]] = {}
    hints = set()
    for instance_id in target_instance_ids:
        match = re.search(
            r"lunar_ice_sp50_(\d{3})_(\d{3})_",
            instance_id,
        )
        if match:
            hints.add((
                f"lunar_ice_sp50_{match.group(1)}",
                f"instance_{match.group(2)}_logical_graph.json",
            ))
    for root in roots:
        for path in sorted(root.rglob("*_logical_graph.json")):
            try:
                if hints and not any(
                    group in path.parts and path.name == filename
                    for group, filename in hints
                ):
                    continue
                raw = _load(path)
                if str(raw.get("instance_id") or "") not in target_instance_ids:
                    continue
                data = load_lunar_ice_data(raw)
            except Exception:
                continue
            by_hash.setdefault(data.instance_content_hash, []).append(
                path.resolve()
            )
    normalized = {
        key: tuple(sorted(set(values))) for key, values in by_hash.items()
    }
    duplicates = {
        key: [str(path) for path in values]
        for key, values in normalized.items()
        if len(values) > 1
    }
    return normalized, duplicates


def _wall_stratum(value) -> str:
    if value is None:
        return "missing"
    wall = max(0.0, float(value))
    if wall < 10.0:
        return "lt10"
    if wall < 60.0:
        return "10to60"
    if wall < 300.0:
        return "60to300"
    return "ge300"


def _stable_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
