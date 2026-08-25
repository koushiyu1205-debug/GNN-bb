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

- model: `P0V4_BIDIRECTIONAL_SRI_GROUP_SCREEN_ALL_SCALE_CANDIDATE_V5_S50_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `32b415e72f52668b`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `50`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `50`, exact harvest target `128`
- rows: `29`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `199256` / `199244` / `12` / `199256`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 29 | 0 | 0 | 29 | 294.137547 | 295.236682 | 293.014792 | None | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 50 | instance_002 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.001434 | 293.090577 | None | None | 5434 | 0 | 0 | 5379 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_003 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.620945 | 293.586043 | None | None | 6376 | 0 | 0 | 6321 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_004 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.69129 | 292.673733 | None | None | 6508 | 0 | 0 | 6453 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_005 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.619903 | 292.721867 | None | None | 5597 | 0 | 0 | 5542 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_006 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.536564 | 292.421845 | None | None | 6969 | 0 | 0 | 6914 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_007 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.233301 | 293.181294 | None | None | 6327 | 0 | 0 | 6272 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_008 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.266568 | 293.311249 | None | None | 5496 | 0 | 0 | 5441 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_009 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.924902 | 292.661745 | None | None | 7795 | 0 | 0 | 7740 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_010 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.4519 | 293.560943 | None | None | 5457 | 0 | 0 | 5402 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_011 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.244447 | 291.842892 | None | None | 8761 | 0 | 0 | 8706 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_012 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.364814 | 293.476944 | None | None | 5431 | 0 | 0 | 5376 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_013 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.412446 | 293.280498 | None | None | 6808 | 0 | 0 | 6753 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_014 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.336825 | 293.039279 | None | None | 8203 | 0 | 0 | 8148 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_015 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.694313 | 293.417819 | None | None | 8154 | 0 | 0 | 8100 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_016 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.713714 | 293.669814 | None | None | 6327 | 0 | 0 | 6272 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_017 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.843461 | 292.852389 | None | None | 6021 | 0 | 0 | 5967 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_018 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.585164 | 293.52766 | None | None | 5714 | 0 | 0 | 5659 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_019 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.196981 | 293.332379 | None | None | 5278 | 0 | 0 | 5223 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_020 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.939096 | 292.583381 | None | None | 8515 | 0 | 0 | 8460 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_021 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.307011 | 292.284703 | None | None | 6205 | 0 | 0 | 6150 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_022 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.225685 | 293.13123 | None | None | 6337 | 0 | 0 | 6282 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_023 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.711291 | 293.589337 | None | None | 6730 | 0 | 0 | 6675 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_024 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.569748 | 292.434826 | None | None | 7351 | 0 | 0 | 7296 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_025 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.559443 | 293.152358 | None | None | 9015 | 0 | 0 | 8960 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_026 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.815854 | 292.759598 | None | None | 6243 | 0 | 0 | 6189 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_027 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 295.236682 | 293.877343 | None | None | 8674 | 0 | 0 | 8626 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_028 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.085153 | 292.795303 | None | None | 8297 | 0 | 0 | 8242 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_029 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.572236 | 292.429733 | None | None | 7487 | 0 | 0 | 7432 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_030 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.22769 | 292.742194 | None | None | 9329 | 0 | 0 | 9276 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
