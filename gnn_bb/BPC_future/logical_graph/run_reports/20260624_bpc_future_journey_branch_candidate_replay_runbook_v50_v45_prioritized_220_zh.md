# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624
entry_count = 12
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 3
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = priority_top
candidate_log_top_n = 100
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624']
branch_impact_priority_context_count = 29
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n2_r5_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [8, 12]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:8,12
source_alt_rank = 5
source_alt_pool_max_child_width = 150
source_alt_pool_total_child_width = 282
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/001_candidate_alt_d1_n2_r5_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/001_candidate_alt_d1_n2_r5_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/001_candidate_alt_d1_n2_r5_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/001_candidate_alt_d1_n2_r5_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:8,12' --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d1_n2_r6_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [8, 14]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:8,14
source_alt_rank = 6
source_alt_pool_max_child_width = 152
source_alt_pool_total_child_width = 268
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/002_candidate_alt_d1_n2_r6_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/002_candidate_alt_d1_n2_r6_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/002_candidate_alt_d1_n2_r6_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/002_candidate_alt_d1_n2_r6_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:8,14' --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d1_n2_r11_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [14, 18]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:14,18
source_alt_rank = 11
source_alt_pool_max_child_width = 152
source_alt_pool_total_child_width = 274
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/003_candidate_alt_d1_n2_r11_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/003_candidate_alt_d1_n2_r11_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/003_candidate_alt_d1_n2_r11_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/003_candidate_alt_d1_n2_r11_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:14,18' --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d1_n2_r7_8_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [8, 18]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:8,18
source_alt_rank = 7
source_alt_pool_max_child_width = 155
source_alt_pool_total_child_width = 282
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/004_candidate_alt_d1_n2_r7_8_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/004_candidate_alt_d1_n2_r7_8_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/004_candidate_alt_d1_n2_r7_8_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/004_candidate_alt_d1_n2_r7_8_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:8,18' --set journey_branch_candidate_log_top_n=100
```

### 005_candidate_alt_d0_n0_r22_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [7, 15]
forced_pair_path_rule = force_pair_path:0:7,15
source_alt_rank = 22
source_alt_pool_max_child_width = 344
source_alt_pool_total_child_width = 584
source_alt_branch_score = None
branch_impact_priority = 45.0
branch_impact_priority_reason = active_touch=1;completion_retries=12;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/005_candidate_alt_d0_n0_r22_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/005_candidate_alt_d0_n0_r22_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/005_candidate_alt_d0_n0_r22_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/005_candidate_alt_d0_n0_r22_7_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,15 --set journey_branch_candidate_log_top_n=100
```

### 006_candidate_alt_d0_n0_r13_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [2, 15]
forced_pair_path_rule = force_pair_path:0:2,15
source_alt_rank = 13
source_alt_pool_max_child_width = 344
source_alt_pool_total_child_width = 585
source_alt_branch_score = None
branch_impact_priority = 45.0
branch_impact_priority_reason = active_touch=1;completion_retries=12;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/006_candidate_alt_d0_n0_r13_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/006_candidate_alt_d0_n0_r13_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/006_candidate_alt_d0_n0_r13_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/006_candidate_alt_d0_n0_r13_2_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,15 --set journey_branch_candidate_log_top_n=100
```

### 007_candidate_alt_d0_n0_r28_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [6, 8]
forced_pair_path_rule = force_pair_path:0:6,8
source_alt_rank = 28
source_alt_pool_max_child_width = 348
source_alt_pool_total_child_width = 610
source_alt_branch_score = None
branch_impact_priority = 45.0
branch_impact_priority_reason = active_touch=1;completion_retries=12;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/007_candidate_alt_d0_n0_r28_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/007_candidate_alt_d0_n0_r28_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/007_candidate_alt_d0_n0_r28_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/007_candidate_alt_d0_n0_r28_6_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,8 --set journey_branch_candidate_log_top_n=100
```

### 008_candidate_alt_d0_n0_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [7, 11]
forced_pair_path_rule = force_pair_path:0:7,11
source_alt_rank = 21
source_alt_pool_max_child_width = 349
source_alt_pool_total_child_width = 625
source_alt_branch_score = None
branch_impact_priority = 45.0
branch_impact_priority_reason = active_touch=1;completion_retries=12;negative_events=8;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/008_candidate_alt_d0_n0_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/008_candidate_alt_d0_n0_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/008_candidate_alt_d0_n0_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/008_candidate_alt_d0_n0_r21_7_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,11 --set journey_branch_candidate_log_top_n=100
```

### 009_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 18]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:3,17
source_alt_rank = 35
source_alt_pool_max_child_width = 173
source_alt_pool_total_child_width = 299
source_alt_branch_score = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/009_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/009_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/009_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/009_candidate_alt_d0_n0_r35_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,17 --set journey_branch_candidate_log_top_n=100
```

### 010_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 18]
forced_pair = [10, 17]
forced_pair_path_rule = force_pair_path:0:10,17
source_alt_rank = 43
source_alt_pool_max_child_width = 174
source_alt_pool_total_child_width = 287
source_alt_branch_score = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/010_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/010_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/010_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/010_candidate_alt_d0_n0_r43_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,17 --set journey_branch_candidate_log_top_n=100
```

### 011_candidate_alt_d0_n0_r45_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 18]
forced_pair = [10, 20]
forced_pair_path_rule = force_pair_path:0:10,20
source_alt_rank = 45
source_alt_pool_max_child_width = 175
source_alt_pool_total_child_width = 295
source_alt_branch_score = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/011_candidate_alt_d0_n0_r45_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/011_candidate_alt_d0_n0_r45_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/011_candidate_alt_d0_n0_r45_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/011_candidate_alt_d0_n0_r45_10_20_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,20 --set journey_branch_candidate_log_top_n=100
```

### 012_candidate_alt_d0_n0_r32_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [8, 18]
forced_pair = [2, 13]
forced_pair_path_rule = force_pair_path:0:2,13
source_alt_rank = 32
source_alt_pool_max_child_width = 175
source_alt_pool_total_child_width = 305
source_alt_branch_score = None
branch_impact_priority = 42.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/012_candidate_alt_d0_n0_r32_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/012_candidate_alt_d0_n0_r32_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/012_candidate_alt_d0_n0_r32_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs/012_candidate_alt_d0_n0_r32_2_13_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,13 --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
