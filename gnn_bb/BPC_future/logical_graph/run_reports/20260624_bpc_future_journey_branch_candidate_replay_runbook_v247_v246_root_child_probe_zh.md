# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624
entry_count = 50
candidate_event_count_seen = 160
candidate_event_count_with_replay_entries = 9
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 6
candidate_source = priority_top
candidate_selection = layered
candidate_log_top_n = 200
min_source_depth = 0
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
probe_max_cg_iterations = 20
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
depth_filter_skip_count = 151
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.194476
source_selected_pair = [8, 18]
forced_pair = [14, 18]
forced_pair_path_rule = force_pair_path:0:14,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 177
source_alt_pool_total_child_width = 315
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/001_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/001_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/001_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/001_candidate_alt_d0_n0_r1_14_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:14,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 002_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.194476
source_selected_pair = [8, 18]
forced_pair = [15, 18]
forced_pair_path_rule = force_pair_path:0:15,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 183
source_alt_pool_total_child_width = 326
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/002_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/002_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/002_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/002_candidate_alt_d0_n0_r2_15_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 003_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.194476
source_selected_pair = [8, 18]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:3,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 35
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 173
source_alt_pool_total_child_width = 299
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/003_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/003_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/003_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/003_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 004_candidate_alt_d0_n0_r38_8_15_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.194476
source_selected_pair = [8, 18]
forced_pair = [8, 15]
forced_pair_path_rule = force_pair_path:0:8,15
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 38
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 177
source_alt_pool_total_child_width = 351
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/004_candidate_alt_d0_n0_r38_8_15_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/004_candidate_alt_d0_n0_r38_8_15_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/004_candidate_alt_d0_n0_r38_8_15_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/004_candidate_alt_d0_n0_r38_8_15_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 005_candidate_alt_d0_n0_r18_5_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.194476
source_selected_pair = [8, 18]
forced_pair = [5, 18]
forced_pair_path_rule = force_pair_path:0:5,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 18
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 179
source_alt_pool_total_child_width = 321
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/005_candidate_alt_d0_n0_r18_5_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/005_candidate_alt_d0_n0_r18_5_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/005_candidate_alt_d0_n0_r18_5_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/005_candidate_alt_d0_n0_r18_5_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 006_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 43.194476
source_selected_pair = [8, 18]
forced_pair = [10, 17]
forced_pair_path_rule = force_pair_path:0:10,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 43
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 174
source_alt_pool_total_child_width = 287
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/006_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/006_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/006_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/006_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 007_candidate_alt_d0_n0_r1_2_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 42.686285
source_selected_pair = [2, 5]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:2,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 123
source_alt_pool_total_child_width = 220
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/007_candidate_alt_d0_n0_r1_2_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/007_candidate_alt_d0_n0_r1_2_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/007_candidate_alt_d0_n0_r1_2_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/007_candidate_alt_d0_n0_r1_2_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 008_candidate_alt_d0_n0_r2_5_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 42.686285
source_selected_pair = [2, 5]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:5,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 121
source_alt_pool_total_child_width = 215
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/008_candidate_alt_d0_n0_r2_5_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/008_candidate_alt_d0_n0_r2_5_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/008_candidate_alt_d0_n0_r2_5_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/008_candidate_alt_d0_n0_r2_5_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 009_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 75.00732
source_selected_pair = [1, 12]
forced_pair = [4, 15]
forced_pair_path_rule = force_pair_path:0:4,15
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 249
source_alt_pool_total_child_width = 427
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/009_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/009_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/009_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/009_candidate_alt_d0_n0_r1_4_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 010_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 75.00732
source_selected_pair = [1, 12]
forced_pair = [7, 11]
forced_pair_path_rule = force_pair_path:0:7,11
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.428571429
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 246
source_alt_pool_total_child_width = 436
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/010_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/010_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/010_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/010_candidate_alt_d0_n0_r2_7_11_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,11 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 011_candidate_alt_d0_n0_r45_8_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 75.00732
source_selected_pair = [1, 12]
forced_pair = [8, 18]
forced_pair_path_rule = force_pair_path:0:8,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 45
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.142857143
source_alt_required_tie_tolerance = 0.285714286
source_alt_pool_max_child_width = 228
source_alt_pool_total_child_width = 406
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/011_candidate_alt_d0_n0_r45_8_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/011_candidate_alt_d0_n0_r45_8_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/011_candidate_alt_d0_n0_r45_8_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/011_candidate_alt_d0_n0_r45_8_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 012_candidate_alt_d0_n0_r17_1_14_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 75.00732
source_selected_pair = [1, 12]
forced_pair = [1, 14]
forced_pair_path_rule = force_pair_path:0:1,14
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 17
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.142857143
source_alt_pool_max_child_width = 248
source_alt_pool_total_child_width = 489
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/012_candidate_alt_d0_n0_r17_1_14_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/012_candidate_alt_d0_n0_r17_1_14_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/012_candidate_alt_d0_n0_r17_1_14_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/012_candidate_alt_d0_n0_r17_1_14_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,14 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 013_candidate_alt_d0_n0_r31_14_20_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 75.00732
source_selected_pair = [1, 12]
forced_pair = [14, 20]
forced_pair_path_rule = force_pair_path:0:14,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 31
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.285714286
source_alt_required_tie_tolerance = 0.142857143
source_alt_pool_max_child_width = 250
source_alt_pool_total_child_width = 470
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/013_candidate_alt_d0_n0_r31_14_20_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/013_candidate_alt_d0_n0_r31_14_20_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/013_candidate_alt_d0_n0_r31_14_20_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/013_candidate_alt_d0_n0_r31_14_20_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:14,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 014_candidate_alt_d0_n0_r32_9_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 75.00732
source_selected_pair = [1, 12]
forced_pair = [9, 15]
forced_pair_path_rule = force_pair_path:0:9,15
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 32
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.428571429
source_alt_fractionality = 0.142857143
source_alt_required_tie_tolerance = 0.285714286
source_alt_pool_max_child_width = 232
source_alt_pool_total_child_width = 387
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/014_candidate_alt_d0_n0_r32_9_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/014_candidate_alt_d0_n0_r32_9_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/014_candidate_alt_d0_n0_r32_9_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/014_candidate_alt_d0_n0_r32_9_15_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,15 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 015_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.810646
source_selected_pair = [8, 13]
forced_pair = [8, 16]
forced_pair_path_rule = force_pair_path:0:8,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 299
source_alt_pool_total_child_width = 557
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/015_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/015_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/015_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/015_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 016_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.810646
source_selected_pair = [8, 13]
forced_pair = [12, 17]
forced_pair_path_rule = force_pair_path:0:12,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 498
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/016_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/016_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/016_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/016_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 017_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.810646
source_selected_pair = [8, 13]
forced_pair = [8, 17]
forced_pair_path_rule = force_pair_path:0:8,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 15
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 285
source_alt_pool_total_child_width = 487
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/017_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/017_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/017_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/017_candidate_alt_d0_n0_r15_8_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 018_candidate_alt_d0_n0_r3_13_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.810646
source_selected_pair = [8, 13]
forced_pair = [13, 16]
forced_pair_path_rule = force_pair_path:0:13,16
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 3
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 299
source_alt_pool_total_child_width = 557
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/018_candidate_alt_d0_n0_r3_13_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/018_candidate_alt_d0_n0_r3_13_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/018_candidate_alt_d0_n0_r3_13_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/018_candidate_alt_d0_n0_r3_13_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:13,16 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 019_candidate_alt_d0_n0_r22_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.810646
source_selected_pair = [8, 13]
forced_pair = [17, 18]
forced_pair_path_rule = force_pair_path:0:17,18
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 22
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 290
source_alt_pool_total_child_width = 489
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/019_candidate_alt_d0_n0_r22_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/019_candidate_alt_d0_n0_r22_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/019_candidate_alt_d0_n0_r22_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/019_candidate_alt_d0_n0_r22_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:17,18 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 020_candidate_alt_d0_n0_r20_13_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.810646
source_selected_pair = [8, 13]
forced_pair = [13, 17]
forced_pair_path_rule = force_pair_path:0:13,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 20
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 287
source_alt_pool_total_child_width = 485
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/020_candidate_alt_d0_n0_r20_13_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/020_candidate_alt_d0_n0_r20_13_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/020_candidate_alt_d0_n0_r20_13_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/020_candidate_alt_d0_n0_r20_13_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:13,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 021_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 62.636153
source_selected_pair = [3, 10]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:3,17
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 295
source_alt_pool_total_child_width = 498
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/021_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/021_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/021_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/021_candidate_alt_d0_n0_r1_3_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,17 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 022_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 62.636153
source_selected_pair = [3, 10]
forced_pair = [3, 19]
forced_pair_path_rule = force_pair_path:0:3,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 292
source_alt_pool_total_child_width = 488
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/022_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/022_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/022_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/022_candidate_alt_d0_n0_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 023_candidate_alt_d0_n0_r13_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 62.636153
source_selected_pair = [3, 10]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 13
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 271
source_alt_pool_total_child_width = 485
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/023_candidate_alt_d0_n0_r13_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/023_candidate_alt_d0_n0_r13_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/023_candidate_alt_d0_n0_r13_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/023_candidate_alt_d0_n0_r13_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 024_candidate_alt_d0_n0_r10_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 62.636153
source_selected_pair = [3, 10]
forced_pair = [10, 19]
forced_pair_path_rule = force_pair_path:0:10,19
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 10
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 557
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/024_candidate_alt_d0_n0_r10_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/024_candidate_alt_d0_n0_r10_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/024_candidate_alt_d0_n0_r10_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/024_candidate_alt_d0_n0_r10_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,19 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 025_candidate_alt_d0_n0_r38_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 62.636153
source_selected_pair = [3, 10]
forced_pair = [12, 13]
forced_pair_path_rule = force_pair_path:0:12,13
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 38
source_alt_selection_reason = rank_diversity
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 294
source_alt_pool_total_child_width = 508
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/025_candidate_alt_d0_n0_r38_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/025_candidate_alt_d0_n0_r38_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/025_candidate_alt_d0_n0_r38_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/025_candidate_alt_d0_n0_r38_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,13 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 026_candidate_alt_d0_n0_r28_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 62.636153
source_selected_pair = [3, 10]
forced_pair = [1, 12]
forced_pair_path_rule = force_pair_path:0:1,12
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 28
source_alt_selection_reason = legacy_fill
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 274
source_alt_pool_total_child_width = 478
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/026_candidate_alt_d0_n0_r28_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/026_candidate_alt_d0_n0_r28_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/026_candidate_alt_d0_n0_r28_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/026_candidate_alt_d0_n0_r28_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,12 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 027_candidate_alt_d0_n0_r1_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.021689
source_selected_pair = [1, 2]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 244
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/027_candidate_alt_d0_n0_r1_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/027_candidate_alt_d0_n0_r1_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/027_candidate_alt_d0_n0_r1_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/027_candidate_alt_d0_n0_r1_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 028_candidate_alt_d0_n0_r2_1_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.021689
source_selected_pair = [1, 2]
forced_pair = [1, 7]
forced_pair_path_rule = force_pair_path:0:1,7
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 239
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/028_candidate_alt_d0_n0_r2_1_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/028_candidate_alt_d0_n0_r2_1_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/028_candidate_alt_d0_n0_r2_1_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/028_candidate_alt_d0_n0_r2_1_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,7 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 029_candidate_alt_d0_n0_r5_1_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.021689
source_selected_pair = [1, 2]
forced_pair = [1, 20]
forced_pair_path_rule = force_pair_path:0:1,20
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 5
source_alt_selection_reason = min_max_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 242
source_alt_pool_total_child_width = 417
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/029_candidate_alt_d0_n0_r5_1_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/029_candidate_alt_d0_n0_r5_1_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/029_candidate_alt_d0_n0_r5_1_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/029_candidate_alt_d0_n0_r5_1_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,20 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

### 030_candidate_alt_d0_n0_r6_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.021689
source_selected_pair = [1, 2]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
source_alt_rank = 6
source_alt_selection_reason = balanced_child_width
source_alt_focus_strong_positive = None
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 247
source_alt_pool_total_child_width = 472
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json --time-limit 120 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/030_candidate_alt_d0_n0_r6_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/030_candidate_alt_d0_n0_r6_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/030_candidate_alt_d0_n0_r6_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624/runs/030_candidate_alt_d0_n0_r6_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=200 --set max_nodes=3 --set journey_max_nodes=3 --set max_cg_iterations=20 --set journey_max_cg_iterations=20 --set journey_tail_action_audit_enabled=True --set journey_corrected_node_bound_audit_enabled=True --set journey_corrected_node_bound_fathom_enabled=False --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False
```

- Report truncated to first 30 entries; full runbook has 50 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.

In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.
