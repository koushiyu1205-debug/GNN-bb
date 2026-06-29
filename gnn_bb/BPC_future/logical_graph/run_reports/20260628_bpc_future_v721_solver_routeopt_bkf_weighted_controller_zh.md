# V721 Solver 内 RouteOpt/BKF weighted phased controller 更新

日期：2026-06-28

## 这一步解决的问题

V717-V720 paired probe 暴露了一个具体问题：

- `[10,19]` 和 `[15,17]` 没有 phase2 negative child，但实测比 baseline 慢。
- `[4,6]` 有 `phase2_negative_child_count=1`，但实测最快，wall time 相对 baseline `[15,19]` 改善约 `9.87s`，child proof CPU 也更低。

这说明当前 phased testing / BKF 逻辑不能把“出现少量负列”硬当成坏信号。更合理的是把它和双 child LP gain、gain product、child width balance、phase2 negative severity、probe time 一起加权判断。

## 当前代码状态

solver 内其实已经有 RouteOpt 风格 phased branch testing，不是只有离线 runbook：

- phase0 cheap screen
- phase1 child LP probe
- phase2 short heuristic pricing probe
- dynamic K
- diverse pool
- branch candidate log/metadata

关键文件：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

## 本次改动

### 1. 新增 opt-in BKF weighted score

新增 helper：

```python
_journey_branch_candidate_phased_bkf_score(candidate, phased_testing)
```

它计算：

- `phase1_min_child_lp_gain`
- `phase1_child_lp_gain_product`
- `phase1_sum_child_lp_gain`
- `phase2_negative_child_count`
- `phase2_negative_journey_count`
- `phase2_worst_negative_severity`
- `child_width_balance`
- `child_max_width`
- `fractionality`
- `phase_wall`
- incomplete probe penalty
- dynamic-K excluded penalty
- exact effect penalty

注意：这个 score 只用于 branch candidate ordering，不是 lower bound、certificate 或 pruning signal。

### 2. 新增配置入口

默认关闭，避免影响现有 baseline：

```text
journey_branch_candidate_phased_testing_bkf_score_order_enabled=False
```

打开后，phase1/phase2 probed candidates 会按 weighted BKF score 排序。

主要权重默认值：

```text
phase1_min_gain_weight      = 6.0
phase1_product_weight       = 0.03
phase2_negative_child_penalty   = 0.75
phase2_negative_journey_penalty = 0.005
phase2_worst_negative_penalty   = 0.25
child_width_balance_penalty     = 0.0015
child_max_width_penalty         = 0.0002
phase_wall_time_penalty         = 0.01
incomplete_probe_penalty        = 100.0
dynamic_k_excluded_penalty      = 30.0
```

这组默认值是按 V717-V720 的校准结果调整的：少量 phase2 negative 仍会扣分，但不会压倒明显更好的双 child gain/product。

### 2.1 phase-specific dynamic-K

V722 smoke 暴露出一个预算问题：phase1 和 phase2 不能共用一个很小的 dynamic-K cap。phase1 是便宜 child LP probe，应该覆盖更宽的 near-tie pool；phase2 是更贵的 heuristic pricing probe，才应该收窄。

新增配置：

```text
journey_branch_candidate_phased_testing_dynamic_k_phase1_max_candidates
journey_branch_candidate_phased_testing_dynamic_k_phase2_max_candidates
```

如果不设置，仍回退到原来的全局：

```text
journey_branch_candidate_phased_testing_dynamic_k_max_candidates
```

同时，`dynamic_k_excluded` candidate 的 BKF score 现在会加 penalty，避免未进入 phase2 的候选因为 `phase2_negative=0` 被误读成比已测试候选更好。这个字段用于日志和训练解释，不提供 bound/certificate。

### 3. 日志补齐

`journey_branch_candidates` 的 selected/top/priority_top candidate payload 增加：

- `phased_testing_bkf_score`
- `phased_testing_bkf_reason`

node-level log 增加：

- `phased_testing_bkf_score_order_enabled`
- `phased_testing_bkf_phase1_min_gain_weight`
- `phased_testing_bkf_phase1_product_weight`
- `phased_testing_bkf_fractionality_weight`
- `phased_testing_bkf_phase2_negative_child_penalty`
- `phased_testing_bkf_phase2_worst_negative_penalty`
- `phased_testing_dynamic_k_phase1_max_candidates`
- `phased_testing_dynamic_k_phase2_max_candidates`

`journey_branch` metadata 增加：

