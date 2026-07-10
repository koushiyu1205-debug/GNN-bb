# B4.1 Partition Candidate Audit

## Boundary

- This audit summarizes required-task-set partition probe artifacts.
- A passing partition gate is still diagnostic-only until final judge ledger integration.
- No official no-negative certificate or `BPC_TREE_OPTIMAL` claim is made here.

## Summary

- partition_probe_count: `1`
- partition_gate_pass_count: `0`
- partition_gate_fail_count: `1`
- partition_candidate_can_certify_no_negative_count: `0`
- partition_negative_region_count: `1`
- partition_negative_payload_available_count: `1`
- partition_best_negative_rc: `-0.0008186`
- partition negative relation counts: already_active `0`; replacement `0`; new_task_set `1`
- partition dual/active scope mismatch count: `0`
- partition negative RC audit fail count: `0`
- redline_fail_count: `0`
- gate issue counts: `{'incomplete_residual_task_count_region': 1, 'missing_residual_task_count_region': 1, 'mixed_formulation_partition_rows': 1, 'mixed_variant_partition_rows': 1, 'negative_bound_residual_task_count_region': 1, 'unproven_residual_task_count_region': 1}`

| probe | instance | target sets | gate | issue count | issues | variant | dual source | refresh status | negatives | already active | new task-set | dual/source cols | scope mismatches | RC audit fail | best neg RC | full-space valid | candidate no-neg | official allowed |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| /home/kai/work/GAT_BPC_moonTerk/runs/b4_1_v4_residual_task_count_k5_variant_sweep_probe/required_task_set_partition_probe.json | lunar_ice_sp50_030_001_seed929001 | 1 | False | 6 | incomplete_residual_task_count_region, missing_residual_task_count_region, mixed_formulation_partition_rows, mixed_variant_partition_rows, negative_bound_residual_task_count_region, unproven_residual_task_count_region |  | refreshed_active_pool_restricted_rmp | RESTRICTED_RMP_OPTIMAL | 1 | 0 | 1 | 346/346 | 0 | 0 | -0.0008186 | False | False | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| partition_report_official_certificate_claim_count | 0 | 0 |
| partition_report_can_claim_certificate_count | 0 | 0 |
| partition_row_certificate_claim_count | 0 | 0 |
| partition_gate_official_certificate_allowed_count | 0 | 0 |
| partition_gate_missing_count | 0 | 0 |
