# Native Live SRI V1：50/100 bounded no-cut 安全回归

日期：2026-07-23  
总状态：`PASS_LEGAL_INCOMPLETE`

## 1. 结论

50 和 100 规模的 `instance_001` 均按冻结要求完成了独立、串行、cold-start、no-resume 的 host-backend 回归。两例都在 exact label frontier 达到 8 GiB host 内存限制时返回 `BPC_INCOMPLETE_PRICING`，属于计划明确允许的合法 incomplete：

- 没有签发 no-negative 或 exact 证书；
- `search_exhaustive=false` 且 `frontier_empty=false`；
- 唯一 certificate blocker 是 `host_memory_limit`；
- 零 redline、零证书泄漏、零 RC 审计失败；
- engine start/child/end hash 一致；
- 未发现 hash、resume 或 cache 错误；
- `live_sri_policy=no_cut`、Native cut state 关闭、`active_cut_count=0`；
- 未使用旧 checkpoint、mature pool、external probe 或 manual columns。

因此，本阶段证明的是“共享 Native/host 代码在 50/100 上安全 fail closed”，不是 50/100 exact closure 或性能晋级。

## 2. 正式结果

| 规模 | wall time | 终态 | 唯一 blocker | peak host RSS | redline | engine binding | cut state |
|---:|---:|---|---|---:|---:|---|---|
| 50 | 340.135371s | legal incomplete | `host_memory_limit` | 8.0028 GiB | 0 | valid | off / 0 cuts |
| 100 | 300.159294s | legal incomplete | `host_memory_limit` | 8.0006 GiB | 0 | valid | off / 0 cuts |

配置：

```text
config = configs/native_no_cut_50_100_bounded_regression_v1.yaml
config SHA-256 = e613b79b59edede0fbd6e53347b12523c3b95dded6b2b1dc1934179cc56265ee
backend = native_rcspp_host
host engine hash = d44cd21da6dae8c0
row limit = 600s
effective memory limit = 8 GiB
tree max nodes = 1
branch depth = 0
solver resume = false
```

## 3. signed-zero dual binding 缺陷与修复

第一次回归保留在：

```text
runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_20260723/
```

它暴露了真实的证书绑定缺陷：HiGHS 可以返回合法的 fleet dual `-0.0`，但 host IPC 重建使用 `dual_payload.get("fleet_limit") or 0.0`，把 present `-0.0` 改成了 `+0.0`。二者数学值相同，但 canonical JSON hash 保留 signed zero，因此 child 正确地返回：

```text
engine_status = HASH_MISMATCH
certificate_blockers = ["native_dual_binding_hash_mismatch"]
```

修复仅把读取改成带缺省值的 `get`，保留 present `-0.0`。没有删除、跳过或放宽 hash 检查。随后增加 host IPC 集成回归测试，并在新目录完整重跑 50/100。修复后两例的 dual-binding mismatch 都为 0，host 才真正进入 exact labeling，最终按 8 GiB 限制安全退出。

## 4. 证据目录

```text
runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_v2_signed_zero_fix_20260723/
  bounded_regression_summary.json
  bounded_regression_report_zh.md
  scale_050/
    native_spprc_acceptance_summary.json
    scale_050/pools/scale_050/instance_001/stage_001/probe.json
  scale_100/
    native_spprc_acceptance_summary.json
    scale_100/pools/scale_100/instance_001/stage_001/probe.json
```

