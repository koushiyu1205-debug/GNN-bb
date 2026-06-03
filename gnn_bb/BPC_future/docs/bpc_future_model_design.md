# BPC_future Model And Path-Option Design

This document records the current `BPC_future/` model, data pipeline, and solver
logic. The design goal is an exact, auditable multi-sortie CVRPTW solver on a
Moon Trek-derived physical map, while preserving a clear path toward faster
20-task proofs.

## 1. Scope

`BPC_future/` is independent of the legacy `bpc/` and `branchpricecut/`
implementations. It reads existing benchmark JSON files and the new Moon Trek
logical graph JSON files, but does not import legacy solver, pricing, checker,
or oracle modules.

The current model is exact for this configured universe:

- fixed depot and task points;
- fixed directed logical graph;
- fixed physical path options per directed logical edge;
- fixed event/bucket start-time candidates;
- fixed BPC configuration, including path-option and pricing budgets.

If pricing hits a time, sequence, path-option, or timed-evaluation limit, the
node is marked incomplete and cannot prove optimality.

## 2. Physical Network Layer

The upper terrain layer starts from NASA Moon Trek raster data. The current
patches include Apollo 15 and a Balmer-like Tranquillitatis region. Each patch
is a 20 km by 20 km area saved under:

```text
BPC_future/data/moon_trek/<patch>/
  raw/dem.tif
  raw/slope.tif
  metadata/*.json
  processed/risk_grid.npz
  processed/risk.tif
  processed/impassable.tif
```

The deterministic risk layer is:

```text
risk = 0.75 * (slope / impassable_slope)^2
     + 0.25 * min(local_dem_std / roughness_reference, 1)
```

Cells with slope at or above the configured impassable threshold, currently
30 degrees, are treated as blocked. The risk model is intentionally simple:
it is a physical/rule-based preprocessing layer, not a stochastic predictor
inside BPC. Once preprocessing finishes, BPC sees fixed deterministic metrics.

The operational scenario fixes the depot at `(10.0, 10.0)` km. Tasks are sampled
inside a radius-10 km operating circle, only on passable cells in the depot's
connected passable component. Current benchmark generation also enforces a
minimum 3 km task spacing and rejects instances with unreachable tasks.

## 3. Lower Physical Graph

The terrain raster is downsampled into an implicit 8-neighbor graph. Each
passable coarse cell is a physical graph node. Neighbor edges are directed and
carry terrain-dependent metrics.

For a physical edge from cell `u` to neighbor cell `v`, the current formulas use:

```text
avg_risk      = average risk of u and v
avg_slope     = average slope of u and v
uphill_grade  = max(0, elevation(v) - elevation(u)) / edge_distance_m
slope_penalty = (avg_slope / 30)^2
```

The edge metrics are then:

```text
generalized_cost = distance_km *
  (1 + risk_weight * avg_risk
     + slope_weight * slope_penalty
     + uphill_weight * uphill_grade)

speed_kmh = base_speed_kmh /
  (1 + 1.5 * avg_risk
     + 2.0 * slope_penalty
     + 2.0 * uphill_grade)

travel_time_h = distance_km / max(speed_kmh, min_speed_kmh)

energy_proxy = distance_km *
  (1 + energy_risk_weight * avg_risk
     + energy_uphill_weight * uphill_grade
     + slope_penalty)

risk_integral = distance_km * avg_risk
```

The formulas are deterministic and asymmetric when elevation changes differ by
direction.

## 4. Logical Nodes And Complete Logical Graph

The logical node set is:

```text
V_L = {depot, task_1, ..., task_n}
```

For every ordered pair `(i, j), i != j`, the preprocessing layer computes
physical shortest paths on the lower physical graph. The accepted Moon Trek
benchmark instances are complete directed logical graphs: every ordered pair
has at least one feasible physical path option.

Each logical edge stores full physical path geometry and metrics in JSON:

```text
path_cells
path_xy
path_distance_km
travel_time_min
energy_proxy
risk_integral
generalized_cost
path_type
aliases
```

The BPC solver uses the fixed logical graph. It does not call raster code,
Dijkstra, A*, or risk prediction during optimization.

## 5. The Three Path Options

For each origin node, preprocessing runs three Dijkstra searches to all logical
targets:

```text
low_time   : shortest path by travel_time_h
low_energy : shortest path by energy_proxy
low_risk   : shortest path by risk_integral
```

These are not three arbitrary drawings. They are three deterministic shortest
paths under three different physical objectives. A directed pair can have one,
two, or three retained options:

- if all three objectives produce the same physical geometry, only one option is
  stored and its `aliases` records the duplicate types;
- if two paths are nearly identical in geometry and metrics, they are
  de-duplicated;
- otherwise up to three options are kept.

The de-duplication rule first checks exact same cell sets. It also treats two
paths as duplicates when cell-overlap Jaccard similarity is high and all key
metrics are within the configured relative tolerance:

```text
path_distance_km
risk_integral
energy_proxy
travel_time_min
generalized_cost
```

This is why a plotted edge may show fewer than three visible paths: the missing
type was merged into another option as an alias.

## 6. How Path Options Enter The Objective

Path options are fixed candidates, but BPC does not collapse each node pair to
one cheapest edge. Pricing explicitly chooses a path option for every leg in a
trip.

For Moon Trek logical graphs, each option receives a normalized scalar cost:

```text
option_cost =
  w_distance * distance_km / ref_distance
  + w_energy * energy_proxy / ref_energy
  + w_risk * risk_integral / ref_risk
```

The current default weights are:

```text
w_distance = 1.0
w_energy   = 0.25
w_risk     = 8.0
```

The references are computed from the generated option pool so distance, energy,
and risk are comparable in scale. The large risk weight is intentional: risk is
a first-class deterministic cost term, not only a preprocessing tie-breaker.

The loader Pareto-filters path options by physical metrics and sorts them by
scalar cost, but it keeps non-dominated alternatives. A trip column therefore
contains:

```text
task sequence + chosen path option for every leg + start time
```

The trip cost is:

```text
sum selected option_cost + sum service_cost
```

The full route feasibility uses the selected options' travel time and energy,
not only the scalar objective cost.

## 7. Multi-Sortie Vehicle Policy

Each sortie follows this deterministic policy:

```text
start at depot with full battery
serve one or more tasks
task service starts exactly at arrival
no waiting at task
return to depot
recharge to full before next sortie
depot waiting is allowed
depot chargers are unlimited
```

The current battery semantics are:

```text
usable_battery_capacity_proxy = 80
survival_energy_reserve_proxy = 10
max_roundtrip_energy_proxy    = 70
```

BPC enforces:

```text
travel_energy_proxy
+ service_energy_proxy
+ survival_energy_proxy_per_min * sortie_elapsed_before_recharge_min
<= 70
```

The remaining 10 proxy units are reserved for survival energy and cannot be
spent by routing. Recharge time is:

```text
recharge_time_min = energy_used_proxy / recharge_power_proxy_per_min
```

With the current default `recharge_power_proxy_per_min = 2.0`, a sortie using
60 energy-proxy units occupies 30 minutes of depot recharge time before the
same vehicle can start its next sortie.

## 8. Trip-Time Master

The current master column is a timed single-sortie trip:

```text
theta[tau, r] = vehicle r selects timed trip tau
```

A timed trip includes:

```text
ordered tasks
path option ids for depot/task/task/depot legs
start_time
service_start times
return time
recharge-inclusive end_time
load
energy
risk
distance
cost
time bucket occupation coefficients
```

The RMP contains:

- task cover: each task is covered exactly once;
- task-vehicle linking: a vehicle must be active if it serves a task;
- sortie count: each vehicle has a max number of sorties;
- time occupation: a vehicle cannot execute overlapping sortie/recharge
  intervals;
- vehicle ordering: homogeneous vehicle symmetry reduction;
- branch rows;
- pricing-compatible cuts.

This is different from the old route-vehicle master. The old master could pick
several individually feasible routes for the same vehicle and only later check
whether they formed a real schedule. The Trip-Time master projects much more of
the schedule feasibility into the RMP through timed trip columns and vehicle
time occupation rows.

## 9. Pricing

Pricing enumerates:

```text
task sequence
path option combination for all legs
event/bucket start candidates
```

It evaluates each feasible timed trip and computes reduced cost from current
RMP duals. The exact pricing result can certify a node only if it exhausts the
configured search universe.

The current implementation includes four migrated ideas from the mature
`bpc_clean` line:

1. two-phase RMP;
2. exact-safe resource prechecks;
3. diverse column selection for heuristic pricing;
4. early restricted-pool integer heuristic.

The active speed target is deliberately stronger than the current prototype:

```text
5 tasks  : prove optimality within 10 seconds
10 tasks : prove optimality within 40 seconds
20 tasks : prove optimality within 120 seconds
```

The solver must use the same exact Trip-Time BPC algorithm for all three
scales. Small instances must not switch to a separate complete-enumeration MIP
solver as the official path. Complete enumeration is allowed only as a
diagnostic tool, not as a reported algorithmic shortcut.

The exact-safe resource precheck removes sequences that cannot fit capacity or
cannot satisfy even a lower bound on energy. It is safe because it only removes
provably infeasible sequences.

Heuristic-only path-option pruning/caps can accelerate column discovery, but
they do not prove anything. If an exact pricing call uses a cap or prunes a
non-certified option, the node must remain incomplete.

Recent exact-safe pricing changes are:

- timed-trip construction cache: once a sequence/path/start candidate has been
  evaluated, later vehicles and later column-generation rounds reuse the same
  feasible timed trips and only recompute reduced cost under the new duals;
- exact pricing stop-after-columns: when exact pricing has already found true
  negative reduced-cost columns, it returns to the RMP instead of continuing to
  price other homogeneous vehicles under stale duals. This is exact-safe because
  the node is not certified until a later exact pricing pass exhausts the full
  pricing universe without negative columns;
- delayed certificate mode: complete pricing scans are triggered only after the
  RMP bound is close to the incumbent and after a configured minimum number of
  CG rounds. This avoids wasting most of the time budget on a complete scan of
  the initial restricted pool, where strong negative columns still exist;
- certificate bulk return with early negative stop: in certificate mode, exact
  pricing still proves a node only when the pricing universe is exhausted with
  no negative columns. If negative columns are found, pricing may stop after a
  configured bulk count, return those columns, and mark the scan non-exhaustive.
  This is exact-safe because the node is not certified until a later exhaustive
  pass finds no negative column;
- time-placement reduced-cost dominance: if all time-occupation duals for a
  vehicle are zero, then all feasible start placements of the same
  sequence/path-option combination have identical reduced cost. Exact pricing
  checks one representative placement in that case. This preserves the pricing
  certificate because no omitted placement can have lower reduced cost under
  zero time duals;
- batched negative-column return: a pricing pass can return several negative
  timed placements/path choices per task sequence, so already evaluated
  candidates are not discarded;
- lightweight pricing columns: generated RMP columns store resource metrics and
  `arc_option_ids`, but do not copy the full physical path geometry into every
  timed-trip object. The physical geometries remain in the logical-graph JSON
  and can be reconstructed from the option ids. This keeps the exact same
  mathematical column while reducing Python object construction time and memory
  during certificate pricing;
- initial composite seed columns: before the first RMP solve, the solver may
  call the same pricing routine with deterministic artificial cover bonuses to
  add a small, budgeted set of multi-task timed trips. These columns are only a
  warm start for the restricted master; they do not certify a node, do not
  replace exact pricing, and use the same trip feasibility logic as every later
  pricing round;
- incumbent-derived fleet upper cut: after a valid incumbent is found, the
  solver can add

```text
sum_r y[r] <= floor((incumbent - unavoidable_nonvehicle_cost_lb) / fixed_vehicle_cost)
```

  when this bound is smaller than the current fleet upper bound. The cut is
  valid because any solution using more vehicles has fixed-vehicle cost plus an
  unavoidable non-vehicle lower bound no better than the incumbent.
- root symmetry fleet prefix disable: at nodes without vehicle-specific branch
  constraints, if the incumbent-derived upper bound says at most `K` homogeneous
  vehicles are needed, vehicles `K+1...R` are disabled. This is not a different
  model; it uses the existing vehicle-ordering symmetry and avoids fractional
  LP mass and pricing work on symmetric vehicles that can be renumbered into
  the first `K` positions.
- static root subset-row cuts: small subset-row cuts can be inserted at root
  before column generation. They are pricing-compatible, so every future timed
  trip can compute its coefficient. For 5-task instances the full small-subset
  family is cheap; for 10- and 20-task instances the same separator must be
  budgeted. A large static cut set can make the root RMP slower than pricing and
  delay incumbent discovery, so the 10-task smoke uses a smaller static budget.
- column cleanup: the RMP pool is periodically reduced by keeping positive LP
  columns, incumbent columns, one single-task safety column per task, and a
  bounded number of cheap columns per task set. This does not delete the pricing
  universe. Removed timed trips can be regenerated by exact pricing later, so
  cleanup is a memory/RMP-degeneracy control rather than a heuristic
  restriction.
- restricted-pool integer throttling: the pool MIP is a primal heuristic, not a
  certificate. It is skipped once the RMP column pool exceeds a configured
  threshold, because large degenerate pools can spend most of the short 5-task
  budget inside a heuristic MIP after a good incumbent is already known. This
  does not affect lower bounds or exactness;
- duplicate negative pricing candidates do not block certification: a generated
  trip signature may already be present in the RMP, and an existing variable at
  its upper bound can still have negative reduced cost. That is not a missing
  column. A node is certified when exact pricing exhausts the configured
  universe and no new trip signature is added;
- sequence reduced-cost lower-bound pruning: before expanding a task order into
  all path-option and start-time combinations, exact pricing computes a
  sign-safe lower bound on the reduced cost of any timed trip with that order.
  If the lower bound is already nonnegative, the sequence is skipped. This uses
  minimum possible path cost, exact task/cut dual coefficients, and a conservative
  occupation-dual bound; branch nodes fall back to full checks for branch rows;
- guarded exact path-combination dominance: for a fixed task order, a path-option
  combination dominated in cost, duration, energy, and risk by another
  combination is skipped when all time-occupation duals for the vehicle are
  nonpositive. If any positive occupation dual appears, exact pricing disables
  this dominance and expands all combinations. Safe dominance pruning still
  counts as exhaustive pricing for certification; unsafe heuristic pruning does
  not;
- certificate bulk guard: certificate pricing still returns many negative
  columns in batches before attempting a full no-negative-column certificate.
  This reduces RMP resolve churn while preserving the rule that only exhausted
  exact pricing can certify a node.

### Restart And Child-Ordering Experiments

The journey branch-price driver now has an opt-in exact-safe journey-pool
restart hook. It rebuilds only the finite RMP column pool and keeps active LP
columns, incumbent columns, recent priced columns, singleton safety columns, and
cheap task-set representatives. It never restricts the pricing universe, never
creates a certificate, and never changes the official lower bound. A restart
event is therefore a degeneracy/RMP-memory control only.

The first 20-task Apollo trial showed that root restart is harmful. With
`journey_pool_restart_trigger: degenerate_flat,fixed_interval` and no depth
guard, a fixed-interval root restart at CG iteration 8 reduced the pool from
538 to 219 journeys, but changed the root Ryan-Foster branch from the protected
path and ended at `primal=486.568881` in 200s. The protected branch trial reached
`486.081224`. The restart configuration was therefore changed to support
`journey_pool_restart_min_depth`; experimental restart configs should keep this
at least `1` so the root column-generation path is not disturbed.

With `journey_pool_restart_min_depth: 1`, the restart trial matched the protected
20-task branch result (`TIME_LIMIT`, `primal=486.081224`, no official dual bound,
3 processed nodes). No restart triggered before the 200s limit because the
branch-node progress classification was still mostly `objective_improved`.
Conclusion: restart is exact-safe and useful as a diagnostic/cleanup option, but
it is not the current proof-time bottleneck.

Two exact-safe child ordering experiments were also added:

- `journey_child_priority_mode: lp_rounding` first processes the child matching
  the current fractional Ryan-Foster mass rounded to 0/1.
- `journey_child_priority_mode: lp_rounding_wide_tie` does the same, but when
  the mass is exactly 0.5 it first processes the child with more currently
  allowed journey columns.

Both only change heap insertion order; both children are still queued and exact
pricing remains responsible for all certificates. On the current Apollo 20-task
trial, `lp_rounding` matched the protected result because the root branch mass
was exactly `0.5` and the declared order was unchanged. The wide-tie variant did
change the root order and processed `RF(1,3)=separate_vehicle` first, but it
worsened the incumbent path to `487.624693` in 200s. This indicates a strong
column-pool path dependency: the better incumbent appears after the protected
`same_vehicle` child enriches the global journey pool before the separate child
is processed. For now, the protected branch order remains the better baseline,
and child-order variants should stay experimental.

The current unsolved 20-task bottleneck is therefore branch-node journey pricing
proof, not merely RMP restart or child order. At 200s the useful incumbent is
known, but exact pricing still finds negative journeys or returns incomplete
near the time limit, so no official dual bound can be reported.

  columns, but the bulk size is bounded to avoid one pricing pass creating an
  oversized RMP that is slower than several smaller exact CG rounds. If the
  guard is hit, the scan is non-exhaustive and another exact pricing pass is
  required;
- time-grid calibration: the current Moon Trek smoke configuration uses a
  10-minute time bucket and 10-minute pricing start step after testing 20-minute
  buckets. The coarser 20-minute grid reduced some start placements but degraded
  incumbent quality on Apollo 15, so it is not the current candidate. This keeps the same
  Trip-Time BPC algorithm but changes the configured discretized trip universe.
  The solver remains exact for that configured universe. Finer grids are more
  faithful but currently too slow for the active 5/10/20 second-level targets.

## 10. Phase 1 And Phase 2 RMP

The solver now uses a mature two-phase structure.

Phase 1:

```text
minimize sum artificial_cover[i]
```

Trip and vehicle fixed costs are zero. Artificial cover variables appear only
in phase 1. This avoids million-penalty artificial variables distorting the
dual values.

Phase 2:

```text
minimize fixed_vehicle_cost * used_vehicles + selected trip costs
```

Phase 2 starts only after artificial cover is driven to zero. Bounds, incumbent
comparison, cuts, branching, and proof-relevant pricing are phase-2 concepts.

## 11. Pricing-Compatible Cuts

The current cut direction is pricing-compatible only. A cut is allowed only if
new priced columns can compute its coefficient, so its dual can enter reduced
cost consistently.

Implemented trip-time cuts:

- fleet lower-bound cut;
- sortie lower-bound cut;
- subset-row cuts;
- time-point vehicle-capacity cuts:

```text
sum_{trip covers time t} theta[trip,r] <= y[r]
```

The time-point cut is separated from current LP overlap activity, but it is not
finite-support. Any future trip generated by pricing can compute whether it
covers the separated time point, so the cut dual is included in reduced cost.
This tightens the previous bucket-occupation relaxation and moves the model
closer to the intended continuous no-overlap vehicle schedule.

The journey-column master has a narrower supported cut set:

- fleet lower-bound cut, with coefficient `1` for every nonempty journey;
- subset-row cuts, with coefficient `floor(|J task_set intersect S| / k)`.

The sortie lower-bound cut is intentionally not added to the journey master at
this stage. Its coefficient would be `-number_of_sorties(J)`, which is not a
function of the final task set alone. The current journey pool and pricing
oracle use a same-task-set dominance rule to suppress equivalent columns; adding
a sortie-count row without disabling that dominance could delete a column that
has a different cut coefficient. The config key may remain enabled for the
trip-time master, but journey runs log it as unsupported instead of silently
adding an unsafe row.

Finite-support route-signature cuts are not the main direction in
`BPC_future`, because they do not penalize newly generated columns in pricing
and tend to create a "hit one route, generate a near replacement" effect.

## 12. Incumbent Heuristic

The restricted-pool integer heuristic solves the current column pool as a MIP.
It can improve the primal incumbent early, but it cannot prove a node. A node is
complete only after exact pricing certifies that no negative reduced-cost column
remains in the configured pricing universe.

## 13. Smoke Commands

Run the current 5-task Moon Trek smoke on one Apollo 15 and one Tranquillitatis
instance:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_smoke.yaml \
  --time-limit 3600
```

This command writes:

```text
BPC_future/results/bpc_future_moon_trek_5_smoke.csv
BPC_future/results/logs/moon_trek_5_smoke/
BPC_future/results/solutions/moon_trek_5_smoke/
```

Run the same Trip-Time BPC path on the 10-task smoke pair:

```bash
cd /home/kai/work/gnn_bb
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_10_smoke.yaml \
  --time-limit 40
