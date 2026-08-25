#!/usr/bin/env python3
"""Screen narrower TinyGAT RC buckets without rerunning the Q0 baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
SCHEMA = "lunar_ice_bpc.p0v5_qg2_v5_tinygat_bucket_screen.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force-on-dir",
        default=str(DEFAULT_RUN / "label_gat_force_on_train_screen"),
    )
    parser.add_argument(
        "--training-view",
        default=str(DEFAULT_RUN / "trace_training_view.json"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_RUN / "label_gat_bucket_screen"),
    )
    parser.add_argument("--state-hash", action="append", default=[])
    parser.add_argument(
        "--bucket-widths", nargs="+", type=float,
        default=(1.0e-4, 3.0e-4),
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    force_dir = _resolve(args.force_on_dir)
    training_view_path = _resolve(args.training_view)
    output_dir = _resolve(args.output_dir)
    records_path = force_dir / "force_on_records.jsonl"
    if not records_path.is_file():
        raise SystemExit("TinyGAT bucket screen requires force-on records")
    view = _load(training_view_path)
    corpus_path = _resolve(view.get("source_trace_corpus") or "")
    if (
        not corpus_path.is_file()
        or str(view.get("source_trace_corpus_sha256") or "")
        != _sha256(corpus_path)
    ):
        raise SystemExit("TinyGAT bucket screen trace corpus binding drift")
    corpus = _load(corpus_path)
    rows_by_state = {
        str(row["state_hash"]): dict(row)
        for row in corpus.get("rows") or ()
    }
    records = [
        json.loads(line) for line in records_path.read_text(
            encoding="utf-8"
        ).splitlines() if line.strip()
    ]
    wanted = set(str(value) for value in args.state_hash)
    if wanted:
        records = [row for row in records if str(row["state_hash"]) in wanted]
        missing = wanted - {str(row["state_hash"]) for row in records}
        if missing:
            raise SystemExit(
                "requested state lacks a complete force-on record: "
                + ",".join(sorted(missing))
            )
    else:
        # Default to completed harmful contexts with the largest Q0 wall.
        records = sorted(
            (row for row in records if float(row.get("ratio") or 0.0) >= 1.0),
            key=lambda row: (-float(row.get("q0_median_wall_sec") or 0.0),
                             str(row.get("state_hash") or "")),
        )[:3]
    widths = tuple(sorted(set(float(value) for value in args.bucket_widths)))
    if not records or not widths or min(widths) <= 0.0:
        raise SystemExit("TinyGAT bucket screen has no contexts or valid widths")
    repeats = max(1, int(args.repeats))
    plan = _build_plan(
        force_dir=force_dir,
        rows_by_state=rows_by_state,
        records=records,
        widths=widths,
        repeats=repeats,
        output_dir=output_dir,
        memory_limit_gb=float(args.memory_limit_gb),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _write(output_dir / "screen_plan.json", {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "dry_run": bool(args.dry_run),
        "training_view": str(training_view_path),
        "training_view_sha256": _sha256(training_view_path),
        "trace_corpus": str(corpus_path),
        "trace_corpus_sha256": _sha256(corpus_path),
        "force_on_records": str(records_path),
        "force_on_records_sha256": _sha256(records_path),
        "rows": plan,
    })
    if args.dry_run:
        print(json.dumps({"dry_run": True, "arm_count": len(plan)}))
        return 0

    completed = []
    for index, arm in enumerate(plan, start=1):
        target = Path(arm["output"])
        if not target.is_file():
            command = [
                sys.executable, str(REPLAY),
                "--instance", arm["instance"],
                "--snapshot", arm["snapshot"],
                "--output", str(target),
                "--policy", "QG2",
                "--potential", arm["potential"],
                "--repeat-index", str(arm["repeat"]),
                "--guidance-bucket-width", str(arm["bucket_width"]),
                "--wall-time-limit-sec", str(arm["wall_time_limit_sec"]),
                "--memory-limit-gb", str(arm["memory_limit_gb"]),
                "--source-backend-id", arm["source_backend_id"],
            ]
            target.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                command, cwd=ROOT, env=_environment(), check=False,
            )
            if result.returncode != 0 or not target.is_file():
                raise SystemExit(
                    f"TinyGAT bucket replay failed: {arm['state_hash'][:16]} "
                    f"width={arm['bucket_width']} repeat={arm['repeat']}"
                )
        replay = _load(target)
        _validate_replay(arm, replay)
        completed.append({**arm, "result": _result_summary(replay)})
        _write(output_dir / "progress.json", {
            "schema_version": SCHEMA,
            "completed_arms": index,
            "selected_arms": len(plan),
            "last_state_hash": arm["state_hash"],
            "last_bucket_width": arm["bucket_width"],
        })
    report = _aggregate(completed, records)
    report.update({
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "production_switch_authorized": False,
        "screen_plan_sha256": _sha256(output_dir / "screen_plan.json"),
    })
    _write(output_dir / "bucket_screen.json", report)
    print(json.dumps(report["aggregate"], sort_keys=True))
    return 0


def _build_plan(
    *, force_dir: Path, rows_by_state: dict[str, dict], records: list[dict],
    widths: tuple[float, ...], repeats: int, output_dir: Path,
    memory_limit_gb: float,
) -> list[dict]:
    result = []
    for record in records:
        state = str(record["state_hash"])
        context = rows_by_state.get(state)
        if context is None:
            raise SystemExit(f"training view lacks state {state}")
        scale = int(record["scale"])
        state_dir = force_dir / f"scale{scale}" / state[:16]
        potential = state_dir / "gat_potential.json"
        q0 = state_dir / "q0_rep1.json"
        if not potential.is_file() or not q0.is_file():
            raise SystemExit(f"force-on artifacts are incomplete for {state}")
        baseline = _load(q0)
        for width in widths:
            width_id = f"{width:.0e}".replace("-0", "-").replace("+", "")
            for repeat in range(1, repeats + 1):
                target = (
                    output_dir / f"scale{scale}" / state[:16]
                    / f"qg2_bucket_{width_id}_rep{repeat}.json"
                )
                result.append({
                    "scale": scale,
                    "state_hash": state,
                    "instance": str(context["instance_path"]),
                    "snapshot": str(context["snapshot_path"]),
                    "potential": str(potential),
                    "potential_sha256": _sha256(potential),
                    "bucket_width": width,
                    "repeat": repeat,
                    "wall_time_limit_sec": float(
                        baseline.get("requested_wall_time_limit_sec")
                        or (300.0 if scale == 30 else 600.0)
                    ),
                    "memory_limit_gb": memory_limit_gb,
                    "source_backend_id": str(baseline["source_backend_id"]),
                    "q0_median_wall_sec": float(record["q0_median_wall_sec"]),
                    "q0_milestone_kind": str(record["milestone_kind"]),
                    "output": str(target),
                })
    return result


def _validate_replay(arm: dict, replay: dict) -> None:
    telemetry = dict(replay.get("proof_telemetry") or {})
    if (
        replay.get("policy") != "QG2"
        or str(replay.get("source_state_hash") or "") != arm["state_hash"]
        or not bool(replay.get("ordering_only"))
        or bool(replay.get("can_filter"))
        or bool(replay.get("can_prune"))
        or bool(replay.get("can_change_reduced_cost"))
        or bool(replay.get("can_certify_from_guidance"))
        or bool(replay.get("labels_dropped"))
        or int(telemetry.get("rc_mismatch_count") or 0) != 0
        or list(replay.get("certificate_blockers") or ())
    ):
        raise SystemExit("TinyGAT bucket replay violated exact-safe boundary")


def _result_summary(replay: dict) -> dict:
    telemetry = dict(replay.get("proof_telemetry") or {})
    return {
        "engine_status": str(replay.get("engine_status") or ""),
        "milestone_kind": str(replay.get("milestone_kind") or ""),
        "milestone_reached": bool(replay.get("milestone_reached")),
        "wall_sec": float(replay.get("milestone_wall_sec") or 0.0),
        "processed_labels": int(telemetry.get("processed_labels") or 0),
        "dominance_candidate_checks": int(
            telemetry.get("dominance_candidate_checks") or 0
        ),
        "reordered_label_hash_count": int(
            telemetry.get("proof_queue_guidance_reordered_label_hash_count")
            or 0
        ),
        "covered_bucket_count": int(
            telemetry.get("proof_queue_guidance_covered_bucket_count") or 0
        ),
    }


def _aggregate(arms: list[dict], records: list[dict]) -> dict:
    baseline = {str(row["state_hash"]): row for row in records}
    groups: dict[tuple[str, float], list[dict]] = {}
    for arm in arms:
        groups.setdefault(
            (arm["state_hash"], float(arm["bucket_width"])), []
        ).append(arm)
    rows = []
    for (state, width), values in sorted(groups.items()):
        reached = [
            row for row in values
            if row["result"]["milestone_reached"]
            and row["result"]["milestone_kind"]
            == str(baseline[state]["milestone_kind"])
        ]
        wall = (
            statistics.median(row["result"]["wall_sec"] for row in reached)
            if len(reached) == len(values) else None
        )
        q0 = float(baseline[state]["q0_median_wall_sec"])
        rows.append({
            "scale": int(baseline[state]["scale"]),
            "state_hash": state,
            "bucket_width": width,
            "repeat_count": len(values),
            "all_matched_milestone": len(reached) == len(values),
            "median_wall_sec": wall,
            "q0_median_wall_sec": q0,
            "ratio": None if wall is None else wall / q0,
        })
    by_width = {}
    for width in sorted({row["bucket_width"] for row in rows}):
        matched = [
            row for row in rows
            if row["bucket_width"] == width and row["ratio"] is not None
        ]
        by_width[str(width)] = {
            "context_count": sum(row["bucket_width"] == width for row in rows),
            "matched_context_count": len(matched),
            "beneficial_context_count": sum(row["ratio"] < 1.0 for row in matched),
            "geometric_mean_ratio": (
                math.exp(sum(math.log(row["ratio"]) for row in matched)
                         / len(matched)) if matched else None
            ),
        }
    return {"rows": rows, "aggregate": {"by_bucket_width": by_width}}


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    build = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{build}"
    return env


def _resolve(value) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
