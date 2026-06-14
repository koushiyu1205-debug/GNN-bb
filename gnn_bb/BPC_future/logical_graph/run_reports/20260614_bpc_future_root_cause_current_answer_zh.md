# BPC_future 根因当前答案

日期：2026-06-14

## 目的

本报告是当前根因工作的短入口，只回答当前能确定什么、不能确定什么、
以及为什么目标仍不能标记完成。

它只读已有 evidence summaries，不运行 BPC / pricing / RMP / Pulse，
也不改变 worker、certificate 或 solver 默认行为。

## 当前答案

5/10 失败的直接原因是固定开销敏感；20 失败的根因不是找不到负列，而是 returned batch 对当前 RMP active-basis / dual trajectory 的影响强上下文耦合；当前还没有 production-validated addition-before selector。

前面大量工作证明了 Pulse / worker / capture 路径可以安全地产生或记录 true-RC negative journeys，并且不应误造 official certificate；但这些 true-RC negative journeys 并不自动等价于求解收益。最新 schema gap 审计显示，当前 280 行 replay selector 数据能完整 join 到 122 个 manifest case，但 full active-basis snapshot 没有真正填充，pool/returned-batch composition 只能从 manifest 派生且未持久化进 candidate rows，forbidden pressure 的旧 hash-only 缺口已被 targeted component payload 部分补上。全局 candidate rows 里确实另有 62 行 complete snapshot，其中 14 行来自 active-basis snapshot smoke，48 行来自 targeted component-payload addition-before rows；但主 280 行 replay selector 数据里 complete snapshot 仍为 0，所以当前不是已有样本未利用，而是还没有足够的、已合入 selector holdout 的 no-certificate-effect full-snapshot/component-payload 数据。唯一未命中的 priority context 是 target002 pt0.3；probe matrix 显示当前代码下复现 probe 数为 0，而 trajectory branch 审计显示同一 active hash 附近仍会发生 pool / forbidden signature / RMP objective / returned-batch composition 分叉。因此这不是简单重跑 runbook 就能消除的缺口，而是当前 production selector 必须显式建模的上下文耦合。最新 component capture schema contract 进一步说明：现有 config-matched capture 的 78 个事件已经完整记录 active-basis、pool、returned-batch 和 forbidden-signature payload，其中 12 个事件包含显式 forbidden signature list。最新 component-payload 审计已经把其中 target002 ready payload 转成 6 个 ready local RMP replay case、48 行 addition-before candidate rows，且 active-basis、pool、returned-batch、显式 forbidden-signature 字段完整。这消除了“rows 能不能构造”的阻塞，但它仍只是单 target context calibration evidence；还没有证明 production selector、5/10 不退化或 20 wall-time speedup。最新 component-payload selector holdout extension 已经做了这一步的最小合并检查：base 280 行 + component 48 行 = 328 行，component-only 是单类正样本，合并后 robust all-holdout feature/model 仍为 0。所以现在的问题已经不是字段完全不能构造，而是这些字段尚未在足够宽的负例/上下文分布上产生可泛化选择规则。最新 selector holdout gap matrix 把缺口进一步钉死：全局 630 条 candidate rows 里只有 62 条 complete full-snapshot rows，其中 label mix 是 improved:59 / noop:3，mixed-label context 数为 0；48 条 complete explicit-forbidden rows 全是 improved。因此下一步必须补 negative/noop 与 mixed full-snapshot contexts，不是继续增加单类 positive payload rows。最新 selector holdout target priority matrix 已把这个缺口落到具体 context：当前有 15 个 priority contexts，其中 7 个 mixed contexts 缺 complete full-snapshot，12 个 noop contexts 缺 complete full-snapshot，且仍有 6 个 priority contexts 不在现有 collection manifest 覆盖内。priority collection runbook 进一步显示，这 6 个未覆盖 context 中有 3 个 Apollo target002 contexts 可用现有 profile/config 生成补采命令，另外 3 个来自 baseline/smoke source，当前没有可解析 source profile，必须显式当作 unsupported，而不能当作已补采。实际执行这条 priority collection command 后，采到 12 个 no-certificate-effect 且 active-basis 完整的 capture events，但 3 个 expected target contexts 命中数为 0，ready_for_selector_holdout=false。这把问题进一步收紧为：同一实例/配置/profile 重跑能安全采集新上下文，但不能保证回到 selector 最缺的 mixed/noop target contexts；生产规则必须建模完整 context/trajectory，而不是假设 source profile rerun 能复原目标点。priority capture miss 诊断进一步说明，3 个 expected contexts 中有 2 个没有到达 source active hash，另 1 个虽到达同 active hash，但 pool signature、forbidden signature、returned task-set batch 和 pricing outcome 均发生漂移。最新 selector holdout context action plan 把剩余缺口拆成 12 个高优先context：7 个已经能作为 complete snapshot calibration seed，5 个仍未闭合。这 5 个里有 2 个必须捕获 trajectory variant 才能回到 source active-basis，1 个必须完整匹配 pool/forbidden/returned-batch/RMP/pricing 组件，1 个要重跑或重审既有 manifest command，1 个要先恢复 source profile / instance mapping。因此当前失败不是因为某个单一 Pulse 开关没打开，而是 production selector 所需的上下文分布还没有被稳定采到；盲目重跑同 profile 或只看 active hash 都不能闭环。