```

This command writes:

```text
BPC_future/results/bpc_future_moon_trek_10_smoke.csv
BPC_future/results/logs/moon_trek_10_smoke/
BPC_future/results/solutions/moon_trek_10_smoke/
```

## 14. Current Bottleneck

The 5-task model is now much cleaner than the first Trip-Time prototype, but
the remaining bottleneck is exact pricing certificate time. Even for 5 tasks,
exact pricing may still enumerate many combinations of:

```text
task order x path options x feasible start placements x vehicle
```

The next major speed step should focus on a stronger exact pricing engine:

- tighter label dominance using time, energy, risk, and occupation effects;
- continuous/event start interval dominance instead of many sampled starts;
- faster exact pricing certificates that use the same pricing algorithm across
  5-, 10-, and 20-task instances, without switching small instances to a
  separate complete-enumeration MIP;
- eventually, a native pricing kernel only if Python pricing remains the hard
  bottleneck.

Full trip-universe enumeration is allowed only as an offline diagnostic for
pricing validation. It must not become the official proof path for 5- or
10-task instances, because that would use a different algorithm than the
20-task solver and would make the timing targets incomparable.

## 15. Exact Start Optimization In Pricing

The current exact pricing path now has an optional no-waiting start optimizer,
enabled in the Moon Trek smoke configs by:

```yaml
exact_start_optimization_enabled: true
```

This is still the same Trip-Time BPC algorithm. It does not enumerate the full
trip universe as a separate MIP and it does not use heuristic pricing as a
certificate. For a fixed task sequence and fixed path-option tuple, the
non-time reduced-cost terms are constant. The only start-dependent term is the
time-occupation dual contribution. Since occupation is bucketed, that term is
piecewise linear in the sortie start time. The exact pricing code therefore
checks only the breakpoints where:

```text
trip start crosses a time bucket boundary
trip end crosses a time bucket boundary
the feasible start interval begins or ends
```

If all these breakpoint reduced costs are nonnegative, no start time for that
fixed sequence/path tuple can produce a negative reduced-cost column in the
configured Trip-Time master. Real `TimedTrip` objects are constructed only for
negative breakpoint starts. This cuts object construction and exact pricing
time while preserving the certificate logic.

The optimizer is guarded:

- it is used only for strict no-waiting task service, where the trip duration
  is fixed by the sequence and path options;
- branch nodes and unknown future cut types fall back to the older full start
  scan;
- all candidate columns still use the same `manual_reduced_cost()` validation
  before entering the RMP.

The implementation also avoids constructing bucket-occupation dictionaries
while testing candidate starts. Pricing computes the time-dual overlap directly
and constructs a full `TimedTrip` only for a truly negative reduced-cost start.
The sequence/path/start physical profiles and bucket-overlap coefficients are
cached for the node, so later CG rounds reuse the same feasible structure and
only redo the reduced-cost dot product with the current duals.
Time-point capacity cut duals are handled in the same exact start optimization:
the separated time points add start breakpoints at `t` and `t - trip_duration`
with small one-sided checks around the discontinuity.

If a pricing round has no start-dependent duals at all, all feasible starts for
one fixed task sequence and path-option tuple have identical reduced cost. In
that case exact pricing evaluates only one representative start. This is an
exact reduction, not a heuristic, because no omitted start can have a different
reduced cost in that round.

An experimental switch can return only the best start for each fixed
sequence/path tuple:

```yaml
exact_best_start_per_path_profile_enabled: false
```

This remains exact for detecting whether that tuple has a negative reduced-cost
start, but early tests made 10-task primal progress worse because non-best
starts can still be useful in later schedule combinations. It is therefore kept
off in the smoke configs.

There is an experimental non-certificate early-stop switch for fixed-sequence
negative starts:

```yaml
exact_early_stop_negative_per_sequence_enabled: false
```

When enabled, a non-certificate exact pricing round can stop scanning one fixed
sequence as soon as its per-sequence negative-column budget is met. Such a
result is explicitly marked non-exhaustive and can never certify a node. The
switch remains off in the smoke configs because early experiments made the CG
loop too fragmented on 10-task instances.

## 16. Active-Vehicle Compression From Fleet Prefix Cuts

`BPC_future` may start with a conservative computed `R_bar`. Once a feasible
incumbent proves that vehicles above a prefix cannot be part of an improving
solution, the solver adds a pricing-compatible `fleet_prefix_disable` cut. The
RMP and restricted-pool integer heuristic now use that cut structurally:

```text
disabled vehicles do not receive y variables
disabled vehicles do not receive theta variables
disabled vehicles are treated as y = 0 in fleet cuts
```

This is not a heuristic reduction. It is exactly equivalent to keeping those
variables and enforcing `y_r = 0`, but it avoids a large number of zero-forced
trip-vehicle variables after the first good incumbent. This matters especially
for 10- and 20-task runs where the computed fleet upper bound is intentionally
conservative at the root.

## 17. Restricted-Pool MIP Productivity Guard

The restricted-pool integer MIP is a primal heuristic. It cannot certify a node,
so repeated calls are wasteful when the current LP bound is already equal to the
incumbent. The smoke configs use:

```yaml
pool_integer_skip_if_lp_gap_below: 1.0e-6
```

If an incumbent exists and `incumbent - current_lp_bound` is below this
threshold, the pool MIP is skipped. This is exact-safe because the pool MIP is
only used to improve the primal bound; skipping it never changes the official
dual bound or pricing certificate.

The solver also runs the same restricted-pool MIP once on the initial composite
column pool before the first CG solve:

```yaml
initial_pool_integer_heuristic_enabled: true
```

If it finds a feasible incumbent, the solver immediately adds the same
incumbent-based fleet upper/prefix cuts used later in the search. This can make
the first RMP much smaller when the computed root `R_bar` is conservative. The
step is still only a primal heuristic; no lower bound or fathoming decision uses
the restricted-pool MIP result.

## 18. Exact-Safe No-Waiting Path-Profile Dominance

Moon Trek logical arcs can keep up to three fixed physical path options
(`low_time`, `low_energy`, `low_risk`). The previous exact pricing path first
built the full Cartesian product of path options for one fixed task sequence,
then filtered by aggregate metrics. That was too loose for strict no-waiting
trips: a lower travel time is not automatically dominant at an intermediate
prefix, because arriving earlier can tighten a future ready-time constraint.

The current exact start-optimized pricing therefore uses a stricter no-waiting
profile filter. A completed path-option profile can dominate another only if it
has:

```text
cost no larger
energy no larger
end offset no larger
feasible start interval covering the other profile interval
```

Under nonpositive time-occupation duals, any start feasible for the dominated
profile is also feasible for the dominating profile, and the dominating profile
occupies no more bucket time. The reduced cost can therefore only improve. At
intermediate prefixes the filter is even more conservative: it only compares
profiles with the same accumulated offset, because different offsets can change
future no-waiting release/deadline feasibility in opposite directions.

This filter is disabled automatically when time-point capacity cuts are active,
because point-cut duals can make the exact start-dependent reduced-cost shape
depend on whether a profile crosses a particular time point. In that case the
pricing code falls back to the full profile scan.

Smoke outcome after this change:

```text
5-task Apollo15: OPTIMAL in about 4.14s
5-task Tranquillitatis: OPTIMAL in about 2.83s
10-task Apollo15: still TIME_LIMIT at 40s, 2.46M timed evaluations
10-task Tranquillitatis: still TIME_LIMIT at 40s, 1.80M timed evaluations
```

The filter is exact-safe and useful cleanup, but it does not solve the main
10-task bottleneck. The logs show root CG still repeatedly performs expensive
exact pricing scans and finds negative columns with little bound progress. The
next direction is therefore bulk negative-column return during degenerate root
CG rounds, not more finite-support path-option filtering.

## 19. Start-Evaluation Hotspot Cleanup And Time-Row Experiments

Exact start optimization originally materialized a full bucket-occupation tuple
for every candidate start of every fixed sequence/path profile. Most of those
starts are never added as columns. Pricing now stores only the start value in
the cached start profile and computes the time-dual overlap directly during the
reduced-cost dot product. A full `TimedTrip` with its occupancy dictionary is
constructed only when the start has true negative reduced cost and may enter the
pool.

This is exact-safe because the direct overlap value is tested against the old
occupancy-tuple formula:

```text
base_rc - sum_b dual_b * overlap([start,end), bucket_b) / bucket_size
```

Observed smoke result:

```text
5-task full bucket rows: Apollo15 about 1.93s, Tranquillitatis about 1.17s
10-task full bucket rows at 40s: Apollo15 TIME_LIMIT, incumbent 264.024007
10-task full bucket rows at 40s: Tranquillitatis TIME_LIMIT, incumbent 221.101777
```

This is the first change in this round that clearly helps small instances
without changing the column-generation path.

Three row/column degeneracy experiments were also tested:

```yaml
exact_degenerate_bulk_pricing_enabled: false
time_occupation_row_mode: "full"        # alternatives: bucket_lazy, point_cuts
time_point_capacity_cuts_enabled: false
```

`exact_degenerate_bulk_pricing_enabled` lets exact pricing use the larger
certificate/bulk return budget as soon as the LP objective is already equal to
the incumbent. It is exact-safe because it only adds true negative reduced-cost
columns and still requires exhaustive no-negative pricing for a certificate.
It did not improve the 10-task smoke: Apollo15 still timed out and
Tranquillitatis primal worsened in the tested run. The switch remains off.

`bucket_lazy` starts with no bucket occupation rows and adds violated
`(vehicle,bucket)` rows after each RMP solve. This is exact-safe row generation:
inactive nonviolated rows have zero dual. It made 5-task faster but weakened
10-task root enough to generate many more columns, so it remains off.

`point_cuts` removes built-in bucket rows and separates continuous
`TimePointCapacityCut` rows at violated interval-overlap points. This is closer
to continuous interval packing, but current point-cut duals disable path-profile
dominance in exact pricing. The 10-task smoke then spent far more pricing
evaluations, so point cuts also remain off in the candidate smoke configs.

The current diagnosis is therefore sharper: 10-task is not mainly slow because
individual start overlap calculations are expensive. It is slow because the
Trip-Time master still has severe root degeneracy: many negative columns enter
without moving the LP objective or closing the proof.

## 20. Negative-Column Truncation Exactness Fix And Seed Repair

A certificate bug was found in the pricing return path. If exact pricing scans a
sequence, finds many negative reduced-cost starts, but returns only a truncated
subset because of a per-sequence budget, that pricing result cannot be treated
as exhausted. Otherwise the solver could falsely certify a node when the
returned negative columns are duplicates but omitted negative columns still
exist.

The fix is:

```text
if negative columns are omitted by a return budget:
    pricing_result.exhausted = false
```

This is stricter than the previous behavior and is required for exactness.

After this fix, the previous 5-task second-level results exposed a configuration
problem: the initial composite seed used
`initial_composite_seed_negative_trips_per_sequence > 0`, so it added only a
small number of multi-task columns. The later exact pricing then had to perform
one large scan to recover the missing useful columns. The seed path is only an
initial column generator, not a certificate, so the candidate smoke configs now
use:

```yaml
initial_composite_seed_negative_trips_per_sequence: 0
```

Observed smoke result with the exactness fix and repaired seed:

```text
5-task Apollo15: OPTIMAL, 102.041475, about 2.41s
5-task Tranquillitatis: OPTIMAL, 113.535083, about 1.66s
10-task Apollo15: TIME_LIMIT at 40s, incumbent 264.024007, 3015 columns
10-task Tranquillitatis: TIME_LIMIT at 40s, incumbent 221.101777, 1807 columns
```

A larger 10-task initial seed (`initial_composite_seed_max_trips: 1500`) was
also tested. It did not solve the proof tail: Apollo15 still hit the 40s limit,
and Tranquillitatis failed to improve the primal path in that run. This means
the next useful direction is not simply “more timed-trip columns.” The remaining
bottleneck is the single-sortie Trip-Time master itself: many timed trip columns
with similar task sets and starts still form a highly degenerate root LP.

The next major direction should therefore be a vehicle journey/schedule-column
prototype, where one master column represents a feasible sequence of sorties for
one rover. That removes the time-occupation-row degeneracy from the master
instead of trying to patch it with more timed-trip columns.

## 21. Pricing Loop Diagnostics: Exactness Versus Degeneracy

When root column generation appears to loop, two cases must be separated.

First, the pricing subproblem may not have produced a certificate. In the
current Trip-Time BPC this happens intentionally in many rounds: exact pricing
is still exact-safe, but it stops after finding a budgeted set of true negative
reduced-cost columns and returns `exhausted=false`. Such a round cannot prove
there is no remaining negative column and therefore cannot close the node.

Second, the RMP may be highly degenerate. A new diagnostic event,
`rmp_dual_diagnostics`, records a deterministic dual hash and adjacent-round
dual deltas. A pricing event now also records:

```text
added_trips_this_vehicle
duplicate_trips
```

A short 10-task diagnostic run showed this pattern:

```text
RMP objective unchanged for many rounds
dual hash changes every round
dual L1 delta often hundreds
pricing returns new, nonduplicate negative columns
```

This is not a pure duplicate-column bug. It is mainly degenerate column
generation: the LP objective is flat while the RMP dual solution moves across a
large optimal face and exposes different equivalent negative timed trips.

One exact-safe waste was found in certificate mode. Once any vehicle pricing
finds a negative column, the current dual vector is no longer a certificate
candidate. Continuing to price symmetric vehicles with the stale dual only adds
columns that must be re-evaluated after the next RMP solve. The solver now uses:

```yaml
certificate_stop_after_first_add: true
```

With this setting, a certificate round stops immediately after adding any
negative column and returns to the RMP. If no column is added, pricing still has
to check all relevant vehicles exhaustively before the node can be declared
complete. This preserves exactness while removing stale-dual cross-vehicle
pricing.

Observed short-run effect:

```text
Before: certificate rounds priced vehicle 1/2/3 after vehicle 1 already added
        negative columns; later vehicles often returned duplicate signatures.
After:  certificate rounds stop after the first added column; duplicate_trips
        dropped to zero in the short diagnostic.
```

This is a useful cleanup, but it does not solve the main proof tail. The logs
still show many new negative timed-trip columns with no objective movement.
That supports the previous diagnosis: the next structural change should move
toward journey/schedule columns, not more single-sortie timed-trip patches.

## 22. Finite-Pool Journey Diagnostics

A finite-pool journey diagnostic has been added. A journey is a feasible
sequence of nonoverlapping timed trips for one rover:

```text
J = (trip_1, trip_2, ..., trip_m)
end(trip_a) <= start(trip_{a+1})
task_set(trip_a) are pairwise disjoint
cost(J) = fixed_vehicle_cost + sum_a cost(trip_a)
```

The diagnostic master is a finite set-partitioning model:

```text
min sum_J cost(J) x_J
sum_{J: i in J} x_J = 1                         for every task i
sum_J x_J <= R_bar
x_J in [0,1] for LP diagnostic, x_J in {0,1} for pool MIP diagnostic
```

This is not yet an official BPC certificate. The finite pool is generated only
from timed trips that already exist in the current Trip-Time pool, so it cannot
prove that no missing journey column exists. The solver logs the result under:

```text
journey_pool_diagnostics
official_certificate: false
```

and never uses the journey LP/MIP objective to update the official lower bound,
fathom a node, or replace the incumbent. This preserves the exactness of the
current Trip-Time BPC while giving a direct measurement of how much degeneracy
is caused by representing a rover schedule as many separate timed-trip
variables.

The default smoke configs expose conservative diagnostics knobs but keep the
feature disabled:

```yaml
journey_pool_diagnostics_enabled: false
journey_pool_diagnostics_frequency: 0
journey_pool_source_trip_limit: 800        # 900 for 10-task smoke
journey_pool_max_columns: 2000             # 2500 for 10-task smoke
journey_pool_max_trips_per_journey: 6
journey_pool_max_extensions_per_prefix: 60 # 50 for 10-task smoke
journey_pool_time_limit: 1.0               # 1.5 for 10-task smoke
```

Observed diagnostics:

```text
5-task Apollo15:
  source timed trips: 710
  journey columns: 765
  journey LP/MIP: 102.041475
  selected journeys: 1
  official Trip-Time BPC: OPTIMAL 102.041475 in about 2.5s

10-task Apollo15 short run:
  initial source timed trips: 441
  initial journey columns: 543
  journey LP/MIP: 264.024007
  selected journeys: 3
  official Trip-Time BPC: still TIME_LIMIT in the short run
```

This matters because the 10-task Trip-Time RMP already has a high-quality
integer schedule at the beginning, and the finite journey master can represent
that schedule with only three columns. The official Trip-Time proof still adds
thousands of single-sortie timed-trip columns with no objective movement. That
is direct evidence that the current bottleneck is master degeneracy, not just a
slow implementation detail.

The next major step is therefore to turn the journey representation into the
official master:

```text
master variable: x[J] = choose one complete rover journey
pricing subproblem: exact elementary generation of a negative reduced-cost
                    feasible rover journey
```

Only after complete journey pricing exists may the journey master provide an
official lower bound or optimality certificate. Until then, the finite-pool
journey master remains a diagnostic and design probe.

## 23. Official Root Journey Master Prototype

The first official journey-column master has been implemented behind:

```yaml
master_mode: "journey"
```

It is still root-only, but unlike the finite-pool diagnostic it has an exact-safe
pricing loop. A master variable is now:

```text
x[J] = choose one complete rover journey J
```

where a journey is a sequence of nonoverlapping timed sortie trips for one
vehicle. The root journey RMP is:

```text
min sum_J cost(J) x[J]
sum_{J: i in J} x[J] = 1                 for every task i
sum_J x[J] <= R_bar
0 <= x[J] <= 1
```

The reduced cost of a journey is:

```text
rc(J) = cost(J) - fleet_dual - sum_{i in tasks(J)} cover_dual_i
```

and `test_journey_rmp_reduced_cost_matches_manual_formula` checks this formula
against SCIP reduced costs.

### Journey Pricing

Journey pricing is exact-safe but currently expensive:

1. Enumerate all negative-contribution timed trips under the current cover duals.
2. Solve an exact dynamic program over those trip candidates.
3. The DP state is:

```text
(served_task_mask, sortie_count)
```

and trips are processed by increasing end time. For every candidate trip, the
DP only extends states from snapshots whose end time is no later than the trip
start time. This guarantees continuous-time nonoverlap without using time
buckets. Task disjointness is enforced by the bitmask.

If timed-trip enumeration is incomplete, candidate count exceeds a configured
budget, or DP state count exceeds a configured budget, pricing returns
`exhausted=false`. Such a result may add a true negative journey if one was
found, but it cannot certify optimality.

The driver therefore has two layers:

```text
heuristic journey pricing:
    incomplete scan allowed, but only true negative journeys are added

exact journey pricing:
    required for no-negative-column certificate
```

No heuristic or incomplete result is used for lower bounds, fathoming, or
optimality.

### Current Smoke Results

Current independent configs:

```text
BPC_future/configs/moon_trek_5_journey.yaml
BPC_future/configs/moon_trek_10_journey.yaml
```

Observed results:

```text
5-task Apollo15:
  OPTIMAL 102.041475 in 3.05s

5-task Tranquillitatis:
  OPTIMAL 113.535083 in 1.93s

10-task Apollo15:
  OPTIMAL 264.024007 in 7.70s

10-task Tranquillitatis:
  TIME_LIMIT at 40.22s
  primal 263.454533
  dual 230.441119
  gap 12.531%
```

The 5-task target is now met by the official journey algorithm, and one 10-task
instance is far below the 40s target. The remaining 10-task Tranquillitatis
failure is not a finite-pool issue. Logs show:

```text
initial journey MIP incumbent: 263.454533
root journey LP: about 236.315913, then 230.441119 after partial columns
exact journey pricing: timed-trip enumeration incomplete
```

An 80s diagnostic with exact journey pricing still returned incomplete after
about 152k negative trip candidates and 12.7k generated task sequences. This
means the next bottleneck is the timed-trip enumeration inside journey pricing,
not the journey master itself.

### Next Required Direction

The next change should replace permutation-based timed-trip enumeration inside
journey pricing with a true label-setting pricing oracle. The label should
combine:

```text
task subset / elementarity
current task
no-waiting feasible start interval
route cost
energy feasibility for the current sortie
```

and emit nondominated sortie profiles directly into the journey DP. This avoids
materializing hundreds of thousands of timestamp/profile variants before the
journey selection step.

The current root-only journey master is exact when pricing exhausts and the
root LP/MIP gap closes. It is not yet a full branch-and-price implementation:
if the complete journey LP is fractional and the pool MIP objective is strictly
above the LP bound, branching will still be required before claiming integer
optimality.

## 24. Journey Pricing Loop Diagnostics And Certificate Guard

When the journey solver appears to loop or repeatedly generate similar columns,
the first question is whether the journey pricing subproblem actually solved to
optimality. The current logs now make this explicit:

```text
journey_pricing.exhausted = true
    complete no-negative/negative-column pricing result for the configured
    journey pricing universe

journey_pricing.exhausted = false
    heuristic, time-limited, sequence-limited, profile-limited, or DP-limited
    result; it may add a true negative column, but cannot certify the node
```

The journey driver now reports an official `dual_bound` only after exact journey
pricing returns `exhausted=true` with no new negative journey left to add. A
previous diagnostic bug reported the current RMP LP objective as a dual bound as
soon as the RMP was solved. That is not exact-safe: an RMP objective is only a
valid master lower bound after complete pricing proves that no negative reduced
cost journey remains. Incomplete pricing now leaves `dual_bound` and `gap` as
`null`.

The second question is whether the RMP dual solution is changing. The journey
driver now logs:

```text
journey_rmp_dual_diagnostics:
  dual_hash
  dual_l1_delta
  dual_linf_delta
  objective_delta
  active_support_hash

journey_column_addition:
  requested_journeys
  added_journeys
  duplicate_journeys
  candidate_signature_hash
```

On `tranquillitatis_balmer_like_20km_tasks10_01_seed11000` with the journey
config, the current diagnostic run showed:

```text
cg_iter 1:
  RMP objective 240.540091
  heuristic pricing exhausted=false
  added_journeys=1, duplicate_journeys=0

cg_iter 2:
  RMP objective 223.343231
  dual_l1_delta 177.075438
  dual_linf_delta 18.604032636
  heuristic pricing exhausted=false
  added_journeys=1, duplicate_journeys=0

