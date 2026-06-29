# Journey Branch Forced Replay Delta

日期：2026-06-27

## 目的

把强制 Ryan-Foster pair 的完整 600 秒 replay 结果转成 branch/action 训练 row。该脚本只读完成的 runbook、结果 CSV 和 JSONL 日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/runbook.json
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v465_v464_nonopt_positive_neighbor_full600_20260627
entry_count = 48
row_count = 48
label_type_counts = {'changed_timeout_no_effect_hard_negative': 46, 'strong_positive': 2}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 45, 'EXTERNAL_TIME_LIMIT->OPTIMAL': 2, 'EXTERNAL_TIME_LIMIT->TIME_LIMIT': 1}
skipped_counts = {}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 边界

这些 row 只用于训练 branch 候选排序和 score gate；不能作为剪枝依据，不能替代 exact pricing closure。
