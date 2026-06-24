# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624
entry_count = 4
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 1
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = priority_top
candidate_log_top_n = 100
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r1_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 7]
forced_pair = [3, 10]
forced_pair_path_rule = force_pair_path:0:3,10
source_alt_rank = 1
source_alt_pool_max_child_width = 229
source_alt_pool_total_child_width = 384
source_alt_branch_score = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/001_candidate_alt_d0_n0_r1_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/001_candidate_alt_d0_n0_r1_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/001_candidate_alt_d0_n0_r1_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/001_candidate_alt_d0_n0_r1_3_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,10 --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d0_n0_r44_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 7]
forced_pair = [10, 13]
forced_pair_path_rule = force_pair_path:0:10,13
source_alt_rank = 44
source_alt_pool_max_child_width = 229
source_alt_pool_total_child_width = 387
source_alt_branch_score = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/002_candidate_alt_d0_n0_r44_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/002_candidate_alt_d0_n0_r44_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/002_candidate_alt_d0_n0_r44_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/002_candidate_alt_d0_n0_r44_10_13_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:10,13 --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 7]
forced_pair = [9, 10]
forced_pair_path_rule = force_pair_path:0:9,10
source_alt_rank = 41
source_alt_pool_max_child_width = 241
source_alt_pool_total_child_width = 402
source_alt_branch_score = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/003_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/003_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/003_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/003_candidate_alt_d0_n0_r41_9_10_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,10 --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [3, 7]
forced_pair = [4, 5]
forced_pair_path_rule = force_pair_path:0:4,5
source_alt_rank = 13
source_alt_pool_max_child_width = 241
source_alt_pool_total_child_width = 468
source_alt_branch_score = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/004_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/004_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/004_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs/004_candidate_alt_d0_n0_r13_4_5_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:4,5 --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
