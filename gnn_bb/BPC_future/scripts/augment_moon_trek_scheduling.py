#!/usr/bin/env python3
"""Add deterministic multi-sortie CVRPTW scheduling fields to generated data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.preprocess.scheduling_augmentation import (  # noqa: E402
    SchedulingAugmentationConfig,
    augment_manifest_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Augment Moon Trek instances with CVRPTW scheduling fields.")
    parser.add_argument("--manifest", default="BPC_future/data/generated/moon_trek_60/manifest.json")
    parser.add_argument("--horizon-min", type=float, default=720.0)
    parser.add_argument("--fleet-size", type=int, default=3)
    parser.add_argument("--vehicle-capacity-task-units", type=float, default=6.0)
    parser.add_argument("--max-sorties-per-vehicle", type=int, default=8)
    parser.add_argument("--usable-battery-capacity-proxy", type=float, default=80.0)
    parser.add_argument("--recharge-power-proxy-per-min", type=float, default=2.0)
    parser.add_argument("--service-energy-proxy-per-min", type=float, default=0.04)
    parser.add_argument("--survival-energy-proxy-per-min", type=float, default=0.01)
    parser.add_argument("--fixed-vehicle-cost", type=float, default=50.0)
    parser.add_argument("--task-window-length-min", type=float, default=480.0)
    parser.add_argument("--task-window-bucket-min", type=float, default=30.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SchedulingAugmentationConfig(
        horizon_min=float(args.horizon_min),
        fleet_size=int(args.fleet_size),
        vehicle_capacity_task_units=float(args.vehicle_capacity_task_units),
        max_sorties_per_vehicle=int(args.max_sorties_per_vehicle),
        usable_battery_capacity_proxy=float(args.usable_battery_capacity_proxy),
        recharge_power_proxy_per_min=float(args.recharge_power_proxy_per_min),
        service_energy_proxy_per_min=float(args.service_energy_proxy_per_min),
        survival_energy_proxy_per_min=float(args.survival_energy_proxy_per_min),
        fixed_vehicle_cost=float(args.fixed_vehicle_cost),
        task_window_length_min=float(args.task_window_length_min),
        task_window_bucket_min=float(args.task_window_bucket_min),
    )
    manifest = augment_manifest_dataset(args.manifest, config=config)
    print(
        json.dumps(
            {
                "manifest": str(Path(args.manifest)),
                "instances": len(manifest.get("instances", [])),
                "scheduling_augmentation": manifest["scheduling_augmentation"],
                "sortie_policy": manifest["sortie_policy"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
