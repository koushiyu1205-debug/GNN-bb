<!--
Lunar-GAT-BPC-Exact 可消融 baseline 递增路线文档。
原则：每一层都是一个可运行 candidate baseline；只有在真实 5/10/20/30 规模消融中优于当前 best accepted baseline，才可晋级。
-->
# 03_B2_Pricing_Tail_Optimization_Layer

## 0. 定位

B2 不是“沿着 B1 继续堆代码”，而是一个可消融的候选层：

```text
B2 = best_accepted_baseline + root pricing-tail / addability / duplicate / hidden-negative 优化
```

当前 best accepted baseline 至少包括：

```text
B0: fixed-graph direct-DP oracle
B1: root-only true-dual BPC proof core
```

但 B1 当前只在 5-scale 证明了完整 proof-safe root closure；10-scale selected rows 已经暴露 row timeout；20/30 当前主要用于 fail-closed 和 selected direct probe。B2 的任务不是假设 B1 已经在 10/20 成功，而是要回答：

```text
在同一批真实实例上，B2 是否比 B1 更能把 root CG / final judge / addability tail 推向 closure？
```

B2 不启用：

```text
branch tree
cuts / formulation
GAT guidance
route-order branch
complex tail scheduler
```

B2 只优化 root node pricing-tail。它不能改变证书语义。

---

## 1. B2 核心目标

B2 要解决 B1 暴露出的 root pricing-tail 问题：

```text
1. B1A full-universe audit 可以验证证书边界，但不代表 seeded CG 能工作。
2. B1B seeded-root-CG 在 5-scale 能 add columns 并闭合，但在 10-scale selected rows 超时。
3. 20-scale direct20 需要同组 B0/B1A/B1B/B2 对照，不能再把 fail-closed guard 误读成 B0 失败。
4. Final judge 找到 negative columns 后，必须先过 addability，不能把 duplicate / forbidden / in-pool-not-master / current-master-duplicate 当成有效 harvest。
5. DUPLICATE_ONLY 必须触发 RMP-membership / manual-RC / pricing-RC / signature-coefficient audit，不能静默通过。
```

B2 的真实优化目标是：

```text
B2 should reduce root pricing closure workload or improve root closure rate
relative to B1 on the same real instances, under the same certificate semantics.
```

---

## 2. 与 B1 的关系

B2 比较对象不是“理论上的 B1”，而是当前 best accepted baseline 中的 B1 配置：

```text
B1A_full_universe_root_audit:
    full fixed-graph direct universe is preloaded.
    Purpose: root LP / dual / certificate audit.

B1B_seeded_root_CG:
    initial columns = direct-DP incumbent journeys + singleton/canonical seed columns.
    Purpose: actual column generation from a non-full seed pool.
```

B2 应主要对比 B1B，因为 B2 的价值在于：

```text
seeded pool -> true-dual final judge -> addable negative columns -> RMP progress -> closure
```

B2 不应默认预装 full universe。若需要使用 full universe，只能用于 B2A audit fast path，不能混入 B2B seeded-CG 性能结论。

---

## 3. B2 子模式

### 3.1 B2A_full_universe_rc_audit_fast_path

目标：避免在 full universe 已经预装时重复 label-pricing 枚举。

使用条件必须同时满足：

```text
full_universe_preloaded = true
full_universe_complete = true
path_option_dominance_policy matches certificate scope
RMP dual vector bound to current RMP
all columns in full universe are in MasterColumnView
manual RC audit over all full-universe columns complete
min_manual_rc >= -eps
ProofDebtQueue empty
```

允许结论：

```text
BPC_NODE_LP_CERTIFIED for fixed-graph root LP
```

禁止：

```text
BPC_TREE_OPTIMAL
BPC_INFEASIBLE_CERTIFIED
any claim beyond fixed-graph root LP
```

目的：

```text
减少 B1A full-universe audit 的重复 final-judge 枚举成本。
```

### 3.2 B2B_seeded_tail_CG

这是 B2 的主模式。

起点：

```text
initial_columns = B0 incumbent journeys + singleton/canonical seed columns
full_universe_preloaded = false
```

流程：

```text
solve root RMP
run true-dual final judge
collect all true-RC negative candidates
run addability check
select master-addable batch
add to ColumnPool + MasterColumnView
repeat until no-negative certificate or fail-closed
```

B2B 必须证明：

