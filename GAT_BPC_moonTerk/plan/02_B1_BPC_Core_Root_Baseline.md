# B1：BPC-Core Root Baseline

## 1. 目标

B1 是第一个真正的 BPC baseline，但它只做 root node。

它必须满足：

```text
Root-only true-dual BPC
No branch
No live cuts
No GAT
No advanced harvesting
No default completion-bound pruning
```

B1 的目标不是追求速度，而是建立一个可以与 B0 direct-DP oracle 对齐的 **最小 true-dual BPC 闭环**。

---

## 2. B1 新增内容

相对 B0，B1 新增：

```text
Journey RMP
ReducedCostContext
true-dual pricing final judge
certificate ledger
TaskIndexMap
ColumnSemanticSignature
ColumnPool
MasterColumnView
ProofDebtQueue 空壳
PathOptionUniverse / dominance audit
```

B1 不新增：

```text
branch tree
GAT guidance
live cut
complex tail scheduler
route-order branch
support-aware harvesting
```

---

## 3. 必须实现的模块

建议路径：

```text
src/lunar_ice_bpc/exact/bpc/pricing/status.py
src/lunar_ice_bpc/exact/bpc/certificates/certificate_ledger.py
src/lunar_ice_bpc/exact/bpc/core/task_index.py
src/lunar_ice_bpc/exact/bpc/core/column_signature.py
src/lunar_ice_bpc/exact/bpc/core/column_pool.py
src/lunar_ice_bpc/exact/bpc/core/master_column_view.py
src/lunar_ice_bpc/exact/bpc/master/reduced_cost.py
src/lunar_ice_bpc/exact/bpc/master/journey_master.py
src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py
src/lunar_ice_bpc/exact/bpc/certificates/proof_debt_queue.py
src/lunar_ice_bpc/exact/bpc/solver/root_node_solver.py
```

如果项目已有部分同名功能，可复用，但必须满足本文件的接口语义。

---

## 4. 核心数据结构

### 4.1 TaskIndexMap

禁止任何模块自行：

```python
int(task_id)
```

外部 task id 必须始终是 string。内部 bit mask 必须通过：

```text
TaskIndexMap.external_id_to_index
TaskIndexMap.index_to_external_id
TaskIndexMap.mask_of(task_id)
TaskIndexMap.ids_from_mask(mask)
```

测试必须覆盖：

```text
"001" 不得变成 1
solution / manifest / figure / GAT node mapping 使用同一 external id
```

### 4.2 ColumnSemanticSignature

第一版至少包含：

```text
task_set
sortie_partition
ordered_task_sequences
path_option_signature
service_timing_signature
resource_profile_signature
branch_signature
cut_coefficient_vector_hash
```

如果某些字段暂未启用，也必须保留空位或 version 字段。

### 4.3 ColumnPool 与 MasterColumnView

必须区分：

```text
ColumnPool:
    所有已知 columns。

MasterColumnView:
    当前 node RMP 实际加载的 columns。
```

这三件事不能混：

```text
column exists in pool
column exists in current RMP
column is addable to current RMP
```

接口建议：

```text
ColumnPool.contains_signature(sig)
ColumnPool.addability_check(column, node_context) -> AddabilityReport
ColumnPool.add(column, node_context) -> AddResult
MasterColumnView.contains_signature(sig, node_id)
MasterColumnView.add_from_pool(column, node_context)
```

### 4.4 ReducedCostContext

必须是不可变上下文：

```text
task_duals
fleet_dual
cut_duals
branch_context
cut_context
dual_fingerprint
rmp_iteration_id
```

pricing、manual check、harvest、audit 必须共用同一个 reduced-cost 函数。

### 4.5 ProofDebtQueue

B1 只需要空壳，但必须存在：

```text
ProofDebtQueue.add(candidate)
ProofDebtQueue.release_all_before_certificate()
ProofDebtQueue.block_certificate_if_unreleased()
ProofDebtQueue.audit()
```

