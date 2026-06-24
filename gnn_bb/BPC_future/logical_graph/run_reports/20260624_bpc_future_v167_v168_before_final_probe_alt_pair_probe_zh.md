# V167/V168 before-final-probe 替代 pair 探针

## 背景

V166 证明 before-final-probe D 类 no-column early branch 能触发，但单独使用会把 proof tail 推到 child subtree。为避免继续只调 early-branch gate，V167 把 V166 的 hard-negative tail-action rows 转成 branch-tail runbook，允许在同一 branch path 下替换目标 depth 的 Ryan-Foster pair。

## V167 改动

`build_journey_branch_tail_positive_runbook.py` 新增 `--tail-action-profile before_final_probe`。

该 profile 会为 tail-action 条目生成 V166 对齐的命令：

```text
journey_tail_action_audit_enabled=True
journey_tail_action_early_branch_enabled=False
journey_tail_action_no_column_early_branch_enabled=True
journey_tail_action_no_column_early_branch_before_final_probe_enabled=True
journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe=True
journey_tail_action_no_column_early_branch_min_tasks=20
journey_tail_action_no_column_early_branch_min_depth=<source_depth>
journey_tail_action_no_column_early_branch_max_depth=<source_depth>
```

这修正了旧 V12 runbook 固定 `min_depth=max_depth=2`、未打开 before-final-probe 行为门的问题。生成物：

```text
runbook = BPC_future/results/journey_branch_tail_positive_runbook_v167_v166_before_final_probe_alt_pairs_20260624
report  = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_tail_positive_runbook_v167_v166_before_final_probe_alt_pairs_zh.md
entry_count = 12
tail_action_profile = before_final_probe
tail_alt_pairs_per_node = 2
```

## V168 运行

只跑了 V167 中 node1 的两个替代 pair：

```text
source V166 node1 selected pair = [4,7]
alt pair 1 = [1,10]
alt pair 2 = [4,11]
time_limit = 220s
```

两条都仍为 `EXTERNAL_TIME_LIMIT`。

审计输出：

```text
audit = BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624
tail_impact = BPC_future/results/journey_tail_impact_training_rows_v168_v167_node1_alt_pairs_20260624
```

V168 汇总：

```text
tail_action rows = 114
early_branch_trigger = 3
no_column gate rows = 46
no_column gate D rows = 46
exact_completion_bound_retry rows = 40
training_row_count = 3
y_tail_risk = 3
y_useful_tail_reduction = 0
```

## 对比

V166 源 node1 `[4,7]`：

```text
child_subtree_pricing = 59
child_subtree_negative_pricing = 31
child_subtree_completion_retry = 14
child_subtree_no_column_chain = 9
status = EXTERNAL_TIME_LIMIT
```

V168 alt `[1,10]` 在 node1 局部：

```text
child_subtree_pricing = 17
child_subtree_negative_pricing = 10
child_subtree_completion_retry = 6
child_subtree_no_column_chain = 0
status = EXTERNAL_TIME_LIMIT
```

但同一 run 的后续 node2 又出现：

```text
child_subtree_pricing = 92
child_subtree_negative_pricing = 37
child_subtree_completion_retry = 56
```

V168 alt `[4,11]` 在 node1 局部：

```text
child_subtree_pricing = 25
child_subtree_negative_pricing = 13
child_subtree_completion_retry = 12
child_subtree_no_column_chain = 0
status = EXTERNAL_TIME_LIMIT
```

## V169 反事实 delta

V169 对 V167/V168 做了离线反事实 delta 审计：

```text
script = BPC_future/scripts/audit_journey_tail_action_counterfactual_delta.py
output = BPC_future/results/journey_tail_action_counterfactual_delta_v169_v168_node1_alt_pairs_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_action_counterfactual_delta_v169_node1_alt_pairs_zh.md
matched_counterfactual_count = 2
local_tail_improved_count = 2
whole_run_improved_count = 0
local_improved_but_whole_run_not_count = 2
right_censored_counterfactual_count = 2
whole_run_training_ready = false
```

两条替代 pair 的标签结果：

```text
[1,10]:
  local_tail_cost_delta = -42.35
  status = EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
  wall_time_delta = -0.002188

[4,11]:
  local_tail_cost_delta = -32.95
  status = EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
  wall_time_delta = -0.00199
```

这说明 V168 的确是 local-only improvement：源 node1 的 proof-tail 成本下降了，但整轮没有从 timeout 变成 OPTIMAL，也没有形成可解释的 wall-time 改善。

V170 已把这两条 counterfactual delta 接入统一 tail-impact training rows v4：

```text
output = BPC_future/results/journey_tail_impact_training_rows_v170_v166_plus_v169_counterfactual_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_impact_training_rows_v170_v166_plus_v169_counterfactual_zh.md
training_row_count = 22
tail_action_counterfactual_row_count = 2
y_local_tail_improved = 2
y_whole_run_improved = 0
y_local_improved_but_whole_run_not = 2
```

也就是说，这两条样本现在会进入 hard-negative catalog，而不是作为 useful-tail-reduction 正例。

## 判断

V167/V168 说明替代 pair 确实会改变局部 proof-tail 形态，甚至能减少源 node1 的 negative pricing / retry / no-column chain。但它仍没有形成整棵树加速，因为 tail 会转移到 sibling/deeper node。

因此这批数据仍是 hard-negative / partial-local-improvement 样本，不能作为 production branch-score 正例。V169 的作用是把这个边界机器化：后续 GAT/score-map 训练不能只看 local child subtree proof cost，必须同时要求 whole-run improvement、timeout resolved，或至少全 run exact-pricing / completion-bound retry 同步下降。下一步如果继续采样，应优先找能够同时降低：

- 源节点 child subtree proof cost；
- sibling subtree proof cost；
- 全 run exact-pricing / completion-bound retry；
- 220s 或 200s 内 OPTIMAL 状态。
