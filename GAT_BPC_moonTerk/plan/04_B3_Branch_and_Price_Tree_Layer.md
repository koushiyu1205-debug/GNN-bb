# 04_B3_Branch_and_Price_Tree_Layer

## 0. 当前定位

B3 的目标不是重新证明 direct-DP，也不是继续做 root pricing-tail。当前 accepted B3B 的核心任务是：

```text
在 fixed-graph direct journey universe 的任务集合代表列上，
用 branch-context-aware reduced-cost audit 给 node LP official bound，
再用 branch-and-price tree gate 把 node LP certificates 推进到 BPC_TREE_OPTIMAL。
```

当前 accepted B3B 不是纯 B2B_R3 worker-tail。它使用：

```text
best-task-subset representative universe
  -> small seeded node RMP
  -> branch-context-aware membership RC audit
  -> tree gate: integer incumbent / bound pruning / infeasible-node audit
```

这里的 `complete universe` 是历史兼容名，准确语义是：

```text
每个非空 task subset 保留一条 fixed-graph objective-best representative journey。
它不是同一个 task subset 下所有 route variants 的全集。
```

该压缩表示在 B3 中是 exact-safe 的原因是：B3 只启用 Ryan-Foster same/different-journey branching，不启用 cuts 或 route-order branch；同一 task subset 的不同路线变体只会改变 objective，不会改变覆盖、fleet 使用或 branch membership。

当前可接受前置状态：

```text
B0:
    fixed-graph direct-DP oracle。

B2_PRODUCT:
    product exact fallback。
    scope = DIRECT_DP_FIXED_GRAPH_OPTIMAL。
    不是 BPC certificate。

B2A:
    full-universe RC audit fast path。
    只在 full universe complete + all columns in master + RC audit pass 时给 BPC_NODE_LP_CERTIFIED。

B2B_R3:
    accepted root-level BPC seeded-CG baseline。
    使用 true-dual negative-search worker + worker-before-final-judge policy。
    worker 不能 certificate；final judge 仍是唯一 CERTIFIED_NO_NEGATIVE 来源。

B3B:
    accepted exact tree baseline for current 5/10/20 fixed-graph instances。
    使用 best-task-subset representative universe + branch RC audit + tree gate。
    20-scale current dataset: BPC_TREE_OPTIMAL 20/20。
```

B2B_R3 仍保留为 root-pricing baseline 和 fallback/diagnostic node engine；当前 20-scale accepted closure 以 B3B representative-universe audit path 为准。

---

## 1. 为什么当前 B3 文档需要澄清

早期 B3 计划要求把 B2B_R3 worker-tail 抽成 node engine。后续实验证明，20-scale 的主要 blocker 不是 branch tree 本身，而是 root/node proof-tail 的重复枚举、过大 seed pool 和 fractional node 上的 expensive integer pool search。因此当前 accepted B3B 改成了更窄、更可证的路径。

### 1.1 当前 accepted B3B

```text
B3B_seeded_branch_price_tree
node_pricing_mode = B3_complete_universe_branch_rc_audit
column_universe_semantics = best_task_subset_representative_fixed_graph_columns
```

它不是“预装所有列然后直接结束”。实际流程是：

```text
B0-compatible columns + singleton seed columns
  -> solve node RMP
  -> final judge audits cached task-subset representative universe under BranchContext
  -> add negative columns in batches
  -> repeat until no negative RC
  -> if RMP primal integral, promote node to INTEGER_INCUMBENT
  -> if fractional, branch or prune
```

### 1.2 B2B_R3 的当前角色

```text
B2B_R3 remains:
    root-pricing baseline;
    diagnostic comparison;
    fallback node engine when representative-universe audit is disabled.

B2B_R3 is not the accepted 20-scale closure path.
```

---

## 2. B3 非目标

本阶段不做：

```text
不启用 GAT。
不启用 cuts。
不启用 route-order branch。
不启用 same_sortie / different_sortie branch。
不默认启用 completion-bound pruning。
不让 direct-DP 提供 BPC certificate。
不把 worker no-column 当作 node closure。
不把 NO_FRACTIONAL_RF_PAIR 当作 integrality proof。
```