finish:
  status TIME_LIMIT
  primal 223.343231
  dual null
  gap null
```

This run is therefore not a pure “same column repeated forever” bug. The priced
journeys were nonduplicates, and the RMP dual vector changed substantially. It
is mainly incomplete journey pricing plus dual degeneracy. A true duplicate
negative result is still guarded: if exact pricing returns a negative journey
but the pool rejects it as a duplicate, the driver stops without certifying the
RMP objective. That situation indicates reduced-cost inconsistency, signature
over-coarsening, or a stale-dual pricing path and must be diagnosed before any
optimality claim.

The remaining implementation bottleneck is that a single journey pricing call
can still exceed the outer time limit because time checks are only performed
between generated task sequences, not inside every expensive path-profile
optimization. The next speed/exactness improvement should add finer-grained
pricing interruption checks or replace the profile materialization step with a
proper label-setting journey pricing oracle.

## 25. Pricing Time Guards, Batch Journey Return, And Labeling Trial

The next implementation pass tightened the journey pricing loop without
changing the mathematical model.

### Time Budget Semantics

`time_limit=0` in the low-level pricing config means “unlimited.” This is useful
for internal exhaustive calls, but it was unsafe in the driver: after the outer
solver time was exhausted, the driver could still launch an exact pricing call
with zero remaining budget, which then ran as unlimited. The journey driver now
checks the remaining time before every pricing call and skips pricing if the
remaining budget is below `journey_min_pricing_time`.

Pricing time checks were also pushed inside:

```text
path-option/profile generation
start breakpoint evaluation
journey profile dynamic programming
```

If any of these checks hits the deadline, pricing returns `exhausted=false`.
Any negative journey produced before the deadline may be added as a valid
column, but it is not a certificate.

### Post-Pricing Reserve

Exact pricing can find a useful negative journey at the very end of the time
limit. If the solver has no time left to re-solve the RMP or finite-pool MIP,
the column cannot improve the incumbent or diagnostics before termination. The
driver now reserves a small post-pricing window:

```yaml
journey_post_pricing_time_reserve: 2.0
```

When exact pricing adds a column, the driver immediately runs a finite-pool MIP
probe if time remains. This probe only updates the incumbent. It does not prove
optimality.

### Exact-Only Pricing For 10-Task Smoke

For the current 10-task smoke instances, exact-only pricing was better than
spending the first two rounds in heuristic journey pricing. The config now uses:

```yaml
journey_heuristic_pricing_enabled: false
journey_pricing_max_returned_journeys: 64
journey_post_pricing_time_reserve: 2.0
```

The exact pricing call may still be incomplete and may still return negative
journeys. Those journeys are true priced columns, but `exhausted=false` means
the node is not certified.

### Batch Negative Journey Return

The profile DP originally returned only the single best negative journey. This
caused many RMP resolves on nearly identical dual faces. The DP now collects a
deterministic list of negative journey labels and returns up to
`journey_pricing_max_returned_journeys` columns. This is exact-safe: every
returned column is a feasible journey with negative reduced cost under the
current duals, but returning many columns is still not a no-negative
certificate.

### Label-Setting Sortie Profile Trial

A first no-waiting sortie-profile labeling generator was implemented behind:

```yaml
journey_pricing_profile_labeling_enabled: false
```

It labels states by `(served_task_mask, last_task)` and dominates partial
sortie profiles when, for the same state, one label has no later lower-start,
no earlier upper-start, no larger offset, no larger travel cost, and no larger
energy. This is an exact-safe dominance relation for the current no-waiting
sortie model.

The first implementation was not fast enough:

```text
5-task Apollo15: still optimal, about 2.29s
5-task Tranquillitatis: still optimal, about 1.21s
10-task Apollo15: optimal but slower, about 23.15s
10-task Tranquillitatis: TIME_LIMIT, primal about 227.075713
```

Therefore profile labeling remains disabled by default. It is kept as a future
direction, but the current default uses the older profile generation path.

### Current 5/10 Evidence

After the time guards and exact-only candidate settings:

```text
5-task Apollo15:
  OPTIMAL 102.041475 in about 2.09s

5-task Tranquillitatis:
  OPTIMAL 113.535083 in about 1.27s

10-task Apollo15:
  OPTIMAL 264.024007 in about 7.04-7.32s with static subset-row cuts

10-task Tranquillitatis, static subset-row cuts enabled:
  TIME_LIMIT at about 40.18s
  primal 214.934333
  dual null
  exact pricing still found negative journeys

10-task Tranquillitatis, static subset-row cuts disabled diagnostic:
  TIME_LIMIT at about 40.02s
  primal 203.590287 in one run, 202.698698 in another run
  dual null
```

The no-static-SRC diagnostic improves the incumbent for Tranquillitatis but
breaks the Apollo15 proof path under the shared 10-task smoke config. Static
subset-row cuts therefore remain enabled in `moon_trek_10_journey.yaml`; the
no-SRC setting is experimental, not the default.

### Remaining Bottleneck

The evidence is now clear: 5-task is solved within target, and one 10-task
instance is solved within target, but the harder 10-task Tranquillitatis instance
is not close to proof. Even after adding 64 negative journey columns per pricing
pass, exact pricing continues to find negative journeys and the root LP keeps
moving. A 120s no-static-SRC diagnostic still ended with:

```text
status TIME_LIMIT
primal 206.709702
dual null
root LP about 193.551555 before the final incomplete pricing call
```

This means the next required improvement is not more finite-pool MIP probing or
larger batches alone. The core remaining work is a stronger exact journey
pricing oracle or branch-and-price beyond the root journey master. The current
Python profile materialization still cannot exhaust the 10-task hard pricing
universe fast enough, and the 20-task 120s target is unlikely to be reached
without replacing that pricing engine.

## 26. Cross-Profile Dominance And Dynamic SRC Trial

A profiling pass on the hard 10-task Tranquillitatis instance showed that the
journey pricing time is split between:

```text
sortie profile generation: about 9s in a 12s pricing sample
journey profile DP: about 3.3-3.6s
```

Inside profile generation, the largest Python costs were the no-waiting
path-profile Pareto filters and repeated dominance checks. Two exact-safe
changes were tested.

### Cross-Profile Sortie Dominance

Before the journey DP, generated sortie profiles are now compressed across
different task orders and path options. For the same task set, profile `A`
dominates profile `B` if:

```text
contribution(A) <= contribution(B)
lower_start(A) <= lower_start(B)
upper_start(A) >= upper_start(B)
end_offset(A) <= end_offset(B)
```

This is safe because any journey schedule that used `B` can use `A` instead:
`A` can start no later than `B`, remains feasible over at least the same start
window, finishes no later, serves exactly the same task set, and has no larger
reduced-cost contribution. Subset-row cut coefficients also depend only on the
task set, so replacing `B` with `A` preserves cut coefficients.

Observed effect:

```text
5-task Apollo15:
  OPTIMAL 102.041475, about 1.79s

5-task Tranquillitatis:
  OPTIMAL 113.535083, about 1.13s

10-task Apollo15:
  OPTIMAL 264.024007, about 6.46s

10-task Tranquillitatis:
  TIME_LIMIT, primal 202.698698, dual null, about 40.13s
```

On the hard 10-task instance, one pricing pass pruned tens of thousands of
profiles:

```text
profile_dominance_pruned around 77k in the first pricing pass
candidate profiles after pruning around 25k
```

This improves the 5-task and Apollo 10-task proof path and keeps the best
Tranquillitatis incumbent found so far, but it still does not produce a pricing
certificate within 40 seconds.

### Partial-Profile Dominance Grouping

Partial no-waiting path-profile dominance only applies when the accumulated
offset is equal. The filter now groups partial labels by rounded offset before
comparing them. This avoids many impossible dominance checks. It is safe because
the old dominance predicate already returned false for different offsets.

The grouped filter did not materially change the hard-instance proof outcome,
but it keeps the code closer to the actual dominance relation and avoids
unnecessary comparisons.

### Dynamic Subset-Row Cuts

A root-only dynamic subset-row separator for the journey master was added behind
configuration:

```yaml
journey_dynamic_subset_row_cuts_enabled: false
```

It separates only currently violated subset-row cuts from the active journey LP
support and skips duplicate keys. This is pricing-compatible: the same
subset-row coefficient is used by the journey RMP and by journey pricing.

Diagnostic result with static SRC disabled and dynamic SRC enabled:

```text
10-task Apollo15:
  TIME_LIMIT, primal 264.024007, dual null, about 7.52s

10-task Tranquillitatis:
  TIME_LIMIT, primal 202.698698, dual null, about 40.09s
```

The dynamic separator did not preserve Apollo15's proof path. Therefore it
remains experimental and disabled by default. Static subset-row cuts remain
enabled in the 10-task journey smoke because they help prove Apollo15, even
though no-static-SRC diagnostics can improve Tranquillitatis incumbents.

### Current Interpretation

The current official journey-root algorithm now meets the 5-task target and one
10-task target instance. The hard 10-task instance still fails because complete
journey pricing cannot exhaust the negative-column universe fast enough. The
next large step should be a stronger pricing oracle, not more root finite-pool
probing:

```text
replace per-sequence profile materialization with a better label-setting oracle
or add full branch-and-price once pricing certificates are fast enough
```

## 27. Repeated-Column And Dual-Degeneracy Diagnostics

When column generation appears to loop, there are two distinct cases:

1. The journey pricing subproblem has not been solved to optimality.
2. The RMP objective is flat but SCIP is moving among alternative optimal duals,
   so the process is degenerate rather than mathematically stuck.

The journey driver now logs both cases explicitly.

### Existing-Column Filtering

Journey pricing receives the current RMP journey signatures and filters them out
when instantiating priced candidates. The profile DP asks for a larger batch of
negative candidates:

```yaml
journey_pricing_duplicate_retry_factor: 4
```

Then instantiation keeps at most `journey_pricing_max_returned_journeys` new
journeys after filtering existing signatures. This is exact-safe because it
does not remove any column from the mathematical model; it only avoids returning
columns that are already present in the restricted master.

If every negative candidate is already in the pool, the driver records
`journey_pricing_duplicate_block` with:

```text
duplicate_signature_count
duplicate_manual_rc_min / duplicate_manual_rc_max
duplicate_negative_manual_rc_count
duplicate_cost_delta_min / duplicate_cost_delta_max
dual_hash
rmp_objective
pricing_status / pricing_reason
existing_journeys_filtered
```

An existing RMP column should not have negative reduced cost under the current
optimal RMP dual. If `duplicate_negative_manual_rc_count > 0`, the issue is not
ordinary degeneracy; it indicates a reduced-cost consistency problem between
RMP coefficients and pricing coefficients.

### RMP Dual Progress Classification

Each CG iteration now logs `journey_cg_progress_diagnostics`:

```text
initial_rmp
objective_improved
dual_changed_degenerate
support_changed_objective_flat
stalled_same_dual_support
objective_worsened
```

This separates an actual stalled RMP from a degenerate RMP where the objective is
unchanged but the optimal dual solution changes.

### Current Evidence

After this diagnostic patch:

```text
5-task Apollo15:
  OPTIMAL 102.041475, about 1.79s

5-task Tranquillitatis:
  OPTIMAL 113.535083, about 1.14s

10-task Apollo15:
  OPTIMAL 264.024007, about 6.45s

10-task Tranquillitatis:
  TIME_LIMIT, primal 202.698698, dual null, about 40.13s
```

The current Tranquillitatis 10-task run did not repeat exact signatures:

```text
duplicate_journeys = 0
existing_journeys_filtered = 0
```

Its pricing calls were incomplete:

```text
cg1 exact pricing: INCOMPLETE, partial_dp_negative_journey
cg2 exact pricing: INCOMPLETE, partial_dp_negative_journey
cg3 exact pricing: INCOMPLETE, profile_dp_incomplete
```

Therefore the current failure mode is primarily not "same column loop"; it is
that exact journey pricing cannot finish the proof within the 40-second budget.
The RMP dual diagnostics also show objective-improving iterations on the hard
instance, while Apollo15 has one flat-objective step classified as
`dual_changed_degenerate` before the final exact no-negative certificate.

## 28. Pricing Proof Optimizations After Repeated-Column Audit

The next changes stayed inside the same exact journey-root algorithm. They do
not change the column definition, the master constraints, or the pricing
certificate rule.

### Cut-Dual Value Cache

Journey profile DP repeatedly evaluates the same subset-row cut dual value for
the same journey task mask. This value now has a local cache inside
`_solve_best_journey_profile_dp`.

This is a pure reduced-cost evaluation cache:

```text
cache key = journey task bit mask
value = sum subset-row dual * floor(overlap / k)
```

It changes neither the candidate set nor certificate logic.

### Subset-Row Penalty Pruning At Profile Generation

Static subset-row cuts have nonpositive duals under the minimization RMP. For a
sortie profile with task mask `M`, the cut contribution of any journey
containing that sortie is at least the profile's own subset-row penalty:

```text
penalty(M) = sum_c max(0, -pi_c) floor(|M intersect S_c| / k_c)
```

Therefore a sortie profile can be safely pruned when:

```text
profile_contribution + penalty(M) >= max(0, -base_reduced_cost)
```

If any subset-row dual has an unexpected positive sign, this pruning is disabled
for that pricing call. This keeps the pruning one-sided and exact-safe.

Diagnostic field:

```text
profile_cut_penalty_pruned
```

Observed effect on the 10-task smoke:

```text
Apollo15:
  evaluated_timed_trips 11064 -> 11028
  OPTIMAL around 6.10s

Tranquillitatis:
  evaluated_timed_trips about 316k -> about 276k-290k
  incumbent remains 202.698698
  still no dual certificate within 40s
```

### Task-Mask Compatible Profile Cache In Journey DP

For 10 tasks and below, profile DP now groups sortie profiles by task mask and
iterates only profile masks that are disjoint from the current journey mask. For
larger instances it falls back to the old overlap check to avoid building a
large `2^n` cache.

This is exact-safe because it only avoids iterating profiles that would be
rejected by the old:

```python
if mask & profile.mask:
    continue
```

check.

Observed effect:

```text
5-task Apollo15:
  OPTIMAL 102.041475, about 1.78s

5-task Tranquillitatis:
  OPTIMAL 113.535083, about 1.11s

10-task Apollo15:
  OPTIMAL 264.024007, about 6.10s

10-task Tranquillitatis:
  TIME_LIMIT, primal 202.698698, dual null, about 40.18s
```

### Incumbent-Based Fleet Cap

The journey root master now tightens its fleet limit when the current incumbent
makes extra vehicles cost-impossible. If the incumbent uses `R_inc` vehicles,
the cap can be tightened to `R_inc` only when:

```text
(R_inc + 1) * fixed_vehicle_cost + unavoidable_nonvehicle_cost_lb >= incumbent
```

This is exact-safe for the objective value: any solution with more vehicles
cannot improve the incumbent. It is also pricing-compatible because it only
changes the RHS of the existing fleet row; the pricing reduced-cost formula
already includes the fleet-row dual.

Observed diagnostics:

```text
Apollo15 10-task:
  fleet limit 8 -> 3 after initial incumbent

Tranquillitatis 10-task:
  fleet limit 6 -> 3 after initial incumbent
  fleet limit 3 -> 2 after the 214.934333 incumbent
```

This did not solve the hard proof tail, but it is retained because it is safe,
auditable, and avoids pointless high-vehicle LP alternatives.

### Early Negative Return Trial

An optional flag was added:

```yaml
journey_pricing_early_return_negative: false
```

When enabled, journey DP may return immediately after constructing a valid
negative journey and marks the pricing call incomplete. This is exact-safe for
column generation because it never certifies no-negative columns.

Diagnostic result:

```text
10-task Apollo15 with early return:
  OPTIMAL 264.024007, about 6.09s

10-task Tranquillitatis with early return:
  TIME_LIMIT, primal 263.454533
```

The hard instance lost the good 202.698698 incumbent, so early return remains
disabled. The current evidence says the hard case needs a stronger exact pricing
certificate, not earlier low-quality negative columns.

### Larger Negative-Journey Batches

The hard instance also showed a tailing pattern in a 120-second run:

```text
RMP objective reaches 202.698697
pricing remains exhausted=True but keeps finding negative journeys
each exhausted pricing call adds another batch of negative columns
dual bound remains null
```

Increasing the returned negative journey batch was tested:

```text
40s, max_returned=128:
  TIME_LIMIT, primal 202.698698

40s, max_returned=256:
  TIME_LIMIT, primal 202.698698

40s, max_returned=512:
  TIME_LIMIT, primal 202.698698

40s, max_returned=1024:
  TIME_LIMIT, primal 202.698698
```

The 1024 setting reduces some repeated iterations and does not hurt the Apollo
10-task proof, but it still cannot produce a 40-second certificate on the hard
Tranquillitatis instance.

A 120-second run with `max_returned=1024` still timed out:

```text
TIME_LIMIT, primal 202.698697, dual null, about 118.42s
```

Even after returning 1024 negative journeys in early rounds, later exhausted
pricing calls continued to find more negative journeys at the same RMP objective.
This indicates a deep column-generation degeneracy tail, not merely a small
batch-size issue.

### Batch Early-Return Trial

The early-return logic was extended to support a minimum batch size before
returning:

```yaml
journey_pricing_early_return_negative_min_count: 1
```

Diagnostic settings such as:

```text
max_returned=1024
early_return_min_count=256
profile_generation_time_fraction=0.4
```

did not solve the hard case:

```text
min256_frac04:
  TIME_LIMIT, primal 203.590287

min512_frac05:
  TIME_LIMIT, primal 202.698698
```

This again suggests that finding columns earlier is not sufficient; the solver
needs a pricing oracle/dual strategy that can finish the no-negative proof.

### Alternative Optimal Dual Selection Trial

A dual stabilization LP was added behind configuration:

```yaml
journey_dual_stabilization_enabled: false
```

It solves the dual of the current journey RMP over the current pool, constrains
the dual objective to match the RMP objective, and minimizes L1 distance to the
previous pricing dual. This is exact-safe: if pricing proves no negative journey
under this alternative optimal dual, the dual bound is official.

The LP is accepted only when its objective matches the RMP objective within
tolerance. Unit tests verify that the stabilized dual has nonnegative reduced
cost for all current-pool journey columns.

Diagnostic result:

```text
10-task Apollo15:
  OPTIMAL 264.024007, about 6.18s

10-task Tranquillitatis:
  TIME_LIMIT, primal 214.934333
```

The hard instance got a worse incumbent path, so this stabilization mode remains
disabled. The next promising direction is no longer a small controller tweak:
the exact journey pricing oracle itself needs a stronger label-setting/search
scheme that avoids materializing tens of thousands of sortie profiles and then
running a separate journey DP over them.

## 29. Pricing Oracle Structure, Dual Stability, And Weak Negative Columns

The current journey-pricing bottleneck is not caused by one repeated duplicate
column alone.  The hard 10-task Tranquillitatis run shows a deeper tail:

```text
RMP objective reaches the incumbent value
exact pricing still finds more negative journeys
adding those journeys does not move the objective
eventually the remaining time is consumed by another incomplete pricing proof
```

This is a column-generation degeneracy tail.  Three possible remedies were
reviewed and implemented only where exactness is preserved.

### Interior-Point Duals Versus Current Duals

The current RMP dual used by pricing is still captured from the SCIP LP solve.
It should be treated as a simplex/basic-style optimal dual, not an interior
point or analytic-center dual.  A previous alternative-dual LP selects another
dual from the same optimal face by minimizing L1 distance to a reference dual:

```yaml
journey_dual_stabilization_enabled: false
```

That method is exact-safe because it enforces all current-pool dual constraints
and verifies that the dual objective equals the RMP objective.  It is not a true
interior-point replacement.  A true analytic-center dual would need a nonlinear
or barrier-like model over the optimal dual face; it can only be used for the
official certificate if the returned dual is still feasible for every current
pool column and has the exact RMP objective value.

The L1 stabilized dual was tested and worsened the hard 10-task incumbent path,
so it remains disabled.

### DOI/DDOI Boundary

Dual optimal inequalities can help degeneracy only if they are mathematically
valid.  Arbitrarily clamping cover duals is unsafe because pricing would prove
optimality for a restricted dual problem rather than for the original master.

The exact-safe forms for this codebase are:

```text
1. primal-side valid inequalities whose duals naturally stabilize pricing
2. alternative-dual selection constraints that keep the same RMP dual objective
   and enforce every current-pool dual column inequality
3. diagnostic-only DOI bounds that are not used for fathoming or official lower
   bounds
```

The current implementation therefore does not add unproven DOI/DDOI bounds to
the official pricing certificate path.

### Weak Negative Column Threshold

A new optional admission threshold was added:

```yaml
journey_pricing_min_add_reduced_cost: 0.0
```

The default value keeps the old behavior.  If this is set to a positive value,
pricing may decline to add a negative journey whose true reduced cost is below
`-pricing_eps` but not below `-journey_pricing_min_add_reduced_cost`.

This is exact-safe only because filtering such a weak negative journey forces
the pricing result to remain incomplete:

```text
weak_negative_journeys_filtered > 0
pricing.exhausted = false
pricing.reason = weak_negative_journeys_filtered
```

Thus the threshold can be used to diagnose whether tailing columns are low
quality, but it cannot be used as the no-negative-column certificate.

### Streaming Profile/Journey Oracle

The old profile oracle materializes sortie profiles first and then runs journey
DP.  A new optional streaming oracle interleaves these steps:

```yaml
journey_pricing_streaming_enabled: false
journey_pricing_streaming_profile_batch_size: 5000
journey_pricing_streaming_min_negative_batch: 1
```

After each profile batch, it runs the journey DP on the profiles generated so
far.  If a negative journey is found, the journey is valid and may be added, but
the result is not a certificate because profile generation has not been
exhausted.  If profile generation completes and the final DP proves no negative
journey, the result can still be an exact certificate.

Unit tests cover both cases:

```text
streaming negative column search returns a true negative journey
streaming complete no-negative search returns exhausted=True
```

Diagnostics:

```text
5-task Apollo15 default:
  OPTIMAL 102.041475, about 1.80s

