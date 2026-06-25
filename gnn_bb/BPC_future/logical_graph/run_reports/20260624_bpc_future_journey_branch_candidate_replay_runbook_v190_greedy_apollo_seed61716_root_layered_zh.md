# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624
entry_count = 6
candidate_event_count_seen = 2
candidate_event_count_with_replay_entries = 1
skipped_missing_instance_event_count = 0
entry_limit_reached = False
alt_pairs_per_event = 6
candidate_source = priority_top
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
probe_mode = full_replay
probe_max_nodes = None
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = None
excluded_entry_key_count = 0
excluded_entry_skip_count = 0
focus_context_count = 0
focus_event_skip_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 1
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.57875
source_selected_pair = [4, 12]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:5,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.466666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 287
source_alt_pool_total_child_width = 513
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 280 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,13 --set journey_branch_candidate_log_top_n=200
```

### 002_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.57875
source_selected_pair = [4, 12]
forced_pair = [5, 14]
forced_pair_path_rule = force_pair_path:0:5,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.466666667
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 289
source_alt_pool_total_child_width = 510
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 280 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/002_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/002_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/002_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/002_candidate_alt_d0_n0_r2_5_14_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,14 --set journey_branch_candidate_log_top_n=200
```

### 003_candidate_alt_d0_n0_r35_8_20_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.57875
source_selected_pair = [4, 12]
forced_pair = [8, 20]
forced_pair_path_rule = force_pair_path:0:8,20
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 35
source_alt_selection_reason = min_max_child_width
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.133333334
source_alt_pool_max_child_width = 271
source_alt_pool_total_child_width = 453
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 280 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/003_candidate_alt_d0_n0_r35_8_20_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/003_candidate_alt_d0_n0_r35_8_20_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/003_candidate_alt_d0_n0_r35_8_20_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/003_candidate_alt_d0_n0_r35_8_20_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,20 --set journey_branch_candidate_log_top_n=200
```

### 004_candidate_alt_d0_n0_r12_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.57875
source_selected_pair = [4, 12]
forced_pair = [12, 15]
forced_pair_path_rule = force_pair_path:0:12,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 12
source_alt_selection_reason = balanced_child_width
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.066666667
source_alt_pool_max_child_width = 287
source_alt_pool_total_child_width = 551
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 280 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/004_candidate_alt_d0_n0_r12_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/004_candidate_alt_d0_n0_r12_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/004_candidate_alt_d0_n0_r12_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/004_candidate_alt_d0_n0_r12_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,15 --set journey_branch_candidate_log_top_n=200
```

### 005_candidate_alt_d0_n0_r71_5_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.57875
source_selected_pair = [4, 12]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:5,8
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 71
source_alt_selection_reason = rank_diversity
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.133333333
source_alt_required_tie_tolerance = 0.333333334
source_alt_pool_max_child_width = 277
source_alt_pool_total_child_width = 450
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 280 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/005_candidate_alt_d0_n0_r71_5_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/005_candidate_alt_d0_n0_r71_5_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/005_candidate_alt_d0_n0_r71_5_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/005_candidate_alt_d0_n0_r71_5_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,8 --set journey_branch_candidate_log_top_n=200
```

### 006_candidate_alt_d0_n0_r46_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.57875
source_selected_pair = [4, 12]
forced_pair = [4, 19]
forced_pair_path_rule = force_pair_path:0:4,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 46
source_alt_selection_reason = legacy_fill
source_selected_fractionality = 0.466666667
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.133333334
source_alt_pool_max_child_width = 272
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 280 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/006_candidate_alt_d0_n0_r46_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/006_candidate_alt_d0_n0_r46_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/006_candidate_alt_d0_n0_r46_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v190_greedy_apollo_seed61716_root_layered_20260624/runs/006_candidate_alt_d0_n0_r46_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,19 --set journey_branch_candidate_log_top_n=200
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
