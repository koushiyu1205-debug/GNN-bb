# P0 V3 六规模全量冷启动复测

- 状态：`COMPLETE`
- 完成 / 计划：1 / 1
- exact：1
- legal incomplete：0
- resource-censored incomplete：0
- unsafe failure：0
- 全部 exact：`True`

| scale | 完成 | exact | legal inc | censored | unsafe | mean s | p50 s | max s | peak RSS GiB |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 0 | 0 | 0 | 1.604405 | 1.604405 | 1.604405 | 0.005119 |

50/100 的 legal incomplete 或 resource-censored incomplete 只表示安全地没有给出 exact 证书，不能解释为最优解或完整 BPC closure。
所有实例均从实例 JSON 冷启动；不使用 checkpoint、外部列池、人工列或 GAT guidance。
