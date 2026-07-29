# P0 V3 六规模全量冷启动复测

- 状态：`INCOMPLETE`
- 完成 / 计划：81 / 120
- exact：80
- legal incomplete：0
- resource-censored incomplete：0
- memory-censored incomplete：1
- unsafe failure：0
- 全部 exact：`False`

| scale | 完成 | exact | legal inc | resource censored | memory censored | unsafe | mean s | p50 s | max s | peak RSS GiB |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 20 | 20 | 0 | 0 | 0 | 0 | 0.479243 | 0.479737 | 0.530257 | 0.005032 |
| 10 | 20 | 20 | 0 | 0 | 0 | 0 | 1.567372 | 1.074785 | 5.454645 | 0.005432 |
| 20 | 20 | 20 | 0 | 0 | 0 | 0 | 38.974689 | 18.032615 | 190.537035 | 1.287945 |
| 30 | 20 | 20 | 0 | 0 | 0 | 0 | 197.313479 | 79.579199 | 1157.471105 | 3.074051 |
| 50 | 1 | 0 | 0 | 0 | 1 | 0 | 710.849528 | 710.849528 | 710.849528 | 8.858261 |
| 100 | 0 | 0 | 0 | 0 | 0 | 0 |  |  |  | 0.000000 |

50/100 的 legal、resource-censored 或 memory-censored incomplete只表示
安全地没有给出exact证书，不能解释为最优解或完整BPC closure。
memory-censored不能计为正式3600秒time-limit完成行。
所有实例均从实例 JSON 冷启动；不使用 checkpoint、外部列池、人工列或 GAT guidance。

scale50/001 在 8 GiB Native 内存上限返回 `MEMORY_LIMIT`，仅作为当前
15.5 GiB 主机的内存墙诊断。其后 scale50/100 正式队列已暂停，停止原因
为 `PAUSED_INSUFFICIENT_LARGE_SCALE_MEMORY`；不得把该诊断行解释为可与
大内存环境下 3600 秒 time-limit 实验比较的正式性能结果。

执行束说明：Recovered 5-30 rows may carry the earlier harness bundle; the frozen native binary and config are unchanged. The later bundle only separates the host emergency RSS watchdog from the native cooperative memory limit for scale 50/100.
