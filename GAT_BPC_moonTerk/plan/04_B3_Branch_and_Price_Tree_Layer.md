<!--
Lunar-GAT-BPC-Exact 可消融 baseline 递增路线文档。
原则：每一层都是一个可运行 candidate baseline；只有在真实 5/10/20/30 规模消融中优于当前 best accepted baseline，才可晋级。
-->
# 04_B3_Branch_and_Price_Tree_Layer

## 0. 定位

B3 是一个独立的可消融候选层：

```text
B3 = best_accepted_baseline + branch-and-price tree
```

B3 不等于“无条件接在 B2 后面”。如果 B2 没有被接受，B3 的比较对象应回退到当前 best accepted baseline，而不是被 B2 带偏。

B3 的核心任务：

```text
将 root LP certificate / root gap 转化为 integer proof。
```

B3 只解决：

```text
LP fractional -> branch tree -> BPC_TREE_OPTIMAL or clear fail-closed status
```

B3 不解决：

```text
root pricing-tail 太慢
cut/formulation lower-bound weak
GAT ordering
route-order branch
live cuts
```

---

## 1. Entry gate

B3 可以开始 implementation scaffold，但不能被接受为 baseline，除非满足：

```text
1. B1 root proof semantics redlines pass.
2. B2 either:
   a. accepted as pricing-tail improvement, or
   b. explicitly not accepted and best_accepted_baseline is reset to B1.
3. There is at least one real or controlled instance where root LP is fractional or tree closure is required.
4. Direct-DP/BPC objective alignment remains valid on 5-scale.
```

If all real 5-scale roots are integral, B3 must include a controlled fractional fixture plus 10/20 real diagnostics. It cannot claim performance improvement solely on a fixture.

---

## 2. B3 核心目标

B3 must improve over the previous accepted baseline in one of these ways:

```text
1. Convert BPC_NODE_LP_CERTIFIED + fractional root into BPC_TREE_OPTIMAL.
2. Close branch nodes that previous baseline left incomplete.
3. Reduce integer optimality gap by valid branch-and-bound.
4. Provide clearer branch-incomplete classification without certificate leakage.
```

B3 must not:

```text
change root objective
weaken B1/B2 certificate scope
use direct-DP optimum as BPC proof
use GAT branch score
enable cuts
enable route-order branch by default
```

---

## 3. B3 子模式

### 3.1 B3A_full_universe_tree_audit

Purpose:

```text
Verify branch-context semantics with a full fixed-graph column universe.
```

Allowed:

```text
preload full universe per node for audit
check same/different_journey filters
verify branch children partition fractional solution
verify no branch-infeasible column enters node RMP
```

Not allowed:

```text
use this as scalable performance claim
claim BPC tree scalability from full-universe preload
```

### 3.2 B3B_seeded_branch_price_tree

Main B3 candidate.

Use:

```text
seeded root columns
B2-style addability-aware pricing-tail if B2 accepted;
otherwise B1 seeded-CG plus required minimal addability checks
```

This is the real branch-and-price tree path.

### 3.3 B3C_branch_diagnostic_only

For 20/30 if tree closure is not feasible:

```text
run root/first-child branch probe
report branch pair
child RMP status
child pricing status
fail-closed reason
no certificate upgrade
```

---

## 4. Required modules

```text
exact/bpc/branching/ryan_foster.py
exact/bpc/branching/branch_selector.py
exact/bpc/branching/branch_fallback.py
exact/bpc/branching/branch_context.py
exact/bpc/solver/node_solver.py
exact/bpc/solver/tree_solver.py
exact/bpc/solver/incumbent.py
exact/bpc/solver/tree_ledger.py
runners/b3_branch_price_ablation.py
```

---

## 5. Branch semantics

First live branch type:

```text
same_journey(i, j)
different_journey(i, j)
```

Formula:

```text
same_mass(i,j) = sum_p lambda_p * 1[i in S_p and j in S_p]
```

Branch candidate is fractional if:

```text
eps < same_mass(i,j) < 1 - eps
```

Hard tests:

```text
test_same_mass_matches_primal_solution
test_same_child_allows_only_columns_with_both_or_neither_together
test_different_child_forbids_columns_with_both_tasks
test_child_contexts_partition_parent_fractional_mass
```

---

## 6. Branch completeness fallback

Hard rule:

```text
NO_FRACTIONAL_RF_PAIR != NODE_INTEGRAL
```

Fallback order:

```text
1. Ryan-Foster same/different journey pair.
2. route / journey signature family branch.
3. exact column-signature forbid branch.
4. aggregation certificate proving representative-level fractionality harmless.
```

First implementation should avoid strong `lambda_p = 1` branch unless pricing can enforce it. Preferred fallback:

```text
forbid exact ColumnSemanticSignature
```

Because it is pricing-compatible if signature matching is exact and audited.

---

## 7. Node solver requirements

Each node must have:

