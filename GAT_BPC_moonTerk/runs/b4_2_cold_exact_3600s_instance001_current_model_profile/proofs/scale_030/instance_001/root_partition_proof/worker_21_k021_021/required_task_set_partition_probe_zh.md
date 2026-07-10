# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_3600s_instance001_current_model_profile/pools/scale_030/instance_001/stage_010/probe.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `0`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['missing_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `0` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `False`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- dual/active scope: source active `655`; dual active `655`; delta `0`; mismatch rows `0`
- dual source: `refreshed_active_pool_restricted_rmp`; refresh status `RESTRICTED_RMP_OPTIMAL`; refresh min RC `-1e-09`; refresh negatives `0`
- region MIP-start: enabled `0`; OK `0`; exact OK `0`; residual OK `0`
- negative RC audit fail count: `0`
- adaptive active-sortie refinement: enabled `False`; attempts `0`; coarse accepted `0`; refined `0`; discarded coarse wall `0.0`; total wall `8.719657`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| residual_task_count_021_active_sorties_001 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_002 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_003 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_004 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_005 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_006 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_007 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_008 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_009 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_010 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_011 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_012 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_013 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_014 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_015 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_016 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_017 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_018 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_019 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_020 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |
| residual_task_count_021_active_sorties_021 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 655 | 655 | True | True | False | False | False |  |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
