# V762 Route/Order 候选级 BKF 特征契约

日期：2026-06-29

## 目的

V761 已经把 route/order region 做成节点级 audit，但它只能说明当前 active RMP 的整体形态，不能告诉 branch controller：

```text
某一个 Ryan-Foster pair 是否正好处在 route/order 冲突区域。
```

因此 V762 补的是候选级 route/order 风险特征，让 `routeopt_bkf_staged`、replay runbook 和 GAT branch action dataset 都能看到同一类 state-scoped 信号。

## 本轮改动

### 1. Solver 候选级 route/order metrics

在 branch candidate 生成时，对每个 pair 记录当前 active support 中的方向关系：

```text
route_order_same_route_mass
route_order_i_before_j_mass
route_order_j_before_i_mass
route_order_direction_conflict_mass
route_order_direction_balance_ratio
route_order_adjacent_i_before_j_mass
route_order_adjacent_j_before_i_mass
route_order_adjacent_conflict_mass
route_order_adjacent_balance_ratio
```

这些字段进入：

- `journey_branch_candidates.selected`
- `journey_branch_candidates.top`
- `journey_branch_candidates.priority_top`
- `journey_branch` selection metadata

含义：

- `direction_conflict_mass`：同一候选 pair 在 active route 中同时出现 `i before j` 和 `j before i` 的质量；
- `adjacent_conflict_mass`：进一步要求二者相邻；
- `balance_ratio`：两种方向质量的均衡程度。

### 2. BKF reason / 可选惩罚项

`_journey_branch_candidate_phased_bkf_score()` 现在会在 reason 中输出：

```text
route_order_direction_conflict_mass
route_order_direction_balance_ratio
route_order_adjacent_conflict_mass
route_order_adjacent_balance_ratio
```

新增两个默认关闭的 live 权重：

```text
journey_branch_candidate_phased_testing_bkf_route_order_direction_conflict_penalty = 0.0
journey_branch_candidate_phased_testing_bkf_route_order_adjacent_conflict_penalty = 0.0
```

默认值为 `0.0`，所以不会改变 V736/V750 已验证的 branch path。只有显式 opt-in 时，BKF 排序才会对 route/order 冲突候选做惩罚。

### 3. Replay runbook

`build_journey_branch_candidate_replay_runbook.py` 现在会把候选级 route/order 字段写成：

```text
source_alt_route_order_*
```

离线 RouteOpt/BKF 采样分数也会轻微惩罚：

```text
route_order_direction_conflict_mass
route_order_adjacent_conflict_mass
```

这只影响 replay 采样顺序，不运行 BPC/pricing/RMP，不产生 bound 或 certificate。

### 4. Branch action dataset

GAT branch action context feature schema 新增：

```text
route_order_candidate_same_route_mass
route_order_candidate_i_before_j_mass
route_order_candidate_j_before_i_mass
route_order_candidate_direction_conflict_mass
route_order_candidate_direction_balance_ratio
route_order_candidate_adjacent_conflict_mass
route_order_candidate_adjacent_balance_ratio
```

配合 V761 的节点级 route/order audit 字段，后续训练可以同时看到：

- 节点整体 route/order 平台；
- 当前候选 pair 自身是否位于冲突区域。

## Exact-Safe 边界

本轮仍然不改变：

- official lower bound；
- pricing certificate；
- fathom/prune 条件；
- child lower bound exactness；
- cut validity；
- 默认 V736/V750 branch path。

新增字段只用于：

```text
diagnostic
candidate ordering when explicitly opt-in
offline replay sampling
GAT training features
```

## 验证

编译通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_journey_branch_candidate_replay_runbook.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py
```

focused tests 通过：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook
```

结果：

```text
Ran 23 tests
OK
```

solver focused tests 通过：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_logs_candidate_route_order_conflict \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_weighted_score_does_not_over_penalize_small_phase2_negative \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters
```

结果：

```text
Ran 4 tests
OK
```

## 对主线的意义

这一步仍不是 full60 加速实验，因此不会改变当前最好成绩：

```text
V545 = 36/60 OPTIMAL, capped mean 341.54s
```

它推进的是 Branch Score 主线里的两个关键缺口：

1. `routeopt_bkf_staged` 不再只看 fractionality、child width、child LP gain 和 negative pressure，也能记录候选 pair 的 route/order 冲突风险；
2. 后续 GAT 训练可以学习“这个 state 下的这个 pair 是否处在 route/order 风险区域”，而不是继续学全局 pair 偏好。

## 下一步

1. 用 V762 字段重建 branch action dataset。
2. 在 hard-case replay 中对高 route-order conflict 的 pair 采样 hard negative / proof-cost 标签。
3. 设计一个 opt-in `routeopt_bkf_v762` preset，小规模比较 route-order penalty 是否改善 seed61635 类 proof tail。
4. 若 penalty 只改善排序但 dual 仍不动，继续推进 branch-state scoped route/resource cuts，而不是全局 task-set rows。
