# 2026-06-23 BPC_future GAT Stage 3 v139 Train-only Failure Analog Boost 综合报告

## 结论

v139 是一次 Stage 3 诊断性训练推进，不是 Stage 4 candidate。

本轮先对 v138 focused pair failures 做 train-only analog mining，再用
`v134 existing boost ∪ v139 analog rows` 作为 focused-pair boost selector
重训。结果显示：

- v138 的 `b361 812>815`、`ddcb 779>398`、`7cb 810>808` 被修复；
- focused strict pass 从 `74/78` 提升到 `75/78`；
- 但仍有 `3/78` focused pair failure；
- checkpoint gate 仍失败，`stage4_candidate_ready=false`。

因此 v139 证明 train-only analog boost 有方向性收益，但还不能进入 Stage 4
shadow / opt-in，也不能绑定 kNN/OOD 安全壳来包装成候选。

## 复读边界

本轮重新对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 训练和训练硬门槛报告
- Stage 4 v53 execution synthesis
- v138 action-priority residual 综合结论

主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT 只能做 discovery / ordering / finite-delay admission scheduling；不能作为
pricing oracle，不能产生 official lower bound，不能生成 certificate，不能永久
丢弃 true-RC negative。最终 proof 仍必须由 exact pricing 在当前 branch/cut/dual
下对完整配置宇宙做 no-negative closure。

## 本轮新增 Artifact

Train-only analog 审计：

```text
summary =
  BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/summary.json

selector =
  BPC_future/results/gat_batch_impact_v139_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v139_train_only_failure_analog_audit_zh.md
```

训练：

```text
metrics =
  BPC_future/results/gat_batch_impact_training_v139_trainonly_failure_analog_boost_seed13_20260623/metrics.json

checkpoint =
  BPC_future/results/gat_batch_impact_training_v139_trainonly_failure_analog_boost_seed13_20260623/model.pt

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v139_trainonly_failure_analog_boost_seed13_zh.md
```

Focused pair failure audit：

```text
summary =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v139_trainonly_failure_analog_boost_20260623/summary.json

rows =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v139_trainonly_failure_analog_boost_20260623/focused_pair_failure_rows.jsonl

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v139_trainonly_failure_analog_boost_pair_failure_audit_zh.md
```

## Leakage Guard

Train-only analog mining 结果：

```text
failed_pair_count = 4
failure_split_counts = {'train_visible': 2, 'validation_gate_only': 2}
train_pair_universe_count = 63
analog_pair_count = 32
analog_row_index_count = 32
existing_boost_row_index_count = 9
combined_boost_row_index_count = 37
new_analog_row_index_count = 28
excluded_validation_row_indices = [812, 813, 815]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
all_checks_pass = true
```

含义：

- `b361` 的 validation focused rows `812/813/815` 没有进入训练 selector；
- 这些 rows 只用于查询 train split 内相似 action/feature delta；
- v139 boost selector 保留 v134 的 train-only boost，并加入 analog rows；
- row index 语义仍是 `batch_impact_source_row_index`。

## v138 / v139 对比

| version | best epoch | accepted | ROI | ROI CI-low | false delay | safe CI-low | HP precision | HP CI-low | raw | admission | delay | strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v138 action-priority residual | 2 | 35 | 19.596107 | 10.534233 | 0.003610 | 0.901096 | 0.999077 | 0.994788 | 75/78 | 74/78 | 74/78 | 74/78 |
| v139 train-only analog boost | 4 | 37 | 17.519526 | 8.779186 | 0.007220 | 0.905939 | 0.996460 | 0.987186 | 75/78 | 75/78 | 75/78 | 75/78 |

解释：

- v139 修复了一个 focused strict failure，且 accepted count 从 35 到 37；
- safe precision CI-low 略升；
- ROI / ROI CI-low、HP precision / HP CI-low、false-delay 都比 v138 稍差；
- 这说明 analog boost 有用，但仍在 safety / ROI / focused ordering 之间拉扯。

## 剩余 Focused Failures

| context | family | task | positive | negative | positive ROI | raw margin | admission margin | delay-risk margin | diagnosis |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| b36178f6655c5f75 | greedy-anchor | 20 | 813 | 815 | 1.320944 | -0.008139 | -0.005949 | -0.003045 | near_margin_loss_tuning_candidate |
| 84ae11479ed592d4 | greedy-anchor | 20 | 998 | 1001 | 1.464020 | -0.026710 | -0.021564 | -0.012455 | mixed_margin_failure |
| be33b2560df0147a | random-wave | 30 | 849 | 848 | 11.920404 | -0.029570 | -0.043314 | -0.031283 | mixed_margin_failure |

重要变化：

- `ddcb 779>398` 从 v138 failure 变为 pass；
- `7cb 810>808` 从 v138 failure 变为 pass；
- `b361 812>815` 从 v138 failure 变为 pass；
- `b361 813>815` 仍失败，但已经变成 near-margin；
- 新暴露的 `84ae` 和 `be33` 是 mixed-margin，不能靠把当前 validation row 直接塞回训练解决。

## 判断

v139 的结论是：

```text
train-only analog boost improves focused ordering,
but does not close the strict focused gate.
```

当前不应进入 Stage 4：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
```

主要 blockers：

```text
raw_pair_pass_rate_below_threshold
admission_pair_pass_rate_below_threshold
delay_risk_pair_pass_rate_below_threshold
strict_pair_pass_rate_below_threshold
knn_ood_audit_missing
knn_ood_holdout_audit_not_run
online_shadow_and_opt_in_ab_not_run
```

其中 kNN/OOD 不是当前首要动作，因为 focused gate 已经失败。kNN/OOD 只能在
focused gate 先闭合之后作为安全壳验收，不能弥补 focused ranking failure。

## 下一步

下一步不要盲目继续 multiplier sweep。更合理的 Stage 3 方向：

1. 对 `b361 813>815` 做小步 near-margin tuning，但必须保持 validation row 不进训练。
2. 对 `84ae 998>1001` 和 `be33 849>848` 做 train-only analog mining 或 action-consequence feature audit。
3. 优先审计当前模型可见 feature 是否表达了：
   - path-token / arc-option consequence；
   - slack / risk / idle-time interaction；
   - batch-vs-context action contrast；
   - risk-adjusted admission score 与 raw action priority 的抵消。
4. 只有 focused gate 达到 `78/78` 后，才运行 checkpoint-bound kNN/OOD safety shell。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

本轮没有修改 RMP、pricing、branching、cuts、final judge、certificate path 或 benchmark
默认配置。最终 optimality proof 仍只能来自 exact pricing full closure。
