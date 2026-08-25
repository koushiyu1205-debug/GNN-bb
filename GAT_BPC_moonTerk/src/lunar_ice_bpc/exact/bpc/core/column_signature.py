"""Semantic signatures for BPC journey columns."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from lunar_ice_bpc.exact.core.journey import JourneyColumn


@dataclass(frozen=True)
class ColumnSemanticSignature:
    task_set: tuple[str, ...]
    sortie_partition: tuple[tuple[str, ...], ...]
    ordered_task_sequences: tuple[tuple[str, ...], ...]
    path_option_signature: tuple[tuple[str, ...], ...]
    service_timing_signature: tuple[tuple[str, float], ...]
    resource_profile_signature: tuple[tuple[str, float], ...]
    branch_signature: tuple[str, ...] = tuple()
    cut_coefficient_vector_hash: str = ""
    version: str = "column_semantic_signature.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_set", tuple(str(task_id) for task_id in self.task_set))


def column_signature_from_journey(column: JourneyColumn) -> ColumnSemanticSignature:
    return ColumnSemanticSignature(
        task_set=tuple(sorted(str(task_id) for task_id in column.task_set)),
        sortie_partition=tuple(tuple(str(task_id) for task_id in sortie.tasks) for sortie in column.sorties),
        ordered_task_sequences=tuple(tuple(str(task_id) for task_id in sortie.tasks) for sortie in column.sorties),
        path_option_signature=tuple(
            tuple(str(leg.path_type) for leg in sortie.legs)
            for sortie in column.sorties
        ),
        service_timing_signature=tuple(
            (str(task_id), float(start))
            for sortie in column.sorties
            for task_id, start in sorted(sortie.service_starts.items())
        ),
        resource_profile_signature=(
            ("journey_end_time", float(column.end_time)),
            ("journey_energy_proxy", float(column.energy_proxy)),
            ("journey_risk_integral", float(column.risk_integral)),
            ("journey_objective", float(column.objective)),
            *(
                item
                for sortie_index, sortie in enumerate(column.sorties)
                for item in (
                    (f"sortie_{sortie_index}_end_time", float(sortie.end_time)),
                    (f"sortie_{sortie_index}_energy_proxy", float(sortie.energy_proxy)),
                    (f"sortie_{sortie_index}_risk_integral", float(sortie.risk_integral)),
                    (f"sortie_{sortie_index}_shadow_exposure_min", float(sortie.shadow_exposure_min)),
                )
            ),
        ),
    )


def column_semantic_signature_hash(
    signature: ColumnSemanticSignature,
) -> str:
    """Return the stable hash used by Native/Python route audit bindings."""

    return hashlib.sha256(repr(signature).encode("utf-8")).hexdigest()
