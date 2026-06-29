# V773 BKF Phase2 Pricing Pressure Balance

## 目的

V772 的 route-order child pricing probe 说明了一个关键现象：

有限池 child RMP gain 很大，不代表这个分支真的能闭环。短预算 pricing 经常马上找到负列，甚至 `best_reduced_cost` 很负。

因此 V773 不再只把 Phase2 记录成：

```text
negative_child_count
negative_journey_count
worst_negative_severity
```

而是把 pricing pressure 拆成双 child 可训练字段，进入 solver 内 `routeopt_bkf_staged` 的日志和 opt-in BKF score。

## 修改内容

文件：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

### 1. Phase2 heuristic probe 新增双 child pressure 字段

每个 candidate 的 `_phase2_heuristic_probe` 新增：

```text
same_child_negative_severity
separate_child_negative_severity
negative_severity_sum
negative_severity_gap
negative_severity_balance_ratio
negative_child_presence_balance_gap
```

含义：

- `same_child_negative_severity = max(0, -same_child_best_reduced_cost)`
- `separate_child_negative_severity = max(0, -separate_child_best_reduced_cost)`
- `negative_severity_sum`：两边负列压力总量
- `negative_severity_gap`：两边压力不均衡程度
- `negative_severity_balance_ratio`：两边压力均衡比例
- `negative_child_presence_balance_gap`：是否只有一边出现负列压力

这些字段不提供 bound，不产生 certificate，不剪枝。

### 2. BKF score 新增 pressure penalty

新增配置：

```text
journey_branch_candidate_phased_testing_bkf_phase2_negative_severity_sum_penalty=0.02
journey_branch_candidate_phased_testing_bkf_phase2_negative_severity_gap_penalty=0.05
journey_branch_candidate_phased_testing_bkf_phase2_negative_child_balance_penalty=0.25
```

BKF score 新增扣分：

```text
- severity_sum_penalty * negative_severity_sum
- severity_gap_penalty * negative_severity_gap
- child_balance_penalty * negative_child_presence_balance_gap
```

这比只看 `worst_negative_severity` 更接近 RouteOpt 的双 child balanced testing 思路：不仅看有没有一个 child 好，还看两个 child 是否都能降低 proof risk。

### 3. 日志和 metadata 补齐

`journey_branch_candidates` 的 candidate payload 新增：

```text
phase2_same_child_negative_severity
phase2_separate_child_negative_severity
phase2_negative_severity_sum
phase2_negative_severity_gap
phase2_negative_severity_balance_ratio
phase2_negative_child_presence_balance_gap
```

event 顶层新增：

```text
phased_testing_phase2_negative_severity_sum_total
phased_testing_phase2_negative_severity_gap_max
phased_testing_phase2_negative_severity_balance_ratio_min
phased_testing_bkf_phase2_negative_severity_sum_penalty
phased_testing_bkf_phase2_negative_severity_gap_penalty
phased_testing_bkf_phase2_negative_child_balance_penalty
```

`journey_branch` metadata 同步新增同名 phase2 字段，方便 full replay / dataset builder 不只依赖 branch candidate log。

## 精确性边界

V773 只影响：

- opt-in `routeopt_bkf_staged` 候选排序；
- branch candidate 日志；
- branch metadata；
- 后续训练特征。

它不影响：

- official lower bound；
- no-negative certificate；
- fathom/prune；
- exact pricing closure。

所有新增字段都来自短预算 heuristic probe，只能作为风险/调度信号。

## 测试

编译：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
```

聚焦测试：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_weighted_score_does_not_over_penalize_small_phase2_negative \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v762_preset_adds_route_order_penalty_only \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap
```

结果：

```text
Ran 6 tests in 0.039s
OK
```

## 当前意义

V773 把 V772 的结论真正接进了 solver 内 phased branch testing：

- child LP gain 仍然重要；
- 但如果 child pricing pressure 很大，BKF score 会降权；
- 如果只有一边 child 有严重负列压力，也会降权；
- 日志现在能区分“一个 pair 看起来 RMP gain 好”与“这个 pair 的某个 child 仍然有严重 pricing tail”。

这一步仍然不能单独实现 20 规模全量 600s OPTIMAL，但它让下一轮训练/score map 更接近真实闭环目标。

## 下一步

1. 把这些 phase2 pressure 字段接入 branch action dataset builder。
2. 在 random-TW hard cases 上比较 V762/V773 score ordering 是否减少“RMP gain 大但 pricing pressure 更差”的误选。
3. 继续并行推进 cuts/formulation：phase2 pressure 高的状态优先作为 route-aware cuts / stronger formulation 的目标样本。

