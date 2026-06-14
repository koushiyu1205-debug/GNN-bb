# BPC_future 根因审计补充：RC-C priority replay 与 return12 ablation

日期：2026-06-13

## 目标

本轮继续根因审计，目标不是把 RC-C 作为生产优化，而是验证：

1. 先前 RC-C 小跑为什么没有判定力；
2. 修正候选域后，`tranq20_01` 的 context-specific priority replay 是否能复现正向 trajectory；
3. 正向结果到底来自 priority task-set chain，还是来自更粗的 return12 / early quota 轨迹扰动。

本轮不启用 Sharded Pulse worker，不开放 certificate gate，不改变 lower-bound 语义。

## 实现修正

上一轮 `root_cause_rcc_context_replay_*` 小跑在当前默认 calibration 参数下没有进入有效 profile-DP negative candidate 域：

- 当前日志：`pricing_max_dp_states=1`，`profile_negative_candidate_count=0`；
- 旧 Phase 10H 有效日志：`pricing_max_dp_states=1000`，每轮有数百个 negative candidates。

因此那轮不能证明或证伪 RC-C。

本轮做了两个极窄修正：

1. `experimental_rcc_tranq20_task1_chain_20_only` 只在 `tranq20_01` / 20-task 下把 `journey_pricing_max_dp_states` 和 `journey_heuristic_max_dp_states` 提到至少 `1000`；
2. 增加纯诊断字段：
   - `profile_priority_candidate_count`
   - `profile_priority_selected_candidate_count`
   - summary 中对应 `profile_dp_tail_priority_candidate_count`
   - summary 中对应 `profile_dp_tail_priority_selected_candidate_count`

这些字段只记录 priority mask 命中数量，不改变 reduced cost、materialization、RMP、certificate 或 lower-bound。

## 实验 1：baseline vs RC-C profile

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/root_cause_rcc_context_replay_profiledp1000_v2_20260613 \
  --instances apollo5 tranq5 apollo10 tranq20_01 \
  --profiles phase_rcc_context_replay \
  --repeat-count 3 \
  --time-limit 8.0 \
  --pricing-time-limit 0.2 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 8 \
  --quiet
```

结果文件：

- `BPC_future/results/root_cause_rcc_context_replay_profiledp1000_v2_20260613/summary.json`
- `BPC_future/results/root_cause_rcc_context_replay_profiledp1000_v2_20260613/summary.csv`

### 5/10 guard

在同一 `dp_states=1000` 校准域内，RC-C profile 对非目标实例 no-op：

| instance | baseline primal | RC-C primal | priority selected |
|---|---:|---:|---:|
| apollo5 r0/r1/r2 | 165.623455 / 165.623455 / 165.623455 | 165.623455 / 165.623455 / 165.623455 | 0 / 0 / 0 |
| tranq5 r0/r1/r2 | 180.521929 / 180.521929 / 180.521929 | 180.521929 / 180.521929 / 180.521929 | 0 / 0 / 0 |
| apollo10 r0/r1/r2 | 405.125490 / 405.125490 / 405.125490 | 405.125490 / 405.125490 / 405.125490 | 0 / 0 / 0 |

注意：这里证明的是 RC-C profile 本身 no-op，不代表 `dp_states=1000` 可默认用于小实例生产配置。生产默认仍不能放开。

### `tranq20_01`

| profile | primal r0 | primal r1 | primal r2 | priority selected | returned |
|---|---:|---:|---:|---:|---:|
| baseline | 783.715884 | 680.562363 | 783.715884 | 0 / 0 / 0 | 3 / 5 / 3 |
| RC-C priority | 584.389510 | 588.579014 | 588.579014 | 2 / 4 / 4 | 93 / 96 / 96 |

RC-C profile 让 `tranq20_01` 三次 repeat 均显著改善，并把 early sequence 推到 task-1 anchored active-support-changing additions。

但这还不能说明“priority chain 本身就是根因修复”，因为 RC-C profile 同时启用了 return12 / early quota。

## 实验 2：return12 ablation

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613 \
  --instances tranq20_01 \
  --profiles baseline experimental_early_new_task_set_quota_3_return12_20_only experimental_rcc_tranq20_task1_chain_20_only \
  --repeat-count 3 \
  --time-limit 8.0 \
  --pricing-time-limit 0.2 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 8 \
  --quiet
```

