# V758-V759 Weighted Rank-1 Cut Audit

日期：2026-06-29

## 目的

V754-V757 已经说明：

```text
普通 SRC 能进入 RMP、binding、且有 nonzero cut dual，
但 seed61635 的 best dual 始终卡在 526.651393。
```

因此本轮不再继续只扩大普通 SRC，而是建立下一类 stronger cut 的 exact-safe 诊断入口：

```text
weighted rank-1-like task cut
coeff(column) = floor(sum_i weight_i * a_i(column) / denominator)
rhs = floor(sum_i weight_i / denominator)
```

它是普通 SRC 的加权泛化。当前只做 audit，不加入 RMP，不进入 pricing，不产生 official bound / certificate / prune。

## 代码变化

新增：

- `WeightedSubsetRowCut`
  - 文件：`BPC_future/core/cuts.py`
  - 字段：`tasks`, `weights`, `denominator`
  - 默认 `kind=weighted_subset_row`
  - 只定义 cut contract / payload / coefficient。

- `journey_weighted_rank1_cut_audit`
  - 文件：`BPC_future/solver/journey_driver.py`
  - root 和 branch node 的 RMP optimal 后记录。
  - 默认关闭：`journey_weighted_rank1_cut_audit_enabled=False`
  - 事件明确包含：

```text
audit_only=True
production_ready=False
pricing_supported=False
official_bound_effect=False
certificate_effect=False
```

默认不生成 uniform weights，避免把普通 SRC k=3/k=4 误当成新信号。若需要对照，可显式开启：

```text
journey_weighted_rank1_cut_audit_include_uniform_src=True
```

随后补齐了 live-RC 基础支持，但仍未默认启用 weighted cut 加入：

- `BPC_future/master/journey_rmp.py`
  - `_journey_cut_coefficient()` 支持 `weighted_subset_row`。
  - `manual_journey_reduced_cost()` 通过统一 cut coefficient 自动计入 weighted cut dual。

- `BPC_future/pricing/journey_pricing.py`
  - `_journey_cut_dual_value()` 支持 weighted row 的 mask coefficient。
  - `_journey_pricing_cut_supported()` 识别 `weighted_subset_row`。
  - `_cut_masks()` 对 weighted row 记录 `(denominator, weighted_bits)`。
  - completion-bound / profile pruning 对 nonzero weighted cut dual 仍 fail-closed，不把 weighted cut 用进 optimistic pruning。

这一步只是把“如果未来 opt-in 添加 weighted cuts，true reduced cost 不会算错”的底座补上；当前没有 separator 会把它们加入 RMP，也没有 production 配置默认打开。

## 验证

通过：

```text
python -m py_compile \
  BPC_future/core/cuts.py \
  BPC_future/master/journey_rmp.py \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

通过聚焦测试：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_pricing_compatible_cut_coefficients_and_duplicates \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_weighted_subset_row_live_pricing_is_rc_consistent_and_fail_closed_for_bounds \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_weighted_rank1_cut_audit_logs_candidates_without_bound_effect \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_audit_logs_violations_without_adding_cuts \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_cut_dual_diagnostics_logs_binding_subset_row_dual
```

结果：

```text
Ran 5 tests
OK
```

## Seed61635 45s 诊断

实例：

```text
tasks020_07_seed61635
```

配置：

- RouteOpt/BKF staged preset：`routeopt_bkf_v736`
- dynamic SRC：on，gate best violation `0.25`
- weighted rank-1 audit：on，denominators `3,4`
- time limit：45s

输出：

```text
BPC_future/results/20260629_v759_weighted_rank1_nonuniform_audit_seed61635_45/
```

求解结果：

```text
status = TIME_LIMIT
primal = 561.030445
dual = 526.651393
gap = 0.061278
nodes = 3
columns = 388
```

该结果与 audit-only 预期一致：weighted audit 没有改变求解行为，也没有移动 dual。

## Audit 结果

weighted rank-1 audit：

```text
weighted_events = 31
violated_events = 19
max_best_violation = 0.666666667
include_uniform_src = False
```

典型候选：

```text
node0 cg5:
tasks=[2,10,12,20]
weights=[2,1,1,1]
denominator=3
rhs=1
violation=0.333333333

node1 depth1 cg7:
tasks=[11,15,17,18]
weights=[1,1,1,2]
denominator=3
rhs=1
violation=0.666666667
```

普通 SRC 同 run 对照：

```text
src_events = 6
src_violated_events = 5
src_max_best_violation = 0.5
src_added_total = 9
```

cut-dual 对照：

```text
cut_dual_events = 31
nonzero_events = 12
max_cut_dual_abs_sum = 6.960402857
```

## 解释

这轮结果说明：

1. 非均匀 weighted rank-1 rows 在 seed61635 的 fractional RMP 中确实有 violation；
2. 它们不是普通 uniform SRC 的重复信号；
3. 但当前只是 active-RMP audit，不能说明它们能提高 full LP lower bound；
4. 也不能直接上线，因为 pricing / completion-bound / dominance 还没有声明支持。

因此它是一个值得继续推进的 cut family 候选，但还不是 production cut。

## Exact-Safe 边界

当前没有改变：

- RMP constraints；
- 默认 pricing / RMP 行为；
- completion-bound pruning；
- task-set dominance；
- branch selection；
- official lower bound / fathom / certificate。

所有 weighted rank-1 事件都是 diagnostic-only。

已补齐但未默认触发：

- weighted cut 在 RMP / manual RC / pricing cut dual value 中的一致 coefficient；
- nonzero weighted cut dual 下的 completion-bound / profile-pruning fail-closed。

## 下一步

下一步不能直接把 weighted cut 加进默认 RMP。应按以下顺序推进：

1. 小规模穷举验证：所有 feasible integer journeys 满足 weighted rank-1 inequality；
2. 做一个显式 opt-in 的 weighted separator，默认仍关闭；
3. live separator 只在 root / 指定 hard-node 上试跑，记录 cut dual、RMP dual、true pricing closure；
4. 对 task-set dominance，只有确认 weighted coefficient 仍只依赖 task mask 后才允许；
5. seed61635 with-cut opt-in 对照，看 best dual 是否从 `526.651393` 移动；
6. 若 dual 移动，再评估是否纳入 RouteOpt/BKF preset；若不移动，继续往 route/order/resource-aware formulation 或 incumbent/cuts 联动推进。

如果 with-cut 后 dual 仍不动，说明问题不是 rank-1-like task cut，而要继续往 route/order/resource-aware formulation 或 incumbent/cuts 联动推进。
