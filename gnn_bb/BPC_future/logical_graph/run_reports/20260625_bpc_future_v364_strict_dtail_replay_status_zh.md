# V364 Strict D-tail Replay 结果

日期：2026-06-25

## 目的

执行 V364 gate-only strict-productivity runbook 的 5 条 replay，检查 `pricing_unproductive_no_negative_columns` 的 D 类 before-final-probe gate 是否能通过 forced branch / child ordering 产生 timeout-resolved 或更短 certificate 标签。

## 输入

```text
runbook = BPC_future/results/journey_branch_tail_positive_runbook_v364_v360_gate_only_strict_productivity_20260625
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
time_limit = 600
command_count = 5
tail_action_profile = before_final_probe
tail_action_productivity_filter = pricing_unproductive_no_negative_columns
```

## 运行结果

```text
01 depth0 node0 pair [3, 7]  -> EXTERNAL_TIME_LIMIT, wall=600.026475
02 depth1 node2 pair [3, 6]  -> EXTERNAL_TIME_LIMIT, wall=600.024297
03 depth2 node4 pair [1, 3]  -> EXTERNAL_TIME_LIMIT, wall=600.024741
04 depth3 node5 pair [9, 13] -> EXTERNAL_TIME_LIMIT, wall=600.026711
05 depth3 node6 pair [3, 4]  -> EXTERNAL_TIME_LIMIT, wall=600.027013
```

没有 `OPTIMAL`，没有 timeout-resolved，不能作为 strong positive。

## V365 Tail-action 审计

```text
audit = BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625
report = BPC_future/logical_graph/run_reports/20260625_bpc_future_journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_zh.md

log_file_count = 5
row_count = 146
tail_action_class_counts = {
  B_BROAD_PLATEAU: 2,
  C_CONTINUE_CG: 48,
  D_EARLY_BRANCH: 96,
}
tail_action_productivity_class_counts = {
  pricing_active_support_productive: 24,
  pricing_has_negative_columns: 6,
  pricing_no_negative_columns: 2,
  pricing_productivity_signals_incomplete: 18,
  pricing_unproductive_no_negative_columns: 89,
  pricing_weak_columns_tail: 7,
}
early_branch_trigger_count = 7
tail_action_no_column_early_branch_trigger_count = 7
tail_action_queued_child_count = 14
tail_action_observed_child_audit_count = 43
no_column_gate_row_count = 30
no_column_gate_D_EARLY_BRANCH = 28
```

这说明不是 gate 没触发，而是 D 类 early-branch/child-ordering 触发后仍无法在 600 秒内完成 seed61000。

## V366 Training Rows

```text
training = BPC_future/results/journey_tail_impact_training_rows_v366_v365_strict_dtail_hard_negative_20260625
report = BPC_future/logical_graph/run_reports/20260625_bpc_future_journey_tail_impact_training_rows_v366_v365_strict_dtail_hard_negative_zh.md

training_row_count = 7
source_counts = {tail_action_proof_cost: 7}
tail_action_class_counts = {D_EARLY_BRANCH: 7}
tail_action_productivity_class_counts = {pricing_unproductive_no_negative_columns: 7}
y_tail_risk = 7
y_completion_bound_tail = 7
y_negative_chain_continues = 7
y_tail_action_no_column = 7
y_timeout_resolved = 0
y_whole_run_improved = 0
hard_negative_catalog_ready = true
strict_tail_training_ready = false
```

## 结论

V364 不是正例来源；它证明 seed61000 的这批 strict D-tail forced branch / child-ordering 候选仍是 hard negative / right-censored。后续不应继续围绕同一个 seed61000、同一类 gate-only forced-pair 做盲扫。

下一步应转向：

- 更系统的 limited strong branching / child proof-cost probe；
- incumbent improvement；
- pricing-compatible cuts / stronger formulation；
- 或从 canonical random-TW 60-instance 中寻找其他 context 的真正 timeout-resolved positive。

