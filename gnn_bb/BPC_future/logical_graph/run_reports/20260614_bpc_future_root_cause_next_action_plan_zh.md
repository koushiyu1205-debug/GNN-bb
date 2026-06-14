# Root Cause Next Action Plan 报告

日期：2026-06-14

## 目的

本报告把当前根因结论转成下一步可执行证据门槛。它只读已有
summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或
certificate 默认行为。

## 当前结论

5/10 失败的直接原因是固定开销敏感；20 失败的根因不是找不到负列，而是 returned batch 对当前 RMP active-basis / dual trajectory 的影响强上下文耦合；当前还没有 production-validated addition-before selector。

```text
root_cause_next_action_plan = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = calibration_only_next_action
current_allowed_stage = calibration_only_selector_holdout
production_direction_proven = false
goal_complete = false
missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup
required_selector_holdouts = context,instance,dataset
selector_blocker_count = 6
holdout_gap_recommended_next_stage = collect_negative_and_mixed_full_snapshot_contexts
target_priority_recommended_next_stage = collect_priority_negative_noop_mixed_full_snapshot_contexts
worker_negative_roi_blocker_status = worker_negative_columns_not_sufficient_for_roi
worker_negative_phase7o_nonbaseline_worsened_rows = 96
priority_capture_miss_status = selector_holdout_priority_capture_miss_diagnosed
priority_capture_miss_exact_hit_context_count = 0
all_checks_pass = true
```

## 现在允许做什么

### extend_no_certificate_effect_exact_context_replay

扩展 no-certificate-effect exact-context replay / active-basis snapshot 数据

原因：现有数据已经能说明 true-RC / new-task-set / 单个 active-basis scalar 不足，但还没有 production selector；gap matrix 进一步显示 complete full-snapshot rows 的 noop/mixed 覆盖太稀疏，priority capture miss 显示单纯 source profile rerun 不能保证回到目标 context。

产物要求：所有 rows 必须保持 official_effect_count=0，并包含 returned batch、true-RC、task-set、sequence、context hash、active-basis churn、RMP degeneracy pressure、explicit forbidden signature payload 与 replay impact label。

### fit_addition_before_selector_only

只用 addition-before 特征校准 selector

原因：hindsight / post-addition 特征不能在线使用；worker 找到负列也不是 production ROI 证明。

产物要求：selector 输入必须排除 post-addition / hindsight 字段，并输出 context / instance / dataset holdout 指标。

### require_all_holdout_pass_before_ab

通过 context / instance / dataset holdout 后才进入 BPC A/B

原因：当前 blocker catalog 仍有 concrete false positive/false negative、fold gate 不稳定、rule family 无全 fold 规则等阻塞项。

产物要求：必须生成 production_selector_validated=true 的 summary，且 blocker_count=0。

### run_5_10_no_regression_before_20_speedup

先跑 5/10 full no-regression，再跑 selected 20 hard-repeat speedup

原因：5/10 已证明对触发式固定开销敏感；不能直接把 20-task worker 策略推到 production。

产物要求：5/10 full A/B 必须无 official regression；20-task hard-repeat 必须显示 wall-time / gap / status / tail 改善。

## 立即子动作

### collect_mixed_noop_full_snapshot_contexts

父动作：extend_no_certificate_effect_exact_context_replay

原因：priority matrix reports mixed/noop contexts without complete full-snapshot coverage; these are the rows needed to test selector false positives and false negatives.

产物要求：complete full-snapshot rows with both improved and noop labels, not only positive component payload rows.

### collect_explicit_forbidden_payload_for_noop_contexts

父动作：extend_no_certificate_effect_exact_context_replay

原因：current complete explicit-forbidden rows are positive-only, so they cannot calibrate a production reject rule.

产物要求：explicit forbidden signature payload for noop and mixed contexts, with no certificate or official-bound effect.

### replace_source_profile_rerun_with_context_trajectory_protocol

父动作：extend_no_certificate_effect_exact_context_replay

原因：priority capture miss shows 0 exact hits for 3 expected contexts: two did not reach the source active hash and one drifted in pool/forbidden/returned-batch components despite the same active hash.

产物要求：next capture protocol must record and target context components beyond active hash: pool signature, forbidden signature, returned batch, RMP objective, and pricing outcome.

