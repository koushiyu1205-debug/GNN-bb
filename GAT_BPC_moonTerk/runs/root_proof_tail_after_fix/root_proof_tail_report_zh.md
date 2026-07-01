# Root Proof-Tail After-Fix Selected5 Report

本报告只跑 B0 direct-DP 与 B1B seeded root-CG；20-scale 不跑 B1A full-universe RMP，避免高内存。

| scale | mode | runs | direct optimal | BPC node LP certified | incomplete | mean wall | max wall |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | B0_pure_direct_dp | 5 | 5 | 0 | 0 | 0.00402 | 0.005044 |
| 5 | B1B_seeded_root_CG | 5 | 0 | 5 | 0 | 0.010148 | 0.012708 |
| 10 | B0_pure_direct_dp | 5 | 5 | 0 | 0 | 0.092237 | 0.125672 |
| 10 | B1B_seeded_root_CG | 5 | 0 | 5 | 0 | 0.216015 | 0.288667 |
| 20 | B0_pure_direct_dp | 5 | 5 | 0 | 0 | 10.283416 | 19.945939 |
| 20 | B1B_seeded_root_CG | 5 | 0 | 5 | 0 | 39.203863 | 54.005663 |
| 30 | B0_pure_direct_dp | 5 | 0 | 0 | 5 | 0.002041 | 0.00244 |
| 30 | B1B_seeded_root_CG | 5 | 0 | 0 | 5 | 0.001577 | 0.001769 |

- 10/20 selected5 B1B accepted: True。
- max_rss_mb: 263.8。
- 30-scale 使用 max_direct_tasks=20 fail-closed；本报告不声称 30-scale BPC root closure。
