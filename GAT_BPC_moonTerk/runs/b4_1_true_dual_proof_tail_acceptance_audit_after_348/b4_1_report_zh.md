# B4.1 True-Dual Proof-Tail Strengthening 报告

## Boundary

- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。
- makespan 只作为 metric，不进入 pricing objective。
- B4.1 diagnostic frontier 不自动升级 certificate。
- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_acceptance_audit_after_348/b4_1_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_acceptance_audit_after_348/b4_1_summary.json`

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
| R2_stage_a_regression_clean | pass | {"missing_modes":[],"observed_modes":["stageA_B3B_accepted_baseline","stageA_B4V2_default_final_judge_harvesting"],"stage_a_regression_clean":true,"stage_a_row_count":121} |  |
| R3_stage_b_matrix_complete | pass | {"missing":[],"observed":["B4V2_baseline","B4V2_frontier_ledger_diagnostic","B4V2_harvesting","B4V2_harvesting_frontier_ledger_diagnostic","B4V2_hidden_negative_audit","B4V4_combined_formulation_diagnostic"],"stage_b_row_count":12} |  |
| R4_stage_c_selected_diagnostic | pass | {"stage_c_diagnostic_clean":true,"stage_c_row_count":10,"stage_c_selected_row_count":10} |  |
| R5_stage_bc_diagnostic_only | pass | {"frontier_lb_official_row_count":0,"stage_bc_certificate_claim_count":0,"stage_bc_row_count":22} |  |
| R6_tail_dual_worker_only | pass | {"tail_dual_certificate_leak_count":0,"tail_dual_enabled_count":1,"tail_dual_no_column_can_certify_count":0,"tail_dual_official_true_dual_source_count":1,"tail_dual_true_dual_recomputed_count":1,"tail_dual_worker_only_count":1} |  |
| R7_30_scale_exact_closure | incomplete | {"known_boundary":"30-scale remains DIAGNOSTIC_PRICING_FRONTIER until true-dual no-negative proof closes.","thirty_scale_bpc_tree_optimal_count":0} | Continue proof-tail strengthening until a 30-scale true-dual no-negative proof supports BPC_TREE_OPTIMAL. |

## Summary

| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | stageA_B2B_R2_worker_tail_dual_on |  | 1 | 0 | 0 | 0 | 0 | None | 0.067854 |
| A | stageA_B3B_accepted_baseline |  | 60 | 60 | 0 | 0 | 0 | None | 12.381732 |
| A | stageA_B4V2_default_final_judge_harvesting |  | 60 | 60 | 0 | 0 | 0 | None | 12.444268 |
| B | B4.1_compact_pricing_formulation | V2_latest_service_start_slot_bound | 2 | 0 | 0 | 0 | 0 | -0.432157206 | 58.443408 |
| B | B4.1_compact_pricing_formulation | V4_combined_endpoint_pair_latest_start_time_window | 2 | 0 | 0 | 0 | 0 | -0.198360699 | 53.610464 |
| B | B4.1_probe_final_judge_evidence | V2_latest_service_start_slot_bound | 1 | 0 | 0 | 0 | 1 | None | 59.762075 |
| B | B4.1_probe_final_judge_evidence | V4_combined_endpoint_pair_latest_start_time_window | 6 | 0 | 0 | 0 | 18 | -0.00091019 | 598.219812 |
| B | B4.1_worker_tail_hidden_negative_evidence | V2_latest_service_start_slot_bound | 1 | 0 | 0 | 0 | 0 | None | 3.102362 |
| C | B4.1_selected_30_diagnostic | V4_combined_endpoint_pair_latest_start_time_window | 10 | 0 | 0 | 0 | 9 | -0.770056922 | 50.680774 |

## Stage B/C Telemetry

| stage | mode | variant | active cols | active after merge | best neg RC | last best RC | final judge wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | stageA_B2B_R2_worker_tail_dual_on |  | None | None | None | None | 0.067854 |
| A | stageA_B3B_accepted_baseline |  | None | None | None | None | 12.381732 |
| A | stageA_B4V2_default_final_judge_harvesting |  | None | None | None | None | 12.444268 |
| B | B4.1_compact_pricing_formulation | V2_latest_service_start_slot_bound | None | None | None | 0.002707375 | 58.443408 |
| B | B4.1_compact_pricing_formulation | V4_combined_endpoint_pair_latest_start_time_window | None | None | None | 0.005458125 | 53.610464 |
| B | B4.1_probe_final_judge_evidence | V2_latest_service_start_slot_bound | None | None | -0.272798 | -0.272798 | 59.762075 |
| B | B4.1_probe_final_judge_evidence | V4_combined_endpoint_pair_latest_start_time_window | 340.5 | 340.5 | -0.005443 | -0.005443 | 598.219812 |
| B | B4.1_worker_tail_hidden_negative_evidence | V2_latest_service_start_slot_bound | None | None | -0.38047 | -0.38047 | 3.102362 |
| C | B4.1_selected_30_diagnostic | V4_combined_endpoint_pair_latest_start_time_window | None | None | -1.127206 | -1.127206 | 50.680774 |

## Latest Stage B Frontier

| mode | variant | active cols | added | negatives | latest neg RC | latest frontier LB | proof kind | scope | final judge wall | source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| B4.1_probe_final_judge_evidence | V4_combined_endpoint_pair_latest_start_time_window | 348 | 3 | 3 | -0.005443 | -0.005443385 | FRONTIER_BOUND_INCOMPLETE | DIAGNOSTIC_PRICING_FRONTIER | 596.760631 | /home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_345_600s/stage_001/probe.json |

## Acceptance State

- Stage A regression clean: `True`。
- Stage B diagnostic clean: `True`。
- Stage B planned matrix complete: `True`。
- Stage C selected diagnostic clean: `True`。
- B4.1 code path exercised: `True`。
- Full long experiment complete: `False`。
- `b4_1_full_experiment_complete=False` 是刻意保守：需要另外完成 5/10/20 full regression 和 30-scale staged frontier/selected diagnostics。

## Proof-Tail Diagnostics

- Negative-discovery budget exhausted rows: `0`。
- Feasibility-proof budget exhausted rows: `0`。
- Missing optimization-proof rows: `0`。
- Positive incumbent RC but negative frontier bound rows: `5`。
- Hidden-negative miss reasons: `none`。
- Hidden-negative top miss reason: `none`。
- Tail-dual worker rows: `1`；worker-only `1`；true-dual RC recomputed `1`；tail no-column certifies `0`。
- Stage A observed regression modes: `stageA_B3B_accepted_baseline, stageA_B4V2_default_final_judge_harvesting`。
- Stage A missing regression modes: `none`。
- Stage B observed matrix cells: `B4V2_baseline, B4V2_frontier_ledger_diagnostic, B4V2_harvesting, B4V2_harvesting_frontier_ledger_diagnostic, B4V2_hidden_negative_audit, B4V4_combined_formulation_diagnostic`。
- Stage B missing matrix cells: `none`。
