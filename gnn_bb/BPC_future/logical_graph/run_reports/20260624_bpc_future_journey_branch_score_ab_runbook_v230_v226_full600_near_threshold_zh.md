# Journey Branch Score A/B Runbook

该 runbook 只生成 baseline / branch-score-horizon 成对命令；不运行 BPC，不产生 official bound 或 certificate。

## Machine Fields

```text
output_dir = BPC_future/results/journey_branch_score_ab_runbook_v230_v226_full600_near_threshold_20260624
score_path = BPC_future/results/journey_branch_score_map_v226_v212_combined_strict_full_replay_only_20260624/journey_branch_score_rows.json
entry_count = 4
command_count = 8
candidate_log_top_n = 200
score_horizon_tie_tolerance = 0.2
score_horizon_min_score = 0.0
raw_score_row_count = 20
score_instance_count = 4
skipped_missing_result_count = 0
skipped_status_count = 0
skipped_wall_count = 0
official_bound_effect = false
certificate_effect = false
```

## Entries

### 001 BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json

```text
status = OPTIMAL
wall_time = 253.703779
score_row_count = 1
top_pair = [12, 15]
top_score = 3.4249861
```

### 002 BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json

```text
status = OPTIMAL
wall_time = 327.745824
score_row_count = 3
top_pair = [2, 6]
top_score = 2.547759323
```

### 003 BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json

```text
status = OPTIMAL
wall_time = 220.160814
score_row_count = 3
top_pair = [6, 16]
top_score = 1.985119013
```

### 004 BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json

```text
status = OPTIMAL
wall_time = 287.679798
score_row_count = 1
top_pair = [2, 5]
top_score = 0.04228335
```

