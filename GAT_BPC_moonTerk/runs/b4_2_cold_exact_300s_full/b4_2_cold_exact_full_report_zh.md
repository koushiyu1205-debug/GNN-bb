# B4.2 Cold-Start Exact 300s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 目前固定 seed 为 B0 incumbent + singleton；更丰富的自动模板 seed 仍需后续实现。

## 汇总

- model: `B4_2_COLD_EXACT_V1`
- config hash: `35a5a63f17a3b8df`
- rows: `1`
- no-cheat fail: `0`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 1 | 0 | 0 | 1 | 300.422414 | 300.422414 | 298.148662 | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | tree | active cols | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 30 | instance_001 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 300.422414 | 298.148662 | None | 92 | instance_json_fixed_seed_and_same_run_checkpoints | root pool did not certify no-negative within cold-start row limit |
