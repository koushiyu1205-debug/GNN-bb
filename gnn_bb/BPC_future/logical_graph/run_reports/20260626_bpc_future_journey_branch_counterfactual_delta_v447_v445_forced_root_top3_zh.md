# Journey Branch Counterfactual Delta v447

日期：2026-06-26

## Summary

```text
row_count = 3
label_counts = {'observed_walltime_gain': 1, 'changed_timeout_no_effect_hard_negative': 2}
status_pair_counts = {'TIME_LIMIT->TIME_LIMIT': 1, 'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 2}
positive_walltime_gain_count = 1
```

## Rows

- seed61414_pair13_17: TIME_LIMIT 556.130s -> TIME_LIMIT 427.521s, gain=128.610s, pair=[13, 17], label=observed_walltime_gain
- seed61103_pair15_19: EXTERNAL_TIME_LIMIT 600.017s -> EXTERNAL_TIME_LIMIT 600.017s, gain=0.000s, pair=[15, 19], label=changed_timeout_no_effect_hard_negative
- seed61520_pair4_8: EXTERNAL_TIME_LIMIT 600.017s -> EXTERNAL_TIME_LIMIT 600.016s, gain=0.000s, pair=[4, 8], label=changed_timeout_no_effect_hard_negative

## Exact-Safe Boundary

这些 rows 只来自已完成 replay 的日志/CSV，用于训练排序；不产生 official bound、certificate 或剪枝依据。
