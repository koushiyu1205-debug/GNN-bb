# 5-Task Ablation No-GNN Baseline Run

## Inputs

- Manifest: `BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks5_ablation_20260610/manifest.json`
- Validation JSON: `BPC_future/results/20260610_tasks5_ablation_instance_validation.json`
- Results CSV: `BPC_future/results/20260610_tasks5_ablation_no_gnn_baseline.csv`
- Run log: `BPC_future/results/20260610_tasks5_ablation_no_gnn_baseline_run.log`
- Config base: `BPC_future/configs/moon_trek_5_journey.yaml`
- Explicit no-GNN overrides: `journey_learning_enabled=False`, `journey_learning_required=False`, `journey_learning_fail_hard=False`, `journey_learning_force_light_profile_pricing=False`, `journey_learning_prewarm_enabled=False`, `journey_learning_pricing_enabled=False`.
- Time limit per instance: `60s`.

## Instance Validation

- Issue count: `0`
- Instances: `60`; attempts retained: `140`; skipped attempts retained: `80`
- By mode: `{'greedy-anchor': 20, 'random-wave': 20, 'sector-wave': 20}`
- By terrain: `{'apollo15_20km': 30, 'tranquillitatis_balmer_like_20km': 30}`
- Time pair feasible ratio: `{'count': 60, 'max': 1.0, 'mean': 0.745, 'median': 0.7, 'min': 0.4}`
- Time triple feasible ratio: `{'count': 60, 'max': 0.8, 'mean': 0.488333, 'median': 0.5, 'min': 0.1}`
- Energy pair feasible ratio: `{'count': 60, 'max': 0.9, 'mean': 0.686667, 'median': 0.7, 'min': 0.5}`
- Energy triple feasible ratio: `{'count': 60, 'max': 0.5, 'mean': 0.248333, 'median': 0.2, 'min': 0.2}`
- Window width / horizon median distribution: `{'count': 60, 'max': 0.362256, 'mean': 0.308673, 'median': 0.306918, 'min': 0.25712}`
- Multi-path spread / window width median distribution: `{'count': 60, 'max': 0.54538, 'mean': 0.125517, 'median': 0.108978, 'min': 0.049486}`

## Solver Summary

- Status counts: `{'OPTIMAL': 60}`
- Solving time: `n=60, mean=0.321, med=0.297, p90=0.374, max=0.854` seconds; total solver-reported time `19.264s`.
- Node counts: `n=60, mean=1.067, med=1.000, p90=1.000, max=3.000`
- Slowest instance: `apollo15_20km_random-wave_randomtw_tasks005_03_seed1046207` at `0.854s`.
- Largest tree: `apollo15_20km_random-wave_randomtw_tasks005_03_seed1046207` with `3` nodes.
- No learning/GNN log events were found under the run log directory.

## By Mode

| mode | n | mean time | median time | max time | mean nodes | max nodes | mean pricing | mean exact pricing | mean columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| greedy-anchor | 20 | 0.331 | 0.320 | 0.435 | 1.00 | 1 | 4.90 | 3.90 | 20.6 |
| random-wave | 20 | 0.310 | 0.270 | 0.854 | 1.10 | 3 | 4.40 | 3.30 | 14.1 |
| sector-wave | 20 | 0.323 | 0.308 | 0.816 | 1.10 | 3 | 4.45 | 3.35 | 14.8 |

## By Terrain And Mode

| terrain | mode | statuses | mean time | median time | max time | mean nodes | max nodes | mean pricing | mean exact pricing | mean columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | OPTIMAL:10 | 0.301 | 0.292 | 0.371 | 1.00 | 1 | 4.00 | 3.00 | 16.0 |
| apollo15_20km | random-wave | OPTIMAL:10 | 0.323 | 0.267 | 0.854 | 1.20 | 3 | 4.80 | 3.60 | 12.4 |
| apollo15_20km | sector-wave | OPTIMAL:10 | 0.291 | 0.300 | 0.362 | 1.00 | 1 | 4.10 | 3.10 | 13.2 |
| tranquillitatis_balmer_like_20km | greedy-anchor | OPTIMAL:10 | 0.361 | 0.363 | 0.435 | 1.00 | 1 | 5.80 | 4.80 | 25.3 |
| tranquillitatis_balmer_like_20km | random-wave | OPTIMAL:10 | 0.296 | 0.291 | 0.338 | 1.00 | 1 | 4.00 | 3.00 | 15.8 |
| tranquillitatis_balmer_like_20km | sector-wave | OPTIMAL:10 | 0.354 | 0.315 | 0.816 | 1.20 | 3 | 4.80 | 3.60 | 16.4 |

