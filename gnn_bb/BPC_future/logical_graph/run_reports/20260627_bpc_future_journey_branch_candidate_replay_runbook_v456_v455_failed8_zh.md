# Journey Branch Candidate Replay Runbook

日期：2026-06-27

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627
entry_count = 32
candidate_event_count_seen = 175
candidate_event_count_with_replay_entries = 8
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = both
candidate_selection = positive_neighbor
candidate_log_top_n = 200
min_source_depth = 0
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
focus_strong_positive_pair_count = 0
focus_strong_positive_pair_available_count = 0
focus_strong_positive_pair_missing_count = 0
focus_strong_positive_entry_count = 0
coverage_priority_context_count = 0
coverage_gap_skip_count = 0
depth_filter_skip_count = 167
source_event_time_filter_skip_count = 0
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r27_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.210651
source_selected_pair = [1, 2]
forced_pair = [4, 16]
forced_pair_path_rule = force_pair_path:0:4,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 27
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.104888886
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 399
source_alt_pool_total_child_width = 743
source_alt_branch_score = 0.543834847
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/001_candidate_alt_d0_n0_r27_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/001_candidate_alt_d0_n0_r27_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/001_candidate_alt_d0_n0_r27_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/001_candidate_alt_d0_n0_r27_4_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,16 --set journey_branch_candidate_log_top_n=200
```

### 002_candidate_alt_d0_n0_r21_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.210651
source_selected_pair = [1, 2]
forced_pair = [12, 15]
forced_pair_path_rule = force_pair_path:0:12,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 21
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.107555553
source_selected_fractionality = 0.5
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.166666667
source_alt_pool_max_child_width = 400
source_alt_pool_total_child_width = 743
source_alt_branch_score = 0.526183945
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/002_candidate_alt_d0_n0_r21_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/002_candidate_alt_d0_n0_r21_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/002_candidate_alt_d0_n0_r21_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/002_candidate_alt_d0_n0_r21_12_15_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,15 --set journey_branch_candidate_log_top_n=200
```

### 003_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.210651
source_selected_pair = [1, 2]
forced_pair = [1, 5]
forced_pair_path_rule = force_pair_path:0:1,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 4.014888889
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 368
source_alt_pool_total_child_width = 593
source_alt_branch_score = 0.455862227
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/003_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/003_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/003_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/003_candidate_alt_d0_n0_r1_1_5_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,5 --set journey_branch_candidate_log_top_n=200
```

### 004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 49.210651
source_selected_pair = [1, 2]
forced_pair = [1, 10]
forced_pair_path_rule = force_pair_path:0:1,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.892
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 612
source_alt_branch_score = 0.463119128
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/004_candidate_alt_d0_n0_r2_1_10_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,10 --set journey_branch_candidate_log_top_n=200
```

### 005_candidate_alt_d0_n0_r34_8_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.86269
source_selected_pair = [10, 15]
forced_pair = [8, 14]
forced_pair_path_rule = force_pair_path:0:8,14
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 34
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 0.674484851
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.272727273
source_alt_required_tie_tolerance = 0.181818182
source_alt_pool_max_child_width = 326
source_alt_pool_total_child_width = 618
source_alt_branch_score = 0.466352355
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/005_candidate_alt_d0_n0_r34_8_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/005_candidate_alt_d0_n0_r34_8_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/005_candidate_alt_d0_n0_r34_8_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/005_candidate_alt_d0_n0_r34_8_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,14 --set journey_branch_candidate_log_top_n=200
```

### 006_candidate_alt_d0_n0_r41_17_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.86269
source_selected_pair = [10, 15]
forced_pair = [17, 18]
forced_pair_path_rule = force_pair_path:0:17,18
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 41
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 0.677595962
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.272727273
source_alt_required_tie_tolerance = 0.181818182
source_alt_pool_max_child_width = 327
source_alt_pool_total_child_width = 619
source_alt_branch_score = 0.503649276
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/006_candidate_alt_d0_n0_r41_17_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/006_candidate_alt_d0_n0_r41_17_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/006_candidate_alt_d0_n0_r41_17_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/006_candidate_alt_d0_n0_r41_17_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:17,18 --set journey_branch_candidate_log_top_n=200
```

