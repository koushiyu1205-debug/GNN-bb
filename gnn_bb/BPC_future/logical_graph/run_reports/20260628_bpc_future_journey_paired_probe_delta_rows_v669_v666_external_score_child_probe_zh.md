# Journey Paired-Probe Delta Rows

日期：2026-06-28

## 目的

把 paired child-probe 的 proof-risk evidence 转成 branch-action 数据集可读取的 calibration rows。输出是 proxy-only，不能当完整求解反事实标签。

## 机器字段

```text
input_row_count = 24
output_row_count = 2
input_paired_label_counts = {'hard_negative_proxy': 2, 'missing_baseline': 5, 'neutral_proxy': 7}
output_counterfactual_label_counts = {'paired_probe_hard_negative_proxy': 2}
skipped_counts = {'neutral_proxy_excluded': 7, 'not_convertible': 15}
rows_path = BPC_future/results/journey_paired_probe_delta_rows_v669_v666_external_score_child_probe_20260628/branch_counterfactual_delta_rows.jsonl
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 输出样本

- apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json d=0 pair=[5, 18] type=paired_probe_hard_negative_proxy wall_gain=-9.260 gap_improvement=-0.002354 weight=3.486
- apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json d=0 pair=[1, 18] type=paired_probe_hard_negative_proxy wall_gain=19.262 gap_improvement=-0.001218 weight=2.609

## 边界

这些 row 的 `right_censored_counterfactual=True`，只用于 proof-risk / hard-negative calibration。任何 positive proxy 都不能直接升级为 full-replay positive；后续仍需完整 replay 或 exact pricing closure 验证。
