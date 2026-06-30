"""Scenario constants for the lunar water-ice benchmark."""

from __future__ import annotations

from dataclasses import dataclass


SCALES: tuple[int, ...] = (5, 10, 20, 30, 50, 100)
PATH_TYPES: tuple[str, ...] = ("low_time", "low_energy", "low_risk")
OPERATION_MODES: tuple[str, ...] = ("detect", "sample", "drill")
SYNTHETIC_GENERATOR_ID = "synthetic_polar_resource_grid_v1"
RISK_SCHEMA_VERSION = "lunar_ice_risk_v2"
TIME_WINDOW_POLICY_ID = "sp50_three_temporal_modes_v1"
PATH_OPTION_POLICY_ID = "sp50_three_path_psr_rim_slope_contrast_v2"

FLEET_BY_SCALE = {5: 1, 10: 2, 20: 3, 30: 4, 50: 5, 100: 8}
SOLVE_TIME_LIMIT_SEC_BY_SCALE = {5: 600.0, 10: 600.0, 20: 600.0, 30: 3600.0, 50: 3600.0, 100: 3600.0}
HORIZON_BY_SCALE = {5: 960.0, 10: 960.0, 20: 1680.0, 30: 1680.0, 50: 3000.0, 100: 4560.0}
ACTIVE_FOOTPRINT_BY_SCALE = {5: 50.0, 10: 50.0, 20: 50.0, 30: 50.0, 50: 50.0, 100: 50.0}
SHADOW_CAP_BY_SCALE = {5: 180.0, 10: 180.0, 20: 240.0, 30: 240.0, 50: 300.0, 100: 300.0}

WINDOW_WIDTH_CAP_BY_SCALE = {5: 180.0, 10: 150.0, 20: 120.0, 30: 100.0, 50: 80.0, 100: 60.0}
MEAN_WINDOW_WIDTH_CAP_BY_SCALE = {5: 150.0, 10: 130.0, 20: 100.0, 30: 85.0, 50: 70.0, 100: 65.0}


def _term(*parts: str) -> str:
    return "".join(parts)


DISALLOWED_LINK_KEYS = (
    _term("co", "mm"),
    _term("co", "mm", "unication"),
    _term("black", "out"),
    _term("link", "_margin"),
    _term("earth", "_visibility"),
    _term("relay", "_visibility"),
    _term("direct", "_to_", "earth"),
    _term("D", "TE"),
    _term("LOS", "_to_", "earth"),
    _term("LOS", "_to_", "base"),
)


@dataclass(frozen=True)
class OperationModeSpec:
    """Fixed first-version service parameters for one target operation mode."""

    ratio: float
    service_time_min: tuple[float, float]
    service_energy_proxy: tuple[float, float]
    demand: float


OPERATION_MODE_SPECS: dict[str, OperationModeSpec] = {
    "detect": OperationModeSpec(ratio=0.50, service_time_min=(10.0, 20.0), service_energy_proxy=(2.0, 4.0), demand=0.5),
    "sample": OperationModeSpec(ratio=0.30, service_time_min=(25.0, 45.0), service_energy_proxy=(6.0, 10.0), demand=1.0),
    "drill": OperationModeSpec(ratio=0.20, service_time_min=(45.0, 90.0), service_energy_proxy=(12.0, 20.0), demand=1.5),
}


@dataclass(frozen=True)
class LunarIceConfig:
    """Default benchmark configuration from the refactor plan."""

    resource_map_extent_km: float = 50.0
    synthetic_grid_resolution_m: float = 100.0
    time_bucket_size: float = 10.0
    max_tasks_per_trip: int = 6
    q_ice: float = 6.0
    rover_max_speed_kmh: float = 30.0
    rover_target_mean_speed_kmh: float = 18.0
    energy_unit: str = "dimensionless_proxy"
    b_use: float = 500.0
    dock_overhead_min: float = 8.0
    recharge_power_proxy_per_min: float = 4.0
    depot_chargers: str = "unlimited"
    objective_alpha_discovery_completion: float = 1.0
    objective_beta_journey_end_time: float = 0.05
    objective_gamma_lunar_ice_risk: float = 0.10
    objective_delta_energy: float = 0.01


def scale_label(scale: int) -> str:
    """Return the three-digit benchmark scale label."""

    value = int(scale)
    if value not in SCALES:
        raise ValueError(f"unsupported scale {scale}; expected one of {SCALES}")
    return f"{value:03d}"


def snap_down(value: float, bucket: float) -> float:
    return float(int(float(value) // float(bucket)) * float(bucket))


def snap_up(value: float, bucket: float) -> float:
    bucket = float(bucket)
    quotient = int(float(value) // bucket)
    if abs(float(value) - quotient * bucket) <= 1.0e-9:
        return float(quotient * bucket)
    return float((quotient + 1) * bucket)
