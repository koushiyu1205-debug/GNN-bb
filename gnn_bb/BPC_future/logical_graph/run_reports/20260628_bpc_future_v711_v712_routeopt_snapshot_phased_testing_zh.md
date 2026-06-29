# 20260628 V711/V712：RouteOpt-Style Phased Testing Snapshot 修复

## 结论

本轮修复了 `routeopt_bkf_staged` 的一个关键工程问题：同一个 branch node 上，候选日志、实际分支选择、branch metadata 不能各自重跑 phased testing。

现在主流程改成：

1. 在节点分支前生成一次 `branch_decision_snapshot`；
2. `journey_branch_candidates` 日志使用该 snapshot；
3. 实际 Ryan-Foster pair 从该 snapshot 的 `priority_order[0]` 生成；
4. `journey_branch` metadata 继续使用同一 snapshot，并用实际 left/right 做 override 审计。

这样 Phase2 heuristic probe 不会因为重复运行和时间预算波动导致：

- candidate log 说选了一个 pair；
- actual branch 执行另一个 pair；
- branch-impact training row 又记录第三个 pair。

## 代码修改

主要文件：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

新增/调整：

- `_journey_branch_constraints_from_candidate`
- `_journey_branch_decision_snapshot`
- `_log_journey_branch_candidates(..., branch_decision=...)`
- `_journey_branch_selection_metadata(..., branch_decision=...)`
- branch-price 主流程两个分支点都改为 snapshot 驱动

exact-safe 边界不变：

- Phase1/Phase2 只影响候选排序和诊断字段；
- 不产生 official bound；
- 不产生 certificate；
- 不改变 fathom/prune 依据；
- child 仍继承合法旧 lower bound，最终仍靠 exact pricing closure。

## 单测

已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/scripts/audit_journey_branch_impact.py
```

已通过 RouteOpt/BKF 相关窄测试：

```text
Ran 7 tests in 0.595s
OK
```

新增回归测试：

- `test_journey_branch_decision_snapshot_feeds_log_and_metadata_without_reordering`

该测试先生成 snapshot，然后 mock 掉 `_ordered_journey_branch_candidates_for_priority`，确认 log 和 metadata 不会再次触发 ordering/probe。

## V711 Smoke

实例：

`BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json`

输出：

- `BPC_future/results/20260628_v711_routeopt_snapshot_seed61716/results.csv`
- `BPC_future/results/20260628_v711_routeopt_snapshot_seed61716/logs`

结果：

```text
status = TIME_LIMIT
time = 89.352199s
primal = 514.432848
dual = 510.748639
gap = 0.007162
nodes = 3
columns = 333
```

这不是性能验收，只用于验证日志一致性。

第一处分支事件：

```text
candidate selected_pair = [15, 19]
journey_branch left pair = [15, 19]
journey_branch selected_pair = [15, 19]
priority_selected_pair = [15, 19]
selected_pair_from_branch_override = False
```

Phase 字段：

```text
phased_testing_stage = phase2_heuristic
phased_testing_decision = probed_complete
phase1_min_child_lp_gain = 3.684208667
phase1_child_lp_gain_product = 43.257703779
phase1_child_width_balance = 61
phase2_negative_child_count = 0
phase2_wall_time = 0.063699682
```

## V712 Branch-Impact Audit

输出：

- `BPC_future/results/journey_branch_impact_v712_v711_routeopt_snapshot_seed61716/summary.json`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_impact_v712_v711_routeopt_snapshot_seed61716_zh.md`

关键字段：

```text
branch_count = 1
candidate_log_branch_count = 1
selected_match_count = 1
right_censored_branch_count = 1
usable_branch_impact_training_count = 0
run_status_counts = {"TIME_LIMIT": 1}
tail_class_counts = {"negative_chain_continues": 1}
total_child_completion_bound_retries = 0
total_child_negative_pricing_events = 4
```

训练行已透传 phased feature：

```text
task_i/task_j = 15/19
phased_testing_stage = phase2_heuristic
phased_testing_decision = probed_complete
phase1_min_child_lp_gain = 3.684208667
phase1_child_lp_gain_product = 43.257703779
phase1_child_width_balance = 61
phase2_negative_child_count = 0
phase2_negative_journey_count = 0
right_censored = True
usable_for_branch_impact_training = False
```

解释：V712 证明字段透传正确，但该样本仍是右删失，不能当 strict positive。

## 对主线的意义

这是 RouteOpt-style branch testing controller 的必要基础层。

之前的问题是：Phase2 heuristic probe 是短预算启发式，会受时间、搜索顺序和重复调用影响。如果同一个 node 重跑三次，就可能出现日志、实际分支、训练标签不一致。这样的数据不能用于训练 GAT branch action。

现在至少保证：

- 一次节点决策只产生一个 phased-testing 排序结果；
- solver 实际执行的 pair 和日志记录一致；
- branch-impact audit 看到的是实际执行 action；
- 后续 paired replay / full replay 标签不会从错误 action 起步。

## 下一步

1. 用 V711+ 日志重新生成 phased-feature delta rows，旧 V703 前后但未经过 snapshot 的日志不应作为 production branch-action 训练数据。
2. 在 hard cases 上继续做 depth1/depth2 paired replay，但每个 replay 必须用 snapshot 日志作为 source of truth。
3. branch score 训练标签继续引入双 child 均衡收益：
   - `min(child_lb_gain)`
   - `child_gain_product`
   - `child_width_balance`
   - `gap_improvement`
   - `fathom_gain`
   - `completion_bound_retry_delta`
4. 下一轮再评估 `routeopt_bkf_staged` 的性能，不把 V711 这个 90s TIME_LIMIT smoke 当性能结论。
