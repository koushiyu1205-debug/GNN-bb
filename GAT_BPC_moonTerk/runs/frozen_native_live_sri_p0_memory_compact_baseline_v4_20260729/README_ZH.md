# P0 V4 memory-compact 冻结基准

- freeze ID: `FROZEN_NATIVE_LIVE_SRI_P0_MEMORY_COMPACT_BASELINE_V4`
- 历史 control: `FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3`
- scale30: 20/20 exact，mean ratio `0.766377`，
  paired geometric mean ratio `0.763179`
- scale50/001: 3600 秒 `BPC_INCOMPLETE_PRICING`，安全 fail closed
- scale50 全量：按用户指示未运行
- scale5/10/20 V4 二进制：未重新跑正式全量
- scale100：未运行
- production 默认：`no_cut`，未切换

本目录冻结的是新的实验基准，不是六规模 promotion 证明。未来实验必须同时报告
上述未验证边界，不得把 scale50 的安全 timeout 写成 exact closure。
