"""Synthetic polar resource grid and path-option construction."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable

from lunar_ice_bpc.domain.scenario import LunarIceConfig, PATH_TYPES


Point = tuple[float, float]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _gaussian(x: float, y: float, cx: float, cy: float, radius: float) -> float:
    dist2 = (float(x) - float(cx)) ** 2 + (float(y) - float(cy)) ** 2
    return math.exp(-dist2 / max(1.0e-9, 2.0 * float(radius) ** 2))


@dataclass(frozen=True)
class SyntheticPolarField:
    """Analytic 30 x 30 km polar resource field.

    The field behaves like a 100 m synthetic grid without storing every cell in
    each instance. Paths and plots sample the same deterministic functions.
    """

    seed: int
    extent_km: float = 30.0
    resolution_m: float = 100.0
    depot_xy_km: Point = (15.0, 15.0)
    psr_centers: tuple[Point, ...] = ()

    @classmethod
    def build(cls, *, seed: int, extent_km: float = 30.0, resolution_m: float = 100.0) -> "SyntheticPolarField":
        rng = random.Random(int(seed))
        centers: list[Point] = []
        for angle_deg, radius in ((235.0, 7.5), (315.0, 8.5), (30.0, 6.5), (150.0, 9.0)):
            jitter_angle = math.radians(angle_deg + rng.uniform(-12.0, 12.0))
            jitter_radius = radius + rng.uniform(-1.2, 1.2)
            centers.append((15.0 + jitter_radius * math.cos(jitter_angle), 15.0 + jitter_radius * math.sin(jitter_angle)))
        return cls(seed=int(seed), extent_km=float(extent_km), resolution_m=float(resolution_m), psr_centers=tuple(centers))

    @property
    def grid_shape(self) -> tuple[int, int]:
        size = int(round(float(self.extent_km) * 1000.0 / float(self.resolution_m)))
        return (size, size)

    def fields_at(self, x: float, y: float) -> dict[str, float]:
        x = _clamp(float(x), 0.0, float(self.extent_km))
        y = _clamp(float(y), 0.0, float(self.extent_km))
        ridge = _gaussian(x, y, self.depot_xy_km[0], self.depot_xy_km[1], 5.0)
        psr = max(_gaussian(x, y, cx, cy, 2.5) for cx, cy in self.psr_centers)
        secondary_psr = sum(_gaussian(x, y, cx, cy, 4.5) for cx, cy in self.psr_centers) / max(1, len(self.psr_centers))
        wave = 0.5 + 0.5 * math.sin(0.7 * x + 0.35 * y + 0.01 * self.seed)
        illumination = _clamp(0.30 + 0.60 * ridge - 0.55 * psr + 0.08 * wave)
        shadow = _clamp(0.20 + 0.75 * psr + 0.20 * secondary_psr - 0.45 * ridge)
        ice_confidence = _clamp(0.12 + 0.70 * shadow + 0.20 * secondary_psr + 0.08 * wave)
        slope_risk = _clamp(0.12 + 0.20 * abs(math.sin(0.35 * x)) + 0.18 * abs(math.cos(0.25 * y)))
        roughness_risk = _clamp(0.10 + 0.22 * abs(math.sin(0.23 * x + 0.53 * y)))
        thermal_risk = _clamp(0.15 + 0.75 * shadow - 0.30 * illumination)
        ice_operation_risk = _clamp(0.10 + 0.35 * ice_confidence + 0.30 * shadow)
        lunar_ice_cell_risk = _clamp(
            0.22 * slope_risk
            + 0.18 * roughness_risk
            + 0.30 * shadow
            + 0.20 * thermal_risk
            + 0.10 * ice_operation_risk
        )
        return {
            "illumination": illumination,
            "shadow": shadow,
            "ice_confidence": ice_confidence,
            "slope_risk": slope_risk,
            "roughness_risk": roughness_risk,
            "thermal_risk": thermal_risk,
            "ice_operation_risk": ice_operation_risk,
            "lunar_ice_cell_risk": lunar_ice_cell_risk,
        }

    def preview(self, *, cells: int = 72) -> list[list[float]]:
        result: list[list[float]] = []
        denom = max(1, int(cells) - 1)
        for row in range(int(cells)):
            y = float(self.extent_km) * float(row) / float(denom)
            values: list[float] = []
            for col in range(int(cells)):
                x = float(self.extent_km) * float(col) / float(denom)
                fields = self.fields_at(x, y)
                values.append(round(0.55 * fields["ice_confidence"] + 0.45 * fields["shadow"], 4))
            result.append(values)
        return result

    def to_payload(self) -> dict:
        return {
            "type": "synthetic_polar_resource_grid",
            "seed": int(self.seed),
            "extent_km": float(self.extent_km),
            "resolution_m": float(self.resolution_m),
            "grid_shape": list(self.grid_shape),
            "depot_xy_km": [float(self.depot_xy_km[0]), float(self.depot_xy_km[1])],
            "psr_centers": [[round(x, 6), round(y, 6)] for x, y in self.psr_centers],
        }


def distance_km(points: Iterable[Point]) -> float:
    seq = list(points)
    return sum(math.dist(seq[index - 1], seq[index]) for index in range(1, len(seq)))


def _interpolate(a: Point, b: Point, fraction: float) -> Point:
    return (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)


def _bend_path(a: Point, b: Point, *, field: SyntheticPolarField, kind: str) -> list[Point]:
    if kind == "low_time":
        return [a, b]
    mid = _interpolate(a, b, 0.5)
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    norm = math.hypot(dx, dy) or 1.0
    perp = (-dy / norm, dx / norm)
    nearest_psr = min(field.psr_centers, key=lambda c: math.dist(mid, c))
    away = (mid[0] - nearest_psr[0], mid[1] - nearest_psr[1])
    away_norm = math.hypot(away[0], away[1]) or 1.0
    away = (away[0] / away_norm, away[1] / away_norm)
    if kind == "low_energy":
        depot = field.depot_xy_km
        toward_depot = (depot[0] - mid[0], depot[1] - mid[1])
        depot_norm = math.hypot(toward_depot[0], toward_depot[1]) or 1.0
        offset = (toward_depot[0] / depot_norm * 1.2 + perp[0] * 0.4, toward_depot[1] / depot_norm * 1.2 + perp[1] * 0.4)
    elif kind == "low_risk":
        offset = (away[0] * 1.8 + perp[0] * 0.6, away[1] * 1.8 + perp[1] * 0.6)
    else:
        raise ValueError(f"unknown path kind {kind!r}")
    bend = (_clamp(mid[0] + offset[0], 0.0, field.extent_km), _clamp(mid[1] + offset[1], 0.0, field.extent_km))
    return [a, bend, b]


def _sample_polyline(points: list[Point], *, samples_per_segment: int = 8) -> list[Point]:
    sampled: list[Point] = []
    for index in range(1, len(points)):
        a = points[index - 1]
        b = points[index]
        for step in range(samples_per_segment):
            sampled.append(_interpolate(a, b, float(step) / float(samples_per_segment)))
    sampled.append(points[-1])
    return sampled


def path_option(field: SyntheticPolarField, source_xy: Point, target_xy: Point, path_type: str, config: LunarIceConfig) -> dict:
    if path_type not in PATH_TYPES:
        raise ValueError(f"unsupported path_type {path_type!r}")
    points = _bend_path(source_xy, target_xy, field=field, kind=path_type)
    path_distance = distance_km(points)
    samples = _sample_polyline(points)
    fields = [field.fields_at(x, y) for x, y in samples]
    avg_risk = sum(item["lunar_ice_cell_risk"] for item in fields) / len(fields)
    avg_shadow = sum(item["shadow"] for item in fields) / len(fields)
    avg_thermal = sum(item["thermal_risk"] for item in fields) / len(fields)
    avg_slope = sum(item["slope_risk"] for item in fields) / len(fields)
    speed = config.rover_max_speed_kmh / (1.0 + 0.55 * avg_risk + 0.45 * avg_shadow + 0.25 * avg_slope)
    speed = max(8.0, min(config.rover_max_speed_kmh, speed))
    travel_time_min = 60.0 * path_distance / max(1.0e-9, speed)
    shadow_exposure = travel_time_min * avg_shadow
    thermal_survival_energy = shadow_exposure * 0.08
    energy = 1.60 * path_distance + 2.20 * path_distance * avg_risk + thermal_survival_energy
    risk_integral = path_distance * (0.35 * avg_risk + 0.25 * avg_shadow + 0.20 * avg_thermal + 0.20 * avg_slope)
    generalized = {
        "low_time": travel_time_min,
        "low_energy": energy,
        "low_risk": risk_integral,
    }[path_type]
    return {
        "path_type": path_type,
        "aliases": [path_type],
        "path_distance_km": round(path_distance, 6),
        "travel_time_min": round(travel_time_min, 6),
        "energy_proxy": round(energy, 6),
        "risk_integral": round(risk_integral, 6),
        "generalized_cost": round(generalized, 6),
        "shadow_exposure_min": round(shadow_exposure, 6),
        "thermal_survival_energy_proxy": round(thermal_survival_energy, 6),
        "slope_risk": round(avg_slope, 6),
        "roughness_risk": round(sum(item["roughness_risk"] for item in fields) / len(fields), 6),
        "path_cells": [],
        "path_xy": [[round(x, 6), round(y, 6)] for x, y in points],
    }


def build_edge_options(field: SyntheticPolarField, nodes: dict[str, Point], config: LunarIceConfig) -> list[dict]:
    edges: list[dict] = []
    for source_id, source_xy in nodes.items():
        for target_id, target_xy in nodes.items():
            if source_id == target_id:
                continue
            edges.append(
                {
                    "from": source_id,
                    "to": target_id,
                    "path_options": [path_option(field, source_xy, target_xy, path_type, config) for path_type in PATH_TYPES],
                }
            )
    return edges

