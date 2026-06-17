# 2026-06-17 BPC_future GAT Stage 3 v95 Focused Tranche Mining 报告

## 目的

从 batch-impact dataset manifest 中挖掘同一 context 的 high-ROI positive vs delay / hard-negative focused regression tranche。该审计不加载模型，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_tranche_mining = current
status = gat_batch_impact_focused_tranche_mined
sample_count = 392
context_count = 296
trainable_context_count = 11
focused_row_count = 82
focused_pair_count = 145
focused_family_counts = {'random-wave': 24, 'sector-wave': 58}
focused_task_count_counts = {'20': 80, '50': 2}
recommended_selector = explicit_row_indices
row_index_min_selector = {'row_index_min': 10, 'selected_count': 382, 'focused_count': 82, 'extra_nonfocused_count': 300, 'extra_nonfocused_rate': 0.7853403141361257}
stage3_focused_tranche_ready = true
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- 可训练同 context positive/negative context 数：`11`。
- 可形成 focused pair：`145`。
- focused rows 覆盖 family：`{'random-wave': 24, 'sector-wave': 58}`。
- negative-only contexts：`66`，这些只能提供 delay / hard-negative 监督，不能单独训练 positive > negative ranking。
- 当前 `row_index_min` selector 会额外带入 `300` 个非 focused row；后续 trainer 应支持 explicit row-index selector。

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/summary.json
focused_rows = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_rows.jsonl
focused_pairs = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_pairs.jsonl
focused_row_indices = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
