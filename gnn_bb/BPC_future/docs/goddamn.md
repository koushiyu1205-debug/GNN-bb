# BPC Future 20-Scale Root-Tail Audit

## 2026-06-08 20:33:30 +0800

### Scope

This note records the current and previous conversation findings about the
`BPC_future/` exact journey BPC line, especially why 20-task instances stall in
root-tail final proof. It is an audit log, not an implementation change.

### Current Exactness Boundary

- Official optimality/no-column certificate must come from the true-dual
  direct-label final judge path.
- Heuristic/profile/streaming workers may find negative columns, but their
  no-column result is not an official certificate.
- GNN/learning is only an early/mid pricing anchor or ordering aid. It must not
  enter official bounds or certificates.
- 5-task and 10-task current model/config should remain frozen while diagnosing
  20-task behavior.

### Previous Conversation Results

- The `tasks_10` root-tail zero-reference gate was useful as a root-tail
  break-glass tool, but it must remain gated and root-tail-specific because
  zero-reference inside branch-heavy subtrees can distort branch-local dual
  meaning and weaken Apollo-like speed on normal nodes.
- 5-scale and 10-scale behavior was treated as the current best line and should
  not be broken by 20-scale experiments.
- A prior `tranq10_09` hard case reached exactness around `189s` with safe
  settings. The bottleneck there was not many completion-bound retries anymore;
  it was two expensive true-dual final judge calls.
- A real exactness bug was already fixed before this note: when
  `unique_task_bound=None` and `unique_route_bound!=None`, partial/suffix bound
  previously passed an invalid zero available mask to unique-route. That could
  create a false certificate. The fix and regression test were added earlier.
- Direct-label profiling and exact-safe caches were added earlier:
  unique-task caches, unique-route exact-first-step cache, positive-cut fast
  return, active-label stale checks, and profile timing fields.

### 20-Task Probe Results

Single-instance probe:

```text
instance:
BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_20/tranquillitatis_balmer_like_20km_tasks20_01_seed21000_logical_graph.json
```

Default 900-second outer limit:

```text
status=TIME_LIMIT
time=761.986322s
nodes=1
rmp_solves=68
pricing_calls=96
exact_pricing_calls=28
columns=712
primal=382.038993
dual=None
reason at root tail=direct_label_sequence_budget
```

High-budget diagnostic run, intentionally stopped after the 6M base final
judge returned and entered 12M escalation:

```text
base final judge max_sequences=6000000
result=INCOMPLETE
reason=direct_label_sequence_budget
negative_journeys=0
profile_generation_time=543.461739s
generated_sequences=6000001
expanded_labels_before_bound=13595746
expanded_labels_after_bound=12960762
dp_bound_pruned_labels=634984
next_sortie_total_time=511.982933624s
dominance_time=209.251144453s
completion_time=77.070119188s
bound_check_time=73.315950113s
```

Interpretation:

- Raising the outer time limit alone is not enough. The run can terminate early
  because the final judge internal sequence budget is exhausted.
- Raising the base final judge budget from 1.5M to 6M still did not prove
  no-negative and did not find a hidden negative column.
- The 12M escalation was terminated manually to avoid spending more time and
  memory on an already diagnostic run.
- The main runtime inside final judge is `next_sortie` expansion, with
  dominance also expensive. This is not primarily RMP time or branch-tree time.

### Pathological Instance Checks

The suspected explicit pathologies were checked on `tranq20_01`.

Not an infinite single-sortie capacity case:

```text
Q=6.0
task demand d=1.0 for every task
max_tasks_per_trip=6
task_count=20
```

Not a full-day all-task waiting model:

```text
H=720 minutes
r min/max = 0.0 / 210.0
D min/max = 480.0 / 690.0
task_waiting_allowed=False
depot_waiting_allowed=True
```

No negative waiting reward or negative path cost:

```text
arc option cost min=2.355906, max=18.788233
arc option tau min=39.018011, max=266.242794
arc option energy min=4.112399, max=28.398902
all checked arc option costs/times/energies are nonnegative
```

However, the instance is still proof-hard:

- `max_tasks_per_trip=6` gives `P(20, 6)=27,907,200` possible ordered 6-task
  sequences before path-option choices.
- The logical graph has up to 3 physical path options per directed pair.
  Length-4 ordered task sequences already expand from `116,280` task orders to
  about `28,107,324` order-option combinations.
