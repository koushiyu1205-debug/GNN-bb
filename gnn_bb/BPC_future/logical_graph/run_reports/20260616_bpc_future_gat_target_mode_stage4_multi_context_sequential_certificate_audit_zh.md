# 2026-06-15 BPC_future GAT Target Mode Certificate Audit 报告

## 结论

all_checks_pass = true
violation_count = 0

该审计只读 solver jsonl 日志，用来检查 GAT target-mode 事件是否越过 exact-safe 边界。

## 统计

log_files = 1
gat_events = 0
shadow_events = 0
admission_events = 0
candidate_journeys = 0
true_negative_journeys = 0
high_priority_journeys = 0
delay_queue_journeys = 0
reject_nonnegative_only_journeys = 0
shadow_delay_queue_journeys = 0
admission_delay_queue_journeys = 0
admission_online_safe_hit_journeys = 0
certificate_candidate_gat_events = 0
certificate_candidate_delayed_negative_events = 0
global_certificate_pricing_events = 0
pricing_kinds = none

## 检查项

- `selector_can_certificate` 必须为 false；
- `selector_is_pricing_oracle` 必须为 false；
- `official_bound_effect` 必须为 false；
- `hard_filter_enabled` 必须为 false；
- true-RC negative sample 不能被 `REJECT_NONNEGATIVE_ONLY`；
- 非 OPTIMAL finish 不能带 official `dual_bound`。

## Violations

- none

## Exactness Boundary

GAT/CBF/kNN/OOD 只能做 ordering、priority 或 finite-delay scheduling。
最终 certificate 仍必须来自当前 branch/cut/dual 下的 exact pricing full closure。
