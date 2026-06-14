# Active Basis Capture Schema Feasibility 审计

日期：2026-06-14

## 目的

检查完整 active basis / lambda 快照是否能从当前已计算对象中导出。
该审计只读源码，不运行 BPC、pricing、RMP、Pulse 或 benchmark。

## 机器字段

```text
active_basis_capture_schema_feasibility = current
diagnostic_only = true
runs_bpc_or_pricing = false
feasible_target_schema_field_count = 9
missing_target_schema_field_count = 0
solution_has_journey_values = true
solution_has_variable_values = true
solution_has_reduced_costs = true
solve_returns_full_variable_values = true
solve_can_return_reduced_costs = true
driver_passes_variable_values_to_diagnostics = false
counterfactual_capture_passes_active_variable_values = true
counterfactual_capture_supports_active_basis_snapshot = true
diagnostics_emits_full_snapshot = false
requires_solver_model_change = false
requires_pricing_change = false
requires_certificate_effect = false
requires_no_certificate_effect_logging_guard = true
capture_schema_implementation_status = implemented_default_off
all_checks_pass = true
```

## 字段来源

| target field | feasible | source |
|---|---:|---|
| `active_journey_pool_index` | true | solution.variable_values + journey_pool.journeys index |
| `active_lambda_value` | true | solution.variable_values[index] |
| `active_journey_signature` | true | journey_pool.journeys[index].signature |
| `active_journey_task_set` | true | journey_pool.journeys[index].task_set |
| `active_journey_cost` | true | journey_pool.journeys[index].cost |
| `active_journey_trip_signatures` | true | journey_pool.journeys[index].trips[*].signature |
| `active_journey_trip_task_sets` | true | journey_pool.journeys[index].trips[*].task_set |
| `active_journey_reduced_cost` | true | manual_journey_reduced_cost(journey, true_duals, cuts); optional solver reduced cost comes from solution.reduced_costs |
| `active_basis_snapshot_hash` | true | stable hash of sorted active snapshot rows |

## 关键判断

- `JourneyRMPSolution` 已保留 `journey_values`、`variable_values` 和可选 `reduced_costs`；
- `solution.variable_values` 与 `journey_pool.journeys[index]` 配对后可导出 pool index、lambda、signature、task set、cost 和 trip 结构；
- 当前 driver 的 pool diagnostics 只接收 `solution.journey_values`，并只输出 aggregate/hash/top samples；
- 默认关闭的 counterfactual replay capture 已支持 full active basis rows；
- 因此当前 active-basis 观测缺口已经从 schema 缺口收窄为重新采集 no-certificate-effect replay 数据的缺口。

## 结论

The full active-basis/lambda snapshot is derivable from the current JourneyRMPSolution and journey pool without changing the solver model or pricing semantics.  A default-off counterfactual replay capture schema now exists for full active rows; existing replay artifacts remain incomplete until new no-certificate-effect captures are collected.

下一步若继续根因 selector 主线，应使用默认关闭的 no-certificate-effect
诊断捕获重新采集 exact-context replay payload，并重新做 selector holdout；
不应把 schema-ready 或 capture-ready 解释为优化方向已证明。
