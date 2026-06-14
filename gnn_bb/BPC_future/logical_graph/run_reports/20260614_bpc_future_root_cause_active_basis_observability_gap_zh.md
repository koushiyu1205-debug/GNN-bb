# Active Basis Observability Gap 审计

日期：2026-06-14

## 目的

检查当前 exact-context replay 证据包是否足以恢复真正的 active-basis churn
和 RMP degeneracy pressure。该审计只读现有 summary / manifest / JSONL，
不运行 BPC、pricing、RMP、Pulse 或 replay。

## 机器字段

```text
active_basis_observability_gap = current
diagnostic_only = true
runs_bpc_or_pricing = false
manifest_case_count = 82
source_file_exists_count = 82
cases_with_pool_journeys = 82
cases_with_pool_journey_active_marker = 0
cases_with_full_active_manifest_snapshot = 0
cases_with_full_active_event_snapshot = 0
cases_with_active_hash = 81
cases_with_active_top_samples = 81
cases_with_truncated_active_top_samples = 66
exact_active_basis_churn_reconstructable_case_count = 0
exact_rmp_degeneracy_pressure_reconstructable_case_count = 0
robust_enriched_feature_count = 0
robust_model_count = 0
all_checks_pass = true
```

## 关键观察

- `pool_journeys` 存在，但 journey payload 不带 active/lambda 标记；
- JSONL 有 active task-set count、hash 和 top samples，但没有完整 active task-set / journey / lambda 快照；
- top samples 在部分 case 中短于 active task-set count，因此不能当作完整 active basis；
- 当前只能构造 hash churn / degeneracy proxy，而这些 proxy 已经没有通过 production holdout。

## 示例 case

| case_id | instance | cg_iter | active_task_set_count | top_sample_count | active_hash_present | pool_journey_count |
|---|---|---:|---:|---:|---:|---:|
| capture_case_0001 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | 1 | 12 | 8 | True | 164 |
| capture_case_0001 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | 1 | 12 | 8 | True | 164 |
| capture_case_0002 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | 2 | 8 | 8 | True | 172 |
| capture_case_0003 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | 3 | 10 | 8 | True | 180 |
| capture_case_0004 | apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 | 1 | 12 | 8 | True | 164 |

## 结论

Existing replay artifacts expose active-basis counts, hashes, and top samples, but not a full active journey/task-set/lambda snapshot.  Therefore exact active-basis churn and exact degeneracy pressure cannot be reconstructed from the current evidence bundle; only proxy fields are available, and those proxies already failed production holdouts.

因此下一步如果继续 selector 主线，必须先补 no-certificate-effect capture schema：
在加列前记录完整 active basis task sets / journey ids / lambda values。
在此之前，active-basis churn 和 degeneracy pressure 只能作为 proxy，不能作为
production-safe 优化方向。
