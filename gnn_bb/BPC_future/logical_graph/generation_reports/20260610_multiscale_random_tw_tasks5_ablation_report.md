# 5-Task Multiscale Random-TW Ablation Generation Report

Generated on 2026-06-10 from `generate_moon_trek_multiscale_random_tw_benchmark.py`.

## Scope

- Manifest: `BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks5_ablation_20260610/manifest.json`
- Raw generation log: `BPC_future/results/generate_multiscale_random_tw_tasks5_ablation_20260610.log`
- Output root: `BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks5_ablation_20260610`
- Scale generated: `task_count=5` only.
- Time-window ablation modes: `greedy-anchor`, `random-wave`, `sector-wave`.
- Accepted instances: `60`; attempts retained in manifest: `140`; skipped attempts: `80`.
- Official benchmark graph pruning: disabled. Full directed logical graphs and full GNN tensors are retained.
- Monte Carlo / finite-sample audit intervals are generation-screening diagnostics only; they are not solver proof or certificate logic.

## Overall By Mode

| mode | accepted/attempts | acceptance | skips | pair feasible med[min,max] | triple feasible med[min,max] | energy pair med[min,max] | energy triple med[min,max] | window/horizon med[min,max] | spread/window med[min,max] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| greedy-anchor | 20/73 | 0.274 | 53 | 0.700 [0.500,0.900] | 0.700 [0.200,0.800] | 0.600 [0.500,0.900] | 0.200 [0.200,0.500] | 0.296 [0.257,0.333] | 0.114 [0.050,0.545] |
| random-wave | 20/24 | 0.833 | 4 | 0.800 [0.400,1.000] | 0.300 [0.100,0.800] | 0.700 [0.600,0.900] | 0.200 [0.200,0.400] | 0.325 [0.276,0.358] | 0.089 [0.059,0.159] |
| sector-wave | 20/43 | 0.465 | 23 | 0.800 [0.500,1.000] | 0.400 [0.100,0.700] | 0.700 [0.500,0.900] | 0.200 [0.200,0.400] | 0.306 [0.273,0.362] | 0.118 [0.049,0.328] |

## By Terrain And Mode

| terrain | mode | accepted/attempts | acceptance | skips | pair feasible | triple feasible | energy pair | energy triple | window/horizon | spread/window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/22 | 0.455 | 12 | 0.700 [0.500,0.900] | 0.550 [0.200,0.700] | 0.600 [0.500,0.900] | 0.200 [0.200,0.500] | 0.289 [0.266,0.329] | 0.134 [0.050,0.545] |
| apollo15_20km | random-wave | 10/14 | 0.714 | 4 | 0.650 [0.400,1.000] | 0.200 [0.100,0.500] | 0.700 [0.600,0.900] | 0.250 [0.200,0.400] | 0.333 [0.276,0.358] | 0.078 [0.060,0.159] |
| apollo15_20km | sector-wave | 10/17 | 0.588 | 7 | 0.650 [0.500,1.000] | 0.350 [0.100,0.700] | 0.650 [0.500,0.800] | 0.200 [0.200,0.400] | 0.311 [0.273,0.362] | 0.156 [0.049,0.328] |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/51 | 0.196 | 41 | 0.700 [0.600,0.800] | 0.800 [0.600,0.800] | 0.600 [0.500,0.800] | 0.200 [0.200,0.400] | 0.302 [0.257,0.333] | 0.114 [0.063,0.168] |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 1.000 | 0 | 0.900 [0.700,0.900] | 0.600 [0.300,0.800] | 0.700 [0.600,0.900] | 0.200 [0.200,0.300] | 0.311 [0.285,0.353] | 0.094 [0.059,0.132] |
| tranquillitatis_balmer_like_20km | sector-wave | 10/26 | 0.385 | 16 | 0.900 [0.700,1.000] | 0.550 [0.200,0.700] | 0.750 [0.600,0.900] | 0.200 [0.200,0.400] | 0.295 [0.277,0.358] | 0.100 [0.070,0.150] |

## Skip Reasons

