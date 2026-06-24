# Journey Branch Score Candidate Coverage

日期：2026-06-24

## 目的

统计 branch-score map 对已有 `journey_branch_candidates` 日志的命中情况。该脚本只读 score map 和 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
score_entry_count = 12
candidate_event_count = 3
candidate_event_with_score_hit_count = 3
candidate_event_with_selected_score_count = 0
candidate_event_would_change_selected_count = 3
full_logged_candidate_coverage_count = 0
scored_candidate_count_sum = 6
unscored_logged_candidate_count_sum = 30
selected_unscored_count = 3
production_ready = False
official_bound_effect = False
```

## 命中行

- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json.jsonl, node=0, depth=0, selected=2,5, selected_score=None, best_scored=3,18:10.0, would_change=True, scored_count=2/12, unscored_count=10
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json.jsonl, node=1, depth=1, selected=2,17, selected_score=None, best_scored=8,18:2.264785633, would_change=True, scored_count=2/12, unscored_count=10
- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json.jsonl, node=2, depth=1, selected=3,17, selected_score=None, best_scored=3,18:2.875487683, would_change=True, scored_count=2/12, unscored_count=10

## 边界

覆盖审计只说明 score map 是否能命中已记录候选；它不能证明 branch-score A/B 的 wall-time 收益，也不能作为 official bound 或 certificate。
