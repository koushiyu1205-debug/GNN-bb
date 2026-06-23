# 2026-06-17 BPC_future GAT Stage 3 v98 Focused Pair Failure Anatomy 报告

## 目的

对 v96 explicit focused tranche 的 same-context pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
 表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 0
failed_pair_count = 0
strict_pair_pass_rate = None
raw_fail_rate = None
admission_fail_rate = None
delay_risk_fail_rate = None
all_failed_heads_near_rate_among_failed = None
any_failed_head_deep_rate_among_failed = None
signature_overlap_pair_rate = None
path_token_jaccard_median = None
primary = none
recommended_next_step = focused_pair_gate_passed_move_to_global_stage3_gate
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`0`，失败：`0`。
- near-margin 失败占失败 pair：`None`。
- deep 失败占失败 pair：`None`。
- signature overlap pair rate：`None`。
- 主要诊断：`none`。

## Recommended Next Step

```json
{
  "primary": "focused_pair_gate_passed_move_to_global_stage3_gate",
  "reason": "no focused pair ordering failures were found"
}
```

## Margin Stats

```json
{
  "admission_margin_stats": {
    "count": 0,
    "max": null,
    "mean": null,
    "median": null,
    "min": null
  },
  "delay_risk_margin_stats": {
    "count": 0,
    "max": null,
    "mean": null,
    "median": null,
    "min": null
  },
  "diagnosis_counts": {},
  "raw_margin_stats": {
    "count": 0,
    "max": null,
    "mean": null,
    "median": null,
    "min": null
  }
}
```

## Top Contexts

```json
[]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v110_v109_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v110_v109_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v110_v109_5000_20260622/focused_pair_failure_contexts.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `runs_rmp=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
