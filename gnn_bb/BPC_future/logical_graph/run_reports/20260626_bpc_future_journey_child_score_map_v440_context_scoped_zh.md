# Journey Child Score Map

日期：2026-06-26

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 4366
child_probe_row_count = 746
filtered_out_child_probe_row_count = 3620
right_censored_filter_skip_count = 1876
skipped_row_count = 0
child_score_row_count = 696
child_score_map_entry_count = 304
duplicate_unscoped_key_count = 172
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = False
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v440_existing_probe_context_scoped_20260626/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v440_existing_probe_context_scoped_20260626/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v440_existing_probe_context_scoped_20260626/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.632656342 obs=1 fathom=1.0 gain=33.678155 cpu=8.081239
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.632400183 obs=1 fathom=1.0 gain=33.678155 cpu=8.111978
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.632296608 obs=2 fathom=2.0 gain=33.678155 cpu=16.248814
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.632057825 obs=1 fathom=1.0 gain=33.678155 cpu=8.153061
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.631496792 obs=1 fathom=1.0 gain=33.678155 cpu=8.220385
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.631450458 obs=1 fathom=1.0 gain=33.678155 cpu=8.225945
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.631384292 obs=1 fathom=1.0 gain=33.678155 cpu=8.233885
- key=node:3:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.631032075 obs=1 fathom=1.0 gain=33.678155 cpu=8.276151
- key=node:4:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.595367767 obs=1 fathom=1.0 gain=33.831597 cpu=12.555868
- key=node:4:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.59519185 obs=1 fathom=1.0 gain=33.831597 cpu=12.576978
- key=node:4:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.594571292 obs=2 fathom=2.0 gain=33.831597 cpu=25.30289
- key=node:4:depth:2:1,8:same_vehicle pair=[1, 8] kind=same_vehicle score=11.594231167 obs=1 fathom=1.0 gain=33.831597 cpu=12.69226

## v438 12-Smoke 覆盖检查

```text
checked_against = BPC_future/results/20260626_v438_branch_score_proofrisk_gate067_smoke20_topscore12/analysis_summary.json
instances = 12
root_child_covered_instances = 0
context_covered_instances = 3
```

这说明 v440 目前主要是历史 child-probe 的诊断 map，不是可以直接推进 20-scale 12-smoke 的 root proof-tail 加速器。把它和 v439 branch score 直接组合跑 600s smoke，预期不会改变多数 root 分支闭环；下一步更应该补当前 random-TW 20 smoke 失败实例的 root-child / depth1 child-probe 覆盖，再做 opt-in child ordering 实测。

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
