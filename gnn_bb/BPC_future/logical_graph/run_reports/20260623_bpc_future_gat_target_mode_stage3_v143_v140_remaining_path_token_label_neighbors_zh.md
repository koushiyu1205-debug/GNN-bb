# 2026-06-23 BPC_future GAT Stage 3 v143 Path-token 邻域标签审计

日期：2026-06-23

## 结论

本轮只扫描离线 dataset 的候选 path-token 邻域，检查 v142 失败候选在
train/validation split 中的相似路径标签分布；不运行模型推理、BPC、pricing、RMP 或 certificate。

```text
candidate_record_count = 12684
query_count = 6
pair_count = 3
pair_primary = negative_path_tokens_have_train_safe_conflict
positive_train_delay_biased_query_count = 0
negative_train_safe_conflict_query_count = 3
recommended_next_step = audit_negative_path_label_conflicts_and_signature_overlap
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
```

## Pair 邻域摘要

| context | pair | pair diagnosis | pos train safe/delay | neg train safe/delay | pos maxJ | neg maxJ |
|---|---|---|---:|---:|---:|---:|
| b36178f6655c5f75 | 813>815 | negative_path_tokens_have_train_safe_conflict | 0.800/0.200 | 0.650/0.350 | 0.222 | 0.222 |
| 84ae11479ed592d4 | 998>1001 | negative_path_tokens_have_train_safe_conflict | 0.700/0.300 | 1.000/0.000 | 0.286 | 0.500 |
| 9f80ae35ea87da5b | 183>845 | negative_path_tokens_have_train_safe_conflict | 1.000/0.000 | 0.850/0.150 | 0.222 | 0.286 |

## 判断

- v142 已证明 path-token 分支在当前 checkpoint 上伤害剩余 focused pair；
- v143 用 train split 邻域检查这种伤害是否来自数据邻域标签偏置；
- 若相似 train path 本身以 delay 为主，下一步应补 train-only 正 counterexample，而不是提高 path 分支权重；
- 若邻域标签支持当前正负标签，则应优先做 path 分支正则或 context-pair loss，而不是继续扩数据。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
production_ready = false
default_enabled = false
stage3_completed = false
stage4_candidate_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_path_token_label_neighbors_v143_v140_remaining_20260623/summary.json
queries = BPC_future/results/gat_batch_impact_path_token_label_neighbors_v143_v140_remaining_20260623/path_token_label_neighbor_queries.jsonl
pairs = BPC_future/results/gat_batch_impact_path_token_label_neighbors_v143_v140_remaining_20260623/path_token_label_neighbor_pairs.jsonl
```