- The current incumbent contains three 6-task long sorties plus two singleton
  sorties, so long columns are not just theoretical noise.

### Comparison With Other Code In This Repository

Other related implementations:

- `bpc/`: clean route-vehicle BPC on older JSON benchmark instances.
- `branchpricecut/`: earlier vehicle-schedule BPC line.
- `BPC_future/`: current logical/physical Moon Trek journey-column exact BPC.

Important differences:

- Older clean BPC generally uses a single cheapest closure path per task pair.
  `BPC_future` prices over multiple physical path options per directed logical
  edge.
- Older benchmark 20 instances have `H=240`, smaller service times, and a
  different data distribution. `BPC_future` Moon Trek has `H=720`, service times
  around 18-26 minutes, survival energy, recharge, and physical path-option
  choices.
- `bpc/configs` explicitly keeps pricing completion bound out of the default
  paper-grade mainline. `BPC_future` currently relies on a completion-bound
  direct-label final judge for official proof.
- Older 20-scale code is not uniformly easy either: recorded
  `branchpricecut` paper baseline results include `bench_20_01` exact around
  `3535.978769s`, and other 20 cases timed out at 3600s in that record. The
  apparent difference is where the pain appears: older code spreads cost across
  branch tree and full route pricing; `BPC_future` exposes it as a root-tail
  direct-label final proof bottleneck.

### Dominance Rule Assessment

Current evidence does not support "infinite label-loop proliferation" as the
primary failure mode.

Why it does not look like an infinite loop:

- In `_direct_next_sortie_trips`, every partial sortie extension adds a new
  unvisited task bit to `label.mask`.
- The same task cannot be revisited inside the partial label because expansion
  skips tasks already in `used_mask` or `label.mask`.
- A partial sortie is capped by `max_tasks_per_trip=6`.
- Journey labels are capped by the finite global task mask and sortie count.
- Probe logs hit exact sequence budgets:

```text
1.5M run: generated_sequences=1500001
3M escalation: generated_sequences=3000001
6M diagnostic: generated_sequences=6000001
```

This is bounded enumeration up to the configured budget, not a cycle.

The dominance rules appear conservative, not obviously unsound:

- `_add_sortie_partial_label` buckets labels by `(local_mask, last)` and prunes
  only when the old label has no worse feasible start interval, offset, travel
  cost, travel energy, service cost, and service energy.
- `_add_direct_journey_label_with_cross_count_dominance` only compares same
  task mask labels across sortie counts, and a fewer-sortie label dominates only
  when end time and reduced-cost value are no worse.
- The stale heap protection uses active label IDs, so removed partial labels
  should not keep expanding from the heap.

But the dominance is probably too weak or too costly for 20-scale final proof:

- In the 6M final judge, `direct_label_profile_dominance_checks=5,365,016`.
- `direct_label_profile_dominance_time=209.251144453s`.
- `direct_label_cross_count_pruned_labels=0` at the CG68 proof point.
- Most of the work is still `next_sortie` expansion, so even perfect same-mask
  dominance would not eliminate the path-option/order explosion by itself.

Working hypothesis:

```text
The root-tail failure is finite but huge exact enumeration caused by:
  task-order permutations
  x physical path-option products
  x wide-enough no-wait start intervals
  x conservative exact-safe dominance
  x official proof requiring true-dual final judge exhaustion.
```

This is different from "dominance bug causes infinite cycling".

### Next No-Code Diagnostics

Before changing code, run only lightweight diagnostics:

1. For all `tasks_20` instances, compute:
   - task window widths,
   - count of feasible default-option sequences by length 1-4,
   - path-option product by length,
   - max and average path-option count per arc.
2. For one hard instance, log final judge per-depth counts:
   - partial labels popped by sequence length,
   - labels retained per `(mask,last)` bucket,
   - dominance bucket max/mean length,
   - completed sortie segments generated per parent journey label.
3. Confirm whether dominance is weak because labels differ mainly by:
   - path option choices,
   - start interval lower/upper bounds,
   - energy,
   - cost,
   - or last node.
4. Only after that decide whether to implement an exact-safe stronger
   dominance or a proof-safe path-option lower-envelope compression.

## 2026-06-09 03:08:00 CST - 5/10 Harvesting A/B and Tail Probes

