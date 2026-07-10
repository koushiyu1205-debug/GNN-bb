# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `0`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['missing_residual_region', 'no_target_task_sets']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `0` / `0` / `0`
- residual observed / proven / negative: `False` / `False` / `False`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- dual/active scope: source active `0`; dual active `0`; delta `0`; mismatch rows `0`
- dual source: ``; refresh status ``; refresh min RC `None`; refresh negatives `0`
- region MIP-start: enabled `0`; OK `0`; exact OK `0`; residual OK `0`
- negative RC audit fail count: `0`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
