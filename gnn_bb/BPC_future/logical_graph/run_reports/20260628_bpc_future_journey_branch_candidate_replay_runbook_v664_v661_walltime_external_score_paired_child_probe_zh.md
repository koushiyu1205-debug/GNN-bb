# Journey Branch Candidate Replay Runbook

日期：2026-06-28

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628
entry_count = 24
candidate_event_count_seen = 566
candidate_event_count_with_replay_entries = 15
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 1
candidate_source = both
candidate_selection = external_branch_score
candidate_log_top_n = 200
min_source_depth = 0
max_source_depth = 0
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628', 'BPC_future/results/journey_branch_candidate_replay_runbook_v654_v648_near_positive_full600_20260628']
focus_delta_input_paths = []
coverage_input_paths = []
branch_score_input_paths = ['BPC_future/results/gat_branch_action_v661_v659_walltime_on_v545_full60_logs_20260628']
external_branch_score_context_count = 18823
external_branch_score_event_count = 42
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 60
max_events_per_instance = 1
paired_probe = True
paired_group_count = 10
paired_baseline_entry_count = 10
paired_alternative_entry_count = 14
paired_selected_missing_skip_count = 0
instance_event_limit_skip_count = 0
accepted_event_count_by_instance = {'BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json': 1, 'BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json': 1}
excluded_entry_key_count = 72
excluded_entry_skip_count = 5
focus_context_count = 0
focus_event_skip_count = 0
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 524
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_selected_d0_n0_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.715418
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph__d0__n0__sel_5,19
pair_role = selected_baseline
source_selected_pair = [5, 19]
forced_pair = [5, 19]
forced_pair_path_rule = force_pair_path:0:5,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.6993146538734436
external_branch_score_event_pair = [3, 10]
external_branch_score_event_predicted_walltime_gain = 84.40365600585938
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
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/001_candidate_selected_d0_n0_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/001_candidate_selected_d0_n0_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/001_candidate_selected_d0_n0_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/001_candidate_selected_d0_n0_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r7_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.715418
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph__d0__n0__sel_5,19
pair_role = alternative
source_selected_pair = [5, 19]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 7
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.6993146538734436
external_branch_score_event_pair = [3, 10]
external_branch_score_event_predicted_walltime_gain = 84.40365600585938
source_selected_fractionality = 0.25
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 299
source_alt_pool_total_child_width = 547
source_alt_pool_balance_gap = 51
source_alt_branch_score = 0.6993146538734436
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/002_candidate_alt_d0_n0_r7_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/002_candidate_alt_d0_n0_r7_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/002_candidate_alt_d0_n0_r7_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/002_candidate_alt_d0_n0_r7_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_selected_d0_n0_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 17.672952
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph__d0__n0__sel_3,19
pair_role = selected_baseline
source_selected_pair = [3, 19]
forced_pair = [3, 19]
forced_pair_path_rule = force_pair_path:0:3,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.6987790465354919
external_branch_score_event_pair = [2, 5]
external_branch_score_event_predicted_walltime_gain = 84.14905548095703
source_selected_fractionality = 0.184782609
source_alt_fractionality = 0.184782609
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/003_candidate_selected_d0_n0_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/003_candidate_selected_d0_n0_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/003_candidate_selected_d0_n0_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/003_candidate_selected_d0_n0_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r44_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 17.672952
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph__d0__n0__sel_3,19
pair_role = alternative
source_selected_pair = [3, 19]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 44
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.6987790465354919
external_branch_score_event_pair = [2, 5]
external_branch_score_event_predicted_walltime_gain = 84.14905548095703
source_selected_fractionality = 0.184782609
source_alt_fractionality = 0.184782609
source_alt_required_tie_tolerance = 0.315217391
source_alt_pool_max_child_width = 193
source_alt_pool_total_child_width = 348
source_alt_pool_balance_gap = 38
source_alt_branch_score = 0.6987790465354919
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/004_candidate_alt_d0_n0_r44_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/004_candidate_alt_d0_n0_r44_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/004_candidate_alt_d0_n0_r44_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/004_candidate_alt_d0_n0_r44_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_selected_d0_n0_5_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 23.23904
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d0__n0__sel_5,14
pair_role = selected_baseline
source_selected_pair = [5, 14]
forced_pair = [5, 14]
forced_pair_path_rule = force_pair_path:0:5,14
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.6743976473808289
external_branch_score_event_pair = [2, 14]
external_branch_score_event_predicted_walltime_gain = 72.81431579589844
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/005_candidate_selected_d0_n0_5_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/005_candidate_selected_d0_n0_5_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/005_candidate_selected_d0_n0_5_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/005_candidate_selected_d0_n0_5_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d0_n0_r27_2_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 23.23904
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d0__n0__sel_5,14
pair_role = alternative
source_selected_pair = [5, 14]
forced_pair = [2, 14]
forced_pair_path_rule = force_pair_path:0:2,14
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 27
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.6743976473808289
external_branch_score_event_pair = [2, 14]
external_branch_score_event_predicted_walltime_gain = 72.81431579589844
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.166666666
source_alt_pool_max_child_width = 328
source_alt_pool_total_child_width = 565
source_alt_pool_balance_gap = 91
source_alt_branch_score = 0.6743976473808289
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/006_candidate_alt_d0_n0_r27_2_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/006_candidate_alt_d0_n0_r27_2_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/006_candidate_alt_d0_n0_r27_2_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/006_candidate_alt_d0_n0_r27_2_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d0_n0_r36_3_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 41.872751
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_8,18
pair_role = alternative
source_selected_pair = [8, 18]
forced_pair = [3, 18]
forced_pair_path_rule = force_pair_path:0:3,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 36
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.6330696940422058
external_branch_score_event_pair = [3, 18]
external_branch_score_event_predicted_walltime_gain = 54.54087829589844
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 179
source_alt_pool_total_child_width = 294
source_alt_pool_balance_gap = 64
source_alt_branch_score = 0.6330696940422058
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/007_candidate_alt_d0_n0_r36_3_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/007_candidate_alt_d0_n0_r36_3_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/007_candidate_alt_d0_n0_r36_3_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/007_candidate_alt_d0_n0_r36_3_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r13_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.733932
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph__d0__n0__sel_6,20
pair_role = alternative
source_selected_pair = [6, 20]
forced_pair = [2, 16]
forced_pair_path_rule = force_pair_path:0:2,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 13
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.6247202157974243
external_branch_score_event_pair = [2, 16]
external_branch_score_event_predicted_walltime_gain = 50.963199615478516
source_selected_fractionality = 0.25
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 433
source_alt_pool_total_child_width = 770
source_alt_pool_balance_gap = 96
source_alt_branch_score = 0.6247202157974243
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/008_candidate_alt_d0_n0_r13_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/008_candidate_alt_d0_n0_r13_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/008_candidate_alt_d0_n0_r13_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/008_candidate_alt_d0_n0_r13_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_selected_d0_n0_1_12_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 72.990487
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph__d0__n0__sel_1,12
pair_role = selected_baseline
source_selected_pair = [1, 12]
forced_pair = [1, 12]
forced_pair_path_rule = force_pair_path:0:1,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5742433667182922
external_branch_score_event_pair = [2, 18]
external_branch_score_event_predicted_walltime_gain = 29.918542861938477
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.428571429
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/009_candidate_selected_d0_n0_1_12_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/009_candidate_selected_d0_n0_1_12_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/009_candidate_selected_d0_n0_1_12_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/009_candidate_selected_d0_n0_1_12_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d0_n0_r48_2_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 72.990487
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph__d0__n0__sel_1,12
pair_role = alternative
source_selected_pair = [1, 12]
forced_pair = [2, 18]
forced_pair_path_rule = force_pair_path:0:2,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 48
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5742433667182922
external_branch_score_event_pair = [2, 18]
external_branch_score_event_predicted_walltime_gain = 29.918542861938477
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.142857143
source_alt_required_tie_tolerance = 0.285714286
source_alt_pool_max_child_width = 235
source_alt_pool_total_child_width = 402
source_alt_pool_balance_gap = 68
source_alt_branch_score = 0.5742433667182922
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/010_candidate_alt_d0_n0_r48_2_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/010_candidate_alt_d0_n0_r48_2_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/010_candidate_alt_d0_n0_r48_2_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/010_candidate_alt_d0_n0_r48_2_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d0_n0_r76_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.544614
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph__d0__n0__sel_12,13
pair_role = alternative
source_selected_pair = [12, 13]
forced_pair = [3, 19]
forced_pair_path_rule = force_pair_path:0:3,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 76
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5668148994445801
external_branch_score_event_pair = [3, 19]
external_branch_score_event_predicted_walltime_gain = 26.886770248413086
source_selected_fractionality = 0.5
source_alt_fractionality = 0.076923077
source_alt_required_tie_tolerance = 0.423076923
source_alt_pool_max_child_width = 277
source_alt_pool_total_child_width = 476
source_alt_pool_balance_gap = 78
source_alt_branch_score = 0.5668148994445801
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/011_candidate_alt_d0_n0_r76_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/011_candidate_alt_d0_n0_r76_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/011_candidate_alt_d0_n0_r76_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/011_candidate_alt_d0_n0_r76_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 46.750718
pair_group_id = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph__d0__n0__sel_5,9
pair_role = alternative
source_selected_pair = [5, 9]
forced_pair = [2, 16]
forced_pair_path_rule = force_pair_path:0:2,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 67
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5550069808959961
external_branch_score_event_pair = [2, 16]
external_branch_score_event_predicted_walltime_gain = 22.09221076965332
source_selected_fractionality = 0.5
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 420
source_alt_pool_total_child_width = 817
source_alt_pool_balance_gap = 23
source_alt_branch_score = 0.5550069808959961
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/012_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/012_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/012_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/012_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d0_n0_r69_3_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 57.840267
pair_group_id = apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph__d0__n0__sel_4,12
pair_role = alternative
source_selected_pair = [4, 12]
forced_pair = [3, 8]
forced_pair_path_rule = force_pair_path:0:3,8
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 69
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5548619031906128
external_branch_score_event_pair = [3, 8]
external_branch_score_event_predicted_walltime_gain = 22.033491134643555
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.133333333
source_alt_required_tie_tolerance = 0.333333334
source_alt_pool_max_child_width = 286
source_alt_pool_total_child_width = 480
source_alt_pool_balance_gap = 92
source_alt_branch_score = 0.5548619031906128
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/013_candidate_alt_d0_n0_r69_3_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/013_candidate_alt_d0_n0_r69_3_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/013_candidate_alt_d0_n0_r69_3_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/013_candidate_alt_d0_n0_r69_3_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,8 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_selected_d0_n0_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.356791
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph__d0__n0__sel_3,10
pair_role = selected_baseline
source_selected_pair = [3, 10]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5459670424461365
external_branch_score_event_pair = [5, 20]
external_branch_score_event_predicted_walltime_gain = 18.43889045715332
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/014_candidate_selected_d0_n0_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/014_candidate_selected_d0_n0_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/014_candidate_selected_d0_n0_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/014_candidate_selected_d0_n0_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d0_n0_r34_5_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 63.356791
pair_group_id = tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph__d0__n0__sel_3,10
pair_role = alternative
source_selected_pair = [3, 10]
forced_pair = [5, 20]
forced_pair_path_rule = force_pair_path:0:5,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 34
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5459670424461365
external_branch_score_event_pair = [5, 20]
external_branch_score_event_predicted_walltime_gain = 18.43889045715332
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 285
source_alt_pool_total_child_width = 495
source_alt_pool_balance_gap = 75
source_alt_branch_score = 0.5459670424461365
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/015_candidate_alt_d0_n0_r34_5_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/015_candidate_alt_d0_n0_r34_5_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/015_candidate_alt_d0_n0_r34_5_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/015_candidate_alt_d0_n0_r34_5_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_selected_d0_n0_4_8_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 40.807728
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d0__n0__sel_4,8
pair_role = selected_baseline
source_selected_pair = [4, 8]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,8
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5452807545661926
external_branch_score_event_pair = [5, 18]
external_branch_score_event_predicted_walltime_gain = 18.16206169128418
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_8_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_8_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_8_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/016_candidate_selected_d0_n0_4_8_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,8 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d0_n0_r45_5_18_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 40.807728
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d0__n0__sel_4,8
pair_role = alternative
source_selected_pair = [4, 8]
forced_pair = [5, 18]
forced_pair_path_rule = force_pair_path:0:5,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 45
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5452807545661926
external_branch_score_event_pair = [5, 18]
external_branch_score_event_predicted_walltime_gain = 18.16206169128418
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 226
source_alt_pool_total_child_width = 366
source_alt_pool_balance_gap = 86
source_alt_branch_score = 0.5452807545661926
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/017_candidate_alt_d0_n0_r45_5_18_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/017_candidate_alt_d0_n0_r45_5_18_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/017_candidate_alt_d0_n0_r45_5_18_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/017_candidate_alt_d0_n0_r45_5_18_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_selected_d0_n0_5_6_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 29.683826
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph__d0__n0__sel_5,6
pair_role = selected_baseline
source_selected_pair = [5, 6]
forced_pair = [5, 6]
forced_pair_path_rule = force_pair_path:0:5,6
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5409200191497803
external_branch_score_event_pair = [1, 18]
external_branch_score_event_predicted_walltime_gain = 16.404699325561523
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/018_candidate_selected_d0_n0_5_6_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/018_candidate_selected_d0_n0_5_6_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/018_candidate_selected_d0_n0_5_6_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/018_candidate_selected_d0_n0_5_6_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,6 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d0_n0_r31_1_18_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 29.683826
pair_group_id = apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph__d0__n0__sel_5,6
pair_role = alternative
source_selected_pair = [5, 6]
forced_pair = [1, 18]
forced_pair_path_rule = force_pair_path:0:1,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 31
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5409200191497803
external_branch_score_event_pair = [1, 18]
external_branch_score_event_predicted_walltime_gain = 16.404699325561523
source_selected_fractionality = 0.5
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 133
source_alt_pool_total_child_width = 230
source_alt_pool_balance_gap = 36
source_alt_branch_score = 0.5409200191497803
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/019_candidate_alt_d0_n0_r31_1_18_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/019_candidate_alt_d0_n0_r31_1_18_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/019_candidate_alt_d0_n0_r31_1_18_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/019_candidate_alt_d0_n0_r31_1_18_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_selected_d0_n0_3_7_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.79365
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph__d0__n0__sel_3,7
pair_role = selected_baseline
source_selected_pair = [3, 7]
forced_pair = [3, 7]
forced_pair_path_rule = force_pair_path:0:3,7
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5406067371368408
external_branch_score_event_pair = [1, 18]
external_branch_score_event_predicted_walltime_gain = 16.278553009033203
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.454545455
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/020_candidate_selected_d0_n0_3_7_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/020_candidate_selected_d0_n0_3_7_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/020_candidate_selected_d0_n0_3_7_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/020_candidate_selected_d0_n0_3_7_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,7 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d0_n0_r56_1_18_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.79365
pair_group_id = apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph__d0__n0__sel_3,7
pair_role = alternative
source_selected_pair = [3, 7]
forced_pair = [1, 18]
forced_pair_path_rule = force_pair_path:0:1,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 56
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5406067371368408
external_branch_score_event_pair = [1, 18]
external_branch_score_event_predicted_walltime_gain = 16.278553009033203
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.136363636
source_alt_required_tie_tolerance = 0.318181819
source_alt_pool_max_child_width = 204
source_alt_pool_total_child_width = 387
source_alt_pool_balance_gap = 21
source_alt_branch_score = 0.5406067371368408
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/021_candidate_alt_d0_n0_r56_1_18_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/021_candidate_alt_d0_n0_r56_1_18_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/021_candidate_alt_d0_n0_r56_1_18_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/021_candidate_alt_d0_n0_r56_1_18_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 13.16681
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_3,6
pair_role = selected_baseline
source_selected_pair = [3, 6]
forced_pair = [3, 6]
forced_pair_path_rule = force_pair_path:0:3,6
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5389631390571594
external_branch_score_event_pair = [3, 10]
external_branch_score_event_predicted_walltime_gain = 15.616915702819824
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/022_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/022_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/022_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/022_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,6 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d0_n0_r20_3_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 13.16681
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_3,6
pair_role = alternative
source_selected_pair = [3, 6]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = 20
source_alt_selection_reason = external_branch_score_priority
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = 1
external_branch_score_event_priority = 0.5389631390571594
external_branch_score_event_pair = [3, 10]
external_branch_score_event_predicted_walltime_gain = 15.616915702819824
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 236
source_alt_pool_total_child_width = 412
source_alt_pool_balance_gap = 60
source_alt_branch_score = 0.5389631390571594
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/023_candidate_alt_d0_n0_r20_3_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/023_candidate_alt_d0_n0_r20_3_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/023_candidate_alt_d0_n0_r20_3_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/023_candidate_alt_d0_n0_r20_3_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,10 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_selected_d0_n0_3_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 10.519053
pair_group_id = tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d0__n0__sel_3,5
pair_role = selected_baseline
source_selected_pair = [3, 5]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:3,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 60
source_alt_rank = -1
source_alt_selection_reason = selected_baseline
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = None
source_alt_routeopt_bkf_score = None
source_alt_routeopt_bkf_reason = None
source_alt_external_branch_score_rank = None
external_branch_score_event_priority = 0.5384684205055237
external_branch_score_event_pair = [1, 15]
external_branch_score_event_predicted_walltime_gain = 15.417848587036133
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
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
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/024_candidate_selected_d0_n0_3_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/024_candidate_selected_d0_n0_3_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/024_candidate_selected_d0_n0_3_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/runs/024_candidate_selected_d0_n0_3_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=60 --set journey_max_cg_iterations=60 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
