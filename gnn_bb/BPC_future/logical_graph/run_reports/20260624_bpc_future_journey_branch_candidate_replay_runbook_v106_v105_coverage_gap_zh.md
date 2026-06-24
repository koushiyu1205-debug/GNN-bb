# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624
entry_count = 24
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 12
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 2
candidate_source = priority_top
candidate_log_top_n = 100
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v44_top100_balanced6_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v80_v58_positive_context_next4_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624']
focus_delta_input_paths = []
coverage_input_paths = ['BPC_future/results/journey_branch_score_candidate_coverage_v105_v95_on_v44_horizon02_required_tol_20260624']
coverage_gap_only = True
excluded_entry_key_count = 80
excluded_entry_skip_count = 48
focus_context_count = 0
focus_event_skip_count = 0
coverage_priority_context_count = 29
coverage_gap_skip_count = 2
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n1_r7_6_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [8, 12]
forced_pair = [6, 12]
forced_pair_path_rule = force_pair_path:0:2,18=same_vehicle;1:6,12
source_alt_rank = 7
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 285
source_alt_pool_total_child_width = 485
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/001_candidate_alt_d1_n1_r7_6_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/001_candidate_alt_d1_n1_r7_6_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/001_candidate_alt_d1_n1_r7_6_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/001_candidate_alt_d1_n1_r7_6_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=same_vehicle;1:6,12' --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d1_n1_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [8, 12]
forced_pair = [6, 16]
forced_pair_path_rule = force_pair_path:0:2,18=same_vehicle;1:6,16
source_alt_rank = 18
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 285
source_alt_pool_total_child_width = 489
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/002_candidate_alt_d1_n1_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/002_candidate_alt_d1_n1_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/002_candidate_alt_d1_n1_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/002_candidate_alt_d1_n1_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=same_vehicle;1:6,16' --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d1_n2_r29_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [1, 6]
forced_pair = [2, 15]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:2,15
source_alt_rank = 29
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 362
source_alt_pool_total_child_width = 617
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/003_candidate_alt_d1_n2_r29_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/003_candidate_alt_d1_n2_r29_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/003_candidate_alt_d1_n2_r29_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/003_candidate_alt_d1_n2_r29_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:2,15' --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d1_n2_r25_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [1, 6]
forced_pair = [6, 8]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:6,8
source_alt_rank = 25
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 363
source_alt_pool_total_child_width = 635
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/004_candidate_alt_d1_n2_r25_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/004_candidate_alt_d1_n2_r25_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/004_candidate_alt_d1_n2_r25_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/004_candidate_alt_d1_n2_r25_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:6,8' --set journey_branch_candidate_log_top_n=100
```

### 005_candidate_alt_d2_n6_r26_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 6
source_depth = 2
source_selected_pair = [1, 10]
forced_pair = [2, 15]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:2,15
source_alt_rank = 26
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 355
source_alt_pool_total_child_width = 603
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/005_candidate_alt_d2_n6_r26_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/005_candidate_alt_d2_n6_r26_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/005_candidate_alt_d2_n6_r26_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/005_candidate_alt_d2_n6_r26_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:2,15' --set journey_branch_candidate_log_top_n=100
```

### 006_candidate_alt_d2_n6_r5_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 6
source_depth = 2
source_selected_pair = [1, 10]
forced_pair = [2, 9]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:2,9
source_alt_rank = 5
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 356
source_alt_pool_total_child_width = 655
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/006_candidate_alt_d2_n6_r5_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/006_candidate_alt_d2_n6_r5_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/006_candidate_alt_d2_n6_r5_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/006_candidate_alt_d2_n6_r5_2_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:2,9' --set journey_branch_candidate_log_top_n=100
```

### 007_candidate_alt_d3_n7_r24_9_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 7
source_depth = 3
source_selected_pair = [8, 12]
forced_pair = [9, 15]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=same_vehicle;3:9,15
source_alt_rank = 24
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 271
source_alt_pool_total_child_width = 455
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/007_candidate_alt_d3_n7_r24_9_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/007_candidate_alt_d3_n7_r24_9_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/007_candidate_alt_d3_n7_r24_9_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/007_candidate_alt_d3_n7_r24_9_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=same_vehicle;3:9,15' --set journey_branch_candidate_log_top_n=100
```

