# B4.1 True-Dual Proof-Tail Strengthening Plan

## 0. Scope

B4.1 narrows B4 from master-cut live optimization to true-dual proof-tail
strengthening. The target bottleneck is:

```text
true-dual pricing / final judge / compact pricing no-negative proof
```

Fixed boundaries:

```text
official objective = normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion
makespan = metric only
5/10/20 B3B = accepted exact baseline when BPC_TREE_OPTIMAL is certified
30-scale = DIAGNOSTIC_PRICING_FRONTIER until true-dual no-negative proof closes
GAT/learning/dual smoothing = candidate search only, never official bound/certificate
```

## 1. Default Proof-Tail Formulation

B4.1 freezes the 30-scale compact pricing default as B4V2:

```text
latest_service_start_slot_bound = true
mtz_endpoint_order_cuts = false
pair_adjacency_cuts = false
time_window_arc_pruning = false
```

V4 remains an explicit diagnostic probe:

```text
latest_service_start_slot_bound = true
mtz_endpoint_order_cuts = true
pair_adjacency_cuts = true
time_window_arc_pruning = true
```

The solver-side compact final judge now also supports an explicit V4 diagnostic
profile without changing the default:

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE unset/empty/B4V2:
    B4V2_latest_start_only

LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4:
    B4V4_endpoint_pair_latest_start_time_window
```

The V4 profile is diagnostic opt-in only. It may be used for staged-resume
frontier probes, but it does not upgrade 30-scale rows to a certificate unless
the true-dual no-negative proof itself closes.

B4.1 also adds an explicit compact-pricing proof-row diagnostic:

```text
LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS=1
LUNAR_ICE_COMPACT_DEMAND_COVER_CUT=1
LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB=1
LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB=1
LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_QUAD_TIME_WINDOW_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT=1
```

This is not a master cut and it is not part of the B4V2 default. It adds
service-start, return, and same-sortie pair route-duration lower-bound rows
inside the compact pricing MILP only:

```text
if task i is selected in a sortie:
    service_start_i >= sortie_start + shortest_travel_lb(depot, i)
    sortie_return >= service_start_i + service_time_i + shortest_travel_lb(i, depot)

if tasks i and j are both selected in a sortie:
    sortie_return - sortie_start >= min(
        shortest_travel_lb(depot, i) + service_i + shortest_travel_lb(i, j) + service_j + shortest_travel_lb(j, depot),
        shortest_travel_lb(depot, j) + service_j + shortest_travel_lb(j, i) + service_i + shortest_travel_lb(i, depot)
    )

if sortie slot s is active:
    sortie_start_s >= s * min_active_sortie_duration
    sortie_end_s >= (s + 1) * min_active_sortie_duration
    sortie_start_s <= latest_service_start_upper_bound - min_depot_outbound_travel_lower_bound

if sum_{i in S} demand_i > sortie_capacity for a minimal bounded cover S:
    sum_{i in S} y_i_slot <= |S| - 1

if task i is selected in a sortie:
    total_sortie_energy >= shortest_energy_lb(depot, i) + service_energy_i + shortest_energy_lb(i, depot)
    total_sortie_shadow >= shortest_shadow_lb(depot, i) + service_shadow_i + shortest_shadow_lb(i, depot)

if pair_energy_lb(i, j) > sortie_energy_limit:
    y_i_slot + y_j_slot <= 1

if every ordering of tasks i, j, k violates time windows or horizon return
under full-graph shortest travel lower bounds:
    y_i_slot + y_j_slot + y_k_slot <= 2

if every ordering of tasks i, j, k, l violates time windows or horizon return
under full-graph shortest travel lower bounds:
    y_i_slot + y_j_slot + y_k_slot + y_l_slot <= 3

if triple_energy_lb(i, j, k) > sortie_energy_limit
and no pair inside the triple is already pair-infeasible:
    y_i_slot + y_j_slot + y_k_slot <= 2

if pair_shadow_lb(i, j) > sortie_shadow_limit:
    y_i_slot + y_j_slot <= 1

if triple_shadow_lb(i, j, k) > sortie_shadow_limit
and no pair inside the triple is already pair-shadow-infeasible:
    y_i_slot + y_j_slot + y_k_slot <= 2
```

The lower bound is computed by shortest travel time over the full fixed graph,
not by assuming direct depot-task triangle inequality. Therefore it is
exact-safe as a formulation strengthening but remains diagnostic until it
helps produce a true-dual no-negative proof.

The slot-position bounds are exact-safe because active sortie slots are
left-packed (`z_{s+1} <= z_s`) and every active sortie consumes at least the
global minimum active sortie duration. The latest-start bound is also safe:
an active sortie must contain at least one task, and even the fastest outbound
travel must reach that task before the global latest feasible service start.
These rows are low-count formulation strengthening rows, not master cuts.

The demand cover cut is exact-safe because all selected tasks in a sortie must
fit the sortie capacity. It is bounded to minimal covers up to size 5 in the
current implementation to avoid size-6 row explosion on 30-scale instances.
It is not part of the default route because the first 30-scale smoke added many
rows without improving the proof bound.

The single-task energy/shadow lower-bound rows are exact-safe because any
sortie visiting task i contains a depot-to-i prefix, task service, and an
i-to-depot suffix. The lower bounds use shortest paths over the full fixed
graph for the relevant resource. They are useful for diagnosis and harvesting,
but they are not currently a recommended proof-bound default because the first
30-scale probes worsened the 60s bound.

The sparse triple-energy infeasible cut is also exact-safe under the fixed
graph because it is triggered only by a full-graph shortest energy lower bound
that already exceeds the sortie energy limit. It is intentionally excluded from
the default/recommended route until measured proof-bound behavior improves over
the sparse pair-energy cut.

The sparse pair/triple-shadow infeasible cuts are exact-safe for the same
reason: they use full-graph shortest shadow-exposure lower bounds plus service
shadow exposure. They remain diagnostic-only. On the current 30-scale
instance001 active pool, pair-shadow found no infeasible pairs, while
triple-shadow found sparse infeasible triples but did not improve the 60s proof
bound enough to become a recommended route.

The sparse triple-time-window infeasible cut is exact-safe because it cuts a
triple only when all six task orders fail under optimistic shortest-travel lower
bounds and earliest-start scheduling. It is stronger than pair time-window cuts
on the current prefix_3 restricted region, but remains diagnostic opt-in until
repeated staged probes show stable proof-tail improvement or closure.

The sparse quad-time-window infeasible cut uses the same conservative logic for
four-task subsets and all 24 possible orders. It remains diagnostic-only. On the
current prefix_3 restricted-region 30s probe it worsened the proof bound versus
the triple-only row, so it is evidence against promoting larger subset
time-window rows without more selective filtering.

Staged-resume command line support:

```text
scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode proof_only

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode feasibility_proof_only

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode feasibility_proof_only \
    --compact-service-start-depot-travel-lb \
    --compact-task-to-depot-return-travel-lb \
    --compact-pair-route-duration-lb \
    --compact-pair-energy-infeasible-cut

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode feasibility_proof_only \
    --compact-service-start-depot-travel-lb \
    --compact-task-to-depot-return-travel-lb \
    --compact-pair-route-duration-lb \
    --compact-sortie-slot-position-bounds \
    --compact-single-task-energy-lb \
    --compact-single-task-shadow-lb \
    --compact-pair-energy-infeasible-cut

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode feasibility_proof_only \
    --compact-service-start-depot-travel-lb \
    --compact-task-to-depot-return-travel-lb \
    --compact-pair-route-duration-lb \
    --compact-sortie-slot-position-bounds \
    --compact-pair-energy-infeasible-cut

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode feasibility_proof_only \
    --compact-service-start-depot-travel-lb \
    --compact-task-to-depot-return-travel-lb \
    --compact-pair-route-duration-lb \
    --compact-demand-cover-cut \
    --compact-pair-energy-infeasible-cut

scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-profile V4 \
    --compact-final-judge-phase-mode feasibility_proof_only \
    --compact-service-start-depot-travel-lb \
    --compact-task-to-depot-return-travel-lb \
    --compact-pair-route-duration-lb \
    --compact-pair-energy-infeasible-cut \
    --compact-triple-time-window-infeasible-cut \
    --compact-quad-time-window-infeasible-cut \
    --compact-triple-shadow-infeasible-cut \
    --compact-triple-energy-infeasible-cut
```

The staged-resume manifest/report records `compact_final_judge_profile` per
stage and `compact_final_judge_phase_mode` per stage, so future 30-scale probes
can distinguish default B4V2, explicit V4 diagnostic runs, and proof-only
diagnostic runs.

`feasibility_proof_only` is a full-space exact diagnostic: it skips no-good
harvesting and solves the `RC <= -eps` feasibility model without forbidden
patterns. If that model is proven infeasible, the result is a true-dual
no-negative proof; if it times out, it remains fail-closed.

V1 endpoint/pair and V3 time-window are no longer default optimization routes.

## 2. Final Judge Harvesting

When the true-dual final judge finds negative reduced-cost columns, B4.1 can
harvest a batch under the same RMP dual before returning.

Default:

```text
harvest_target = 5
selection = deduplicate candidate signatures, prefer new task-set representatives by true RC, then fill remaining target with replacements by true RC
audit = manual RC, pricing RC, branch context, cut context, addability
```

Safety:

```text
restricted/no-good no-column never certifies no-negative
non-addable-only negatives fall through to unrestricted proof or incomplete
all selected columns are recomputed with current true RMP dual
duplicate candidate signatures are never selected twice in one harvest batch
```

Telemetry now preserved through solver payloads and B4.1 CSV rows:

```text
harvest_candidate_negative_count
harvest_selected_count
harvest_selected_new_task_set_count
harvest_selected_replacement_task_set_count
harvest_rejected_duplicate_count
harvest_rejected_not_addable_count
harvest_source_phase
harvest_pricing_rc_audit_available
harvest_pricing_rc_audit_pass
harvest_pricing_rc_max_abs_diff
harvest_best_true_rc
harvest_worst_selected_true_rc
harvest_avg_pairwise_jaccard
```

`B4V2_harvesting` report cells are counted only for compact-final-judge
harvesting. B2/B3 outer post-final-judge addability harvest and worker
candidate-search harvest keep their telemetry, but they do not satisfy the
B4.1 final-judge harvesting requirement.

Stage B matrix coverage is source-aware: a row contributes harvesting cells
only when `harvest_source_phase` is compact-final-judge harvesting, or when it
is a legacy `B4.1_probe_final_judge_evidence` row parsed from an old
final-judge payload. A worker-tail row cannot satisfy harvesting coverage by
setting `b4_1_harvesting_enabled=true`.

The compact final-judge harvest pricing-RC audit is not hard-coded. New
compact pricing payloads expose `pricing_model_reduced_cost`, and selected
harvest columns compare that solver-side value against the true-dual manual
reduced cost. If the solver-side RC is unavailable for a selected column,
`harvest_pricing_rc_audit_available=false` and the pricing-RC audit does not
pass.

B4.1 also adds an optimization-proof harvest path. Its target follows the
B4.1 default `harvest_target=5`; staged diagnostic runs may lower it explicitly
when a shorter row budget is required:

```text
LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_TARGET=3
LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE=task_set
scripts/run_lunar_ice_compact_pricing_staged_resume.py \
    --compact-final-judge-phase-mode proof_only \
    --compact-optimization-harvest-target 3 \
    --compact-optimization-harvest-no-good-scope task_set
