# B4.1 True-Dual Proof-Tail Strengthening 报告

## Boundary

- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。
- makespan 只作为 metric，不进入 pricing objective。
- B4.1 diagnostic frontier 不自动升级 certificate。
- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_consolidated_matrix/b4_1_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_consolidated_matrix/b4_1_summary.json`

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

## Summary

| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | B4.1_compact_pricing_formulation | V2_latest_service_start_slot_bound | 2 | 0 | 0 | 0 | 0 | -0.432157206 | 58.443408 |
| B | B4.1_compact_pricing_formulation | V4_combined_endpoint_pair_latest_start_time_window | 2 | 0 | 0 | 0 | 0 | -0.198360699 | 53.610464 |
| B | B4.1_probe_final_judge_evidence | V2_latest_service_start_slot_bound | 1 | 0 | 0 | 0 | 1 | None | 59.762075 |
| B | B4.1_worker_tail_hidden_negative_evidence | V2_latest_service_start_slot_bound | 1 | 0 | 0 | 0 | 0 | None | 3.102362 |

## Stage B/C Telemetry

| stage | mode | variant | active cols | active after merge | best neg RC | last best RC | final judge wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| B | B4.1_compact_pricing_formulation | V2_latest_service_start_slot_bound | None | None | None | 0.002707375 | 58.443408 |
| B | B4.1_compact_pricing_formulation | V4_combined_endpoint_pair_latest_start_time_window | None | None | None | 0.005458125 | 53.610464 |
| B | B4.1_probe_final_judge_evidence | V2_latest_service_start_slot_bound | None | None | -0.272798 | -0.272798 | 59.762075 |
| B | B4.1_worker_tail_hidden_negative_evidence | V2_latest_service_start_slot_bound | None | None | -0.38047 | -0.38047 | 3.102362 |

## Acceptance State

- Stage A regression clean: `False`。
- Stage B diagnostic clean: `True`。
- Stage B planned matrix complete: `True`。
- Stage C selected diagnostic clean: `False`。
- B4.1 code path exercised: `True`。
- Full long experiment complete: `False`。
- `b4_1_full_experiment_complete=False` 是刻意保守：需要另外完成 5/10/20 full regression 和 30-scale staged frontier/selected diagnostics。

## Proof-Tail Diagnostics

- Negative-discovery budget exhausted rows: `0`。
- Feasibility-proof budget exhausted rows: `0`。
- Missing optimization-proof rows: `0`。
- Positive incumbent RC but negative frontier bound rows: `4`。
- Hidden-negative miss reasons: `none`。
- Hidden-negative top miss reason: `none`。
- Tail-dual worker rows: `0`；worker-only `0`；true-dual RC recomputed `0`；tail no-column certifies `0`。
- Stage B observed matrix cells: `B4V2_baseline, B4V2_frontier_ledger_diagnostic, B4V2_harvesting, B4V2_harvesting_frontier_ledger_diagnostic, B4V2_hidden_negative_audit, B4V4_combined_formulation_diagnostic`。
- Stage B missing matrix cells: `none`。
