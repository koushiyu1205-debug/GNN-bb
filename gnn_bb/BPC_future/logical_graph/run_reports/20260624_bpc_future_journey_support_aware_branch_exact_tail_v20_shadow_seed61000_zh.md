# Journey Support-Aware Branch Exact Tail Audit

日期：2026-06-24

## 目的

解析 solver JSONL 中 branch exact pricing tail 的 support-aware admission 日志，统计 active-support-changing、new task-set 与 inactive-only 的构成。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_support_aware_branch_exact_tail_audit = current
output_dir = BPC_future/results/journey_support_aware_branch_exact_tail_v20_shadow_seed61000_20260624
log_count = 1
admission_event_count = 2
support_enabled_event_count = 2
min_depth = 1
min_time = 0.0
pricing_kind_prefixes = ['exact']
total_candidate_journeys = 3
total_true_negative_journeys = 0
total_support_active_journeys = 3
total_support_new_journeys = 2
total_support_inactive_journeys = 0
support_inactive_share = 0.0
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

## Support 分类

```json
{
  "active_support_changing": 2
}
```

## Pricing Kind

```json
{
  "exact": 2
}
```

## 解释

Rows are support-aware admission log events in branch exact pricing tails. The audit only measures active/new/inactive-only composition; it does not change column admission, certify no-negative pricing, or provide official node bounds. A large inactive share would justify a later opt-in delay A/B; a low inactive share points toward branch-impact, child proof-cost, cuts, or incumbent-search rather than inactive-only delay.
