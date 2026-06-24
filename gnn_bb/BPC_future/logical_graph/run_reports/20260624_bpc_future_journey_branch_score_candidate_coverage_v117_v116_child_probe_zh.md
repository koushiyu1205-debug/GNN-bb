# Journey Branch Score Candidate Coverage

日期：2026-06-24

## 目的

统计 branch-score map 对已有 `journey_branch_candidates` 日志的命中情况。该脚本只读 score map 和 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
score_entry_count = 39
tie_tolerance_override = None
score_min_score = 0.0
candidate_event_count = 39
candidate_event_with_score_hit_count = 7
candidate_event_with_eligible_score_hit_count = 3
candidate_event_with_selected_score_count = 4
candidate_event_would_change_selected_count = 1
candidate_event_would_change_selected_any_logged_count = 3
candidate_event_with_best_scored_requiring_recorded_horizon_expansion_count = 4
candidate_event_with_best_scored_requiring_effective_horizon_expansion_count = 4
best_scored_required_tie_tolerance_count = 7
best_scored_required_tie_tolerance_le_0_count = 3
best_scored_required_tie_tolerance_le_0_05_count = 3
best_scored_required_tie_tolerance_le_0_1_count = 3
best_scored_required_tie_tolerance_le_0_2_count = 6
best_scored_required_tie_tolerance_gt_0_2_count = 1
best_scored_required_tie_tolerance_max = 0.25
full_logged_candidate_coverage_count = 39
scored_candidate_count_sum = 12
eligible_scored_candidate_count_sum = 5
unscored_logged_candidate_count_sum = 1069
selected_unscored_count = 35
production_ready = False
official_bound_effect = False
```

## 命中行

- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=0, depth=0, selected=2,6, selected_score=5.393553672, best_scored=2,6:5.393553672, best_scored_required_tie_tolerance=0.2, best_eligible=None:None, would_change=False, would_change_any_logged=False, scored_count=2/30, eligible_scored_count=0/12, unscored_count=28
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=2, depth=1, selected=8,12, selected_score=6.536062081, best_scored=8,12:6.536062081, best_scored_required_tie_tolerance=0.0, best_eligible=8,12:6.536062081, would_change=False, would_change_any_logged=False, scored_count=2/27, eligible_scored_count=2/7, unscored_count=25
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=0, depth=0, selected=2,6, selected_score=5.393553672, best_scored=2,6:5.393553672, best_scored_required_tie_tolerance=0.2, best_eligible=None:None, would_change=False, would_change_any_logged=False, scored_count=2/30, eligible_scored_count=0/12, unscored_count=28
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=2, depth=1, selected=8,12, selected_score=6.536062081, best_scored=8,12:6.536062081, best_scored_required_tie_tolerance=0.0, best_eligible=8,12:6.536062081, would_change=False, would_change_any_logged=False, scored_count=2/27, eligible_scored_count=2/7, unscored_count=25
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=0, depth=0, selected=2,18, selected_score=None, best_scored=2,6:5.393553672, best_scored_required_tie_tolerance=0.2, best_eligible=None:None, would_change=False, would_change_any_logged=True, scored_count=2/30, eligible_scored_count=0/12, unscored_count=28
- log=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=2, depth=1, selected=3,7, selected_score=None, best_scored=8,12:6.536062081, best_scored_required_tie_tolerance=0.0, best_eligible=8,12:6.536062081, would_change=True, would_change_any_logged=True, scored_count=1/16, eligible_scored_count=1/16, unscored_count=15
- log=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=2, depth=1, selected=8,13, selected_score=None, best_scored=8,12:6.536062081, best_scored_required_tie_tolerance=0.25, best_eligible=None:None, would_change=False, would_change_any_logged=True, scored_count=1/23, eligible_scored_count=0/5, unscored_count=22

## 边界

覆盖审计只说明 score map 是否能命中已记录候选；它不能证明 branch-score A/B 的 wall-time 收益，也不能作为 official bound 或 certificate。
