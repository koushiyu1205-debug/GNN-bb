# Journey Branch Candidate Replay Runbook

日期：2026-06-29

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45
entry_count = 4
candidate_event_count_seen = 1
candidate_event_count_with_replay_entries = 1
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 3
candidate_source = priority_top
candidate_selection = layered
staged_bkf_min_alternatives = 1
staged_bkf_max_alternatives = 3
staged_bkf_score_gap = 0.75
staged_bkf_max_pool_child_width = None
staged_bkf_max_pool_total_child_width = None
staged_bkf_max_pool_balance_gap = None
staged_bkf_require_score = False
staged_bkf_min_branch_score = None
staged_bkf_allow_filtered_fallback = True
candidate_log_top_n = 200
min_source_depth = None
max_source_depth = None
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
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
max_events_per_instance = None
paired_probe = True
paired_group_count = 1
paired_baseline_entry_count = 1
paired_alternative_entry_count = 3
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 0
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json': 1}
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
depth_filter_skip_count = 0
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
phased_testing_priority_context_count = 1
phased_testing_exact_effect_skip_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.064609
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_3,4
pair_role = selected_baseline
source_selected_pair = [3, 4]
forced_pair = [3, 4]
forced_pair_path_rule = force_pair_path:0:3,4
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
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
phased_testing_priority = 13.658727284060001
phased_testing_priority_reason = phase1_best_min_gain=2.91046;phase1_best_product=31.9974;phase1_complete=12;phase2_negative_child=1;phase2_negative_journey=1;phase2_worst_negative=14.8815;phase_wall=0.338815;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 2.910461119
phased_testing_phase1_best_child_lp_gain_product = 31.997387104
phased_testing_phase2_negative_child_count_total = 1
phased_testing_phase2_worst_negative_severity_max = 14.881469
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 45 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,4 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.064609
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_3,4
pair_role = alternative
source_selected_pair = [3, 4]
forced_pair = [1, 13]
forced_pair_path_rule = force_pair_path:0:1,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
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
source_alt_pool_max_child_width = 332
source_alt_pool_total_child_width = 561
source_alt_pool_balance_gap = 103
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 13.658727284060001
phased_testing_priority_reason = phase1_best_min_gain=2.91046;phase1_best_product=31.9974;phase1_complete=12;phase2_negative_child=1;phase2_negative_journey=1;phase2_worst_negative=14.8815;phase_wall=0.338815;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 2.910461119
phased_testing_phase1_best_child_lp_gain_product = 31.997387104
phased_testing_phase2_negative_child_count_total = 1
phased_testing_phase2_worst_negative_severity_max = 14.881469
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 45 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/002_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/002_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/002_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/002_candidate_alt_d0_n0_r1_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r2_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.064609
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_3,4
pair_role = alternative
source_selected_pair = [3, 4]
forced_pair = [1, 9]
forced_pair_path_rule = force_pair_path:0:1,9
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
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
source_alt_pool_max_child_width = 333
source_alt_pool_total_child_width = 575
source_alt_pool_balance_gap = 91
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 13.658727284060001
phased_testing_priority_reason = phase1_best_min_gain=2.91046;phase1_best_product=31.9974;phase1_complete=12;phase2_negative_child=1;phase2_negative_journey=1;phase2_worst_negative=14.8815;phase_wall=0.338815;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 2.910461119
phased_testing_phase1_best_child_lp_gain_product = 31.997387104
phased_testing_phase2_negative_child_count_total = 1
phased_testing_phase2_worst_negative_severity_max = 14.881469
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 45 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/003_candidate_alt_d0_n0_r2_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/003_candidate_alt_d0_n0_r2_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/003_candidate_alt_d0_n0_r2_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/003_candidate_alt_d0_n0_r2_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,9 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r6_2_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.064609
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d0__n0__sel_3,4
pair_role = alternative
source_selected_pair = [3, 4]
forced_pair = [2, 19]
forced_pair_path_rule = force_pair_path:0:2,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 6
source_alt_selection_reason = min_max_child_width
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
source_alt_pool_max_child_width = 323
source_alt_pool_total_child_width = 532
source_alt_pool_balance_gap = 114
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
phased_testing_priority = 13.658727284060001
phased_testing_priority_reason = phase1_best_min_gain=2.91046;phase1_best_product=31.9974;phase1_complete=12;phase2_negative_child=1;phase2_negative_journey=1;phase2_worst_negative=14.8815;phase_wall=0.338815;exact_effect=False
phased_testing_phase1_best_min_child_lp_gain = 2.910461119
phased_testing_phase1_best_child_lp_gain_product = 31.997387104
phased_testing_phase2_negative_child_count_total = 1
phased_testing_phase2_worst_negative_severity_max = 14.881469
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 45 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/004_candidate_alt_d0_n0_r6_2_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/004_candidate_alt_d0_n0_r6_2_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/004_candidate_alt_d0_n0_r6_2_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/runs/004_candidate_alt_d0_n0_r6_2_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
