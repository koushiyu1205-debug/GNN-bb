# Journey Branch-Impact Audit

日期：2026-06-28

## 目的

读取 solver JSONL 日志，聚合每次 Journey 分支后的子节点负列、列添加、active-support 和证明尾段行为。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_impact_audit = current
log_count = 4
branch_count = 0
branch_training_row_count = 0
child_probe_row_count = 0
tail_class_counts = {}
priority_mode_counts = {}
selected_match_count = 0
top_contains_branch_count = 0
top_first_branch_count = 0
priority_top_first_branch_count = 0
candidate_log_branch_count = 0
forced_pair_branch_count = 0
forced_pair_matched_branch_count = 0
right_censored_branch_count = 0
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
run_status_counts = {}
active_touch_branch_count = 0
inactive_only_branch_count = 0
unprocessed_child_count = 0
total_child_negative_pricing_events = 0
total_child_exact_pricing_events = 0
total_child_certificate_pricing_events = 0
total_child_column_additions = 0
total_child_added_journeys = 0
total_child_completion_bound_retries = 0
total_child_early_branch_triggers = 0
total_child_fathom_events = 0
max_child_lower_bound_gain = None
max_child_corrected_bound_gain = None
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

没有找到 journey_branch 事件。

## Feature / Label Schema

```json
{
  "branch_feature_schema": [
    "depth",
    "candidate_count",
    "eligible_count",
    "has_candidate_log",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "same_mass",
    "fractionality",
    "support_count",
    "incumbent_relation_known",
    "incumbent_relation_same",
    "incumbent_disagreement",
    "pool_same_allowed",
    "pool_separate_allowed",
    "pool_max_child_width",
    "pool_total_child_width",
    "pool_balance_gap"
  ],
  "branch_label_schema": [
    "y_tail_improved",
    "y_completion_bound_tail",
    "y_early_branch_continues",
    "y_negative_chain_continues",
    "y_active_touch",
    "y_inactive_only",
    "y_child_negative_pricing_events",
    "y_child_exact_pricing_events",
    "y_child_completion_bound_retries",
    "y_child_early_branch_triggers",
    "y_child_fathom_events",
    "y_child_max_safe_bound_gain",
    "y_child_max_corrected_bound_gain"
  ],
  "child_probe_label_schema": [
    "child_lower_bound_gain",
    "child_max_corrected_node_lb",
    "child_max_corrected_bound_gain",
    "child_pricing_event_count",
    "child_exact_pricing_event_count",
    "child_negative_pricing_event_count",
    "child_completion_bound_retry_count",
    "child_early_branch_trigger_count",
    "child_proof_cpu",
    "child_time_to_first_certificate",
    "child_time_to_fathom",
    "child_fathomed"
  ]
}
```

## 注意

若 `selected_match_count = 0` 但 `top_contains_branch_count > 0`，通常表示输入日志生成于 `selected` / `priority_top` 字段加入之前；此时只能从 `top` 中反推实际分支候选位置，不能把 `selected_match_count = 0` 解读为分支选择错误。

若 `candidate_log_branch_count = 0`，说明该批日志完全缺少 branch-candidate 特征；这些 rows 只能作为 proof-cost / tail-risk 诊断，不能作为 GAT branch-impact 排序训练 row。

## Records

```json
[]
```
