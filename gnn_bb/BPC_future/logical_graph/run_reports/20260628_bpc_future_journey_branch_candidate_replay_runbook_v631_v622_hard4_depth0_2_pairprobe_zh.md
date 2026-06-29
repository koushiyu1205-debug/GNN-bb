# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628
entry_count = 24
candidate_event_count_seen = 162
candidate_event_count_with_replay_entries = 8
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 0
max_source_depth = 2
max_source_event_time = None
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_v630_v622_retry_on_hard4_20260628']
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 5
probe_max_cg_iterations = 36
max_events_per_instance = 2
paired_probe = True
paired_group_count = 8
paired_baseline_entry_count = 8
paired_alternative_entry_count = 16
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 10
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json': 2, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 2, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json': 2, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 2}
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
depth_filter_skip_count = 136
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 162
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d0_n0_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 30.470654
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_15,18
pair_role = selected_baseline
source_selected_pair = [15, 18]
forced_pair = [15, 18]
forced_pair_path_rule = force_pair_path:0:15,18
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/001_candidate_selected_d0_n0_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/001_candidate_selected_d0_n0_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/001_candidate_selected_d0_n0_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/001_candidate_selected_d0_n0_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r6_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 30.470654
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_15,18
pair_role = alternative
source_selected_pair = [15, 18]
forced_pair = [13, 20]
forced_pair_path_rule = force_pair_path:0:13,20
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 6
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 337
source_alt_pool_total_child_width = 615
source_alt_branch_score = 0.889209121
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/002_candidate_alt_d0_n0_r6_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/002_candidate_alt_d0_n0_r6_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/002_candidate_alt_d0_n0_r6_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/002_candidate_alt_d0_n0_r6_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:13,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r9_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 30.470654
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_15,18
pair_role = alternative
source_selected_pair = [15, 18]
forced_pair = [12, 20]
forced_pair_path_rule = force_pair_path:0:12,20
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 9
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 333
source_alt_pool_total_child_width = 620
source_alt_branch_score = 0.888904798
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/003_candidate_alt_d0_n0_r9_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/003_candidate_alt_d0_n0_r9_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/003_candidate_alt_d0_n0_r9_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/003_candidate_alt_d0_n0_r9_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_selected_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 87.755804
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__sel_11,18
pair_role = selected_baseline
source_selected_pair = [11, 18]
forced_pair = [11, 18]
forced_pair_path_rule = force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:11,18
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/004_candidate_selected_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/004_candidate_selected_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/004_candidate_selected_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/004_candidate_selected_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:11,18' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d2_n6_r1_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 87.755804
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__sel_11,18
pair_role = alternative
source_selected_pair = [11, 18]
forced_pair = [12, 20]
forced_pair_path_rule = force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:12,20
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 362
source_alt_pool_total_child_width = 666
source_alt_branch_score = 0.890110952
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/005_candidate_alt_d2_n6_r1_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/005_candidate_alt_d2_n6_r1_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/005_candidate_alt_d2_n6_r1_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/005_candidate_alt_d2_n6_r1_12_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:12,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d2_n6_r2_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 87.755804
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__sel_11,18
pair_role = alternative
source_selected_pair = [11, 18]
forced_pair = [11, 17]
forced_pair_path_rule = force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:11,17
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 362
source_alt_pool_total_child_width = 666
source_alt_branch_score = 0.89002319
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 28.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/006_candidate_alt_d2_n6_r2_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/006_candidate_alt_d2_n6_r2_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/006_candidate_alt_d2_n6_r2_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/006_candidate_alt_d2_n6_r2_11_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:11,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_selected_d0_n0_17_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.634197
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d0__n0__sel_17,20
pair_role = selected_baseline
source_selected_pair = [17, 20]
forced_pair = [17, 20]
forced_pair_path_rule = force_pair_path:0:17,20
probe_mode = child_probe
probe_max_nodes = 6
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
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/007_candidate_selected_d0_n0_17_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/007_candidate_selected_d0_n0_17_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/007_candidate_selected_d0_n0_17_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/007_candidate_selected_d0_n0_17_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:17,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.634197
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d0__n0__sel_17,20
pair_role = alternative
source_selected_pair = [17, 20]
forced_pair = [16, 20]
forced_pair_path_rule = force_pair_path:0:16,20
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
source_alt_pool_max_child_width = 312
source_alt_pool_total_child_width = 551
source_alt_branch_score = 0.887637186
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/008_candidate_alt_d0_n0_r1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/008_candidate_alt_d0_n0_r1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/008_candidate_alt_d0_n0_r1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/008_candidate_alt_d0_n0_r1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:16,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 25.634197
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d0__n0__sel_17,20
pair_role = alternative
source_selected_pair = [17, 20]
forced_pair = [16, 17]
forced_pair_path_rule = force_pair_path:0:16,17
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
source_alt_pool_max_child_width = 312
source_alt_pool_total_child_width = 579
source_alt_branch_score = 0.887597883
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/009_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/009_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/009_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/009_candidate_alt_d0_n0_r2_16_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:16,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_selected_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 34.687337
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_16,20
pair_role = selected_baseline
source_selected_pair = [16, 20]
forced_pair = [16, 20]
forced_pair_path_rule = force_pair_path:0:17,20=same_vehicle;1:16,20
probe_mode = child_probe
probe_max_nodes = 7
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
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/010_candidate_selected_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/010_candidate_selected_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/010_candidate_selected_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/010_candidate_selected_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:17,20=same_vehicle;1:16,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d1_n1_r1_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 34.687337
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_16,20
pair_role = alternative
source_selected_pair = [16, 20]
forced_pair = [15, 17]
forced_pair_path_rule = force_pair_path:0:17,20=same_vehicle;1:15,17
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
source_alt_pool_max_child_width = 245
source_alt_pool_total_child_width = 445
source_alt_branch_score = 0.879745162
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/011_candidate_alt_d1_n1_r1_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/011_candidate_alt_d1_n1_r1_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/011_candidate_alt_d1_n1_r1_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/011_candidate_alt_d1_n1_r1_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:17,20=same_vehicle;1:15,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d1_n1_r2_14_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 34.687337
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_16,20
pair_role = alternative
source_selected_pair = [16, 20]
forced_pair = [14, 19]
forced_pair_path_rule = force_pair_path:0:17,20=same_vehicle;1:14,19
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
source_alt_pool_max_child_width = 242
source_alt_pool_total_child_width = 415
source_alt_branch_score = 0.879677624
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/012_candidate_alt_d1_n1_r2_14_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/012_candidate_alt_d1_n1_r2_14_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/012_candidate_alt_d1_n1_r2_14_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/012_candidate_alt_d1_n1_r2_14_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:17,20=same_vehicle;1:14,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_selected_d2_n3_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 35.311459
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n3__sel_4,7
pair_role = selected_baseline
source_selected_pair = [4, 7]
forced_pair = [4, 7]
forced_pair_path_rule = force_pair_path:0:14,19=same_vehicle;1:8,20=same_vehicle;2:4,7
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
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/013_candidate_selected_d2_n3_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/013_candidate_selected_d2_n3_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/013_candidate_selected_d2_n3_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/013_candidate_selected_d2_n3_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:14,19=same_vehicle;1:8,20=same_vehicle;2:4,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d2_n3_r1_4_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 35.311459
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n3__sel_4,7
pair_role = alternative
source_selected_pair = [4, 7]
forced_pair = [4, 11]
forced_pair_path_rule = force_pair_path:0:14,19=same_vehicle;1:8,20=same_vehicle;2:4,11
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
source_alt_pool_max_child_width = 99
source_alt_pool_total_child_width = 179
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/014_candidate_alt_d2_n3_r1_4_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/014_candidate_alt_d2_n3_r1_4_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/014_candidate_alt_d2_n3_r1_4_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/014_candidate_alt_d2_n3_r1_4_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:14,19=same_vehicle;1:8,20=same_vehicle;2:4,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d2_n3_r2_4_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 35.311459
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n3__sel_4,7
pair_role = alternative
source_selected_pair = [4, 7]
forced_pair = [4, 12]
forced_pair_path_rule = force_pair_path:0:14,19=same_vehicle;1:8,20=same_vehicle;2:4,12
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
source_alt_pool_max_child_width = 96
source_alt_pool_total_child_width = 178
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/015_candidate_alt_d2_n3_r2_4_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/015_candidate_alt_d2_n3_r2_4_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/015_candidate_alt_d2_n3_r2_4_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/015_candidate_alt_d2_n3_r2_4_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:14,19=same_vehicle;1:8,20=same_vehicle;2:4,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_selected_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 58.241923
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n6__sel_11,20
pair_role = selected_baseline
source_selected_pair = [11, 20]
forced_pair = [11, 20]
forced_pair_path_rule = force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:11,20
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/016_candidate_selected_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/016_candidate_selected_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/016_candidate_selected_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/016_candidate_selected_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:11,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d2_n6_r1_7_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 58.241923
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n6__sel_11,20
pair_role = alternative
source_selected_pair = [11, 20]
forced_pair = [7, 15]
forced_pair_path_rule = force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:7,15
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 167
source_alt_pool_total_child_width = 307
source_alt_branch_score = 0.875338829
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/017_candidate_alt_d2_n6_r1_7_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/017_candidate_alt_d2_n6_r1_7_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/017_candidate_alt_d2_n6_r1_7_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/017_candidate_alt_d2_n6_r1_7_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:7,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d2_n6_r2_4_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 58.241923
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d2__n6__sel_11,20
pair_role = alternative
source_selected_pair = [11, 20]
forced_pair = [4, 20]
forced_pair_path_rule = force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:4,20
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 165
source_alt_pool_total_child_width = 300
source_alt_branch_score = 0.875094426
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 20.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=5;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/018_candidate_alt_d2_n6_r2_4_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/018_candidate_alt_d2_n6_r2_4_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/018_candidate_alt_d2_n6_r2_4_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/018_candidate_alt_d2_n6_r2_4_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:4,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_selected_d0_n0_11_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 12.964151
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_11,17
pair_role = selected_baseline
source_selected_pair = [11, 17]
forced_pair = [11, 17]
forced_pair_path_rule = force_pair_path:0:11,17
probe_mode = child_probe
probe_max_nodes = 6
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
branch_impact_priority = 18.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/019_candidate_selected_d0_n0_11_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/019_candidate_selected_d0_n0_11_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/019_candidate_selected_d0_n0_11_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/019_candidate_selected_d0_n0_11_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:11,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d0_n0_r1_10_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 12.964151
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_11,17
pair_role = alternative
source_selected_pair = [11, 17]
forced_pair = [10, 20]
forced_pair_path_rule = force_pair_path:0:10,20
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
source_alt_pool_max_child_width = 252
source_alt_pool_total_child_width = 442
source_alt_branch_score = 0.878823572
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 18.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/020_candidate_alt_d0_n0_r1_10_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/020_candidate_alt_d0_n0_r1_10_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/020_candidate_alt_d0_n0_r1_10_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/020_candidate_alt_d0_n0_r1_10_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d0_n0_r2_6_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 12.964151
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_11,17
pair_role = alternative
source_selected_pair = [11, 17]
forced_pair = [6, 20]
forced_pair_path_rule = force_pair_path:0:6,20
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
source_alt_pool_max_child_width = 254
source_alt_pool_total_child_width = 472
source_alt_branch_score = 0.878742069
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 18.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/021_candidate_alt_d0_n0_r2_6_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/021_candidate_alt_d0_n0_r2_6_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/021_candidate_alt_d0_n0_r2_6_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/021_candidate_alt_d0_n0_r2_6_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_selected_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 73.14304
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d2__n6__sel_14,16
pair_role = selected_baseline
source_selected_pair = [14, 16]
forced_pair = [14, 16]
forced_pair_path_rule = force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:14,16
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
branch_impact_priority = 17.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=2;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/022_candidate_selected_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/022_candidate_selected_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/022_candidate_selected_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/022_candidate_selected_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:14,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d2_n6_r1_12_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 73.14304
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d2__n6__sel_14,16
pair_role = alternative
source_selected_pair = [14, 16]
forced_pair = [12, 14]
forced_pair_path_rule = force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:12,14
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
source_alt_pool_max_child_width = 259
source_alt_pool_total_child_width = 441
source_alt_branch_score = 0.880851537
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 17.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=2;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/023_candidate_alt_d2_n6_r1_12_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/023_candidate_alt_d2_n6_r1_12_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/023_candidate_alt_d2_n6_r1_12_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/023_candidate_alt_d2_n6_r1_12_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:12,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d2_n6_r2_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 73.14304
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d2__n6__sel_14,16
pair_role = alternative
source_selected_pair = [14, 16]
forced_pair = [8, 14]
forced_pair_path_rule = force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:8,14
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
source_alt_pool_max_child_width = 263
source_alt_pool_total_child_width = 441
source_alt_branch_score = 0.880798233
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 17.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=2;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/024_candidate_alt_d2_n6_r2_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/024_candidate_alt_d2_n6_r2_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/024_candidate_alt_d2_n6_r2_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/runs/024_candidate_alt_d2_n6_r2_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:8,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
