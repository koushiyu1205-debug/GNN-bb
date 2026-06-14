# BPC_future 根因审计补充：stage-aware selector audit

日期：2026-06-13

## 目标

前两轮结论：

1. returned batch 的 aggregate low-overlap 是强 root-cause feature candidate；
2. 但 Apollo20 return12 r2 是低 overlap 却 worsened 的关键 false positive；
3. false positive 的直接原因是 cg3 退化为 weak-RC、active-redundant 的 `[2,20]` family，加入后 RMP objective / active hash 不动。

本轮继续只读分析：

**把 early returned batch 拆成 CG stage 级别，加入当前 active top samples 的关系，检查 stage-aware 特征是否比 aggregate low-overlap 更接近根因。**

本轮不改 solver、不改 pricing、不改 RMP、不改 Pulse、不跑新 benchmark。

## 数据

主分析集仍为：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- 对应 `logs/*.jsonl`
- 18 个非 baseline 20-task rows；
- improved 10 行；
- worsened 8 行。

每个 run 提取前三个 heuristic `journey_pricing` 的完整 returned task-set list：

- `diagnostic_selected_returned_task_set_samples`

同时读取对应 CG 的：

- `journey_pool_structure_diagnostics.pool_active_top_task_set_value_samples`
- `journey_pool_structure_diagnostics.pool_active_task_set_hash`
- `journey_pool_structure_diagnostics.pool_active_fractional_value_sum`
- 下一轮 `journey_rmp.objective`
- 下一轮 active hash / fractional sum

## Stage-level 特征

对每个 CG stage 计算：

- batch pairwise overlap / Jaccard；
- batch union；
- max task frequency；
- returned count；
- best RC；
- batch 到当前 active top samples 的平均最大 Jaccard；
- batch 到当前 active top samples 的平均最大 overlap；
- active-redundant fraction：returned sets 中 max active overlap >= 2/3 的比例；
- post-addition objective delta；
- post-addition active hash 是否变化；
- post-addition fractional sum delta。

注意：

- post-addition objective / active hash 是结果诊断，不是上线 selector 可用的前置特征；
- current active relation 是 addition 前可见的；
- returned batch 特征仍属于 returned 后可见，若要变成 selector，需要在 candidate-list 层模拟。

## Aggregate by outcome

### CG1

| outcome | rows | pair_overlap | active_avg_overlap | active_redundant_frac | best_rc | objective_delta | frac_delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| improved | 10 | 0.437879 | 0.550000 | 0.125000 | -59.880046 | -81.378176 | -2.600000 |
| worsened | 8 | 0.410376 | 0.820312 | 0.671875 | -101.990051 | -171.271821 | +0.593750 |

CG1 上，worsened rows 反而有更强 RC、更大 objective drop，但它们到当前 active top samples 更冗余。

这再次证明：

> early objective drop / best RC 更强，不等于后续 trajectory 更好。

### CG2

| outcome | rows | pair_overlap | active_avg_overlap | active_redundant_frac | best_rc | objective_delta | frac_delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| improved | 10 | 0.498268 | 0.568750 | 0.337500 | -52.472196 | -41.816175 | +2.025000 |
| worsened | 8 | 0.436147 | 0.657986 | 0.614583 | -70.909295 | -45.174315 | +2.266827 |

CG2 继续显示 worsened rows 更 active-redundant，且 best RC 更强。

### CG3

| outcome | rows | pair_overlap | active_avg_overlap | active_redundant_frac | best_rc | objective_delta | frac_delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| improved | 10 | 0.385768 | 0.565972 | 0.316667 | -33.966075 | -29.206518 | -1.085714 |
| worsened | 8 | 0.312500 | 0.388021 | 0.328125 | -13.604258 | -6.786567 | -0.235577 |

CG3 aggregate 不如 CG1/CG2 直接，因为不同 instance 的 trajectory 已经分叉；但 Apollo false positive 正是在 cg3 被解释出来。

## Stage-level separability

只用 Phase 10H 18 行拟合单特征阈值。

最强 stage-aware 前置特征：

```text
cg1_active_avg_overlap <= 0.5
accuracy = 17 / 18 = 0.944444
tp = 9
fp = 0
tn = 8
fn = 1
```

等价强信号：

```text
cg1_active_avg_jacc <= 0.2875
accuracy = 17 / 18
tp = 9
fp = 0
tn = 8
fn = 1

cg1_active_redundant_frac <= 0.08333333333333333
accuracy = 17 / 18
tp = 9
fp = 0
tn = 8
fn = 1
```

解释：

- 这个规则没有 false positive；
- 它能过滤掉所有 worsened rows；
- 但它漏掉了一个真实 improved row。

唯一 false negative 是：

```text
mt20_greedy_apollo_01
experimental_early_new_task_set_quota_3_20_only
repeat = 2
outcome = improved
```

这个 row 的 cg1 active relation 很冗余：

```text
cg1 active_avg_overlap = 1.0
cg1 active_redundant_frac = 1.0
```

