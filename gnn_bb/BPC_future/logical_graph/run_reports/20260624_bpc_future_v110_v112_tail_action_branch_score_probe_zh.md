# BPC_future V110/V112 Tail Action 与 Branch-score 复验报告

日期：2026-06-24

## 目的

验证 Tail Action Controller 从 audit 进入受控 opt-in 后，是否能在 completion-bound final probe 前对 D 类 no-column tail 执行 exact-safe early branch，并判断它单独使用、以及与已知 branch-score 正例叠加时的效果。

## 代码变化

- 新增 `journey_tail_action_no_column_early_branch_gate` 诊断日志：在 opt-in 且 final-probe 前 gate 未通过时记录失败原因。
- 新增 `journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe`：
  - 默认关闭；
  - 只在 final-probe 前允许 `INCOMPLETE_LIMIT` + no-column + Tail Action D 类节点提前分支；
  - 不产生 official bound / certificate；
  - 子节点继承已有 `node.lower_bound`，不使用当前 RMP objective 剪枝。
- 保留 width guard 语义：`max_pool_child_width=0` 是严格上限，不是关闭开关。关闭 width guard 应省略该 cap。

## 验证

```text
tests:
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_early_branch_gate_is_tail_only \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_final_probe_when_opted_in

py_compile:
PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

两项均通过。

## V109 opt-in3 复盘

```text
csv = BPC_future/results/20260624_v109_tail_action_before_final_probe_optin3_220.csv
status = 3/3 EXTERNAL_TIME_LIMIT
tail_action EARLY_BRANCH audit rows = 103
journey_early_branch_trigger = 0
```

原因不是没有 D 类机会，而是：

- 命令把 `max_pool_child_width` / `max_pool_total_child_width` / `max_pool_balance_gap` 都设成 `0`，实际等价于禁止有宽度的分支；
- 很多 final-probe 前节点是 `INCOMPLETE_LIMIT`，不是严格的 `LOCAL_NO_COLUMN_UNCERTIFIED`。

## V110 tail-action only

实例：

```text
BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
```

结果：

```text
120s csv = BPC_future/results/20260624_v110_tail_action_incomplete_before_final_probe_seed61001_120.csv
120s status = EXTERNAL_TIME_LIMIT
120s trigger = 5
120s completion-bound retry = 6

220s csv = BPC_future/results/20260624_v110_tail_action_incomplete_before_final_probe_seed61001_220.csv
220s status = EXTERNAL_TIME_LIMIT
220s trigger = 7
220s completion-bound retry = 15
220s child_queued = 22
```

结论：V110 入口确实能触发，并能跳过一部分 completion-bound final probe；但默认 branch pair / child ordering 质量不够，单靠“更早分支”不能把该 hard instance 拉进 200 秒。

## V111 context mismatch

把 `greedy-anchor/tranquillitatis seed61001` 的 score map 误用于 `random-wave/tranquillitatis seed61001`：

```text
csv = BPC_future/results/20260624_v111_branch_score_plus_tail_action_seed61001_140.csv
status = EXTERNAL_TIME_LIMIT
branch_score_used = 0
```

这只是 context mismatch，不能作为 branch-score 或 tail-action 的算法负例。

## V112 branch-score + V110

实例：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
```

配置：

```text
journey_branch_candidate_priority=branch_score_horizon
journey_branch_candidate_score_path=BPC_future/results/journey_branch_score_map_seed61001_root_only_replay6_20260624/journey_branch_score_rows.json
journey_branch_candidate_score_horizon_tie_tolerance=0.2
journey_tail_action_no_column_early_branch_enabled=True
journey_tail_action_no_column_early_branch_before_final_probe_enabled=True
journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe=True
```

结果：

```text
csv = BPC_future/results/20260624_v112_branch_score_plus_tail_action_greedy_seed61001_140.csv
status = OPTIMAL
wall = 89.431052s
solving_time = 87.315572s
root selected pair = [2,6]
branch_score = 3.787759323
branch_score_source = node:0:depth:0:2,6
tail-action before-final-probe trigger = 1
completion-bound retry = 4
```

对比旧 score-only 复验：

```text
BPC_future/results/20260624_seed61001_branch_score_root_only_replay6_optin_fixed_220.csv
wall = 96.959669s
```

结论：正确 context 下，V110 没有破坏 `[2,6]` branch-score 正例链路，并略微减少 wall time。但这仍只是单实例 in-context 证据，不是 canonical `tasks_020` 60/60 达标。

## 当前判断

Tail Action Controller 应继续作为第一优先级推进，但它不能替代 branch pair / child ordering。当前最有效的方向是：

1. 保持 V110 为受控 opt-in，默认关闭。
2. 对 D 类节点使用 early branch 时，必须优先接入 branch-score / limited strong branching / child proof-cost 标签。
3. 继续扩大 mixed positive/negative branch context，而不是盲扫 coverage-gap 或只按 tail 风险线性采样。
