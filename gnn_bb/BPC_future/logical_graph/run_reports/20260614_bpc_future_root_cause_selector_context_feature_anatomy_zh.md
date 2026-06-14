# Selector Context Feature Anatomy 审计

日期：2026-06-14

## 目标

按 context 汇总 exact replay rows 的正例率、实例、数据集、control objective、
true-RC/cost 范围，并与 context fold failure kind 对齐。
该审计只读已有 replay 与 selector summary，不运行求解器。

## 结论

all_checks_pass = true
selector_context_feature_anatomy = current
row_count = 279
context_count = 27
low_positive_context_count = 8
high_positive_context_count = 17
mixed_instance_group_count = 2
mixed_dataset_group_count = 2
failure_kind_counts = {'false_positive_no_positive_context': 4, 'material_pass_or_not_failed': 17, 'missed_positive_context': 3, 'mixed_low_precision_or_recall_context': 3}
production_validated_selector = false

解释：同一 instance / dataset 内同时存在 low-positive 与 high-positive context，
所以失败不能归因到实例或数据集粗粒度差异。context/RMP trajectory 本身必须
进入 selector 解释。

## Mixed Instance Groups

| Instance | Contexts | Min Rate | Max Rate | Low | High |
|---|---:|---:|---:|---:|---:|
| apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | 15 | 0.000000 | 1.000000 | 6 | 8 |
| tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 | 9 | 0.000000 | 1.000000 | 2 | 6 |

## Low Positive Context Samples

| Context | Rate | Rows | Instance | Dataset | Control Objective | Failure |
|---|---:|---:|---|---|---|---|
| e55ea3e7d277b6d1 | 0.000000 | 3 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [921.640296] | false_positive_no_positive_context |
| d60fcf4b919b7d22 | 0.000000 | 3 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [923.116819] | false_positive_no_positive_context |
| c5a59a95c2c9971a | 0.000000 | 3 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [721.502279] | false_positive_no_positive_context |
| 46e7a2883459d4fb | 0.000000 | 4 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_target002_capture_pt03_r3_20260613 | [766.96965575] | material_pass_or_not_failed |
| 3f914a0d2b97fd27 | 0.000000 | 5 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_target002_capture_pt03_r3_20260613 | [766.81749575] | false_positive_no_positive_context |
| 1db815e33b9ea471 | 0.166667 | 6 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [761.626550333] | missed_positive_context |
| 7f2e531534d18ad2 | 0.181818 | 11 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [761.626550333] | missed_positive_context |
| 79de1ece885a7f67 | 0.200000 | 15 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [703.486314444] | mixed_low_precision_or_recall_context |

## High Positive Context Samples

| Context | Rate | Rows | Instance | Dataset | Control Objective | Failure |
|---|---:|---:|---|---|---|---|
| 080a188d2484ee3e | 1.000000 | 58 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [1061.554044] | material_pass_or_not_failed |
| 8c60fac6ce5f475f | 1.000000 | 30 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [800.4027645] | material_pass_or_not_failed |
| 827ddca748a70f26 | 1.000000 | 16 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_target002_capture_pt03_r3_20260613 | [859.3571305] | material_pass_or_not_failed |
| c30ee076e24e6460 | 1.000000 | 13 | tranquillitatis_balmer_like_20km_tasks20_01_seed21000 | root_cause_counterfactual_target_capture_dp1000_tranq20_20260613 | [838.0048415] | material_pass_or_not_failed |
| 7ca23eb07bf4da54 | 1.000000 | 12 | tranquillitatis_balmer_like_20km_tasks20_01_seed21000 | root_cause_counterfactual_target_capture_dp1000_tranq20_20260613 | [767.9957425] | material_pass_or_not_failed |
| 691a0f9c2446aabc | 1.000000 | 8 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | root_cause_target002_capture_pt03_r3_20260613 | [859.3571305] | material_pass_or_not_failed |
| f67cf0852ea7df8b | 1.000000 | 6 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [761.814403] | material_pass_or_not_failed |
| 51514350b5894d8e | 1.000000 | 3 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 | root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 | [718.540357] | material_pass_or_not_failed |

## Interpretation

这进一步说明：当前 selector 失败不是因为 Apollo/Tranq 或某个 replay dataset
整体难，而是同一粗粒度分组内部的 context 状态已经改变了 returned batch
的 downstream impact。下一步证据应聚焦 addition-before 的 RMP/context
trajectory 特征，而不是继续堆 true-RC/cost/new-task-set 局部规则。