结果文件：

- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.json`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`

结果：

| profile | primal r0 | primal r1 | primal r2 | avg primal | priority selected | returned |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 783.715884 | 680.562363 | 783.715884 | 749.331377 | 0 / 0 / 0 | 3 / 5 / 7 |
| return12 quota | 592.501876 | 584.336280 | 584.336280 | 587.058145 | 0 / 0 / 0 | 96 / 96 / 96 |
| RC-C priority | 588.579014 | 588.579014 | 591.005020 | 589.387683 | 4 / 4 / 4 | 96 / 72 / 96 |

关键判断：

- return12 quota 不需要 priority mask 命中，也能达到与 RC-C 相同量级的改善；
- 本轮 return12 平均 primal 甚至略好于 RC-C；
- RC-C priority 确实改变了部分 later CG returned masks，例如 `[1,3,6]`、`[1,3,10]`，但没有稳定优于普通 return12；
- 因此不能把 `tranq20_01` 的改善归因于手写 priority chain 本身。

## 根因更新

本轮把根因进一步收紧：

> 当前最有证据支持的不是“某条固定 priority task-set chain”，而是 early returned batch 是否能产生有利的 active-support-changing RMP trajectory。return quota、batch size、具体 materialized JourneyColumn、signature、active basis transition 共同决定结果。

这解释了：

1. 为什么 Pulse worker 能加 true-RC negative columns 但没有稳定 ROI；
2. 为什么更负 RC 不一定更好；
3. 为什么 task-set family whitelist 不够；
4. 为什么 return12 可以在 `tranq20_01` 有效，却不能直接默认推广到 Apollo20 / Tranq20 hard set；
5. 为什么当前还不能宣称已经找到最终优化方向。

## 当前不能做的结论

不能说：

- RC-C priority chain 已证明是生产优化；
- return12 quota 可默认启用；
- task-1 anchored family 应默认优先；
- 20-task 已经能稳定大幅加速；
- 5/10 no-regression 与 20 improvement 已经同时满足；
- 目标完成。

可以说：

- context-sensitive early trajectory 是当前最有证据的根因层；
- 粗粒度 return batch 干预在 `tranq20_01` 上有可重复正信号；
- 手写 priority chain 不是充分解释；
- 下一步必须转向 active-support-changing batch / active-basis impact 的预测，而不是继续扩大 Pulse worker 或继续手写 task-set whitelist。

## 下一步建议

下一步不应做 production 默认优化。

建议进入一个新的 calibration-only phase：

1. 对 `tranq20_01`、`mt20_greedy_tranq_01`、`mt20_greedy_apollo_01` 同时记录 returned batch 的 active-support-changing count、new/replacement composition、signature hash 和下一轮 fractional pressure；
2. 比较 return8 / return12 / RC-C priority 中哪些 batch 让 `fractional_sum` 快速归零；
3. 只把能预测 active-support-changing impact 的规则作为候选，不再只看 task-set family 或 rough RC；
4. 继续保持 5/10 no-op、no certificate effect、no critical disagreement。

## 验证

Focused tests：

```text
Ran 4 tests in 0.003s
OK
```

语法检查：

```text
py_compile passed
```

本轮 smoke：

- `root_cause_rcc_context_replay_profiledp1000_v2_20260613`：24 rows；
- `root_cause_rcc_context_replay_return12_ablation_20260613`：9 rows；
- 所有 rows `critical_disagreement_count=0`；
- 无 Sharded Pulse worker；
- 无 official certificate / lower-bound effect。

目标仍未完成。