### Full 5/10 A/B, 600s Limit

Ran the requested baseline/probe matrix:

- 5-task baseline: 20/20 OPTIMAL, avg 0.906s.
- 5-task final-judge harvesting probe: 20/20 OPTIMAL, avg 0.904s.
- 10-task baseline: 20/20 OPTIMAL, avg 86.985s, max 290.393s.
- 10-task final-judge harvesting probe: 20/20 OPTIMAL, avg 74.768s, max 211.634s.

The 5-task runs are effectively unchanged because the final-judge harvesting
path is not active in meaningful volume at that scale.

The 10-task probe improves aggregate time, mainly on a few Tranquillitatis hard
cases:

- tranq10_01: 290.393s -> 172.735s.
- tranq10_04: 241.548s -> 144.308s.
- tranq10_05: 57.085s -> 45.560s.
- tranq10_07: 151.298s -> 136.001s.

But the mechanism quality is not clean:

- selected_new_mask_count: baseline 1, probe 1.
- selected_support_changing_count: baseline 1, probe 1.
- active_changed_task_set_count: both 0.
- final_judge_replacement_journeys: baseline 47, probe 42.
- root_tail_rmp_rounds: baseline 74, probe 79.

This means the runtime improvement is real in this run, but it is not yet caused
by the intended support-changing/new-mask mechanism. It mostly changes the
replacement-tail trajectory. It should remain opt-in, not default.

### Extra Tail Probe Results

Tested two additional opt-in directions on the hard Tranquillitatis subset
01/04/09/10:

1. Final-judge replacement repair:
   - Strict run avg 206.450s.
   - Mostly adds overhead; usually finds no useful extra negative column.
   - tranq10_09 worsened from baseline 195.367s to 253.793s.
   - Do not promote this direction.

2. Final-judge same-dual supplement:
   - Basic run improved 01/04, but worsened 09 badly.
   - Candidate-window gate run:
     - tranq10_01: 152.195s.
     - tranq10_04: 116.855s.
     - tranq10_09: 309.494s.
     - tranq10_10: 69.740s.
   - It can break some replacement tails, but the current gate still causes
     extra final-judge cycles on tranq10_09:
     - baseline 09 retry sequence: INCOMPLETE, OPTIMAL-with-9-replacements,
       final OPTIMAL no-negative.
     - candidate-gate 09 retry sequence: INCOMPLETE, INCOMPLETE with one new
       mask, then three more OPTIMAL replacement batches before final proof.

### Current Interpretation

Harvesting did not make the single final judge search cheaper. It only changes
which negative columns return after an expensive judge call. When those columns
are mostly replacement-only, the RMP can move along the same degenerate face and
trigger more exact retries.

The promising signal is that same-dual supplement can greatly help 01/04, but
the gate must learn to avoid 09-style cases where it creates extra replacement
rounds. The next exact-safe direction should be a stronger, logged trigger based
on final-judge retry sequence state and active support change, not simply
candidate count.

## 2026-06-09 03:47:22 CST - Direction Reset After NG And Cache Probes

### User Requirement Restated

The actual target is not another local tail tweak:

- 10-task full 20 instances: all OPTIMAL, average time < 50s.
- 20-task full 20 instances: average time < 200s, at least 18/20 OPTIMAL within
  600s, with diagnostic runs allowed up to 1200s.
- Exactness remains mandatory: no worker-local no-column result may become an
  official certificate.

### Implemented This Round

1. Added a final-judge-only NG/DSSR relaxed preprobe path.
   - New internal config boundary:
     `direct_journey_label_ng_completion_bound_preprobe_enabled`.
   - New top-level certificate switch:
     `journey_certificate_completion_bound_ng_preprobe_enabled`.
   - The preprobe is allowed only when completion-bound final judge is active.
   - If relaxed NG proves no negative, it can return a true-dual certificate.
   - If it only finds materialized elementary negative journeys, they remain
     negative-column evidence, not no-column proof.
   - If it cannot prove or return enough columns, control falls back to the
     existing elementary completion-bound final judge.

2. Fixed a pricing state semantic bug:
   - `_merge_ng_probe_pricing_result(...)` can merge true-RC negative journeys
     from NG probe into a fallback result.
   - The merged result previously inherited fallback `pricing_state`, which
     could remain `LOCAL_NO_COLUMN_UNCERTIFIED`.
   - It now explicitly sets `pricing_state=FOUND_NEGATIVE` when selected
     negative journeys are returned.

