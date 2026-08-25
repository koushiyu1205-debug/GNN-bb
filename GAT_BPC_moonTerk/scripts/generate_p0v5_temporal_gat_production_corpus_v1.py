#!/usr/bin/env python3
"""Generate and freeze the outcome-blind 80+80 real-map temporal-GAT corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.real_instance import generate_real_map_instance  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.io.instance_io import validate_instance, write_json  # noqa: E402


DEFAULT_CONFIG = (
    ROOT / "configs/experiments/p0v5_temporal_gat_production_v1.json"
)
TIME_WINDOW_MODES = ("outer_to_inner", "inner_to_outer", "easy_to_hard")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--task-limit", type=int)
    parser.add_argument("--raw-map-dir", type=Path, default=ROOT / "data/raw_maps")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = _load(config_path)
    corpus_root = (ROOT / config["corpus_root"]).resolve()
    corpus_root.mkdir(parents=True, exist_ok=True)
    manifest_path = corpus_root / "corpus.freeze.json"
    if manifest_path.exists():
        _verify_frozen(config_path, corpus_root, manifest_path)
        print(json.dumps({"status": "ALREADY_FROZEN", "manifest": str(manifest_path)}))
        return 0

    protected, protected_audit = _protected_hashes(corpus_root)
    rows = _existing_rows(corpus_root, protected, config)
    completed = {(int(row["scale"]), int(row["index"])) for row in rows}
    limit = None if args.task_limit is None else max(0, int(args.task_limit))
    generated = 0
    for scale in map(int, config["scales"]):
        for index in range(1, int(config["instances_per_scale"]) + 1):
            if (scale, index) in completed:
                continue
            if limit is not None and generated >= limit:
                _write_state(corpus_root, config, rows, "PARTIAL")
                print(json.dumps({"status": "PARTIAL", "generated": generated,
                                  "row_count": len(rows)}, sort_keys=True))
                return 0
            checkpoint_root = (
                corpus_root / "generation_checkpoints"
                / f"scale_{scale:03d}" / f"instance_{index:03d}"
            )
            payload, data, seed, seed_attempt, rejection_audit = (
                _generate_accepted_instance(
                    config=config, scale=scale, index=index,
                    raw_map_dir=args.raw_map_dir.resolve(),
                    checkpoint_root=checkpoint_root, protected=protected,
                )
            )
            directory = corpus_root / f"scale_{scale:03d}"
            target = directory / f"instance_{index:03d}_logical_graph.json"
            # Publish a generated instance only after a complete temporary
            # file can be parsed and validated.  A killed generator may leave
            # a ``.partial`` file, but can never expose a truncated JSON file
            # as a resumable corpus row.
            temporary = target.with_suffix(target.suffix + ".partial")
            if not temporary.exists():
                write_json(temporary, payload)
            published_payload = _load(temporary)
            published_issues = validate_instance(published_payload)
            published_data = load_lunar_ice_data(published_payload)
            rejection_reasons = list(published_issues[:8])
            if not bool(dict(
                published_payload.get("validation") or {}
            ).get("accepted")):
                rejection_reasons.append("validation.accepted is false")
            # Raster metadata legitimately contains JSON NaN (for example a
            # GeoTIFF nodata value).  Direct Python container equality treats
            # NaN as unequal to itself, so compare canonical JSON encodings
            # instead of rejecting a byte-for-byte reproducible round trip.
            if _canonical_payload_sha256(published_payload) != (
                _canonical_payload_sha256(payload)
            ):
                rejection_reasons.append("canonical payload mismatch")
            if published_data.instance_content_hash != data.instance_content_hash:
                rejection_reasons.append("instance content hash mismatch")
            if rejection_reasons:
                raise SystemExit(
                    f"temporary generated instance drift/rejection scale={scale} "
                    f"index={index}:" + ";".join(rejection_reasons)
                )
            os.replace(temporary, target)
            row = {
                "scale": scale,
                "index": index,
                "seed": seed,
                "seed_attempt": seed_attempt,
                "time_window_mode": TIME_WINDOW_MODES[(index - 1) % 3],
                "path": str(target.relative_to(ROOT)),
                "file_sha256": _sha256(target),
                "instance_content_hash": data.instance_content_hash,
                "generation_rejection_audit_path": (
                    str(rejection_audit.relative_to(ROOT))
                    if rejection_audit is not None else None
                ),
                "generation_rejection_audit_sha256": (
                    _sha256(rejection_audit)
                    if rejection_audit is not None else None
                ),
            }
            rows.append(row)
            completed.add((scale, index))
            protected.add(data.instance_content_hash)
            generated += 1
            _write_state(corpus_root, config, rows, "GENERATING")

    expected = len(config["scales"]) * int(config["instances_per_scale"])
    if len(rows) != expected:
        raise SystemExit(f"corpus row count mismatch:{len(rows)} != {expected}")
    hashes = [str(row["instance_content_hash"]) for row in rows]
    if len(hashes) != len(set(hashes)):
        raise SystemExit("fresh corpus contains duplicate content hashes")
    final_protected, final_protected_audit = _protected_hashes(corpus_root)
    if (
        final_protected_audit != protected_audit
        or any(value in final_protected for value in hashes)
    ):
        raise SystemExit(
            "protected historical inventory changed during corpus generation"
        )
    _assign_splits(rows, config)
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_corpus.v1",
        "status": "FROZEN_BEFORE_QUEUE_OUTCOMES",
        "experiment_id": config["experiment_id"],
        "source_config": str(config_path),
        "source_config_sha256": _sha256(config_path),
        "generator": "lunar_ice_bpc.domain.real_instance.generate_real_map_instance",
        "driver_source_sha256": _sha256(Path(__file__).resolve()),
        "generator_source_sha256": _sha256(
            ROOT / "src/lunar_ice_bpc/domain/real_instance.py"
        ),
        "real_map_source_sha256": _sha256(
            ROOT / "src/lunar_ice_bpc/domain/real_maps.py"
        ),
        "real_map_generation": config["real_map_generation"],
        "split_assignment": "scale_then_sha256_content_hash_v1",
        "official_or_historical_overlap_count": 0,
        "protected_history_audit": protected_audit,
        "row_count": len(rows),
        "rows": sorted(rows, key=lambda row: (row["scale"], row["index"])),
    }
    _write_once(manifest_path, payload)
    _write_state(corpus_root, config, rows, "FROZEN")
    print(json.dumps({"status": "FROZEN", "manifest": str(manifest_path),
                      "row_count": len(rows)}, sort_keys=True))
    return 0


def _assign_splits(rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    counts = dict(config["split_counts_by_scale"])
    order = ("train", "calibration", "development_e2e", "sealed_final")
    for scale in map(int, config["scales"]):
        selected = sorted(
            (row for row in rows if int(row["scale"]) == scale),
            key=lambda row: hashlib.sha256(
                f"temporal-v1-split:{scale}:{row['instance_content_hash']}".encode()
            ).hexdigest(),
        )
        cursor = 0
        for partition in order:
            target = int(counts[partition])
            for row in selected[cursor:cursor + target]:
                row["partition"] = partition
            cursor += target
        if cursor != len(selected):
            raise SystemExit(f"split count mismatch for scale{scale}")


def _generate_accepted_instance(
    *, config: dict[str, Any], scale: int, index: int,
    raw_map_dir: Path, checkpoint_root: Path, protected: set[str],
):
    policy = _generation_retry_policy(config)
    rejections: list[dict[str, Any]] = []
    for attempt in range(policy["maximum_attempts"]):
        seed = _generation_seed(config, scale, index, attempt)
        checkpoint_dir = (
            checkpoint_root if attempt == 0
            else checkpoint_root / f"retry_{attempt:03d}"
        )
        payload = generate_real_map_instance(
            scale, raw_map_dir=raw_map_dir, seed=seed, index=index,
            time_window_mode=TIME_WINDOW_MODES[(index - 1) % 3],
            output_cells=int(config["real_map_generation"]["output_cells"]),
            edge_generation_mode=str(
                config["real_map_generation"]["edge_generation_mode"]
            ),
            edge_checkpoint_dir=checkpoint_dir,
        )
        issues = list(validate_instance(payload))
        accepted = bool(dict(payload.get("validation") or {}).get("accepted"))
        data = None
        if not issues and accepted:
            data = load_lunar_ice_data(payload)
            if data.instance_content_hash in protected:
                issues.append("instance_content_hash overlaps protected history")
        if not issues and accepted and data is not None:
            audit_path = None
            if rejections:
                audit_path = checkpoint_root / "rejected_attempts.audit.json"
                _write_atomic(audit_path, {
                    "schema_version": (
                        "lunar_ice_bpc.temporal_gat_generation_rejections.v1"
                    ),
                    "scale": scale,
                    "index": index,
                    "retry_policy": policy,
                    "accepted_attempt": attempt,
                    "accepted_seed": seed,
                    "rejected_attempts": rejections,
                })
            return payload, data, seed, attempt, audit_path
        rejection = {
            "attempt": attempt,
            "seed": seed,
            "validation_accepted": accepted,
            "reasons": issues[:32] or ["validation.accepted is false"],
        }
        rejections.append(rejection)
        _write_atomic(checkpoint_root / "rejected_attempts.audit.json", {
            "schema_version": (
                "lunar_ice_bpc.temporal_gat_generation_rejections.v1"
            ),
            "scale": scale,
            "index": index,
            "retry_policy": policy,
            "accepted_attempt": None,
            "accepted_seed": None,
            "rejected_attempts": rejections,
        })
    raise SystemExit(
        f"generated instance exhausted deterministic retries scale={scale} "
        f"index={index}:" + ";".join(rejections[-1]["reasons"][:8])
    )


def _generation_retry_policy(config: dict[str, Any]) -> dict[str, Any]:
    policy = dict(config.get("generation_retry") or {})
    maximum_attempts = int(policy.get("maximum_attempts") or 1)
    seed_stride = int(policy.get("seed_stride") or 0)
    if (
        maximum_attempts < 1
        or seed_stride <= int(config["instances_per_scale"])
        or policy.get(
            "retry_only_on_instance_validation_or_protected_hash_rejection"
        ) is not True
    ):
        raise SystemExit("invalid outcome-blind generation retry contract")
    return {
        "maximum_attempts": maximum_attempts,
        "seed_stride": seed_stride,
        "retry_only_on_instance_validation_or_protected_hash_rejection": True,
    }


def _generation_seed(
    config: dict[str, Any], scale: int, index: int, attempt: int
) -> int:
    policy = _generation_retry_policy(config)
    if not 0 <= attempt < policy["maximum_attempts"]:
        raise ValueError("generation seed attempt outside frozen retry contract")
    return (
        int(config["seed_base_by_scale"][str(scale)]) + int(index)
        + int(attempt) * policy["seed_stride"]
    )


def _generation_seed_attempt(
    config: dict[str, Any], scale: int, index: int, seed: int
) -> int:
    policy = _generation_retry_policy(config)
    delta = int(seed) - (
        int(config["seed_base_by_scale"][str(scale)]) + int(index)
    )
    if delta < 0 or delta % policy["seed_stride"]:
        raise SystemExit("existing corpus seed is outside retry subranges")
    attempt = delta // policy["seed_stride"]
    if attempt >= policy["maximum_attempts"]:
        raise SystemExit("existing corpus seed attempt exceeds retry contract")
    return attempt


def _protected_hashes(corpus_root: Path) -> tuple[set[str], dict[str, Any]]:
    cache_path = corpus_root / "protected_history_hashes.cache.json"
    # Protect every persisted historical/official instance under both data/
    # and runs/, not only the current official acceptance tree.  A handful of
    # generation-audit and self-check instances live under runs/ and must not
    # disappear from the no-overlap proof merely because they were not copied
    # into data/.  The active corpus itself is the sole excluded subtree.
    paths = sorted({
        path
        for base in (ROOT / "data", ROOT / "runs")
        for path in base.rglob("*logical_graph.json")
        if corpus_root not in path.parents
    })
    inventory = [{
        "path": str(path.relative_to(ROOT)),
        "size": int(path.stat().st_size),
        "mtime_ns": int(path.stat().st_mtime_ns),
    } for path in paths]
    inventory_sha256 = hashlib.sha256(json.dumps(
        inventory, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    rows = None
    cache_build_audit: dict[str, Any] = {}
    if cache_path.is_file():
        cached = _load(cache_path)
        if cached.get("inventory_sha256") == inventory_sha256:
            rows = list(cached.get("rows") or ())
            cache_build_audit = dict(cached.get("cache_build_audit") or {})
    if rows is None:
        reusable, reusable_cache_sha256 = _best_reusable_protected_rows(
            corpus_root, paths
        )
        rows = []
        parsed_row_count = 0
        for path in paths:
            relative = str(path.relative_to(ROOT))
            if relative in reusable:
                rows.append({
                    "path": relative,
                    "instance_content_hash": reusable[relative],
                })
                continue
            try:
                rows.append({
                    "path": relative,
                    "instance_content_hash": load_lunar_ice_data(
                        _load(path)
                    ).instance_content_hash,
                })
                parsed_row_count += 1
            except Exception as exc:
                raise SystemExit(
                    f"cannot audit protected instance {path}:{exc}"
                ) from exc
        cache_build_audit = {
            "reused_row_count": len(reusable),
            "parsed_row_count": parsed_row_count,
            "reused_from_cache_sha256": reusable_cache_sha256,
        }
        _write_atomic(cache_path, {
            "schema_version": (
                "lunar_ice_bpc.temporal_gat_protected_history_cache.v1"
            ),
            "inventory_sha256": inventory_sha256,
            "file_count": len(paths),
            "cache_build_audit": cache_build_audit,
            "rows": rows,
        })
    if len(rows) != len(paths) or {
        str(row["path"]) for row in rows
    } != {str(row["path"]) for row in inventory}:
        raise SystemExit("protected history cache coverage mismatch")
    values = {str(row["instance_content_hash"]) for row in rows}
    return values, {
        "cache_path": str(cache_path.relative_to(ROOT)),
        "cache_sha256": _sha256(cache_path),
        "inventory_sha256": inventory_sha256,
        "file_count": len(paths),
        "inventory_roots": ["data", "runs"],
        "unique_content_hash_count": len(values),
        "cache_build_audit": cache_build_audit,
    }


def _best_reusable_protected_rows(
    corpus_root: Path, current_paths: list[Path]
) -> tuple[dict[str, str], str | None]:
    """Reuse only a cache bound by a frozen corpus and unchanged inventory."""
    current_relative = {
        str(path.relative_to(ROOT)): path for path in current_paths
    }
    best: dict[str, str] = {}
    best_cache_sha256 = None
    for manifest_path in sorted((ROOT / "data").glob("*/corpus.freeze.json")):
        if manifest_path.parent.resolve() == corpus_root.resolve():
            continue
        try:
            manifest = _load(manifest_path)
            if (
                manifest.get("schema_version")
                    != "lunar_ice_bpc.p0v5_temporal_gat_corpus.v1"
                or manifest.get("status")
                    != "FROZEN_BEFORE_QUEUE_OUTCOMES"
            ):
                continue
            audit = dict(manifest.get("protected_history_audit") or {})
            candidate_path = ROOT / str(audit.get("cache_path") or "")
            if (
                not candidate_path.is_file()
                or _sha256(candidate_path) != audit.get("cache_sha256")
            ):
                continue
            candidate = _load(candidate_path)
            candidate_rows = list(candidate.get("rows") or ())
            relative_paths = [str(row.get("path") or "") for row in candidate_rows]
            if (
                len(candidate_rows) != int(candidate.get("file_count") or -1)
                or len(relative_paths) != len(set(relative_paths))
                or not set(relative_paths).issubset(current_relative)
                or any(not str(row.get("instance_content_hash") or "")
                       for row in candidate_rows)
            ):
                continue
            candidate_inventory = [{
                "path": relative,
                "size": int(current_relative[relative].stat().st_size),
                "mtime_ns": int(current_relative[relative].stat().st_mtime_ns),
            } for relative in sorted(relative_paths)]
            candidate_inventory_sha256 = hashlib.sha256(json.dumps(
                candidate_inventory, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            if (
                candidate_inventory_sha256
                    != candidate.get("inventory_sha256")
                or candidate_inventory_sha256
                    != audit.get("inventory_sha256")
            ):
                continue
            if len(candidate_rows) > len(best):
                best = {
                    str(row["path"]): str(row["instance_content_hash"])
                    for row in candidate_rows
                }
                best_cache_sha256 = _sha256(candidate_path)
        except (OSError, ValueError, TypeError):
            continue
    return best, best_cache_sha256


def _existing_rows(
    corpus_root: Path, protected: set[str], config: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(corpus_root.glob("scale_*/instance_*_logical_graph.json")):
        payload = _load(path)
        data = load_lunar_ice_data(payload)
        if data.instance_content_hash in protected:
            raise SystemExit(f"existing corpus row overlaps protected data:{path}")
        scale = int(payload["scale"])
        index = int(path.stem.split("_")[1])
        seed = int(payload.get("seed") or 0)
        seed_attempt = _generation_seed_attempt(config, scale, index, seed)
        expected_seed = _generation_seed(config, scale, index, seed_attempt)
        expected_mode = TIME_WINDOW_MODES[(index - 1) % len(TIME_WINDOW_MODES)]
        scheduling = dict(payload.get("scheduling") or {})
        resource_map = dict(payload.get("resource_map") or {})
        generation = dict(config["real_map_generation"])
        if (
            scale not in {int(value) for value in config["scales"]}
            or not 1 <= index <= int(config["instances_per_scale"])
            or seed != expected_seed
            or str(scheduling.get("time_window_mode") or "") != expected_mode
            or list(resource_map.get("grid_shape") or ()) != [
                int(generation["output_cells"]), int(generation["output_cells"])
            ]
            or abs(float(resource_map.get("resolution_m") or 0.0) - 100.0)
                > 1.0e-12
            or str(resource_map.get("edge_generation_mode") or "")
                != str(generation["edge_generation_mode"])
            or not bool(dict(payload.get("validation") or {}).get("accepted"))
        ):
            raise SystemExit(f"existing corpus generation contract drift:{path}")
        rejection_audit = (
            corpus_root / "generation_checkpoints"
            / f"scale_{scale:03d}" / f"instance_{index:03d}"
            / "rejected_attempts.audit.json"
        )
        if seed_attempt > 0:
            if not rejection_audit.is_file():
                raise SystemExit(
                    f"existing retry row lacks rejection audit:{path}"
                )
            rejection_payload = _load(rejection_audit)
            if (
                int(rejection_payload.get("accepted_attempt") or -1)
                    != seed_attempt
                or int(rejection_payload.get("accepted_seed") or -1) != seed
                or len(rejection_payload.get("rejected_attempts") or ())
                    != seed_attempt
            ):
                raise SystemExit(
                    f"existing retry row rejection audit drift:{path}"
                )
        elif rejection_audit.exists():
            raise SystemExit(
                f"primary-seed row unexpectedly has rejection audit:{path}"
            )
        rows.append({
            "scale": scale,
            "index": index,
            "seed": seed,
            "seed_attempt": seed_attempt,
            "time_window_mode": expected_mode,
            "path": str(path.relative_to(ROOT)),
            "file_sha256": _sha256(path),
            "instance_content_hash": data.instance_content_hash,
            "generation_rejection_audit_path": (
                str(rejection_audit.relative_to(ROOT))
                if seed_attempt > 0 else None
            ),
            "generation_rejection_audit_sha256": (
                _sha256(rejection_audit) if seed_attempt > 0 else None
            ),
        })
        protected.add(data.instance_content_hash)
    return rows


def _verify_frozen(config_path: Path, root: Path, manifest_path: Path) -> None:
    manifest = _load(manifest_path)
    if manifest.get("status") != "FROZEN_BEFORE_QUEUE_OUTCOMES":
        raise SystemExit("corpus freeze status drift")
    if manifest.get("source_config_sha256") != _sha256(config_path):
        raise SystemExit("corpus config hash drift")
    if manifest.get("driver_source_sha256") != _sha256(
        Path(__file__).resolve()
    ):
        raise SystemExit("corpus driver source hash drift")
    protected = dict(manifest.get("protected_history_audit") or {})
    cache = ROOT / str(protected.get("cache_path") or "")
    if not cache.is_file() or _sha256(cache) != protected.get("cache_sha256"):
        raise SystemExit("protected history cache drift")
    for row in manifest.get("rows") or ():
        path = ROOT / row["path"]
        if not path.is_file() or _sha256(path) != row["file_sha256"]:
            raise SystemExit(f"frozen corpus file drift:{path}")


def _write_state(root: Path, config: dict[str, Any], rows: list[dict[str, Any]], status: str) -> None:
    _write_atomic(root / "generation_state.json", {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_generation_state.v1",
        "experiment_id": config["experiment_id"],
        "status": status,
        "generated_rows": len(rows),
        "target_rows": len(config["scales"]) * int(config["instances_per_scale"]),
    })


def _load(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_payload_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _write_once(path: Path, payload: object) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable artifact drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
