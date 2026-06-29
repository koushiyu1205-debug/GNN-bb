# V684 Solver RouteOpt/BKF Phase-1 Current-Pool LP Testing

日期：2026-06-28

## 结论摘要

本轮在 V683 的 solver 内 `routeopt_bkf_staged` Phase-0 cheap screen 后，补上 opt-in Phase-1 current-pool LP testing。

已完成：

- `routeopt_bkf_staged` 可在 Phase-0 之后，对动态 K 个候选 pair 做双 child 当前列池 RMP probe。
- 记录 same / separate 两个 child 的当前池 LP status、objective、LP gain 和 width balance。
- Phase-1 结果进入候选排序和日志字段。
- `journey_branch_candidates` 和最终 `journey_branch` metadata 都能记录 selected pair 的 Phase-1 结果。
- 所有 Phase-1 字段明确标记 `official_bound_effect=False`、`certificate_effect=False`。
- 默认关闭，不改变现有 benchmark。

这一步不是完整 RouteOpt strong branching，也不是 exact proof。它只是一个便宜、可审计的分支前测，用于避免只凭单点 score 或 fractionality 选 pair。

## 新增配置

```text
journey_branch_candidate_phased_testing_phase1_lp_enabled
journey_branch_candidate_phased_testing_phase1_max_candidates
```

推荐实验入口：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_enabled=True
journey_branch_candidate_phased_testing_base_priority=branch_score_horizon
journey_branch_candidate_phased_testing_phase1_lp_enabled=True
journey_branch_candidate_phased_testing_phase1_max_candidates=4
```

## 行为边界

Phase-1 对每个候选 pair 构造两个 child：

- `same_vehicle(i,j)`
- `separate_vehicle(i,j)`

然后只用当前 `journey_pool` 中已经存在的列求 child RMP，不运行 pricing，不生成新列，不跑 completion-bound / final-judge。

排序优先级为：

```text
complete child LP probe
min_child_lp_gain 大
child_lp_gain_product 大
sum_child_lp_gain 大
child_width_balance 小
child_max_width 小
fractionality 大
task index 小
```

因此它更偏向“双 child 都能抬高当前池 LP、且 child 宽度更均衡”的 pair，而不是只看某一个 child 好不好。

## Exact-Safe 契约

Phase-1 的 child LP probe 不是 official lower bound：

```text
official_bound_effect=False
certificate_effect=False
```

它不能用于：

- fathom；
- prune；
- 更新 exact node bound；
- 替代 exact pricing closure。

early branch child 仍然只继承合法旧 lower bound；正常 branch child 仍按原本 exact-safe 路径走。Phase-1 只影响 pair 排序和训练观测。

## 新增日志字段

`journey_branch_candidates` 增加：

```text
phased_testing_phase1_lp_enabled
phased_testing_phase1_max_candidates
```

candidate payload 增加：

```text
phased_testing_phase1_lp_enabled
phased_testing_phase1_lp_complete
phased_testing_phase1_lp_reason
phase1_same_child_status
phase1_separate_child_status
phase1_same_child_objective
phase1_separate_child_objective
phase1_same_child_lp_gain
phase1_separate_child_lp_gain
phase1_min_child_lp_gain
phase1_sum_child_lp_gain
phase1_child_lp_gain_product
phase1_child_width_balance
phase1_child_max_width
phase1_child_total_width
phase1_official_bound_effect
phase1_certificate_effect
```

`journey_branch` metadata 也增加 selected pair 的同名字段，保证后续训练数据不必只依赖 candidate list。

## 测试

新增测试：

```text
test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe
```

验证：

- Phase-1 打开时会对动态 K 个候选写入 child LP probe 字段；
- selected pair 的 metadata 也有 Phase-1 字段；
- same / separate child 当前池 RMP 能返回 LP status；
- `phase1_official_bound_effect=False`；
- `phase1_certificate_effect=False`。

回归测试：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_branch_score_opt_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
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
Ran 33 tests in 1.229s
OK
```

Opt-in smoke：

```text
PYTHONDONTWRITEBYTECODE=1 python BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml \
  --time-limit 30 \
  --results-csv BPC_future/results/20260628_v684_routeopt_phase1_smoke_tasks5/results.csv \
  --log-dir BPC_future/results/20260628_v684_routeopt_phase1_smoke_tasks5/logs \
  --solution-dir BPC_future/results/20260628_v684_routeopt_phase1_smoke_tasks5/solutions \
  --set journey_branch_candidate_priority=routeopt_bkf_staged \
  --set journey_branch_candidate_phased_testing_enabled=true \
  --set journey_branch_candidate_phased_testing_base_priority=fractionality \
  --set journey_branch_candidate_phased_testing_phase1_lp_enabled=true \
  --set journey_branch_candidate_phased_testing_phase1_max_candidates=4 \
  --set journey_branch_candidate_log_top_n=20 \
  --quiet
```

结果：

```text
apollo15 tasks05: OPTIMAL, wall 1.898248s
tranquillitatis tasks05: OPTIMAL, wall 1.278817s
```

这两个 smoke 实例没有进入分支，所以 Phase-1 字段覆盖主要由 targeted unit test 保证。

## 对主线的意义

当前 20-scale 的主要问题不是“GAT 能不能给一个 pair 打高分”，而是高分 pair 是否真的让两个 child 更快闭环。V684 加入的 Phase-1 给了一个低成本的中间观测：

- 当前列池下两个 child 是否都可解；
- 两个 child 的 LP objective 是否都有上升；
- 是否只有单 child 好、另一个 child 仍很宽；
- 当前候选 score 是否与 child LP gain 一致。

这为后续训练 `predicted_child_proof_cpu`、`predicted_time_to_certificate`、`predicted_walltime_gain` 提供了比纯 score replay 更接近因果的字段。

## 当前未达成项

仍未达成：

- 20-scale random-TW `60/60 OPTIMAL within 600s`
- Phase-1 heuristic CG probe
- Phase-2 exact paired replay
- BKF 根据历史测试收益动态调 K
- cuts / formulation / incumbent 主线

下一步应在 hard 20-scale 实例上跑 `routeopt_bkf_staged + Phase-1` 的 branch log，不急着当生产加速配置，而是先比较：

- Phase-1 top pair 与 V682/GAT top pair 是否一致；
- Phase-1 `min_child_lp_gain` 是否能解释 V680 那类 345s -> 50s 的严格 replay 正例；
- Phase-1 低 gain / 高 width imbalance 是否对应后续 timeout 或 retry-heavy child。
