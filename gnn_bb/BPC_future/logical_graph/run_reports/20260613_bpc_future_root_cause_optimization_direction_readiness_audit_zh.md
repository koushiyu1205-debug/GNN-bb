# BPC_future 根因优化方向 Readiness 审计

日期：2026-06-13

最后复核：2026-06-14

## 目的

本报告只审计一件事：

> 当前证据是否已经足够支持一个 production 优化方向，在保证 exactness、5/10 不退化的前提下，大幅加速 20-task 最优求解。

结论不是。

当前根因解释已经有强证据，但优化方向尚未达到上线门槛。不能把“已经解释为什么失败”误报成“已经找到可安全加速的方案”。

## 当前 completion requirements

来自 `BPC_future/results/root_cause_evidence_ledger_20260613/summary.json` 的 `optimization_direction_readiness`：

| requirement | 当前值 | 解释 |
|---|---:|---|
| `has_small_no_regression_guard` | true | 未触发 worker/probe/audit 的 5/10 rows official result 不变；小规模必须靠严格 gate 或 no-op 保护 |
| `has_task5_noop_no_regression_guard` | true | task5 nontriggered rows official result 不变 |
| `has_task10_noop_no_regression_guard` | true | task10 nontriggered rows official result 不变 |
| `has_task10_triggered_regression_evidence` | true | task10 triggered rows 出现 `worsened=133` 和 `official_changed=61` |
| `has_full_5_10_production_ab_evidence` | false | 还没有 production-candidate full BPC A/B 同时证明 5/10 no-regression 与 selected 20 improvement |
| `has_20_negative_columns` | true | Phase 8Q 中 worker returned/added journeys 为 `10/10`，其中 new task sets 为 `8` |
| `has_local_rmp_impact` | true | Apollo20 exact-context replay 中 clean v2 capture 有 `4` 个 high-impact candidates，best delta `-137.116184` |
| `has_noop_counterexample` | true | duplicate/no-op replay 中 true-RC negative candidate 的 local RMP delta 为 `0.0` |
| `has_robust_all_fold_selector` | false | feature / model / rule-family selector 都没有同时通过 context / instance / dataset 全部 holdout |
| `has_production_validated_selector` | false | 还没有任何 selector 进入并通过 full BPC A/B；当前只能 calibration-only |
| `has_multi_context_clean_replay_calibration` | true | clean high-impact exact-context replay 已覆盖多个 20-task context family，包括 Apollo20、`tranq20_01` 和 `mt20_greedy_tranq_01` 相关 capture |
| `has_20_walltime_speedup_evidence` | false | Phase 7O / Phase 8Q worker rows 仍没有 20-task wall-time / status 稳定改善证据 |
| `production_direction_proven` | false | 上述必要条件没有同时成立 |

## 关键数字

