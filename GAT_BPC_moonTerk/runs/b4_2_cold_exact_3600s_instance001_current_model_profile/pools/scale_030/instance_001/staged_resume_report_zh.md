# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_3600s_instance001_current_model_profile/pools/scale_030/instance_001/stage_010/probe.json`
- stage_count: `10`
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
| 1 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 0 | 151 | 117 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.551745 | route_template_pre_harvest | -0.431978 | None | 80.092779 |
| 2 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 151 | 279 | 128 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.4642345 | route_template_pre_harvest | -0.256892353 | None | 80.396611 |
| 3 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 279 | 407 | 128 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.313369818 | route_template_pre_harvest | -0.160097215 | None | 81.685923 |
| 4 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 407 | 512 | 105 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.207389335 | route_template_pre_harvest | -0.144578 | None | 84.044734 |
| 5 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 512 | 576 | 64 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.28638875 | negative_feasibility_batch | -0.2162525 | 0.0 | 150.346727 |
| 6 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 576 | 596 | 20 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.125257333 | negative_feasibility_batch | -0.125257333 | 0.0 | 150.316319 |
| 7 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 596 | 607 | 11 | 3 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.076552 | negative_feasibility_search | None | None | 151.997374 |
| 8 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 607 | 622 | 15 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.184438353 | negative_feasibility_search | None | None | 151.913094 |
| 9 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 622 | 643 | 21 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.06014275 | route_template_pre_harvest | -0.029645769 | None | 87.095705 |
| 10 | V4SH | harvest_then_proof | 16 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 32 | 4 | 643 | 655 | 12 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.203389559 | negative_feasibility_search | None | None | 152.256601 |
