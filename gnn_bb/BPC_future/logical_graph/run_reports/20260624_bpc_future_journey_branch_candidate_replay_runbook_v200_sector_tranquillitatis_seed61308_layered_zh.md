# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624
entry_count = 12
candidate_event_count_seen = 2
candidate_event_count_with_replay_entries = 2
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 6
candidate_source = both
candidate_selection = layered
candidate_log_top_n = 100
min_source_depth = None
max_source_depth = 1
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
depth_filter_skip_count = 0
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.110443
source_selected_pair = [12, 13]
forced_pair = [5, 13]
forced_pair_path_rule = force_pair_path:0:5,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 271
source_alt_pool_total_child_width = 519
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/001_candidate_alt_d0_n0_r1_5_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,13 --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.110443
source_selected_pair = [12, 13]
forced_pair = [9, 13]
forced_pair_path_rule = force_pair_path:0:9,13
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 282
source_alt_pool_total_child_width = 521
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/002_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,13 --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.110443
source_selected_pair = [12, 13]
forced_pair = [3, 16]
forced_pair_path_rule = force_pair_path:0:3,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 17
source_alt_selection_reason = min_max_child_width
source_selected_fractionality = 0.5
source_alt_fractionality = 0.384615385
source_alt_required_tie_tolerance = 0.115384615
source_alt_pool_max_child_width = 259
source_alt_pool_total_child_width = 454
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/003_candidate_alt_d0_n0_r17_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,16 --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.110443
source_selected_pair = [12, 13]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:2,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 27
source_alt_selection_reason = balanced_child_width
source_selected_fractionality = 0.5
source_alt_fractionality = 0.384615385
source_alt_required_tie_tolerance = 0.115384615
source_alt_pool_max_child_width = 266
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
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/004_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/004_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/004_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/004_candidate_alt_d0_n0_r27_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,5 --set journey_branch_candidate_log_top_n=100
```

### 005_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.110443
source_selected_pair = [12, 13]
forced_pair = [11, 14]
forced_pair_path_rule = force_pair_path:0:11,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 77
source_alt_selection_reason = rank_diversity
source_selected_fractionality = 0.5
source_alt_fractionality = 0.076923077
source_alt_required_tie_tolerance = 0.423076923
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 467
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/005_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/005_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/005_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/005_candidate_alt_d0_n0_r77_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:11,14 --set journey_branch_candidate_log_top_n=100
```

### 006_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 56.110443
source_selected_pair = [12, 13]
forced_pair = [3, 14]
forced_pair_path_rule = force_pair_path:0:3,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 52
source_alt_selection_reason = legacy_fill
source_selected_fractionality = 0.5
source_alt_fractionality = 0.192307692
source_alt_required_tie_tolerance = 0.307692308
source_alt_pool_max_child_width = 262
source_alt_pool_total_child_width = 433
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/006_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/006_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/006_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/006_candidate_alt_d0_n0_r52_3_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,14 --set journey_branch_candidate_log_top_n=100
```

### 007_candidate_alt_d1_n2_r1_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 152.257833
source_selected_pair = [6, 11]
forced_pair = [8, 14]
forced_pair_path_rule = force_pair_path:0:12,13=separate_vehicle;1:8,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_selected_fractionality = 0.4375
source_alt_fractionality = 0.4375
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 370
source_alt_pool_total_child_width = 604
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/007_candidate_alt_d1_n2_r1_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/007_candidate_alt_d1_n2_r1_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/007_candidate_alt_d1_n2_r1_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/007_candidate_alt_d1_n2_r1_8_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,13=separate_vehicle;1:8,14' --set journey_branch_candidate_log_top_n=100
```

### 008_candidate_alt_d1_n2_r2_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 152.257833
source_selected_pair = [6, 11]
forced_pair = [11, 14]
forced_pair_path_rule = force_pair_path:0:12,13=separate_vehicle;1:11,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_selected_fractionality = 0.4375
source_alt_fractionality = 0.4375
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 339
source_alt_pool_total_child_width = 596
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/008_candidate_alt_d1_n2_r2_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/008_candidate_alt_d1_n2_r2_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/008_candidate_alt_d1_n2_r2_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/008_candidate_alt_d1_n2_r2_11_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,13=separate_vehicle;1:11,14' --set journey_branch_candidate_log_top_n=100
```

### 009_candidate_alt_d1_n2_r20_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 152.257833
source_selected_pair = [6, 11]
forced_pair = [2, 5]
forced_pair_path_rule = force_pair_path:0:12,13=separate_vehicle;1:2,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 20
source_alt_selection_reason = min_max_child_width
source_selected_fractionality = 0.4375
source_alt_fractionality = 0.3125
source_alt_required_tie_tolerance = 0.125
source_alt_pool_max_child_width = 341
source_alt_pool_total_child_width = 650
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/009_candidate_alt_d1_n2_r20_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/009_candidate_alt_d1_n2_r20_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/009_candidate_alt_d1_n2_r20_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/009_candidate_alt_d1_n2_r20_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,13=separate_vehicle;1:2,5' --set journey_branch_candidate_log_top_n=100
```

### 010_candidate_alt_d1_n2_r67_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 152.257833
source_selected_pair = [6, 11]
forced_pair = [6, 15]
forced_pair_path_rule = force_pair_path:0:12,13=separate_vehicle;1:6,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 67
source_alt_selection_reason = balanced_child_width
source_selected_fractionality = 0.4375
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.3125
source_alt_pool_max_child_width = 354
source_alt_pool_total_child_width = 670
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/010_candidate_alt_d1_n2_r67_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/010_candidate_alt_d1_n2_r67_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/010_candidate_alt_d1_n2_r67_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/010_candidate_alt_d1_n2_r67_6_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,13=separate_vehicle;1:6,15' --set journey_branch_candidate_log_top_n=100
```

### 011_candidate_alt_d1_n2_r43_12_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 152.257833
source_selected_pair = [6, 11]
forced_pair = [12, 20]
forced_pair_path_rule = force_pair_path:0:12,13=separate_vehicle;1:12,20
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 43
source_alt_selection_reason = rank_diversity
source_selected_fractionality = 0.4375
source_alt_fractionality = 0.3125
source_alt_required_tie_tolerance = 0.125
source_alt_pool_max_child_width = 370
source_alt_pool_total_child_width = 627
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/011_candidate_alt_d1_n2_r43_12_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/011_candidate_alt_d1_n2_r43_12_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/011_candidate_alt_d1_n2_r43_12_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/011_candidate_alt_d1_n2_r43_12_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,13=separate_vehicle;1:12,20' --set journey_branch_candidate_log_top_n=100
```

### 012_candidate_alt_d1_n2_r10_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
source_node_id = 2
source_depth = 1
source_event_time = 152.257833
source_selected_pair = [6, 11]
forced_pair = [3, 16]
forced_pair_path_rule = force_pair_path:0:12,13=separate_vehicle;1:3,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 10
source_alt_selection_reason = legacy_fill
source_selected_fractionality = 0.4375
source_alt_fractionality = 0.375
source_alt_required_tie_tolerance = 0.0625
source_alt_pool_max_child_width = 343
source_alt_pool_total_child_width = 606
source_alt_branch_score = None
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/012_candidate_alt_d1_n2_r10_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/012_candidate_alt_d1_n2_r10_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/012_candidate_alt_d1_n2_r10_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v200_sector_tranquillitatis_seed61308_layered_20260624/runs/012_candidate_alt_d1_n2_r10_3_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:12,13=separate_vehicle;1:3,16' --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
