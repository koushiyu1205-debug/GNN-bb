# Native SPPRC 六规模验收报告

- model: `NATIVE_SPPRC_ACCEPTANCE_V1`
- cold_start: `True`
- baseline_commit: `d05b9a4168ddcc5f5bb11070310d4c5d599153b3`
- config_hash: `52a5f452916c5243a6a6bf19697049b943453dae772a0aefffcfd9aa991b826c`
- engine_build_hashes: `{'native_rcspp_bidirectional_midpoint_hybrid_v1': 'ecfdcda3303cf69b'}`
- missing_scales: `[]`
- acceptance: `{'all_available_profile_gates_pass': True, 'scale30_full20_exact': True, 'scale30_all_under_1800': False, 'scale30_p50_le_900': True, 'scale30_stretch_p50_le_600': True, 'scale30_phase11_release_gate': True}`

| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 5 | native_rcspp_bidirectional_midpoint_hybrid_v1 | 20 | 20 | 3600.0 | 0.443059 | 0.49835 | True | EXACT_CLOSED | 9.513326 |
| 10 | native_rcspp_bidirectional_midpoint_hybrid_v1 | 20 | 20 | 3600.0 | 0.927679 | 3.209719 | True | EXACT_CLOSED | 24.989871 |
| 20 | native_rcspp_bidirectional_midpoint_hybrid_v1 | 20 | 20 | 3600.0 | 6.430759 | 94.013367 | True | EXACT_CLOSED | 407.121984 |
| 30 | native_rcspp_bidirectional_midpoint_hybrid_v1 | 20 | 20 | 3600.0 | 52.011789 | 371.001991 | True | EXACT_CLOSED | 1791.732775 |

`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。
`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。
`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。
native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。
任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。
