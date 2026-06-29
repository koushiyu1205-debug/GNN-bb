# 20260627 GAT Branch Action v455 Overlay Smoke12 诊断报告

## 结论

v455 evidence overlay 在 12 个 20-scale random-TW smoke 实例上有局部改善，但不满足扩大到全量 60-instance 的条件。

核心改善来自一个已验证强正例的精确重放：

- `tranquillitatis ... greedy-anchor ... seed61414`
- v438: `TIME_LIMIT`, wall `556.130s`
- v455: `OPTIMAL`, wall `96.152s`
- capped wall-time gain: `+459.978s`
- root branch pair 从 baseline `[13,16]` 改为 evidence overlay pair `[6,20]`

其余已完成实例基本持平；多数困难实例仍为 `EXTERNAL_TIME_LIMIT`。因此 v455 说明“强证据 pair 的 score-gated opt-in 重放有效”，但还不能说明模型已经学会跨 context 泛化。

## 配置

运行目录：

`BPC_future/results/20260627_v455_v454_overlay_gate850_smoke12/`

score map：

`BPC_future/results/gat_branch_action_v453_weighted_walltime_20260627/score_map_v454_evidence_overlay_v438logs/journey_branch_score_rows.json`

关键配置：

- `journey_branch_candidate_priority=branch_score_horizon`
- `journey_branch_candidate_score_selection_gate_enabled=True`
- `journey_branch_candidate_score_selection_gate_min_score=0.67`
- `journey_branch_candidate_score_selection_gate_max_pool_total_child_width=850`
- `journey_branch_candidate_score_selection_gate_max_pool_balance_gap=100`
- `journey_branch_candidate_score_selection_gate_max_pool_child_width=450`
- `journey_early_branching_enabled=False`
- `journey_tail_action_early_branch_enabled=False`
- `journey_tail_action_no_column_early_branch_enabled=False`

注意：本轮 v455 没有启用 early branch，只验证 branch score 改 Ryan-Foster pair 排序本身。

## 总体指标

| 配置 | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT | capped mean | OPTIMAL-only mean | OPTIMAL-only median | <=200s OPTIMAL |
|---|---:|---:|---:|---:|---:|---:|---:|
| v438 proofrisk gate067 smoke12 | 3/12 | 1/12 | 8/12 | 497.043s | 202.794s | 144.881s | 2/12 |
| v455 evidence overlay gate850 smoke12 | 4/12 | 0/12 | 8/12 | 458.875s | 176.625s | 120.629s | 3/12 |

相对 v438：

- OPTIMAL 数：`+1`
- capped mean：`-38.168s`
- `<=200s OPTIMAL`：`+1`
- 主要贡献：seed61414 单实例 `+459.978s`

## 逐实例对比

| instance | v438 | v438 wall | v455 | v455 wall | gain |
|---|---:|---:|---:|---:|---:|
| greedy seed61744 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| greedy seed61206 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| greedy seed61414 | TIME_LIMIT | 556.130 | OPTIMAL | 96.152 | +459.978 |
| greedy seed61001 | OPTIMAL | 58.415 | OPTIMAL | 59.044 | -0.629 |
| sector seed61923 | OPTIMAL | 405.086 | OPTIMAL | 406.198 | -1.112 |
| apollo seed61103 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| greedy seed61846 | OPTIMAL | 144.881 | OPTIMAL | 145.107 | -0.226 |
| greedy seed61520 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| random seed61411 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| greedy seed61103 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| sector seed61104 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |
| random seed61001 | EXTERNAL_TIME_LIMIT | 600.000 | EXTERNAL_TIME_LIMIT | 600.000 | 0.000 |

## Root Branch Score Gate 命中

