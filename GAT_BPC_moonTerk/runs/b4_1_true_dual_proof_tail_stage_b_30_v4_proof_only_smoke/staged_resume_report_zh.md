# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_proof_only_smoke/stage_001/probe.json`
- stage_count: `1`
- compact_final_judge_profile: `V4`
- compact_final_judge_phase_mode: `proof_only`

| stage | profile | mode | batch | round cap | resume cols | active cols | added | rounds | state | scope | best neg RC | final phase | final RC | final bound | elapsed s |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|
| 1 | V4 | proof_only | 1 | 1 | 304 | 304 | 0 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | optimization_proof | 0.050987667 | -0.216844928 | 55.211764 |
