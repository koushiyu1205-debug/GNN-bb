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

- model: `P0V4_BIDIRECTIONAL_PARTIAL_ESCAPE_BATCH_ALL_SCALE_CANDIDATE_V3_S50_native_rcspp_bidirectional_midpoint_partial_hybrid_v2`
- config hash: `7ade82e07c06d923`
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
- root-pool post-final-judge selected/new/replacement/added: `63485` / `63485` / `0` / `63485`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 10 | 7 | 3 | 3 | 1251.36927 | 3603.678283 | 742.238809 | None | 562.611595 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 50 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 389.388834 | 346.586864 | None | 40.034652 | 7538 | 0 | 0 | 7483 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 458.113947 | 312.841342 | None | 142.267237 | 7641 | 0 | 0 | 7586 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 284.132829 | 230.539179 | None | 50.760888 | 6944 | 0 | 0 | 6889 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 247.629962 | 223.52465 | None | 21.620779 | 5669 | 0 | 0 | 5614 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_005 | BPC_GAP_AVAILABLE | BPC_NODE_LP_CERTIFIED | CERTIFIED_NO_NEGATIVE | False | False | 3602.811132 | 638.045304 | None | 2962.729468 | 3729 | 0 | 0 | 3674 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | tree closure did not produce BPC_TREE_OPTIMAL |
| 50 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 270.179995 | 234.04032 | None | 32.953455 | 6583 | 0 | 0 | 6528 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 450.904591 | 404.570711 | None | 42.869498 | 8173 | 0 | 0 | 8118 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_008 | BPC_GAP_AVAILABLE | BPC_NODE_LP_CERTIFIED | CERTIFIED_NO_NEGATIVE | False | False | 3603.678283 | 2630.728607 | None | 969.838646 | 5899 | 0 | 0 | 5844 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | tree closure did not produce BPC_TREE_OPTIMAL |
| 50 | instance_009 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 1452.315375 | 1450.055343 | None | None | 5788 | 0 | 0 | 5733 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 1754.537755 | 951.455771 | None | 800.42973 | 6071 | 0 | 0 | 6016 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
