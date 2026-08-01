"""Fail-closed runtime for the V5 bidirectional-prepass GAT gate."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import os
import re
from threading import RLock
from time import perf_counter
from typing import Any, Mapping


BIDIRECTIONAL_GATE_MANIFEST_ENV = (
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST"
)
BIDIRECTIONAL_GATE_EVALUATION_ENV = (
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE"
)
_LOCK = RLock()
_CACHE: dict[str, tuple[dict[str, Any], Any, str]] = {}
_STATE: dict[str, dict[str, Any]] = {}


@dataclass(frozen=True)
class BidirectionalGateDecision:
    action: str = "RUN"
    reason: str = "v5_default"
    failure_probability: float | None = None
    expected_wasted_time_sec: float | None = None
    inference_wall_ms: float = 0.0
    ood: bool = False
    manifest_sha256: str = ""
    checkpoint_sha256: str = ""

    @property
    def skips_prepass(self) -> bool:
        return self.action == "SKIP"


def decide_bidirectional_prepass_from_environment(
    request,
) -> BidirectionalGateDecision:
    """Return RUN on every validation or inference failure."""

    manifest_value = str(
        os.getenv(BIDIRECTIONAL_GATE_MANIFEST_ENV, "")
    ).strip()
    if not manifest_value:
        return BidirectionalGateDecision(reason="runtime_not_configured")
    try:
        return _decide(request, Path(manifest_value).resolve())
    except Exception as exc:
        return BidirectionalGateDecision(
            action="RUN", reason=f"fail_closed:{exc!r}"
        )


def record_bidirectional_prepass_outcome(
    request,
    *,
    accepted: bool | None,
    skipped: bool = False,
) -> None:
    """Record only already-observed outcomes for the next root-CG call."""

    key = _state_key(request)
    round_index = _round_index(request.rmp_iteration_id)
    with _LOCK:
        state = _state_before_call(key, round_index)
        if skipped:
            state["refresh_required"] = True
        elif accepted is not None:
            failed = not bool(accepted)
            state["previous_outcome"] = "FAILED" if failed else "ACCEPTED"
            state["failure_streak"] = (
                int(state.get("failure_streak") or 0) + 1 if failed else 0
            )
            state["refresh_required"] = False
        state["last_round"] = round_index
        _STATE[key] = state


def _decide(request, manifest_path: Path) -> BidirectionalGateDecision:
    from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
        PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    )
    from lunar_ice_bpc.guidance.bidirectional_gate_gat import (
        BIDIRECTIONAL_GATE_GAT_POLICY_ID,
        build_bidirectional_gate_features,
    )

    if not request.exact_proof_mode:
        return BidirectionalGateDecision(reason="non_exact_request")
    if request.pricing_lifecycle_scope != PRICING_LIFECYCLE_SCOPE_ROOT_CG:
        return BidirectionalGateDecision(reason="non_root_cg_scope")
    manifest, model, checkpoint_hash = _load(manifest_path)
    if str(manifest.get("policy_id") or "") != (
        BIDIRECTIONAL_GATE_GAT_POLICY_ID
    ):
        raise ValueError("bidirectional GAT policy mismatch")
    if str(manifest.get("runtime_implementation_hash") or "") != (
        bidirectional_gate_runtime_implementation_hash()
    ):
        raise ValueError("bidirectional GAT runtime drift")
    scale = int(request.data.scale)
    if scale not in {int(value) for value in manifest.get("allowed_scales", ())}:
        raise ValueError("bidirectional GAT scale is outside manifest scope")
    allowed_engines = {
        str(value) for value in manifest.get("allowed_exact_engine_hashes", ())
    }
    if allowed_engines and str(request.engine_hash or "") not in allowed_engines:
        raise ValueError("bidirectional GAT engine hash mismatch")
    evaluation = str(
        os.getenv(BIDIRECTIONAL_GATE_EVALUATION_ENV, "0")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if evaluation:
        if not bool(manifest.get("evaluation_authorized")):
            raise ValueError("bidirectional GAT evaluation not authorized")
    elif not bool(manifest.get("deployment_authorized")):
        return BidirectionalGateDecision(reason="deployment_not_authorized")

    round_index = _round_index(request.rmp_iteration_id)
    key = _state_key(request)
    with _LOCK:
        state = dict(_state_before_call(key, round_index))
    if bool(state.get("refresh_required")):
        return BidirectionalGateDecision(reason="refresh_after_skip")
    features = build_bidirectional_gate_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=float(request.true_duals.fleet_limit),
        round_index=round_index,
        previous_midpoint_outcome=str(
            state.get("previous_outcome") or "NONE"
        ),
        consecutive_observed_failures=int(
            state.get("failure_streak") or 0
        ),
    )
    ood, reason = _is_ood(
        features, dict(manifest.get("feature_envelope") or {})
    )
    if ood:
        return BidirectionalGateDecision(
            reason=reason,
            ood=True,
            manifest_sha256=_sha256(manifest_path),
            checkpoint_sha256=checkpoint_hash,
        )
    import torch

    torch.set_num_threads(max(1, int(manifest.get("torch_num_threads") or 1)))
    started = perf_counter()
    with torch.inference_mode():
        output = model(**features.to_tensors())
    inference_ms = (perf_counter() - started) * 1000.0
    probability = float(output["failure_probability"])
    magnitude = float(output["conditional_wasted_time_sec"])
    expected = probability * magnitude
    calibration = dict(manifest.get("calibration") or {})
    gate_pass = bool(calibration.get("gate_pass"))
    skip = bool(
        gate_pass
        and probability
        >= float(calibration.get("failure_probability_threshold") or 1.0)
        and expected
        >= float(calibration.get("expected_waste_threshold_sec") or 0.0)
    )
    return BidirectionalGateDecision(
        action="SKIP" if skip else "RUN",
        reason="calibrated_skip" if skip else "calibrated_run",
        failure_probability=probability,
        expected_wasted_time_sec=expected,
        inference_wall_ms=inference_ms,
        manifest_sha256=_sha256(manifest_path),
        checkpoint_sha256=checkpoint_hash,
    )


def _load(path: Path):
    key = f"{path}:{path.stat().st_mtime_ns}:{path.stat().st_size}"
    with _LOCK:
        cached = _CACHE.get(key)
        if cached is not None:
            return cached
        manifest = json.loads(path.read_text(encoding="utf-8"))
        checkpoint = Path(str(manifest["checkpoint_path"]))
        if not checkpoint.is_absolute():
            checkpoint = (path.parent / checkpoint).resolve()
        checkpoint_hash = _sha256(checkpoint)
        if checkpoint_hash != str(manifest.get("checkpoint_sha256") or ""):
            raise ValueError("bidirectional GAT checkpoint hash mismatch")
        from lunar_ice_bpc.guidance.bidirectional_gate_gat import (
            load_checkpoint,
        )

        model, metadata = load_checkpoint(str(checkpoint))
        if str(metadata.get("training_data_hash") or "") != str(
            manifest.get("training_data_hash") or ""
        ):
            raise ValueError("bidirectional GAT training hash mismatch")
        _CACHE.clear()
        cached = (manifest, model, checkpoint_hash)
        _CACHE[key] = cached
        return cached


def _round_index(value: str) -> int:
    matches = re.findall(r"(?:^|[-_:])(\d+)(?:$|[-_:])", str(value))
    return 0 if not matches else int(matches[-1])


def _state_key(request) -> str:
    return ":".join(
        (
            str(request.data.instance_content_hash),
            str(request.engine_hash or ""),
            str(request.config_hash or ""),
        )
    )


def _state_before_call(key: str, round_index: int) -> dict[str, Any]:
    state = dict(_STATE.get(key) or {})
    last_round = int(state.get("last_round") or 0)
    if round_index <= 1 or (last_round and round_index <= last_round):
        state = {
            "last_round": 0,
            "previous_outcome": "NONE",
            "failure_streak": 0,
            "refresh_required": False,
        }
    return state


def _is_ood(features, envelope: Mapping[str, Any]) -> tuple[bool, str]:
    if not envelope:
        return True, "missing_feature_envelope"
    context = tuple(float(value) for value in features.context_features)
    lower = tuple(float(value) for value in envelope.get("context_min", ()))
    upper = tuple(float(value) for value in envelope.get("context_max", ()))
    if len(context) != len(lower) or len(context) != len(upper):
        return True, "feature_envelope_dimension_mismatch"
    margin = max(0.0, float(envelope.get("relative_margin") or 0.0))
    for value, lo, hi in zip(context, lower, upper, strict=True):
        width = max(1.0e-9, hi - lo)
        if value < lo - margin * width or value > hi + margin * width:
            return True, "context_outside_feature_envelope"
    node_max = max(abs(value) for row in features.node_features for value in row)
    edge_max = max(abs(value) for row in features.edge_features for value in row)
    if node_max > float(envelope.get("node_max_abs") or 0.0) * (1.0 + margin):
        return True, "node_features_outside_envelope"
    if edge_max > float(envelope.get("edge_max_abs") or 0.0) * (1.0 + margin):
        return True, "edge_features_outside_envelope"
    return False, ""


def bidirectional_gate_runtime_implementation_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (
        root / "bidirectional_gate_gat.py",
        Path(__file__).resolve(),
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
