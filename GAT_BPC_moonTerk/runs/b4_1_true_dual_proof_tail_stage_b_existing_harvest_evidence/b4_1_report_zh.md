# B4.1 True-Dual Proof-Tail Strengthening 报告

## Boundary

- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。
- makespan 只作为 metric，不进入 pricing objective。
- B4.1 diagnostic frontier 不自动升级 certificate。
- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。

## Artifacts

- CSV rows: `runs/b4_1_true_dual_proof_tail_stage_b_existing_harvest_evidence/b4_1_rows.csv`
- JSON summary: `runs/b4_1_true_dual_proof_tail_stage_b_existing_harvest_evidence/b4_1_summary.json`

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_leak_count | 0 | 0 |
| manual_rc_fail_count | 0 | 0 |
| pricing_rc_fail_count | 0 | 0 |
| diagnostic_claimed_certificate_count | 0 | 0 |
| resource_guard_stopped_count | 0 | 0 |
| exception_fail_closed_count | 0 | 0 |
| stage_a_tree_closure_miss_count | 0 | 0 |

## Summary

| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | B4.1_probe_final_judge_evidence | V2_latest_service_start_slot_bound | 1 | 0 | 0 | 0 | 1 | None | 59.762075 |

## Acceptance State

- Stage A regression clean: `False`。
- Stage B diagnostic clean: `True`。
- Stage B planned matrix complete: `False`。
- Stage C selected diagnostic clean: `False`。
- B4.1 code path exercised: `True`。
- Full long experiment complete: `False`。
- `b4_1_full_experiment_complete=False` 是刻意保守：需要另外完成 5/10/20 full regression 和 30-scale staged frontier/selected diagnostics。

## Proof-Tail Diagnostics

- Negative-discovery budget exhausted rows: `0`。
- Feasibility-proof budget exhausted rows: `0`。
- Missing optimization-proof rows: `0`。
- Positive incumbent RC but negative frontier bound rows: `0`。
- Stage B observed matrix cells: `B4V2_baseline, B4V2_frontier_ledger_diagnostic, B4V2_harvesting, B4V2_harvesting_frontier_ledger_diagnostic`。
- Stage B missing matrix cells: `B4V2_hidden_negative_audit, B4V4_combined_formulation_diagnostic`。