但它后续在 cg3 通过 `[5,10,18]` / `[5,14,18]` family 改写了 active basis。

因此：

> cg1 active-redundancy 是强 negative filter，但不是完整 positive selector。

## Apollo r2 的 stage-aware 解释

### return8 r2 improved

```text
cg1:
  returned = 8
  best_rc = -139.913748
  active_avg_overlap = 1.000
  active_redundant_frac = 1.000
  objective_delta = -202.197
  active_hash_changed = True

cg2:
  returned = 8
  best_rc = -123.353561
  active_avg_overlap = 0.688
  active_redundant_frac = 0.375
  objective_delta = -78.771
  active_hash_changed = True

cg3:
  returned = 8
  best_rc = -20.1912655
  active_avg_overlap = 0.479
  active_redundant_frac = 0.125
  objective_delta = -10.375
  active_hash_changed = True
```

关键：

- cg1 看起来很冗余；
- 真正的正向分叉发生在 cg3；
- cg3 batch 的 active redundancy 降低，并实际改变 RMP objective / active hash。

### return12 r2 worsened

```text
cg1:
  returned = 12
  best_rc = -139.913748
  active_avg_overlap = 1.000
  active_redundant_frac = 1.000
  objective_delta = -238.007
  active_hash_changed = True

cg2:
  returned = 12
  best_rc = -73.862591
  active_avg_overlap = 0.722
  active_redundant_frac = 0.583
  objective_delta = -58.238
  active_hash_changed = True

cg3:
  returned = 4
  best_rc = -6.110727
  active_avg_overlap = 0.583
  active_redundant_frac = 0.500
  objective_delta = 0.000
  active_hash_changed = False
```

关键：

- return12 前两轮把 context 推到另一条轨迹；
- 到 cg3 时，只剩 weak-RC `[2,20]` family；
- 该 batch 与当前 active top samples 更冗余；
- 加入后 RMP objective / active hash 完全不动；
- 下一轮直接进入 incomplete tail。

## 这说明什么

### 1. Aggregate low-overlap 不够

return12 r2 的前三轮 aggregate overlap 很低，但 cg3 marginal batch 无效。

所以 selector 不能只看：

- first3 aggregate overlap；
- first3 aggregate union；
- first3 aggregate Jaccard；
- returned count。

### 2. Stage-aware active relation 更接近机制

CG1 active-redundancy threshold 能无 false-positive 地排除所有 worsened rows，但会漏掉 Apollo return8 r2。

这说明它适合作为 negative filter，不适合作为完整 positive rule。

### 3. Positive selector 需要 late-stage bridge detection

Apollo return8 r2 的好处不是 cg1，而是 cg3：

- cg3 returned batch active redundancy 降低；
- cg3 objective delta 非零；
- cg3 active hash 改变；
- cg3 fractional sum 从 7.0 变为 0。

这类信号不能用单个 early aggregate metric捕捉。

### 4. 后验 movement 不能直接上线

`objective_delta` 和 `active_hash_changed` 是 batch 加入后的结果，不能作为 addition 前 selector。

但它们能作为 offline label：

- 用来训练/校准 candidate-list 前置特征；
- 用来判断某个 batch 是否真的有 marginal bridge value；
- 用来排除“低 overlap 但加了也不动”的 batch。

## 当前根因更新

当前根因更精确地收紧为：

> 20-task hard-tail 的关键不是“返回更多列”或“返回更低 overlap 的列”，而是需要在每个 CG stage、当前 active basis context 下，选择能降低 active redundancy、桥接 fractional active families，并具有 marginal RMP movement 潜力的 concrete JourneyColumn signature batch。现有 return8/return12、rough-RC 排序、Pulse worker、global low-overlap rule 都没有这个 stage/context 选择能力。

## 下一步建议

仍然只能 calibration-only：

1. 构造 stage-aware per-batch dataset：
   - 每个 `journey_pricing` returned batch 一行；
   - 特征为 addition 前可见：
     - batch overlap / Jaccard；
     - relation to current active top samples；
     - active-redundant fraction；
     - RC distribution；
     - sequence / signature / start-time / arc-option family diversity；
     - current RMP fractional pressure；
   - 标签为 addition 后可见：
     - objective_delta；
     - active_hash_changed；
     - fractional_sum_delta；
     - subsequent incumbent / tail outcome；
2. 优先验证 negative filter：
   - `cg1_active_avg_overlap <= 0.5` 类信号是否能在更大 hard set 上无 false-positive 地过滤坏 batch；
3. 再验证 positive bridge rule：
   - 必须解释 Apollo return8 r2 的 cg3 positive bridge；
   - 必须排除 Apollo return12 r2 的 cg3 `[2,20]` active-redundant no-op batch；
4. 在以上通过前，不做 production A/B。

## 目标状态

目标仍未完成。

本轮进一步证明了根因所在机制，但也说明没有一个简单低-overlap selector 足够。下一步需要 stage-aware / context-aware offline dataset，而不是继续调全局 returned count、Pulse worker、DP cap 或 certificate gate。

