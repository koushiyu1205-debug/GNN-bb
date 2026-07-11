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
- partition_negative_region_count: `5`
- partition_negative_payload_available_count: `5`
- partition_best_negative_rc: `-0.320061357`
- partition negative relation counts: already_active `0`; replacement `0`; new_task_set `5`
- partition dual/active scope mismatch count: `0`
- partition negative RC audit fail count: `0`
- redline_fail_count: `0`
- gate issue counts: `{'missing_residual_task_count_region': 1, 'negative_bound_residual_task_count_region': 1, 'negative_residual_task_count_region': 1, 'unproven_residual_task_count_region': 1}`

| probe | instance | target sets | gate | issue count | issues | variant | dual source | refresh status | negatives | already active | new task-set | dual/source cols | scope mismatches | RC audit fail | best neg RC | full-space valid | candidate no-neg | official allowed |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| /home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_worker_cap4_30_001_300s_probe_20260711/proofs/scale_030/instance_001/root_partition_feedback/round_01_partition_harvest/worker_05_k005_005/required_task_set_partition_probe.json | lunar_ice_sp50_030_001_seed929001 | 32 | False | 4 | missing_residual_task_count_region, negative_bound_residual_task_count_region, negative_residual_task_count_region, unproven_residual_task_count_region | V4_current_pair_conflict_capacity_bound | refreshed_active_pool_restricted_rmp | RESTRICTED_RMP_OPTIMAL | 5 | 0 | 5 | 221/221 | 0 | 0 | -0.320061357 | False | False | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| partition_report_official_certificate_claim_count | 0 | 0 |
| partition_report_can_claim_certificate_count | 0 | 0 |
| partition_row_certificate_claim_count | 0 | 0 |
| partition_gate_official_certificate_allowed_count | 0 | 0 |
| partition_gate_missing_count | 0 | 0 |
