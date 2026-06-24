# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 8
context_count = 2
ranking_pair_count = 0
label_counts = {}
context_counts = {'neutral_only_context': 2}
proxy_contradiction_counts = {}
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 context

- node=2 depth=1 baseline=[2,3], alts=4, spread=0.00422, best=00 [3, 17] wall_delta=-0.023025, worst=00 [13, 17] wall_delta=-0.018805
- node=0 depth=0 baseline=[2,3], alts=4, spread=0.002647, best=00 [3, 10] wall_delta=-0.004607, worst=00 [8, 14] wall_delta=-0.00196

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
当前没有形成有效排序对，需要继续补同 parent alternatives。