```text
added_column_count > 0 on rows where B1B timed out because it could not close from a non-full seed pool,
or it must classify why addability/pricing did not produce progress.
```

### 3.3 B2C_diagnostic_tail_profile

只记录 profiling，不改变 solver behavior。

用于 20/30：

```text
labels_generated
labels_extended
completion_bound_check_time
candidate_negative_count
candidate_addable_count
duplicate_only_count
hidden_negative_count
```

B2C 可以在 20/30 上运行，即使 B2B 还不能 close。

---

## 4. 必须实现的模块

```text
exact/bpc/pricing/harvest.py
exact/bpc/pricing/hidden_negative_audit.py
exact/bpc/pricing/duplicate_only_audit.py
exact/bpc/pricing/profiling.py
exact/bpc/pricing/worker_seed_catalog.py
exact/bpc/pricing/completion_bounds.py  # audit/order only; pruning default off
exact/bpc/solver/pricing_tail_solver.py
runners/b2_pricing_tail_ablation.py
```

### 4.1 Harvesting pipeline

```text
candidate negative
  -> true reduced-cost filter
  -> branch/cut feasibility filter
  -> forbidden signature filter
  -> ColumnPool.addability_check
  -> MasterColumnView membership check
  -> would_enter_master == true filter
  -> batch selector
  -> add to pool + current master view
```

MVP selector:

```text
1. true_rc < -eps
2. unique full ColumnSemanticSignature
3. would_enter_master == true
4. prefer new task set
5. then strongest true reduced cost
6. cap per batch
7. log active_support_difference, but do not use it yet
```

### 4.2 Addability report fields

```text
is_new_signature
is_forbidden_signature
is_allowed_by_branch
is_allowed_by_cut_context
current_master_contains_signature
pool_contains_signature
would_replace_existing
would_change_active_support
would_enter_master
reject_reason
dominance_key
cut_coefficients
branch_signature
```

### 4.3 Duplicate-only audit

If final judge returns negative candidates but no candidate enters master, classify:

```text
duplicate_in_current_master
in_pool_not_master
forbidden_signature
branch_infeasible
cut_infeasible
dominance_filtered
rc_inconsistent
other
```

Hard rule:

```text
DUPLICATE_ONLY cannot close certificate.
DUPLICATE_ONLY cannot be counted as harmless.
```

### 4.4 Completion-bound policy

Default:

```text
ordering / audit only
pruning disabled
```

Pruning opt-in only after:

```text
bound-on/off consistency passes
direct-DP/BPC alignment still passes
profiling shows net benefit
5/10 no-regression passes
```

---

## 5. B2 消融实验设计

Every B2 run must compare against the current best accepted previous baseline:

```text
previous_baseline = B1A and B1B, plus B0 direct oracle where applicable
candidate_baseline = B2A / B2B / B2C
```

### 5.1 5-scale full

Run all 20 real instances:

```text
B0_pure_direct_dp
B1A_full_universe_root_audit
B1B_seeded_root_CG
B2A_full_universe_rc_audit_fast_path
B2B_seeded_tail_CG
```

Required:

```text
B2 objective == B1 objective where B1 certified
B2 certificate_scope == B1 certificate_scope where B1 certified
B2 wall_time <= B1 wall_time on aggregate, or clear non-regression explanation
B2B added_column_count > 0 on seeded-CG rows unless root already closed
```

### 5.2 10-scale selected then full

First selected 5 real instances. If row-time allows, run full 20.

Compare:

```text
B1A vs B2A
B1B vs B2B
```

Primary metrics:

```text
BPC_NODE_LP_CERTIFIED_count
row_timeout_count
pricing_round_count
added_column_count
candidate_addable_count
duplicate_only_count
mean wall
p90 wall
```

B2 pass condition for 10-scale selected:

```text
B2B improves at least one of:
    certified_count
    timeout_count
    mean/p90 wall
    final_judge_call_count
    pricing_round_count
without any certificate scope regression.
```

### 5.3 20-scale

Two groups are mandatory.

#### Group A: fail-closed guard

```text
max_direct_tasks < 20
B0 / B1 / B2 must fail closed
```

Required:

```text
no BPC_NODE_LP_CERTIFIED
no direct-root official leak
no true-dual BPC certificate
```

#### Group B: selected direct20 probe

For 1-3 selected real 20-scale instances, run:

```text
B0_pure_direct_dp with max_direct_tasks=20
B1A_full_universe_root_audit
B1B_seeded_root_CG
B2A_full_universe_rc_audit_fast_path
B2B_seeded_tail_CG
```