5-task Tranquillitatis default:
  OPTIMAL 113.535083, about 1.13s

5-task Apollo15 streaming:
  OPTIMAL 102.041475, about 7.33s

5-task Tranquillitatis streaming:
  OPTIMAL 113.535083, about 4.29s

10-task Tranquillitatis streaming, 40s:
  TIME_LIMIT, primal 220.734292, dual null
```

The streaming oracle is slower on 5-task and worsens the hard 10-task incumbent
path because it returns earlier but lower-quality columns.  It remains disabled.
The useful conclusion is negative: the hard case needs a stronger exact
label-setting oracle or stronger pricing-compatible stabilization/cuts, not
more aggressive early return.

## 30. Exact DP Dominance And Profile-Catalog Trials

The next pricing-proof attempt focused on exact-safe reductions inside the
journey profile DP.

### Optimistic Remaining-Contribution Bound

For a journey DP label, the code can compute the most optimistic remaining
profile contribution by selecting the cheapest negative sortie profiles that
are disjoint from the current task mask, while ignoring time compatibility and
mutual overlap among those future profiles.  This is an optimistic lower bound:
it can only be better than any real continuation.  Therefore, if even this
optimistic value cannot produce a negative reduced-cost journey, extending the
label is safe to skip.

The feature is controlled by:

```yaml
journey_pricing_dp_bound_pruning_enabled: true
```

Unit tests verify both sides:

```text
obviously nonnegative labels can be pruned and still certificate no negative
possible negative labels are not pruned
```

Diagnostics showed that this bound is too loose on the hard instance:

```text
10-task Tranquillitatis, 40s:
  dp_bound_pruned_labels = 0
  TIME_LIMIT, primal 202.698698
```

The bound is retained because it is exact-safe, but it is not the missing proof
mechanism.

### Dual-Independent Sortie Profile Catalog

A higher-level feasible sortie-profile catalog was added behind:

```yaml
journey_pricing_profile_catalog_enabled: false
journey_pricing_profile_catalog_max_tasks: 10
journey_pricing_profile_catalog_max_profiles: 200000
```

The catalog stores only physical feasibility data:

```text
task sequence
path-option tuple
feasible start interval
end offset
physical cost
task mask
```

It is independent of RMP duals.  When reused, current cover duals and cut duals
are applied again to compute the true reduced-cost contribution.  A catalog is
cached only if it is generated completely and does not exceed the configured
profile limit.  Incomplete catalogs are never used as a certificate.

Unit tests verify that a catalog generated under one dual vector can be reused
under a different dual vector and still finds a true negative journey.

Diagnostics:

```text
5-task Apollo15:
  OPTIMAL 102.041475, about 1.90s

5-task Tranquillitatis:
  OPTIMAL 113.535083, about 1.18s

10-task Apollo15:
  OPTIMAL 264.024007, about 5.27s

10-task Tranquillitatis:
  TIME_LIMIT, primal 214.934333
```

The catalog improves the easy Apollo 10-task proof, but it hurts the hard
Tranquillitatis incumbent path.  The log shows why:

```text
profile_catalog_hit = false
profile_catalog_size around 121k then 130k
```

The hard catalog generation does not complete early enough to be reused, so it
adds overhead and changes the column-generation path.  The feature remains
available for experiments but is disabled by default.

### Cross Sortie-Count Label Dominance

The DP previously compared labels only within the same sortie count.  A stronger
exact dominance rule is now enabled:

```yaml
journey_pricing_dp_cross_count_dominance_enabled: true
```

For the same served task mask, label `A` dominates label `B` if:

```text
A uses no more sorties than B
A ends no later than B
A has no larger accumulated reduced-cost value than B
```

This is exact-safe because `A` can reproduce every future extension feasible for
`B`, while retaining at least as many remaining sortie slots.

Unit tests cover a case where one sortie serving `{1,2}` dominates two separate
sorties serving `{1}` and `{2}`.

Diagnostics:

```text
5-task Apollo15:
  OPTIMAL 102.041475, about 1.77s

5-task Tranquillitatis:
  OPTIMAL 113.535083, about 1.11s

10-task Apollo15:
  OPTIMAL 264.024007, about 6.10s
  dp_cross_count_pruned_labels about 7.3k total

10-task Tranquillitatis:
  TIME_LIMIT, primal 202.698698
  dp_cross_count_pruned_labels about 300k total
```

This dominance is useful and does not hurt the current best hard-instance
incumbent path, but it still does not produce a 40-second proof.

### Shorter Pricing-Round Budget Trial

Since hard runs spend most of the time in a few exact pricing calls, shorter
per-call pricing budgets were tested without changing exactness.  Incomplete
pricing still cannot certify a node.

```text
pricing_limit=8s:
  TIME_LIMIT, primal 203.590288, pricing calls 5

pricing_limit=12s:
  TIME_LIMIT, primal 209.197029, pricing calls 4

pricing_limit=16s:
  TIME_LIMIT, primal 209.197029, pricing calls 4
```

More short incomplete rounds worsen the incumbent path.  The next productive
direction is not controller tuning; it is reducing exact profile generation or
adding stronger pricing-compatible cuts that shrink the pricing search space.

## 31. Profile Generation Timing And Path-Option Dominance

After DP-level pruning failed to prove the hard 10-task instance, pricing was
instrumented with phase timing:

```text
profile_generation_time
profile_filter_time
profile_dp_time
```

The hard Tranquillitatis 10-task root shows where the time goes:

```text
cg1:
  profile generation about 22.5s
  profile filter about 0.8s
  journey DP about 3.7s

cg2:
  profile generation about 5.7s
  profile filter about 0.8s
  journey DP about 1.1s

cg3:
  only about 1.8s remains, pricing is incomplete
```

So the dominant bottleneck is no longer the journey DP alone.  It is the
sortie profile generation loop: task sequence enumeration plus path-option
profile construction.

### Dynamic Subset-Row Trial

Dynamic root subset-row separation was tested because these cuts are
pricing-compatible.  The separator did not find violated cuts:

```text
generated 201 or 401 candidates
violated 0
added 0
```

Both tested variants remained:

```text
TIME_LIMIT, primal 202.698698
```

This means the current hard root fractional solution is not mainly missing
small subset-row cuts.

### No-Waiting Profile Labeling Trial

The disabled no-waiting sortie-profile labeling entry was retested.  It still
worsens the hard incumbent path:

```text
label_default:
  TIME_LIMIT, primal 221.101777

label_return256:
  TIME_LIMIT, primal 221.087540
```

It remains disabled.

### Return-Batch Trial

Increasing negative journey batch size after cross-count dominance was retested:

```text
max_returned=128:
  TIME_LIMIT, primal 202.698698

max_returned=256:
  TIME_LIMIT, primal 202.698698

max_returned=512:
  TIME_LIMIT, primal 202.698698
```

This confirms that the hard case is not solved by simply returning more
negative columns.

### Path-Option Dominance Correction

Path-option dominance previously required:

```text
cost, time, energy, risk all no worse
```

This double-counts risk for dominance purposes.  Risk already enters
`ArcOption.cost` through the deterministic objective scalarization.  It is not
a separate resource constraint in pricing.  Therefore exact dominance only
needs:

```text
cost, time, energy all no worse
```

Risk is still retained as a tie-breaker in sorting and remains inside the cost.
Unit tests verify that a lower-cost path can dominate another path even when
its raw risk integral is higher.

Diagnostics after this correction:

```text
5-task Apollo15:
  OPTIMAL 102.041475, about 1.70s

5-task Tranquillitatis:
  OPTIMAL 113.535083, about 1.09s

10-task Apollo15:
  OPTIMAL 264.024007, about 6.12s

10-task Tranquillitatis:
  TIME_LIMIT, primal 202.698698
```

The correction is exact-safe and does not hurt the current best hard incumbent
path, but it does not materially reduce the profile-generation bottleneck.

### Generalized Partial Dominance Trial

A stronger partial path-profile dominance rule was tested.  It compares
profiles by the absolute time interval at which the current prefix finishes,
rather than requiring identical elapsed offset.  The rule is promising
mathematically, but it changed the hard column-generation path:

```text
10-task Tranquillitatis:
  TIME_LIMIT, primal 212.044702
```

Because it hurts the best hard-instance path, it is kept only as an explicit
experimental flag:

```yaml
journey_pricing_generalized_partial_dominance_enabled: false
```

The next useful direction is a more structural sortie-pricing oracle that avoids
enumerating task permutations and path-option products so repeatedly.  The
timing evidence says profile generation, not RMP solves or journey DP alone, is
the active bottleneck.

### Profile Generation Time Fraction Trial

The first exact pricing call stops profile generation at:

```yaml
journey_pricing_profile_generation_time_fraction: 0.75
```

Increasing this fraction was tested to see whether completing more of the
profile set in the first call would leave enough time for a proof.  It did not:

```text
fraction=0.85:
  TIME_LIMIT, primal 215.513436

fraction=0.90:
  TIME_LIMIT, primal 214.934333

fraction=0.95:
  TIME_LIMIT, primal 214.934333
```

The default 0.75 split gives a better column-generation path.  More complete
profile generation in early calls reduces the number of CG rounds and hurts the
incumbent path.

### Diverse Negative-Journey Selection Trial

Negative journey selection was made configurable:

```yaml
journey_pricing_selection_mode: reduced_cost
```

The default returns the most negative reduced-cost journeys.  The experimental
`diverse` mode keeps some of the most negative journeys and then fills the batch
with distinct task masks.  All returned journeys still have true negative
reduced cost, so this is exact-safe as a column admission policy.

The hard 10-task diagnostic:

```text
selection_mode=diverse:
  TIME_LIMIT, primal 202.698698
```

It preserves the best incumbent path but does not prove the instance within
40 seconds.  Therefore the default remains `reduced_cost`.

### Pricing Oracle Duplicate Awareness And Dual-Selection Audit

The journey pricing oracle now filters existing journey signatures inside the
DP candidate selection step, not only after instantiating the selected profiles.
The old order was:

```text
profile generation -> journey DP top candidates -> instantiate -> filter pool duplicates
```

The new order is:

```text
profile generation -> journey DP top candidates -> skip forbidden signatures
                   -> instantiate nonduplicate candidates
```

This addresses the failure mode where pricing repeatedly returns the same
negative column already present in the RMP. The fix is exact-safe:

- if the oracle finds a nonduplicate negative journey, it is a valid column;
- if weak negative columns are filtered by `journey_pricing_min_add_reduced_cost`,
  the pricing result is incomplete and cannot certify the node;
- if exact DP sees negative candidates but they are all already in the pool, the
  driver still refuses to certify because that indicates numerical/degenerate
  duplicate tail rather than a clean no-negative proof;
- if duplicate scanning is capped by `journey_pricing_duplicate_scan_limit`, the
  result remains incomplete whenever that cap prevents a clean conclusion.

New pricing log fields:

```text
oracle_classification
duplicate_candidate_scan_count
duplicate_candidates_filtered
duplicate_scan_limited
duplicate_scan_limit
```

The hard 10-task Tranquillitatis audit after this change:

```text
default:
  TIME_LIMIT, primal 202.698698
  cg1 duplicate_candidates_filtered = 0
  cg2 duplicate_candidates_filtered = 0
  cg3 classification = pricing_incomplete

slack_center dual:
  TIME_LIMIT, primal 214.934333
  cg2/cg3 dual_l1_delta extremely large
```

So the current stall is not a repeated-identical-column loop. The oracle is
still incomplete because profile generation consumes the remaining proof time.

### Interior-Point Duals, DOI, And Epsilon Admission

The current default pricing dual is still SCIP's RMP LP dual. It should be
treated as a simplex/basic-style dual, not a true interior-point or analytic
center dual.

An exact-safe optional selector was added:

```yaml
journey_dual_stabilization_enabled: false
journey_dual_stabilization_mode: slack_center
journey_dual_stabilization_slack_cap: 1000.0
```

This solves an LP over the current optimal dual face and maximizes capped slack
in the current pool's dual column inequalities. It is not a barrier/interior
point method, but if accepted it is a valid RMP-optimal dual: current-pool dual
constraints hold and the dual objective equals the RMP objective. Therefore a
complete pricing proof under this dual would still be official.

The experiment above shows that `slack_center` worsens the incumbent path, so
it remains disabled. Deep dual optimal inequalities are not added to the
official model yet. Arbitrary dual clamps would change the dual problem being
priced and could create a false certificate. Any future DOI/DDOI must either be
derived from primal valid inequalities that enter the RMP and reduced-cost
formula, or remain diagnostic only.

The epsilon admission threshold remains:

```yaml
journey_pricing_min_add_reduced_cost: 0.0
```

Positive values can suppress low-quality tail columns, but only diagnostically:
if a true negative column is skipped because its reduced cost is between
`-pricing_eps` and `-journey_pricing_min_add_reduced_cost`, the pricing result
is incomplete and no lower-bound certificate is produced.

### Best-First Label-Setting Sortie Profile Search

The label-setting sortie-profile generator was changed from depth-order
expansion to an optional dual-aware best-first expansion:

```yaml
journey_pricing_profile_labeling_enabled: false
journey_pricing_profile_labeling_min_cg_iter: 1
journey_pricing_profile_labeling_best_first_enabled: true
```

The priority is the current partial sortie reduced-cost proxy:

```text
partial travel/service cost - sum cover duals of visited tasks
```

This does not change exactness. If the heap is exhausted, all feasible labels
under the same dominance rules have been considered. If a time or state limit
stops the heap, pricing remains incomplete and cannot certify the node.

A CG-iteration gate was added so the default permutation oracle can still be
used for early high-quality columns, while the best-first label oracle is used
only in tail/proof rounds:

```yaml
journey_pricing_profile_labeling_min_cg_iter: 3
```

The hard 10-task Tranquillitatis evidence:

```text
bestfirst from cg3:
  TIME_LIMIT, primal 202.698698
  pricing calls: 4
  evaluated profiles: 252198

bestfirst from cg2:
  TIME_LIMIT, primal 214.934333

bestfirst from cg1:
  TIME_LIMIT, primal 210.897612
```

Interpretation: best-first labeling is useful as a tail accelerator, but it
should not replace the early permutation oracle because it changes the incumbent
path. It still does not produce a 40-second certificate on the hard instance.

### Late Batch And Time-Cap Trials

Late returned-column batch control was added:

```yaml
journey_pricing_late_max_returned_journeys: 0
journey_pricing_late_max_returned_min_cg_iter: 3
```

This lets later tail rounds return more true negative journeys without changing
early column-generation behavior.

Hard 10-task results:

```text
bestfirst cg3 + late128:
  TIME_LIMIT, primal 202.698698

bestfirst cg3 + late256:
  TIME_LIMIT, primal 202.698698

bestfirst cg3 + late512:
  TIME_LIMIT, primal 202.698698
  cg3 added 271 true negative journeys
  no time remained for a final certificate
```

Shortening early exact-pricing time limits was also tested:

```text
20s first pricing cap:
  TIME_LIMIT, primal 208.817223

25s first pricing cap:
  TIME_LIMIT, primal 202.698698

15s first pricing cap:
  TIME_LIMIT, primal 209.197029
```

The evidence says the first long pricing call is expensive but currently
important for the good incumbent path. A simple time cap is not enough.

### Late Alternative-Dual And Dynamic SRC Trials

Alternative dual selection was tried only after the good incumbent path had
formed:

```text
l1_reference from cg3/cg4:
  TIME_LIMIT, primal 202.698698

slack_center from cg3:
  TIME_LIMIT, primal 202.698698
```

These settings preserve the incumbent but do not prove the node. Full
slack-center from cg1 remains disabled because it worsens the path.

Dynamic journey subset-row separation was also tested:

```yaml
journey_dynamic_subset_row_cuts_enabled: true
```

On the hard 10-task instance the separator generated candidates but found no
violated dynamic cuts:

```text
journey_cut_separation: violated = 0
```

Therefore the next major direction should not be more small controller tweaks.
The active bottleneck is still exact pricing proof: the model needs a stronger
complete pricing oracle, probably direct journey-label pricing or a tighter
dual-feasible certificate search that avoids materializing thousands of sortie
profiles before every proof round.

### Direct Journey-Label Pricing Trial

A first direct journey-label oracle was added behind an experimental switch:

```yaml
journey_pricing_direct_journey_label_pricing_enabled: false
journey_pricing_direct_journey_label_min_cg_iter: 1
journey_pricing_direct_journey_label_early_return_negative: true
```

Instead of materializing all sortie profiles and then solving a separate journey
DP, it expands labels of the form:

```text
(used task mask, sortie count, vehicle end time, reduced-cost value, selected trips)
```

For each label it generates feasible next sorties starting no earlier than the
label end time.  Dominance is exact-safe for equal used masks:

```text
earlier/equal end time and lower/equal value dominates
```

A complete direct-label search can certify no negative journey.  If it hits a
time, sequence, or state limit, the result is incomplete and cannot be used as a
lower-bound certificate.

Unit tests cover:

```text
direct oracle returns a true negative journey
direct oracle can certify no negative journey on a tiny instance
```

Hard 10-task Tranquillitatis evidence:

```text
direct from cg1:
  TIME_LIMIT, primal 263.454533
  reason = direct_label_sequence_budget

direct from cg3:
  TIME_LIMIT, primal 202.698698
  reason = time_limit

direct from cg3 with no inherited sequence budget:
  TIME_LIMIT, primal 202.698698
  reason = time_limit
```

The direct oracle is exact-safe but not yet useful enough: it does not find the
same negative columns as the materialized/profile oracle in the hard tail.  The
main issue is that generating a next sortie per journey label repeats too much
work and still burns the remaining certificate time.  It remains disabled.

### Final-Reserve Trial

The late-batch profile-labeling path sometimes used almost all remaining time
adding more negative columns, leaving no budget for a final no-negative proof.
Increasing the post-pricing reserve was tested:

```text
bestfirst cg3 + late512 + reserve5:
  TIME_LIMIT, primal 202.698698

bestfirst cg3 + late512 + reserve8:
  TIME_LIMIT, primal 202.698698
```

More reserve reduced evaluated profiles modestly but still did not produce a
certificate.  The tail is not just a scheduling issue around the last call; the
root pricing problem continues to find valid negative columns near the time
limit.

### Pricing Oracle Structure: Interior Dual, DOI/DDOI, And Weak-Column Threshold

The next pricing-oracle change addressed three degeneracy questions directly.

First, the solver now has an explicit optional alternative-dual selector over
the current RMP optimal dual face.  This is not a barrier solve and it does not
replace the official RMP objective.  It solves a secondary LP:

```text
keep the current RMP dual objective
keep all current column dual constraints
then choose a point on that optimal dual face
```

The existing `l1_reference` and `slack_center` modes were extended with the
alias `interior_slack`.  The `interior_slack` mode maximizes capped slack in the
current column dual constraints.  It is a practical interior-like selector: it
avoids taking an arbitrary SCIP basis dual when the RMP dual is degenerate, but
it remains exact-safe because the selected dual must still match the RMP
objective and satisfy every current column constraint.  If the secondary LP does
not return an accepted optimal dual, pricing falls back to SCIP's original dual.

Second, optional dual optimal inequality selectors were added:

```text
journey_dual_optimal_inequalities_enabled
journey_deep_dual_optimal_inequalities_enabled
```

These constraints are used only inside the secondary dual-selection LP.  The
current implementation derives deterministic upper bounds from exact current
journey columns:

```text
pi_i <= cheapest current singleton journey covering i
pi_i + pi_j <= cheapest current two-task journey covering {i,j}
```

The pair inequalities are the "deep" option.  They are selection constraints,
not master constraints.  Therefore they cannot invalidate the official model:
if they cut off the current optimal dual face, the selector is rejected and the
solver uses the original RMP dual.

Third, the weak negative-column admission threshold was audited.  The config
entry remains:

```text
journey_pricing_min_add_reduced_cost: 0.0
```

If set to a positive value, a column with reduced cost below `-pricing_eps` but
not below `-journey_pricing_min_add_reduced_cost` may be ignored as a tailing
column.  This is exact-safe only if the pricing call is not treated as a
certificate.  All journey-pricing paths now return `INCOMPLETE` with reason
`weak_negative_journeys_filtered` in that case, including the non-profile path.
Thus the threshold can reduce low-quality column admission in experiments, but
it cannot prove optimality or update a lower bound.

The cut-dual pruning guard was also tightened.  Journey-level cut coefficients
depend on the final task mask, not on a single sortie alone.  The direct and
profile oracles now disable single-sortie contribution threshold pruning only
when cut-dual signs make that pruning unsafe.  If the cut duals can only make a
sortie more expensive, the safe penalty pruning remains active.

Unit coverage added:

```text
test_journey_interior_dual_with_doi_bounds_is_rmp_dual_feasible
test_direct_journey_label_pricing_keeps_cut_dual_reward_candidate
test_nonprofile_weak_negative_threshold_is_not_certificate
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 69 tests in 0.228s, OK
```

Performance check:

```text
5-task Apollo15:
  OPTIMAL, objective 102.041475, time 1.707303s