- `phased_testing_bkf_score_order_enabled`
- `phased_testing_bkf_score`
- `phased_testing_bkf_reason`

这些字段后续可以进入 branch label / score map / replay 数据集。

## 为什么这是 RouteOpt 启发下的正确方向

RouteOpt 的 branching 思路不是 top-N 全扫，也不是模型单次拍板，而是：

```text
cheap screen
-> LP testing
-> heuristic testing
-> 少量 exact/paired replay
-> 用测试反馈调整分支选择
```

V721 把我们已有 solver 内 phased testing 往这个方向推进了一步：

- 仍保留 dynamic K，避免 top200 硬扫。
- 排序目标从“少 negative 优先”的硬规则，改成“两个 child 均衡收益 + proof risk”的 weighted score。
- 保持 opt-in，避免影响现有 canonical baseline。
- 明确 fail-safe：学习/score 不提供 exact bound，也不剪枝。

## 测试

已运行：

```bash
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
```

```bash
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
Ran 8 tests in 0.086s
OK
```

追加 phase-specific dynamic-K / dynamic-K excluded penalty 后再次运行：

```text
Ran 8 tests in 0.063s
OK
```

## Seed61716 smoke 结果

实例：

`apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716`

统一条件：

- time limit：`220s`
- `max_nodes=5`
- `journey_max_cg_iterations=32`
- early branch off
- `journey_corrected_node_bound_fathom_enabled=False`
- exact pricing closure 保持不变

| 版本 | root branch 策略 | status | wall_time | solving_time | pricing | exact | generated seq | evaluated trips | 备注 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| V717 forced selected | force `[15,19]` | OPTIMAL | 159.353445 | 138.100026 | 39 | 14 | 2,030,973 | 1,058,117 | 旧 selected baseline |
| V717 forced alt | force `[4,6]` | OPTIMAL | 149.480225 | 116.775387 | 36 | 13 | 1,932,706 | 953,514 | paired probe 中最快 forced pair |
| V722 | weighted BKF，但 phase1/phase2 共用小 K | OPTIMAL | 193.133375 | 161.538771 | 43 | 17 | 2,721,936 | 1,260,424 | 选到低 fractionality `[12,15]`，明显变慢 |
| V723 | phase0 min fractionality + phase1 wide / phase2 narrow | OPTIMAL | 144.131386 | 141.985225 | 39 | 15 | 2,302,467 | 1,161,352 | root 选 `[10,19]`，wall 最短 |
| V724 | phase1 至少测 9 个，phase2 仍测 3 个 | OPTIMAL | 145.598911 | 143.507099 | 39 | 15 | 2,302,640 | 1,162,181 | root 仍选 `[10,19]`，`[4,6]` 已进入 phase1/phase2 probe |

### smoke 解读

1. V722 证明“只加 weighted score”不够。没有 fractionality cheap screen、phase1 K 又太窄时，controller 会选到 `[12,15]` 这种 LP gain 高但 root branching 整体较慢的 pair。

2. V723/V724 证明 RouteOpt 式分阶段预算是必要的：phase0 限制 near-tie，phase1 放宽测试，phase2 收窄测试，能避免 V722 的明显退化。

3. V724 中 `[4,6]` 已进入 phase1/phase2 probe，但 root 仍选 `[10,19]`。这说明当前 BKF score 不只是复现 forced `[4,6]`，而是在当前 solver 状态下选了另一个也能 145s 左右闭环的 pair。这个结果是正面的，但还只是单实例 smoke。

4. V724 暴露出一个日志风险：未进入 phase2 的候选不能把缺失 negative signal 当作 0 风险。代码已追加 `dynamic_k_excluded_penalty`，后续新日志会避免这种训练解释污染。

## 下一步

1. 用 V723/V724 这类配置跑 4-8 个 hard contexts smoke。
2. 对比旧 phased order vs weighted BKF order：
   - selected pair 是否变化；
   - phase1 min gain/product 是否提高；
   - phase2 negative 是否只是小风险，而不是 proof tail 爆炸；
   - wall time / child proof CPU / CB retry 是否改善。
3. 新 smoke 必须使用 dynamic-K excluded penalty 后的新日志，避免旧 V724 里未测试候选分数偏高的问题进入训练。
4. 如果 4-8 hard contexts 不退化，再放到 random-TW 20-scale full60 的 branch-score mainline。
5. 同时继续推进 retry taxonomy 和 cuts/formulation，因为 BKF weighted branch 只能优化 proof-tail 子树闭环，不能解决所有 `z_RMP < UB` 的下界不足问题。
