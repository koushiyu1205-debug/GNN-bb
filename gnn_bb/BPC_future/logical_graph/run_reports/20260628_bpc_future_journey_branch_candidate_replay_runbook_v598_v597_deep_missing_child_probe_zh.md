# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628
entry_count = 24
candidate_event_count_seen = 88
candidate_event_count_with_replay_entries = 12
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 1
max_source_depth = 4
max_source_event_time = 360.0
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_v597_v596_timeout_suppressed_root035_smoke4_20260628/summary.json']
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = ['BPC_future/results/20260628_v569_branch_timeout_evidence/deep_missing_context_rows.jsonl', 'BPC_future/results/20260628_v597_branch_timeout_evidence/deep_missing_context_rows.jsonl']
coverage_gap_only = True
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 36
max_events_per_instance = 6
instance_event_limit_skip_count = 0
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json': 6, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json': 3, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 2}
excluded_entry_key_count = 0
excluded_entry_skip_count = 0
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 265
coverage_gap_skip_count = 0
depth_filter_skip_count = 43
source_event_time_filter_skip_count = 11
branch_impact_priority_context_count = 88
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d4_n13_r1_5_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 13
source_depth = 4
source_event_time = 303.279536
source_selected_pair = [3, 5]
forced_pair = [5, 9]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,8=same_vehicle;4:5,9
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 404
source_alt_pool_total_child_width = 733
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=15;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/001_candidate_alt_d4_n13_r1_5_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/001_candidate_alt_d4_n13_r1_5_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/001_candidate_alt_d4_n13_r1_5_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/001_candidate_alt_d4_n13_r1_5_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,8=same_vehicle;4:5,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d4_n13_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 13
source_depth = 4
source_event_time = 303.279536
source_selected_pair = [3, 5]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,8=same_vehicle;4:3,9
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 390
source_alt_pool_total_child_width = 716
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=15;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/002_candidate_alt_d4_n13_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/002_candidate_alt_d4_n13_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/002_candidate_alt_d4_n13_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/002_candidate_alt_d4_n13_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,8=same_vehicle;4:3,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d2_n5_r1_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 159.664289
source_selected_pair = [3, 5]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=same_vehicle;2:3,9
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 346
source_alt_pool_total_child_width = 625
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 33.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=same_vehicle;2:3,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d2_n5_r2_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 159.664289
source_selected_pair = [3, 5]
forced_pair = [4, 5]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=same_vehicle;2:4,5
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 359
source_alt_pool_total_child_width = 648
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 33.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=same_vehicle;2:4,5' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 9
source_depth = 3
source_event_time = 204.850247
source_selected_pair = [1, 8]
forced_pair = [1, 11]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,11
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 313
source_alt_pool_total_child_width = 591
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 33.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/005_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/005_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/005_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/005_candidate_alt_d3_n9_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 9
source_depth = 3
source_event_time = 204.850247
source_selected_pair = [1, 8]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 309
source_alt_pool_total_child_width = 558
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 33.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/006_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/006_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/006_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/006_candidate_alt_d3_n9_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 214.648187
source_selected_pair = [3, 8]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,9
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
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
branch_impact_priority = 33.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/007_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/007_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/007_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/007_candidate_alt_d1_n2_r1_3_9_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 214.648187
source_selected_pair = [3, 8]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
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
branch_impact_priority = 33.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/008_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/008_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/008_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/008_candidate_alt_d1_n2_r2_3_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d1_n2_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 134.004626
source_selected_pair = [1, 6]
forced_pair = [1, 7]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,7
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 455
source_alt_pool_total_child_width = 759
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 32.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/009_candidate_alt_d1_n2_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/009_candidate_alt_d1_n2_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/009_candidate_alt_d1_n2_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/009_candidate_alt_d1_n2_r1_1_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d1_n2_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 134.004626
source_selected_pair = [1, 6]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,8
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 461
source_alt_pool_total_child_width = 832
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 32.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/010_candidate_alt_d1_n2_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/010_candidate_alt_d1_n2_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/010_candidate_alt_d1_n2_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/010_candidate_alt_d1_n2_r2_1_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d4_n11_r1_2_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 11
source_depth = 4
source_event_time = 251.704505
source_selected_pair = [2, 4]
forced_pair = [2, 20]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,8=same_vehicle;4:2,20
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 469
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 32.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/011_candidate_alt_d4_n11_r1_2_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/011_candidate_alt_d4_n11_r1_2_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/011_candidate_alt_d4_n11_r1_2_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/011_candidate_alt_d4_n11_r1_2_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,8=same_vehicle;4:2,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d4_n11_r2_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 11
source_depth = 4
source_event_time = 251.704505
source_selected_pair = [2, 4]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,8=same_vehicle;4:3,5
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 267
source_alt_pool_total_child_width = 464
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 32.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/012_candidate_alt_d4_n11_r2_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/012_candidate_alt_d4_n11_r2_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/012_candidate_alt_d4_n11_r2_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/012_candidate_alt_d4_n11_r2_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=same_vehicle;3:1,8=same_vehicle;4:3,5' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d3_n10_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 229.079565
source_selected_pair = [1, 8]
forced_pair = [1, 11]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,11
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 466
source_alt_pool_total_child_width = 870
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 31.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/013_candidate_alt_d3_n10_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/013_candidate_alt_d3_n10_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/013_candidate_alt_d3_n10_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/013_candidate_alt_d3_n10_r1_1_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 229.079565
source_selected_pair = [1, 8]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 457
source_alt_pool_total_child_width = 814
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 31.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/014_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/014_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/014_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/014_candidate_alt_d3_n10_r2_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:18,19=separate_vehicle;1:1,6=separate_vehicle;2:1,7=separate_vehicle;3:1,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 166.756795
source_selected_pair = [4, 5]
forced_pair = [4, 7]
forced_pair_path_rule = force_pair_path:0:4,9=same_vehicle;1:4,7
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
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
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=0;completion_retries=7;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/015_candidate_alt_d1_n1_r1_4_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=same_vehicle;1:4,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 166.756795
source_selected_pair = [4, 5]
forced_pair = [4, 11]
forced_pair_path_rule = force_pair_path:0:4,9=same_vehicle;1:4,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
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
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=0;completion_retries=7;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/016_candidate_alt_d1_n1_r2_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=same_vehicle;1:4,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d1_n2_r1_8_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 50.298994
source_selected_pair = [5, 13]
forced_pair = [8, 19]
forced_pair_path_rule = force_pair_path:0:7,8=separate_vehicle;1:8,19
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 167
source_alt_pool_total_child_width = 289
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_8_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_8_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_8_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_8_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:7,8=separate_vehicle;1:8,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d1_n2_r2_13_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 50.298994
source_selected_pair = [5, 13]
forced_pair = [13, 19]
forced_pair_path_rule = force_pair_path:0:7,8=separate_vehicle;1:13,19
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 168
source_alt_pool_total_child_width = 274
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_13_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_13_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_13_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_13_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:7,8=separate_vehicle;1:13,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d2_n4_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 177.175561
source_selected_pair = [4, 12]
forced_pair = [4, 13]
forced_pair_path_rule = force_pair_path:0:12,15=same_vehicle;1:1,2=separate_vehicle;2:4,13
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 316
source_alt_pool_total_child_width = 560
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 25.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/019_candidate_alt_d2_n4_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,15=same_vehicle;1:1,2=separate_vehicle;2:4,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d2_n4_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 177.175561
source_selected_pair = [4, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:12,15=same_vehicle;1:1,2=separate_vehicle;2:4,15
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 319
source_alt_pool_total_child_width = 597
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 25.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/020_candidate_alt_d2_n4_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,15=same_vehicle;1:1,2=separate_vehicle;2:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 329.194194
source_selected_pair = [8, 12]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:4,8
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 36
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
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/021_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/021_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/021_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/021_candidate_alt_d2_n6_r1_4_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:4,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 329.194194
source_selected_pair = [8, 12]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:5,8
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 36
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
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/022_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/022_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/022_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/022_candidate_alt_d2_n6_r2_5_8_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,9=separate_vehicle;1:3,8=separate_vehicle;2:5,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d1_n1_r1_1_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 38.473896
source_selected_pair = [1, 10]
forced_pair = [1, 15]
forced_pair_path_rule = force_pair_path:0:7,8=same_vehicle;1:1,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 156
source_alt_pool_total_child_width = 288
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 23.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/023_candidate_alt_d1_n1_r1_1_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/023_candidate_alt_d1_n1_r1_1_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/023_candidate_alt_d1_n1_r1_1_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/023_candidate_alt_d1_n1_r1_1_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:7,8=same_vehicle;1:1,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d1_n1_r2_2_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 38.473896
source_selected_pair = [1, 10]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:7,8=same_vehicle;1:2,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 157
source_alt_pool_total_child_width = 287
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 23.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/024_candidate_alt_d1_n1_r2_2_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/024_candidate_alt_d1_n1_r2_2_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/024_candidate_alt_d1_n1_r2_2_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v598_v597_deep_missing_child_probe_20260628/runs/024_candidate_alt_d1_n1_r2_2_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:7,8=same_vehicle;1:2,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