3. Added tests:
   - Completion-bound final judge uses NG certificate preprobe only when
     explicitly enabled.
   - Ordinary NG/DSSR no-negative fallback behavior is preserved.
   - Certificate config mapping for the new preprobe switch is opt-in.

### Probe Results

`tranq10_09` with final-judge-only NG preprobe:

```text
baseline previous run:          195.367s
NG completion-bound preprobe:   194.103s
status:                         OPTIMAL
```

Final retry sequence:

- Retry 1: NG quickly found relaxed/elementary negative signal, completion-bound
  still returned replacement-heavy negative batch.
- Retry 2: same pattern.
- Final proof: NG relaxation still had a very negative relaxed value
  (`ng_best_relaxed_reduced_cost=-100.0`), so it could not certify no negative.
  The elementary completion-bound judge still had to prove the node.

Conclusion: NG relaxed preprobe is exact-safe and may help cases where the
relaxation itself certifies, but it does not solve the current `tranq10_09`
root-tail proof bottleneck.

### Rejected Direction

Tried an opt-in cached-next-sortie idea: allow completion-bound final judge to
cache the full next-sortie universe by used task mask, skipping parent-specific
partial pruning.

This was rejected and removed from code.

Evidence:

- On `tranq10_09`, the first cached final judge did not return an event after
  more than six minutes.
- Process memory reached 94.3%.
- This means complete next-sortie caching explodes memory and is not a viable
  20-scale direction.

### Current Best Direction

Stop optimizing final judge return policy and stop caching full sortie
universes.

The next direction should be a proof-safe, memory-bounded reduction inside
`_direct_next_sortie_trips(...)`, specifically:

1. Add detailed retained-label diagnostics per `(local_mask,last)` bucket:
   - number of labels per bucket,
   - max/mean bucket size,
   - which dimensions prevent dominance: time interval, offset, travel cost,
     travel energy, service cost, service energy.
2. Use that evidence to strengthen exact-safe partial dominance, not by capping
   labels, but by proving additional dominance implications for no-wait partial
   profiles.
3. Target the expensive part directly:
   - reduce retained partial labels,
   - reduce dominance comparisons,
   - reduce completed sortie materializations,
   - without weakening official `CERTIFIED_NO_NEGATIVE`.

The next code change should therefore be diagnostic instrumentation plus one
small dominance improvement driven by those diagnostics, not more final-judge
harvest or retry-trigger tuning.

## 2026-06-09 04:07:44 CST - 5/10 A/B Interpretation And Unique-Route Diagnostics

### Requested 5/10 Hard-Case Benchmark Interpretation

The full 5-task and 10-task A/B matrix with a 600-second limit was completed
before this note.

Results:

- 5-task baseline: 20/20 OPTIMAL, average 0.906s.
- 5-task final-judge harvesting probe: 20/20 OPTIMAL, average 0.904s.
- 10-task baseline: 20/20 OPTIMAL, average 86.985s, max 290.393s.
- 10-task final-judge harvesting probe: 20/20 OPTIMAL, average 74.768s,
  max 211.634s.

The harvesting probe is therefore faster on 10-task aggregate, but it is not a
clean default candidate:

- selected_new_mask_count stayed at 1.
- selected_support_changing_count stayed at 1.
- active_changed_task_set_count stayed at 0.
- root_tail_rmp_rounds increased from 74 to 79.

Interpretation: the improvement is mostly a replacement-tail trajectory effect,
not the intended support-changing/new-mask mechanism.  It can remain an
opt-in probe, but should not be promoted to default on this evidence.

### Rejected Or Non-Default Directions

Final-judge-only NG/DSSR relaxed preprobe was implemented as an exact-safe,
opt-in certificate preprobe.  On `tranq10_09` it produced essentially no
improvement:

```text
baseline/profile range:   about 191-195s
NG preprobe run:          194.103s
status:                   OPTIMAL
```

The NG relaxation remained negative at the final proof point, so it could not
certify no negative.  The elementary completion-bound final judge still had to
run.

Full next-sortie caching by used-mask was tested and rejected.  It did not
return from the first cached final judge after more than six minutes and pushed
memory to about 94%.  The idea was removed from code.