```text
node_id
parent_node_id
depth
branch_context
inherited_column_pool_id
current_master_view_id
incumbent_at_entry
node_lp_bound
node_lp_bound_official
pricing_state
certificate_scope
proof_debt_state
child_generation_reason
node_status
```

Node statuses:

```text
NODE_LP_CERTIFIED
INTEGER_INCUMBENT
PRUNED_BY_BOUND
BRANCHED
INCOMPLETE_LIMIT
NO_FRACTIONAL_RF_PAIR_UNRESOLVED
NODE_RMP_INFEASIBLE_UNCERTIFIED
BPC_INFEASIBLE_CERTIFIED
```

Restricted pool no cover must never become infeasibility certificate.

---

## 8. B3 消融实验设计

Every B3 result must compare to previous best accepted baseline.

### 8.1 5-scale full

Run all 20 real instances:

```text
previous_best_baseline
B3A_full_universe_tree_audit
B3B_seeded_branch_price_tree
```

Expected:

```text
No certificate regression.
If previous root was integral, B3 should match previous result and report no branch needed.
If fractional root exists, B3 should either close tree or report precise incomplete reason.
```

### 8.2 10-scale selected then full

Run selected 5 first. Then full 20 if feasible.

Metrics:

```text
BPC_TREE_OPTIMAL_count
BPC_NODE_LP_CERTIFIED_count
integer_incumbent_count
open_node_count
incomplete_node_count
node_count
tree_depth
branch_count
mean wall
p90 wall
```

B3 must improve at least one:

```text
BPC_TREE_OPTIMAL_count
integer gap
open node count
certificate explanation quality
```

without proof regression.

### 8.3 20-scale

Run both:

```text
20 fail-closed guard
20 selected branch-tree probe
```

Selected probe modes:

```text
B0_pure_direct_dp
previous_best_baseline
B3A_full_universe_tree_audit
B3B_seeded_branch_price_tree
```

Purpose:

```text
If B0 direct-DP solves but previous baseline only has root LP / incomplete, B3 should show whether branch tree is the next bottleneck or root pricing remains the bottleneck.
```

### 8.4 30-scale

Diagnostic only unless 20 is stable:

```text
no certificate leak
root/child branch diagnostics
clear fail-closed reason
```

---

## 9. Required output fields

```text
scale
instance_id
mode
previous_baseline_mode
algorithm_status
certificate_scope
tree_certificate_scope
uses_true_dual_bpc_certificate
BPC_TREE_OPTIMAL
BPC_NODE_LP_CERTIFIED_count
node_count
open_node_count
closed_node_count
pruned_by_bound_count
branched_node_count
incomplete_node_count
max_depth_reached
branch_count
selected_branch_pair
selected_branch_source
no_fractional_rf_pair_count
no_fractional_rf_pair_treated_as_integral
fallback_branch_count
column_signature_branch_count
node_rmp_infeasible_uncertified_count
BPC_infeasible_certified_count
incumbent_objective
global_lower_bound
global_gap
direct_dp_objective
bpc_tree_objective_matches_direct_dp
manual_rc_audit_pass
pricing_rc_audit_pass
proof_debt_unreleased_count
wall_time
fail_closed_reason
```

---

## 10. B3 pass / fail rules

### Hard redlines

```text
no_fractional_rf_pair_treated_as_integral = 0
certificate_scope_regression_count = 0
objective_mismatch_count = 0
manual_rc_fail_count = 0
pricing_rc_fail_count = 0
proof_debt_unreleased_count = 0 for certified rows
direct_dp_used_as_bpc_tree_certificate = 0
```

### Improvement requirement

B3 is accepted only if on real 5/10/20/30 ablation it improves over previous accepted baseline in at least one meaningful metric:

```text
BPC_TREE_OPTIMAL_count increases
or integer gap decreases
or open_node_count decreases
or node closure classification improves without wall-time blowup
```

If B3 only adds tree scaffolding but no real improvement:

```text
B3 remains diagnostic.
Do not enter B4 as an accepted next layer.
```

---

## 11. Report requirements

Produce:

```text
runs/b3_branch_price_ablation/b3_branch_price_rows.csv
runs/b3_branch_price_ablation/b3_branch_price_summary.json
runs/b3_branch_price_ablation/b3_branch_price_report_zh.md
```

Markdown sections:

```text
1. Accepted previous baseline used
2. B3 modes
3. Redlines
4. 5/10/20/30 matrix
5. Branch completeness audit
6. NO_FRACTIONAL_RF_PAIR audit
7. Node ledger summary
8. Direct-DP/BPC tree objective alignment
9. B3 accepted? yes/no
10. If no, next bottleneck
```

---

## 12. Exit statement

B3 is not accepted because a tree solver exists. It is accepted only if:

```text
it proves integer optimality or improves valid branch-and-price closure behavior
over the previous accepted baseline on real 5/10/20/30 instances.
```
