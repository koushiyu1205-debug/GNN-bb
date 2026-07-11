# BPC Labeling Worker 诊断报告

## 口径

- 每个 row 从 instance JSON 自动生成 reference-repair + singleton seed。
- 禁止历史列池、成熟 probe、手工补列；本报告只比较 worker 找列能力。
- direct_label 与 relaxed_labeling 共用同一个 B2B_R3 node pricing engine。
- worker 找到的列必须用 current true RMP dual 复算 reduced cost。
- worker no-column 不能升级为 no-negative certificate。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/labeling_worker_diagnostic_refinement_seed_smoke/labeling_worker_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/labeling_worker_diagnostic_refinement_seed_smoke/labeling_worker_summary.json`

## Summary

- row_count: 4
- config_hash: `4cf11d520b30f0c2`

| scale | worker | rows | found addable | mean added | mean worker sec | mean wall sec | final judge calls |
|---:|---|---:|---:|---:|---:|---:|---:|
| 5 | direct_label | 1 | 1 | 5.000 | 0.053 | 0.053 | 0 |
| 5 | relaxed_labeling | 1 | 1 | 5.000 | 0.075 | 0.076 | 0 |
| 30 | direct_label | 1 | 1 | 4.000 | 0.058 | 0.060 | 0 |
| 30 | relaxed_labeling | 1 | 1 | 9.000 | 0.107 | 0.109 | 0 |

## 证书边界

- `uses_true_dual_bpc_certificate=true` 只允许来自 exact final proof；worker 行默认不应出现。
- `labeling_no_column_uncertified=true` 表示 worker 没找到列，但不能证明无负列。
- 这份报告用于判断 relaxed/ng-route worker 是否值得接入 B4.2，不是 30-scale exact closure 报告。

## Rows

| scale | instance | worker | status | scope | pricing | added | worker sec | wall sec | note |
|---:|---|---|---|---|---|---:|---:|---:|---|
| 30 | lunar_ice_sp50_030_001_seed929001 | direct_label | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 4 | 0.058455 | 0.060308 | Stopped after max_rounds=1; B2B_R3 node proof is incomplete. |
| 30 | lunar_ice_sp50_030_001_seed929001 | relaxed_labeling | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 9 | 0.107022 | 0.108674 | Stopped after max_rounds=1; B2B_R3 node proof is incomplete. |
| 5 | lunar_ice_sp50_005_001_seed679001 | direct_label | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 5 | 0.052723 | 0.053227 | Stopped after max_rounds=1; B2B_R3 node proof is incomplete. |
| 5 | lunar_ice_sp50_005_001_seed679001 | relaxed_labeling | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | 5 | 0.075256 | 0.075749 | Stopped after max_rounds=1; B2B_R3 node proof is incomplete. |
