# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628
entry_count = 36
candidate_event_count_seen = 566
candidate_event_count_with_replay_entries = 12
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = routeopt_bkf_staged
staged_bkf_min_alternatives = 1
staged_bkf_max_alternatives = 2
staged_bkf_score_gap = 0.75
staged_bkf_max_pool_child_width = 900.0
staged_bkf_max_pool_total_child_width = 1800.0
staged_bkf_max_pool_balance_gap = 500.0
staged_bkf_require_score = False
candidate_log_top_n = 200
min_source_depth = None
max_source_depth = None
max_source_event_time = None
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v549_v545_full60_20260627/summary.json']
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628', 'BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628', 'BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628', 'BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628']
focus_delta_input_paths = []
coverage_input_paths = []
branch_score_input_paths = ['BPC_future/results/gat_branch_action_proofrisk_overlay_v667_v543_plus_v666_paired_probe_20260628']
external_branch_score_context_count = 20723
external_branch_score_event_count = 538
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 60
max_events_per_instance = 1
paired_probe = True
paired_group_count = 12
paired_baseline_entry_count = 12
paired_alternative_entry_count = 24
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 5
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json': 1}
excluded_entry_key_count = 136
excluded_entry_skip_count = 27
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 0
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 566
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d1_n2_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 283.698615
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph__d1__n2__sel_1,4
pair_role = selected_baseline
source_selected_pair = [1, 4]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:1,4
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 3.2479656707129857e-21
external_branch_score_event_pair = [18, 19]
external_branch_score_event_predicted_walltime_gain = 1.3781219720840454
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
branch_impact_priority = 55.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=20;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/001_candidate_selected_d1_n2_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/001_candidate_selected_d1_n2_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/001_candidate_selected_d1_n2_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/001_candidate_selected_d1_n2_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:1,4' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n2_r1_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 283.698615
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph__d1__n2__sel_1,4
pair_role = alternative
source_selected_pair = [1, 4]
forced_pair = [1, 8]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:1,8
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.549
source_alt_routeopt_bkf_reason = branch_score=5.32545e-22;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=383;pool_total_child_width=724;pool_balance_gap=42;incumbent_disagreement=0.5;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 3.2479656707129857e-21
external_branch_score_event_pair = [18, 19]
external_branch_score_event_predicted_walltime_gain = 1.3781219720840454
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 383
source_alt_pool_total_child_width = 724
source_alt_pool_balance_gap = 42
source_alt_branch_score = 5.325448762288738e-22
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 55.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=20;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/002_candidate_alt_d1_n2_r1_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/002_candidate_alt_d1_n2_r1_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/002_candidate_alt_d1_n2_r1_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/002_candidate_alt_d1_n2_r1_1_8_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:1,8' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d1_n2_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 283.698615
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph__d1__n2__sel_1,4
pair_role = alternative
source_selected_pair = [1, 4]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:1,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.547
source_alt_routeopt_bkf_reason = branch_score=6.33739e-22;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=378;pool_total_child_width=707;pool_balance_gap=49;incumbent_disagreement=0.5;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 3.2479656707129857e-21
external_branch_score_event_pair = [18, 19]
external_branch_score_event_predicted_walltime_gain = 1.3781219720840454
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 378
source_alt_pool_total_child_width = 707
source_alt_pool_balance_gap = 49
source_alt_branch_score = 6.33738589998981e-22
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 55.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=20;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/003_candidate_alt_d1_n2_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/003_candidate_alt_d1_n2_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/003_candidate_alt_d1_n2_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/003_candidate_alt_d1_n2_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:1,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_selected_d2_n4_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 347.087241
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph__d2__n4__sel_1,3
pair_role = selected_baseline
source_selected_pair = [1, 3]
forced_pair = [1, 3]
forced_pair_path_rule = force_pair_path:0:1,4=separate_vehicle;1:1,20=separate_vehicle;2:1,3
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 1.5839367093353634e-26
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.4126696586608887
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
branch_impact_priority = 54.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/004_candidate_selected_d2_n4_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/004_candidate_selected_d2_n4_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/004_candidate_selected_d2_n4_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/004_candidate_selected_d2_n4_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,4=separate_vehicle;1:1,20=separate_vehicle;2:1,3' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d2_n4_r3_2_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 347.087241
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph__d2__n4__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [2, 3]
forced_pair_path_rule = force_pair_path:0:1,4=separate_vehicle;1:1,20=separate_vehicle;2:2,3
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = 3
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 1.815
source_alt_routeopt_bkf_reason = branch_score=1.14946e-27;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=597;pool_total_child_width=1080;pool_balance_gap=114;incumbent_disagreement=0.5;rank=3
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 1.5839367093353634e-26
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.4126696586608887
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 597
source_alt_pool_total_child_width = 1080
source_alt_pool_balance_gap = 114
source_alt_branch_score = 1.1494590279809532e-27
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 54.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/005_candidate_alt_d2_n4_r3_2_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/005_candidate_alt_d2_n4_r3_2_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/005_candidate_alt_d2_n4_r3_2_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/005_candidate_alt_d2_n4_r3_2_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,4=separate_vehicle;1:1,20=separate_vehicle;2:2,3' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d2_n4_r6_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 347.087241
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph__d2__n4__sel_1,3
pair_role = alternative
source_selected_pair = [1, 3]
forced_pair = [3, 4]
forced_pair_path_rule = force_pair_path:0:1,4=separate_vehicle;1:1,20=separate_vehicle;2:3,4
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = 6
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 1.812
source_alt_routeopt_bkf_reason = branch_score=1.34356e-27;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=585;pool_total_child_width=1047;pool_balance_gap=123;incumbent_disagreement=0.5;rank=6
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 1.5839367093353634e-26
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.4126696586608887
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 585
source_alt_pool_total_child_width = 1047
source_alt_pool_balance_gap = 123
source_alt_branch_score = 1.3435615663100875e-27
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 54.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/006_candidate_alt_d2_n4_r6_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/006_candidate_alt_d2_n4_r6_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/006_candidate_alt_d2_n4_r6_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/006_candidate_alt_d2_n4_r6_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,4=separate_vehicle;1:1,20=separate_vehicle;2:3,4' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_selected_d2_n4_3_5_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 414.097311
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d2__n4__sel_3,5
pair_role = selected_baseline
source_selected_pair = [3, 5]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:1,15=separate_vehicle;2:3,5
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 5.42588302975152e-31
external_branch_score_event_pair = [15, 19]
external_branch_score_event_predicted_walltime_gain = 2.116239070892334
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
branch_impact_priority = 47.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=12;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/007_candidate_selected_d2_n4_3_5_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/007_candidate_selected_d2_n4_3_5_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/007_candidate_selected_d2_n4_3_5_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/007_candidate_selected_d2_n4_3_5_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:1,15=separate_vehicle;2:3,5' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d2_n4_r6_5_9_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 414.097311
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d2__n4__sel_3,5
pair_role = alternative
source_selected_pair = [3, 5]
forced_pair = [5, 9]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:1,15=separate_vehicle;2:5,9
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = 6
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 1.625999998
source_alt_routeopt_bkf_reason = branch_score=1.30187e-31;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=410;pool_total_child_width=736;pool_balance_gap=84;incumbent_disagreement=0.666667;rank=6
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 5.42588302975152e-31
external_branch_score_event_pair = [15, 19]
external_branch_score_event_predicted_walltime_gain = 2.116239070892334
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 410
source_alt_pool_total_child_width = 736
source_alt_pool_balance_gap = 84
source_alt_branch_score = 1.3018740994678933e-31
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 47.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=12;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/008_candidate_alt_d2_n4_r6_5_9_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/008_candidate_alt_d2_n4_r6_5_9_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/008_candidate_alt_d2_n4_r6_5_9_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/008_candidate_alt_d2_n4_r6_5_9_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:1,15=separate_vehicle;2:5,9' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d2_n4_r7_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 414.097311
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d2__n4__sel_3,5
pair_role = alternative
source_selected_pair = [3, 5]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:4,7=same_vehicle;1:1,15=separate_vehicle;2:5,13
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = 7
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 1.624999999
source_alt_routeopt_bkf_reason = branch_score=1.76707e-31;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=404;pool_total_child_width=715;pool_balance_gap=93;incumbent_disagreement=0.666667;rank=7
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 5.42588302975152e-31
external_branch_score_event_pair = [15, 19]
external_branch_score_event_predicted_walltime_gain = 2.116239070892334
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 404
source_alt_pool_total_child_width = 715
source_alt_pool_balance_gap = 93
source_alt_branch_score = 1.7670719921250208e-31
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 47.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=12;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/009_candidate_alt_d2_n4_r7_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/009_candidate_alt_d2_n4_r7_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/009_candidate_alt_d2_n4_r7_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/009_candidate_alt_d2_n4_r7_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:4,7=same_vehicle;1:1,15=separate_vehicle;2:5,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_selected_d2_n6_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 86.593093
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__sel_3,5
pair_role = selected_baseline
source_selected_pair = [3, 5]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=separate_vehicle;2:3,5
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 2.2647662945018965e-07
external_branch_score_event_pair = [13, 20]
external_branch_score_event_predicted_walltime_gain = -0.021945282816886902
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
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=21;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/010_candidate_selected_d2_n6_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/010_candidate_selected_d2_n6_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/010_candidate_selected_d2_n6_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/010_candidate_selected_d2_n6_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=separate_vehicle;2:3,5' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d2_n6_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 86.593093
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__sel_3,5
pair_role = alternative
source_selected_pair = [3, 5]
forced_pair = [3, 12]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=separate_vehicle;2:3,12
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.77600017
source_alt_routeopt_bkf_reason = branch_score=6.79124e-08;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=309;pool_total_child_width=581;pool_balance_gap=37;incumbent_disagreement=0.5;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 2.2647662945018965e-07
external_branch_score_event_pair = [13, 20]
external_branch_score_event_predicted_walltime_gain = -0.021945282816886902
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 309
source_alt_pool_total_child_width = 581
source_alt_pool_balance_gap = 37
source_alt_branch_score = 6.791241702330808e-08
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=21;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/011_candidate_alt_d2_n6_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/011_candidate_alt_d2_n6_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/011_candidate_alt_d2_n6_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/011_candidate_alt_d2_n6_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=separate_vehicle;2:3,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d2_n6_r2_3_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 6
source_depth = 2
source_event_time = 86.593093
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n6__sel_3,5
pair_role = alternative
source_selected_pair = [3, 5]
forced_pair = [3, 13]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:2,10=separate_vehicle;2:3,13
probe_mode = child_probe
probe_max_nodes = 5
probe_max_cg_iterations = 60
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.760000193
source_alt_routeopt_bkf_reason = branch_score=7.71645e-08;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=310;pool_total_child_width=580;pool_balance_gap=40;incumbent_disagreement=0.5;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 2.2647662945018965e-07
external_branch_score_event_pair = [13, 20]
external_branch_score_event_predicted_walltime_gain = -0.021945282816886902
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 310
source_alt_pool_total_child_width = 580
source_alt_pool_balance_gap = 40
source_alt_branch_score = 7.71644508290592e-08
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=0;completion_retries=11;negative_events=21;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/012_candidate_alt_d2_n6_r2_3_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/012_candidate_alt_d2_n6_r2_3_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/012_candidate_alt_d2_n6_r2_3_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/012_candidate_alt_d2_n6_r2_3_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:2,10=separate_vehicle;2:3,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=5 --set journey_max_nodes=5 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_selected_d1_n2_2_3_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 116.680711
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_2,3
pair_role = selected_baseline
source_selected_pair = [2, 3]
forced_pair = [2, 3]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,3
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 1.3517246211236511e-09
external_branch_score_event_pair = [17, 18]
external_branch_score_event_predicted_walltime_gain = 0.06507153809070587
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
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/013_candidate_selected_d1_n2_2_3_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/013_candidate_selected_d1_n2_2_3_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/013_candidate_selected_d1_n2_2_3_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/013_candidate_selected_d1_n2_2_3_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,3' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 116.680711
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_2,3
pair_role = alternative
source_selected_pair = [2, 3]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.089000001
source_alt_routeopt_bkf_reason = branch_score=2.74643e-10;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=195;pool_total_child_width=324;pool_balance_gap=66;incumbent_disagreement=0.5;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 1.3517246211236511e-09
external_branch_score_event_pair = [17, 18]
external_branch_score_event_predicted_walltime_gain = 0.06507153809070587
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 195
source_alt_pool_total_child_width = 324
source_alt_pool_balance_gap = 66
source_alt_branch_score = 2.7464255869524834e-10
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/014_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/014_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/014_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/014_candidate_alt_d1_n2_r1_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 116.680711
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_2,3
pair_role = alternative
source_selected_pair = [2, 3]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 3
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.087000001
source_alt_routeopt_bkf_reason = branch_score=3.50792e-10;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=194;pool_total_child_width=337;pool_balance_gap=51;incumbent_disagreement=0.5;rank=3
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 1.3517246211236511e-09
external_branch_score_event_pair = [17, 18]
external_branch_score_event_predicted_walltime_gain = 0.06507153809070587
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 194
source_alt_pool_total_child_width = 337
source_alt_pool_balance_gap = 51
source_alt_branch_score = 3.507918122647169e-10
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/015_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/015_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/015_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/015_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_selected_d3_n10_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 157.221969
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d3__n10__sel_5,19
pair_role = selected_baseline
source_selected_pair = [5, 19]
forced_pair = [5, 19]
forced_pair_path_rule = force_pair_path:0:1,10=same_vehicle;1:2,3=separate_vehicle;2:3,17=separate_vehicle;3:5,19
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 5.590476540896783e-13
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.037737488746643
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
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/016_candidate_selected_d3_n10_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/016_candidate_selected_d3_n10_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/016_candidate_selected_d3_n10_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/016_candidate_selected_d3_n10_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,10=same_vehicle;1:2,3=separate_vehicle;2:3,17=separate_vehicle;3:5,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d3_n10_r3_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 157.221969
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d3__n10__sel_5,19
pair_role = alternative
source_selected_pair = [5, 19]
forced_pair = [13, 19]
forced_pair_path_rule = force_pair_path:0:1,10=same_vehicle;1:2,3=separate_vehicle;2:3,17=separate_vehicle;3:13,19
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 60
source_alt_rank = 3
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.031
source_alt_routeopt_bkf_reason = branch_score=4.4446e-13;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=212;pool_total_child_width=371;pool_balance_gap=53;incumbent_disagreement=0.5;rank=3
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 5.590476540896783e-13
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.037737488746643
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 212
source_alt_pool_total_child_width = 371
source_alt_pool_balance_gap = 53
source_alt_branch_score = 4.4446038646381303e-13
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/017_candidate_alt_d3_n10_r3_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/017_candidate_alt_d3_n10_r3_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/017_candidate_alt_d3_n10_r3_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/017_candidate_alt_d3_n10_r3_13_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,10=same_vehicle;1:2,3=separate_vehicle;2:3,17=separate_vehicle;3:13,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d3_n10_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 157.221969
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d3__n10__sel_5,19
pair_role = alternative
source_selected_pair = [5, 19]
forced_pair = [7, 13]
forced_pair_path_rule = force_pair_path:0:1,10=same_vehicle;1:2,3=separate_vehicle;2:3,17=separate_vehicle;3:7,13
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.015
source_alt_routeopt_bkf_reason = branch_score=1.67661e-13;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=223;pool_total_child_width=390;pool_balance_gap=56;incumbent_disagreement=0.5;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 5.590476540896783e-13
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.037737488746643
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 223
source_alt_pool_total_child_width = 390
source_alt_pool_balance_gap = 56
source_alt_branch_score = 1.6766138987139162e-13
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 44.0
branch_impact_priority_reason = active_touch=1;completion_retries=11;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/018_candidate_alt_d3_n10_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/018_candidate_alt_d3_n10_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/018_candidate_alt_d3_n10_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/018_candidate_alt_d3_n10_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,10=same_vehicle;1:2,3=separate_vehicle;2:3,17=separate_vehicle;3:7,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_selected_d4_n12_1_4_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 12
source_depth = 4
source_event_time = 199.131543
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph__d4__n12__sel_1,4
pair_role = selected_baseline
source_selected_pair = [1, 4]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,8=separate_vehicle;3:1,9=separate_vehicle;4:1,4
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 7.651579802430471e-15
external_branch_score_event_pair = [13, 17]
external_branch_score_event_predicted_walltime_gain = 0.658367931842804
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
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=9;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/019_candidate_selected_d4_n12_1_4_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/019_candidate_selected_d4_n12_1_4_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/019_candidate_selected_d4_n12_1_4_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/019_candidate_selected_d4_n12_1_4_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,8=separate_vehicle;3:1,9=separate_vehicle;4:1,4' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d4_n12_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 12
source_depth = 4
source_event_time = 199.131543
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph__d4__n12__sel_1,4
pair_role = alternative
source_selected_pair = [1, 4]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,8=separate_vehicle;3:1,9=separate_vehicle;4:1,10
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.494999999
source_alt_routeopt_bkf_reason = branch_score=1.99381e-15;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=160;pool_total_child_width=305;pool_balance_gap=15;incumbent_disagreement=0.666667;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 7.651579802430471e-15
external_branch_score_event_pair = [13, 17]
external_branch_score_event_predicted_walltime_gain = 0.658367931842804
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 160
source_alt_pool_total_child_width = 305
source_alt_pool_balance_gap = 15
source_alt_branch_score = 1.9938115845423475e-15
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=9;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/020_candidate_alt_d4_n12_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/020_candidate_alt_d4_n12_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/020_candidate_alt_d4_n12_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/020_candidate_alt_d4_n12_r1_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,8=separate_vehicle;3:1,9=separate_vehicle;4:1,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d4_n12_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
source_node_id = 12
source_depth = 4
source_event_time = 199.131543
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph__d4__n12__sel_1,4
pair_role = alternative
source_selected_pair = [1, 4]
forced_pair = [1, 17]
forced_pair_path_rule = force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,8=separate_vehicle;3:1,9=separate_vehicle;4:1,17
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 60
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.468999999
source_alt_routeopt_bkf_reason = branch_score=3.57036e-15;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=162;pool_total_child_width=299;pool_balance_gap=25;incumbent_disagreement=0.666667;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 7.651579802430471e-15
external_branch_score_event_pair = [13, 17]
external_branch_score_event_predicted_walltime_gain = 0.658367931842804
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 162
source_alt_pool_total_child_width = 299
source_alt_pool_balance_gap = 25
source_alt_branch_score = 3.570361610256544e-15
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 43.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=9;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/021_candidate_alt_d4_n12_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/021_candidate_alt_d4_n12_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/021_candidate_alt_d4_n12_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/021_candidate_alt_d4_n12_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,3=separate_vehicle;1:1,2=same_vehicle;2:1,8=separate_vehicle;3:1,9=separate_vehicle;4:1,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_selected_d1_n1_6_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 75.531964
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d1__n1__sel_6,14
pair_role = selected_baseline
source_selected_pair = [6, 14]
forced_pair = [6, 14]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:6,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 7.337321221712045e-07
external_branch_score_event_pair = [16, 20]
external_branch_score_event_predicted_walltime_gain = 0.356289267539978
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
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/022_candidate_selected_d1_n1_6_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/022_candidate_selected_d1_n1_6_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/022_candidate_selected_d1_n1_6_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/022_candidate_selected_d1_n1_6_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:6,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 75.531964
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d1__n1__sel_6,14
pair_role = alternative
source_selected_pair = [6, 14]
forced_pair = [7, 14]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:7,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.918000724
source_alt_routeopt_bkf_reason = branch_score=2.89602e-07;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=249;pool_total_child_width=433;pool_balance_gap=65;incumbent_disagreement=0.5;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 7.337321221712045e-07
external_branch_score_event_pair = [16, 20]
external_branch_score_event_predicted_walltime_gain = 0.356289267539978
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 249
source_alt_pool_total_child_width = 433
source_alt_pool_balance_gap = 65
source_alt_branch_score = 2.8960170084246784e-07
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/023_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/023_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/023_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/023_candidate_alt_d1_n1_r2_7_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:7,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d1_n1_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 75.531964
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d1__n1__sel_6,14
pair_role = alternative
source_selected_pair = [6, 14]
forced_pair = [8, 15]
forced_pair_path_rule = force_pair_path:0:1,5=same_vehicle;1:8,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 5
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.917000855
source_alt_routeopt_bkf_reason = branch_score=3.4208e-07;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=241;pool_total_child_width=422;pool_balance_gap=60;incumbent_disagreement=0.5;rank=5
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 7.337321221712045e-07
external_branch_score_event_pair = [16, 20]
external_branch_score_event_predicted_walltime_gain = 0.356289267539978
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 241
source_alt_pool_total_child_width = 422
source_alt_pool_balance_gap = 60
source_alt_branch_score = 3.420803693643393e-07
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=16;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/024_candidate_alt_d1_n1_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/024_candidate_alt_d1_n1_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/024_candidate_alt_d1_n1_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/024_candidate_alt_d1_n1_r5_8_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,5=same_vehicle;1:8,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 025_candidate_selected_d1_n2_1_7_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 388.643743
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph__d1__n2__sel_1,7
pair_role = selected_baseline
source_selected_pair = [1, 7]
forced_pair = [1, 7]
forced_pair_path_rule = force_pair_path:0:2,5=separate_vehicle;1:1,7
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 6.39682043032733e-29
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.7479292154312134
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
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=13;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/025_candidate_selected_d1_n2_1_7_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/025_candidate_selected_d1_n2_1_7_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/025_candidate_selected_d1_n2_1_7_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/025_candidate_selected_d1_n2_1_7_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=separate_vehicle;1:1,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 026_candidate_alt_d1_n2_r3_3_4_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 388.643743
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph__d1__n2__sel_1,7
pair_role = alternative
source_selected_pair = [1, 7]
forced_pair = [3, 4]
forced_pair_path_rule = force_pair_path:0:2,5=separate_vehicle;1:3,4
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 3
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.393
source_alt_routeopt_bkf_reason = branch_score=6.09814e-30;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=415;pool_total_child_width=748;pool_balance_gap=82;incumbent_disagreement=0.5;rank=3
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 6.39682043032733e-29
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.7479292154312134
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 415
source_alt_pool_total_child_width = 748
source_alt_pool_balance_gap = 82
source_alt_branch_score = 6.098137434438759e-30
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=13;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/026_candidate_alt_d1_n2_r3_3_4_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/026_candidate_alt_d1_n2_r3_3_4_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/026_candidate_alt_d1_n2_r3_3_4_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/026_candidate_alt_d1_n2_r3_3_4_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=separate_vehicle;1:3,4' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 027_candidate_alt_d1_n2_r5_4_10_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 388.643743
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph__d1__n2__sel_1,7
pair_role = alternative
source_selected_pair = [1, 7]
forced_pair = [4, 10]
forced_pair_path_rule = force_pair_path:0:2,5=separate_vehicle;1:4,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 5
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.298
source_alt_routeopt_bkf_reason = branch_score=1.19357e-29;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=429;pool_total_child_width=743;pool_balance_gap=115;incumbent_disagreement=0.5;rank=5
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 6.39682043032733e-29
external_branch_score_event_pair = [19, 20]
external_branch_score_event_predicted_walltime_gain = 1.7479292154312134
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 429
source_alt_pool_total_child_width = 743
source_alt_pool_balance_gap = 115
source_alt_branch_score = 1.1935747704916072e-29
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=0;completion_retries=13;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/027_candidate_alt_d1_n2_r5_4_10_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/027_candidate_alt_d1_n2_r5_4_10_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/027_candidate_alt_d1_n2_r5_4_10_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/027_candidate_alt_d1_n2_r5_4_10_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=separate_vehicle;1:4,10' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 028_candidate_selected_d3_n10_1_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 188.770602
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d3__n10__sel_1,12
pair_role = selected_baseline
source_selected_pair = [1, 12]
forced_pair = [1, 12]
forced_pair_path_rule = force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,3=separate_vehicle;3:1,12
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_routeopt_bkf_stage = None
source_alt_routeopt_bkf_dynamic_k = None
source_alt_routeopt_bkf_stage_rank = None
source_alt_routeopt_bkf_filtered_count = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.01
external_branch_score_event_pair = [10, 20]
external_branch_score_event_predicted_walltime_gain = None
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
branch_impact_priority_reason = active_touch=0;completion_retries=14;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/028_candidate_selected_d3_n10_1_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/028_candidate_selected_d3_n10_1_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/028_candidate_selected_d3_n10_1_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/028_candidate_selected_d3_n10_1_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,3=separate_vehicle;3:1,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 029_candidate_alt_d3_n10_r1_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 188.770602
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d3__n10__sel_1,12
pair_role = alternative
source_selected_pair = [1, 12]
forced_pair = [3, 16]
forced_pair_path_rule = force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,3=separate_vehicle;3:3,16
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.791
source_alt_routeopt_bkf_reason = branch_score=5.05549e-15;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=303;pool_total_child_width=566;pool_balance_gap=40;incumbent_disagreement=0.5;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.01
external_branch_score_event_pair = [10, 20]
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 303
source_alt_pool_total_child_width = 566
source_alt_pool_balance_gap = 40
source_alt_branch_score = 5.05549496986361e-15
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=0;completion_retries=14;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/029_candidate_alt_d3_n10_r1_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/029_candidate_alt_d3_n10_r1_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/029_candidate_alt_d3_n10_r1_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/029_candidate_alt_d3_n10_r1_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,3=separate_vehicle;3:3,16' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 030_candidate_alt_d3_n10_r2_5_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 10
source_depth = 3
source_event_time = 188.770602
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d3__n10__sel_1,12
pair_role = alternative
source_selected_pair = [1, 12]
forced_pair = [5, 12]
forced_pair_path_rule = force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,3=separate_vehicle;3:5,12
probe_mode = child_probe
probe_max_nodes = 6
probe_max_cg_iterations = 60
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.778
source_alt_routeopt_bkf_reason = branch_score=3.26146e-15;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=299;pool_total_child_width=543;pool_balance_gap=55;incumbent_disagreement=0.5;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 2
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.01
external_branch_score_event_pair = [10, 20]
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 299
source_alt_pool_total_child_width = 543
source_alt_pool_balance_gap = 55
source_alt_branch_score = 3.2614594940629784e-15
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 41.0
branch_impact_priority_reason = active_touch=0;completion_retries=14;negative_events=10;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/030_candidate_alt_d3_n10_r2_5_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/030_candidate_alt_d3_n10_r2_5_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/030_candidate_alt_d3_n10_r2_5_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v671_v545_v667_routeopt_bkf_staged_child_probe_20260628/runs/030_candidate_alt_d3_n10_r2_5_12_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,14=separate_vehicle;1:2,7=separate_vehicle;2:1,3=separate_vehicle;3:5,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=6 --set journey_max_nodes=6 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

- Report truncated to first 30 entries; full runbook has 36 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
