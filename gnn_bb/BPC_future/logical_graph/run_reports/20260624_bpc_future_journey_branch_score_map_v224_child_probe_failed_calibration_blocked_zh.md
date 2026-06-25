# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 0
raw_ranking_pair_row_count = 0
include_child_probe = True
child_probe_score_map_blocked = True
child_probe_score_map_block_reason = child_probe_proxy_top_pair_mismatch
child_probe_calibration_input_paths = ['BPC_future/results/journey_branch_child_probe_proxy_calibration_v223_v222_vs_v210_sector_apollo_20260624']
child_probe_calibration_matched_pair_count = 4
child_probe_calibration_top_pair_mismatch_count = 1
child_probe_calibration_discordant_pair_count = 2
raw_child_probe_row_count = 8
child_probe_row_count = 0
child_probe_branch_row_count = 0
filtered_out_child_probe_row_count = 8
filtered_out_row_count = 0
branch_score_row_count = 0
branch_score_map_entry_count = 0
instance_count = 0
key_scope = node_depth
include_instance_contains = []
exclude_instance_contains = []
include_child_probe_log_contains = []
exclude_child_probe_log_contains = []
solver_priority_mode = branch_score_horizon
solver_score_path = BPC_future/results/journey_branch_score_map_v224_v221_child_probe_failed_calibration_blocked_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows


## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
child-probe proof-cost 分数只有在提供 proxy-vs-full 校准且校准通过时才会进入 score map；未校准或校准出现 top mismatch / pairwise discordance 时必须 fail-closed。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