```

This path first runs the unrestricted compact optimization proof. If that
proof returns a true-dual negative column, the final judge adds optimization
harvest no-good restrictions and continues solving restricted optimization
pricing calls under the same current RMP dual. The optimization-harvest
no-good scope is deliberately separate from the negative-feasibility batch
scope:

```text
negative-feasibility batch default no-good scope = arc
optimization-harvest default no-good scope = task_set
```

The task-set default matches B4.1's tail objective: after the first exact
optimization proof discovers one representative task set, restricted harvest
should spend its remaining time searching a different task set instead of
route variants of the same set. Selected columns still pass the same manual-RC,
pricing-RC, branch/cut, and addability audits.

Certificate boundary:

```text
unrestricted optimization proof can certify no-negative
restricted optimization harvest can only discover more negative columns
restricted optimization harvest no-column never certifies no-negative
```

Telemetry added to payloads, staged-resume reports, B4.1 rows, and B4 pricing
diagnostic rows:

```text
compact_optimization_harvest_enabled
compact_optimization_harvest_target
compact_optimization_harvest_no_good_scope
compact_optimization_harvest_found_count
compact_optimization_harvest_search_call_count
```

## 3. Hidden-Negative Audit

Every hidden negative found by final judge or replay must record a miss reason:

```text
worker_not_generated
pruned_by_task_bound
pruned_by_resource_bound
pruned_by_dominance
duplicate_filtered
reduced_cost_mismatch
pricing_timeout_only
unknown
```

This keeps the proof-tail diagnosis actionable: generation, pruning, dominance,
timeout, and replacement-only failures are separated.

B4.1 artifacts must also surface the same information at row/report level:

```text
hidden_negative_miss_reason_counts
hidden_negative_top_miss_reason
hidden_negative_worker_not_generated_count
hidden_negative_pruned_by_dominance_count
hidden_negative_pricing_timeout_only_count
```

Older probe payloads that only contain `hidden_negative_audit.rows` are
backfilled into these counts when reports are regenerated, so diagnosis does
not require rerunning expensive 30-scale probes.

## 4. Frontier Ledger Diagnostic

B4.1 records frontier lower-bound fields but does not use them to close a
certificate unless coverage is exhaustive and audited.

Allowed current proof kind:

```text
FRONTIER_BOUND_INCOMPLETE
```

Future upgrade condition:

```text
global_remaining_rc_lb >= -eps
coverage_complete = true
frontier_unsupported_region_count = 0
if exhaustive contrast is available:
    global_remaining_rc_lb <= true_remaining_best_rc + eps
```

The ledger records the optional contrast fields:

```text
true_remaining_best_rc
global_remaining_rc_lb_leq_true_remaining_best_rc
```

If the reported lower bound exceeds the exhaustive true remaining best RC in a
small-scale contrast, the ledger adds
`frontier_lower_bound_exceeds_true_remaining_best_rc` and cannot certify.

Until then, Stage B/C rows are forced to:

```text
certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
can_certify_no_negative = false
frontier_lb_official = false
```

Underlying compact-pricing certificate fields are preserved separately for
audit, but suppressed from official B4.1 status.

## 5. Tail Dual Stabilization

Tail dual stabilization is opt-in and worker-only:

```text
enabled = false
alpha = 0.7
window = 5
worker_dual = alpha * current_true_dual + (1 - alpha) * moving_average_dual
```

The worker dual may rank candidate columns, but every candidate is scored again
with the current true RMP dual. Worker no-column never certifies no-negative.

Required telemetry for every tail-dual worker row:

```text
worker_dual_source = tail_dual_stabilized_worker_dual
official_dual_source = current_true_rmp_dual
worker_dual_only = true
true_dual_rc_recomputed = true
tail_dual_no_column_can_certify = false
tail_dual_stabilization_alpha/window/center_task_count/current_task_count
```

If any tail-dual row claims no-negative certification, skips true-dual RC
recompute, is not worker-only, or uses a non-current official dual source, the
B4.1 report must raise `tail_dual_certificate_leak_count`.

## 6. Stage A Regression Defaults

Stage A is intentionally conservative and resumable.

Current default proof-tail parameters:

```text
max_rounds = 16
max_columns_per_round = 128
max_tree_nodes = 31
max_branch_depth = 4
```

The 128 column-per-round and 16-round defaults are required because 20-scale
full Stage A exposed two parameter-limited proof-tail failures:

```text
64 columns/round, 8 rounds:
    instance001 can still have true negative columns.

128 columns/round, 8 rounds:
    20-scale full B3B/B4V2 closed only 9/20 instances.
    Some failures still had root negative columns.
    Some failures had certified root no-negative but an unfinished tree.

128 columns/round, 16 rounds:
    representative failures instance002, instance010, instance016,
    instance017, and instance019 closed as BPC_TREE_OPTIMAL.
    the full 8-round failure subset, 11 instances x B3B/B4V2,
    closed 22/22 as BPC_TREE_OPTIMAL.
```

This is not a certificate relaxation. It gives the existing true-dual root/tree
proof-tail enough rounds to finish adding valid negative columns and close
branch nodes.

Stage A rows now record:

```text
max_rounds
max_columns_per_round
max_tree_nodes
max_branch_depth
node_count
root_round_count
root_added_column_count
root_last_pricing_state
root_last_negative_column_count
tree_gate_issue_count
```

Stage B/C diagnostic rows now additionally record:

```text
compact_final_judge_profile
compact_final_judge_formulation_profile
phase_budget_sec
negative_feasibility_budget_sec
optimization_proof_budget_sec
negative_discovery_budget_exhausted
optimization_proof_missing
stage_b_observed_matrix_cells
stage_b_missing_matrix_cells
active_column_count
pool_column_count
columns_added
active_columns_after_merge
new_task_set_count
replacement_task_set_count
best_negative_rc
last_best_reduced_cost
final_judge_wall_time
rmp_round_count
```

These are diagnostic fields only. In particular, `optimization_proof_missing`
explains rows like Stage B stage4 where the run consumed the staged budget in
negative-feasibility discovery and never produced an unrestricted optimization
proof bound.

The Stage B matrix coverage audit uses the plan-required cells:

```text
B4V2_baseline
B4V2_harvesting
B4V2_hidden_negative_audit
B4V2_frontier_ledger_diagnostic
B4V2_harvesting_frontier_ledger_diagnostic
B4V4_combined_formulation_diagnostic
```

One physical row may cover more than one cell. For example, a V2 row with the
frontier ledger enabled covers both `B4V2_baseline` and
`B4V2_frontier_ledger_diagnostic`; it does not cover harvesting or
hidden-negative audit unless those flags are present in the row.

Stage B also has zero-solve evidence rows. They parse existing payloads and do
not invoke a compact MILP.

`probe_final_judge_evidence` parses an existing staged-resume or batch probe's
`final_judge` payload and can cover:

```text
B4V2_harvesting
B4V2_harvesting_frontier_ledger_diagnostic
```

`worker_tail_hidden_negative_evidence` parses an existing B2/B2B worker-tail
payload with an explicit top-level `hidden_negative_audit` object and can cover:

```text
B4V2_hidden_negative_audit
```

If the same B2/B2B payload carries top-level `harvest_*` telemetry, that
telemetry is still recorded for diagnosis. It covers B4.1 harvesting only when
`harvest_source_phase` explicitly identifies compact-final-judge harvesting;
ordinary worker or post-final-judge addability harvest does not count.
Ordinary `candidate_negative_count` is not enough to count as B4.1 harvesting
evidence.

These evidence rows never upgrade certificate scope. They only prevent
rerunning compact formulation variants just to prove that planned harvesting,
frontier, or hidden-negative telemetry is present.

## 7. Current Artifact State

Implemented runner:

```text
scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py
src/lunar_ice_bpc/runners/b4_1_true_dual_proof_tail.py
```

Primary output directories:

```text
runs/b4_1_true_dual_proof_tail_strengthening/
runs/b4_1_true_dual_proof_tail_stage_a_20_probe/
runs/b4_1_true_dual_proof_tail_stage_b_30_v2_60s/
runs/b4_1_true_dual_proof_tail_stage_b_30_v2_v4_60s/
runs/b4_1_true_dual_proof_tail_stage_a_20_closure_audit/
runs/b4_1_true_dual_proof_tail_stage_a_5_10_20_mainline_r16/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_600_900s/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_replay_merge/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_merged_staged_resume/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_frontier_integration_audit/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_profile_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_proof_only_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_feasibility_proof_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_service_start_lb_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_service_start_and_return_lb_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_lb_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_time_and_pair_energy_lb_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_lb_pair_energy_cut_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_pair_triple_energy_cut_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_existing_harvest_evidence/
runs/b4_1_true_dual_proof_tail_stage_c_selected30_input_probes/
runs/b4_1_true_dual_proof_tail_stage_c_selected30_v4_60s/
runs/b4_1_true_dual_proof_tail_stage_c_selected30_audit/
runs/b4_1_true_dual_proof_tail_stage_b_30_worker_tail_hidden_probe/
runs/b4_1_true_dual_proof_tail_stage_b_consolidated_matrix/
runs/b4_1_true_dual_proof_tail_tail_dual_telemetry_smoke/
runs/b4_1_true_dual_proof_tail_acceptance_audit/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_pair_energy_shadow_cut_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_pair_energy_triple_shadow_cut_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_pair_energy_demand_cover_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_pair_energy_slot_position_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_slot_position_single_resource_pair_energy_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_slot_position_single_energy_pair_energy_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_slot_position_single_shadow_pair_energy_feasibility_smoke/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_slot_position_pair_energy_after_single_energy_merge/
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_slot_position_pair_energy_after_single_energy_merge_180s/
```

Current verified status:

```text
5/10 Stage A full regression: clean
20 instance001 Stage A probe: B3B and B4V2 both BPC_TREE_OPTIMAL with 128 columns/round
20 full Stage A with 128 columns/round and 8 rounds: B3B/B4V2 both 9/20 BPC_TREE_OPTIMAL
20 8-round failure subset with 128 columns/round and 16 rounds: B3B/B4V2 both 11/11 BPC_TREE_OPTIMAL
5/10/20 mainline Stage A with 128 columns/round and 16 rounds:
    B3B accepted baseline = 60/60 BPC_TREE_OPTIMAL
    B4V2 default final judge harvesting = 60/60 BPC_TREE_OPTIMAL
    redlines = 0
30 instance001 short V2 diagnostic: still DIAGNOSTIC_PRICING_FRONTIER
30 instance001 short V4 diagnostic: improves frontier LB versus V2 but still remains incomplete
    V2 best global_remaining_rc_lb ~= -0.432157206
    V4 best global_remaining_rc_lb ~= -0.198360699
30 instance001 long V4 diagnostic:
    600/900s V4 best global_remaining_rc_lb ~= -0.007881834
    exact compact replay found one true negative column with RC ~= -0.0080034
    merging that column increased active columns 297 -> 298
    four staged resume stages increased active columns 298 -> 304
    staged added columns by stage = 2, 1, 1, 2
    stages 1-3 reached optimization_proof with positive final best RC
    stages 1-3 still had negative final dual bounds:
        -0.192496096, -0.179285852, -0.165591678
    stage4 exhausted the staged budget in negative_feasibility_search
    stage4 therefore has no final optimization-proof bound
    the new proof-tail diagnostics mark this as optimization_proof_missing
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
30 instance001 V4 solver-profile smoke:
    staged-resume entrypoint accepted --compact-final-judge-profile V4
    final judge payload recorded compact_final_judge_profile = V4
    endpoint/order, pair-adjacency, latest-start, and time-window options were all enabled
    60s smoke added 0 columns and produced no no-negative proof
    this validates the diagnostic plumbing, not closure progress
30 instance001 V4 proof-only smoke:
    staged-resume entrypoint accepted --compact-final-judge-phase-mode proof_only
    negative-feasibility discovery was skipped
    final judge phase = optimization_proof
    60s proof-only best RC ~= 0.050987667
    60s proof-only dual bound ~= -0.216844928
    no negative column was found, but no no-negative proof closed
    conclusion: this smoke points at weak proof bound/formulation, not at missing harvesting
