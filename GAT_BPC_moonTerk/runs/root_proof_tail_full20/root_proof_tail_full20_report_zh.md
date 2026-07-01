# Root Proof-Tail Full20 Report

本报告覆盖 5/10/20/30 每个尺度各 20 个真实实例，只跑 B0 direct-DP 与 B1B seeded root-CG。

| scale | mode | runs | direct optimal | BPC node LP certified | incomplete | official root bound | mean wall | max wall |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | B0_pure_direct_dp | 20 | 20 | 0 | 0 | 0 | 0.005309 | 0.010848 |
| 5 | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 20 | 0.007318 | 0.013105 |
| 10 | B0_pure_direct_dp | 20 | 20 | 0 | 0 | 0 | 0.150652 | 0.338536 |
| 10 | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 20 | 0.199415 | 0.412064 |
| 20 | B0_pure_direct_dp | 20 | 20 | 0 | 0 | 0 | 13.29037 | 31.588598 |
| 20 | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 20 | 30.057448 | 42.321256 |
| 30 | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0 | 0.002087 | 0.003505 |
| 30 | B1B_seeded_root_CG | 20 | 0 | 0 | 20 | 0 | 2.8e-05 | 6.7e-05 |

- accepted_10_full20_b1b: True。
- accepted_20_full20_b1b: True。
- accepted_10_20_full20_b1b: True。
- redlines: {'root_bound_gt_B0_violation_count': 0, 'manual_rc_fail_count': 0, 'pricing_rc_fail_count': 0, 'proof_debt_unreleased_certified_count': 0}。
- elapsed_sec: 881.068068；max_rss_mb: 347.7。
- 30-scale 使用 max_direct_tasks=20 fail-closed；本报告不声称 30-scale BPC root closure。
