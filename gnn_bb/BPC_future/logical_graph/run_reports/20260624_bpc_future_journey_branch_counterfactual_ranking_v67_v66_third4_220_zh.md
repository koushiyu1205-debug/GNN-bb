# Journey Branch Counterfactual Ranking Audit

日期：2026-06-24

## 目的

把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
counterfactual_row_count = 4
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

- node=0 depth=0 baseline=[8,18], alts=4, spread=0.005521, best=00 [3, 17] wall_delta=-0.022767, worst=01 [10, 20] wall_delta=-0.017246

## 判断

这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
当前没有形成有效排序对，需要继续补同 parent alternatives。

人工判断：该 context 的 spread 只有 `0.005521s`，全部 alternative 和 baseline 都是 220s external timeout，因此 V67 没有产生 ranking pair 是正确结果。后续不应把这组低 fractionality `0.125` 远端 root 候选当成强正例来源。
