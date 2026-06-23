# 2026-06-23 BPC_future GAT Stage 3 v142 Path-token 失败归因审计

日期：2026-06-23

## 结论

本轮只审计 v140 剩余 focused pair failures 的 path-token 输入和消融影响，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/model.pt
metrics = BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/metrics.json
failed_pair_count = 3
path_token_encoder_enabled = true
path_ablation_repairs_failure_count = 2
path_signal_helped_pair_count = 0
path_signal_hurt_pair_count = 3
low_selected_raw_path_overlap_pair_count = 3
primary = path_token_branch_hurts_this_pair
recommended_next_step = audit_path_token_collision_or_label_alignment_before_more_training
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
```

## 解释

v141 的 feature-structure 报告提示 `selected_arc_option_sequence` 欠指定。
本轮核对当前模型后，需要把这个结论收窄：v140 checkpoint 实际启用了
`PathTokenEncoder`，数据样本也包含 `candidate_path_token_ids / pair_ids / type_ids / mask`。
因此问题不是“完全没有 path token”，而是 path-token 分支是否足以改变
context-local positive-vs-hard-negative 排序。

## 剩余失败 Pair

| context | family | pair | raw | adm | delay | ablated raw | ablated adm | ablated delay | raw path J | diagnosis |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| b36178f6655c5f75 | greedy-anchor | 813>815 | -0.010699 | 0.006940 | 0.014306 | 0.491184 | 0.175011 | 0.357920 | 0.167 | path_token_branch_hurts_this_pair |
| 84ae11479ed592d4 | greedy-anchor | 998>1001 | -0.034815 | -0.018148 | -0.005573 | 0.184714 | 0.046850 | 0.164906 | 0.000 | path_token_branch_hurts_this_pair |
| 9f80ae35ea87da5b | random-wave | 183>845 | -0.037907 | -0.019208 | -0.014735 | -0.033397 | 0.003093 | 0.017155 | 0.000 | path_token_branch_moves_margin_wrong_direction |

## 判断

- path token 已进入模型输入，不能再把下一步简单描述为“添加 path token”；
- 如果 path 消融后失败仍在，说明当前 head/comparator 对已有 path-token 信号利用不足；
- 如果某个 pair 消融后反而修复，说明 path-token 分支可能在该局部给出误导信号，需要查 token collision 或 label 对齐；
- 无论哪一种，本轮都不满足 focused gate，不能进入 Stage 4。

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

最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_path_token_failure_attribution_v142_v140_remaining_20260623/summary.json
pairs = BPC_future/results/gat_batch_impact_path_token_failure_attribution_v142_v140_remaining_20260623/path_token_failure_pair_rows.jsonl
rows = BPC_future/results/gat_batch_impact_path_token_failure_attribution_v142_v140_remaining_20260623/path_token_failure_row_rows.jsonl
```
