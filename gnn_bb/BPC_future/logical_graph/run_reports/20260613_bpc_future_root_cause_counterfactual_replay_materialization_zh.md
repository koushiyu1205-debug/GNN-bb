# Counterfactual Replay Materialization 审计报告

日期：2026-06-13

## 目标

本轮仍然只做只读诊断，不运行 BPC、不接 driver、不改 production pricing path。

上一轮 readiness 审计说明：首批 replay candidates 不是 exact replay payload。本轮进一步检查一个更窄的问题：

> 给定当前 observational descriptor 中的 `sequence + arc_family + recovered start_time`，能否解析到具体 `ArcOption` 并通过现有 `evaluate_timed_trip()` / Phase 3A materialization helper 物化为 `TimedTrip`？

这个检查用于区分两类问题：

1. descriptor 本身是否连可行 TimedTrip 都不能构造；
2. descriptor 可以构造局部 trip，但仍缺 exact replay 所需的完整 batch / RMP / dual / cut 快照。

## 输入

候选 manifest：

```text
BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/summary.json
```

candidate rows：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv
```

脚本：

```text
BPC_future/scripts/audit_counterfactual_replay_materialization.py
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_materialization_20260613/summary.json
```

## 实例路径解析

这轮确认 3 个 replay candidates 使用的是 calibration 脚本里的实例别名，而不是当前默认 balanced-60 实例名直接查找：

```text
mt20_greedy_tranq_01
  BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json

mt20_greedy_apollo_01
  BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json

tranq20_01
  BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_20/tranquillitatis_balmer_like_20km_tasks20_01_seed21000_logical_graph.json
```

这说明未来 replay harness 必须显式记录 `instance_path`，不能只记录短实例名。

## 汇总结果

```text
recommended_candidate_count = 3
descriptor_count = 6
entry_count = 27
materialized_entry_count = 27
observed_descriptors_materialized = 6
complete_descriptors_materialized = 5
```

检查：

```text
recommended_candidates_present = true
all_instances_loaded = true
all_observed_entries_materialized = true
not_all_complete_descriptors_materialized = true
still_not_exact_replay_payload = true
```

含义：

- 所有 3 个实例都能按别名路径加载；
- 27 个已观测 descriptor entries 都能从 `arc_family` 唯一解析到 concrete `ArcOption`；
- 27 个已观测 descriptor entries 都能用 recovered `start_time` 通过 `materialize_pulse_sortie()` 物化；
- 但完整 descriptor 只有 5/6 个可完整物化；
- 仍不能做 exact replay，因为这只是 `TimedTrip` 局部物化，不是完整 `JourneyColumn batch + RMP/dual/cut snapshot`。

## 候选明细

### replay_candidate_001

```text
context = mt20_greedy_tranq_01 | cg_iter=2 | heuristic | active=5c6420f757a39d2d | rmp=761.814403
```

improved descriptor：

```text
sequence = 2,7,9
arc_option_ids =
  0->2:low_risk:2
  2->7:low_risk:1
  7->9:low_risk:1
  9->0:low_risk:2
start_time = 47.875727
materialized = true
```

worsened descriptor：

```text
sequence = 17,10,9,7
arc_option_ids =
  0->17:low_energy:1
  17->10:low_time:0
  10->9:low_risk:2
  9->7:low_risk:1
  7->0:low_energy:1
start_time = 0.0
materialized = true
```

### replay_candidate_003

```text
context = mt20_greedy_apollo_01 | cg_iter=3 | heuristic | active=16862add48072518 | rmp=780.586496
```

结果：

```text
improved returned_count = 8
improved materialized entries = 8
worsened returned_count = 8
worsened materialized entries = 8
```

示例 improved entry：

```text
sequence = 14,18,5
arc_option_ids =
  0->14:low_time:0
  14->18:low_risk:2
  18->5:low_time:0
  5->0:low_time:0
start_time = 17.485936
materialized = true
```

示例 worsened entry：

```text
sequence = 14,18,4
arc_option_ids =
  0->14:low_energy:1
  14->18:low_time:0
  18->4:low_time:0
  4->0:low_time:0
start_time = 37.886889
materialized = true
```

### replay_candidate_004

```text
context = tranq20_01 | cg_iter=1 | heuristic | active=aa2b834c9d43f2a6 | rmp=838.004841
```

结果：

```text
improved returned_count = 12
improved observed entries = 8
improved materialized entries = 8
improved missing entries due to sampling = 4
worsened returned_count = 1
worsened materialized entries = 1
```

示例 common entry：

```text
sequence = 20,15,5
arc_option_ids =
  0->20:low_risk:2
  20->15:low_risk:2
  15->5:low_risk:2
  5->0:low_risk:2
start_time = 0.0
materialized = true
```

这个候选仍适合作为 stress context，但 improved batch 被日志采样截断，不能直接 exact replay。

## 对根因判断的影响

这轮把 replay 缺口进一步拆清楚了：

1. `arc_family` 在这 3 个候选实例中足以唯一解析到 concrete `ArcOption`；
2. 已观测 entries 的 `sequence + arc_option_ids + start_time` 可以通过现有 materialization helper 构造 `TimedTrip`；
3. 因此下一步 replay 的主要阻塞不是路径 family 不唯一，也不是 TimedTrip 物化失败；
4. 主要阻塞是日志层面缺 full returned batch、full JourneyColumn signatures、source run identity、RMP pool、true dual、cuts；
5. 这再次说明：现有 observational logs 能定位实验方向，但不能直接证明 production selector。

## 结论

首批 replay candidates 的局部 trip 物化是可行的，但 exact controlled replay 仍未就绪。

下一步如果继续，应实现 no-certificate-effect replay capture / harness，至少捕获：

- `instance_path`；
- source log path / repeat；
- full returned `JourneyColumn.signature`；
- full `TimedTrip` signatures；
- concrete arc option ids；
- start times；
- true reduced cost per journey；
- RMP pool snapshot；
- true dual snapshot；
- cut snapshot；
- replay 后下一轮 RMP objective / dual / active hash / pricing state。

在这之前，不能把任何 selector / worker / returned policy 当作已证明的优化方向。
