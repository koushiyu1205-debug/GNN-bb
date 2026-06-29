# Journey Branch Candidate Replay Runbook

日期：2026-06-27

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627
entry_count = 48
candidate_event_count_seen = 546
candidate_event_count_with_replay_entries = 13
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = priority_top
candidate_selection = positive_neighbor
candidate_log_top_n = 200
min_source_depth = 0
max_source_depth = 0
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runbook.json']
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = full_replay
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 32
excluded_entry_skip_count = 16
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 520
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.014049
source_selected_pair = [1, 2]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 6
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.024888889
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = 0.527347943
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/001_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/001_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/001_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/001_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=200
```

### 002_candidate_alt_d0_n0_r29_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.014049
source_selected_pair = [1, 2]
forced_pair = [15, 16]
forced_pair_path_rule = force_pair_path:0:15,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 29
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.133333331
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 399
source_alt_pool_total_child_width = 759
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/002_candidate_alt_d0_n0_r29_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/002_candidate_alt_d0_n0_r29_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/002_candidate_alt_d0_n0_r29_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/002_candidate_alt_d0_n0_r29_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,16 --set journey_branch_candidate_log_top_n=200
```

### 003_candidate_alt_d0_n0_r17_14_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.014049
source_selected_pair = [1, 2]
forced_pair = [14, 18]
forced_pair_path_rule = force_pair_path:0:14,18
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 17
source_alt_selection_reason = best_branch_score
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 4.058444444
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 390
source_alt_pool_total_child_width = 628
source_alt_branch_score = 0.53801927
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/003_candidate_alt_d0_n0_r17_14_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/003_candidate_alt_d0_n0_r17_14_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/003_candidate_alt_d0_n0_r17_14_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/003_candidate_alt_d0_n0_r17_14_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:14,18 --set journey_branch_candidate_log_top_n=200
```

### 004_candidate_alt_d0_n0_r23_13_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.014049
source_selected_pair = [1, 2]
forced_pair = [13, 15]
forced_pair_path_rule = force_pair_path:0:13,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 23
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.271777778
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 401
source_alt_pool_total_child_width = 736
source_alt_branch_score = 0.533590424
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/004_candidate_alt_d0_n0_r23_13_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/004_candidate_alt_d0_n0_r23_13_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/004_candidate_alt_d0_n0_r23_13_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/004_candidate_alt_d0_n0_r23_13_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:13,15 --set journey_branch_candidate_log_top_n=200
```

### 005_candidate_alt_d0_n0_r26_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 243.331798
source_selected_pair = [1, 18]
forced_pair = [5, 16]
forced_pair_path_rule = force_pair_path:0:5,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 26
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.310222222
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 342
source_alt_pool_total_child_width = 635
source_alt_branch_score = 0.536767471
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/005_candidate_alt_d0_n0_r26_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/005_candidate_alt_d0_n0_r26_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/005_candidate_alt_d0_n0_r26_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/005_candidate_alt_d0_n0_r26_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,16 --set journey_branch_candidate_log_top_n=200
```

### 006_candidate_alt_d0_n0_r24_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 243.331798
source_selected_pair = [1, 18]
forced_pair = [5, 11]
forced_pair_path_rule = force_pair_path:0:5,11
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 24
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.317777778
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 344
source_alt_pool_total_child_width = 637
source_alt_branch_score = 0.523685429
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/006_candidate_alt_d0_n0_r24_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/006_candidate_alt_d0_n0_r24_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/006_candidate_alt_d0_n0_r24_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/006_candidate_alt_d0_n0_r24_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,11 --set journey_branch_candidate_log_top_n=200
```

### 007_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 243.331798
source_selected_pair = [1, 18]
forced_pair = [2, 3]
forced_pair_path_rule = force_pair_path:0:2,3
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.805555556
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 341
source_alt_pool_total_child_width = 572
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/007_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/007_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/007_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/007_candidate_alt_d0_n0_r1_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,3 --set journey_branch_candidate_log_top_n=200
```

### 008_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 243.331798
source_selected_pair = [1, 18]
forced_pair = [2, 6]
forced_pair_path_rule = force_pair_path:0:2,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.601333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 561
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/008_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/008_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/008_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/008_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,6 --set journey_branch_candidate_log_top_n=200
```

### 009_candidate_alt_d0_n0_r3_1_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 132.000257
source_selected_pair = [4, 7]
forced_pair = [1, 7]
forced_pair_path_rule = force_pair_path:0:1,7
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 3
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.17577778
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 461
source_alt_pool_total_child_width = 862
source_alt_branch_score = 0.538823014
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/009_candidate_alt_d0_n0_r3_1_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/009_candidate_alt_d0_n0_r3_1_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/009_candidate_alt_d0_n0_r3_1_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/009_candidate_alt_d0_n0_r3_1_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,7 --set journey_branch_candidate_log_top_n=200
```

### 010_candidate_alt_d0_n0_r7_7_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 132.000257
source_selected_pair = [4, 7]
forced_pair = [7, 16]
forced_pair_path_rule = force_pair_path:0:7,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 7
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.317555557
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 474
source_alt_pool_total_child_width = 876
source_alt_branch_score = 0.540449226
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/010_candidate_alt_d0_n0_r7_7_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/010_candidate_alt_d0_n0_r7_7_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/010_candidate_alt_d0_n0_r7_7_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/010_candidate_alt_d0_n0_r7_7_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,16 --set journey_branch_candidate_log_top_n=200
```

