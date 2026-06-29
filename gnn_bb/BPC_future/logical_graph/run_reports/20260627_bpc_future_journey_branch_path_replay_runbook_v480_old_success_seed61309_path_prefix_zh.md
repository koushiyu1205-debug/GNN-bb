# Journey Branch Path Replay Runbook

该 runbook 只从已有 JSONL 日志抽取分支路径，不运行 BPC / pricing / RMP；不产生 official bound 或 certificate。

## Summary

- source_log_count: `1`
- entry_count: `12`
- time_limit: `600`
- depth range: `0..4`

## Entries

### 001_path_d0_n0_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `0` / `0`
- source pair: `[2, 5]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle`

### 002_path_d1_n1_17_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `1` / `1`
- source pair: `[17, 20]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=same_vehicle;1:17,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle`

### 003_path_d1_n2_17_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `1` / `2`
- source pair: `[17, 20]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=separate_vehicle;1:17,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle`

### 004_path_d2_n3_12_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `2` / `3`
- source pair: `[12, 18]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=same_vehicle;1:17,20=same_vehicle;2:12,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:same_vehicle;2:same_vehicle`

### 005_path_d2_n4_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `2` / `4`
- source pair: `[17, 18]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=same_vehicle;1:17,20=separate_vehicle;2:17,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:same_vehicle`

### 006_path_d3_n10_16_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `3` / `10`
- source pair: `[16, 20]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=same_vehicle;1:17,20=separate_vehicle;2:17,18=separate_vehicle;3:16,20`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:separate_vehicle;3:same_vehicle`

### 007_path_d4_n11_12_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `4` / `11`
- source pair: `[12, 18]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=same_vehicle;1:17,20=separate_vehicle;2:17,18=separate_vehicle;3:16,20=same_vehicle;4:12,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:separate_vehicle;3:same_vehicle;4:same_vehicle`

### 008_path_d4_n12_12_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `4` / `12`
- source pair: `[12, 18]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=same_vehicle;1:17,20=separate_vehicle;2:17,18=separate_vehicle;3:16,20=separate_vehicle;4:12,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:separate_vehicle;3:separate_vehicle;4:same_vehicle`

### 009_path_d2_n5_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `2` / `5`
- source pair: `[10, 19]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=separate_vehicle;1:17,20=same_vehicle;2:10,19`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:same_vehicle;2:same_vehicle`

### 010_path_d2_n6_17_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `2` / `6`
- source pair: `[17, 18]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=separate_vehicle;1:17,20=separate_vehicle;2:17,18`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:same_vehicle`

### 011_path_d3_n20_1_14_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `3` / `20`
- source pair: `[1, 14]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=separate_vehicle;1:17,20=separate_vehicle;2:17,18=separate_vehicle;3:1,14`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle;3:same_vehicle`

### 012_path_d4_n22_1_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph

- instance: `BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json`
- source depth/node: `4` / `22`
- source pair: `[1, 7]`
- source first child kind: `same_vehicle`
- forced_pair_path_rule: `force_pair_path:0:2,5=separate_vehicle;1:17,20=separate_vehicle;2:17,18=separate_vehicle;3:1,14=separate_vehicle;4:1,7`
- forced_child_kind_depth_rule: `force_child_kind_depth:0:separate_vehicle;1:separate_vehicle;2:separate_vehicle;3:separate_vehicle;4:same_vehicle`

