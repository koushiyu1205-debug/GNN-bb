# V763/V764 RouteOpt/BKF V762 Preset - seed61635 45s Smoke

日期：2026-06-29

## 目的

V762 增加了候选级 route/order conflict 特征。本轮把它做成 opt-in preset：

```text
journey_branch_candidate_phased_testing_preset = routeopt_bkf_v762
```

它继承 V736 的 staged BKF 参数，只额外给 route/order conflict 一个小的候选排序惩罚：

```text
bkf_route_order_direction_conflict_penalty = 0.25
bkf_route_order_adjacent_conflict_penalty = 0.50
```

默认 V736 不变。V762 仍只影响 branch candidate ordering，不产生 bound / certificate / prune。

## 代码变化

### 1. `routeopt_bkf_v762` preset

继承：

```text
base_priority = fractionality
phase0_min_fractionality = 0.45
phase1_max_candidates = 12
phase2_max_candidates = 3
phase2_time_limit = 0.08
dynamic_k_min_candidates = 9
dynamic_k_phase1_max_candidates = 12
dynamic_k_phase2_max_candidates = 3
dynamic_k_diverse_pool_enabled = true
dynamic_k_diverse_pool_extra_candidates = 2
```

新增：

```text
route_order_direction_conflict_penalty = 0.25
route_order_adjacent_conflict_penalty = 0.50
```

### 2. RF 候选承接摘要

`journey_branch_candidates` 新增：

```text
route_order_candidate_direction_conflict_count
route_order_candidate_adjacent_conflict_count
route_order_candidate_max_direction_conflict_mass
route_order_candidate_max_adjacent_conflict_mass
route_order_candidate_conflict_mass_tol
```

用途是判断：节点级 route/order conflict 是否落在当前可分支的 Ryan-Foster candidate 集合里。

## 验证

编译通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

focused tests 通过：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_logs_candidate_route_order_conflict \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v762_preset_adds_route_order_penalty_only
```

结果：

```text
Ran 3 tests
OK
```

## seed61635 45s smoke

实例：

```text
tasks020_07_seed61635
```

输出：

```text
BPC_future/results/20260629_v764_routeopt_bkf_v762_seed61635_45/results.csv
```

结果：

```text
status = TIME_LIMIT
primal = 561.030445
dual = 526.651393
gap = 0.061278
nodes = 3
columns = 388
cuts_added = 10
subset_row_cuts_added = 9
```

这与 V761 / V763 的 45s 结果一致，说明 V762 route-order penalty 没有推动 seed61635 的早期 bound。

## 日志解释

V764 root branch：

```text
selected_pair = [12, 20]
phased_testing_bkf_score = 64.728863019
route_order_direction_conflict_mass = 0.0
route_order_adjacent_conflict_mass = 0.0
```

root `journey_branch_candidates` 摘要：

```text
route_order_candidate_direction_conflict_count = 0
route_order_candidate_adjacent_conflict_count = 0
route_order_candidate_max_direction_conflict_mass = 0.0
route_order_candidate_max_adjacent_conflict_mass = 0.0
```

但同一 run 的节点级 route/order audit 仍有：

```text
route_order_events = 31
max_route_order_conflict_count = 1
max_route_order_conflict_mass = 1.0
```

解释：

```text
节点级 route/order conflict 存在，
但没有落在 root 的可分支 RF candidate 集合里。
```

因此，对 seed61635，单纯给 root RF candidate 加 route/order conflict penalty 不会改变 root branch，也不会改善 early dual/gap。

## 当前判断

V762 是有用的诊断/训练特征，但它不是 seed61635 的直接加速按钮。

更准确地说：

1. 若 route/order conflict 落在 fractional RF candidate 上，V762 可以让 branch testing / GAT 学到该 pair 的风险；
2. seed61635 root 的 conflict 不在 RF candidate 集合里，所以 root branch score 用不上；
3. 这支持 V761 的判断：seed61635 更可能需要 branch-state scoped route/resource cuts 或 stronger formulation，而不是继续调 root pair 权重。

## 下一步

1. 在 child nodes 继续统计 `route_order_candidate_*_conflict_count`，看 conflict 是否在 deeper states 变成可分支候选；
2. 用 V762 字段重建 branch action dataset，把“节点有 conflict 但 RF candidate 无 conflict”作为 hard context；
3. 设计 route/resource cut audit：目标不是直接 branch on conflict，而是让 formulation 看到 route/order/resource 结构；
4. full60 前先做 hard-case smoke，不再把 route-order penalty 直接推到全量。
