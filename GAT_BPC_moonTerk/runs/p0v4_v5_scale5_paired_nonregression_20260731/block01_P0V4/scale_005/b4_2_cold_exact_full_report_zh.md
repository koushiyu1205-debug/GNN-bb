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

- model: `NATIVE_LIVE_SRI_P0V3_MEMORY_COMPACT_CANDIDATE_V3_S5_native_rcspp_inprocess`
- config hash: `49f7fec5284b4cd2`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `5`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `5`, exact harvest target `8`
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
- root-pool post-final-judge selected/new/replacement/added: `191` / `173` / `18` / `191`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 20 | 0 | 0 | 20 | 0.329164 | 1.515095 | 0.184325 | None | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 5 | instance_001 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 1.515095 | 1.27164 | None | None | 6 | 0 | 0 | 0 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_002 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.263323 | 0.124948 | None | None | 23 | 0 | 0 | 18 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_003 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.261772 | 0.127602 | None | None | 6 | 0 | 0 | 1 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_004 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.260981 | 0.116542 | None | None | 12 | 0 | 0 | 7 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_005 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.275635 | 0.137673 | None | None | 23 | 0 | 0 | 18 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_006 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.251167 | 0.116073 | None | None | 23 | 0 | 0 | 18 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_007 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.262379 | 0.121522 | None | None | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_008 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.303745 | 0.157318 | None | None | 20 | 0 | 0 | 15 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_009 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.25979 | 0.121172 | None | None | 18 | 0 | 0 | 13 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_010 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.285826 | 0.149533 | None | None | 9 | 0 | 0 | 4 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_011 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.256316 | 0.117622 | None | None | 15 | 0 | 0 | 10 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_012 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.241138 | 0.101571 | None | None | 13 | 0 | 0 | 8 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_013 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.256479 | 0.119331 | None | None | 6 | 0 | 0 | 1 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_014 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.26538 | 0.128442 | None | None | 10 | 0 | 0 | 5 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_015 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.280665 | 0.132818 | None | None | 19 | 0 | 0 | 14 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_016 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.269145 | 0.131244 | None | None | 9 | 0 | 0 | 4 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_017 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.258649 | 0.121599 | None | None | 6 | 0 | 0 | 0 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_018 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.299491 | 0.153669 | None | None | 13 | 0 | 0 | 8 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_019 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.2513 | 0.110569 | None | None | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 5 | instance_020 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 0.265 | 0.125611 | None | None | 20 | 0 | 0 | 15 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
