# V527 State-Key Root Overlay Smoke4

日期：2026-06-27

## 目的

验证 V526 新增的 `branch_state_key` / `journey_branch_candidate_score_require_state_key=True` 不会破坏现有 V467 strict replay root overlay 的 exact-safe 求解链路。

本轮只测试 4 个已知 root overlay 正例；不是 full60 通过证据。

## 配置

```text
config = BPC_future/configs/moon_trek_20_smoke.yaml
score_path = BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/score_map_v467_conservative_overlay_on_branchonly60/journey_branch_score_rows.json
time_limit = 600
max_workers = 4
journey_branch_candidate_priority = branch_score_horizon
journey_branch_candidate_score_horizon_tie_tolerance = 1.0
journey_branch_candidate_score_horizon_min_score = 0.0
journey_branch_candidate_score_require_state_key = True
journey_branch_candidate_score_selection_gate_enabled = True
journey_branch_candidate_score_selection_gate_min_score = 0.67
journey_branch_candidate_score_selection_gate_max_pool_total_child_width = 850
journey_branch_candidate_score_selection_gate_max_pool_balance_gap = 100
journey_branch_candidate_score_selection_gate_max_pool_child_width = 450
journey_early_branching_enabled = False
journey_tail_action_early_branch_enabled = False
journey_tail_action_no_column_early_branch_enabled = False
journey_gat_admission_scheduler_enabled = False
```

输出：

```text
BPC_future/results/20260627_v527_v467_statekey_root_overlay_smoke4_tasks20/results.csv
BPC_future/results/20260627_v527_v467_statekey_root_overlay_smoke4_tasks20/logs
```

## 结果

| instance | V468 | V527 state-key | delta |
|---|---:|---:|---:|
| apollo greedy seed61614 | OPTIMAL 340.47s | OPTIMAL 365.31s | +24.84s |
| apollo random seed61408 | OPTIMAL 475.39s | OPTIMAL 496.71s | +21.32s |
| tranq greedy seed61001 | OPTIMAL 57.23s | OPTIMAL 76.78s | +19.55s |
| tranq random seed61411 | OPTIMAL 341.75s | OPTIMAL 363.46s | +21.71s |

汇总：

```text
rows = 4
OPTIMAL = 4
capped_mean = 325.565534
median = 364.387019
max = 496.705216
<=200s OPTIMAL = 1
```

## State-Key 审计

4 个实例的 root score 均从 state-key 命中：

```text
apollo greedy seed61614: selected [4,19], source state:root::node:0:depth:0:4,19
apollo random seed61408: selected [5,13], source state:root::node:0:depth:0:5,13
tranq greedy seed61001: selected [3,4], source state:root::node:0:depth:0:3,4
tranq random seed61411: selected [2,10], source state:root::node:0:depth:0:2,10
```

child/deeper 节点没有 state score 时均按 `missing_score_source` 回退到正常 fractionality 选择；没有把 root score 误用到 child context。

## Exact-Safe 边界

- `journey_early_branch_trigger = 0`
- admission scheduler 关闭
- 学习组件只改变 Ryan-Foster branch ordering
- 没有使用学习分数作为 official bound、certificate 或剪枝依据
- 最终 4 个实例均由原 exact pricing / completion-bound closure 返回 `OPTIMAL`

## 结论

V526/V527 解决的是上下文错配风险：现有 root strict overlay 可以在 `require_state_key=True` 下继续生效，而 child context 缺分数时 fail closed。

但这不提升 full60 覆盖率。V468 仍只有 `33/60 OPTIMAL`，剩余 27 个非最优实例需要继续生成 strict replay positive，尤其是 state-aware child/deeper branch context 的证据。

下一步不应直接跑同一 root-only overlay full60；更有效的是：

1. 对 V468 剩余非最优实例重新采集带 `branch_state_key` 的 branch candidate 日志；
2. 生成 state-aware child/depth replay runbook；
3. 用短 fixed-expansion/child-probe 筛掉明显 hard negative；
4. 只对高希望 pair 做 600s full replay，新增 strict positive 后再 overlay。
