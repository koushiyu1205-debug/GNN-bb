# SCIP Path-Based CVRPTW Model

This version replaces the arc-recursion MILP with a path-based MILP.

The workflow is:

1. Build a reproducible terrain instance.
2. Compute shortest-path closures between the base and task nodes.
3. Generate feasible sortie routes that already satisfy time windows, load, and battery limits.
4. Solve a set-partitioning MILP that chooses generated routes for vehicle-sortie slots.
5. Validate coverage and resource limits.

Because route feasibility is handled before the MILP, the master problem does not need the old time/load/energy Big-M recursion constraints.

## Run

```bash
cd /home/kai/work/gnn_bb/model/scip-version
python3.12 main.py --instance very_small --time-limit 30
python3.12 main.py --instance medium --time-limit 60
```

Outputs are written to `outputs/`:

- `instance_<name>.json`
- `routes_<name>.json`
- `solution_<name>.json`

Useful route-generation controls:

```bash
python3.12 main.py --instance medium --max-route-tasks 4 --successor-limit 6 --max-routes 10000
```

Notes:

- The generated route pool is exact only for the generated routes. Smaller `successor-limit` and `max-routes` values make the model faster but more heuristic.
- Singleton routes are always generated first, so each feasible task has a fallback route.
- Default medium settings generate about 1.3k routes, which gives about 26k route-slot binaries for 5 vehicles and 4 sorties.