## 最新 worker 负列 ROI 阻塞结论

```json
{
  "interpretation": "Worker paths can add true-RC negative columns, including new task sets and support-changing replacements, without critical disagreement.  However, Phase 7O non-baseline rows all worsened and Phase 8Q worker-added rows did not produce improved rows.  Therefore negative-column discovery is not sufficient; the unresolved blocker is returned-batch impact and low-overhead addition-before selection.",
  "phase7o": {
    "critical_disagreement_rows": 0,
    "nonbaseline_rows": 96,
    "nonbaseline_worsened_rows": 96,
    "row_count": 108,
    "worker_added_journeys": 63,
    "worker_added_new_task_sets": 30,
    "worker_added_rows": 20,
    "worker_added_support_changing": 13
  },
  "phase8q": {
    "critical_disagreement_rows": 0,
    "improved_without_worker_added_count": 1,
    "nonbaseline_improved_rows": 1,
    "nonbaseline_rows": 28,
    "row_count": 35,
    "worker_added_journeys": 10,
    "worker_added_new_task_sets": 8,
    "worker_added_rows": 3,
    "worker_added_support_changing": 2
  },
  "status": "worker_negative_columns_not_sufficient_for_roi"
}
```

解释：worker 已经能加入 true-RC negative journeys，包括 new task-set 和 support-changing 列；但 Phase 7O expanded 的 non-baseline rows 全部 worsened，Phase 8Q 中 worker-added rows 也没有成为 improved rows。这直接排除了“继续找更多或更负负列即可优化”的充分性。

## 最新 component capture 结论

```json
{
  "capture_event_count": 78,
  "code_supports_explicit_forbidden_payload": true,
  "complete_active_basis_events": 78,
  "complete_pool_events": 78,
  "forbidden_explicit_events": 12,
  "holdout_runbook_enables_explicit_forbidden_payload": true,
  "returned_batch_complete_events": 78,
  "returned_batch_nonempty_events": 60
}
```

解释：active-basis、pool、returned-batch payload 已经在当前 config-matched capture 中完整可观测；目标补采已经验证 explicit forbidden signature list 可落盘。

## 最新 component payload rows 结论

```json
{
  "candidate_row_count": 48,
  "explicit_forbidden_true_count": 48,
  "high_impact_candidate_count": 48,
  "noop_candidate_count": 0,
  "raw_capture_case_count": 12,
  "ready_case_count": 6,
  "runs_local_rmp_replay": true
}
```

解释：component payload 已经可以转成 addition-before candidate rows，且显式 forbidden-signature 字段完整。这只是校准数据构造证据，不是 production selector、BPC speedup 或 certificate effect。

## 最新 component payload selector holdout extension 结论

```json
{
  "base_row_count": 280,
  "combined_best_context_model_context_folds": "18/30",
  "combined_robust_feature_count": 0,
  "combined_robust_model_count": 0,
  "combined_row_count": 328,
  "component_positive_only": true,
  "component_row_count": 48
}
```

解释：把 48 行 component payload rows 合入现有 280 行 selector rows 后，合并集仍没有通过 context / instance / dataset all-holdout 的特征或模型。这说明 payload 字段补齐降低了 schema gap，但还没有形成 production selector。

## 最新 selector holdout gap matrix 结论