即使 GAT 未启用，也要让 certificate ledger 知道：

```text
certificate must be blocked if unreleased true-RC negative proof debt exists.
```

---

## 5. B1 root node 主循环

```text
Input:
    root context
    empty branch context
    empty cut context
    B0 / seed column pool

Loop:
    1. solve journey RMP
    2. build ReducedCostContext
    3. audit all current-master columns RC
    4. run true-dual root final judge
    5. if FOUND_NEGATIVE:
           add columns to pool/master view
           continue
    6. if CERTIFIED_NO_NEGATIVE:
           mark root LP bound official
           return BPC_NODE_LP_CERTIFIED
    7. if INCOMPLETE_LIMIT:
           return BPC_INCOMPLETE_PRICING
```

B1 不允许 worker-local no-column 生成 certificate。

---

## 6. Direct-DP / BPC Alignment Tests

B1 的核心不是速度，而是对齐。

必须新增：

```text
test_objective_same_on_one_column
test_sortie_cost_same_as_direct_dp
test_journey_cost_same_as_direct_dp
test_full_fixed_column_ip_equals_direct_dp
test_manual_reduced_cost_equals_pricing_reduced_cost
test_root_lp_bound_le_direct_dp_integer_objective
test_root_pricing_closure_has_no_missing_columns_5scale
```

正确关系：

```text
root LP bound <= direct-DP integer objective
```

如果相等：

```text
integral_root = true
```

如果不等：

```text
branch-and-price required for BPC_TREE_OPTIMAL
```

Codex 不得把 root LP closure 等同于 integer optimality。

---

## 7. B1 消融实验

对比：

```text
B1 Root-only BPC
vs
B0 Direct-DP Frozen Oracle
```

关注：

```text
objective alignment
column universe coverage
manual RC consistency
pricing RC consistency
certificate scope correctness
root LP / integer gap
```

不以 wall time 为主验收。

---

## 8. B1 输出字段

每个 run 必须输出：

```text
algorithm_status
certificate_scope
uses_true_dual_bpc_certificate
pricing_state
root_rmp_status
root_rmp_objective
root_lp_bound_official
root_lp_vs_direct_dp_gap
integral_root
rmp_iteration_count
pricing_round_count
final_judge_status
final_judge_min_reduced_cost
manual_rc_audit_pass
pricing_rc_audit_pass
proof_debt_unreleased_count
```

---

## 9. B1 通过标准

进入 B2 前，必须满足：

```text
1. status / certificate scope 已用 enum + schema validator。
2. TaskIndexMap 不允许任何隐式 int(task_id)。
3. ColumnPool 与 MasterColumnView 分离。
4. ReducedCostContext fingerprint 稳定。
5. manual RC == pricing RC。
6. 5-scale root closure 可完成 BPC_NODE_LP_CERTIFIED 或明确 BPC_INCOMPLETE_PRICING。
7. Direct-DP integer objective 与 complete fixed-column IP objective 一致。
8. root LP bound <= direct-DP integer objective。
9. root LP fractional 时不声明 BPC_TREE_OPTIMAL。
10. exact/bpc 不 import torch/checkpoint/GAT/OOD。
```

---

## 10. B1 失败标准

任一情况失败：

```text
1. 根节点 local no-column 被当成 certificate。
2. direct-DP optimal 被写成 BPC_TREE_OPTIMAL。
3. BPC root LP bound > direct-DP integer objective。
4. manual RC 与 pricing RC 不一致。
5. ColumnPool 和 current RMP membership 混淆。
6. string task id 被转成 int 后出现在输出中。
7. GAT / torch 被 exact/bpc import。
```

---

## 11. Codex 禁止事项

B1 阶段不准写：

```text
full branch tree solver
GAT policy
live cuts
route-order branch
advanced completion-bound pruning
complex tail scheduler
```

先把 root BPC 的数学语义和 direct-DP 对齐写硬。
