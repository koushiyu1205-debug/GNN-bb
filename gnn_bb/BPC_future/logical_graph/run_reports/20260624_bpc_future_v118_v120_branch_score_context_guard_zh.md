# BPC Future V118-V120 Branch Score Context Guard

日期：2026-06-24

## 目的

把 V113-V115 的 child-probe proof-cost 标签推进到 solver 可读的 branch-score map，同时修正 V116/V117 暴露的静态 score map 上下文误用风险。该线仍是 opt-in 调度层：不产生 official bound，不产生 certificate，不改变 exact pricing closure。

## 代码修改

- `BPC_future/scripts/build_journey_branch_score_map.py`
  - 新增 `--include-child-probe-log-contains`
  - 新增 `--exclude-child-probe-log-contains`
  - summary/report 新增 child-probe 过滤前后行数
- `BPC_future/solver/journey_driver.py`
  - 新增 score map context gate 配置：
    - `journey_branch_candidate_score_context_include_contains`
    - `journey_branch_candidate_score_context_exclude_contains`
  - gate 为空时旧行为不变
  - gate 不匹配时 score map 置空，`branch_score_horizon` 回退到原 fractionality 选择
  - `start` 日志新增：
    - `branch_score_context_gate_enabled`
    - `branch_score_context_gate_allowed`
    - `branch_score_context_gate_reason`
    - `branch_score_context_include_contains`
    - `branch_score_context_exclude_contains`
    - `branch_score_entry_count`

## V116/V117 发现的问题

V116 把 V114 positive chain 与 V115 coverage-gap hard negatives 混合生成 node-depth scoped proof-cost score map：

```text
raw_child_probe_row_count = 90
child_probe_branch_row_count = 45
branch_score_map_entry_count = 39
positive_score_count = 5
negative_score_count = 34
```

V117 coverage 显示该 map 会跨上下文命中：

```text
candidate_event_count = 39
candidate_event_with_score_hit_count = 7
candidate_event_would_change_selected_count = 1
selected_unscored_count = 35
```

核心风险是：`node:2:depth:1:8,12` 来自 greedy-anchor 正链，但会在 random-wave / coverage-gap 日志中命中并可能改变选择。它不影响精确性，但会污染性能 A/B。

## V118

只使用 V114 positive-chain greedy-anchor child-probe rows 重建 score map：

```text
score_map = BPC_future/results/journey_branch_score_map_v118_positive_chain_child_probe_greedy_context_20260624
include_child_probe_log_contains = ['greedy-anchor']
raw_child_probe_row_count = 20
child_probe_row_count = 20
child_probe_branch_row_count = 10
branch_score_map_entry_count = 6
```

Top score rows：

```text
node:2:depth:1:8,12 score=6.536062081
node:6:depth:2:2,6 score=6.224246683
node:0:depth:0:2,6 score=5.393553672
node:2:depth:1:6,8 score=5.290700483
node:0:depth:0:7,11 score=3.658089175
node:1:depth:1:6,8 score=-9.711256583
```

## V119

只在匹配的 greedy-anchor seed61001 候选日志上做 coverage：

```text
coverage = BPC_future/results/journey_branch_score_candidate_coverage_v119_v118_positive_greedy_context_20260624
candidate_event_count = 4
candidate_event_with_score_hit_count = 4
candidate_event_with_eligible_score_hit_count = 2
candidate_event_with_selected_score_count = 4
candidate_event_would_change_selected_count = 0
best_scored_required_tie_tolerance_max = 0.2
selected_unscored_count = 0
```

解释：在正确上下文里，V118 map 命中完整，且不会改变当前已知最优正链选择；它主要记录哪些 event 需要 horizon 打到 0.2。

## V120

刻意把同一个 V118 map 误用到 coverage-gap/random-wave 日志：

```text
coverage = BPC_future/results/journey_branch_score_candidate_coverage_v120_v118_misapplied_coverage_gap_guard_20260624
candidate_event_count = 35
candidate_event_with_score_hit_count = 3
candidate_event_with_eligible_score_hit_count = 1
candidate_event_would_change_selected_count = 1
selected_unscored_count = 35
```

解释：仅靠“构图数据源过滤”不够；只要 solver 全局加载这个 node-depth map，错误上下文仍会命中。因此新增 solver context gate 是必要护栏。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_score_map
5 tests OK

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_branch_score_opt_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_branch_score_selection \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_branch_score_horizon \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_context_gate_disables_mismatched_map
4 tests OK

PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/build_journey_branch_score_map.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_journey_branch_score_map.py
OK
```

## 当前结论

V118-V120 是安全性和数据闭环修正，不是新的全量 20-scale 加速证据。它完成了：

- child-probe proof-cost score map 的离线构建；
- 匹配上下文 coverage 诊断；
- 错误上下文误用审计；
- solver 侧 opt-in context gate。

下一步真实 A/B 必须在配置里显式设置 context gate，例如只允许包含对应 `greedy-anchor` / seed / instance token 的 run 启用该 map。长期生产方向仍然是训练可泛化的 branch-impact ranking / tail-action head，而不是依赖 node-depth 静态 lookup。
