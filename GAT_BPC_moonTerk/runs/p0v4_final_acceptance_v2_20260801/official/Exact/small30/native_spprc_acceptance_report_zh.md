# Native SPPRC 六规模验收报告

- model: `NATIVE_SPPRC_ACCEPTANCE_V1`
- cold_start: `True`
- baseline_commit: `d05b9a4168ddcc5f5bb11070310d4c5d599153b3`
- config_hash: `96ef769d43ffb7baf946765f9370905807aa453435b030bb32ebbfbd60121d3f`
- engine_build_hashes: `{'native_rcspp_bidirectional_root_partial_hybrid_v3': 'a3be48f74fb8ec8a'}`
- missing_scales: `[]`
- acceptance: `{'all_available_profile_gates_pass': True, 'scale30_full20_exact': True, 'scale30_all_under_1800': False, 'scale30_p50_le_900': True, 'scale30_stretch_p50_le_600': True, 'scale30_phase11_release_gate': True}`

| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 5 | native_rcspp_bidirectional_root_partial_hybrid_v3 | 20 | 20 | 3600.0 | 0.455156 | 0.516271 | True | EXACT_CLOSED | 9.902034 |
| 10 | native_rcspp_bidirectional_root_partial_hybrid_v3 | 20 | 20 | 3600.0 | 0.958221 | 3.159665 | True | EXACT_CLOSED | 24.795689 |
| 20 | native_rcspp_bidirectional_root_partial_hybrid_v3 | 20 | 20 | 3600.0 | 6.470019 | 98.014374 | True | EXACT_CLOSED | 396.714549 |
| 30 | native_rcspp_bidirectional_root_partial_hybrid_v3 | 20 | 20 | 3600.0 | 52.386023 | 260.425934 | True | EXACT_CLOSED | 1620.942656 |

`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。
`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。
`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。
native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。
任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。
