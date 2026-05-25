#!/usr/bin/env python3
"""Run small task-level schedule-capacity separator ablations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gnn_bb.baseline.config import load_config  # noqa: E402


VARIANTS: dict[str, dict[str, Any]] = {
    "baseline": {
        "task_schedule_capacity_cuts_enabled": False,
        "root_schedule_capacity_cuts_enabled": False,
    },
    "root_only": {
        "task_schedule_capacity_cuts_enabled": True,
        "task_schedule_capacity_max_depth": 0,
    },
    "root_depth1": {
        "task_schedule_capacity_cuts_enabled": True,
        "task_schedule_capacity_max_depth": 1,
    },
    "pair_only": {
        "task_schedule_capacity_cuts_enabled": True,
        "task_schedule_capacity_max_depth": 0,
        "task_schedule_capacity_pair_budget": 100,
        "task_schedule_capacity_triple_budget": 0,
        "task_schedule_capacity_small_set_budget": 0,
    },
    "pair_triple": {
        "task_schedule_capacity_cuts_enabled": True,
        "task_schedule_capacity_max_depth": 0,
        "task_schedule_capacity_pair_budget": 100,
        "task_schedule_capacity_triple_budget": 50,
        "task_schedule_capacity_small_set_budget": 0,
    },
    "witness_only": {
        "task_schedule_capacity_cuts_enabled": True,
        "task_schedule_capacity_max_depth": 1,
        "task_schedule_capacity_use_top_z_mass": False,
        "task_schedule_capacity_use_support_route_union": False,
        "task_schedule_capacity_use_rim_witness": True,
        "task_schedule_capacity_use_route_pack_witness": True,
        "task_schedule_capacity_use_incompatibility_witness": True,
        "task_schedule_capacity_small_set_budget": 10,
    },
    "top_z_only": {
        "task_schedule_capacity_cuts_enabled": True,
        "task_schedule_capacity_max_depth": 0,
        "task_schedule_capacity_use_top_z_mass": True,
        "task_schedule_capacity_use_support_route_union": False,
        "task_schedule_capacity_use_rim_witness": False,
        "task_schedule_capacity_use_route_pack_witness": False,
        "task_schedule_capacity_use_incompatibility_witness": False,
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run task schedule-capacity separator ablations.")
    parser.add_argument("--config", default="configs/bpc_task_schedule_capacity_ablation.yaml")
    parser.add_argument("--instances", nargs="*", help="Override configured instances.")
    parser.add_argument("--variants", nargs="*", choices=sorted(VARIANTS), help="Override configured variants.")
    parser.add_argument("--time-limit", type=float, help="Override per-variant time limit.")
    parser.add_argument("--max-nodes", type=int, help="Override max nodes.")
    parser.add_argument("--run-id", help="Output run id.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    base = load_config(config.get("base_config", "configs/bpc_clean.yaml"))
    instances = args.instances or config.get("instances", ["very_small"])
    variants = args.variants or config.get("variants", list(VARIANTS))
    run_id = args.run_id or config.get("run_id") or datetime.now().strftime("%Y%m%d_%H%M%S_task_schedcap")
    time_limit = float(args.time_limit if args.time_limit is not None else config.get("time_limit", base.get("time_limit", 300)))
    max_nodes = int(args.max_nodes if args.max_nodes is not None else config.get("max_nodes", base.get("max_nodes", 100000)))
    run_root = ROOT / "results" / "task_schedule_capacity_ablation" / str(run_id)
    config_dir = run_root / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)

    for variant in variants:
        merged = dict(base)
        merged.update(VARIANTS[str(variant)])
        merged["instances"] = list(instances)
        merged["time_limit"] = time_limit
        merged["max_nodes"] = max_nodes
        variant_config = config_dir / f"{variant}.json"
        variant_config.write_text(json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "run_bpc_clean.py"),
            "--config",
            str(variant_config),
            "--results-csv",
            str(run_root / f"{variant}.csv"),
            "--log-dir",
            str(run_root / "logs" / str(variant)),
            "--solution-dir",
            str(run_root / "solutions" / str(variant)),
        ]
        if args.quiet:
            cmd.append("--quiet")
        print(" ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=ROOT, check=True)
    print(f"task schedule-capacity ablation outputs: {run_root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
