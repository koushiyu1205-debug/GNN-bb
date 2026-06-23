# Journey Branch-Tail Positive Collection Runbook

日期：2026-06-23

## 目的

在已有 5000 个 Stage 3 样本基础上追加 branch-tail intervention 样本，而不是重新生成全部样本。runbook 只生成 opt-in 命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_tail_positive_runbook = current
output_dir = BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623
entry_count = 2
base_sample_strategy = extend_existing_5000_with_branch_tail_interventions
candidate_source = root_level_near_positive_rows
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 条目

### 01_force_pair_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
forced_pair = [2, 13]
source_tail_class = early_branch_continues
source_tail_badness_score = 58.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200 --results-csv BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/01_force_pair_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/01_force_pair_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/01_force_pair_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/01_force_pair_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_early_branching_enabled=True --set journey_early_branching_min_cg_iter=56 --set journey_early_branching_child_min_cg_iter=3 --set journey_early_branching_max_depth=1 --set journey_child_priority_by_width_enabled=True --set journey_early_branching_after_incomplete_no_column_enabled=True --set journey_early_branching_after_incomplete_no_column_min_remaining=20.0 --set journey_branch_fractionality_tie_tolerance=0.05 --set journey_branch_candidate_priority=force_pair:2,13 --set journey_branch_candidate_log_top_n=12
```

### 02_force_pair_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
forced_pair = [2, 3]
source_tail_class = early_branch_continues
source_tail_badness_score = 59.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200 --results-csv BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/02_force_pair_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/02_force_pair_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/02_force_pair_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs/02_force_pair_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_early_branching_enabled=True --set journey_early_branching_min_cg_iter=56 --set journey_early_branching_child_min_cg_iter=3 --set journey_early_branching_max_depth=1 --set journey_child_priority_by_width_enabled=True --set journey_early_branching_after_incomplete_no_column_enabled=True --set journey_early_branching_after_incomplete_no_column_min_remaining=20.0 --set journey_branch_fractionality_tie_tolerance=0.05 --set journey_branch_candidate_priority=force_pair:2,3 --set journey_branch_candidate_log_top_n=12
```

## 边界

这些命令只改变 Ryan-Foster 候选选择顺序；如果 forced pair 不是当前合法 fractional candidate，会回退到默认 fractionality 选择。最终 no-negative closure 仍只来自 exact pricing。