30 next diagnostic target:
    V4 feasibility_proof_only was run on the same 304-column active pool
    negative-feasibility proof phase = negative_feasibility_proof
    full-space feasibility proof attempted = true
    60s feasibility-proof dual bound ~= -0.22153565
    no negative column was found, but infeasibility/no-negative was not proven
    diagnostic rows now distinguish feasibility_proof_budget_exhausted from negative_discovery_budget_exhausted
    conclusion: the next target is stronger full-space feasibility formulation/bounds
30 instance001 V4 feasibility-proof smoke with service-start depot-travel LB:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        --compact-service-start-depot-travel-lb
    exact-safe row semantics:
        if task i is selected in a sortie, service_start_i >= sortie_start + shortest_travel_lb(depot, i)
        shortest_travel_lb is computed over the full fixed graph, not by assuming direct-arc triangle inequality
    60s feasibility-proof dual bound ~= -0.206168025
    service_start_depot_travel_lb_count = 630
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: the new row gives a small proof-bound lift versus the previous 60s feasibility-proof smoke, but does not close 30-scale
30 instance001 V4 feasibility-proof smoke with service-start + task-return LB:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
    exact-safe row semantics:
        if task i is selected in a sortie:
            service_start_i >= sortie_start + shortest_travel_lb(depot, i)
            sortie_return >= service_start_i + service_time_i + shortest_travel_lb(i, depot)
    60s feasibility-proof dual bound ~= -0.199035597
    service_start_depot_travel_lb_count = 630
    task_to_depot_return_travel_lb_count = 630
    variables stayed 24109
    constraints increased to 58347
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: the paired rows improve the 60s full-space feasibility bound from -0.221535650 to -0.199035597, but still do not close 30-scale
30 instance001 V4 feasibility-proof smoke with service-start + task-return + pair-route LB:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
    exact-safe row semantics:
        if tasks i and j are both selected in a sortie:
            sortie_return - sortie_start must cover the shorter of depot-i-j-depot and depot-j-i-depot lower-bound tours
    60s feasibility-proof dual bound ~= -0.192185417
    service_start_depot_travel_lb_count = 630
    task_to_depot_return_travel_lb_count = 630
    pair_route_duration_lb_count = 9135
    variables stayed 24109
    constraints increased to 67482
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: the three-row package improves the 60s full-space feasibility bound from -0.221535650 to -0.192185417, but still does not close 30-scale
30 instance001 dense pair-energy LB diagnostic:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_PAIR_ENERGY_LB=1
        --compact-pair-energy-lb
    result:
        pair_energy_lb_count = 9135
        pair_energy_lb_exceeds_limit_count = 37
        constraints increased to 76617
        60s HiGHS returned TIME_LIMIT_REACHED without a usable dual_bound
    conclusion:
        dense pair-energy lower-bound rows are exact-safe, but not a good proof-tail route in this form;
        prefer the sparse infeasible-pair cut below.
30 instance001 V4 feasibility-proof smoke with three time LBs + sparse pair-energy infeasible cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
        --compact-pair-energy-infeasible-cut
    exact-safe row semantics:
        for task pairs whose full-graph shortest energy lower bound exceeds sortie energy limit:
            y_i_slot + y_j_slot <= 1
    30 instance001 signal:
        pair_energy_infeasible_pair_count = 37
        pair_energy_infeasible_cut_count = 777
    60s feasibility-proof dual bound ~= -0.184780451
    variables stayed 24109
    constraints increased to 68259
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: sparse pair-energy infeasible cuts improve the 60s bound from -0.192185417 to -0.184780451 and avoid the dense pair-energy LB no-bound failure
30 instance001 V4 feasibility-proof staged smoke with three time LBs + slot-position bounds + sparse pair-energy infeasible cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS=1
        LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
        --compact-sortie-slot-position-bounds
        --compact-pair-energy-infeasible-cut
    exact-safe row semantics:
        for active sortie slot s:
            sortie_start_s >= s * min_active_sortie_duration
            sortie_end_s >= (s + 1) * min_active_sortie_duration
            sortie_start_s <= latest_service_start_upper_bound - min_depot_outbound_travel_lower_bound
    30 instance001 stage1 signal:
        sortie_slot_position_bound_count = 62
        constraint_count = 68321
        60s feasibility-proof dual bound ~= -0.176899749
        true negative column found with RC ~= -0.010620295
        active columns increased 304 -> 305
    30 instance001 stage2 signal:
        resumed from the 305-column pool
        no negative column found in the 60s feasibility-proof run
        60s feasibility-proof dual bound ~= -0.187253602
        active columns stayed 305
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: slot-position bounds are the best short-run sparse proof-row signal so far because they improve the 60s bound and harvest one true negative column, but they still do not close no-negative proof; continue staged harvesting/proof instead of upgrading the certificate
30 instance001 V4 feasibility-proof smokes with three time LBs + slot-position bounds + single-task resource LBs + sparse pair-energy cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB=1
        LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB=1
        --compact-single-task-energy-lb
        --compact-single-task-shadow-lb
    exact-safe row semantics:
        if task i is selected:
            total_sortie_energy must cover shortest depot-i energy, service energy, and shortest i-depot energy
            total_sortie_shadow must cover shortest depot-i shadow, service shadow, and shortest i-depot shadow
    combined energy+shadow signal:
        single_task_energy_lb_count = 630
        single_task_shadow_lb_count = 630
        constraint_count = 69581
        60s feasibility-proof dual bound ~= -0.195820223
        no negative column found
    energy-only signal:
        single_task_energy_lb_count = 630
        constraint_count = 68951
        true negative column found with RC ~= -0.005348375
        active columns increased 305 -> 306
        60s feasibility-proof dual bound ~= -0.195067330
    shadow-only signal:
        single_task_shadow_lb_count = 630
        constraint_count = 68951
        60s feasibility-proof dual bound ~= -0.192305961
        no negative column found
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: single-task resource rows are exact-safe and energy-only can harvest a small true negative, but all three 60s bounds are worse than the slot-position + sparse pair-energy baseline; keep them diagnostic/harvest-only, not default proof-bound rows
30 instance001 resumed clean proof after merging the single-task-energy harvested column:
    source:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_three_time_slot_position_single_energy_pair_energy_feasibility_smoke/stage_001/probe.json
    resumed active pool:
        306 columns
    clean formulation:
        service-start depot-travel LB
        task-to-depot return-travel LB
        pair route-duration LB
        slot-position bounds
        sparse pair-energy infeasible cut
        no single-task resource LB rows
    60s staged follow-up:
        stage1:
            no negative column found
            dual bound ~= -0.170915893
            active columns stayed 306
        stage2:
            no negative column found
            dual bound ~= -0.170915195
            active columns stayed 306
    180s staged follow-up:
        stage1:
            true negative column found with RC ~= -0.001481529
            dual bound ~= -0.111860253
            active columns increased 306 -> 307
        stage2:
            true negative column found with RC ~= -0.003097000
            dual bound ~= -0.102248554
            active columns increased 307 -> 308
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: the clean slot-position + sparse pair-energy formulation is the current best B4.1 route. Longer stages improve the proof bound substantially and continue harvesting tiny true-negative tail columns, but 30-scale no-negative proof is still not closed.
30 instance001 V4 feasibility-proof smoke with three time LBs + sparse pair-energy cut + sparse triple-energy cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
        LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
        --compact-pair-energy-infeasible-cut
        --compact-triple-energy-infeasible-cut
    exact-safe row semantics:
        for task triples whose full-graph shortest energy lower bound exceeds sortie energy limit,
        and which are not already explained by an infeasible pair:
            y_i_slot + y_j_slot + y_k_slot <= 2
    30 instance001 signal:
        triple_energy_infeasible_triple_count = 488
        triple_energy_infeasible_cut_count = 10248
        triple_energy_infeasible_lb_min ~= 500.058267
        triple_energy_infeasible_lb_max ~= 654.663083
    60s feasibility-proof dual bound ~= -0.188890519
    variables stayed 24109
    constraints increased to 78507
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: the triple cut is diagnostic-only for now; it is exact-safe, but its 60s bound is worse than the sparse pair-energy-only bound -0.184780451
30 instance001 V4 feasibility-proof smoke with three time LBs + sparse pair-energy cut + sparse pair-shadow cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
        LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
        --compact-pair-energy-infeasible-cut
        --compact-pair-shadow-infeasible-cut
    exact-safe row semantics:
        for task pairs whose full-graph shortest shadow-exposure lower bound exceeds sortie shadow-exposure limit:
            y_i_slot + y_j_slot <= 1
    30 instance001 signal:
        pair_shadow_infeasible_pair_count = 0
        pair_shadow_infeasible_cut_count = 0
        pair_shadow_infeasible_lb_min ~= 5.551162437
        pair_shadow_infeasible_lb_max ~= 210.478652
    60s feasibility-proof dual bound ~= -0.186068137
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: pair-shadow plumbing is exact-safe and reportable, but instance001 has no pair-shadow infeasible rows; it is not a useful breakthrough route for this hard case
30 instance001 V4 feasibility-proof smoke with three time LBs + sparse pair-energy cut + sparse triple-shadow cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
        LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
        --compact-pair-energy-infeasible-cut
        --compact-triple-shadow-infeasible-cut
    exact-safe row semantics:
        for task triples whose full-graph shortest shadow-exposure lower bound exceeds sortie shadow-exposure limit,
        and which are not already explained by a pair-shadow infeasible cut:
            y_i_slot + y_j_slot + y_k_slot <= 2
    30 instance001 signal:
        triple_shadow_infeasible_triple_count = 33
        triple_shadow_infeasible_cut_count = 693
        triple_shadow_infeasible_lb_min ~= 241.316840
        triple_shadow_infeasible_lb_max ~= 295.154036
    60s feasibility-proof dual bound ~= -0.195643744
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: triple-shadow cuts have real sparse signal, but their 60s bound is worse than the sparse pair-energy-only bound -0.184780451; keep them diagnostic-only rather than default
30 instance001 V4 feasibility-proof smoke with three time LBs + sparse pair-energy cut + bounded demand-cover cut:
    opt-in env/CLI:
        LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
        LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
        LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
        LUNAR_ICE_COMPACT_DEMAND_COVER_CUT=1
        --compact-service-start-depot-travel-lb
        --compact-task-to-depot-return-travel-lb
        --compact-pair-route-duration-lb
        --compact-pair-energy-infeasible-cut
        --compact-demand-cover-cut
    exact-safe row semantics:
        for each bounded minimal same-sortie demand cover S with sum demand_i > sortie_capacity:
            sum_{i in S} y_i_slot <= |S| - 1
    30 instance001 signal:
        demand_cover_subset_count = 1686
        demand_cover_cut_count = 35406
        demand_cover_max_size = 5
        demand_cover_min_demand = 6.5
        demand_cover_max_demand = 7.5
    60s feasibility-proof dual bound ~= -0.197151724
    active columns stayed 304 and added columns = 0
    no negative column was found, but infeasibility/no-negative was not proven
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: demand-cover cuts are exact-safe and expose real capacity structure, but this bounded size-5 variant adds too many rows and gives a worse 60s bound than sparse pair-energy-only; keep it diagnostic-only rather than default
30 existing probe Stage B harvesting evidence:
    source probe:
        runs/b4_1_true_dual_proof_tail_stage_c_selected30_input_probes/instance_001/stage_001/probe.json
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_existing_harvest_evidence/
    evidence-only command:
        scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py --stage-b --stage-b-variants
    observed Stage B matrix cells:
        B4V2_baseline
        B4V2_frontier_ledger_diagnostic
        B4V2_harvesting
        B4V2_harvesting_frontier_ledger_diagnostic
    remaining Stage B missing cells:
        B4V2_hidden_negative_audit
        B4V4_combined_formulation_diagnostic
    certificate remains DIAGNOSTIC_PRICING_FRONTIER
    conclusion: existing probe evidence proves final-judge harvesting telemetry is available for 30-scale instance001,
    but it does not prove hidden-negative audit because the source probe did not carry a hidden_negative_audit payload.
