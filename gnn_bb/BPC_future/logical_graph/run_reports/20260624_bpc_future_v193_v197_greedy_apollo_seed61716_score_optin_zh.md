# V193-V197 Greedy-Apollo Seed61716 Score Opt-in

日期：2026-06-24

## 结论

V193-V197 把 seed61716 的强正例从 forced replay 推进到非强制 solver opt-in：

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
baseline = full600 default, OPTIMAL, wall=253.703779s, node_count=5
opt-in = branch_score_horizon + V194 score map, OPTIMAL, wall=163.102069s, node_count=3
wall_delta = -90.601710s
exact_pricing_calls_delta = -5
node_count_delta = -2
root pair = [12,15]
```

该结果说明 score map 不是只在离线 replay 表里好看；在真实求解时，它能把 root pair 调度到 `[12,15]`，并在这个 canonical 20-scale 实例上把求解时间推入 200s 以内。

## V193 Ranking

```text
output = BPC_future/results/journey_branch_counterfactual_ranking_v193_v192_greedy_apollo_seed61716_root_layered_replay4_20260624
context_count = 1
context_counts = {'mixed_positive_negative_context': 1}
counterfactual_row_count = 4
ranking_pair_count = 5
minimal_ranking_signal_ready = true
strict_ranking_training_ready = false
ranking_training_ready = false
proxy_contradiction_counts = {'fewer_child_negative_but_regressed': 3}
```

V193 同时保留了三条 regression 负例，因此这个 context 不是纯正例重复灌水。但它仍只有一个 parent context、一个 instance、一个 time-window family，且没有 positive holdout context；因此只能算 minimal ranking signal，不是 production branch GAT 的严格训练 ready。

## V194 Score Map

```text
output = BPC_future/results/journey_branch_score_map_v194_v193_greedy_apollo_seed61716_root_layered_replay4_20260624
branch_score_map_entry_count = 4
top_pair = [12,15]
top_score = 3.4249861
```

## V195 Non-forced Opt-in

```text
csv = BPC_future/results/20260624_v195_branch_score_horizon_v194_greedy_apollo_seed61716_220.csv
log_dir = BPC_future/results/logs_20260624_v195_branch_score_horizon_v194_greedy_apollo_seed61716_220
status = OPTIMAL
wall = 163.102069s
solving_time = 161.044551s
node_count = 3
pricing_calls = 43
exact_pricing_calls = 17
selected root pair = [12,15]
branch_score = 3.4249861
branch_score_source = node:0:depth:0:12,15
```

该 run 没有 forced pair；score 只用于 branch candidate priority，official bound 和 certificate 仍由原 exact 求解流程产生。

## V196/V197 Audit

V196 branch-impact：

```text
output = BPC_future/results/journey_branch_impact_audit_v196_v195_greedy_apollo_seed61716_score_horizon_20260624
branch_count = 1
priority_mode_counts = {'branch_score_horizon': 1}
selected_pair = [12,15]
branch_rank_in_top = 12
branch_rank_in_priority_top = 0
run_status_counts = {'OPTIMAL': 1}
```

V197 A/B：

```text
output = BPC_future/results/journey_branch_score_ab_audit_v197_v195_greedy_apollo_seed61716_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v197_v195_greedy_apollo_seed61716_zh.md
paired_instance_count = 1
both_optimal_count = 1
branch_score_used_count = 1
selected_pair_changed_count = 1
wall_time_delta_sum = -90.601710
exact_pricing_calls_delta_sum = -5
node_count_delta_sum = -2
wall_regressed_count = 0
```

## 边界

这仍是 in-context 单实例证据，不是 production branch GAT 泛化证据，也不是 random-TW 20-scale 60/60 达标证据。它的价值是证明闭环有效：`counterfactual ranking -> score map -> branch_score_horizon -> solver opt-in` 可以在 exact-safe 边界内真正减少求解时间。这里的 score map 是诊断/受控 opt-in 工具；严格训练集仍需要继续扩展到更多 canonical random-TW 20 parent contexts，并保留 positive holdout。
