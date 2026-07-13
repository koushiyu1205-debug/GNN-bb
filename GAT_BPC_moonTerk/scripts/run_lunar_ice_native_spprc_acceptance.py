#!/usr/bin/env python3
"""Run parameterized native SPPRC acceptance without changing the B4.3 runner."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.io.config import load_config
from lunar_ice_bpc.runners.native_spprc_acceptance import run_native_spprc_acceptance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/benchmarks/native_spprc_acceptance.yaml")
    parser.add_argument("--scales", nargs="+", type=int, default=[5, 10, 20, 30, 50, 100])
    parser.add_argument(
        "--backend",
        choices=("python_reference", "native_rcspp_inprocess", "native_rcspp_host"),
    )
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output-dir", default="runs/native_spprc_acceptance")
    parser.add_argument("--resume", action="store_true", default=False)
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    summary = run_native_spprc_acceptance(
        project_root=ROOT,
        config=load_config(config_path),
        scales=tuple(args.scales),
        backend_override=args.backend,
        instances=tuple(args.instance),
        limit=args.limit,
        output_dir=args.output_dir,
        resume=args.resume,
        dry_run=args.dry_run,
    )
    print(
        f"native SPPRC acceptance rows={len(summary['rows'])} "
        f"missing_scales={summary['missing_scales']} output={args.output_dir}"
    )
    return 0 if summary["all_available_runs_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