```text
small_triggered_worse_count = 220
small_nontriggered_official_changed = 0
task5_nontriggered_official_changed = 0
task10_nontriggered_official_changed = 0
task10_triggered_worsened = 133
task10_triggered_official_changed = 61

phase8q_added_journeys = 10
phase8q_added_new_task_sets = 8

clean_replay_high_impact_candidate_count = 4
clean_replay_noop_candidate_count = 1
combined_replay_candidate_row_count = 5

capture_expansion_event_count = 0
capture_expansion_state_cap_tail_count = 2
global_capture_scan_event_count = 4
global_capture_scan_ready_20_context_count = 1
global_capture_scan_nonready_missing_vehicle_count = 3
replay_candidate_count = 40
replay_recommended_candidate_count = 3
replay_candidate_to_ready_20_context_gap = 2
counterfactual_capture_target_count = 3
counterfactual_capture_exact_context_count = 3
counterfactual_capture_target_coverage_event_count = 104
counterfactual_capture_target_near_match_count = 3
counterfactual_capture_target_exact_coverage_count = 2
counterfactual_capture_target_uncovered_count = 1
current_capture_target_coverage_event_count = 114
current_capture_target_exact_coverage_count = 3
current_capture_target_uncovered_count = 0
current_capture_targets_all_covered = true
counterfactual_tranq20_target_ready_case_count = 4
counterfactual_tranq20_target_high_impact_candidate_count = 26
counterfactual_tranq20_target_best_objective_delta = -70.009099
counterfactual_target_001_002_ready_case_count = 66
counterfactual_target_001_002_high_impact_candidate_count = 117
counterfactual_target_001_002_noop_candidate_count = 59
counterfactual_target_001_002_best_objective_delta = -267.639664

exact_replay_selector_candidate_row_count = 280
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
recommended_selector_precision = 0.89
recommended_selector_recall = 0.8516746411483254
recommended_selector_false_positive_count = 22
recommended_selector_false_negative_count = 31

selector_passing_model_count = 0
exact_replay_single_passing_feature_count = 0
exact_replay_pair_passing_holdout_gate_count = 0
exact_replay_model_all_holdout_passing_models = []
counterfactual_replay_selector_gate_with_target002_passing_feature_count = 4
counterfactual_replay_model_selector_with_target002_all_holdout_passing_count = 2
replay_local_selector_candidates_are_not_production = true

selector_micro_vs_fold_gate = current
robust_all_fold_passing_feature_count = 0
selector_model_micro_vs_fold_gate = current
robust_all_fold_passing_model_count = 0
selector_rule_family_search = current
rule_family_rule_count = 18887
rule_family_material_all_fold_passing_rule_count = 0
selector_rule_family_search_20only = current
rule_family_20only_rule_count = 18901
rule_family_20only_material_all_fold_passing_rule_count = 0
selector_rule_family_train_holdout = current
rule_family_train_context_material_passing_folds = 17/28
selector_rule_family_train_holdout_20only = current
rule_family_train_20only_context_material_passing_folds = 17/27
selector_context_fold_anatomy = current
context_fold_anatomy_twenty_false_positive_no_positive_context_count = 4
context_fold_anatomy_twenty_missed_positive_context_count = 3
selector_context_feature_anatomy = current
context_feature_mixed_instance_group_count = 2
context_feature_mixed_dataset_group_count = 2

phase7o_worker_rows = 24
phase8q_worker_rows = 35
```

## 为什么这能回答“到底为什么”

当前失败不是一个单点原因：

1. **5/10 不能不退化**：真实机制一触发就有固定开销，小规模收益空间不足；证据是 triggered small rows `220/220` 变差，而 non-triggered rows official result 不变。进一步拆分后，task10 triggered rows `worsened=133` 且 `official_changed=61`，说明 5/10 no-regression 目前只是 no-op gate 证据，不是 worker/probe 本身已有生产收益。
2. **20 不能稳定优化**：20 中有负列，也有局部高 impact batch，但 worker 加列没有稳定变成 wall-time / optimality 改善。
3. **负 RC 不够**：duplicate/no-op replay 证明 true-RC negative 也可能不改变 RMP。
4. **selector 缺失**：现有 addition-before 可见特征不能稳定判断 batch impact；feature / model / rule-family selector 都没有 robust all-fold passing 证据。
5. **selector 仍未证明**：clean exact-context replay 已扩展到多个 20-task context family，但还没有 production-validated selector，也没有 20-task wall-time speedup 证据。

