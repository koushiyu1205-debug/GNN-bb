# Journey Branch Candidate Replay Runbook

日期：2026-06-27

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627
entry_count = 160
candidate_event_count_seen = 511
candidate_event_count_with_replay_entries = 20
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 8
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 0
max_source_depth = 0
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runbook.json']
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = 3
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 24
excluded_entry_key_count = 48
excluded_entry_skip_count = 23
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 487
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
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/001_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/002_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r19_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [18, 20]
forced_pair_path_rule = force_pair_path:0:18,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 19
source_alt_selection_reason = best_branch_score
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 387
source_alt_pool_total_child_width = 676
source_alt_branch_score = 0.382223102
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/003_candidate_alt_d0_n0_r19_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/003_candidate_alt_d0_n0_r19_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/003_candidate_alt_d0_n0_r19_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/003_candidate_alt_d0_n0_r19_18_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:18,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r12_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [5, 18]
forced_pair_path_rule = force_pair_path:0:5,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 12
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 375
source_alt_pool_total_child_width = 611
source_alt_branch_score = 0.294287743
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/004_candidate_alt_d0_n0_r12_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/004_candidate_alt_d0_n0_r12_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/004_candidate_alt_d0_n0_r12_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/004_candidate_alt_d0_n0_r12_5_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [10, 18]
forced_pair_path_rule = force_pair_path:0:10,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 14
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 374
source_alt_pool_total_child_width = 634
source_alt_branch_score = 0.325553331
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [1, 20]
forced_pair_path_rule = force_pair_path:0:1,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 5
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 374
source_alt_pool_total_child_width = 664
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d0_n0_r7_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:2,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 7
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 376
source_alt_pool_total_child_width = 607
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/007_candidate_alt_d0_n0_r7_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/007_candidate_alt_d0_n0_r7_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/007_candidate_alt_d0_n0_r7_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/007_candidate_alt_d0_n0_r7_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r11_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.463464
source_selected_pair = [1, 2]
forced_pair = [5, 14]
forced_pair_path_rule = force_pair_path:0:5,14
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 11
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 378
source_alt_pool_total_child_width = 600
source_alt_branch_score = 0.289147611
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/008_candidate_alt_d0_n0_r11_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/008_candidate_alt_d0_n0_r11_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/008_candidate_alt_d0_n0_r11_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/008_candidate_alt_d0_n0_r11_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:6,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 30
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 296
source_alt_pool_total_child_width = 563
source_alt_branch_score = 0.205500297
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/009_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/009_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/009_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/009_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d0_n0_r6_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [2, 12]
forced_pair_path_rule = force_pair_path:0:2,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 6
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 297
source_alt_pool_total_child_width = 560
source_alt_branch_score = 0.202415054
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/010_candidate_alt_d0_n0_r6_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/010_candidate_alt_d0_n0_r6_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/010_candidate_alt_d0_n0_r6_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/010_candidate_alt_d0_n0_r6_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d0_n0_r56_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [18, 19]
forced_pair_path_rule = force_pair_path:0:18,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 56
source_alt_selection_reason = best_branch_score
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 345
source_alt_pool_total_child_width = 609
source_alt_branch_score = 0.234226787
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/011_candidate_alt_d0_n0_r56_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/011_candidate_alt_d0_n0_r56_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/011_candidate_alt_d0_n0_r56_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/011_candidate_alt_d0_n0_r56_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:18,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d0_n0_r43_8_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [8, 13]
forced_pair_path_rule = force_pair_path:0:8,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 43
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 307
source_alt_pool_total_child_width = 554
source_alt_branch_score = 0.203578924
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/012_candidate_alt_d0_n0_r43_8_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/012_candidate_alt_d0_n0_r43_8_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/012_candidate_alt_d0_n0_r43_8_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/012_candidate_alt_d0_n0_r43_8_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d0_n0_r7_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:2,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 7
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 298
source_alt_pool_total_child_width = 552
source_alt_branch_score = 0.199570251
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/013_candidate_alt_d0_n0_r7_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/013_candidate_alt_d0_n0_r7_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/013_candidate_alt_d0_n0_r7_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/013_candidate_alt_d0_n0_r7_2_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d0_n0_r34_6_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [6, 17]
forced_pair_path_rule = force_pair_path:0:6,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 34
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 308
source_alt_pool_total_child_width = 540
source_alt_branch_score = 0.210103586
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/014_candidate_alt_d0_n0_r34_6_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/014_candidate_alt_d0_n0_r34_6_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/014_candidate_alt_d0_n0_r34_6_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/014_candidate_alt_d0_n0_r34_6_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d0_n0_r31_6_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [6, 13]
forced_pair_path_rule = force_pair_path:0:6,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 31
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 309
source_alt_pool_total_child_width = 543
source_alt_branch_score = 0.20232169
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/015_candidate_alt_d0_n0_r31_6_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/015_candidate_alt_d0_n0_r31_6_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/015_candidate_alt_d0_n0_r31_6_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/015_candidate_alt_d0_n0_r31_6_13_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d0_n0_r49_12_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 247.559256
source_selected_pair = [1, 18]
forced_pair = [12, 17]
forced_pair_path_rule = force_pair_path:0:12,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 49
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 312
source_alt_pool_total_child_width = 539
source_alt_branch_score = 0.218182883
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/016_candidate_alt_d0_n0_r49_12_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/016_candidate_alt_d0_n0_r49_12_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/016_candidate_alt_d0_n0_r49_12_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/016_candidate_alt_d0_n0_r49_12_17_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d0_n0_r19_1_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [1, 16]
forced_pair_path_rule = force_pair_path:0:1,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 19
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.111111111
source_alt_required_tie_tolerance = 0.111111111
source_alt_pool_max_child_width = 468
source_alt_pool_total_child_width = 867
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/017_candidate_alt_d0_n0_r19_1_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/017_candidate_alt_d0_n0_r19_1_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/017_candidate_alt_d0_n0_r19_1_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/017_candidate_alt_d0_n0_r19_1_16_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d0_n0_r17_16_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [16, 17]
forced_pair_path_rule = force_pair_path:0:16,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 17
source_alt_selection_reason = best_branch_score
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 477
source_alt_pool_total_child_width = 864
source_alt_branch_score = 0.568310446
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/018_candidate_alt_d0_n0_r17_16_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/018_candidate_alt_d0_n0_r17_16_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/018_candidate_alt_d0_n0_r17_16_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/018_candidate_alt_d0_n0_r17_16_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:16,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d0_n0_r10_1_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [1, 15]
forced_pair_path_rule = force_pair_path:0:1,15
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 10
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 465
source_alt_pool_total_child_width = 834
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/019_candidate_alt_d0_n0_r10_1_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/019_candidate_alt_d0_n0_r10_1_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/019_candidate_alt_d0_n0_r10_1_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/019_candidate_alt_d0_n0_r10_1_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d0_n0_r11_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [1, 17]
forced_pair_path_rule = force_pair_path:0:1,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 11
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 466
source_alt_pool_total_child_width = 848
source_alt_branch_score = 0.519837135
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/020_candidate_alt_d0_n0_r11_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/020_candidate_alt_d0_n0_r11_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/020_candidate_alt_d0_n0_r11_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/020_candidate_alt_d0_n0_r11_1_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 9
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 468
source_alt_pool_total_child_width = 816
source_alt_branch_score = 0.503131205
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/021_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/021_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/021_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/021_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:4,15
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 4
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 469
source_alt_pool_total_child_width = 806
source_alt_branch_score = 0.525039703
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/022_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/022_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/022_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/022_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d0_n0_r18_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 18
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.111111111
source_alt_required_tie_tolerance = 0.111111111
source_alt_pool_max_child_width = 469
source_alt_pool_total_child_width = 869
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/023_candidate_alt_d0_n0_r18_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/023_candidate_alt_d0_n0_r18_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/023_candidate_alt_d0_n0_r18_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/023_candidate_alt_d0_n0_r18_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d0_n0_r8_15_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 133.095187
source_selected_pair = [4, 7]
forced_pair = [15, 17]
forced_pair_path_rule = force_pair_path:0:15,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 8
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 470
source_alt_pool_total_child_width = 835
source_alt_branch_score = 0.555377489
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/024_candidate_alt_d0_n0_r8_15_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/024_candidate_alt_d0_n0_r8_15_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/024_candidate_alt_d0_n0_r8_15_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/024_candidate_alt_d0_n0_r8_15_17_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 025_candidate_alt_d0_n0_r9_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 122.66354
source_selected_pair = [1, 2]
forced_pair = [2, 3]
forced_pair_path_rule = force_pair_path:0:2,3
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 9
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.071428571
source_alt_pool_max_child_width = 367
source_alt_pool_total_child_width = 595
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/025_candidate_alt_d0_n0_r9_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/025_candidate_alt_d0_n0_r9_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/025_candidate_alt_d0_n0_r9_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/025_candidate_alt_d0_n0_r9_2_3_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,3 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 026_candidate_alt_d0_n0_r48_7_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 122.66354
source_selected_pair = [1, 2]
forced_pair = [7, 19]
forced_pair_path_rule = force_pair_path:0:7,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 48
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.142857143
source_alt_required_tie_tolerance = 0.357142857
source_alt_pool_max_child_width = 384
source_alt_pool_total_child_width = 743
source_alt_branch_score = 0.403871244
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/026_candidate_alt_d0_n0_r48_7_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/026_candidate_alt_d0_n0_r48_7_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/026_candidate_alt_d0_n0_r48_7_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/026_candidate_alt_d0_n0_r48_7_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 027_candidate_alt_d0_n0_r27_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 122.66354
source_selected_pair = [1, 2]
forced_pair = [18, 19]
forced_pair_path_rule = force_pair_path:0:18,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 27
source_alt_selection_reason = best_branch_score
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.071428571
source_alt_pool_max_child_width = 394
source_alt_pool_total_child_width = 709
source_alt_branch_score = 0.443259743
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/027_candidate_alt_d0_n0_r27_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/027_candidate_alt_d0_n0_r27_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/027_candidate_alt_d0_n0_r27_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/027_candidate_alt_d0_n0_r27_18_19_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:18,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 028_candidate_alt_d0_n0_r59_9_20_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 122.66354
source_selected_pair = [1, 2]
forced_pair = [9, 20]
forced_pair_path_rule = force_pair_path:0:9,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 59
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.071428571
source_alt_required_tie_tolerance = 0.428571429
source_alt_pool_max_child_width = 395
source_alt_pool_total_child_width = 730
source_alt_branch_score = 0.412379426
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/028_candidate_alt_d0_n0_r59_9_20_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/028_candidate_alt_d0_n0_r59_9_20_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/028_candidate_alt_d0_n0_r59_9_20_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/028_candidate_alt_d0_n0_r59_9_20_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 029_candidate_alt_d0_n0_r30_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 122.66354
source_selected_pair = [1, 2]
forced_pair = [3, 13]
forced_pair_path_rule = force_pair_path:0:3,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 30
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.071428571
source_alt_pool_max_child_width = 373
source_alt_pool_total_child_width = 597
source_alt_branch_score = 0.344586188
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/029_candidate_alt_d0_n0_r30_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/029_candidate_alt_d0_n0_r30_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/029_candidate_alt_d0_n0_r30_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/029_candidate_alt_d0_n0_r30_3_13_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 030_candidate_alt_d0_n0_r32_3_17_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 122.66354
source_selected_pair = [1, 2]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:3,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 24
source_alt_rank = 32
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.071428571
source_alt_pool_max_child_width = 375
source_alt_pool_total_child_width = 611
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/030_candidate_alt_d0_n0_r32_3_17_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/030_candidate_alt_d0_n0_r32_3_17_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/030_candidate_alt_d0_n0_r32_3_17_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runs/030_candidate_alt_d0_n0_r32_3_17_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=24 --set journey_max_cg_iterations=24 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

- Report truncated to first 30 entries; full runbook has 160 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
