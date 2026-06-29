# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628
entry_count = 16
candidate_event_count_seen = 28
candidate_event_count_with_replay_entries = 4
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 3
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 1
max_source_depth = 2
max_source_event_time = 100.0
branch_impact_input_paths = []
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 6
probe_max_cg_iterations = 36
max_events_per_instance = 4
paired_probe = True
paired_group_count = 4
paired_baseline_entry_count = 4
paired_alternative_entry_count = 12
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 0
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json': 4}
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
depth_filter_skip_count = 22
source_event_time_filter_skip_count = 2
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d1_n1_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 43.798483
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_1,3
pair_role = selected_baseline
source_selected_pair = [1, 3]
forced_pair = [1, 3]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n1_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 43.798483
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,6
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 271
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,6' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d1_n1_r2_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 43.798483
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,10
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 271
source_alt_pool_total_child_width = 468
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d1_n1_r7_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 43.798483
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:3,10
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 7
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 259
source_alt_pool_total_child_width = 432
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/004_candidate_alt_d1_n1_r7_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/004_candidate_alt_d1_n1_r7_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/004_candidate_alt_d1_n1_r7_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/004_candidate_alt_d1_n1_r7_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:3,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_selected_d1_n2_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 65.212631
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_1,3
pair_role = selected_baseline
source_selected_pair = [1, 3]
forced_pair = [1, 3]
forced_pair_path_rule = force_pair_path:0:16,17=separate_vehicle;1:1,3
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/005_candidate_selected_d1_n2_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/005_candidate_selected_d1_n2_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/005_candidate_selected_d1_n2_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/005_candidate_selected_d1_n2_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=separate_vehicle;1:1,3' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d1_n2_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 65.212631
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:16,17=separate_vehicle;1:1,6
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 331
source_alt_pool_total_child_width = 627
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d1_n2_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d1_n2_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d1_n2_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d1_n2_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=separate_vehicle;1:1,6' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d1_n2_r2_1_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 65.212631
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [1, 15]
forced_pair_path_rule = force_pair_path:0:16,17=separate_vehicle;1:1,15
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 332
source_alt_pool_total_child_width = 591
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/007_candidate_alt_d1_n2_r2_1_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/007_candidate_alt_d1_n2_r2_1_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/007_candidate_alt_d1_n2_r2_1_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/007_candidate_alt_d1_n2_r2_1_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=separate_vehicle;1:1,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d1_n2_r5_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 65.212631
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:16,17=separate_vehicle;1:3,10
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 5
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 316
source_alt_pool_total_child_width = 528
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n2_r5_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n2_r5_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n2_r5_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n2_r5_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=separate_vehicle;1:3,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_selected_d2_n3_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 75.891434
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n3__sel_1,10
pair_role = selected_baseline
source_selected_pair = [1, 10]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:1,10
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/009_candidate_selected_d2_n3_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/009_candidate_selected_d2_n3_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/009_candidate_selected_d2_n3_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/009_candidate_selected_d2_n3_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:1,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d2_n3_r1_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 75.891434
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n3__sel_1,10
pair_role = alternative
source_selected_pair = [1, 10]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:3,10
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 207
source_alt_pool_total_child_width = 361
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/010_candidate_alt_d2_n3_r1_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/010_candidate_alt_d2_n3_r1_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/010_candidate_alt_d2_n3_r1_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/010_candidate_alt_d2_n3_r1_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:3,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d2_n3_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 75.891434
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n3__sel_1,10
pair_role = alternative
source_selected_pair = [1, 10]
forced_pair = [4, 9]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:4,9
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 205
source_alt_pool_total_child_width = 351
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d2_n3_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d2_n3_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d2_n3_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d2_n3_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:4,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d2_n3_r18_10_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 75.891434
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n3__sel_1,10
pair_role = alternative
source_selected_pair = [1, 10]
forced_pair = [10, 15]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:10,15
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = 18
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 199
source_alt_pool_total_child_width = 330
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d2_n3_r18_10_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d2_n3_r18_10_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d2_n3_r18_10_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d2_n3_r18_10_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=same_vehicle;2:10,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_selected_d2_n4_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 90.43681
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n4__sel_1,13
pair_role = selected_baseline
source_selected_pair = [1, 13]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:1,13
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/013_candidate_selected_d2_n4_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/013_candidate_selected_d2_n4_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/013_candidate_selected_d2_n4_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/013_candidate_selected_d2_n4_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:1,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d2_n4_r1_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 90.43681
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n4__sel_1,13
pair_role = alternative
source_selected_pair = [1, 13]
forced_pair = [1, 19]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:1,19
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 277
source_alt_pool_total_child_width = 479
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/014_candidate_alt_d2_n4_r1_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/014_candidate_alt_d2_n4_r1_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/014_candidate_alt_d2_n4_r1_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/014_candidate_alt_d2_n4_r1_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:1,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d2_n4_r2_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 90.43681
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n4__sel_1,13
pair_role = alternative
source_selected_pair = [1, 13]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:5,8
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 269
source_alt_pool_total_child_width = 500
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/015_candidate_alt_d2_n4_r2_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/015_candidate_alt_d2_n4_r2_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/015_candidate_alt_d2_n4_r2_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/015_candidate_alt_d2_n4_r2_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:5,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d2_n4_r16_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 90.43681
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n4__sel_1,13
pair_role = alternative
source_selected_pair = [1, 13]
forced_pair = [13, 19]
forced_pair_path_rule = force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:13,19
probe_mode = child_probe
probe_max_nodes = 9
probe_max_cg_iterations = 36
source_alt_rank = 16
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 453
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/016_candidate_alt_d2_n4_r16_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/016_candidate_alt_d2_n4_r16_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/016_candidate_alt_d2_n4_r16_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/runs/016_candidate_alt_d2_n4_r16_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:16,17=same_vehicle;1:1,3=separate_vehicle;2:13,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=9 --set journey_max_nodes=9 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
