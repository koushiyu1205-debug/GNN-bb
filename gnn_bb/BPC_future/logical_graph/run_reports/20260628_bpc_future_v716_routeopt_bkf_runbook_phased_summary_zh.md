# 20260628 V716：RouteOpt/BKF Runbook 消费 Phased Summary

## 结论

本轮把 V715 已经进入 solver/audit 日志链路的 RouteOpt/BKF phased-testing 摘要接到了离线 branch candidate replay runbook。

这不是 solver 行为变更，不运行 BPC / pricing / RMP，也不产生 official bound 或 certificate。它只改变后续 counterfactual replay / child-probe 的采样优先级，让 runbook 不再只按 top200、width、branch score 硬扫。

## 修改内容

代码：

- `BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py`
- `BPC_future/tests/test_journey_branch_candidate_replay_runbook.py`

新增能力：

1. runbook 读取节点级 phased summary：
   - `phased_testing_controller_active`
   - `phased_testing_phase1_best_min_child_lp_gain`
   - `phased_testing_phase1_best_child_lp_gain_product`
   - `phased_testing_phase2_negative_child_count_total`
   - `phased_testing_phase2_negative_journey_count_total`
   - `phased_testing_phase2_worst_negative_severity_max`

2. runbook 读取候选级 phase1/phase2 指标：
   - `phase1_min_child_lp_gain`
   - `phase1_child_lp_gain_product`
   - `phase2_negative_child_count`
   - `phase2_negative_journey_count`
   - `phase2_worst_negative_severity`
   - phase wall time

3. `routeopt_bkf` / `routeopt_bkf_staged` 的采样分数加入双 child 逻辑：
   - 奖励 `phase1_min_child_lp_gain`
   - 奖励 `phase1_child_lp_gain_product`
   - 惩罚 phase2 负列链、负列严重度和测试耗时
   - 继续保留 fractionality、branch score、child width、balance gap 等 cheap screen

4. exact-safe fail-closed：
   - 如果 phased source 标记了 `official_bound_effect` 或 `certificate_effect`，runbook 跳过该 event。
   - 候选级 phase probe 若标记 bound/certificate effect，在 staged BKF 中被过滤。
   - 报告新增 `phased_testing_exact_effect_skip_count`。

## 为什么这一步重要

V631/V636 说明单个 root pair 替代能改善 gap、fathom 和 branch count，但仍可能 600s timeout。问题不再是“有没有另一个 pair”，而是“这个 pair 是否同时让两个 child 的 proof path 变短”。

RouteOpt/BKF 的启发是：先用 cheap screen 缩小候选，再用有限测试信号判断是否值得 replay。V716 先在离线 runbook 层实现这一点，使后续 child-probe / paired replay 更像正式 phased branch testing 的数据采样，而不是盲扫 top200。

## 验证

已通过：

```text
python -m py_compile BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/tests/test_journey_branch_candidate_replay_runbook.py
python -m unittest BPC_future.tests.test_journey_branch_candidate_replay_runbook
```

单测结果：

```text
Ran 22 tests in 0.132s
OK
```

新增测试覆盖：

- 候选级 phase1 双 child gain 可以压过单纯高 branch score。
- phase2 negative-chain 风险会降低采样优先级。
- 节点级 phased summary 会提高 source event 优先级。
- 任何 phased official-bound/certificate effect 都 fail-closed 跳过。

## 仍未完成

这一步仍是离线 runbook 改进，不是最终目标：

- 还没有把 phased testing 升级为默认 solver 内 branch controller。
- 还没有跑全量 20-scale 60-instance 验证。
- 还没有解决 best dual 不动的 cuts/formulation 问题。
- 还没有证明所有 20 规模都能 600s 内 OPTIMAL。

下一步应把 V716 runbook 用在 V545/V622 hard contexts 上生成更干净的 paired child-probe/full replay 数据，然后再决定是否把相同 phased score 逻辑推进到 solver 内 opt-in branch controller。
