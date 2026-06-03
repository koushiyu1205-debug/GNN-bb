# BPC_future

`BPC_future/` is a self-contained trip-time Branch-Price-and-Cut prototype. It is
separate from the legacy `bpc/` and `branchpricecut/` trees.

For the current full model/data/solver description, including how
`low_time`, `low_energy`, and `low_risk` path options are generated and selected
inside pricing, see `BPC_future/docs/bpc_future_model_design.md`.

The v1 master uses timed single-sortie trip columns:

```text
theta[tau, r] = vehicle r selects timed trip tau
```

The RMP contains task cover, vehicle sortie count, vehicle time-occupation rows,
task-vehicle linking, vehicle ordering, and pricing-compatible branch rows.
For Moon Trek logical graphs, each directed logical edge keeps the fixed
physical path options generated upstream (`low_time`, `low_energy`, and
`low_risk`, after Pareto de-duplication). Pricing enumerates task sequences and
path-option combinations, then places the timed trip on event/bucket start
candidates instead of scanning every 1-minute start time. Heuristic pricing can
add columns but never proves a node. A node bound is proof-relevant only after
the configured exact pricing universe is exhausted.

The v1 exactness boundary is explicit: it is exact only for the configured
fixed path-option and start-candidate trip universe. If pricing hits sequence,
timed-evaluation, or wall-time limits, the node is marked incomplete and cannot
prove optimality. The next exactness milestone is continuous-time pricing over
the same fixed physical path options.

The current Python prototype now adapts four mature ideas from `bpc_clean`
without importing legacy solver modules:

- two-phase RMP: phase 1 minimizes artificial cover only, then phase 2 switches
  to true trip and fleet costs;
- exact-safe pricing pruning: capacity/energy lower-bound prechecks are used in
  exact pricing, while path-option Pareto pruning/caps are heuristic-only unless
  the pricing result is marked incomplete;
- diverse column selection: heuristic pricing prefers a mix of best reduced
  cost, task coverage, and task-set diversity instead of flooding the RMP with
  near-duplicates;
- early pool-integer heuristic: the current restricted pool can improve the
  incumbent, but it never proves a node before exact pricing exhaustion.

Run the smoke config:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/very_small.yaml
```

Run 20-task plumbing smoke commands:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/bench_20_smoke.yaml \
  --instances bench_20_01 bench_20_02 \
  --time-limit 20
```

`bench_20_smoke.yaml` is intentionally capped. It validates instance loading,
Trip-Time RMP construction, CG logging, and output files; it is not a full
20-task proof configuration.

Run the generated Moon Trek 5-task path-option smoke:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_smoke.yaml
```

Run the generated Moon Trek 20-task capped smoke:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_20_smoke.yaml
```

Build the deterministic Moon Trek physical-risk patch:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py
```

The default site remains Apollo 15. A flatter 20 km x 20 km Balmer Basin NAC
patch can be built with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py \
  --site balmer_flat
```

For a smoother, more complete mare patch, use the ApolloZone DEM preset. This
site derives slope deterministically from the downloaded DEM because Moon Trek
does not expose a paired slope layer for that global product:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py \
  --site crisium_smooth
```

For a Balmer-like but continuous patch, use the Mare Tranquillitatis preset:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_moon_trek_patch.py \
  --site tranquillitatis_balmer_like
```

The preprocessing layer downloads fixed DEM/Slope GeoTIFFs from NASA Moon Trek,
computes an auditable slope/roughness risk grid, and writes manifests under the
selected `BPC_future/data/moon_trek/<patch>/` directory. See
`BPC_future/docs/moon_trek_preprocessing.md`.

Draw the terrain/risk figures and sample a radius-10 km operational scenario:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py
```

For the smoother Crisium patch:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py \
  --terrain-dir BPC_future/data/moon_trek/crisium_smooth_20km
```

For the Balmer-like Tranquillitatis patch:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/draw/draw_moon_trek_patch.py \
  --terrain-dir BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km
