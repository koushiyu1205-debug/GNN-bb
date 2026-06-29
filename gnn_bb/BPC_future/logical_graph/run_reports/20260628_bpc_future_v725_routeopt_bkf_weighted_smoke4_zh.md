# V725 RouteOpt/BKF Weighted Phased Controller Hard4 Smoke

日期：2026-06-28

## 背景

本轮继续 Branch Score 主线，参考 RouteOpt/BKF 的分阶段 branch testing 思路，把 solver 内的 `routeopt_bkf_staged` 用在 V622 hard4 上做 600s smoke。

目标不是让学习组件提供 bound/certificate，而是只改变 Ryan-Foster branch pair 的排序：

```text
phase0 cheap screen
-> phase1 child LP probe
-> phase2 short heuristic pricing probe
-> weighted BKF score ordering
```

exact-safe 边界保持不变：

- branch score / phased testing 只影响分支候选排序；
- 不把 RMP objective 当 exact node bound；
- 不用学习结果剪枝；
- child 最终仍靠 exact pricing closure。

## V725 配置摘要

输入实例来自 V622 hard4：

- `greedy-anchor ... tasks020_04_seed61311`
- `greedy-anchor ... tasks020_07_seed61635`
- `sector-wave ... tasks020_05_seed61410`
- `sector-wave ... tasks020_08_seed61718`

