# BPC_future V4：support-aware GAT true-RC filter 在 random-TW 20 seed61000 上的对照

日期：2026-06-23

## 结论

本轮把 GAT/learning 产生的 true-RC negative 列从“只按 reduced cost 强弱截断”改为 20-scale opt-in 的 support-aware 排序：

```yaml
journey_learning_true_rc_support_aware_filter_enabled: True
journey_learning_true_rc_support_overlap_threshold: 0.6
```

该策略只改变已通过真实 reduced cost 校验的负列加入顺序/保留顺序，不提供 certificate，不参与 lower bound 或 pruning。

结果：对 canonical random-TW 20 seed61000 有局部收益，但仍未达到 200 秒最优目标。

## 实例

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/
apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
```

## 对照结果

### 200 秒

输出：

```text
BPC_future/results/20260623_v4_support_aware_gat_200_randomtw20_seed61000.csv
```

结果：

- `EXTERNAL_TIME_LIMIT`
- wall time `200.019183s`
- root 在约 `106.50s` 完成 `exact_completion_bound_retry`
- node 1 在约 `154.86s` 完成普通 exact `no_negative_journey`
- 随后进入 node 1 final completion-bound probe，200 秒外部时限前未返回

### 300 秒

输出：

```text
BPC_future/results/20260623_v4_support_aware_gat_300_randomtw20_seed61000.csv
```

结果：

- `EXTERNAL_TIME_LIMIT`
- wall time `300.019277s`
- root 在约 `105.70s` 完成 `direct_label_no_negative_journey`
- node 1 在约 `181.37s` 返回 `FRONTIER_BOUND_INCOMPLETE`
- node 2 在约 `233.31s` 完成 `direct_label_no_negative_journey`
- node 3 到约 `276.01s` 进入 hidden-negative/final-probe 区域，外部 300 秒时限前未闭合

## 相对上一轮 weak-final-probe 对照

上一轮 300 秒对照：

```text
BPC_future/results/20260623_v4_weak_final_probe_300_randomtw20_seed61000.csv
```

关键位置：

- root completion-bound certificate：约 `124.82s`
- node 1 completion-bound incomplete：约 `248.77s`
- 最终内部 `TIME_LIMIT`，solve time `284.406915s`

support-aware GAT 对照：

- root completion-bound certificate：约 `105.70s`
- node 1 completion-bound incomplete：约 `181.37s`
- 搜索推进到 depth=2 node 3，但仍被 final-probe/hidden-negative tail 卡住

## GAT 是否真正用上

本轮 JSONL 中：

```text
journey_learning_true_rc_filter events = 41
kept true-RC negative journeys = 63
support-aware candidate active-support-changing = 55
support-aware selected active-support-changing = 38
selected new task-set journeys = 61
selected replacement journeys = 2
```

列加入日志：

```text
journey_column_addition events = 37
added journeys = 112
active_replacement_task_set events = 4
changed_inactive_only events = 33
active_changed_task_sets = 5
inactive_changed_task_sets = 107
```

解释：

- GAT/learning 不再只是按最负 reduced cost 选列；
- support-aware 排序确实把一部分候选转向 active-support-changing；
- 但实际加入后仍以 inactive-only 为主；
- 因此它能缩短 root/部分 branch 前段 CG，却不能解决 final-probe frontier LB 太松。

## 当前阻塞

node 1 的 final probe 仍返回：

```text
pricing_proof_kind = FRONTIER_BOUND_INCOMPLETE
global_remaining_rc_lb ≈ -426.051784
frontier_region_count = 23470
corrected_node_lb ≈ -6662.658869
```

这说明当前 corrected-bound 无法剪枝，不是因为 GAT 没有找列，而是因为未探索 frontier 的安全 reduced-cost 下界太松。

## 决策

保留该策略为 20-scale 配置默认 opt-in：

- 文件：`BPC_future/configs/moon_trek_20_smoke.yaml`
- 5/10 配置不启用该策略，避免扩大 no-regression 风险
- 单测锁定：`BPCFutureTests.test_mainline_learning_anchor_configs_are_exact_safe`

后续主攻仍然是：

1. 收紧 direct-label final probe 的 frontier suffix bound；
2. 降低 hidden-negative / final-probe tail；
3. 继续让 GAT 学 branch-impact 和 proof-tail ROI，而不是只学 true-RC hit。

