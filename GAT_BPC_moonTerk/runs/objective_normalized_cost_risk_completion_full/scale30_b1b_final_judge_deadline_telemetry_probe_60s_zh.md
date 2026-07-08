# 30-scale B1B Final-Judge Deadline Telemetry Probe

## 目的

该 probe 验证 B1 root solver 是否能把 row-level budget 传入 true-dual final judge，并在 final judge 超时时返回 fail-closed partial telemetry，而不是依赖外层 SIGALRM 截断整行。

## 关键代码边界

- `solve_b1_root_node_baseline()` 记录 B1 起始时间，并把剩余预算传给 `run_true_dual_root_final_judge()`。
- final judge 在 complete-universe RC audit 枚举超时时返回 `COMPLETE_UNIVERSE_RC_AUDIT_TIME_LIMIT`。
- B1 遇到 `PricingState.INCOMPLETE_LIMIT` 会立即 fail-closed 返回 payload，不再重复下一轮。
- 证书门槛不变：该路径不产生 `BPC_NODE_LP_CERTIFIED`。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b1b_reference_seed_deadline_60s/`
- row time setting: `60s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- initial columns: `34`
- reference incumbent seed columns: `4`
- reference incumbent used as certificate: `false`

## B1B 结果

| field | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B1 root LP bound | `1.919465` |
| root LP bound official | `false` |
| pricing rounds | `1` |
| final judge status | `COMPLETE_UNIVERSE_RC_AUDIT_TIME_LIMIT` |
| final judge wall time | `49.975240s` |
| final judge generated journey count | `33,002` |
| final judge representative universe total | `1,073,741,823` |
| final judge representative universe audited | `33,002` |
| final judge representative universe completion ratio | `0.000030735508` |
| final judge representative universe remaining | `1,073,708,821` |
| final judge generated sortie count | `6,989,722` |
| final judge route template count | `1,519,698` |
| final judge pareto label count | `153,632` |
| pricing RC audit pass | `false` |

## 结论

该改动把 30-scale B1B 的失败边界从“外层 row timeout 截断，缺少内部归因”推进到“final judge 内部 fail-closed，并给出 pricing-tail partial telemetry”。

当前 30-scale 仍未闭合。新的瓶颈证据更明确：B1B root RMP 本身可以形成 diagnostic bound，但 true-dual complete-universe RC audit 在 50s 级别只审计了 `33,002 / 1,073,741,823` 个 task-subset representatives，完成比例约 `0.0030735508%`。