5-task Tranquillitatis:
  OPTIMAL, objective 113.535083, time 1.075617s

10-task Tranquillitatis default check:
  TIME_LIMIT, primal 202.698698, dual None, time 40.424497s
```

Interior-dual/DOI experiments on the same hard 10-task instance were not
accepted as a candidate baseline:

```text
interior_slack + DOI/DDOI:
  TIME_LIMIT, primal 212.296655, dual None, time 40.478011s

interior_slack + DOI/DDOI + direct journey-label from cg3:
  TIME_LIMIT, primal 214.934333, dual None, time 40.021376s
```

The reason is not a correctness failure.  The alternative duals are accepted
and exact-safe, but they perturb the column path and lose the better incumbent
trajectory.  Direct journey-label pricing remains too expensive in the hard
tail: with the current Python implementation it spends the remaining certificate
budget in label generation/search and does not close the root proof.

### Direct Cache, Streaming, And Time-Limit Controller Trials

The next attempt focused on reducing repeated sortie-profile work without
changing the mathematical model.  Four exact-safe changes were added:

```text
direct_journey_label_next_sortie_cache_enabled
journey_pricing_streaming_min_cg_iter
fixed streaming early-return min-count bug
deadline checks inside direct profile-to-trip conversion
```

The direct cache stores next-sortie profiles by used task mask inside one
pricing call.  The cached object is an untimed sortie profile, not a final trip.
Each journey label still instantiates it at its own earliest feasible depot
start time.  This keeps the same column universe and only reduces repeated
partial-label generation.  A unit test verifies that cached profile conversion
returns the same trip signatures as the old uncached direct next-sortie
generator.

The streaming bug was a real robustness issue in the experimental path: early
return attempted to use `limited` before it was assigned when the number of
negative candidates was still below `early_return_min_count`.  It is now covered
by:

```text
test_journey_profile_dp_early_return_waits_for_min_count
test_direct_next_sortie_profile_cache_matches_uncached_generation
```

Regression after these changes:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 71 tests in 0.236s, OK
```

5-task smoke remains within the target:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.736103s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.096716s
```

Hard 10-task Tranquillitatis results:

```text
default check:
  TIME_LIMIT, primal 202.698698, time 40.424497s

direct from cg3, cache off:
  TIME_LIMIT, primal 214.934333, time 40.026012s

direct from cg3, cache on:
  TIME_LIMIT, primal 203.590288, time 40.106916s
```

The cache helps the direct oracle relative to cache-off, but it is still not
better than the default materialized/profile oracle.  Its third call hit the
direct sequence budget after one cache miss and no useful cache hits:

```text
direct cache-on cg3:
  reason = direct_label_sequence_budget
  direct_next_sortie_cache_hits = 0
  direct_next_sortie_cache_misses = 1
```

Thus the direct tail is not primarily repeated same-mask next-sortie generation;
the hard part is proving or searching the first large `used_mask=0` next-sortie
set itself.

Streaming early return was also tested.  It is very fast, but the columns are
too weak:

```text
stream batch3000 min16:
  TIME_LIMIT, primal 228.751214, time 15.550731s, pricing_calls 30

stream batch5000 min32:
  TIME_LIMIT, primal 221.087540, time 24.415173s, pricing_calls 30
```

Late-only streaming, after two full profile rounds, also failed to preserve the
best incumbent path:

```text
stream late cg3 batch3000 min16:
  TIME_LIMIT, primal 226.211519, time 40.120752s

stream late cg3 batch8000 min32:
  TIME_LIMIT, primal 263.454533, time 38.047891s
```

Finally, shortening full-profile pricing also lost column quality:

```text
full profile time15 return64:
  TIME_LIMIT, primal 213.814160, time 40.168564s

full profile time12 return128:
  TIME_LIMIT, primal 214.934333, time 40.354960s

full profile time20 return128:
  TIME_LIMIT, primal 203.590288, time 40.329994s
```

Conclusion: the current hard 10-task bottleneck is not solved by returning
columns earlier, caching the direct next-sortie call, or shortening pricing
budgets.  These changes either lose the incumbent path or still fail to produce
a certificate.  The next useful direction should strengthen the complete
certificate search itself: better lower bounds/dominance in the profile DP,
more informative resource-state dominance for no-waiting sortie profiles, or a
compact exact MIP/DP certificate over already generated high-quality profiles.

### Dual Safety Audit For Pricing Oracle Structure

The pricing-oracle discussion raised three exactness questions.

First, the default solver still does not replace SCIP's RMP dual with an
interior-point dual.  Pricing uses the SCIP LP dual unless the optional
alternative-dual selector is explicitly enabled:

```text
journey_dual_stabilization_enabled: false
```

When enabled, the selector solves a secondary LP on the current RMP optimal
dual face.  The accepted dual is therefore an alternative optimal current-pool
dual, not a barrier or analytic-center solution.  The implementation now
performs an explicit current-pool reduced-cost audit before accepting that
dual:

```text
current-pool dual objective must match the RMP objective
all current-pool journey reduced costs must be >= -tolerance
otherwise pricing falls back to SCIP's original dual
```

The pricing log now records:

```text
pricing_dual_source
current_pool_min_reduced_cost
current_pool_negative_reduced_cost_count
current_pool_dual_feasible
```

Second, DOI/DDOI remain optional selector constraints, not official model rows.
The current implementation only uses deterministic bounds derived from exact
current-pool singleton and two-task journey columns.  If these bounds cut off
the optimal dual face, the secondary selector is rejected and the original SCIP
dual is used.  This preserves exactness because the DOI/DDOI constraints do not
create a false lower-bound certificate.

Third, the reduced-cost admission threshold remains exact-safe only as a column
admission policy:

```text
journey_pricing_min_add_reduced_cost: 0.0
```

If a positive value filters a true negative column with reduced cost between
`-pricing_eps` and `-journey_pricing_min_add_reduced_cost`, the pricing result
is marked incomplete with:

```text
weak_negative_journeys_filtered
```

Such a result cannot certify no negative columns, cannot set a node lower bound,
and cannot prove optimality.  Therefore the threshold can diagnose or defer
tailing columns, but it cannot replace exact pricing.

Regression after the dual-audit patch:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 75 tests in 0.242s, OK
```

5-task smoke remains unchanged:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.773846s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.121317s
```

This patch does not claim to solve the hard 10-task proof tail.  It makes the
pricing-oracle structure safer and more auditable before the next larger change
to the complete pricing search.

### Generalized Sortie-Profile Label Dominance Trial

The profile-labeling oracle now has an optional stronger dominance test for
partial sortie labels.  For labels with the same served-task mask and current
last node, the generalized test compares the current-arrival interval:

```text
[lower_start + offset, upper_start + offset]
```

instead of only comparing the raw trip-start interval.  This is exact-safe for
no-waiting sortie profiles because every future extension from the same last
node depends on the current time interval, accumulated resources, and cost.  It
is controlled by the existing flag:

```text
journey_pricing_generalized_partial_dominance_enabled
```

The default remains `false`.

Unit tests added:

```text
test_sortie_partial_generalized_dominance_prunes_current_time_interval
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 76 tests in 0.247s, OK
```

Default 5-task smoke remains unchanged:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.769765s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.113628s
```

Hard 10-task Tranquillitatis with profile labeling and generalized dominance
enabled from the first CG round:

```text
TIME_LIMIT, primal 210.897612, dual None, time 37.970851s
generated_sequences = 93866
evaluated_timed_trips = 158436
```

The run pruned many profiles:

```text
cg1 profile_dominance_pruned = 31701
cg2 profile_dominance_pruned = 29344
cg3 profile_dominance_pruned = 31064
```

but still lost the better default incumbent path:

```text
default hard 10-task incumbent: 202.698698
generalized-label trial incumbent: 210.897612
```

Conclusion: generalized partial dominance is a valid oracle-structure cleanup,
but it is not a candidate baseline when enabled from the start.  If reused, it
should be tested only as a tail-only or certificate-round option.

### Tail-Only Alternative Dual Stabilization

A tail-only gate was added for the alternative-dual selector:

```text
journey_dual_stabilization_tail_only_enabled
```

When this gate is enabled, the secondary dual selector is skipped unless the CG
progress classification indicates a flat or degenerate tail:

```text
dual_changed_degenerate
support_changed_objective_flat
stalled_same_dual_support
```

This avoids perturbing the first improving CG rounds, which are currently
important for finding good incumbents.  The selector is still exact-safe:
accepted alternative duals must match the current RMP objective and pass the
current-pool reduced-cost audit.

Unit coverage:

```text
test_journey_pricing_dual_selector_tail_only_gate
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 77 tests in 0.250s, OK
```

Default 5-task smoke remains unchanged:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.765573s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.108522s
```

Hard 10-task Tranquillitatis, 40s, with tail-only `interior_slack + DOI/DDOI`
from `cg_iter >= 3`:

```text
TIME_LIMIT, primal 202.698698, dual None, time 40.518701s
```

This preserved the default incumbent path, unlike full-run interior duals, but
it still did not prove optimality.  The log shows why:

```text
cg1: objective 240.540091, exact pricing time about 27.1s
cg2: objective 214.934333, exact pricing time about 7.4s
cg3: objective 202.698698, progress_classification = objective_improved
     tail-only selector skipped
     profile_dp_time only 0.106888s before the time limit
```

Therefore the hard tail is not currently solved by dual stabilization.  At the
critical third round, the RMP is still improving, so the tail-only gate correctly
does not activate.  The actual bottleneck is that the first two exact-pricing
rounds consume almost the entire 40-second budget, leaving too little time for a
complete third-round no-negative proof.  The next direction should reserve or
compress exact proof work, not further tune dual selection.

### Certificate-Candidate Pricing Budget Controller

The next controller looked at `journey_post_pricing_time_reserve`.  Previously,
the solver always held back this reserve from exact pricing if enough time
remained.  On the hard 10-task case this meant the third pricing call, which is
the first proof-candidate round, received only a tiny DP budget.

A conservative controller was added:

```text
journey_certificate_no_reserve_enabled: true
journey_certificate_no_reserve_min_cg_iter: 3
```

When the current RMP objective is already at the incumbent value and the CG
round is at least the configured minimum, the exact pricing call receives the
full remaining time instead of reserving time for another pool MIP probe.  This
is exact-safe: it only changes time allocation.  It never treats incomplete
pricing as a certificate.

Unit coverage:

```text
test_journey_exact_pricing_budget_uses_reserve_until_certificate_candidate
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 78 tests in 0.251s, OK
```

Default 5-task smoke:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.752867s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.118509s
```

Hard 10-task Tranquillitatis with the conservative `cg_iter >= 3` controller:

```text
TIME_LIMIT, primal 202.698698, dual None, time 40.593112s
```

The controller preserved the default incumbent path.  It also did what it was
designed to do:

```text
cg2:
  remaining = 9.300910s
  exact_budget = 7.300910s
  reserve_used = 2.0s
  reason = post_pricing_reserve

cg3:
  remaining = 1.799409s
  exact_budget = 1.799409s
  reserve_used = 0.0s
  reason = certificate_candidate_no_reserve
```

However, this still did not prove optimality.  In cg3 the exact oracle spent:

```text
profile_generation_time = 1.474363s
profile_filter_time     = 0.812864s
profile_dp_time         = 0.099676s
candidate_trips         = 25301
```

The remaining hard bottleneck is therefore not just the 2-second post-pricing
reserve.  The certificate round still materializes and filters too many sortie
profiles before the journey DP gets enough time.  The next exact-safe target is
to reduce the certificate profile pool or make its DP/filtering substantially
faster, while preserving the same pricing certificate semantics.

A 60-second diagnostic with the same controller did not monotonically improve
the run:

```text
TIME_LIMIT, primal 214.934333, dual None, time 60.126695s
```

The reason was path sensitivity in the second exact-pricing round:

```text
cg2:
  exact_budget = 27.476931s
  best_reduced_cost = -21.853991
  negative_journeys = 64
  pool MIP objective stayed 214.934333
```

In the 40-second run, the second round had a much shorter budget and produced a
column set that let the pool MIP find the better 202.698698 incumbent.  This
shows that simply giving pricing more time is not enough; the early pricing
rounds need column-quality and diversity control so that they keep the incumbent
path while still leaving enough time for proof.

### Integer-Diverse Negative Journey Selection Trial

The next column-selection change added:

```text
journey_pricing_selection_mode: integer_diverse
```

This mode still keeps the most negative reduced-cost candidates, but it fills
the returned batch with structurally different candidates: different task masks,
different sortie counts, and different coarse start-time buckets.  It remains
exact-safe because every returned journey is still a true negative reduced-cost
column.  If pricing is incomplete, it remains incomplete; diversity selection
does not create a certificate.

Unit coverage:

```text
test_negative_journey_integer_diverse_selection_keeps_structural_variety
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 79 tests in 0.248s, OK
```

Default 5-task smoke remains unchanged:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.742506s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.102311s
```

Hard 10-task Tranquillitatis with exact pricing selection set to
`integer_diverse`:

```text
TIME_LIMIT, primal 202.698698, dual None, time 40.528409s
generated_sequences = 25276
evaluated_timed_trips = 350982
```

Compared with the reduced-cost-only run, this preserved the better incumbent and
slightly reduced generated/evaluated profile work, but it still did not close
the proof.  The certificate round remained dominated by profile materialization
and filtering:

```text
cg3:
  candidate_trips = 25448
  profile_generation_time = 1.272734s
  profile_filter_time = 0.821818s
  profile_dp_time = 0.102580s
  reason = profile_dp_incomplete
```

Conclusion: integer-diverse selection is a useful exact-safe column-quality
cleanup, but it is not enough for the 10-task proof target.  The next change
must reduce the profile pool or accelerate the exact DP/filtering in the
certificate round.

### Sortie Profile Filter Pre-Dedup Trial

An exact-equivalent pre-dedup step was added before sortie-profile dominance
filtering.  For identical resource intervals:

```text
mask, lower_start, upper_start, end_offset
```

only the lowest-contribution profile is kept.  This cannot remove a useful
column, because the dropped profile has identical timing resources and a no
better reduced-cost contribution.

Unit coverage:

```text
test_sortie_profile_filter_deduplicates_identical_resources
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 80 tests in 0.249s, OK
```

Default 5-task smoke remains unchanged:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.776724s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.114192s
```

Hard 10-task Tranquillitatis:

```text
TIME_LIMIT, primal 202.698698, dual None, time 40.659440s
```

This did not improve the proof tail.  The certificate round still had roughly
the same profile count and filter time:

```text
cg3:
  candidate_trips = 25306
  profile_filter_time = 0.945666s
  profile_dp_time = 0.108903s
  reason = profile_dp_incomplete
```

Conclusion: duplicate resource profiles are not the main source of the hard
tail.  The next attempt should target the certificate DP/search itself rather
than this simple pre-dedup cleanup.

### Task-Set Lower-Bound Pruning Trial

An exact-safe task-set lower bound was added behind a configuration switch:

```text
journey_pricing_task_set_bound_pruning_enabled: false
```

For a task set S, the bound solves a small Held-Karp dynamic program over the
cheapest logical arc option between tasks, then adds service cost and subtracts
the relevant cover/task-vehicle/sortie duals.  It ignores time and energy
feasibility, so it is optimistic for every feasible sortie over S.  Therefore,
if this lower bound is already above the profile threshold, every sequence and
path-option combination for S can be skipped without losing a negative
reduced-cost profile.

The switch is intentionally default-off.  The first implementation changed the
permutation order by grouping task combinations first.  That was exact, but it
degraded the limited-time column discovery path on the hard 10-task
Tranquillitatis instance.  The implementation was revised to preserve the
original permutation order and only use the bound as a skip test.

Unit coverage:

```text
test_task_set_profile_lower_bound_skips_arc_expansion
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 81 tests in 0.259s, OK
```

Default-off 5-task smoke:

```text
Apollo15 task5:
  OPTIMAL, objective 102.041475, time 1.744473s

Tranquillitatis task5:
  OPTIMAL, objective 113.535083, time 1.118483s
```

Default-off hard 10-task Tranquillitatis:

```text
TIME_LIMIT, primal 202.698698, dual None, time 40.750254s
```

The optional pruning did not materially improve the proof tail.  With the
switch on, the hard 10-task run still reached the same incumbent but did not
certificate within 40 seconds:

```text
cg1:
  candidate_trips = 25898
  profile_generation_time = 22.613235s
  profile_filter_time = 0.896912s
  profile_dp_time = 3.652365s

cg2:
  candidate_trips = 23182
  profile_generation_time = 5.465149s
  profile_filter_time = 0.794248s
  profile_dp_time = 1.026527s

cg3:
  candidate_trips = 24667
  profile_generation_time = 1.365404s
  profile_filter_time = 0.877744s
  profile_dp_time = 0.241813s
  reason = profile_dp_incomplete
```

Other exact-safe trials in this round were also not adopted:

```text
early_return_negative, min_count = 64:
  TIME_LIMIT, primal 207.547459, dual None, time 40.330133s

early_return_negative, min_count = 256:
  TIME_LIMIT, primal 206.875263, dual None, time 40.406971s

heuristic journey pricing enabled:
  TIME_LIMIT, primal 211.929136, dual None, time 40.416028s

direct journey label pricing from cg1:
  TIME_LIMIT, primal 263.454533, dual None, time 16.672541s
  reason = direct_label_sequence_budget
```

A 60-second diagnostic exposed strong column-selection path sensitivity:

```text
default selection, 60s:
  TIME_LIMIT, primal 214.934333, dual None

integer_diverse selection, 60s:
  TIME_LIMIT, primal 214.934333, dual None
```

More time allowed the second pricing round to select a different set of 64
negative journey columns, but the integer pool probe stayed at 214.934333
instead of reaching the 202.698698 incumbent seen in the 40-second path.  This
is evidence that the main issue is no longer just lack of time in the final
certificate pass.  The pricing oracle is also path-sensitive: it can return
valid negative columns that are poor for integer progress and then spend the
remaining budget proving over a different RMP face.

Current conclusion:

```text
5-task target: satisfied on the two smoke instances (< 2s).
10-task hard target: not satisfied; best observed incumbent is 202.698698,
but no dual certificate within 40s.
Main remaining bottleneck: exact journey-pricing certificate plus column
selection degeneracy.  Future work should target a stronger integrated
label-setting oracle or incumbent-aware-but-exact-safe candidate selection,
not weaker finite-support cuts or low-count early return.
```

## Certificate-Mode Dual Stabilization and Streaming Trial

This round targeted the hard 10-task Tranquillitatis case:

```text
BPC_future/data/generated/moon_trek_60/logical_graphs/
  tranquillitatis_balmer_like_20km/tasks_10/
  tranquillitatis_balmer_like_20km_tasks10_01_seed11000_logical_graph.json
```

The root evidence after the savings seed is now clear:

```text
initial incumbent = 202.698698
first RMP objective = 202.698698
active root support = 2 journeys
```

So the hard part is not finding the integer solution. The hard part is
certifying that no unseen journey column can improve the LP. SCIP's basic dual
and an interior-slack alternative dual both led pricing into many valid but
degenerate negative columns. The useful dual strategy in this round was
`l1_reference`: stay on the optimal dual face but close to SCIP/the previous
pricing dual.

Implemented exact-safe changes:

```text
journey_dual_stabilization_certificate_candidate_enabled
  Allows tail-only dual stabilization when an incumbent exists and the current
  RMP objective is already at the incumbent value. The selected dual must still
  match the RMP objective and be feasible for every current journey column.

shared initial seed trip_cache
  The journey driver now passes one deterministic arc-profile cache through the
  initial composite/savings seed and later pricing. This only avoids recomputing
  identical physical path/start profiles when keys match.

streaming_min_returned_journeys
  Streaming profile pricing no longer has to return after only one or two
  instantiated negative journeys. The default remains 1, preserving previous
  behavior. Candidate experiments used 64.
```

Best proof run from this round:

```text
Config fragments:
  initial_savings_seed_enabled = true
  initial_savings_seed_max_tasks = 5
  initial_savings_seed_max_evaluations = 2000
  initial_savings_seed_max_trips = 120
  journey_pricing_early_return_negative = true
  journey_pricing_early_return_negative_min_count = 512
  journey_pricing_max_returned_journeys = 256
  journey_pricing_profile_online_dominance_enabled = true
  journey_pricing_task_set_bound_pruning_enabled = true
  journey_certificate_no_reserve_min_cg_iter = 1
  journey_dual_stabilization_enabled = true
  journey_dual_stabilization_tail_only_enabled = true
  journey_dual_stabilization_certificate_candidate_enabled = true
  journey_dual_stabilization_mode = l1_reference
  journey_dual_optimal_inequalities_enabled = true
  journey_deep_dual_optimal_inequalities_enabled = true

Result:
  OPTIMAL
  primal = dual = 202.698697
  time = 89.590995s
  pricing_calls = 5
  final journey columns = 2282
```

The 89.6s proof is progress, but it misses the 40s target. The CG trajectory
shows why:

```text
cg1 pricing:
  negative_journeys = 256
  profile_generation_time = 22.52s
  profile_dp_time = 1.42s

cg2 pricing:
  negative_journeys = 256
  profile_generation_time = 22.53s
  profile_dp_time = 0.18s

cg3 pricing:
  exhausted = true
  negative_journeys = 90
  profile_generation_time = 9.10s
  profile_dp_time = 4.29s

cg4 pricing:
  exhausted = true
  negative_journeys = 21
  profile_generation_time = 5.21s
  profile_dp_time = 4.54s

cg5 pricing:
  exhausted = true
  negative_journeys = 0
  profile_generation_time = 5.32s
  profile_dp_time = 4.16s
```

