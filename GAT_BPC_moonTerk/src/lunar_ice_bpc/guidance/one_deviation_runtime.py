"""Opt-in runtime adapter for the calibrated one-deviation GAT."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from math import log1p
import os
from pathlib import Path
from threading import Lock
from time import perf_counter_ns
from typing import Any, Mapping, Sequence

import torch

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.one_deviation import (
    ONE_DEVIATION_RELATIONAL_CONTEXT_SCHEMA,
    OneDeviationDecision,
    OneDeviationLedger,
    TwoHeadOneDeviationGAT,
    augment_one_deviation_candidate_contexts,
    select_one_deviation,
)
from lunar_ice_bpc.guidance.tensorization import (
    build_static_graph_features,
    dynamic_node_features,
)
from lunar_ice_bpc.guidance.route_admission import (
    fixed_exact_admission_batch_size,
)
from lunar_ice_bpc.guidance.one_deviation_rollout import (
    selected_exact_runtime_binding,
)


ONE_DEVIATION_MANIFEST_ENV = "LUNAR_ICE_ONE_DEVIATION_MANIFEST"
ONE_DEVIATION_EVALUATION_ENV = (
    "LUNAR_ICE_ONE_DEVIATION_EVALUATION_MODE"
)
ONE_DEVIATION_RUNTIME_POLICY_ID = (
    "one_deviation_full_audited_p0_prefix_v1"
)
_LOCK = Lock()
_CACHE: dict[str, tuple[dict, TwoHeadOneDeviationGAT]] = {}
_LEDGER = OneDeviationLedger()


def infer_one_deviation_from_environment(
    *,
    request,
    ordered_candidates: Sequence[Mapping[str, Any]],
    batch_size: int,
    root_key: str,
    adverse_memory_event: bool = False,
) -> tuple[OneDeviationDecision, dict[str, Any]]:
    """Infer one bounded promotion; every validation issue returns no-op."""

    manifest_value = str(
        os.getenv(ONE_DEVIATION_MANIFEST_ENV, "")
    ).strip()
    inference_started_ns: int | None = None
    if not manifest_value:
        return OneDeviationDecision(reason="runtime_not_configured"), {
            "one_deviation_runtime_enabled": False
        }
    try:
        manifest_path = Path(manifest_value).resolve()
        manifest, model = _load_model(manifest_path)
        if str(manifest.get("runtime_implementation_hash") or "") != (
            one_deviation_runtime_implementation_hash()
        ):
            raise ValueError("one-deviation runtime implementation drift")
        evaluation_mode = str(
            os.getenv(ONE_DEVIATION_EVALUATION_ENV, "0")
        ).strip().lower() in {"1", "true", "yes", "on"}
        if not bool(manifest.get("deployment_authorized")) and not (
            evaluation_mode
            and bool(manifest.get("evaluation_authorized"))
        ):
            raise ValueError(
                "manifest did not authorize deployment or held-out evaluation"
            )
        if str(manifest.get("runtime_policy_id") or "") != (
            ONE_DEVIATION_RUNTIME_POLICY_ID
        ):
            raise ValueError("one-deviation runtime policy mismatch")
        if int(request.data.scale) not in {
            int(value)
            for value in manifest.get("allowed_scales", ())
        }:
            raise ValueError("scale is outside the trained deployment scope")
        current_engine_hash = str(
            getattr(request, "engine_hash", "") or ""
        )
        current_config_hash = str(
            getattr(request, "config_hash", "") or ""
        )
        allowed_engine_hashes = {
            str(value)
            for value in manifest.get(
                "allowed_exact_engine_hashes", ()
            )
        }
        allowed_binary_hashes = {
            str(value)
            for value in manifest.get(
                "allowed_exact_binary_hashes", ()
            )
        }
        if (
            not current_engine_hash
            or current_engine_hash not in allowed_engine_hashes
            or current_engine_hash not in allowed_binary_hashes
        ):
            raise ValueError("exact engine/binary hash mismatch")
        if (
            not current_config_hash
            or current_config_hash
            not in {
                str(value)
                for value in manifest.get(
                    "training_exact_config_hashes", ()
                )
            }
        ):
            raise ValueError("exact config hash mismatch")
        fixed_k = json.loads(
            Path(manifest["fixed_k_selection"]).read_text(
                encoding="utf-8"
            )
        )
        if _sha256(Path(manifest["fixed_k_selection"])) != str(
            manifest["fixed_k_selection_sha256"]
        ):
            raise ValueError("fixed-K selection hash mismatch")
        expected_batch_size = fixed_exact_admission_batch_size(
            fixed_k, scale=int(request.data.scale)
        )
        if expected_batch_size != int(batch_size):
            raise ValueError("runtime batch size differs from frozen E_K")
        exact_runtime = selected_exact_runtime_binding(
            fixed_k,
            scale=int(request.data.scale),
        )
        exact_runtime_hash = str(
            exact_runtime["runtime_binding_hash"]
        )
        if exact_runtime_hash not in {
            str(value)
            for value in manifest.get(
                "allowed_exact_runtime_binding_hashes", ()
            )
        }:
            raise ValueError("exact runtime binding hash is not trained")
        manifest_runtime = dict(
            dict(
                manifest.get("exact_runtime_bindings_by_scale") or {}
            ).get(str(int(request.data.scale)))
            or {}
        )
        if manifest_runtime != exact_runtime:
            raise ValueError(
                "deployment manifest exact runtime binding mismatch"
            )
        _validate_exact_runtime_environment(exact_runtime)
        candidate_rows = tuple(ordered_candidates)
        omitted = candidate_rows[
            int(batch_size) : int(batch_size) + 32
        ]
        if len(omitted) < 8:
            return OneDeviationDecision(
                reason="fewer_than_eight_omitted_candidates"
            ), {
                "one_deviation_runtime_enabled": True,
                "one_deviation_fallback_to_noop": True,
            }
        rank_offsets = tuple(
            int(value)
            for value in manifest.get("deployment_rank_offsets", ())
        )
        if (
            not rank_offsets
            or len(rank_offsets) != len(set(rank_offsets))
            or any(value < 1 or value > 32 for value in rank_offsets)
        ):
            raise ValueError(
                "deployment rank-offset scope is invalid"
            )
        scoped = tuple(
            (offset, omitted[offset - 1])
            for offset in rank_offsets
            if offset <= len(omitted)
        )
        if len(scoped) != len(rank_offsets):
            raise ValueError(
                "deployment rank-offset scope exceeds omitted window"
            )
        inference_started_ns = perf_counter_ns()
        tensors, feature_payload = _tensorize_request(
            request,
            tuple(row for _offset, row in scoped),
            candidate_rank_offsets=tuple(
                offset for offset, _row in scoped
            ),
            selected_candidates=candidate_rows[: int(batch_size)],
        )
        feature_schema = _runtime_feature_schema(tensors)
        if stable_payload_hash(feature_schema) != str(
            manifest.get("feature_schema_hash") or ""
        ):
            raise ValueError("one-deviation feature schema mismatch")
        ood = not _within_feature_envelope(
            feature_payload,
            dict(manifest.get("feature_envelope") or {}),
        )
        with torch.no_grad():
            outputs = model(**tensors)
        input_hash = stable_payload_hash(feature_payload)
        calibration = dict(manifest["calibration"])
        decision = select_one_deviation(
            candidate_ids=tuple(
                str(row["candidate_id"])
                for _offset, row in scoped
            ),
            candidate_ranks=tuple(
                int(batch_size) + offset
                for offset, _row in scoped
            ),
            positive_probabilities=tuple(
                float(value)
                for value in outputs[
                    "positive_probability"
                ].tolist()
            ),
            conditional_positive_relative_gains=tuple(
                float(value)
                for value in outputs[
                    "conditional_positive_relative_gain"
                ].tolist()
            ),
            batch_size=int(batch_size),
            probability_threshold=float(
                calibration["probability_threshold"]
            ),
            expected_relative_gain_threshold=float(
                calibration["expected_relative_gain_threshold"]
            ),
            root_key=str(root_key),
            ledger=_LEDGER,
            context_hash=input_hash,
            expected_context_hash=input_hash,
            model_hash=str(manifest["checkpoint_sha256"]),
            expected_model_hash=_sha256(Path(manifest["checkpoint"])),
            calibration_gate_pass=bool(calibration["gate_pass"]),
            ood=ood,
            adverse_memory_event=bool(
                adverse_memory_event
                or str(
                    os.getenv(
                        "LUNAR_ICE_ONE_DEVIATION_MEMORY_ADVERSE_EVENT",
                        "0",
                    )
                ).strip().lower()
                in {"1", "true", "yes", "on"}
            ),
        )
        return decision, {
            "one_deviation_runtime_enabled": True,
            "one_deviation_evaluation_mode": evaluation_mode,
            "one_deviation_manifest": str(manifest_path),
            "one_deviation_manifest_sha256": _sha256(manifest_path),
            "one_deviation_checkpoint_sha256": str(
                manifest["checkpoint_sha256"]
            ),
            "one_deviation_input_hash": input_hash,
            "one_deviation_exact_engine_hash": (
                current_engine_hash
            ),
            "one_deviation_request_config_hash": str(
                current_config_hash
            ),
            "one_deviation_exact_runtime_binding_hash": (
                exact_runtime_hash
            ),
            "one_deviation_deployment_rank_offsets": list(
                rank_offsets
            ),
            "one_deviation_feature_schema_hash": (
                stable_payload_hash(feature_schema)
            ),
            "one_deviation_ood": ood,
            "one_deviation_decision_reason": decision.reason,
            "one_deviation_probability": (
                decision.probability_positive
            ),
            "one_deviation_expected_relative_gain": (
                decision.expected_positive_relative_gain
            ),
            "one_deviation_inference_wall_ms": (
                (perf_counter_ns() - inference_started_ns) / 1_000_000.0
            ),
        }
    except Exception as exc:
        return OneDeviationDecision(
            reason="runtime_validation_failed"
        ), {
            "one_deviation_runtime_enabled": True,
            "one_deviation_fallback_to_noop": True,
            "one_deviation_runtime_error": repr(exc),
            "one_deviation_inference_wall_ms": (
                None
                if inference_started_ns is None
                else (
                    perf_counter_ns() - inference_started_ns
                )
                / 1_000_000.0
            ),
        }


def _validate_exact_runtime_environment(
    runtime: Mapping[str, Any],
    *,
    environment: Mapping[str, str] | None = None,
) -> None:
    """Fail closed unless deployment is running under the labelled Exact V5."""

    values = os.environ if environment is None else environment
    expected_strings = {
        "LUNAR_ICE_SPPRC_EXACT_BACKEND": str(runtime["backend_id"]),
        "LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES": str(
            int(runtime["graph_cache_entries"])
        ),
        "LUNAR_ICE_SPPRC_COMPLETION_BOUND": _bool_text(
            runtime["completion_bound_enabled"]
        ),
        "LUNAR_ICE_SPPRC_SUBSET_DOMINANCE": _bool_text(
            runtime["subset_dominance_enabled"]
        ),
        "LUNAR_ICE_SPPRC_CUT_STATE": _bool_text(
            runtime["cut_state_enabled"]
        ),
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED": _bool_text(
            runtime["negative_escape_enabled"]
        ),
        "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED": _bool_text(
            runtime["batch_master_admission_enabled"]
        ),
        "LUNAR_ICE_LABELING_WORKER_NG_SIZES": ",".join(
            str(int(value))
            for value in runtime["worker_ng_sizes"]
        ),
        "LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST": _bool_text(
            runtime["exact_final_judge_first"]
        ),
        "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY": str(
            runtime["final_judge_pass_policy"]
        ),
    }
    mismatches = []
    for key, expected in expected_strings.items():
        actual = str(values.get(key, "")).strip()
        if actual != expected:
            mismatches.append(f"{key}={actual!r},expected={expected!r}")
    float_key = "LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC"
    try:
        actual_float = float(str(values.get(float_key, "")).strip())
    except ValueError:
        actual_float = float("nan")
    if actual_float != float(runtime["worker_hard_time_cap_sec"]):
        mismatches.append(
            f"{float_key}={values.get(float_key)!r},expected="
            f"{float(runtime['worker_hard_time_cap_sec'])!r}"
        )
    adaptive_key = (
        "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC"
    )
    expected_adaptive = runtime.get("adaptive_harvest_cap_sec")
    actual_adaptive = str(values.get(adaptive_key, "")).strip()
    if expected_adaptive is None:
        if actual_adaptive:
            mismatches.append(
                f"{adaptive_key}={actual_adaptive!r},expected=unset"
            )
    else:
        try:
            adaptive_matches = (
                float(actual_adaptive) == float(expected_adaptive)
            )
        except ValueError:
            adaptive_matches = False
        if not adaptive_matches:
            mismatches.append(
                f"{adaptive_key}={actual_adaptive!r},expected="
                f"{float(expected_adaptive)!r}"
            )
    if mismatches:
        raise ValueError(
            "selected Exact runtime environment mismatch: "
            + ";".join(mismatches)
        )


def _bool_text(value: Any) -> str:
    return "1" if bool(value) else "0"


@lru_cache(maxsize=1)
def one_deviation_runtime_implementation_hash() -> str:
    """Bind the learned policy to its inference and integration sources."""

    package_root = Path(__file__).resolve().parents[1]
    sources = (
        package_root / "guidance/one_deviation.py",
        package_root / "guidance/one_deviation_runtime.py",
        package_root / "guidance/tensorization.py",
        package_root / "exact/bpc/pricing/harvest.py",
        package_root / "exact/bpc/solver/pricing_tail_solver.py",
    )
    digest = hashlib.sha256()
    for path in sources:
        if not path.is_file():
            raise ValueError(f"one-deviation runtime source is missing: {path}")
        digest.update(str(path.relative_to(package_root)).encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _load_model(
    manifest_path: Path,
) -> tuple[dict, TwoHeadOneDeviationGAT]:
    manifest_hash = _sha256(manifest_path)
    with _LOCK:
        cached = _CACHE.get(manifest_hash)
        if cached is not None:
            return cached
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        checkpoint_path = Path(manifest["checkpoint"]).resolve()
        if _sha256(checkpoint_path) != str(
            manifest["checkpoint_sha256"]
        ):
            raise ValueError("checkpoint hash mismatch")
        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=True
        )
        dimensions = dict(checkpoint["dimensions"])
        model = TwoHeadOneDeviationGAT(**dimensions)
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        model.eval()
        _CACHE.clear()
        _CACHE[manifest_hash] = (manifest, model)
        return manifest, model


def _runtime_feature_schema(
    tensors: Mapping[str, torch.Tensor],
) -> dict[str, Any]:
    return {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_feature_schema.v1"
        ),
        "node_input_dim": int(tensors["node_features"].shape[1]),
        "edge_input_dim": int(tensors["edge_features"].shape[1]),
        "candidate_context_dim": int(
            tensors["candidate_context"].shape[1]
        ),
        "global_context_dim": int(
            tensors["global_context"].shape[0]
        ),
        "candidate_context_schema": [
            "true_reduced_cost",
            "would_change_active_support",
            "is_new_task_set",
            "task_fraction",
            *ONE_DEVIATION_RELATIONAL_CONTEXT_SCHEMA,
        ],
        "global_context_schema": [
            "log1p_memory_limit_bytes",
            "log1p_remaining_wall_time_sec",
            "reserved_0",
            "reserved_1",
        ],
    }


def _tensorize_request(
    request,
    candidates: Sequence[Mapping[str, Any]],
    *,
    candidate_rank_offsets: Sequence[int],
    selected_candidates: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    static = build_static_graph_features(request.data)
    dynamic = dynamic_node_features(request)
    node_features = [
        [*static_row, *dynamic_row]
        for static_row, dynamic_row in zip(
            static.node_features, dynamic, strict=True
        )
    ]
    edge_features = [list(row) for row in static.arc_features]
    node_index = {
        node_id: index
        for index, node_id in enumerate(static.node_ids)
    }
    def mask_for(row: Mapping[str, Any]) -> list[float]:
        mask = [0.0] * len(static.node_ids)
        task_ids = tuple(str(value) for value in row["task_ids"])
        for task_id in task_ids:
            mask[node_index[task_id]] = 1.0
        return mask

    masks = [mask_for(row) for row in candidates]
    selected_masks = [mask_for(row) for row in selected_candidates]
    candidate_context = augment_one_deviation_candidate_contexts(
        candidate_task_masks=masks,
        candidate_contexts=[
            [float(value) for value in row["context"]]
            for row in candidates
        ],
        candidate_rank_offsets=candidate_rank_offsets,
        selected_task_masks=selected_masks,
        selected_contexts=[
            [float(value) for value in row["context"]]
            for row in selected_candidates
        ],
    )
    global_context = [
        log1p(max(0.0, float(request.memory_limit_gb)) * 1024.0**3),
        log1p(
            max(
                0.0,
                0.0
                if request.wall_time_limit_sec is None
                else float(request.wall_time_limit_sec),
            )
        ),
        0.0,
        0.0,
    ]
    feature_payload = {
        "node_features": node_features,
        "edge_index": [
            list(static.arc_sources),
            list(static.arc_targets),
        ],
        "edge_features": edge_features,
        "candidate_task_masks": masks,
        "candidate_context": candidate_context,
        "global_context": global_context,
        "candidate_ids": [
            str(row["candidate_id"]) for row in candidates
        ],
    }
    tensors = {
        "node_features": torch.tensor(
            node_features, dtype=torch.float32
        ),
        "edge_index": torch.tensor(
            [list(static.arc_sources), list(static.arc_targets)],
            dtype=torch.long,
        ),
        "edge_features": torch.tensor(
            edge_features, dtype=torch.float32
        ),
        "candidate_task_masks": torch.tensor(
            masks, dtype=torch.float32
        ),
        "candidate_context": torch.tensor(
            candidate_context, dtype=torch.float32
        ),
        "global_context": torch.tensor(
            global_context, dtype=torch.float32
        ),
    }
    return tensors, feature_payload


def _within_feature_envelope(
    payload: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> bool:
    for key in (
        "node_features",
        "edge_features",
        "candidate_context",
        "global_context",
    ):
        rows = (
            payload[key]
            if key != "global_context"
            else [payload[key]]
        )
        bounds = dict(envelope.get(key) or {})
        minimum = list(bounds.get("minimum") or [])
        maximum = list(bounds.get("maximum") or [])
        if not rows or not minimum or len(minimum) != len(maximum):
            return False
        if any(len(row) != len(minimum) for row in rows):
            return False
        if any(
            float(value) < float(minimum[index])
            or float(value) > float(maximum[index])
            for row in rows
            for index, value in enumerate(row)
        ):
            return False
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
