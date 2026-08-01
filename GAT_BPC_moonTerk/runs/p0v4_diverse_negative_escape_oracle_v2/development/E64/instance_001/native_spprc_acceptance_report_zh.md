# Native SPPRC 六规模验收报告

- model: `NATIVE_SPPRC_ACCEPTANCE_V1`
- cold_start: `True`
- baseline_commit: `d05b9a4168ddcc5f5bb11070310d4c5d599153b3`
- config_hash: `eeca68bd3095283b83b0a389dcb9f20dc0f46f684bb47efcf3235c38cf4509bb`
- engine_build_hashes: `{'native_rcspp_host': '7e479055e3bc1dcb'}`
- missing_scales: `[]`
- acceptance: `{'all_available_profile_gates_pass': False, 'scale30_full20_exact': False, 'scale30_all_under_1800': False, 'scale30_p50_le_900': False, 'scale30_stretch_p50_le_600': False, 'scale30_phase11_release_gate': False}`

| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 50 | native_rcspp_host | 1 | 0 | 3600.0 | 3592.311472 | 3592.311472 | True | FAIL_CLOSED | 3592.419896 |

`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。
`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。
`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。
native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。
任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。