### 007_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.86269
source_selected_pair = [10, 15]
forced_pair = [15, 19]
forced_pair_path_rule = force_pair_path:0:15,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.418888889
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.454545455
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 331
source_alt_pool_total_child_width = 629
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/007_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/007_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/007_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/007_candidate_alt_d0_n0_r1_15_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:15,19 --set journey_branch_candidate_log_top_n=200
```

### 008_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 48.86269
source_selected_pair = [10, 15]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.874
source_selected_fractionality = 0.454545455
source_alt_fractionality = 0.363636364
source_alt_required_tie_tolerance = 0.090909091
source_alt_pool_max_child_width = 320
source_alt_pool_total_child_width = 558
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/008_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/008_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/008_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/008_candidate_alt_d0_n0_r2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=200
```

### 009_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 47.441024
source_selected_pair = [5, 9]
forced_pair = [2, 16]
forced_pair_path_rule = force_pair_path:0:2,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 67
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.28622222
source_selected_fractionality = 0.5
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.333333333
source_alt_pool_max_child_width = 420
source_alt_pool_total_child_width = 817
source_alt_branch_score = 0.581625938
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/009_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/009_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/009_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/009_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,16 --set journey_branch_candidate_log_top_n=200
```

### 010_candidate_alt_d0_n0_r55_7_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 47.441024
source_selected_pair = [5, 9]
forced_pair = [7, 18]
forced_pair_path_rule = force_pair_path:0:7,18
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 55
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.309555556
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 423
source_alt_pool_total_child_width = 719
source_alt_branch_score = 0.533993566
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/010_candidate_alt_d0_n0_r55_7_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/010_candidate_alt_d0_n0_r55_7_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/010_candidate_alt_d0_n0_r55_7_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/010_candidate_alt_d0_n0_r55_7_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,18 --set journey_branch_candidate_log_top_n=200
```

### 011_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 47.441024
source_selected_pair = [5, 9]
forced_pair = [3, 5]
forced_pair_path_rule = force_pair_path:0:3,5
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.501555556
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 427
source_alt_pool_total_child_width = 749
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/011_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/011_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/011_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/011_candidate_alt_d0_n0_r1_3_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,5 --set journey_branch_candidate_log_top_n=200
```

### 012_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 47.441024
source_selected_pair = [5, 9]
forced_pair = [3, 9]
forced_pair_path_rule = force_pair_path:0:3,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.238666667
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 421
source_alt_pool_total_child_width = 768
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/012_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/012_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/012_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/012_candidate_alt_d0_n0_r2_3_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,9 --set journey_branch_candidate_log_top_n=200
```

### 013_candidate_alt_d0_n0_r17_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.822234
source_selected_pair = [4, 7]
forced_pair = [11, 15]
forced_pair_path_rule = force_pair_path:0:11,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 17
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 0.328666667
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 336
source_alt_pool_total_child_width = 621
source_alt_branch_score = 0.564443743
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/013_candidate_alt_d0_n0_r17_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/013_candidate_alt_d0_n0_r17_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/013_candidate_alt_d0_n0_r17_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/013_candidate_alt_d0_n0_r17_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:11,15 --set journey_branch_candidate_log_top_n=200
```

### 014_candidate_alt_d0_n0_r14_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.822234
source_selected_pair = [4, 7]
forced_pair = [6, 15]
forced_pair_path_rule = force_pair_path:0:6,15
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 14
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.420444444
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 336
source_alt_pool_total_child_width = 610
source_alt_branch_score = 0.549921042
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/014_candidate_alt_d0_n0_r14_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/014_candidate_alt_d0_n0_r14_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/014_candidate_alt_d0_n0_r14_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/014_candidate_alt_d0_n0_r14_6_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,15 --set journey_branch_candidate_log_top_n=200
```