| instance | selected pair | changed | score | gate | reason | baseline pair | baseline rank |
|---|---:|---:|---:|---:|---|---:|---:|
| apollo seed61103 | `[1,2]` | false | 0.458 | false | score_below_min | `[1,2]` | 1 |
| greedy seed61001 | `[3,12]` | true | 0.720 | true | ok | `[2,18]` | 17 |
| greedy seed61103 | `[10,15]` | false | 0.417 | false | score_below_min | `[10,15]` | 1 |
| greedy seed61206 | `[5,9]` | false | 0.432 | false | score_below_min | `[5,9]` | 1 |
| greedy seed61414 | `[6,20]` | true | 0.740 | true | ok | `[13,16]` | 18 |
| greedy seed61520 | `[4,7]` | false | 0.508 | false | score_below_min | `[4,7]` | 1 |
| greedy seed61744 | `[1,4]` | false | 0.408 | false | score_below_min | `[1,4]` | 1 |
| greedy seed61846 | `[2,5]` | false | 0.494 | false | score_below_min | `[2,5]` | 1 |
| random seed61001 | `[8,13]` | false | 0.491 | false | score_below_min | `[8,13]` | 1 |
| random seed61411 | `[1,9]` | false | 0.486 | false | score_below_min | `[1,9]` | 1 |
| sector seed61104 | `[5,14]` | false | 0.473 | false | score_below_min | `[5,14]` | 1 |
| sector seed61923 | `[13,20]` | true | 0.720 | true | ok | `[1,13]` | 12 |

实际改 pair 的只有 3 个：

- `[6,20]` on greedy seed61414：强正例，带来 `TIME_LIMIT -> OPTIMAL`
- `[3,12]` on greedy seed61001：已是快速 OPTIMAL，基本持平
- `[13,20]` on sector seed61923：已是 OPTIMAL，基本持平

这说明 gate 的保守性是有效的：大多数陌生 context 没有被低置信度 score 改 pair。但这也说明当前 score map 的泛化覆盖不足。

## Exact-Safe 审计

v455 关闭了 early branch，score 只影响正常分支候选排序。

已审计 seed61414 和 seed61001 的 root 分支前都有 `FULL_LP_CERTIFICATE` / `CERTIFIED_NO_NEGATIVE`，child 继承的是已闭合 LP bound，而不是 early branch 中未闭合 RMP objective。

本轮没有用 GAT score 提供 official bound、certificate 或剪枝依据。

## 解释

v455 的收益不是来自“模型已经普遍学会分支”，而是来自 evidence overlay 将已确认强正例 `[6,20]` 提升到足够高的 score，并放宽 width cap 让它通过 gate。

之前 gate cap 更紧时，seed61414 的 `[6,20]` 会被 `pool_total_width` / `pool_child_width` 阻挡。v455 的 `850/450` cap 让这条强正例通过，因此完整求解时间从 556s 降到 96s。

但对于其它 8 个仍超时实例，score map 没有给出高置信替代 pair，系统回退 baseline pair，所以状态基本没有变化。这符合当前数据状态：强正例数量太少，而且主要是 instance/context specific replay，还不足以训练出稳健的跨 context ranking。

## 判断

不建议直接跑全量 60-instance v455。

原因：

- smoke 只有 `4/12 OPTIMAL`，仍有 `8/12 EXTERNAL_TIME_LIMIT`
- capped mean `458.875s`，距离 20-scale 600s 全求优目标很远
- 改善主要集中在一个已知强正例，泛化证据不足
- 对未知困难实例，gate 大多回退 baseline，不能解决 proof tail

## 下一步

继续主攻 branch score，但不要扩大部署。下一轮应补三类数据：

1. 对仍超时实例做 root forced replay 的高价值候选搜索，优先围绕 v455 没有改 pair 的 `score_below_min` context。
2. 对已知强正例做邻域反事实：同实例相邻 pair、同 family 同时间窗结构 pair，区分“可迁移特征”与“单实例记忆”。
3. 对 false/no-effect pair 继续做 hard negative overlay，避免模型把“高 child score / 宽分支”误当成 wall-time gain。

训练门槛仍不应降低：

- strong/weak wall-time gain 正例需要跨 context；
- hard negative 至少同量级；
- score map 在 production 前必须标记 strict full replay 覆盖，不应只依赖 child-probe 或 right-censored 代理。

## Verification

已通过：

```text
python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_gat_branch_action_sanity_training \
  BPC_future.tests.test_gat_branch_score_proofrisk_overlay \
  BPC_future.tests.test_journey_child_score_map \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_child_min_iter_and_child_order \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_selection_gate_falls_back_on_width_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_score_gate_requires_confident_scored_pair
```

结果：`Ran 10 tests ... OK`

