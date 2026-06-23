# 2026-06-23 BPC_future GAT Stage 3 v139 Train-only Failure Analog 审计报告

## 结论

本报告只做 offline train-only analog mining，不运行 BPC、pricing、RMP、worker 或 certificate。
目标是为 v138 focused pair failure 找训练 split 内的相似正负对，避免把 validation focused gate row 直接加入训练。

```text
failed_pair_count = 4
failure_split_counts = {'train_visible': 2, 'validation_gate_only': 2}
train_pair_universe_count = 63
analog_pair_count = 32
analog_row_index_count = 32
existing_boost_row_index_count = 9
combined_boost_row_index_count = 37
new_analog_row_index_count = 28
excluded_validation_row_indices = [812, 813, 815]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
recommendation = v139_training_allowed_as_diagnostic_with_train_only_analog_boost_and_feature_audit
all_checks_pass = true
```

## Artifact

- summary: `BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/summary.json`
- failed pairs: `BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/failed_pair_records.jsonl`
- train pair universe: `BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/train_pair_universe.jsonl`
- analog pairs: `BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/train_only_analog_pairs.jsonl`
- row selector: `BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/train_only_analog_row_indices.json`
- combined boost selector: `BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json`

## Failed Pair Split

| target | family | task | positive | negative | split class | diagnosis | raw | admission | delay-risk |
|---|---|---:|---:|---:|---|---|---:|---:|---:|
| 812>815 | greedy-anchor | 20 | 812 | 815 | validation_gate_only | mixed_margin_failure | -0.040343 | -0.031348 | -0.019685 |
| 813>815 | greedy-anchor | 20 | 813 | 815 | validation_gate_only | mixed_margin_failure | -0.035937 | -0.027949 | -0.017414 |
| 779>398 | random-wave | 20 | 779 | 398 | train_visible | mixed_margin_failure | -0.035207 | -0.021463 | -0.008262 |
| 810>808 | random-wave | 20 | 810 | 808 | train_visible | near_margin_loss_tuning_candidate | 0.008552 | -0.000842 | -0.007609 |

## Top Analogs

| target | analog pair | family | task | ROI delta | distance | same family | same task | existing boost pair |
|---|---|---|---:|---:|---:|---|---|---|
| 812>815 | 1018>1021 | greedy-anchor | 20 | 4.236324 | 1.602888 | True | True | False |
| 812>815 | 1050>1051 | greedy-anchor | 20 | 2.430493 | 1.636099 | True | True | False |
| 812>815 | 1019>1021 | greedy-anchor | 20 | 4.784814 | 1.655436 | True | True | False |
| 812>815 | 993>991 | greedy-anchor | 20 | 2.217900 | 1.667063 | True | True | False |
| 812>815 | 1040>1041 | greedy-anchor | 20 | 1.116950 | 1.713456 | True | True | False |
| 812>815 | 990>991 | greedy-anchor | 20 | 0.989111 | 1.756637 | True | True | False |
| 812>815 | 1022>1024 | greedy-anchor | 20 | 0.692529 | 1.763614 | True | True | False |
| 812>815 | 1025>1024 | greedy-anchor | 20 | 1.340167 | 1.767441 | True | True | False |
| 813>815 | 1019>1021 | greedy-anchor | 20 | 4.784814 | 1.518459 | True | True | False |
| 813>815 | 1050>1051 | greedy-anchor | 20 | 2.430493 | 1.598694 | True | True | False |
| 813>815 | 990>991 | greedy-anchor | 20 | 0.989111 | 1.620113 | True | True | False |
| 813>815 | 1018>1021 | greedy-anchor | 20 | 4.236324 | 1.621031 | True | True | False |
| 813>815 | 993>991 | greedy-anchor | 20 | 2.217900 | 1.643997 | True | True | False |
| 813>815 | 1022>1024 | greedy-anchor | 20 | 0.692529 | 1.740726 | True | True | False |
| 813>815 | 1040>1041 | greedy-anchor | 20 | 1.116950 | 1.753688 | True | True | False |
| 813>815 | 1025>1024 | greedy-anchor | 20 | 1.340167 | 1.787206 | True | True | False |
| 779>398 | 960>962 | random-wave | 20 | 2.827841 | 2.313835 | True | True | False |
| 779>398 | 961>962 | random-wave | 20 | 1.547866 | 2.360237 | True | True | False |
| 779>398 | 795>792 | random-wave | 20 | 2.411269 | 2.476645 | True | True | False |
| 779>398 | 795>793 | random-wave | 20 | 2.411269 | 2.545680 | True | True | False |
| 779>398 | 781>783 | random-wave | 20 | 2.876634 | 2.608908 | True | True | True |
| 779>398 | 780>783 | random-wave | 20 | 10.645973 | 2.618098 | True | True | True |
| 779>398 | 959>956 | random-wave | 20 | 1.328626 | 2.793204 | True | True | False |
| 779>398 | 969>967 | random-wave | 20 | 0.942495 | 2.829806 | True | True | False |
| 810>808 | 958>956 | random-wave | 20 | 0.731888 | 1.657764 | True | True | False |
| 810>808 | 980>981 | random-wave | 20 | 2.458712 | 1.730244 | True | True | False |
| 810>808 | 980>978 | random-wave | 20 | 2.458712 | 1.819709 | True | True | False |
| 810>808 | 980>979 | random-wave | 20 | 2.458712 | 1.900402 | True | True | False |
| 810>808 | 795>793 | random-wave | 20 | 2.411269 | 2.215106 | True | True | False |
| 810>808 | 782>783 | random-wave | 20 | 2.499917 | 2.332269 | True | True | True |
| 810>808 | 795>792 | random-wave | 20 | 2.411269 | 2.337602 | True | True | False |
| 810>808 | 781>783 | random-wave | 20 | 2.876634 | 2.374051 | True | True | True |

## 判断

- 该 selector 的 row index 语义是 `batch_impact_source_row_index`；
- validation failure rows 只用于查询相似训练样本，不进入输出 selector；
- 若后续训练 v139，只能作为 Stage 3 diagnostic，不是 Stage 4 candidate；
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