worker-tail hidden-negative evidence parser:
    implemented as zero-solve `B4.1_worker_tail_hidden_negative_evidence`
    input requirement:
        schema_version is B2/B2B-style or payload has b2_mode/node_pricing_mode/worker_seed_catalog
        top-level hidden_negative_audit object is present
    output:
        certificate_scope is forced to DIAGNOSTIC_PRICING_FRONTIER
        can_certify_no_negative is forced false
        B4V2_hidden_negative_audit matrix cell is covered
    live worker-tail probe support:
        implemented as `run_b4_1_stage_b_worker_tail_hidden_probe`
        CLI entry:
            scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py --stage-b-worker-tail-hidden-probe
        default behavior can skip expensive B0 direct-DP and use a diagnostic
        reference-solution seed. This is only for proof-tail evidence plumbing;
        it is never an official B0/BPC certificate.
        B2B_R2 now propagates the remaining row wall-time into final judge, so
        short worker-tail probes fail closed instead of overrunning the row.
    current 30 instance001 artifact:
        output:
            runs/b4_1_true_dual_proof_tail_stage_b_30_worker_tail_hidden_probe/
        command shape:
            LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC=10 \
            PYTHONPATH=src python scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py \
                --stage-b-worker-tail-hidden-probe \
                --instance data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json \
                --output-dir runs/b4_1_true_dual_proof_tail_stage_b_30_worker_tail_hidden_probe \
                --stage-b-worker-tail-max-direct-tasks 30 \
                --stage-b-worker-tail-max-rounds 2 \
                --stage-b-worker-tail-time-limit-sec 30 \
                --stage-b-worker-tail-max-columns-per-round 32 \
                --no-resume
        result:
            algorithm_status = BPC_INCOMPLETE_PRICING
            certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
            pricing_state = INCOMPLETE_LIMIT
            pricing_round_count = 2
            final_judge_call_count = 2
            harvest_candidate_negative_count = 16
            harvest_selected_count = 16
            harvest_source_phase = empty/outer B2 addability harvest, not compact final judge harvest
            harvest_best_true_rc ~= -0.380470
            harvest_worst_selected_true_rc ~= -0.0700505
            hidden_negative_count = 0
            fail_closed_reason = NO_HIDDEN_NEGATIVE
            redlines = 0
        interpretation:
            this is a real 30-scale Stage B worker-tail/final-judge artifact,
            not a synthetic row. It covers the planned hidden-negative audit
            telemetry cell by proving that no hidden-negative miss was observed
            in this short run. The 16 harvested columns are outer B2 addability
            harvest telemetry, not compact final-judge `harvest_target=5`
            telemetry. Therefore this artifact no longer covers
            `B4V2_harvesting`. It still does not close proof-tail, and the row
            correctly remains DIAGNOSTIC_PRICING_FRONTIER.
        observed Stage B matrix cells in this artifact:
            B4V2_baseline
            B4V2_frontier_ledger_diagnostic
            B4V2_hidden_negative_audit
        missing Stage B matrix cells in this artifact:
            B4V2_harvesting
            B4V2_harvesting_frontier_ledger_diagnostic
            B4V4_combined_formulation_diagnostic
consolidated Stage B matrix artifact:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_consolidated_matrix/
    input rows:
        runs/b4_1_true_dual_proof_tail_stage_b_30_worker_tail_hidden_probe/b4_1_rows.jsonl
        runs/b4_1_true_dual_proof_tail_stage_b_existing_harvest_evidence/b4_1_rows.jsonl
        runs/b4_1_true_dual_proof_tail_stage_b_30_v2_v4_60s/b4_1_rows.jsonl
    command shape:
        PYTHONPATH=src python scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py \
            --output-dir runs/b4_1_true_dual_proof_tail_stage_b_consolidated_matrix \
            --import-rows-jsonl runs/b4_1_true_dual_proof_tail_stage_b_30_worker_tail_hidden_probe/b4_1_rows.jsonl \
            --import-rows-jsonl runs/b4_1_true_dual_proof_tail_stage_b_existing_harvest_evidence/b4_1_rows.jsonl \
            --import-rows-jsonl runs/b4_1_true_dual_proof_tail_stage_b_30_v2_v4_60s/b4_1_rows.jsonl \
            --no-resume
    result:
        row_count = 6
        stage_b_matrix_complete = true
        stage_b_diagnostic_clean = true
        observed Stage B matrix cells:
            B4V2_baseline
            B4V2_frontier_ledger_diagnostic
            B4V2_harvesting
            B4V2_harvesting_frontier_ledger_diagnostic
            B4V2_hidden_negative_audit
            B4V4_combined_formulation_diagnostic
        missing Stage B matrix cells:
            none
        redlines = 0
    interpretation:
        this is a consolidated evidence report only. It merges already persisted
        Stage B rows and does not rerun compact pricing. It proves the planned
        Stage B diagnostic matrix is reportable in one artifact. The harvesting
        cells come from the existing final-judge evidence row, while the
        worker-tail row contributes hidden-negative audit evidence. The report
        still keeps `b4_1_full_experiment_complete=false` and all 30-scale rows
        diagnostic-only.
tail-dual telemetry smoke:
    output:
        runs/b4_1_true_dual_proof_tail_tail_dual_telemetry_smoke/
    command shape:
        PYTHONPATH=src python scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py \
            --stage-a \
            --instance data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json \
            --stage-a-modes stageA_B2B_R2_worker_tail_dual_on \
            --output-dir runs/b4_1_true_dual_proof_tail_tail_dual_telemetry_smoke \
            --max-direct-tasks 5 \
            --max-rounds 1 \
            --max-columns-per-round 32 \
            --row-time-limit-sec 60 \
            --no-resume
    result:
        row_count = 1
        tail_dual_enabled_count = 1
        worker_dual_source = tail_dual_stabilized_worker_dual
        official_dual_source = current_true_rmp_dual
        worker_dual_only = true
        true_dual_rc_recomputed = true
        tail_dual_no_column_can_certify = false
        redlines = 0
    interpretation:
        this is a small telemetry proof that tail-dual smoothing is still
        worker-only under the current schema. It is not a closure experiment.
combined B4.1 acceptance audit artifact:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit/
    input rows:
        runs/b4_1_true_dual_proof_tail_stage_a_5_10_20_mainline_r16/b4_1_rows.jsonl
        runs/b4_1_true_dual_proof_tail_tail_dual_telemetry_smoke/b4_1_rows.jsonl
        runs/b4_1_true_dual_proof_tail_stage_b_consolidated_matrix/b4_1_rows.jsonl
        runs/b4_1_true_dual_proof_tail_stage_c_selected30_v4_60s/b4_1_rows.jsonl
    result:
        row_count = 137
        Stage A regression clean = true
        Stage B matrix complete = true
        Stage C selected diagnostic clean = true
        diagnostic-only Stage B/C rows = true
        tail-dual worker-only audit = true
        redlines = 0
        30-scale exact closure = incomplete
    interpretation:
        R1-R6 in the machine-readable requirement audit pass. R7 remains
        incomplete because no 30-scale row has a true-dual proof supporting
        BPC_TREE_OPTIMAL yet.
30 selected 5-instance Stage C V4 60s diagnostic:
    input probes generated for instances 001-005
    Stage C rows = 10
    all rows remained DIAGNOSTIC_PRICING_FRONTIER
    no row claimed can_certify_no_negative
    every selected instance still had a negative frontier LB
    best selected frontier LB ~= -0.770056922
    Stage C confirms the proof-tail bottleneck generalizes beyond instance001
30 instance001 V4 optimization-harvest smoke after 313-column pool:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_after_313/
    command shape:
        PYTHONPATH=src python scripts/run_lunar_ice_compact_pricing_staged_resume.py \
            --instance data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json \
            --initial-resume-probe runs/b4_1_true_dual_proof_tail_stage_b_30_v4_slot_position_pair_energy_proof_only_after_312/stage_001/probe.json \
            --stage-count 1 \
            --stage-time-limit-sec 300 \
            --max-rounds-per-stage 1 \
            --compact-optimization-harvest-target 3 \
            --compact-final-judge-profile V4 \
            --compact-final-judge-phase-mode proof_only \
            --compact-service-start-depot-travel-lb \
            --compact-task-to-depot-return-travel-lb \
            --compact-pair-route-duration-lb \
            --compact-sortie-slot-position-bounds \
            --compact-pair-energy-infeasible-cut
    result:
        stage_count = 1
        resume active columns = 313
        active columns after merge = 314
        added columns = 1
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 3
        compact_optimization_harvest_found_count = 1
        compact_optimization_harvest_search_call_count = 2
        harvest_source_phase = compact_final_judge_optimization_harvest
        harvest_selected_new_task_set_count = 1
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 4.95e-07
        best true RC ~= -0.003386077
        compact dual bound ~= -0.003385582
        final judge wall ~= 293.33s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    interpretation:
        optimization-harvest is wired and audit-safe, but it did not close
        30-scale. The restricted harvest could not find enough additional
        columns within the same 300s row; 30-scale remains a frontier.
30 instance001 V4 optimization-harvest task-set smoke after 314-column pool:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_314/
    change tested:
        optimization harvest no-good scope was separated from negative batch
        no-good scope and set to task_set by default.
    result:
        resume active columns = 314
        active columns after merge = 315
        added columns = 1
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 3
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 1
        compact_optimization_harvest_search_call_count = 2
        forbidden_arc_pattern_count = 0
        forbidden_task_set_count = 1
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 1.27e-07
        best true RC ~= -0.00749804
        compact dual bound ~= -0.007498167
        final judge wall ~= 293.23s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    restricted harvest phase:
        optimization_proof wall ~= 243.34s and found the first exact negative
        optimization_harvest_2 had only ~= 49.89s remaining
        optimization_harvest_2 status = TIME_LIMIT_REACHED
        optimization_harvest_2 incumbent RC ~= 0.04557424
        optimization_harvest_2 dual bound ~= -0.178436792
    interpretation:
        task-set no-good is now applied correctly and avoids same-task-set
        route-variant harvest. It still does not close 30-scale because the
        first unrestricted optimization proof consumes most of a 300s row,
        leaving too little time for restricted harvest to prove or find the
        next task-set negative.
30 instance001 V4 optimization-harvest task-set smoke after 315-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_315_600s/
    result:
        resume active columns = 315
        active columns after merge = 318
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 3
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 3
        harvest_selected_new_task_set_count = 3
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 2.61e-07
        best true RC ~= -0.004252723
        compact dual bound ~= -0.004252789
        final judge wall ~= 503.42s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 147.98s
            rc ~= -0.004252723
        optimization_harvest_2 restricted exact negative:
            wall ~= 180.48s
            rc ~= -0.004137002
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted exact negative:
            wall ~= 174.96s
            rc ~= -0.003719724
            forbidden_task_set_count = 2
    interpretation:
        the previous 300s failure was mostly a budget issue, not proof
        unsoundness. With enough row budget, task-set optimization harvest
        can return multiple exact, addable, audited hidden negatives under
        the same true RMP dual. It still does not certify no-negative; it
        is a stronger column-harvesting tail route for continuing the 30-scale
        staged frontier.
30 instance001 V4 optimization-harvest task-set smoke after 318-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_318_600s/
    result:
        resume active columns = 318
        active columns after merge = 321
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 3
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 1.67e-07
        best true RC ~= -0.00298
        compact dual bound ~= -0.002979877
        final judge wall ~= 600.48s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 205.76s
            rc ~= -0.00298
        optimization_harvest_2 restricted exact negative:
            wall ~= 242.92s
            rc ~= -0.002906
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit incumbent negative:
            wall ~= 134.19s
            rc ~= -0.001157
            dual bound ~= -0.104992552
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 17.61s
            incumbent RC ~= 0.10968
            dual bound ~= -0.203768486
            forbidden_task_set_count = 3
    interpretation:
        the 600s route continues to make progress, but target=5 cannot fit
        five exact restricted proofs into one row. It added three audited
        columns and then exhausted the row during the fourth restricted region.
        This supports continuing staged 600s frontier harvesting, while also
        showing that a future no-negative proof still needs a stronger global
        remaining-region bound or a faster restricted proof.
