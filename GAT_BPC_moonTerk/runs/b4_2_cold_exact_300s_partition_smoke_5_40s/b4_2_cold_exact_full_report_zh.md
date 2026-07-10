# B4.2 Cold-Start Exact 300s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。

## 汇总

- model: `B4_2_COLD_EXACT_V1`
- config hash: `e408e032b2546f1d`
- rows: `1`
- no-cheat fail: `0`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 0 | 0.289445 | 0.289445 | 0.009126 | None | 0.172514 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 5 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.289445 | 0.009126 | None | 0.172514 | 26 | instance_json_fixed_seed_and_same_run_checkpoints |  |
