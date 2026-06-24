# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624
entry_count = 16
candidate_event_count_seen = 30
candidate_event_count_with_replay_entries = 8
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = priority_top
candidate_log_top_n = 100
min_source_depth = 0
max_source_depth = 1
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v141_prefix4_20260624']
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624']
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 8
excluded_entry_key_count = 12
excluded_entry_skip_count = 12
focus_context_count = 0
focus_event_skip_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 19
branch_impact_priority_context_count = 30
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n2_r9_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [12, 16]
forced_pair = [15, 16]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:15,16
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 9
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 411
source_alt_pool_total_child_width = 780
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/001_candidate_alt_d1_n2_r9_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/001_candidate_alt_d1_n2_r9_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/001_candidate_alt_d1_n2_r9_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/001_candidate_alt_d1_n2_r9_15_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:15,16' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d1_n2_r6_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [12, 16]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:1,2=separate_vehicle;1:4,15
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 6
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 412
source_alt_pool_total_child_width = 764
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 38.0
branch_impact_priority_reason = active_touch=1;completion_retries=6;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/002_candidate_alt_d1_n2_r6_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/002_candidate_alt_d1_n2_r6_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/002_candidate_alt_d1_n2_r6_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/002_candidate_alt_d1_n2_r6_4_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=separate_vehicle;1:4,15' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r18_5_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 6]
forced_pair = [5, 19]
forced_pair_path_rule = force_pair_path:0:5,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 8
source_alt_rank = 18
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 311
source_alt_pool_total_child_width = 545
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/003_candidate_alt_d0_n0_r18_5_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/003_candidate_alt_d0_n0_r18_5_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/003_candidate_alt_d0_n0_r18_5_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/003_candidate_alt_d0_n0_r18_5_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,19 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r19_6_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 6]
forced_pair = [6, 19]
forced_pair_path_rule = force_pair_path:0:6,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 8
source_alt_rank = 19
source_selected_fractionality = 0.444444444
source_alt_fractionality = 0.444444444
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 311
source_alt_pool_total_child_width = 567
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 34.0
branch_impact_priority_reason = active_touch=1;completion_retries=1;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/004_candidate_alt_d0_n0_r19_6_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/004_candidate_alt_d0_n0_r19_6_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/004_candidate_alt_d0_n0_r19_6_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/004_candidate_alt_d0_n0_r19_6_19_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,19 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d1_n1_r29_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:3,7=same_vehicle;1:2,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 29
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 167
source_alt_pool_total_child_width = 285
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 26.0
branch_impact_priority_reason = active_touch=0;completion_retries=8;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/005_candidate_alt_d1_n1_r29_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/005_candidate_alt_d1_n1_r29_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/005_candidate_alt_d1_n1_r29_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/005_candidate_alt_d1_n1_r29_2_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=same_vehicle;1:2,10' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d1_n1_r2_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [2, 9]
forced_pair_path_rule = force_pair_path:0:3,7=same_vehicle;1:2,9
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 2
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 167
source_alt_pool_total_child_width = 303
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 26.0
branch_impact_priority_reason = active_touch=0;completion_retries=8;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/006_candidate_alt_d1_n1_r2_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/006_candidate_alt_d1_n1_r2_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/006_candidate_alt_d1_n1_r2_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/006_candidate_alt_d1_n1_r2_2_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=same_vehicle;1:2,9' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d1_n2_r48_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [9, 10]
forced_pair_path_rule = force_pair_path:0:3,7=separate_vehicle;1:9,10
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 48
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 243
source_alt_pool_total_child_width = 406
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=7;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/007_candidate_alt_d1_n2_r48_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/007_candidate_alt_d1_n2_r48_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/007_candidate_alt_d1_n2_r48_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/007_candidate_alt_d1_n2_r48_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=separate_vehicle;1:9,10' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d1_n2_r37_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [1, 9]
forced_pair = [4, 5]
forced_pair_path_rule = force_pair_path:0:3,7=separate_vehicle;1:4,5
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 37
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 243
source_alt_pool_total_child_width = 471
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=7;negative_events=7;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/008_candidate_alt_d1_n2_r37_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/008_candidate_alt_d1_n2_r37_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/008_candidate_alt_d1_n2_r37_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/008_candidate_alt_d1_n2_r37_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:3,7=separate_vehicle;1:4,5' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [2, 12]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:2,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 5
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 213
source_alt_pool_total_child_width = 400
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 23.0
branch_impact_priority_reason = active_touch=1;completion_retries=2;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/009_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/009_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/009_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/009_candidate_alt_d1_n1_r5_2_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:2,12' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:1,18=same_vehicle;1:6,12
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 24
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 220
source_alt_pool_total_child_width = 412
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 23.0
branch_impact_priority_reason = active_touch=1;completion_retries=2;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/010_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/010_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/010_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/010_candidate_alt_d1_n1_r24_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,18=same_vehicle;1:6,12' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d1_n1_r31_10_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 10]
forced_pair = [10, 14]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:10,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 31
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 221
source_alt_pool_total_child_width = 364
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 21.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/011_candidate_alt_d1_n1_r31_10_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/011_candidate_alt_d1_n1_r31_10_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/011_candidate_alt_d1_n1_r31_10_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/011_candidate_alt_d1_n1_r31_10_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:10,14' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d1_n1_r30_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [1, 10]
forced_pair = [5, 14]
forced_pair_path_rule = force_pair_path:0:1,2=same_vehicle;1:5,14
probe_mode = child_probe
probe_max_nodes = 4
probe_max_cg_iterations = 8
source_alt_rank = 30
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 222
source_alt_pool_total_child_width = 357
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 21.0
branch_impact_priority_reason = active_touch=0;completion_retries=6;negative_events=6;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/012_candidate_alt_d1_n1_r30_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/012_candidate_alt_d1_n1_r30_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/012_candidate_alt_d1_n1_r30_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/012_candidate_alt_d1_n1_r30_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:1,2=same_vehicle;1:5,14' --set journey_branch_candidate_log_top_n=100 --set max_nodes=4 --set journey_max_nodes=4 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [1, 18]
forced_pair = [2, 6]
forced_pair_path_rule = force_pair_path:0:2,6
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 8
source_alt_rank = 2
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 561
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 14.0
branch_impact_priority_reason = active_touch=0;completion_retries=1;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/013_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/013_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/013_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/013_candidate_alt_d0_n0_r2_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,6 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [1, 18]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:6,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 8
source_alt_rank = 30
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 296
source_alt_pool_total_child_width = 563
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 14.0
branch_impact_priority_reason = active_touch=0;completion_retries=1;negative_events=9;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/014_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/014_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/014_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/014_candidate_alt_d0_n0_r30_6_12_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,12 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [1, 2]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 8
source_alt_rank = 1
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 11.0
branch_impact_priority_reason = active_touch=0;completion_retries=0;negative_events=10;tail_class=early_branch_continues;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/015_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/015_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/015_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/015_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [1, 2]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 8
source_alt_rank = 6
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 11.0
branch_impact_priority_reason = active_touch=0;completion_retries=0;negative_events=10;tail_class=early_branch_continues;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 60 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/016_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/016_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/016_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624/runs/016_candidate_alt_d0_n0_r6_2_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=100 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=8 --set journey_max_cg_iterations=8 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
