# Journey Branch Score Candidate Coverage

日期：2026-06-24

## 目的

统计 branch-score map 对已有 `journey_branch_candidates` 日志的命中情况。该脚本只读 score map 和 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
score_entry_count = 12
tie_tolerance_override = 0.2
candidate_event_count = 29
candidate_event_with_score_hit_count = 4
candidate_event_with_eligible_score_hit_count = 3
candidate_event_with_selected_score_count = 0
candidate_event_would_change_selected_count = 3
candidate_event_would_change_selected_any_logged_count = 4
full_logged_candidate_coverage_count = 29
scored_candidate_count_sum = 19
eligible_scored_candidate_count_sum = 17
unscored_logged_candidate_count_sum = 797
selected_unscored_count = 29
production_ready = False
official_bound_effect = False
```

## 命中行

- log=apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl, node=0, depth=0, selected=3,7, selected_score=None, best_scored=6,13:1.519738944, best_eligible=6,13:1.519738944, would_change=True, would_change_any_logged=True, scored_count=4/60, eligible_scored_count=4/60, unscored_count=56
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=0, depth=0, selected=2,18, selected_score=None, best_scored=2,6:3.751747162, best_eligible=2,6:3.751747162, would_change=True, would_change_any_logged=True, scored_count=12/30, eligible_scored_count=12/30, unscored_count=18
- log=apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl, node=0, depth=0, selected=8,18, selected_score=None, best_scored=9,11:-0.339247511, best_eligible=None:None, would_change=False, would_change_any_logged=True, scored_count=2/53, eligible_scored_count=0/14, unscored_count=51
- log=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl, node=0, depth=0, selected=2,3, selected_score=None, best_scored=9,11:-0.339247511, best_eligible=9,11:-0.339247511, would_change=True, would_change_any_logged=True, scored_count=1/37, eligible_scored_count=1/22, unscored_count=36

## 边界

覆盖审计只说明 score map 是否能命中已记录候选；它不能证明 branch-score A/B 的 wall-time 收益，也不能作为 official bound 或 certificate。
