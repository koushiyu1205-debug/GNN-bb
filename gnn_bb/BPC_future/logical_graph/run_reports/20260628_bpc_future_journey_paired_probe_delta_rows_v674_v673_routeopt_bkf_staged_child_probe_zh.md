# Journey Paired-Probe Delta Rows

日期：2026-06-28

## 目的

把 paired child-probe 的 proof-risk evidence 转成 branch-action 数据集可读取的 calibration rows。输出是 proxy-only，不能当完整求解反事实标签。

## 机器字段

```text
input_row_count = 36
output_row_count = 0
input_paired_label_counts = {'neutral_proxy': 24}
output_counterfactual_label_counts = {}
skipped_counts = {'neutral_proxy_excluded': 24, 'not_convertible': 12}
rows_path = BPC_future/results/journey_paired_probe_delta_rows_v674_v673_routeopt_bkf_staged_child_probe_20260628/branch_counterfactual_delta_rows.jsonl
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 输出样本


## 边界

这些 row 的 `right_censored_counterfactual=True`，只用于 proof-risk / hard-negative calibration。任何 positive proxy 都不能直接升级为 full-replay positive；后续仍需完整 replay 或 exact pricing closure 验证。
