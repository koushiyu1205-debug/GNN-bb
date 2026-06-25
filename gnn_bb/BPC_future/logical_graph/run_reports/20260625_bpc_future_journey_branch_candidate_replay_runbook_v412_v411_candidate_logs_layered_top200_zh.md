# Journey Branch Candidate Replay Runbook

日期：2026-06-25

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625
entry_count = 9
candidate_event_count_seen = 26
candidate_event_count_with_replay_entries = 3
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 4
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = None
max_source_depth = 1
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625']
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = full_replay
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 6
excluded_entry_skip_count = 6
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 23
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.473613
source_selected_pair = [12, 13]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 27
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.384615385
source_alt_required_tie_tolerance = 0.115384615
source_alt_pool_max_child_width = 266
source_alt_pool_total_child_width = 510
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/001_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/001_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/001_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/001_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=200
```

### 002_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.473613
source_selected_pair = [12, 13]
forced_pair = [11, 14]
forced_pair_path_rule = force_pair_path:0:11,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 77
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.076923077
source_alt_required_tie_tolerance = 0.423076923
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 467
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/002_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/002_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/002_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/002_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:11,14 --set journey_branch_candidate_log_top_n=200
```

### 003_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.473613
source_selected_pair = [12, 13]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:3,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 52
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.192307692
source_alt_required_tie_tolerance = 0.307692308
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 433
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/003_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/003_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/003_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/003_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,14 --set journey_branch_candidate_log_top_n=200
```

### 004_candidate_alt_d0_n0_r8_3_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.473613
source_selected_pair = [12, 13]
forced_pair = [3, 7]
forced_pair_path_rule = force_pair_path:0:3,7
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 8
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.461538462
source_alt_required_tie_tolerance = 0.038461538
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 456
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/004_candidate_alt_d0_n0_r8_3_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/004_candidate_alt_d0_n0_r8_3_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/004_candidate_alt_d0_n0_r8_3_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/004_candidate_alt_d0_n0_r8_3_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,7 --set journey_branch_candidate_log_top_n=200
```

### 005_candidate_alt_d0_n0_r2_1_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 15.585433
source_selected_pair = [1, 3]
forced_pair = [1, 14]
forced_pair_path_rule = force_pair_path:0:1,14
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
source_alt_pool_max_child_width = 203
source_alt_pool_total_child_width = 362
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/005_candidate_alt_d0_n0_r2_1_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/005_candidate_alt_d0_n0_r2_1_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/005_candidate_alt_d0_n0_r2_1_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/005_candidate_alt_d0_n0_r2_1_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,14 --set journey_branch_candidate_log_top_n=200
```

### 006_candidate_alt_d1_n2_r1_1_8_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 35.095563
source_selected_pair = [1, 2]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,8
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
source_alt_pool_max_child_width = 214
source_alt_pool_total_child_width = 382
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/006_candidate_alt_d1_n2_r1_1_8_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/006_candidate_alt_d1_n2_r1_1_8_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/006_candidate_alt_d1_n2_r1_1_8_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/006_candidate_alt_d1_n2_r1_1_8_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,8' --set journey_branch_candidate_log_top_n=200
```

### 007_candidate_alt_d1_n2_r2_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 35.095563
source_selected_pair = [1, 2]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,10
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
source_alt_pool_max_child_width = 210
source_alt_pool_total_child_width = 391
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/007_candidate_alt_d1_n2_r2_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/007_candidate_alt_d1_n2_r2_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/007_candidate_alt_d1_n2_r2_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/007_candidate_alt_d1_n2_r2_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,10' --set journey_branch_candidate_log_top_n=200
```

### 008_candidate_alt_d1_n2_r3_1_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 35.095563
source_selected_pair = [1, 2]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 3
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 203
source_alt_pool_total_child_width = 357
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/008_candidate_alt_d1_n2_r3_1_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/008_candidate_alt_d1_n2_r3_1_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/008_candidate_alt_d1_n2_r3_1_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/008_candidate_alt_d1_n2_r3_1_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,13' --set journey_branch_candidate_log_top_n=200
```

### 009_candidate_alt_d1_n2_r7_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 35.095563
source_selected_pair = [1, 2]
forced_pair = [8, 10]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:8,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 7
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 210
source_alt_pool_total_child_width = 394
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/009_candidate_alt_d1_n2_r7_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/009_candidate_alt_d1_n2_r7_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/009_candidate_alt_d1_n2_r7_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v412_v411_candidate_logs_layered_top200_20260625/runs/009_candidate_alt_d1_n2_r7_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:8,10' --set journey_branch_candidate_log_top_n=200
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
