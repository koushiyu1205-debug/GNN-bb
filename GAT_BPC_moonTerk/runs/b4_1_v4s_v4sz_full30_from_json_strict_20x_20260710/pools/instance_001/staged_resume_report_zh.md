# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_v4s_v4sz_full30_from_json_strict_20x_20260710/pools/instance_001/stage_003/probe.json`
- stage_count: `3`
- compact_final_judge_profile: `V4S`
- compact_final_judge_phase_mode: `proof_only`
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
| 1 | V4S | proof_only | 5 | task_set | 5 | 5 | 0 | 0 |  | False | False | None | None | 1 | 1 | 0 | 39 | 5 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.5989875 | optimization_harvest | -0.5989875 | -0.598987461 | 36.024274 |
| 2 | V4S | proof_only | 16 | task_set | 16 | 16 | 0 | 0 |  | False | False | None | None | 1 | 4 | 39 | 103 | 64 | 4 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -1.0154355 | optimization_harvest | -0.059415 | -0.059414744 | 475.286042 |
| 3 | V4S | proof_only | 32 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1 | 4 | 103 | 151 | 48 | 4 | CERTIFIED_NO_NEGATIVE | BPC_NODE_LP_CERTIFIED | -0.081925 | optimization_proof | 0.0 | -3.68e-07 | 541.376706 |
