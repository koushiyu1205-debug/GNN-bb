# Journey Branch Candidate Replay Runbook

日期：2026-06-25

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625
entry_count = 4
candidate_event_count_seen = 9
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
focus_delta_input_paths = []
coverage_input_paths = []
coverage_gap_only = False
probe_mode = child_probe
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 36
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
depth_filter_skip_count = 8
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_4_8_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 42.307365
source_selected_pair = [4, 6]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,8
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 233
source_alt_pool_total_child_width = 409
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/001_candidate_alt_d0_n0_r1_4_8_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/001_candidate_alt_d0_n0_r1_4_8_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/001_candidate_alt_d0_n0_r1_4_8_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/001_candidate_alt_d0_n0_r1_4_8_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,8 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r2_4_11_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 42.307365
source_selected_pair = [4, 6]
forced_pair = [4, 11]
forced_pair_path_rule = force_pair_path:0:4,11
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 228
source_alt_pool_total_child_width = 424
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/002_candidate_alt_d0_n0_r2_4_11_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/002_candidate_alt_d0_n0_r2_4_11_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/002_candidate_alt_d0_n0_r2_4_11_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/002_candidate_alt_d0_n0_r2_4_11_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,11 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r25_6_12_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 42.307365
source_selected_pair = [4, 6]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:6,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 25
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 217
source_alt_pool_total_child_width = 371
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/003_candidate_alt_d0_n0_r25_6_12_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/003_candidate_alt_d0_n0_r25_6_12_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/003_candidate_alt_d0_n0_r25_6_12_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/003_candidate_alt_d0_n0_r25_6_12_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r4_4_15_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 42.307365
source_selected_pair = [4, 6]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:4,15
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 36
source_alt_rank = 4
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 229
source_alt_pool_total_child_width = 414
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 180 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/004_candidate_alt_d0_n0_r4_4_15_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/004_candidate_alt_d0_n0_r4_4_15_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/004_candidate_alt_d0_n0_r4_4_15_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v324_v315_seed61204_child_probe_20260625/runs/004_candidate_alt_d0_n0_r4_4_15_apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=36 --set journey_max_cg_iterations=36 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
