# Exact Pricing Completion Bounds Design Notes

This document records the agreed design contract for accelerating the
true-dual exact pricing certificate tail in `BPC_future`.  It complements
`learning_dual_stabilization_design.md`: learning-based Wentges smoothing is a
heuristic column generator, while the mechanisms below target the official
true-dual certificate path.

## Performance Goal

The current engineering target is:

```text
5-task instances:  under 5 seconds
10-task instances: under 60 seconds
20-task instances: under 200 seconds
```

The learning component should make the solver find the same or better incumbent
earlier, concentrate true-RC negative columns, and reduce RMP iterations.  The
completion-bound component should reduce the expensive true-dual exact pricing
proof tail.

## Exactness Contract

- This feature is an exact-pricing accelerator, not a heuristic certificate.
- It is enabled only in true-dual certificate pricing.
- It must never prune a label unless the bound is a valid optimistic lower bound
  on every feasible continuation.
- If a pricing run hits any limit, the result remains incomplete.
- Official lower bounds and optimality certificates still require true-dual
  exact pricing exhaustion.
- Keep the feature opt-in and easy to disable while benchmarking.

## Primary Target

First implementation target:

```text
direct journey-label pricing at the root certificate tail
```

Do not start with sortie profile generation.  The root true-dual certificate is
the dominant bottleneck; sortie-profile generation can reuse the same idea later
if the direct-label version is validated.

Branch depth policy:

```text
depth = 0: eligible
depth > 0: disabled by default
```

Deep branch nodes have smaller search spaces and branch constraints that are
harder to represent safely in a relaxed lower bound.  Root-first keeps the first
implementation focused on the dominant proof tail.

## Activation Policy

Completion bounds are tail-only.  They should activate only after heuristic or
smoothed-dual pricing fails and the solver is entering true-dual certificate
pricing.

Do not enable this heavy bound in early or middle CG rounds.  In those rounds,
GNN-smoothed pricing and lightweight heuristics are expected to find negative
columns cheaply.

## Bound Rebuild Policy

The lower bound must be rebuilt for each true-dual pricing call.  The reduced
cost network changes whenever task-cover duals change:

```text
arc/task reduced costs depend on the current true RMP pi
```

The rebuild is acceptable because the bound is a relaxed polynomial-time
precomputation, while exact pricing expansion is exponential in the hard tail.

## Bound State

First-version state:

```text
LB(last_node, remaining_slots, time_bucket)
```

Do not include full NG memory in the reverse-bound state.  The reverse bound is
intentionally memoryless and relaxed; that is safe as long as it remains
optimistic.  Full NG memory would destroy the speed advantage.

Configuration knobs:

```text
completion_bound_time_buckets: configurable, suggested 5-15
completion_bound_energy_buckets: configurable, suggested 5-15
```

The first implementation can start with time buckets only.  If energy buckets
are added, path-option handling must preserve a safe resource envelope; see the
path-option rule below.

## Reduced-Cost Components

The completion bound includes only task-cover duals:

```text
travel/service lower cost - task-cover pi
```

Do not include subset-row cuts, fleet cuts, branch-row duals, or other dynamic
rows in the first bound.  Omitting these terms makes the bound looser, but still
safe if it remains optimistic.  Including them would add state dimensions and
sign cases that slow down the bound and increase exactness risk.

The forward exact label still uses the full true RMP reduced cost when evaluating
actual candidate journeys.

## Cycle Control

Because the reverse bound is memoryless, it can otherwise create artificial
negative cycles by repeatedly collecting task dual rewards.  First-version cycle
control:

```text
2-cycle elimination: remember predecessor node and forbid immediate return
coarse time/energy buckets: consume resource to truncate longer cycles
```

The bound must remain optimistic.  It is better to be too small and prune less
than to be too large and prune a valid negative column.

## NG-Route And DSSR

The forward exact pricing route should use:

```text
NG-route relaxation + DSSR
```

Do not use full elementary bitmask DP for 20-task pricing.  A full `2^20`
subset state becomes too large once time and energy dimensions are added.

DSSR policy:

- If the best bound-guided negative column violates elementary constraints,
  extract the cycle/conflict tasks.
- Add those tasks to a node-level critical forbidden memory set.
- Do not globally expand all NG neighborhoods.

This keeps state growth local to the actual conflicts seen by pricing.

## Retry NG-DSSR Opt-In Probe (2026-06-04)

A small exact-safe retry hook was added for diagnostics:

```text
journey_retry_incomplete_no_column_force_ng_enabled
journey_retry_incomplete_no_column_force_ng_root_only
journey_retry_incomplete_no_column_force_ng_max_labels
journey_retry_incomplete_no_column_force_ng_min_negative_journeys
journey_retry_incomplete_no_column_force_ng_probe_time_limit
journey_retry_incomplete_no_column_force_ng_probe_min_journeys_for_early_return
```

Default status:

```text
disabled
root-only when enabled
```

Purpose:

- When a short true-dual exact pricing pass is incomplete and returns no column,
  the existing retry pass can optionally force NG-DSSR even if the normal
  `journey_pricing_direct_journey_label_ng_min_cg_iter` gate would disable it.
- This retry still uses true RMP duals.
- It does not create a proof by itself unless an explicit exact-safe NG
  certificate flag is also enabled.  Otherwise, it is only a front-end for
  finding elementary negative journeys before the existing fallback logic.

Validation:

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_retry_force_ng_config_is_opt_in_and_root_only_by_default \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_config_maps_ng_probe_controls \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_learning_defaults_are_conservative_but_overridable \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_can_close_profile_pricing \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_can_close_ryan_foster_branch_pricing \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_rejects_non_ryan_foster_branch_pricing
```

Result: 6 tests passed.

Probe:

```text
BPC_future/results/retry_force_ng_tranq10_06_20260604.csv
  instance = tranquillitatis_balmer_like_20km_tasks10_06_seed11090
  status = OPTIMAL
  objective = 196.791797
  time = 48.306388s
  retry_force_ng = true on cg_iter 3 and 4
  NG retry found negative journeys, but wall-clock was roughly neutral
```

Interpretation:

- The hook is useful for controlled experiments and logging.
- On Tranq 10-06 it did not beat the default result (`47.588866s` in the
  current all-10 rerun), so it should remain opt-in.
- It does not address the Apollo 10-04 branch-tail failure by default because
  the first version is root-only.

## Path-Option Rule

For a pure reduced-cost bound without resource dimensions, each ordered node pair
can use the path option with the lowest current reduced cost.

If the bound uses time or energy buckets, do not blindly keep only the lowest-RC
option when that option consumes extreme resources.  Dropping a slower or
lower-energy option can make the relaxed continuation artificially worse and
therefore unsafe.  In resource-aware mode, retain a coarse resource envelope:

```text
for each pair and coarse resource transition, keep the minimum reduced cost
```

The Moon Trek graph is physically asymmetric.  Uphill and downhill costs differ,
so reverse-bound construction must use the correct directed option data.  A
reverse relaxation from `j` to predecessor `i` must account for the original
directed arc `i -> j`, not assume symmetry.

## Branch Constraints

First version:

```text
root only
branch depth > 0: disabled
```

If simple separate-vehicle constraints are later supported, represent them by
setting incompatible edge or mask transitions to infinity in the relaxed graph.
If a branch condition cannot be represented one-sided and safely, disable the
bound for that node.

## Pruning Rule

Prune immediately when a new forward direct-journey label is generated:

```text
current_rc + LB(last_node, remaining_slots, time_bucket) >= -1e-5
```

Do not wait until the label is pushed to the heap.  Fail-fast pruning avoids
heap growth and priority-queue churn.

During exact certificate pricing, do not use heuristic thresholds such as
`min_add_reduced_cost` to prune weak negative columns.  The certificate threshold
must be the true pricing epsilon.

## Debug Safety

Early development must use a dual-run audit mode:

```text
bare exact DP without completion-bound pruning
bound-pruned exact DP
```

Required assertions:

```text
small instances:
  best_true_rc(bound_on) == best_true_rc(bound_off)

all debug modes:
  if bound_on declares no negative, bound_off must also declare no negative
```

If these disagree, the bound is unsafe and experiments must stop until the bug
is fixed.

Debug tiers:

```text
Debug mandatory:
  all 5-task instances, strict equality on best RC and certificate status

Diagnostic sampled:
  selected 10-task instances, limit-aware mismatch audit

Hard-case limited:
  selected 20-task hard cases, limited diagnostic only, not default benchmark
```

## Logging And Paper Metrics

Metrics should be grouped into three layers.

Bound construction:

```text
bound_build_time
lb_state_count
lb_min_value
lb_mean_value
lb_negative_state_count
ng_memory_size_avg
```

Pricing search:

```text
expanded_labels_before_bound
expanded_labels_after_bound
lb_pruned_labels
energy_return_pruned_labels
time_return_pruned_labels
dominance_pruned_labels
generated_next_sorties_before_bound
generated_next_sorties_after_bound
evaluated_timed_trips
```

Certificate:

```text
best_true_rc
true_negative_journeys
certificate_status
exact_pricing_time
tail_certificate_time
bound_enabled
branch_depth
dual_source = true_dual
```

Paper-facing ratios:

```text
label_reduction_ratio = lb_pruned_labels / expanded_labels_before_bound
certificate_speedup   = T_no_bound / T_with_bound
```

The wall-clock speedup should be reported together with label-pruning evidence
so the improvement is attributable to the exact pricing proof mechanism, not
only solver-path noise.

## Relationship To Learning Stabilization

Learning stabilization and completion bounds have separate roles:

```text
GNN/Wentges smoothing:
  get useful columns and incumbents earlier, reduce RMP trajectory noise