### 015_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.822234
source_selected_pair = [4, 7]
forced_pair = [4, 8]
forced_pair_path_rule = force_pair_path:0:4,8
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.291333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 332
source_alt_pool_total_child_width = 615
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/015_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/015_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/015_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/015_candidate_alt_d0_n0_r1_4_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,8 --set journey_branch_candidate_log_top_n=200
```

### 016_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 21.822234
source_selected_pair = [4, 7]
forced_pair = [4, 9]
forced_pair_path_rule = force_pair_path:0:4,9
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.599555556
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 325
source_alt_pool_total_child_width = 569
source_alt_branch_score = 0.508389562
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/016_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/016_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/016_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/016_candidate_alt_d0_n0_r2_4_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,9 --set journey_branch_candidate_log_top_n=200
```

### 017_candidate_alt_d0_n0_r48_9_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 110.19212
source_selected_pair = [1, 4]
forced_pair = [9, 12]
forced_pair_path_rule = force_pair_path:0:9,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 48
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.430666667
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 639
source_alt_pool_total_child_width = 1143
source_alt_branch_score = 0.511681187
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/017_candidate_alt_d0_n0_r48_9_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/017_candidate_alt_d0_n0_r48_9_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/017_candidate_alt_d0_n0_r48_9_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/017_candidate_alt_d0_n0_r48_9_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,12 --set journey_branch_candidate_log_top_n=200
```

### 018_candidate_alt_d0_n0_r44_5_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 110.19212
source_selected_pair = [1, 4]
forced_pair = [5, 12]
forced_pair_path_rule = force_pair_path:0:5,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 44
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.130222222
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 650
source_alt_pool_total_child_width = 1207
source_alt_branch_score = 0.536845422
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/018_candidate_alt_d0_n0_r44_5_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/018_candidate_alt_d0_n0_r44_5_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/018_candidate_alt_d0_n0_r44_5_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/018_candidate_alt_d0_n0_r44_5_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,12 --set journey_branch_candidate_log_top_n=200
```

### 019_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 110.19212
source_selected_pair = [1, 4]
forced_pair = [1, 6]
forced_pair_path_rule = force_pair_path:0:1,6
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 4.963111111
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 630
source_alt_pool_total_child_width = 1073
source_alt_branch_score = 0.409717044
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/019_candidate_alt_d0_n0_r1_1_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,6 --set journey_branch_candidate_log_top_n=200
```

### 020_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 110.19212
source_selected_pair = [1, 4]
forced_pair = [1, 19]
forced_pair_path_rule = force_pair_path:0:1,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.623333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 643
source_alt_pool_total_child_width = 1116
source_alt_branch_score = 0.423174506
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/020_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/020_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/020_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/020_candidate_alt_d0_n0_r2_1_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,19 --set journey_branch_candidate_log_top_n=200
```

### 021_candidate_alt_d0_n0_r13_7_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.605857
source_selected_pair = [8, 13]
forced_pair = [7, 19]
forced_pair_path_rule = force_pair_path:0:7,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 13
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 0.510444444
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 295
source_alt_pool_total_child_width = 532
source_alt_branch_score = 0.536010712
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/021_candidate_alt_d0_n0_r13_7_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/021_candidate_alt_d0_n0_r13_7_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/021_candidate_alt_d0_n0_r13_7_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/021_candidate_alt_d0_n0_r13_7_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,19 --set journey_branch_candidate_log_top_n=200
```

### 022_candidate_alt_d0_n0_r12_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.605857
source_selected_pair = [8, 13]
forced_pair = [5, 19]
forced_pair_path_rule = force_pair_path:0:5,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 12
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 0.612888889
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 290
source_alt_pool_total_child_width = 512
source_alt_branch_score = 0.525047719
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/022_candidate_alt_d0_n0_r12_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/022_candidate_alt_d0_n0_r12_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/022_candidate_alt_d0_n0_r12_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/022_candidate_alt_d0_n0_r12_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,19 --set journey_branch_candidate_log_top_n=200
```

