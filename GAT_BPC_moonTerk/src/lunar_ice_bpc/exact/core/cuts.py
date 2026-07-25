"""Exact cut-context helpers for journey-column reduced costs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import floor
import struct
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.core.journey import JourneyColumn


SUBSET_ROW_CUT = "subset_row"
FLEET_LOWER_BOUND_CUT = "fleet_lower_bound"
CUT_TYPES = (SUBSET_ROW_CUT, FLEET_LOWER_BOUND_CUT)
LIVE_SRI_DIVISOR = 2
LIVE_SRI_SUBSET_SIZES = frozenset({3, 5})
MAX_NATIVE_ACTIVE_CUTS = 16
CUT_CONTEXT_SCHEMA_VERSION = "lunar_ice_bpc.cut_context.v2"
CUT_LINEAGE_SCHEMA_VERSION = "lunar_ice_bpc.cut_lineage.v1"
CUT_STATE_SCHEMA_VERSION = (
    "lunar_ice_bpc.native_cut_state.packed_exact_sri3_2bit_sri5_3bit_u64.v2"
)
CUT_DUAL_PROJECTION_SCHEMA_VERSION = (
    "lunar_ice_bpc.native_pricing_cut_projection.exact_nonzero_dual.v1"
)


@dataclass(frozen=True)
class CutDefinition:
    cut_id: str
    cut_type: str
    tasks: tuple[str, ...] = tuple()
    divisor: int = 2
    rhs: float = 0.0

    def __post_init__(self) -> None:
        if not str(self.cut_id):
            raise ValueError("cut_id must be non-empty")
        if str(self.cut_type) not in CUT_TYPES:
            raise ValueError(f"unsupported cut_type {self.cut_type!r}")
        normalized_tasks = tuple(sorted({str(task_id) for task_id in self.tasks}))
        object.__setattr__(self, "tasks", normalized_tasks)
        object.__setattr__(self, "cut_type", str(self.cut_type))
        object.__setattr__(self, "cut_id", str(self.cut_id))
        object.__setattr__(self, "divisor", int(self.divisor))
        object.__setattr__(self, "rhs", float(self.rhs))
        if self.cut_type == SUBSET_ROW_CUT:
            if len(normalized_tasks) < 2:
                raise ValueError("subset_row cut requires at least two tasks")
            if int(self.divisor) < 2:
                raise ValueError("subset_row divisor must be at least 2")
        if self.cut_type == FLEET_LOWER_BOUND_CUT and float(self.rhs) <= 0.0:
            raise ValueError("fleet_lower_bound cut requires positive rhs")

    def coefficient(self, column: JourneyColumn) -> float:
        if self.cut_type == SUBSET_ROW_CUT:
            overlap = len({str(task_id) for task_id in column.task_set}.intersection(self.tasks))
            return float(floor(overlap / int(self.divisor)))
        if self.cut_type == FLEET_LOWER_BOUND_CUT:
            return 1.0 if column.task_set else 0.0
        raise ValueError(f"unsupported cut_type {self.cut_type!r}")

    def to_payload(self) -> dict:
        return {
            "cut_id": self.cut_id,
            "cut_type": self.cut_type,
            "tasks": list(self.tasks),
            "divisor": self.divisor,
            "rhs": self.rhs,
        }

    @property
    def canonical_key(self) -> tuple:
        return (
            str(self.cut_type),
            int(self.divisor),
            tuple(self.tasks),
            str(self.cut_id),
        )

    @property
    def mathematical_key(self) -> tuple:
        return (
            str(self.cut_type),
            int(self.divisor),
            tuple(self.tasks),
            round(float(self.rhs), 12),
        )


@dataclass(frozen=True)
class CutContext:
    cuts: tuple[CutDefinition, ...] = tuple()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(tuple(self.cuts), key=lambda cut: cut.canonical_key))
        object.__setattr__(self, "cuts", ordered)
        seen: set[str] = set()
        seen_math: set[tuple] = set()
        for cut in ordered:
            if cut.cut_id in seen:
                raise ValueError(f"duplicate cut_id {cut.cut_id!r}")
            if cut.mathematical_key in seen_math:
                raise ValueError(f"duplicate mathematical cut {cut.mathematical_key!r}")
            seen.add(cut.cut_id)
            seen_math.add(cut.mathematical_key)

    @property
    def empty(self) -> bool:
        return not self.cuts

    def coefficients_for(self, column: JourneyColumn) -> dict[str, float]:
        return cut_coefficients_for_journey(column, self)

    def to_payload(self) -> dict:
        return {
            "schema_version": CUT_CONTEXT_SCHEMA_VERSION,
            "cut_count": len(self.cuts),
            "cuts": [cut.to_payload() for cut in self.cuts],
            "note": "Exact cut coefficient context. Current runner records no active cuts by default.",
        }

    def mathematical_payload(self) -> dict:
        return {
            "schema_version": "lunar_ice_bpc.active_cut_mathematics.v1",
            "cuts": [
                {
                    "cut_type": cut.cut_type,
                    "divisor": cut.divisor,
                    "tasks": list(cut.tasks),
                    "rhs": cut.rhs,
                }
                for cut in self.cuts
            ],
        }

    @property
    def active_cut_context_hash(self) -> str:
        return stable_payload_hash(self.mathematical_payload())


@dataclass(frozen=True)
class CutLineageEntry:
    cut_id: str
    scope: str
    origin_node_id: str
    ancestor_path: tuple[str, ...] = tuple()
    policy_version: str = "native_live_sri_v1"

    def __post_init__(self) -> None:
        if not str(self.cut_id):
            raise ValueError("lineage cut_id must be non-empty")
        if str(self.scope) not in {"global", "local"}:
            raise ValueError("cut lineage scope must be global or local")
        object.__setattr__(self, "cut_id", str(self.cut_id))
        object.__setattr__(self, "scope", str(self.scope))
        object.__setattr__(self, "origin_node_id", str(self.origin_node_id))
        object.__setattr__(self, "ancestor_path", tuple(str(node) for node in self.ancestor_path))
        object.__setattr__(self, "policy_version", str(self.policy_version))

    def to_payload(self) -> dict:
        return {
            "cut_id": self.cut_id,
            "scope": self.scope,
            "origin_node_id": self.origin_node_id,
            "ancestor_path": list(self.ancestor_path),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class CutLineage:
    entries: tuple[CutLineageEntry, ...] = tuple()
    policy_version: str = "native_live_sri_v1"

    def __post_init__(self) -> None:
        ordered = tuple(sorted(tuple(self.entries), key=lambda row: row.cut_id))
        if len({entry.cut_id for entry in ordered}) != len(ordered):
            raise ValueError("duplicate cut_id in lineage")
        object.__setattr__(self, "entries", ordered)
        object.__setattr__(self, "policy_version", str(self.policy_version))

    @property
    def empty(self) -> bool:
        return not self.entries

    def to_payload(self) -> dict:
        return {
            "schema_version": CUT_LINEAGE_SCHEMA_VERSION,
            "policy_version": self.policy_version,
            "entry_count": len(self.entries),
            "entries": [entry.to_payload() for entry in self.entries],
        }

    @property
    def cut_lineage_hash(self) -> str:
        return stable_payload_hash(self.to_payload())

    def validate_context(self, context: CutContext) -> tuple[str, ...]:
        context_ids = {cut.cut_id for cut in context.cuts}
        lineage_ids = {entry.cut_id for entry in self.entries}
        issues = []
        if context_ids != lineage_ids:
            issues.append("cut_lineage_context_id_mismatch")
        return tuple(issues)


def stable_payload_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_sri_cut_id(tasks: Iterable[str], *, divisor: int = LIVE_SRI_DIVISOR) -> str:
    ordered = tuple(sorted({str(task_id) for task_id in tasks}))
    return f"sri:d{int(divisor)}:n{len(ordered)}:" + ",".join(ordered)


def canonical_subset_row_cut(
    tasks: Iterable[str],
    *,
    divisor: int = LIVE_SRI_DIVISOR,
) -> CutDefinition:
    ordered = tuple(sorted({str(task_id) for task_id in tasks}))
    return subset_row_cut(canonical_sri_cut_id(ordered, divisor=divisor), ordered, divisor=divisor)


def true_dual_binding_hash(
    cover: Mapping[str, float],
    *,
    fleet_limit: float = 0.0,
    cuts: Mapping[str, float] | None = None,
) -> str:
    """Return the V2 mathematical dual binding.

    Signed zero has no mathematical reduced-cost effect.  Bit-level transport
    diagnostics remain available separately through ``raw_ieee_dual_hash``.
    """

    return stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.true_dual_binding.v2",
            "cover": sorted(
                (str(key), _canonical_mathematical_float(value))
                for key, value in cover.items()
            ),
            "fleet_limit": _canonical_mathematical_float(fleet_limit),
            "cuts": sorted(
                (str(key), _canonical_mathematical_float(value))
                for key, value in (cuts or {}).items()
            ),
        }
    )


def raw_ieee_dual_hash(
    cover: Mapping[str, float],
    *,
    fleet_limit: float = 0.0,
    cuts: Mapping[str, float] | None = None,
) -> str:
    """Return a diagnostic-only dual hash that preserves every IEEE bit."""

    return stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.raw_ieee_dual.v1",
            "cover": sorted(
                (str(key), _float64_hex(value))
                for key, value in cover.items()
            ),
            "fleet_limit": _float64_hex(fleet_limit),
            "cuts": sorted(
                (str(key), _float64_hex(value))
                for key, value in (cuts or {}).items()
            ),
        }
    )


def _canonical_mathematical_float(value: float) -> float:
    parsed = float(value)
    return 0.0 if parsed == 0.0 else parsed


def _float64_hex(value: float) -> str:
    return struct.pack(">d", float(value)).hex()


def pricing_cut_context_from_duals(
    context: CutContext,
    cut_duals: Mapping[str, float] | None,
    *,
    enabled: bool = True,
) -> CutContext:
    """Project only exact-zero cut duals out of a pricing context.

    ``context`` remains the full RMP/certificate context.  No numerical
    tolerance is allowed here: every nonzero floating-point value, however
    small, remains in pricing.
    """

    if not bool(enabled):
        return context
    duals = cut_duals or {}
    return CutContext(
        cuts=tuple(
            cut
            for cut in context.cuts
            if float(duals.get(cut.cut_id, 0.0)) != 0.0
        )
    )


def subset_row_cut(cut_id: str, tasks: Iterable[str], *, divisor: int = 2) -> CutDefinition:
    task_tuple = tuple(str(task_id) for task_id in tasks)
    return CutDefinition(
        cut_id=str(cut_id),
        cut_type=SUBSET_ROW_CUT,
        tasks=task_tuple,
        divisor=int(divisor),
        rhs=float(floor(len(set(task_tuple)) / int(divisor))),
    )


def fleet_lower_bound_cut(cut_id: str, *, min_vehicles: int) -> CutDefinition:
    return CutDefinition(
        cut_id=str(cut_id),
        cut_type=FLEET_LOWER_BOUND_CUT,
        tasks=tuple(),
        divisor=1,
        rhs=float(min_vehicles),
    )


def cut_coefficients_for_journey(column: JourneyColumn, context: CutContext | None) -> dict[str, float]:
    if context is None or context.empty:
        return {}
    return {
        cut.cut_id: coefficient
        for cut in context.cuts
        for coefficient in (cut.coefficient(column),)
        if abs(float(coefficient)) > 1.0e-12
    }


def cut_context_from_payload(payload: dict | None) -> CutContext:
    if not payload:
        return CutContext()
    cuts = []
    for row in payload.get("cuts", []) or []:
        cuts.append(
            CutDefinition(
                cut_id=str(row["cut_id"]),
                cut_type=str(row["cut_type"]),
                tasks=tuple(str(task_id) for task_id in row.get("tasks", []) or []),
                divisor=int(row.get("divisor", 2)),
                rhs=float(row.get("rhs", 0.0)),
            )
        )
    return CutContext(cuts=tuple(cuts))


def cut_lineage_from_payload(payload: dict | None) -> CutLineage:
    if not payload:
        return CutLineage()
    entries = tuple(
        CutLineageEntry(
            cut_id=str(row["cut_id"]),
            scope=str(row["scope"]),
            origin_node_id=str(row.get("origin_node_id") or ""),
            ancestor_path=tuple(str(node) for node in row.get("ancestor_path", []) or []),
            policy_version=str(row.get("policy_version") or payload.get("policy_version") or "native_live_sri_v1"),
        )
        for row in payload.get("entries", []) or []
    )
    return CutLineage(
        entries=entries,
        policy_version=str(payload.get("policy_version") or "native_live_sri_v1"),
    )


def validate_live_sri_context(
    context: CutContext,
    *,
    max_active_cuts: int = MAX_NATIVE_ACTIVE_CUTS,
) -> tuple[str, ...]:
    issues: list[str] = []
    if len(context.cuts) > int(max_active_cuts):
        issues.append("active_cut_count_exceeds_native_capability")
    for cut in context.cuts:
        if cut.cut_type != SUBSET_ROW_CUT:
            issues.append(f"unsupported_live_cut_type:{cut.cut_type}")
            continue
        if int(cut.divisor) != LIVE_SRI_DIVISOR:
            issues.append(f"unsupported_live_sri_divisor:{cut.cut_id}")
        if len(cut.tasks) not in LIVE_SRI_SUBSET_SIZES:
            issues.append(f"unsupported_live_sri_size:{cut.cut_id}")
        expected_rhs = float(floor(len(cut.tasks) / LIVE_SRI_DIVISOR))
        if abs(float(cut.rhs) - expected_rhs) > 1.0e-12:
            issues.append(f"live_sri_rhs_mismatch:{cut.cut_id}")
    return tuple(issues)
