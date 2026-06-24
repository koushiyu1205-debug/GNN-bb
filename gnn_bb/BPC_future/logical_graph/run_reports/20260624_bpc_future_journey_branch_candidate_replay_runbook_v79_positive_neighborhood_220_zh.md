# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624
entry_count = 4
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 1
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = priority_top
candidate_log_top_n = 100
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624']
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624']
excluded_entry_key_count = 24
excluded_entry_skip_count = 4
branch_impact_priority_context_count = 29
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [5, 12]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:5,12
source_alt_rank = 2
source_alt_pool_max_child_width = 155
source_alt_pool_total_child_width = 284
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/001_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/001_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/001_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/001_candidate_alt_d1_n2_r2_5_12_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,12' --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d1_n2_r3_5_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [5, 14]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:5,14
source_alt_rank = 3
source_alt_pool_max_child_width = 156
source_alt_pool_total_child_width = 271
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/002_candidate_alt_d1_n2_r3_5_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/002_candidate_alt_d1_n2_r3_5_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/002_candidate_alt_d1_n2_r3_5_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/002_candidate_alt_d1_n2_r3_5_14_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,14' --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d1_n2_r4_5_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [5, 18]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:5,18
source_alt_rank = 4
source_alt_pool_max_child_width = 156
source_alt_pool_total_child_width = 288
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/003_candidate_alt_d1_n2_r4_5_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/003_candidate_alt_d1_n2_r4_5_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/003_candidate_alt_d1_n2_r4_5_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/003_candidate_alt_d1_n2_r4_5_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,18' --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d1_n2_r9_12_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [5, 8]
forced_pair = [12, 18]
forced_pair_path_rule = force_pair_path:0:2,3=separate_vehicle;1:12,18
source_alt_rank = 9
source_alt_pool_max_child_width = 157
source_alt_pool_total_child_width = 281
source_alt_branch_score = None
branch_impact_priority = 46.0
branch_impact_priority_reason = active_touch=1;completion_retries=8;negative_events=17;tail_class=completion_bound_tail;right_censored=True
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/004_candidate_alt_d1_n2_r9_12_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/004_candidate_alt_d1_n2_r9_12_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/004_candidate_alt_d1_n2_r9_12_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v79_v45_positive_neighborhood_excluding_v50_v72_220_20260624/runs/004_candidate_alt_d1_n2_r9_12_18_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:12,18' --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