Completion bounds:
  accelerate true-dual exact pricing after heuristic/smoothed pricing fails
```

The handoff is:

```text
smoothed/heuristic pricing fails
alpha forced to 0
true-dual exact pricing starts
tail-only completion bound becomes eligible
```

No GNN output participates in this certificate bound.

## External References To Inspect

These references were identified as useful implementation comparisons.  They
should be inspected before copying design details, because their modeling
assumptions differ from Moon Trek.

- `mouadmorabit/MLColumnSelection`: TensorFlow code for the machine-learning
  part of Morabit, Desaulniers, and Lodi's 2021 Transportation Science paper on
  ML-based column selection for column generation.
- `INFORMSJoC/2023.0404`: JOC archive for the Electric Vehicle Routing and
  Overnight Charging Scheduling Problem on a Multigraph, with BPC code and data.
- `inria-UFF/VRPSolverEasy`: Python interface to VRPSolver / BaPCod-style
  Branch-Cut-and-Price exact VRP solving.
- `Zhengzhong-You/RouteOpt`: modern C++ exact VRP optimization framework related
  to learning-to-branch Branch-Price-and-Cut work.

Use these as architecture references, not as authority to relax the exactness
contract in this project.

## First Implementation Checklist

- Add config flags for root/tail-only completion-bound activation.
- Implement a true-dual direct-label completion bound with state
  `LB(last_node, remaining_slots, time_bucket)`.
- Rebuild the bound every true-dual pricing call.
- Include only task-cover duals in the bound.
- Preserve directed Moon Trek arc asymmetry.
- Add immediate label-generation pruning.
- Keep branch-depth > 0 disabled by default.
- Add debug dual-run assertions on all 5-task instances.
- Log bound construction, pricing search, and certificate metrics.
- Compare against the same config with the bound disabled.

## Current Implementation Snapshot

Implemented in `BPC_future/pricing/journey_pricing.py` and
`BPC_future/solver/journey_driver.py`:

- opt-in direct journey-label completion-bound flags;
- root-only certificate activation through
  `journey_certificate_completion_bound_enabled`;
- optional all-true-dual direct-pricing activation through
  `journey_pricing_direct_journey_label_completion_bound_enabled`;
- directed-arc coarse suffix table with configurable time buckets;
- cut-safe activation for subset-row and fleet cuts;
- immediate pruning for completed direct journey labels;
- online no-waiting partial-sortie pruning when completion bounds are active;
- O(N) unique-task reward lower bound so each remaining task dual is collected
  at most once in partial-sortie pruning;
- logging for bound construction and pruning counters.

Diagnostic evidence collected on 2026-06-03, using no-waiting direct-label mode:

```text
5-task apollo15_20km_tasks05_01:
  status OPTIMAL, primal = dual = 102.041475
  solving_time about 1.3s
  bound_build_time about 0.0009s
  lb_pruned_labels / expanded_labels_before_bound = 9404 / 14520

10-task apollo15_20km_tasks10_01:
  status OPTIMAL, primal = dual = 264.024007
  solving_time about 6.6s
  bound_build_time about 0.0039s
  lb_pruned_labels / expanded_labels_before_bound = 61993 / 85679
```

The 5-task and 10-task diagnostics are below the wall-clock targets, but the
10-task label reduction is not yet a full order of magnitude in the latest
safe unique-task version.

20-task status:

```text
apollo15_20km_tasks20_02:
  bounded diagnostic with max_sequences = 50000
  bound_build_time about 0.058s
  lb_pruned_labels / expanded_labels_before_bound = 0 / 50000
```

This means the current first-version bound is still too loose for 20-task proof.
The bottleneck is direct next-sortie generation before any complete journey
label can be certified.  Do not run unbounded 20-task direct-label scans from
Python while this remains true; they can create severe memory pressure.

Next required improvement for 20-task:

```text
add a stronger physical completion bound with coarse time and energy buckets,
or move the proof-critical pricing core to NG-route/DSSR style labeling.
```

The current O(N) unique-task bound is memory-safe, but it ignores too much route
physics.  It cannot by itself prove the 20-task hard cases under the requested
200s target.

## Root 10-Task Tail Diagnostics (2026-06-03)

`tranquillitatis_balmer_like_20km_tasks10_01` remains the most useful root
certificate hard case.  Current default exact run:

```text
status = TIME_LIMIT
primal = 202.698698
dual = None
time ~= 60.05s
columns = 412
```

Important negative results:

- `journey_certificate_completion_bound_min_flat_rounds=0` is unsafe as a
  performance policy.  It is still mathematically exact, but it activates direct
  completion-bound pricing before the solver has enough columns.  On the hard
  root case it found no negative journey, consumed the full pricing budget, and
  left a worse incumbent (`206.709701`).
- `journey_certificate_proof_round_metric=no_column` with
  `journey_certificate_completion_bound_min_flat_rounds=1` also failed on the
  same case.  The retry used completion-bound direct pricing, pruned many labels,
  but replaced the streaming retry that normally finds a large batch of negative
  columns.
- For this instance, completion bounds must remain true tail-only.  They should
  not replace early or mid CG negative-column discovery.

NG-route/DSSR observations:

```text
NG from cg_iter=1, max_labels=50000:
  status = TIME_LIMIT
  primal = 202.698698
  columns = 333
  pricing calls = 19

NG from cg_iter=1, max_labels=100000:
  status = TIME_LIMIT
  primal = 202.698698
  columns = 333
  pricing calls = 17

NG from cg_iter=5, max_labels=50000:
  status = TIME_LIMIT
  primal = 202.698698
  columns = 404
```

Starting NG at iteration 1 reaches the incumbent earlier but returns too few
columns per pricing call and increases RMP iterations.  Raising the label cap to
100k did not solve the proof bottleneck.  Starting NG at iteration 5 perturbs the
default path less, but still does not close the certificate.

An opt-in diagnostic control now exists for profile-mode NG preprobes:

```text
journey_pricing_direct_journey_label_ng_probe_time_limit
journey_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return
```

With a small NG probe budget (`1.5s`) and a high early-return threshold (`16`),
the solver can continue streaming/profile pricing and merge true-negative NG
journeys into the returned candidate list.  This is exact-safe and useful for
experiments, but on the hard root case it did not improve the 60s certificate.

Next exact-pricing direction:

- keep streaming/profile as the early batch negative-column engine;
- use NG-route/DSSR later, but improve its certificate-tail behavior rather than
  simply starting it earlier or increasing the label cap;
- investigate a real NG certificate path with better dominance/state-space
  refinement, or a stronger resource-aware completion bound that helps only
  after negative-column discovery has slowed.

## Exact-Safe Dual Stabilization Evidence (2026-06-04)

Before replacing exact pricing, the current best safe speedup is to allow the
existing true-RMP dual stabilization to operate in the certificate-candidate
tail, but only after the first few CG rounds:

```text
journey_dual_stabilization_min_cg_iter = 3
journey_dual_stabilization_disable_on_certificate_candidate = False
journey_dual_stabilization_tail_only_enabled = True
journey_dual_stabilization_certificate_candidate_enabled = True
journey_dual_stabilization_mode = l1_reference
```

This is not GNN smoothing.  It uses a dual selected from the current RMP/column
pool and is accepted only when the stabilized dual passes the solver's existing
objective and current-pool dual-feasibility checks.  Official node completion
still requires true-dual exact pricing exhaustion.

Full 5-task regression after applying the 10-task config change:

```text
BPC_future/results/all_tasks05_after_10stabcfg_20260604.csv
20/20 OPTIMAL
mean time = 0.342575s
max time  = 1.130299s
```

Full 10-task rerun with the new default 10-task config:

```text
BPC_future/results/all_tasks10_default_stabcfg_20260604.csv
17/20 OPTIMAL
17/20 closed
mean time  = 26.450225s
total time = 529.004500s
max time   = 60.065157s
```

Compared with the previous default run:

```text
BPC_future/results/all_tasks10_current_docsread_20260603.csv
15/20 OPTIMAL
15/20 closed
mean time  = 28.518331s
total time = 570.366629s
```

Key improved instances:

```text
apollo15_20km_tasks10_02:
  10.189s -> 3.948s, same certified objective

tranquillitatis_balmer_like_20km_tasks10_01:
  TIME_LIMIT -> OPTIMAL, 56.455s, same objective 202.698698

tranquillitatis_balmer_like_20km_tasks10_05:
  31.948s -> 22.408s, same certified objective

tranquillitatis_balmer_like_20km_tasks10_07:
  TIME_LIMIT -> OPTIMAL, 43.173s, same objective 202.288221

tranquillitatis_balmer_like_20km_tasks10_10:
  30.784s -> 24.183s, same certified objective
```

Remaining failures:

```text
apollo15_20km_tasks10_04:
  TIME_LIMIT, primal = 288.332462, dual = 268.585633, gap = 0.068486

