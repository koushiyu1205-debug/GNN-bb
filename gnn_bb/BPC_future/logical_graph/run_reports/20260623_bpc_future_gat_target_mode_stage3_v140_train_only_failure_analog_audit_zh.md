# 2026-06-23 BPC_future GAT Stage 3 v140 Train-only Failure Analog 审计报告

## 结论

本报告只做 offline train-only analog mining，不运行 BPC、pricing、RMP、worker 或 certificate。
目标是为 v138 focused pair failure 找训练 split 内的相似正负对，避免把 validation focused gate row 直接加入训练。

```text
failed_pair_count = 3
failure_split_counts = {'validation_gate_only': 3}
train_pair_universe_count = 63
analog_pair_count = 24
analog_row_index_count = 29
existing_boost_row_index_count = 37
combined_boost_row_index_count = 44
new_analog_row_index_count = 7
excluded_validation_row_indices = [813, 815, 848, 849, 998, 1001]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
recommendation = v140_training_allowed_as_diagnostic_with_train_only_analog_boost_and_feature_audit
all_checks_pass = true
```

## Artifact

- summary: `BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/summary.json`
- failed pairs: `BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/failed_pair_records.jsonl`
- train pair universe: `BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/train_pair_universe.jsonl`
- analog pairs: `BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/train_only_analog_pairs.jsonl`
- row selector: `BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/train_only_analog_row_indices.json`
- combined boost selector: `BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json`

## Failed Pair Split

| target | family | task | positive | negative | split class | diagnosis | raw | admission | delay-risk |
|---|---|---:|---:|---:|---|---|---:|---:|---:|
| 813>815 | greedy-anchor | 20 | 813 | 815 | validation_gate_only | near_margin_loss_tuning_candidate | -0.008139 | -0.005949 | -0.003045 |
| 998>1001 | greedy-anchor | 20 | 998 | 1001 | validation_gate_only | mixed_margin_failure | -0.026710 | -0.021564 | -0.012455 |
| 849>848 | random-wave | 30 | 849 | 848 | validation_gate_only | mixed_margin_failure | -0.029570 | -0.043314 | -0.031283 |

## Top Analogs

| target | analog pair | family | task | ROI delta | distance | same family | same task | existing boost pair |
|---|---|---|---:|---:|---:|---|---|---|
| 813>815 | 1019>1021 | greedy-anchor | 20 | 4.784814 | 1.518459 | True | True | True |
| 813>815 | 1050>1051 | greedy-anchor | 20 | 2.430493 | 1.598694 | True | True | True |
| 813>815 | 990>991 | greedy-anchor | 20 | 0.989111 | 1.620113 | True | True | True |
| 813>815 | 1018>1021 | greedy-anchor | 20 | 4.236324 | 1.621031 | True | True | True |
| 813>815 | 993>991 | greedy-anchor | 20 | 2.217900 | 1.643997 | True | True | True |
| 813>815 | 1022>1024 | greedy-anchor | 20 | 0.692529 | 1.740726 | True | True | True |
| 813>815 | 1040>1041 | greedy-anchor | 20 | 1.116950 | 1.753688 | True | True | True |
| 813>815 | 1025>1024 | greedy-anchor | 20 | 1.340167 | 1.787206 | True | True | True |
| 998>1001 | 1019>1021 | greedy-anchor | 20 | 4.784814 | 1.332612 | True | True | True |
| 998>1001 | 1050>1051 | greedy-anchor | 20 | 2.430493 | 1.386948 | True | True | True |
| 998>1001 | 990>991 | greedy-anchor | 20 | 0.989111 | 1.469332 | True | True | True |
| 998>1001 | 993>991 | greedy-anchor | 20 | 2.217900 | 1.579271 | True | True | True |
| 998>1001 | 1040>1041 | greedy-anchor | 20 | 1.116950 | 1.622248 | True | True | True |
| 998>1001 | 1018>1021 | greedy-anchor | 20 | 4.236324 | 1.642242 | True | True | True |
| 998>1001 | 985>983 | greedy-anchor | 20 | 1.953166 | 1.722473 | True | True | False |
| 998>1001 | 1025>1023 | greedy-anchor | 20 | 1.340167 | 1.780349 | True | True | False |
| 849>848 | 847>846 | random-wave | 30 | 1.174393 | 1.392297 | True | True | True |
| 849>848 | 176>846 | random-wave | 30 | 0.827943 | 1.838427 | True | True | True |
| 849>848 | 842>843 | random-wave | 30 | 19.688071 | 2.369352 | True | True | False |
| 849>848 | 781>783 | random-wave | 20 | 2.876634 | 2.445957 | True | False | True |
| 849>848 | 780>783 | random-wave | 20 | 10.645973 | 2.497264 | True | False | True |
| 849>848 | 959>956 | random-wave | 20 | 1.328626 | 2.528533 | True | False | True |
| 849>848 | 177>843 | random-wave | 30 | 1.139771 | 2.599851 | True | True | False |
| 849>848 | 969>966 | random-wave | 20 | 0.942495 | 2.679897 | True | False | False |

## 判断

- 该 selector 的 row index 语义是 `batch_impact_source_row_index`；
- validation failure rows 只用于查询相似训练样本，不进入输出 selector；
- 若后续训练 v140，只能作为 Stage 3 diagnostic，不是 Stage 4 candidate；
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
