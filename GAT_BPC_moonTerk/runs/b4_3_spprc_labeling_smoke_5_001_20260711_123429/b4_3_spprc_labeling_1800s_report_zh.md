# B4.3 SPPRC Labeling 1800s Cold-Start Report

## 边界

- 每个正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止历史列池、mature probe、手工补列、按实例调参。
- seed、worker、pricing、tree、certificate 全部计入 `cold_start_total_sec`。
- `RELAXED_NG_WORKER` 只找列，不能给 no-negative 证书。
- `EXACT_ELEMENTARY_PROOF` 是唯一正式 no-negative 证书路径。
- B4.2 `(k,m)` partition ledger 在 B4.3 中不是 official certificate path。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。

## 汇总

- model: `B4_3_SPPRC_LABELING_V1`
- config hash: `e638ac6fcc2cadbb`
- engine: `internal_resource_label_core` / `237f3857714e68a1`
- worker/exact: `RELAXED_NG_WORKER` / `EXACT_ELEMENTARY_PROOF`
- ng sizes: `[6, 10, 14, 30]`
- accepted: `False`
- redlines zero: `True`
- full 30 complete: `False`

| scale | rows | exact | under1800 exact | under300 exact | fail-closed | mean total | max total | mean SPPRC worker | mean SPPRC exact |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 1 | 0 | 0.856348 | 0.856348 | 0.453857 | 0.006237 |

## Per-Instance

| scale | instance | scope | pricing | exact | under1800 | total | root | tree | SPPRC exact | ng | terminal | fail reason |
|---:|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 5 | instance_001 | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.856348 | 0.453857 | 0.251471 | 0.006237 | [6, 10, 14, 30] | True |  |