Streaming profile pricing was tested as a way to reduce the first two expensive
partial rounds. It did return much earlier, but it returned too few and too weak
columns unless forced to wait. With `streaming_min_returned_journeys = 64` and
batch size 12000:

```text
40s result:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 2

cg1:
  negative_journeys = 128
  generated_sequences = 4398
  evaluated_timed_trips = 72083

cg2:
  no negative journey returned before time limit
  reason = profile_dp_incomplete
```

The next structural change should be an integrated exact journey
labeling/certificate oracle that avoids repeatedly rebuilding large sortie
profile sets from scratch. The current root proof bottleneck is now:

```text
dual degeneracy handled partially by l1_reference dual selection
remaining bottleneck = repeated exact profile generation and final journey-DP
certificate over the same task/path universe
```

Validation after this round:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 84 tests in 0.280s
OK
```

## Profile-Labeling Pricing Trial

The permutation-based profile generator was still too expensive for the hard
10-task proof tail. This round tested the existing no-waiting sortie
profile-labeling oracle:

```text
journey_pricing_profile_labeling_enabled = true
journey_pricing_profile_labeling_best_first_enabled = true
journey_pricing_max_sequences = 100000
```

This is the same journey master and the same pricing problem. It changes only
how sortie profiles are generated inside exact pricing. Incomplete label scans
still cannot certify a node.

Best 40-second hard 10-task result in this round used:

```text
initial_composite_seed_enabled = false
initial_savings_seed_enabled = true
initial_savings_seed_max_evaluations = 2000
initial_savings_seed_max_trips = 120
journey_pricing_profile_generation_time_fraction = 0.65
journey_retry_incomplete_no_column_enabled = true
journey_pool_integer_heuristic_enabled = false
```

Result:

```text
TIME_LIMIT
primal = 202.698698
dual = None
time = 39.982676s
pricing_calls = 5
columns = 868
```

The important change is that the root no longer spends 20+ seconds per pricing
round after the first major column batch. The trajectory was:

```text
cg1:
  added_journeys = 256
  profile_generation_time = 19.51s
  best_reduced_cost = -27.747038

cg2:
  added_journeys = 27
  profile_generation_time = 10.06s
  best_reduced_cost = -5.614590

cg3:
  added_journeys = 8
  profile_generation_time = 3.19s
  best_reduced_cost = -2.9873155

cg4:
  negative_journeys = 0
  best_reduced_cost = 0.0
  reason = partial_profile_scan_no_negative_journey
  profile_generation_time = 0.88s

cg4 retry:
  negative_journeys = 0
  best_reduced_cost = 0.861641
  reason = partial_profile_scan_no_negative_journey
  profile_generation_time = 0.27s
```

This shows the current bottleneck has shifted again. The solver can now find the
incumbent immediately and can drive reduced cost to nonnegative-looking values
inside 40 seconds, but the final label scan remains incomplete. Because the scan
is incomplete, the run cannot be marked optimal.

Implemented exact-safe support changes:

```text
profile_catalog_resume_enabled
  Adds an optional resumable physical sortie-profile catalog for permutation
  profile generation. It is default-off. It caches only dual-independent
  physical profiles and never certifies unless the catalog is exhausted.

journey_retry_incomplete_no_column_enabled
  If exact pricing returns no columns but is incomplete and time remains, the
  solver retries the same RMP/dual once with the remaining time. This uses time
  that was previously left unused; it does not turn an incomplete pricing run
  into a certificate.
```

Validation:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 85 tests in 0.265s
OK
```

Next required structural change:

```text
Implement a resumable/streaming profile-labeling certificate state.
The current retry restarts label generation, so the last no-negative incomplete
scan repeats work instead of continuing from the previous partial label frontier.
This is now the most direct route to proving the hard 10-task case under 40s.
```

## Resumable Labeling And Physical Catalog Evidence

This round implemented the requested pricing-oracle structural change without
changing the mathematical model:

```text
profile_labeling_resume_enabled
  Maintains a resumable best-first sortie-label frontier for the same
  dual/config/pricing threshold.  It is exact-safe because a stopped label is
  requeued before returning; retry can continue the frontier without dropping
  any unexpanded task/path option.  The state can certify only when the heap is
  exhausted.

profile_labeling_physical_catalog_resume_enabled
  Maintains a dual-independent physical sortie-profile catalog generated by the
  label oracle.  Later CG rounds with different dual vectors reuse the same
  physical catalog and only recompute reduced-cost contributions under the
  current dual.  If the physical catalog is not exhausted, pricing is still
  incomplete and cannot certify the RMP bound.
```

The implementation deliberately separates two caches:

```text
same-dual label frontier
  Key includes the dual vector and threshold.  This is useful for exact retry in
  the same CG round.

physical label catalog
  Key includes instance, task universe, max tasks, budgets, and dominance mode,
  but not the dual order.  This lets different duals reuse physical feasible
  sortie profiles.  Current duals are applied only during filtering.
```

Unit coverage after this round:

```text
test_resumable_sortie_label_state_requeues_partial_expansion
  Confirms a stopped label is put back on the heap and a later continuation
  reaches the same physical profile keys as a fresh complete run.

test_label_physical_catalog_reuses_across_duals
  Confirms a Moon Trek 5-task physical catalog is generated once and reused by
  a second pricing call with different cover duals; the second call has zero
  generated/evaluated physical profiles and a different reduced cost.
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 87 tests in 0.450s
OK
```

Hard 10-task evidence on
`tranquillitatis_balmer_like_20km_tasks10_01_seed11000`:

```text
same-dual label resume, 40s:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 4
  columns = 981

  cg3 no-negative call:
    profile_catalog_hit = false
    profile_catalog_size = 22029
    reason = partial_profile_scan_no_negative_journey

  cg3 retry:
    profile_catalog_hit = true
    profile_catalog_size = 25707
    reason = partial_profile_scan_no_negative_journey
```

This confirms same-dual retry now continues the label state, but the remaining
time in the 40-second run is too small to exhaust the frontier.

Physical catalog with a dual-independent key was then tested:

```text
physical catalog shared key, 40s:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 3
  columns = 833

  cg1:
    profile_catalog_hit = false
    profile_catalog_size = 58783
    profile_generation_time = 20.07s
    negative_journeys = 128

  cg2:
    profile_catalog_hit = true
    profile_catalog_size = 70340
    profile_generation_time = 10.35s
    negative_journeys = 128

  cg3:
    profile_catalog_hit = true
    profile_catalog_size = 72976
    reason = profile_dp_incomplete
```

Lowering the generation fraction to 0.30 made the first call cheaper but did
not solve the proof:

```text
physical catalog, generation fraction 0.30, 40s:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 5
  columns = 885

  final retry:
    profile_catalog_hit = true
    profile_catalog_size = 71383
    reason = profile_dp_incomplete
```

Current conclusion:

```text
The active bottleneck is no longer just duplicate regeneration under different
dual vectors.  The exact physical sortie-profile universe for the hard 10-task
case is still too large for the current Python label/profile/DP certificate
path to exhaust within 40 seconds.  The next productive direction is a stronger
complete pricing certificate that prunes at the journey level before
materializing thousands of physical sortie profiles, or an exact bidirectional /
meet-in-the-middle journey labeling oracle.  More finite-support cuts or small
time-allocation tweaks are unlikely to reach the 40s proof target.
```

## Direct Journey Continuation-Bound Trial

The next exact-safe attempt pushed a task-set lower bound into the direct
journey-label oracle.  The goal was to avoid generating next-sortie profiles
for a journey label when even the most optimistic continuation cannot produce a
negative journey.

Implemented:

```text
direct_journey_label_task_set_bound_pruning_enabled
  Default true, but only active when direct journey-label pricing is enabled.

_TaskSetContinuationLowerBoundCache
  For a used task mask and remaining sortie count, computes the most optimistic
  sum of negative task-set sortie lower bounds over disjoint remaining subsets.
  It ignores timing/order compatibility, so it is a lower bound on the best
  possible continuation.  If:

    fixed/fleet base + current label value + optimistic continuation >= -eps

  the direct journey label is safely pruned.

Important correction:
  A previous draft also tried to prune sortie-label expansion when the current
  exact task set was not attractive enough.  That is not exact-safe: a superset
  can become attractive after adding high-dual tasks.  That single-task-set
  expansion prune was removed.  Only continuation bounds that consider all
  relevant supersets are allowed.
```

Exactness conditions:

```text
The continuation bound is only used as a lower bound.
If it prunes, no feasible continuation can have negative reduced cost.
If pricing hits time/sequence/state limits, the result remains INCOMPLETE and
cannot certify the node.
```

Unit coverage added:

```text
test_direct_journey_label_task_set_bound_prunes_initial_label
  Uses a no-negative synthetic graph and verifies direct journey-label pricing
  can certify without generating next-sortie labels when the optimistic
  continuation bound is nonnegative.

test_label_generator_keeps_superset_expansion_when_singleton_not_negative
  Guards the exactness correction: a singleton can be nonnegative while a
  two-task superset is negative, so label expansion must keep exploring.
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 89 tests in 0.437s
OK
```

Hard 10-task evidence:

```text
direct journey-label from cg3, next-sortie cache enabled:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 3
  direct cg3 reason = direct_label_sequence_budget
  generated_sequences = 100001
  evaluated_timed_trips = 147866
  dp_bound_pruned_labels = 0

direct journey-label from cg3, next-sortie cache disabled:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 3
  direct cg3 reason = time_limit
  generated_sequences = 33633
  evaluated_timed_trips = 53670
  dp_bound_pruned_labels = 0
```

The no-cache direct path reduced the direct cg3 work from about 42k generated
sequences in the previous no-cache test to about 33.6k, but still could not
finish the certificate in the remaining 5 seconds.  The continuation bound did
not prune journey labels on this dual face because the optimistic task-set
continuations remain negative enough to keep labels alive.

Current conclusion:

```text
Single-direction direct journey labeling is not strong enough for the hard
10-task certificate tail.  The next structural direction should be
bidirectional or meet-in-the-middle pricing: generate exact forward and
backward label frontiers with resource/dominance bounds, combine them by task
mask and time feasibility, and use the combined lower bound to prove no
negative journey without enumerating the full sortie-profile universe.
```

## Superset Lower-Bound Label Pruning Trial

After removing the unsafe exact-task-set expansion prune, a safe replacement was
implemented:

```text
profile_labeling_task_set_superset_pruning_enabled
  For a partial sortie-label task mask M, compute the best optimistic lower
  bound among every superset T such that M subset T and |T| <= max_tasks.
  Only if every such superset is still above the reduced-cost threshold can the
  partial label be pruned.
```

This is exact-safe because the bound asks whether any future extension of the
partial task set could become useful.  It does not prune just because the
current task set is weak.

Unit coverage:

```text
test_label_superset_bound_prunes_when_no_superset_can_be_negative
  Confirms all-positive task sets can be pruned without label expansion.

test_label_generator_keeps_superset_expansion_when_singleton_not_negative
  Confirms a high-dual two-task superset is still generated even when one
  singleton is not negative.
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 90 tests in 0.437s
OK
```

Hard 10-task evidence with superset pruning enabled:

```text
TIME_LIMIT
primal = 202.698698
dual = None
pricing_calls = 5
columns = 839

cg1:
  generated_sequences = 35198
  evaluated_timed_trips = 55360

cg2:
  generated_sequences = 26428
  evaluated_timed_trips = 41419

cg4 retry:
  reason = profile_dp_incomplete
  generated_sequences = 1197
  evaluated_timed_trips = 1879
```

The safe superset bound did not materially improve the hard 10 proof.  The
current dual face leaves many optimistic supersets alive, so this bound is too
weak for the main bottleneck.  The next direction remains a stronger
bidirectional or meet-in-the-middle pricing certificate.

## Label Streaming And Task-Set Journey Dominance

The hard 10-task runs showed a different failure mode from simple slow column
search:

```text
RMP objective = incumbent = 202.698698 from cg1
pricing still finds many negative reduced-cost journeys
added journeys do not change the RMP objective
```

A direct reduced-cost audit on the first priced batch confirmed that the
columns are true negative columns under the current SCIP dual:

```text
initial journey RMP objective = 202.698698
returned journey reduced costs: min = -22.846718, max = -0.162666
after adding 78 journeys: RMP objective delta = 0.0
```

This means the issue is not a reduced-cost sign bug.  The root master is highly
degenerate: many different physical schedules have the same task coverage
effect in the journey master, so they repair the dual face without improving
the primal objective.

Implemented exact-safe changes:

```text
1. Label streaming now works with best-first profile labeling.
   Before this change, streaming_profile_batch_size only affected the older
   permutation generator; profile_labeling_enabled still waited for a large
   profile pool before running journey DP.  The label generator now calls the
   same streaming callback every profile batch.  A streaming hit returns an
   incomplete negative-column search result, never a certificate.

2. Certificate-candidate SCIP-dual gate.
   Optional config:
     journey_dual_stabilization_disable_on_certificate_candidate
   If RMP objective has caught the incumbent, pricing can force the original
   SCIP dual instead of an alternative stabilized dual.  This avoids using an
   interior/stabilized dual to keep feeding columns on a degenerate optimal
   face when the next useful action is certificate.

3. Full certificate scan gate.
   Optional config:
     journey_certificate_full_scan_after_flat_rounds
     journey_certificate_full_scan_max_sequences
     journey_certificate_full_scan_max_timed_evaluations
   After repeated certificate-candidate flat RMP rounds, pricing disables
   streaming and early return and spends the remaining budget on a full exact
   scan.  The scan still proves optimality only if the oracle exhausts.

4. JourneyPool task-set dominance.
   Current journey-master coefficients are task cover, fleet count, and
   subset-row cuts.  They depend only on task_set, not on physical schedule
   signature.  Therefore, for the current master, a journey with the same
   task_set and higher cost is dominated and can be ignored.  The pool now
   stores only the cheapest journey per task_set, while keeping dominated
   signatures mapped so duplicate filtering does not repeatedly propose them.

5. Loader arc-option dominance exactness fix.
   Path-option dominance now requires no-worse scalarized cost, travel time,
   and energy.  The old loader filter used distance/energy/risk and did not
   explicitly include travel time, which was too weak as an exactness guard.
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 96 tests in 0.451s
OK
```

Hard 10-task evidence:

```text
label streaming + SCIP dual on certificate candidate:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 24
  columns = 945
  RMP objective remained flat at 202.698698

label streaming + full certificate scan after 5 flat rounds:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 7
  columns = 893
  full scan cg5:
    generated_sequences = 43340
    evaluated_timed_trips = 66207
    exhausted = false

task-set journey dominance + same full-scan gate:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  pricing_calls = 7
  initial_journey_columns: 577 -> 235
  final columns: 258
  duplicate priced journeys in cg1: 39 / 50
  full scan cg5:
    generated_sequences = 44702
    evaluated_timed_trips = 66138
    exhausted = false
```

Conclusion:

```text
Task-set journey dominance substantially cleans the RMP and reduces duplicate
columns, but it does not solve the certificate bottleneck.  After the master
degeneracy is compressed, the active bottleneck is clearly the single-sortie
profile oracle: a 30-second full scan still cannot exhaust profile generation
on the hard 10-task dual face.

The next major direction should target the profile oracle itself, not more
master-column filtering.  The most plausible exact-safe routes are:
  - bidirectional / meet-in-the-middle sortie-profile labeling;
  - stronger time-window and energy infeasibility bounds for partial labels;
  - exact task-set feasibility/capacity caches for small masks;
  - pricing-compatible cuts that change the dual face before certificate.
```

## Resource-Precheck Cache And Online Profile Skyline

The next implemented step stayed inside the same journey-column BPC model and
kept the same exact pricing semantics.

Changes:

```text
1. Sequence resource-precheck cache.
   The resource precheck for a task sequence depends only on the loaded
   instance and the ordered task tuple.  It now caches:
     - task demand / service time / service energy;
     - minimum arc energy and time over fixed path options;
     - feasible/infeasible result by sequence.

   The cache is keyed per FutureData object and capped at 300000 entries per
   instance.  If the cap is reached, the run-local cache clears rather than
   growing without bound.  This is exact-safe because clearing only loses
   speed, not information used for bounds or pruning.

2. Online profile skyline for label-generated sortie profiles.
   When profile_online_dominance is enabled together with
   profile_cross_dominance, the label generator now applies the same
   mask-level dominance rule during generation that the batch filter used
   afterwards:

     contribution no larger,
     lower_start no later,
     upper_start no earlier,
     end_offset no larger,
     with at least one strict improvement.

   Equivalent resource profiles with the same mask/lower/upper/end_offset keep
   only the best sorted profile, matching the existing batch deduplication.
   This reduces the DP candidate pool without changing the mathematical
   pricing oracle.
```

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 98 tests in 0.393s
OK
```

5-task target check:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 10

apollo15_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 102.041475, time = 1.70s, nodes = 1

tranquillitatis_balmer_like_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 113.535083, time = 1.04s, nodes = 1
```

Hard 10-task evidence after resource-precheck cache:

```text
trq tasks10_01, 40s limit, profile labeling + full-scan gate:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  columns = 246
  sequence resource cache:
    entries = 23261
    hits = 1166216
    clears = 0
  cg5 full scan:
    generated_sequences = 561350
    evaluated_timed_trips = 699710
    raw profile_catalog_size = 699672
    candidate_trips after batch dominance = 29126
    profile_generation_time = 25.19s
    profile_filter_time = 5.33s
    profile_dp_time = 0.13s
```

Hard 10-task evidence with online skyline enabled:

```text
trq tasks10_01, 40s limit:
  TIME_LIMIT
  primal = 202.698698
  dual = None
  columns = 278
  sequence resource cache:
    entries = 21132
    hits = 1003645
    clears = 0
  cg5 full scan:
    generated_sequences = 379053
    evaluated_timed_trips = 494120
    skyline profile_catalog_size = 23121
    profile_filter_time = ~0s
    profile_generation_time = 30.00s

The online skyline removes the expensive batch filter and keeps the DP pool
smaller, but it spends the whole pricing budget in profile generation and still
does not prove the root certificate on this hard 10-task instance.
```

Interpretation:

```text
The 5-task target is now satisfied for the two generated smoke instances.
The hard 10-task blocker is not the RMP solve and not integer branching.  The
root LP remains degenerate: new true negative reduced-cost journeys are found,
but the RMP objective stays flat.  After enough flat rounds the full certificate
still requires a very large exact pricing scan.

The next direction should be structural, not another small cache:
  - move toward a bidirectional/meet-in-the-middle sortie profile oracle;
  - add stronger exact task-set/time-window feasibility caches;
  - strengthen pricing-compatible cuts that change the root dual face;
  - avoid finite-support cuts or size-specific full enumeration shortcuts.
```

## Task-Set Resource Lower-Bound Pruning

The next exact-safe pruning test added a task-set resource lower-bound cache to
the profile-labeling pricing oracle.  For a task mask, it computes optimistic
closed-tour lower bounds using:

```text
min-energy closed tour over the task set
min-time closed tour over the task set
sum of task demand, service time, and service energy
survival energy lower bound = survival_rate * min_time
recharge lower bound = energy_lower_bound / rho
```

The energy and time tours are allowed to use different path options, so the
test is optimistic.  A task set is pruned only if even this optimistic lower
bound violates capacity, battery, or horizon plus recharge.  Therefore the
pruning is safe for exact pricing; incomplete pricing remains incomplete.

Regression after wiring the cache into both non-resume and best-first label
expansion:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 101 tests in 0.392s
OK
```

5-task target check remained stable:

```text
apollo15_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 102.041475, time = 1.73s, nodes = 1

tranquillitatis_balmer_like_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 113.535083, time = 1.06s, nodes = 1
```

Hard 10-task Tranquillitatis, 40s, profile labeling + online skyline +
task-set resource pruning:

```text
TIME_LIMIT
primal = 202.698698
dual = None
columns = 290

cg5 full scan:
  generated_sequences = 379576
  evaluated_timed_trips = 494994
  candidate_trips = 23191
  task_set_resource_pruned_sequences = 152241
  profile_generation_time = 30.00s

cg5 retry:
  best_reduced_cost = -13.2987945
  negative_journeys = 35
```

Interpretation:

```text
The resource lower-bound cache is active and exact-safe, but it does not solve
the hard 10 certificate bottleneck.  Compared with the previous online-skyline
run, the full-scan generated/evaluated counts are almost unchanged.  The
dominant remaining profiles are physically feasible under optimistic resource
checks; the failure is still root LP degeneracy plus a large feasible sortie
profile certificate space, not simply infeasible task-set expansion.
```

## Partial-Label Reduced-Cost Bound Trial

An additional exact-safe partial-label continuation bound was tested.  For a
partial sortie label, the bound adds the current partial contribution to the
cheapest possible reduced-cost tail:

```text
current travel/service cost - covered-task duals
+ min over: return now, or visit any remaining task and recurse
```

The tail uses cheapest logical arc costs and ignores future time/energy
feasibility, so it is optimistic.  A partial label is pruned only if this
optimistic completion bound is already above the sortie-profile threshold.

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 102 tests in 3.424s
OK
```

5-task target check remained stable:

```text
apollo15_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 102.041475, time = 1.68s

tranquillitatis_balmer_like_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 113.535083, time = 1.04s
```