tranquillitatis_balmer_like_20km_tasks10_04:
  TIME_LIMIT, primal = 207.893439, no certificate dual

tranquillitatis_balmer_like_20km_tasks10_09:
  TIME_LIMIT, primal = 203.102839, no certificate dual
```

Implication: traditional stabilized-dual selection should stay enabled in the
10-task default because it is exact-safe and improves the root certificate tail
on multiple instances.  It does not solve the remaining root hard cases, so the
next work should still target NG-route/DSSR certificate behavior or a stronger
tail-only completion bound.

## Tail Diagnostics After Stabilization (2026-06-04)

The remaining root hard cases are not all the same:

```text
tranquillitatis_balmer_like_20km_tasks10_04:
  60s default: TIME_LIMIT, primal = 207.893439, no certificate dual
  90s default: OPTIMAL, time = 72.504419s, columns = 445

tranquillitatis_balmer_like_20km_tasks10_09:
  60s default: TIME_LIMIT, primal = 203.102839, no certificate dual
```

`tranq10_04` is still discovering useful negative columns near the 60s cutoff.
At 90s it closes after two more pricing/RMP rounds.  This is not a pure
no-negative proof bottleneck; the solver still needs better late negative-column
discovery or better initial columns.

`tranq10_09` reaches a final certificate candidate, then the current NG/DSSR
tail returns only weak/small batches and can consume the last pricing budget.

Negative configuration diagnostics:

```text
certificate fast negative return, min_count = 16:
  tranq10_01 regressed from OPTIMAL to TIME_LIMIT.
  tranq10_04 remained TIME_LIMIT with fewer columns.

NG/DSSR min_cg_iter = 5:
  tranq10_01 regressed from OPTIMAL to TIME_LIMIT.

completion bound enabled at certificate_flat_rounds >= 4:
  tranq10_01 regressed from OPTIMAL to TIME_LIMIT.

streaming_profile_batch_size = 1000:
  tranq10_04 remained TIME_LIMIT and returned fewer columns.

streaming_profile_batch_size = 10000:
  tranq10_04 remained TIME_LIMIT and returned fewer columns.

journey_pricing_time_limit = 60:
  tranq10_04 reached more CG rounds and more columns, but still remained
  TIME_LIMIT at 60.050615s.  The final short tail switched to NG/DSSR and did
  not certify.

journey_pricing_time_limit = 60 plus NG/DSSR disabled:
  tranq10_04 still remained TIME_LIMIT at 61.427989s.  The last round returned
  profile_dp_incomplete, so simply removing the 4-second short-pass/retry
  cadence is not enough.
```

No-default-change diagnostic:

```text
disable NG/DSSR tail:
  single tranq10_09 run closed in 59.249901s,
  but the full 10-task rerun did not improve overall results.

Full 10-task with NG tail disabled:
  BPC_future/results/all_tasks10_default_stabcfg_no_ngtail_20260604.csv
  17/20 OPTIMAL
  mean time  = 27.387274s
  total time = 547.745470s

Default stabilized config with NG tail enabled:
  BPC_future/results/all_tasks10_default_stabcfg_20260604.csv
  17/20 OPTIMAL
  mean time  = 26.450225s
  total time = 529.004500s
```

Therefore the 10-task default should keep the current NG/DSSR tail enabled for
now, even though it is not yet the right long-term certificate replacement.  The
next NG/DSSR work should avoid one-column weak tail returns and should provide a
real proof-tail advantage before being made more aggressive.  The next
completion-bound work should be stricter than simple flat-round activation,
because even flat round 4 was too early for instances that still need negative
columns.

## NG/DSSR Short-Budget Gate (2026-06-04)

Additional root-tail evidence showed that `tranq10_09` fails when the final
certificate rounds spend the last few seconds in NG/DSSR:

```text
default stabilized config:
  cg7 remaining = 5.223099s
  ng_dssr_elementary_negative_journey, 50000 labels, 1 column
  cg8 remaining = 2.143798s
  ng_dssr_time_limit, no certificate
  final status = TIME_LIMIT

single diagnostic with NG tail disabled:
  final status = OPTIMAL
  time = 59.249901s
```

The accepted V1 fix is a budget gate:

```text
journey_pricing_direct_journey_label_ng_disable_below_remaining = 8.0
```

When the exact-pricing budget remaining is below this threshold, NG/DSSR is
disabled and the solver falls back to the original exact profile/DP pricing
path.  This is exact-safe because it only removes a heuristic/relaxed front-end;
the official no-negative certificate is still produced by true-dual exact
pricing.

Validation:

```text
BPC_future/results/probe_ng_remaining_gate8_t09_20260604.csv
  tranq10_09: OPTIMAL, time = 59.169420s

BPC_future/results/probe_ng_remaining_gate8_t04_t01_20260604.csv
  tranq10_04: TIME_LIMIT, time = 61.409052s, columns = 445
  tranq10_01: OPTIMAL, time = 57.480601s

BPC_future/results/all_tasks10_ng_remaining_gate8_20260604.csv
  18/20 OPTIMAL
  mean time  = 26.513728s
  total time = 530.274563s
  max time   = 61.393672s

BPC_future/results/all_tasks05_after_ng_gate8_20260604.csv
  20/20 OPTIMAL
  mean time = 0.345386s
  max time  = 1.156171s
```

Compared with `all_tasks10_default_stabcfg_20260604.csv`, the gate improves
the full 10-task closure count from `17/20` to `18/20`.  The new certified
instance is:

```text
tranquillitatis_balmer_like_20km_tasks10_09:
  TIME_LIMIT 60.045788s -> OPTIMAL 57.839864s
```

Remaining 10-task failures after this gate:

```text
apollo15_20km_tasks10_04:
  TIME_LIMIT, primal = 288.332462, dual = 268.585633, gap = 0.068486

tranquillitatis_balmer_like_20km_tasks10_04:
  TIME_LIMIT, primal = 207.893439, no certificate dual
```

Implication: the 8-second NG/DSSR short-budget gate should stay in the 10-task
trial config.  It solves the known one-column NG tail failure without sacrificing
exactness.  It does not solve `tranq10_04`, whose logs still show late strong
negative-column discovery and insufficient CG rounds before the 60-second
cutoff.

Rerun audit after a temporary config drift to `0.0`:

```text
BPC_future/results/all_tasks10_current_20260604_rerun.csv
  current config with NG short-budget gate = 0.0
  17/20 OPTIMAL
  mean time  = 26.300761s
  total time = 526.015227s
  max time   = 61.378340s
  failed: apollo10_04, tranq10_04, tranq10_09

BPC_future/results/all_tasks10_doc_gate8_20260604_rerun.csv
  same current code, command-line override gate = 8.0
  18/20 OPTIMAL
  mean time  = 26.011679s
  total time = 520.233583s
  max time   = 61.175973s
  failed: apollo10_04, tranq10_04

BPC_future/results/all_tasks05_current_20260604_rerun.csv
  20/20 OPTIMAL
  mean time = 0.398405s
  max time  = 1.147436s
```

The only status difference in the 10-task rerun was:

```text
tranquillitatis_balmer_like_20km_tasks10_09:
  gate = 0.0: TIME_LIMIT, primal = 203.102839, no certificate dual
  gate = 8.0: OPTIMAL, primal = dual = 203.102839, time = 57.443249s
```

Therefore the 10-task trial config must keep:

```text
journey_pricing_direct_journey_label_ng_disable_below_remaining = 8.0
```

## NG Probe Certificate Switch (2026-06-04)

An opt-in certificate return path now exists for profile-mode NG preprobes:

```text
journey_pricing_direct_journey_label_ng_probe_certificate_enabled
```

Default is `False`.  When enabled, profile pricing lets the NG preprobe run with
`direct_journey_label_ng_certificate_enabled=True`.  The preprobe may close the
pricing call only if all of the following hold:

```text
ng_probe.exhausted = True
ng_probe.status = OPTIMAL
ng_probe.ng_certificate_from_relaxation = True
```

This is exact-safe because NG-route relaxation is a superset of elementary
journeys: if the relaxed pricing is exhausted and has no negative reduced-cost
journey, then no elementary journey can be negative either.  In all incomplete
or time-limited cases the solver still falls back to the ordinary profile/DP
pricing path.

Initial hard-case probes with:

```text
journey_pricing_direct_journey_label_ng_probe_certificate_enabled = True
journey_pricing_direct_journey_label_ng_min_cg_iter = 6
journey_pricing_direct_journey_label_ng_disable_below_remaining = 0.0
journey_pricing_direct_journey_label_ng_max_labels = 200000
```

did not close the two remaining 10-task failures:

```text
BPC_future/results/probe_t04_ng_probe_cert_200k_20260604.csv
  tranq10_04: TIME_LIMIT, time = 60.050383s, columns = 445

BPC_future/results/probe_a04_ng_probe_cert_200k_20260604.csv
  apollo10_04: TIME_LIMIT, time = 60.092921s, gap = 0.068486
```

For `tranq10_04`, the final NG probe had positive best relaxed RC
(`0.266823346`) but stopped with `ng_dssr_time_limit`, so it could not issue an
official relaxed certificate.  The conclusion is that the certificate return
path is useful infrastructure, but the current NG/DSSR implementation still
needs stronger dominance/state-space control or more targeted activation before
it can replace the profile proof tail.

Follow-up diagnostics that were not adopted:

```text
direct long certificate pricing after flat round 1:
  tranq10_04 remained TIME_LIMIT, columns increased to 467.
  It removed short 4s empty passes but still found late strong negative columns.
  tranq10_09 regressed from OPTIMAL to TIME_LIMIT, so this must not be default.

