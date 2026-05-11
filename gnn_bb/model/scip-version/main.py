import argparse
import time

from src.instance_data import build_instance
from src.io_utils import ensure_dir, log, project_path, write_json
from src.path_milp import build_path_milp
from src.route_generation import generate_routes
from src.solve import solve_path_model
from src.terrain import build_task_closure
from src.validation import validate_solution


def parse_args():
    parser = argparse.ArgumentParser(description="Path-based SCIP MILP for terrain CVRPTW instances.")
    parser.add_argument("--instance", default="very_small", choices=["very_small", "medium"])
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--max-route-tasks", type=int, default=4)
    parser.add_argument("--successor-limit", type=int, default=5)
    parser.add_argument("--max-routes", type=int, default=10000)
    parser.add_argument("--output-dir", default="outputs")
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("--verbose", dest="verbose", action="store_true", default=True, help="show SCIP solver log (default)")
    verbosity.add_argument("--quiet", dest="verbose", action="store_false", help="hide SCIP solver log")
    return parser.parse_args()


def timed(label, func):
    started = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - started
    log(f"{label}: {elapsed:.3f}s")
    return result


def main():
    args = parse_args()
    output_dir = ensure_dir(project_path(args.output_dir))

    instance = timed("Build instance", lambda: build_instance(args.instance))
    instance_path = output_dir / f"instance_{args.instance}.json"
    write_json(instance_path, instance)
    log(f"Instance written to {instance_path}")

    pairwise = timed("Build task closure", lambda: build_task_closure(instance, weight="cost"))
    routes, route_report = timed(
        "Generate feasible routes",
        lambda: generate_routes(
            instance,
            pairwise,
            max_route_tasks=args.max_route_tasks,
            successor_limit=args.successor_limit,
            max_routes=args.max_routes,
        ),
    )
    route_path = output_dir / f"routes_{args.instance}.json"
    write_json(route_path, {"report": route_report, "routes": routes})
    log(f"Routes written to {route_path}")
    log(f"Route generation summary: {route_report}")

    model, variables, metadata = timed("Build path MILP", lambda: build_path_milp(instance, routes))
    solution = timed(
        "Solve path MILP",
        lambda: solve_path_model(model, variables, metadata, time_limit=args.time_limit, verbose=args.verbose),
    )
    validation = validate_solution(instance, routes, solution)
    solution["route_generation"] = route_report
    solution["validation"] = validation

    solution_path = output_dir / f"solution_{args.instance}.json"
    write_json(solution_path, solution)
    log(f"Solution written to {solution_path}")
    log(f"SCIP summary: {solution['summary']}")
    log(f"Validation: {validation}")


if __name__ == "__main__":
    main()
