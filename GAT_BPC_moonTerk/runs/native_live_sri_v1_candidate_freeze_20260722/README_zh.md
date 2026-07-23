# P0 screened candidate 冻结说明

这里冻结的是 P0 候选，不是已晋级 release。正式 fresh paired promotion 已于
2026-07-23 完成并判定为 `NOT_PROMOTED`；本目录继续作为历史候选冻结包保留，不改写
其 frozen hashes。

- policy hash：`9f0e7c4f7e2cab50267e197d55a17950aeee35aad388e47448f24873a7e92ba1`；
- config SHA-256：`a928c1c5dfe83b35b77f483ff2dd6268966e3b8999321e1afb74aea0a6d1c13d`；
- in-process engine：`dfaedf6d273c5c56`；
- host engine：`bddc7afddc232ceb`；
- 当前生产默认：`no_cut`。

正式 promotion 共完成 1040/1040 slots，所有正确性门禁通过；5/10/20 规模通过性能门禁，
但 30 规模的 mean、paired point estimate 和 paired 95% CI 上界未通过。因此
`default_switch_allowed=false`，5/10/20/30 仍统一使用 `no_cut`，不得按规模拆分切换。

最终决策证据：

```text
runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/
  promotion_summary.json
  promotion_post_amendment_audit.json
  promotion_decision_manifest.json
```
