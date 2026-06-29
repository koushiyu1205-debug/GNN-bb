# V751 RouteOpt/BKF 双 Child 均衡特征契约

日期：2026-06-29

## 背景

RouteOpt/BKF 对分支候选的核心启发是：一个 Ryan-Foster pair 不能只看单侧 child 是否好，而要看两个 child 是否同时变好、证明成本是否均衡。

我们当前 hard case 也验证了这一点：

- V631/V636 中 root pair 替换能改善 gap/fathom，但单个 root pair 仍不能闭环；
- V750 中 seed61311 能靠稳定 staged branch-cut 路径闭环，seed61635 的 lower bound 仍不动；
- 因此 branch score 后续必须学习 state-scoped 的双 child proof-cost，而不是全局 pair 偏好。

## 本轮改动

本轮只补日志和训练特征，不改变任何求解行为。

### 1. Phase1 LP child-gain 均衡字段

在 solver 内部 Phase1 child LP probe 中新增：

```text
phase1_child_lp_gain_gap
phase1_child_lp_gain_balance_ratio
phase1_cut_snapshot_child_lp_gain_gap
phase1_cut_snapshot_child_lp_gain_balance_ratio
```

含义：

- `gap = abs(same_child_gain - separate_child_gain)`
- `balance_ratio = min(gain) / max(gain)`，当两侧都没有 gain 时记为 `0`

这些字段进入：

- `journey_branch_candidates.selected`
- `journey_branch_candidates.priority_top`
- `journey_branch` selection metadata
- GAT branch action context feature schema

### 2. Phase2 heuristic child pressure 均衡字段

新增：

```text
phase2_negative_journey_balance_gap
phase2_child_wall_time_balance_gap
phase2_child_status_mismatch
```

用途：

- 判断一个候选 pair 是否把负列链/证明压力集中到某一侧 child；
- 给后续 GAT branch action 训练提供 proof-tail 辅助信号；
- 辅助 dynamic-K / BKF 诊断哪些候选虽然局部 gain 好，但子树风险不均衡。

### 3. BKF reason 可解释字段

`phased_testing_bkf_reason` 新增：

```text
phase1_child_lp_gain_gap
phase1_child_lp_gain_balance_ratio
```

当前没有给这些字段新增默认 live 权重，因此不会改变 V736/V750 这类已验证路径。

## Exact-Safe 边界

本轮改动不改变：

- official lower bound；
- pricing certificate；
- fathom/prune 条件；
- child lower bound exactness；
- cut validity；
- branch candidate 默认排序权重。

所有新增字段都是 diagnostic/training features。

## 验证

已通过静态编译：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py
```

已通过聚焦 solver 测试：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_phase1_cut_snapshot_is_diagnostic \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_weighted_score_does_not_over_penalize_small_phase2_negative \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1 \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters
```

结果：

```text
Ran 6 tests
OK
```

已通过 dataset 测试：

```text
python -m unittest BPC_future.tests.test_gat_branch_action_sanity_dataset
```

结果：

```text
Ran 1 test
OK
```

## 对主线的意义

这一步没有直接提高 20-scale OPTIMAL 数，但它补齐了下一轮训练需要的关键因果观测：

1. GAT 可以区分“单侧 child 好”和“双侧 child 都好”；
2. BKF/dynamic-K 日志可以解释候选被淘汰是因为 probe 不完整、dynamic-K 排除，还是 child pressure 不均衡；
3. 后续 score map 可以从 wall-time-only 转向 `gap/fathom/retry/child-balance` 多目标；
4. 对 seed61635 这类 dual 不动的 hard case，后续仍必须并行推进 stronger cuts/formulation。

## 下一步

1. 用 V751 字段重建/增量更新 branch action dataset。
2. 在 hard case replay 中优先采样高 `child_lp_gain_gap` 或高 `phase2_negative_journey_balance_gap` 的候选，形成 hard negative。
3. 对 seed61635 做 route-aware / rank-1-like cut diagnostic，不再只扩大普通 dynamic SRC。
4. 若 full replay 证明 balance-ratio 对 wall/gap/fathom 有稳定收益，再考虑把它作为 BKF live weight 的 opt-in 配置。
