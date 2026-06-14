# BPC_future Root Cause Failure Matrix 报告

日期：2026-06-13

## 目标

把“做了很多为什么仍不行”拆成逐路线、逐证据的失败归因矩阵。
本报告只读取现有 evidence ledger，不运行 BPC / pricing / Pulse / RMP。

## 总结

all_checks_pass = true
route_count = 7
blocked_or_ruled_out_route_count = 7
production_direction_proven = false
missing_requirement_names = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup

根因短句：

5/10 is fixed-overhead sensitive; 20 has true-RC negative columns but batch impact is trajectory/context coupled; no production-validated addition-before selector exists.

## 路线矩阵

| Route | Status | Why not enough | Key evidence |
|---|---|---|---|
| Pulse wiring / materialization / certificate semantics | ruled_out_as_primary_root_cause | Worker/capture paths can safely add or record true-RC negative journeys without critical disagreement; the remaining failure is ROI. | phase8q_added_journeys=10; phase8q_added_new_task_sets=8; phase8q_all_time_limit=True; code_boundary_pass=True |
| Find or return more true-RC negative columns | ruled_out_as_sufficient_condition | 20-task runs can add true-RC negative journeys, including new task sets, but Phase 7O/8Q still end in TIME_LIMIT. | phase7o_all_time_limit=True; phase8q_all_time_limit=True; phase8q_added_journeys=10; phase8q_added_new_task_sets=8; phase8q_completion_bound_retry_count=0 |
| Expand worker budget or enable worker by default | ruled_out_for_5_10_safety | 5/10 scale is fixed-overhead sensitive: triggered mechanisms consistently worsen wall time, while non-triggered rows preserve official results. | triggered_rows=220; triggered_worse_count=220; triggered_better_count=0; nontriggered_official_changed=0 |
| Use true-RC threshold / task-set / sequence local features | not_production_validated | Replay-local selector candidates exist, but exact holdout still has false positives and false negatives; mixed task-set/sequence groups prove local column shape is insufficient. | recommended_selector_candidate=true_reduced_cost_<=_-12.430587; exact_false_positive_count=22; exact_false_negative_count=31; false_positive_new_task_set_noop_count=21; false_negative_new_task_set_improved_count=23; perfect_threshold_count=0; task_set_mixed_group_count=6; task_sequence_mixed_group_count=5; task_set_true_rc_improved_lower_count=2; task_set_true_rc_noop_lower_count=4 |
| Simple ML / batch-level selector | not_production_validated | Simple candidate and batch selectors show local signal, but strict context/instance/dataset gates do not pass simultaneously. | candidate_selector_passing_models=[]; batch_level_pre_batch_lod_precision=0.4392156862745098; batch_gate_positive_lod_precision=0.0; context_only_dataset_precision=0.5679012345679012 |
| Use simple RMP trajectory proxy selector | not_production_validated | Recovered RMP/context fields plus addition-before active-basis hash churn and degeneracy proxy fields still do not pass context/instance/dataset holdout. | enriched_feature_count=16; active_basis_hash_churn_context_folds=14; rmp_degeneracy_proxy_context_folds=9; robust_enriched_feature_count=0; best_multifeature_model=shallow_tree_depth3; best_multifeature_context_folds=15; robust_model_count=0 |
| Use single-context local replay success as production proof | forbidden_shortcut | Exact replay contains both high-impact and no-op candidates; single-context movement does not prove holdout-stable production ROI. | real_capture_high_impact_candidate_count=4; duplicate_noop_candidate_count=1; apollo_primal_deltas=[-41.372067, 49.762092]; apollo_wall_deltas=[-0.041594, -0.059809]; all_profile_statuses=['TIME_LIMIT', 'TIME_LIMIT', 'TIME_LIMIT', 'TIME_LIMIT', 'TIME_LIMIT', 'TIME_LIMIT'] |

## 结论

当前已经能解释为什么各条直觉路线不够：

- 继续扩大 worker / audit / probe 会伤害 5/10；
- 继续找更多 true-RC negative columns 不能自动改善 20；
- true-RC 阈值、task-set、sequence、简单 ML selector 都没有生产 holdout 证据；
- 单 context replay 或局部 RMP movement 只能作为 calibration，不是 production proof。

因此下一步仍是 calibration-only：扩展 no-certificate-effect exact-context replay，
证明 addition-before selector 同时通过 context / instance / dataset holdout，
之后才能进入 full BPC A/B。
