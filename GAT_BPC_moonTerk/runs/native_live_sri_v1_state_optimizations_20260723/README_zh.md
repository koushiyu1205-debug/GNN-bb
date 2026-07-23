# Native Live SRI V1 定价状态优化证据

日期：2026-07-23

本目录记录正式 P0 promotion 失败后实施的两个 exact-safe 优化：

1. 只向 Native pricing 投影 dual 数值严格非零的 active cuts；
2. SRI-3 2-bit、SRI-5 3-bit 的精确 overlap packed state。

`projection_pre_packing_scale20_009.json` 与
`projection_post_packing_scale20_009.json` 使用相同 scale20 instance009、两个真实 root
dual snapshots、graph cache 关闭、AB/BA 顺序和每模式每 snapshot 10 次重放。所有 exact
global-best/no-negative、frontier、blocker 和逐列 RC audit 门禁一致。

`projection_post_packing_schema_guard_scale20_009.json` 是加入 Native binary
state-schema fail-closed guard 后，使用最终代码/hash 的同负载复跑。

`end_to_end_schema_guard_scale20_009_no_cut/` 与
`end_to_end_schema_guard_scale20_009_p0/` 是最终代码各一次 strict cold-start、
no-resume 的端到端诊断。它们不属于正式 promotion 样本，不能用于切换默认策略。

机器可读汇总见 `state_optimization_summary.json`。production default 仍为 `no_cut`。