## 最新缺口证据

### Worker Negative ROI Blocker

```json
{
  "phase7o_nonbaseline_rows": 96,
  "phase7o_nonbaseline_worsened_rows": 96,
  "phase7o_worker_added_journeys": 63,
  "phase7o_worker_added_new_task_sets": 30,
  "phase7o_worker_added_support_changing": 13,
  "phase8q_improved_without_worker_added_count": 1,
  "phase8q_worker_added_journeys": 10,
  "phase8q_worker_added_rows": 3,
  "status": "worker_negative_columns_not_sufficient_for_roi"
}
```

解释：worker 能加入 true-RC negative columns，但 Phase 7O expanded 仍是全部 non-baseline worsened，Phase 8Q 的 worker-added rows 也没有成为 improved rows。因此下一步不能简单增加 worker 预算或默认启用 worker。

### Holdout Gap

```json
{
  "complete_explicit_forbidden_label_counts": {
    "improved": 48
  },
  "complete_explicit_forbidden_mixed_context_count": 0,
  "complete_explicit_forbidden_noop_only_context_count": 0,
  "complete_explicit_forbidden_positive_only_context_count": 4,
  "complete_explicit_forbidden_row_count": 48,
  "complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "complete_snapshot_mixed_context_count": 0,
  "complete_snapshot_noop_only_context_count": 3,
  "complete_snapshot_positive_only_context_count": 14,
  "complete_snapshot_row_count": 62,
  "recommended_next_stage": "collect_negative_and_mixed_full_snapshot_contexts",
  "total_candidate_row_count": 630
}
```

### Target Priority

```json
{
  "mixed_missing_full_snapshot_context_count": 7,
  "noop_missing_full_snapshot_context_count": 12,
  "priority_context_count": 15,
  "recommended_next_stage": "collect_priority_negative_noop_mixed_full_snapshot_contexts",
  "top_priority_contexts": [
    "774573a2964cb1c5",
    "3c36c602289637b4",
    "79de1ece885a7f67",
    "7f2e531534d18ad2",
    "1db815e33b9ea471"
  ],
  "uncovered_priority_context_count": 6
}
```

### Priority Capture Miss

```json
{
  "exact_hit_context_count": 0,
  "expected_context_count": 3,
  "observed_event_count": 12,
  "same_active_component_drift_context_count": 1,
  "source_active_hash_missing_context_count": 2,
  "status": "selector_holdout_priority_capture_miss_diagnosed"
}
```

## 进入 production A/B 前必须满足

- selector_feature_scope == addition_before_only
- required_holdouts == context,instance,dataset
- production_validated_selector == true
- selector_blocker_count == 0
- no certificate effect in replay/capture rows
- worker default remains disabled before A/B
- official certificate gate remains closed before A/B

## 失败即停止条件

- selector fails any context/instance/dataset holdout -> stay in calibration; do not run production A/B
- 5/10 production candidate A/B regresses -> reject selector/gate even if 20-task signal exists
- 20 hard-repeat A/B has no wall-time/gap/status/tail improvement -> reject optimization direction as insufficient

## 现在禁止做什么

- default_enable_worker_or_audit
- increase_worker_budget_without_selector_roi
- open_official_certificate_gate
- treat_true_rc_or_new_task_set_as_selector
- use_post_addition_or_hindsight_features_online
- enter_production_ab_before_selector_holdout
- claim_goal_complete_without_5_10_and_20_ab

## 检查项

```json
{
  "action_plan_has_required_items": true,
  "allowed_stage_is_calibration_only": true,
  "counterexample_blocks_simple_true_rc": true,
  "counterexamples_passed": true,
  "current_answer_passed": true,
  "holdout_gap_requires_negative_mixed_contexts": true,
  "missing_requirements_match_expected": true,
  "next_protocol_passed": true,
  "no_approved_production_direction": true,
  "objective_audit_passed": true,
  "priority_capture_miss_blocks_source_profile_rerun_shortcut": true,
  "production_direction_not_proven": true,
  "registry_passed": true,
  "required_holdouts_match_expected": true,
  "selector_blocker_passed": true,
  "selector_blockers_still_present": true,
  "target_priority_requires_noop_mixed_full_snapshot": true,
  "worker_negative_roi_blocker_passed": true
}
```
