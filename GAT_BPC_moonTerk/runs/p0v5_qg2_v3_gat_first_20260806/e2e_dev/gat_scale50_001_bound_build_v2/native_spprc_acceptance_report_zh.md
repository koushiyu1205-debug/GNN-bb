# Native SPPRC 六规模验收报告

- model: `NATIVE_SPPRC_ACCEPTANCE_V1`
- cold_start: `True`
- baseline_commit: `5453fbcdab4cd5febfea745fdb0a23b91af92c61`
- config_hash: `96ef769d43ffb7baf946765f9370905807aa453435b030bb32ebbfbd60121d3f`
- engine_build_hashes: `{'native_rcspp_bidirectional_root_partial_hybrid_v3': 'e69335fd88f14a9b'}`
- missing_scales: `[]`
- acceptance: `{'all_available_profile_gates_pass': True, 'scale30_full20_exact': False, 'scale30_all_under_1800': False, 'scale30_p50_le_900': False, 'scale30_stretch_p50_le_600': False, 'scale30_phase11_release_gate': False}`

| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 50 | native_rcspp_bidirectional_root_partial_hybrid_v3 | 1 | 1 | 3600.0 | 430.269228 | 430.269228 | True | EXACT_CLOSED | 430.550155 |

`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。
`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。
`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。
native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。
任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。
