# V686 Solver RouteOpt/BKF Dynamic-K Testing Budget

日期：2026-06-28

## 结论摘要

本轮在 V685 的 solver 内 Phase-0 / Phase-1 / Phase-2 staged branch testing 基础上，补上 BKF-style dynamic K testing budget。

之前 Phase-1/2 只能固定测试：

```text
phase1_max_candidates
phase2_max_candidates
```

现在可以 opt-in 使用 dynamic K：

```text
actual_K = clamp(ceil(sqrt(candidate_count) * sqrt_factor), min_K, max_K, phase_cap)
```

这解决的是 RouteOpt 启发里的一个关键点：不要 top200 硬扫，也不要永远固定测同样数量的候选，而是让测试规模随当前状态的候选宽度变化。

默认关闭；不开 dynamic K 时，既有固定 K 行为不变。

## 新增配置

```text
journey_branch_candidate_phased_testing_dynamic_k_enabled
journey_branch_candidate_phased_testing_dynamic_k_min_candidates
journey_branch_candidate_phased_testing_dynamic_k_max_candidates
journey_branch_candidate_phased_testing_dynamic_k_sqrt_factor
```

推荐采集配置：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_enabled=True
journey_branch_candidate_phased_testing_base_priority=branch_score_horizon

journey_branch_candidate_phased_testing_phase1_lp_enabled=True
journey_branch_candidate_phased_testing_phase2_heuristic_enabled=True
journey_branch_candidate_phased_testing_phase2_time_limit=0.05

journey_branch_candidate_phased_testing_dynamic_k_enabled=True
journey_branch_candidate_phased_testing_dynamic_k_min_candidates=1
journey_branch_candidate_phased_testing_dynamic_k_sqrt_factor=1.0
```

如果某个阶段仍显式设置：

```text
journey_branch_candidate_phased_testing_phase1_max_candidates
journey_branch_candidate_phased_testing_phase2_max_candidates
```

则该值作为阶段硬上限，不会被 dynamic K 超过。

## 行为边界

dynamic K 只决定 Phase-1 / Phase-2 测多少候选：

- 不改变候选本身；
- 不新增列；
- 不更新 RMP；
- 不产生 lower bound；
- 不产生 certificate；
- 不剪枝。

它只控制 testing cost 和训练观测覆盖。

## 新增日志字段

`journey_branch_candidates` 增加：

```text
phased_testing_dynamic_k_enabled
phased_testing_dynamic_k_min_candidates
phased_testing_dynamic_k_max_candidates
phased_testing_dynamic_k_sqrt_factor
```

candidate payload 和 `journey_branch` selected metadata 增加：

```text
phase1_dynamic_k_enabled
phase1_dynamic_k_reason
phase1_dynamic_k_actual_limit
phase1_dynamic_k_candidate_count

phase2_dynamic_k_enabled
phase2_dynamic_k_reason
phase2_dynamic_k_actual_limit
phase2_dynamic_k_candidate_count
```

未进入实际测试的候选仍保留：

```text
phased_testing_phase1_lp_reason=dynamic_k_excluded
phased_testing_phase2_heuristic_reason=dynamic_k_excluded
```

这样后续可以区分：

- 该候选被 Phase-0 淘汰；
- 该候选通过 Phase-0 但超出 dynamic K；
- 该候选被测过但 child LP / heuristic probe 不理想。

## 测试

新增测试：

```text
test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap
test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1
```

验证：

- dynamic K 关闭时保留 fixed limit；
- dynamic K 打开时使用 `ceil(sqrt(n) * factor)`；
- `phase_max_candidates` 仍是硬上限；
- 3 个 fractional pair 时，`sqrt(3)` 只测试 2 个；
- 被排除候选标记 `dynamic_k_excluded`；
- 日志写出 `phase1_dynamic_k_actual_limit=2` 和 `phase1_dynamic_k_reason=sqrt_dynamic_k`。

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
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1 \
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
Ran 36 tests in 0.580s
OK
```

Opt-in smoke：

```text
PYTHONDONTWRITEBYTECODE=1 python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml \
  --time-limit 30 \
  --results-csv BPC_future/results/20260628_v686_routeopt_dynamic_k_smoke_tasks5/results.csv \
  --log-dir BPC_future/results/20260628_v686_routeopt_dynamic_k_smoke_tasks5/logs \
  --solution-dir BPC_future/results/20260628_v686_routeopt_dynamic_k_smoke_tasks5/solutions \
  --set journey_branch_candidate_priority=routeopt_bkf_staged \
  --set journey_branch_candidate_phased_testing_enabled=true \
  --set journey_branch_candidate_phased_testing_base_priority=fractionality \
  --set journey_branch_candidate_phased_testing_phase1_lp_enabled=true \
  --set journey_branch_candidate_phased_testing_phase2_heuristic_enabled=true \
  --set journey_branch_candidate_phased_testing_phase2_time_limit=0.05 \
  --set journey_branch_candidate_phased_testing_phase2_max_returned_journeys=1 \
  --set journey_branch_candidate_phased_testing_dynamic_k_enabled=true \
  --set journey_branch_candidate_phased_testing_dynamic_k_min_candidates=1 \
  --set journey_branch_candidate_phased_testing_dynamic_k_sqrt_factor=1.0 \
  --set journey_branch_candidate_log_top_n=20 \
  --quiet
```

结果：

```text
apollo15 tasks05: OPTIMAL, wall 1.978318s
tranquillitatis tasks05: OPTIMAL, wall 1.306077s
```

这两个 smoke 实例未进入分支，dynamic K 的字段覆盖由 focused unit test 保证。

## 对主线的意义

V686 把 RouteOpt/BKF 的“测试多少候选”从固定参数推进到状态相关预算控制。它还不是完整 BKF，因为还没有基于历史 testing ROI 自适应更新 K；但已经具备下一步需要的数据口径：

- 当前状态 candidate_count；
- actual testing K；
- 哪些候选因为 dynamic K 未测；
- Phase-1 双 child LP gain；
- Phase-2 heuristic negative signal；
- selected pair 的 state-scoped metadata。

下一步应在 hard 20-scale 上采集一批 `routeopt_bkf_staged + dynamic K` 日志，观察：

- dynamic K 是否减少右删失 probe 浪费；
- 被 dynamic K 排除的候选是否确实低价值；
- Phase-1/2 指标是否能预测后续 timeout / retry-heavy / gap 停滞；
- 是否需要从 sqrt rule 升级到基于历史收益的 BKF rule。

## 当前未达成项

仍未达成：

- 20-scale random-TW `60/60 OPTIMAL within 600s`
- solver 内 Phase-3 exact / paired replay
- 基于 observed testing ROI 的真正 BKF 自适应 K
- branch 标签多目标训练更新
- cuts / formulation / incumbent 主线

本轮只是把 staged branch testing 的 testing budget 从固定 K 推进到 opt-in dynamic K。
