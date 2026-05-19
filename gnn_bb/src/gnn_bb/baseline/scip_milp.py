"""中文摘要：本文件构建并求解纯 SCIP compact MILP baseline，不使用列生成或分支定价。"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gnn_bb.data.instances import task_ids
from gnn_bb.data.io_utils import ensure_dir, finite_or_none, read_json, round_float
from gnn_bb.data.terrain import arc_key, build_task_closure


@dataclass
class BaselineResult:
    instance: str
    task_count: int
    vehicle_count: int
    sortie_count: int
    variable_count: int
    constraint_count: int
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    solving_time: float | None
    node_count: float | None
    memory_mb: float | None
    log_path: str
    instance_path: str
    seed: int | None

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


def _task_value(instance: dict[str, Any], task_id: int, field: str) -> float:
    return float(instance["tasks"][str(task_id)][field])


def _safe_call(func, default=None):
    try:
        value = func()
    except Exception:
        return default
    return finite_or_none(value)


def _status_name(status: Any) -> str:
    text = str(status).lower()
    status_map = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
        "nodelimit": "NODE_LIMIT",
        "gaplimit": "GAP_LIMIT",
        "memlimit": "MEMORY_LIMIT",
        "userinterrupt": "INTERRUPTED",
        "solutionlimit": "SOLUTION_LIMIT",
    }
    return status_map.get(text, text.upper())


def _try_set_param(model, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        # 中文注释：不同 SCIP 版本参数名可能略有差异；baseline 继续运行，并在日志中保留求解器默认值。
        pass


def _visit_expr(x: dict[tuple[int, int, int, int], Any], nodes: list[int], r: int, s: int, task_id: int):
    from pyscipopt import quicksum

    return quicksum(x[r, s, i, task_id] for i in nodes if i != task_id)


def build_compact_milp(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    scip_params: dict[str, Any] | None = None,
    time_limit: float | None = None,
    log_path: str | Path | None = None,
    verbose: bool = True,
):
    from pyscipopt import Model, quicksum

    tasks = task_ids(instance)
    nodes = [0, *tasks]
    vehicles = instance["vehicles"]
    R = list(range(1, int(vehicles["R_bar"]) + 1))
    S = list(range(1, int(vehicles["S_bar"]) + 1))
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])
    rho = float(vehicles["rho"])
    fixed_vehicle_cost = float(vehicles["F"])
    max_due = max(_task_value(instance, task_id, "D") for task_id in tasks)

    model = Model(f"scip_baseline_{instance.get('name', 'instance')}")
    if time_limit is not None:
        _try_set_param(model, "limits/time", float(time_limit))
    for name, value in (scip_params or {}).items():
        _try_set_param(model, name, value)
    # 中文注释：命令行 quiet/verbose 是最终显示策略，放在配置参数之后覆盖 display/verblevel。
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    if log_path is not None:
        ensure_dir(Path(log_path).parent)
        try:
            model.setLogfile(str(log_path))
        except Exception:
            Path(log_path).write_text("当前 PySCIPOpt/SCIP 版本不支持 setLogfile，无法捕获 solver log。\n", encoding="utf-8")

    x = {}
    for r in R:
        for s in S:
            for i in nodes:
                for j in nodes:
                    if i == j:
                        continue
                    if i == 0 and j == 0:
                        continue
                    arc_cost = float(pairwise[arc_key(i, j)]["cost"])
                    service_cost = 0.0 if j == 0 else _task_value(instance, j, "c_srv")
                    x[r, s, i, j] = model.addVar(vtype="B", obj=arc_cost + service_cost, name=f"x[{r},{s},{i},{j}]")

    z = {(r, s): model.addVar(vtype="B", name=f"z[{r},{s}]") for r in R for s in S}
    y = {r: model.addVar(vtype="B", obj=fixed_vehicle_cost, name=f"y[{r}]") for r in R}
    start_time = {
        (r, s, i): model.addVar(lb=0.0, ub=max_due, vtype="C", name=f"T[{r},{s},{i}]")
        for r in R
        for s in S
        for i in tasks
    }
    load = {
        (r, s, i): model.addVar(lb=0.0, ub=q_limit, vtype="C", name=f"L[{r},{s},{i}]")
        for r in R
        for s in S
        for i in tasks
    }
    energy = {
        (r, s, i): model.addVar(lb=0.0, ub=b_limit, vtype="C", name=f"E[{r},{s},{i}]")
        for r in R
        for s in S
        for i in tasks
    }
    return_time = {(r, s): model.addVar(lb=0.0, ub=horizon, vtype="C", name=f"RT[{r},{s}]") for r in R for s in S}
    return_energy = {(r, s): model.addVar(lb=0.0, ub=b_limit, vtype="C", name=f"RE[{r},{s}]") for r in R for s in S}

    # 中文注释：每个任务恰好有一个入弧，因此被服务一次。
    for task_id in tasks:
        model.addCons(
            quicksum(x[r, s, i, task_id] for r in R for s in S for i in nodes if i != task_id) == 1,
            name=f"cover[{task_id}]",
        )

    for r in R:
        for s in S:
            model.addCons(quicksum(x[r, s, 0, j] for j in tasks) == z[r, s], name=f"depart[{r},{s}]")
            model.addCons(quicksum(x[r, s, i, 0] for i in tasks) == z[r, s], name=f"return[{r},{s}]")
            model.addCons(z[r, s] <= y[r], name=f"slot_requires_vehicle[{r},{s}]")
            model.addCons(return_time[r, s] <= horizon * z[r, s], name=f"return_time_active[{r},{s}]")
            model.addCons(return_energy[r, s] <= b_limit * z[r, s], name=f"return_energy_active[{r},{s}]")

            for task_id in tasks:
                incoming = quicksum(x[r, s, i, task_id] for i in nodes if i != task_id)
                outgoing = quicksum(x[r, s, task_id, j] for j in nodes if j != task_id)
                model.addCons(incoming == outgoing, name=f"flow[{r},{s},{task_id}]")
                model.addCons(start_time[r, s, task_id] >= _task_value(instance, task_id, "r") * incoming, name=f"time_lb[{r},{s},{task_id}]")
                model.addCons(start_time[r, s, task_id] <= _task_value(instance, task_id, "D") * incoming, name=f"time_ub[{r},{s},{task_id}]")
                model.addCons(load[r, s, task_id] <= q_limit * incoming, name=f"load_active[{r},{s},{task_id}]")
                model.addCons(energy[r, s, task_id] <= b_limit * incoming, name=f"energy_active[{r},{s},{task_id}]")

                tau_from_base = float(pairwise[arc_key(0, task_id)]["tau"])
                energy_from_base = float(pairwise[arc_key(0, task_id)]["energy"])
                service_energy = _task_value(instance, task_id, "g")
                model.addCons(
                    start_time[r, s, task_id] >= tau_from_base - tau_from_base * (1 - x[r, s, 0, task_id]),
                    name=f"time_base[{r},{s},{task_id}]",
                )
                model.addCons(
                    load[r, s, task_id] >= _task_value(instance, task_id, "d") - _task_value(instance, task_id, "d") * (1 - x[r, s, 0, task_id]),
                    name=f"load_base[{r},{s},{task_id}]",
                )
                model.addCons(
                    energy[r, s, task_id] >= energy_from_base + service_energy - (energy_from_base + service_energy) * (1 - x[r, s, 0, task_id]),
                    name=f"energy_base[{r},{s},{task_id}]",
                )

            for i in tasks:
                for j in tasks:
                    if i == j:
                        continue
                    tau = float(pairwise[arc_key(i, j)]["tau"])
                    arc_energy = float(pairwise[arc_key(i, j)]["energy"])
                    sigma_i = _task_value(instance, i, "sigma")
                    demand_j = _task_value(instance, j, "d")
                    service_energy_j = _task_value(instance, j, "g")
                    time_m = _task_value(instance, i, "D") + sigma_i + tau
                    load_m = q_limit + demand_j
                    energy_m = b_limit + arc_energy + service_energy_j
                    model.addCons(
                        start_time[r, s, j] >= start_time[r, s, i] + sigma_i + tau - time_m * (1 - x[r, s, i, j]),
                        name=f"time_arc[{r},{s},{i},{j}]",
                    )
                    model.addCons(
                        load[r, s, j] >= load[r, s, i] + demand_j - load_m * (1 - x[r, s, i, j]),
                        name=f"load_arc[{r},{s},{i},{j}]",
                    )
                    model.addCons(
                        energy[r, s, j] >= energy[r, s, i] + arc_energy + service_energy_j - energy_m * (1 - x[r, s, i, j]),
                        name=f"energy_arc[{r},{s},{i},{j}]",
                    )

            for i in tasks:
                tau_to_base = float(pairwise[arc_key(i, 0)]["tau"])
                energy_to_base = float(pairwise[arc_key(i, 0)]["energy"])
                sigma_i = _task_value(instance, i, "sigma")
                time_m = _task_value(instance, i, "D") + sigma_i + tau_to_base
                energy_m = b_limit + energy_to_base
                model.addCons(
                    return_time[r, s] >= start_time[r, s, i] + sigma_i + tau_to_base - time_m * (1 - x[r, s, i, 0]),
                    name=f"return_time[{r},{s},{i}]",
                )
                model.addCons(
                    return_energy[r, s] >= energy[r, s, i] + energy_to_base - energy_m * (1 - x[r, s, i, 0]),
                    name=f"return_energy[{r},{s},{i}]",
                )

    for r in R:
        model.addCons(
            quicksum(return_time[r, s] + return_energy[r, s] / rho for s in S) <= horizon * y[r],
            name=f"vehicle_cycle_time[{r}]",
        )
        for s in S[:-1]:
            model.addCons(z[r, s + 1] <= z[r, s], name=f"sortie_sequence[{r},{s}]")
    for r in R[:-1]:
        model.addCons(y[r + 1] <= y[r], name=f"vehicle_sequence[{r}]")

    data = {
        "x": x,
        "z": z,
        "y": y,
        "start_time": start_time,
        "load": load,
        "energy": energy,
        "return_time": return_time,
        "return_energy": return_energy,
        "R": R,
        "S": S,
        "tasks": tasks,
    }
    return model, data


def solve_scip_baseline(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    instance_path: str | Path,
    time_limit: float,
    log_path: str | Path,
    scip_params: dict[str, Any] | None = None,
    seed: int | None = None,
    verbose: bool = True,
) -> BaselineResult:
    model, data = build_compact_milp(
        instance,
        pairwise,
        scip_params=scip_params,
        time_limit=time_limit,
        log_path=log_path,
        verbose=verbose,
    )
    original_variable_count = int(_safe_call(model.getNVars, 0) or 0)
    original_constraint_count = int(_safe_call(model.getNConss, 0) or 0)
    model.optimize()
    solution_count = int(_safe_call(model.getNSols, 0) or 0)
    primal_bound = _safe_call(model.getPrimalbound)
    if primal_bound is None and solution_count > 0:
        primal_bound = _safe_call(model.getObjVal)
    result = BaselineResult(
        instance=str(instance.get("name", Path(instance_path).stem)),
        task_count=len(data["tasks"]),
        vehicle_count=len(data["R"]),
        sortie_count=len(data["S"]),
        variable_count=original_variable_count,
        constraint_count=original_constraint_count,
        status=_status_name(_safe_call(model.getStatus, "unknown")),
        primal_bound=round_float(primal_bound),
        dual_bound=round_float(_safe_call(model.getDualbound)),
        gap=round_float(_safe_call(model.getGap)),
        solving_time=round_float(_safe_call(model.getSolvingTime, 0.0)),
        node_count=round_float(_safe_call(model.getNNodes, 0.0)),
        memory_mb=round_float(_safe_call(getattr(model, "getMemUsed", lambda: None))),
        log_path=str(log_path),
        instance_path=str(instance_path),
        seed=seed,
    )
    return result


def _write_result_csv(path: Path, result: BaselineResult) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BaselineResult.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerow(result.to_row())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行单个 JSON 实例的纯 SCIP compact MILP baseline。")
    parser.add_argument("--instance-path", required=True, help="实例 JSON 路径。")
    parser.add_argument("--time-limit", type=float, default=3600.0, help="SCIP 时间限制，单位秒。")
    parser.add_argument("--results-csv", help="可选：写出单行结果 CSV。")
    parser.add_argument("--log-path", help="可选：SCIP 日志路径。")
    parser.add_argument("--seed", type=int, default=20260511)
    parser.add_argument("--quiet", action="store_true", help="隐藏 SCIP 控制台日志。")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    instance_path = Path(args.instance_path)
    instance = read_json(instance_path)
    pairwise = build_task_closure(instance, weight="cost")
    instance_name = str(instance.get("name", instance_path.stem))
    log_path = Path(args.log_path) if args.log_path else ROOT / "results" / "logs" / "scip_baseline" / f"{instance_name}.log"
    scip_params = {
        "display/verblevel": 0 if args.quiet else 4,
        "randomization/randomseedshift": int(args.seed),
        "randomization/permutationseed": int(args.seed),
        "randomization/lpseed": int(args.seed),
        "parallel/maxnthreads": 1,
    }
    result = solve_scip_baseline(
        instance,
        pairwise,
        instance_path=instance_path,
        time_limit=float(args.time_limit),
        log_path=log_path,
        scip_params=scip_params,
        seed=int(args.seed),
        verbose=not args.quiet,
    )
    if args.results_csv:
        _write_result_csv(Path(args.results_csv), result)
    print(
        f"{result.instance}: status={result.status}, primal={result.primal_bound}, "
        f"dual={result.dual_bound}, gap={result.gap}, time={result.solving_time}s, "
        f"nodes={result.node_count}, vars={result.variable_count}, cons={result.constraint_count}"
    )


if __name__ == "__main__":
    main()
