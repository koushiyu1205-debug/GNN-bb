# Journey Child Score Map

日期：2026-06-26

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 168
child_probe_row_count = 60
filtered_out_child_probe_row_count = 108
right_censored_filter_skip_count = 0
skipped_row_count = 0
child_score_row_count = 60
child_score_map_entry_count = 56
duplicate_unscoped_key_count = 4
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = True
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v443_v441_v442_rightcensored_diag_20260626/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v443_v441_v442_rightcensored_diag_20260626/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v443_v441_v442_rightcensored_diag_20260626/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:0:depth:0:13,17:same_vehicle pair=[13, 17] kind=same_vehicle score=-1.604281017 obs=1 fathom=1.0 gain=28.312032 cpu=36.513722
- key=node:0:depth:0:15,19:same_vehicle pair=[15, 19] kind=same_vehicle score=-2.798079183 obs=1 fathom=1.0 gain=18.888643 cpu=33.096934
- key=node:0:depth:0:13,16:separate_vehicle pair=[13, 16] kind=separate_vehicle score=-4.024424742 obs=1 fathom=1.0 gain=12.232707 cpu=20.515937
- key=node:0:depth:0:16,17:same_vehicle pair=[16, 17] kind=same_vehicle score=-4.054629533 obs=1 fathom=1.0 gain=12.232707 cpu=24.140512
- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=-5.008486408 obs=1 fathom=0.0 gain=17.0907625 cpu=15.196669
- key=node:0:depth:0:3,5:same_vehicle pair=[3, 5] kind=same_vehicle score=-5.651040275 obs=1 fathom=0.0 gain=15.629318667 cpu=57.228481
- key=node:0:depth:0:3,9:same_vehicle pair=[3, 9] kind=same_vehicle score=-5.815115083 obs=1 fathom=0.0 gain=13.828117375 cpu=33.688627
- key=node:0:depth:0:5,9:separate_vehicle pair=[5, 9] kind=separate_vehicle score=-5.8212057 obs=1 fathom=0.0 gain=13.828117375 cpu=34.419501
- key=node:0:depth:0:4,9:same_vehicle pair=[4, 9] kind=same_vehicle score=-6.203996467 obs=1 fathom=0.0 gain=11.109894 cpu=15.117032
- key=node:0:depth:0:8,9:same_vehicle pair=[8, 9] kind=same_vehicle score=-6.237206525 obs=1 fathom=0.0 gain=11.109894 cpu=19.102239
- key=node:0:depth:0:16,17:separate_vehicle pair=[16, 17] kind=separate_vehicle score=-6.687361988 obs=1 fathom=0.0 gain=9.4294386 cpu=32.789965
- key=node:0:depth:0:13,16:same_vehicle pair=[13, 16] kind=same_vehicle score=-6.714338097 obs=1 fathom=0.0 gain=9.4294386 cpu=36.027098

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