30 instance001 V4 optimization-harvest task-set smoke after 321-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_321_600s/
    result:
        resume active columns = 321
        active columns after merge = 324
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 3
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 2.69e-07
        best true RC ~= -0.005548143
        compact dual bound ~= -0.005547991
        final judge wall ~= 596.83s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 181.62s
            rc ~= -0.005548143
        optimization_harvest_2 restricted exact negative:
            wall ~= 195.03s
            rc ~= -0.005548143
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted exact negative:
            wall ~= 169.19s
            rc ~= -0.005332929
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 50.98s
            incumbent RC ~= 1e-09
            dual bound ~= -0.181390497
            forbidden_task_set_count = 3
    interpretation:
        staged 600s task-set harvest still finds exact addable negatives after
        321 active columns, so the 30-scale tail is not depleted. The best
        negative RC is not monotone across stages because each merge changes
        the RMP dual. The repeated pattern is now clear: each 600s row can
        usually certify and add about three task-set negatives, then runs out
        during the next restricted region. B4.1 should keep this as the
        current 30-scale frontier expansion route, but no exact closure is
        justified until an unrestricted proof returns no negative with complete
        coverage.
30 instance001 V4 optimization-harvest task-set smoke after 324-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_324_600s/
    result:
        resume active columns = 324
        active columns after merge = 327
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 3
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 3.87e-07
        best true RC ~= -0.002800193
        compact dual bound ~= -0.00280016
        final judge wall ~= 600.54s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 173.49s
            rc ~= -0.002800193
        optimization_harvest_2 restricted exact negative:
            wall ~= 186.84s
            rc ~= -0.002722192
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit incumbent negative:
            wall ~= 217.29s
            rc ~= -0.002358808
            dual bound ~= -0.062942591
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 22.92s
            incumbent RC ~= 0.099895135
            dual bound ~= -0.163186609
            forbidden_task_set_count = 3
    interpretation:
        the 324-column frontier still produces three audited addable negative
        columns in one 600s stage. This confirms the staged tail is still live.
        The third negative came from a time-limited restricted solve, so the
        tail route is useful for harvesting but still insufficient for a
        no-negative proof. Continue staged expansion before attempting a final
        unrestricted no-negative closure.
30 instance001 V4 optimization-harvest task-set smoke after 327-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_327_600s/
    result:
        resume active columns = 327
        active columns after merge = 330
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 3
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        best true RC ~= -0.004225517
        compact dual bound ~= -0.004226017
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 593.55s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 170.50s
            rc ~= -0.004225517
        optimization_harvest_2 restricted exact negative:
            wall ~= 167.60s
            rc ~= -0.003493001
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted exact negative:
            wall ~= 198.13s
            rc ~= -0.002979001
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 56.97s
            incumbent RC ~= -0.0
            dual bound ~= -0.173507466
            forbidden_task_set_count = 3
    interpretation:
        the 327-column frontier still has at least three new task-set negative
        columns under the current true RMP dual. The repeated 600s pattern is
        now stable: exact unrestricted proof plus two restricted exact harvest
        phases usually fit, while the fourth region remains unresolved. This
        is useful frontier expansion evidence, but it is also strong evidence
        that 30-scale is not yet closeable by harvesting alone. The next safe
        continuation point is this 330-column probe; any certificate upgrade
        still requires complete coverage and a true-dual no-negative proof.
30 instance001 V4 optimization-harvest task-set smoke after 330-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_330_600s/
    result:
        resume active columns = 330
        active columns after merge = 333
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 2
        harvest_selected_replacement_task_set_count = 1
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 3.11e-07
        best true RC ~= -0.002031375
        compact dual bound ~= -0.002031064
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 597.27s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 192.87s
            rc ~= -0.002031375
        optimization_harvest_2 restricted exact negative:
            wall ~= 224.78s
            rc ~= -0.001633375
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit incumbent negative:
            wall ~= 163.15s
            rc ~= -0.000923125
            dual bound ~= -0.118664892
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 16.46s
            incumbent RC ~= 0.103447375
            dual bound ~= -0.209748622
            forbidden_task_set_count = 3
    interpretation:
        the 330-column frontier still produces audited addable negatives, but
        the harvest is no longer purely new-task-set expansion: two selected
        columns introduce new task sets and one is a replacement. This suggests
        the tail has shifted from only missing task-set coverage toward a mix
        of missing coverage and representative-quality improvement. The best
        negative RC is closer to zero than several earlier stages, but the
        unresolved restricted region still has a strongly negative dual bound.
        No certificate upgrade is justified; the next continuation point is the
        333-column probe.
30 instance001 V4 staged probe acceptance-audit integration:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_333/
    report parser fix:
        B4.1 Stage B probe-evidence parsing now accepts both:
            V2_latest_service_start_slot_bound
            V4_combined_endpoint_pair_latest_start_time_window
        V4 staged-resume probes are recorded as V4 diagnostic evidence rows,
        not as V2 harvesting coverage and not as certificate claims.
    acceptance snapshot:
        row_count = 138
        stage_counts = {A: 121, B: 7, C: 10}
        latest V4 staged evidence:
            active_column_count = 333
            active_columns_after_merge = 333
            columns_added = 3
            harvest_selected_count = 3
            harvest_selected_new_task_set_count = 2
            harvest_selected_replacement_task_set_count = 1
            compact_optimization_harvest_found_count = 3
            certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
            can_certify_no_negative = false
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 333-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_333_600s/
    result:
        resume active columns = 333
        active columns after merge = 336
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 2
        harvest_selected_replacement_task_set_count = 1
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 4.53e-07
        best true RC ~= -0.002404501
        worst selected true RC ~= -0.000054999
        compact dual bound ~= -0.002404048
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 597.61s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 206.30s
            rc ~= -0.002404501
        optimization_harvest_2 restricted exact negative:
            wall ~= 276.18s
            rc ~= -0.002403502
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit incumbent negative:
            wall ~= 107.21s
            rc ~= -0.000054999
            dual bound ~= -0.145109374
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 7.92s
            best RC = missing
            dual bound = missing
            forbidden_task_set_count = 3
    interpretation:
        the 333-column frontier still has harvestable negative columns, so
        30-scale is not closed. The third selected negative is now very shallow,
        but the preceding restricted region still has a strongly negative bound.
        This is evidence of tail thinning, not evidence of no-negative proof.
        Continue from the 336-column probe only with diagnostic scope unless a
        complete unrestricted true-dual no-negative proof is obtained.
30 instance001 V4 staged probe acceptance-audit after 336-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_336/
    acceptance snapshot:
        row_count = 139
        stage_counts = {A: 121, B: 8, C: 10}
        V4 staged evidence rows:
            row_count = 2
            negative_column_count = 6
            mean_active_column_count = 334.5
            mean_active_columns_after_merge = 334.5
            best_negative_rc ~= -0.002404501
            best_global_remaining_rc_lb ~= -0.002031064
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 336-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_336_600s/
    result:
        resume active columns = 336
        active columns after merge = 339
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        harvest_selected_new_task_set_count = 3
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 4.83e-07
        best true RC ~= -0.001103750
        worst selected true RC ~= -0.000870250
        compact dual bound ~= -0.001103634
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 596.74s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 203.59s
            rc ~= -0.001103750
        optimization_harvest_2 restricted exact negative:
            wall ~= 198.93s
            rc ~= -0.001103750
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted exact negative:
            wall ~= 166.61s
            rc ~= -0.000870250
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit no selected negative:
            wall ~= 27.61s
            incumbent RC ~= 0.000001
            dual bound ~= -0.219920841
            forbidden_task_set_count = 3
    interpretation:
        the 336-column frontier still produces three exact, audited, addable
        new-task-set negatives in one 600s stage. The negative RC values are
        shallow compared with earlier stages, but the fourth restricted region
        still has a strongly negative unresolved bound. This remains tail
        progress, not a no-negative certificate. The next continuation point is
        the 339-column probe.
30 instance001 V4 staged probe acceptance-audit after 339-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_339/
    acceptance snapshot:
        row_count = 140
        stage_counts = {A: 121, B: 9, C: 10}
        V4 staged evidence rows:
            row_count = 3
            negative_column_count = 9
            mean_active_column_count = 336.0
            mean_active_columns_after_merge = 336.0
            best_negative_rc ~= -0.002404501
            best_global_remaining_rc_lb ~= -0.001103634
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 339-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_339_600s/
    result:
        resume active columns = 339
        active columns after merge = 342
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        optimization exact negatives = 2
        optimization time-limit negatives = 1
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 3
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 3.86e-07
        best true RC ~= -0.005159500
        worst selected true RC ~= -0.005120500
        compact dual bound ~= -0.005159725
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 600.53s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    interpretation:
        the 339-column frontier still produces three audited, addable,
        new-task-set negatives. This is not monotone tail convergence: the
        best negative RC is deeper than the previous 336 -> 339 stage
        (-0.0051595 vs. -0.00110375). B4.1 therefore still has a hidden
        true-dual tail, and the next continuation point is the 342-column
        probe. No no-negative proof is available.
30 instance001 V4 staged probe acceptance-audit after 342-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_342/
    acceptance snapshot:
        row_count = 141
        stage_counts = {A: 121, B: 10, C: 10}
        V4 staged evidence rows:
            row_count = 4
            negative_column_count = 12
            mean_active_column_count = 337.5
            mean_active_columns_after_merge = 337.5
            best_negative_rc ~= -0.005159500
            best_global_remaining_rc_lb ~= -0.001103634
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 342-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_342_600s/
    result:
        resume active columns = 342
        active columns after merge = 345
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        optimization exact negatives = 2
        optimization time-limit negatives = 1
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 2
        harvest_selected_replacement_task_set_count = 1
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 4.36e-07
        best true RC ~= -0.000910522
        worst selected true RC ~= -0.000349261
        compact dual bound ~= -0.000910190
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 600.41s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    interpretation:
        the 342-column frontier still finds three audited, addable negatives,
        so no no-negative proof is available. Compared with the prior
        339 -> 342 stage, the best true RC became much shallower
        (-0.000910522 vs. -0.0051595) and the best frontier LB improved to
        about -0.000910190. This is useful tail progress, but replacement
        task-set evidence remains, and unsupported frontier regions still
        block certificate closure. The next continuation point is the
        345-column probe.
30 instance001 V4 staged probe acceptance-audit after 345-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_345/
    acceptance snapshot:
        row_count = 142
        stage_counts = {A: 121, B: 11, C: 10}
        V4 staged evidence rows:
            row_count = 5
            negative_column_count = 15
            mean_active_column_count = 339.0
            mean_active_columns_after_merge = 339.0
            best_negative_rc ~= -0.005159500
            best_global_remaining_rc_lb ~= -0.000910190
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 345-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_345_600s/
    result:
        resume active columns = 345
        active columns after merge = 348
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        optimization exact negatives = 3
        optimization time-limit negatives = 0
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 3
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 3.85e-07
        best true RC ~= -0.005443000
        worst selected true RC ~= -0.004638000
        compact dual bound ~= -0.005443385
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 596.76s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    interpretation:
        the 345-column frontier again finds three audited, addable,
        new-task-set exact negatives. The tail is not monotonically
        converging: latest best RC moved from about -0.000910522 back to
        -0.005443. This suggests the current staged harvest is still revealing
        hidden true-dual regions rather than exhausting them. The next
        continuation point is the 348-column probe.
