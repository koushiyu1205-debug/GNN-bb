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
- root-pool post-final-judge selected/new/replacement/added: `77677` / `77677` / `0` / `77677`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 10 | 0 | 0 | 10 | 294.561318 | 295.876902 | 293.293942 | None | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 50 | instance_111 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.30788 | 293.422544 | None | None | 5047 | 0 | 0 | 4992 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_112 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 295.354624 | 294.076563 | None | None | 7744 | 0 | 0 | 7689 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_113 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.796837 | 293.522672 | None | None | 7457 | 0 | 0 | 7402 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_114 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.404487 | 293.376876 | None | None | 6106 | 0 | 0 | 6051 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_115 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.253942 | 292.827648 | None | None | 9447 | 0 | 0 | 9392 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_116 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 293.35857 | 291.8672 | None | None | 9389 | 0 | 0 | 9334 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_117 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.094798 | 293.123625 | None | None | 6071 | 0 | 0 | 6016 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_118 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 295.876902 | 294.079573 | None | None | 11193 | 0 | 0 | 11138 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_119 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.845295 | 293.702197 | None | None | 6907 | 0 | 0 | 6852 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
| 50 | instance_120 | GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 294.319842 | 292.940518 | None | None | 8866 | 0 | 0 | 8811 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | diagnostic route-opportunity collection stopped after the configured natural root trajectory; tree closure was intentionally skipped and no  |