## Per Instance

| terrain | mode | # | status | time | objective | nodes | pricing | exact pricing | columns | instance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 1 | OPTIMAL | 0.281 | 231.639865 | 1 | 4 | 3 | 10 | apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001 |
| apollo15_20km | greedy-anchor | 2 | OPTIMAL | 0.343 | 235.981733 | 1 | 4 | 3 | 9 | apollo15_20km_greedy-anchor_randomtw_tasks005_02_seed46105 |
| apollo15_20km | greedy-anchor | 3 | OPTIMAL | 0.281 | 186.21093 | 1 | 4 | 3 | 17 | apollo15_20km_greedy-anchor_randomtw_tasks005_03_seed46207 |
| apollo15_20km | greedy-anchor | 4 | OPTIMAL | 0.312 | 240.541971 | 1 | 4 | 3 | 17 | apollo15_20km_greedy-anchor_randomtw_tasks005_04_seed46311 |
| apollo15_20km | greedy-anchor | 5 | OPTIMAL | 0.313 | 175.269952 | 1 | 4 | 3 | 19 | apollo15_20km_greedy-anchor_randomtw_tasks005_05_seed46416 |
| apollo15_20km | greedy-anchor | 6 | OPTIMAL | 0.371 | 191.835132 | 1 | 4 | 3 | 23 | apollo15_20km_greedy-anchor_randomtw_tasks005_06_seed46518 |
| apollo15_20km | greedy-anchor | 7 | OPTIMAL | 0.289 | 246.539479 | 1 | 4 | 3 | 11 | apollo15_20km_greedy-anchor_randomtw_tasks005_07_seed46620 |
| apollo15_20km | greedy-anchor | 8 | OPTIMAL | 0.263 | 164.910019 | 1 | 4 | 3 | 17 | apollo15_20km_greedy-anchor_randomtw_tasks005_08_seed46722 |
| apollo15_20km | greedy-anchor | 9 | OPTIMAL | 0.264 | 169.826072 | 1 | 4 | 3 | 19 | apollo15_20km_greedy-anchor_randomtw_tasks005_09_seed46826 |
| apollo15_20km | greedy-anchor | 10 | OPTIMAL | 0.295 | 179.196252 | 1 | 4 | 3 | 18 | apollo15_20km_greedy-anchor_randomtw_tasks005_10_seed46930 |
| apollo15_20km | random-wave | 1 | OPTIMAL | 0.269 | 226.153022 | 1 | 4 | 3 | 11 | apollo15_20km_random-wave_randomtw_tasks005_01_seed1046000 |
| apollo15_20km | random-wave | 2 | OPTIMAL | 0.267 | 219.050616 | 1 | 4 | 3 | 12 | apollo15_20km_random-wave_randomtw_tasks005_02_seed1046102 |
| apollo15_20km | random-wave | 3 | OPTIMAL | 0.854 | 231.991886 | 3 | 12 | 9 | 14 | apollo15_20km_random-wave_randomtw_tasks005_03_seed1046207 |
| apollo15_20km | random-wave | 4 | OPTIMAL | 0.266 | 196.37468 | 1 | 4 | 3 | 12 | apollo15_20km_random-wave_randomtw_tasks005_04_seed1046309 |
| apollo15_20km | random-wave | 5 | OPTIMAL | 0.246 | 201.973312 | 1 | 4 | 3 | 14 | apollo15_20km_random-wave_randomtw_tasks005_05_seed1046411 |
| apollo15_20km | random-wave | 6 | OPTIMAL | 0.248 | 198.177189 | 1 | 4 | 3 | 13 | apollo15_20km_random-wave_randomtw_tasks005_06_seed1046513 |
| apollo15_20km | random-wave | 7 | OPTIMAL | 0.287 | 253.687115 | 1 | 4 | 3 | 12 | apollo15_20km_random-wave_randomtw_tasks005_07_seed1046615 |
| apollo15_20km | random-wave | 8 | OPTIMAL | 0.253 | 233.511909 | 1 | 4 | 3 | 11 | apollo15_20km_random-wave_randomtw_tasks005_08_seed1046717 |
| apollo15_20km | random-wave | 9 | OPTIMAL | 0.261 | 230.26826 | 1 | 4 | 3 | 11 | apollo15_20km_random-wave_randomtw_tasks005_09_seed1046819 |
| apollo15_20km | random-wave | 10 | OPTIMAL | 0.277 | 181.163329 | 1 | 4 | 3 | 14 | apollo15_20km_random-wave_randomtw_tasks005_10_seed1046922 |
| apollo15_20km | sector-wave | 1 | OPTIMAL | 0.347 | 284.084294 | 1 | 4 | 3 | 14 | apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000 |
| apollo15_20km | sector-wave | 2 | OPTIMAL | 0.362 | 173.960361 | 1 | 5 | 4 | 21 | apollo15_20km_sector-wave_randomtw_tasks005_02_seed2046103 |
| apollo15_20km | sector-wave | 3 | OPTIMAL | 0.299 | 259.070722 | 1 | 4 | 3 | 15 | apollo15_20km_sector-wave_randomtw_tasks005_03_seed2046206 |
| apollo15_20km | sector-wave | 4 | OPTIMAL | 0.301 | 167.416806 | 1 | 4 | 3 | 13 | apollo15_20km_sector-wave_randomtw_tasks005_04_seed2046312 |
| apollo15_20km | sector-wave | 5 | OPTIMAL | 0.240 | 236.961278 | 1 | 4 | 3 | 12 | apollo15_20km_sector-wave_randomtw_tasks005_05_seed2046414 |
| apollo15_20km | sector-wave | 6 | OPTIMAL | 0.323 | 225.189414 | 1 | 4 | 3 | 14 | apollo15_20km_sector-wave_randomtw_tasks005_06_seed2046516 |
| apollo15_20km | sector-wave | 7 | OPTIMAL | 0.221 | 335.423792 | 1 | 4 | 3 | 7 | apollo15_20km_sector-wave_randomtw_tasks005_07_seed2046618 |
| apollo15_20km | sector-wave | 8 | OPTIMAL | 0.240 | 209.790544 | 1 | 4 | 3 | 12 | apollo15_20km_sector-wave_randomtw_tasks005_08_seed2046720 |
| apollo15_20km | sector-wave | 9 | OPTIMAL | 0.240 | 219.456184 | 1 | 4 | 3 | 10 | apollo15_20km_sector-wave_randomtw_tasks005_09_seed2046822 |
| apollo15_20km | sector-wave | 10 | OPTIMAL | 0.334 | 238.788735 | 1 | 4 | 3 | 14 | apollo15_20km_sector-wave_randomtw_tasks005_10_seed2046925 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 1 | OPTIMAL | 0.402 | 174.654601 | 1 | 6 | 5 | 30 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 2 | OPTIMAL | 0.423 | 186.931792 | 1 | 11 | 10 | 28 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_02_seed146110 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 3 | OPTIMAL | 0.435 | 180.626947 | 1 | 6 | 5 | 30 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_03_seed146214 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 4 | OPTIMAL | 0.415 | 164.12496 | 1 | 6 | 5 | 28 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_04_seed146322 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 5 | OPTIMAL | 0.362 | 168.411028 | 1 | 6 | 5 | 26 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_05_seed146425 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 6 | OPTIMAL | 0.328 | 175.851659 | 1 | 4 | 3 | 26 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_06_seed146533 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 7 | OPTIMAL | 0.245 | 183.198927 | 1 | 4 | 3 | 20 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_07_seed146638 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 8 | OPTIMAL | 0.335 | 185.192702 | 1 | 6 | 5 | 24 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_08_seed146740 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 9 | OPTIMAL | 0.364 | 182.335251 | 1 | 5 | 4 | 21 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_09_seed146853 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10 | OPTIMAL | 0.301 | 181.431003 | 1 | 4 | 3 | 20 | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_10_seed146959 |
| tranquillitatis_balmer_like_20km | random-wave | 1 | OPTIMAL | 0.262 | 175.839086 | 1 | 4 | 3 | 13 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_01_seed1146000 |
| tranquillitatis_balmer_like_20km | random-wave | 2 | OPTIMAL | 0.292 | 165.679787 | 1 | 4 | 3 | 18 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_02_seed1146102 |
| tranquillitatis_balmer_like_20km | random-wave | 3 | OPTIMAL | 0.338 | 174.767157 | 1 | 4 | 3 | 18 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_03_seed1146204 |
| tranquillitatis_balmer_like_20km | random-wave | 4 | OPTIMAL | 0.326 | 179.989769 | 1 | 4 | 3 | 17 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_04_seed1146306 |
| tranquillitatis_balmer_like_20km | random-wave | 5 | OPTIMAL | 0.327 | 229.295366 | 1 | 4 | 3 | 15 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_05_seed1146408 |
| tranquillitatis_balmer_like_20km | random-wave | 6 | OPTIMAL | 0.260 | 225.323211 | 1 | 4 | 3 | 13 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_06_seed1146510 |
| tranquillitatis_balmer_like_20km | random-wave | 7 | OPTIMAL | 0.289 | 164.730564 | 1 | 4 | 3 | 19 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_07_seed1146612 |
| tranquillitatis_balmer_like_20km | random-wave | 8 | OPTIMAL | 0.265 | 227.991573 | 1 | 4 | 3 | 13 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_08_seed1146714 |
| tranquillitatis_balmer_like_20km | random-wave | 9 | OPTIMAL | 0.271 | 228.816202 | 1 | 4 | 3 | 12 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_09_seed1146816 |
| tranquillitatis_balmer_like_20km | random-wave | 10 | OPTIMAL | 0.330 | 166.077981 | 1 | 4 | 3 | 20 | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_10_seed1146918 |
| tranquillitatis_balmer_like_20km | sector-wave | 1 | OPTIMAL | 0.337 | 179.982081 | 1 | 4 | 3 | 18 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011 |
| tranquillitatis_balmer_like_20km | sector-wave | 2 | OPTIMAL | 0.278 | 170.433147 | 1 | 4 | 3 | 17 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_02_seed2146113 |
| tranquillitatis_balmer_like_20km | sector-wave | 3 | OPTIMAL | 0.330 | 171.850456 | 1 | 4 | 3 | 23 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_03_seed2146215 |
| tranquillitatis_balmer_like_20km | sector-wave | 4 | OPTIMAL | 0.316 | 167.166392 | 1 | 4 | 3 | 16 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_04_seed2146317 |
| tranquillitatis_balmer_like_20km | sector-wave | 5 | OPTIMAL | 0.263 | 179.189428 | 1 | 4 | 3 | 13 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_05_seed2146420 |
| tranquillitatis_balmer_like_20km | sector-wave | 6 | OPTIMAL | 0.286 | 181.647154 | 1 | 4 | 3 | 13 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_06_seed2146522 |
| tranquillitatis_balmer_like_20km | sector-wave | 7 | OPTIMAL | 0.314 | 188.912037 | 1 | 4 | 3 | 15 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_07_seed2146624 |
| tranquillitatis_balmer_like_20km | sector-wave | 8 | OPTIMAL | 0.816 | 227.481205 | 3 | 12 | 9 | 14 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_08_seed2146729 |
| tranquillitatis_balmer_like_20km | sector-wave | 9 | OPTIMAL | 0.279 | 175.361126 | 1 | 4 | 3 | 17 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_09_seed2146831 |
| tranquillitatis_balmer_like_20km | sector-wave | 10 | OPTIMAL | 0.324 | 173.991131 | 1 | 4 | 3 | 18 | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_10_seed2146934 |

## Assessment

- The generated 5-task benchmark is solver-compatible: all instances load through `load_future_data`, all graph tensors load through `FutureGraphBuilder`, all single-task timed checks pass, and full directed pair graphs are retained.
- The no-GNN baseline is far below the 5-task target: all 60 instances solved exactly in under 1 second each on this run.
- Two instances required 3 BPC nodes; all others solved at the root. The harder cases are still tiny at N=5, so this dataset scale is useful for correctness and distribution audit, not stress testing pricing.

