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
- config hash: `dab1cb143c280072`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `30`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `30`, exact harvest target `64`
- rows: `20`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `25948` / `25935` / `13` / `25948`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 20 | 0 | 0 | 20 | 67.788177 | 292.58354 | 67.080042 | None | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 30 | instance_001 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 52.046273 | 51.322495 | None | None | 1583 | 0 | 0 | 1549 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_002 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 19.3932 | 18.700779 | None | None | 1198 | 0 | 0 | 1166 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_003 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 26.811765 | 26.114115 | None | None | 1098 | 0 | 0 | 1064 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_004 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 17.209111 | 16.521128 | None | None | 1358 | 0 | 0 | 1324 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_005 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 13.46419 | 12.807116 | None | None | 1058 | 0 | 0 | 1024 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_006 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 14.183439 | 13.517943 | None | None | 985 | 0 | 0 | 953 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_007 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 39.311269 | 38.632759 | None | None | 1308 | 0 | 0 | 1275 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_008 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 25.516689 | 24.774443 | None | None | 1442 | 0 | 0 | 1408 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_009 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 292.58354 | 291.813689 | None | None | 1289 | 0 | 0 | 1256 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_010 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 210.422326 | 209.668543 | None | None | 1469 | 0 | 0 | 1435 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_011 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 39.730801 | 38.996196 | None | None | 1254 | 0 | 0 | 1221 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_012 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 291.53098 | 290.743774 | None | None | 2075 | 0 | 0 | 2042 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_013 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 58.279963 | 57.576672 | None | None | 1370 | 0 | 0 | 1339 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_014 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 87.151754 | 86.450915 | None | None | 1348 | 0 | 0 | 1314 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_015 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 19.008953 | 18.337067 | None | None | 1183 | 0 | 0 | 1149 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_016 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 18.009467 | 17.306649 | None | None | 1256 | 0 | 0 | 1223 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_017 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 24.329427 | 23.65092 | None | None | 1099 | 0 | 0 | 1065 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_018 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 38.482712 | 37.804997 | None | None | 1235 | 0 | 0 | 1201 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_019 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 38.157215 | 37.462507 | None | None | 1233 | 0 | 0 | 1199 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 30 | instance_020 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | CERTIFIED_NO_NEGATIVE | False | False | 30.140463 | 29.398135 | None | None | 1774 | 0 | 0 | 1741 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
