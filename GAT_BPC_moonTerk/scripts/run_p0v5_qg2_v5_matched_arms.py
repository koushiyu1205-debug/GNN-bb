#!/usr/bin/env python3
"""Collect partition-balanced QD1/QB1 arms and retain parent-view binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
COLLECTOR = ROOT / "scripts/collect_p0v5_qg2_realmap_v4_matched_arms.py"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
MATCHED_SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_matched_arms.v1"
SELECTION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v5_matched_arm_selection.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--parent-view", default=str(RUN / "trace_training_view.json")
    )
    parser.add_argument(
        "--selection-view",
        default=str(
            RUN / "matched_arm_selection_view_force_instance_balanced.json"
        ),
    )
    parser.add_argument(
        "--instance-split",
        default=str(
            ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
            / "realmap_v4_instance_split.json"
        ),
    )
    parser.add_argument(
        "--output-dir", default=str(RUN / "matched_arms_qd1_qb1")
    )
    parser.add_argument(
        "--output", default=str(RUN / "matched_arms_qd1_qb1.json")
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scale30-wall-sec", type=float, default=300.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    args = parser.parse_args()

    parent_path = _resolve(args.parent_view)
    selection_path = _resolve(args.selection_view)
    split_path = _resolve(args.instance_split)
    output_dir = _resolve(args.output_dir)
    output = _resolve(args.output)
    parent = _load(parent_path)
    selection = _load(selection_path)
    _validate_selection(
        parent_path=parent_path, parent=parent,
        selection_path=selection_path, selection=selection,
    )
    raw_output = output_dir / "matched_arms_selection_bound_raw.json"
    command = [
        sys.executable, str(COLLECTOR),
        "--oracle-summary", str(selection_path),
        "--instance-split", str(split_path),
        "--output-dir", str(output_dir),
        "--output", str(raw_output),
        "--repeats", str(max(3, int(args.repeats))),
        "--scale30-wall-sec", str(float(args.scale30_wall_sec)),
        "--scale50-wall-sec", str(float(args.scale50_wall_sec)),
        "--memory-limit-gb", str(float(args.memory_limit_gb)),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(), check=False,
    )
    if completed.returncode != 0 or not raw_output.is_file():
        return int(completed.returncode) or 2
    raw = _load(raw_output)
    _validate_raw(raw, selection=selection, selection_path=selection_path)
    final = {
        **raw,
        "oracle_summary": str(parent_path),
        "oracle_summary_sha256": _sha256(parent_path),
        "selection_view": str(selection_path),
        "selection_view_sha256": _sha256(selection_path),
        "selection_view_schema_version": SELECTION_SCHEMA,
        "selection_is_strict_parent_subset": True,
        "selection_uses_action_outcomes": False,
        "raw_selection_bound_report": str(raw_output),
        "raw_selection_bound_report_sha256": _sha256(raw_output),
        "production_switch_authorized": False,
        "deployable": False,
        "development_only": True,
    }
    _write_or_validate(output, final)
    print(json.dumps({
        "output": str(output),
        "record_count": len(final.get("records") or ()),
        "all_safe": bool(final.get("all_safe")),
        "summary": final.get("summary"),
    }, sort_keys=True))
    return 0


def _validate_selection(*, parent_path, parent, selection_path, selection):
    if (
        parent.get("schema_version") != ORACLE_SCHEMA
        or selection.get("schema_version") != ORACLE_SCHEMA
        or selection.get("selection_view_schema_version") != SELECTION_SCHEMA
        or _resolve(selection.get("source_training_view") or "")
        != parent_path
        or str(selection.get("source_training_view_sha256") or "")
        != _sha256(parent_path)
        or bool(selection.get("selection_uses_action_outcomes"))
        or bool(selection.get("deployable"))
    ):
        raise SystemExit(
            f"V5 matched-arm selection binding failed: {selection_path}"
        )
    parent_states = {
        str(row["state_hash"]) for row in parent.get("initial_rows") or ()
    }
    selected_states = {
        str(row["state_hash"]) for row in selection.get("initial_rows") or ()
    }
    if (
        not selected_states
        or not selected_states.issubset(parent_states)
        or len(selected_states) != int(selection.get("selected_context_count") or 0)
    ):
        raise SystemExit("V5 matched-arm selection is not a strict parent subset")


def _validate_raw(raw, *, selection, selection_path):
    selected_states = {
        str(row["state_hash"]) for row in selection.get("initial_rows") or ()
    }
    record_states = {
        str(row["state_hash"]) for row in raw.get("records") or ()
    }
    if (
        raw.get("schema_version") != MATCHED_SCHEMA
        or _resolve(raw.get("oracle_summary") or "") != selection_path
        or str(raw.get("oracle_summary_sha256") or "")
        != _sha256(selection_path)
        or record_states != selected_states
        or int(raw.get("repeat_count") or 0) < 3
        or not bool(raw.get("all_safe"))
        or bool(raw.get("deployable"))
    ):
        raise SystemExit("V5 matched-arm raw report failed provenance/safety")


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    build = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{build}"
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
    ):
        env.pop(key, None)
    return env


def _write_or_validate(path: Path, payload: dict) -> None:
    if path.is_file():
        if _load(path) != payload:
            raise SystemExit("V5 matched-arm final report drift")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _resolve(value) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