Direct-DP 在 B3 中只能作为：

```text
feasible incumbent source
small-scale objective oracle
product exact baseline
```

不能作为：

```text
node LP certificate
branch tree closure proof
BPC_TREE_OPTIMAL certificate
```

---

## 3. B3 核心优化目标

B3 需要在消融实验中证明：

```text
B3 比当前 best accepted baseline 更进一步：
    B2B_R3 只能给 root-level BPC_NODE_LP_CERTIFIED；
    B3 能在需要整数证明时给 BPC_TREE_OPTIMAL。
```

最小可接受目标：

```text
5-scale full:
    B3 20/20 BPC_TREE_OPTIMAL；
    objective 与 B0 direct-DP exact objective 一致；
    redlines 全 0。

10-scale selected5:
    B3 至少不退化；
    若 root LP integral，则 B3 应快速把 BPC_NODE_LP_CERTIFIED 晋级为 BPC_TREE_OPTIMAL；
    若 root LP fractional，则 B3 应实际 branch，且输出可解释 tree ledger。

20-scale selected direct20:
    不强制 BPC_TREE_OPTIMAL；
    必须输出 branch/tree diagnostic，不能污染 certificate。

30-scale:
    fail-closed diagnostic。
```

如果 B3 不能在真实实例上把 `BPC_NODE_LP_CERTIFIED` 推进到 `BPC_TREE_OPTIMAL`，则 B3 只能保留为 diagnostic，不得进入 B4。

---

## 4. B3 主要求解流程

### 4.1 Root / node 输入

每个 B3 node 输入：

```text
node_id
parent_node_id
depth
BranchContext
inherited column pool / seed columns
incumbent objective
node limit / depth limit
B3 representative-universe audit config
```

### 4.2 Node pricing engine

当前 accepted B3B node engine 是：

```text
solve_b3_node_with_task_subset_representative_audit(
    data,
    branch_context,
    node_id,
    b0-compatible seed columns + singleton seed columns,
    cached task-subset representative universe,
    incumbent_objective,
    max_rounds,
    max_columns_per_round,
)
```

核心逻辑：

```text
1. solve node RMP
2. final judge audits all task-subset representative columns satisfying BranchContext
3. add addable negative columns in batches
4. re-solve node RMP
5. certify no-negative only by final judge membership RC audit
6. if RMP seed is infeasible, repair from the same representative universe
7. never treat B0/direct-DP as BPC certificate
```

输出：

```text
NODE_LP_CERTIFIED
NODE_INCOMPLETE
NODE_RMP_INFEASIBLE_UNCERTIFIED
DUPLICATE_ONLY
DIAGNOSTIC_PRICING_FRONTIER
```

### 4.3 Tree loop

Tree loop：

```text
initialize root node
load feasible incumbent from B0 / B2_PRODUCT, certificate scope remains DIRECT_DP_FIXED_GRAPH_OPTIMAL
while queue not empty and node limit not hit:
    solve node pricing with representative-universe audit engine
    if node LP not certified:
        mark node incomplete
        continue
    if node primal integral:
        update incumbent
        mark INTEGER_INCUMBENT
        continue
    if node lower bound >= incumbent:
        mark PRUNED_BY_BOUND
        continue
    select fractional branch pair
    if no RF pair:
        trigger fallback branch or aggregation certificate
    create same/different children
```

---

## 5. Branch semantics

### 5.1 Ryan-Foster same/different journey

B3 第一版只实现：

```text
same_journey(i, j)
different_journey(i, j)
```

这里的 `journey` 是一台 rover 的 multi-sortie schedule，不是单次 sortie。

### 5.2 same_mass 公式

必须使用：

```text
same_mass(i,j) = sum_p lambda_p * 1[i in S_p and j in S_p]
```

候选 pair 来自：

```text
0 < same_mass(i,j) < 1
```

优先选择接近 0.5 的 pair，也可以记录 task mode / spatial sector / pricing pressure 等 diagnostic features。

### 5.3 Branch child feasibility

对于 candidate pair `(i,j)`：

