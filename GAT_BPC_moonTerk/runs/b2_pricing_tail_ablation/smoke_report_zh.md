# B2 Pricing-Tail Optimization 消融报告

## Completed Scope

- 当前只评估 B2 root pricing-tail；不进入 B3 branch tree、B4 cuts/formulation、B5 GAT guidance。
- B2B_seeded_tail_CG 是主模式；B2A_full_universe_rc_audit_fast_path 只作为显式 full-universe audit fast path。
- completion-bound pruning 默认关闭；只保留 audit / ordering / profiling 语义。

## Artifacts

- CSV rows: `runs/b2_pricing_tail_ablation/smoke_rows.csv`
- JSON summary: `runs/b2_pricing_tail_ablation/smoke_summary.json`

## Baseline Comparison Matrix

- 5-scale full: 0 instances。
- 10-scale: 0/0 instances。
- 20-scale fail-closed guard: 0 instances。
- 20-scale selected direct20 probe: 0 instances。
- 20-scale selected direct20 probe modes: 。
- 30-scale fail-closed diagnostic: 0 instances。

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| root_bound_gt_B0_violation_count | 0 | 0 |
| direct_root_official_leak_count | 0 | 0 |
| manual_rc_fail_count | 0 | 0 |
| pricing_rc_fail_count | 0 | 0 |
| certificate_scope_regression_count | 0 | 0 |
| objective_mismatch_count | 0 | 0 |
| b1_5scale_regression_count | 0 | 0 |

## Summary

| scale | group | candidate | runs | BPC node LP | fail-closed | timeout | mean wall | p90 wall | mean added | mean rounds | mean final judge | candidate negatives | addable negatives | duplicate-only | hidden-negative |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 |  | B0_pure_direct_dp | 1 | 0 | 0 | 0 | 0.003537 | 0.003537 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 |  | B1A_full_universe_root_audit | 1 | 1 | 0 | 0 | 0.032815 | 0.032815 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| 5 |  | B1B_seeded_root_CG | 1 | 1 | 0 | 0 | 0.058565 | 0.058565 | 17 | 3 | 3 | 0 | 0 | 0 | 0 |
| 5 |  | B2A_full_universe_rc_audit_fast_path | 1 | 1 | 0 | 0 | 0.007635 | 0.007635 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| 5 |  | B2B_seeded_tail_CG | 1 | 1 | 0 | 0 | 0.060093 | 0.060093 | 17 | 3 | 3 | 40 | 40 | 0 | 0 |

## Addability Breakdown

- candidate_negative_count: 40。
- addable_negative_count: 40。
- duplicate_in_current_master_count: 0。
- in_pool_not_master_count: 0。
- forbidden_signature_count: 0。
- branch_filtered_count: 0。
- cut_filtered_count: 0。

## Duplicate-Only Audit Breakdown

- duplicate_only_count: 0。
- duplicate_only_audit_status_counts: {'': 5}。

## Hidden-Negative Audit

- hidden_negative_count: 0。

## B2 Accepted?

- B2 accepted: False。
- B2A fast path accepted as full-universe audit optimization: True。
- B2B seeded tail accepted as next baseline: False。
- improvement_count: 1。
- reason: B2 remains diagnostic until B2B shows a 10/20-scale improvement without redline violations.。

## B3 Entry

- 只有 `b2b_seeded_tail_accepted=true` 且 redlines 全为 0 时，才允许把 B2B 作为进入 B3 的 accepted baseline。
