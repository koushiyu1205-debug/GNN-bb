# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624
entry_count = 4
candidate_event_count_seen = 3
candidate_event_count_with_replay_entries = 1
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 4
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = None
max_source_depth = 0
max_source_event_time = None
branch_impact_input_paths = []
exclude_runbook_paths = []
focus_delta_input_paths = ['BPC_future/results/journey_branch_counterfactual_delta_v210_v173_sector_apollo_seed61408_root_replay6_strict_20260624']
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 0
excluded_entry_skip_count = 0
focus_context_count = 1
focus_event_skip_count = 0
focus_strong_positive_pair_count = 4
focus_strong_positive_pair_available_count = 4
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 4
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 2
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r18_7_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 33.541547
source_selected_pair = [1, 6]
forced_pair = [7, 14]
forced_pair_path_rule = force_pair_path:0:7,14
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 18
source_alt_selection_reason = focus_strong_positive
source_alt_focus_strong_positive = True
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 140
source_alt_pool_total_child_width = 246
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 90 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/001_candidate_alt_d0_n0_r18_7_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/001_candidate_alt_d0_n0_r18_7_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/001_candidate_alt_d0_n0_r18_7_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/001_candidate_alt_d0_n0_r18_7_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r33_6_16_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 33.541547
source_selected_pair = [1, 6]
forced_pair = [6, 16]
forced_pair_path_rule = force_pair_path:0:6,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 33
source_alt_selection_reason = focus_strong_positive
source_alt_focus_strong_positive = True
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 143
source_alt_pool_total_child_width = 260
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 90 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/002_candidate_alt_d0_n0_r33_6_16_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/002_candidate_alt_d0_n0_r33_6_16_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/002_candidate_alt_d0_n0_r33_6_16_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/002_candidate_alt_d0_n0_r33_6_16_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r9_3_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 33.541547
source_selected_pair = [1, 6]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:3,14
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 9
source_alt_selection_reason = focus_strong_positive
source_alt_focus_strong_positive = True
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 144
source_alt_pool_total_child_width = 235
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 90 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/003_candidate_alt_d0_n0_r9_3_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/003_candidate_alt_d0_n0_r9_3_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/003_candidate_alt_d0_n0_r9_3_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/003_candidate_alt_d0_n0_r9_3_14_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r7_3_6_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 33.541547
source_selected_pair = [1, 6]
forced_pair = [3, 6]
forced_pair_path_rule = force_pair_path:0:3,6
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = None
source_alt_rank = 7
source_alt_selection_reason = focus_strong_positive
source_alt_focus_strong_positive = True
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 144
source_alt_pool_total_child_width = 254
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 90 --results-csv BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/004_candidate_alt_d0_n0_r7_3_6_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/004_candidate_alt_d0_n0_r7_3_6_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/004_candidate_alt_d0_n0_r7_3_6_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_child_probe_runbook_v220_sector_apollo_seed61408_focus_strong_top200_20260624/runs/004_candidate_alt_d0_n0_r7_3_6_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,6 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