late fast-negative return after proof round 6, min_count = 8:
  tranq10_04 remained TIME_LIMIT, columns = 461.
  The late 8 negative journeys were still found near the end of the search, so
  the smaller batch did not buy enough extra RMP/certificate time.

streaming negative batch = 128 with direct long pricing:
  tranq10_04 remained TIME_LIMIT, columns = 468.
  Larger batches changed the column mix but did not reduce the proof tail.

skip initial journey pool MIP:
  tranq10_04 remained TIME_LIMIT, columns = 461.

SCIP original duals on certificate candidates:
  tranq10_04 remained TIME_LIMIT, columns = 468.

profile catalog/resume instead of label physical catalog:
  tranq10_04 remained TIME_LIMIT, columns = 252.
  This generated too few useful columns and should not replace the current label
  physical catalog path.

streaming final-DP time reserve:
  New opt-in control:
    journey_pricing_streaming_final_dp_time_reserve
  Default remains 0.0.  The control shortens only streaming profile-generation
  time, leaving the final journey DP with the original pricing deadline.  This
  is exact-safe because interrupted generation leaves the pricing result
  incomplete; it cannot produce a no-negative certificate.

  tranq10_04, reserve = 0.75:
    TIME_LIMIT, time = 60.775519s, columns = 418.
    It did make cg2/cg3 run nonzero final-DP labels before returning negative
    columns, but later rounds still fell back to retry/incomplete behavior.

  tranq10_04, reserve = 1.5:
    TIME_LIMIT, time = 60.039870s, columns = 380.

  Conclusion:
    This is useful diagnostic infrastructure for separating profile generation
    time from final DP time, but it is not a default 10-task speedup.

profile record time-filter cache:
  The compatible-profile cache now also memoizes repeated
  `(used_mask, min_upper_start)` filtered record lists for 10-task-and-smaller
  DP calls.  This does not change the candidate set or exactness; it only avoids
  rebuilding identical filtered tuples during profile-journey DP.

  tranq10_04:
    BPC_future/results/probe_t04_profile_record_cache_20260604.csv
    TIME_LIMIT, time = 60.456623s, columns = 445.

  sanity:
    tranq05_03 OPTIMAL, time = 0.612373s.
    apollo10_07 OPTIMAL, time = 21.421739s.

  Conclusion:
    Safe to keep as a small default cache, but it does not solve the remaining
    certificate bottleneck.

profile-DP cut-aware suffix bound:
  The profile-journey DP suffix bound was extended to stay enabled when the
  active cut duals are subset-row cuts and fleet cuts.  The safe pruning formula
  now evaluates:

    base_rc + current_profile_value + optimistic_suffix_profile_value
      - realized_cut_dual_value(current_mask)
      - future_positive_src_reward_upper_bound
      - future_positive_fleet_reward_upper_bound

  Positive subset-row duals are handled by subtracting an upper bound on the
  extra reward reachable with the remaining sortie/task capacity.  Negative SRC
  duals only add future penalties, so ignoring those future penalties remains
  optimistic.  Fleet cuts are safe because their journey coefficient is fully
  realized once the partial mask is non-empty; for the empty start mask the
  bound subtracts the maximum positive fleet reward that could appear in any
  future non-empty completion.  Other dynamic cut families still disable this
  profile-DP suffix pruning path.

  Unit tests added:
    journey_profile_dp_bound_pruning_keeps_positive_src_reward_negative
    journey_profile_dp_bound_pruning_uses_positive_src_reward_bound
    journey_profile_dp_bound_pruning_keeps_positive_fleet_reward_negative

  Probes:
    tranq05_03 sanity:
      OPTIMAL, time = 0.594562s / 0.613241s in the follow-up sanity run.

    tranq10_04 default with cut-aware bound:
      TIME_LIMIT, time = 60.303189s, columns = 445.
      dp_bound_pruned_labels stayed 0.  In the early rounds, optimistic
      continuation values were still negative enough that no label could be
      pruned; in later rounds, profile generation exhausted the capped pricing
      deadline before profile-DP processed labels.

    tranq10_04 with streaming_final_dp_time_reserve = 0.75:
      TIME_LIMIT, time = 60.772686s, columns = 418.
      profile-DP processed labels in cg2-cg4, but dp_bound_pruned_labels still
      stayed 0.  Cross-count dominance, not completion-bound pruning, remained
      the dominant reducer.

  Conclusion:
    This is exact-safe and covered by tests, but it is not the main bottleneck
    on the current tranq10_04 proof tail.

certificate-stage parameter probes, not adopted:
  immediate certificate no-reserve:
    Added as an opt-in helper
      journey_certificate_immediate_no_reserve_enabled
    but kept disabled in the 10-task trial config.  On tranq10_04 it changed the
    column generation path and worsened the result:
      TIME_LIMIT, time = 61.302478s, columns = 467.

  streaming negative batch = 128:
    TIME_LIMIT, time = 61.515639s, columns = 455.
    More negative journeys per batch increased per-round work and did not remove
    the proof tail.

  SCIP original duals on certificate candidates:
    TIME_LIMIT, time = 60.941419s, columns = 422.
    This reduced columns versus the stabilized path but still did not close
    within 60s, so it is not enough by itself.

  retry generation fraction = 0.0:
    TIME_LIMIT, time = 61.408900s, columns = 445.
    It followed essentially the same capped-exact plus retry pattern, so this
    did not remove the repeated profile-generation cost.

NG/DSSR certificate safety note:
  Current default 10-task runs use NG/DSSR only as a probe/helper; relaxed
  no-negative certificates are not accepted unless
  `direct_journey_label_ng_certificate_enabled=True`.

  A safety guard was added for that future certificate mode: when NG relaxed
  dominance is used with nonzero cut duals, the dominance key includes the
  unique visited-task mask.  Without this, two labels with the same NG memory,
  current partial state, and completed-sortie count but different SRC/fleet cut
  masks could incorrectly dominate each other.  That would be unacceptable for
  an official relaxed no-negative certificate.

  Unit test added:
    direct_ng_certificate_dominance_key_can_include_visit_mask

  Sanity:
    apollo10_01 with the current default probe behavior:
      OPTIMAL, time = 1.824199s, primal/dual = 264.024007.

profile-DP time-filter index:
  The compatible-profile cache now uses a lazy per-mask segment index for
  `upper_start >= current_label_end_time` queries.  It preserves the existing
  profile-DP scan order but avoids linearly scanning time-infeasible profiles
  for every DP label.  This is exact-safe because it returns the same records
  as the old filter in the same order.

  Unit tests added/updated:
    compatible_profile_cache_time_index_preserves_scan_order
    compatible_profile_cache_reuses_time_filtered_records

  Probes:
    tranq05_03 sanity:
      OPTIMAL, time = 0.602224s.

    apollo10_01 sanity:
      OPTIMAL, time = 1.772932s, primal/dual = 264.024007.

    tranq10_04:
      TIME_LIMIT, time = 60.059618s, columns = 445.
      This is slightly faster than the prior 60.303s/60.178s probes, and cg6
      reached the final negative batch at about 60.01s, but it still cannot
      complete the next RMP solve and no-negative certificate within 60s.

  Conclusion:
    Safe to keep as a small default micro-optimization, but the remaining
    10-task hard-case gap still requires a larger certificate-tail change.

NG dominance key experiment:
  Added an opt-in control:

    journey_pricing_direct_journey_label_ng_sequence_key_enabled

  Default remains True.  When disabled, NG dominance keys use the current sortie
  task mask instead of the full current sequence.  This can strengthen
  dominance for future NG certificate work, while the certificate cut-mask guard
  described above remains active when relaxed certificates are enabled.

  Probe:
    tranq10_04 with sequence key disabled:
      TIME_LIMIT, time = 60.142769s, columns = 445.
      NG did not become active before the 60s cutoff on this run, so this did
      not improve the current hard case.  Keep it opt-in for now.

Branch-node NG preprobe support:
  NG/DSSR profile preprobes can now run at branch nodes.  Returned candidate
  journeys are filtered with the same task-set branch semantics used by the
  profile-pricing path:

    same_vehicle(i, j): returned journey must contain either both tasks or
      neither task.

    separate_vehicle(i, j): returned journey must not contain both tasks.

  This is exact-safe because NG still contributes only feasible true-negative
  candidate columns.  Relaxed NG no-negative certificates remain disabled when
  branch constraints are present, and the elementary direct-label fallback is
  not used under branch constraints because that fallback currently does not
  carry branch rows.

  Unit coverage:
    ng_preprobe_profile_pricing_filters_branch_infeasible_journeys

  Probes on `apollo15_20km_tasks10_04`:

    branch NG from cg1, probe time limit = 0.5s:
      TIME_LIMIT, time = 60.191749s, nodes = 10, columns = 236.
      The branch tree became smaller than the default 14-node path, but repeated
      NG probes consumed enough time that the instance still did not close.

    branch NG from cg1, probe time limit = 0.2s:
      TIME_LIMIT, time = 60.129714s, nodes = 12, columns = 240.
      This kept some tree reduction, but still did not produce a 60s
      certificate.  Logs show 28 NG probe events and about 93k NG label pops,
      so all-node probing is still too expensive as a default policy.

  Default sanity after the branch-NG implementation:

    apollo10_01:
      OPTIMAL, time = 1.774874s, primal/dual = 264.024007.

    tranq10_09:
      OPTIMAL, time = 57.364718s, primal/dual = 203.102839.

  Conclusion:
    Branch-node NG preprobe is now available for controlled experiments and is
    branch-safe, but it should stay off by default until a more selective
    trigger is identified.