### 023_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.605857
source_selected_pair = [8, 13]
forced_pair = [8, 16]
forced_pair_path_rule = force_pair_path:0:8,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.456222222
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 299
source_alt_pool_total_child_width = 557
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/023_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/023_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/023_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/023_candidate_alt_d0_n0_r1_8_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,16 --set journey_branch_candidate_log_top_n=200
```

### 024_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.605857
source_selected_pair = [8, 13]
forced_pair = [12, 17]
forced_pair_path_rule = force_pair_path:0:12,17
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.011333333
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 293
source_alt_pool_total_child_width = 498
source_alt_branch_score = 0.482116988
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/024_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/024_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/024_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/024_candidate_alt_d0_n0_r2_12_17_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,17 --set journey_branch_candidate_log_top_n=200
```

### 025_candidate_alt_d0_n0_r3_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.468896
source_selected_pair = [1, 9]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:2,10
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 3
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.236222222
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 356
source_alt_pool_total_child_width = 665
source_alt_branch_score = 0.498540699
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/025_candidate_alt_d0_n0_r3_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/025_candidate_alt_d0_n0_r3_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/025_candidate_alt_d0_n0_r3_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/025_candidate_alt_d0_n0_r3_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,10 --set journey_branch_candidate_log_top_n=200
```

### 026_candidate_alt_d0_n0_r9_4_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.468896
source_selected_pair = [1, 9]
forced_pair = [4, 12]
forced_pair_path_rule = force_pair_path:0:4,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 9
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 2.256
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 702
source_alt_branch_score = 0.519952285
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/026_candidate_alt_d0_n0_r9_4_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/026_candidate_alt_d0_n0_r9_4_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/026_candidate_alt_d0_n0_r9_4_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/026_candidate_alt_d0_n0_r9_4_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,12 --set journey_branch_candidate_log_top_n=200
```

### 027_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.468896
source_selected_pair = [1, 9]
forced_pair = [1, 12]
forced_pair_path_rule = force_pair_path:0:1,12
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 1
source_alt_selection_reason = highest_fractionality
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.262
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 370
source_alt_pool_total_child_width = 681
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/027_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/027_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/027_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/027_candidate_alt_d0_n0_r1_1_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,12 --set journey_branch_candidate_log_top_n=200
```

### 028_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 20.468896
source_selected_pair = [1, 9]
forced_pair = [2, 4]
forced_pair_path_rule = force_pair_path:0:2,4
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 2
source_alt_selection_reason = near_tie
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 3.198666667
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 371
source_alt_pool_total_child_width = 690
source_alt_branch_score = 0.05
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/028_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/028_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/028_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/028_candidate_alt_d0_n0_r2_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,4 --set journey_branch_candidate_log_top_n=200
```

### 029_candidate_alt_d0_n0_r20_12_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 22.995485
source_selected_pair = [5, 14]
forced_pair = [12, 16]
forced_pair_path_rule = force_pair_path:0:12,16
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 20
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.043999997
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 328
source_alt_pool_total_child_width = 603
source_alt_branch_score = 0.501750153
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/029_candidate_alt_d0_n0_r20_12_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/029_candidate_alt_d0_n0_r20_12_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/029_candidate_alt_d0_n0_r20_12_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/029_candidate_alt_d0_n0_r20_12_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:12,16 --set journey_branch_candidate_log_top_n=200
```

### 030_candidate_alt_d0_n0_r36_18_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
source_node_id = 0
source_depth = 0
source_event_time = 22.995485
source_selected_pair = [5, 14]
forced_pair = [18, 19]
forced_pair_path_rule = force_pair_path:0:18,19
probe_mode = full_replay
probe_max_nodes = None
probe_max_cg_iterations = None
source_alt_rank = 36
source_alt_selection_reason = positive_neighbor
source_alt_focus_strong_positive = None
source_alt_positive_neighbor_score = 1.462888886
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.166666667
source_alt_required_tie_tolerance = 0.166666666
source_alt_pool_max_child_width = 324
source_alt_pool_total_child_width = 581
source_alt_branch_score = 0.55901764
coverage_gap_priority = 0.0
coverage_gap_priority_reason = None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/030_candidate_alt_d0_n0_r36_18_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/030_candidate_alt_d0_n0_r36_18_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/030_candidate_alt_d0_n0_r36_18_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/runs/030_candidate_alt_d0_n0_r36_18_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:18,19 --set journey_branch_candidate_log_top_n=200
```

- Report truncated to first 30 entries; full runbook has 32 entries.

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
