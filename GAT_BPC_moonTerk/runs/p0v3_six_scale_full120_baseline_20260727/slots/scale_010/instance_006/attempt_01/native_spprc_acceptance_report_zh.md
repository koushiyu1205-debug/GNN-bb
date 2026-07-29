# Native SPPRC 六规模验收报告

- model: `NATIVE_SPPRC_ACCEPTANCE_V1`
- cold_start: `True`
- baseline_commit: `339304ca3f749ba2f6832ee4c5679255e30efdbd`
- config_hash: `9523de66a1b71578f831660465167e60f6dd6bd51541a9229a0ccf6900f2fa0f`
- engine_build_hashes: `{'native_rcspp_inprocess': 'aeb042c95c69704b'}`
- missing_scales: `[]`
- acceptance: `{'all_available_profile_gates_pass': True, 'scale30_full20_exact': False, 'scale30_all_under_1800': False, 'scale30_p50_le_900': False, 'scale30_stretch_p50_le_600': False, 'scale30_phase11_release_gate': False}`

| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 10 | native_rcspp_inprocess | 1 | 1 | 3600.0 | 1.062584 | 1.062584 | True | EXACT_CLOSED | 1.171086 |

`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。
`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。
`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。
native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。
任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。
