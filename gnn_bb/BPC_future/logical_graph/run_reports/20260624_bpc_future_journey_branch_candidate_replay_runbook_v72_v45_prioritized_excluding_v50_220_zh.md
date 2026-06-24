# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624
entry_count = 12
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 3
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = priority_top
candidate_log_top_n = 100
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624']
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624']
excluded_entry_key_count = 12
excluded_entry_skip_count = 12
branch_impact_priority_context_count = 29
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n2_r24_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [10, 17]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:10,17
source_alt_rank = 24
source_alt_pool_max_child_width = 187
source_alt_pool_total_child_width = 309
source_alt_branch_score = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=4;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/001_candidate_alt_d1_n2_r24_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/001_candidate_alt_d1_n2_r24_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/001_candidate_alt_d1_n2_r24_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/001_candidate_alt_d1_n2_r24_10_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:10,17' --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d1_n2_r6_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [3, 17]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:3,17
source_alt_rank = 6
source_alt_pool_max_child_width = 191
source_alt_pool_total_child_width = 319
source_alt_branch_score = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=4;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/002_candidate_alt_d1_n2_r6_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/002_candidate_alt_d1_n2_r6_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/002_candidate_alt_d1_n2_r6_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/002_candidate_alt_d1_n2_r6_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:3,17' --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d1_n2_r34_13_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [13, 17]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:13,17
source_alt_rank = 34
source_alt_pool_max_child_width = 192
source_alt_pool_total_child_width = 316
source_alt_branch_score = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=4;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/003_candidate_alt_d1_n2_r34_13_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/003_candidate_alt_d1_n2_r34_13_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/003_candidate_alt_d1_n2_r34_13_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/003_candidate_alt_d1_n2_r34_13_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:13,17' --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d1_n2_r28_11_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [2, 3]
forced_pair = [11, 17]
forced_pair_path_rule = force_pair_path:0:8,18=separate_vehicle;1:11,17
source_alt_rank = 28
source_alt_pool_max_child_width = 192
source_alt_pool_total_child_width = 340
source_alt_branch_score = None
branch_impact_priority = 40.0
branch_impact_priority_reason = active_touch=1;completion_retries=4;negative_events=19;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/004_candidate_alt_d1_n2_r28_11_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/004_candidate_alt_d1_n2_r28_11_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/004_candidate_alt_d1_n2_r28_11_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/004_candidate_alt_d1_n2_r28_11_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:8,18=separate_vehicle;1:11,17' --set journey_branch_candidate_log_top_n=100
```

### 005_candidate_alt_d0_n0_r32_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 3]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:5,8
source_alt_rank = 32
source_alt_pool_max_child_width = 122
source_alt_pool_total_child_width = 240
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/005_candidate_alt_d0_n0_r32_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/005_candidate_alt_d0_n0_r32_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/005_candidate_alt_d0_n0_r32_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/005_candidate_alt_d0_n0_r32_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,8 --set journey_branch_candidate_log_top_n=100
```

### 006_candidate_alt_d0_n0_r19_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 3]
forced_pair = [8, 12]
forced_pair_path_rule = force_pair_path:0:8,12
source_alt_rank = 19
source_alt_pool_max_child_width = 123
source_alt_pool_total_child_width = 237
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/006_candidate_alt_d0_n0_r19_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/006_candidate_alt_d0_n0_r19_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/006_candidate_alt_d0_n0_r19_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/006_candidate_alt_d0_n0_r19_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,12 --set journey_branch_candidate_log_top_n=100
```

### 007_candidate_alt_d0_n0_r34_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 3]
forced_pair = [8, 14]
forced_pair_path_rule = force_pair_path:0:8,14
source_alt_rank = 34
source_alt_pool_max_child_width = 125
source_alt_pool_total_child_width = 228
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/007_candidate_alt_d0_n0_r34_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/007_candidate_alt_d0_n0_r34_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/007_candidate_alt_d0_n0_r34_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/007_candidate_alt_d0_n0_r34_8_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:8,14 --set journey_branch_candidate_log_top_n=100
```

### 008_candidate_alt_d0_n0_r6_3_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 3]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,10
source_alt_rank = 6
source_alt_pool_max_child_width = 126
source_alt_pool_total_child_width = 228
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/008_candidate_alt_d0_n0_r6_3_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/008_candidate_alt_d0_n0_r6_3_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/008_candidate_alt_d0_n0_r6_3_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/008_candidate_alt_d0_n0_r6_3_10_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,10 --set journey_branch_candidate_log_top_n=100
```

### 009_candidate_alt_d1_n1_r7_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [4, 11]
forced_pair = [8, 12]
forced_pair_path_rule = force_pair_path:0:2,3=same_vehicle;1:8,12
source_alt_rank = 7
source_alt_pool_max_child_width = 100
source_alt_pool_total_child_width = 191
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/009_candidate_alt_d1_n1_r7_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/009_candidate_alt_d1_n1_r7_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/009_candidate_alt_d1_n1_r7_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/009_candidate_alt_d1_n1_r7_8_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=same_vehicle;1:8,12' --set journey_branch_candidate_log_top_n=100
```

### 010_candidate_alt_d1_n1_r16_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [4, 11]
forced_pair = [14, 18]
forced_pair_path_rule = force_pair_path:0:2,3=same_vehicle;1:14,18
source_alt_rank = 16
source_alt_pool_max_child_width = 103
source_alt_pool_total_child_width = 189
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/010_candidate_alt_d1_n1_r16_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/010_candidate_alt_d1_n1_r16_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/010_candidate_alt_d1_n1_r16_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/010_candidate_alt_d1_n1_r16_14_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=same_vehicle;1:14,18' --set journey_branch_candidate_log_top_n=100
```

### 011_candidate_alt_d1_n1_r13_12_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [4, 11]
forced_pair = [12, 14]
forced_pair_path_rule = force_pair_path:0:2,3=same_vehicle;1:12,14
source_alt_rank = 13
source_alt_pool_max_child_width = 104
source_alt_pool_total_child_width = 183
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/011_candidate_alt_d1_n1_r13_12_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/011_candidate_alt_d1_n1_r13_12_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/011_candidate_alt_d1_n1_r13_12_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/011_candidate_alt_d1_n1_r13_12_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=same_vehicle;1:12,14' --set journey_branch_candidate_log_top_n=100
```

### 012_candidate_alt_d1_n1_r5_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [4, 11]
forced_pair = [5, 12]
forced_pair_path_rule = force_pair_path:0:2,3=same_vehicle;1:5,12
source_alt_rank = 5
source_alt_pool_max_child_width = 104
source_alt_pool_total_child_width = 188
source_alt_branch_score = None
branch_impact_priority = 24.0
branch_impact_priority_reason = active_touch=0;completion_retries=4;negative_events=13;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/012_candidate_alt_d1_n1_r5_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/012_candidate_alt_d1_n1_r5_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/012_candidate_alt_d1_n1_r5_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624/runs/012_candidate_alt_d1_n1_r5_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=same_vehicle;1:5,12' --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
