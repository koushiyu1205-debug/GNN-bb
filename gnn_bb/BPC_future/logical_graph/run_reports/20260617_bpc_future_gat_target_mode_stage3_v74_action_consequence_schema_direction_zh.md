# 2026-06-17 BPC_future GAT Stage 3 v74 Action-consequence Schema Direction 综合报告

## 结论

v72 已经确认当前 blocker 是同一 RMP context 内 positive target 和 tail-delay hard-negative 的 action-consequence 排序失败；v73 进一步回答了下一步特征是否可从现有数据恢复。

结论是：`arc-option token sequence`、`time-window slack`、`resource/survival slack`、`occupancy payload` 和 `active/pool overlap proxy` 在 v66 全量 dataset 与 v71 focused 反例中都可恢复。下一步可以进入 schema/model 改造，不需要先重新采集这些 payload。

但 `per-candidate cut interaction` 当前不可用：v73 全量和 focused 都是 `cut_payload_coverage = 0.0`、`candidate_cut_coefficients_count = 0`。它应作为后续 capture 增强项，而不是阻塞 arc-token/slack 模型结构改造。

## v73 全量审计

```text
summary = BPC_future/results/gat_batch_impact_action_consequence_feature_availability_v73_v66_20260617/summary.json
report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v73_action_consequence_feature_availability_zh.md
audited_sample_count = 392
audited_candidate_count = 4703
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 120}
task_count_counts = {'5': 2, '10': 8, '20': 209, '30': 76, '50': 96, '100': 1}
arc_token_sequence_coverage = 1.0
parseable_arc_token_coverage = 1.0
time_window_slack_coverage = 1.0
resource_slack_coverage = 1.0
occupancy_payload_coverage = 1.0
pool_overlap_proxy_coverage = 1.0
active_basis_direct_payload_coverage = 1.0
branch_payload_coverage = 1.0
cut_payload_coverage = 0.0
unique_arc_option_token_count = 2307
unique_arc_option_pair_count = 1234
unique_arc_option_type_values = ['low_energy', 'low_risk', 'low_time']
primary = per_candidate_cut_interaction_payload_missing
recommended_next_step = add_arc_token_sequence_and_slack_features_then_retrain
```

## v73 Focused 反例审计

```text
summary = BPC_future/results/gat_batch_impact_action_consequence_feature_availability_v73_focus_v66_20260617/summary.json
report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v73_focused_action_consequence_feature_availability_zh.md
focus_row_index_min = 383
audited_sample_count = 9
audited_candidate_count = 9
arc_token_sequence_coverage = 1.0
parseable_arc_token_coverage = 1.0
time_window_slack_coverage = 1.0
resource_slack_coverage = 1.0
pool_overlap_proxy_coverage = 1.0
cut_payload_coverage = 0.0
unique_arc_option_token_count = 37
unique_arc_option_pair_count = 34
primary = per_candidate_cut_interaction_payload_missing
```

这说明 v71 的 focused ranking failure 不是因为反例缺少路径序列或 slack payload。当前模型没用这些信息，是 schema/model 表示不足。

## 对 v72 的更新

v72 的下一步候选有四类：

1. selected arc-option token sequence / path option embedding；
2. task time-window slack、resource slack、survival-energy slack；
3. active basis / dual movement overlap；
4. per-candidate branch/cut coefficient interaction。

v73 后的优先级应调整为：

1. 立即推进 arc-option token sequence encoder；
2. 同时把 task-level slack / survival slack 作为 candidate scalar 或 token-side attributes 接入；
3. active/pool overlap 先用现有 payload 做 proxy；
4. cut interaction 暂不进入模型必需输入，先补 capture/cut coefficient payload 后再接入。

## 建议实现方向

下一步不是再训练 v67，也不是继续扫 threshold。应先做 Stage 1/3 的 schema/model 改造：

- dataset schema 新增 per-candidate `arc_option_token_ids` / `arc_option_pair_ids` / `arc_option_type_ids`；
- 模型新增 candidate path-token encoder，对每个 journey 的 ordered arc-option sequence 做 embedding / attention / pooling；
- task slack 先作为 candidate scalar 扩展：`min_late_slack`、`min_early_slack`、`min_survival_energy`、`occupancy_bucket_count`；
- focused pair gate 作为 checkpoint selection hard gate 保留；
- 重建 v75 dataset 后训练 v76，并重新跑 v71/v73/v69 类型审计。

## Exactness Boundary

本轮只做离线数据可用性审计：

```text
runs_bpc_or_pricing = false
production_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
stage4_candidate_ready = false
```

即使后续 token/slack 模型改善排序，它仍只能做 discovery / ordering / finite-delay admission scheduling。进入 RMP 的列必须 true-RC verified；最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。

## Verification

```text
py_compile audit_gat_batch_impact_action_consequence_feature_availability.py = pass
py_compile audit_gat_batch_impact_individual_context_ranking.py = pass
unittest BPC_future.tests.test_gat_batch_impact_action_consequence_feature_availability = 2 tests OK
unittest BPC_future.tests.test_gat_batch_impact_individual_context_ranking = 5 tests OK
v73 focused availability audit = pass
v73 full v66 availability audit = pass
```

