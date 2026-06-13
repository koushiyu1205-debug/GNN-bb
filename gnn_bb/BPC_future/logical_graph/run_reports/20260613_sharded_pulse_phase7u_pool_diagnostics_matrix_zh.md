# Sharded Pulse Phase 7U Pool Diagnostics Matrix 报告

日期：2026-06-13

## 目标

本轮使用 Phase 7U 新增的 `journey_pool_structure_diagnostics` 字段，跑一个小型 diagnostic-only matrix。

目标不是证明性能提升，也不是继续调 worker gate，而是回答：

1. 5/10 gate 是否继续阻止 active worker 干扰小实例；
2. 20-task 中 worker 加列后，RMP/列池结构是否有可解释变化；
3. 当前 active worker ROI 缺口更像 column-pool/RMP 问题，还是 pricing / final-judge residual tail 问题。

## 运行矩阵

### 5/10/20 短 matrix

输出目录：

`BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_matrix_20260613/`

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_matrix_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 tranq20_01 mt20_greedy_apollo_01 mt20_greedy_tranq_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 1.0 \
--pricing-time-limit 0.2 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.12 \
--current-probe-max-recursions 50000 \
--worker-max-recursions 50000 \
--max-cg-iterations 3 \
--quiet
```

### 20-only 1s diagnostic smoke

输出目录：

`BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_20_smoke_1s_20260613/`

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_20_smoke_1s_20260613 \
--instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 1.0 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 5000 \
--quiet
```

## 5/10 Gate 结论

短 matrix 中：

| instance | scale | worker events | added | official changed | critical |
|---|---:|---:|---:|---:|---:|
| apollo5 | 5 | 0 | 0 | false | 0 |
| tranq5 | 5 | 0 | 0 | false | 0 |
| apollo10 | 10 | 0 | 0 | false | 0 |
| tranq10_09 | 10 | 0 | 0 | false | 0 |

结论：

- 20-only worker profile 没有在 5/10 上触发；
- official result 没有被 worker 改动；
- no critical disagreement；
- 这继续支持“worker 默认关闭 / scale gate 必须保留”。

## 20-task Pool/RMP 观测

### 短 matrix

| instance | profile | worker | added | pool unique | duplicate ratio | active sets | active fractional ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| tranq20_01 | baseline | 0 | 0 | 250 | 0.0 | 13 | 0.538461538 |
| tranq20_01 | worker | 0 | 0 | 250 | 0.0 | 13 | 0.538461538 |
| mt20_greedy_apollo_01 | baseline | 0 | 0 | 164 | 0.0 | 12 | 0.0 |
| mt20_greedy_apollo_01 | worker | 1 | 1 | 164 | 0.0 | 12 | 0.0 |
| mt20_greedy_tranq_01 | baseline | 0 | 0 | 250 | 0.0 | 15 | 0.866666667 |
| mt20_greedy_tranq_01 | worker | 0 | 0 | 250 | 0.0 | 15 | 0.866666667 |

短 matrix 中 `mt20_greedy_apollo_01` worker 加列发生在尾部，没有 follow-up RMP，因此 pool fields 仍是加列前最后一次 RMP 快照，不能用于判断吸收效果。

### 20-only 1s diagnostic smoke

| instance | profile | wall | primal | worker | added | pool unique | active sets | active fractional | follow-up |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| mt20_greedy_apollo_01 | baseline | 0.765276 | 921.640296 | 0 | 0 | 166 | 10 | 0.0 | no_worker_add |
| mt20_greedy_apollo_01 | worker | 0.791958 | 890.088613 | 1 | 1 | 167 | 10 | 0.0 | followup_found_negative |
| mt20_greedy_tranq_01 | baseline | 0.789723 | 758.608258 | 0 | 0 | 252 | 10 | 0.4 | no_worker_add |
| mt20_greedy_tranq_01 | worker | 0.790659 | 758.608258 | 1 | 0 | 252 | 10 | 0.4 | no_worker_add |
| tranq20_01 | baseline | 0.869841 | 783.715884 | 0 | 0 | 252 | 9 | 0.0 | no_worker_add |
| tranq20_01 | worker | 0.864987 | 783.715884 | 0 | 0 | 252 | 9 | 0.0 | no_worker_add |

关键点：

- `pool_duplicate_task_set_ratio_last=0.0` 对所有 20-task 行成立；
- `mt20_greedy_apollo_01` worker 增加了 1 个 new task-set，pool unique `166 -> 167`；
- `mt20_greedy_apollo_01` worker 后 active task-set hash 改变，RMP objective delta 为 `-171.465431`；
- 但 follow-up 仍是 `followup_found_negative`，且 wall `0.765276 -> 0.791958`；
- `mt20_greedy_tranq_01` worker 触发但没有加列；
- `tranq20_01` worker 没触发。

## ROI 判断

本轮诊断进一步确认：

1. active worker 子路线能在 `mt20_greedy_apollo_01` 改善 under-budget primal；
2. 该改善不是 pool duplicate 压力缓解带来的，因为 duplicate ratio 始终为 0；
3. worker 加列后 RMP 确实吸收了新 task-set，active support hash 变化，objective 明显移动；
4. 但 follow-up 仍找到负列，说明 worker 没有替代 legacy pricing / final judge tail；
5. 对 `mt20_greedy_tranq_01` / `tranq20_01`，worker 没有稳定产出可加列。

因此当前 blocker 更像：

- pricing residual tail / ordinary exact pricing 仍需找负列；
- worker 找到的是局部有用列，但不能减少后续 pricing 负列发现；
- 不是简单的 task-set duplicate column-pool 膨胀。

## Exactness 边界

本轮仍保持：

- worker profile opt-in；
- official certificate gate 关闭；
- Pulse no-column / incomplete / duplicate-only 不影响 official lower bound；
- worker 返回列仍走正常 add-column path；
- diagnostic fields 只读，不参与任何求解决策。

没有发现 critical disagreement。

## 下一步建议

不要继续做 active worker gate-stacking。

下一步建议转为：

### Phase 7V：Residual pricing / legacy tail attribution

目标：

定位 worker 加列后，follow-up `FOUND_NEGATIVE` 的来源：

- 是 ordinary pricing 仍快速找到强负列；
- 还是 profile-DP / direct-label tail 在当前池上仍大量展开；
- 或是 RMP dual 变化后产生了另一批 unrelated negative；
- 或是 worker 返回列没有覆盖后续 negative 的 task-set neighborhood。

建议新增只读诊断：

- follow-up negative journey task-set hash；
- worker changed task-set 与 follow-up negative task-set 的 overlap / Jaccard；
- follow-up negative true-RC decomposition；
- follow-up negative 是否 new task-set / replacement / active-support changing；
- follow-up generated/evaluated/profile-DP state 归因。

如果 Phase 7V 显示 follow-up negatives 与 worker task-set 关系很弱，则 active worker 不适合作为减少 tail 的工具，应转向 direct-label/profile pricing 本体优化。

如果 follow-up negatives 与 worker task-set 高度相关，则再考虑 support-neighborhood harvesting，而不是扩大 worker time limit。

## 结论

Phase 7U matrix 没有给出性能提升证据。

它给出的有用结论是：

- 小实例 gate 正常；
- pool duplicate pressure 不是当前主要问题；
- worker 的有效列可以被 RMP 吸收；
- 但 follow-up pricing 仍会继续找到负列；
- 当前更应诊断 residual pricing / legacy tail，而不是继续堆 worker gate 或做 official certificate gate。
