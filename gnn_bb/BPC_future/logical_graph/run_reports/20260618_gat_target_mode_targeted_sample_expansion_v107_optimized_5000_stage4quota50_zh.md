# GAT Target Mode v107 Optimized Targeted Sample Expansion - Stage 4 Quota50 Report

日期：2026-06-19

## 执行边界

本报告只记录离线样本扩充与 artifact 重建结果；没有训练模型，没有启用 GAT online，没有生成 certificate 或 official bound。100-scale sector-wave 补样过程中补齐了 diagnostic-only replay capture event，目的是让日志采集与 root heuristic 分支一致；该改动不改变 pricing 选择、bound、certificate 或 production solver 语义。

当前结论只针对 5000 条 selected target-level rows 的样本配额合同。Stage 4 audit binding 仍未完成，因此不能声明 `stage4_candidate_ready`、`stage4_audit_precondition_data_ready` 或 production readiness。

## Stage 4 偏置配额合同

计划规模保持 `5000` 条 selected target-level rows，但配额改为更偏 Stage 4 的版本：

| scale | target rows | 占比 | 80% 最低线 |
|---:|---:|---:|---:|
| 20 | 2500 | 50% | 2000 |
| 30 | 500 | 10% | 400 |
| 50 | 1000 | 20% | 800 |
| 100 | 1000 | 20% | 800 |

family 总配额保持 `sector-wave=2000`、`random-wave=1800`、`greedy-anchor=1200`。交叉配额为：

| scale | sector-wave | random-wave | greedy-anchor | total |
|---:|---:|---:|---:|---:|
| 20 | 1000 | 900 | 600 | 2500 |
| 30 | 175 | 200 | 125 | 500 |
| 50 | 425 | 350 | 225 | 1000 |
| 100 | 400 | 350 | 250 | 1000 |

Stage 4 20-scale 支撑门槛：

```text
20-scale total rows >= 2000
20-scale Level A/B target rows >= 800
20-scale hard pairs >= 600
```

## 输入与输出

当前 graph dataset：

```text
BPC_future/data/gat_batch_impact/v107_optimized_5000_stage4_biased_first362_scale30first16_greedy30cap4_worker16_sector30cap4_worker16_scale50sgcap12_scale100open34_batch24_sectorcapfix_20context180new120batch4_followup40_20260619
```

当前 selected subset 输出：

```text
BPC_future/results/gat_target_mode_targeted_sample_expansion_v107_optimized_20260619_expanded_stage4quota50_first362_scale100open34_batch24_sectorcapfix_20context180new120batch4_followup40
```

主要 artifacts：

```text
stage3_targeted_target_rows_v107_optimized.jsonl
stage3_targeted_batch_samples_v107_optimized.jsonl
stage3_targeted_pair_index_v107_optimized.jsonl
selection_manifest_v107_optimized.json
sample_allocation_report_v107_optimized.md
stage4_gate_audit_binding_manifest_v107_optimized.json
```

## 补样轨迹

first238 版本解决了 100-scale coverage，但 20-scale Level A/B 仍不足：

```text
effective_target_rows = 5000
effective_batch_samples = 761
same-context hard pairs = 2149
Level A/B target rows = 1160
Level C weak rows = 3840
20-scale Level A/B rows = 330
100-scale rows = 809
```

first327 版本追加 20-scale context180/new120/batch4 worker rows 后，总 Level A/B 过线，但 20-scale Level A/B 仍差 120：

```text
effective_target_rows = 5000
effective_batch_samples = 754
same-context hard pairs = 5560
Level A/B target rows = 1510
Level C weak rows = 3490
20-scale Level A/B rows = 680
20-scale hard pairs = 5050
```

followup40 worker-only runbook 继续只补 20-scale Level A/B：

```text
commands = 38
executed = 38
failed = 0
elapsed_s = 1002.63
all_checks_pass = true
worker rows = 35
positive trajectory ROI rows = 23
nonpositive trajectory ROI rows = 12
```

合并后 first362 graph dataset：

