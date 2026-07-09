# B4.1 Restricted Region Task-Set Diagnostic

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_proof_kind: `FRONTIER_BOUND_INCOMPLETE`
- global_remaining_rc_lb: `-0.00770611`
- frontier_unsupported_region_count: `3`
- This report is diagnostic-only. No no-negative certificate is claimed.

## Harvested Negatives

| id | true RC | pricing RC | size | would enter | task set |
| --- | ---: | ---: | ---: | --- | --- |
| H1 | -0.007705961 | -0.00770611 | 7 | True | ice_site_008, ice_site_009, ice_site_010, ice_site_016, ice_site_018, ice_site_024, ice_site_026 |
| H2 | -0.002763549 | -0.002763188 | 8 | True | ice_site_001, ice_site_002, ice_site_008, ice_site_020, ice_site_021, ice_site_023, ice_site_024, ice_site_026 |
| H3 | -0.000586 | -0.000586223 | 8 | True | ice_site_001, ice_site_002, ice_site_008, ice_site_013, ice_site_020, ice_site_021, ice_site_023, ice_site_026 |

## Task Frequency

| task | count |
| --- | ---: |
| ice_site_008 | 3 |
| ice_site_026 | 3 |
| ice_site_001 | 2 |
| ice_site_002 | 2 |
| ice_site_020 | 2 |
| ice_site_021 | 2 |
| ice_site_023 | 2 |
| ice_site_024 | 2 |
| ice_site_009 | 1 |
| ice_site_010 | 1 |
| ice_site_013 | 1 |
| ice_site_016 | 1 |
| ice_site_018 | 1 |

## Pairwise Overlap

| pair | intersection | Jaccard | shared tasks |
| --- | ---: | ---: | --- |
| H1-H2 | 3 | 0.25 | ice_site_008, ice_site_024, ice_site_026 |
| H1-H3 | 2 | 0.153846 | ice_site_008, ice_site_026 |
| H2-H3 | 7 | 0.777778 | ice_site_001, ice_site_002, ice_site_008, ice_site_020, ice_site_021, ice_site_023, ice_site_026 |

## Restricted Region Rows

| phase | status | exact | best RC | dual bound | forbidden task sets | wall s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| optimization_proof | COMPACT_HIGHS_PRICING_OPTIMAL | EXACT_PRICING_OPTIMAL | -0.007705961 | -0.00770611 | 0 | 186.708639 |
| optimization_harvest_2 | COMPACT_HIGHS_PRICING_OPTIMAL | RESTRICTED_PRICING_OPTIMAL | -0.002763549 | -0.002763188 | 1 | 229.826581 |
| optimization_harvest_3 | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | -0.000586 | -0.121782748 | 2 | 169.140462 |
| optimization_harvest_4 | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.169087764 | -0.317649341 | 3 | 14.719334 |

## Interpretation

- Hot tasks: `ice_site_008, ice_site_026`.
- Repeated tasks: `ice_site_008, ice_site_026, ice_site_001, ice_site_002, ice_site_020, ice_site_021, ice_site_023, ice_site_024`.
- High-overlap pairs: `H2-H3`.
- Negative time-limit regions: `1`.
- Incomplete time-limit regions: `2`.

## Next Actions

- Keep this diagnostic non-certifying until an unrestricted true-dual no-negative proof closes.
- Target the time-limit restricted regions first; bound movement there is more important than finding more columns.
- Compare V2 and V4 proof rows on the high-overlap task-set cluster before adding more harvest stages.
- Audit resource/time-window bounds around repeated hot tasks: ice_site_008, ice_site_026.
