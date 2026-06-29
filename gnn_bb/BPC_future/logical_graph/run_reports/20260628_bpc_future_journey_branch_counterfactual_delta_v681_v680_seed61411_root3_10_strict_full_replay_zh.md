# Journey Branch Full Replay Gap Delta

日期：2026-06-28

## 目的

把强制 Ryan-Foster pair 的完整 replay 结果转成 branch counterfactual 标签：both-OPTIMAL 且目标值一致时生成严格 wall-time 正/负例；未闭环时只生成弱 gap/fathom 辅助标签。该脚本只读既有 CSV/JSONL，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
baseline_pair = [2, 10]
row_count = 1
label_type_counts = {'strong_positive': 1}
status_pair_counts = {'OPTIMAL->OPTIMAL': 1}
skipped_counts = {}
strict_full_replay_positive_count = 1
counterfactual_training_count = 1
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 行级结果

| alternative_pair | label | gap_improvement | primal_improvement | fathom_gain | CB/final-judge retry gain | wall_gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| [3, 10] | strong_positive | 0.000000 | 0.000000 | -14 | 28 | 294.995732 |

## 解释

both-OPTIMAL 且目标值一致的 row 可以作为严格 wall-time counterfactual 训练样本；right-censored row 只能说明在同一截断下 alternative pair 改善了 gap、incumbent 或局部 fathom 结构，不能算 strict full-replay positive。所有 row 都不能用于 official prune/certificate。
