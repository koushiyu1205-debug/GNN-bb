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
- config hash: `aa436d1b80b01932`
- engine: `internal_resource_label_core` / `237f3857714e68a1`
- worker/exact: `RELAXED_NG_WORKER` / `EXACT_ELEMENTARY_PROOF`
- exact-final-judge-first: `True`
- ng sizes: `[6, 10, 14, 30]`
- accepted: `False`
- redlines zero: `True`
- full 30 complete: `False`

| scale | rows | exact | under1800 exact | under300 exact | fail-closed | mean total | max total | mean SPPRC worker | mean SPPRC exact |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 1 | 0 | 0 | 0 | 1 | 607.784329 | 607.784329 | 0.0 | 0.0 |

## Per-Instance

| scale | instance | scope | pricing | exact | under1800 | total | root | tree | SPPRC exact | ng | terminal | fail reason |
|---:|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 30 | instance_001 | DIAGNOSTIC_PRICING_FRONTIER |  | False | False | 607.784329 | 0.0 | None | 0.0 | [6, 10, 14, 30] | True | STAGE_SUBPROCESS_TIMEOUT: command exceeded 605.000s fail-closed |