Hard 10-task Tranquillitatis, 40s:

```text
TIME_LIMIT
primal = 202.698698
dual = None
columns = 290

cg5 full scan:
  generated_sequences = 370522
  evaluated_timed_trips = 484509
  candidate_trips = 22839
  task_set_resource_pruned_sequences = 148938
  partial_profile_bound_pruned_labels = 0
  profile_generation_time = 30.00s

cg5 retry:
  best_reduced_cost = -13.2987945
  negative_journeys = 35
```

The partial continuation bound did not prune on this dual face.  The optimistic
tail remains low enough that every generated partial could still lead to a
threshold-passing profile.

The existing generalized partial dominance switch was also tested only in the
trial config.  It did not help this instance:

```text
cg5 full scan with generalized partial dominance:
  generated_sequences = 407820
  evaluated_timed_trips = 518993
  candidate_trips = 23597
  partial_profile_bound_pruned_labels = 0
  status = TIME_LIMIT
```

This reinforces that small dominance/cache changes are not enough for the hard
10 certificate.  The next useful direction should change the pricing proof
structure or the root dual face, rather than adding another local feasibility
precheck.

## Cross-Dual Catalog And Restart Trial

The next experiment targeted the observed root behavior:

```text
RMP objective is flat at the incumbent value
SCIP/stabilized duals still change
pricing keeps finding true negative journeys
dual_bound remains None because pricing never exhausts
```

Two exact-safe mechanisms were added behind experimental switches.

First, label physical catalog resume now has a hard
`profile_catalog_max_profiles` guard and can reuse a physical sortie-profile
label state across different RMP duals.  The state stores feasible partial
labels and profiles, not a dual certificate.  On a cache hit the heap is
reprioritized with the current dual, so the next pricing round continues from
the same physical search space but explores labels in current reduced-cost
order.  Resource lower-bound pruning is also applied while building the
physical catalog.  This is exact-safe because no current-dual pruning is used to
delete a physical profile from the catalog; incomplete catalog generation still
returns `exhausted=false`.

Second, an optional root journey-pool restart was added:

```text
journey_pool_restart_enabled
journey_pool_restart_after_flat_rounds
journey_pool_restart_min_columns
journey_pool_restart_keep_task_sets
journey_pool_restart_keep_recent
journey_pool_restart_max_times
```

The restart keeps current active RMP journeys, incumbent journeys, recent priced
journeys, singleton feasibility journeys, and a small number of task-set-best
representatives.  It is only column-pool management.  Deleted journeys may be
regenerated by exact pricing, and a lower bound is reported only after exact
pricing exhausts against the current dual.  Therefore restart does not change
the mathematical model or proof semantics.

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 104 tests in 0.435s
OK
```

5-task target check after these changes:

```text
apollo15_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 102.041475, time = 1.67s

tranquillitatis_balmer_like_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 113.535083, time = 1.03s
```

Hard 10-task Tranquillitatis catalog trial, 40s, without restart:

```text
TIME_LIMIT, primal = 202.698698, dual = None

cg1:
  negative_journeys = 32
  profile_catalog_hit = false
  profile_catalog_size = 20377
  label_physical_catalog_exhausted = false
  label_resume_heap = 508
  profile_generation_time = 19.69s

cg2:
  negative_journeys = 41
  profile_catalog_hit = true
  profile_catalog_size = 26471
  label_resume_heap = 106
  profile_generation_time = 10.29s

cg3:
  negative_journeys = 15
  profile_catalog_hit = true
  profile_generation_time = 3.19s
  best_reduced_cost = -4.65659191
```

A 60s diagnostic still did not close the root:

```text
TIME_LIMIT, primal = 202.698698, dual = None
cg4 profile_catalog_hit = true
label_resume_heap = 52
reason = profile_dp_incomplete
```

Restart trial, 40s:

```text
journey_pool_restart:
  old_journeys = 297
  new_journeys = 123
  source_counts = active 2, recent 41, singleton 10, task_set_best 70

finish:
  TIME_LIMIT, primal = 202.698698, dual = None
  final columns = 133
```

The restart reduced the RMP pool but did not change the flat root objective or
the need for more exact pricing.  It is useful as a diagnostic switch, but it is
not a candidate baseline yet.  The remaining bottleneck is still the complete
pricing certificate: even after catalog reuse, exact pricing continues to find
meaningful negative journeys rather than only epsilon-tail columns.

## Streaming Physical Catalog Trial

The next change combined two exact-safe mechanisms that were previously
separate:

- cross-dual physical label catalog reuse for single-sortie profiles;
- streaming negative-column return during profile generation.

The key control-flow fix is that a streaming batch whose journey DP is
incomplete and returns no addable column no longer aborts pricing.  It simply
continues generating profiles until it either finds a true negative journey or
reaches the exact pricing budget.  Partial streaming results are used only to
add columns.  A no-negative certificate is still reported only when the physical
catalog is exhausted and the journey DP is solved under the current true duals.

The physical catalog branch is now compatible with streaming.  The cached heap
is reprioritized under the current dual, profile counts are logged before early
return, and the same catalog can be resumed across CG rounds.  This preserves
the original exactness rule: incomplete catalog states never prove a bound.

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 106 tests in 0.423s
OK
```

5-task target check:

```text
apollo15_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 102.041475, time = 1.68s

tranquillitatis_balmer_like_20km_tasks05_01_seed6000:
  OPTIMAL, objective = 113.535083, time = 1.05s
```

Hard 10-task Tranquillitatis streaming/catalog trial:

```text
config: BPC_future/configs/tranq10_streaming_trial.yaml
time limit: 60s
status: OPTIMAL
objective = dual = 202.698698
time = 57.75s
nodes = 1
columns = 289
pricing calls = 7
```

Important pricing trajectory:

```text
cg1: 4000 catalog profiles, 3 negative journeys, best rc -20.719865667
cg2: 8000 catalog profiles, 3 negative journeys, best rc -13.811602667
cg3: 12002 catalog profiles, 2 negative journeys, best rc -6.2889825
cg4: 16002 catalog profiles, 1 negative journey, best rc -1.087487333
cg5: catalog exhausted at 29065 profiles, 40 negative journeys
cg6: cached exhausted catalog, 14 negative journeys
cg7: cached exhausted catalog, no negative journey certificate
```

A smaller streaming batch returned too few columns per CG round and missed the
60s target.  Disabling subset-row cuts reduced per-row overhead but increased
the number of tailing CG rounds, so the current hard-10 candidate keeps the
120-cut root setup and uses a 4000-profile streaming batch.

This meets the updated 10-task target on the current hard Tranquillitatis trial.
It does not yet prove the 20-task 200s target.  The next work should run the
same streaming physical-catalog configuration on the 20-task Apollo15 and
Tranquillitatis sets, then decide whether the remaining bottleneck is catalog
generation size or cached journey-DP proof time.

## Apollo20 Root Diagnostics

The first Apollo20 trial exposed a data-quality issue before solver tuning:

```text
apollo15_20km_tasks20_01_seed21000: task 17 has no feasible depot-task-depot sortie
apollo15_20km_tasks20_03_seed21036: task 16 has no feasible depot-task-depot sortie
all other generated 20-task files passed the single-task sortie feasibility check
```

The active 20-task diagnostic therefore uses:

```text
BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_20/
apollo15_20km_tasks20_02_seed21018_logical_graph.json
```

Cross-dual physical catalog reuse is not yet suitable for this 20-task case.
With an 8000-profile streaming batch and a 200k profile cap, root pricing was
still building the global physical catalog at 200s:

```text
status = TIME_LIMIT
primal = 631.092855
dual = None
cached profiles at timeout = about 117k
catalog exhausted = false
```

Switching to per-dual thresholded streaming avoids the large cross-dual catalog
and improves the incumbent, but still does not prove the root within 200s:

```text
status = TIME_LIMIT
primal = 556.426385
dual = None
nodes = 1
columns = 415
pricing calls = 15
```

The RMP trajectory reached the incumbent value by the end:

```text
cg11 RMP objective = 557.147838
cg12 candidate incumbent = 557.147838
cg15 RMP objective = 556.426385
finish primal = 556.426385
```

However, pricing remained incomplete.  Many late pricing rounds still returned
only one to five negative journeys, often with small reduced costs around
`-0.4` to `-0.7`, so the current 20-task bottleneck is root certificate tailing
after useful upper-bound improvement.  Forcing streaming to wait for at least
eight addable journeys was worse: the first pricing round spent about 66s,
generated about 53k profiles, and returned no columns before incomplete status.

Current conclusion:

- 5-task target is met.
- The hard 10-task target is met by streaming physical catalog pricing.
- 20-task target is not met.
- The next 20-task change should not be larger streaming batches or a higher
  minimum returned-column count.  It should be a stronger exact certificate
  oracle for the tail, most likely a meet-in-the-middle or subset-DP sortie
  profile generator that exploits `max_tasks_per_sortie = 6` without building a
  full cross-dual profile catalog.

## Restart Strategy Audit

The restart strategy was extended as an opt-in diagnostic rather than a proof
mechanism.  The historical trigger remains `certificate_flat`; new experimental
triggers can rebuild the finite RMP journey pool after degenerate flat rounds
or at a fixed CG interval:

```text
journey_pool_restart_trigger: certificate_flat | degenerate_flat | objective_flat | fixed_interval
journey_pool_restart_after_degenerate_rounds
journey_pool_restart_interval
```

The restart is exact-safe only because it changes the current restricted master
pool, not the original column space.  It keeps active RMP journeys, incumbent
journeys, recent priced journeys, singleton feasibility journeys, and
task-set-best representatives.  Any deleted journey can be regenerated by
pricing, and no lower bound is certified until exact pricing is exhausted.

Regression after adding the trigger logic:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 108 tests in 0.437s
OK
```

The already-good scales were preserved:

```text
5-task Apollo15:          OPTIMAL, 102.041475, 1.700019s
5-task Tranquillitatis:   OPTIMAL, 113.535083, 1.057045s
hard 10-task Tranq:       OPTIMAL, 202.698698, 58.536078s
```

The 20-task restart trial enabled:

```text
journey_pool_restart_trigger = degenerate_flat,fixed_interval
journey_pool_restart_interval = 6
journey_pool_restart_min_columns = 260
journey_pool_restart_keep_task_sets = 160
journey_pool_restart_keep_recent = 128
```

It triggered once at `cg6`:

```text
old_journeys = 428
new_journeys = 173
trigger_reason = fixed_interval
source_counts = active 6, recent 8, singleton 19, task_set_best 140
official_bound_unchanged = true
```

The result was not a candidate improvement:

```text
Apollo20_02, 200s:
  status = TIME_LIMIT
  primal = 550.076891
  dual = None
  columns = 226
```

The previous no-restart streaming trial reached a better incumbent
`548.308756` in the same 200s budget, also without a dual bound.  After restart,
pricing still found strong true negative journeys in late rounds and the RMP
objective moved again from `550.076891` to `546.567777` near `cg14`.  Therefore
the current 20-task failure is not mainly "low-value repeated columns stuck in
the RMP basis."  It is still incomplete root pricing: the oracle continues to
discover meaningful negative journeys before it can certify no more exist.

Conclusion: keep restart as an opt-in diagnostic/cleanup tool, but do not use it
as the 20-task candidate baseline.  The next algorithmic move should be a
structural pricing change, not more restart tuning.

## Streaming Per-Mask Profile Cap Audit

A second exact-safe diagnostic was added to test whether streaming pricing was
being flooded by too many resource variants for the same task mask:

```text
journey_pricing_streaming_profile_cap_per_mask
```

The cap is applied only while a streaming callback is active.  If it prunes any
profile, the sortie-profile label state is forced to remain incomplete:

```text
state.exhausted = false
state.reason = profile_mask_cap_incomplete
```

Thus the cap can only help find columns earlier.  It can never prove a
no-negative pricing certificate.  Unit coverage was added for both the capped
online skyline behavior and the "cap prevents exhausted certificate" rule.

Regression:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 110 tests in 0.436s
OK
```

The default-off 5-task smoke still solved both generated 5-task instances:

```text
Apollo15 5-task:        OPTIMAL, 102.041475, 1.714792s
Tranquillitatis 5-task: OPTIMAL, 113.535083, 1.056761s
```

Apollo20 with `journey_pricing_streaming_profile_cap_per_mask = 4` was stopped
early because the first pricing round was clearly worse:

```text
cg1:
  profile_mask_cap_pruned = 564753
  task_set_resource_pruned_sequences = 1927859
  label_resume_profiles = 7896
  negative_journeys = 0
  reason = profile_dp_incomplete
  time = 65.155250s
```

The no-cap configuration had returned eight valid negative journeys in about
14 seconds in the same first round.  Therefore this cap is not a useful current
candidate.  It remains available only as an opt-in diagnostic; the active
20-task configuration keeps it off.

## Physical Catalog Streaming and Dynamic SRC Audit

The next 20-task trials used the same journey-column master and exact pricing
semantics, but enabled the physical sortie-profile catalog resume path together
with streaming negative-column return.  This made the 20-task Apollo15 pricing
path much more useful than the earlier per-dual streaming run: the root loop
kept finding true negative journeys quickly and the restricted-pool MIP found
better incumbents.

Baseline physical streaming, root only:

```text
Apollo20_02, 200s:
  status = TIME_LIMIT
  primal = 562.343144
  dual = None
  columns = 463
  exact_pricing_calls = 14
```

A root dynamic subset-row separator was then enabled.  It added only two
pricing-compatible cuts:

```text
subset_row(k=2, S={2,12,13}), violation = 0.285714286
subset_row(k=2, S={3,13,17}), violation = 0.285714286
```

The root bound impact was small, from `618.551226` to `618.639926`, but the
integer pool path improved materially:

```text
Apollo20_02, dynamic SRC, 200s:
  status = TIME_LIMIT
  primal = 554.148185
  dual = None
  columns = 459
  cuts_added = 2
```

A CSV bug was fixed at the same time: journey-driver results had hard-coded
`cuts_added = 0`, so dynamic journey cuts were invisible in the CSV even when
they were logged.  The result object and finish log now report the dynamic
subset-row count.

## Certificate Fast-Return Audit

When the RMP objective reached the incumbent, exact pricing was still waiting
for the normal batch of eight negative journeys before returning.  A
certificate-candidate mode was added:

```text
journey_certificate_fast_negative_return_enabled
journey_certificate_fast_negative_return_min_count
```

This mode is exact-safe because it only returns true negative columns sooner.
It never treats incomplete pricing as a certificate.  A second bug was fixed:
if the current RMP solution is integral and improves the incumbent, the
`certificate_candidate` flag is recomputed before exact pricing is configured.

The experiment was not a candidate improvement.  It triggered earlier, but it
returned only one degenerate negative journey and reduced the diversity passed
to the pool MIP:

```text
Apollo20_02, dynamic SRC + fast return, 200s:
  status = TIME_LIMIT
  primal = 554.309839
  dual = None
  columns = 456
```

Therefore the code remains available and tested, but the current candidate
configuration keeps fast return disabled.

## Larger Streaming Negative Batch

The more successful change was to return more true negative journeys per
pricing call:

```text
journey_pricing_streaming_min_negative_batch = 24
journey_pricing_early_return_negative_min_count = 24
```

This keeps the same pricing oracle and the same exactness rule.  It only changes
how many validated negative journey columns are handed to the RMP before the
next resolve.

On the same Apollo20_02 run:

```text
Apollo20_02, dynamic SRC + batch24, 200s:
  status = TIME_LIMIT
  primal = 547.962506
  dual = None
  columns = 580
  cuts_added = 2
```

The incumbent path improved much faster:

```text
7.45s:   incumbent = 556.426098
16.74s:  incumbent = 550.076891
35.10s:  incumbent = 549.026328
53.49s:  incumbent = 548.308756
129.76s: incumbent = 547.962506
```

However, the RMP objective also dropped to about `514`, showing that the root
journey relaxation is still weak once enough negative columns are present.
This is important: the earlier "RMP bound close to incumbent" behavior was a
restricted-column artifact, not a real certificate-ready root bound.

## Current 20-Task Blocker

The current `journey_driver` is still a root-only column generation driver:

```text
node_count = 1
dual_bound = None
```

For 5-task and the tested 10-task cases the root journey pool can become
integral after exact pricing, so this is sufficient.  For the 20-task Apollo15
case, once batch24 exposes more of the true column space, the root LP remains
far below the incumbent.  Therefore pricing improvements alone cannot prove
20-task optimality within 200 seconds.

The next necessary structural step is a real journey-level branch-and-price
loop, initially with pricing-compatible Ryan-Foster task-pair branching.  The
branch constraints already exist in the lower-level trip RMP/pricing code; the
journey driver needs to lift them to journey columns and process more than the
root node.  Until that is implemented, 20-task exact proof is structurally
blocked even when the incumbent is good.

## Journey Ryan-Foster Branching Support, Step 1

The first branch-and-price preparation step was implemented in the exact
pricing layer.

For the journey master, a selected journey is one rover schedule.  Therefore a
Ryan-Foster pair has a direct task-set interpretation:

```text
same_vehicle(i,j):
  every journey column must contain either both i,j or neither

separate_vehicle(i,j):
  no journey column may contain both i,j
```

This does not introduce finite-support cuts and does not change reduced-cost
duals.  It restricts the column universe at a branch node.  The exact pricing
oracle now accepts these two branch kinds instead of returning
`UNSUPPORTED`.  The profile DP prunes `separate_vehicle` masks as soon as both
tasks appear and filters final `same_vehicle` candidates that contain exactly
one of the pair.  Candidate instantiation applies the same task-set guard as a
final safety check.

The journey driver also gained helper functions to:

```text
_journey_allowed_by_branch
_filter_journeys_by_branch
_choose_journey_branch
```

`_choose_journey_branch` uses fractional same-pair mass:

```text
same_mass(i,j) = sum_{journey contains both i,j} x_journey
```

and selects a pair with fractional same mass.  Unit tests cover branch-aware
pricing and the journey branch helper behavior.  This is not yet a full
multi-node driver; it is the necessary exact-pricing foundation for the next
implementation step.

## Journey Ryan-Foster Branch-Price Driver, Step 2

The journey driver now has an opt-in multi-node branch-and-price path:

```text
journey_branching_enabled: True
```

The old root-only journey driver remains the default unless this switch is set.
The new path uses the same journey-column master and the same journey pricing
oracle as the 5-, 10-, and 20-task runs.  It is not a small-instance full
enumeration shortcut.

Node processing is exact-safe:

```text
1. Filter the current global journey pool by the node's Ryan-Foster constraints.
2. Solve the node RMP over that filtered finite pool.
3. Optionally add root dynamic subset-row cuts.
4. Run heuristic pricing only to find valid negative columns.
5. Run exact journey pricing with the node branch constraints.
6. Treat the node LP objective as an official lower bound only if exact pricing
   is exhausted.
7. If the exact-priced node LP is fractional, branch on fractional same-pair
   journey mass.
```

If a branch node's finite pool is temporarily infeasible, the node is marked
incomplete rather than fathomed.  This is deliberate: missing branch-feasible
columns in the current pool are not an infeasibility proof.  A future refinement
can add phase-I artificial journey columns or branch-feasible seed pricing for
these nodes, but the current implementation avoids incorrect pruning.

New trial configs:

```text
BPC_future/configs/moon_trek_5_journey_branch_trial.yaml
BPC_future/configs/moon_trek_10_journey_branch_trial.yaml
BPC_future/configs/apollo20_physical_branch_trial.yaml
```

Current evidence after the first implementation:

```text
Apollo15 5-task branch trial:
  status = OPTIMAL
  time   = 5.873966s
  primal = dual = 102.041475
  nodes  = 1

Apollo15 10-task branch trial:
  status = OPTIMAL
  time   = 1.857912s
  primal = dual = 264.024007
  nodes  = 1

Apollo15 20-task branch trial, 200s:
  status = TIME_LIMIT
  primal = 487.624693
  dual   = None
  nodes  = 1
  RMP objective at cg_iter 19 = 469.090510
```

The 20-task result is materially better on primal quality than the previous
batch24 root-only run (`547.962506`), but it still does not prove optimality.
The log shows no branch was created because root exact pricing never exhausted:
each long pricing call still found negative journeys until the final short
budget ended with `profile_dp_incomplete`.  Therefore the next blocker is root
CG/pricing convergence, not branch-node explosion.

The next algorithmic direction is to make the root exact pricing phase expose
more useful negative journeys per expensive scan and/or strengthen the
pricing-compatible relaxation before the certificate phase.  Exactness remains
unchanged: incomplete pricing still gives no node bound, and branch nodes are
fathomed only after exact pricing certificate, bound dominance, or integrality.

## Streaming Batch Return and Early Branch Audit

The next pricing change focused on root CG tailing.  The previous streaming
callback could stop after a very small number of instantiated journeys even
when the config requested a larger negative batch.  The reason was:

```text
streaming_min_negative_batch controls DP early-candidate search
streaming_min_returned_journeys controls instantiated journey return count
```

When `streaming_min_returned_journeys` was `1`, a callback with only 3 to 5
usable journeys could stop the scan.  The implementation now caches the best
partial negative result and waits for `streaming_min_returned_journeys` before
returning.  If time runs out, the cached negative columns are returned as an
incomplete pricing result.  This remains exact-safe because it never reports
`exhausted=True`.

For the 20-task branch trial, the config uses:

```text
journey_pricing_streaming_min_negative_batch: 24
journey_pricing_streaming_min_returned_journeys: 24
```

