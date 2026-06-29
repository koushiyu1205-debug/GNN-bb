# Journey Branch Candidate Replay Runbook

日期：2026-06-27

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627
entry_count = 96
candidate_event_count_seen = 511
candidate_event_count_with_replay_entries = 16
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 6
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 1
max_source_depth = 1
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 24
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
depth_filter_skip_count = 465
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 80.908036
source_selected_pair = [1, 10]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:2,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 231
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:2,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 80.908036
source_selected_pair = [1, 10]
forced_pair = [5, 11]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:5,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 231
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:5,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 80.908036
source_selected_pair = [1, 10]
forced_pair = [5, 10]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:5,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 29
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/003_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/003_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/003_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/003_candidate_alt_d1_n1_r29_5_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:5,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d1_n1_r28_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 80.908036
source_selected_pair = [1, 10]
forced_pair = [15, 16]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:15,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 28
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.066666667
source_alt_pool_max_child_width = 237
source_alt_pool_total_child_width = 450
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/004_candidate_alt_d1_n1_r28_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/004_candidate_alt_d1_n1_r28_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/004_candidate_alt_d1_n1_r28_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/004_candidate_alt_d1_n1_r28_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:15,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d1_n1_r15_5_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 80.908036
source_selected_pair = [1, 10]
forced_pair = [5, 20]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:5,20
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 15
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 228
source_alt_pool_total_child_width = 387
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/005_candidate_alt_d1_n1_r15_5_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/005_candidate_alt_d1_n1_r15_5_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/005_candidate_alt_d1_n1_r15_5_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/005_candidate_alt_d1_n1_r15_5_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:5,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 80.908036
source_selected_pair = [1, 10]
forced_pair = [10, 18]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:10,18
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 4
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/006_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/006_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/006_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/006_candidate_alt_d1_n1_r4_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:10,18' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 107.557018
source_selected_pair = [4, 12]
forced_pair = [4, 13]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 387
source_alt_pool_total_child_width = 692
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/007_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/007_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/007_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/007_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 107.557018
source_selected_pair = [4, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 384
source_alt_pool_total_child_width = 711
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/008_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/008_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/008_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/008_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d1_n2_r7_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 107.557018
source_selected_pair = [4, 12]
forced_pair = [12, 13]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:12,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 7
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 382
source_alt_pool_total_child_width = 702
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/009_candidate_alt_d1_n2_r7_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/009_candidate_alt_d1_n2_r7_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/009_candidate_alt_d1_n2_r7_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/009_candidate_alt_d1_n2_r7_12_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:12,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d1_n2_r6_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 107.557018
source_selected_pair = [4, 12]
forced_pair = [15, 16]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:15,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 6
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 383
source_alt_pool_total_child_width = 728
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/010_candidate_alt_d1_n2_r6_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/010_candidate_alt_d1_n2_r6_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/010_candidate_alt_d1_n2_r6_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/010_candidate_alt_d1_n2_r6_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:15,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d1_n2_r4_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 107.557018
source_selected_pair = [4, 12]
forced_pair = [12, 15]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:12,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 4
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 385
source_alt_pool_total_child_width = 715
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/011_candidate_alt_d1_n2_r4_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/011_candidate_alt_d1_n2_r4_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/011_candidate_alt_d1_n2_r4_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/011_candidate_alt_d1_n2_r4_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:12,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d1_n2_r3_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 107.557018
source_selected_pair = [4, 12]
forced_pair = [4, 16]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 3
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 384
source_alt_pool_total_child_width = 713
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/012_candidate_alt_d1_n2_r3_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/012_candidate_alt_d1_n2_r3_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/012_candidate_alt_d1_n2_r3_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/012_candidate_alt_d1_n2_r3_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d1_n1_r1_2_4_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 429.596324
source_selected_pair = [2, 3]
forced_pair = [2, 4]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,4
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 236
source_alt_pool_total_child_width = 385
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/013_candidate_alt_d1_n1_r1_2_4_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/013_candidate_alt_d1_n1_r1_2_4_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/013_candidate_alt_d1_n1_r1_2_4_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/013_candidate_alt_d1_n1_r1_2_4_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,4' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 429.596324
source_selected_pair = [2, 3]
forced_pair = [2, 6]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,6
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/014_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/014_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/014_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/014_candidate_alt_d1_n1_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,6' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 429.596324
source_selected_pair = [2, 3]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 6
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/015_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/015_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/015_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/015_candidate_alt_d1_n1_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 429.596324
source_selected_pair = [2, 3]
forced_pair = [2, 12]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 5
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 213
source_alt_pool_total_child_width = 400
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/016_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/016_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/016_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/016_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d1_n1_r39_15_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 429.596324
source_selected_pair = [2, 3]
forced_pair = [15, 20]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:15,20
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 39
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 251
source_alt_pool_total_child_width = 447
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/017_candidate_alt_d1_n1_r39_15_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/017_candidate_alt_d1_n1_r39_15_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/017_candidate_alt_d1_n1_r39_15_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/017_candidate_alt_d1_n1_r39_15_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:15,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 429.596324
source_selected_pair = [2, 3]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:6,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 24
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 220
source_alt_pool_total_child_width = 412
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/018_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/018_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/018_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/018_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:6,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d1_n2_r1_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 521.301848
source_selected_pair = [2, 3]
forced_pair = [2, 6]
forced_pair_path_rule = force_pair_path:0:1,18=separate_vehicle;1:2,6
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 282
source_alt_pool_total_child_width = 538
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/019_candidate_alt_d1_n2_r1_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/019_candidate_alt_d1_n2_r1_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/019_candidate_alt_d1_n2_r1_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/019_candidate_alt_d1_n2_r1_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=separate_vehicle;1:2,6' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d1_n2_r2_2_7_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 521.301848
source_selected_pair = [2, 3]
forced_pair = [2, 7]
forced_pair_path_rule = force_pair_path:0:1,18=separate_vehicle;1:2,7
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 300
source_alt_pool_total_child_width = 524
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/020_candidate_alt_d1_n2_r2_2_7_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/020_candidate_alt_d1_n2_r2_2_7_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/020_candidate_alt_d1_n2_r2_2_7_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/020_candidate_alt_d1_n2_r2_2_7_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=separate_vehicle;1:2,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d1_n2_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 521.301848
source_selected_pair = [2, 3]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:1,18=separate_vehicle;1:6,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 30
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 285
source_alt_pool_total_child_width = 541
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/021_candidate_alt_d1_n2_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/021_candidate_alt_d1_n2_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/021_candidate_alt_d1_n2_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/021_candidate_alt_d1_n2_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=separate_vehicle;1:6,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d1_n2_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 521.301848
source_selected_pair = [2, 3]
forced_pair = [2, 12]
forced_pair_path_rule = force_pair_path:0:1,18=separate_vehicle;1:2,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 5
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 286
source_alt_pool_total_child_width = 537
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/022_candidate_alt_d1_n2_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/022_candidate_alt_d1_n2_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/022_candidate_alt_d1_n2_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/022_candidate_alt_d1_n2_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=separate_vehicle;1:2,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d1_n2_r56_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 521.301848
source_selected_pair = [2, 3]
forced_pair = [18, 20]
forced_pair_path_rule = force_pair_path:0:1,18=separate_vehicle;1:18,20
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 56
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 331
source_alt_pool_total_child_width = 563
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/023_candidate_alt_d1_n2_r56_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/023_candidate_alt_d1_n2_r56_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/023_candidate_alt_d1_n2_r56_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/023_candidate_alt_d1_n2_r56_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=separate_vehicle;1:18,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d1_n2_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 521.301848
source_selected_pair = [2, 3]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:1,18=separate_vehicle;1:2,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 6
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 286
source_alt_pool_total_child_width = 529
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/024_candidate_alt_d1_n2_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/024_candidate_alt_d1_n2_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/024_candidate_alt_d1_n2_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/024_candidate_alt_d1_n2_r6_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=separate_vehicle;1:2,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 025_candidate_alt_d1_n1_r1_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 217.832949
source_selected_pair = [1, 15]
forced_pair = [1, 17]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:1,17
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.285714286
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 666
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/025_candidate_alt_d1_n1_r1_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/025_candidate_alt_d1_n1_r1_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/025_candidate_alt_d1_n1_r1_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/025_candidate_alt_d1_n1_r1_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:1,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 026_candidate_alt_d1_n1_r2_4_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 217.832949
source_selected_pair = [1, 15]
forced_pair = [4, 10]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:4,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.285714286
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 378
source_alt_pool_total_child_width = 703
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/026_candidate_alt_d1_n1_r2_4_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/026_candidate_alt_d1_n1_r2_4_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/026_candidate_alt_d1_n1_r2_4_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/026_candidate_alt_d1_n1_r2_4_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:4,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 027_candidate_alt_d1_n1_r20_12_14_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 217.832949
source_selected_pair = [1, 15]
forced_pair = [12, 14]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:12,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 20
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.285714286
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 352
source_alt_pool_total_child_width = 590
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/027_candidate_alt_d1_n1_r20_12_14_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/027_candidate_alt_d1_n1_r20_12_14_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/027_candidate_alt_d1_n1_r20_12_14_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/027_candidate_alt_d1_n1_r20_12_14_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:12,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 028_candidate_alt_d1_n1_r16_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 217.832949
source_selected_pair = [1, 15]
forced_pair = [4, 16]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:4,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 16
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.285714286
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 375
source_alt_pool_total_child_width = 709
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/028_candidate_alt_d1_n1_r16_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/028_candidate_alt_d1_n1_r16_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/028_candidate_alt_d1_n1_r16_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/028_candidate_alt_d1_n1_r16_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:4,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 029_candidate_alt_d1_n1_r28_10_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 217.832949
source_selected_pair = [1, 15]
forced_pair = [10, 16]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:10,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 28
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.285714286
source_alt_fractionality = 0.142857143
source_alt_required_tie_tolerance = 0.142857143
source_alt_pool_max_child_width = 379
source_alt_pool_total_child_width = 688
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/029_candidate_alt_d1_n1_r28_10_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/029_candidate_alt_d1_n1_r28_10_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/029_candidate_alt_d1_n1_r28_10_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/029_candidate_alt_d1_n1_r28_10_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:10,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 030_candidate_alt_d1_n1_r25_14_20_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 217.832949
source_selected_pair = [1, 15]
forced_pair = [14, 20]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:14,20
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 24
source_alt_rank = 25
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.285714286
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 355
source_alt_pool_total_child_width = 588
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/030_candidate_alt_d1_n1_r25_14_20_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/030_candidate_alt_d1_n1_r25_14_20_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/030_candidate_alt_d1_n1_r25_14_20_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/runs/030_candidate_alt_d1_n1_r25_14_20_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:14,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

- Report truncated to first 30 entries; full runbook has 96 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
