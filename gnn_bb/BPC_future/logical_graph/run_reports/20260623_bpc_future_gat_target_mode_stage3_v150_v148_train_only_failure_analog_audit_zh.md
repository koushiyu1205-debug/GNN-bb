# 2026-06-23 BPC_future GAT Stage 3 v150 Train-only Failure Analog 审计报告

## 结论

本报告只做 offline train-only analog mining，不运行 BPC、pricing、RMP、worker 或 certificate。
目标是为 v148 focused pair failure 找训练 split 内的相似正负对，避免把 validation focused gate row 直接加入训练。

```text
failed_pair_count = 3
failure_split_counts = {'validation_gate_only': 3}
train_pair_universe_count = 63
analog_pair_count = 36
analog_row_index_count = 26
existing_boost_row_index_count = 44
combined_boost_row_index_count = 48
new_analog_row_index_count = 4
excluded_validation_row_indices = [183, 767, 768, 844, 845]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
recommendation = v150_training_allowed_as_diagnostic_with_train_only_analog_boost_and_feature_audit
all_checks_pass = true
```

## Artifact

- summary: `BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/summary.json`
- failed pairs: `BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/failed_pair_records.jsonl`
- train pair universe: `BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/train_pair_universe.jsonl`
- analog pairs: `BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/train_only_analog_pairs.jsonl`
- row selector: `BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/train_only_analog_row_indices.json`
- combined boost selector: `BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json`

## Failed Pair Split

| target | family | task | positive | negative | split class | diagnosis | raw | admission | delay-risk |
|---|---|---:|---:|---:|---|---|---:|---:|---:|
| 768>767 | random-wave | 20 | 768 | 767 | validation_gate_only | deep_structural_score_gap | -0.042223 | -0.002428 | -0.104074 |
| 183>845 | random-wave | 30 | 183 | 845 | validation_gate_only | deep_structural_score_gap | -0.060492 | -0.076350 | -0.059923 |
| 844>845 | random-wave | 30 | 844 | 845 | validation_gate_only | mixed_margin_failure | -0.042733 | -0.038630 | -0.014343 |

## Top Analogs

| target | analog pair | family | task | ROI delta | distance | same family | same task | existing boost pair |
|---|---|---|---:|---:|---:|---|---|---|
| 768>767 | 781>783 | random-wave | 20 | 2.876634 | 1.487161 | True | True | True |
| 768>767 | 780>783 | random-wave | 20 | 10.645973 | 1.492107 | True | True | True |
| 768>767 | 959>956 | random-wave | 20 | 1.328626 | 1.627062 | True | True | True |
| 768>767 | 969>966 | random-wave | 20 | 0.942495 | 1.628826 | True | True | True |
| 768>767 | 795>792 | random-wave | 20 | 2.411269 | 1.843331 | True | True | True |
| 768>767 | 795>793 | random-wave | 20 | 2.411269 | 2.035219 | True | True | True |
| 768>767 | 969>967 | random-wave | 20 | 0.942495 | 2.084568 | True | True | True |
| 768>767 | 782>783 | random-wave | 20 | 2.499917 | 2.155097 | True | True | True |
| 768>767 | 958>956 | random-wave | 20 | 0.731888 | 2.261599 | True | True | True |
| 768>767 | 810>811 | random-wave | 20 | 0.671808 | 2.329315 | True | True | False |
| 768>767 | 961>962 | random-wave | 20 | 1.547866 | 2.348930 | True | True | True |
| 768>767 | 960>962 | random-wave | 20 | 2.827841 | 2.402586 | True | True | True |
| 183>845 | 176>846 | random-wave | 30 | 0.827943 | 1.229806 | True | True | True |
| 183>845 | 177>843 | random-wave | 30 | 1.139771 | 1.975477 | True | True | True |
| 183>845 | 847>846 | random-wave | 30 | 1.174393 | 2.126270 | True | True | True |
| 183>845 | 842>843 | random-wave | 30 | 19.688071 | 2.197388 | True | True | True |
| 183>845 | 133>402 | random-wave | 50 | 7.245838 | 2.361222 | True | False | False |
| 183>845 | 795>793 | random-wave | 20 | 2.411269 | 2.774286 | True | False | True |
| 183>845 | 795>792 | random-wave | 20 | 2.411269 | 2.885384 | True | False | True |
| 183>845 | 781>783 | random-wave | 20 | 2.876634 | 2.921245 | True | False | True |
| 183>845 | 780>783 | random-wave | 20 | 10.645973 | 2.936515 | True | False | True |
| 183>845 | 969>967 | random-wave | 20 | 0.942495 | 2.996309 | True | False | True |
| 183>845 | 959>956 | random-wave | 20 | 1.328626 | 3.024177 | True | False | True |
| 183>845 | 969>966 | random-wave | 20 | 0.942495 | 3.096791 | True | False | True |
| 844>845 | 176>846 | random-wave | 30 | 0.827943 | 1.782982 | True | True | True |
| 844>845 | 847>846 | random-wave | 30 | 1.174393 | 1.878434 | True | True | True |
| 844>845 | 842>843 | random-wave | 30 | 19.688071 | 1.925626 | True | True | True |
| 844>845 | 177>843 | random-wave | 30 | 1.139771 | 2.231480 | True | True | True |
| 844>845 | 795>793 | random-wave | 20 | 2.411269 | 2.360670 | True | False | True |
| 844>845 | 795>792 | random-wave | 20 | 2.411269 | 2.536278 | True | False | True |
| 844>845 | 781>783 | random-wave | 20 | 2.876634 | 2.592364 | True | False | True |
| 844>845 | 780>783 | random-wave | 20 | 10.645973 | 2.600790 | True | False | True |

## 判断

- 该 selector 的 row index 语义是 `batch_impact_source_row_index`；
- validation failure rows 只用于查询相似训练样本，不进入输出 selector；
- 若后续训练 v150，只能作为 Stage 3 diagnostic，不是 Stage 4 candidate；
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
