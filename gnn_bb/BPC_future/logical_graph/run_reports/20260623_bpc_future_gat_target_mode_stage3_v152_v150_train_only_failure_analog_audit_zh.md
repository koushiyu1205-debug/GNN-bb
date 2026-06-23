# 2026-06-23 BPC_future GAT Stage 3 v152 Train-only Failure Analog 审计报告

## 结论

本报告只做 offline train-only analog mining，不运行 BPC、pricing、RMP、worker 或 certificate。
目标是为 v150 focused pair failure 找训练 split 内的相似正负对，避免把 validation focused gate row 直接加入训练。

```text
failed_pair_count = 2
failure_split_counts = {'validation_gate_only': 2}
train_pair_universe_count = 63
analog_pair_count = 24
analog_row_index_count = 20
existing_boost_row_index_count = 48
combined_boost_row_index_count = 52
new_analog_row_index_count = 4
excluded_validation_row_indices = [813, 814, 815]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
recommendation = v152_training_allowed_as_diagnostic_with_train_only_analog_boost_and_feature_audit
all_checks_pass = true
```

## Artifact

- summary: `BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/summary.json`
- failed pairs: `BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/failed_pair_records.jsonl`
- train pair universe: `BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/train_pair_universe.jsonl`
- analog pairs: `BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/train_only_analog_pairs.jsonl`
- row selector: `BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/train_only_analog_row_indices.json`
- combined boost selector: `BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json`

## Failed Pair Split

| target | family | task | positive | negative | split class | diagnosis | raw | admission | delay-risk |
|---|---|---:|---:|---:|---|---|---:|---:|---:|
| 813>814 | greedy-anchor | 20 | 813 | 814 | validation_gate_only | mixed_margin_failure | -0.036538 | -0.024236 | -0.015176 |
| 813>815 | greedy-anchor | 20 | 813 | 815 | validation_gate_only | mixed_margin_failure | -0.010646 | -0.004198 | -0.000282 |

## Top Analogs

| target | analog pair | family | task | ROI delta | distance | same family | same task | existing boost pair |
|---|---|---|---:|---:|---:|---|---|---|
| 813>814 | 990>991 | greedy-anchor | 20 | 0.989111 | 1.536489 | True | True | True |
| 813>814 | 1019>1021 | greedy-anchor | 20 | 4.784814 | 1.584389 | True | True | True |
| 813>814 | 1050>1051 | greedy-anchor | 20 | 2.430493 | 1.611308 | True | True | True |
| 813>814 | 1022>1023 | greedy-anchor | 20 | 0.692529 | 1.644889 | True | True | True |
| 813>814 | 1022>1024 | greedy-anchor | 20 | 0.692529 | 1.706208 | True | True | True |
| 813>814 | 993>991 | greedy-anchor | 20 | 2.217900 | 1.715736 | True | True | True |
| 813>814 | 1010>1011 | greedy-anchor | 20 | 3.733501 | 1.723571 | True | True | False |
| 813>814 | 1025>1023 | greedy-anchor | 20 | 1.340167 | 1.731159 | True | True | True |
| 813>814 | 1018>1021 | greedy-anchor | 20 | 4.236324 | 1.741466 | True | True | True |
| 813>814 | 1025>1024 | greedy-anchor | 20 | 1.340167 | 1.840586 | True | True | True |
| 813>814 | 1050>1053 | greedy-anchor | 20 | 2.430493 | 1.956637 | True | True | False |
| 813>814 | 985>983 | greedy-anchor | 20 | 1.953166 | 1.967477 | True | True | True |
| 813>815 | 1019>1021 | greedy-anchor | 20 | 4.784814 | 1.518459 | True | True | True |
| 813>815 | 1050>1051 | greedy-anchor | 20 | 2.430493 | 1.598694 | True | True | True |
| 813>815 | 990>991 | greedy-anchor | 20 | 0.989111 | 1.620113 | True | True | True |
| 813>815 | 1018>1021 | greedy-anchor | 20 | 4.236324 | 1.621031 | True | True | True |
| 813>815 | 993>991 | greedy-anchor | 20 | 2.217900 | 1.643997 | True | True | True |
| 813>815 | 1022>1024 | greedy-anchor | 20 | 0.692529 | 1.740726 | True | True | True |
| 813>815 | 1040>1041 | greedy-anchor | 20 | 1.116950 | 1.753688 | True | True | True |
| 813>815 | 1025>1024 | greedy-anchor | 20 | 1.340167 | 1.787206 | True | True | True |
| 813>815 | 1025>1023 | greedy-anchor | 20 | 1.340167 | 1.790044 | True | True | True |
| 813>815 | 1022>1023 | greedy-anchor | 20 | 0.692529 | 1.798895 | True | True | True |
| 813>815 | 985>983 | greedy-anchor | 20 | 1.953166 | 1.819493 | True | True | True |
| 813>815 | 985>982 | greedy-anchor | 20 | 1.953166 | 1.870563 | True | True | False |

## 判断

- 该 selector 的 row index 语义是 `batch_impact_source_row_index`；
- validation failure rows 只用于查询相似训练样本，不进入输出 selector；
- 若后续训练 v152，只能作为 Stage 3 diagnostic，不是 Stage 4 candidate；
- focused gate 仍必须要求 raw / admission / delay / strict 全部通过，不能因为 analog mining 放宽；
- ddcb / 7cb 这类 train-visible failure 仍需要 action-consequence feature audit，不能只靠加权重复训练解决。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT 仍只能做 discovery / ordering / finite-delay admission scheduling；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing full closure。
