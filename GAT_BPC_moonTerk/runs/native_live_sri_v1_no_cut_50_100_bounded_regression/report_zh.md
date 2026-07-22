# Native Live SRI V1：50/100 bounded no-cut 安全回归

日期：2026-07-22  
结论：2/2 通过本计划定义的安全回归；0/2 exact，2/2 合法 incomplete。

共同配置：Native host backend、单实例串行、600 秒上限、8 GiB effective memory limit、strict cold-start、no resume、`live_sri_policy=no_cut`、`cut_count=0`、`cut_state_effective=false`。

| 规模 | 实例 | cold-start | 状态 | redline | hash | no-cheat |
|---:|---|---:|---|---:|---|---|
| 50 | instance_001 | 1.862652s | `BPC_INCOMPLETE_PRICING` | 0 | valid | true |
| 100 | instance_001 | 6.704785s | `BPC_INCOMPLETE_PRICING` | 0 | valid | true |

两例均为 `INCOMPLETE_LIMIT`，没有把未完成 pricing 错写成 exact；`certificate_leak=0`、`pricing_rc_fail=0`、`manual_rc_fail=0`，未使用 resume、external probe、mature pool 或 manual columns。start/child/end engine binding 一致。

acceptance 外层脚本因其通用门禁要求 exact 而返回非零，但本专项门禁明文允许 exact 或合法 incomplete，所以 bounded regression 判定为通过。该结论不属于 Live SRI performance promotion，也不证明 50/100 exact closure。
