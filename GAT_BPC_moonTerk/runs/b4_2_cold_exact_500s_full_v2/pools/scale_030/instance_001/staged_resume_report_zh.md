# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_500s_full_v2/pools/scale_030/instance_001/stage_007/probe.json`
- stage_count: `7`
- compact_final_judge_profile: `V4SH`
- compact_final_judge_phase_mode: `harvest_then_proof`
- compact_optimization_harvest_target: `16`
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
| 1 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 0 | 162 | 128 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.8758525 | route_template_pre_harvest | -0.8758525 | None | 68.929659 |
| 2 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 162 | 290 | 128 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.341397334 | route_template_pre_harvest | -0.2481176 | None | 79.525129 |
| 3 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 290 | 418 | 128 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.376113254 | route_template_pre_harvest | -0.376113254 | None | 81.558624 |
| 4 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 418 | 546 | 128 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.400493845 | route_template_pre_harvest | -0.1605508 | None | 83.593366 |
| 5 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 546 | 618 | 72 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.41830701 | route_template_pre_harvest | -0.235741571 | None | 86.994673 |
| 6 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 618 | 629 | 11 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.082863287 | route_template_pre_harvest | -0.082863287 | None | 88.798026 |
| 7 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 629 | 629 | 0 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | negative_feasibility_search | None | None | 8.767859 |