```text
same_journey child:
    allowed columns must contain both i and j, or contain neither.
    columns containing exactly one of i,j are forbidden.

different_journey child:
    allowed columns must not contain both i and j.
    columns containing neither or exactly one are allowed.
```

所有以下组件必须 respect BranchContext：

```text
seed column loader
ColumnPool.addability_check
B2B_R3 negative-search worker
final judge
manual branch feasibility audit
```

### 5.4 NO_FRACTIONAL_RF_PAIR 不是 integrality proof

硬规则：

```text
NO_FRACTIONAL_RF_PAIR != NODE_INTEGRAL
```

如果 node LP fractional 但没有可用 RF pair，必须进入 fallback：

```text
1. journey signature family / route signature branch diagnostic
2. exact column-signature forbid branch
3. aggregation certificate proving representative-level fractionality harmless
```

B3 第一版可以只实现 fallback diagnostic，但不能把 no-RF-pair 当作 closed node。

---

## 6. Tree certificate 条件

B3 只有在以下条件全部满足时才允许输出：

```text
certificate_scope = BPC_TREE_OPTIMAL
```

条件：

```text
integer incumbent exists
all branch nodes are closed, pruned by valid official bound, or infeasibility-certified
no open nodes
no incomplete nodes
all node LP bounds used for pruning are BPC_NODE_LP_CERTIFIED
all node certificate ledgers valid
all branch-context pricing audits pass
global lower bound >= incumbent objective - eps
proof_debt_queue empty
```

如果只 root node certified：

```text
certificate_scope = BPC_NODE_LP_CERTIFIED
```

如果 any node incomplete：

```text
certificate_scope = DIAGNOSTIC_PRICING_FRONTIER or FEASIBLE_INCUMBENT_ONLY
```

Direct-DP incumbent 不等于 BPC_TREE_OPTIMAL。

---

## 7. Required code changes

### 7.1 Accepted B3B node engine

Current accepted B3B uses a representative-universe node engine:

```text
solve node RMP
-> audit cached best-task-subset representative universe under BranchContext
-> add negative representative columns
-> re-solve until CERTIFIED_NO_NEGATIVE or fail-closed
```

Required support:

```text
branch_context parameter
node_id parameter
small seed columns
cached representative universe
incumbent objective
node-local ColumnPool/MasterColumnView
node-local profiling
node-local proof debt audit
```

The B2B_R3 node engine remains available as fallback/diagnostic code, but it is not the accepted 20-scale closure path.

### 7.2 Update B3 entry

```text
B3B default:
    use_complete_universe_audit = True
    column_universe_semantics = best_task_subset_representative_fixed_graph_columns

B2 root diagnostic:
    may call mode=B2B_R3_true_dual_negative_search_worker for comparison,
    but should be skipped on larger cases when it would only consume row timeout.
```

### 7.3 Name the universe boundary explicitly

Do not describe the accepted B3B universe as "all route variants". The compatible payload key may still say `complete_universe_*`, but the proof boundary is:

```text
one objective-best fixed-graph journey per nonempty task subset
no route-dependent cuts
no route-order branch
Ryan-Foster task-set membership branch only
```

This path is exact for current B3. If B4 adds route-dependent cuts or route-order branching, B4 must extend the pricing universe or fall back to route-variant pricing.

### 7.4 Add branch-aware harvesting/addability

```text
harvest negative representative columns
reject branch-infeasible columns
record branch_filtered_count
do not treat rejected negative columns as proof debt once they are branch-infeasible
```

Harvest selected columns must satisfy:

```text
true_rc < -eps
BranchContext feasible
ColumnPool / MasterColumnView addability pass
would_enter_master = true
```

Selected harvest addability failure is a redline.

---

## 8. Required tests

### 8.1 Branch feasibility tests

```text
test_same_journey_child_allows_both_or_neither
test_same_journey_child_rejects_exactly_one
test_different_journey_child_rejects_both
test_different_journey_child_allows_neither_or_exactly_one
```

### 8.2 Pricing context tests

```text
test_worker_respects_branch_context
test_final_judge_respects_branch_context
test_harvest_selected_columns_respect_branch_context
test_column_pool_addability_respects_branch_context
```

