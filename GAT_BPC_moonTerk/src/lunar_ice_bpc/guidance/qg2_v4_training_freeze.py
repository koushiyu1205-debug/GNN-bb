"""Two-stage provenance freeze for real-map QG2 model training."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable


SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_training_freeze.v2"
ROOT = Path(__file__).resolve().parents[3]


def create_training_freeze(
    *,
    output: Path,
    oracle_summary: Path,
    oracle_execution_freeze: Path,
    instance_split: Path,
    training_gate: Path,
    source_paths: Iterable[Path],
    forbidden_preexisting_outputs: Iterable[Path] = (),
    pretraining_smoke_report: Path | None = None,
) -> dict:
    """Create the post-Oracle freeze, refusing outcome or source ambiguity."""

    output = Path(output).resolve()
    oracle_summary = Path(oracle_summary).resolve()
    oracle_execution_freeze = Path(oracle_execution_freeze).resolve()
    instance_split = Path(instance_split).resolve()
    training_gate = Path(training_gate).resolve()
    if output.exists():
        raise FileExistsError(f"training freeze refuses overwrite: {output}")
    if (
        not oracle_summary.is_file()
        or not oracle_execution_freeze.is_file()
        or not instance_split.is_file()
        or not training_gate.is_file()
    ):
        raise ValueError("training freeze requires completed Oracle provenance")
    oracle = _load(oracle_summary)
    if (
        not oracle.get("initial_rows")
        or not oracle.get("context_rows")
        or not bool(oracle.get("training_permitted"))
        or not bool(dict(oracle.get("oracle_gate") or {}).get("passed"))
    ):
        raise ValueError("training freeze requires completed Oracle outcomes")
    if any(Path(path).exists() for path in forbidden_preexisting_outputs):
        raise ValueError(
            "training freeze must precede every formal model output"
        )
    smoke_path = (
        None
        if pretraining_smoke_report is None
        else Path(pretraining_smoke_report).resolve()
    )
    if smoke_path is None or not smoke_path.is_file():
        raise ValueError("training freeze requires passed pretraining smoke")
    smoke = _load(smoke_path)
    _validate_training_authority(
        oracle,
        oracle_summary=oracle_summary,
        instance_split=instance_split,
        training_gate=training_gate,
    )
    _validate_smoke_report(
        smoke,
        smoke_path=smoke_path,
        oracle_summary=oracle_summary,
        instance_split=instance_split,
    )
    _validate_upstream_freeze(oracle_execution_freeze)
    sources = tuple(sorted({Path(path).resolve() for path in source_paths}))
    if not sources or any(not path.is_file() for path in sources):
        raise ValueError("training freeze source set is incomplete")
    payload = {
        "schema_version": SCHEMA,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "deployable": False,
        "production_switch_authorized": False,
        "created_after_pretraining_smoke": True,
        "created_before_formal_training": True,
        "oracle_summary": str(oracle_summary),
        "oracle_summary_sha256": sha256(oracle_summary),
        "oracle_execution_freeze": str(oracle_execution_freeze),
        "oracle_execution_freeze_sha256": sha256(oracle_execution_freeze),
        "instance_split": str(instance_split),
        "instance_split_sha256": sha256(instance_split),
        "training_gate": str(training_gate),
        "training_gate_sha256": sha256(training_gate),
        "oracle_source_drift_at_freeze": [],
        "pretraining_smoke_report": str(smoke_path),
        "pretraining_smoke_report_sha256": sha256(smoke_path),
        "instance_balancing_policy": (
            "uniform_instance_steps_rotating_contexts.v1"
        ),
        "optimizer_sampling_unit": "instance",
        "calibration_aggregation_unit": "instance",
        "threshold_net_metric": "instance_balanced_geomean_ratio",
        "fallback_action": "Q0",
        "source_sha256": {
            str(path): sha256(path) for path in sources
        },
    }
    _write(output, payload)
    return payload


def validate_training_freeze(path: Path) -> dict:
    path = Path(path).resolve()
    payload = _load(path)
    errors = []
    if payload.get("schema_version") != SCHEMA:
        errors.append("schema")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or bool(payload.get("production_switch_authorized"))
        or not bool(payload.get("created_after_pretraining_smoke"))
        or not bool(payload.get("created_before_formal_training"))
        or str(payload.get("fallback_action") or "") != "Q0"
    ):
        errors.append("safety")
    for key in (
        "oracle_summary", "oracle_execution_freeze", "instance_split",
        "training_gate",
    ):
        source = Path(str(payload.get(key) or ""))
        expected = str(payload.get(f"{key}_sha256") or "")
        if not source.is_file() or sha256(source) != expected:
            errors.append(f"{key}_drift")
    smoke = Path(str(payload.get("pretraining_smoke_report") or ""))
    if not smoke.is_file() or sha256(smoke) != str(
        payload.get("pretraining_smoke_report_sha256") or ""
    ):
        errors.append("pretraining_smoke_drift")
    else:
        try:
            _validate_training_authority(
                _load(Path(str(payload.get("oracle_summary") or ""))),
                oracle_summary=Path(str(payload.get("oracle_summary") or "")),
                instance_split=Path(str(payload.get("instance_split") or "")),
                training_gate=Path(str(payload.get("training_gate") or "")),
            )
            _validate_smoke_report(
                _load(smoke),
                smoke_path=smoke,
                oracle_summary=Path(
                    str(payload.get("oracle_summary") or "")
                ),
                instance_split=Path(
                    str(payload.get("instance_split") or "")
                ),
            )
        except (OSError, ValueError, TypeError, KeyError):
            errors.append("pretraining_smoke_or_authority_drift")
    source_drift = []
    for raw, expected in dict(payload.get("source_sha256") or {}).items():
        source = Path(raw)
        if not source.is_file() or sha256(source) != str(expected):
            source_drift.append(str(source))
    if source_drift:
        errors.append("training_source_drift")
    if not errors:
        try:
            _validate_upstream_freeze(
                Path(str(payload["oracle_execution_freeze"]))
            )
        except ValueError:
            errors.append("upstream_oracle_source_drift")
    if errors:
        raise ValueError(
            "instance-balanced training freeze invalid:"
            + ",".join(errors + source_drift)
        )
    return payload


def _validate_training_authority(
    oracle: dict,
    *,
    oracle_summary: Path,
    instance_split: Path,
    training_gate: Path,
) -> None:
    authority = dict(oracle.get("realmap_v4_training_authority") or {})
    gate = _load(training_gate)
    if (
        not bool(oracle.get("training_permitted"))
        or not bool(dict(oracle.get("oracle_gate") or {}).get("passed"))
        or not bool(gate.get("training_authorized"))
        or not bool(dict(gate.get("gate") or {}).get("passed"))
        or Path(str(authority.get("gate_report") or "")).resolve()
        != training_gate.resolve()
        or str(authority.get("gate_report_sha256") or "")
        != sha256(training_gate)
        or Path(str(authority.get("instance_split") or "")).resolve()
        != instance_split.resolve()
        or str(authority.get("instance_split_sha256") or "")
        != sha256(instance_split)
    ):
        raise ValueError("training authority binding is invalid")


def _validate_smoke_report(
    smoke: dict,
    *,
    smoke_path: Path,
    oracle_summary: Path,
    instance_split: Path,
) -> None:
    del smoke_path
    if (
        not bool(smoke.get("passed"))
        or str(smoke.get("instance_balancing_policy") or "")
        != "uniform_instance_steps_rotating_contexts.v1"
        or Path(
            str(smoke.get("source_authorized_oracle_summary") or "")
        ).resolve() != oracle_summary.resolve()
        or str(smoke.get("source_authorized_oracle_summary_sha256") or "")
        != sha256(oracle_summary)
        or Path(str(smoke.get("instance_split") or "")).resolve()
        != instance_split.resolve()
        or str(smoke.get("instance_split_sha256") or "")
        != sha256(instance_split)
    ):
        raise ValueError("training freeze requires passed pretraining smoke")
    for key in (
        "smoke_oracle_view", "ranker_training_report", "checkpoint",
    ):
        artifact = Path(str(smoke.get(key) or "")).resolve()
        if (
            not artifact.is_file()
            or str(smoke.get(f"{key}_sha256") or "") != sha256(artifact)
        ):
            raise ValueError(f"pretraining smoke artifact drift:{key}")


def _validate_upstream_freeze(path: Path) -> None:
    payload = _load(path)
    drift = []
    frozen = dict(
        payload.get("frozen_file_sha256")
        or payload.get("source_sha256")
        or {}
    )
    if not frozen:
        raise ValueError("upstream Oracle freeze has no frozen sources")
    for raw, expected in frozen.items():
        source = Path(raw)
        source = source if source.is_absolute() else (ROOT / source).resolve()
        if not source.is_file() or sha256(source) != str(expected):
            drift.append(str(source))
    if drift:
        raise ValueError("upstream Oracle source drift:" + ",".join(drift))


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)
