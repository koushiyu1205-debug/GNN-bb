# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 24
child_probe_row_count = 0
filtered_out_child_probe_row_count = 24
right_censored_filter_skip_count = 9
skipped_row_count = 0
child_score_row_count = 0
child_score_map_entry_count = 0
duplicate_unscoped_key_count = 0
context_scoped_rows = False
key_scope = pair
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = False
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v572_v571_complete_only_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v572_v571_complete_only_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v572_v571_complete_only_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows


## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
