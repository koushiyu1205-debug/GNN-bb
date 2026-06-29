# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628
entry_count = 24
candidate_event_count_seen = 566
candidate_event_count_with_replay_entries = 12
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 1
max_source_depth = 4
max_source_event_time = 120.0
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_v573_v545_full60_retrytax_20260628']
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 12
max_events_per_instance = 1
instance_event_limit_skip_count = 2
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json': 1}
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
depth_filter_skip_count = 236
source_event_time_filter_skip_count = 239
branch_impact_priority_context_count = 566
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 81.546842
source_selected_pair = [5, 8]
forced_pair = [8, 15]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:8,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 159
source_alt_pool_total_child_width = 287
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 52.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/001_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/001_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/001_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/001_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:8,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 81.546842
source_selected_pair = [5, 8]
forced_pair = [5, 12]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:5,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 155
source_alt_pool_total_child_width = 284
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 52.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 75.854938
source_selected_pair = [2, 5]
forced_pair = [2, 12]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,12
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 171
source_alt_pool_total_child_width = 304
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/003_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 75.854938
source_selected_pair = [2, 5]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,13
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 169
source_alt_pool_total_child_width = 303
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/004_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 116.680711
source_selected_pair = [2, 3]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 195
source_alt_pool_total_child_width = 324
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/005_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/005_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/005_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/005_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d1_n2_r2_2_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 116.680711
source_selected_pair = [2, 3]
forced_pair = [2, 11]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 205
source_alt_pool_total_child_width = 350
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/006_candidate_alt_d1_n2_r2_2_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/006_candidate_alt_d1_n2_r2_2_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/006_candidate_alt_d1_n2_r2_2_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/006_candidate_alt_d1_n2_r2_2_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d1_n1_r1_1_9_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 72.345599
source_selected_pair = [1, 2]
forced_pair = [1, 9]
forced_pair_path_rule = force_pair_path:0:4,8=same_vehicle;1:1,9
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 217
source_alt_pool_total_child_width = 377
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/007_candidate_alt_d1_n1_r1_1_9_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/007_candidate_alt_d1_n1_r1_1_9_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/007_candidate_alt_d1_n1_r1_1_9_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/007_candidate_alt_d1_n1_r1_1_9_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,8=same_vehicle;1:1,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d1_n1_r2_1_11_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 72.345599
source_selected_pair = [1, 2]
forced_pair = [1, 11]
forced_pair_path_rule = force_pair_path:0:4,8=same_vehicle;1:1,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 221
source_alt_pool_total_child_width = 372
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/008_candidate_alt_d1_n1_r2_1_11_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/008_candidate_alt_d1_n1_r2_1_11_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/008_candidate_alt_d1_n1_r2_1_11_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/008_candidate_alt_d1_n1_r2_1_11_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,8=same_vehicle;1:1,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d1_n1_r1_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 75.531964
source_selected_pair = [6, 14]
forced_pair = [6, 15]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:6,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 250
source_alt_pool_total_child_width = 424
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/009_candidate_alt_d1_n1_r1_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/009_candidate_alt_d1_n1_r1_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/009_candidate_alt_d1_n1_r1_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/009_candidate_alt_d1_n1_r1_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:6,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 75.531964
source_selected_pair = [6, 14]
forced_pair = [7, 14]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:7,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 249
source_alt_pool_total_child_width = 433
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/010_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/010_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/010_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/010_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:7,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d1_n2_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.023305
source_selected_pair = [1, 4]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:6,15=separate_vehicle;1:1,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 376
source_alt_pool_total_child_width = 621
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/011_candidate_alt_d1_n2_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/011_candidate_alt_d1_n2_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/011_candidate_alt_d1_n2_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/011_candidate_alt_d1_n2_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:6,15=separate_vehicle;1:1,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d1_n2_r2_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.023305
source_selected_pair = [1, 4]
forced_pair = [1, 16]
forced_pair_path_rule = force_pair_path:0:6,15=separate_vehicle;1:1,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 367
source_alt_pool_total_child_width = 614
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/012_candidate_alt_d1_n2_r2_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/012_candidate_alt_d1_n2_r2_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/012_candidate_alt_d1_n2_r2_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/012_candidate_alt_d1_n2_r2_1_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:6,15=separate_vehicle;1:1,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d3_n13_r1_4_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 13
source_depth = 3
source_event_time = 98.610829
source_selected_pair = [13, 19]
forced_pair = [4, 13]
forced_pair_path_rule = force_pair_path:0:3,5=separate_vehicle;1:3,9=separate_vehicle;2:4,5=same_vehicle;3:4,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.416666667
source_alt_fractionality = 0.416666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 131
source_alt_pool_total_child_width = 239
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 39.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=4;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/013_candidate_alt_d3_n13_r1_4_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/013_candidate_alt_d3_n13_r1_4_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/013_candidate_alt_d3_n13_r1_4_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/013_candidate_alt_d3_n13_r1_4_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,5=separate_vehicle;1:3,9=separate_vehicle;2:4,5=same_vehicle;3:4,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d3_n13_r2_4_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 13
source_depth = 3
source_event_time = 98.610829
source_selected_pair = [13, 19]
forced_pair = [4, 19]
forced_pair_path_rule = force_pair_path:0:3,5=separate_vehicle;1:3,9=separate_vehicle;2:4,5=same_vehicle;3:4,19
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.416666667
source_alt_fractionality = 0.416666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 131
source_alt_pool_total_child_width = 219
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 39.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=4;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/014_candidate_alt_d3_n13_r2_4_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/014_candidate_alt_d3_n13_r2_4_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/014_candidate_alt_d3_n13_r2_4_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/014_candidate_alt_d3_n13_r2_4_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,5=separate_vehicle;1:3,9=separate_vehicle;2:4,5=same_vehicle;3:4,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d2_n3_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 42.542927
source_selected_pair = [1, 8]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,10
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 144
source_alt_pool_total_child_width = 276
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 37.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=3;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/015_candidate_alt_d2_n3_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/015_candidate_alt_d2_n3_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/015_candidate_alt_d2_n3_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/015_candidate_alt_d2_n3_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d2_n3_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 3
source_depth = 2
source_event_time = 42.542927
source_selected_pair = [1, 8]
forced_pair = [1, 17]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,17
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 145
source_alt_pool_total_child_width = 275
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 37.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=3;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/016_candidate_alt_d2_n3_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/016_candidate_alt_d2_n3_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/016_candidate_alt_d2_n3_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/016_candidate_alt_d2_n3_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 106.963298
source_selected_pair = [4, 12]
forced_pair = [4, 13]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
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
branch_impact_priority = 36.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/017_candidate_alt_d1_n2_r1_4_13_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 106.963298
source_selected_pair = [4, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
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
branch_impact_priority = 36.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/018_candidate_alt_d1_n2_r2_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d1_n1_r1_2_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 49.545665
source_selected_pair = [2, 17]
forced_pair = [2, 18]
forced_pair_path_rule = force_pair_path:0:2,5=same_vehicle;1:2,18
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 329
source_alt_pool_total_child_width = 554
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 36.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=12;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/019_candidate_alt_d1_n1_r1_2_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/019_candidate_alt_d1_n1_r1_2_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/019_candidate_alt_d1_n1_r1_2_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/019_candidate_alt_d1_n1_r1_2_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=same_vehicle;1:2,18' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d1_n1_r2_3_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 49.545665
source_selected_pair = [2, 17]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:2,5=same_vehicle;1:3,17
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 321
source_alt_pool_total_child_width = 531
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 36.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=12;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/020_candidate_alt_d1_n1_r2_3_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/020_candidate_alt_d1_n1_r2_3_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/020_candidate_alt_d1_n1_r2_3_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/020_candidate_alt_d1_n1_r2_3_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=same_vehicle;1:3,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d1_n1_r1_3_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 98.653743
source_selected_pair = [3, 6]
forced_pair = [3, 11]
forced_pair_path_rule = force_pair_path:0:3,10=same_vehicle;1:3,11
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 192
source_alt_pool_total_child_width = 359
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 36.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/021_candidate_alt_d1_n1_r1_3_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/021_candidate_alt_d1_n1_r1_3_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/021_candidate_alt_d1_n1_r1_3_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/021_candidate_alt_d1_n1_r1_3_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,10=same_vehicle;1:3,11' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d1_n1_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 98.653743
source_selected_pair = [3, 6]
forced_pair = [3, 19]
forced_pair_path_rule = force_pair_path:0:3,10=same_vehicle;1:3,19
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 192
source_alt_pool_total_child_width = 370
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 36.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/022_candidate_alt_d1_n1_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/022_candidate_alt_d1_n1_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/022_candidate_alt_d1_n1_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/022_candidate_alt_d1_n1_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,10=same_vehicle;1:3,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d2_n6_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 109.451791
source_selected_pair = [1, 3]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,6
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 12
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 300
source_alt_pool_total_child_width = 537
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 35.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/023_candidate_alt_d2_n6_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/023_candidate_alt_d2_n6_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/023_candidate_alt_d2_n6_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/023_candidate_alt_d2_n6_r1_1_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,6' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d2_n6_r2_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 109.451791
source_selected_pair = [1, 3]
forced_pair = [4, 7]
forced_pair_path_rule = force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:4,7
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 12
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 297
source_alt_pool_total_child_width = 502
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 35.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 240 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/024_candidate_alt_d2_n6_r2_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/024_candidate_alt_d2_n6_r2_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/024_candidate_alt_d2_n6_r2_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/runs/024_candidate_alt_d2_n6_r2_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:4,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=12 --set journey_max_cg_iterations=12 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
