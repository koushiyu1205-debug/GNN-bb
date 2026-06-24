# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 12
context_count = 6
ranking_pair_count = 6
label_counts = {'proof_cost_improved': 1, 'regression': 9, 'wall_improved': 2}
context_counts = {'mixed_positive_negative_context': 2, 'regression_only_context': 4}
proxy_contradiction_counts = {'fewer_child_negative_but_regressed': 6, 'more_child_negative_but_wall_improved': 1}
ranking_training_ready = True
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 context

- node=0 depth=0 baseline=[2,5], alts=2, spread=230.70339, best=01 [3, 18] wall_delta=-89.781081, worst=02 [5, 8] wall_delta=140.922309
- node=1 depth=1 baseline=[2,17], alts=2, spread=33.887138, best=03 [8, 18] wall_delta=77.206493, worst=04 [8, 17] wall_delta=111.093631
- node=2 depth=1 baseline=[3,17], alts=2, spread=40.529261, best=05 [3, 18] wall_delta=1.015413, worst=06 [13, 18] wall_delta=41.544674
- node=0 depth=0 baseline=[1,2], alts=2, spread=15.65818, best=07 [1, 18] wall_delta=-4.178415, worst=08 [1, 4] wall_delta=11.479765
- node=0 depth=0 baseline=[5,6], alts=2, spread=13.11501, best=09 [6, 7] wall_delta=65.67387, worst=10 [7, 11] wall_delta=78.78888
- node=1 depth=1 baseline=[5,7], alts=2, spread=1.922064, best=12 [6, 7] wall_delta=-0.255814, worst=11 [7, 10] wall_delta=1.66625

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
proxy_contradiction_counts 非空说明 child negative count / pool proxy 不能直接当排序标签。
