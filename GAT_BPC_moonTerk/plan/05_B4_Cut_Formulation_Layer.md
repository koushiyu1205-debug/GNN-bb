# B4：Cut / Formulation Layer

## 1. 目标

B4 在 B3 branch-and-price tree 稳定后，引入数学有效不等式和 formulation strengthening。

它解决的问题是：

```text
root / child LP bound 太弱；
branch tree 太大；
pricing 能 close，但 lower bound 长期低于 incumbent；
proof tail 因 formulation 弱而无法缩短。
```

B4 不是 GAT 模块。Cut 不能由 GAT 决定 validity。

---

## 2. B4 相对 B3 新增

```text
CutContext
CutContextVersion
CutCoefficientVector
CutDominanceCompatibilityReport
subset-row cut diagnostic
subset-row cut opt-in live path
cut reduced-cost audit
cut dual sign audit
cut-aware ColumnSemanticSignature / dominance report
```

---

## 3. Cut 上线原则

任何 cut 上线前必须满足：

```text
integer validity proof
journey coefficient function
RMP coefficient audit
pricing coefficient audit
manual reduced cost == pricing reduced cost
cut dual sign audit
branch/cut context completion-bound fail-closed or proved safe
dominance safety audit under active cut
```

GAT 不得决定：

```text
cut 是否 valid
cut 是否 live
cut 是否用于 official lower bound
cut 是否可 prune node
```

---

## 4. MVP cut family

第一版候选：

```text
subset-row cut
```

建议策略：

```text
subset-row diagnostic first
subset-row live opt-in only after RC consistency tests pass
```

`fleet lower-bound cut` 保持：

```text
diagnostic-only until explicit proof under multi-sortie journey master
```

原因：journey master 中一个 selected column 是一台 rover 的 multi-sortie schedule。fleet 数、journey 数、sortie 数之间不等同于普通 CVRP route count。

---

## 5. CutContext 数据结构

建议：

```text
CutContext:
    version
    active_cut_ids
    cut_kind
    rhs
    sense
    coefficient_function_id
    dominance_compatibility
    pricing_supported
    completion_bound_supported
```

每个 column 必须能得到：

```text
CutCoefficientVector(column, cut_context)
```

该 vector 必须进入：

```text
RMP row coefficient
manual reduced cost
pricing reduced cost
column semantic signature hash when active cuts can change dominance
```

---

## 6. Completion-bound 与 cuts

默认规则：

```text
cut context 非空时，completion-bound pruning fail-closed。
```

除非某个 completion bound 明确证明支持 active cut dual 和 cut coefficient function，否则只能：

```text
ordering
audit
profiling
```

不能用于 pruning 或 certificate。

---

## 7. Dominance 与 cuts

如果 active cut coefficient 只依赖 task set，且 dominance key 包含 task set，则可能安全。

如果 active cut coefficient 依赖：

```text
route order
sortie count
time profile
resource profile
path option signature
```

则默认禁用相关 dominance。

ColumnPool dominance key 至少应包含：

```text
task_set
branch_signature
cut_coefficient_vector_hash
route_order_signature if route/order-sensitive
resource_profile_hash if resource-sensitive
```

---

## 8. Cut reduced-cost 公式

统一 reduced cost：

```text
rc(p) = c_p - sum_i pi_i - mu - sum_h gamma_h a_hp
```

其中：

```text
a_hp = cut coefficient of column p under cut h
```

测试必须覆盖：

```text
manual RC with cuts == pricing RC with cuts
RMP cut coefficient == pricing cut coefficient
cut dual sign convention stable
```

---

## 9. B4 消融实验

对比：

```text
B4 = B3 + cuts/formulation
vs
B3 = branch-and-price without cuts
```

A/B：

```text
cuts off
subset-row diagnostic-only
subset-row live opt-in
fleet-lower-bound diagnostic-only
```

---

## 10. B4 验收指标

```text
lp_bound_delta
root_gap_delta
node_gap_delta
branch_node_count_delta
pricing_round_delta
final_judge_time_delta
bpc_tree_optimal_count_delta
manual_rc_cut_consistency_pass_count
cut_dual_nonzero_count
cut_violation_count
cut_added_count
cut_pricing_supported_count
cut_completion_bound_fail_closed_count
```

注意：

```text
cut_added_count 不是成功指标。
```

成功指标是：

```text
LP bound 上升
gap 下降
node count 下降
certificate time 不恶化
BPC_TREE_OPTIMAL count 不下降，最好上升
```

---

## 11. B4 通过标准

进入 B5 前，必须满足：

```text
1. 5/10 no regression。
2. manual RC == pricing RC with active cuts。
3. active cut context 下 completion-bound pruning fail-closed，除非已证明支持。
4. dominance compatibility report 通过。
5. subset-row diagnostic 能解释 violated / binding / nonzero dual。
6. live opt-in cuts 不改变 final integer optimum。
7. B4 vs B3 的边际贡献可报告。
```

---

## 12. B4 失败标准

任一情况失败：

```text
1. cut coefficient 在 RMP 与 pricing 中不一致。
2. cut dual sign 与 reduced-cost 公式不一致。
3. active cut context 下仍使用未经证明的 completion-bound pruning。
4. task-set dominance 删除 cut coefficient 不同的 columns。
5. fleet lower-bound cut 未证明就 live。
6. cut 增加但 LP bound / gap 完全不动，仍声称 cut 有效。
```

---

## 13. Codex 禁止事项

B4 不准：

```text
让 GAT 选择 cut validity
把 violated cut count 当成功指标
未经 proof live fleet lower-bound cut
让 route/resource-sensitive cut 与 task-set dominance 默认共存
用 diagnostic cut bound 生成 certificate
```

---

## 14. 为什么 cuts 放在 GAT 前

Cut 会改变：

```text
RMP duals
reduced cost
pricing pressure
branch child behavior
harvest candidate quality
GAT labels
```

如果先训练/启用 GAT，再加入 cuts，GAT 学到的是无 cut regime 下的 policy。为了消融干净，应先稳定 B4，再让 B5 的 GAT 在稳定 exact/cut baseline 上学习 guidance。
