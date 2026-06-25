# Journey Branch Score Candidate Coverage

日期：2026-06-24

## 目的

统计 branch-score map 对已有 `journey_branch_candidates` 日志的命中情况。该脚本只读 score map 和 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
score_entry_count = 20
tie_tolerance_override = None
score_min_score = None
candidate_event_count = 0
candidate_event_with_score_hit_count = 0
candidate_event_with_eligible_score_hit_count = 0
candidate_event_with_selected_score_count = 0
candidate_event_would_change_selected_count = 0
candidate_event_would_change_selected_any_logged_count = 0
candidate_event_with_best_scored_requiring_recorded_horizon_expansion_count = 0
candidate_event_with_best_scored_requiring_effective_horizon_expansion_count = 0
best_scored_required_tie_tolerance_count = 0
best_scored_required_tie_tolerance_le_0_count = 0
best_scored_required_tie_tolerance_le_0_05_count = 0
best_scored_required_tie_tolerance_le_0_1_count = 0
best_scored_required_tie_tolerance_le_0_2_count = 0
best_scored_required_tie_tolerance_gt_0_2_count = 0
best_scored_required_tie_tolerance_max = None
full_logged_candidate_coverage_count = 0
scored_candidate_count_sum = 0
eligible_scored_candidate_count_sum = 0
unscored_logged_candidate_count_sum = 0
selected_unscored_count = 0
production_ready = False
official_bound_effect = False
```

## 命中行

- 无 score 命中。

## 边界

覆盖审计只说明 score map 是否能命中已记录候选；它不能证明 branch-score A/B 的 wall-time 收益，也不能作为 official bound 或 certificate。
