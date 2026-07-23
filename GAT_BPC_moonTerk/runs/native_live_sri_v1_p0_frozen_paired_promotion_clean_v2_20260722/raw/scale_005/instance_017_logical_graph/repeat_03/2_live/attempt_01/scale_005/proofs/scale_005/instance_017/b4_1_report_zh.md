# B4.1 True-Dual Proof-Tail Strengthening 报告

## Boundary

- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。
- makespan 只作为 metric，不进入 pricing objective。
- B4.1 diagnostic frontier 不自动升级 certificate。
- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/raw/scale_005/instance_017_logical_graph/repeat_03/2_live/attempt_01/scale_005/proofs/scale_005/instance_017/b4_1_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/raw/scale_005/instance_017_logical_graph/repeat_03/2_live/attempt_01/scale_005/proofs/scale_005/instance_017/b4_1_summary.json`

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
| partition_candidate_certificate_leak_count | 0 | 0 |

## Requirement Audit

| id | status | evidence | next action |
| --- | --- | --- | --- |
| R1_redlines_zero | pass | {"redline_count":9,"redline_failures":{}} |  |
| R2_stage_a_regression_clean | missing | {"missing_modes":["stageA_B3B_accepted_baseline","stageA_B4V2_default_final_judge_harvesting"],"observed_modes":[],"stage_a_regression_clean":false,"stage_a_row_count":0} | Run/import Stage A 5/10/20 regression rows and keep redlines at zero. |
| R3_stage_b_matrix_complete | missing | {"missing":["B4V2_baseline","B4V2_harvesting","B4V2_hidden_negative_audit","B4V2_frontier_ledger_diagnostic","B4V2_harvesting_frontier_ledger_diagnostic","B4V4_combined_formulation_diagnostic"],"observed":[],"stage_b_row_count":0} | Import or run evidence for every missing Stage B matrix cell. |
| R4_stage_c_selected_diagnostic | missing | {"stage_c_diagnostic_clean":false,"stage_c_row_count":0,"stage_c_selected_row_count":0} | Run/import the selected 30-scale Stage C diagnostic rows. |
| R5_stage_bc_diagnostic_only | pass | {"frontier_lb_official_row_count":0,"stage_bc_certificate_claim_count":0,"stage_bc_row_count":0} |  |
| R6_tail_dual_worker_only | pass | {"tail_dual_certificate_leak_count":0,"tail_dual_enabled_count":1,"tail_dual_no_column_can_certify_count":0,"tail_dual_official_true_dual_source_count":1,"tail_dual_true_dual_recomputed_count":1,"tail_dual_worker_only_count":1} |  |
| R7_30_scale_exact_closure | incomplete | {"known_boundary":"A 30-scale root LP no-negative proof can be recorded as underlying evidence, but R7 remains incomplete until BPC_TREE_OPTIMAL is proven.","thirty_scale_bpc_tree_optimal_count":0,"thirty_scale_underlying_exhaustive_no_negative_count":1,"thirty_scale_underlying_node_lp_certified_count":1} | Use the root no-negative proof as B4.1 tail evidence, then continue tree-level closure work toward BPC_TREE_OPTIMAL. |

## Summary

| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D | B4.1_30_tree_closure_from_probe | V4_root_tail_probe_tree_gate | 1 | 1 | 1 | 0 | 0 | -1e-06 | 0.074011 |

## Stage B/C Telemetry

| stage | mode | variant | active cols | active after merge | best neg RC | last best RC | final judge wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| D | B4.1_30_tree_closure_from_probe | V4_root_tail_probe_tree_gate | 22.0 | 22.0 | None | None | 0.013757 |

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
- Positive incumbent RC but negative frontier bound rows: `1`。
- 30-scale underlying root LP certified rows: `1`。
- 30-scale underlying exhaustive no-negative proofs: `1`。
- Hidden-negative miss reasons: `none`。
- Hidden-negative top miss reason: `none`。
- Tail-dual worker rows: `1`；worker-only `1`；true-dual RC recomputed `1`；tail no-column certifies `0`。
- Dual-search audit rows: `1`；false-positive rows `0`；miss rows `0`；mean false+ `None`；mean miss `None`。
- Partition candidate audit rows: `0`；gate pass `0`；gate fail `0`；candidate no-negative `0`；redline fail `0`。
- Partition candidate top issue: `none`；issue counts `{}`。
- Partition negative regions: `0`；payload available `0`；best negative RC `None`。
- Partition negative relation: already active `0`；replacement `0`；new task-set `0`。
- Partition model size: max variables `0`；max constraints `0`；max mean variables `None`；max mean constraints `None`。
- Partition slot pruning: max feasible assignments `0`；pruned assignments sum `0`；pruned arc options sum `0`。
- Partition dual/active scope mismatch rows: `0`；max active-pool-after-dual delta `0`；negative RC audit fail `0`。
- Partition region MIP-start: enabled `0`；OK `0`；exact OK `0`；residual OK `0`。
- Residual task-count partition: enabled rows `0`；expected `0`；observed `0`；proven `0`；incomplete `0`；negative `0`；missing `0`。
- Partition refreshed dual rows: `0`；refresh negative count `0`；refresh min RC `None`。
- Stage A observed regression modes: `none`。
- Stage A missing regression modes: `stageA_B3B_accepted_baseline, stageA_B4V2_default_final_judge_harvesting`。
- Stage B observed matrix cells: `none`。
- Stage B missing matrix cells: `B4V2_baseline, B4V2_harvesting, B4V2_hidden_negative_audit, B4V2_frontier_ledger_diagnostic, B4V2_harvesting_frontier_ledger_diagnostic, B4V4_combined_formulation_diagnostic`。
