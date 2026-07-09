# B4.1 True-Dual Proof-Tail Strengthening 报告

## Boundary

- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。
- makespan 只作为 metric，不进入 pricing objective。
- B4.1 diagnostic frontier 不自动升级 certificate。
- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_pair_tw_mainline_smoke/b4_1_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_pair_tw_mainline_smoke/b4_1_summary.json`

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
| tail_dual_certificate_leak_count | 0 | 0 |

## Requirement Audit

| id | status | evidence | next action |
| --- | --- | --- | --- |
| R1_redlines_zero | pass | {"redline_count":8,"redline_failures":{}} |  |
| R2_stage_a_regression_clean | missing | {"missing_modes":["stageA_B3B_accepted_baseline"],"observed_modes":["stageA_B4V2_default_final_judge_harvesting"],"stage_a_regression_clean":false,"stage_a_row_count":1} | Run/import Stage A 5/10/20 regression rows and keep redlines at zero. |
| R3_stage_b_matrix_complete | missing | {"missing":["B4V2_baseline","B4V2_harvesting","B4V2_hidden_negative_audit","B4V2_frontier_ledger_diagnostic","B4V2_harvesting_frontier_ledger_diagnostic","B4V4_combined_formulation_diagnostic"],"observed":[],"stage_b_row_count":0} | Import or run evidence for every missing Stage B matrix cell. |
| R4_stage_c_selected_diagnostic | missing | {"stage_c_diagnostic_clean":false,"stage_c_row_count":0,"stage_c_selected_row_count":0} | Run/import the selected 30-scale Stage C diagnostic rows. |
| R5_stage_bc_diagnostic_only | pass | {"frontier_lb_official_row_count":0,"stage_bc_certificate_claim_count":0,"stage_bc_row_count":0} |  |
| R6_tail_dual_worker_only | pass | {"tail_dual_certificate_leak_count":0,"tail_dual_enabled_count":0,"tail_dual_no_column_can_certify_count":0,"tail_dual_official_true_dual_source_count":0,"tail_dual_true_dual_recomputed_count":0,"tail_dual_worker_only_count":0} |  |
| R7_30_scale_exact_closure | incomplete | {"known_boundary":"30-scale remains DIAGNOSTIC_PRICING_FRONTIER until true-dual no-negative proof closes.","thirty_scale_bpc_tree_optimal_count":0} | Continue proof-tail strengthening until a 30-scale true-dual no-negative proof supports BPC_TREE_OPTIMAL. |

## Summary

| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | stageA_B4V2_default_final_judge_harvesting |  | 1 | 1 | 0 | 0 | 0 | None | 0.188321 |

## Stage B/C Telemetry

| stage | mode | variant | active cols | active after merge | best neg RC | last best RC | final judge wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | stageA_B4V2_default_final_judge_harvesting |  | None | None | None | None | 0.188321 |

## Acceptance State

- Stage A regression clean: `False`。
- Stage B diagnostic clean: `False`。
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
- Hidden-negative miss reasons: `none`。
- Hidden-negative top miss reason: `none`。
- Tail-dual worker rows: `0`；worker-only `0`；true-dual RC recomputed `0`；tail no-column certifies `0`。
- Stage A observed regression modes: `stageA_B4V2_default_final_judge_harvesting`。
- Stage A missing regression modes: `stageA_B3B_accepted_baseline`。
- Stage B observed matrix cells: `none`。
- Stage B missing matrix cells: `B4V2_baseline, B4V2_harvesting, B4V2_hidden_negative_audit, B4V2_frontier_ledger_diagnostic, B4V2_harvesting_frontier_ledger_diagnostic, B4V4_combined_formulation_diagnostic`。
