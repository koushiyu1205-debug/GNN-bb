# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624
entry_count = 9
candidate_event_count_seen = 30
candidate_event_count_with_replay_entries = 3
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 3
candidate_source = priority_top
candidate_log_top_n = 100
min_source_depth = 0
max_source_depth = 0
max_source_event_time = 180.0
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v141_prefix4_20260624']
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624', 'BPC_future/results/journey_branch_candidate_child_probe_runbook_v149_v141_apollo_root_only_20260624']
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 20
excluded_entry_skip_count = 8
focus_context_count = 0
focus_event_skip_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 26
source_event_time_filter_skip_count = 1
branch_impact_priority_context_count = 30
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r47_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 171.26982
source_selected_pair = [3, 6]
forced_pair = [5, 16]
forced_pair_path_rule = force_pair_path:0:5,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 47
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.111111111
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 312
source_alt_pool_total_child_width = 562
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/001_candidate_alt_d0_n0_r47_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/001_candidate_alt_d0_n0_r47_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/001_candidate_alt_d0_n0_r47_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/001_candidate_alt_d0_n0_r47_5_16_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,16 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r44_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 171.26982
source_selected_pair = [3, 6]
forced_pair = [5, 11]
forced_pair_path_rule = force_pair_path:0:5,11
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 44
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.222222222
source_alt_required_tie_tolerance = 0.222222222
source_alt_pool_max_child_width = 312
source_alt_pool_total_child_width = 575
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/002_candidate_alt_d0_n0_r44_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/002_candidate_alt_d0_n0_r44_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/002_candidate_alt_d0_n0_r44_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/002_candidate_alt_d0_n0_r44_5_11_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,11 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r48_6_8_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 171.26982
source_selected_pair = [3, 6]
forced_pair = [6, 8]
forced_pair_path_rule = force_pair_path:0:6,8
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 48
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.111111111
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 313
source_alt_pool_total_child_width = 570
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/003_candidate_alt_d0_n0_r48_6_8_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/003_candidate_alt_d0_n0_r48_6_8_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/003_candidate_alt_d0_n0_r48_6_8_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/003_candidate_alt_d0_n0_r48_6_8_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,8 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 50.314584
source_selected_pair = [1, 2]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 2
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 612
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 11.0
branch_impact_priority_reason = active_touch=0;completion_retries=0;negative_events=10;tail_class=early_branch_continues;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,10 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 50.314584
source_selected_pair = [1, 2]
forced_pair = [10, 18]
forced_pair_path_rule = force_pair_path:0:10,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 14
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 374
source_alt_pool_total_child_width = 634
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 11.0
branch_impact_priority_reason = active_touch=0;completion_retries=0;negative_events=10;tail_class=early_branch_continues;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/005_candidate_alt_d0_n0_r14_10_18_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,18 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 50.314584
source_selected_pair = [1, 2]
forced_pair = [1, 20]
forced_pair_path_rule = force_pair_path:0:1,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 5
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 374
source_alt_pool_total_child_width = 664
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 11.0
branch_impact_priority_reason = active_touch=0;completion_retries=0;negative_events=10;tail_class=early_branch_continues;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/006_candidate_alt_d0_n0_r5_1_20_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,20 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 114.992307
source_selected_pair = [3, 7]
forced_pair = [9, 10]
forced_pair_path_rule = force_pair_path:0:9,10
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 41
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 241
source_alt_pool_total_child_width = 402
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 8.0
branch_impact_priority_reason = active_touch=0;completion_retries=1;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/007_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/007_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/007_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/007_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,10 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 114.992307
source_selected_pair = [3, 7]
forced_pair = [4, 5]
forced_pair_path_rule = force_pair_path:0:4,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 13
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 241
source_alt_pool_total_child_width = 468
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 8.0
branch_impact_priority_reason = active_touch=0;completion_retries=1;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/008_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/008_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/008_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/008_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,5 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d0_n0_r26_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 114.992307
source_selected_pair = [3, 7]
forced_pair = [2, 9]
forced_pair_path_rule = force_pair_path:0:2,9
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 26
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 244
source_alt_pool_total_child_width = 446
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 8.0
branch_impact_priority_reason = active_touch=0;completion_retries=1;negative_events=3;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/009_candidate_alt_d0_n0_r26_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/009_candidate_alt_d0_n0_r26_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/009_candidate_alt_d0_n0_r26_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624/runs/009_candidate_alt_d0_n0_r26_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,9 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
