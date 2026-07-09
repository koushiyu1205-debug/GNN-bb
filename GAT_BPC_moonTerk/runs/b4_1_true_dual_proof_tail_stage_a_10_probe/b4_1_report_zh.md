# B4.1 True-Dual Proof-Tail Strengthening 报告

## Boundary

- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。
- makespan 只作为 metric，不进入 pricing objective。
- B4.1 diagnostic frontier 不自动升级 certificate。
- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_a_10_probe/b4_1_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_a_10_probe/b4_1_summary.json`

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_leak_count | 0 | 0 |
| manual_rc_fail_count | 0 | 0 |
| pricing_rc_fail_count | 0 | 0 |
| diagnostic_claimed_certificate_count | 0 | 0 |
| resource_guard_stopped_count | 0 | 0 |
| exception_fail_closed_count | 0 | 0 |

## Summary

| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | stageA_B2B_R2_worker_tail_dual_off |  | 1 | 0 | 1 | 0 | 0 | None | 1.072569 |
| A | stageA_B2B_R2_worker_tail_dual_on |  | 1 | 0 | 1 | 0 | 0 | None | 1.110751 |
| A | stageA_B3B_accepted_baseline |  | 1 | 1 | 0 | 0 | 0 | None | 1.386833 |
| A | stageA_B4V2_default_final_judge_harvesting |  | 1 | 1 | 0 | 0 | 0 | None | 1.379448 |

## Acceptance State

- Stage A regression clean: `True`。
- Stage B diagnostic clean: `False`。
- Stage C selected diagnostic clean: `False`。
- B4.1 code path exercised: `True`。
- Full long experiment complete: `False`。
- `b4_1_full_experiment_complete=False` 是刻意保守：需要另外完成 5/10/20 full regression 和 30-scale staged frontier/selected diagnostics。
