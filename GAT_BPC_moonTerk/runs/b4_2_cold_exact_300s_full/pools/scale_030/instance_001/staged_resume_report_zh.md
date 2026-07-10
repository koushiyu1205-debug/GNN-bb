# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_300s_full/pools/scale_030/instance_001/stage_008/probe.json`
- stage_count: `8`
- compact_final_judge_profile: `V4SZ`
- compact_final_judge_phase_mode: `harvest_then_proof`
- compact_optimization_harvest_target: `8`
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
| 1 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 0 | 42 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.124878 | negative_feasibility_batch | -0.032452 | 0.0 | 47.21065 |
| 2 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 42 | 50 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.26953 | negative_feasibility_batch | -0.26953 | 0.0 | 38.415294 |
| 3 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 50 | 58 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.157736 | negative_feasibility_batch | -0.157736 | 0.0 | 38.003708 |
| 4 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 58 | 66 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.248269 | negative_feasibility_batch | -0.0426165 | 0.0 | 40.101806 |
| 5 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 66 | 74 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.041861 | negative_feasibility_batch | -0.041861 | 0.0 | 39.690687 |
| 6 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 74 | 82 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.1427115 | negative_feasibility_batch | -0.034725667 | 0.0 | 42.075496 |
| 7 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 82 | 90 | 8 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.067694 | negative_feasibility_batch | -0.067694 | 0.0 | 39.387196 |
| 8 | V4SZ | harvest_then_proof | 8 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 4 | 2 | 90 | 92 | 2 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.036302 | negative_feasibility_search | None | None | 13.263825 |
