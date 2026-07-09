# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_005_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_c_selected30_input_probes/instance_005/stage_001/probe.json`
- stage_count: `1`

| stage | batch | round cap | resume cols | active cols | added | rounds | state | scope | best RC | elapsed s |
|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| 1 | 5 | 3 | 0 | 39 | 5 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -1.925501 | 301.781144 |
