# Native SPPRC 六规模验收报告

- model: `NATIVE_SPPRC_ACCEPTANCE_V1`
- cold_start: `True`
- baseline_commit: `d05b9a4168ddcc5f5bb11070310d4c5d599153b3`
- config_hash: `04470ec33577bff85ea0ecbce7473e42efac46884bb063e89bcbc14bd959259c`
- engine_build_hashes: `{'native_rcspp_bidirectional_midpoint_partial_hybrid_v2': 'c116ed790031db21'}`
- missing_scales: `[]`
- acceptance: `{'all_available_profile_gates_pass': True, 'scale30_full20_exact': True, 'scale30_all_under_1800': False, 'scale30_p50_le_900': True, 'scale30_stretch_p50_le_600': True, 'scale30_phase11_release_gate': True}`

| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 5 | native_rcspp_bidirectional_midpoint_partial_hybrid_v2 | 20 | 20 | 3600.0 | 0.446199 | 0.492369 | True | EXACT_CLOSED | 10.014009 |
| 10 | native_rcspp_bidirectional_midpoint_partial_hybrid_v2 | 20 | 20 | 3600.0 | 0.926785 | 3.160527 | True | EXACT_CLOSED | 24.963079 |
| 20 | native_rcspp_bidirectional_midpoint_partial_hybrid_v2 | 20 | 20 | 3600.0 | 6.371578 | 93.203409 | True | EXACT_CLOSED | 404.030582 |
| 30 | native_rcspp_bidirectional_midpoint_partial_hybrid_v2 | 20 | 20 | 3600.0 | 51.922957 | 408.580573 | True | EXACT_CLOSED | 1876.888661 |

`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。
`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。
`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。
native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。
任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。
