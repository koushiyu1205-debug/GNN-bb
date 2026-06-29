# V683 Solver RouteOpt/BKF Phase-0 Branch Testing Controller

日期：2026-06-28

## 结论摘要

本轮把 `routeopt_bkf_staged` 从离线 runbook sampling 往 solver 内正式控制器推进了一步。

已完成的是 solver 内 opt-in Phase-0 cheap screen：

- 新增 `journey_branch_candidate_phased_testing_enabled`
- 新增 `journey_branch_candidate_priority=routeopt_bkf_staged`
- 在正式 `_choose_journey_branch` / `_select_journey_branch_candidate` 路径中生效
- 对候选记录 Phase-0 pass/fail/reason/rank
- 支持 fail-closed 回退到原 priority order
- 默认关闭，不改变现有 benchmark

尚未完成的是 RouteOpt 完整三阶段：

- Phase-1 heuristic CG probe
- Phase-2 exact/paired replay
- BKF 根据历史收益动态决定 K
- 两个 child 的真实 LB/proof-cost probe

## 新增配置

```text
journey_branch_candidate_phased_testing_enabled
journey_branch_candidate_phased_testing_phase0_enabled
journey_branch_candidate_phased_testing_base_priority
journey_branch_candidate_phased_testing_phase0_min_fractionality
journey_branch_candidate_phased_testing_phase0_min_score
journey_branch_candidate_phased_testing_phase0_require_score_source
journey_branch_candidate_phased_testing_phase0_max_pool_total_child_width
journey_branch_candidate_phased_testing_phase0_max_pool_balance_gap
journey_branch_candidate_phased_testing_phase0_max_pool_child_width
journey_branch_candidate_phased_testing_phase0_max_candidates
journey_branch_candidate_phased_testing_fail_closed_to_priority_order
```

推荐实验入口：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_enabled=True
journey_branch_candidate_phased_testing_base_priority=branch_score_horizon
```

## 行为边界

Phase-0 只使用当前已经可用的候选字段：

- fractionality
- branch score / score source
- pool_total_child_width
- pool_balance_gap
- pool_max_child_width
- candidate rank / dynamic K cap

它不运行 pricing，不运行 RMP，不生成新 bound，不生成 certificate，也不剪枝。

如果 Phase-0 把候选全部过滤掉，默认：

```text
journey_branch_candidate_phased_testing_fail_closed_to_priority_order=True
```

即回退到原 priority order，避免因为 gate 过严导致没有 branch candidate。

## 新增日志字段

`journey_branch_candidates` 增加：

```text
phased_testing_enabled
phased_testing_phase0_enabled
phased_testing_base_priority
phased_testing_phase0_min_fractionality
phased_testing_phase0_min_score
phased_testing_phase0_require_score_source
phased_testing_phase0_max_pool_total_child_width
phased_testing_phase0_max_pool_balance_gap
phased_testing_phase0_max_pool_child_width
phased_testing_phase0_max_candidates
phased_testing_phase0_pass_count
phased_testing_phase0_fail_count
phased_testing_fail_closed_to_priority_order
```

每个 candidate payload 增加：

```text
phased_testing_phase0_rank
phased_testing_phase0_passed
phased_testing_phase0_reason
```

`journey_branch` metadata 增加：

```text
phased_testing_enabled
phased_testing_phase0_passed
phased_testing_phase0_reason
phased_testing_phase0_rank
phased_testing_base_priority
```

这些字段用于后续训练标签和 audit，不影响 exactness。

## 测试

新增测试：

```text
test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate
```

该测试构造一个高 score 但 fractionality 低于 Phase-0 门槛的 pair，验证：

- 单纯 `branch_score_horizon` 会选高 score pair；
- `routeopt_bkf_staged` 会在 Phase-0 淘汰它；
- solver 内实际选择转向通过 Phase-0 的 pair；
- JSONL 日志记录 `fractionality_below_min`。

回归测试：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile BPC_future/solver/journey_driver.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_branch_score_opt_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_branch_score_selection \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_branch_score_horizon \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_selection_gate_falls_back_on_width_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_context_gate_disables_mismatched_map \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_rows_preserve_branch_state_keys \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook \
  BPC_future.tests.test_journey_branch_full_replay_gap_delta_rows \
  BPC_future.tests.test_gat_branch_action_sanity_dataset
```

结果：

```text
Ran 32 tests in 0.058s
OK
```

默认路径 smoke：

```text
PYTHONDONTWRITEBYTECODE=1 python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml \
  --time-limit 30 \
  --results-csv BPC_future/results/20260628_v683_routeopt_phase0_default_smoke_tasks5/results.csv \
  --log-dir BPC_future/results/20260628_v683_routeopt_phase0_default_smoke_tasks5/logs \
  --solution-dir BPC_future/results/20260628_v683_routeopt_phase0_default_smoke_tasks5/solutions \
  --quiet
```

结果：

```text
apollo15 tasks05: OPTIMAL, wall 1.875994s
tranquillitatis tasks05: OPTIMAL, wall 1.288314s
```

## 对主线的意义

这一步解决的是结构问题：之前 `routeopt_bkf_staged` 只在离线 runbook 中采样候选，solver 内正式 branch 仍然只是直接排序选 pair。现在 solver 内已经有了 staged controller 的第一层入口。

这使后续可以自然接入：

1. Phase-1 短预算 heuristic CG probe。
2. Phase-2 dynamic-K paired exact replay。
3. 双 child 均衡收益：
   - `min(child_lb_gain)`
   - `child_gain_product`
   - `child_width_balance`
   - `completion_bound_retry_delta`
   - `gap_improvement`
4. BKF-style 历史收益统计，用 observed gain / testing CPU 动态调 K。

## 当前未达成项

仍未达成：

- 20-scale random-TW `60/60 OPTIMAL within 600s`
- solver 内完整 RouteOpt 3-phase branch testing
- Phase-1/Phase-2 的真实 child proof-cost 标签
- cuts/formulation/incumbent 主线

本轮只是把 Phase-0 cheap screen 从离线采样推进到 solver 内 opt-in 控制器。