30 instance001 V4 staged probe acceptance-audit after 348-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_348/
    acceptance snapshot:
        row_count = 143
        stage_counts = {A: 121, B: 12, C: 10}
        V4 staged evidence rows:
            row_count = 6
            negative_column_count = 18
            mean_active_column_count = 340.5
            mean_active_columns_after_merge = 340.5
            best_negative_rc ~= -0.005443000
            best_global_remaining_rc_lb ~= -0.000910190
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        latest frontier row:
            active columns after merge = 348
            latest negative RC ~= -0.005443000
            latest frontier LB ~= -0.005443385
            pricing proof kind = FRONTIER_BOUND_INCOMPLETE
            certificate scope = DIAGNOSTIC_PRICING_FRONTIER
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 348-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_348_600s/
    result:
        resume active columns = 348
        active columns after merge = 350
        added columns = 2
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 2
        compact_optimization_harvest_search_call_count = 3
        optimization exact negatives = 2
        optimization time-limit negatives = 0
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 1
        harvest_selected_replacement_task_set_count = 1
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 1.00e-07
        best true RC ~= -0.000930999
        worst selected true RC ~= -0.000011999
        compact dual bound ~= -0.000930899
        frontier coverage complete = false
        frontier unsupported region count = 2
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 582.39s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 212.74s
            rc ~= -0.000930999
        optimization_harvest_2 restricted exact negative:
            wall ~= 223.35s
            rc ~= -0.000011999
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit incomplete:
            wall ~= 146.29s
            incumbent RC ~= -0.000000999
            dual bound ~= -0.133267301
            forbidden_task_set_count = 2
    interpretation:
        the 348-column frontier shows a better tail signal than the prior
        oscillatory stage: only two audited, addable negatives are harvested,
        the latest best RC is shallow again, and unsupported frontier regions
        drop from 3 to 2. It still cannot certify no-negative because the
        third restricted region remains incomplete with a negative dual bound.
        The next continuation point is the 350-column probe.
30 instance001 V4 staged probe acceptance-audit after 350-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_350/
    acceptance snapshot:
        row_count = 144
        stage_counts = {A: 121, B: 13, C: 10}
        V4 staged evidence rows:
            row_count = 7
            negative_column_count = 20
            mean_active_column_count ~= 341.857143
            mean_active_columns_after_merge ~= 341.857143
            best_negative_rc ~= -0.005443000
            best_global_remaining_rc_lb ~= -0.000910190
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        latest frontier row:
            active columns after merge = 350
            latest negative RC ~= -0.000930999
            latest frontier LB ~= -0.000930899
            frontier unsupported region count = 2
            pricing proof kind = FRONTIER_BOUND_INCOMPLETE
            certificate scope = DIAGNOSTIC_PRICING_FRONTIER
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 350-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_350_600s/
    result:
        resume active columns = 350
        active columns after merge = 352
        added columns = 2
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 2
        compact_optimization_harvest_search_call_count = 3
        optimization exact negatives = 2
        optimization time-limit negatives = 0
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 2
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 4.48e-07
        best true RC ~= -0.001071001
        worst selected true RC ~= -0.000855001
        compact dual bound ~= -0.001071449
        frontier coverage complete = false
        frontier unsupported region count = 2
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 589.51s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 216.17s
            rc ~= -0.001071001
        optimization_harvest_2 restricted exact negative:
            wall ~= 251.93s
            rc ~= -0.000855001
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit incomplete:
            wall ~= 121.41s
            incumbent RC ~= -0.000000001
            dual bound ~= -0.146817541
            forbidden_task_set_count = 2
    interpretation:
        the 350-column frontier keeps the smaller tail shape from the previous
        stage: two audited, addable negatives and two unsupported regions. It
        still cannot certify no-negative because the third restricted region
        times out with a negative bound. The next continuation point is the
        352-column probe.
30 instance001 V4 staged probe acceptance-audit after 352-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_352/
    acceptance snapshot:
        row_count = 145
        stage_counts = {A: 121, B: 14, C: 10}
        V4 staged evidence rows:
            row_count = 8
            negative_column_count = 22
            mean_active_column_count = 343.125
            mean_active_columns_after_merge = 343.125
            best_negative_rc ~= -0.005443000
            best_global_remaining_rc_lb ~= -0.000910190
            can_certify_no_negative_count = 0
            diagnostic_claimed_certificate_count = 0
        latest frontier row:
            active columns after merge = 352
            latest negative RC ~= -0.001071001
            latest frontier LB ~= -0.001071449
            frontier unsupported region count = 2
            pricing proof kind = FRONTIER_BOUND_INCOMPLETE
            certificate scope = DIAGNOSTIC_PRICING_FRONTIER
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 352-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_352_600s/
    result:
        resume active columns = 352
        active columns after merge = 355
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        optimization exact negatives = 3
        optimization time-limit negatives = 0
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 3
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 2.14e-07
        best true RC ~= -0.004949500
        worst selected true RC ~= -0.004949499
        compact dual bound ~= -0.004949713
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 595.11s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 169.18s
            rc ~= -0.004949499
            dual bound ~= -0.004949713
        optimization_harvest_2 restricted exact negative:
            wall ~= 196.94s
            rc ~= -0.004949499
            dual bound ~= -0.004949691
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted exact negative:
            wall ~= 189.01s
            rc ~= -0.004949500
            dual bound ~= -0.004949527
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit incomplete:
            wall ~= 39.98s
            incumbent RC = 0.0
            dual bound ~= -0.189444409
            forbidden_task_set_count = 3
    interpretation:
        the 352-column continuation did not preserve the smaller two-region
        tail shape. It found three audited, addable new task-set negatives with
        a deeper best RC than the prior 350-column run and left three
        unsupported regions. This confirms the current 30-scale proof-tail is
        still oscillating: harvesting is improving the column pool, but it is
        not yet producing a monotone no-negative closure. The next continuation
        point is the 355-column probe.
30 instance001 V4 staged probe acceptance-audit after 355-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_355/
    acceptance snapshot:
        row_count = 146
        stage_counts = {A: 121, B: 15, C: 10}
        latest frontier row:
            active columns after merge = 355
            added columns = 3
            latest negative RC ~= -0.004949500
            latest frontier LB ~= -0.004949713
            frontier unsupported region count = 3
            pricing proof kind = FRONTIER_BOUND_INCOMPLETE
            certificate scope = DIAGNOSTIC_PRICING_FRONTIER
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 355-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_355_600s/
    result:
        resume active columns = 355
        active columns after merge = 358
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        optimization exact negatives = 3
        optimization time-limit negatives = 0
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 1
        harvest_selected_replacement_task_set_count = 2
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 4.75e-07
        best true RC ~= -0.002815000
        worst selected true RC ~= -0.000325000
        compact dual bound ~= -0.002814525
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 593.26s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 153.71s
            rc ~= -0.002815000
            dual bound ~= -0.002814525
        optimization_harvest_2 restricted exact negative:
            wall ~= 178.74s
            rc ~= -0.000702000
            dual bound ~= -0.000702202
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted exact negative:
            wall ~= 177.77s
            rc ~= -0.000325000
            dual bound ~= -0.000325192
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit incomplete:
            wall ~= 83.03s
            incumbent RC ~= -0.000000001
            dual bound ~= -0.128640991
            forbidden_task_set_count = 3
    interpretation:
        the 355-column continuation is a weaker tail than the prior 352-column
        step but still not a proof close. The best negative RC improved toward
        zero, yet only one selected column is a new task-set representative and
        two are replacement representatives. Unsupported regions remain at
        three, so the current bottleneck has shifted from pure task-set coverage
        toward representative quality plus restricted-region proof. The next
        continuation point is the 358-column probe.
30 instance001 V4 staged probe acceptance-audit after 358-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_358/
    acceptance snapshot:
        row_count = 147
        stage_counts = {A: 121, B: 16, C: 10}
        latest frontier row:
            active columns after merge = 358
            added columns = 3
            latest negative RC ~= -0.002815000
            latest frontier LB ~= -0.002814525
            frontier unsupported region count = 3
            pricing proof kind = FRONTIER_BOUND_INCOMPLETE
            certificate scope = DIAGNOSTIC_PRICING_FRONTIER
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
        requirement audit:
            R1_redlines_zero = pass
            R2_stage_a_regression_clean = pass
            R3_stage_b_matrix_complete = pass
            R4_stage_c_selected_diagnostic = pass
            R5_stage_bc_diagnostic_only = pass
            R6_tail_dual_worker_only = pass
            R7_30_scale_exact_closure = incomplete
30 instance001 V4 optimization-harvest task-set smoke after 358-column pool with 600s row:
    output:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/
    result:
        resume active columns = 358
        active columns after merge = 361
        added columns = 3
        compact_pricing_phase = optimization_harvest
        compact_optimization_harvest_target = 5
        compact_optimization_harvest_no_good_scope = task_set
        compact_optimization_harvest_found_count = 3
        compact_optimization_harvest_search_call_count = 4
        optimization exact negatives = 2
        optimization time-limit negatives = 1
        optimization time-limit no-negative/incomplete = 1
        harvest_selected_new_task_set_count = 3
        harvest_selected_replacement_task_set_count = 0
        harvest_rejected_duplicate_count = 0
        harvest_rejected_not_addable_count = 0
        harvest_addability_audit_pass = true
        harvest_pricing_rc_audit_pass = true
        harvest_pricing_rc_max_abs_diff ~= 3.61e-07
        best true RC ~= -0.007705961
        worst selected true RC ~= -0.000586000
        compact dual bound ~= -0.007706110
        frontier coverage complete = false
        frontier unsupported region count = 3
        pricing proof kind = FRONTIER_BOUND_INCOMPLETE
        final judge wall ~= 600.40s
        certificate scope = DIAGNOSTIC_PRICING_FRONTIER
    phase details:
        optimization_proof exact negative:
            wall ~= 186.71s
            rc ~= -0.007705961
            dual bound ~= -0.007706110
        optimization_harvest_2 restricted exact negative:
            wall ~= 229.83s
            rc ~= -0.002763549
            dual bound ~= -0.002763188
            forbidden_task_set_count = 1
        optimization_harvest_3 restricted time-limit negative:
            wall ~= 169.14s
            rc ~= -0.000586000
            dual bound ~= -0.121782748
            forbidden_task_set_count = 2
        optimization_harvest_4 restricted time-limit incomplete:
            wall ~= 14.72s
            incumbent RC ~= 0.169087764
            dual bound ~= -0.317649341
            forbidden_task_set_count = 3
    interpretation:
        the 358-column continuation exposed a deeper hidden tail rather than a
        monotone close. It added three new task-set columns, but the best RC
        worsened to about -0.007706 and the final two restricted regions hit
        time limits with substantially negative lower bounds. This is stronger
        evidence that plain staged harvesting is not enough by itself for
        30-scale closure. The next B4.1 step should shift from more linear
        harvesting to a targeted restricted-region proof strategy: analyze the
        task sets and resource patterns of these hidden negatives, compare
        V2/V4 formulation rows on those regions, and add proof-safe bounds that
        attack the time-limit restricted regions directly.
