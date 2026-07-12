# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_3_spprc_exact_first_30_001_1800s_20260711_160000/pools/scale_030/instance_001/stage_008/probe.json`
- stage_count: `8`
- compact_final_judge_profile: `V4SZ`
- compact_final_judge_phase_mode: `harvest_then_proof`
- compact_optimization_harvest_target: `32`
- compact_optimization_harvest_no_good_scope: `task_set`
- compact_service_start_depot_travel_lb: `True`
- compact_task_to_depot_return_travel_lb: `True`
- compact_pair_route_duration_lb: `True`
- compact_sortie_slot_position_bounds: `True`
- compact_demand_cover_cut: `False`
- compact_single_task_energy_lb: `False`
- compact_single_task_shadow_lb: `False`
- compact_pair_energy_lb: `False`
- compact_pair_energy_infeasible_cut: `True`
- compact_pair_shadow_infeasible_cut: `False`
- compact_triple_time_window_infeasible_cut: `True`
- compact_quad_time_window_infeasible_cut: `False`
- compact_triple_shadow_infeasible_cut: `False`
- compact_triple_energy_infeasible_cut: `False`

| stage | profile | mode | opt harvest | opt scope | opt found | opt exact neg | opt tl neg | opt tl no-neg | feas status | feas neg | feas cert | feas RC | feas bound | batch | round cap | resume cols | active cols | added | rounds | state | scope | best neg RC | final phase | final RC | final bound | elapsed s |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|
| 1 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 34 | 546 | 512 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.212164545 | None | 183.562008 |
| 2 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 546 | 1058 | 512 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.096255451 | None | 193.819804 |
| 3 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 1058 | 1570 | 512 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.052852392 | None | 194.886815 |
| 4 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 1570 | 2082 | 512 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.04845075 | None | 202.183366 |
| 5 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 2082 | 2594 | 512 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.092948039 | None | 211.909485 |
| 6 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 2594 | 3106 | 512 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.007020016 | None | 227.018797 |
| 7 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 3106 | 3613 | 507 | 16 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.087825685 | None | 329.283705 |
| 8 | V4SZ | harvest_then_proof | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 64 | 16 | 3613 | 3887 | 274 | 9 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.073188526 | None | 257.905626 |
