# V188-V192 Greedy-Apollo Seed61716 Branch Positive

日期：2026-06-24

## 结论

seed61716 不再只是“找不到正例”的状态。本轮在 canonical random-TW 20-scale 60-instance 集合内，找到一个新的闭环强正例：

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
baseline root pair = [4,12]
alternative root pair = [12,15]
baseline wall = 253.703779s
alternative wall = 167.174268s
wall_delta = -86.529511s
label_type = strong_positive
```

该 pair 把该 20-scale 实例从 200s 目标线外拉到 200s 内。

## 标签修正

本轮按 `624.2` 审阅意见补齐了显式多级标签：

```text
strong_positive
budget_dominant_improvement
local_only_hard_negative
regression
unknown_right_censored
```

相关脚本版本：

```text
tail_action_counterfactual_delta schema = v4
tail_action_counterfactual_delta_audit schema = v3
branch_counterfactual_delta schema = v4
branch_counterfactual_delta_audit schema = v4
```

边界保持 conservative：预算优势样本不会升级为 `y_whole_run_improved`；局部 child proof-cost 下降但全 run 退化时，只作为 hard negative / regression。tail-action 反事实在日志可用时还会检查 completion-retry proof-work payback，避免把 sibling/deeper subtree 回吃误标成正例。

## V190 Replay

V190 root layered runbook：

```text
output = BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624
source_selected_pair = [4,12]
candidate_selection = layered
candidate_log_top_n = 200
entry_count = 6
```

已执行前 4 个：

```text
[5,13]  -> TIME_LIMIT,          wall=275.988135
[5,14]  -> EXTERNAL_TIME_LIMIT, wall=280.015137
[8,20]  -> EXTERNAL_TIME_LIMIT, wall=280.017030
[12,15] -> OPTIMAL,             wall=167.174268
```

## V192 Counterfactual

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v192_v190_greedy_apollo_seed61716_root_layered_replay4_20260624
matched_counterfactual_count = 4
forced_pair_matched_count = 4
status_pair_counts = {'OPTIMAL->EXTERNAL_TIME_LIMIT': 2, 'OPTIMAL->OPTIMAL': 1, 'OPTIMAL->TIME_LIMIT': 1}
counterfactual_label_type_counts = {'regression': 3, 'strong_positive': 1}
wall_improvement_positive_count = 1
timeout_regression_count = 3
minimal_counterfactual_signal_ready = true
strict_counterfactual_training_ready = false
counterfactual_training_ready = false
```

`[12,15]` 的 full-run delta：

```text
pricing_calls_delta = -10
exact_pricing_calls_delta = -5
node_count_delta = -2
solving_time_delta = -86.190139
gap_delta = 0
```

## 当前含义

现在的问题不是没有正例，而是正例覆盖仍不足：

```text
known clean anchors:
- greedy-anchor/tranquillitatis seed61001 root [2,6]
- sector-wave/apollo seed61408 root [6,16]
- greedy-anchor/apollo seed61716 root [12,15]
```

还不能直接训练 production branch GAT。当前只证明了一个 parent context 上的 minimal counterfactual signal；严格训练门槛仍要求 strong positives 跨多个 parent contexts、instances、time-window families，并保留 positive holdout。下一步应继续在 canonical random-TW 20-scale 60-instance 内按 layered/full-replay 找更多 parent context。

## 后续 opt-in 复验

V193-V197 已把该正例接入 score map 并做非强制 solver opt-in：

```text
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_v193_v197_greedy_apollo_seed61716_score_optin_zh.md
optin selected root pair = [12,15]
optin wall = 163.102069s
baseline full600 wall = 253.703779s
wall_delta = -90.601710s
exact_pricing_calls_delta = -5
node_count_delta = -2
```

这证明本 context 的 `ranking rows -> score map -> branch_score_horizon` 链路能真实改变求解行为，但仍只是单实例 in-context 证据。
