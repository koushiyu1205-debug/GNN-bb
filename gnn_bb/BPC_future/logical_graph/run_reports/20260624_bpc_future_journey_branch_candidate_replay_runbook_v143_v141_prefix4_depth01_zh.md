# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624
entry_count = 12
candidate_event_count_seen = 30
candidate_event_count_with_replay_entries = 6
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = priority_top
candidate_log_top_n = 100
min_source_depth = 0
max_source_depth = 1
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v141_prefix4_20260624']
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
excluded_entry_key_count = 0
excluded_entry_skip_count = 0
focus_context_count = 0
focus_event_skip_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 19
branch_impact_priority_context_count = 30
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n2_r1_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [12, 16]
forced_pair = [12, 13]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:12,13
source_alt_rank = 1
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 407
source_alt_pool_total_child_width = 752
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/001_candidate_alt_d1_n2_r1_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/001_candidate_alt_d1_n2_r1_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/001_candidate_alt_d1_n2_r1_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/001_candidate_alt_d1_n2_r1_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:12,13' --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d1_n2_r5_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [12, 16]
forced_pair = [4, 12]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,12
source_alt_rank = 5
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 411
source_alt_pool_total_child_width = 756
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/002_candidate_alt_d1_n2_r5_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/002_candidate_alt_d1_n2_r5_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/002_candidate_alt_d1_n2_r5_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/002_candidate_alt_d1_n2_r5_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,12' --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d0_n0_r3_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 6]
forced_pair = [3, 13]
forced_pair_path_rule = force_pair_path:0:3,13
source_alt_rank = 3
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 304
source_alt_pool_total_child_width = 492
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/003_candidate_alt_d0_n0_r3_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/003_candidate_alt_d0_n0_r3_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/003_candidate_alt_d0_n0_r3_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/003_candidate_alt_d0_n0_r3_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,13 --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d0_n0_r34_3_14_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 6]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:3,14
source_alt_rank = 34
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.277777778
source_alt_required_tie_tolerance = 0.166666666
source_alt_pool_max_child_width = 308
source_alt_pool_total_child_width = 503
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/004_candidate_alt_d0_n0_r34_3_14_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/004_candidate_alt_d0_n0_r34_3_14_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/004_candidate_alt_d0_n0_r34_3_14_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/004_candidate_alt_d0_n0_r34_3_14_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,14 --set journey_branch_candidate_log_top_n=100
```

### 005_candidate_alt_d1_n1_r33_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [4, 5]
forced_pair_path_rule = force_pair_path:0:3,7=same_vehicle;1:4,5
source_alt_rank = 33
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 162
source_alt_pool_total_child_width = 316
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 26.0
branch_impact_priority_reason = active_touch=0;completion_retries=8;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/005_candidate_alt_d1_n1_r33_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/005_candidate_alt_d1_n1_r33_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/005_candidate_alt_d1_n1_r33_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/005_candidate_alt_d1_n1_r33_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=same_vehicle;1:4,5' --set journey_branch_candidate_log_top_n=100
```

### 006_candidate_alt_d1_n1_r39_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [5, 18]
forced_pair_path_rule = force_pair_path:0:3,7=same_vehicle;1:5,18
source_alt_rank = 39
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 162
source_alt_pool_total_child_width = 319
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 26.0
branch_impact_priority_reason = active_touch=0;completion_retries=8;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/006_candidate_alt_d1_n1_r39_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/006_candidate_alt_d1_n1_r39_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/006_candidate_alt_d1_n1_r39_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/006_candidate_alt_d1_n1_r39_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=same_vehicle;1:5,18' --set journey_branch_candidate_log_top_n=100
```

### 007_candidate_alt_d1_n2_r49_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [10, 13]
forced_pair_path_rule = force_pair_path:0:3,7=separate_vehicle;1:10,13
source_alt_rank = 49
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 230
source_alt_pool_total_child_width = 391
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=7;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/007_candidate_alt_d1_n2_r49_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/007_candidate_alt_d1_n2_r49_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/007_candidate_alt_d1_n2_r49_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/007_candidate_alt_d1_n2_r49_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=separate_vehicle;1:10,13' --set journey_branch_candidate_log_top_n=100
```

### 008_candidate_alt_d1_n2_r34_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,7=separate_vehicle;1:3,10
source_alt_rank = 34
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 233
source_alt_pool_total_child_width = 391
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=7;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/008_candidate_alt_d1_n2_r34_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/008_candidate_alt_d1_n2_r34_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/008_candidate_alt_d1_n2_r34_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/008_candidate_alt_d1_n2_r34_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=separate_vehicle;1:3,10' --set journey_branch_candidate_log_top_n=100
```

### 009_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [2, 6]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,6
source_alt_rank = 2
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 210
source_alt_pool_total_child_width = 408
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 23.0
branch_impact_priority_reason = active_touch=1;completion_retries=2;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/009_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/009_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/009_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/009_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,6' --set journey_branch_candidate_log_top_n=100
```

### 010_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,13
source_alt_rank = 6
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 212
source_alt_pool_total_child_width = 392
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 23.0
branch_impact_priority_reason = active_touch=1;completion_retries=2;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/010_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/010_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/010_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/010_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,13' --set journey_branch_candidate_log_top_n=100
```

### 011_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 10]
forced_pair = [5, 10]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:5,10
source_alt_rank = 29
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 216
source_alt_pool_total_child_width = 359
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 21.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/011_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/011_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/011_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/011_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:5,10' --set journey_branch_candidate_log_top_n=100
```

### 012_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 10]
forced_pair = [10, 18]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:10,18
source_alt_rank = 4
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 218
source_alt_pool_total_child_width = 377
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 21.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/012_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/012_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/012_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624/runs/012_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:10,18' --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
