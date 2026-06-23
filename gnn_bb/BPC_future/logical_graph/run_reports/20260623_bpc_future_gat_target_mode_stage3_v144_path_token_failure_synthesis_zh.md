# 2026-06-23 BPC_future GAT Stage 3 v144 Path-token Failure 综合报告

## 结论

v140 剩余 focused gate 失败不应再描述为“缺少 path token / selected arc-option
sequence”。当前 v140 checkpoint 已经启用 `PathTokenEncoder`，v119 数据样本也包含
`candidate_path_token_ids / candidate_path_pair_ids / candidate_path_type_ids /
candidate_path_token_mask`。

新的问题是：path-token 分支在当前 checkpoint 上对剩余 3 个 focused pair 起了负作用。
v142 直接消融 path token 后：

- `813>815` 从 raw 反排变成三头全通过；
- `998>1001` 从三头反排变成三头全通过；
- `183>845` 的 admission / delay-risk 变成通过，但 raw 仍差 `0.033397`。

因此下一步不能盲目增强 path-token 权重，也不能简单“再添加 path 序列特征”。更合理的
方向是做 path 分支的标签冲突审计、正则化或默认关闭 ablation retrain。

## Artifact

```text
v142_path_token_attribution_summary =
  BPC_future/results/gat_batch_impact_path_token_failure_attribution_v142_v140_remaining_20260623/summary.json

v142_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v142_v140_remaining_path_token_failure_attribution_zh.md

v143_path_neighbor_summary =
  BPC_future/results/gat_batch_impact_path_token_label_neighbors_v143_v140_remaining_20260623/summary.json

v143_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v143_v140_remaining_path_token_label_neighbors_zh.md
```

## v142 Path-token 消融结果

| pair | normal raw | normal adm | normal delay | ablated raw | ablated adm | ablated delay | diagnosis |
|---|---:|---:|---:|---:|---:|---:|---|
| `813>815` | -0.010699 | 0.006940 | 0.014306 | 0.491184 | 0.175011 | 0.357920 | path_token_branch_hurts_this_pair |
| `998>1001` | -0.034815 | -0.018148 | -0.005573 | 0.184714 | 0.046850 | 0.164906 | path_token_branch_hurts_this_pair |
| `183>845` | -0.037907 | -0.019208 | -0.014735 | -0.033397 | 0.003093 | 0.017155 | path_token_branch_moves_margin_wrong_direction |

机器字段：

```text
path_token_encoder_enabled = true
path_ablation_repairs_failure_count = 2
path_signal_helped_pair_count = 0
path_signal_hurt_pair_count = 3
low_selected_raw_path_overlap_pair_count = 3
primary = path_token_branch_hurts_this_pair
recommended_next_step = audit_path_token_collision_or_label_alignment_before_more_training
stage4_candidate_ready = false
```

## v143 Path-token 邻域标签结果

v143 扫描了当前离线 dataset 的 `12684` 个候选 path-token 记录。结论不是“正样本缺少
train 支撑”：3 个 positive query 的 train 邻域都偏 safe。问题集中在 3 个 negative
query：它们的相似 train 邻域都有 safe-label 冲突。

| pair | pair diagnosis | positive top20 safe/delay | negative top20 safe/delay | positive maxJ | negative maxJ |
|---|---|---:|---:|---:|---:|
| `813>815` | negative_path_tokens_have_train_safe_conflict | 0.800 / 0.200 | 0.650 / 0.350 | 0.222 | 0.222 |
| `998>1001` | negative_path_tokens_have_train_safe_conflict | 0.700 / 0.300 | 1.000 / 0.000 | 0.286 | 0.500 |
| `183>845` | negative_path_tokens_have_train_safe_conflict | 1.000 / 0.000 | 0.850 / 0.150 | 0.222 | 0.286 |

Top-5 sanity check：

- `998>1001` 的 negative query 最强，top5 train 全 safe，max token Jaccard `0.5`；
- `813>815` 和 `183>845` 的 negative query 也偏 safe，但最大 Jaccard 只有
  `0.222` / `0.286`，属于中低相似邻域，不能把 path-neighborhood 当 safe source；
- 所有 pair 的 same-signature cross-role neighbor count 为 `0`，当前证据更像 path
  fragment/context 条件冲突，不是完全相同 signature 泄漏。

## 判断

1. v141 的 recommended next step 需要收窄：
   - 不是“添加 selected arc-option sequence”；
   - 而是“审计并修复已有 path-token 分支在 context-local ranking 上的误导”。
2. v142/v143 都支持先做 diagnostic ablation，而不是继续全局 boost：
   - path token 消融能修复 2/3 个剩余 focused failures；
   - negative path 的 train 邻域存在 safe-label 冲突；
   - 继续增大 path-aware loss 或盲目加 path 权重有较高风险。
3. 下一步最小安全实验：
   - 给 `train_gat_batch_impact.py` 增加默认关闭的 `--disable-path-token-encoder`
     诊断开关；
   - 用同一 v140 数据和 focused selector 训练一个 no-path-token ablation checkpoint；
   - 只比较 Stage 3 metrics 和 focused gate，不进入 Stage 4；
   - 若 no-path 关闭 focused gate，再考虑 path dropout / path branch regularization；
   - 若 no-path 牺牲全局 ROI/precision，则改做 context-conditioned path comparator，
     不直接删除 path token。

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

GAT/path-token/kNN/OOD 仍只能影响 offline ranking 或有限延迟 admission scheduling；
最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
no-negative closure。
