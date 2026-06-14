# BPC_future 根因审计补充：counterfactual replay candidate manifest

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

上一轮 counterfactual replay coverage 说明：

- 现有日志有少量 pure improved-vs-pure worsened descriptor pairs；
- 这些 pairs 只能作为 controlled replay 候选；
- 不能直接作为 production selector 训练集。

本轮目标是把这些候选展开成可执行 manifest，并选出首批 3 个 replay 候选。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_counterfactual_replay_coverage_20260613/summary.json
```

脚本：

```text
BPC_future/scripts/select_counterfactual_replay_candidates.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/select_counterfactual_replay_candidates.py \
--output-dir BPC_future/results/root_cause_counterfactual_replay_candidates_20260613 \
--top-n 3
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/summary.json
BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/candidates.csv
```

## Manifest 结果

```text
candidate_count = 40
low_context_noise_candidate_count = 3
mixed_descriptor_context_candidate_count = 37
recommended_candidate_ids = [
  replay_candidate_001,
  replay_candidate_003,
  replay_candidate_004
]
```

选择策略：

1. 优先选 `mixed_descriptor_count = 0` 的 low-context-noise exact contexts；
2. low-context-noise 候选尽量来自不同 exact context；
3. 加一个 high-coverage mixed-descriptor context 作为 stress case；
4. 这些候选只用于 replay，不是优化证据。

## 推荐候选 1：replay_candidate_001

风险等级：

```text
candidate_risk = low_context_noise
```

exact context：

```text
instance = mt20_greedy_tranq_01
cg_iter = 2
pricing_kind = heuristic
active_hash_before = 5c6420f757a39d2d
rmp_objective_before = 761.814403
```

context labels：

```text
{improved: 3, worsened: 4}
```

improved descriptor：

```text
rows = 3
best_rc = -32.4676425
returned_count = 1
returned_task_sets = 2,7,9
returned_sequences = 2,7,9
returned_arc_families = low_risk,low_risk,low_risk,low_risk
```

worsened descriptor：

```text
rows = 2
best_rc = -50.859356
returned_count = 1
returned_task_sets = 7,9,10,17
returned_sequences = 17,10,9,7
returned_arc_families = low_energy,low_time,low_risk,low_risk,low_energy
```

这个候选值得优先 replay，因为同 exact context 下没有 mixed descriptors，且 improved / worsened descriptor 都有重复样本支持。

## 推荐候选 2：replay_candidate_003

风险等级：

```text
candidate_risk = low_context_noise
```

exact context：

```text
instance = mt20_greedy_apollo_01
cg_iter = 3
pricing_kind = heuristic
active_hash_before = 16862add48072518
rmp_objective_before = 780.586496
```

context labels：

```text
{improved: 1, worsened: 1}
```

improved descriptor：

```text
rows = 1
best_rc = -20.1912655
returned_count = 8
returned_task_sets = 5,14,18|3,14,18|10,14,18|14,18|14,15,18|5,12,18|4,8,14|5,10,18
returned_sequences = 14,18,5|3,14,18|10,14,18|14,18|14,18,15|12,18,5|14,8,4|10,18,5
```

worsened descriptor：

```text
rows = 1
best_rc = -64.283449
returned_count = 8
returned_task_sets = 4,14,18|5,14,18|3,14,18|10,14,18|14,18|14,15,18|5,12,18|4,8,14
returned_sequences = 14,18,4|14,18,5|3,14,18|10,14,18|14,18|14,18,15|12,18,5|14,8,4
```

这个候选样本支持弱，但它是另一个 low-context-noise context，并且 improved descriptor 的 best RC 反而不如 worsened descriptor，更适合检验“更负 RC 不等于更好 trajectory”。

## 推荐候选 3：replay_candidate_004

风险等级：

```text
candidate_risk = mixed_descriptor_context
```

exact context：

```text
instance = tranq20_01
cg_iter = 1
pricing_kind = heuristic
active_hash_before = aa2b834c9d43f2a6
rmp_objective_before = 838.004841
```

context labels：

```text
{improved: 13, worsened: 7}
```

improved descriptor：

```text
rows = 3
best_rc = -57.0891735
returned_count = 12
returned_task_sets = 5,15,20|13,18,20|5,18,20|2,18,20|13,15,20|1,15,20|1,18,20|10,18,20|3,15,20|10,15,20|12,15,20|12,18,20
returned_sequences = 20,15,5|20,18,13|20,18,5|20,18,2|20,15,13|20,15,1|20,18,1|20,18,10
```

worsened descriptor：

```text
rows = 3
best_rc = -57.089173441
returned_count = 1
returned_task_sets = 5,15,20
returned_sequences = 20,15,5
```

这个候选不是低噪声 context，因为同 context 中仍有 mixed descriptor；它适合作为 stress case，检验“同一个 seed sequence 扩展成更大 returned batch 是否改变 trajectory”。

## 对根因判断的影响

这轮没有证明优化方向已经成立，但把下一步从泛泛的“做 replay”收窄为 3 个具体候选：

1. 一个 Tranq20 low-context-noise single-column contrast；
2. 一个 Apollo20 low-context-noise returned-batch contrast；
3. 一个 Tranq20 high-coverage mixed-context stress contrast。

这些候选如果后续 controlled replay 仍无法稳定区分 trajectory，就说明现有 returned descriptor 层特征还不够，需要更深的 RMP/dual path replay 或主动构造 counterfactual batch。

如果 replay 成功，才可以讨论 opt-in selector A/B。

## 当前目标状态

目标仍未完成。

理由：

- 现在只有 replay 候选清单；
- 还没有执行 controlled replay；
- 还没有证明任何 selector / worker / pricing 修改能 exact-safe、5/10 不退化、20 大幅加速。
