# Journey Branch Candidate Replay Runbook

日期：2026-06-26

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9
entry_count = 24
candidate_event_count_seen = 24
candidate_event_count_with_replay_entries = 8
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 3
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
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 36
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
depth_filter_skip_count = 15
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
source_event_time = 49.048261
source_selected_pair = [1, 2]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = 0.64037177
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.048261
source_selected_pair = [1, 2]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 612
source_alt_branch_score = 0.643381602
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.048261
source_selected_pair = [1, 2]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 6
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = 0.628790545
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/003_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/003_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/003_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/003_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.435887
source_selected_pair = [10, 15]
forced_pair = [15, 19]
forced_pair_path_rule = force_pair_path:0:15,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.454545455
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 331
source_alt_pool_total_child_width = 629
source_alt_branch_score = 0.62550925
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/004_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/004_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/004_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/004_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.435887
source_selected_pair = [10, 15]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.363636364
source_alt_required_tie_tolerance = 0.090909091
source_alt_pool_max_child_width = 320
source_alt_pool_total_child_width = 558
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/005_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/005_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/005_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/005_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d0_n0_r3_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.435887
source_selected_pair = [10, 15]
forced_pair = [1, 16]
forced_pair_path_rule = force_pair_path:0:1,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 3
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.363636364
source_alt_required_tie_tolerance = 0.090909091
source_alt_pool_max_child_width = 310
source_alt_pool_total_child_width = 539
source_alt_branch_score = 0.638576126
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/006_candidate_alt_d0_n0_r3_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/006_candidate_alt_d0_n0_r3_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/006_candidate_alt_d0_n0_r3_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/006_candidate_alt_d0_n0_r3_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.955461
source_selected_pair = [5, 9]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:3,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 427
source_alt_pool_total_child_width = 749
source_alt_branch_score = 0.688705599
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/007_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/007_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/007_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/007_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.955461
source_selected_pair = [5, 9]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:3,9
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 421
source_alt_pool_total_child_width = 768
source_alt_branch_score = 0.680701488
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/008_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/008_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/008_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/008_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,9 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.955461
source_selected_pair = [5, 9]
forced_pair = [7, 13]
forced_pair_path_rule = force_pair_path:0:7,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 68
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 397
source_alt_pool_total_child_width = 684
source_alt_branch_score = 0.628896594
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/009_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/009_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/009_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/009_candidate_alt_d0_n0_r68_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d0_n0_r1_13_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 61.622694
source_selected_pair = [13, 16]
forced_pair = [13, 17]
forced_pair_path_rule = force_pair_path:0:13,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 437
source_alt_pool_total_child_width = 827
source_alt_branch_score = 0.677495146
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/010_candidate_alt_d0_n0_r1_13_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/010_candidate_alt_d0_n0_r1_13_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/010_candidate_alt_d0_n0_r1_13_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/010_candidate_alt_d0_n0_r1_13_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:13,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 61.622694
source_selected_pair = [13, 16]
forced_pair = [16, 17]
forced_pair_path_rule = force_pair_path:0:16,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 436
source_alt_pool_total_child_width = 831
source_alt_branch_score = 0.672543573
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/011_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/011_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/011_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/011_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:16,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d0_n0_r5_1_2_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 61.622694
source_selected_pair = [13, 16]
forced_pair = [1, 2]
forced_pair_path_rule = force_pair_path:0:1,2
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 5
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 424
source_alt_pool_total_child_width = 746
source_alt_branch_score = 0.682629555
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/012_candidate_alt_d0_n0_r5_1_2_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/012_candidate_alt_d0_n0_r5_1_2_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/012_candidate_alt_d0_n0_r5_1_2_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/012_candidate_alt_d0_n0_r5_1_2_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,2 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.761006
source_selected_pair = [4, 7]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,8
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 332
source_alt_pool_total_child_width = 615
source_alt_branch_score = 0.650687385
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/013_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,8 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.761006
source_selected_pair = [4, 7]
forced_pair = [4, 9]
forced_pair_path_rule = force_pair_path:0:4,9
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 325
source_alt_pool_total_child_width = 569
source_alt_branch_score = 0.647457916
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/014_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,9 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.761006
source_selected_pair = [4, 7]
forced_pair = [8, 9]
forced_pair_path_rule = force_pair_path:0:8,9
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 7
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 329
source_alt_pool_total_child_width = 583
source_alt_branch_score = 0.640348178
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/015_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/015_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/015_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/015_candidate_alt_d0_n0_r7_8_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,9 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 126.610832
source_selected_pair = [1, 4]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:1,6
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 630
source_alt_pool_total_child_width = 1073
source_alt_branch_score = 0.707990426
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/016_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/016_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/016_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/016_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,6 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 126.610832
source_selected_pair = [1, 4]
forced_pair = [1, 19]
forced_pair_path_rule = force_pair_path:0:1,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 643
source_alt_pool_total_child_width = 1116
source_alt_branch_score = 0.709810925
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/017_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/017_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/017_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/017_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d0_n0_r49_9_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 126.610832
source_selected_pair = [1, 4]
forced_pair = [9, 20]
forced_pair_path_rule = force_pair_path:0:9,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 49
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 600
source_alt_pool_total_child_width = 989
source_alt_branch_score = 0.677744919
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/018_candidate_alt_d0_n0_r49_9_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/018_candidate_alt_d0_n0_r49_9_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/018_candidate_alt_d0_n0_r49_9_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/018_candidate_alt_d0_n0_r49_9_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.383049
source_selected_pair = [8, 13]
forced_pair = [8, 16]
forced_pair_path_rule = force_pair_path:0:8,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 299
source_alt_pool_total_child_width = 557
source_alt_branch_score = 0.633325857
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/019_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/019_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/019_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/019_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.383049
source_selected_pair = [8, 13]
forced_pair = [12, 17]
forced_pair_path_rule = force_pair_path:0:12,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 498
source_alt_branch_score = 0.622402632
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/020_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/020_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/020_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/020_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.383049
source_selected_pair = [8, 13]
forced_pair = [8, 17]
forced_pair_path_rule = force_pair_path:0:8,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 15
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 285
source_alt_pool_total_child_width = 487
source_alt_branch_score = 0.621323836
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/021_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/021_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/021_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/021_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.681832
source_selected_pair = [1, 9]
forced_pair = [1, 12]
forced_pair_path_rule = force_pair_path:0:1,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 370
source_alt_pool_total_child_width = 681
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/022_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/022_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/022_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/022_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.681832
source_selected_pair = [1, 9]
forced_pair = [2, 4]
forced_pair_path_rule = force_pair_path:0:2,4
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 690
source_alt_branch_score = 0.647095364
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/023_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/023_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/023_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/023_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,4 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d0_n0_r17_7_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.681832
source_selected_pair = [1, 9]
forced_pair = [7, 11]
forced_pair_path_rule = force_pair_path:0:7,11
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 17
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 333
source_alt_pool_total_child_width = 566
source_alt_branch_score = 0.617165869
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/024_candidate_alt_d0_n0_r17_7_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/024_candidate_alt_d0_n0_r17_7_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/024_candidate_alt_d0_n0_r17_7_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v442_root_child_probe_from_v441_failed9/runs/024_candidate_alt_d0_n0_r17_7_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,11 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
