# BPC_future GAT target-mode Stage 3 context-pair comparator 审计报告

日期：2026-06-23

## 结论

本报告只审计 `gat_batch_impact_training_v134_raw_action_context_pair_seed13_20260623` 中默认关闭的 context-pair comparator head，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v134_raw_action_context_pair_seed13_20260623/model.pt
metrics = BPC_future/results/gat_batch_impact_training_v134_raw_action_context_pair_seed13_20260623/metrics.json
pair_count = 78
existing_strict_pair_pass = 74/78
comparator_pair_pass = 73/78
comparator_repaired_existing_failure_count = 0
comparator_unresolved_existing_failure_count = 4
comparator_conflicts_existing_pass_count = 1
primary = comparator_does_not_repair_focused_failures
recommended_next_step = do_not_fuse_comparator_prioritize_action_consequence_feature_or_label_reaudit
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
```

## Top Contexts

| context | family | pairs | existing failed | comparator repaired | comparator unresolved | comparator conflicts |
|---|---|---:|---:|---:|---:|---:|
| 9f80ae35ea87da5b | random-wave | 2 | 2 | 0 | 2 | 0 |
| b36178f6655c5f75 | greedy-anchor | 4 | 1 | 0 | 1 | 0 |
| 62c86745ed2b3aaa | random-wave | 2 | 1 | 0 | 1 | 0 |
| 4e481a6307fca228 | sector-wave | 10 | 0 | 0 | 0 | 0 |
| ce3508e12ad69da7 | sector-wave | 6 | 0 | 0 | 0 | 0 |
| ddb0ce64af10976a | greedy-anchor | 4 | 0 | 0 | 0 | 0 |
| 7db256d4f7224cc6 | greedy-anchor | 3 | 0 | 0 | 0 | 0 |
| 1b5a36a64a700b58 | random-wave | 3 | 0 | 0 | 0 | 0 |
| 67925c0d2fd4abde | greedy-anchor | 3 | 0 | 0 | 0 | 0 |
| 5c522ff2995f86be | random-wave | 3 | 0 | 0 | 0 | 0 |
| a77e5457bde80b8e | random-wave | 3 | 0 | 0 | 0 | 0 |
| 7cb380a02e30e5a8 | random-wave | 3 | 0 | 0 | 0 | 0 |
| 03605a430acbd104 | random-wave | 3 | 0 | 0 | 0 | 0 |
| 45baa40751a0bf77 | sector-wave | 3 | 0 | 0 | 0 | 0 |
| f9d0b6b18a0a28d3 | greedy-anchor | 2 | 0 | 0 | 0 | 0 |
| 84ae11479ed592d4 | greedy-anchor | 2 | 0 | 0 | 0 | 0 |
| 39d7643d5a478407 | greedy-anchor | 2 | 0 | 0 | 0 | 0 |
| 4575716b3939cb89 | random-wave | 2 | 0 | 0 | 0 | 0 |
| ff6827bb236f4831 | random-wave | 2 | 0 | 0 | 0 | 0 |
| 77bc967e4038b08b | greedy-anchor | 2 | 0 | 0 | 0 | 0 |

## 判断

- comparator 只是离线诊断 head，不是 admission score，也不是 pricing oracle；
- 即使 comparator 能修复部分 focused pair，也不能直接升级 Stage 4；
- 下一步是否值得做 fused score 或 head 回流，取决于 comparator 是否能覆盖当前原 head 失败 pair。

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_context_pair_comparator_audit_v134_raw_action_context_pair_20260623/summary.json
pairs = BPC_future/results/gat_batch_impact_context_pair_comparator_audit_v134_raw_action_context_pair_20260623/context_pair_comparator_pair_rows.jsonl
contexts = BPC_future/results/gat_batch_impact_context_pair_comparator_audit_v134_raw_action_context_pair_20260623/context_pair_comparator_context_rows.jsonl
```
