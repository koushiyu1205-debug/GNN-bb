# Selector Context Fold Anatomy 审计

日期：2026-06-14

## 目标

复查 train-holdout rule-family 审计中失败的 context folds，区分失败来自
全 noop context 的 false positive，还是有正例 context 的 missed positive。
该审计只读已有 replay 与 selector summary，不运行求解器。

## 结论

all_checks_pass = true
selector_context_fold_anatomy = current
all_context_material_passing_folds = 17/28
twenty_context_material_passing_folds = 17/27
twenty_context_failure_kind_counts = {'missed_positive_context': 3, 'mixed_low_precision_or_recall_context': 3, 'false_positive_no_positive_context': 4}
twenty_low_positive_context_count = 8
twenty_high_positive_context_count = 17
production_validated_selector = false

解释：20-only 下仍有 context fold 失败，且失败同时包含两类相反形态：
某些 context 几乎全是 noop 但规则仍选中 false positive；另一些 context
存在正例但训练集选出的规则完全漏掉正例。这说明问题不是单一阈值偏松或
偏紧，而是 context/RMP trajectory 改变了 returned batch 的有效性。

## 20-only Failed Context Samples

| Context | Failure Kind | Total | Pos | Noop | Rule | Test TP/FP/FN |
|---|---|---:|---:|---:|---|---:|
| 05695ab419abfb4b | missed_positive_context | 3 | 3 | 0 | true_reduced_cost<=-6.72239 AND cost>=73.9194 | 0/0/3 |
| 1db815e33b9ea471 | missed_positive_context | 6 | 1 | 5 | true_reduced_cost<=-6.72239 AND cost>=73.9194 | 0/0/1 |
| 3c36c602289637b4 | mixed_low_precision_or_recall_context | 24 | 12 | 12 | true_reduced_cost<=-6.72239 AND cost>=73.9194 | 12/12/0 |
| 3f914a0d2b97fd27 | false_positive_no_positive_context | 5 | 0 | 5 | cost>=73.9194 AND true_reduced_cost<=-3.82619 | 0/1/0 |
| 774573a2964cb1c5 | mixed_low_precision_or_recall_context | 24 | 12 | 12 | true_reduced_cost<=-6.72239 AND cost>=73.9194 | 12/9/0 |
| 79de1ece885a7f67 | mixed_low_precision_or_recall_context | 15 | 3 | 12 | cost>=73.9194 AND true_reduced_cost<=-3.82619 | 3/6/0 |
| 7f2e531534d18ad2 | missed_positive_context | 11 | 2 | 9 | true_reduced_cost<=-6.72239 AND cost>=73.9194 | 0/0/2 |
| c5a59a95c2c9971a | false_positive_no_positive_context | 3 | 0 | 3 | cost>=73.9194 AND true_reduced_cost<=-3.82619 | 0/3/0 |
| d60fcf4b919b7d22 | false_positive_no_positive_context | 3 | 0 | 3 | cost>=73.9194 AND true_reduced_cost<=-3.82619 | 0/3/0 |
| e55ea3e7d277b6d1 | false_positive_no_positive_context | 3 | 0 | 3 | cost>=73.9194 AND true_reduced_cost<=-3.82619 | 0/3/0 |

## Interpretation

这进一步收紧当前根因：selector 不稳主要发生在 context 维度，
而不是 instance/dataset 粗粒度。下一步若继续 selector 路线，必须找
addition-before 的 RMP/context trajectory 特征；继续只调 true-RC / cost /
new-task-set 规则无法解释这些相反失败形态。
