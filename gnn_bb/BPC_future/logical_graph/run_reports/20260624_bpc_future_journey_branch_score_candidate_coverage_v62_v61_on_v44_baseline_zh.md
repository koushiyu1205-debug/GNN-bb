# Journey Branch Score Candidate Coverage

日期：2026-06-24

## 目的

统计 branch-score map 对已有 `journey_branch_candidates` 日志的命中情况。该脚本只读 score map 和 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
score_entry_count = 4
tie_tolerance_override = 0.2
candidate_event_count = 29
candidate_event_with_score_hit_count = 1
candidate_event_with_eligible_score_hit_count = 1
candidate_event_with_selected_score_count = 0
candidate_event_would_change_selected_count = 1
candidate_event_would_change_selected_any_logged_count = 1
full_logged_candidate_coverage_count = 29
scored_candidate_count_sum = 4
eligible_scored_candidate_count_sum = 4
unscored_logged_candidate_count_sum = 812
selected_unscored_count = 29
production_ready = False
official_bound_effect = False
```

## 命中行

- log=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json.jsonl, node=0, depth=0, selected=2,18, selected_score=None, best_scored=7,11:2.061865917, best_eligible=7,11:2.061865917, would_change=True, would_change_any_logged=True, scored_count=4/30, eligible_scored_count=4/30, unscored_count=26

## 人工判断

该报告使用 `tie_tolerance_override=0.2`，用于评估 V63 opt-in 配置下的候选覆盖。V44 baseline 日志原始 `tie_tolerance=0.0`，默认最高 fractionality 层为 `0.4` 并选 `[2,18]`；V61 命中的 `[7,11]`、`[6,8]`、`[2,15]`、`[7,15]` fractionality 均为 `0.2`。因此默认 horizon 下这些 score 只能算 `any_logged` 命中；在 V63 的 `0.2` horizon 下才是 eligible 命中并会改变 root 选择。

## 边界

覆盖审计只说明 score map 是否能命中已记录候选；它不能证明 branch-score A/B 的 wall-time 收益，也不能作为 official bound 或 certificate。
