# BPC Labeling Worker 诊断报告

## 口径

- 每个 row 从 instance JSON 自动生成 reference-repair + singleton seed。
- 禁止历史列池、成熟 probe、手工补列；本报告只比较 worker 找列能力。
- direct_label 与 relaxed_labeling 共用同一个 B2B_R3 node pricing engine。
- worker 找到的列必须用 current true RMP dual 复算 reduced cost。
- worker no-column 不能升级为 no-negative certificate。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/labeling_worker_diagnostic_path_variants_smoke/labeling_worker_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/labeling_worker_diagnostic_path_variants_smoke/labeling_worker_summary.json`

## Summary

- row_count: 2
- config_hash: `abae13f1603dead7`

| scale | worker | rows | found addable | mean added | mean label cols | mean path variants | mean selected | mean new task-set | mean harvest Jaccard | worker cert leaks | tail-dual leaks | RC recompute missing | mean false+ | mean miss | false+ rows | miss rows | mean worker sec | mean wall sec | final judge calls |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | direct_label | 1 | 1 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 | 0.000 | 0.000 | 0 | 0 | 0.050 | 0.050 | 0 |
| 5 | relaxed_labeling | 1 | 1 | 8.000 | 9.000 | 1761.000 | 8.000 | 7.000 | 0.486 | 0 | 0 | 0 | 0.000 | 0.000 | 0 | 0 | 0.082 | 0.083 | 0 |

## 证书边界

- `uses_true_dual_bpc_certificate=true` 只允许来自 exact final proof；worker 行默认不应出现。
- `labeling_no_column_uncertified=true` 表示 worker 没找到列，但不能证明无负列。
- 这份报告用于判断 relaxed/ng-route worker 是否值得接入 B4.2，不是 30-scale exact closure 报告。

## Rows

| scale | instance | worker | status | scope | pricing | seed policy | harvest policy | label cols | path variants | added | selected | new task-set | worker sec | wall sec | note |
|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 5 | lunar_ice_sp50_005_001_seed679001 | direct_label | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT |  |  | 0 | 0 | 4 | 0 | 0 | 0.049594 | 0.050139 | Stopped after max_rounds=1; B2B_R3 node proof is incomplete. |
| 5 | lunar_ice_sp50_005_001_seed679001 | relaxed_labeling | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | protected_refinement_then_source_task_count_coverage_then_low_overlap_fill | best_true_rc_first_then_min_overlap_distinct_task_sets_then_replacements | 9 | 1761 | 8 | 8 | 7 | 0.082311 | 0.082874 | Stopped after max_rounds=1; B2B_R3 node proof is incomplete. |
