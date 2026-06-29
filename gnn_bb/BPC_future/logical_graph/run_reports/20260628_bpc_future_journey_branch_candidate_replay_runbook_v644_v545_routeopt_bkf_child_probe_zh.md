# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628
entry_count = 72
candidate_event_count_seen = 566
candidate_event_count_with_replay_entries = 24
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = routeopt_bkf
candidate_log_top_n = 200
min_source_depth = None
max_source_depth = 2
max_source_event_time = 180.0
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_v573_v545_full60_retrytax_20260628']
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 5
probe_max_cg_iterations = 36
max_events_per_instance = 1
paired_probe = True
paired_group_count = 24
paired_baseline_entry_count = 24
paired_alternative_entry_count = 48
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 11
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json': 1}
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
depth_filter_skip_count = 371
source_event_time_filter_skip_count = 54
branch_impact_priority_context_count = 566
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d1_n2_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 81.546842
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_5,8
pair_role = selected_baseline
source_selected_pair = [5, 8]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:5,8
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 52.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/001_candidate_selected_d1_n2_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/001_candidate_selected_d1_n2_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/001_candidate_selected_d1_n2_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/001_candidate_selected_d1_n2_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 81.546842
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_5,8
pair_role = alternative
source_selected_pair = [5, 8]
forced_pair = [5, 12]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:5,12
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.488999998
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=155;pool_total_child_width=284;pool_balance_gap=26;incumbent_disagreement=0.666667;rank=2
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 155
source_alt_pool_total_child_width = 284
source_alt_pool_balance_gap = 26
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 52.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/002_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 81.546842
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_5,8
pair_role = alternative
source_selected_pair = [5, 8]
forced_pair = [8, 15]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:8,15
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.481999999
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=159;pool_total_child_width=287;pool_balance_gap=31;incumbent_disagreement=0.666667;rank=1
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 159
source_alt_pool_total_child_width = 287
source_alt_pool_balance_gap = 31
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 52.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/003_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:8,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_selected_d2_n5_2_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 75.854938
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n5__sel_2,5
pair_role = selected_baseline
source_selected_pair = [2, 5]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,5
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/004_candidate_selected_d2_n5_2_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/004_candidate_selected_d2_n5_2_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/004_candidate_selected_d2_n5_2_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/004_candidate_selected_d2_n5_2_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,5' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 75.854938
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n5__sel_2,5
pair_role = alternative
source_selected_pair = [2, 5]
forced_pair = [2, 12]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,12
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.189
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=171;pool_total_child_width=304;pool_balance_gap=38;incumbent_disagreement=0.5;rank=1
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 171
source_alt_pool_total_child_width = 304
source_alt_pool_balance_gap = 38
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/005_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/005_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/005_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/005_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 5
source_depth = 2
source_event_time = 75.854938
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n5__sel_2,5
pair_role = alternative
source_selected_pair = [2, 5]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,13
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.188
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=169;pool_total_child_width=303;pool_balance_gap=35;incumbent_disagreement=0.5;rank=2
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 169
source_alt_pool_total_child_width = 303
source_alt_pool_balance_gap = 35
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/006_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/006_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/006_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/006_candidate_alt_d2_n5_r2_2_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=same_vehicle;2:2,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_selected_d0_n0_8_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 41.872751
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_8,18
pair_role = selected_baseline
source_selected_pair = [8, 18]
forced_pair = [8, 18]
forced_pair_path_rule = force_pair_path:0:8,18
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/007_candidate_selected_d0_n0_8_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/007_candidate_selected_d0_n0_8_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/007_candidate_selected_d0_n0_8_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/007_candidate_selected_d0_n0_8_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r3_17_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 41.872751
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_8,18
pair_role = alternative
source_selected_pair = [8, 18]
forced_pair = [17, 18]
forced_pair_path_rule = force_pair_path:0:17,18
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 3
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.812760298
source_alt_routeopt_bkf_reason = branch_score=0.273904;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=180;pool_total_child_width=308;pool_balance_gap=52;incumbent_disagreement=0.5;rank=3
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 180
source_alt_pool_total_child_width = 308
source_alt_pool_balance_gap = 52
source_alt_branch_score = 0.273904119
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/008_candidate_alt_d0_n0_r3_17_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/008_candidate_alt_d0_n0_r3_17_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/008_candidate_alt_d0_n0_r3_17_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/008_candidate_alt_d0_n0_r3_17_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:17,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 41.872751
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_8,18
pair_role = alternative
source_selected_pair = [8, 18]
forced_pair = [14, 18]
forced_pair_path_rule = force_pair_path:0:14,18
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.295
source_alt_routeopt_bkf_reason = branch_score=0.05;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=177;pool_total_child_width=315;pool_balance_gap=39;incumbent_disagreement=0.5;rank=1
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 177
source_alt_pool_total_child_width = 315
source_alt_pool_balance_gap = 39
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 48.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/009_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/009_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/009_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/009_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:14,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_selected_d0_n0_4_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.467011
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph__d0__n0__sel_4,7
pair_role = selected_baseline
source_selected_pair = [4, 7]
forced_pair = [4, 7]
forced_pair_path_rule = force_pair_path:0:4,7
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/010_candidate_selected_d0_n0_4_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/010_candidate_selected_d0_n0_4_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/010_candidate_selected_d0_n0_4_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/010_candidate_selected_d0_n0_4_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,7 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d0_n0_r4_7_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.467011
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph__d0__n0__sel_4,7
pair_role = alternative
source_selected_pair = [4, 7]
forced_pair = [7, 8]
forced_pair_path_rule = force_pair_path:0:7,8
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 4
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 4.045008763
source_alt_routeopt_bkf_reason = branch_score=0.558804;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=336;pool_total_child_width=618;pool_balance_gap=54;incumbent_disagreement=0.5;rank=4
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 336
source_alt_pool_total_child_width = 618
source_alt_pool_balance_gap = 54
source_alt_branch_score = 0.558803505
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/011_candidate_alt_d0_n0_r4_7_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/011_candidate_alt_d0_n0_r4_7_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/011_candidate_alt_d0_n0_r4_7_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/011_candidate_alt_d0_n0_r4_7_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,8 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d0_n0_r5_7_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.467011
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph__d0__n0__sel_4,7
pair_role = alternative
source_selected_pair = [4, 7]
forced_pair = [7, 10]
forced_pair_path_rule = force_pair_path:0:7,10
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 5
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 4.02744142
source_alt_routeopt_bkf_reason = branch_score=0.556577;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=336;pool_total_child_width=616;pool_balance_gap=56;incumbent_disagreement=0.5;rank=5
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 336
source_alt_pool_total_child_width = 616
source_alt_pool_balance_gap = 56
source_alt_branch_score = 0.556576568
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=11;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/012_candidate_alt_d0_n0_r5_7_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/012_candidate_alt_d0_n0_r5_7_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/012_candidate_alt_d0_n0_r5_7_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/012_candidate_alt_d0_n0_r5_7_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_selected_d1_n1_1_2_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 72.345599
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d1__n1__sel_1,2
pair_role = selected_baseline
source_selected_pair = [1, 2]
forced_pair = [1, 2]
forced_pair_path_rule = force_pair_path:0:4,8=same_vehicle;1:1,2
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/013_candidate_selected_d1_n1_1_2_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/013_candidate_selected_d1_n1_1_2_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/013_candidate_selected_d1_n1_1_2_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/013_candidate_selected_d1_n1_1_2_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,8=same_vehicle;1:1,2' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d1_n1_r12_3_15_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 72.345599
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d1__n1__sel_1,2
pair_role = alternative
source_selected_pair = [1, 2]
forced_pair = [3, 15]
forced_pair_path_rule = force_pair_path:0:4,8=same_vehicle;1:3,15
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 12
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.297
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.4;required_tie_tolerance=0;pool_max_child_width=190;pool_total_child_width=367;pool_balance_gap=13;incumbent_disagreement=0.4;rank=12
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 190
source_alt_pool_total_child_width = 367
source_alt_pool_balance_gap = 13
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/014_candidate_alt_d1_n1_r12_3_15_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/014_candidate_alt_d1_n1_r12_3_15_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/014_candidate_alt_d1_n1_r12_3_15_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/014_candidate_alt_d1_n1_r12_3_15_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,8=same_vehicle;1:3,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d1_n1_r5_2_3_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 72.345599
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d1__n1__sel_1,2
pair_role = alternative
source_selected_pair = [1, 2]
forced_pair = [2, 3]
forced_pair_path_rule = force_pair_path:0:4,8=same_vehicle;1:2,3
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 5
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.284
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.4;required_tie_tolerance=0;pool_max_child_width=203;pool_total_child_width=349;pool_balance_gap=57;incumbent_disagreement=0.4;rank=5
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 203
source_alt_pool_total_child_width = 349
source_alt_pool_balance_gap = 57
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=10;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/015_candidate_alt_d1_n1_r5_2_3_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/015_candidate_alt_d1_n1_r5_2_3_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/015_candidate_alt_d1_n1_r5_2_3_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/015_candidate_alt_d1_n1_r5_2_3_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,8=same_vehicle;1:2,3' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_selected_d0_n0_4_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 134.647366
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_4,7
pair_role = selected_baseline
source_selected_pair = [4, 7]
forced_pair = [4, 7]
forced_pair_path_rule = force_pair_path:0:4,7
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=18;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,7 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 134.647366
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_4,7
pair_role = alternative
source_selected_pair = [4, 7]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:4,15
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 4
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.233599257
source_alt_routeopt_bkf_reason = branch_score=0.52504;fractionality=0.222222;required_tie_tolerance=0;pool_max_child_width=469;pool_total_child_width=806;pool_balance_gap=132;incumbent_disagreement=0.777778;rank=4
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 469
source_alt_pool_total_child_width = 806
source_alt_pool_balance_gap = 132
source_alt_branch_score = 0.525039703
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=18;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/017_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/017_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/017_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/017_candidate_alt_d0_n0_r4_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 134.647366
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_4,7
pair_role = alternative
source_selected_pair = [4, 7]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 9
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.143828012
source_alt_routeopt_bkf_reason = branch_score=0.503131;fractionality=0.222222;required_tie_tolerance=0;pool_max_child_width=468;pool_total_child_width=816;pool_balance_gap=120;incumbent_disagreement=0.777778;rank=9
source_selected_fractionality = 0.222222222
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 468
source_alt_pool_total_child_width = 816
source_alt_pool_balance_gap = 120
source_alt_branch_score = 0.503131205
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=18;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/018_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/018_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/018_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/018_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_selected_d2_n4_6_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 174.083585
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d2__n4__sel_6,10
pair_role = selected_baseline
source_selected_pair = [6, 10]
forced_pair = [6, 10]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:6,14=separate_vehicle;2:6,10
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/019_candidate_selected_d2_n4_6_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/019_candidate_selected_d2_n4_6_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/019_candidate_selected_d2_n4_6_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/019_candidate_selected_d2_n4_6_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:6,14=separate_vehicle;2:6,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d2_n4_r4_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 174.083585
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d2__n4__sel_6,10
pair_role = alternative
source_selected_pair = [6, 10]
forced_pair = [8, 10]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:6,14=separate_vehicle;2:8,10
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 4
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.945
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=235;pool_total_child_width=410;pool_balance_gap=60;incumbent_disagreement=0.5;rank=4
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 235
source_alt_pool_total_child_width = 410
source_alt_pool_balance_gap = 60
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/020_candidate_alt_d2_n4_r4_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/020_candidate_alt_d2_n4_r4_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/020_candidate_alt_d2_n4_r4_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/020_candidate_alt_d2_n4_r4_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:6,14=separate_vehicle;2:8,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d2_n4_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 174.083585
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d2__n4__sel_6,10
pair_role = alternative
source_selected_pair = [6, 10]
forced_pair = [8, 15]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:6,14=separate_vehicle;2:8,15
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 5
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.931
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=237;pool_total_child_width=416;pool_balance_gap=58;incumbent_disagreement=0.5;rank=5
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 237
source_alt_pool_total_child_width = 416
source_alt_pool_balance_gap = 58
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/021_candidate_alt_d2_n4_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/021_candidate_alt_d2_n4_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/021_candidate_alt_d2_n4_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/021_candidate_alt_d2_n4_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:6,14=separate_vehicle;2:8,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_selected_d1_n2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.023305
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph__d1__n2__sel_1,4
pair_role = selected_baseline
source_selected_pair = [1, 4]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:6,15=separate_vehicle;1:1,4
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/022_candidate_selected_d1_n2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/022_candidate_selected_d1_n2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/022_candidate_selected_d1_n2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/022_candidate_selected_d1_n2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:6,15=separate_vehicle;1:1,4' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d1_n2_r7_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.023305
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph__d1__n2__sel_1,4
pair_role = alternative
source_selected_pair = [1, 4]
forced_pair = [4, 9]
forced_pair_path_rule = force_pair_path:0:6,15=separate_vehicle;1:4,9
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 7
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.517
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=367;pool_total_child_width=672;pool_balance_gap=62;incumbent_disagreement=0.5;rank=7
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 367
source_alt_pool_total_child_width = 672
source_alt_pool_balance_gap = 62
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/023_candidate_alt_d1_n2_r7_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/023_candidate_alt_d1_n2_r7_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/023_candidate_alt_d1_n2_r7_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/023_candidate_alt_d1_n2_r7_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:6,15=separate_vehicle;1:4,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d1_n2_r5_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 117.023305
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph__d1__n2__sel_1,4
pair_role = alternative
source_selected_pair = [1, 4]
forced_pair = [4, 5]
forced_pair_path_rule = force_pair_path:0:6,15=separate_vehicle;1:4,5
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 5
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.51
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=367;pool_total_child_width=645;pool_balance_gap=89;incumbent_disagreement=0.5;rank=5
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 367
source_alt_pool_total_child_width = 645
source_alt_pool_balance_gap = 89
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/024_candidate_alt_d1_n2_r5_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/024_candidate_alt_d1_n2_r5_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/024_candidate_alt_d1_n2_r5_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/024_candidate_alt_d1_n2_r5_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:6,15=separate_vehicle;1:4,5' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 025_candidate_selected_d0_n0_12_20_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 107.133573
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_12,20
pair_role = selected_baseline
source_selected_pair = [12, 20]
forced_pair = [12, 20]
forced_pair_path_rule = force_pair_path:0:12,20
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=16;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/025_candidate_selected_d0_n0_12_20_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/025_candidate_selected_d0_n0_12_20_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/025_candidate_selected_d0_n0_12_20_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/025_candidate_selected_d0_n0_12_20_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 026_candidate_alt_d0_n0_r4_6_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 107.133573
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_12,20
pair_role = alternative
source_selected_pair = [12, 20]
forced_pair = [6, 9]
forced_pair_path_rule = force_pair_path:0:6,9
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 4
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.878226549
source_alt_routeopt_bkf_reason = branch_score=0.290491;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=253;pool_total_child_width=457;pool_balance_gap=49;incumbent_disagreement=0.666667;rank=4
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 253
source_alt_pool_total_child_width = 457
source_alt_pool_balance_gap = 49
source_alt_branch_score = 0.29049062
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=16;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/026_candidate_alt_d0_n0_r4_6_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/026_candidate_alt_d0_n0_r4_6_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/026_candidate_alt_d0_n0_r4_6_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/026_candidate_alt_d0_n0_r4_6_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,9 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 027_candidate_alt_d0_n0_r8_11_12_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 107.133573
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_12,20
pair_role = alternative
source_selected_pair = [12, 20]
forced_pair = [11, 12]
forced_pair_path_rule = force_pair_path:0:11,12
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 8
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.856526806
source_alt_routeopt_bkf_reason = branch_score=0.301411;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=254;pool_total_child_width=453;pool_balance_gap=55;incumbent_disagreement=0.666667;rank=8
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 254
source_alt_pool_total_child_width = 453
source_alt_pool_balance_gap = 55
source_alt_branch_score = 0.301410723
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=16;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/027_candidate_alt_d0_n0_r8_11_12_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/027_candidate_alt_d0_n0_r8_11_12_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/027_candidate_alt_d0_n0_r8_11_12_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/027_candidate_alt_d0_n0_r8_11_12_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:11,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 028_candidate_selected_d0_n0_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 57.840267
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph__d0__n0__sel_4,12
pair_role = selected_baseline
source_selected_pair = [4, 12]
forced_pair = [4, 12]
forced_pair_path_rule = force_pair_path:0:4,12
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.466666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=14;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/028_candidate_selected_d0_n0_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/028_candidate_selected_d0_n0_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/028_candidate_selected_d0_n0_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/028_candidate_selected_d0_n0_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 029_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 57.840267
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph__d0__n0__sel_4,12
pair_role = alternative
source_selected_pair = [4, 12]
forced_pair = [5, 14]
forced_pair_path_rule = force_pair_path:0:5,14
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.301556559
source_alt_routeopt_bkf_reason = branch_score=0.262623;fractionality=0.466667;required_tie_tolerance=0;pool_max_child_width=289;pool_total_child_width=510;pool_balance_gap=68;incumbent_disagreement=0.533333;rank=2
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.466666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 289
source_alt_pool_total_child_width = 510
source_alt_pool_balance_gap = 68
source_alt_branch_score = 0.262622623
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=14;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/029_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/029_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/029_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/029_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 030_candidate_alt_d0_n0_r3_6_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 57.840267
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph__d0__n0__sel_4,12
pair_role = alternative
source_selected_pair = [4, 12]
forced_pair = [6, 15]
forced_pair_path_rule = force_pair_path:0:6,15
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 36
source_alt_rank = 3
source_alt_selection_reason = routeopt_bkf_test_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.254774349
source_alt_routeopt_bkf_reason = branch_score=0.23791;fractionality=0.466667;required_tie_tolerance=0;pool_max_child_width=286;pool_total_child_width=520;pool_balance_gap=52;incumbent_disagreement=0.533333;rank=3
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.466666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 286
source_alt_pool_total_child_width = 520
source_alt_pool_balance_gap = 52
source_alt_branch_score = 0.237909739
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=14;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/030_candidate_alt_d0_n0_r3_6_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/030_candidate_alt_d0_n0_r3_6_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/030_candidate_alt_d0_n0_r3_6_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/runs/030_candidate_alt_d0_n0_r3_6_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

- Report truncated to first 30 entries; full runbook has 72 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
