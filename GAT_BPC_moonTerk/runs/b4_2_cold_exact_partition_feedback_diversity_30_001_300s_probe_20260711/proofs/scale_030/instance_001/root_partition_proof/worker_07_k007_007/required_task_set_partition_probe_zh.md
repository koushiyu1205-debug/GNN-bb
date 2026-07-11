# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_partition_feedback_diversity_30_001_300s_probe_20260711/pools/scale_030/instance_001/stage_002/probe.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `32`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['missing_residual_task_count_region', 'negative_bound_residual_task_count_region', 'negative_residual_task_count_region', 'unproven_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `32` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `True`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `5`
- dual/active scope: source active `340`; dual active `340`; delta `0`; mismatch rows `0`
- dual source: `refreshed_active_pool_restricted_rmp`; refresh status `RESTRICTED_RMP_OPTIMAL`; refresh min RC `-0.0`; refresh negatives `0`
- region MIP-start: enabled `37`; OK `15`; exact OK `10`; residual OK `5`
- negative RC audit fail count: `0`
- adaptive active-sortie refinement: enabled `False`; attempts `0`; coarse accepted `0`; refined `0`; discarded coarse wall `0.0`; total wall `21.085141`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| exact_001 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_002 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_003 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.063363876 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_004 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_005 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_006 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.031048724 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_007 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_008 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_009 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.027456335 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_010 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_011 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.000795764 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_012 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_013 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_014 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_015 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_016 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.104313925 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_017 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_018 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_019 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_020 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_021 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.0 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_022 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_023 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_024 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_025 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.119027751 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_026 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_027 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.090581829 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_028 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.101659152 |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_029 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_030 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_031 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| exact_032 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.152564711 |  |  | 340 | 340 | True | True | False | False | False |  |
| residual_task_count_007_active_sorties_001 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |
| residual_task_count_007_active_sorties_002 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL | -0.277054204 | -0.277054204 | 0.0 | 340 | 340 | True | False | True | True | False | new_task_set |
| residual_task_count_007_active_sorties_003 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL | -0.264815859 | -0.264815859 | 0.0 | 340 | 340 | True | False | True | True | False | new_task_set |
| residual_task_count_007_active_sorties_004 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL | -0.237101859 | -0.237101859 | 0.0 | 340 | 340 | True | False | True | True | False | new_task_set |
| residual_task_count_007_active_sorties_005 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL | -0.181978098 | -0.181978098 | 0.0 | 340 | 340 | True | False | True | True | False | new_task_set |
| residual_task_count_007_active_sorties_006 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL | -0.014831651 | -0.014831651 | 0.0 | 340 | 340 | True | False | True | True | False | new_task_set |
| residual_task_count_007_active_sorties_007 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 340 | 340 | True | True | False | False | False |  |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
