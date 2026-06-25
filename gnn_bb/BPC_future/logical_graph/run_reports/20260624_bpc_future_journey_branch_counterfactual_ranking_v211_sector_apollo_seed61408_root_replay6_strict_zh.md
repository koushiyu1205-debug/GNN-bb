# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 6
context_count = 1
ranking_pair_count = 14
label_counts = {'proof_cost_improved': 2, 'regression': 2, 'wall_improved': 4}
context_counts = {'mixed_positive_negative_context': 1}
proxy_contradiction_counts = {'fewer_child_negative_but_regressed': 1, 'more_child_negative_but_wall_improved': 1}
minimal_ranking_signal_ready = True
strict_ranking_training_ready = False
strong_positive_count = 4
strong_positive_context_count = 1
strong_positive_instance_count = 1
strong_positive_time_window_family_count = 1
positive_holdout_context_count = 0
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 context

- node=0 depth=0 baseline=[1,6], alts=6, spread=45.171207, best=00 [6, 16] wall_delta=-45.692556, worst=00 [14, 19] wall_delta=-0.521349

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
proxy_contradiction_counts 非空说明 child negative count / pool proxy 不能直接当排序标签。