Generalized partial dominance was tested on `tranq10_09` and was essentially
neutral:

```text
default/profile run:                  about 191.354s
generalized partial dominance probe:  about 191.352s
```

It did not reduce final judge generated sequences or dominance cost in a useful
way.

### Current Code Changes From This Round

Added exact-safe diagnostics and a small internal micro-optimization:

- `_UniqueRouteCompletionLowerBound` now precomputes `(task, bit)` pairs to
  avoid repeated task-bit dictionary lookup and shifting inside tight DP loops.
- When direct-label profile timing is enabled, unique-route exact-first-step
  records coarse resource-bucket reuse diagnostics:
  - `direct_label_unique_route_exact_first_step_resource_bucket_count`
  - `direct_label_unique_route_exact_first_step_resource_bucket_revisits`
- The diagnostics are propagated into journey pricing logs.

This does not change pricing status, `exhausted`, RMP, cuts, branching, or the
official certificate path.

Unit verification:

```text
unique-route exact-first-step tests: 4/4 OK
compileall on touched files: OK
```

### `tranq10_09` Diagnostic Probe After The Change

Command profile result:

```text
status=OPTIMAL
primal=203.102839
dual=203.102839
time=192.215782s
nodes=1
cols=492
```

The final judge retry sequence remained the same kind of trajectory:

```text
cg_iter 12: FOUND_NEGATIVE, 10 negative journeys, generated 55,279
cg_iter 20: FOUND_NEGATIVE,  9 negative journeys, generated 2,625,442
cg_iter 21: CERTIFIED_NO_NEGATIVE, generated 2,584,071
```

Key final proof diagnostics:

```text
next_sortie_total_time:        54.278000670s
bound_check_time:              17.841707436s
unique_route_time:              9.800999591s
dominance_time:                 8.582775050s
completion_time:                8.401243235s
extend_time:                    9.763858835s
partial_bucket_count:          17,948
partial_bucket_label_count:   304,811
partial_bucket_max_size:          845
```

Unique-route exact-first-step cache diagnostics:

```text
raw exact-first-step cache hits:      19
raw exact-first-step cache misses:    755,986
raw exact-first-step cache size:      100,000
resource bucket key count:            11,652
resource bucket revisits:             744,334
```

Interpretation:

- The existing raw-float exact-first-step cache is almost useless.
- Coarse resource buckets have very high reuse potential:
  `744,334 / 755,986` exact-first-step misses revisit a previously seen
  resource bucket.
- A future bucket-level reuse optimization could be high leverage, but it must
  be proven as a valid optimistic lower bound before use in pruning.

### Next Exact-Safe Direction

Do not promote harvesting default yet.

The next code direction should be a proof-safe unique-route exact-first-step
reuse rule:

1. Define a bucket-level value that is guaranteed no larger than the true exact
   first-step lower bound for every precise state inside that bucket.
2. Use it only as an optimistic lower bound and keep the existing
   `max(bucketed, exact_first)` safety relationship.
3. Add tests showing the bucket-reused value never prunes a journey that the
   precise exact-first-step path would keep.

If that proof cannot be made cleanly, prefer a pure compute optimization inside
`_partial_value_exact_first_step(...)` over any cache reuse that changes bound
tightness.

## 2026-06-09 05:23:23 CST - Corrected Direction: Pre-Dominance Before Bound Check

### What Was Rejected

Tried to reuse unique-route exact-first-step results by one-sided resource
dominance.

Result on `tranq10_09`:

```text
status=OPTIMAL
time=230.959231s
```

Although this reduced per-call unique-route time, it weakened the effective
bound because finite cached lower bounds were less tight than the precise
exact-first-step value.  The final judge needed more negative/proof rounds, so
overall runtime worsened.  This direction was removed from the default path.

The lesson is important: exact-safe is not enough.  A weaker safe lower bound
can still destroy tail performance by increasing final judge retries.

### Implemented Direction

Implemented pre-dominance in `_direct_next_sortie_trips(...)`:

- Before running expensive completion/unique-route bound checks, check whether
  the new partial sortie label is already dominated by an existing label in the
  same `(local_mask, last)` bucket.
- The precheck uses exactly the same `_dominates_sortie_partial_label(...)`
  predicate that `_add_sortie_partial_label(...)` already used later.
- If the candidate is dominated, it would have been discarded anyway, so
  skipping bound/completion work is exact-safe.