30 instance001 V4 staged probe acceptance-audit after 361-column frontier:
    output:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/
    restricted-region diagnostic:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/restricted_region_taskset_diagnostic.json
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/restricted_region_taskset_diagnostic_zh.md
        generated by:
            scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py
                --restricted-region-taskset-diagnostic
                --source-probe-json runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json
    targeted restricted-region proof probe:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe.json
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_zh.md
        generated by:
            scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py
                --targeted-restricted-region-proof-probe
                --targeted-region-variants V2_latest_service_start_slot_bound V4_current_strengthening
                --targeted-region-time-limit-sec 30
                --targeted-region-max-regions 1
                --source-probe-json runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json
        result:
            targeted region = prefix_2
            source phase = optimization_harvest_3
            source phase dual bound ~= -0.121782748
            V2 latest-start 30s:
                status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                best RC ~= 0.119161098
                dual bound ~= -0.571479122
                source-bound delta ~= -0.449696374
                certificate allowed = false
            V4 current strengthening 30s:
                status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                best RC ~= 0.030820431
                dual bound ~= -0.189663739
                source-bound delta ~= -0.067880991
                certificate allowed = false
            interpretation:
                both targeted rows remain diagnostic and time-limited. V4 current
                strengthening dominates V2 on this 30s targeted rerun, but neither
                improves the source restricted-region bound. This argues against
                simply switching the tail back to V2 and supports focusing next
                on proof-safe bounds that specifically lift prefix_2/prefix_3
                restricted-region lower bounds.
    targeted pair-time-window infeasible cut probe:
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_pair_tw_30s.json
        runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_pair_tw_30s_zh.md
        generated by:
            scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py
                --targeted-restricted-region-proof-probe
                --targeted-region-variants V4_current_strengthening
                --targeted-region-time-limit-sec 30
                --targeted-region-max-regions 1
                --targeted-region-basename targeted_restricted_region_probe_pair_tw_30s
                --source-probe-json runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json
        result:
            targeted region = prefix_2
            status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
            best RC ~= 0.012103490
            dual bound ~= -0.188384591
            source phase dual bound ~= -0.121782748
            source-bound delta ~= -0.066601843
            pair time-window infeasible pairs = 52
            pair time-window infeasible cut rows = 1092
            pair time-window infeasible margin range ~= [0.187471, 165.517145]
            certificate allowed = false
        interpretation:
            the new pair time-window infeasible cut is active and exact-safe as
            a compact-pricing formulation strengthening. It slightly improves
            the previous 30s V4 targeted bound (-0.189663739 -> -0.188384591),
            but it still does not recover the stronger source restricted-region
            bound and remains diagnostic-only. Keep it as an opt-in B4.1
            strengthening signal; do not promote it to a closure claim.
    targeted prefix_3 proof probe:
        implementation:
            add CLI filter:
                --targeted-region-id prefix_3
            add runner argument:
                target_region_ids
            behavior:
                only the requested restricted-region id is solved.
                unknown ids fail fast with the list of available regions.
                default behavior is unchanged when no id is supplied.
        artifacts:
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_30s.json
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_30s_zh.md
        generated by:
            scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py
                --targeted-restricted-region-proof-probe
                --targeted-region-variants V4_current_strengthening
                --targeted-region-id prefix_3
                --targeted-region-time-limit-sec 30
                --targeted-region-basename targeted_restricted_region_probe_prefix3_30s
                --source-probe-json runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json
        result:
            targeted region = prefix_3
            status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
            best RC ~= 0.073821628
            dual bound ~= -0.188226491
            source phase dual bound ~= -0.317649341
            source-bound delta ~= +0.129422850
            pair time-window infeasible cut rows = 1092
            certificate allowed = false
        interpretation:
            this is a real restricted-region proof-bound improvement over the
            source phase for prefix_3, but the row remains time-limited and
            diagnostic-only. It narrows the worst ledger bound substantially,
            without changing official certificate scope.
    compact final-judge env opt-in probe:
        command shape:
            call _run_compact_single_journey_pricing_final_judge directly on
            runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json
            with:
                LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4
                LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
                LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB=1
                LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB=1
                LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB=1
                LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS=1
                LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
                LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_INFEASIBLE_CUT=1
        result:
            status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
            pricing state = INCOMPLETE_LIMIT
            pricing proof kind = FRONTIER_BOUND_INCOMPLETE
            best RC ~= 0.007730392
            dual bound ~= -0.188741027
            pair energy infeasible cut rows = 777
            pair time-window infeasible pairs = 52
            pair time-window infeasible cut rows = 1092
            pair time-window infeasible margin range ~= [0.187471, 165.517145]
            can certify no negative = false
        interpretation:
            the pair time-window cut is now reachable from the official compact
            final-judge env opt-in path and is preserved in the top-level payload
            and optimization_proof phase payload. The 30s proof remains
            incomplete, so this is implementation validation only, not a new
            acceptance result.
    pair shadow lower-bound diagnostic:
        implementation:
            add opt-in compact pricing argument:
                pair_shadow_lb
            add env switch:
                LUNAR_ICE_COMPACT_PAIR_SHADOW_LB
            add B4.1 telemetry:
                pair_shadow_lb_enabled
                pair_shadow_lb_count
                pair_shadow_lb_exceeds_limit_count
        comparison on the same after_358 30-scale source dual, 30s each:
            without pair_shadow_lb:
                status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                best RC ~= 0.007730392
                dual bound ~= -0.188741027
                constraints = 69412
            with pair_shadow_lb:
                status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                best RC = null
                dual bound = null
                pair shadow lb rows = 9135
                constraints = 78547
        interpretation:
            pair_shadow_lb is exact-safe, but on this hard restricted-region
            probe it adds many rows and fails to produce a useful 30s bound.
            Keep it as an explicit diagnostic/env opt-in only. Do not include it
            in V4_current_strengthening or any accepted B4.1 default until a
            later measured run shows a real proof-tail benefit.
    pair time-window precedence diagnostic:
        implementation:
            add opt-in compact pricing argument:
                pair_time_window_precedence_cut
            add env switch:
                LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_PRECEDENCE_CUT
            add helper:
                pair_time_window_forced_precedence_pairs
            semantics:
                if task i before task j is impossible by full-graph shortest
                travel lower bounds and time windows, but j before i is still
                possible, then selecting both tasks in the same sortie forces
                j to precede i through MTZ order variables.
        direct final-judge probe on the after_358 30-scale source dual, 30s:
            enabled with:
                pair_time_window_infeasible_cut
                pair_time_window_precedence_cut
                pair_energy_infeasible_cut
                service/return/pair-duration/slot-position bounds
            result:
                status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                best RC ~= 0.056855588
                dual bound ~= -0.187750337
                forced precedence pairs = 383
                precedence cut rows = 8043
                constraints = 77455
                can certify no negative = false
        targeted restricted-region probe:
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_pair_tw_precedence_30s.json
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_pair_tw_precedence_30s_zh.md
            result:
                targeted region = prefix_2
                status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                best RC ~= 0.056855588
                dual bound ~= -0.188823874
                source phase dual bound ~= -0.121782748
                forced precedence pairs = 383
                precedence cut rows = 8043
                certificate allowed = false
        interpretation:
            the cut is exact-safe and gives a small direct final-judge bound
            improvement, but it does not improve the more relevant prefix_2
            restricted-region proof target versus the pair-time-window-only
            targeted run. Keep it as explicit diagnostic/env opt-in only; do
            not include it in V4_current_strengthening or accepted defaults yet.
    targeted pair weighted completion LB probe:
        implementation:
            add an opt-in compact pricing row:
                pair_weighted_completion_lb
            semantics:
                for a task pair served in one sortie, enforce a shortest-path
                lower bound on weighted service-start time relative to sortie
                start. This targets the normalized weighted-completion part of
                the official objective. It is a formulation strengthening row,
                not a master cut, and remains diagnostic opt-in.
        artifacts:
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_pair_weighted_completion_30s.json
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_pair_weighted_completion_30s_zh.md
        result:
            targeted region = prefix_3
            variant = V4_current_pair_weighted_completion_lb
            status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
            best RC ~= 0.068946588
            dual bound ~= -0.189944334
            source phase dual bound ~= -0.317649341
            pair weighted completion LB rows = 9135
            certificate allowed = false
        interpretation:
            the row is exact-safe and improves the prefix_3 source phase bound,
            but it is slightly worse than the existing prefix_3
            V4_current_strengthening targeted bound ~= -0.188226491. Keep it
            as an explicit diagnostic variant; do not promote it to default
            proof-tail formulation until it improves a relevant restricted
            region or reduces wall/proof rounds in a repeated probe.
    targeted triple time-window infeasible probe:
        implementation:
            add an opt-in compact pricing row:
                triple_time_window_infeasible_cut
            semantics:
                for a task triple, test all six within-sortie task orders under
                full-graph shortest-travel lower bounds and earliest-start
                scheduling. If every optimistic order violates a task time
                window or horizon return, add y_i + y_j + y_k <= 2 for the
                sortie slot. This is a formulation strengthening row, not a
                master cut, and remains diagnostic opt-in.
        artifacts:
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_triple_tw_30s.json
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_triple_tw_30s_zh.md
        result:
            targeted region = prefix_3
            variant = V4_current_triple_time_window_infeasible
            status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
            best RC ~= 0.098483078
            dual bound ~= -0.186524912
            source phase dual bound ~= -0.317649341
            pair time-window cut rows = 1092
            triple time-window cut rows = 210
            triple infeasible task triples = 10
            certificate allowed = false
        interpretation:
            this is the strongest prefix_3 restricted-region bound so far in
            the after_361 ledger, improving the previous targeted
            V4_current_strengthening bound from about -0.188226491 to about
            -0.186524912. It is a real proof-tail improvement but still
            time-limited and restricted, so it cannot certify no-negative.
        120s follow-up:
            artifacts:
                runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_triple_tw_120s.json
                runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_triple_tw_120s_with_column.json
                runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_triple_tw_120s_with_column_zh.md
            best bound observed:
                dual bound ~= -0.142071959
                pricing_state = FOUND_NEGATIVE
                best RC ~= -0.000016569
                certificate allowed = false
            targeted negative column telemetry:
                task count = 9
                task set =
                    ice_site_008, ice_site_009, ice_site_010,
                    ice_site_017, ice_site_018, ice_site_019,
                    ice_site_023, ice_site_024, ice_site_030
                forbidden seen = false
            interpretation:
                longer proof time lifts the restricted-region bound
                substantially, but it also finds a shallow true-dual negative
                column. This is not no-negative proof; the next operational
                step is to add this new task-set representative to the active
                pool, re-solve the RMP, and rerun the frontier proof.
        follow-up payload/merge:
            artifacts:
                runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_triple_tw_120s_payload.json
                runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/probe_after_targeted_prefix3_triple_tw_merge.json
            result:
                targeted row now carries targeted_negative_solution_payload
                targeted negative task count = 9
                targeted true RC ~= -0.000016569
                source active columns = 361
                active columns after merge = 362
                duplicate/signature already present = false
            interpretation:
                the restricted-region shallow negative is now a real resumable
                active-pool column, not just a task-set telemetry row.
        staged resume after targeted merge:
            artifact:
                runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_prefix3_triple_tw_merge_120s/
            config:
                initial resume probe =
                    runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/probe_after_targeted_prefix3_triple_tw_merge.json
                stage time limit = 120s
                final judge profile = V4
                phase mode = proof_only
                triple_time_window_infeasible_cut = true
            result:
                resume initial columns = 362
                active columns after stage = 363
                added columns = 1
                certificate scope = DIAGNOSTIC_PRICING_FRONTIER
                pricing state = INCOMPLETE_LIMIT
                final best RC ~= -0.000066000
                final dual bound ~= -0.171572967
                triple time-window cut rows = 27909
                no-negative certified = false
            interpretation:
                the merge path works and the next true-dual negative is still
                shallow, but the 30-scale proof-tail remains open. R7 is still
                incomplete; this row is evidence for continued frontier
                harvesting, not for certificate promotion.
        continued proof-only staged resume:
            same artifact:
                runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_prefix3_triple_tw_merge_120s/
            result:
                stage_002:
                    resume columns = 363
                    active columns after stage = 364
                    added columns = 1
                    final best RC ~= -0.000011001
                    final dual bound ~= -0.146458524
                    certificate scope = DIAGNOSTIC_PRICING_FRONTIER
                stage_003:
                    resume columns = 364
                    active columns after stage = 364
                    added columns = 0
                    final best RC ~= -0.000000001
                    final dual bound ~= -0.152085011
                    certificate scope = DIAGNOSTIC_PRICING_FRONTIER
            interpretation:
                optimization-proof mode reached a no-add stage, but the
                compact proof bound stayed negative. This does not certify
                no-negative; it means optimization proof alone is not strong
                enough to close the final judge.
        full-space feasibility proof follow-up:
            artifact:
                runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_prefix3_triple_tw_merge_feasibility_300s/
            config:
                initial resume probe =
                    runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_prefix3_triple_tw_merge_120s/stage_003/probe.json
                phase mode = feasibility_proof_only
                stage time limit = 300s
                triple_time_window_infeasible_cut = true
            result:
                stage_001:
                    resume columns = 364
                    active columns after stage = 365
                    added columns = 1
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                    best RC ~= -0.000273333
                    dual bound ~= -0.015139443
                    full-space feasibility proof can certify = false
                stage_002:
                    resume columns = 365
                    active columns after stage = 366
                    added columns = 1
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_OPTIMAL
                    best RC ~= -0.003694900
                    dual bound ~= -0.003694500
                    full-space feasibility proof can certify = false
                stage_003:
                    resume columns = 366
                    active columns after stage = 366
                    added columns = 0
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
                    best RC = none
                    dual bound ~= -0.076163596
                    full-space feasibility proof can certify = false
                stage_004:
                    resume columns = 366
                    active columns after stage = 367
                    added columns = 1
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_OPTIMAL
                    best RC ~= -0.000587555
                    dual bound ~= -0.000587406
                    full-space feasibility proof can certify = false
                stage_005:
                    resume columns = 367
                    active columns after stage = 368
                    added columns = 1
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_OPTIMAL
                    best RC ~= -0.001287668
                    dual bound ~= -0.001287427
                    full-space feasibility proof can certify = false
                stage_006:
                    resume columns = 368
                    active columns after stage = 369
                    added columns = 1
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_OPTIMAL
                    best RC ~= -0.000002000
                    dual bound ~= -0.000001748
                    full-space feasibility proof can certify = false
                stage_007:
                    resume columns = 369
                    active columns after stage = 369
                    added columns = 0
                    final phase = negative_feasibility_proof
                    status = COMPACT_HIGHS_PRICING_OPTIMAL
                    best RC ~= -0.000001000
                    dual bound ~= -0.000001382
                    full-space feasibility proof can certify = false
            interpretation:
                the tail is not merely proof-incomplete. A full-space
                feasibility proof can still reveal hidden negative columns
                after optimization-proof mode reports no addable column under
                the same active pool. B4.1 should promote feasibility-proof
                replay as the next 30-scale tail worker, while preserving the
                rule that only infeasible full-space feasibility proof may
                certify no-negative. Stage_003 also shows that a no-column
                time-limit row is not enough: longer follow-up found more
                exact negative columns in stages 004 and 005. Stage_007 then
                exposed an epsilon-boundary stall: an exact optimal feasibility
                solve found a feasible column around the official negative_eps
                boundary, but it could not certify no-negative.
        epsilon-band merge and official-eps closure follow-up:
            artifacts:
                runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_prefix3_triple_tw_merge_feasibility_300s/stage_007_epsilon_band_replay.json
                runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_prefix3_triple_tw_merge_feasibility_300s/probe_after_stage007_epsilon_band_merge.json
                runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/
            diagnostic replay:
                replay negative_eps = 1e-7
                official certificate epsilon remains unchanged
                exact status = EXACT_PRICING_OPTIMAL
                best RC ~= -0.000001000
                dual bound ~= -0.000001382
                active columns after epsilon-band merge = 370
                purpose = add a feasible boundary column to stabilize the RMP;
                          not a no-negative certificate
            official eps staged follow-up:
                stage_001:
                    resume columns = 370
                    active columns after stage = 371
                    added columns = 1
                    status = COMPACT_HIGHS_PRICING_OPTIMAL
                    best RC ~= -0.000743417
                    dual bound ~= -0.000743749
                    certificate scope = DIAGNOSTIC_PRICING_FRONTIER
                stage_002:
                    resume columns = 371
                    active columns after stage = 371
                    added columns = 0
                    status = COMPACT_HIGHS_PRICING_INFEASIBLE_NO_NEGATIVE
                    exact status = EXACT_NEGATIVE_FEASIBILITY_INFEASIBLE
                    pricing state = CERTIFIED_NO_NEGATIVE
                    underlying certificate scope = BPC_NODE_LP_CERTIFIED
                    pricing proof kind = EXHAUSTIVE_NO_NEGATIVE
                    full-space feasibility proof can certify = true
            interpretation:
                this is the first 30-scale instance001 root final-judge closure
                under B4.1. It proves no negative reduced-cost root-pricing
                column remains for the active 371-column RMP dual. It does not
                prove BPC_TREE_OPTIMAL, so R7 remains incomplete, but the
                proof-tail bottleneck has moved from root no-negative closure
                to integrating this closure into the tree-level exact solve.
    targeted quad time-window infeasible probe:
        implementation:
            add an opt-in compact pricing row:
                quad_time_window_infeasible_cut
            semantics:
                for a task quad, test all 24 within-sortie task orders under
                full-graph shortest-travel lower bounds and earliest-start
                scheduling. If every optimistic order violates a task time
                window or horizon return, add sum(y_i) <= 3 for the sortie slot.
                This is diagnostic formulation strengthening only.
        artifacts:
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_quad_tw_30s.json
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/targeted_restricted_region_probe_prefix3_quad_tw_30s_zh.md
        result:
            targeted region = prefix_3
            variant = V4_current_quad_time_window_infeasible
            status = COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED
            best RC ~= 0.012631215
            dual bound ~= -0.191022613
            source phase dual bound ~= -0.317649341
            pair time-window cut rows = 1092
            triple time-window cut rows = 210
            quad time-window cut rows = 252
            quad infeasible task quads = 12
            certificate allowed = false
        interpretation:
            quad time-window rows are exact-safe but too heavy/weak in the 30s
            prefix_3 probe: they improved the source phase but lost against the
            triple-only targeted bound ~= -0.186524912. Keep them as explicit
            diagnostic evidence only; do not promote to recommended B4.1 route.
    restricted-region bound ledger:
        implementation:
            add diagnostic-only builder/writer:
                build_b4_1_restricted_region_bound_ledger
                write_b4_1_restricted_region_bound_ledger
            add CLI switches:
                --restricted-region-bound-ledger
                --restricted-region-bound-ledger-basename
                --targeted-region-result-json
        artifacts:
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/restricted_region_bound_ledger.json
            runs/b4_1_true_dual_proof_tail_acceptance_audit_after_361/restricted_region_bound_ledger_zh.md
        semantics:
            the ledger selects the strongest known restricted-region lower bound
            per prefix region from already-computed source phase payloads and
            optional targeted restricted/no-good probe rows.
            It is diagnostic-only:
                pricing_proof_kind = FRONTIER_BOUND_INCOMPLETE
                certificate_allowed = false
                frontier_lb_official = false
                can_claim_certificate = false
        after_361 result:
            region_count = 3
            selected_bound_sources = {source_phase: 2, targeted_probe: 1}
            source_bound_reuse_count = 2
            targeted_bound_improvement_count = 1
            best known bounds:
                prefix_1 source_phase ~= -0.002763188
                prefix_2 source_phase ~= -0.121782748
                prefix_3 targeted_probe ~= -0.188226491
            targeted prefix_2 pair-time-window bound ~= -0.188384591
            targeted prefix_2 precedence bound ~= -0.188823874
            targeted prefix_3 V4_current_strengthening bound ~= -0.188226491
            targeted prefix_3 pair-weighted-completion bound ~= -0.189944334
            targeted prefix_3 triple-time-window 30s bound ~= -0.186524912
            targeted prefix_3 triple-time-window 120s bound ~= -0.142071959
            targeted prefix_3 quad-time-window bound ~= -0.191022613
            best known global remaining RC LB ~= -0.142071959
        interpretation:
            targeted reruns are region-sensitive: prefix_2 did not beat the
            source phase, while prefix_3 improved the source phase lower bound
            from about -0.31765 to about -0.14207. The ledger preserves the
            best known bound per region for trend tracking while keeping
            certificate scope closed. The next useful work is to attack the
            remaining shallow negative column directly, not unsupported
            certificate promotion.
    acceptance snapshot:
        row_count = 149
        stage_counts = {A: 121, B: 18, C: 10}
        latest frontier row:
            active columns after merge = 371
            latest controlled feasibility stage added columns = 0
            latest negative RC = none
            latest controlled-stage frontier LB = none
            underlying proof kind = EXHAUSTIVE_NO_NEGATIVE
            underlying certificate scope = BPC_NODE_LP_CERTIFIED
            certificate scope in B4.1 diagnostic report = DIAGNOSTIC_PRICING_FRONTIER
        redlines:
            certificate_leak_count = 0
            diagnostic_claimed_certificate_count = 0
            manual_rc_fail_count = 0
            pricing_rc_fail_count = 0
            tail_dual_certificate_leak_count = 0
    requirement audit:
        R1_redlines_zero = pass
        R2_stage_a_regression_clean = pass
        R3_stage_b_matrix_complete = pass
        R4_stage_c_selected_diagnostic = pass
        R5_stage_bc_diagnostic_only = pass
        R6_tail_dual_worker_only = pass
        R7_30_scale_exact_closure = incomplete
