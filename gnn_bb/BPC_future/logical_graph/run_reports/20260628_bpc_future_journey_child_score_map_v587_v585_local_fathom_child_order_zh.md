# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 92
child_probe_row_count = 4
filtered_out_child_probe_row_count = 88
right_censored_filter_skip_count = 34
skipped_row_count = 0
child_score_row_count = 4
child_score_map_entry_count = 3
duplicate_unscoped_key_count = 1
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = False
include_fathomed_right_censored = True
fathomed_right_censored_included_count = 4
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v587_v585_local_fathom_child_order_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v587_v585_local_fathom_child_order_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v587_v585_local_fathom_child_order_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=1.356317333 obs=1 fathom=1.0 gain=5.152441 cpu=20.900504
- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=1.355439575 obs=1 fathom=1.0 gain=5.152441 cpu=21.005835
- key=node:1:depth:1:1,9:same_vehicle pair=[1, 9] kind=same_vehicle score=0.812192492 obs=1 fathom=1.0 gain=0.066067 cpu=24.122509
- key=node:1:depth:1:1,11:same_vehicle pair=[1, 11] kind=same_vehicle score=-3.013593293 obs=1 fathom=1.0 gain=0.631502909 cpu=46.787265

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
`--include-fathomed-right-censored` 只允许已启动且本 child 已被 exact-safe fathom 的右删失 child 进入局部诊断 map；它仍不是完整 branch-pair 标签。