```

Figures are written under `BPC_future/draw/figures/<patch>/`, and the sampled
depot/task scenario is written under `BPC_future/draw/scenarios/<patch>/`. The
depot is fixed at `(10.0, 10.0)` km, tasks are randomized only on passable cells
in the depot's connected passable component, and the sampled scenario enforces
the configured vehicle roundtrip screen.

Build the lower physical grid graph and logical task graph for a sampled
scenario:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_terrain_graph.py \
  --terrain-dir BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km \
  --scenario BPC_future/draw/scenarios/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_region_seed7_tasks20.json \
  --grid-size 256
```

This writes graph JSON and visualizations under
`BPC_future/draw/graphs/<patch>/`.

Generate the 60-instance Moon Trek multi-sortie CVRPTW dataset:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/generate_moon_trek_benchmark.py \
  --task-counts 5,10,20 \
  --instances-per-size 10 \
  --min-point-spacing-km 3.0 \
  --vehicle-max-roundtrip-km 30.0 \
  --vehicle-max-roundtrip-energy-proxy 70.0 \
  --usable-battery-capacity-proxy 80.0 \
  --recharge-power-proxy-per-min 2.0 \
  --grid-size 256
```

The generated dataset is written under
`BPC_future/data/generated/moon_trek_60/`. Each accepted instance is a complete
directed logical graph, and every task must have at least one physical
`depot -> task -> depot` option pair that satisfies the configured roundtrip
path-distance and energy-proxy budgets.

Scheduling fields can be re-applied without regenerating the physical paths:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/augment_moon_trek_scheduling.py \
  --manifest BPC_future/data/generated/moon_trek_60/manifest.json
```

The deterministic scheduling policy is:

```text
each sortie starts at the depot with a full battery
the vehicle completes one or more tasks
task service starts exactly at arrival, so task waiting is not allowed
the sortie returns to the depot
the depot has unlimited chargers
the vehicle recharges to full before its next sortie
```

Recharge time is computed from the energy used by the completed sortie:

```text
energy_used_proxy =
  travel_energy_proxy
  + service_energy_proxy
  + survival_energy_proxy_per_min * sortie_elapsed_before_recharge_min

recharge_time_min = energy_used_proxy / recharge_power_proxy_per_min
```

The current generated data uses `recharge_power_proxy_per_min = 2.0`, so a
sortie that uses `60.0` energy-proxy units requires `30.0` minutes of depot
recharge before the next sortie. Energy is still a deterministic proxy until a
physical rover battery model is calibrated.

Battery semantics in the generated data are deliberately conservative:

```text
usable_battery_capacity_proxy = 80.0
survival_energy_reserve_proxy = 10.0
max_roundtrip_energy_proxy = 70.0
```

The BPC model enforces `travel + service + survival-during-sortie <= 70.0`.
The remaining `10.0` proxy units are treated as a survival reserve and cannot be
spent by route construction. This prevents a sortie from returning with an empty
battery in the abstract model.

Fleet sizing and cuts are also configuration-controlled in `BPC_future`. The
Moon Trek smoke configs use:

```yaml
fleet_bound_mode: "computed"
fleet_bound_slack: 1
fleet_bound_cost_safe: true
cuts_enabled: true
fleet_lower_bound_cut_enabled: true
sortie_lower_bound_cut_enabled: true
subset_row_cuts_enabled: true
```

The computed fleet bound is applied in memory after loading an instance; it does
not rewrite the generated JSON. A constructive single-task schedule gives a
feasible upper bound `UB` and vehicle count `R_feas`. The active vehicle upper
bound is reduced only when the fixed vehicle cost proves that using more
vehicles cannot beat `UB`; otherwise the loader falls back to an objective-safe
cap. The master still decides actual vehicle use through `y[r]`.

Current cuts are pricing-compatible: their coefficients are computed for every
new priced column and included in reduced-cost calculations. In the trip-time
master this includes fleet lower-bound, sortie lower-bound, time-point, and
small subset-row rows. In the current journey-column master, fleet lower-bound
and subset-row rows are supported. The sortie lower-bound row is deliberately
not enabled for journey columns yet, because its coefficient depends on the
number of sorties inside a journey and would invalidate the current
same-task-set column dominance rule unless that dominance is disabled.
