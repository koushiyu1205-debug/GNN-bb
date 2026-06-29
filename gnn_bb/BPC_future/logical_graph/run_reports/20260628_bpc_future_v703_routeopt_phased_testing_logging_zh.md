# V703 RouteOpt Phased Testing 日志增强

## 结论

V703 不改变 solver 决策逻辑，只增强 `routeopt_bkf_staged` 分支候选日志，方便后续构造 state-scoped branch replay / GAT branch action 数据集。

新增候选级字段：

```text
phased_testing_stage
phased_testing_decision
phased_testing_reason
phased_testing_elimination_reason
```

这些字段同时出现在：

- `journey_branch_candidates.top`
- `journey_branch_candidates.priority_top`
- 最终 `journey_branch` selected metadata

## 字段含义

典型取值：

| stage | decision | 含义 |
|---|---|---|
| `disabled` | `disabled` | phased testing 未启用 |
| `depth_gate` | `depth_gate_fallback` | 超过 phased testing 深度限制，回退原排序 |
| `score_gate_preserve` | `preserved_score_gate_winner` | score gate 高置信 winner 被保护 |
| `score_gate_preserve` | `skipped_by_score_gate_winner_preserve` | 因保护 winner，未进入后续 phased test |
| `phase0_cheap_screen` | `filtered` | cheap screen 淘汰 |
| `phase1_lp` | `skipped_by_dynamic_k` | dynamic-K 未选入 LP probe |
| `phase1_lp` | `probed_complete` / `probed_incomplete` | 已做 child LP probe |
| `phase2_heuristic` | `skipped_by_dynamic_k` | dynamic-K 未选入 heuristic probe |
| `phase2_heuristic` | `probed_complete` / `probed_incomplete` | 已做短预算 heuristic child probe |

`phased_testing_elimination_reason` 只在候选被 filter / skip / incomplete 时填入；通过完整 probe 的候选为空字符串。

## 为什么要做

之前日志已经有：

- `phase1_min_child_lp_gain`
- `phase1_child_lp_gain_product`
- `phase1_child_width_balance`
- `phase2_negative_child_count`
- `phase2_worst_negative_severity`

但数据构建脚本仍要从多个字段推断一个候选到底为什么没有被选择。V703 把这个判断前移到 solver 日志里，后续可以直接区分：

1. cheap screen 不合格；
2. score gate 保护导致未测；
3. dynamic-K 未覆盖；
4. LP probe 不完整；
5. heuristic probe 不完整；
6. 完整 probe 后排序落后。

这对应 RouteOpt/BKF 思路里的 phased candidate testing，有助于训练“何时测、测多少、选哪个 pair”，而不是继续盲目扩大 top-K replay。

## Exact-Safe 边界

V703 只增加日志字段：

- 不改变 branch pair 排序；
- 不改变 child queue 顺序；
- 不改变 retry / final judge；
- 不提供 official bound；
- 不提供 certificate；
- 不作为 prune/fathom 依据。

## 测试

通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1 \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_child_order_can_use_phase1_lp_objective \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_cuts_are_branch_depth_opt_in
```

## 下一步

下一步应把 V703 字段接入 branch replay 数据构建：

- 统计每个 context 的 `skipped_by_dynamic_k` 是否包含后验强正例；
- 用 `phase1_min_child_lp_gain`、`phase1_child_lp_gain_product`、`phase2_negative_child_count` 做多目标排序标签；
- 对 `probed_incomplete` 和右删失样本单独降权，避免把“没证完”误标成负例；
- 在 hard 20-scale 上优先收集 phase1/phase2 完整覆盖而不是继续扩大无结构 top-K。
