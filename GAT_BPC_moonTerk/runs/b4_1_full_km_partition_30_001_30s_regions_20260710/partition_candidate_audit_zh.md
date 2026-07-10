# B4.1 Partition Candidate Audit

## Boundary

- This audit summarizes required-task-set partition probe artifacts.
- A passing partition gate is still diagnostic-only until final judge ledger integration.
- No official no-negative certificate or `BPC_TREE_OPTIMAL` claim is made here.

## Summary

- partition_probe_count: `1`
- partition_gate_pass_count: `1`
- partition_gate_fail_count: `0`
- partition_candidate_can_certify_no_negative_count: `1`
- partition_negative_region_count: `0`
- partition_negative_payload_available_count: `0`
- partition_best_negative_rc: `None`
- partition negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- partition dual/active scope mismatch count: `465`
- partition negative RC audit fail count: `0`
- redline_fail_count: `0`
- gate issue counts: `{}`

| probe | instance | target sets | gate | issue count | issues | variant | dual source | refresh status | negatives | already active | new task-set | dual/source cols | scope mismatches | RC audit fail | best neg RC | full-space valid | candidate no-neg | official allowed |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| /home/kai/work/GAT_BPC_moonTerk/runs/b4_1_full_km_partition_30_001_30s_regions_20260710/required_task_set_partition_probe.json | lunar_ice_sp50_030_001_seed929001 | 0 | True | 0 | none | V4_current_pair_conflict_capacity_bound | selected_history_dual |  | 0 | 0 | 0 | 338/371 | 465 | 0 | None | True | True | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| partition_report_official_certificate_claim_count | 0 | 0 |
| partition_report_can_claim_certificate_count | 0 | 0 |
| partition_row_certificate_claim_count | 0 | 0 |
| partition_gate_official_certificate_allowed_count | 0 | 0 |
| partition_gate_missing_count | 0 | 0 |
