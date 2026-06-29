# V610 Branch Score Failure Evidence

source_experiment = `v618_v617_structural_overlay_smoke4`
run_root = `BPC_future/results/20260628_v618_v617_structural_overlay_smoke4_tasks20`
output_dir = `BPC_future/results/journey_branch_score_failure_evidence_v619_v618_v617_smoke4_20260628`

## 结论

本脚本把已完成且未最优的 branch-score opt-in full run 转成 diagnostic hard-negative evidence。输出只用于训练/overlay 调度，不能产生 official bound、certificate 或剪枝依据。

## 汇总

```text
result_rows = 4
nonoptimal_result_rows = 4
branch_events = 154
scored_branch_events = 70
hard_negative_rows = 70
tree_policy_rows = 70
status_counts = {'EXTERNAL_TIME_LIMIT': 4}
depth_counts = {'0': 4, '1': 8, '2': 14, '3': 23, '4': 28, '5': 25, '6': 15, '7': 11, '8': 10, '9': 6, '10': 6, '11': 2, '12': 2}
selected_pair_changed_count = 70
completion_bound_retry_count = 174
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 输出

- timeout hard-negative: `BPC_future/results/journey_branch_score_failure_evidence_v619_v618_v617_smoke4_20260628/score_timeout_hard_negative_rows.jsonl`
- tree-policy event rows: `BPC_future/results/journey_branch_score_failure_evidence_v619_v618_v617_smoke4_20260628/tree_policy_event_rows.jsonl`
- summary: `BPC_future/results/journey_branch_score_failure_evidence_v619_v618_v617_smoke4_20260628/summary.json`
