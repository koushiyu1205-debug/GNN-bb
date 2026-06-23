# 2026-06-23 BPC_future GAT Stage 3 v140 Train-only Failure Analog Boost 综合报告

## 结论

v140 是一次 Stage 3 诊断性推进，不是 Stage 4 candidate。

本轮从 v139 剩余的 3 个 validation-only focused failures 出发，只挖掘 train split
内的相似正负对，并把它们并入 focused-pair boost selector。训练后 local deployment
gate 仍然通过，ROI / precision 指标略优于 v139，但 focused same-context gate 仍未关闭：

- v140 combined boost selector 共 `44` 个 row，全部来自 train split；
- validation failure rows `813/815/848/849/998/1001` 没有进入 boost selector；
- validation accepted ROI 从 v139 的 `17.519526` 提高到 `19.665638`；
- ROI CI-low 从 `8.779186` 提高到 `10.619181`；
- focused admission / delay-risk pass 从 `75/78` 提高到 `76/78`；
- focused raw / strict 仍为 `75/78`，checkpoint gate 仍失败；
- `stage4_candidate_ready=false`，不应运行或绑定 Stage 4 kNN/OOD safe source。

因此 v140 说明 train-only analog boost 仍有局部收益，但已经不是“单纯补相似训练对就能关门”的问题。剩余失败包含 raw-only 近似反排、greedy mixed-margin 失败，以及 random-wave shared-signature confounder；下一步应修 context/action-consequence 表示或 targeted comparator，而不是盲目继续加 loss multiplier。

## 复读边界

本轮重新对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 训练报告
- Stage 3 训练硬门槛报告
- Stage 4 v53 execution synthesis
- v139 train-only failure analog boost 综合结论

主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；
不能作为 pricing oracle，不能产生 official lower bound，不能生成 certificate，不能永久
丢弃 true-RC negative。最终 proof 仍必须由当前 branch/cut/dual 下的 exact pricing
对完整配置宇宙做 no-negative closure。

## 本轮 Artifact

Train-only analog 审计：

```text
summary =
  BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/summary.json

selector =
  BPC_future/results/gat_batch_impact_v140_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v140_train_only_failure_analog_audit_zh.md
```

训练：

```text
metrics =
  BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/metrics.json

checkpoint =
  BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/model.pt

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v140_trainonly_failure_analog_boost_seed13_zh.md
```

Focused pair failure audit：

```text
summary =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v140_trainonly_failure_analog_boost_20260623/summary.json

rows =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v140_trainonly_failure_analog_boost_20260623/focused_pair_failure_rows.jsonl

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v140_trainonly_failure_analog_boost_pair_failure_audit_zh.md
```

## Leakage Guard

v140 analog mining 结果：

```text
failed_pair_count = 3
failure_split_counts = {'validation_gate_only': 3}
train_pair_universe_count = 63
analog_pair_count = 24
analog_row_index_count = 29
existing_boost_row_index_count = 37
new_analog_row_index_count = 7
combined_boost_row_index_count = 44
excluded_validation_row_indices = [813, 815, 848, 849, 998, 1001]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
all_checks_pass = true
```

含义：

- v139 剩余 validation failures 只用于查询相似 train-only analog；
- v140 boost selector 没有把 validation gate rows 直接喂回训练；
- row index 语义仍是 `batch_impact_source_row_index`；
- 这只允许后续诊断训练，不能作为 Stage 4 准入理由。

## v139 / v140 对比

| version | best epoch | best loss epoch | accepted | ROI | ROI CI-low | false delay | safe CI-low | HP precision | HP CI-low | raw | admission | delay | strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v139 train-only analog boost | 4 | 4 | 37 | 17.519526 | 8.779186 | 0.007220 | 0.905939 | 0.996460 | 0.987186 | 75/78 | 75/78 | 75/78 | 75/78 |
| v140 cumulative train-only analog boost | 5 | 3 | 35 | 19.665638 | 10.619181 | 0.007220 | 0.901096 | 0.996473 | 0.987231 | 75/78 | 76/78 | 76/78 | 75/78 |

解释：

- v140 的 ROI point estimate 和 CI-low 更好；
- accepted count 从 `37` 降到 `35`，但仍满足 local useful coverage；
- false-delay 与 v139 相同，仍低于 `1%` gate；
- focused admission / delay-risk 各修复 1 个 pair；
- raw / strict 没改善，说明最终 focused gate 仍被 candidate raw ranking 卡住。

## 剩余 Focused Failures

| context | family | task | pair | ROI | diagnosis | raw margin | admission margin | delay-risk margin | 说明 |
|---|---|---:|---|---:|---|---:|---:|---:|---|
| `b36178f6655c5f75` | greedy-anchor | 20 | `813>815` | 1.320944 | mixed_margin_failure | -0.010699 | 0.006940 | 0.014305 | admission/delay 已翻正，但 raw 仍反排，strict 失败。 |
| `84ae11479ed592d4` | greedy-anchor | 20 | `998>1001` | 1.464020 | mixed_margin_failure | -0.034815 | -0.018148 | -0.005573 | 三个头仍反排，是稳定结构性失败。 |
| `9f80ae35ea87da5b` | random-wave | 30 | `183>845` | 1.105978 | shared_signature_confounder | -0.037907 | -0.019208 | -0.014735 | 新暴露的 shared-signature confounder；v139 的 `849>848` 已修复。 |

对比 v139：

```text
v139 failures = 813>815, 998>1001, 849>848
v140 failures = 813>815, 998>1001, 183>845
```

也就是说，v140 修复了 `be33 / 849>848`，但引入或暴露 `9f80 / 183>845`。
这说明 cumulative analog boost 不是单调收敛；它会在相邻 random-wave task30
结构上移动错误边界。

## 判断

v140 不能进入 Stage 4，理由是：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons =
  [
    admission_pair_pass_rate_below_threshold,
    delay_risk_pair_pass_rate_below_threshold,
    knn_ood_audit_missing,
    raw_pair_pass_rate_below_threshold,
    strict_pair_pass_rate_below_threshold
  ]
```

其中 `knn_ood_audit_missing` 是外部 blocker，但当前不应先补 kNN/OOD，因为 focused gate
本身仍失败。按计划合同，任一前置 gate 失败时不能用更好的 ROI、更低 loss 或 kNN/OOD
包装成 Stage 4 candidate。

## 下一步

建议下一步不要继续盲目 sweep multiplier，而是做 v141 结构/特征诊断：

1. 对 `b361 / 813>815` 做 raw-head targeted repair：admission 和 delay-risk 已正，说明 raw candidate head 缺少区分弱正 ROI 与 hard-negative 的 action consequence 特征。
2. 对 `84ae / 998>1001` 保留为 greedy structural hard pair，优先查 candidate path tokens、signature、batch features 与 context features 的可分性。
3. 对 `9f80 / 183>845` 做 shared-signature confounder audit，重点检查 positive/negative 是否在 signature/path token 上过度重叠，以及当前 primary candidate selection 是否拿错代表候选。
4. 若继续训练，优先增加显式 comparator / action-consequence feature，或只对这 3 个 failure family/context 生成 train-only analog，不再扩大全局 boost。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
production_ready = false
default_enabled = false
stage3_completed = false
stage4_candidate_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT 仍只能帮助排序和有限延迟 admission scheduling；所有进入 RMP 的列必须 true-RC
verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing full closure。