### 011_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 132.000257
source_selected_pair = [4, 7]
forced_pair = [7, 15]
forced_pair_path_rule = force_pair_path:0:7,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.676888891
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 468
source_alt_pool_total_child_width = 846
source_alt_branch_score = 0.540995404
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/011_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/011_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/011_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/011_candidate_alt_d0_n0_r1_7_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,15 --set journey_branch_candidate_log_top_n=200
```

### 012_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 132.000257
source_selected_pair = [4, 7]
forced_pair = [7, 17]
forced_pair_path_rule = force_pair_path:0:7,17
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.879555557
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 480
source_alt_pool_total_child_width = 849
source_alt_branch_score = 0.540595853
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/012_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/012_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/012_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/012_candidate_alt_d0_n0_r2_7_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,17 --set journey_branch_candidate_log_top_n=200
```

### 013_candidate_alt_d0_n0_r20_12_16_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 121.736993
source_selected_pair = [1, 2]
forced_pair = [12, 16]
forced_pair_path_rule = force_pair_path:0:12,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 20
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.865682543
source_selected_fractionality = 0.5
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.071428571
source_alt_pool_max_child_width = 392
source_alt_pool_total_child_width = 730
source_alt_branch_score = 0.538296777
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/013_candidate_alt_d0_n0_r20_12_16_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/013_candidate_alt_d0_n0_r20_12_16_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/013_candidate_alt_d0_n0_r20_12_16_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/013_candidate_alt_d0_n0_r20_12_16_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,16 --set journey_branch_candidate_log_top_n=200
```

### 014_candidate_alt_d0_n0_r17_7_12_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 121.736993
source_selected_pair = [1, 2]
forced_pair = [7, 12]
forced_pair_path_rule = force_pair_path:0:7,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 17
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.87434921
source_selected_fractionality = 0.5
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.071428571
source_alt_pool_max_child_width = 388
source_alt_pool_total_child_width = 733
source_alt_branch_score = 0.537164086
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/014_candidate_alt_d0_n0_r17_7_12_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/014_candidate_alt_d0_n0_r17_7_12_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/014_candidate_alt_d0_n0_r17_7_12_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/014_candidate_alt_d0_n0_r17_7_12_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,12 --set journey_branch_candidate_log_top_n=200
```

### 015_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 121.736993
source_selected_pair = [1, 2]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.235777778
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 387
source_alt_pool_total_child_width = 712
source_alt_branch_score = 0.533334628
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/015_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/015_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/015_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/015_candidate_alt_d0_n0_r1_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=200
```

### 016_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 121.736993
source_selected_pair = [1, 2]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:1,8
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.118666667
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 391
source_alt_pool_total_child_width = 732
source_alt_branch_score = 0.534154326
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/016_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/016_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/016_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/016_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,8 --set journey_branch_candidate_log_top_n=200
```

### 017_candidate_alt_d0_n0_r64_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 76.059659
source_selected_pair = [1, 2]
forced_pair = [4, 19]
forced_pair_path_rule = force_pair_path:0:4,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 64
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.375555556
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 319
source_alt_pool_total_child_width = 587
source_alt_branch_score = 0.533498606
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/017_candidate_alt_d0_n0_r64_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/017_candidate_alt_d0_n0_r64_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/017_candidate_alt_d0_n0_r64_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/017_candidate_alt_d0_n0_r64_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,19 --set journey_branch_candidate_log_top_n=200
```

### 018_candidate_alt_d0_n0_r66_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 76.059659
source_selected_pair = [1, 2]
forced_pair = [9, 10]
forced_pair_path_rule = force_pair_path:0:9,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 66
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.380444444
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 318
source_alt_pool_total_child_width = 589
source_alt_branch_score = 0.534004065
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/018_candidate_alt_d0_n0_r66_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/018_candidate_alt_d0_n0_r66_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/018_candidate_alt_d0_n0_r66_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/018_candidate_alt_d0_n0_r66_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,10 --set journey_branch_candidate_log_top_n=200
```

### 019_candidate_alt_d0_n0_r1_1_6_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 76.059659
source_selected_pair = [1, 2]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:1,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.333555556
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 327
source_alt_pool_total_child_width = 602
source_alt_branch_score = 0.526840582
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,6 --set journey_branch_candidate_log_top_n=200
```

### 020_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 76.059659
source_selected_pair = [1, 2]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:1,8
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.697333333
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 325
source_alt_pool_total_child_width = 558
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/020_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/020_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/020_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/020_candidate_alt_d0_n0_r2_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,8 --set journey_branch_candidate_log_top_n=200
```