关键配置：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_base_priority=fractionality
journey_branch_candidate_phased_testing_phase0_min_fractionality=0.45
journey_branch_candidate_phased_testing_phase1_lp_enabled=True
journey_branch_candidate_phased_testing_phase1_max_candidates=12
journey_branch_candidate_phased_testing_phase2_heuristic_enabled=True
journey_branch_candidate_phased_testing_phase2_max_candidates=3
journey_branch_candidate_phased_testing_phase2_time_limit=0.08
journey_branch_candidate_phased_testing_dynamic_k_enabled=True
journey_branch_candidate_phased_testing_dynamic_k_min_candidates=9
journey_branch_candidate_phased_testing_dynamic_k_phase1_max_candidates=12
journey_branch_candidate_phased_testing_dynamic_k_phase2_max_candidates=3
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_enabled=True
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_extra_candidates=2
journey_branch_candidate_phased_testing_bkf_score_order_enabled=True
journey_corrected_node_bound_fathom_enabled=False
journey_tail_action_early_branch_enabled=False
journey_tail_action_no_column_early_branch_enabled=False
```

输出：

- `BPC_future/results/20260628_v725_routeopt_bkf_weighted_smoke4_tasks20/results.csv`
- `BPC_future/results/20260628_v725_routeopt_bkf_weighted_smoke4_tasks20/logs/`

## 总体结果

与 V622 `retry_on` 相比，V725 在 hard4 中：

- `2/4` 从 `EXTERNAL_TIME_LIMIT` 变成 `OPTIMAL`；
- 另外 `2/4` 仍 timeout，但 gap 均改善；
- 没有出现 gap 恶化；
- sector-wave family 明显受益，greedy-anchor family 仍未闭环。

| instance | V622 status | V622 gap | V725 status | V725 wall | V725 gap | 变化 |
|---|---:|---:|---:|---:|---:|---|
| greedy seed61311 | EXTERNAL_TIME_LIMIT | 0.051215 | EXTERNAL_TIME_LIMIT | 600.019958 | 0.041522 | gap 改善 0.009693 |
| greedy seed61635 | EXTERNAL_TIME_LIMIT | 0.061278 | EXTERNAL_TIME_LIMIT | 600.018201 | 0.060588 | gap 改善 0.000690 |
| sector seed61410 | EXTERNAL_TIME_LIMIT | 0.034203 | OPTIMAL | 278.161323 | 0.000000 | timeout -> OPTIMAL |
| sector seed61718 | EXTERNAL_TIME_LIMIT | 0.043777 | OPTIMAL | 335.792500 | 0.000000 | timeout -> OPTIMAL |

## Root Branch / Phase 信息

| instance | root baseline | root selected | root candidates | phase1 probes | phase2 probes | branch | CB retry | fathom | 结果 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| greedy seed61311 | `[1,10]` | `[2,16]` | 41 | 10 | 4 | 24 | 38 | 6 | timeout, gap 改善 |
| greedy seed61635 | `[1,3]` | `[12,20]` | 57 | 11 | 3 | 34 | 38 | 3 | timeout, gap 小幅改善 |
| sector seed61410 | `[3,6]` | `[4,7]` | 27 | 10 | 4 | 7 | 15 | 8 | OPTIMAL |
| sector seed61718 | `[3,5]` | `[7,8]` | 30 | 11 | 3 | 17 | 35 | 18 | OPTIMAL |

### sector seed61410

Root selected `[4,7]`：

- phase1 min child LP gain: `2.66763`
- child gain product: `79.7445`
- phase2 negative child count: `0`
- root phase2 只测 `4` 个候选
- 最终 `278.16s OPTIMAL`

这说明分阶段 branch testing 能把原来 600s proof tail 的节点导向更快闭环路径。

### sector seed61718

Root selected `[7,8]`：

- phase1 min child LP gain: `11.8025`
- child gain product: `256.142`
- phase2 negative child count: `2`
- 最终 `335.79s OPTIMAL`

注意：这次运行使用的是 phase0 fallback 日志修补前的代码，日志里 root candidate 仍显示 `decision=filtered`。实际行为是 phase0 全部过滤后 fail-closed 回退到原候选池继续 phase1/phase2。这个行为 exact-safe，但旧日志容易误导训练。

## 意外点

### 1. Phase2 有 negative 不一定是坏事

`sector seed61718` root `[7,8]` 有 `phase2_negative_child_count=2`，但最终仍能闭环。这和 V717/V720 的 `[4,6]` 现象一致：不能把“短预算 heuristic probe 发现负列”硬判成坏分支。

更合理的 score 应继续看：

- `min(child_lp_gain)`
- `child_gain_product`
- `child_width_balance`
- negative severity / count
- 后续 fathom/gap/CB retry

### 2. Greedy-anchor 的 best dual 没动

两个 greedy-anchor timeout 的 best dual 与 V622 一样：

- seed61311: `547.186422`
- seed61635: `526.651393`

它们的改善主要来自 incumbent / gap，而不是 root corrected lower bound 抬升。这说明对这类 family，单靠 branch pair 选择不够，后续必须加 cuts/formulation 或更强 incumbent。

### 3. Phase0 全过滤 fallback 需要显式标记

旧日志里 `phase0_min_fractionality=0.45` 会在某些节点把所有候选过滤掉，然后 fail-closed 回退继续 phase1/phase2。行为没问题，但日志会把被选候选显示成 `filtered`。

这会污染训练标签，因此已补日志字段：

- `phased_testing_phase0_fallback_count`
- `phased_testing_phase0_fallback_all_filtered`
- `phased_testing_phase0_fallback_reason`
- candidate 级别：
  - `phased_testing_phase0_fallback_enabled`
  - `phased_testing_phase0_fallback_reason`

后续 V726+ 日志会正确区分：

```text
正常 phase0 通过
phase0 filtered
phase0 全过滤后 fail-closed fallback
```

## 代码变更

文件：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

本次新增的是日志/标签解释修补，不改变求解逻辑：

1. phase0 全过滤且 `fail_closed_to_priority_order=True` 时，给候选打 `_phased_testing_phase0_fallback` 标记。
2. `journey_branch_candidates` node 级日志记录 fallback count/reason。
3. candidate payload 记录 fallback enabled/reason。
4. summary 不再把 fallback 后继续 probe 的候选显示为单纯 `filtered`。

## 测试

已运行：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
```

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_weighted_score_does_not_over_penalize_small_phase2_negative \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_decision_snapshot_feeds_log_and_metadata_without_reordering \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1
```

结果：

```text
Ran 8 tests in 0.070s
OK
```

## 判断

V725 是明确正信号：

- RouteOpt/BKF phased branch testing 已经不只是离线 runbook；
- 在 hard4 上拿到 `2` 条严格 `TIMEOUT -> OPTIMAL` positive；
- 另 `2` 条 timeout 也有 gap 改善；
- 说明 branch pair controller 是当前最值得继续推进的主线。

但它还没有达到最终目标：

- hard4 仍有 `2/4` timeout；
- greedy-anchor 的 dual 不动，说明 formulation/cuts/incumbent 仍是瓶颈；
- 当前权重还没有证明能 full60 稳定提升。

## 下一步

建议顺序：

1. 用日志修补后的 V726 重跑同一 hard4，确认行为不变且 fallback 日志正确。
2. 对 greedy seed61311/61635 做 depth-1/depth-2 paired replay，重点看后续 child path，而不是只看 root pair。
3. 把 V725 的两条 strict positive 加入 branch action 数据集：
   - sector seed61410: `[3,6] -> [4,7]`
   - sector seed61718: `[3,5] -> [7,8]`
4. 对 greedy-anchor 标记为 `gap/fathom weak positive`，但不要当 strict full-solve positive。
5. 并行启动 pricing-compatible cuts / route-aware cuts / incumbent heuristic 设计，因为 greedy-anchor 的 best dual 没动。
6. V726 hard4 稳定后，再跑 random-TW 20 full60；如果 full60 只改善 sector-wave，不改善 greedy-anchor，则 cuts/formulation 优先级上调。
