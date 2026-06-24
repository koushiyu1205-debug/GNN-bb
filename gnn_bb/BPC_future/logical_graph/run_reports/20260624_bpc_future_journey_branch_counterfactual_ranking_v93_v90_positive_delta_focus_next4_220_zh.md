# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 4
context_count = 1
ranking_pair_count = 6
label_counts = {}
context_counts = {'neutral_only_context': 1}
proxy_contradiction_counts = {}
ranking_training_ready = True
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 context

- node=0 depth=0 baseline=[2,18], alts=4, spread=75.303944, best=00 [6, 13] wall_delta=-75.315375, worst=00 [2, 11] wall_delta=-0.011431

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