Streaming profile/DP time split audit:
  The streaming-profile pricing path now honors
  `profile_generation_time_fraction` when computing the generation deadline,
  matching the non-streaming profile oracle semantics.  The existing
  `streaming_final_dp_time_reserve` remains active and can shorten that
  deadline further.  Unit coverage was added for both controls.

  The current 10-task default config intentionally sets:

    journey_pricing_profile_generation_time_fraction = 1.0
    journey_retry_incomplete_no_column_generation_fraction = 1.0

  Rationale:
    Before this fix, streaming mode effectively behaved like fraction 1.0.
    Enabling the old configured 0.9/0.95 split changed the hard-case column
    path and did not improve the certificate tail.

  Probes on `tranquillitatis_balmer_like_20km_tasks10_04`:

    default after honoring 0.9/0.95:
      TIME_LIMIT, time = 61.305140s, columns = 418.
      cg2 found 31 negative journeys in the first 4s call, but the later path
      still failed to certify within 60s.

    restore streaming behavior with 1.0/1.0:
      TIME_LIMIT, time = 60.233080s, columns = 445.
      This is closer to the previous streaming path but still not a certificate.

    streaming negative batch 32:
      TIME_LIMIT, time = 61.093953s, columns = 321.

    streaming negative batch 16:
      TIME_LIMIT, time = 60.631526s, columns = 286.
      It reached cg7 but still only found more negative columns before the
      deadline; no no-negative certificate was obtained.

    static/dynamic SRC disabled:
      TIME_LIMIT, time = 60.843978s, columns = 249.
      Startup remained expensive because the initial trip/journey pool build,
      not SRC construction, is the dominant pre-CG cost on this instance.

    initial savings seed budget reduced to 1000 evaluations / 80 trips:
      TIME_LIMIT, time = 61.377330s, columns = 402.

  Sanity with restored 1.0/1.0 config:

    apollo10_01:
      OPTIMAL, time = 1.791404s, primal/dual = 264.024007.

    tranq10_09:
      OPTIMAL, time = 56.983726s, primal/dual = 203.102839.

  Conclusion:
    The streaming time-split control is now correctly wired and can be used for
    future experiments, but the current hard 10-task root tail still requires a
    stronger pricing/certificate mechanism.  Do not lower the default
    generation fraction or negative-batch threshold based on the current probes.
