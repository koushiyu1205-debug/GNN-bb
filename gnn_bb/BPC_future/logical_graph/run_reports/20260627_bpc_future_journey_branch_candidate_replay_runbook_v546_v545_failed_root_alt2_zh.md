# Journey Branch Candidate Replay Runbook

日期：2026-06-27

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627
entry_count = 42
candidate_event_count_seen = 429
candidate_event_count_with_replay_entries = 21
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 0
max_source_depth = 0
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = full_replay
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 0
excluded_entry_skip_count = 0
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 408
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.323805
source_selected_pair = [1, 2]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = 0.293212134
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=200
```

### 002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.323805
source_selected_pair = [1, 2]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 612
source_alt_branch_score = 0.305996461
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,10 --set journey_branch_candidate_log_top_n=200
```

### 003_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 243.645579
source_selected_pair = [1, 18]
forced_pair = [2, 3]
forced_pair_path_rule = force_pair_path:0:2,3
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 341
source_alt_pool_total_child_width = 572
source_alt_branch_score = 0.0
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/003_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/003_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/003_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/003_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,3 --set journey_branch_candidate_log_top_n=200
```

### 004_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 243.645579
source_selected_pair = [1, 18]
forced_pair = [2, 6]
forced_pair_path_rule = force_pair_path:0:2,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 561
source_alt_branch_score = 0.0
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/004_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/004_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/004_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/004_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,6 --set journey_branch_candidate_log_top_n=200
```

### 005_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 134.647366
source_selected_pair = [4, 7]
forced_pair = [7, 15]
forced_pair_path_rule = force_pair_path:0:7,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 468
source_alt_pool_total_child_width = 846
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/005_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/005_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/005_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/005_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,15 --set journey_branch_candidate_log_top_n=200
```

### 006_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 134.647366
source_selected_pair = [4, 7]
forced_pair = [7, 17]
forced_pair_path_rule = force_pair_path:0:7,17
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 480
source_alt_pool_total_child_width = 849
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/006_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/006_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/006_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/006_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,17 --set journey_branch_candidate_log_top_n=200
```

### 007_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 123.531309
source_selected_pair = [1, 2]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 387
source_alt_pool_total_child_width = 712
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/007_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/007_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/007_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/007_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=200
```

### 008_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 123.531309
source_selected_pair = [1, 2]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:1,8
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 391
source_alt_pool_total_child_width = 732
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/008_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/008_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/008_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/008_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,8 --set journey_branch_candidate_log_top_n=200
```

### 009_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 46.750718
source_selected_pair = [5, 9]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:3,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 427
source_alt_pool_total_child_width = 749
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/009_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/009_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/009_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/009_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,5 --set journey_branch_candidate_log_top_n=200
```

### 010_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 46.750718
source_selected_pair = [5, 9]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:3,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 421
source_alt_pool_total_child_width = 768
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/010_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/010_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/010_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/010_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,9 --set journey_branch_candidate_log_top_n=200
```

### 011_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.506277
source_selected_pair = [1, 10]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:1,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 316
source_alt_pool_total_child_width = 561
source_alt_branch_score = 7.6356e-05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/011_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/011_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/011_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/011_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,13 --set journey_branch_candidate_log_top_n=200
```

### 012_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.506277
source_selected_pair = [1, 10]
forced_pair = [1, 19]
forced_pair_path_rule = force_pair_path:0:1,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 316
source_alt_pool_total_child_width = 549
source_alt_branch_score = 0.000106599
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/012_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/012_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/012_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/012_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,19 --set journey_branch_candidate_log_top_n=200
```

### 013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.467011
source_selected_pair = [4, 7]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,8
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 332
source_alt_pool_total_child_width = 615
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,8 --set journey_branch_candidate_log_top_n=200
```

### 014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.467011
source_selected_pair = [4, 7]
forced_pair = [4, 9]
forced_pair_path_rule = force_pair_path:0:4,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 325
source_alt_pool_total_child_width = 569
source_alt_branch_score = 0.518813801
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,9 --set journey_branch_candidate_log_top_n=200
```

### 015_candidate_alt_d0_n0_r1_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 30.316217
source_selected_pair = [1, 3]
forced_pair = [1, 9]
forced_pair_path_rule = force_pair_path:0:1,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 333
source_alt_pool_total_child_width = 575
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/015_candidate_alt_d0_n0_r1_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/015_candidate_alt_d0_n0_r1_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/015_candidate_alt_d0_n0_r1_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/015_candidate_alt_d0_n0_r1_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,9 --set journey_branch_candidate_log_top_n=200
```

### 016_candidate_alt_d0_n0_r2_1_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 30.316217
source_selected_pair = [1, 3]
forced_pair = [1, 12]
forced_pair_path_rule = force_pair_path:0:1,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 331
source_alt_pool_total_child_width = 563
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/016_candidate_alt_d0_n0_r2_1_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/016_candidate_alt_d0_n0_r2_1_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/016_candidate_alt_d0_n0_r2_1_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/016_candidate_alt_d0_n0_r2_1_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,12 --set journey_branch_candidate_log_top_n=200
```

### 017_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 107.980564
source_selected_pair = [1, 4]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:1,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 630
source_alt_pool_total_child_width = 1073
source_alt_branch_score = 0.542280561
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/017_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/017_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/017_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/017_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,6 --set journey_branch_candidate_log_top_n=200
```

### 018_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 107.980564
source_selected_pair = [1, 4]
forced_pair = [1, 19]
forced_pair_path_rule = force_pair_path:0:1,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 643
source_alt_pool_total_child_width = 1116
source_alt_branch_score = 0.552354157
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/018_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/018_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/018_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/018_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,19 --set journey_branch_candidate_log_top_n=200
```