### 008_candidate_alt_d3_n7_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 7
source_depth = 3
source_selected_pair = [8, 12]
forced_pair = [7, 11]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=same_vehicle;3:7,11
source_alt_rank = 21
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 272
source_alt_pool_total_child_width = 487
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/008_candidate_alt_d3_n7_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/008_candidate_alt_d3_n7_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/008_candidate_alt_d3_n7_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/008_candidate_alt_d3_n7_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=same_vehicle;3:7,11' --set journey_branch_candidate_log_top_n=100
```

### 009_candidate_alt_d3_n8_r1_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 8
source_depth = 3
source_selected_pair = [6, 8]
forced_pair = [6, 13]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=separate_vehicle;3:6,13
source_alt_rank = 1
source_selected_fractionality = 0.4
source_alt_fractionality = 0.4
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 358
source_alt_pool_total_child_width = 620
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/009_candidate_alt_d3_n8_r1_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/009_candidate_alt_d3_n8_r1_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/009_candidate_alt_d3_n8_r1_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/009_candidate_alt_d3_n8_r1_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=separate_vehicle;3:6,13' --set journey_branch_candidate_log_top_n=100
```

### 010_candidate_alt_d3_n8_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 8
source_depth = 3
source_selected_pair = [6, 8]
forced_pair = [6, 16]
forced_pair_path_rule = force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=separate_vehicle;3:6,16
source_alt_rank = 18
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 358
source_alt_pool_total_child_width = 632
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/010_candidate_alt_d3_n8_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/010_candidate_alt_d3_n8_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/010_candidate_alt_d3_n8_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/010_candidate_alt_d3_n8_r18_6_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,18=separate_vehicle;1:1,6=separate_vehicle;2:1,10=separate_vehicle;3:6,16' --set journey_branch_candidate_log_top_n=100
```

### 011_candidate_alt_d0_n0_r30_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 18]
forced_pair = [2, 10]
forced_pair_path_rule = force_pair_path:0:2,10
source_alt_rank = 30
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 176
source_alt_pool_total_child_width = 293
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/011_candidate_alt_d0_n0_r30_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/011_candidate_alt_d0_n0_r30_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/011_candidate_alt_d0_n0_r30_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/011_candidate_alt_d0_n0_r30_2_10_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,10 --set journey_branch_candidate_log_top_n=100
```

### 012_candidate_alt_d0_n0_r44_10_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 18]
forced_pair = [10, 18]
forced_pair_path_rule = force_pair_path:0:10,18
source_alt_rank = 44
source_selected_fractionality = 0.5
source_alt_fractionality = 0.125
source_alt_required_tie_tolerance = 0.375
source_alt_pool_max_child_width = 177
source_alt_pool_total_child_width = 285
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/012_candidate_alt_d0_n0_r44_10_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/012_candidate_alt_d0_n0_r44_10_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/012_candidate_alt_d0_n0_r44_10_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/012_candidate_alt_d0_n0_r44_10_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,18 --set journey_branch_candidate_log_top_n=100
```

### 013_candidate_alt_d1_n1_r23_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [11, 12]
forced_pair = [10, 20]
forced_pair_path_rule = force_pair_path:0:8,18=same_vehicle;1:10,20
source_alt_rank = 23
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 150
source_alt_pool_total_child_width = 248
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/013_candidate_alt_d1_n1_r23_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/013_candidate_alt_d1_n1_r23_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/013_candidate_alt_d1_n1_r23_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/013_candidate_alt_d1_n1_r23_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=same_vehicle;1:10,20' --set journey_branch_candidate_log_top_n=100
```

### 014_candidate_alt_d1_n1_r16_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [11, 12]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:8,18=same_vehicle;1:3,17
source_alt_rank = 16
source_selected_fractionality = 0.4
source_alt_fractionality = 0.2
source_alt_required_tie_tolerance = 0.2
source_alt_pool_max_child_width = 151
source_alt_pool_total_child_width = 249
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/014_candidate_alt_d1_n1_r16_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/014_candidate_alt_d1_n1_r16_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/014_candidate_alt_d1_n1_r16_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/014_candidate_alt_d1_n1_r16_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=same_vehicle;1:3,17' --set journey_branch_candidate_log_top_n=100
```

### 015_candidate_alt_d1_n2_r26_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [10, 20]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:10,20
source_alt_rank = 26
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 194
source_alt_pool_total_child_width = 326
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/015_candidate_alt_d1_n2_r26_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/015_candidate_alt_d1_n2_r26_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/015_candidate_alt_d1_n2_r26_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/015_candidate_alt_d1_n2_r26_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:10,20' --set journey_branch_candidate_log_top_n=100
```

### 016_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,13
source_alt_rank = 3
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 194
source_alt_pool_total_child_width = 337
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/016_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/016_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/016_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/016_candidate_alt_d1_n2_r3_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,13' --set journey_branch_candidate_log_top_n=100
```

### 017_candidate_alt_d2_n5_r36_16_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 5
source_depth = 2
source_selected_pair = [16, 18]
forced_pair = [16, 17]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,3=same_vehicle;2:16,17
source_alt_rank = 36
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 143
source_alt_pool_total_child_width = 256
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/017_candidate_alt_d2_n5_r36_16_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/017_candidate_alt_d2_n5_r36_16_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/017_candidate_alt_d2_n5_r36_16_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/017_candidate_alt_d2_n5_r36_16_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,3=same_vehicle;2:16,17' --set journey_branch_candidate_log_top_n=100
```