- `_add_sortie_partial_label(...)` now accepts `candidate_not_dominated=True`
  to avoid repeating the first dominance loop after a successful precheck.
- The default non-generalized, non-coarsened dominance predicate now has a fast
  early-return path.  This keeps the same inequalities but avoids building the
  full no-worse/strict expression for every comparison.
- Empty dominance buckets skip precheck entirely.

This does not change RMP, branching, cuts, official lower bound semantics, or
the `CERTIFIED_NO_NEGATIVE` certificate path.

### Validation

Unit and compile checks:

```text
direct_journey_label tests: OK
dominance tests: OK
unique-route exact-first-step tests: OK
compileall touched files: OK
```

`tranq10_09` profile comparison:

```text
before pre-dominance/profile: 192.215782s
pre-dominance/profile:        183.871050s
fast-path profile:            169.184704s
fast-path no-profile:         164.176175s
```

Final proof profile before:

```text
generated_sequences:        2,584,071
bound_checks:               2,584,071
next_sortie_total_time:        54.278s
bound_check_time:              17.842s
unique_route_time:              9.801s
dominance_time:                 8.583s
```

Final proof profile after fast path:

```text
generated_sequences:        2,584,071
bound_checks:               2,266,216
pre_dominance_checks:         763,021
pre_dominance_pruned:         317,855
next_sortie_total_time:        46.009s
bound_check_time:              13.031s
unique_route_time:              7.107s
pre_dominance_time:             3.579s
dominance_time:                 2.379s
```

This is the first useful direction in this round because it reduces internal
final judge work without weakening the lower bound.

### Batch Runner Fix

A hard-case batch run showed `tranq10_09` could become much slower when run
after several previous instances in the same Python process:

```text
single no-profile 09: 164.176175s
hard6 batch 09 before runner cache isolation: 268.556788s
```

The run script now clears the global trip sequence resource-precheck cache
before and after each instance.  A two-instance batch `tranq10_01 -> tranq10_09`
then gave:

```text
tranq10_01: 211.833948s
tranq10_09: 164.868664s
```

So at least part of the batch instability was process/cache isolation, not the
pricing algorithm itself.

### Remaining Gap

The current change is not enough for the final target.

Hard-case signals:

```text
tranq10_01 old baseline: 290.393s
tranq10_01 current pair batch: 211.834s
tranq10_01 current profile single: 147.464s
tranq10_04 old baseline: 241.548s
tranq10_04 current hard batch: 138.571s
apollo10_04 old baseline: 215.055s
apollo10_04 current hard batch: 177.674s
```

The right next drill-down is not harvesting and not finite lower-bound cache.
It is:

1. Make final judge/RMP tail trajectory deterministic enough that 01 does not
   swing between ~147s and ~212s across runs.
2. Continue reducing `_direct_next_sortie_trips(...)` internal work:
   especially bound-check and dominance work on candidates that will never
   enter the retained partial-label frontier.
3. Re-run 10-task full 20 only after the hard six are stable, because current
   hard-case times still imply the 10-task average will remain above 50s.

## 2026-06-09 05:43:57 CST - 5/10 Full 600s Harvest A/B Conclusion

The requested 600s A/B over all 5-task and 10-task instances completed.

5-task:

```text
baseline: 20/20 OPTIMAL, avg 0.906482s, max 1.916284s
harvest:  20/20 OPTIMAL, avg 0.904496s, max 1.919776s
delta:    -0.001986s avg
```

All structural counters were unchanged: columns, RMP solves, pricing calls, and
exact pricing calls matched instance-by-instance.  The harvest summary showed no
final-judge harvested journeys.  Therefore the 5-task result is effectively
unchanged; the millisecond-level delta is runtime noise.

10-task:

```text
baseline: 20/20 OPTIMAL, avg 86.984917s, max 290.393109s
harvest:  20/20 OPTIMAL, avg 74.768479s, max 211.633891s
delta:    -12.216439s avg
```

The improvement is real at the aggregate level but not yet a clean
support-aware-harvesting win.  Key diagnostics:

```text
exact_completion_bound_retry_calls: 83 -> 80
selected_new_mask_count:            1  -> 1
selected_support_changing_count:    1  -> 1
selected_weak_replacement_count:    2  -> 4
fallback_fill_count:                9  -> 11
root_tail_rmp_rounds:               74 -> 79
final_judge_added_journeys:         48 -> 43
final_judge_replacement_journeys:   47 -> 42
```