### 019_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 41.872751
source_selected_pair = [8, 18]
forced_pair = [14, 18]
forced_pair_path_rule = force_pair_path:0:14,18
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 177
source_alt_pool_total_child_width = 315
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/019_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/019_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/019_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/019_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:14,18 --set journey_branch_candidate_log_top_n=200
```

### 020_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 41.872751
source_selected_pair = [8, 18]
forced_pair = [15, 18]
forced_pair_path_rule = force_pair_path:0:15,18
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 183
source_alt_pool_total_child_width = 326
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/020_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/020_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/020_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/020_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,18 --set journey_branch_candidate_log_top_n=200
```

### 021_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 72.990487
source_selected_pair = [1, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:4,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 249
source_alt_pool_total_child_width = 427
source_alt_branch_score = 0.204270535
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/021_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/021_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/021_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/021_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,15 --set journey_branch_candidate_log_top_n=200
```

### 022_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 72.990487
source_selected_pair = [1, 12]
forced_pair = [7, 11]
forced_pair_path_rule = force_pair_path:0:7,11
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 246
source_alt_pool_total_child_width = 436
source_alt_branch_score = 0.207070705
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/022_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/022_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/022_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/022_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,11 --set journey_branch_candidate_log_top_n=200
```

### 023_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.356791
source_selected_pair = [3, 10]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:3,17
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 295
source_alt_pool_total_child_width = 498
source_alt_branch_score = 3.877e-06
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/023_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/023_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/023_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/023_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,17 --set journey_branch_candidate_log_top_n=200
```

### 024_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.356791
source_selected_pair = [3, 10]
forced_pair = [3, 19]
forced_pair_path_rule = force_pair_path:0:3,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 292
source_alt_pool_total_child_width = 488
source_alt_branch_score = 0.305715117
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/024_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/024_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/024_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/024_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,19 --set journey_branch_candidate_log_top_n=200
```

### 025_candidate_alt_d0_n0_r1_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 81.283191
source_selected_pair = [4, 9]
forced_pair = [4, 11]
forced_pair_path_rule = force_pair_path:0:4,11
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 350
source_alt_pool_total_child_width = 624
source_alt_branch_score = 0.297760543
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/025_candidate_alt_d0_n0_r1_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/025_candidate_alt_d0_n0_r1_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/025_candidate_alt_d0_n0_r1_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/025_candidate_alt_d0_n0_r1_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,11 --set journey_branch_candidate_log_top_n=200
```

### 026_candidate_alt_d0_n0_r2_5_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 81.283191
source_selected_pair = [4, 9]
forced_pair = [5, 11]
forced_pair_path_rule = force_pair_path:0:5,11
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 360
source_alt_pool_total_child_width = 653
source_alt_branch_score = 0.321121106
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/026_candidate_alt_d0_n0_r2_5_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/026_candidate_alt_d0_n0_r2_5_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/026_candidate_alt_d0_n0_r2_5_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/026_candidate_alt_d0_n0_r2_5_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,11 --set journey_branch_candidate_log_top_n=200
```

### 027_candidate_alt_d0_n0_r1_2_9_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 32.2878
source_selected_pair = [2, 3]
forced_pair = [2, 9]
forced_pair_path_rule = force_pair_path:0:2,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 136
source_alt_pool_total_child_width = 239
source_alt_branch_score = 0.000182766
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/027_candidate_alt_d0_n0_r1_2_9_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/027_candidate_alt_d0_n0_r1_2_9_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/027_candidate_alt_d0_n0_r1_2_9_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/027_candidate_alt_d0_n0_r1_2_9_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,9 --set journey_branch_candidate_log_top_n=200
```

### 028_candidate_alt_d0_n0_r2_2_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 32.2878
source_selected_pair = [2, 3]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:2,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 130
source_alt_pool_total_child_width = 236
source_alt_branch_score = 0.000226443
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/028_candidate_alt_d0_n0_r2_2_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/028_candidate_alt_d0_n0_r2_2_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/028_candidate_alt_d0_n0_r2_2_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/028_candidate_alt_d0_n0_r2_2_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,10 --set journey_branch_candidate_log_top_n=200
```

### 029_candidate_alt_d0_n0_r1_2_20_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 152.959451
source_selected_pair = [2, 5]
forced_pair = [2, 20]
forced_pair_path_rule = force_pair_path:0:2,20
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 478
source_alt_pool_total_child_width = 816
source_alt_branch_score = 0.241808969
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/029_candidate_alt_d0_n0_r1_2_20_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/029_candidate_alt_d0_n0_r1_2_20_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/029_candidate_alt_d0_n0_r1_2_20_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/029_candidate_alt_d0_n0_r1_2_20_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,20 --set journey_branch_candidate_log_top_n=200
```

### 030_candidate_alt_d0_n0_r2_3_5_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 152.959451
source_selected_pair = [2, 5]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:3,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 474
source_alt_pool_total_child_width = 809
source_alt_branch_score = 0.24675567
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/030_candidate_alt_d0_n0_r2_3_5_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/030_candidate_alt_d0_n0_r2_3_5_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/030_candidate_alt_d0_n0_r2_3_5_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runs/030_candidate_alt_d0_n0_r2_3_5_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,5 --set journey_branch_candidate_log_top_n=200
```

- Report truncated to first 30 entries; full runbook has 42 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
