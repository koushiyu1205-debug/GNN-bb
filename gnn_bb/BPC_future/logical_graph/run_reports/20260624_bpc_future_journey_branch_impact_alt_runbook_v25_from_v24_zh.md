# Journey Branch-Impact Alternative Runbook

日期：2026-06-24

## 目的

从完整 branch-impact audit 的 `priority_top` 中生成同节点 alternative forced-pair replay 命令，用于补充 branch 候选排序所需的反事实标签。runbook 只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_impact_alt_runbook = current
output_dir = BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624
entry_count = 12
branch_impact_input_paths = ['BPC_future/results/journey_branch_impact_audit_v24_branch_candidate_log_600_3opt_branch_20260624']
alt_pairs_per_node = 2
time_limit = 600
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 条目

### 01_branch_alt_pair_d0_n0_r4_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 5]
forced_pair = [3, 18]
forced_pair_path_rule = force_pair_path:0:3,18
source_alt_rank = 4
source_alt_pool_max_child_width = 375
source_alt_pool_total_child_width = 644
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/01_branch_alt_pair_d0_n0_r4_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/01_branch_alt_pair_d0_n0_r4_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/01_branch_alt_pair_d0_n0_r4_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/01_branch_alt_pair_d0_n0_r4_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:3,18 --set journey_branch_candidate_log_top_n=12
```

### 02_branch_alt_pair_d0_n0_r7_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [2, 5]
forced_pair = [5, 8]
forced_pair_path_rule = force_pair_path:0:5,8
source_alt_rank = 7
source_alt_pool_max_child_width = 376
source_alt_pool_total_child_width = 625
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/02_branch_alt_pair_d0_n0_r7_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/02_branch_alt_pair_d0_n0_r7_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/02_branch_alt_pair_d0_n0_r7_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/02_branch_alt_pair_d0_n0_r7_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:5,8 --set journey_branch_candidate_log_top_n=12
```

### 03_branch_alt_pair_d1_n1_r9_8_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [2, 17]
forced_pair = [8, 18]
forced_pair_path_rule = force_pair_path:0:2,5=same_vehicle;1:8,18
source_alt_rank = 9
source_alt_pool_max_child_width = 295
source_alt_pool_total_child_width = 483
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/03_branch_alt_pair_d1_n1_r9_8_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/03_branch_alt_pair_d1_n1_r9_8_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/03_branch_alt_pair_d1_n1_r9_8_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/03_branch_alt_pair_d1_n1_r9_8_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=same_vehicle;1:8,18' --set journey_branch_candidate_log_top_n=12
```

### 04_branch_alt_pair_d1_n1_r8_8_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [2, 17]
forced_pair = [8, 17]
forced_pair_path_rule = force_pair_path:0:2,5=same_vehicle;1:8,17
source_alt_rank = 8
source_alt_pool_max_child_width = 300
source_alt_pool_total_child_width = 491
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/04_branch_alt_pair_d1_n1_r8_8_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/04_branch_alt_pair_d1_n1_r8_8_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/04_branch_alt_pair_d1_n1_r8_8_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/04_branch_alt_pair_d1_n1_r8_8_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=same_vehicle;1:8,17' --set journey_branch_candidate_log_top_n=12
```

### 05_branch_alt_pair_d1_n2_r1_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [3, 17]
forced_pair = [3, 18]
forced_pair_path_rule = force_pair_path:0:2,5=separate_vehicle;1:3,18
source_alt_rank = 1
source_alt_pool_max_child_width = 385
source_alt_pool_total_child_width = 665
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/05_branch_alt_pair_d1_n2_r1_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/05_branch_alt_pair_d1_n2_r1_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/05_branch_alt_pair_d1_n2_r1_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/05_branch_alt_pair_d1_n2_r1_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=separate_vehicle;1:3,18' --set journey_branch_candidate_log_top_n=12
```

### 06_branch_alt_pair_d1_n2_r11_13_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
source_node_id = 2
source_depth = 1
source_selected_pair = [3, 17]
forced_pair = [13, 18]
forced_pair_path_rule = force_pair_path:0:2,5=separate_vehicle;1:13,18
source_alt_rank = 11
source_alt_pool_max_child_width = 389
source_alt_pool_total_child_width = 649
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/06_branch_alt_pair_d1_n2_r11_13_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/06_branch_alt_pair_d1_n2_r11_13_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/06_branch_alt_pair_d1_n2_r11_13_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/06_branch_alt_pair_d1_n2_r11_13_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,5=separate_vehicle;1:13,18' --set journey_branch_candidate_log_top_n=12
```