```json
{
  "complete_explicit_forbidden_label_counts": {
    "improved": 48
  },
  "complete_explicit_forbidden_row_count": 48,
  "complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "complete_snapshot_mixed_context_count": 0,
  "complete_snapshot_row_count": 62,
  "recommended_next_stage": "collect_negative_and_mixed_full_snapshot_contexts",
  "total_candidate_row_count": 630
}
```

解释：当前 full-snapshot 和 explicit-forbidden payload 已经能采到，但完整样本几乎全是正例，且 mixed-label context 为 0。下一步需要补 negative/noop 与 mixed full-snapshot contexts，而不是把正例 payload 当成 production selector。

## 最新 selector holdout target priority matrix 结论

```json
{
  "manifest_priority_context_overlap_count": 9,
  "mixed_missing_full_snapshot_context_count": 7,
  "noop_missing_explicit_forbidden_context_count": 15,
  "noop_missing_full_snapshot_context_count": 12,
  "priority_context_count": 15,
  "recommended_next_stage": "collect_priority_negative_noop_mixed_full_snapshot_contexts",
  "uncovered_priority_context_count": 6,
  "uncovered_priority_contexts": [
    "1b95888aae8dd7c2",
    "46e7a2883459d4fb",
    "794ecbd6fefaa1d7",
    "7b9a35f8f7c6581a",
    "988c728382b4a376",
    "c27d904416342f6b"
  ]
}
```

解释：缺口现在已经落到具体 context。现有 manifest 覆盖了一部分高优先目标，但仍有 priority contexts 未覆盖；这些目标应该优先补采 complete full-snapshot 与 explicit-forbidden payload，用来验证 production selector 是否能同时拒绝 noop 和保留 improved。

## 最新 selector holdout priority collection runbook 结论

```json
{
  "command_count": 1,
  "commandable_context_count": 3,
  "commandable_contexts": [
    "46e7a2883459d4fb",
    "794ecbd6fefaa1d7",
    "c27d904416342f6b"
  ],
  "status": "selector_holdout_priority_collection_runbook_ready",
  "target_context_count": 6,
  "unsupported_context_count": 3,
  "unsupported_contexts": [
    "1b95888aae8dd7c2",
    "7b9a35f8f7c6581a",
    "988c728382b4a376"
  ]
}
```

解释：未覆盖 priority contexts 里只有一部分能直接转成 config-matched 采集命令；unsupported contexts 必须另行补 profile/source 解析，不能把 runbook ready 当作 selector holdout 已完成。

## 最新 selector holdout priority collection capture audit 结论

```json
{
  "active_basis_bad_count": 0,
  "capture_event_count": 12,
  "expected_context_complete_hit_count": 0,
  "expected_context_hash_count": 3,
  "expected_context_hit_count": 0,
  "missing_expected_context_count": 3,
  "no_certificate_bad_count": 0,
  "ready_for_selector_holdout": false,
  "status": "selector_holdout_collection_capture_audited"
}
```

解释：priority collection 实际运行是安全的，采到的 capture event 没有 certificate effect 且 active-basis 完整；但 3 个 expected target context 一个都没命中，所以它只能证明补采链路安全，不能证明 selector holdout 数据已经补齐。

## 最新 selector holdout priority capture miss 诊断

```json
{
  "exact_hit_context_count": 0,
  "expected_context_count": 3,
  "observed_event_count": 12,
  "observed_unique_context_count": 6,
  "same_active_component_drift_context_count": 1,
  "source_active_hash_missing_context_count": 2,
  "status": "selector_holdout_priority_capture_miss_diagnosed"
}
```

解释：补采没有命中目标 context 的原因不是 capture 不安全，而是轨迹本身发生分叉。两个目标 context 没到达 source active hash；一个目标context 到达同 active hash 但 pool / forbidden / returned-batch 组成漂移。

## 最新 selector holdout context action plan 结论

```json
{
  "complete_snapshot_action_count": 7,
  "row_count": 12,
  "status": "selector_holdout_context_action_plan_ready",
  "unresolved_action_count": 5,
  "unresolved_execution_category_counts": {
    "full_component_match_required": 1,
    "run_or_reaudit_existing_manifest_command": 1,
    "source_mapping_recovery_required": 1,
    "trajectory_variant_capture_required": 2
  },
  "unresolved_with_command_count": 4,
  "unresolved_without_command_count": 1
}
```