This group must include B0. Without B0, the report is invalid.

Purpose:

```text
Show whether direct-DP still solves.
Show whether B2 reduces B1 root closure cost.
If B0 solves but B1/B2 fail, classify as BPC root proof-tail problem, not direct-DP failure.
```

### 5.4 30-scale

Diagnostic only:

```text
B0 skip/fail-closed
B1 fail-closed
B2 fail-closed or diagnostic profiling only
```

B2 success at 30-scale is not certification; it is better diagnostic classification:

```text
tail_profile_present = true
no certificate leak
no official bound leak
clear fail_closed_reason
```

---

## 6. Required output columns

Every row must include:

```text
scale
instance_id
mode
previous_baseline_mode
candidate_layer
algorithm_status
certificate_scope
pricing_state
uses_true_dual_bpc_certificate
bpc_certificate_status
official_lower_bound_source
official_lower_bound_scope
best_diagnostic_bound_source

B0_direct_objective
previous_root_lp_bound
candidate_root_lp_bound
root_bound_le_direct_dp_integer_objective
root_lp_vs_direct_dp_gap
integral_root

pricing_round_count
final_judge_call_count
added_column_count
candidate_negative_count
candidate_addable_count
candidate_duplicate_count
candidate_forbidden_count
candidate_current_master_duplicate_count
candidate_in_pool_not_master_count
candidate_dominance_filtered_count
duplicate_only_count
hidden_negative_count

manual_rc_audit_pass
pricing_rc_audit_pass
proof_debt_unreleased_count
wall_time
fail_closed_reason
```

Summary must include:

```text
BPC_NODE_LP_CERTIFIED_count
fail_closed_count
timeout_count
certificate_scope_regression_count
objective_mismatch_count
root_bound_gt_B0_violation_count
manual_rc_fail_count
pricing_rc_fail_count
direct_root_official_leak_count
mean_wall
p90_wall
mean_added_columns
mean_pricing_rounds
mean_candidate_addable_ratio
duplicate_only_rate
hidden_negative_rate
```

---

## 7. B2 pass / fail rules

### Hard pass requirements

```text
root_bound_gt_B0_violation_count = 0
direct_root_official_leak_count = 0
manual_rc_fail_count = 0
pricing_rc_fail_count = 0
certificate_scope_regression_count = 0
objective_mismatch_count = 0
proof_debt_unreleased_count = 0 for certified rows
```

### Performance improvement requirement

B2 is accepted only if it improves over B1 on real instances in at least one accepted metric:

```text
10-scale selected:
    higher BPC_NODE_LP_CERTIFIED_count
    or lower timeout_count
    or lower p90 wall
    or lower final_judge_call_count
    or lower pricing_round_count
    or higher addable_negative_ratio with same certificate outcome

20-scale selected direct20:
    if B0 solves and B1 fails, B2 must either improve B1 status/wall or produce a clearer proof-tail classification.
```

If B2 only adds logging with no performance or classification improvement:

```text
B2 remains diagnostic, not accepted.
Do not enter B3 as an accepted next layer.
```

---

## 8. B2 blocked states

Do not enter B3 if:

```text
B2 has certificate leakage
B2 weakens any B1 certificate scope
B2 changes objective
B2 cannot explain duplicate-only rows
B2 cannot produce valid 20-scale direct20 B0/B1/B2 comparison
B2 has no improvement over B1 on 5/10/20/30 ablation
```

---

## 9. Report requirements

Produce:

```text
runs/b2_pricing_tail_ablation/b2_pricing_tail_rows.csv
runs/b2_pricing_tail_ablation/b2_pricing_tail_summary.json
runs/b2_pricing_tail_ablation/b2_pricing_tail_report_zh.md
```

Markdown report sections:

```text
1. Completed scope
2. Baseline comparison matrix
3. Redlines
4. 5-scale full results
5. 10-scale selected/full results
6. 20-scale fail-closed and direct20 probe
7. 30-scale diagnostic
8. Addability breakdown
9. Duplicate-only audit breakdown
10. Hidden-negative audit
11. B2 accepted? yes/no
12. If no, exact reason and next repair target
```

---

## 10. Exit statement

B2 does not become accepted because it exists. It becomes accepted only if:

```text
It preserves B1 proof semantics,
and it measurably improves root pricing-tail behavior over B1 on real 5/10/20/30 ablation.
```
