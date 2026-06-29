# Journey Branch Full Replay Gap Delta

日期：2026-06-28

## 目的

把强制 Ryan-Foster root pair 的完整 600 秒 replay 结果转成弱 gap/fathom 标签。该脚本只读既有 CSV/JSONL，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
baseline_pair = [4, 12]
row_count = 1
label_type_counts = {'right_censored_neutral': 1}
status_pair_counts = {'OPTIMAL->OPTIMAL': 1}
skipped_counts = {}
usable_for_counterfactual_training = false
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 行级结果

| alternative_pair | label | gap_improvement | primal_improvement | fathom_gain | CB/final-judge retry gain | wall_gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| [6, 15] | right_censored_neutral | 0.000000 | 0.000000 | -1 | 2 | 101.845444 |

## 解释

这些 row 只说明在同一 600 秒截断下，alternative pair 改善了 gap、incumbent 或局部 fathom 结构；因为 baseline 和 alternative 都仍是 EXTERNAL_TIME_LIMIT，所以不能算 strict full-replay positive，也不能用于 official prune/certificate。
