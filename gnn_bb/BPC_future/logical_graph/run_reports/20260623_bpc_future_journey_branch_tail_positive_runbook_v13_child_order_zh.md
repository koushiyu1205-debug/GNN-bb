# Journey Branch-Tail Positive Collection Runbook

日期：2026-06-23

## 目的

在已有 5000 个 Stage 3 样本基础上追加 branch-tail intervention 样本，而不是重新生成全部样本。runbook 只生成 opt-in 命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_tail_positive_runbook = current
output_dir = BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623
entry_count = 2
base_sample_strategy = extend_existing_5000_with_branch_tail_interventions
candidate_source = root_level_near_positive_rows_and_tail_action_proof_cost_rows
tail_impact_input_paths = ['BPC_future/results/journey_tail_impact_training_rows_v12_tail_action_20260623']
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 条目

### 01_tail_action_child_order_d2_n3_4_12_separate_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
forced_pair = [4, 12]
forced_pair_depth_rule = force_pair_depth:0:3,7;1:2,10;2:4,12
forced_child_kind_depth_rule = force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:separate_vehicle
preferred_target_child_kind = separate_vehicle
source_tail_class = tail_action_no_column
source_tail_badness_score = None
source_type = tail_action_proof_cost
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/01_tail_action_child_order_d2_n3_4_12_separate_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/01_tail_action_child_order_d2_n3_4_12_separate_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/01_tail_action_child_order_d2_n3_4_12_separate_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/01_tail_action_child_order_d2_n3_4_12_separate_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_early_branching_enabled=False --set journey_tail_action_early_branch_enabled=True --set journey_tail_action_early_branch_min_cg_iter=35 --set journey_tail_action_early_branch_child_min_cg_iter=2 --set journey_tail_action_early_branch_max_depth=1 --set journey_tail_action_early_branch_min_true_rc_productivity=1 --set journey_tail_action_child_priority_enabled=True --set journey_tail_action_child_priority_width=-1 --set journey_tail_action_no_column_early_branch_enabled=True --set journey_tail_action_no_column_early_branch_min_depth=2 --set journey_tail_action_no_column_early_branch_max_depth=2 --set journey_tail_action_no_column_early_branch_child_min_cg_iter=1 --set journey_tail_action_no_column_early_branch_min_true_rc_productivity=0 --set journey_tail_action_no_column_early_branch_require_complete_productivity_signals=False --set journey_tail_action_no_column_early_branch_max_pool_child_width=180 --set journey_tail_action_no_column_early_branch_max_pool_total_child_width=360 --set journey_tail_action_no_column_early_branch_max_pool_balance_gap=180 --set journey_branch_fractionality_tie_tolerance=0.05 --set 'journey_branch_candidate_priority=force_pair_depth:0:3,7;1:2,10;2:4,12' --set 'journey_child_priority_mode=force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:separate_vehicle' --set journey_branch_candidate_log_top_n=12
```

### 02_tail_action_child_order_d2_n4_1_9_same_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
forced_pair = [1, 9]
forced_pair_depth_rule = force_pair_depth:0:3,7;1:2,10;2:1,9
forced_child_kind_depth_rule = force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:same_vehicle
preferred_target_child_kind = same_vehicle
source_tail_class = tail_action_no_column
source_tail_badness_score = None
source_type = tail_action_proof_cost
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/02_tail_action_child_order_d2_n4_1_9_same_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/02_tail_action_child_order_d2_n4_1_9_same_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/02_tail_action_child_order_d2_n4_1_9_same_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623/runs/02_tail_action_child_order_d2_n4_1_9_same_vehicle_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_early_branching_enabled=False --set journey_tail_action_early_branch_enabled=True --set journey_tail_action_early_branch_min_cg_iter=35 --set journey_tail_action_early_branch_child_min_cg_iter=2 --set journey_tail_action_early_branch_max_depth=1 --set journey_tail_action_early_branch_min_true_rc_productivity=1 --set journey_tail_action_child_priority_enabled=True --set journey_tail_action_child_priority_width=-1 --set journey_tail_action_no_column_early_branch_enabled=True --set journey_tail_action_no_column_early_branch_min_depth=2 --set journey_tail_action_no_column_early_branch_max_depth=2 --set journey_tail_action_no_column_early_branch_child_min_cg_iter=1 --set journey_tail_action_no_column_early_branch_min_true_rc_productivity=0 --set journey_tail_action_no_column_early_branch_require_complete_productivity_signals=False --set journey_tail_action_no_column_early_branch_max_pool_child_width=180 --set journey_tail_action_no_column_early_branch_max_pool_total_child_width=360 --set journey_tail_action_no_column_early_branch_max_pool_balance_gap=180 --set journey_branch_fractionality_tie_tolerance=0.05 --set 'journey_branch_candidate_priority=force_pair_depth:0:3,7;1:2,10;2:1,9' --set 'journey_child_priority_mode=force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:same_vehicle' --set journey_branch_candidate_log_top_n=12
```

## 边界

这些命令只改变 Ryan-Foster 候选选择顺序；如果 forced pair 不是当前合法 fractional candidate，会回退到默认 fractionality 选择。最终 no-negative closure 仍只来自 exact pricing。

## 已执行结果

两条命令均已在 canonical random-TW 20 `seed61000` 上执行，外部预算均为 260s，结果均为 `EXTERNAL_TIME_LIMIT`。

| 条目 | status | proof-cost 对比 |
|---|---|---|
| `01_tail_action_child_order_d2_n3_4_12_separate_vehicle...` | `EXTERNAL_TIME_LIMIT` | node3 subtree 从 V12 的 `pricing=1, negative_pricing=0, span=36.14s` 变成 `pricing=3, negative_pricing=1, span=44.70s` |
| `02_tail_action_child_order_d2_n4_1_9_same_vehicle...` | `EXTERNAL_TIME_LIMIT` | node1 subtree `pricing=17, negative_pricing=6, span=117.94s`；node3 subtree `pricing=7, negative_pricing=3, span=82.83s` |

结论：这两条 depth-scoped child-ordering counterfactual 都不是 useful-tail-reduction positive；它们应作为 hard negatives 进入 tail-impact 数据，而不是作为 GAT 加速正例。
