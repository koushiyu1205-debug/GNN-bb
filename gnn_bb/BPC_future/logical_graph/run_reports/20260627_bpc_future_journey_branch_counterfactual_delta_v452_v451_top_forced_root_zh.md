# Journey Branch Counterfactual Delta v452

日期：2026-06-27

## Summary

```text
row_count = 4
label_counts = {'strong_positive': 1, 'changed_timeout_no_effect_hard_negative': 3}
status_pair_counts = {'TIME_LIMIT->OPTIMAL': 1, 'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 3}
positive_walltime_gain_count = 1
```

## Rows

- seed61414_pair6_20: TIME_LIMIT 556.130s -> OPTIMAL 96.397s, gain=459.734s, pair=[6, 20], label=strong_positive
- apollo_seed61103_pair15_16: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[15, 16], label=changed_timeout_no_effect_hard_negative
- seed61744_pair12_15: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[12, 15], label=changed_timeout_no_effect_hard_negative
- sector_seed61104_pair11_18: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[11, 18], label=changed_timeout_no_effect_hard_negative

## Interpretation

v451 加权模型作为采样器找回 seed61414 `[6,20]` 强正例，但另外三条高分候选仍为 600s 假阳性。该 checkpoint 仍不能 production，但可用于 guided replay 数据采集。

## Exact-Safe Boundary

这些 rows 只来自已完成 replay 的日志/CSV，用于训练排序；不产生 official bound、certificate 或剪枝依据。
