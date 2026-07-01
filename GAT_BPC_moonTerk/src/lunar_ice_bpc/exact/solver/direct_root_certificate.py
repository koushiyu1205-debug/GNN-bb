"""Fixed-graph root certificate scaffold for small lunar-ice instances."""

from __future__ import annotations

from dataclasses import dataclass

from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.master.journey_rmp import solve_restricted_journey_rmp
from lunar_ice_bpc.exact.solver.journey_driver import enumerate_direct_journey_columns
from lunar_ice_bpc.exact.solver.lower_bounds import relative_gap


@dataclass(frozen=True)
class DirectRootCertificate:
    enabled: bool
    status: str
    exact_status: str
    certificate_scope: str
    lp_bound: float | None
    integer_objective: float | None
    root_gap: float | None
    task_count: int
    fleet_size: int
    max_direct_tasks: int
    generated_journey_count: int
    generated_sortie_count: int
    route_template_count: int
    pareto_label_count: int
    active_column_count: int
    universe_column_count: int
    iteration_count: int
    min_reduced_cost: float | None
    fleet_dual: float | None
    task_cover_duals: dict[str, float]
    integer_matches_root_lp: bool
    uses_true_dual_bpc_certificate: bool
    note: str

    def to_payload(self) -> dict:
        return {
            "enabled": self.enabled,
            "status": self.status,
            "exact_status": self.exact_status,
            "certificate_scope": self.certificate_scope,
            "lp_bound": self.lp_bound,
            "integer_objective": self.integer_objective,
            "root_gap": self.root_gap,
            "task_count": self.task_count,
            "fleet_size": self.fleet_size,
            "max_direct_tasks": self.max_direct_tasks,
            "generated_journey_count": self.generated_journey_count,
            "generated_sortie_count": self.generated_sortie_count,
            "route_template_count": self.route_template_count,
            "pareto_label_count": self.pareto_label_count,
            "active_column_count": self.active_column_count,
            "universe_column_count": self.universe_column_count,
            "iteration_count": self.iteration_count,
            "min_reduced_cost": self.min_reduced_cost,
            "fleet_dual": self.fleet_dual,
            "task_cover_duals": self.task_cover_duals,
            "integer_matches_root_lp": self.integer_matches_root_lp,
            "uses_true_dual_bpc_certificate": self.uses_true_dual_bpc_certificate,
            "note": self.note,
        }


def build_direct_root_certificate(
    data: LunarIceData,
    *,
    max_direct_tasks: int = 5,
    integer_objective: float | None = None,
    gap_eps: float = 1.0e-6,
) -> DirectRootCertificate:
    """Audit the direct fixed-graph root LP for small task counts.

    The certificate scans the exhaustive direct journey-column universe produced
    by the current three-path logical graph. This artifact is deliberately kept
    diagnostic: B0 direct-DP proves only the fixed-graph oracle objective, not a
    true-dual BPC node certificate.
    """

    task_count = len(data.task_ids)
    max_direct_tasks = int(max_direct_tasks)
    if task_count > max_direct_tasks:
        return DirectRootCertificate(
            enabled=False,
            status="SKIPPED_TOO_LARGE_FOR_DIRECT_ROOT_CERTIFICATE",
            exact_status="NOT_SOLVED",
            certificate_scope="fixed_logical_graph_direct_root",
            lp_bound=None,
            integer_objective=integer_objective,
            root_gap=None,
            task_count=task_count,
            fleet_size=data.fleet_size,
            max_direct_tasks=max_direct_tasks,
            generated_journey_count=0,
            generated_sortie_count=0,
            route_template_count=0,
            pareto_label_count=0,
            active_column_count=0,
            universe_column_count=0,
            iteration_count=0,
            min_reduced_cost=None,
            fleet_dual=None,
            task_cover_duals={},
            integer_matches_root_lp=False,
            uses_true_dual_bpc_certificate=False,
            note=f"task_count={task_count} exceeds max_direct_tasks={max_direct_tasks}.",
        )

    universe = enumerate_direct_journey_columns(data, max_exact_tasks=max_direct_tasks)
    rmp = solve_restricted_journey_rmp(
        data.task_ids,
        universe.columns,
        fleet_size=data.fleet_size,
    )
    if rmp.status != "RESTRICTED_RMP_OPTIMAL" or rmp.objective_bound is None:
        return DirectRootCertificate(
            enabled=True,
            status="DIRECT_ROOT_RMP_NOT_OPTIMAL",
            exact_status="NOT_SOLVED",
            certificate_scope="fixed_logical_graph_direct_root",
            lp_bound=rmp.objective_bound,
            integer_objective=integer_objective,
            root_gap=relative_gap(integer_objective, rmp.objective_bound),
            task_count=task_count,
            fleet_size=data.fleet_size,
            max_direct_tasks=max_direct_tasks,
            generated_journey_count=len(universe.columns),
            generated_sortie_count=universe.generated_sortie_count,
            route_template_count=universe.route_template_count,
            pareto_label_count=universe.pareto_label_count,
            active_column_count=rmp.active_column_count,
            universe_column_count=rmp.universe_column_count,
            iteration_count=rmp.iteration_count,
            min_reduced_cost=rmp.min_reduced_cost,
            fleet_dual=rmp.duals.fleet_limit,
            task_cover_duals=dict(rmp.duals.cover),
            integer_matches_root_lp=False,
            uses_true_dual_bpc_certificate=False,
            note="Direct fixed-graph root RMP did not prove restricted optimality.",
        )

    root_gap = relative_gap(integer_objective, rmp.objective_bound)
    integer_matches_root_lp = (
        integer_objective is not None
        and rmp.objective_bound is not None
        and abs(float(integer_objective) - float(rmp.objective_bound)) <= abs(float(gap_eps))
    )
    status = (
        "DIRECT_ROOT_FIXED_GRAPH_INTEGER_MATCH_DIAGNOSTIC"
        if integer_matches_root_lp
        else "DIRECT_ROOT_FIXED_GRAPH_LP_AUDIT_DIAGNOSTIC"
    )
    exact_status = (
        "FIXED_GRAPH_ROOT_LP_INTEGRAL_DIAGNOSTIC"
        if integer_matches_root_lp
        else "FIXED_GRAPH_ROOT_LP_DIAGNOSTIC"
    )
    return DirectRootCertificate(
        enabled=True,
        status=status,
        exact_status=exact_status,
        certificate_scope="fixed_logical_graph_direct_root",
        lp_bound=rmp.objective_bound,
        integer_objective=integer_objective,
        root_gap=root_gap,
        task_count=task_count,
        fleet_size=data.fleet_size,
        max_direct_tasks=max_direct_tasks,
        generated_journey_count=len(universe.columns),
        generated_sortie_count=universe.generated_sortie_count,
        route_template_count=universe.route_template_count,
        pareto_label_count=universe.pareto_label_count,
        active_column_count=rmp.active_column_count,
        universe_column_count=rmp.universe_column_count,
        iteration_count=rmp.iteration_count,
        min_reduced_cost=rmp.min_reduced_cost,
        fleet_dual=rmp.duals.fleet_limit,
        task_cover_duals=dict(rmp.duals.cover),
        integer_matches_root_lp=integer_matches_root_lp,
        uses_true_dual_bpc_certificate=False,
        note=(
            "Audited only for the exhaustive direct journey-column universe of the fixed three-path "
            "logical graph at the root LP; direct-DP is not a true-dual BPC certificate."
        ),
    )
