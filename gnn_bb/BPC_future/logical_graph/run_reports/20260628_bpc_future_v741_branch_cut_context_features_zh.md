# V741 Branch Cut-Context Features

日期：2026-06-28

## 背景

V740 证明 `child-only dynamic SRC` 不是默认主线：

- seed61311 仍 OPTIMAL，但从 V736 的 `110.914s` 退化到 `360.263s`；
- seed61635 仍 timeout，gap/dual 不变；
- root 是否加 SRC 会改变 branch controller 输入和后续 tree shape。

因此 branch score / GAT 不能只学习：

```text
state -> pair
```

而必须学习：

```text
state + cut regime -> pair
```

否则 `[2,8]`、`[1,9]`、`[16,17]` 这类 pair 会被不同 cut 环境下的效果混在一起。

## 修改

### 1. branch 日志补 cut context

`journey_branch_candidates` 和 `journey_branch` 现在都会记录：

```text
cut_context_hash
cut_context_active_count
cut_context_subset_row_count
cut_context_fleet_lb_count
cut_context_dynamic_subset_row_regime
cut_context_dynamic_subset_row_cuts_enabled
cut_context_dynamic_subset_row_audit_enabled
cut_context_dynamic_subset_row_cut_gate_enabled
cut_context_dynamic_subset_row_min_depth
cut_context_dynamic_subset_row_min_add_depth
cut_context_dynamic_subset_row_max_depth
cut_context_dynamic_subset_row_max_rounds
cut_context_dynamic_subset_row_gate_min_best_violation
cut_context_dynamic_subset_row_gate_min_violated
```

`cut_context_dynamic_subset_row_regime` 当前取值：

```text
dynamic_src_off
dynamic_src_audit_only
dynamic_src_on
dynamic_src_gated
dynamic_src_child_or_deeper
```

### 2. GAT branch-action dataset 补 context features

`BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA` 末尾新增：

```text
cut_context_active_count
cut_context_subset_row_count
cut_context_fleet_lb_count
cut_context_dynamic_subset_row_regime_code
cut_context_dynamic_subset_row_cuts_enabled
cut_context_dynamic_subset_row_cut_gate_enabled
cut_context_dynamic_subset_row_min_add_depth
cut_context_dynamic_subset_row_max_depth
cut_context_dynamic_subset_row_gate_min_best_violation
```

旧日志没有这些字段时默认填 `0`，不会破坏已有数据构建；新日志可让模型区分 root-gated SRC、child-only SRC、audit-only 等上下文。

## 为什么这一步重要

V736/V740 对同一 seed61311 的对比说明：

| config | status | wall | nodes | exact pricing | CB retry | SRC added |
|---|---:|---:|---:|---:|---:|---:|
| V736 root+child gated SRC | OPTIMAL | 110.914 | 7 | 30 | 7 | 20 |
| V740 child-only gated SRC | OPTIMAL | 360.263 | 21 | 97 | 62 | 9 |

如果训练数据只记录 pair，不记录 cut context，模型会把两个完全不同的 proof landscape 混成一个状态，后续 score map 会不稳定。

## 验证

已通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_metadata_records_cut_context \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_min_add_depth_delays_root_cut_addition \
  BPC_future.tests.test_gat_branch_action_sanity_dataset.GATBranchActionSanityDatasetTests.test_builds_graph_samples_with_walltime_gain_as_main_label
```

## Exact-Safe

这些字段只用于日志和训练特征，不参与：

- official bound；
- pricing certificate；
- fathom/prune；
- child lower-bound inheritance。

它们不会改变求解行为，只让后续 GAT/branch-score 数据避免 cut-regime 泄漏。
