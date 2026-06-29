# Journey Branch Counterfactual Delta v449

日期：2026-06-27

## Summary

```text
row_count = 6
label_counts = {'changed_timeout_no_effect_hard_negative': 6}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 5, 'TIME_LIMIT->TIME_LIMIT': 1}
positive_walltime_gain_count = 0
```

## Rows

- seed61206_pair3_5: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[3, 5], label=changed_timeout_no_effect_hard_negative
- seed61206_pair3_9: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[3, 9], label=changed_timeout_no_effect_hard_negative
- seed61414_pair16_17: TIME_LIMIT 556.130s -> TIME_LIMIT 570.819s, gain=-14.688s, pair=[16, 17], label=changed_timeout_no_effect_hard_negative
- seed61520_pair8_9: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[8, 9], label=changed_timeout_no_effect_hard_negative
- seed61001_random_pair8_16: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[8, 16], label=changed_timeout_no_effect_hard_negative
- seed61411_random_pair2_4: EXTERNAL_TIME_LIMIT 600.000s -> EXTERNAL_TIME_LIMIT 600.000s, gain=0.000s, pair=[2, 4], label=changed_timeout_no_effect_hard_negative

## Interpretation

本批按 v442 right-censored child-probe corrected-bound gain 继续外推，但 6 条 full replay 没有产生新的 wall-time 正例。这说明 child-probe gain 只能做辅助特征，不能作为 root pair 选择主准则。

## Exact-Safe Boundary

这些 rows 只来自已完成 replay 的日志/CSV，用于训练排序；不产生 official bound、certificate 或剪枝依据。
