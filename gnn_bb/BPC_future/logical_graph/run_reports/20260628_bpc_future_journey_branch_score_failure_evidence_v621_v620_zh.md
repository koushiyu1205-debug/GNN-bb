# V610 Branch Score Failure Evidence

source_experiment = `v620_v617_score_depth2_smoke4`
run_root = `BPC_future/results/20260628_v620_v617_score_depth2_smoke4_tasks20`
output_dir = `BPC_future/results/journey_branch_score_failure_evidence_v621_v620_depth2_smoke4_20260628`

## 结论

本脚本把已完成且未最优的 branch-score opt-in full run 转成 diagnostic hard-negative evidence。输出只用于训练/overlay 调度，不能产生 official bound、certificate 或剪枝依据。

## 汇总

```text
result_rows = 4
nonoptimal_result_rows = 4
branch_events = 162
scored_branch_events = 44
hard_negative_rows = 44
tree_policy_rows = 44
status_counts = {'EXTERNAL_TIME_LIMIT': 4}
depth_counts = {'0': 4, '1': 8, '2': 14, '3': 19, '4': 23, '5': 22, '6': 20, '7': 22, '8': 14, '9': 8, '10': 6, '11': 2}
selected_pair_changed_count = 25
completion_bound_retry_count = 175
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 输出

- timeout hard-negative: `BPC_future/results/journey_branch_score_failure_evidence_v621_v620_depth2_smoke4_20260628/score_timeout_hard_negative_rows.jsonl`
- tree-policy event rows: `BPC_future/results/journey_branch_score_failure_evidence_v621_v620_depth2_smoke4_20260628/tree_policy_event_rows.jsonl`
- summary: `BPC_future/results/journey_branch_score_failure_evidence_v621_v620_depth2_smoke4_20260628/summary.json`