```

Root-only late NG preprobe default audit (2026-06-04):

  Default change:
    Enable direct journey-label NG/DSSR probing only at the root, only from the
    late CG tail, with a small probe budget:

      journey_pricing_direct_journey_label_ng_min_cg_iter = 7
      journey_pricing_direct_journey_label_ng_disable_below_remaining = 0.0
      journey_pricing_direct_journey_label_ng_probe_time_limit = 0.4
      journey_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return = 4
      journey_branch_pricing_direct_journey_label_ng_dssr_enabled = False

    This keeps branch nodes on the original exact path and keeps NG as a
    candidate-column preprobe, not as a relaxed certificate.

  Full 5-task audit:

    BPC_future/results/all_tasks05_after_ng_root_tail_default_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.754659s
      mean solver time  = 0.337733s
      max solver time   = 1.119035s

    Compared with
    BPC_future/results/all_tasks05_docread_current_20260604_060015.csv:
      20 / 20 OPTIMAL before and after
      no objective/status changes

  Full 10-task audit:

    BPC_future/results/all_tasks10_ng_root_tail_default_20260604.csv
      18 / 20 OPTIMAL
      total solver time = 517.997096s
      mean solver time  = 25.899855s
      max solver time   = 61.157995s

    Compared with
    BPC_future/results/all_tasks10_docread_current_20260604_060015.csv:
      17 / 20 OPTIMAL -> 18 / 20 OPTIMAL
      total solver time 522.382398s -> 517.997096s
      tranq10_09 closed:
        TIME_LIMIT 61.116034s -> OPTIMAL 58.219922s
        columns 437 -> 436

    Remaining failures:
      apollo15_20km_tasks10_04:
        TIME_LIMIT, primal = 288.332462, dual = 268.585633,
        gap = 0.068486, nodes = 14, columns = 241.

      tranquillitatis_balmer_like_20km_tasks10_04:
        TIME_LIMIT, primal = 207.893439, no certificate dual,
        root node only, columns = 445.

  Conclusion:
    The root-only late NG preprobe is a safe small default improvement: it
    closes one boundary 10-task instance without changing 5-task behavior.  It
    does not solve the main hard-case bottleneck.  The next acceleration target
    remains true-dual exact-pricing proof work, especially completion bounds and
    a production NG-route+DSSR certificate path.

Completion-bound activation probes (2026-06-04):

  The code already contains an opt-in direct-label completion bound:

    journey_certificate_completion_bound_enabled
    journey_certificate_completion_bound_min_flat_rounds
    journey_certificate_completion_bound_time_buckets
    journey_certificate_completion_bound_energy_buckets

  A new diagnostic switch was added:

    journey_certificate_completion_bound_partial_pruning_enabled

  Default remains True.  When True, completion-bound pruning can run inside
  sortie partial-label generation, and direct-label pricing disables the
  next-sortie profile cache because the partial bound depends on the parent
  journey label value, count, and end time.  When False, pruning is only applied
  after a complete sortie has been instantiated as a journey-label extension,
  allowing the next-sortie profile cache to stay active.  This is exact-safe
  because disabling partial pruning only removes pruning.

  Probes on `tranquillitatis_balmer_like_20km_tasks10_04`:

    completion bound, flat metric, min round = 1, time buckets = 10:
      BPC_future/results/probe_tranq10_04_completion_min1_20260604.csv
      TIME_LIMIT, time = 60.459384s, columns = 240.
      Final retry pruned 28,013 labels out of 466,257 checked labels.
      Max RSS about 3.38 GB.

    completion bound, energy buckets = 10:
      BPC_future/results/probe_tranq10_04_completion_energy10_20260604.csv
      TIME_LIMIT, time = 60.459124s, columns = 240.
      Final retry pruned 34,068 labels out of 473,002 checked labels.
      Max RSS about 3.38 GB.

    completion bound with no-column proof metric:
      BPC_future/results/probe_tranq10_04_completion_nocolumn_20260604.csv
      TIME_LIMIT, time = 60.447595s, columns = 240.
      The first 4-second profile call at cg2 returned no column, so the retry
      immediately switched to direct-label completion-bound proof and skipped
      the streaming retry that normally finds another 64 negative journeys.

    cache-preserving completion bound:
      BPC_future/results/probe_tranq10_04_completion_cache_20260604.csv
      TIME_LIMIT, time = 61.054846s, columns = 240.
      Max RSS rose to about 8.53 GB because the cached profile set became large,
      and no journey-label pruning occurred before the profile generation time
      limit.  Keep this mode experimental only.

  Conclusion:
    Do not enable completion bounds by default yet.  The current bound is cheap
    to build and exact-safe, but on this hard root-tail instance it activates
    too early and diverts time away from streaming negative-column discovery.
    The next useful step is a stricter activation contract: completion-bound
    proof should start only after the normal exact retry path has also failed to
    return a true-RC negative column, or inside a dedicated final certificate
    call with enough remaining time.

  Default-path regression after adding the partial-pruning switch:

    BPC_future/results/all_tasks05_after_completion_switch_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.299535s
      mean solver time  = 0.314977s
      max solver time   = 1.435529s
      max RSS about 78 MB

    BPC_future/results/probe_apollo10_01_after_completion_switch_20260604.csv
      OPTIMAL, time = 1.960886s, primal/dual = 264.024007.

    Since completion bounds remain disabled by default, the new switch does not
    change the normal 5-task path or the representative fast 10-task path.

    Default-path regression after adding the after-retry switch:

      BPC_future/results/all_tasks05_after_afterretry_switch_20260604.csv
        20 / 20 OPTIMAL
        total solver time = 6.360781s
        mean solver time  = 0.318039s
        max solver time   = 1.475342s
        max RSS about 78 MB

      BPC_future/results/probe_apollo10_01_after_afterretry_switch_20260604.csv
        OPTIMAL, time = 1.830687s, primal/dual = 264.024007.

  After-retry activation contract:

    A stricter opt-in activation switch was added:

      journey_certificate_completion_bound_after_retry_enabled

    When enabled, normal exact pricing and the normal incomplete-no-column retry
    do not activate completion bounds.  Completion-bound direct-label pricing is
    only eligible for a final retry after that normal retry also returns no
    true-RC negative journey and remains incomplete.  This preserves the
    streaming/profile retry path that is still useful for discovering negative
    columns.

    Probe:

      BPC_future/results/probe_tranq10_04_completion_after_retry_20260604.csv
        TIME_LIMIT, time = 61.404445s, columns = 445.
        Max RSS about 310 MB.

    The log confirms that cg2-cg5 normal retries still returned 64 negative
    journeys each, matching the default column-discovery path.  No
    completion-bound final retry ran because the last cg6 exact call had only
    about 1 second left, below the useful final-retry budget.

    Conclusion:
      The after-retry contract fixes the premature-activation problem and keeps
      memory under control, but by itself it does not close `tranq10_04`.  The
      next bottleneck is budget allocation: the normal retry can consume nearly
      all tail time while still finding negative columns, leaving no time for a
      final certificate attempt.

  Final-retry time reserve probe:

    A second opt-in budget switch was added:

      journey_certificate_completion_bound_after_retry_reserve_time

    When a final after-retry completion-bound call is eligible, this caps the
    normal incomplete-no-column retry so the requested reserve remains for the
    final certificate attempt.  The default is `0.0`, so the normal retry budget
    is unchanged unless this probe switch is explicitly set.

    Probe:

      BPC_future/results/probe_tranq10_04_completion_after_retry_reserve8_20260604.csv
        TIME_LIMIT, time = 60.110976s, columns = 390.
        Max RSS about 746 MB.

    The log confirms:

      cg2-cg4 normal retries still returned 64 negative journeys each.
      cg5 normal retry was capped from about 13.0s to about 5.0s.
      cg5 final completion-bound retry then ran for about 6.7s.
      The final bound pruned only 72 labels out of 53,818 checked labels and
      remained incomplete.

    Default-path regression after adding the reserve switch:

      BPC_future/results/all_tasks05_after_retry_reserve_switch_20260604.csv
        20 / 20 OPTIMAL
        total solver time = 6.336102s
        mean solver time  = 0.316805s
        max solver time   = 1.438991s
        max RSS about 78 MB

      BPC_future/results/probe_apollo10_01_after_retry_reserve_switch_20260604.csv
        OPTIMAL, time = 1.834156s, primal/dual = 264.024007.

    Conclusion:
      Reserving time for the current completion bound is not enough.  The
      direct-label completion bound is too loose on this instance.  Future work
      should focus on a stronger certificate oracle, most likely production
      NG-route+DSSR with tighter dominance and completion bounds, rather than
      spending more default budget on the current direct-label bound.

NG memory boundary audit (2026-06-04):

  The direct NG labeler previously carried `ng_memory` across a completed
  sortie into the next depot-started sortie.  That is too restrictive for a
  relaxed certificate oracle: NG neighborhood memory is local route-segment
  memory and should reset at a depot/recharge boundary.  Only DSSR critical
  tasks should remain globally forbidden across sorties.

  Implementation:

    direct_journey_label_ng_reset_memory_between_sorties_enabled

  Default is `False` for ordinary NG preprobes to preserve the current
  performance path.  When `direct_journey_label_ng_certificate_enabled=True`,
  the reset is forced internally because a relaxed no-negative certificate must
  be based on a true relaxation rather than on an over-restricted state space.

  Probe on `tranquillitatis_balmer_like_20km_tasks10_04`:

    Baseline diagnostic with earlier NG and 2s probe:
      BPC_future/results/probe_tranq10_04_ng_mincg5_probe2_20260604.csv
      TIME_LIMIT, time = 60.046173s, columns = 445.
      NG best relaxed RC stayed positive at about 0.56458.

    Opt-in boundary reset with same 2s probe:
      BPC_future/results/probe_tranq10_04_ng_reset_probe2_20260604.csv
      TIME_LIMIT, time = 61.462557s, columns = 390.
      NG still did not find negative columns; the extra NG search displaced
      streaming retry time and reduced the column count.

  Default-path regression after adding the switch:

    BPC_future/results/all_tasks05_after_ng_memory_switch_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.342126s
      mean solver time  = 0.317106s
      max solver time   = 1.497842s
      max RSS about 78 MB

    BPC_future/results/probe_apollo10_01_after_ng_memory_switch_20260604.csv
      OPTIMAL, time = 1.846687s, primal/dual = 264.024007.

    BPC_future/results/probe_tranq10_09_after_ng_memory_switch_20260604.csv
      OPTIMAL, time = 58.340447s, primal/dual = 203.102839.

  Conclusion:
    The boundary reset is necessary infrastructure for a future relaxed NG
    certificate, but it is not a speed improvement for the current ordinary
    preprobe.  Keep it opt-in outside certificate mode.

NG branch partial-mask pruning audit (2026-06-04):

  Branch-side NG probing is still not a default speedup, but the NG labeler now
  has one exact-safe partial pruning rule for branch nodes:

    when all active branch rows are same/separate Ryan-Foster rows,
    immediately reject a partial relaxed NG label whose unique visited-task mask
    already violates a `separate_vehicle(i, j)` row.

  This is one-sided and exact-safe:

    - `separate_vehicle`: once both tasks are already in the same journey label,
      no future sortie can repair the violation.
    - `same_vehicle`: partial labels are not pruned just because only one side
      has appeared; the missing side may still be added later.
    - task-vehicle or unknown branch rows are not handled by this partial rule.

  Unit coverage:

    `test_direct_ng_relaxed_iteration_prunes_separate_branch_partial_mask`
    constructs a two-task case where single-task journeys are nonnegative but
    the two-task journey is negative.  Without the branch row, relaxed NG returns
    the two-task negative journey.  With `separate_vehicle(1,2)`, it returns no
    negative journey and the relaxed best RC is nonnegative.

  Opt-in probe on `apollo15_20km_tasks10_04`, with branch NG enabled from cg1
  and a 0.2s probe budget:

    Before partial pruning:
      BPC_future/results/probe_apollo10_04_branch_ng_20260604_0730.csv
      TIME_LIMIT, time = 60.119274s, nodes = 12, columns = 238.
      NG events generated 104,619 labels and pruned 57,222 by dominance.

    After partial pruning:
      BPC_future/results/probe_apollo10_04_branch_ng_partialprune_20260604.csv
      TIME_LIMIT, time = 60.006230s, nodes = 12, columns = 240.
      NG events generated 102,401 labels and pruned 55,193 by dominance.

  Interpretation:

    The pruning is directionally correct and useful infrastructure for future
    branch NG/DSSR, but the observed reduction is too small to justify enabling
    branch NG by default.  Keep
    `journey_branch_pricing_direct_journey_label_ng_dssr_enabled=False`.

  Negative streaming-batch probe on `tranquillitatis_balmer_like_20km_tasks10_04`:

    BPC_future/results/probe_tranq10_04_stream_min32_20260604.csv
      TIME_LIMIT, time = 61.398115s, columns = 321.

    Lowering `streaming_min_negative_batch` from 64 to 32 returned smaller
    batches too early and reduced useful column volume.  Do not adopt this
    parameter as a default.

Skip-short exact-pricing cadence probe (2026-06-04):

  Diagnostic conclusion from comparing 60s and 90s logs on
  `tranquillitatis_balmer_like_20km_tasks10_04`:

    - The 60s and 90s default paths are essentially identical through cg5.
    - At about 58.7s the 90s run still has enough time to finish cg6 negative
      pricing and cg7 no-negative certification.
    - The 60s run reaches cg6 with only about 1.3s of pricing budget left.

  An opt-in cadence switch was added:

    journey_skip_short_exact_after_retry_negative_enabled
    journey_skip_short_exact_min_retry_negative_rounds
    journey_skip_short_exact_min_cg_iter
    journey_skip_short_exact_root_only
    journey_skip_short_exact_certificate_only
    journey_skip_short_exact_max_time_limit

  Default is disabled.  When enabled, after repeated rounds where a short exact
  pass returns no column but the retry returns true-negative columns, the next
  short exact pass can be skipped and replaced by the same true-dual pricing
  oracle using the longer retry-style budget.  This is exact-safe because an
  incomplete pricing run remains incomplete; the switch never creates a
  no-negative certificate.

  Probe:

    BPC_future/results/probe_tranq10_04_skip_short_exact_h2_20260604.csv
      TIME_LIMIT, time = 61.516166s, columns = 463.

    BPC_future/results/probe_tranq10_04_skip_short_h2_nggate8_20260604.csv
      TIME_LIMIT, time = 61.576554s, columns = 463.

  Interpretation:

    The switch behaved as intended and skipped the short pass at cg4-cg7.  It
    increased the number of generated columns from the default 445 to 463, but
    still did not leave enough time for a certificate.  Adding the 8-second NG
    remaining-time gate changed the final oracle back to profile/DP, but the
    final cg7 call still had only about 2.2s and remained incomplete.  Keep this
    switch as diagnostic infrastructure only; do not enable it by default.

  Default-path regression after adding the disabled switch:

    BPC_future/results/all_tasks05_after_skip_short_switch_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.907732s
      mean solver time  = 0.345387s
      max solver time   = 1.158440s

    BPC_future/results/probe_10_representative_after_skip_short_switch_20260604.csv
      apollo15_20km_tasks10_01:
        OPTIMAL, time = 1.799659s, primal/dual = 264.024007.
      tranquillitatis_balmer_like_20km_tasks10_09:
        OPTIMAL, time = 58.848515s, primal/dual = 203.102839.
        Max RSS for the two-instance run was about 297 MB.

Streaming timing diagnostics (2026-06-04):

  The streaming-profile partial-return path now records nonzero timing and DP
  counters for both callback returns and ordinary incomplete returns:

    - `profile_generation_time` for time spent generating/resuming sortie
      profiles before the callback/final DP.
    - `profile_dp_time` for the profile-to-journey DP call.
    - `dp_processed_labels`, `dp_state_count`, `dp_profile_record_scans`, and
      `dp_extension_attempts` even when the profile DP returns early with a
      negative journey.

  Tests:

    test_streaming_partial_result_records_callback_times
    test_journey_profile_dp_early_return_records_stats

  Diagnostic probe:

    BPC_future/results/probe_tranq10_04_stream_stats25_fulltiming_20260604.csv
      TIME_LIMIT by design at 25s, columns = 339, max RSS about 202 MB.

  Key log evidence on `tranquillitatis_balmer_like_20km_tasks10_04`:

    cg1 exact:
      streaming_partial_negative_journey
      profile_generation_time = 1.356716s
      profile_dp_time         = 0.250966s
      dp_processed_labels     = 3998

    cg2 exact short pass:
      profile_dp_incomplete
      profile_generation_time = 4.139769s
      profile_dp_time         = 0.064591s
      dp_processed_labels     = 0

    cg2 exact_retry:
      streaming_partial_negative_journey
      profile_generation_time = 5.586094s
      profile_dp_time         = 0.446298s
      dp_processed_labels     = 5

    cg4 exact short pass:
      profile_dp_incomplete
      profile_generation_time = 4.139720s
      profile_dp_time         = 0.238820s

  Interpretation:

    The expensive part of the `tranq10_04` tail is not the profile-to-journey
    DP.  The short no-column passes are spending almost all of their 4-second
    budget inside sortie profile generation/resume before the DP sees enough
    profiles.  The next real speed target is therefore the profile-label
    generation/resume engine, especially why later batches require many more
    evaluated timed trips to append another useful block of profiles.

  Default-path regression after adding the timing-only diagnostics:

    BPC_future/results/all_tasks05_after_stream_timing_stats_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.885955s
      mean solver time  = 0.344298s
      max solver time   = 1.147544s

    BPC_future/results/probe_apollo10_01_after_stream_timing_stats_20260604.csv
      OPTIMAL, time = 1.809634s, primal/dual = 264.024007.

  Default-path regression after adding the partial-mask pruning:

    BPC_future/results/all_tasks05_after_ng_branch_partialprune_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.848770s
      mean solver time  = 0.342439s
      max solver time   = 1.133384s

    BPC_future/results/probe_10_representative_after_ng_branch_partialprune_20260604.csv
      apollo15_20km_tasks10_01:
        OPTIMAL, time = 1.827224s, primal/dual = 264.024007.
      tranquillitatis_balmer_like_20km_tasks10_09:
        OPTIMAL, time = 59.159807s, primal/dual = 203.102839.
        Max RSS for the two-instance run was about 296 MB.

## Resume Label Active-Set Check (2026-06-04)

The sortie profile resume heap uses lazy deletion: dominated partial labels can
remain in the heap until they are popped.  The old validity check used:

```text
label in state.labels_by_key[(mask, last)]
```

which is a linear list membership test.  In late `tranq10_04` root-tail rounds,
the resume state contains tens of thousands of labels/profiles, so this check
adds Python overhead on every stale heap pop.

Implemented exact-safe data-structure change:

```text
_SortieLabelResumeState.active_label_ids: set[int]
```

When a partial label is inserted, its `id()` is added to the set.  When it is
removed by partial-label dominance, its `id()` is removed.  Heap-pop validity
now uses O(1) membership in this active-id set.  This does not change dominance,
profile generation, reduced-cost calculations, candidate filtering, or the
certificate path.

Unit coverage:

```text
test_sortie_partial_active_label_ids_track_dominance
```

Validation:

```text
python -m unittest BPC_future.tests.test_bpc_future -k sortie_partial_active_label_ids
python -m unittest BPC_future.tests.test_bpc_future -k direct_ng
python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/tests/test_bpc_future.py
```

Representative probes:

```text
BPC_future/results/probe_t05_active_label_ids_sanity_20260604.csv
  tranq05_03: OPTIMAL, time = 0.614287s

