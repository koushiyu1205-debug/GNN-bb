# B3：Branch-and-Price Tree Layer

## 1. 目标

B3 在 B2 的 root BPC + tail optimization 基础上，实现真正的 Branch-and-Price tree。

它解决的问题是：

```text
root RMP LP closure 只能证明 LP relaxation；
如果 root LP fractional，必须通过 branch tree 证明 integer optimality。
```

B3 仍然不默认启用：

```text
GAT guidance
live cuts
route-order branch
completion-bound pruning under branch context unless separately proved
```

---

## 2. B3 相对 B2 新增

```text
Ryan-Foster same_journey / different_journey branch
BranchContext
NodeQueue
NodeSolver
TreeSolver
Global LB / UB ledger
Branch completeness fallback
Node infeasibility taxonomy
```

---

## 3. 第一版 Branch 语义

第一版使用：

```text
same_journey(i, j)
different_journey(i, j)
```

这里的 `journey` 是：

```text
一台 rover 的 multi-sortie schedule
```

不是单次 sortie。

第一版不实现：

```text
same_sortie / different_sortie
route-order / precedence branch
```

---

## 4. Ryan-Foster fractional mass 公式

必须明确：

```text
same_mass(i,j) = sum_p lambda_p * 1[i in S_p and j in S_p]
```

其中：

```text
lambda_p 来自当前 node RMP primal LP solution
S_p 是 journey column 覆盖的 task set
```

候选 pair 通常选择：

```text
0 < same_mass(i,j) < 1
且 closest to 0.5
```

测试：

```text
test_same_journey_fractional_mass_matches_primal_solution
test_rf_branch_children_partition_current_fractional_solution
```

---

## 5. BranchContext 对 pricing 的要求

same child：

```text
i and j must appear in the same journey column, or neither appears.
```

不同 child：

```text
i and j may not appear in the same journey column.
```

所有 pricing 生成的 columns 必须先经过 branch context 过滤：

```text
price candidate
  -> branch_context.is_column_allowed(column)
  -> only allowed columns can enter ReducedCost / Harvest
```

测试：

```text
test_same_child_pricing_filters_columns
test_different_child_pricing_filters_columns
test_branch_filtered_generated_columns_all_satisfy_context
```

---

## 6. Branch completeness fallback

硬规则：

```text
NO_FRACTIONAL_RF_PAIR != NODE_INTEGRAL
```

原因：journey master 允许同一 task set 下保留多个 route/path/timing/resource representative。LP 可能在这些 representative 之间 fractional，而 Ryan-Foster task-pair relation 完全一样。

Fallback 顺序：

```text
1. same_journey / different_journey Ryan-Foster branch
2. journey signature family / route signature branch
3. exact column-signature forbid branch
4. aggregation certificate
```

第一版不建议实现强 `lambda_p = 1` branch。若需要 column branch，先实现：

```text
forbid exact ColumnSemanticSignature branch
```

因为它更容易 pricing-compatible。

---

## 7. Column-signature branch 约束

如果使用 exact column-signature forbid branch：

```text
left child forbids exact ColumnSemanticSignature
right child follows original candidate selection path or requires aggregation proof
```

禁止实现无法被 pricing 支持的 branch rule。

任何 branch rule 都必须回答：

```text
Can pricing filter future generated columns by this BranchContext?
Can ColumnPool.addability_check enforce it?
Can reduced-cost audit see the same context?
```

否则只能 diagnostic。

---

## 8. Node infeasibility taxonomy

必须区分：

```text
NO_COLUMN_COVER_IN_POOL:
    当前 restricted pool 无法 cover；diagnostic only。

NODE_RMP_INFEASIBLE_UNCERTIFIED:
    当前 node RMP infeasible，但 pricing 可能生成修复列。

BPC_INFEASIBLE_CERTIFIED:
    complete pricing / column-universe coverage 证明没有 feasible cover。
```

禁止把 restricted pool no-cover 当成 infeasible certificate。

---

## 9. Global Tree Ledger

每个 node 必须记录：

```text
node_id
parent_id
branch_context
rmp_status
pricing_state
node_lp_bound
node_lp_bound_official
certificate_scope
incumbent_objective_at_entry
incumbent_objective_at_exit
node_status:
    OPEN
    BRANCHED
    NODE_LP_CERTIFIED
    PRUNED_BY_BOUND
    INTEGER_INCUMBENT
    INCOMPLETE
    INFEASIBLE_CERTIFIED
    INFEASIBLE_UNCERTIFIED
```

全局必须记录：

```text
global_ub
global_lb
open_node_count
closed_node_count
pruned_node_count
incomplete_node_count
integer_incumbent_source
certificate_scope
```

---

## 10. BPC_TREE_OPTIMAL 条件

只有满足：

```text
integer incumbent exists
all nodes closed / pruned / infeasible-certified
all node lower bounds official
no incomplete nodes remain
global lower bound == incumbent within tolerance
all certificate ledgers valid
```

才能输出：

```text
certificate_scope = BPC_TREE_OPTIMAL
```

---

## 11. B3 消融实验

对比：

```text
B3 = B2 + branch-and-price tree
vs
B2 = root-only BPC + tail optimization
```

只在 root LP fractional instances 上评估 branch contribution。

消融开关：

```text
branching off
Ryan-Foster branch on
Ryan-Foster + fallback diagnostic
Ryan-Foster + exact signature forbid branch opt-in
```

---

## 12. B3 验收指标

```text
root_integral_count
root_fractional_count
branch_node_count
node_lp_certified_count
integer_incumbent_count
pruned_by_bound_count
incomplete_node_count
no_fractional_rf_pair_count
fallback_branch_count
bpc_tree_optimal_count
objective_match_direct_dp_count
```

必须报告：

```text
BPC_TREE_OPTIMAL count
BPC_NODE_LP_CERTIFIED count
NODE_INCOMPLETE count
NO_FRACTIONAL_RF_PAIR fallback count
```

---

## 13. B3 通过标准

进入 B4 前，必须满足：

```text
1. 5/10 小规模能完成 BPC_TREE_OPTIMAL 或明确 incomplete reason。
2. direct-DP closed small instances 与 BPC tree integer incumbent objective 对齐。
3. NO_FRACTIONAL_RF_PAIR 不被当成 integrality proof。
4. branch-filtered pricing columns 全部满足 node BranchContext。
5. Global LB / UB ledger 可解释每个 node。
6. B2 和 B3 在 root integral instances 上结果一致。
```

---

## 14. B3 失败标准

任一情况失败：

```text
1. root LP fractional 但输出 BPC_TREE_OPTIMAL。
2. NO_FRACTIONAL_RF_PAIR 被当成 NODE_INTEGRAL。
3. pricing 生成违反 branch context 的 column。
4. NODE_RMP_INFEASIBLE_UNCERTIFIED 被写成 BPC_INFEASIBLE_CERTIFIED。
5. open / incomplete node 存在时输出 tree optimal。
6. column signature branch 不能被 pricing enforce。
```

---

## 15. Codex 禁止事项

B3 不准：

```text
默认启用 GAT branch score
默认启用 cuts
默认启用 route-order branch
使用 finite-pool child RMP gain 做 official prune
把 child LP bound 当 official bound，除非 child pricing closure certified
```

先把 branch-and-price tree 的证书语义做稳。
