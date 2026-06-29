# Journey Child Order Paired Replay Runbook

该 runbook 只从已有 JSONL 日志抽取 hard-path branch 节点并生成 same-first / separate-first 成对 replay 命令；生成本身不运行 BPC / pricing / RMP。

## Summary

- source_log_count: `4`
- source_branch_event_count: `158`
- selected_pair_count: `12`
- entry_count: `24`
- time_limit: `240`
- probe_extra_nodes_after_branch: `5`
- probe_max_cg_iterations: `36`

## Entries

### 001_child_order_same_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `357.0`
- subtree CB retry: `54`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 002_child_order_separate_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `357.0`
- subtree CB retry: `54`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle`

### 003_child_order_same_vehicle_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[11, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `293.0`
- subtree CB retry: `44`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:11,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:same_vehicle`

### 004_child_order_separate_vehicle_d2_n6_11_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[11, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `293.0`
- subtree CB retry: `44`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:11,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle`

### 005_child_order_same_vehicle_d1_n2_16_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[16, 19]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `284.0`
- subtree CB retry: `41`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 006_child_order_separate_vehicle_d1_n2_16_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[16, 19]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `284.0`
- subtree CB retry: `41`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle`

### 007_child_order_same_vehicle_d3_n14_2_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `3` / `14`
- source pair: `[2, 6]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `257.0`
- subtree CB retry: `38`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:11,20=separate_vehicle;3:2,6`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle;3:same_vehicle`

### 008_child_order_separate_vehicle_d3_n14_2_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json`
- source depth/node: `3` / `14`
- source pair: `[2, 6]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `257.0`
- subtree CB retry: `38`
- forced_pair_path_rule: `force_pair_path:0:14,19=separate_vehicle;1:13,20=separate_vehicle;2:11,20=separate_vehicle;3:2,6`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle;3:separate_vehicle`

### 009_child_order_same_vehicle_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[14, 16]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `191.0`
- subtree CB retry: `27`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:14,16`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:same_vehicle`

### 010_child_order_separate_vehicle_d2_n6_14_16_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[14, 16]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `191.0`
- subtree CB retry: `27`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:14,16`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle`

### 011_child_order_same_vehicle_d3_n10_1_9_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `3` / `10`
- source pair: `[1, 9]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `178.0`
- subtree CB retry: `25`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:14,16=separate_vehicle;3:1,9`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle;3:same_vehicle`

### 012_child_order_separate_vehicle_d3_n10_1_9_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`
- source depth/node: `3` / `10`
- source pair: `[1, 9]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `178.0`
- subtree CB retry: `25`
- forced_pair_path_rule: `force_pair_path:0:11,17=separate_vehicle;1:16,19=separate_vehicle;2:14,16=separate_vehicle;3:1,9`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle;3:separate_vehicle`

### 013_child_order_same_vehicle_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[16, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `167.0`
- subtree CB retry: `25`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle`

### 014_child_order_separate_vehicle_d1_n1_16_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[16, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `167.0`
- subtree CB retry: `25`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle`

### 015_child_order_same_vehicle_d2_n3_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `2` / `3`
- source pair: `[15, 17]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `154.0`
- subtree CB retry: `23`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20=same_vehicle;2:15,17`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:same_vehicle`

### 016_child_order_separate_vehicle_d2_n3_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `2` / `3`
- source pair: `[15, 17]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `154.0`
- subtree CB retry: `23`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20=same_vehicle;2:15,17`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:separate_vehicle`

### 017_child_order_same_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `134.0`
- subtree CB retry: `19`
- forced_pair_path_rule: `force_pair_path:0:15,18=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 018_child_order_separate_vehicle_d1_n2_13_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[13, 20]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `134.0`
- subtree CB retry: `19`
- forced_pair_path_rule: `force_pair_path:0:15,18=separate_vehicle;1:13,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle`

### 019_child_order_same_vehicle_d1_n1_16_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[16, 18]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `129.0`
- subtree CB retry: `19`
- forced_pair_path_rule: `force_pair_path:0:15,18=same_vehicle;1:16,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle`

### 020_child_order_separate_vehicle_d1_n1_16_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[16, 18]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `129.0`
- subtree CB retry: `19`
- forced_pair_path_rule: `force_pair_path:0:15,18=same_vehicle;1:16,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle`

### 021_child_order_same_vehicle_d3_n7_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `3` / `7`
- source pair: `[1, 9]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `122.0`
- subtree CB retry: `18`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20=same_vehicle;2:15,17=same_vehicle;3:1,9`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:same_vehicle;3:same_vehicle`

### 022_child_order_separate_vehicle_d3_n7_1_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`
- source depth/node: `3` / `7`
- source pair: `[1, 9]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `122.0`
- subtree CB retry: `18`
- forced_pair_path_rule: `force_pair_path:0:17,20=same_vehicle;1:16,20=same_vehicle;2:15,17=same_vehicle;3:1,9`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:same_vehicle;3:separate_vehicle`

### 023_child_order_same_vehicle_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[11, 18]`
- target_child_kind: `same_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `121.0`
- subtree CB retry: `17`
- forced_pair_path_rule: `force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:11,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:same_vehicle`

### 024_child_order_separate_vehicle_d2_n6_11_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[11, 18]`
- target_child_kind: `separate_vehicle`
- source_first_child_kind: `same_vehicle`
- priority_score: `121.0`
- subtree CB retry: `17`
- forced_pair_path_rule: `force_pair_path:0:15,18=separate_vehicle;1:13,20=separate_vehicle;2:11,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle`