### 8.3 Certificate tests

```text
test_worker_no_column_does_not_close_node
test_node_lp_certified_only_after_final_judge_no_negative
test_direct_dp_incumbent_not_tree_certificate
test_no_fractional_rf_pair_not_integrality_proof
test_tree_optimal_requires_all_leaves_closed
```

### 8.4 Regression tests

```text
test_b3_root_integral_promotes_to_tree_optimal_when_valid
test_b3_objective_matches_direct_dp_on_closed_5scale
test_b3_no_redline_certificate_scope_regression
```

---

## 9. B3 ablation experiment design

B3 must compare against current best accepted baseline:

```text
B2B_R3_true_dual_negative_search_worker
```

### 9.1 Modes

```text
B0_pure_direct_dp
B2_PRODUCT_EXACT_SOLVER
B2B_R3_true_dual_negative_search_worker
B3A_full_universe_branch_audit        # diagnostic only
B3B_seeded_branch_price_tree           # candidate accepted baseline
```

### 9.2 Matrix

```text
5-scale full:
    all 20 instances

10-scale selected5:
    first gate

10-scale full:
    only if selected5 passes with acceptable wall time

20-scale selected direct20:
    at least 5 instances
    diagnostic / improvement only

20-scale fail-closed guard:
    max_direct_tasks < 20
    verify fail-closed behavior

30-scale fail-closed diagnostic:
    verify no certificate leakage
```

### 9.3 Row fields

Each row must include:

```text
scale
instance_id
mode
algorithm_status
certificate_scope
pricing_state
uses_true_dual_bpc_certificate
B0_direct_objective
B2B_R3_root_lp_bound
B3_global_lb
B3_global_ub
B3_global_gap
B3_tree_closed
BPC_TREE_OPTIMAL_count
BPC_NODE_LP_CERTIFIED_count
node_count
evaluated_node_count
open_node_count
incomplete_node_count
pruned_by_bound_count
integer_incumbent_count
branch_count
max_depth_reached
NO_FRACTIONAL_RF_PAIR_count
manual_rc_audit_pass
pricing_rc_audit_pass
branch_pricing_audit_pass
proof_debt_unreleased_count
selected_harvest_addability_fail_count
all_node_ledgers_valid
wall_time
fail_closed_reason
```

### 9.4 Redlines

All must be zero:

```text
root_bound_gt_B0_violation_count
tree_incumbent_diff_vs_B0_count
certificate_scope_regression_count
manual_rc_fail_count
pricing_rc_fail_count
branch_pricing_audit_fail_count
proof_debt_unreleased_certified_count
selected_harvest_addability_fail_count
direct_dp_certificate_leak_count
NO_FRACTIONAL_RF_PAIR_treated_as_integral_count
open_node_but_tree_optimal_count
incomplete_node_but_tree_optimal_count
```

---

## 10. B3 acceptance criteria

B3B can be accepted only if:

```text
1. All redlines = 0.
2. 5-scale full: BPC_TREE_OPTIMAL on 20/20, objective equals B0 direct-DP objective.
3. 10-scale full: BPC_TREE_OPTIMAL on 20/20, objective equals B0 direct-DP objective.
4. 20-scale full: BPC_TREE_OPTIMAL on 20/20 under current fixed-graph data.
5. B3 never uses direct-DP as BPC certificate.
6. All BPC_TREE_OPTIMAL rows have all node ledgers valid and no incomplete/open nodes.
```

Optional stronger acceptance:

```text
more root-fractional / branch-heavy fixtures close with nontrivial branching.
runtime improves without weakening tree certificate gates.
```

If B3 fails 5/10/20 current fixed-graph BPC_TREE_OPTIMAL or leaks a tree certificate with invalid ledgers/open nodes, B3 remains diagnostic and cannot enter B4.

---

## 11. What B3 should report

The Chinese markdown report must answer:

