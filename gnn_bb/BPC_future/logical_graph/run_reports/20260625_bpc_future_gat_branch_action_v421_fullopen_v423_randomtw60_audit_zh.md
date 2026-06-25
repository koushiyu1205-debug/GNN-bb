# V421/V423 full-open random-TW 60-instance audit

日期：2026-06-26

## 机器字段

```text
instance_count = 60
baseline_status_counts = {'EXTERNAL_TIME_LIMIT': 30, 'TIME_LIMIT': 4, 'OPTIMAL': 26}
fullopen_status_counts = {'OPTIMAL': 29, 'EXTERNAL_TIME_LIMIT': 26, 'TIME_LIMIT': 5}
class_counts = {'timeout_resolved_to_optimal': 4, 'both_unsolved': 30, 'optimal_wall_regressed': 5, 'optimal_wall_improved': 6, 'neutral': 14, 'lost_optimal': 1}
baseline_optimal_count = 26
fullopen_optimal_count = 29
baseline_le_200_count = 20
fullopen_le_200_count = 20
baseline_capped_mean = 381.77389505
fullopen_capped_mean = 357.27243063333333
capped_mean_delta = -24.501464416666668
wins_gt5_count = 11
losses_gt5_count = 8
neutral_abs_le5_count = 41
common_optimal_count = 25
common_optimal_mean_delta = -14.789311080000001
material_positive_count = 10
material_regression_count = 8
```

## 解释

- `200s` 只作为验收统计，不作为训练硬断点。
- 主比较看 `OPTIMAL` 闭环数、common-OPTIMAL wall-time、以及 600s capped wall-time 平均。
- 未 OPTIMAL 的 TIME_LIMIT/EXTERNAL_TIME_LIMIT 不作为严格正例；它们只进入资源占用统计。

## 最大改善

- -441.817s: `apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json` EXTERNAL_TIME_LIMIT 600.050s -> TIME_LIMIT 158.183s (both_unsolved)
- -356.626s: `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json` EXTERNAL_TIME_LIMIT 600.022s -> OPTIMAL 243.374s (timeout_resolved_to_optimal)
- -305.164s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json` EXTERNAL_TIME_LIMIT 600.018s -> OPTIMAL 294.836s (timeout_resolved_to_optimal)
- -269.121s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json` OPTIMAL 327.746s -> OPTIMAL 58.625s (optimal_wall_improved)
- -231.613s: `apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json` EXTERNAL_TIME_LIMIT 600.022s -> OPTIMAL 368.387s (timeout_resolved_to_optimal)
- -128.158s: `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json` EXTERNAL_TIME_LIMIT 600.017s -> OPTIMAL 471.842s (timeout_resolved_to_optimal)
- -124.648s: `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json` OPTIMAL 522.147s -> OPTIMAL 397.499s (optimal_wall_improved)
- -71.067s: `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json` OPTIMAL 173.764s -> OPTIMAL 102.697s (optimal_wall_improved)
- -48.940s: `apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json` OPTIMAL 220.161s -> OPTIMAL 171.221s (optimal_wall_improved)
- -22.359s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json` OPTIMAL 144.821s -> OPTIMAL 122.462s (optimal_wall_improved)
- -8.916s: `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json` OPTIMAL 42.301s -> OPTIMAL 33.384s (optimal_wall_improved)
- -3.504s: `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json` OPTIMAL 51.974s -> OPTIMAL 48.470s (neutral)

## 最大回归

- +310.125s: `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json` OPTIMAL 287.680s -> TIME_LIMIT 597.804s (lost_optimal)
- +86.237s: `apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json` OPTIMAL 188.584s -> OPTIMAL 274.821s (optimal_wall_regressed)
- +44.254s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json` TIME_LIMIT 555.746s -> EXTERNAL_TIME_LIMIT 600.019s (both_unsolved)
- +31.452s: `apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json` OPTIMAL 129.364s -> OPTIMAL 160.816s (optimal_wall_regressed)
- +27.160s: `apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json` OPTIMAL 198.987s -> OPTIMAL 226.146s (optimal_wall_regressed)
- +21.208s: `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json` OPTIMAL 253.704s -> OPTIMAL 274.912s (optimal_wall_regressed)
- +6.783s: `apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json` TIME_LIMIT 544.970s -> TIME_LIMIT 551.754s (both_unsolved)
- +6.732s: `apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json` OPTIMAL 213.972s -> OPTIMAL 220.705s (optimal_wall_regressed)
- +2.198s: `apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json` TIME_LIMIT 240.134s -> TIME_LIMIT 242.332s (both_unsolved)
- +1.442s: `apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json` OPTIMAL 55.590s -> OPTIMAL 57.033s (neutral)
- +1.306s: `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json` OPTIMAL 47.515s -> OPTIMAL 48.820s (neutral)
- +0.929s: `apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json` OPTIMAL 106.645s -> OPTIMAL 107.574s (neutral)
