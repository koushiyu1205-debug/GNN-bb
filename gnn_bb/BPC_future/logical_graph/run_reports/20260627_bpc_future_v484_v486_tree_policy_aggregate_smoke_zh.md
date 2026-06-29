# V484/V485/V486 Tree-Policy 聚合 Smoke 报告

日期：2026-06-27

## 目的

在 V481/V482 证明 instance-level tree replay 能恢复 2 个 V468 超时实例后，本轮测试更宽的泛化策略：

```text
多个成功日志
→ 按 family/site + depth 聚合 branch pair 和 child ordering
→ 在 V468 失败 holdout 实例上 opt-in replay
```

该策略只改变 branch pair 排序和 same/separate child 入队顺序，不提供 lower bound、certificate 或剪枝依据。

## V484 Map

输入：

```text
V468 当前 OPTIMAL 日志: 33
V481 恢复成功日志: 1
V482 恢复成功日志: 1
合计 parsed_log_count = 35
```

输出：

```text
BPC_future/results/journey_tree_policy_score_map_v484_v468opt_v481_v482_family_site_depth_20260627/
```

机器字段：

```text
key_scope = depth
context_scope = family_site
branch_score_row_count = 109
child_score_row_count = 218
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## V485 Holdout Smoke

6 个 holdout 都来自 V468 非 OPTIMAL 集合，且不使用它们自身成功树：

```text
greedy-anchor/apollo15 seed61103: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
greedy-anchor/tranq seed61744: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
random-wave/apollo15 seed61102: TIME_LIMIT -> TIME_LIMIT
random-wave/tranq seed61001: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
sector-wave/apollo15 seed61000: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
sector-wave/tranq seed61104: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
```

结论：

```text
OPTIMAL recovery = 0/6
hard_negative_count = 6
```

## 诊断

V485 不是没有生效，而是生效后仍无法闭环：

```text
greedy/apollo seed61103:
  branch hit 3/16, changed 1

greedy/tranq seed61744:
  branch hit 6/10, changed 4

random/apollo seed61102:
  branch hit 0/0, unchanged

random/tranq seed61001:
  branch hit 10/32, changed 9

sector/apollo seed61000:
  branch hit 1/25, changed 1

sector/tranq seed61104:
  branch hit 17/33, changed 16
```

这说明简单的 `family/site + depth + pair` 频率聚合不是可靠因果。它会在一些实例上大量改变分支，但这些改变并没有带来 proof closure，甚至可能只是把搜索导向另一个同样困难的 tree。

## 标签包

已落盘：

```text
BPC_future/data/gat_branch_action_sanity/v486_tree_policy_aggregate_smoke_labels_20260627/tree_policy_aggregate_labels.jsonl
```

汇总：

```text
row_count = 6
strong_positive_count = 0
hard_negative_count = 6
production_ready = False
```

这些是 tree-policy aggregate hard negative，不应混入 single-pair counterfactual dataset。

## 结论

V481/V482 的成功说明：

```text
具体实例的多节点 tree policy 可以恢复闭环
```

V485 的失败说明：

```text
仅按 family/site + depth 聚合成功树，不足以泛化
```

下一步应让 GAT 学上下文条件，而不是继续扩大频率聚合：

- node-level LP/RMP/proof-tail 状态；
- candidate set 结构；
- branch tree 的局部 constraint path；
- child width/balance；
- completion-bound retry / exact pricing proof cost；
- full replay wall-time gain。

也就是说，branch score 主线应从“pair 频率”转向“上下文 tree-policy 预测”。

## 已验证

```text
python -m unittest \
  BPC_future.tests.test_journey_tree_policy_score_map \
  BPC_future.tests.test_journey_tree_replay_score_map \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_force_pair_for_controlled_ab

python -m py_compile \
  BPC_future/scripts/build_journey_tree_policy_score_map.py \
  BPC_future/scripts/build_journey_tree_replay_score_map.py \
  BPC_future/solver/journey_driver.py
```