```

Tree-closure handoff from the 371-column root proof:

```text
runs/b4_1_true_dual_proof_tail_tree_closure_from_371/
    source:
        runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json
    method:
        B3 tree was warm-started from the saved 371 active columns.
        Direct DP was intentionally not rerun or used as a BPC certificate.
        The root RMP and true-dual compact final judge were rerun under the
        normal B3 tree gate.
    result:
        algorithm_status = BPC_OPTIMAL
        certificate_scope = BPC_TREE_OPTIMAL
        exact_status = BPC_TREE_OPTIMAL
        pricing_state = CERTIFIED_NO_NEGATIVE
        tree_closed = true
        node_count = 1
        root_node_status = INTEGER_INCUMBENT
        root_integral = true
        global_lower_bound = 1.487678
        incumbent_objective = 1.487678
        global_gap = 0.0
        tree_certificate_gate_issues = []
    root final judge:
        status = COMPACT_HIGHS_PRICING_INFEASIBLE_NO_NEGATIVE
        exact_status = EXACT_NEGATIVE_FEASIBILITY_INFEASIBLE
        pricing_proof_kind = EXHAUSTIVE_NO_NEGATIVE
        can_certify_no_negative = true
        negative_feasibility_full_space_proof_can_certify = true
        frontier_unsupported_region_count = 0
    interpretation:
        30-scale instance001 is now closed as a formal BPC_TREE_OPTIMAL
        certificate under the normalized additive objective. This is the first
        30-scale exact BPC tree closure evidence for B4.1; it does not imply
        all 30-scale instances are closed.
```

Accepted B4.1 audit with tree closure:

```text
runs/b4_1_true_dual_proof_tail_acceptance_audit_with_tree_closure/
    row_count = 150
    stage_counts = {A: 121, B: 18, C: 10, D: 1}
    redlines:
        certificate_leak_count = 0
        diagnostic_claimed_certificate_count = 0
        exception_fail_closed_count = 0
        manual_rc_fail_count = 0
        pricing_rc_fail_count = 0
        resource_guard_stopped_count = 0
        stage_a_tree_closure_miss_count = 0
        tail_dual_certificate_leak_count = 0
    requirement audit:
        R1_redlines_zero = pass
        R2_stage_a_regression_clean = pass
        R3_stage_b_matrix_complete = pass
        R4_stage_c_selected_diagnostic = pass
        R5_stage_bc_diagnostic_only = pass
        R6_tail_dual_worker_only = pass
        R7_30_scale_exact_closure = pass
```

Current code verification:

```text
git diff --check: pass
PYTHONPATH=src python -m compileall -q src scripts tests: pass
PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests:
    179 tests OK
```