### 018_candidate_alt_d2_n5_r19_10_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 5
source_depth = 2
source_selected_pair = [16, 18]
forced_pair = [10, 11]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:2,3=same_vehicle;2:10,11
source_alt_rank = 19
source_selected_fractionality = 0.333333333
source_alt_fractionality = 0.333333333
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 144
source_alt_pool_total_child_width = 240
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/018_candidate_alt_d2_n5_r19_10_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/018_candidate_alt_d2_n5_r19_10_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/018_candidate_alt_d2_n5_r19_10_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/018_candidate_alt_d2_n5_r19_10_11_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:2,3=same_vehicle;2:10,11' --set journey_branch_candidate_log_top_n=100
```

### 019_candidate_alt_d0_n0_r9_5_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 13]
forced_pair = [5, 7]
forced_pair_path_rule = force_pair_path:0:5,7
source_alt_rank = 9
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 291
source_alt_pool_total_child_width = 501
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/019_candidate_alt_d0_n0_r9_5_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/019_candidate_alt_d0_n0_r9_5_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/019_candidate_alt_d0_n0_r9_5_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/019_candidate_alt_d0_n0_r9_5_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,7 --set journey_branch_candidate_log_top_n=100
```

### 020_candidate_alt_d0_n0_r11_5_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 13]
forced_pair = [5, 18]
forced_pair_path_rule = force_pair_path:0:5,18
source_alt_rank = 11
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 292
source_alt_pool_total_child_width = 511
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/020_candidate_alt_d0_n0_r11_5_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/020_candidate_alt_d0_n0_r11_5_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/020_candidate_alt_d0_n0_r11_5_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/020_candidate_alt_d0_n0_r11_5_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,18 --set journey_branch_candidate_log_top_n=100
```

### 021_candidate_alt_d1_n1_r12_10_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [3, 7]
forced_pair = [10, 18]
forced_pair_path_rule = force_pair_path:0:8,13=same_vehicle;1:10,18
source_alt_rank = 12
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 232
source_alt_pool_total_child_width = 424
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/021_candidate_alt_d1_n1_r12_10_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/021_candidate_alt_d1_n1_r12_10_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/021_candidate_alt_d1_n1_r12_10_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/021_candidate_alt_d1_n1_r12_10_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,13=same_vehicle;1:10,18' --set journey_branch_candidate_log_top_n=100
```

### 022_candidate_alt_d1_n1_r5_5_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [3, 7]
forced_pair = [5, 10]
forced_pair_path_rule = force_pair_path:0:8,13=same_vehicle;1:5,10
source_alt_rank = 5
source_selected_fractionality = 0.5
source_alt_fractionality = 0.5
source_alt_required_tie_tolerance = 0.0
source_alt_pool_max_child_width = 233
source_alt_pool_total_child_width = 395
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/022_candidate_alt_d1_n1_r5_5_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/022_candidate_alt_d1_n1_r5_5_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/022_candidate_alt_d1_n1_r5_5_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/022_candidate_alt_d1_n1_r5_5_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,13=same_vehicle;1:5,10' --set journey_branch_candidate_log_top_n=100
```

### 023_candidate_alt_d1_n2_r17_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 5]
forced_pair = [5, 19]
forced_pair_path_rule = force_pair_path:0:8,13=separate_vehicle;1:5,19
source_alt_rank = 17
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 288
source_alt_pool_total_child_width = 508
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/023_candidate_alt_d1_n2_r17_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/023_candidate_alt_d1_n2_r17_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/023_candidate_alt_d1_n2_r17_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/023_candidate_alt_d1_n2_r17_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,13=separate_vehicle;1:5,19' --set journey_branch_candidate_log_top_n=100
```

### 024_candidate_alt_d1_n2_r8_2_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 5]
forced_pair = [2, 7]
forced_pair_path_rule = force_pair_path:0:8,13=separate_vehicle;1:2,7
source_alt_rank = 8
source_selected_fractionality = 0.5
source_alt_fractionality = 0.25
source_alt_required_tie_tolerance = 0.25
source_alt_pool_max_child_width = 289
source_alt_pool_total_child_width = 506
source_alt_branch_score = None
coverage_gap_priority = 108.0
coverage_gap_priority_reason = scored=0;eligible_scored=0;selected_unscored=True;full_logged=True;would_change=False;would_change_any=False;required_tie_tolerance=None
coverage_best_scored_pair = None
coverage_best_scored_required_tie_tolerance = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/024_candidate_alt_d1_n2_r8_2_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/024_candidate_alt_d1_n2_r8_2_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/024_candidate_alt_d1_n2_r8_2_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs/024_candidate_alt_d1_n2_r8_2_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,13=separate_vehicle;1:2,7' --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