```text
1. Did B3 produce BPC_TREE_OPTIMAL, or only BPC_NODE_LP_CERTIFIED?
2. How many instances closed without branching because root LP was integral?
3. How many instances required actual branching?
4. How many nodes were evaluated / pruned / incomplete?
5. Did any branch node violate branch-context pricing?
6. Did any no-RF-pair state occur, and how was it handled?
7. Did B3 objective match B0 direct-DP on closed small instances?
8. Is B3B accepted as the next baseline?
9. Is it safe to proceed to B4 cuts/formulation?
```

---

## 12. B4 entry rule

Only enter B4 if:

```text
B3B_seeded_branch_price_tree accepted = true
redlines all zero
5-scale full BPC_TREE_OPTIMAL = 20/20
10-scale full BPC_TREE_OPTIMAL = 20/20
20-scale full BPC_TREE_OPTIMAL = 20/20 under current fixed-graph data
30-scale remains explicit fail-closed diagnostic unless a larger exact universe is implemented
```

If not, continue B3. Do not use cuts to hide branch-context or tree-certificate bugs.

---

## 13. 2026-07-02 20-scale closure update

Current B3 implementation adds a formal task-subset representative branch RC audit path:

```text
small seeded node RMP
-> true-dual final judge over cached best-task-subset representative universe
-> add negative columns in batches
-> certify no-negative by membership RC audit
-> promote root-integral node to BPC_TREE_OPTIMAL
```

Important proof boundary:

```text
B0 direct-DP is only a feasible incumbent / objective comparison.
B0 direct-DP is not used as the BPC certificate.
Node LP certificates still require representative-universe reduced-cost audit.
The compatible `complete_universe_*` payload fields mean one best fixed-graph column per task subset, not all route variants.
```

Verified selected5 supplemental result:

```text
report: runs/b3_20_tree_closure_probe/b3_20_tree_closure_probe_report_zh.md
scale: 20 selected5
B3B BPC_TREE_OPTIMAL: 5/5
mean B3 wall time: 27.997986
max B3 wall time: 35.18185
max node count: 1
max incomplete node count: 0
max |B3 incumbent - B0 objective|: 1e-06
objective match tolerance: 5e-06
objective match within tolerance: 5/5
```

This supersedes the older B3 ablation matrix row where 20-scale B3B timed out at `row_time_limit_sec=60` before returning a useful payload. That older row is now historical diagnostic evidence for the old B2B_R3-tail entry path, not the current B3 20-scale closure status.

Root-fractional hardcase closure:

```text
hardcase: lunar_ice_sp50_020_012_seed829012
report: runs/b3_20_tree_closure_probe/b3_20_fractional_hardcase_012_report_zh.md
B3 status: BPC_OPTIMAL
BPC_TREE_OPTIMAL: yes
node_count: 7
open_node_count: 0
incomplete_node_count: 0
global_lb = global_ub = 5996.219161
tree issues: []
```

Implementation changes that closed 012:

```text
1. Branch nodes no longer seed the RMP with every <=4-task column; they start from B0-compatible columns plus singleton columns.
2. If a branch seed is infeasible, exact-cover repair searches the branch-filtered representative universe and adds only a small feasible cover.
3. Representative-universe final judge still performs the official no-negative reduced-cost audit.
4. Integer witness generation first checks whether the RMP primal is already integral; if it is fractional, B3 branches/prunes instead of running integer DP over the representative priced universe.
```

Full20 sweep result:

```text
selected5: formally closed 5/5
hardcase 012: formally closed
full20 all 20 instances: formally closed 20/20
report: runs/b3_full20_sweep/b3_full20_sweep_report_zh.md
BPC_OPTIMAL: 20/20
BPC_TREE_OPTIMAL: 20/20
objective match with B0 within tolerance: 20/20
max |B3 incumbent - B0 objective|: 1e-06
tree objective tolerance: 5e-06
max node count: 7
branching instances: 2/20
max open_node_count: 0
max incomplete_node_count: 0
```

So B3 now has full 20-scale evidence on the current `lunar_ice_sp50_020` dataset. The next layer can treat B3B as the accepted exact tree baseline for these 20-task fixed-graph instances, while preserving the proof boundary that B0 is only an incumbent/objective oracle and not a BPC certificate.
