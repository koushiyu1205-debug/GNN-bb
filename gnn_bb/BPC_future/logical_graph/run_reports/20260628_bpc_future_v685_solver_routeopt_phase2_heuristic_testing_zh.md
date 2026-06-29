# V685 Solver RouteOpt/BKF Phase-2 Short Heuristic Testing

日期：2026-06-28

## 结论摘要

本轮在 V684 的 solver 内 Phase-1 current-pool LP testing 后，继续补上 opt-in Phase-2 short heuristic pricing probe。

当前 `routeopt_bkf_staged` 的 solver 内 staged controller 已形成三层：

```text
Phase-0 cheap screen
  fractionality / branch score / score source / child width / balance gap / dynamic K

Phase-1 current-pool LP testing
  same/separate child 当前列池 RMP objective gain 与 width balance

Phase-2 short heuristic pricing testing
  same/separate child 用短预算 heuristic pricing 检查是否仍快速出现负列
```

这一步仍然默认关闭，只在显式 opt-in 时运行。

## 新增配置

```text
journey_branch_candidate_phased_testing_phase2_heuristic_enabled
journey_branch_candidate_phased_testing_phase2_max_candidates
journey_branch_candidate_phased_testing_phase2_time_limit
journey_branch_candidate_phased_testing_phase2_max_returned_journeys
journey_branch_candidate_phased_testing_phase2_require_lp_complete
```

推荐采集配置：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_enabled=True
journey_branch_candidate_phased_testing_base_priority=branch_score_horizon
journey_branch_candidate_phased_testing_phase1_lp_enabled=True
journey_branch_candidate_phased_testing_phase1_max_candidates=4
journey_branch_candidate_phased_testing_phase2_heuristic_enabled=True
journey_branch_candidate_phased_testing_phase2_max_candidates=2
journey_branch_candidate_phased_testing_phase2_time_limit=0.05
journey_branch_candidate_phased_testing_phase2_max_returned_journeys=1
```

## Phase-2 行为

对进入 Phase-2 的候选 pair：

1. 构造 `same_vehicle(i,j)` 和 `separate_vehicle(i,j)` 两个 child。
2. 用当前列池解 child RMP，拿到 child dual。
3. 用极短时间预算运行 heuristic `price_journeys`。
4. 只记录是否快速发现负列、负列数量、best reduced cost、耗时和 pricing 工作量。

Phase-2 排序倾向：

```text
probe complete
negative_child_count 小
worst_negative_severity 小
Phase-1 LP complete
min_child_lp_gain 大
child_lp_gain_product 大
fractionality 大
task index 小
```

直观解释：如果一个 pair 的两个 child 当前池 LP gain 不错，并且短预算 heuristic pricing 也没有马上发现很强负列，那么它更像“容易闭环”的 branch。

## Exact-Safe 契约

Phase-2 不会：

- 把 heuristic pricing 结果加入列池；
- 更新 RMP；
- 更新 official lower bound；
- 产生 certificate；
- fathom / prune；
- 把未证明的 no-column 当成证书。

日志中明确记录：

```text
phase2_official_bound_effect=False
phase2_certificate_effect=False
```

因此 Phase-2 只是 branch candidate testing 和训练观测，不改变精确性边界。

## 新增日志字段

`journey_branch_candidates` 增加：

```text
phased_testing_phase2_heuristic_enabled
phased_testing_phase2_max_candidates
phased_testing_phase2_time_limit
phased_testing_phase2_max_returned_journeys
```

candidate payload 和 `journey_branch` selected metadata 增加：

```text
phased_testing_phase2_heuristic_enabled
phased_testing_phase2_heuristic_complete
phased_testing_phase2_heuristic_reason
phase2_same_child_status
phase2_separate_child_status
phase2_same_child_found_negative
phase2_separate_child_found_negative
phase2_same_child_negative_journeys
phase2_separate_child_negative_journeys
phase2_same_child_best_reduced_cost
phase2_separate_child_best_reduced_cost
phase2_same_child_wall_time
phase2_separate_child_wall_time
phase2_negative_child_count
phase2_negative_journey_count
phase2_best_reduced_cost
phase2_worst_negative_severity
phase2_generated_sequences
phase2_evaluated_timed_trips
phase2_wall_time
phase2_official_bound_effect
phase2_certificate_effect
```

未进入 dynamic K 的候选也会写：

```text
phased_testing_phase2_heuristic_reason=dynamic_k_excluded
```

这样后续能区分“没测”和“测了但没收益”。

## 测试

新增测试：

```text
test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe
```

验证：

- Phase-2 opt-in 后只对 dynamic K 个候选执行 heuristic probe。
- 未测试候选标记 `dynamic_k_excluded`。
- candidate log 和 `journey_branch` metadata 都带 Phase-2 字段。
- `phase2_official_bound_effect=False`。
- `phase2_certificate_effect=False`。

回归测试：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_branch_score_opt_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
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
Ran 34 tests in 0.488s
OK
```

Opt-in smoke：

```text
PYTHONDONTWRITEBYTECODE=1 python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml \
  --time-limit 30 \
  --results-csv BPC_future/results/20260628_v685_routeopt_phase2_heuristic_smoke_tasks5/results.csv \
  --log-dir BPC_future/results/20260628_v685_routeopt_phase2_heuristic_smoke_tasks5/logs \
  --solution-dir BPC_future/results/20260628_v685_routeopt_phase2_heuristic_smoke_tasks5/solutions \
  --set journey_branch_candidate_priority=routeopt_bkf_staged \
  --set journey_branch_candidate_phased_testing_enabled=true \
  --set journey_branch_candidate_phased_testing_base_priority=fractionality \
  --set journey_branch_candidate_phased_testing_phase1_lp_enabled=true \
  --set journey_branch_candidate_phased_testing_phase1_max_candidates=4 \
  --set journey_branch_candidate_phased_testing_phase2_heuristic_enabled=true \
  --set journey_branch_candidate_phased_testing_phase2_max_candidates=2 \
  --set journey_branch_candidate_phased_testing_phase2_time_limit=0.05 \
  --set journey_branch_candidate_phased_testing_phase2_max_returned_journeys=1 \
  --set journey_branch_candidate_log_top_n=20 \
  --quiet
```

结果：

```text
apollo15 tasks05: OPTIMAL, wall 1.907636s
tranquillitatis tasks05: OPTIMAL, wall 1.274804s
```

这两个 smoke 实例没有进入分支，所以 Phase-2 字段覆盖由 targeted unit test 保证。

## 对主线的意义

V685 解决的是 RouteOpt 启发中的“不要 top200 硬扫”的下一层：候选先过滤，再用动态 K 做便宜 testing。它比直接 full replay 更便宜，也比只看 GAT score 更接近真实闭环成本。

下一步应该在 random-TW 20-scale hard 实例上采集：

- Phase-1 `min_child_lp_gain` / `child_gain_product`
- Phase-2 `negative_child_count` / `worst_negative_severity`
- 后续节点是否 timeout、retry-heavy、gap 停滞

然后检验这些字段是否能解释 V680 这类严格正例，以及 V631/V636 这类“gap 改善但仍不闭环”的失败样本。

## 当前未达成项

仍未达成：

- 20-scale random-TW `60/60 OPTIMAL within 600s`
- solver 内 Phase-3 exact / paired replay
- BKF 根据 observed testing ROI 动态调 K
- branch 标签多目标训练更新
- cuts / formulation / incumbent 主线

下一步建议先做一个 hard-20 `routeopt_bkf_staged + Phase-1/2 log-only` 采集批次，再决定 Phase-2 是否应该默认参与排序，还是只作为训练特征。
