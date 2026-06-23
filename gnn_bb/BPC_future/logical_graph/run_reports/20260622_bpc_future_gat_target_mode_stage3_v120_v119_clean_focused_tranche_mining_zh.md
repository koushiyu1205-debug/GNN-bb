# 2026-06-17 BPC_future GAT Stage 3 v95 Focused Tranche Mining 报告

## 目的

从 batch-impact dataset manifest 中挖掘同一 context 的 high-ROI positive vs delay / hard-negative focused regression tranche。该审计不加载模型，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_tranche_mining = current
status = gat_batch_impact_focused_tranche_mined
sample_count = 1117
context_count = 546
trainable_context_count = 30
focused_row_count = 102
focused_pair_count = 78
focused_family_counts = {'greedy-anchor': 33, 'random-wave': 47, 'sector-wave': 22}
focused_task_count_counts = {'20': 83, '30': 17, '50': 2}
recommended_selector = explicit_row_indices
row_index_min_selector = {'row_index_min': 106, 'selected_count': 1017, 'focused_count': 102, 'extra_nonfocused_count': 915, 'extra_nonfocused_rate': 0.8997050147492626}
stage3_focused_tranche_ready = true
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- 可训练同 context positive/negative context 数：`30`。
- 可形成 focused pair：`78`。
- focused rows 覆盖 family：`{'greedy-anchor': 33, 'random-wave': 47, 'sector-wave': 22}`。
- negative-only contexts：`150`，这些只能提供 delay / hard-negative 监督，不能单独训练 positive > negative ranking。
- 当前 `row_index_min` selector 会额外带入 `915` 个非 focused row；后续 trainer 应支持 explicit row-index selector。

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/summary.json
focused_rows = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_rows.jsonl
focused_pairs = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_pairs.jsonl
focused_row_indices = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
