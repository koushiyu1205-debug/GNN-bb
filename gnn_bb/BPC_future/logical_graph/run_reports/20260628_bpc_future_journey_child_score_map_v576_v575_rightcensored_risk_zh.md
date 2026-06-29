# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 22
child_probe_row_count = 10
filtered_out_child_probe_row_count = 12
right_censored_filter_skip_count = 0
skipped_row_count = 0
child_score_row_count = 10
child_score_map_entry_count = 7
duplicate_unscoped_key_count = 3
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = True
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v576_v575_rightcensored_risk_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v576_v575_rightcensored_risk_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v576_v575_rightcensored_risk_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:1:depth:1:1,4:same_vehicle pair=[1, 4] kind=same_vehicle score=-0.872947189 obs=1 fathom=0.0 gain=22.993111636 cpu=56.588342
- key=node:2:depth:1:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=-1.165358071 obs=1 fathom=0.0 gain=22.782057727 cpu=56.612354
- key=node:2:depth:1:1,10:same_vehicle pair=[1, 10] kind=same_vehicle score=-1.95153905 obs=1 fathom=0.0 gain=34.365177 cpu=84.184686
- key=node:0:depth:0:1,2:separate_vehicle pair=[1, 2] kind=separate_vehicle score=-4.392077984 obs=1 fathom=0.0 gain=2.86e-07 cpu=77.049365
- key=node:0:depth:0:1,2:separate_vehicle pair=[1, 2] kind=separate_vehicle score=-4.392513976 obs=1 fathom=0.0 gain=2.86e-07 cpu=77.101684
- key=node:1:depth:1:1,4:same_vehicle pair=[1, 4] kind=same_vehicle score=-4.852447758 obs=1 fathom=0.0 gain=0.0 cpu=72.293731
- key=node:2:depth:1:1,8:separate_vehicle pair=[1, 8] kind=separate_vehicle score=-5.38144935 obs=1 fathom=0.0 gain=12.5379105 cpu=76.683774
- key=node:0:depth:0:1,2:same_vehicle pair=[1, 2] kind=same_vehicle score=-5.390353784 obs=1 fathom=0.0 gain=0.228719286 cpu=82.331717
- key=node:0:depth:0:1,2:same_vehicle pair=[1, 2] kind=same_vehicle score=-5.394267743 obs=1 fathom=0.0 gain=0.228719286 cpu=82.801392
- key=node:2:depth:1:1,10:separate_vehicle pair=[1, 10] kind=separate_vehicle score=-9.673593683 obs=1 fathom=0.0 gain=12.5379105 cpu=111.741094

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