BPC_future/results/probe_a10_01_active_label_ids_sanity_20260604.csv
  apollo10_01: OPTIMAL, time = 1.744645s

BPC_future/results/probe_t04_active_label_ids_20260604.csv
  tranq10_04: TIME_LIMIT, primal = 207.893439, no certificate dual
  columns = 445
```

`tranq10_04` did not close within 60 seconds, but the profile-generation path
did improve:

```text
before active-id check:
  cg5 exact_retry returned 64 negative journeys at t = 58.579s
  total profile_generation_time through finish = 48.508s

after active-id check:
  cg5 exact_retry returned 64 negative journeys at t = 56.487s
  cg6 found the final 6 negative journeys at t = 59.355s
  total profile_generation_time through finish = 46.545s
```

The run still missed the final no-negative certificate because after cg6 only
about `0.42s` remained for cg7 exact pricing.

Additional timing-only instrumentation now records final streaming
`profile_filter_time`, separating it from generation and DP time.  A 25-second
diagnostic showed:

```text
BPC_future/results/probe_t04_active_filter_timing25_20260604.csv
  cg2 exact:
    profile_generation_time = 4.118362s
    profile_filter_time     = 0.106996s
    profile_dp_time         = 0.065324s

  cg3 exact:
    profile_generation_time = 4.203755s
    profile_filter_time     = 0.239933s
    profile_dp_time         = 0.194178s
```

Interpretation:

- The active-id check is safe and worth keeping as a small default
  micro-optimization.
- It is not enough to meet the 60-second target on `tranq10_04`.
- The next larger exact-pricing target should be a faster exhausted-catalog
  filter/index path or a stronger NG/DSSR certificate path.  At the very end of
  `tranq10_04`, the solver can have an exhausted sortie profile catalog but too
  little remaining time to filter the catalog and run the final profile DP.

20-task status remains substantially harder.  Existing `tasks20_02` trials with
the current physical/journey branch configurations remain `TIME_LIMIT` at about
200s, with no certificate dual.  The best incumbent in those trials is around
`486.081224`, so the 20-task target will require a stronger pricing/column
generation change rather than further small tail toggles.

## Streaming Online-Dominance Filter Skip (2026-06-04)

The streaming profile-pricing callback was still applying the full offline
cross-dominance filter to every streamed profile batch even when profile
generation had already applied online skyline dominance:

```text
journey_pricing_profile_online_dominance_enabled = True
journey_pricing_profile_cross_dominance_enabled  = True
```

For the label physical catalog path, the streamed profile list is already the
per-mask skyline.  Re-running `_filter_dominated_sortie_profiles` on the same
skyline does not change the candidate set, but it costs around `0.5-0.8s` per
late pricing call on 10-task Tranquillitatis hard-tail instances.

Implemented exact-safe change:

```text
if catalog_stats["online_dominance_applied"]:
  reuse streamed profiles directly
else:
  run the existing offline dominance filter
```

This preserves exactness because the online skyline uses the same dominance
predicate as the offline filter.  In a fixed task mask, subtracting task-cover
duals shifts every profile by the same dual sum, so the dominance relation does
not depend on the current dual vector.

Unit coverage:

```text
test_sortie_profile_filter_skips_batch_when_online_dominance_applied
test_label_physical_catalog_marks_online_dominance_applied
test_label_online_profile_dominance_matches_batch_filter
test_sortie_profile_online_skyline_matches_filter
```

Validation:

```text
python -m unittest BPC_future.tests.test_bpc_future \
  BPCFutureTests.test_sortie_profile_filter_skips_batch_when_online_dominance_applied \
  BPCFutureTests.test_label_physical_catalog_marks_online_dominance_applied \
  BPCFutureTests.test_label_online_profile_dominance_matches_batch_filter \
  BPCFutureTests.test_sortie_profile_online_skyline_matches_filter
python -m unittest BPC_future.tests.test_bpc_future -k direct_ng
python -m unittest BPC_future.tests.test_bpc_future -k compatible_profile_cache
python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/tests/test_bpc_future.py
git diff --check
```

Representative probes:

```text
BPC_future/results/probe_t05_online_filter_skip_20260604.csv
  tranq05_03: OPTIMAL, time = 0.616741s

BPC_future/results/probe_a10_01_online_filter_skip_20260604.csv
  apollo10_01: OPTIMAL, time = 1.718229s

BPC_future/results/probe_t09_online_filter_skip_20260604.csv
  tranq10_09: OPTIMAL, time = 51.477815s
  previous comparable single run: 59.775550s
  total profile_filter_time: about 5.066s -> about 0.000018s

BPC_future/results/probe_t04_online_filter_skip_20260604.csv
  tranq10_04: OPTIMAL, time = 57.105744s

BPC_future/results/probe_a10_04_online_filter_skip_20260604.csv
  apollo10_04: TIME_LIMIT, primal = 288.332462, dual = 268.585633
```

Full 10-task rerun:

```text
BPC_future/results/all_tasks10_online_filter_skip_20260604.csv
  18 / 20 OPTIMAL
  mean time  = 24.643803s
  total time = 492.876069s
  max time   = 60.157575s

