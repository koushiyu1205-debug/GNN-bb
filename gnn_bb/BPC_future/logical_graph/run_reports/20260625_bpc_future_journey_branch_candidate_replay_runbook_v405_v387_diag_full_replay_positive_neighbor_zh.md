# Journey Branch Candidate Replay Runbook

日期：2026-06-25

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625
entry_count = 6
candidate_event_count_seen = 26
candidate_event_count_with_replay_entries = 2
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 3
candidate_source = both
candidate_selection = positive_neighbor
candidate_log_top_n = 200
min_source_depth = None
max_source_depth = 0
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_diag_top100_seed61001_140_root_only_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v173_sector_apollo_seed61408_root_only_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624', 'BPC_future/results/journey_branch_proxy_full_replay_runbook_v378_v375_new_positive', 'BPC_future/results/journey_branch_proxy_full_replay_runbook_v320_v319_seed61414_pair6_20_20260625', 'BPC_future/results/journey_branch_target200_sampling_plan_v373_v372_recursive_exclude_20260625', 'BPC_future/results/journey_branch_target200_sampling_plan_v383_after_v381_attempted_v373_20260625', 'BPC_future/results/journey_branch_target200_sampling_plan_v388_after_v387_logs_20260625']
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = full_replay
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 371
excluded_entry_skip_count = 2
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 24
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.735748
source_selected_pair = [12, 13]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:5,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.683333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 271
source_alt_pool_total_child_width = 519
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,13 --set journey_branch_candidate_log_top_n=200
```

### 002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.735748
source_selected_pair = [12, 13]
forced_pair = [9, 13]
forced_pair_path_rule = force_pair_path:0:9,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.495555556
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 282
source_alt_pool_total_child_width = 521
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,13 --set journey_branch_candidate_log_top_n=200
```

### 003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 55.735748
source_selected_pair = [12, 13]
forced_pair = [3, 16]
forced_pair_path_rule = force_pair_path:0:3,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 17
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.010700858
source_selected_fractionality = 0.5
source_alt_fractionality = 0.384615385
source_alt_required_tie_tolerance = 0.115384615
source_alt_pool_max_child_width = 259
source_alt_pool_total_child_width = 454
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,16 --set journey_branch_candidate_log_top_n=200
```

### 004_candidate_alt_d0_n0_r3_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 15.482122
source_selected_pair = [1, 3]
forced_pair = [3, 6]
forced_pair_path_rule = force_pair_path:0:3,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 3
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.012444444
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 199
source_alt_pool_total_child_width = 388
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/004_candidate_alt_d0_n0_r3_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/004_candidate_alt_d0_n0_r3_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/004_candidate_alt_d0_n0_r3_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/004_candidate_alt_d0_n0_r3_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,6 --set journey_branch_candidate_log_top_n=200
```

### 005_candidate_alt_d0_n0_r4_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 15.482122
source_selected_pair = [1, 3]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:3,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 4
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.033111111
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 198
source_alt_pool_total_child_width = 388
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/005_candidate_alt_d0_n0_r4_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/005_candidate_alt_d0_n0_r4_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/005_candidate_alt_d0_n0_r4_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/005_candidate_alt_d0_n0_r4_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,14 --set journey_branch_candidate_log_top_n=200
```

### 006_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 15.482122
source_selected_pair = [1, 3]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:1,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.739333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 203
source_alt_pool_total_child_width = 363
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/006_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/006_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/006_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v405_v387_diag_full_replay_positive_neighbor_20260625/runs/006_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,6 --set journey_branch_candidate_log_top_n=200
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