解释：12 个高优先 context 中只有 7 个可直接用作 complete snapshot calibration seed；剩余 5 个仍需要不同恢复动作。两个要捕获 trajectory variant 才能到达 source active-basis，一个要完整匹配 pool / forbidden / returned-batch / RMP / pricing 组件，一个要重跑或重审既有 manifest command，一个要先恢复 source profile / instance mapping。这说明 selector 数据缺口不是继续盲跑同 profile 可以闭合的简单采样问题。

## 已确定的根因

### small_scale_fixed_overhead_sensitivity

5/10 规模主要卡在固定开销敏感；触发 worker/audit/probe 会吃掉收益。

```json
{
  "missing_requirement": "five_ten_full_no_regression_ab",
  "nontriggered_official_changed": 0,
  "triggered_better_count": 0,
  "triggered_rows": 220,
  "triggered_worse_count": 220
}
```

### twenty_returned_batch_rmp_trajectory_coupling

20 规模不是没有 true-RC negative columns，而是 returned batch 对当前 RMP active-basis / dual trajectory 的影响不稳定。

```json
{
  "active_basis_counterexample_strongest_noop_true_rc": -128.547499,
  "active_basis_counterexample_task20_label_counts": {
    "improved": 10,
    "noop": 2
  },
  "active_basis_counterexample_task20_new_task_sets": 12,
  "active_basis_counterexample_task20_rows": 12,
  "has_20_walltime_speedup_evidence": false,
  "negative_columns_route_evidence": {
    "phase7o_all_time_limit": true,
    "phase8q_added_journeys": 10,
    "phase8q_added_new_task_sets": 8,
    "phase8q_all_time_limit": true,
    "phase8q_completion_bound_retry_count": 0
  },
  "negative_columns_route_status": "ruled_out_as_sufficient_condition",
  "phase7o_nonbaseline_rows": 96,
  "phase7o_nonbaseline_worsened_rows": 96,
  "phase7o_worker_added_journeys": 63,
  "phase7o_worker_added_new_task_sets": 30,
  "phase8q_improved_without_worker_added_count": 1,
  "phase8q_worker_added_journeys": 10,
  "phase8q_worker_added_rows": 3,
  "pulse_route_evidence": {
    "code_boundary_pass": true,
    "phase8q_added_journeys": 10,
    "phase8q_added_new_task_sets": 8,
    "phase8q_all_time_limit": true
  },
  "pulse_route_status": "ruled_out_as_primary_root_cause",
  "weaker_improved_than_strongest_noop_count": 8,
  "worker_negative_roi_blocker_status": "worker_negative_columns_not_sufficient_for_roi"
}
```

### addition_before_selector_not_production_validated

当前缺的是 production-validated addition-before selector；简单 true-RC / new-task-set / 单个 active-basis scalar 都不够。

```json
{
  "active_basis_snapshot_metric_fields": 2,
  "best_context_model": "shallow_tree_depth3",
  "candidate_row_count": 280,
  "component_payload_extension_base_row_count": 280,
  "component_payload_extension_combined_robust_features": 0,
  "component_payload_extension_combined_robust_models": 0,
  "component_payload_extension_combined_row_count": 328,
  "component_payload_extension_component_positive_only": true,
  "component_payload_extension_component_row_count": 48,
  "component_payload_rows_candidate_row_count": 48,
  "component_payload_rows_explicit_forbidden_true_count": 48,
  "component_payload_rows_ready_case_count": 6,
  "component_payload_rows_runs_local_rmp_replay": true,
  "context_trajectory_exact_component_count": 9,
  "context_trajectory_required_payload_count": 9,
  "counterexample_degeneracy_one_label_counts": {
    "improved": 3,
    "noop": 2
  },
  "counterexample_false_positive_count": 2,
  "counterexample_mixed_instance_group_count": 2,
  "counterexample_positive_churn_label_counts": {
    "improved": 4,
    "noop": 2
  },
  "missing_rmp_fields": 0,
  "present_rmp_fields": 17,
  "priority_capture_miss_exact_hit_context_count": 0,
  "priority_capture_miss_expected_context_count": 3,
  "priority_capture_miss_same_active_component_drift_context_count": 1,
  "priority_capture_miss_source_active_hash_missing_context_count": 2,
  "recovered_from_event_history": 8,
  "requires_capture_schema_extension": 0,
  "requires_event_history_join": 0,
  "requires_manifest_pass_through": 0,
  "requires_metric_definition": 0,
  "robust_enriched_features": [],
  "robust_models": [],
  "robust_single_features": [],
  "same_active_hash_is_not_sufficient": true,
  "selector_blocker_count": 6,
  "selector_holdout_blocker_collection_expected_count": 10,
  "selector_holdout_blocker_collection_hit_count": 9,
  "selector_holdout_blocker_complete_explicit_forbidden_label_counts": {
    "improved": 48
  },
  "selector_holdout_blocker_complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "selector_holdout_blocker_priority_expected_count": 3,
  "selector_holdout_blocker_priority_hit_count": 0,
  "selector_holdout_blocker_status": "selector_holdout_blocked_by_snapshot_label_mix",
  "selector_holdout_gap_complete_explicit_label_counts": {
    "improved": 48
  },
  "selector_holdout_gap_complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "selector_holdout_gap_complete_snapshot_rows": 62,
  "selector_holdout_gap_mixed_context_count": 0,
  "selector_holdout_gap_total_candidate_rows": 630,
  "selector_status": "production_selector_not_validated",
  "source_profile_rerun_is_not_sufficient": true
}
```