remaining failures:
  apollo10_04:
    TIME_LIMIT, primal = 288.332462, dual = 268.585633, gap = 0.068486
  tranq10_04:
    TIME_LIMIT in full batch, primal = 207.893439, no certificate dual
    single-instance probe closes at 57.105744s
```

The full rerun improves over the previous current rerun:

```text
BPC_future/results/all_tasks10_current_docsread_20260604_final.csv
  17 / 20 OPTIMAL
  mean time  = 25.433208s
  total time = 508.664159s
```

`tranq10_09` is now comfortably below 60 seconds in both single and full runs.
`tranq10_04` remains a timing-borderline instance: after the filter skip it can
close as a single run, but in the full batch it still sometimes finds one late
negative column and leaves less than one second for the final no-negative
certificate.  `apollo10_04` is a different bottleneck: branch-tree search and a
remaining dual gap, not root profile filtering.

## Bound-Fathom Pool Integer Skip (2026-06-04)

In branch nodes, `_process_journey_branch_node` previously ran a node-local
integer journey-pool MIP after true-dual exact pricing had already exhausted,
even when the certified node LP objective was no better than the incumbent.
The outer branch driver would then immediately fathom the node by bound.

Implemented exact-safe skip:

```text
if exact pricing exhausted and LP bound >= incumbent - integer_tol:
  log journey_pool_integer_skip
  return COMPLETE with the certified LP bound
  let the outer branch driver fathom by bound
```

This cannot miss a better incumbent because every integer solution in that node
has objective at least the certified LP bound, and that bound is already no
smaller than the incumbent.

Unit coverage:

```text
test_journey_branch_node_skips_pool_integer_when_bound_fathoms
```

Validation:

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.\
  test_journey_branch_node_skips_pool_integer_when_bound_fathoms
python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.\
  test_journey_branch_node_reuses_pricing_trip_cache_across_cg_rounds \
  BPCFutureTests.test_journey_branch_node_trip_cache_override_is_branch_only
```

`apollo10_04` single-instance probe:

```text
BPC_future/results/probe_apollo10_04_skip_pool_bound_20260604.csv
  TIME_LIMIT, time = 60.080067s
  primal = 288.332462
  dual   = 268.585633
  gap    = 0.068486
  nodes  = 15
  columns = 241

log evidence:
  journey_pool_integer_skip events = 7
  journey_pool_integer events      = 7
```

The skip removed several redundant pool MIP calls, but those calls were not the
dominant cost on this instance.  A 90-second diagnostic still closes the same
instance:

```text
BPC_future/results/probe_apollo10_04_90s_20260604.csv
  OPTIMAL, time = 65.740480s
  nodes = 17
  columns = 242
```

Additional negative probes on `apollo10_04`:

```text
journey_child_priority_mode = lp_rounding:
  TIME_LIMIT, time = 60.070542s

journey_pricing_dp_same_completion_pruning_enabled = True:
  TIME_LIMIT, time = 60.078141s
  same-completion pruning triggered heavily
  total dp_same_completion_pruned_labels = 92815

lp_rounding + same-completion pruning:
  TIME_LIMIT, time = 60.098102s

journey_pool_integer_heuristic_enabled = False:
  TIME_LIMIT, time = 60.074913s
```

Representative regression after the skip:

```text
BPC_future/results/all_tasks05_after_pool_skip_20260604.csv
  20 / 20 OPTIMAL
  max time = 1.036385s

BPC_future/results/probe_10_representative_after_pool_skip_20260604.csv
  apollo10_01: OPTIMAL, time = 1.730391s
  apollo10_04: TIME_LIMIT, primal = 288.332462, dual = 268.585633
  tranq10_04:  TIME_LIMIT, primal = 207.893439, no certificate dual
  tranq10_09:  OPTIMAL, time = 53.481913s
```

Conclusion:

- Keep the skip as a small exact-safe cleanup.
- It does not solve the remaining 10-task target by itself.
- `apollo10_04` needs branch-node pricing/tree improvement.  The 90-second
  close shows the gap is about 5-6 seconds, not a fundamental objective gap.
- `tranq10_04` remains a separate root-tail timing-borderline case.

## Apollo 10-04 Branch Tail Diagnostics (2026-06-04)

After rereading the learning and exact-pricing design notes, all 5-task and
10-task instances were rerun with the current default path:

```text
BPC_future/results/all_tasks05_reread_docs_20260604.csv
  20 / 20 OPTIMAL
  mean time = 0.323019s
  max time  = 1.059167s

BPC_future/results/all_tasks10_reread_docs_20260604.csv
  19 / 20 OPTIMAL
  mean time = 24.664350s
  max time  = 60.050616s

remaining failure:
  apollo15_20km_tasks10_04_seed11055
    TIME_LIMIT, primal = 288.332462
    dual = 268.585633, gap = 0.068486
```

Current-code single-instance diagnostic:

```text
BPC_future/results/probe_apollo10_04_current70_20260604.csv
  OPTIMAL, time = 65.964770s
  nodes = 17
  columns = 242
```

The remaining 60-second miss is concentrated in the late branch certificate
tail.  In the 70-second run, the final expensive no-negative pricing calls were:

```text
node11: profile_generation_time ~= 3.52s
node12: profile_generation_time ~= 1.74s + 0.51s
node15: profile_generation_time ~= 2.33s
node16: profile_generation_time ~= 2.04s
```

Negative probes:

```text
BPC_future/results/probe_apollo10_04_child_incumbent_relation_20260604.csv
  TIME_LIMIT, time = 60.079820s

BPC_future/results/probe_apollo10_04_cert_fullscan1_20260604.csv
  TIME_LIMIT, time = 60.081645s

BPC_future/results/probe_apollo10_04_no_dual_stab_20260604.csv
  TIME_LIMIT, time = 60.081955s
```

These confirm that child ordering by incumbent relation, early certificate
full-scan, and disabling dual stabilization do not address this bottleneck.

An opt-in cross-node branch pricing cache was added for future experiments:

```text
journey_branch_pricing_cross_node_cache_enabled = False by default
journey_branch_pricing_cross_node_cache_max_entries = 20000
```

It is exact-safe because it only reuses pricing cache objects through the same
`price_journeys` API.  It remains disabled by default because the Apollo probe
did not improve:

```text
BPC_future/results/probe_apollo10_04_cross_node_cache_20260604.csv
  TIME_LIMIT, time = 60.059610s
```

RF same/separate transitive-closure pruning was also tested.  It is
mathematically safe and reduced local profile generation on `node11` from about
`3.52s` to about `1.09s`, but it changed the column/tree trajectory and worsened
the complete 70-second diagnostic:

```text
BPC_future/results/probe_apollo10_04_rf_closure_20260604.csv
  TIME_LIMIT, time = 60.049441s

BPC_future/results/probe_apollo10_04_rf_closure70_20260604.csv
  OPTIMAL, time = 68.320067s
```

Therefore RF closure pruning was not adopted as a default path.  The next
`apollo10_04` work should focus on reducing branch-node no-negative profile
generation without perturbing the column trajectory as strongly, or on a
production NG-route/DSSR certificate that can prove these late branch nodes
faster.

## Physical Catalog Key Probe (2026-06-04)

After the `apollo10_04` branch-tail diagnostic, two physical-catalog cache
experiments were tested.

1. Branchless physical catalog sharing was implemented as an opt-in diagnostic:

```text
journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled = False
```

The implementation shares only physical sortie profiles.  Current pricing still
recomputes reduced costs from the active true duals and applies branch filtering
before profile-DP selection.  It is therefore exact-safe, but it is not a
default speed improvement.

Probe result:

```text
BPC_future/results/probe_apollo10_04_shared_physical_catalog2_20260604.csv
  TIME_LIMIT, time = 60.074454s
  primal = 288.332462, dual = 268.585633
```

The shared branchless catalog lost useful `separate_vehicle` mask pruning and
did not close the hard branch-tail instance.  Keep it off by default.

2. A temporary task-order-key experiment closed `apollo10_04`:

```text
BPC_future/results/probe_apollo10_04_ignore_task_order_catalog_20260604.csv
  OPTIMAL, time = 53.242785s
  nodes = 5, columns = 233
```

However, this was caused by accidentally changing the historical root physical
catalog key semantics.  The old key is intentionally independent of
`task_order`; adding `task_order` to the key damaged root-tail behavior on
Tranquillitatis boundary instances.  The task-order-key change was reverted.

Restored-key validation:

```text
BPC_future/results/probe_tranq10_09_default_key_restored_20260604.csv
  OPTIMAL, time = 51.343195s

BPC_future/results/all_tasks05_after_catalog_key_restore_20260604.csv
  20 / 20 OPTIMAL
  mean time = 0.292046s
  max time  = 1.329532s
```

Conclusion: preserve the task-order-independent physical catalog key.  The
remaining useful path is still branch-tail profile generation reduction or an
NG-route/DSSR certificate, not branchless physical catalog sharing.

Additional diagnostic:

```text
BPC_future/results/probe_apollo10_04_no_physical_catalog_resume_20260604.csv
  TIME_LIMIT, time = 60.066382s
  nodes = 3, columns = 233
```

Disabling physical-catalog resume changes the tree but still does not produce a
60-second certificate.  Do not use this as a default either.
