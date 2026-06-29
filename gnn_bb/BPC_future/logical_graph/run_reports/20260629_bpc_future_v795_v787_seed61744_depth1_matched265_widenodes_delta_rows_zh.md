# Journey Paired-Probe Delta Rows

日期：2026-06-29

## 目的

把 paired child-probe 的 proof-risk evidence 转成 branch-action 数据集可读取的 calibration rows。输出是 proxy-only，不能当完整求解反事实标签。

## 机器字段

```text
input_row_count = 2
output_row_count = 0
input_paired_label_counts = {'target_not_replayed': 1}
output_counterfactual_label_counts = {}
skipped_counts = {'not_convertible': 2}
nonconvertible_label_counts = {'baseline': 1, 'target_not_replayed': 1}
nonconvertible_target_replay_reason_counts = {'ancestor_forced_but_target_child_no_branch': 2}
rows_path = BPC_future/results/journey_paired_probe_delta_rows_v795_v787_seed61744_depth1_matched265_widenodes/branch_counterfactual_delta_rows.jsonl
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 输出样本


## 边界

这些 row 的 `right_censored_counterfactual=True`，只用于 proof-risk / hard-negative calibration。任何 positive proxy 都不能直接升级为 full-replay positive；后续仍需完整 replay 或 exact pricing closure 验证。