## 已排除的解释

- `Pulse 接线、物化或证书语义是主因`：`ruled_out_as_primary_root_cause`。
  Worker/capture paths can safely add or record true-RC negative journeys without critical disagreement; the remaining failure is ROI.
- `只要找更多或更负 true-RC negative columns 就会优化`：`ruled_out_as_sufficient_condition`。
  20-task runs can add true-RC negative journeys, including new task sets, but Phase 7O/8Q still end in TIME_LIMIT.
- `扩大 worker 预算或默认启用 worker`：`ruled_out_for_5_10_safety`。
  5/10 scale is fixed-overhead sensitive: triggered mechanisms consistently worsen wall time, while non-triggered rows preserve official results.
- `用 true-RC 阈值或局部列形状做 selector 已足够`：`not_production_validated`。
  Replay-local selector candidates exist, but exact holdout still has false positives and false negatives; mixed task-set/sequence groups prove local column shape is insufficient.
- `重跑 source profile 或只匹配 active hash 就足够补齐 selector holdout`：`ruled_out_as_sufficient_condition`。
  Priority capture produced safe no-certificate-effect events, but hit 0/3 expected contexts. Two targets did not reach the source active hash, and one same-active case drifted in pool/forbidden/returned-batch components, so source-profile rerun and active-hash-only matching are not sufficient evidence for selector holdout.

## 为什么仍不能标记完成

```text
completion_decision = keep_goal_active
goal_complete = false
missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup
production_ab_entry_gate = blocked
```

缺失项含义：

- 还没有 full 5/10 production-candidate no-regression A/B；
- 还没有用 component-payload addition-before rows 通过 context / instance / dataset holdout 的 production selector；
- 还没有 selected 20-task hard-repeat wall-time/gap/status/tail speedup 证据。

## 下一步证据门槛

- 继续扩展 component-payload / full-snapshot addition-before rows 的负例和 mixed context 分布
- 按完整 context 组件捕获目标轨迹；不能用 source profile 重跑或 active hash 近似替代 exact context
- 只用 addition-before 特征通过 context / instance / dataset selector holdout
- 之后才做 full BPC A/B：先 5/10 no-regression，再 selected 20 hard-repeat speedup

## 检查项

```json
{
  "certificate_gate_forbidden": true,
  "completion_keeps_goal_active": true,
  "component_capture_schema_passed": true,
  "component_payload_holdout_extension_passed": true,
  "component_payload_rows_passed": true,
  "context_schema_gap_passed": true,
  "counterexamples_passed": true,
  "diagnostic_only": true,
  "ledger_core_status_consistent": true,
  "missing_requirements_match_expected": true,
  "objective_audit_passed": true,
  "priority_capture_miss_passed": true,
  "priority_collection_capture_audit_passed": true,
  "priority_collection_runbook_passed": true,
  "production_ab_blocked": true,
  "production_gate_passed": true,
  "selector_context_action_plan_passed": true,
  "selector_holdout_gap_matrix_passed": true,
  "selector_not_production_validated": true,
  "selector_target_priority_matrix_passed": true,
  "small_fixed_overhead_evidence_present": true,
  "snapshot_sample_coverage_passed": true,
  "target002_probe_matrix_passed": true,
  "target002_trajectory_branch_passed": true,
  "twenty_counterexample_evidence_present": true,
  "why_report_passed": true,
  "worker_default_forbidden": true,
  "worker_negative_roi_blocker_passed": true
}
```