### 021_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 45.920385
source_selected_pair = [5, 9]
forced_pair = [7, 13]
forced_pair_path_rule = force_pair_path:0:7,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 68
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.931999997
source_selected_fractionality = 0.5
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 397
source_alt_pool_total_child_width = 684
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/021_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/021_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/021_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/021_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,13 --set journey_branch_candidate_log_top_n=200
```

### 022_candidate_alt_d0_n0_r56_18_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 45.920385
source_selected_pair = [5, 9]
forced_pair = [18, 20]
forced_pair_path_rule = force_pair_path:0:18,20
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 56
source_alt_selection_reason = best_branch_score
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.328888889
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 429
source_alt_pool_total_child_width = 785
source_alt_branch_score = 0.542129999
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/022_candidate_alt_d0_n0_r56_18_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/022_candidate_alt_d0_n0_r56_18_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/022_candidate_alt_d0_n0_r56_18_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/022_candidate_alt_d0_n0_r56_18_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:18,20 --set journey_branch_candidate_log_top_n=200
```

### 023_candidate_alt_d0_n0_r29_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 45.920385
source_selected_pair = [5, 9]
forced_pair = [11, 17]
forced_pair_path_rule = force_pair_path:0:11,17
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 29
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.943333336
source_selected_fractionality = 0.5
source_alt_fractionality = 0.416666667
source_alt_required_tie_tolerance = 0.083333333
source_alt_pool_max_child_width = 426
source_alt_pool_total_child_width = 741
source_alt_branch_score = 0.535683852
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/023_candidate_alt_d0_n0_r29_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/023_candidate_alt_d0_n0_r29_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/023_candidate_alt_d0_n0_r29_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/023_candidate_alt_d0_n0_r29_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:11,17 --set journey_branch_candidate_log_top_n=200
```

### 024_candidate_alt_d0_n0_r41_7_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 45.920385
source_selected_pair = [5, 9]
forced_pair = [7, 19]
forced_pair_path_rule = force_pair_path:0:7,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 41
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.712666669
source_selected_fractionality = 0.5
source_alt_fractionality = 0.416666667
source_alt_required_tie_tolerance = 0.083333333
source_alt_pool_max_child_width = 403
source_alt_pool_total_child_width = 675
source_alt_branch_score = 0.532378036
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/024_candidate_alt_d0_n0_r41_7_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/024_candidate_alt_d0_n0_r41_7_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/024_candidate_alt_d0_n0_r41_7_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/024_candidate_alt_d0_n0_r41_7_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,19 --set journey_branch_candidate_log_top_n=200
```

### 025_candidate_alt_d0_n0_r12_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.23834
source_selected_pair = [1, 10]
forced_pair = [4, 12]
forced_pair_path_rule = force_pair_path:0:4,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 12
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.450222222
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 303
source_alt_pool_total_child_width = 563
source_alt_branch_score = 0.534176579
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/025_candidate_alt_d0_n0_r12_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/025_candidate_alt_d0_n0_r12_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/025_candidate_alt_d0_n0_r12_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/025_candidate_alt_d0_n0_r12_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,12 --set journey_branch_candidate_log_top_n=200
```

### 026_candidate_alt_d0_n0_r30_12_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.23834
source_selected_pair = [1, 10]
forced_pair = [12, 18]
forced_pair_path_rule = force_pair_path:0:12,18
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 30
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.453333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 310
source_alt_pool_total_child_width = 567
source_alt_branch_score = 0.534761006
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/026_candidate_alt_d0_n0_r30_12_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/026_candidate_alt_d0_n0_r30_12_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/026_candidate_alt_d0_n0_r30_12_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/026_candidate_alt_d0_n0_r30_12_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,18 --set journey_branch_candidate_log_top_n=200
```

### 027_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.23834
source_selected_pair = [1, 10]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:1,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.536666667
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 316
source_alt_pool_total_child_width = 561
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/027_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/027_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/027_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/027_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,13 --set journey_branch_candidate_log_top_n=200
```

### 028_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.23834
source_selected_pair = [1, 10]
forced_pair = [1, 19]
forced_pair_path_rule = force_pair_path:0:1,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.645333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 316
source_alt_pool_total_child_width = 549
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/028_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/028_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/028_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/028_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,19 --set journey_branch_candidate_log_top_n=200
```

### 029_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.412113
source_selected_pair = [4, 7]
forced_pair = [8, 9]
forced_pair_path_rule = force_pair_path:0:8,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 7
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.543777778
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 329
source_alt_pool_total_child_width = 583
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/029_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/029_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/029_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/029_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,9 --set journey_branch_candidate_log_top_n=200
```

### 030_candidate_alt_d0_n0_r8_8_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.412113
source_selected_pair = [4, 7]
forced_pair = [8, 10]
forced_pair_path_rule = force_pair_path:0:8,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 8
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.429777778
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 332
source_alt_pool_total_child_width = 631
source_alt_branch_score = 0.536460313
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/030_candidate_alt_d0_n0_r8_8_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/030_candidate_alt_d0_n0_r8_8_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/030_candidate_alt_d0_n0_r8_8_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runs/030_candidate_alt_d0_n0_r8_8_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,10 --set journey_branch_candidate_log_top_n=200
```

- Report truncated to first 30 entries; full runbook has 48 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