```text
sample_count = 1221
candidate_count = 13352
20-scale batch samples = 792
same-context pair count = 2050
same-context comparable pairs = 1543
positive-negative label pairs = 612
training_ready = true
ranking_ready = true
```

## Selected Subset 结果

| 指标 | 当前值 | 门槛 | 状态 |
|---|---:|---:|---|
| effective target rows | 5000 | 5000 | pass |
| effective batch samples | 751 | 500 | pass |
| unique contexts | 391 | 350 | pass |
| same-context hard pairs | 5560 | 1200 | pass |
| Level A/B target rows | 1644 | 1500 | pass |
| Level C weak rows | 3356 | <=3500 | pass |
| Level A/B hard pairs | 5560 | 500 | pass |
| 20-scale rows | 2660 | 2000 | pass |
| 20-scale Level A/B rows | 814 | 800 | pass |
| 20-scale hard pairs | 5050 | 600 | pass |
| 100-scale rows | 809 | 800 | pass |
| Stage4 audit evaluable rows | 0 | >0 / complete audit | fail |

selected scale 分布：

```json
{"20": 2660, "30": 500, "50": 1000, "100": 809, "10": 22, "5": 9}
```

selected family 分布：

```json
{"sector-wave": 2084, "random-wave": 1740, "greedy-anchor": 1176}
```

selected family x scale 分布：

```json
{
  "20|sector-wave": 1160,
  "20|random-wave": 900,
  "20|greedy-anchor": 600,
  "30|sector-wave": 175,
  "30|random-wave": 200,
  "30|greedy-anchor": 125,
  "50|sector-wave": 425,
  "50|random-wave": 350,
  "50|greedy-anchor": 225,
  "100|sector-wave": 320,
  "100|random-wave": 281,
  "100|greedy-anchor": 208
}
```

Level A/B 分布：

```json
{"20": 814, "30": 48, "50": 5, "100": 777}
```

标签组分布：

```json
{
  "high_roi_positive": 1789,
  "accepted_low_roi_negative": 2801,
  "delay_risk_negative": 226,
  "bad_mode_negative": 184
}
```

## 当前结论

Stage 4 偏置的 5000-row 样本配额已经达到样本质量合同。除 Stage 4 audit binding 外，数量、family、scale、family x scale、Level A/B、Level C 上限、hard pairs、20-scale Level A/B 和 20-scale hard pairs 门槛均已通过。

因此，下一步不应继续盲目提高 20-scale 总量。20-scale 已从计划的 2500 实际选到 2660，并且 `20-scale Level A/B target rows=814/800`。继续补 20-scale 只有在能生成 audit-evaluable rows、替换 Level C weak rows、或补充 checkpoint-bound failure cases 时才有意义。

当前仍不能声明：

```text
targeted_sample_expansion_complete = false
stage3_retraining_data_ready = false
stage4_audit_precondition_data_ready = false
stage4_candidate_ready = false
production_ready = false
```

原因是 `stage4_gate_evaluable_rows=0`，当前样本还没有绑定到训练后的 checkpoint、kNN/OOD audit、online shadow gate 和 20-task A/B audit。它们可以支撑 Stage 3 retraining 的 candidate-level heads、same-context pairwise ranking 和 batch-level ROI/tail/CBF heads，但不能直接作为 Stage 4 gate 通过证据。

## 后续优先级

1. 用当前 5000-row selected subset 启动 Stage 3 retraining，不再把“继续采 20-scale 总量”作为默认优先级。
2. 训练后绑定 checkpoint，生成 kNN/OOD audit rows，并把 audit manifest 回填到 `stage4_gate_audit_binding_manifest_v107_optimized.json`。
3. Stage 4 shadow / opt-in 前，单独统计 checkpoint-bound 的 20-task A/B、tail risk、CBF、delay-risk false-safe 和 OOD gate。
4. 如果还要补样，优先补 audit-evaluable / checkpoint-bound rows；其次补 100-scale full quota 缺口；最后才考虑普通 Level C raw rows。

