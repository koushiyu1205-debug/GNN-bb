# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628
entry_count = 48
candidate_event_count_seen = 201
candidate_event_count_with_replay_entries = 24
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 1
max_source_depth = 4
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = ['BPC_future/results/20260628_v569_branch_timeout_evidence/deep_missing_context_rows.jsonl']
coverage_gap_only = True
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 18
max_events_per_instance = 6
instance_event_limit_skip_count = 54
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 6, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json': 6, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json': 6, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 6}
excluded_entry_key_count = 0
excluded_entry_skip_count = 0
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 191
coverage_gap_skip_count = 0
depth_filter_skip_count = 108
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
source_event_time = 79.387847
source_selected_pair = [1, 10]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:2,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
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
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/001_candidate_alt_d1_n1_r1_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:2,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 79.387847
source_selected_pair = [1, 10]
forced_pair = [5, 11]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:5,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
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
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/002_candidate_alt_d1_n1_r2_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:5,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 105.485324
source_selected_pair = [4, 12]
forced_pair = [4, 13]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
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
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 105.485324
source_selected_pair = [4, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
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
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/004_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/004_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/004_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/004_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d2_n3_r1_1_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 144.789244
source_selected_pair = [1, 5]
forced_pair = [1, 14]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,14
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 179
source_alt_pool_total_child_width = 306
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/005_candidate_alt_d2_n3_r1_1_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/005_candidate_alt_d2_n3_r1_1_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/005_candidate_alt_d2_n3_r1_1_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/005_candidate_alt_d2_n3_r1_1_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d2_n3_r2_1_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 144.789244
source_selected_pair = [1, 5]
forced_pair = [1, 18]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,18
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 177
source_alt_pool_total_child_width = 311
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/006_candidate_alt_d2_n3_r2_1_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/006_candidate_alt_d2_n3_r2_1_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/006_candidate_alt_d2_n3_r2_1_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/006_candidate_alt_d2_n3_r2_1_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,18' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d2_n4_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 168.392358
source_selected_pair = [4, 13]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:1,10=separate_vehicle;2:4,15
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 268
source_alt_pool_total_child_width = 498
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/007_candidate_alt_d2_n4_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/007_candidate_alt_d2_n4_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/007_candidate_alt_d2_n4_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/007_candidate_alt_d2_n4_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:1,10=separate_vehicle;2:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d2_n4_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 168.392358
source_selected_pair = [4, 13]
forced_pair = [4, 16]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:1,10=separate_vehicle;2:4,16
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 268
source_alt_pool_total_child_width = 495
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/008_candidate_alt_d2_n4_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/008_candidate_alt_d2_n4_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/008_candidate_alt_d2_n4_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/008_candidate_alt_d2_n4_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:1,10=separate_vehicle;2:4,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d2_n5_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 188.483475
source_selected_pair = [4, 13]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,12=same_vehicle;2:4,15
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 362
source_alt_pool_total_child_width = 681
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/009_candidate_alt_d2_n5_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/009_candidate_alt_d2_n5_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/009_candidate_alt_d2_n5_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/009_candidate_alt_d2_n5_r1_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,12=same_vehicle;2:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d2_n5_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 188.483475
source_selected_pair = [4, 13]
forced_pair = [4, 16]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,12=same_vehicle;2:4,16
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 362
source_alt_pool_total_child_width = 687
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/010_candidate_alt_d2_n5_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/010_candidate_alt_d2_n5_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/010_candidate_alt_d2_n5_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/010_candidate_alt_d2_n5_r2_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,12=same_vehicle;2:4,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d3_n7_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 7
source_depth = 3
source_event_time = 256.346558
source_selected_pair = [4, 12]
forced_pair = [4, 13]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,5=same_vehicle;3:4,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 131
source_alt_pool_total_child_width = 226
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/011_candidate_alt_d3_n7_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/011_candidate_alt_d3_n7_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/011_candidate_alt_d3_n7_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/011_candidate_alt_d3_n7_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,5=same_vehicle;3:4,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d3_n7_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 7
source_depth = 3
source_event_time = 256.346558
source_selected_pair = [4, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,5=same_vehicle;3:4,15
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 127
source_alt_pool_total_child_width = 233
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/012_candidate_alt_d3_n7_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/012_candidate_alt_d3_n7_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/012_candidate_alt_d3_n7_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/012_candidate_alt_d3_n7_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:1,10=same_vehicle;2:1,5=same_vehicle;3:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d1_n1_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 82.941008
source_selected_pair = [1, 6]
forced_pair = [1, 7]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,7
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 365
source_alt_pool_total_child_width = 608
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/013_candidate_alt_d1_n1_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/013_candidate_alt_d1_n1_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/013_candidate_alt_d1_n1_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/013_candidate_alt_d1_n1_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d1_n1_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 82.941008
source_selected_pair = [1, 6]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,8
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 366
source_alt_pool_total_child_width = 665
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/014_candidate_alt_d1_n1_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/014_candidate_alt_d1_n1_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/014_candidate_alt_d1_n1_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/014_candidate_alt_d1_n1_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d1_n2_r1_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.224443
source_selected_pair = [4, 6]
forced_pair = [4, 12]
forced_pair_path_rule = force_pair_path:0:5,9=separate_vehicle;1:4,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 518
source_alt_pool_total_child_width = 900
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n2_r1_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n2_r1_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n2_r1_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n2_r1_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=separate_vehicle;1:4,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d1_n2_r2_4_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.224443
source_selected_pair = [4, 6]
forced_pair = [4, 17]
forced_pair_path_rule = force_pair_path:0:5,9=separate_vehicle;1:4,17
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 516
source_alt_pool_total_child_width = 921
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n2_r2_4_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n2_r2_4_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n2_r2_4_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n2_r2_4_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=separate_vehicle;1:4,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d2_n3_r1_3_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 149.659245
source_selected_pair = [3, 7]
forced_pair = [3, 19]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=same_vehicle;2:3,19
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 292
source_alt_pool_total_child_width = 486
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/017_candidate_alt_d2_n3_r1_3_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/017_candidate_alt_d2_n3_r1_3_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/017_candidate_alt_d2_n3_r1_3_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/017_candidate_alt_d2_n3_r1_3_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=same_vehicle;2:3,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d2_n3_r2_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 149.659245
source_selected_pair = [3, 7]
forced_pair = [7, 15]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=same_vehicle;2:7,15
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 295
source_alt_pool_total_child_width = 491
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/018_candidate_alt_d2_n3_r2_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/018_candidate_alt_d2_n3_r2_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/018_candidate_alt_d2_n3_r2_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/018_candidate_alt_d2_n3_r2_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=same_vehicle;2:7,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d2_n4_r1_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 176.124683
source_selected_pair = [1, 7]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,8
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 415
source_alt_pool_total_child_width = 759
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d2_n4_r2_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 176.124683
source_selected_pair = [1, 7]
forced_pair = [1, 11]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,11
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 412
source_alt_pool_total_child_width = 769
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 9
source_depth = 3
source_event_time = 199.062891
source_selected_pair = [1, 8]
forced_pair = [1, 11]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,11
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 277
source_alt_pool_total_child_width = 525
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/021_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/021_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/021_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/021_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 9
source_depth = 3
source_event_time = 199.062891
source_selected_pair = [1, 8]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 275
source_alt_pool_total_child_width = 499
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/022_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/022_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/022_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/022_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d3_n10_r1_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 220.757752
source_selected_pair = [2, 5]
forced_pair = [2, 9]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:2,9
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 411
source_alt_pool_total_child_width = 780
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/023_candidate_alt_d3_n10_r1_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/023_candidate_alt_d3_n10_r1_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/023_candidate_alt_d3_n10_r1_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/023_candidate_alt_d3_n10_r1_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:2,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 220.757752
source_selected_pair = [2, 5]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 406
source_alt_pool_total_child_width = 711
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/024_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/024_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/024_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/024_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,9=same_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 025_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 144.009169
source_selected_pair = [4, 5]
forced_pair = [4, 7]
forced_pair_path_rule = force_pair_path:0:4,9=same_vehicle;1:4,7
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 264
source_alt_pool_total_child_width = 508
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/025_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/025_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/025_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/025_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=same_vehicle;1:4,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 026_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 144.009169
source_selected_pair = [4, 5]
forced_pair = [4, 11]
forced_pair_path_rule = force_pair_path:0:4,9=same_vehicle;1:4,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 270
source_alt_pool_total_child_width = 506
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/026_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/026_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/026_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/026_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=same_vehicle;1:4,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 027_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 191.708956
source_selected_pair = [3, 8]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,9
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 352
source_alt_pool_total_child_width = 627
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/027_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/027_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/027_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/027_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 028_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 191.708956
source_selected_pair = [3, 8]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 349
source_alt_pool_total_child_width = 625
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/028_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/028_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/028_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/028_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 029_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 303.110244
source_selected_pair = [8, 12]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:4,8
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 360
source_alt_pool_total_child_width = 632
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/029_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/029_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/029_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/029_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:4,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 030_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 303.110244
source_selected_pair = [8, 12]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:5,8
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 18
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 357
source_alt_pool_total_child_width = 661
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/030_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/030_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/030_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs/030_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:5,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=18 --set journey_max_cg_iterations=18 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

- Report truncated to first 30 entries; full runbook has 48 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