### 07_branch_alt_pair_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [1, 2]
forced_pair = [1, 18]
forced_pair_path_rule = force_pair_path:0:1,18
source_alt_rank = 5
source_alt_pool_max_child_width = 154
source_alt_pool_total_child_width = 290
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/07_branch_alt_pair_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/07_branch_alt_pair_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/07_branch_alt_pair_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/07_branch_alt_pair_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,18 --set journey_branch_candidate_log_top_n=12
```

### 08_branch_alt_pair_d0_n0_r1_1_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [1, 2]
forced_pair = [1, 4]
forced_pair_path_rule = force_pair_path:0:1,4
source_alt_rank = 1
source_alt_pool_max_child_width = 157
source_alt_pool_total_child_width = 293
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/08_branch_alt_pair_d0_n0_r1_1_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/08_branch_alt_pair_d0_n0_r1_1_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/08_branch_alt_pair_d0_n0_r1_1_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/08_branch_alt_pair_d0_n0_r1_1_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:1,4 --set journey_branch_candidate_log_top_n=12
```

### 09_branch_alt_pair_d0_n0_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [5, 6]
forced_pair = [6, 7]
forced_pair_path_rule = force_pair_path:0:6,7
source_alt_rank = 5
source_alt_pool_max_child_width = 120
source_alt_pool_total_child_width = 209
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/09_branch_alt_pair_d0_n0_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/09_branch_alt_pair_d0_n0_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/09_branch_alt_pair_d0_n0_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/09_branch_alt_pair_d0_n0_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:6,7 --set journey_branch_candidate_log_top_n=12
```

### 10_branch_alt_pair_d0_n0_r8_7_11_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json
source_node_id = 0
source_depth = 0
source_selected_pair = [5, 6]
forced_pair = [7, 11]
forced_pair_path_rule = force_pair_path:0:7,11
source_alt_rank = 8
source_alt_pool_max_child_width = 122
source_alt_pool_total_child_width = 205
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/10_branch_alt_pair_d0_n0_r8_7_11_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/10_branch_alt_pair_d0_n0_r8_7_11_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/10_branch_alt_pair_d0_n0_r8_7_11_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/10_branch_alt_pair_d0_n0_r8_7_11_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_branch_candidate_priority=force_pair_path:0:7,11 --set journey_branch_candidate_log_top_n=12
```

### 11_branch_alt_pair_d1_n1_r10_7_10_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [5, 7]
forced_pair = [7, 10]
forced_pair_path_rule = force_pair_path:0:5,6=same_vehicle;1:7,10
source_alt_rank = 10
source_alt_pool_max_child_width = 106
source_alt_pool_total_child_width = 199
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/11_branch_alt_pair_d1_n1_r10_7_10_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/11_branch_alt_pair_d1_n1_r10_7_10_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/11_branch_alt_pair_d1_n1_r10_7_10_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/11_branch_alt_pair_d1_n1_r10_7_10_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,6=same_vehicle;1:7,10' --set journey_branch_candidate_log_top_n=12
```

### 12_branch_alt_pair_d1_n1_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph

```text
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json
source_node_id = 1
source_depth = 1
source_selected_pair = [5, 7]
forced_pair = [6, 7]
forced_pair_path_rule = force_pair_path:0:5,6=same_vehicle;1:6,7
source_alt_rank = 5
source_alt_pool_max_child_width = 110
source_alt_pool_total_child_width = 187
source_selected_tail_class = completion_bound_tail
```

```bash
/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/12_branch_alt_pair_d1_n1_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/12_branch_alt_pair_d1_n1_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/12_branch_alt_pair_d1_n1_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/12_branch_alt_pair_d1_n1_r5_6_7_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:5,6=same_vehicle;1:6,7' --set journey_branch_candidate_log_top_n=12
```

## 边界

这些命令只改变 branch 候选优先级；如果 forced pair 在 replay 时不是当前合法 fractional candidate，会按现有 solver 逻辑回退。最终 no-negative closure、node bound、fathom 仍只来自 exact-safe pricing / certificate。
