<!--
Lunar-GAT-BPC-Exact 可消融 baseline 递增路线文档。
原则：每一层都是一个可运行 candidate baseline；只有在真实 5/10/20/30 规模消融中优于当前 best accepted baseline，才可晋级。
-->
# 05_B4_Cut_Formulation_Layer

## 0. 定位

B4 是一个独立可消融候选层：

```text
B4 = best_accepted_baseline + mathematically valid cuts / formulation strengthening
```

B4 不应该被 B2 或 B3 带偏。若 B2/B3 未被接受，B4 的比较对象必须回退到当前 best accepted baseline。B4 的核心是：

```text
用有效不等式或 formulation strengthening 提高 LP lower bound / 减少 branch tree / 减少 proof tail。
```

B4 不使用 GAT 决定 cut validity。

---

## 1. B4 核心目标

B4 must improve at least one of:

```text
1. root LP bound
2. branch-node LP bound
3. root gap
4. tree node count
5. certificate time
6. BPC_TREE_OPTIMAL_count
7. fail-closed classification of lower-bound-stuck cases
```

B4 must not:

```text
change objective
weaken certificate scope
use invalid / unproved cuts
enable fleet lower-bound cut without proof
hide pricing / reduced-cost inconsistency
```

---

## 2. Cut rollout modes

### 2.1 B4A_cut_diagnostic_only

Default first mode.

```text
generate candidate cuts
compute coefficient on current columns
compute violation
compute would-bind / would-dual diagnostics
do not add rows to RMP
do not change pricing
do not change certificate
```

### 2.2 B4B_subset_row_live_opt_in

Only after B4A diagnostics and tests pass.

Live cut candidate:

```text
subset-row cut
```

Required before live:

```text
integer validity proof
RMP coefficient implementation
pricing coefficient implementation
manual RC == pricing RC
cut dual sign audit
CutContextVersion
CutCoefficientVector
CutDominanceCompatibilityReport
completion-bound fail-closed under active cuts
```

### 2.3 B4C_formulation_probe

Diagnostic-only for route/resource/order formulations.

```text
route-resource rows
sortie-count rows
resource-profile rows
route-order partitions
```

No live use until coefficient / dominance / pricing support is proved.

---

## 3. Fleet lower-bound cut policy

Hard rule:

```text
fleet lower-bound cut remains diagnostic-only until explicit proof.
```

Reason:

```text
A journey column represents one rover multi-sortie schedule.
Vehicle count, journey count, route count, and sortie count are not the same.
```

Do not import ordinary CVRP fleet lower-bound intuition without proof.

---

## 4. Cut context and dominance

Any live cut must define:

```text
cut_kind
cut_key
rhs
sense
coefficient(column)
coefficient_vector_hash
pricing_supported
completion_bound_supported
dominance_compatible
```

If a cut coefficient depends only on task set:

```text
task-set dominance may still be unsafe if other active constraints depend on route/resource/timing.
```

If coefficient depends on route/order/resource/time:

```text
task-set dominance must remain disabled unless dominance key includes that coefficient.
```

ColumnSemanticSignature / dominance key must include:

```text
task_set
route_order_signature
path_option_signature
timing_signature
resource_profile_signature
branch_signature
cut_coefficient_vector_hash
```

---

## 5. B4 implementation modules

```text
exact/bpc/cuts/subset_row.py
exact/bpc/cuts/cut_context.py
exact/bpc/cuts/cut_audit.py
exact/bpc/cuts/coefficient_audit.py
exact/bpc/cuts/dominance_compatibility.py
exact/bpc/solver/cut_formulation_solver.py
runners/b4_cut_formulation_ablation.py
```

---

## 6. B4 消融实验设计

Compare B4 to current best accepted baseline, not blindly to B3 if B3 was not accepted.

### 6.1 5-scale full

Run all 20:

```text
previous_best_baseline
B4A_cut_diagnostic_only
B4B_subset_row_live_opt_in
```

Required:

```text
no objective mismatch
no certificate regression
manual RC == pricing RC with cuts
no wall-time blowup unless explained
```

If no cuts violated on 5-scale, B4 can still pass diagnostics but not claim performance improvement.

### 6.2 10-scale selected then full

Run selected 5 first; full 20 if stable.

Metrics:

```text
root_lp_bound
root_gap
BPC_NODE_LP_CERTIFIED_count
BPC_TREE_OPTIMAL_count if tree baseline exists
node_count
certificate_time
cut_candidate_count
cut_violated_count
active_cut_count
cut_dual_nonzero_count
```

B4 should improve lower bound or reduce work.

### 6.3 20-scale

Run:

```text
20 fail-closed guard
20 selected hard/plateau probe
20 selected direct20 probe if relevant
```

Select instances where previous baseline shows:

```text
root gap > 0
LP bound plateau
branch tree incomplete
pricing closes but bound too weak
```

B4 success on 20 may be diagnostic if live cut not yet safe, but report must show whether bound moved.

### 6.4 30-scale

Diagnostic only unless 20 is stable.

Required:

```text
no certificate leak
cut diagnostics present
clear fail-closed reason
```

---

## 7. Required output fields

```text
scale
instance_id
mode
previous_baseline_mode
cut_mode
algorithm_status
certificate_scope
uses_true_dual_bpc_certificate
objective
previous_root_lp_bound
candidate_root_lp_bound
root_lp_bound_delta
previous_gap
candidate_gap
gap_delta
node_count_delta
certificate_time_delta
cut_candidate_count
cut_violated_count
cut_added_count
active_cut_count
cut_dual_nonzero_count
manual_rc_with_cuts_audit_pass
pricing_rc_with_cuts_audit_pass
cut_coefficient_audit_pass
cut_dominance_compatibility_pass
completion_bound_failed_closed_with_cuts
fleet_lower_bound_live_enabled
certificate_scope_regression
wall_time
fail_closed_reason
```

---

## 8. B4 pass / fail rules

### Hard redlines

```text
objective_mismatch_count = 0
certificate_scope_regression_count = 0
manual_rc_with_cuts_fail_count = 0
pricing_rc_with_cuts_fail_count = 0
cut_coefficient_audit_fail_count = 0
fleet_lower_bound_live_enabled = 0 unless proof flag exists
completion_bound_unsafe_with_cuts = 0
```

### Improvement requirement

B4 is accepted only if it improves over the previous accepted baseline on real 5/10/20/30 ablation:

```text
root_lp_bound increases
or gap decreases
or node_count decreases
or certificate_time decreases
or BPC_TREE_OPTIMAL_count increases
or lower-bound-stuck cases get clearer diagnostic classification
```

A row count of cuts is not improvement.

If:

```text
cut_added_count > 0
but root_lp_bound_delta = 0
and node_count_delta = 0
and certificate_time_delta >= 0
```

then B4 is not accepted as optimization.

---

## 9. Report requirements

Produce:

```text
runs/b4_cut_formulation_ablation/b4_cut_rows.csv
runs/b4_cut_formulation_ablation/b4_cut_summary.json
runs/b4_cut_formulation_ablation/b4_cut_report_zh.md
```

Markdown sections:

```text
1. Previous accepted baseline
2. Cut modes
3. Validity and RC audits
4. 5/10/20/30 matrix
5. Bound movement table
6. Node/workload movement table
7. Cut diagnostics
8. Live cut safety
9. B4 accepted? yes/no
10. If no, next cut/formulation target
```

---

## 10. Exit statement

B4 is accepted only if a mathematically valid cut/formulation layer measurably improves lower bound, tree closure, or certificate workload over the previous accepted baseline on real instances.

B4 is not accepted for merely adding cuts.