## 与目标模式五阶段计划的对齐

`gat_bpc_future_target_mode_optimization_plan_zh.md` 的主线定义是：

```text
Learning-guided discovery, exact-certified closure
```

因此本轮 5000-row 扩样的定位必须严格限制在离线训练数据合同：

- GAT / CBF / kNN / OOD 只能学习 discovery、priority、admission scheduling；
- true-RC negative 可以被 `HIGH_PRIORITY` 或 `DELAY_QUEUE` 调度，但不能被永久丢弃；
- `DELAY_QUEUE` 不是 reject，不能参与 no-negative certificate；
- final optimality proof 仍只来自当前 branch/cut/dual 下 exact pricing 的 exhaustive no-negative closure。

五阶段对齐如下：

| 阶段 | 主线目标 | 本轮 5000-row 扩样的作用 | 当前状态 |
|---|---|---|---|
| Stage 1 | batch-impact / trajectory-oriented model structure | 提供 candidate、batch、context 三层 label 粒度，支持 future heads | 数据侧已具备输入，不代表模型结构已完成 |
| Stage 2 | same-context intervention data collection | 已形成 `5000` 条 selected target rows、`751` 个 batch samples、`5560` 个 hard pairs | 样本配额已闭合 |
| Stage 3 | precision-constrained ROI maximization training | 可用于 candidate-level heads、same-context pairwise ranking、batch-level ROI/tail/CBF heads | 仍需重新训练 checkpoint 和 gate-first threshold/OOD selection |
| Stage 4 | shadow / opt-in testing with no-regression and ROI audit | 提供 Stage 4 前置候选数据，但未产生 checkpoint-bound audit rows | `stage4_gate_evaluable_rows=0`，未 ready |
| Stage 5 | 20/30/50/100 exact-safe acceleration | 20-scale 支撑增强，100-scale coverage 达到 80% gate；只能作为后续加速路径数据基础 | 不能声明 20-task exact target 或 production candidate |

最重要的边界是 Stage 3 与 Stage 4 的分界：

```text
样本配额已完成
!= checkpoint gate pass
!= kNN/OOD safe-source ready
!= Stage 4 shadow / opt-in ready
!= production_ready
```

Stage 3 后续训练必须保持主计划里的硬目标：

```text
primary_objective = precision_constrained_roi_maximization
checkpoint_selection_policy = gate_first
```

也就是说，训练脚本、threshold frontier、checkpoint selector 和报告必须先过滤：

```text
precision / safe precision
precision CI lower bound
false-high-priority / false-safe / accepted_bad_mode
accepted ROI
ROI over random / best-RC / old-GAT baseline
accepted ROI CI lower bound
nonzero useful coverage
family / context holdout
```

之后才允许用 utility、tail proxy、validation loss、F1 或 recall 做 tie-breaker。任何只因为 validation loss、F1、AUC、recall 或 embedding separation 更好而选出的 checkpoint，都只能标记为 diagnostic checkpoint。

Stage 4 后续验收必须重新绑定训练后的 checkpoint：

```text
1. frozen threshold / OOD / fallback rule
2. checkpoint-bound decision records
3. kNN/OOD false-safe audit
4. 5/10 no-regression shadow
5. 20-task same-context ROI / tail-risk A/B
6. certificate safety audit
```

本轮的一个重要发现是：100-scale exact-context / `before_exact` 短时 fallback 不稳定地产生 worker materialization row，而 open-context materialization + actual worker context self-binding 可以产出 Level A/B 训练证据；同时 node/B&B heuristic pricing 分支需要 diagnostic-only replay capture parity，才能让 sector-wave 100-scale 补样不被日志缺口卡住。这个发现只改变样本采集与审计可观测性，不改变 solver 决策语义。

因此，下一条主线建议是：

```text
停止普通总量型补样
-> 用当前 5000 selected rows 训练 Stage 3 diagnostic checkpoint
-> 生成 checkpoint-bound threshold / OOD / fallback audit
-> 再决定是否进入 Stage 4 shadow
```
