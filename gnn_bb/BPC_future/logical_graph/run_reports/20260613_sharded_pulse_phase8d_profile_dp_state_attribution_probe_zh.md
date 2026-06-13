# Sharded Pulse Phase 8D Profile-DP State Attribution Probe 报告

日期：2026-06-13

## 目标

Phase 8D 使用 Phase 8C 新增的 profile-DP state-explosion 归因字段，做窄范围真实 probe。

目标不是性能 A/B，也不是打开 Pulse worker 或 certificate gate，而是回答：

1. profile-DP state cap 更像少数 task-mask bucket 爆炸；
2. 还是 reachable mask 面整体扩张；
3. 提高 `journey_pricing_max_dp_states` 是否看起来是稳定修复方向。

## 运行矩阵

实例：

- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`

profiles：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`

运行配置：

- `time_limit=1.5`
- `pricing_time_limit=0.2`
- `max_cg_iterations=3`
- Apollo20: `pricing_max_dp_states=1000` 和 `5000`
- Tranq20: `pricing_max_dp_states=1000`

输出目录：

- `BPC_future/results/sharded_pulse_phase8d_profile_dp_attribution_cap1000_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8d_profile_dp_attribution_cap5000_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8d_profile_dp_attribution_tranq_cap1000_probe_20260613`

## 关键观测

### Apollo20 cap1000

baseline:

- status: `TIME_LIMIT`
- wall: `0.705032`
- primal: `921.640296`
- pricing: `FOUND_NEGATIVE`
- DP records: 3
- max `dp_state_count`: `1001`
- max `dp_nonempty_mask_count`: `132`
- max `dp_max_labels_per_mask_observed`: `24`
- representative `dp_labels_by_sortie_count`: `[[1,873]]`
- representative top buckets:
  - `[1,24,[4,5,15]]`
  - `[1,18,[9,10]]`

worker profile:

- status: `TIME_LIMIT`
- wall: `0.734248`
- primal: `890.088613`
- worker added journeys: `1`
- follow-up first negative: `5,8,15`
- relation to worker task set: `disjoint_task_set`
- follow-up max bucket: `24`
- follow-up nonempty mask count: `132`
- follow-up labels by sortie count: `[[1,873]]`

### Apollo20 cap5000

baseline:

- status: `TIME_LIMIT`
- wall: `0.765277`
- primal: `921.640296`
- pricing: `FOUND_NEGATIVE`
- DP records: 3
- max `dp_state_count`: `5001`
- max `dp_nonempty_mask_count`: `439`
- max `dp_max_labels_per_mask_observed`: `63`
- representative top buckets:
  - `[2,63,[3,4,10,11,18]]`
  - `[2,56,[3,4,10,16,18]]`

worker profile:

- status: `TIME_LIMIT`
- wall: `0.800282`
- primal: `890.088613`
- worker added journeys: `1`
- follow-up first negative: `5,8,15`
- relation to worker task set: `disjoint_task_set`
- follow-up max bucket: `63`
- follow-up nonempty mask count: `411`
- follow-up labels by sortie count: `[[1,1252],[2,2433]]`

### Tranq20 cap1000

baseline:

- status: `TIME_LIMIT`
- wall: `0.714593`
- primal: `738.351023`
- DP records: 3
- max `dp_state_count`: `1001`
- max `dp_nonempty_mask_count`: `90`
- max `dp_max_labels_per_mask_observed`: `30`
- representative top buckets:
  - `[1,30,[2,7,10,17]]`
  - `[1,24,[7,9,17]]`

worker profile:

- status: `TIME_LIMIT`
- wall: `0.714196`
- primal: `738.351023`
- worker added journeys: `0`
- DP records show the same max bucket / nonempty mask shape as baseline.

## 解释

当前 state explosion 不像“单一 mask bucket 灾难”。

更像：

1. cap1000 阶段已经有几十到一百多个 nonempty masks；
2. 单个 bucket 有增长，但 max bucket 约 `24-30`；
3. cap5000 后 Apollo 进入 2-sortie 层，nonempty masks 增到 `343-439`，同时 top bucket 增到 `63`；
4. state 增长来自 reachable mask 面扩张和二层 sortie 组合扩张，叠加部分高-label mask bucket。

因此，单纯提高 `journey_pricing_max_dp_states` 不是稳定修复：

- Apollo cap5000 允许更多搜索，但 wall 增加；
- worker 后 residual `5,8,15` disjoint negative 仍存在；
- 没有看到 completion-tail 被消掉；
- Tranq20 cap1000 没有触发 worker 加列收益。

## Exactness 边界

本轮没有改变：

- pricing DP 转移；
- dominance / pruning；
- Pulse worker trigger；
- candidate selection；
- RMP add-column path；
- certificate / official lower-bound 逻辑。

所有 probe 都保持默认 exactness 语义：

- Pulse incomplete / no-column 不证书化；
- worker added columns 仍走正常 true-RC add-column path；
- audit / summary 字段不影响 solver decision。

## 结论

Phase 8D 说明：profile-DP cap / proof-tail 问题主要不是一个简单的单 bucket 爆炸点，而是 broad reachable-mask expansion，尤其 Apollo cap5000 后进入 2-sortie 组合层导致 state 面快速增长。

下一步不建议继续简单提高 DP cap。

更合理的方向是：

1. 如果继续 profile-DP proof-tail：做结构性 mask/label 控制，例如按 active support / residual family 定向 materialization，而不是全局加 cap；
2. 如果追求整体 ROI：转向 RMP stabilization / active fractional degeneracy 或 column-pool compression；
3. 不应从这些结果打开 Pulse worker default 或 official certificate gate。
