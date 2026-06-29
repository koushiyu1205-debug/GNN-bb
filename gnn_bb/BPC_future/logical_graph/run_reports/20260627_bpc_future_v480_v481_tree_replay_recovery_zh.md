# V480/V481/V482 Tree Replay Recovery 诊断报告

日期：2026-06-27

## 结论

本轮确认了一个关键事实：旧成功实例不能靠单个 root pair 或单条 path-prefix 稳定复现，但可以靠 tree-level branch score + child score 在当前代码中复现为 `OPTIMAL`。

这说明当前 branch 正例的因果粒度应从：

```text
root pair / 单条 path-prefix
```

升级为：

```text
多节点 branch-tree policy + child ordering
```

## V480：path-prefix replay

输入旧成功日志：

```text
BPC_future/results/20260626_ablation_earlybranch_branch_admission_randomtw60/off/tasks020/branch_only/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json.jsonl
```

修复项：

- `force_pair_path` 现在允许当前 depth segment 带 `same_vehicle/separate_vehicle` kind。
- `force_pair_path` 现在忽略未来 depth segment，而不是把当前节点判为不匹配。

验证：

```text
002 depth1 prefix: EXTERNAL_TIME_LIMIT, 600.016s
004 depth2 prefix: EXTERNAL_TIME_LIMIT, 600.016s
007 depth4 prefix: EXTERNAL_TIME_LIMIT, 600.016s
008 depth4 prefix: EXTERNAL_TIME_LIMIT, 600.017s
```

虽然 forced pair 均命中，但没有闭环。因此这些不是严格正例，只能作为 hard negative / insufficient-cause 标签。

## V481/V482：tree-level replay

新增脚本：

```text
BPC_future/scripts/build_journey_tree_replay_score_map.py
```

V481 输出：

```text
BPC_future/results/journey_tree_replay_score_map_v481_old_success_seed61309_20260627/
```

导出内容：

```text
branch_score_row_count = 14
child_score_row_count = 28
solver_branch_priority = branch_score_horizon
solver_child_priority_mode = child_score
production_ready = False
certificate_effect = False
official_bound_effect = False
```

V482 输出：

```text
BPC_future/results/journey_tree_replay_score_map_v482_old_success_seed61513_20260627/
```

运行结果：

```text
seed61309:
  V468 当前 best: EXTERNAL_TIME_LIMIT, 600.017s
  V481 tree replay: OPTIMAL, 468.536s
  旧 ablation branch-only: OPTIMAL, 462.015s
  objective = 552.21958

seed61513:
  V468 当前 best: EXTERNAL_TIME_LIMIT, 600.019s
  V482 tree replay: OPTIMAL, 360.203s
  旧 ablation branch-only: OPTIMAL, 354.444s
  objective = 638.144841
```

V481 的 `journey_branch_candidates` 中 14/14 个 branch event 命中 score source；`journey_child_queued` 中 28 个 child ordering row 命中旧 tree 顺序。

V482 的 `journey_branch_candidates` 中 12/12 个 branch event 命中 score source；`journey_child_queued` 中 24 个 child ordering row 命中旧 tree 顺序。

两者都基本复现了对应旧成功树。

当前从 20260626 ablation 八组结果中能找到的“旧配置 OPTIMAL、V468 当前失败”的 20 规模实例只有 2 个；这 2 个均已通过 tree replay 恢复为 `OPTIMAL`。

## 解释

V477 root-only 和 V480 path-prefix 失败，V481/V482 tree replay 成功，说明这些改善不是某个单独 Ryan-Foster pair 的效果，而是多个节点上的 pair 选择和 same/separate child 顺序共同改变了搜索闭环路径。

所以后续训练数据不能只把 `[2,5]` 这种 root pair 标成强正例；正确标签应记录：

- branch tree 中哪些节点被 score 改变；
- child ordering 是否跟随成功 tree；
- 最终 full replay 是否 `TIME_LIMIT -> OPTIMAL`；
- 若仅 path-prefix 失败，应作为 insufficient-cause hard negative。

## Exact-Safe 边界

V481 只改变：

- branch pair 排序；
- same/separate child 入队顺序。

它不提供：

- official lower bound；
- certificate；
- 剪枝依据；
- RMP objective 的 exact node bound。

子节点仍继承合法 lower bound，最终仍由 exact pricing closure 证明。

## 下一步

1. 用 V481 方式批量扫描旧成功日志，导出 tree-level replay score map。
2. 对 V468 中仍 `EXTERNAL_TIME_LIMIT` 的实例逐个做 tree replay，抽取严格标签：
   - `TIME_LIMIT -> OPTIMAL`：strong positive；
   - path-prefix 失败但 tree replay 成功：tree-policy positive；
   - tree replay 仍失败：hard negative / drift case。
3. 把 `branch_impact_model` 的主标签从单 pair gain 扩展为 tree-policy gain：
   - node-level pair score；
   - child-order score；
   - full replay wall-time gain；
   - branch tree proof cost。
4. score-gated early branch 不应裸用 root score；应要求 tree-policy confidence 或至少多节点 score coverage。

## 标签包

已落盘：

```text
BPC_future/data/gat_branch_action_sanity/v483_tree_replay_labels_20260627/tree_replay_labels.jsonl
```

汇总：

```text
row_count = 6
strong_positive_count = 2
hard_negative_count = 4
strict_time_limit_to_optimal_count = 2
production_ready = False
```

含义：

- 2 条 strong positive：V468 `EXTERNAL_TIME_LIMIT`，tree replay `OPTIMAL`。
- 4 条 hard negative：V480 path-prefix replay 强制命中但仍 `EXTERNAL_TIME_LIMIT`，说明 path-prefix 是 insufficient cause。
- 这些标签是 tree-policy 标签，不是 single-pair 标签。

## 已验证测试

```text
python -m unittest BPC_future.tests.test_journey_tree_replay_score_map \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_force_pair_for_controlled_ab

python -m py_compile \
  BPC_future/scripts/build_journey_tree_replay_score_map.py \
  BPC_future/scripts/build_journey_branch_path_replay_runbook.py \
  BPC_future/solver/journey_driver.py
```
