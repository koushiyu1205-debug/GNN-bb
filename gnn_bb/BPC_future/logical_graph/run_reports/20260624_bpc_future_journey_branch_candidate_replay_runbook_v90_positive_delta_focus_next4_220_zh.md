# Journey Branch Candidate Replay Runbook

日期：2026-06-24

## Purpose

Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624
entry_count = 4
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 1
skipped_missing_instance_event_count = 0
entry_limit_reached = True
alt_pairs_per_event = 4
candidate_source = priority_top
candidate_log_top_n = 100
branch_impact_input_paths = []
exclude_runbook_paths = ['BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624', 'BPC_future/results/journey_branch_candidate_replay_runbook_v80_v58_positive_context_next4_220_20260624']
focus_delta_input_paths = ['BPC_future/results/journey_branch_counterfactual_delta_v59_v58_second4_220_20260624', 'BPC_future/results/journey_branch_counterfactual_delta_v82_v80_positive_context_next4_220_20260624']
excluded_entry_key_count = 28
excluded_entry_skip_count = 8
focus_context_count = 1
focus_event_skip_count = 28
branch_impact_priority_context_count = 0
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## Entries

### 001_candidate_alt_d0_n0_r3_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [6, 13]
forced_pair_path_rule = force_pair_path:0:6,13
source_alt_rank = 3
source_alt_pool_max_child_width = 353
source_alt_pool_total_child_width = 606
source_alt_branch_score = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/001_candidate_alt_d0_n0_r3_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/001_candidate_alt_d0_n0_r3_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/001_candidate_alt_d0_n0_r3_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/001_candidate_alt_d0_n0_r3_6_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,13 --set journey_branch_candidate_log_top_n=100
```

### 002_candidate_alt_d0_n0_r12_2_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [2, 11]
forced_pair_path_rule = force_pair_path:0:2,11
source_alt_rank = 12
source_alt_pool_max_child_width = 353
source_alt_pool_total_child_width = 622
source_alt_branch_score = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/002_candidate_alt_d0_n0_r12_2_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/002_candidate_alt_d0_n0_r12_2_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/002_candidate_alt_d0_n0_r12_2_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/002_candidate_alt_d0_n0_r12_2_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:2,11 --set journey_branch_candidate_log_top_n=100
```

### 003_candidate_alt_d0_n0_r27_6_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [6, 9]
forced_pair_path_rule = force_pair_path:0:6,9
source_alt_rank = 27
source_alt_pool_max_child_width = 354
source_alt_pool_total_child_width = 603
source_alt_branch_score = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/003_candidate_alt_d0_n0_r27_6_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/003_candidate_alt_d0_n0_r27_6_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/003_candidate_alt_d0_n0_r27_6_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/003_candidate_alt_d0_n0_r27_6_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,9 --set journey_branch_candidate_log_top_n=100
```

### 004_candidate_alt_d0_n0_r23_9_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 18]
forced_pair = [9, 11]
forced_pair_path_rule = force_pair_path:0:9,11
source_alt_rank = 23
source_alt_pool_max_child_width = 354
source_alt_pool_total_child_width = 650
source_alt_branch_score = None
branch_impact_priority = 0.0
branch_impact_priority_reason = None
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 220 --results-csv BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/004_candidate_alt_d0_n0_r23_9_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/004_candidate_alt_d0_n0_r23_9_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/004_candidate_alt_d0_n0_r23_9_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_runbook_v90_positive_delta_focus_next4_220_20260624/runs/004_candidate_alt_d0_n0_r23_9_11_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:9,11 --set journey_branch_candidate_log_top_n=100
```

## Boundary

These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.
