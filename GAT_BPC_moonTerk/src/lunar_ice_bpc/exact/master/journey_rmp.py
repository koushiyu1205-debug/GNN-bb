"""Journey RMP reduced-cost boundary.

This module centralizes the manual reduced-cost formula so future BPC code has
one exact-safe place for task-cover and fleet-limit dual arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.core.branching import BranchContext, filter_journey_columns_by_branch_context
from lunar_ice_bpc.exact.core.cuts import (
    FLEET_LOWER_BOUND_CUT,
    SUBSET_ROW_CUT,
    CutContext,
    CutDefinition,
)
from lunar_ice_bpc.exact.core.journey import JourneyColumn


@dataclass(frozen=True)
class JourneyDuals:
    cover: Mapping[str, float]
    fleet_limit: float = 0.0
    cuts: Mapping[str, float] | None = None


@dataclass(frozen=True)
class RestrictedRMPResult:
    status: str
    exact_status: str
    objective_bound: float | None
    duals: JourneyDuals
    active_column_count: int
    universe_column_count: int
    iteration_count: int
    added_column_count: int
    min_reduced_cost: float | None
    pricing_history: tuple[dict, ...]
    branch_context: dict
    branch_filtered_column_count: int
    primal_columns: tuple[dict, ...]
    primal_cover_residual_max: float | None
    primal_fleet_usage: float | None
    note: str
    cut_context: dict | None = None
    cut_count: int = 0
    cut_rows_active: bool = False
    primal_cut_activities: tuple[dict, ...] = tuple()
    primal_cut_violation_max: float | None = None


@dataclass(frozen=True)
class _SimplexResult:
    status: str
    objective: float | None
    solution: tuple[float, ...]
    row_duals: tuple[float, ...]
    iterations: int


@dataclass(frozen=True)
class PhaseOneRMPResult:
    status: str
    artificial_objective: float | None
    artificial_values: Mapping[str, float]
    duals: JourneyDuals
    real_primal_columns: tuple[dict, ...]
    real_fleet_usage: float | None
    branch_context: dict
    branch_filtered_column_count: int
    iteration_count: int
    note: str

    @property
    def artificial_positive_count(self) -> int:
        return sum(1 for value in self.artificial_values.values() if value > 1.0e-8)

    @property
    def feasible_without_artificials(self) -> bool:
        return bool(
            self.status == "PHASE_ONE_OPTIMAL"
            and self.artificial_objective is not None
            and self.artificial_objective <= 1.0e-8
        )


def manual_journey_reduced_cost(
    journey: JourneyColumn,
    duals: JourneyDuals,
    *,
    cut_coefficients: Mapping[str, float] | None = None,
) -> float:
    """Return c_j - mu - sum_i pi_i a_ij - sum_k gamma_k a_kj."""

    value = float(journey.objective) - float(duals.fleet_limit)
    for task_id in journey.task_set:
        value -= float(duals.cover.get(str(task_id), 0.0))
    if duals.cuts and cut_coefficients:
        for cut_id, coefficient in cut_coefficients.items():
            value -= float(duals.cuts.get(str(cut_id), 0.0)) * float(coefficient)
    return round(value, 9)


def solve_restricted_journey_rmp(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    *,
    fleet_size: int,
    negative_eps: float = 1.0e-6,
    max_iterations: int = 100,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> RestrictedRMPResult:
    """Run a restricted-universe journey RMP column-generation loop.

    The LP is solved through its dual over the currently active journey
    columns. Pricing scans the supplied restricted universe, not the full
    resource-constrained journey space, so the result is a diagnostic bound for
    this universe only.
    """

    ordered_tasks = tuple(str(task_id) for task_id in task_ids)
    raw_universe = tuple(columns)
    universe = filter_journey_columns_by_branch_context(raw_universe, branch_context)
    filtered_count = len(raw_universe) - len(universe)
    branch_payload = (branch_context or BranchContext()).to_payload()
    active_cut_context = cut_context or CutContext()
    cut_payload = active_cut_context.to_payload()
    cut_count = len(active_cut_context.cuts)
    cut_rows_active = cut_count > 0
    if not ordered_tasks:
        return RestrictedRMPResult(
            status="EMPTY_RMP",
            exact_status="NOT_SOLVED",
            objective_bound=0.0,
            duals=JourneyDuals(cover={}, fleet_limit=0.0),
            active_column_count=0,
            universe_column_count=len(universe),
            iteration_count=0,
            added_column_count=0,
            min_reduced_cost=None,
            pricing_history=tuple(),
            branch_context=branch_payload,
            branch_filtered_column_count=filtered_count,
            primal_columns=tuple(),
            primal_cover_residual_max=None,
            primal_fleet_usage=0.0,
            note="No tasks were supplied.",
            cut_context=cut_payload,
            cut_count=cut_count,
            cut_rows_active=cut_rows_active,
        )
    if not universe:
        return RestrictedRMPResult(
            status="NO_COLUMNS",
            exact_status="NOT_SOLVED",
            objective_bound=None,
            duals=JourneyDuals(cover={}, fleet_limit=0.0),
            active_column_count=0,
            universe_column_count=0,
            iteration_count=0,
            added_column_count=0,
            min_reduced_cost=None,
            pricing_history=tuple(),
            branch_context=branch_payload,
            branch_filtered_column_count=filtered_count,
            primal_columns=tuple(),
            primal_cover_residual_max=None,
            primal_fleet_usage=None,
            note="No journey columns were supplied to the restricted RMP.",
            cut_context=cut_payload,
            cut_count=cut_count,
            cut_rows_active=cut_rows_active,
        )

    active: dict[tuple[str, ...], JourneyColumn] = {}
    for column in universe:
        _insert_best_column_by_cover(active, column)

    history: list[dict] = []
    added_total = 0
    duals = JourneyDuals(cover={}, fleet_limit=0.0)
    objective: float | None = None
    min_rc: float | None = None
    simplex_status = "NOT_RUN"
    for iteration in range(1, int(max_iterations) + 1):
        active_columns = tuple(active.values())
        simplex = _solve_dual_lp(
            ordered_tasks,
            active_columns,
            fleet_size=int(fleet_size),
            cut_context=active_cut_context,
        )
        simplex_status = simplex.status
        if simplex.status != "OPTIMAL" or simplex.objective is None:
            return RestrictedRMPResult(
                status=f"RMP_{simplex.status}",
                exact_status="NOT_SOLVED",
                objective_bound=None,
                duals=duals,
                active_column_count=len(active),
                universe_column_count=len(universe),
                iteration_count=iteration,
                added_column_count=added_total,
                min_reduced_cost=None,
                pricing_history=tuple(history),
                branch_context=branch_payload,
                branch_filtered_column_count=filtered_count,
                primal_columns=tuple(),
                primal_cover_residual_max=None,
                primal_fleet_usage=None,
                note="Restricted RMP dual simplex did not reach OPTIMAL.",
                cut_context=cut_payload,
                cut_count=cut_count,
                cut_rows_active=cut_rows_active,
            )
        objective = round(simplex.objective, 6)
        duals = _solution_to_duals(ordered_tasks, simplex.solution, active_cut_context)
        priced = sorted(
            (
                (
                    manual_journey_reduced_cost(
                        column,
                        duals,
                        cut_coefficients=active_cut_context.coefficients_for(column),
                    ),
                    column,
                )
                for column in universe
            ),
            key=lambda item: item[0],
        )
        min_rc = priced[0][0] if priced else 0.0
        negative = [
            (rc, column)
            for rc, column in priced
            if rc < -abs(float(negative_eps)) and _column_key(column) not in active
        ]
        add_count = 0
        for _, column in negative[: max(1, min(32, len(negative)))]:
            if _insert_best_column_by_cover(active, column):
                add_count += 1
        added_total += add_count
        history.append(
            {
                "iteration": iteration,
                "active_column_count": len(active),
                "lp_dual_bound": objective,
                "min_reduced_cost": round(float(min_rc), 9),
                "negative_column_count": len(negative),
                "added_column_count": add_count,
                "cut_count": cut_count,
                "cut_rows_active": cut_rows_active,
            }
        )
        if not negative:
            primal_columns = _primal_columns_payload(active_columns, simplex.row_duals, active_cut_context)
            cover_residual, fleet_usage = _primal_feasibility_payload(ordered_tasks, primal_columns)
            cut_activities = _primal_cut_activities_payload(active_cut_context, primal_columns)
            return RestrictedRMPResult(
                status="RESTRICTED_RMP_OPTIMAL",
                exact_status="NOT_BPC_CERTIFIED",
                objective_bound=objective,
                duals=duals,
                active_column_count=len(active),
                universe_column_count=len(universe),
                iteration_count=iteration,
                added_column_count=added_total,
                min_reduced_cost=round(float(min_rc), 9),
                pricing_history=tuple(history),
                branch_context=branch_payload,
                branch_filtered_column_count=filtered_count,
                primal_columns=primal_columns,
                primal_cover_residual_max=cover_residual,
                primal_fleet_usage=fleet_usage,
                note=(
                    "LP bound is optimal only for the supplied restricted journey-column universe; "
                    "all restricted columns were loaded."
                ),
                cut_context=cut_payload,
                cut_count=cut_count,
                cut_rows_active=cut_rows_active,
                primal_cut_activities=cut_activities,
                primal_cut_violation_max=_max_cut_violation(cut_activities),
            )

    return RestrictedRMPResult(
        status="RESTRICTED_RMP_ITERATION_LIMIT",
        exact_status="NOT_SOLVED",
        objective_bound=objective,
        duals=duals,
        active_column_count=len(active),
        universe_column_count=len(universe),
        iteration_count=int(max_iterations),
        added_column_count=added_total,
        min_reduced_cost=round(float(min_rc), 9) if min_rc is not None else None,
        pricing_history=tuple(history),
        branch_context=branch_payload,
        branch_filtered_column_count=filtered_count,
        primal_columns=tuple(),
        primal_cover_residual_max=None,
        primal_fleet_usage=None,
        note=f"Stopped after max_iterations={max_iterations}; last simplex_status={simplex_status}.",
        cut_context=cut_payload,
        cut_count=cut_count,
        cut_rows_active=cut_rows_active,
    )


def solve_phase_one_journey_rmp(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    *,
    fleet_size: int,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> PhaseOneRMPResult:
    """Minimize uncovered-task artificials for a restricted branch master.

    Real journey columns have zero Phase-I cost and task artificials have unit
    cost and do not consume fleet.  The resulting dual is therefore the exact
    pricing context ``0 - sum(pi_i) - mu`` used to restore RMP feasibility or
    certify that the full branch master is infeasible.
    """

    ordered_tasks = tuple(str(task_id) for task_id in task_ids)
    raw_columns = tuple(columns)
    active_columns = filter_journey_columns_by_branch_context(raw_columns, branch_context)
    filtered_count = len(raw_columns) - len(active_columns)
    branch_payload = (branch_context or BranchContext()).to_payload()
    active_cuts = cut_context or CutContext()
    if not active_cuts.empty:
        return PhaseOneRMPResult(
            status="UNSUPPORTED_CUT_CONTEXT",
            artificial_objective=None,
            artificial_values={},
            duals=JourneyDuals(cover={}, fleet_limit=0.0),
            real_primal_columns=tuple(),
            real_fleet_usage=None,
            branch_context=branch_payload,
            branch_filtered_column_count=filtered_count,
            iteration_count=0,
            note="Phase-I v1 requires empty CutContext.",
        )
    simplex = _solve_dual_lp(
        ordered_tasks,
        active_columns,
        fleet_size=int(fleet_size),
        cut_context=active_cuts,
        phase_one=True,
    )
    if simplex.status != "OPTIMAL" or simplex.objective is None:
        return PhaseOneRMPResult(
            status=f"PHASE_ONE_{simplex.status}",
            artificial_objective=None,
            artificial_values={},
            duals=JourneyDuals(cover={}, fleet_limit=0.0),
            real_primal_columns=tuple(),
            real_fleet_usage=None,
            branch_context=branch_payload,
            branch_filtered_column_count=filtered_count,
            iteration_count=simplex.iterations,
            note="Phase-I restricted master did not solve to optimality.",
        )
    real_count = len(active_columns)
    artificial_values = {
        task_id: round(float(simplex.row_duals[real_count + index]), 9)
        for index, task_id in enumerate(ordered_tasks)
    }
    real_primal = _primal_columns_payload(
        active_columns,
        simplex.row_duals[:real_count],
        active_cuts,
    )
    real_fleet_usage = round(
        sum(float(row.get("lambda_value") or 0.0) for row in real_primal),
        9,
    )
    artificial_objective = round(sum(artificial_values.values()), 9)
    return PhaseOneRMPResult(
        status="PHASE_ONE_OPTIMAL",
        artificial_objective=artificial_objective,
        artificial_values=artificial_values,
        duals=_solution_to_duals(ordered_tasks, simplex.solution, active_cuts),
        real_primal_columns=real_primal,
        real_fleet_usage=real_fleet_usage,
        branch_context=branch_payload,
        branch_filtered_column_count=filtered_count,
        iteration_count=simplex.iterations,
        note=(
            "Restricted branch master is feasible without artificials."
            if artificial_objective <= 1.0e-8
            else "Positive artificials remain; exact Phase-I pricing is required."
        ),
    )


def _column_key(column: JourneyColumn) -> tuple[str, ...]:
    return tuple(sorted(str(task_id) for task_id in column.task_set))


def _insert_best_column_by_cover(active: dict[tuple[str, ...], JourneyColumn], column: JourneyColumn) -> bool:
    key = _column_key(column)
    old = active.get(key)
    if old is not None and old.objective <= column.objective + 1.0e-9:
        return False
    active[key] = column
    return True


def _primal_columns_payload(
    columns: tuple[JourneyColumn, ...],
    row_duals: tuple[float, ...],
    cut_context: CutContext | None = None,
) -> tuple[dict, ...]:
    rows: list[dict] = []
    context = cut_context or CutContext()
    for index, (column, value) in enumerate(zip(columns, row_duals)):
        lambda_value = round(float(value), 9)
        if lambda_value <= 1.0e-9:
            continue
        row = {
            "column_index": index,
            "lambda_value": lambda_value,
            "task_count": len(column.task_set),
            "tasks": sorted(str(task_id) for task_id in column.task_set),
            "objective": round(float(column.objective), 6),
            "end_time": round(float(column.end_time), 6),
            "sortie_count": len(column.sorties),
        }
        cut_coefficients = context.coefficients_for(column)
        if cut_coefficients:
            row["cut_coefficients"] = {
                cut_id: round(float(coefficient), 9)
                for cut_id, coefficient in sorted(cut_coefficients.items())
            }
        rows.append(row)
    return tuple(rows)


def _primal_feasibility_payload(task_ids: tuple[str, ...], primal_columns: tuple[dict, ...]) -> tuple[float, float]:
    cover = {str(task_id): 0.0 for task_id in task_ids}
    fleet_usage = 0.0
    for row in primal_columns:
        value = float(row.get("lambda_value") or 0.0)
        fleet_usage += value
        for task_id in row.get("tasks", []) or []:
            if str(task_id) in cover:
                cover[str(task_id)] += value
    residual = max((abs(value - 1.0) for value in cover.values()), default=0.0)
    return round(float(residual), 9), round(float(fleet_usage), 9)


def _primal_cut_activities_payload(
    cut_context: CutContext,
    primal_columns: tuple[dict, ...],
) -> tuple[dict, ...]:
    rows: list[dict] = []
    for cut in cut_context.cuts:
        activity = 0.0
        support_count = 0
        for column_payload in primal_columns:
            coefficient = _payload_cut_coefficient(cut, column_payload)
            if abs(coefficient) <= 1.0e-12:
                continue
            support_count += 1
            activity += coefficient * float(column_payload.get("lambda_value") or 0.0)
        sense = "<=" if cut.cut_type == SUBSET_ROW_CUT else ">="
        raw_violation = activity - cut.rhs if cut.cut_type == SUBSET_ROW_CUT else cut.rhs - activity
        rows.append(
            {
                "cut_id": cut.cut_id,
                "cut_type": cut.cut_type,
                "sense": sense,
                "rhs": round(float(cut.rhs), 9),
                "activity": round(float(activity), 9),
                "violation": round(float(max(0.0, raw_violation)), 9),
                "support_column_count": support_count,
            }
        )
    return tuple(rows)


def _payload_cut_coefficient(cut: CutDefinition, column_payload: Mapping[str, object]) -> float:
    tasks = {str(task_id) for task_id in column_payload.get("tasks", []) or []}
    if cut.cut_type == SUBSET_ROW_CUT:
        return float(len(tasks.intersection(cut.tasks)) // int(cut.divisor))
    if cut.cut_type == FLEET_LOWER_BOUND_CUT:
        return 1.0 if tasks else 0.0
    raise ValueError(f"unsupported cut_type {cut.cut_type!r}")


def _max_cut_violation(cut_activities: tuple[dict, ...]) -> float | None:
    if not cut_activities:
        return None
    return round(max(float(row.get("violation") or 0.0) for row in cut_activities), 9)


def _solution_to_duals(
    task_ids: tuple[str, ...],
    solution: tuple[float, ...],
    cut_context: CutContext | None = None,
) -> JourneyDuals:
    n = len(task_ids)
    cover = {
        task_id: round(float(solution[index]) - float(solution[n + index]), 9)
        for index, task_id in enumerate(task_ids)
    }
    mu_prime = float(solution[2 * n]) if len(solution) > 2 * n else 0.0
    cuts: dict[str, float] = {}
    context = cut_context or CutContext()
    cut_start = 2 * n + 1
    for offset, cut in enumerate(context.cuts):
        raw_value = float(solution[cut_start + offset]) if len(solution) > cut_start + offset else 0.0
        dual_value = -raw_value if cut.cut_type == SUBSET_ROW_CUT else raw_value
        cuts[cut.cut_id] = round(float(dual_value), 9)
    return JourneyDuals(cover=cover, fleet_limit=round(-mu_prime, 9), cuts=cuts)


def _solve_dual_lp(
    task_ids: tuple[str, ...],
    columns: Iterable[JourneyColumn],
    *,
    fleet_size: int,
    cut_context: CutContext | None = None,
    phase_one: bool = False,
) -> _SimplexResult:
    n = len(task_ids)
    context = cut_context or CutContext()
    if phase_one and not context.empty:
        raise ValueError("Phase-I dual currently requires empty CutContext")
    task_index = {task_id: index for index, task_id in enumerate(task_ids)}
    cut_start = 2 * n + 1
    objective = [0.0 for _ in range(cut_start + len(context.cuts))]
    for index in range(n):
        objective[index] = 1.0
        objective[n + index] = -1.0
    objective[2 * n] = -float(fleet_size)
    for offset, cut in enumerate(context.cuts):
        variable_index = cut_start + offset
        if cut.cut_type == SUBSET_ROW_CUT:
            objective[variable_index] = -float(cut.rhs)
        elif cut.cut_type == FLEET_LOWER_BOUND_CUT:
            objective[variable_index] = float(cut.rhs)
        else:
            raise ValueError(f"unsupported cut_type {cut.cut_type!r}")

    rows: list[list[float]] = []
    rhs: list[float] = []
    for column in columns:
        row = [0.0 for _ in range(len(objective))]
        for task_id in column.task_set:
            index = task_index[str(task_id)]
            row[index] += 1.0
            row[n + index] -= 1.0
        row[2 * n] -= 1.0
        for offset, cut in enumerate(context.cuts):
            variable_index = cut_start + offset
            coefficient = cut.coefficient(column)
            if cut.cut_type == SUBSET_ROW_CUT:
                row[variable_index] -= float(coefficient)
            elif cut.cut_type == FLEET_LOWER_BOUND_CUT:
                row[variable_index] += float(coefficient)
            else:
                raise ValueError(f"unsupported cut_type {cut.cut_type!r}")
        rows.append(row)
        rhs.append(0.0 if phase_one else float(column.objective))
    if phase_one:
        # One unit-cost artificial y_i per task-cover equality.  Artificial
        # variables do not consume fleet, hence their dual rows contain only
        # the free cover dual pi_i = pi_i^+ - pi_i^-.
        for task_id in task_ids:
            row = [0.0 for _ in range(len(objective))]
            index = task_index[task_id]
            row[index] = 1.0
            row[n + index] = -1.0
            rows.append(row)
            rhs.append(1.0)
    solver = os.environ.get("LUNAR_ICE_RMP_SOLVER", "highs").strip().lower()
    if solver not in {"simplex", "python"}:
        highs = _highs_max_leq(objective, rows, rhs)
        if highs is not None:
            return highs
    return _simplex_max_leq(objective, rows, rhs)


def _highs_max_leq(
    objective: list[float],
    rows: list[list[float]],
    rhs: list[float],
    *,
    eps: float = 1.0e-9,
) -> _SimplexResult | None:
    """Solve max c'x s.t. Ax <= b, x >= 0 through HiGHS.

    HiGHS is called on the equivalent minimization problem min -c'x.  Row
    duals of the minimization model are therefore negated before being returned
    as primal lambda values for the original restricted master columns.
    """

    if not rows:
        return _SimplexResult(
            status="NO_CONSTRAINTS",
            objective=None,
            solution=tuple(),
            row_duals=tuple(),
            iterations=0,
        )
    for bound in rhs:
        if float(bound) < -eps:
            return _SimplexResult(
                status="NEGATIVE_RHS",
                objective=None,
                solution=tuple(),
                row_duals=tuple(),
                iterations=0,
            )
    try:
        import highspy  # type: ignore[import-not-found]
    except Exception:
        return None

    try:
        highs = highspy.Highs()
        highs.setOptionValue("output_flag", False)
        thread_count = int(os.environ.get("LUNAR_ICE_RMP_HIGHS_THREADS", "1"))
        highs.setOptionValue("threads", max(1, thread_count))
        inf = highs.getInfinity()
        n = len(objective)
        min_objective = [-float(value) for value in objective]
        status = highs.addCols(
            n,
            min_objective,
            [0.0 for _ in range(n)],
            [inf for _ in range(n)],
            0,
            [],
            [],
            [],
        )
        if str(status) != "HighsStatus.kOk":
            return None
        for row, bound in zip(rows, rhs):
            indices: list[int] = []
            values: list[float] = []
            for index, value in enumerate(row):
                numeric = float(value)
                if abs(numeric) <= 1.0e-12:
                    continue
                indices.append(index)
                values.append(numeric)
            status = highs.addRow(-inf, float(bound), len(indices), indices, values)
            if str(status) != "HighsStatus.kOk":
                return None
        highs.run()
        model_status = highs.modelStatusToString(highs.getModelStatus()).upper()
        info = highs.getInfo()
        iterations = int(getattr(info, "simplex_iteration_count", 0) or 0)
        if model_status == "OPTIMAL":
            solution = highs.getSolution()
            objective_value = -float(highs.getObjectiveValue())
            col_values = tuple(round(float(value), 9) for value in solution.col_value[:n])
            row_duals = tuple(
                round(max(0.0, -float(value)), 9)
                for value in solution.row_dual[: len(rows)]
            )
            return _SimplexResult(
                status="OPTIMAL",
                objective=round(objective_value, 9),
                solution=col_values,
                row_duals=row_duals,
                iterations=iterations,
            )
        if "INFEASIBLE" in model_status:
            status_name = "INFEASIBLE"
        elif "UNBOUNDED" in model_status:
            status_name = "UNBOUNDED"
        else:
            status_name = f"HIGHS_{model_status.replace(' ', '_')}"
        return _SimplexResult(
            status=status_name,
            objective=None,
            solution=tuple(),
            row_duals=tuple(),
            iterations=iterations,
        )
    except Exception:
        return None


def _simplex_max_leq(
    objective: list[float],
    rows: list[list[float]],
    rhs: list[float],
    *,
    eps: float = 1.0e-9,
    max_pivots: int = 10000,
) -> _SimplexResult:
    if not rows:
        return _SimplexResult(
            status="NO_CONSTRAINTS",
            objective=None,
            solution=tuple(),
            row_duals=tuple(),
            iterations=0,
        )
    m = len(rows)
    n = len(objective)
    width = n + m + 1
    tableau: list[list[float]] = []
    basis: list[int] = []
    for row_index, (row, bound) in enumerate(zip(rows, rhs)):
        if bound < -eps:
            return _SimplexResult(
                status="NEGATIVE_RHS",
                objective=None,
                solution=tuple(),
                row_duals=tuple(),
                iterations=0,
            )
        current = [0.0 for _ in range(width)]
        for col_index, value in enumerate(row):
            current[col_index] = float(value)
        slack_index = n + row_index
        current[slack_index] = 1.0
        current[-1] = float(bound)
        basis.append(slack_index)
        tableau.append(current)

    obj = [0.0 for _ in range(width)]
    for col_index, value in enumerate(objective):
        obj[col_index] = -float(value)
    tableau.append(obj)

    iterations = 0
    while iterations < int(max_pivots):
        entering = min(range(width - 1), key=lambda col: tableau[-1][col])
        if tableau[-1][entering] >= -eps:
            solution = [0.0 for _ in range(n)]
            for row_index, basic_col in enumerate(basis):
                if basic_col < n:
                    solution[basic_col] = tableau[row_index][-1]
            row_duals = tuple(round(max(0.0, tableau[-1][n + row_index]), 9) for row_index in range(m))
            return _SimplexResult(
                status="OPTIMAL",
                objective=round(tableau[-1][-1], 9),
                solution=tuple(round(value, 9) for value in solution),
                row_duals=row_duals,
                iterations=iterations,
            )
        ratios: list[tuple[float, int]] = []
        for row_index in range(m):
            coefficient = tableau[row_index][entering]
            if coefficient > eps:
                ratios.append((tableau[row_index][-1] / coefficient, row_index))
        if not ratios:
            return _SimplexResult(
                status="UNBOUNDED",
                objective=None,
                solution=tuple(),
                row_duals=tuple(),
                iterations=iterations,
            )
        _, leaving = min(ratios, key=lambda item: (item[0], basis[item[1]]))
        _pivot(tableau, leaving, entering)
        basis[leaving] = entering
        iterations += 1
    return _SimplexResult(
        status="PIVOT_LIMIT",
        objective=None,
        solution=tuple(),
        row_duals=tuple(),
        iterations=iterations,
    )


def _pivot(tableau: list[list[float]], pivot_row: int, pivot_col: int) -> None:
    value = tableau[pivot_row][pivot_col]
    tableau[pivot_row] = [entry / value for entry in tableau[pivot_row]]
    for row_index, row in enumerate(tableau):
        if row_index == pivot_row:
            continue
        factor = row[pivot_col]
        if abs(factor) <= 1.0e-12:
            continue
        tableau[row_index] = [
            entry - factor * pivot_entry
            for entry, pivot_entry in zip(row, tableau[pivot_row])
        ]
