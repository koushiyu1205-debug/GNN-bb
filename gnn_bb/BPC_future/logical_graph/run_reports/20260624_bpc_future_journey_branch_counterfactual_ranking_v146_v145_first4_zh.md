# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 2
context_count = 1
ranking_pair_count = 0
label_counts = {}
context_counts = {'neutral_only_context': 1}
proxy_contradiction_counts = {}
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 context

- node=2 depth=1 baseline=[12,16], alts=2, spread=0.000967, best=00 [12, 13] wall_delta=-380.00532, worst=00 [4, 12] wall_delta=-380.004353

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
当前没有形成有效排序对，需要继续补同 parent alternatives。
