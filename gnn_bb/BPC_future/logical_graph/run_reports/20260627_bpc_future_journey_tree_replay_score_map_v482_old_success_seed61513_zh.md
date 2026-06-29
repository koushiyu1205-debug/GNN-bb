# Journey Tree Replay Score Map

日期：2026-06-27

## 目的

从已成功的 Journey JSONL 日志导出 tree-level branch score 和 child score，用于 opt-in replay。该过程只读日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
input_log_count = 1
branch_score_row_count = 12
child_score_row_count = 24
command_count = 1
skipped_branch_event_count = 0
skipped_child_event_count = 0
solver_branch_priority = branch_score_horizon
solver_child_priority_mode = child_score
branch_score_rows_path = BPC_future/results/journey_tree_replay_score_map_v482_old_success_seed61513_20260627/journey_branch_tree_score_rows.json
child_score_rows_path = BPC_future/results/journey_tree_replay_score_map_v482_old_success_seed61513_20260627/journey_child_tree_score_rows.json
commands_path = BPC_future/results/journey_tree_replay_score_map_v482_old_success_seed61513_20260627/commands.sh
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Branch Rows Preview

- node=0 depth=0 pair=[3, 19] score=998.7628305
- node=1 depth=1 pair=[4, 20] score=997.7534447
- node=3 depth=2 pair=[6, 20] score=994.2394838
- node=4 depth=2 pair=[6, 20] score=993.1467189
- node=5 depth=3 pair=[5, 13] score=990.8837368
- node=7 depth=3 pair=[10, 20] score=987.862511
- node=10 depth=4 pair=[7, 13] score=982.7861817
- node=11 depth=4 pair=[1, 16] score=981.7593174
- node=12 depth=4 pair=[4, 5] score=980.5885023
- node=18 depth=5 pair=[4, 7] score=975.8093867
- node=19 depth=6 pair=[13, 16] score=974.3049742
- node=22 depth=7 pair=[1, 9] score=969.7254502

## Child Rows Preview

- node=0 depth=0 pair=[3, 19] kind=same_vehicle score=100.0
- node=0 depth=0 pair=[3, 19] kind=separate_vehicle score=99.0
- node=1 depth=1 pair=[4, 20] kind=same_vehicle score=100.0
- node=1 depth=1 pair=[4, 20] kind=separate_vehicle score=99.0
- node=3 depth=2 pair=[6, 20] kind=same_vehicle score=100.0
- node=3 depth=2 pair=[6, 20] kind=separate_vehicle score=99.0
- node=4 depth=2 pair=[6, 20] kind=same_vehicle score=100.0
- node=4 depth=2 pair=[6, 20] kind=separate_vehicle score=99.0
- node=5 depth=3 pair=[5, 13] kind=same_vehicle score=100.0
- node=5 depth=3 pair=[5, 13] kind=separate_vehicle score=99.0
- node=7 depth=3 pair=[10, 20] kind=same_vehicle score=100.0
- node=7 depth=3 pair=[10, 20] kind=separate_vehicle score=99.0

## 使用边界

`branch_score_horizon` 和 `child_score` 只改变 branch pair 与 child 入队顺序；它们不提供 bound，不剪枝，不替代 exact pricing closure。
如果 replay 不能复现旧成功，说明旧成功依赖更广的 tree policy、不同列池轨迹或代码/配置漂移，不应把单个 pair/path 当作强正例。