This made early/root pricing add 24 journeys per scan more consistently.

During this audit a branch-driver cache issue was found.  The root-only driver
reused `trip_cache` across CG rounds, but the first branch-node implementation
passed a fresh `{}` into every pricing call.  That disabled physical profile
catalog/resume inside branch nodes.  The code now supports persistent
node-local pricing cache again, guarded by:

```text
journey_pricing_trip_cache_enabled
```

However, on `apollo15_20km_tasks20_02_seed21018`, persistent cache reuse
returned to the older batch24 search path:

```text
200s result with persistent node-local profile cache:
  primal = 547.962506
  dual   = None
  nodes  = 1
```

The no-cache branch trial found a much better incumbent:

```text
200s result with no per-node pricing cache:
  primal = 487.624693
  dual   = None
  nodes  = 1 before early branch
```

This indicates that profile generation order is still highly path-dependent.
Cache reuse is exact-safe, but it can narrow the practical search path and miss
useful incumbent-producing columns in this Python prototype.  The current
20-task branch trial therefore keeps:

```text
journey_pricing_trip_cache_enabled: False
```

The driver also gained exact-safe early branching.  If configured, it may split
a node before exact pricing exhaustion, but it does not use the current RMP
objective as a bound.  Children created this way carry:

```text
lower_bound_exact = False
```

and cannot be pruned by that inherited value.  The branch is still valid because
Ryan-Foster same/separate children partition the parent column universe.

Current best 20-task early-branch evidence:

```text
apollo15_20km_tasks20_02_seed21018, 200s
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 3
```

The run branched at root on `RF(1,3)` after CG round 12, then branched the
`same_vehicle` child on `RF(1,2)`.  It still timed out because child exact
pricing kept finding negative columns and no child reached an exact pricing
certificate.  A depth-aware smaller branch-node pricing batch processed more
nodes (`nodes=5`) but worsened the incumbent (`487.624693`), so it is left as
an opt-in helper rather than part of the current 20-task trial config.

Conclusion: the solver now has a real exact-safe branching path and avoids
reporting diagnostic lower bounds, but the 20-task target is still blocked by
pricing convergence inside branch nodes.  The next useful direction is not more
finite-support cuts; it is stronger pricing-compatible bounds/dominance inside
journey pricing, or a more complete journey/profile enumeration strategy that
can actually exhaust branch-node pricing within the time target.

## Branch-Node Cache And Restart Follow-Up

After the upper-start profile filter and adaptive partial negative return, a
branch-only trip/profile cache was tested as an exact-safe acceleration.  The
cache is controlled by:

```text
journey_pricing_trip_cache_enabled
journey_branch_pricing_trip_cache_enabled
```

The implementation is branch-local and never certifies a node.  It only reuses
physical trip/profile catalog work between CG rounds; every returned journey is
still checked by the current true reduced cost, and incomplete pricing remains
incomplete.

Unit coverage was added for the branch-only override:

```text
global cache off + root depth 0  -> fresh cache per pricing call
global cache off + branch depth 1 + branch override on -> same cache reused
```

Regression tests:

```text
python -m unittest BPC_future/tests/test_bpc_future.py
Ran 125 tests: OK
```

The 5- and 10-task smoke results remained inside the target:

```text
5 tasks:  OPTIMAL, 1.272972s, primal = dual = 102.041475, nodes = 1
10 tasks: OPTIMAL, 1.846950s, primal = dual = 264.024007, nodes = 1
```

The 20-task branch-cache trial was not useful:

```text
config = apollo20_physical_branch_upperfilter_adaptive_branchcache_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 5
columns = 841
pricing calls = 25
generated sequences = 4,416,335
evaluated timed trips = 5,577,467
```

The previous adaptive-return trial without branch cache was better:

```text
status = TIME_LIMIT
primal = 486.039528
dual   = None
nodes  = 4
columns = 765
pricing calls = 21
generated sequences = 1,930,685
evaluated timed trips = 2,695,823
```

Conclusion: branch-cache reuse is exact-safe, but on the current Python journey
pricing implementation it changes the streaming/resume path enough to generate
many more candidates and miss the better incumbent.  It should stay as an
opt-in diagnostic, not a candidate baseline.

The user also suggested periodic RMP restart or limiting the maximum basis/column
set to break low-value column cycles.  This is compatible with the existing
restart audit, but the safe interpretation is column-pool restart, not basis
restriction.  The LP solver basis is not a modeling object we can restrict
without solver-specific side effects.  A column-pool restart remains exact-safe
only if:

```text
1. active LP journeys, incumbent journeys, and feasibility seed journeys are kept;
2. removed journeys are allowed to be regenerated by exact pricing;
3. no lower bound is claimed until exact pricing exhausts after the restart;
4. restart is disabled at root unless a new diagnostic proves it helps.
```

Existing evidence says root restart is harmful, while depth-guarded restart did
not trigger before the time limit on the protected path.  Therefore restart is
not the current main lever for the 20-task proof target.  The next priority is
to reduce branch-node pricing proof work itself: tighter dominance and bounds
inside the journey/profile DP, then selective return policies that add fewer
but higher-impact negative journeys without changing the certificate rule.

## Dynamic Fleet Slack And Branch Selection Trials

The dynamic fleet limit previously attempted to tighten the active master row
directly to the number of vehicles used by the incumbent.  This is often too
aggressive to prove safely.  For the Apollo 20-task instance, after a 5-vehicle
incumbent was found:

```text
fixed vehicle cost = 50.0
unavoidable nonvehicle lower bound = 145.861022
5-vehicle incumbent = 492.815216
```

Tightening to 5 vehicles would require proving every 6-vehicle solution cannot
improve the incumbent:

```text
6 * 50.0 + 145.861022 = 445.861022 < 492.815216
```

so it is not safe.  Tightening to 6 vehicles only excludes 7-or-more-vehicle
solutions:

```text
7 * 50.0 + 145.861022 = 495.861022 >= 492.815216
```

which is safe for objective proof.  The solver therefore gained an opt-in
dynamic slack:

```text
journey_fleet_limit_slack: 1
```

The default remains zero, preserving the previous behavior.  The tightened
limit is still an exact master row: it only removes solutions that cannot beat
the current incumbent under fixed vehicle cost plus a valid unavoidable-cost
lower bound.

Unit coverage:

```text
python -m unittest BPC_future/tests/test_bpc_future.py
Ran 126 tests: OK
```

The 5- and 10-task smoke instances remain solved well under target:

```text
5 tasks:  OPTIMAL, 1.264456s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.857344s, primal = dual = 264.024007
```

20-task fleet-slack trial:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 3
columns = 724
pricing calls = 19
generated sequences = 1,815,234
evaluated timed trips = 2,504,694
```

The useful effect is real: after CG round 8, the active fleet limit tightened
from 17 to 6, and the root pool probe found `486.081224` at about 41s.  In the
previous adaptive-return trial, the same incumbent appeared only after entering
a branch node at about 92s.  The trial also used fewer pricing calls and fewer
columns than the previous adaptive-return run.

However, it did not beat the previous best incumbent `486.039528`, and still
produced no official dual bound.  The reason is branch-path sensitivity:
fleet-slack changed the root branch from the previous `RF(1,3)` to
`RF(9,12)`.  The tighter root master is helpful, but it changes the fractional
pattern used by early branching.

Two follow-up variants were tested:

```text
branch integer-diverse selection:
  config = apollo20_physical_branch_upperfilter_branchdiverse_trial.yaml
  result = TIME_LIMIT, primal = 486.081224, nodes = 4, columns = 756

fleet slack + root early branch at CG14:
  config = apollo20_physical_branch_upperfilter_fleetslack_root14_trial.yaml
  result = TIME_LIMIT, primal = 486.081224, nodes = 3, columns = 698
```

Neither variant improved the incumbent or produced a certificate.  The CG14
delay reduced the number of columns/pricing calls but spent more time in root
tailing and did not recover the old `486.039528` branch path.

The branch code then gained exact-neutral diagnostics and an opt-in stable
tie-break:

```text
journey_branch_candidate_log_top_n
journey_branch_fractionality_tie_tolerance
journey_branch_candidate_priority: fractionality | low_task_index
```

The default remains the old max-fractionality rule.  With
`journey_branch_fractionality_tie_tolerance: 0.05` and
`journey_branch_candidate_priority: low_task_index`, the root branch changed
from `RF(9,12)` to `RF(1,9)`, proving that the tie-break is active.  The trial
still timed out:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_stablebranch_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 4
columns = 753
pricing calls = 20
generated sequences = 1,828,999
evaluated timed trips = 2,539,669
```

The logged root branch candidates showed:

```text
max fractionality = 0.5 for RF(9,12)
near-tie candidates at 0.470588 included RF(1,9), RF(1,17), RF(2,15), RF(3,13)
```

Choosing low-index near-ties is therefore not enough.  The next useful
branching rule should be based on schedule/pricing structure, such as repeated
incumbent conflict cores, pair incompatibility pressure, or tasks appearing in
expensive branch-node pricing witnesses, rather than task id.

An incumbent-disagreement Ryan-Foster rule was then tested.  It uses the current
incumbent only to choose among near-equally fractional pairs and to order the
same/separate children.  This is exact-safe because both children are still
created and no incumbent-derived bound is used:

```text
journey_branch_candidate_priority: incumbent_disagreement
journey_child_priority_mode: incumbent_relation
journey_branch_fractionality_tie_tolerance: 0.05
```

The trial changed the root branch from the fleet-slack `RF(9,12)` to
`RF(9,13)`, and logged incumbent relation/disagreement for the top candidates.
It still timed out:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_incbranch_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 3
columns = 739
pricing calls = 19
generated sequences = 2,144,506
evaluated timed trips = 2,771,859
```

The 5- and 10-task smoke instances remained solved:

```text
5 tasks:  OPTIMAL, 1.341758s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.870946s, primal = dual = 264.024007
```

Conclusion: incumbent disagreement is not enough either.  The branch decision
needs pricing-aware or schedule-conflict-aware evidence, not merely the current
incumbent relation.  In particular, the useful signal should come from pairs
that repeatedly cause expensive incomplete branch pricing or appear in route/
journey conflict witnesses.

A pool-split Ryan-Foster rule was also tested.  It computes, for each
near-fractional pair, how many current journey-pool columns would remain in the
`same_vehicle` and `separate_vehicle` children:

```text
journey_branch_candidate_priority: pool_split
journey_branch_fractionality_tie_tolerance: 0.05
```

This is again exact-safe because it only orders the branch search and both
children are still created.  The root diagnostics showed that `RF(9,12)`, the
plain fleet-slack branch, was also the narrowest near-fractional split:

```text
RF(9,12): same_allowed = 362, separate_allowed = 555, max_child_width = 555
RF(1,9):  same_allowed = 431, separate_allowed = 587, max_child_width = 587
RF(1,17): same_allowed = 394, separate_allowed = 585, max_child_width = 585
RF(9,13): same_allowed = 429, separate_allowed = 583, max_child_width = 583
```

The trial therefore kept the same root branch and matched the fleet-slack
outcome:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_poolsplit_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 3
columns = 724
pricing calls = 19
generated sequences = 1,818,290
evaluated timed trips = 2,509,130
```

The 5- and 10-task smoke instances remained solved:

```text
5 tasks:  OPTIMAL, 1.277625s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.889128s, primal = dual = 264.024007
```

Conclusion: current-pool split width confirms that the fleet-slack branch is
not obviously bad by finite-pool width.  The missing signal is not simple
fractionality, incumbent relation, or finite-pool split.  It likely has to come
from pricing-proof cost itself: pairs/constraints that make child pricing
incomplete or expensive should feed back into the branch score.

Conclusion: dynamic fleet slack is a valid opt-in strengthening and should stay
available.  It improves root incumbent timing and reduces column count, but it
does not solve the 20-task proof problem alone.  The next branch-related change
should be a better Ryan-Foster candidate scoring rule that remains stable under
tighter fleet limits, instead of more root delay or column-pool restart.

## Branch Profile Pruning And Restart Recheck

The journey pricing oracle now pushes `separate_vehicle(i,j)` branch constraints
into sortie-profile generation.  A single sortie profile containing both tasks
can never appear in any valid journey in that child, so pruning that profile mask
is exact-safe.  The same is not done for `same_vehicle(i,j)`, because the two
tasks may need to be served in different sorties of the same vehicle.

Regression after the change:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 130 tests in 0.466s
OK
```

Small smoke instances were preserved:

```text
5 tasks:  OPTIMAL, 1.263916s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.844594s, primal = dual = 264.024007
```

The 20-task Apollo fleet-slack branch-prune trial did prune branch-incompatible
sortie profile masks, but did not improve the overall search:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_branchprune_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 3
columns = 721
pricing calls = 19
generated sequences = 1,846,023
evaluated timed trips = 2,530,564
branch_mask_pruned_sequences = 124,609
```

The user suggested periodic RMP restart / limiting the active column set to
break low-value column cycles.  The exact-safe interpretation is column-pool
restart, not solver-basis restriction.  A follow-up config enabled branch-depth
restart on top of fleet-slack branch-prune:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_branchprune_restart_trial.yaml
journey_pool_restart_enabled = true
journey_pool_restart_min_depth = 1
journey_pool_restart_trigger = degenerate_flat,fixed_interval
journey_pool_restart_interval = 4
```

The result was effectively identical, and no restart event triggered before the
time limit:

```text
status = TIME_LIMIT
primal = 486.081224
dual   = None
nodes  = 3
columns = 721
pricing calls = 19
generated sequences = 1,845,191
evaluated timed trips = 2,529,336
journey_pool_restart events = 0
branch_mask_pruned_sequences = 124,371
```

Conclusion: branch-profile pruning is correct and cheap enough to keep, but it
does not address the main 20-task bottleneck.  Restart remains an opt-in
diagnostic/cleanup tool; on this protected path it either does not trigger, or
historically harms when allowed at root.  The current failure mode is still the
pricing proof tail: exact pricing keeps generating or testing many meaningful
candidate journeys instead of cycling only over a bloated RMP pool.

A same-vehicle DP completion pruning test was then added.  In a
`same_vehicle(i,j)` child, a partial journey containing exactly one side can be
discarded if no remaining time-compatible, task-disjoint sortie profile can add
the missing side.  This is exact-safe, but it is now controlled by:

```text
journey_pricing_dp_same_completion_pruning_enabled
```

and defaults to false.  The diagnostic run with the pruning implicitly active
showed why it should not be a baseline feature yet:

```text
5 tasks:  OPTIMAL, 1.327595s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.890160s, primal = dual = 264.024007

20-task Apollo branch-prune after same-completion pruning:
  status = TIME_LIMIT
  primal = 486.081224
  dual = None
  generated sequences = 1,969,081
  evaluated timed trips = 2,685,174
  branch_mask_pruned_sequences = 124,443
  dp_same_completion_pruned_labels = 89,273
```

Although it pruned many same-child DP labels, total generation and evaluation
increased versus the previous `1,846,023 / 2,530,564`.  The likely reason is
that streaming pricing then has to continue profile generation longer to reach
its returned-negative batch target.  The pruning remains covered by unit tests
and can be enabled for diagnostics, but it should stay off for the protected 20
candidate path.

After making that pruning opt-in, the protected small-scale smoke checks again
matched the target:

```text
5 tasks:  OPTIMAL, 1.247048s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.843402s, primal = dual = 264.024007
```

This reinforces the current diagnosis: local RMP cleanup and branch-level mask
pruning are not enough.  The useful next move has to reduce exact pricing's
physical/profile generation burden or produce a stronger pricing-compatible
bound, rather than merely returning partial negative columns earlier.

## Partial-Bound And Resource-Cache Pricing Audit

The physical profile catalog path keeps all resource-feasible sortie profiles
and filters them under the current dual.  That allows reuse across dual changes,
but it also means finite-threshold partial-profile reduced-cost pruning is not
active on that path.  A dual-specific trial disabled physical-catalog resume and
enabled:

```text
journey_pricing_profile_labeling_physical_catalog_resume_enabled = false
journey_pricing_partial_profile_bound_pruning_enabled = true
```

This remained exact-safe, but was not useful.  It reached the same incumbent
much later:

```text
config = apollo20_physical_branch_upperfilter_fleetslack_partialbound_trial.yaml
status = TIME_LIMIT
primal = 486.081224
dual = None
nodes = 3
columns = 648
generated sequences = 536,956
evaluated timed trips = 797,640
partial_profile_bound_pruned_labels = 0
task_set_resource_pruned_sequences = 2,589,769

incumbent timing:
  556.426098 at 20.76s
  492.815216 at 109.29s
  486.081224 at 175.37s
```

The generated/evaluated counts fell, but wall-clock time worsened badly.  The
actual active pruning was the resource lower-bound test, not the partial
reduced-cost bound.  Disabling physical-catalog reuse therefore trades profile
reuse for expensive repeated Python resource checks and should not be a
candidate baseline.

The resource lower-bound cache was then separated from profile/label caching.
This cache stores only physical, dual-independent facts such as optimistic
closed-tour energy/time feasibility for task masks.  It is exact-safe because it
does not cache columns, reduced costs, heap order, or certificates.  Branch
profile/label cache can remain disabled while resource feasibility is reused
within a node.

Regression after the cache change:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 132 tests in 0.460s
OK

5 tasks:  OPTIMAL, 1.280585s, primal = dual = 102.041475
10 tasks: OPTIMAL, 1.872176s, primal = dual = 264.024007
```

20-task result with the protected branch-prune config:

```text
status = TIME_LIMIT
primal = 486.081224
dual = None
nodes = 3
columns = 721
generated sequences = 1,846,843
evaluated timed trips = 2,531,771
task_set_resource_pruned_sequences = 6,907,716
branch_mask_pruned_sequences = 124,724

incumbent timing:
  492.815216 at 26.84s
  486.081224 at 40.05s
```

This is a small safe cleanup: root incumbent timing improved by roughly two
seconds versus the earlier protected branch-prune run, but it did not change
the proof status.  The remaining gap is not repeated resource-bound recursion;
it is the larger exact pricing proof tail over physical sortie profiles and
journey combinations.

## Restart, Fleet-Bound, And 10-Task Pricing-Proof Audit

A branch-depth journey-pool restart was tested earlier, but it did not trigger
on the protected 20-task path.  Root restart had already been harmful in earlier
trials.  Restart is therefore kept as a diagnostic/opt-in pool-management tool,
not as the main proof strategy.  It can clean a finite RMP pool, but it cannot
replace the exact pricing certificate.

The fleet-limit proof was strengthened with an exact-safe nonvehicle lower
bound.  The new bound is an assignment relaxation of depot-to-depot sortie
paths: for a fixed number of nonempty sorties, each task has one predecessor
and one successor, and the depot is replicated into the required number of
starts and returns.  The relaxation allows disconnected task cycles, so it can
only underestimate the true nonvehicle cost.  For an unconditional bound the
minimum is taken over all feasible sortie counts; for an incumbent fleet-limit
cut, a conditional lower bound is used for the excluded number of nonempty
vehicles.  This keeps the incumbent-based fleet upper cut exact-safe.

On the main 20-task apollo15 instance:

```text
old unavoidable nonvehicle LB ~= 145.861022
new unconditional assignment LB = 176.521621
conditional LB with at least 6 nonempty vehicles = 183.588041
conditional LB with at least 7 nonempty vehicles = 188.961718
```

This is stronger but still not enough to exclude six vehicles for the current
incumbent around 486.081224, because excluding six vehicles would require a
nonvehicle lower bound of about 186.081224.  It explains why the fleet-limit
change is useful but not sufficient.

The 10-task Moon Trek smoke also exposed the current proof bottleneck.  After
the latest exact-safe changes:

```text
5-task apollo15:        OPTIMAL, 102.041475, 1.703650s
5-task tranquilllitatis: OPTIMAL, 113.535083, 1.086790s
10-task apollo15:       OPTIMAL, 264.024007, 6.985607s on the old 10 config
10-task apollo15:       OPTIMAL, 264.024007, 1.800571s on pricing-pruning trial
10-task tranquilllitatis: TIME_LIMIT at 60s, primal 202.698698, no dual bound
```

The slow 10-task tranquilllitatis instance is not waiting for a good incumbent:
the initial journey-pool MIP already finds the final incumbent and tightens the
active fleet limit to two vehicles.  The RMP objective is also equal to the
incumbent from the start.  Nevertheless exact pricing keeps finding negative
journeys while the RMP objective remains flat.  This is the current dominant
pattern:

```text
RMP objective = incumbent = 202.698698
support unchanged or nearly unchanged
dual changes substantially
pricing finds negative journeys
adding many negative journeys gives almost no objective improvement
certificate remains incomplete
```

L1-reference dual stabilization, interior-slack dual selection, and SCIP's
native dual all showed the same qualitative behavior.  Full-scan mode after
flat rounds reduced the number of CG iterations, but full pricing still found
large batches of negative journeys or ran out of time before certifying.  This
means the immediate blocker is not only bad column-pool hygiene or a bad dual
choice; it is the exact pricing proof tail under heavy degeneracy.

Regression after this audit:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future/tests/test_bpc_future.py

Ran 140 tests in 4.360s
OK
```

The test suite now includes journey-master reduced-cost consistency with
pricing-compatible cuts, including the `>=` fleet lower-bound row, so future
cut/pricing changes have a direct guard against false negative columns caused
by row-dual sign mistakes. It also checks that same-task-set journey dominance
can be disabled before any future row whose coefficient depends on sortie count
or timing is added.
