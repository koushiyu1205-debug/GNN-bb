# 20260628 V715：RouteOpt/BKF Phased Controller 节点级审计汇总

## 结论

本轮没有改变 branch pair 排序公式，也没有运行 BPC full60。改动集中在 solver 内 `journey_branch_candidates` 日志：把已有 `routeopt_bkf_staged` 的 phase0 / phase1 / phase2 / dynamic-K 信息汇总成 node-level controller summary。

目的：

- 不再只靠 top/priority_top 每个 candidate 的分散字段判断；
- 后续可以直接按节点筛选“值得 exact / paired replay 的 RouteOpt/BKF 上下文”；
- 明确记录 phased testing 是否触碰 official bound / certificate；
- 为 `min(child_lb_gain)`、`child_gain_product`、`child_width_balance`、retry/fathom/gap 多目标标签继续铺路。

## 新增日志字段

在 `journey_branch_candidates` 事件中新增：

```text
phased_testing_controller_active
phased_testing_controller_input_count
phased_testing_stage_counts
phased_testing_decision_counts
phased_testing_phase0_fail_reason_counts

phased_testing_phase1_candidate_count
phased_testing_phase1_probe_count
phased_testing_phase1_complete_count
phased_testing_phase1_dynamic_k_excluded_count
phased_testing_phase1_reason_counts
phased_testing_phase1_total_wall_time
phased_testing_phase1_best_min_child_lp_gain
phased_testing_phase1_best_child_lp_gain_product
phased_testing_phase1_official_bound_effect_any
phased_testing_phase1_certificate_effect_any

phased_testing_phase2_candidate_count
phased_testing_phase2_probe_count
phased_testing_phase2_complete_count
phased_testing_phase2_dynamic_k_excluded_count
phased_testing_phase2_reason_counts
phased_testing_phase2_total_wall_time
phased_testing_phase2_negative_child_count_total
phased_testing_phase2_negative_journey_count_total
phased_testing_phase2_generated_sequences_total
phased_testing_phase2_evaluated_timed_trips_total
phased_testing_phase2_worst_negative_severity_max
phased_testing_phase2_official_bound_effect_any
phased_testing_phase2_certificate_effect_any

phased_testing_official_bound_effect_any
phased_testing_certificate_effect_any
```

## Exact-safe 边界

这些字段只汇总已有 probe metadata：

- 不额外运行 RMP；
- 不额外运行 pricing；
- 不产生 official bound；
- 不产生 certificate；
- 不剪枝；
- 不改变 branch pair selection。

当前 phase1 / phase2 probe 仍保持：

```text
official_bound_effect = false
certificate_effect = false
```

节点级字段 `phased_testing_official_bound_effect_any` 和 `phased_testing_certificate_effect_any` 用于审计未来改动是否意外越界。

## 代码改动

涉及：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/scripts/audit_journey_branch_impact.py`
- `BPC_future/tests/test_bpc_future.py`
- `BPC_future/tests/test_journey_branch_impact_audit.py`

新增 helper：

```text
_journey_branch_candidate_phased_testing_controller_summary(...)
```

该 helper 只读：

- phase0 status；
- candidate 上已有 `_phase1_lp_probe`；
- candidate 上已有 `_phase2_heuristic_probe`；
- priority order。

同时，`audit_journey_branch_impact.py` 已将这些 node-level summary 字段复制到：

- `branch_impact_rows.jsonl`
- `branch_training_rows.jsonl`

这样后续 runbook / dataset 构建不需要重新解析原始 solver JSONL。

## 验证

已通过：

```bash
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/audit_journey_branch_impact.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_journey_branch_impact_audit.py

python -m unittest \
  BPC_future.tests.test_journey_branch_impact_audit \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1 \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_decision_snapshot_feeds_log_and_metadata_without_reordering

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_force_pair_for_controlled_ab
```

## 意义

这个修改让 `routeopt_bkf_staged` 更接近正式 controller，而不是只靠离线 runbook：

- phase1 现在可以按节点统计实际 probe 数、complete 数、best 双 child LP gain；
- phase2 现在可以按节点统计 heuristic pricing 负列风险、耗时和 dynamic-K 排除；
- 后续 replay runbook 可以直接筛：
  - `phase1_best_min_child_lp_gain` 高；
  - `phase1_best_child_lp_gain_product` 高；
  - `phase2_negative_child_count_total` 低；
  - `phase2_worst_negative_severity_max` 低；
  - dynamic-K 排除较多但存在高 balance-frontier candidate 的节点。

## 下一步

1. 用 V545 full60 日志重跑 branch-impact audit，让审计脚本读取这些 node-level phased summary。
2. 在 `build_journey_branch_candidate_replay_runbook.py` 里优先抽取：
   - phase1 双 child gain 均衡；
   - phase2 负列链风险低；
   - dynamic-K 排除但 balance 好的候选。
3. 对 20-scale hard cases 做 depth 1-4 state-scoped paired replay，继续补 structural aux 标签。
