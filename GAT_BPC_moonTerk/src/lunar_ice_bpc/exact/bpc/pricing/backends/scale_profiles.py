"""Scale-specific native SPPRC acceptance profiles."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NativeSpprcScaleProfile:
    scale: int
    worker_max_tasks: int
    exact_max_tasks: int
    ng_sizes: tuple[int, ...]
    harvest_target: int
    row_time_limit_sec: float
    worker_time_limit_sec: float
    memory_limit_gb: float
    backend_id: str
    graph_cache_entries: int
    exact_mode_supported: bool = True
    tree_max_rounds: int = 16
    tree_max_columns_per_round: int = 128
    tree_max_nodes: int = 31
    tree_max_branch_depth: int = 4

    @property
    def proof_time_limit_sec(self) -> float:
        """Maximum proof budget before any worker time has actually elapsed."""

        return max(0.0, float(self.row_time_limit_sec))

    def remaining_proof_time_sec(self, *, worker_elapsed_sec: float) -> float:
        """Inherit the row clock; never allocate a fresh proof timer."""

        return max(0.0, float(self.row_time_limit_sec) - max(0.0, float(worker_elapsed_sec)))


DEFAULT_NATIVE_SPPRC_SCALE_PROFILES: dict[int, NativeSpprcScaleProfile] = {
    5: NativeSpprcScaleProfile(5, 5, 5, (3, 5), 8, 120.0, 10.0, 2.0, "native_rcspp_inprocess", 4, tree_max_nodes=15, tree_max_branch_depth=4),
    10: NativeSpprcScaleProfile(10, 10, 10, (4, 7, 10), 16, 300.0, 30.0, 4.0, "native_rcspp_inprocess", 2, tree_max_nodes=63, tree_max_branch_depth=6),
    20: NativeSpprcScaleProfile(20, 20, 20, (6, 10, 14, 20), 32, 900.0, 90.0, 8.0, "native_rcspp_inprocess", 1, tree_max_nodes=127, tree_max_branch_depth=8),
    30: NativeSpprcScaleProfile(30, 30, 30, (6, 10, 14, 30), 64, 1800.0, 180.0, 16.0, "native_rcspp_inprocess", 1, tree_max_nodes=255, tree_max_branch_depth=12),
    50: NativeSpprcScaleProfile(50, 50, 50, (8, 16, 32, 50), 96, 1800.0, 300.0, 24.0, "native_rcspp_host", 1, tree_max_nodes=511, tree_max_branch_depth=16),
    100: NativeSpprcScaleProfile(100, 100, 100, (10, 20, 40, 70, 100), 128, 1800.0, 300.0, 32.0, "native_rcspp_host", 1, tree_max_nodes=1023, tree_max_branch_depth=24),
}


def native_spprc_scale_profile(scale: int) -> NativeSpprcScaleProfile:
    try:
        return DEFAULT_NATIVE_SPPRC_SCALE_PROFILES[int(scale)]
    except KeyError as exc:
        raise ValueError(f"unsupported native SPPRC scale {scale!r}") from exc
