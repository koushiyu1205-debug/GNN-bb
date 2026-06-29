# Journey Paired-Probe Delta Rows

日期：2026-06-28

## 目的

把 paired child-probe 的 proof-risk evidence 转成 branch-action 数据集可读取的 calibration rows。输出是 proxy-only，不能当完整求解反事实标签。

## 机器字段

```text
input_row_count = 4
output_row_count = 3
input_paired_label_counts = {'neutral_proxy': 3}
output_counterfactual_label_counts = {'paired_probe_neutral_proxy': 3}
skipped_counts = {'not_convertible': 1}
rows_path = BPC_future/results/journey_paired_probe_delta_rows_v720_v719_phased_summary_pairprobe_20260628/branch_counterfactual_delta_rows.jsonl
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 输出样本

- apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json d=0 pair=[10, 19] type=paired_probe_neutral_proxy wall_gain=-2.567 gap_improvement=0.0 weight=0.000
- apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json d=0 pair=[15, 17] type=paired_probe_neutral_proxy wall_gain=-16.854 gap_improvement=0.0 weight=0.000
- apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json d=0 pair=[4, 6] type=paired_probe_neutral_proxy wall_gain=9.873 gap_improvement=0.0 weight=0.000

## 边界

这些 row 的 `right_censored_counterfactual=True`，只用于 proof-risk / hard-negative calibration。任何 positive proxy 都不能直接升级为 full-replay positive；后续仍需完整 replay 或 exact pricing closure 验证。
