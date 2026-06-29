# V742 Phase1 Branch-Cut Snapshot Testing

日期：2026-06-28

## 背景

V740 的负结果说明：

- root dynamic SRC 不能简单关闭；
- child-only SRC 对 seed61311 明显退化，对 seed61635 无改善；
- branch pair 的效果依赖当前 cut regime。

因此下一步不能继续只做：

```text
pair -> child LP gain
```

而应记录：

```text
pair -> child LP gain under current cuts
pair -> child LP gain after local child dynamic SRC snapshot
```

这对应 RouteOpt 的 candidate testing 思路：先用 cheap/LP test 缩小候选，再用更接近实际 proof landscape 的测试信号决定 branch。

## 修改

在 solver 内的 RouteOpt/BKF phased testing 增加 opt-in：

```text
journey_branch_candidate_phased_testing_phase1_cut_snapshot_enabled
journey_branch_candidate_phased_testing_phase1_cut_snapshot_force_dynamic_src_enabled
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_min_gain_weight
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_product_weight
```

默认：

```text
phase1_cut_snapshot_enabled = False
cut_snapshot BKF weights = 0
```

所以现有配置行为不变。

## 行为

当 `phase1_cut_snapshot_enabled=True` 时，phase1 对每个被 dynamic-K 选中的 branch pair 做：

1. 在当前 cuts 下解 same/separate 两个 child RMP；
2. 对每个 child 的 LP 解本地分离一轮 dynamic SRC；
3. 把本地 cuts 加到临时 cut list；
4. 本地重解 child RMP；
5. 记录 cut 后的 child LP gain。

注意：这些 cut 只存在于 phase1 snapshot 的局部变量中，不会注册到真实 node 的 `cuts/cut_keys`。

## 新增日志字段

candidate / selected / branch metadata 中新增：

```text
phase1_cut_snapshot_enabled
phase1_cut_snapshot_complete
phase1_cut_snapshot_depth
phase1_cut_snapshot_added_total
phase1_same_child_cut_snapshot_status
phase1_separate_child_cut_snapshot_status
phase1_same_child_cut_snapshot_added
phase1_separate_child_cut_snapshot_added
phase1_same_child_cut_snapshot_objective
phase1_separate_child_cut_snapshot_objective
phase1_same_child_cut_snapshot_lp_gain
phase1_separate_child_cut_snapshot_lp_gain
phase1_cut_snapshot_min_child_lp_gain
phase1_cut_snapshot_sum_child_lp_gain
phase1_cut_snapshot_child_lp_gain_product
phase1_same_child_cut_snapshot_wall_time
phase1_separate_child_cut_snapshot_wall_time
```

controller summary 中新增：

```text
phased_testing_phase1_cut_snapshot_enabled_count
phased_testing_phase1_cut_snapshot_complete_count
phased_testing_phase1_cut_snapshot_added_total
phased_testing_phase1_best_cut_snapshot_min_child_lp_gain
phased_testing_phase1_best_cut_snapshot_child_lp_gain_product
```

GAT branch-action dataset context features 中新增：

```text
phase1_cut_snapshot_complete
phase1_cut_snapshot_added_total
phase1_cut_snapshot_min_child_lp_gain
phase1_cut_snapshot_child_lp_gain_product
```

## 为什么这是必要的

V736/V740 显示同一个实例在不同 cut timing 下 proof tree 差异很大：

```text
V736 seed61311: 110.914s, 7 nodes, 30 exact pricing, 7 CB retry
V740 seed61311: 360.263s, 21 nodes, 97 exact pricing, 62 CB retry
```

如果 branch score 只看无 cut 的 child LP gain，会低估 root/child cut 对后续 proof tail 的影响；如果只看全局 pair，也会把不同 cut regime 的效果混在一起。

## 下一步实验

建议新增 V743：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_phase1_lp_enabled=True
journey_branch_candidate_phased_testing_phase1_cut_snapshot_enabled=True
journey_branch_candidate_phased_testing_dynamic_k_enabled=True
journey_branch_candidate_phased_testing_bkf_score_order_enabled=True
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_min_gain_weight=2.0
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_product_weight=0.01
```

先跑 greedy-anchor hard2：

- seed61311：确认不比 V736 明显退化；
- seed61635：看 root/depth1 selected pair、gap、fathom、CB retry 是否改善。

如果 V743 仍不能动 seed61635 的 dual/gap，则说明 seed61635 需要更强 cut family，而不是继续调 branch testing。

## 验证

已通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_phase1_cut_snapshot_is_diagnostic \
  BPC_future.tests.test_gat_branch_action_sanity_dataset.GATBranchActionSanityDatasetTests.test_builds_graph_samples_with_walltime_gain_as_main_label
```

## Exact-Safe

V742 的 cut snapshot：

- 不写入真实 solver cuts；
- 不改变 official bound；
- 不产生 certificate；
- 不参与 fathom/prune；
- 只作为 branch testing 日志、排序特征和训练特征。

如果后续启用 BKF cut-snapshot 权重，它也只影响 branch candidate order，不影响证书边界。