| terrain | mode | skip reason counts |
| --- | --- | --- |
| apollo15_20km | greedy-anchor | time triple density out of band: 8; no balanced energy cap found: 2; single task roundtrip infeasible after cap selection: 1; single task seed feasibility failed: 1 |
| apollo15_20km | random-wave | time triple density out of band: 2; single task seed feasibility failed: 1; single task roundtrip infeasible after cap selection: 1 |
| apollo15_20km | sector-wave | time triple density out of band: 3; no balanced energy cap found: 2; time pair density out of band: 1; single task roundtrip infeasible after cap selection: 1 |
| tranquillitatis_balmer_like_20km | greedy-anchor | time triple density out of band: 38; no balanced energy cap found: 2; single task seed feasibility failed: 1 |
| tranquillitatis_balmer_like_20km | sector-wave | time triple density out of band: 14; no balanced energy cap found: 2 |

## Distribution Notes

### greedy-anchor

- pair feasible ratio: n=20, mean=0.690, med=0.700, p25=0.675, p75=0.700, min=0.500, max=0.900
- triple feasible ratio: n=20, mean=0.635, med=0.700, p25=0.575, p75=0.800, min=0.200, max=0.800
- energy pair feasible ratio: n=20, mean=0.660, med=0.600, p25=0.600, p75=0.725, min=0.500, max=0.900
- energy triple feasible ratio: n=20, mean=0.245, med=0.200, p25=0.200, p75=0.225, min=0.200, max=0.500
- window_width / horizon: n=20, mean=0.298, med=0.296, p25=0.284, p75=0.318, min=0.257, max=0.333
- multi_path_spread / window_width: n=20, mean=0.146, med=0.114, p25=0.083, p75=0.159, min=0.050, max=0.545

### random-wave

- pair feasible ratio: n=20, mean=0.755, med=0.800, p25=0.675, p75=0.900, min=0.400, max=1.000
- triple feasible ratio: n=20, mean=0.395, med=0.300, p25=0.200, p75=0.600, min=0.100, max=0.800
- energy pair feasible ratio: n=20, mean=0.700, med=0.700, p25=0.600, p75=0.800, min=0.600, max=0.900
- energy triple feasible ratio: n=20, mean=0.250, med=0.200, p25=0.200, p75=0.300, min=0.200, max=0.400
- window_width / horizon: n=20, mean=0.321, med=0.325, p25=0.304, p75=0.335, min=0.276, max=0.358
- multi_path_spread / window_width: n=20, mean=0.093, med=0.089, p25=0.067, p75=0.109, min=0.059, max=0.159

### sector-wave

- pair feasible ratio: n=20, mean=0.790, med=0.800, p25=0.675, p75=0.900, min=0.500, max=1.000
- triple feasible ratio: n=20, mean=0.435, med=0.400, p25=0.300, p75=0.625, min=0.100, max=0.700
- energy pair feasible ratio: n=20, mean=0.700, med=0.700, p25=0.600, p75=0.800, min=0.500, max=0.900
- energy triple feasible ratio: n=20, mean=0.250, med=0.200, p25=0.200, p75=0.300, min=0.200, max=0.400
- window_width / horizon: n=20, mean=0.307, med=0.306, p25=0.287, p75=0.319, min=0.273, max=0.362
- multi_path_spread / window_width: n=20, mean=0.138, med=0.118, p25=0.083, p75=0.155, min=0.049, max=0.328

## Per-Instance Results

