# V744 RouteOpt Cut Snapshot Diagnostic Wall Fix

日期：2026-06-29

## 背景

V742 增加了 phase1 child LP probe 后的本地 dynamic SRC cut snapshot，用来观察：

- 当前 branch pair 在两个 child 上的 LP gain；
- 如果 child 局部加入 dynamic SRC，两个 child 的 LP gain 是否改善；
- cut regime 与 branch pair 的交互。

V743 把 cut snapshot 的正权重直接加入 BKF ordering 后，在 greedy-anchor hard2 上出现负结果：

- seed61311 从 V736 的 `110.914s OPTIMAL` 退化为 600s timeout；
- seed61635 仍未闭环；
- root pair 被 cut snapshot 信号改写，但全局 proof tail 没有改善。

这说明 cut snapshot 本身有诊断价值，但不能无校准地直接进入 live ordering。

## 本轮修正

本轮修复一个更隐蔽的问题：即使 cut snapshot 权重为 0，原实现中 phase1 probe 的 `wall_time` 也包含本地 cut snapshot 耗时。

由于 BKF score 里有：

```text
bkf_phase_wall_time_penalty
```

这会导致 cut snapshot 在“理论上 diagnostic-only”的情况下，仍通过耗时惩罚影响 candidate ordering。

现在拆成三类耗时：

```text
phase1_wall_time
```

只包含两个 child 的基础 LP probe 耗时，用于 BKF ordering 的 phase wall penalty。

```text
phase1_cut_snapshot_wall_time
```

只记录本地 cut snapshot 的额外耗时。

```text
phase1_diagnostic_wall_time
```

记录完整诊断耗时，包含基础 LP probe 和 cut snapshot。

controller summary 也对应增加：

```text
phased_testing_phase1_total_wall_time
phased_testing_phase1_cut_snapshot_total_wall_time
phased_testing_phase1_diagnostic_total_wall_time
```

## Exact-Safe 边界

该修复不改变：

- official bound；
- no-negative certificate；
- fathom/prune 逻辑；
- child lower bound exactness；
-真实 solver cuts/cut_keys。

cut snapshot 仍然只在 phase1 局部变量中构造，只作为诊断、训练特征或显式启用权重后的排序特征。

## Dataset 更新

`build_gat_branch_action_sanity_dataset.py` 的 context feature schema 增加：

```text
phase1_cut_snapshot_wall_time
phase1_diagnostic_wall_time
```

这样后续 GAT 分支数据可以区分：

- 基础 child LP testing 成本；
- cut snapshot 诊断成本；
- 完整诊断成本。

这对后续判断“某个 cut-aware signal 是否值得 live 使用”很重要。

## 测试

已通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py
```

已通过聚焦单测：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_phase1_cut_snapshot_is_diagnostic \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_ignores_cut_snapshot_diagnostic_wall_time \
  BPC_future.tests.test_gat_branch_action_sanity_dataset.GATBranchActionSanityDatasetTests.test_builds_graph_samples_with_walltime_gain_as_main_label
```

已通过 RouteOpt/BKF 相关单测组：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_phase1_cut_snapshot_is_diagnostic \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_ignores_cut_snapshot_diagnostic_wall_time \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_weighted_score_does_not_over_penalize_small_phase2_negative \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_is_logged_for_phase1 \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_metadata_records_cut_context \
  BPC_future.tests.test_gat_branch_action_sanity_dataset.GATBranchActionSanityDatasetTests.test_builds_graph_samples_with_walltime_gain_as_main_label
```

结果：

```text
Ran 10 tests in 1.020s
OK
```

## 判断

V744 不声称性能改善。它是一个 correctness-of-experiment 修复：

- 防止 diagnostic-only cut snapshot 偷偷改变 BKF live ordering；
- 让 V743 这类负结果更容易归因；
- 为后续 cut-aware branch training 留下干净字段；
- 保持 exact-safe 证书边界。

下一步应先跑一个小规模 V745 对照：

```text
phase1_cut_snapshot_enabled=True
cut_snapshot BKF weights = 0
```

预期：

- 如果 selected pair 与无 snapshot 基本一致，说明 V744 成功隔离诊断成本；
- 如果仍明显变差，说明 snapshot 的计算开销本身不能放进 live solver，只能离线采样或极小 K opt-in；
- 如果 seed61311 能恢复到接近 V736，而 seed61635 仍不动，则继续推进更强 cut family / formulation，而不是继续调普通 dynamic SRC。
