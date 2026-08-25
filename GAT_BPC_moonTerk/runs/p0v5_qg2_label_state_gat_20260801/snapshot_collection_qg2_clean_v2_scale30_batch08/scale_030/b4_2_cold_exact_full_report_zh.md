# B4.2 Cold-Start Exact 300s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。
- root pool 使用固定 `b2b_r3_worker`，默认 worker 为 `relaxed_labeling`；fixed worker max task cap 是全局 config/hash 字段，不允许按实例调参。
- tail dual stabilization 只作用于 worker candidate search。
- support-continuation seed 只基于当前 RMP support 自动生成 add/drop/swap 邻域列；只找列，不给 no-negative 证书。
- final judge 使用 `labeling_final_judge=auto`：5/10 默认走 exact labeling proof，超过 fixed max exact tasks 时自动回到 compact/exhaustive proof。

## 汇总

- model: `P0V4_BIDIRECTIONAL_SRI_GROUP_SCREEN_ALL_SCALE_CANDIDATE_V5_S30_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `2ccd4d9c2ba2d08e`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `30`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `30`, exact harvest target `64`
- rows: `10`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `20747` / `20729` / `18` / `20747`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 10 | 0 | 0 | 10 | 229.154418 | 293.654615 | 228.720628 | None | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_091 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.146547 | 292.694356 | None | None | 2268 | 0 | 0 | 2246 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_092 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.473766 | 293.003245 | None | None | 2402 | 0 | 0 | 2368 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_093 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.480626 | 293.096694 | None | None | 1492 | 0 | 0 | 1458 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_094 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.579164 | 293.131901 | None | None | 2099 | 0 | 0 | 2065 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_095 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 227.705814 | 227.215776 | None | None | 2893 | 0 | 0 | 2862 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_096 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 209.147081 | 208.695683 | None | None | 2068 | 0 | 0 | 2034 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_097 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.654615 | 293.294286 | None | None | 1390 | 0 | 0 | 1356 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_098 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 206.213799 | 205.704678 | None | None | 2741 | 0 | 0 | 2708 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_099 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 66.202795 | 65.840342 | None | None | 1647 | 0 | 0 | 1613 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_100 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 114.939974 | 114.529319 | None | None | 2069 | 0 | 0 | 2037 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