This means the probe did not improve through the intended signal
`new/support-changing columns up, replacement-only ratio down`.  Instead, it
mostly perturbed tail trajectories.  The large wins came from fewer final judge
retry rounds in a few hard cases:

```text
tranq10_01: 290.393109s -> 172.735320s, retry calls 4 -> 2
tranq10_04: 241.547805s -> 144.307932s, retry calls 3 -> 1
tranq10_05:  57.084811s ->  45.560367s
tranq10_07: 151.297751s -> 136.001140s
```

One case regressed:

```text
tranq10_10: 72.610879s -> 85.505068s, retry calls 3 -> 4
```

The alias override changed final judge return parameters:

```text
max_returned_journeys:        20 -> 128
hidden_negative_max_returned: 20 -> 128
min_new_task_sets:             0 -> 16
```

However, the actual selected new/support-changing counts stayed flat.  Therefore
this should not be promoted as default.  It is exact-safe, but the measured gain
is trajectory-sensitive rather than a robust mechanism.

## 2026-06-09 07:08:32 CST - Redone 5/10 Full 600s Harvest A/B

The full A/B was rerun with a 600s per-instance limit.

Result files:

```text
BPC_future/results/20260609_600s_full_ab_rerun_tasks5_baseline.csv
BPC_future/results/20260609_600s_full_ab_rerun_tasks5_harvest_probe.csv
BPC_future/results/20260609_600s_full_ab_rerun_tasks10_baseline.csv
BPC_future/results/20260609_600s_full_ab_rerun_tasks10_harvest_probe.csv
```

5-task remained frozen:

```text
baseline: 20/20 OPTIMAL, avg 0.901056s, max 1.945643s
harvest:  20/20 OPTIMAL, avg 0.887890s, max 1.864491s
```

The harvest summaries had zero selected final-judge harvested journeys in both
groups.  The small difference is runtime noise.

10-task aggregate:

```text
baseline: 20/20 OPTIMAL, avg 71.100315s, median 45.747993s, max 269.002160s
harvest:  20/20 OPTIMAL, avg 70.538481s, median 51.003760s, max 234.653753s
delta:    -0.561834s avg, +5.255767s median
```

This is not a robust improvement.  The average is slightly better only because
`tranq10_09` improved by about 103s, while `tranq10_01` regressed by about 94s.

Key per-instance deltas:

```text
tranq10_09: 269.002160s -> 165.844333s, retry 6 -> 3
tranq10_10:  78.964476s ->  62.089575s, retry 4 -> 2
tranq10_07: 126.584480s -> 117.805815s
tranq10_01: 140.160357s -> 234.653753s, retry 2 -> 4
tranq10_05:  40.151722s ->  54.622236s
```

Aggregate final-judge diagnostics:

```text
exact_completion_bound_retry_calls: 80 -> 78
harvest_candidate_negative_count:   519 -> 436
harvest_selected_count:             55 -> 44
selected_new_task_set_count:         3 -> 1
selected_support_changing_count:     3 -> 1
selected_weak_replacement_count:     4 -> 1
fallback_fill_count:                12 -> 11
fallback_fill_replacement_count:    12 -> 11
root_tail_rmp_rounds:               81 -> 78
final_judge_added_journeys:         55 -> 44
final_judge_replacement_journeys:   52 -> 43
```

Interpretation:

The current YAML already has completion-bound diverse harvest enabled.  The
probe is not harvest off/on; it is current harvest settings versus alias
overrides with larger max batches and `min_new_masks=16`.

The actual final-judge candidates are still overwhelmingly replacement-only.
Increasing batch limits does not create new task-set masks.  On `tranq10_09`,
batching replacement columns helps because the tail is a representative-cost
tail: fewer repeated final-judge retries are needed.  On `tranq10_01`, the same
mechanism hurts: replacement-only columns increase RMP degeneracy and push the
root tail from 9 to 13 rounds, with generated sequences roughly doubling.

Conclusion:

Do not promote this alias profile as default.  It is exact-safe, but not
performance-robust.  The right next direction is an adaptive gate that only
uses larger final-judge replacement harvesting after the run has demonstrated a
replacement-tail pattern, not on every root-tail instance.
