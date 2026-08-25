#!/usr/bin/env python3
"""Run frozen selector fresh-process evaluation with instance-level GM."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
    instance_balanced_geomean,
    instance_balanced_metric,
)


FROZEN = ROOT / "scripts/evaluate_p0v5_qg2_v3_gat_selector_fresh.py"
SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_fresh.v1"


def main() -> int:
    report = _load(_argument_path("--selector-training-report"))
    if str(report.get("instance_balancing_policy") or "") != (
        INSTANCE_BALANCING_POLICY_V1
    ):
        raise SystemExit("selector fresh evaluation lacks instance authority")
    module = _load_frozen()
    module._summary = _instance_balanced_summary
    returncode = int(module.main())
    output = _argument_path("--output")
    if output.is_file():
        _postprocess(output)
    return returncode


def _instance_balanced_summary(records):
    def one(rows):
        values = [
            {
                "instance_hash": str(row["instance_hash"]),
                "ratio": float(row["ratio"]),
            }
            for row in rows
        ]
        ratio = instance_balanced_geomean(values, ratio_key="ratio")
        units = instance_balanced_metric([
            {
                "instance_hash": str(row["instance_hash"]),
                "unit": 1.0,
            }
            for row in rows
        ], value_key="unit")
        activated = [row for row in rows if row["selected_action"] != "Q0"]
        beneficial = [row for row in rows if bool(row.get("beneficial"))]
        harmful = [row for row in rows if bool(row.get("harmful"))]
        return {
            "context_count": len(rows),
            "instance_count": int(units["instance_count"]),
            "maximum_context_fraction_by_instance": units[
                "maximum_context_fraction_by_instance"
            ],
            "activated_count": len(activated),
            "activated_instance_count": len({
                str(row["instance_hash"]) for row in activated
            }),
            "beneficial_count": len(beneficial),
            "beneficial_instance_count": len({
                str(row["instance_hash"]) for row in beneficial
            }),
            "harmful_count": len(harmful),
            "harmful_instance_count": len({
                str(row["instance_hash"]) for row in harmful
            }),
            "net_geomean_ratio": float(
                ratio["instance_balanced_geomean_ratio"]
                if values else 1.0
            ),
            "context_weighted_net_geomean_ratio": float(
                ratio["context_geomean_ratio"] if values else 1.0
            ),
            "per_instance_geomean_ratio": dict(
                ratio["per_instance_geomean_ratio"]
            ),
            "all_safe": all(bool(row["safe"]) for row in rows),
            "hard_safety_violation_count": sum(
                not bool(row["safe"]) for row in rows
            ),
        }
    return {
        "overall": one(records),
        "scale30": one([
            row for row in records if int(row["scale"]) == 30
        ]),
        "scale50": one([
            row for row in records if int(row["scale"]) == 50
        ]),
    }


def _postprocess(path: Path) -> None:
    payload = _load(path)
    payload.update({
        "instance_balanced_wrapper_schema_version": SCHEMA,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "summary_experimental_unit": "instance",
    })
    _write(path, payload)


def _load_frozen():
    spec = importlib.util.spec_from_file_location(
        "qg2_v4_frozen_selector_fresh", FROZEN
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen selector fresh evaluator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _argument_path(name: str) -> Path:
    try:
        raw = sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit(f"missing fresh-evaluation argument {name}") from exc
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
