# BPC Future V121-V133 Context-Gated Branch Score + Tail Action A/B

日期：2026-06-24

## 目的

验证 V118 context-gated child-probe score map 放入真实 solver 后的表现，并确认它需要怎样和 Tail Action Controller 组合，才能在 canonical random-TW 20 `greedy-anchor/tranquillitatis seed61001` 上恢复 200s 内 exact OPTIMAL。

该线仍是 opt-in 调度层：

- branch-score 只排序 Ryan-Foster pair；
- tail-action 只做 exact-safe early branch；
- 不产生 official bound；
- 不把当前 RMP objective 当 exact node bound；
- 子节点仍靠 exact pricing closure。

## V121: score-only

配置要点：

```text
journey_branch_candidate_priority=branch_score_horizon
journey_branch_candidate_score_path=BPC_future/results/journey_branch_score_map_v118_positive_chain_child_probe_greedy_context_20260624/journey_branch_score_rows.json
journey_branch_candidate_score_context_include_contains=greedy-anchor,seed61001
journey_branch_candidate_score_horizon_tie_tolerance=0.2
journey_branch_fractionality_tie_tolerance=0.0
```

结果：

```text
csv = BPC_future/results/20260624_v121_v118_context_gate_score_only_greedy_seed61001_140.csv
status = EXTERNAL_TIME_LIMIT
wall = 140.658114s
context_gate = matched
branch_score_entry_count = 6
root selected pair = [2,6]
branch_score = 5.393553672
branch_score_source = node:0:depth:0:2,6
early_branch_count = 0
```

解释：V118 map 在真实 solver 中能正确命中并选择 `[2,6]`，但 score-only 不能解决后续 proof tail。

## V122/V125/V128/V130

这些 run 逐步打开 tail-action，但没有恢复 V112 的 node2 early branch：

```text
V122: OPTIMAL, wall=108.508510s, exact_pricing_calls=20, early_branch_count=0
V125: OPTIMAL, wall=96.855960s, exact_pricing_calls=20, early_branch_count=0
V128: OPTIMAL, wall=96.967575s, exact_pricing_calls=20, early_branch_count=0
V130: OPTIMAL, wall=97.188167s, exact_pricing_calls=20, early_branch_count=0
```

关键诊断：

```text
node = 2
depth = 1
pricing_state = LOCAL_NO_COLUMN_UNCERTIFIED
tail_action = EARLY_BRANCH
tail_action_reason = rmp_below_incumbent_pricing_unproductive_for_fathom
```

当前代码在这个 local no-column 状态后没有先触发 no-column early branch，而是进入 completion-bound retry，所以比 V112 多 2 次 exact pricing。

## 代码修正

在 no-new-column / duplicate-retry funnel 前增加：

```text
tail_action_no_column_branch_payload(..., before_final_probe=False)
```

精确性边界：

- 只返回 `BRANCH`；
- 子节点继承已有非 exact lower bound；
- 不剪枝；
- 不生成 certificate；
- 不改变 official bound。

新增测试：

```text
test_journey_tail_action_no_column_branches_before_duplicate_retry_when_opted_in
```

测试确认 `LOCAL_NO_COLUMN_UNCERTIFIED` 下开启 no-column tail-action 后，pricing 只调用 1 次，不进入 completion-bound retry。

## V131: 正确组合

V131 在 V118 score map + context gate 基础上补齐 no-column tail-action gate：

```text
journey_tail_action_early_branch_enabled=True
journey_tail_action_no_column_early_branch_enabled=True
journey_tail_action_no_column_early_branch_max_depth=1
journey_tail_action_no_column_early_branch_require_complete_productivity_signals=False
journey_tail_action_no_column_early_branch_before_final_probe_enabled=True
journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe=True
```

结果：

```text
csv = BPC_future/results/20260624_v131_v118_context_gate_score_tailaction_depth1_signals_greedy_seed61001_140.csv
status = OPTIMAL
wall = 88.368431s
solving_time = 86.296993s
node_count = 5
rmp_solves = 23
pricing_calls = 41
exact_pricing_calls = 18
generated_sequences = 1655334
evaluated_timed_trips = 526904
```

分支行为：

```text
root selected pair = [2,6]
root branch_score = 5.393553672
root source = node:0:depth:0:2,6

depth1 selected pair = [8,12]
depth1 branch_score = 6.536062081
depth1 source = node:2:depth:1:8,12

early_branch_trigger = node2/depth1/cg_iter1
early_branch_reason = rmp_below_incumbent_pricing_unproductive_for_fathom
```

## A/B 审计

V132 对比旧 V112：

```text
paired_instance_count = 1
both_optimal_count = 1
selected_pair_changed_count = 0
branch_score_used_count = 1
wall_time_delta_sum = -1.062621
exact_pricing_calls_delta_sum = 0
node_count_delta_sum = 0
```

V133 对比 V121 score-only：

```text
paired_instance_count = 1
wall_time_delta_sum = -52.289683
EXTERNAL_TIME_LIMIT -> OPTIMAL
```

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. MPLCONFIGDIR=/tmp/mplconfig_bpc_future \
  /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_duplicate_retry_when_opted_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_final_probe_when_opted_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_context_gate_disables_mismatched_map

3 tests OK

PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

OK
```

## 当前结论

V118 context-gated child-probe score map 可以在正确上下文中安全使用。真正起效的是组合：

```text
branch_score_horizon
+ score context gate
+ D-class no-column tail-action early branch at depth 1
```

单独 score map 不够；缺少 no-column early branch 时会多走 completion-bound retry，wall 回到 96-108s 甚至 timeout。V131 是当前该单实例上的最好结果，已经在 200s 目标线内，但它仍不是 20-scale 60-instance 全量达标证据。

下一步应先做小批 no-regression：

1. 5/10 random-TW 小批或全量，score map context gate 不匹配时应自动回退；
2. 20 random-TW 60-instance 诊断时，静态 V118 map 只允许匹配 greedy-anchor seed61001 这类上下文；
3. 后续应训练可泛化 branch-impact ranking / tail-action head，不能依赖 node-depth 静态 lookup。
