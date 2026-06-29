# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 24
child_probe_row_count = 9
filtered_out_child_probe_row_count = 15
right_censored_filter_skip_count = 0
skipped_row_count = 0
child_score_row_count = 9
child_score_map_entry_count = 9
duplicate_unscoped_key_count = 0
context_scoped_rows = True
key_scope = pair
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = True
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v572_v571_rightcensored_risk_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v572_v571_rightcensored_risk_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v572_v571_rightcensored_risk_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=4,8:same_vehicle pair=[4, 8] kind=same_vehicle score=-0.2147501 obs=1 fathom=0.0 gain=9.8627835 cpu=12.061707
- key=5,9:separate_vehicle pair=[5, 9] kind=separate_vehicle score=-0.337037029 obs=1 fathom=0.0 gain=13.828117375 cpu=34.190926
- key=5,9:same_vehicle pair=[5, 9] kind=same_vehicle score=-0.849006492 obs=1 fathom=0.0 gain=7.54206175 cpu=36.19276
- key=3,5:separate_vehicle pair=[3, 5] kind=separate_vehicle score=-0.920070617 obs=1 fathom=0.0 gain=0.0 cpu=7.204237
- key=3,5:same_vehicle pair=[3, 5] kind=same_vehicle score=-1.142385667 obs=1 fathom=0.0 gain=0.0 cpu=11.54314
- key=1,7:same_vehicle pair=[1, 7] kind=same_vehicle score=-1.160676207 obs=1 fathom=0.0 gain=2.2315011 cpu=29.029579
- key=1,2:same_vehicle pair=[1, 2] kind=same_vehicle score=-1.433907437 obs=1 fathom=0.0 gain=0.213464133 cpu=30.315231
- key=1,2:separate_vehicle pair=[1, 2] kind=separate_vehicle score=-1.46065265 obs=1 fathom=0.0 gain=0.258784333 cpu=26.191865
- key=2,10:same_vehicle pair=[2, 10] kind=same_vehicle score=-1.565453783 obs=1 fathom=0.0 gain=0.341029333 cpu=38.973403

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
