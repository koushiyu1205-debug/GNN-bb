# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 16
context_count = 3
ranking_pair_count = 28
label_counts = {'proof_cost_improved': 1, 'regression': 3, 'wall_improved': 1}
context_counts = {'mixed_positive_negative_context': 1, 'neutral_only_context': 2}
proxy_contradiction_counts = {'fewer_child_negative_but_regressed': 3}
minimal_ranking_signal_ready = True
strict_ranking_training_ready = False
strong_positive_count = 5
strong_positive_context_count = 2
strong_positive_instance_count = 2
strong_positive_time_window_family_count = 1
positive_holdout_context_count = 0
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 context

- node=0 depth=0 baseline=[4,12], alts=4, spread=112.842762, best=00 [12, 15] wall_delta=-86.529511, worst=00 [8, 20] wall_delta=26.313251
- node=0 depth=0 baseline=[2,18], alts=6, spread=123.411709, best=00 [2, 6] wall_delta=-123.396565, worst=00 [2, 15] wall_delta=0.015144
- node=0 depth=0 baseline=[12,13], alts=6, spread=98.80104, best=00 [3, 14] wall_delta=-57.992307, worst=00 [11, 14] wall_delta=40.808733

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
proxy_contradiction_counts 非空说明 child negative count / pool proxy 不能直接当排序标签。
