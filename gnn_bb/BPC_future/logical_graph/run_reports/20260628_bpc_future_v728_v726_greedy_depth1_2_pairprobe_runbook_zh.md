# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628
entry_count = 12
candidate_event_count_seen = 58
candidate_event_count_with_replay_entries = 4
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = priority_top
candidate_selection = routeopt_bkf_staged
staged_bkf_min_alternatives = 2
staged_bkf_max_alternatives = 3
staged_bkf_score_gap = 0.75
staged_bkf_max_pool_child_width = None
staged_bkf_max_pool_total_child_width = None
staged_bkf_max_pool_balance_gap = None
staged_bkf_require_score = False
staged_bkf_min_branch_score = None
staged_bkf_allow_filtered_fallback = True
candidate_log_top_n = 200
min_source_depth = 1
max_source_depth = 2
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = []
focus_delta_input_paths = []
coverage_input_paths = []
branch_score_input_paths = []
external_branch_score_context_count = 0
external_branch_score_event_count = 0
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 5
probe_max_cg_iterations = 36
max_events_per_instance = 2
paired_probe = True
paired_group_count = 4
paired_baseline_entry_count = 4
paired_alternative_entry_count = 8
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 4
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json': 2, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 2}
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
depth_filter_skip_count = 48
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
phased_testing_priority_context_count = 10
phased_testing_exact_effect_skip_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d1_n1_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 53.005499
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n1__sel_11,15
pair_role = selected_baseline
source_selected_pair = [11, 15]
forced_pair = [11, 15]
forced_pair_path_rule = force_pair_path:0:12,20=same_vehicle;1:11,15
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
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
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 127.23926005012001
phased_testing_priority_reason = phase1_best_min_gain=13.8641;phase1_best_product=270.79;phase1_complete=11;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.496251;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 13.864076167
phased_testing_phase1_best_child_lp_gain_product = 270.790330523
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/001_candidate_selected_d1_n1_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,20=same_vehicle;1:11,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n1_r1_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 53.005499
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n1__sel_11,15
pair_role = alternative
source_selected_pair = [11, 15]
forced_pair = [15, 18]
forced_pair_path_rule = force_pair_path:0:12,20=same_vehicle;1:15,18
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 30.566625939
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=308;pool_total_child_width=564;pool_balance_gap=52;incumbent_disagreement=0.333333;phase1_min_child_lp_gain=4.16054;phase1_child_lp_gain_product=136.343;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.0909697;phased_exact_effect=False;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 308
source_alt_pool_total_child_width = 564
source_alt_pool_balance_gap = 52
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 127.23926005012001
phased_testing_priority_reason = phase1_best_min_gain=13.8641;phase1_best_product=270.79;phase1_complete=11;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.496251;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 13.864076167
phased_testing_phase1_best_child_lp_gain_product = 270.790330523
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/002_candidate_alt_d1_n1_r1_15_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,20=same_vehicle;1:15,18' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d1_n1_r2_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 53.005499
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n1__sel_11,15
pair_role = alternative
source_selected_pair = [11, 15]
forced_pair = [15, 17]
forced_pair_path_rule = force_pair_path:0:12,20=same_vehicle;1:15,17
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 29.264760781
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.333333;required_tie_tolerance=0;pool_max_child_width=312;pool_total_child_width=559;pool_balance_gap=65;incumbent_disagreement=0.666667;phase1_min_child_lp_gain=4.22797;phase1_child_lp_gain_product=63.9624;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.0903553;phased_exact_effect=False;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 312
source_alt_pool_total_child_width = 559
source_alt_pool_balance_gap = 65
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 127.23926005012001
phased_testing_priority_reason = phase1_best_min_gain=13.8641;phase1_best_product=270.79;phase1_complete=11;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.496251;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 13.864076167
phased_testing_phase1_best_child_lp_gain_product = 270.790330523
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/003_candidate_alt_d1_n1_r2_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,20=same_vehicle;1:15,17' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_selected_d2_n4_7_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 492.947179
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n4__sel_7,14
pair_role = selected_baseline
source_selected_pair = [7, 14]
forced_pair = [7, 14]
forced_pair_path_rule = force_pair_path:0:12,20=same_vehicle;1:11,15=separate_vehicle;2:7,14
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
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
external_branch_score_event_priority = None
external_branch_score_event_pair = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 121.68267389896
phased_testing_priority_reason = phase1_best_min_gain=13.4143;phase1_best_product=234.31;phase1_complete=10;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.415675;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 13.4143055
phased_testing_phase1_best_child_lp_gain_product = 234.309666193
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/004_candidate_selected_d2_n4_7_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/004_candidate_selected_d2_n4_7_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/004_candidate_selected_d2_n4_7_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/004_candidate_selected_d2_n4_7_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,20=same_vehicle;1:11,15=separate_vehicle;2:7,14' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d2_n4_r1_6_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 492.947179
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n4__sel_7,14
pair_role = alternative
source_selected_pair = [7, 14]
forced_pair = [6, 7]
forced_pair_path_rule = force_pair_path:0:12,20=same_vehicle;1:11,15=separate_vehicle;2:6,7
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.248807457
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=379;pool_total_child_width=677;pool_balance_gap=81;incumbent_disagreement=0.5;phase1_min_child_lp_gain=0.120839;phase1_child_lp_gain_product=0.0897131;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.0914936;phased_exact_effect=False;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 379
source_alt_pool_total_child_width = 677
source_alt_pool_balance_gap = 81
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 121.68267389896
phased_testing_priority_reason = phase1_best_min_gain=13.4143;phase1_best_product=234.31;phase1_complete=10;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.415675;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 13.4143055
phased_testing_phase1_best_child_lp_gain_product = 234.309666193
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/005_candidate_alt_d2_n4_r1_6_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/005_candidate_alt_d2_n4_r1_6_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/005_candidate_alt_d2_n4_r1_6_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/005_candidate_alt_d2_n4_r1_6_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,20=same_vehicle;1:11,15=separate_vehicle;2:6,7' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d2_n4_r2_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 4
source_depth = 2
source_event_time = 492.947179
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n4__sel_7,14
pair_role = alternative
source_selected_pair = [7, 14]
forced_pair = [6, 15]
forced_pair_path_rule = force_pair_path:0:12,20=same_vehicle;1:11,15=separate_vehicle;2:6,15
probe_mode = child_probe
probe_max_nodes = 8
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 3.220799874
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=378;pool_total_child_width=654;pool_balance_gap=102;incumbent_disagreement=0.5;phase1_min_child_lp_gain=0.120839;phase1_child_lp_gain_product=0.0897131;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.0922519;phased_exact_effect=False;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 378
source_alt_pool_total_child_width = 654
source_alt_pool_balance_gap = 102
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 121.68267389896
phased_testing_priority_reason = phase1_best_min_gain=13.4143;phase1_best_product=234.31;phase1_complete=10;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.415675;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 13.4143055
phased_testing_phase1_best_child_lp_gain_product = 234.309666193
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d2_n4_r2_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d2_n4_r2_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d2_n4_r2_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/006_candidate_alt_d2_n4_r2_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,20=same_vehicle;1:11,15=separate_vehicle;2:6,15' --set journey_branch_candidate_log_top_n=200 --set max_nodes=8 --set journey_max_nodes=8 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_selected_d1_n1_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 41.028032
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_5,13
pair_role = selected_baseline
source_selected_pair = [5, 13]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:2,16=same_vehicle;1:5,13
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
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
external_branch_score_event_priority = None
external_branch_score_event_pair = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 37.198225700100004
phased_testing_priority_reason = phase1_best_min_gain=3.98927;phase1_best_product=19.6784;phase1_complete=9;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.3041;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 3.9892665
phased_testing_phase1_best_child_lp_gain_product = 19.678367485
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/007_candidate_selected_d1_n1_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/007_candidate_selected_d1_n1_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/007_candidate_selected_d1_n1_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/007_candidate_selected_d1_n1_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,16=same_vehicle;1:5,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d1_n1_r1_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 41.028032
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_5,13
pair_role = alternative
source_selected_pair = [5, 13]
forced_pair = [5, 19]
forced_pair_path_rule = force_pair_path:0:2,16=same_vehicle;1:5,19
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 27.346055064
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=284;pool_total_child_width=501;pool_balance_gap=67;incumbent_disagreement=0.5;phase1_min_child_lp_gain=3.98927;phase1_child_lp_gain_product=19.6784;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.089496;phased_exact_effect=False;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 284
source_alt_pool_total_child_width = 501
source_alt_pool_balance_gap = 67
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 37.198225700100004
phased_testing_priority_reason = phase1_best_min_gain=3.98927;phase1_best_product=19.6784;phase1_complete=9;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.3041;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 3.9892665
phased_testing_phase1_best_child_lp_gain_product = 19.678367485
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n1_r1_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n1_r1_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n1_r1_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/008_candidate_alt_d1_n1_r1_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,16=same_vehicle;1:5,19' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d1_n1_r2_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 1
source_depth = 1
source_event_time = 41.028032
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_5,13
pair_role = alternative
source_selected_pair = [5, 13]
forced_pair = [7, 13]
forced_pair_path_rule = force_pair_path:0:2,16=same_vehicle;1:7,13
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 27.330046262
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=286;pool_total_child_width=505;pool_balance_gap=67;incumbent_disagreement=0.5;phase1_min_child_lp_gain=3.98927;phase1_child_lp_gain_product=19.6784;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.0903763;phased_exact_effect=False;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 286
source_alt_pool_total_child_width = 505
source_alt_pool_balance_gap = 67
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 37.198225700100004
phased_testing_priority_reason = phase1_best_min_gain=3.98927;phase1_best_product=19.6784;phase1_complete=9;phase2_negative_child=0;phase2_negative_journey=0;phase2_worst_negative=0;phase_wall=0.3041;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 3.9892665
phased_testing_phase1_best_child_lp_gain_product = 19.678367485
phased_testing_phase2_negative_child_count_total = 0
phased_testing_phase2_worst_negative_severity_max = 0.0
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/009_candidate_alt_d1_n1_r2_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/009_candidate_alt_d1_n1_r2_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/009_candidate_alt_d1_n1_r2_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/009_candidate_alt_d1_n1_r2_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,16=same_vehicle;1:7,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_selected_d1_n2_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 58.662786
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_5,13
pair_role = selected_baseline
source_selected_pair = [5, 13]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:2,16=separate_vehicle;1:5,13
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
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
external_branch_score_event_priority = None
external_branch_score_event_pair = None
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 7.9500666655200005
phased_testing_priority_reason = phase1_best_min_gain=4.91254;phase1_best_product=24.5263;phase1_complete=9;phase2_negative_child=5;phase2_negative_journey=5;phase2_worst_negative=26.7273;phase_wall=0.395798;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 4.912540133
phased_testing_phase1_best_child_lp_gain_product = 24.526310043
phased_testing_phase2_negative_child_count_total = 5
phased_testing_phase2_worst_negative_severity_max = 26.727348818
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/010_candidate_selected_d1_n2_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/010_candidate_selected_d1_n2_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/010_candidate_selected_d1_n2_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/010_candidate_selected_d1_n2_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,16=separate_vehicle;1:5,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d1_n2_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 58.662786
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_5,13
pair_role = alternative
source_selected_pair = [5, 13]
forced_pair = [7, 13]
forced_pair_path_rule = force_pair_path:0:2,16=separate_vehicle;1:7,13
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 25.665110859
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=326;pool_total_child_width=578;pool_balance_gap=74;incumbent_disagreement=0.5;phase1_min_child_lp_gain=4.91254;phase1_child_lp_gain_product=24.5263;phase2_negative_child_count=2;phase2_negative_journey_count=2;phase2_worst_negative_severity=3.19301;phase_wall=0.0906171;phased_exact_effect=False;rank=1
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 1
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 326
source_alt_pool_total_child_width = 578
source_alt_pool_balance_gap = 74
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 7.9500666655200005
phased_testing_priority_reason = phase1_best_min_gain=4.91254;phase1_best_product=24.5263;phase1_complete=9;phase2_negative_child=5;phase2_negative_journey=5;phase2_worst_negative=26.7273;phase_wall=0.395798;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 4.912540133
phased_testing_phase1_best_child_lp_gain_product = 24.526310043
phased_testing_phase2_negative_child_count_total = 5
phased_testing_phase2_worst_negative_severity_max = 26.727348818
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d1_n2_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d1_n2_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d1_n2_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/011_candidate_alt_d1_n2_r1_7_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,16=separate_vehicle;1:7,13' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d1_n2_r2_4_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 58.662786
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_5,13
pair_role = alternative
source_selected_pair = [5, 13]
forced_pair = [4, 20]
forced_pair_path_rule = force_pair_path:0:2,16=separate_vehicle;1:4,20
probe_mode = child_probe
probe_max_nodes = 7
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = routeopt_bkf_staged
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = 7.959252324
source_alt_routeopt_bkf_reason = branch_score=0;fractionality=0.5;required_tie_tolerance=0;pool_max_child_width=319;pool_total_child_width=584;pool_balance_gap=54;incumbent_disagreement=0.5;phase1_min_child_lp_gain=0.776497;phase1_child_lp_gain_product=19.406;phase2_negative_child_count=0;phase2_negative_journey_count=0;phase2_worst_negative_severity=0;phase_wall=0.0908732;phased_exact_effect=False;rank=2
source_alt_routeopt_bkf_stage = accepted
source_alt_routeopt_bkf_dynamic_k = 3
source_alt_routeopt_bkf_stage_rank = 2
source_alt_routeopt_bkf_filtered_count = 0
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = None
external_branch_score_event_pair = None
external_branch_score_event_predicted_walltime_gain = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 319
source_alt_pool_total_child_width = 584
source_alt_pool_balance_gap = 54
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 7.9500666655200005
phased_testing_priority_reason = phase1_best_min_gain=4.91254;phase1_best_product=24.5263;phase1_complete=9;phase2_negative_child=5;phase2_negative_journey=5;phase2_worst_negative=26.7273;phase_wall=0.395798;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 4.912540133
phased_testing_phase1_best_child_lp_gain_product = 24.526310043
phased_testing_phase2_negative_child_count_total = 5
phased_testing_phase2_worst_negative_severity_max = 26.727348818
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d1_n2_r2_4_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d1_n2_r2_4_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d1_n2_r2_4_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runs/012_candidate_alt_d1_n2_r2_4_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,16=separate_vehicle;1:4,20' --set journey_branch_candidate_log_top_n=200 --set max_nodes=7 --set journey_max_nodes=7 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