| terrain | mode | # | seed | energy cap | pair | pair Wilson95 | triple | triple Wilson95 | energy pair | energy triple | win/horizon med | spread/win med | tensor shape | instance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 1 | 46001 | 59.399 | 0.500 | 0.237-0.763 | 0.200 | 0.057-0.510 | 0.600 | 0.200 | 0.329 | 0.159 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001 |
| apollo15_20km | greedy-anchor | 2 | 46105 | 54.663 | 0.900 | 0.596-0.982 | 0.300 | 0.108-0.603 | 0.500 | 0.200 | 0.317 | 0.113 | x=[6, 9], edge=[2, 30], opt=[86, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_02_seed46105 |
| apollo15_20km | greedy-anchor | 3 | 46207 | 51.213 | 0.700 | 0.397-0.892 | 0.600 | 0.313-0.832 | 0.600 | 0.200 | 0.320 | 0.110 | x=[6, 9], edge=[2, 30], opt=[82, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_03_seed46207 |
| apollo15_20km | greedy-anchor | 4 | 46311 | 47.718 | 0.600 | 0.313-0.832 | 0.600 | 0.313-0.832 | 0.800 | 0.500 | 0.266 | 0.050 | x=[6, 9], edge=[2, 30], opt=[84, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_04_seed46311 |
| apollo15_20km | greedy-anchor | 5 | 46416 | 54.173 | 0.700 | 0.397-0.892 | 0.500 | 0.237-0.763 | 0.900 | 0.400 | 0.288 | 0.080 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_05_seed46416 |
| apollo15_20km | greedy-anchor | 6 | 46518 | 43.064 | 0.700 | 0.397-0.892 | 0.700 | 0.397-0.892 | 0.600 | 0.200 | 0.324 | 0.244 | x=[6, 9], edge=[2, 30], opt=[86, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_06_seed46518 |
| apollo15_20km | greedy-anchor | 7 | 46620 | 57.236 | 0.700 | 0.397-0.892 | 0.400 | 0.168-0.687 | 0.500 | 0.200 | 0.291 | 0.155 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_07_seed46620 |
| apollo15_20km | greedy-anchor | 8 | 46722 | 54.215 | 0.600 | 0.313-0.832 | 0.500 | 0.237-0.763 | 0.900 | 0.300 | 0.275 | 0.272 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_08_seed46722 |
| apollo15_20km | greedy-anchor | 9 | 46826 | 44.966 | 0.600 | 0.313-0.832 | 0.600 | 0.313-0.832 | 0.600 | 0.200 | 0.284 | 0.545 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_09_seed46826 |
| apollo15_20km | greedy-anchor | 10 | 46930 | 56.255 | 0.800 | 0.490-0.943 | 0.700 | 0.397-0.892 | 0.900 | 0.300 | 0.268 | 0.084 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_greedy-anchor_randomtw_tasks005_10_seed46930 |
| apollo15_20km | random-wave | 1 | 1046000 | 68.059 | 0.500 | 0.237-0.763 | 0.100 | 0.018-0.404 | 0.900 | 0.400 | 0.334 | 0.067 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_random-wave_randomtw_tasks005_01_seed1046000 |
| apollo15_20km | random-wave | 2 | 1046102 | 53.690 | 0.500 | 0.237-0.763 | 0.200 | 0.057-0.510 | 0.600 | 0.400 | 0.332 | 0.060 | x=[6, 9], edge=[2, 30], opt=[86, 10] | apollo15_20km_random-wave_randomtw_tasks005_02_seed1046102 |
| apollo15_20km | random-wave | 3 | 1046207 | 45.376 | 0.900 | 0.596-0.982 | 0.300 | 0.108-0.603 | 0.700 | 0.200 | 0.325 | 0.060 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_random-wave_randomtw_tasks005_03_seed1046207 |
| apollo15_20km | random-wave | 4 | 1046309 | 53.961 | 0.700 | 0.397-0.892 | 0.100 | 0.018-0.404 | 0.600 | 0.200 | 0.358 | 0.067 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_random-wave_randomtw_tasks005_04_seed1046309 |
| apollo15_20km | random-wave | 5 | 1046411 | 37.209 | 1.000 | 0.722-1.000 | 0.500 | 0.237-0.763 | 0.600 | 0.300 | 0.329 | 0.065 | x=[6, 9], edge=[2, 30], opt=[86, 10] | apollo15_20km_random-wave_randomtw_tasks005_05_seed1046411 |
| apollo15_20km | random-wave | 6 | 1046513 | 45.713 | 0.700 | 0.397-0.892 | 0.200 | 0.057-0.510 | 0.600 | 0.200 | 0.310 | 0.108 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_random-wave_randomtw_tasks005_06_seed1046513 |
| apollo15_20km | random-wave | 7 | 1046615 | 59.439 | 0.400 | 0.168-0.687 | 0.200 | 0.057-0.510 | 0.700 | 0.400 | 0.276 | 0.159 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_random-wave_randomtw_tasks005_07_seed1046615 |
| apollo15_20km | random-wave | 8 | 1046717 | 50.620 | 0.500 | 0.237-0.763 | 0.100 | 0.018-0.404 | 0.700 | 0.200 | 0.347 | 0.135 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_random-wave_randomtw_tasks005_08_seed1046717 |
| apollo15_20km | random-wave | 9 | 1046819 | 49.172 | 0.600 | 0.313-0.832 | 0.200 | 0.057-0.510 | 0.700 | 0.200 | 0.333 | 0.096 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_random-wave_randomtw_tasks005_09_seed1046819 |
| apollo15_20km | random-wave | 10 | 1046922 | 46.080 | 0.800 | 0.490-0.943 | 0.300 | 0.108-0.603 | 0.800 | 0.300 | 0.339 | 0.090 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_random-wave_randomtw_tasks005_10_seed1046922 |
| apollo15_20km | sector-wave | 1 | 2046000 | 69.486 | 0.500 | 0.237-0.763 | 0.300 | 0.108-0.603 | 0.600 | 0.400 | 0.319 | 0.254 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000 |
| apollo15_20km | sector-wave | 2 | 2046103 | 42.603 | 0.900 | 0.596-0.982 | 0.700 | 0.397-0.892 | 0.600 | 0.200 | 0.315 | 0.049 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_sector-wave_randomtw_tasks005_02_seed2046103 |
| apollo15_20km | sector-wave | 3 | 2046206 | 47.766 | 0.600 | 0.313-0.832 | 0.300 | 0.108-0.603 | 0.700 | 0.300 | 0.303 | 0.085 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_sector-wave_randomtw_tasks005_03_seed2046206 |
| apollo15_20km | sector-wave | 4 | 2046312 | 48.221 | 1.000 | 0.722-1.000 | 0.400 | 0.168-0.687 | 0.800 | 0.200 | 0.288 | 0.328 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_sector-wave_randomtw_tasks005_04_seed2046312 |
| apollo15_20km | sector-wave | 5 | 2046414 | 57.454 | 0.600 | 0.313-0.832 | 0.100 | 0.018-0.404 | 0.800 | 0.400 | 0.308 | 0.176 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_sector-wave_randomtw_tasks005_05_seed2046414 |
| apollo15_20km | sector-wave | 6 | 2046516 | 40.861 | 0.900 | 0.596-0.982 | 0.500 | 0.237-0.763 | 0.700 | 0.200 | 0.314 | 0.079 | x=[6, 9], edge=[2, 30], opt=[88, 10] | apollo15_20km_sector-wave_randomtw_tasks005_06_seed2046516 |
| apollo15_20km | sector-wave | 7 | 2046618 | 45.166 | 0.700 | 0.397-0.892 | 0.400 | 0.168-0.687 | 0.600 | 0.200 | 0.327 | 0.155 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_sector-wave_randomtw_tasks005_07_seed2046618 |
| apollo15_20km | sector-wave | 8 | 2046720 | 43.361 | 0.600 | 0.313-0.832 | 0.300 | 0.108-0.603 | 0.500 | 0.200 | 0.273 | 0.318 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_sector-wave_randomtw_tasks005_08_seed2046720 |
| apollo15_20km | sector-wave | 9 | 2046822 | 46.801 | 0.700 | 0.397-0.892 | 0.100 | 0.018-0.404 | 0.700 | 0.200 | 0.309 | 0.136 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_sector-wave_randomtw_tasks005_09_seed2046822 |
| apollo15_20km | sector-wave | 10 | 2046925 | 55.794 | 0.600 | 0.313-0.832 | 0.400 | 0.168-0.687 | 0.600 | 0.400 | 0.362 | 0.156 | x=[6, 9], edge=[2, 30], opt=[90, 10] | apollo15_20km_sector-wave_randomtw_tasks005_10_seed2046925 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 1 | 146007 | 32.451 | 0.700 | 0.397-0.892 | 0.800 | 0.490-0.943 | 0.700 | 0.200 | 0.306 | 0.076 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 2 | 146110 | 30.066 | 0.700 | 0.397-0.892 | 0.800 | 0.490-0.943 | 0.600 | 0.200 | 0.332 | 0.063 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_02_seed146110 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 3 | 146214 | 28.789 | 0.700 | 0.397-0.892 | 0.800 | 0.490-0.943 | 0.600 | 0.200 | 0.333 | 0.089 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_03_seed146214 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 4 | 146322 | 52.235 | 0.700 | 0.397-0.892 | 0.800 | 0.490-0.943 | 0.800 | 0.400 | 0.290 | 0.159 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_04_seed146322 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 5 | 146425 | 37.651 | 0.700 | 0.397-0.892 | 0.700 | 0.397-0.892 | 0.700 | 0.200 | 0.301 | 0.114 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_05_seed146425 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 6 | 146533 | 33.241 | 0.700 | 0.397-0.892 | 0.800 | 0.490-0.943 | 0.700 | 0.200 | 0.281 | 0.132 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_06_seed146533 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 7 | 146638 | 33.970 | 0.800 | 0.490-0.943 | 0.800 | 0.490-0.943 | 0.600 | 0.200 | 0.257 | 0.114 | x=[6, 9], edge=[2, 30], opt=[88, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_07_seed146638 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 8 | 146740 | 31.688 | 0.700 | 0.397-0.892 | 0.700 | 0.397-0.892 | 0.500 | 0.200 | 0.289 | 0.069 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_08_seed146740 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 9 | 146853 | 43.590 | 0.700 | 0.397-0.892 | 0.800 | 0.490-0.943 | 0.600 | 0.200 | 0.305 | 0.116 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_09_seed146853 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10 | 146959 | 46.297 | 0.600 | 0.313-0.832 | 0.600 | 0.313-0.832 | 0.500 | 0.200 | 0.304 | 0.168 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_10_seed146959 |
| tranquillitatis_balmer_like_20km | random-wave | 1 | 1146000 | 36.695 | 0.900 | 0.596-0.982 | 0.800 | 0.490-0.943 | 0.700 | 0.200 | 0.353 | 0.089 | x=[6, 9], edge=[2, 30], opt=[88, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_01_seed1146000 |
| tranquillitatis_balmer_like_20km | random-wave | 2 | 1146102 | 40.130 | 0.900 | 0.596-0.982 | 0.600 | 0.313-0.832 | 0.800 | 0.200 | 0.342 | 0.101 | x=[6, 9], edge=[2, 30], opt=[88, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_02_seed1146102 |
| tranquillitatis_balmer_like_20km | random-wave | 3 | 1146204 | 31.789 | 0.900 | 0.596-0.982 | 0.600 | 0.313-0.832 | 0.600 | 0.200 | 0.285 | 0.059 | x=[6, 9], edge=[2, 30], opt=[88, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_03_seed1146204 |
| tranquillitatis_balmer_like_20km | random-wave | 4 | 1146306 | 28.738 | 0.900 | 0.596-0.982 | 0.800 | 0.490-0.943 | 0.600 | 0.200 | 0.324 | 0.071 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_04_seed1146306 |
| tranquillitatis_balmer_like_20km | random-wave | 5 | 1146408 | 30.537 | 0.900 | 0.596-0.982 | 0.600 | 0.313-0.832 | 0.800 | 0.200 | 0.295 | 0.099 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_05_seed1146408 |
| tranquillitatis_balmer_like_20km | random-wave | 6 | 1146510 | 39.252 | 0.700 | 0.397-0.892 | 0.300 | 0.108-0.603 | 0.900 | 0.200 | 0.318 | 0.114 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_06_seed1146510 |
| tranquillitatis_balmer_like_20km | random-wave | 7 | 1146612 | 32.752 | 0.900 | 0.596-0.982 | 0.600 | 0.313-0.832 | 0.700 | 0.300 | 0.296 | 0.089 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_07_seed1146612 |
| tranquillitatis_balmer_like_20km | random-wave | 8 | 1146714 | 36.776 | 0.800 | 0.490-0.943 | 0.300 | 0.108-0.603 | 0.600 | 0.200 | 0.305 | 0.116 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_08_seed1146714 |
| tranquillitatis_balmer_like_20km | random-wave | 9 | 1146816 | 39.899 | 0.700 | 0.397-0.892 | 0.400 | 0.168-0.687 | 0.600 | 0.200 | 0.316 | 0.085 | x=[6, 9], edge=[2, 30], opt=[86, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_09_seed1146816 |
| tranquillitatis_balmer_like_20km | random-wave | 10 | 1146918 | 38.823 | 0.900 | 0.596-0.982 | 0.700 | 0.397-0.892 | 0.800 | 0.300 | 0.302 | 0.132 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_10_seed1146918 |
| tranquillitatis_balmer_like_20km | sector-wave | 1 | 2146011 | 39.825 | 1.000 | 0.722-1.000 | 0.700 | 0.397-0.892 | 0.600 | 0.200 | 0.284 | 0.114 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011 |
| tranquillitatis_balmer_like_20km | sector-wave | 2 | 2146113 | 35.290 | 0.900 | 0.596-0.982 | 0.700 | 0.397-0.892 | 0.900 | 0.400 | 0.285 | 0.070 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_02_seed2146113 |
| tranquillitatis_balmer_like_20km | sector-wave | 3 | 2146215 | 37.358 | 0.800 | 0.490-0.943 | 0.700 | 0.397-0.892 | 0.800 | 0.200 | 0.303 | 0.088 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_03_seed2146215 |
| tranquillitatis_balmer_like_20km | sector-wave | 4 | 2146317 | 45.779 | 0.700 | 0.397-0.892 | 0.400 | 0.168-0.687 | 0.900 | 0.200 | 0.325 | 0.121 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_04_seed2146317 |
| tranquillitatis_balmer_like_20km | sector-wave | 5 | 2146420 | 44.107 | 0.900 | 0.596-0.982 | 0.300 | 0.108-0.603 | 0.800 | 0.200 | 0.298 | 0.150 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_05_seed2146420 |
| tranquillitatis_balmer_like_20km | sector-wave | 6 | 2146522 | 36.598 | 0.900 | 0.596-0.982 | 0.400 | 0.168-0.687 | 0.600 | 0.200 | 0.320 | 0.077 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_06_seed2146522 |
| tranquillitatis_balmer_like_20km | sector-wave | 7 | 2146624 | 47.023 | 0.800 | 0.490-0.943 | 0.500 | 0.237-0.763 | 0.700 | 0.200 | 0.292 | 0.124 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_07_seed2146624 |
| tranquillitatis_balmer_like_20km | sector-wave | 8 | 2146729 | 43.424 | 0.900 | 0.596-0.982 | 0.200 | 0.057-0.510 | 0.700 | 0.200 | 0.283 | 0.079 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_08_seed2146729 |
| tranquillitatis_balmer_like_20km | sector-wave | 9 | 2146831 | 30.837 | 0.800 | 0.490-0.943 | 0.600 | 0.313-0.832 | 0.600 | 0.200 | 0.277 | 0.113 | x=[6, 9], edge=[2, 30], opt=[88, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_09_seed2146831 |
| tranquillitatis_balmer_like_20km | sector-wave | 10 | 2146934 | 41.758 | 1.000 | 0.722-1.000 | 0.700 | 0.397-0.892 | 0.800 | 0.300 | 0.358 | 0.084 | x=[6, 9], edge=[2, 30], opt=[90, 10] | tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_10_seed2146934 |

## Interpretation

- `random-wave` accepted fastest in this 5-task run: 20 accepted from 24 attempts. It is not tied to greedy-route structure, so it is a useful ablation control.
- `greedy-anchor` is the hardest to accept on the tranquillittatis terrain: 10 accepted from 51 attempts. Most rejections are energy density too loose or time triple density too loose; this should be discussed rather than hidden.
- `sector-wave` sits between the two: it preserves spatial-temporal structure without using a greedy route, but still rejects loose energy/time samples on the second terrain.
- The accepted 5-task instances keep full directed pair graphs: every tensor has `x=[6, 9]`, `pair_edge_index=[2, 30]`; option counts vary because physical multi-path options differ by terrain/sample.
- `window_width / horizon` medians are mostly around 0.27-0.33, while `multi_path_spread / window_width` medians stay below 0.60 in this run. That means smart jitter leaves legal room for path-option substitution without making windows all-day loose.

