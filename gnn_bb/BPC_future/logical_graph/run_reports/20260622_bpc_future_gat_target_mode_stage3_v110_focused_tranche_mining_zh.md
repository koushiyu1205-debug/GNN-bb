# 2026-06-17 BPC_future GAT Stage 3 v95 Focused Tranche Mining 报告

## 目的

从 batch-impact dataset manifest 中挖掘同一 context 的 high-ROI positive vs delay / hard-negative focused regression tranche。该审计不加载模型，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_tranche_mining = current
status = gat_batch_impact_focused_tranche_mined
sample_count = 1221
context_count = 547
trainable_context_count = 37
focused_row_count = 207
focused_pair_count = 384
focused_family_counts = {'greedy-anchor': 33, 'random-wave': 75, 'sector-wave': 99}
focused_task_count_counts = {'20': 188, '30': 17, '50': 2}
recommended_selector = explicit_row_indices
row_index_min_selector = {'row_index_min': 10, 'selected_count': 1211, 'focused_count': 207, 'extra_nonfocused_count': 1004, 'extra_nonfocused_rate': 0.8290668868703551}
stage3_focused_tranche_ready = true
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- 可训练同 context positive/negative context 数：`37`。
- 可形成 focused pair：`384`。
- focused rows 覆盖 family：`{'greedy-anchor': 33, 'random-wave': 75, 'sector-wave': 99}`。
- negative-only contexts：`148`，这些只能提供 delay / hard-negative 监督，不能单独训练 positive > negative ranking。
- 当前 `row_index_min` selector 会额外带入 `1004` 个非 focused row；后续 trainer 应支持 explicit row-index selector。

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/summary.json
focused_rows = BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_rows.jsonl
focused_pairs = BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_pairs.jsonl
focused_row_indices = BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_row_indices.json
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