target source-profile sweep 进一步收紧了这个判断：低上限 empty scan 证明 `pricing_max_dp_states=1` 会让 `tranq20_01` 命中目标上下文但 returned/captured batch 为 `0`；把同一窄目标提高到 `pricing_max_dp_states=1000` 后，`capture_target_003` 产生 `2` 个 replay-ready exact captures。离线 replay 显示 `4` 个 ready cases、`26` 个 high-impact candidates、full batch `4/4` 改善，best objective delta 为 `-70.009099`。
6. **target001/002 sweep 扩大了 calibration，但也暴露 no-op**：`target001/002` dp1000 capture 产生 `66` 个 ready cases、`176` 个 candidates、`440` 个 treatments；离线 replay 中 `288` 个 treatments 改善、`117` 个 high-impact candidates，但也有 `59` 个 no-op candidates。
7. **candidate-to-capture 缺口从“首批 target 未覆盖”转为“全局 clean replay 样本仍少”**：已有 `40` 个 observational replay candidates 和 `3` 个首批推荐候选；target002 pt0.3 复核后，首批 planned targets 已 `3/3` exact covered，但这仍只是 calibration 数据，不是 production selector 证明。
8. **target coverage 已更新为完整首批覆盖**：最新 target coverage 为 `capture_event_count=114`、`target_with_exact_capture_count=3`、`uncovered_target_count=0`；target002 pt0.3 新增 `73` 个 impact candidate rows，但仍未证明 5/10 no-regression 与 20 wall-time speedup。
9. **target002 复现 gap 的原因已定位**：旧 phase10h 的 Apollo cg1 returned batch 进入 `427b1308ea279e0c`，pt0.2 current-code mirror 的 cg1 returned batch 进入 `6907bf1e60739a97`；target002 从第一轮加列后就发生 trajectory drift，说明 early returned-batch composition 是根因的一部分。pt0.3 能 exact cover target002，说明可以扩展 calibration 数据，但不是 production gate。
10. **replay-local passing 不等于 production selector**：target002 pt0.3 后，280 条 exact replay impact rows 中出现 `4` 个 replay-local passing features 和 `2` 个 replay-local passing models；但 micro-vs-fold 复核仍是 `robust_all_fold_passing_feature_count = 0`、`robust_all_fold_passing_model_count = 0`，且还没有 full BPC A/B，因此这些只能作为 calibration candidates。
11. **exact replay selector candidate 仍未生产验证**：推荐规则 `true_reduced_cost <= -12.430587` 的 full-sample precision 为 `0.89`、recall 为 `0.8516746411483254`，但仍有 `22` 个 false positives 和 `31` 个 false negatives；不能作为 production selector。
12. **rule-family search 也失败**：`18887` 个单条件/两条件 addition-before conjunction 中，`material_all_fold_passing_rule_count = 0`；只保留 20-task rows 后，`18901` 个规则中仍为 `0`。
13. **训练式 rule-family holdout 仍失败**：每个 fold 都用训练集重新选规则，context material folds 仍只有 `17/28`，20-only 仍只有 `17/27`；失败不是 full-sample 规则选择方式造成的。
14. **context failure 形态相反**：20-only context folds 同时有 `4` 个 false-positive/no-positive contexts 和 `3` 个 missed-positive contexts；不是阈值整体偏松或偏紧。
15. **粗粒度 instance/dataset 解释也不够**：同一 instance 内有 `2` 组、同一 dataset 内有 `2` 组同时包含 low-positive 与 high-positive context；必须解释当前 RMP/context trajectory。

所以根本瓶颈可以更精确地写成：

> 系统缺少一个 addition-before、context-aware、低开销、可泛化的 returned-batch impact selector。它必须能区分 local RMP high-impact negative batch 和 duplicate/no-op negative batch，并且不能在 5/10 上触发固定开销回退；同时它还必须稳定控制早期 returned-batch composition，避免像 target002 这样从 cg1 就进入不同 active trajectory。

最新 exact replay selector gate 进一步说明，不能把全样本上看起来好的 `true_reduced_cost` 阈值当成这个 selector；target002 pt0.3 后出现的 replay-local passing features/models 也不能直接上线。它们在同样本、micro average 或部分 aggregate holdout 中有强信号，但一旦要求每个 context / instance / dataset fold 都稳定通过，仍会漏掉 improved rows 或引入 no-op false positives。

## 当前不能做的事

在 `production_direction_proven=false` 前，不能做：

- 打开 Pulse worker default；
- 打开 official certificate gate；
- 简单增加 worker / probe time limit；
- 把单个 Apollo20 replay 当成 20-scale speedup 证明；
- 用后验 active/incumbent 字段做线上 selector；
- 宣称目标完成。

## 下一步证据门槛

要把当前根因解释推进成可优化方向，至少需要：

1. 扩大 no-certificate-effect exact-context replay capture；
2. 每个样本必须包含完整 RMP pool、returned batch、true dual、cuts、effective fleet context、signature、arc options 和 start times；
3. replay manifest 必须 ready，runner control RMP 必须 `OPTIMAL`，single-candidate delta 必须 finite；
4. replay impact dataset 至少覆盖多个独立 20-task contexts，而不是单个 Apollo context；
5. selector 只能使用 addition-before 可见特征；
6. selector 必须通过跨 dataset / 跨 instance gate；
7. 通过 selector 后还必须跑 5/10 no-regression gate 和 20 hard repeat A/B。

## 审计结论

当前可以说：

> 根因解释已经成立：小规模是 fixed-overhead 敏感，20 规模是 returned-batch trajectory selector 缺失。

但不能说：

> 已经找到了可上线优化方向。

当前状态仍是：

```text
check_root_cause_known_but_optimization_direction_unproven = true
has_robust_all_fold_selector = false
has_production_validated_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```
