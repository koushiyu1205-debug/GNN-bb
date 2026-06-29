# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628
entry_count = 6
candidate_event_count_seen = 566
candidate_event_count_with_replay_entries = 3
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 2
candidate_source = both
candidate_selection = routeopt_bkf_staged
staged_bkf_min_alternatives = 1
staged_bkf_max_alternatives = 2
staged_bkf_score_gap = 0.75
staged_bkf_max_pool_child_width = 900.0
staged_bkf_max_pool_total_child_width = 1800.0
staged_bkf_max_pool_balance_gap = 500.0
staged_bkf_require_score = True
staged_bkf_min_branch_score = 0.67
staged_bkf_allow_filtered_fallback = False
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
paired_group_count = 3
paired_baseline_entry_count = 3
paired_alternative_entry_count = 3
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 19
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json': 1}
excluded_entry_key_count = 136
excluded_entry_skip_count = 34
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

### 001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.736239
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph__d0__n0__sel_3,4
pair_role = selected_baseline
source_selected_pair = [3, 4]
forced_pair = [3, 4]
forced_pair_path_rule = force_pair_path:0:3,4
probe_mode = child_probe
probe_max_nodes = 3
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
external_branch_score_event_priority = 0.74
external_branch_score_event_pair = [3, 12]
external_branch_score_event_predicted_walltime_gain = 0.7035738229751587
source_selected_fractionality = 0.2
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 31.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,4 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.736239
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph__d0__n0__sel_3,4
pair_role = alternative
source_selected_pair = [3, 4]
forced_pair = [3, 12]
forced_pair_path_rule = force_pair_path:0:3,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 1.214
source_alt_routeopt_bkf_reason = branch_score=0.74;fractionality=0.2;required_tie_tolerance=0.2;pool_max_child_width=362;pool_total_child_width=684;pool_balance_gap=40;incumbent_disagreement=0.2;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 1
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 28
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.74
external_branch_score_event_pair = [3, 12]
external_branch_score_event_predicted_walltime_gain = 0.7035738229751587
source_selected_fractionality = 0.2
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 362
source_alt_pool_total_child_width = 684
source_alt_pool_balance_gap = 40
source_alt_branch_score = 0.74
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 31.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=7;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/002_candidate_alt_d0_n0_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/002_candidate_alt_d0_n0_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/002_candidate_alt_d0_n0_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/002_candidate_alt_d0_n0_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_selected_d0_n0_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.125514
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph__d0__n0__sel_2,10
pair_role = selected_baseline
source_selected_pair = [2, 10]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:2,10
probe_mode = child_probe
probe_max_nodes = 3
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
external_branch_score_event_priority = 0.74
external_branch_score_event_pair = [3, 10]
external_branch_score_event_predicted_walltime_gain = 0.11533693969249725
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
branch_impact_priority = 17.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/003_candidate_selected_d0_n0_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/003_candidate_selected_d0_n0_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/003_candidate_selected_d0_n0_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/003_candidate_selected_d0_n0_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r1_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.125514
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph__d0__n0__sel_2,10
pair_role = alternative
source_selected_pair = [2, 10]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 4.414
source_alt_routeopt_bkf_reason = branch_score=0.74;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=369;pool_total_child_width=669;pool_balance_gap=69;incumbent_disagreement=0.5;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 1
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 33
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.74
external_branch_score_event_pair = [3, 10]
external_branch_score_event_predicted_walltime_gain = 0.11533693969249725
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 369
source_alt_pool_total_child_width = 669
source_alt_pool_balance_gap = 69
source_alt_branch_score = 0.74
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 17.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=3;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/004_candidate_alt_d0_n0_r1_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/004_candidate_alt_d0_n0_r1_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/004_candidate_alt_d0_n0_r1_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/004_candidate_alt_d0_n0_r1_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_selected_d1_n1_8_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 34.308953
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph__d1__n1__sel_8,12
pair_role = selected_baseline
source_selected_pair = [8, 12]
forced_pair = [8, 12]
forced_pair_path_rule = force_pair_path:0:5,19=same_vehicle;1:8,12
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
external_branch_score_event_priority = 0.91
external_branch_score_event_pair = [12, 13]
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.25
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = None
source_alt_pool_total_child_width = None
source_alt_pool_balance_gap = None
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 16.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=2;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/005_candidate_selected_d1_n1_8_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/005_candidate_selected_d1_n1_8_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/005_candidate_selected_d1_n1_8_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/005_candidate_selected_d1_n1_8_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,19=same_vehicle;1:8,12' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d1_n1_r1_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 34.308953
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph__d1__n1__sel_8,12
pair_role = alternative
source_selected_pair = [8, 12]
forced_pair = [12, 13]
forced_pair_path_rule = force_pair_path:0:5,19=same_vehicle;1:12,13
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 60
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 2.95
source_alt_routeopt_bkf_reason = branch_score=0.91;fractionality=0.25;required_tie_tolerance=0.25;pool_max_child_width=218;pool_total_child_width=400;pool_balance_gap=36;incumbent_disagreement=0.75;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 1
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 24
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.91
external_branch_score_event_pair = [12, 13]
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.25
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 218
source_alt_pool_total_child_width = 400
source_alt_pool_balance_gap = 36
source_alt_branch_score = 0.91
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 16.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=2;tail_class=completion_bound_tail;right_censored=False
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/006_candidate_alt_d1_n1_r1_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/006_candidate_alt_d1_n1_r1_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/006_candidate_alt_d1_n1_r1_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v675_v545_v667_routeopt_bkf_scorefloor_failclosed_20260628/runs/006_candidate_alt_d1_n1_r1_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,19=same_vehicle;1:12,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
