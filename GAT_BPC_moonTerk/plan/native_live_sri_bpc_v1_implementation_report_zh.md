# Native Live SRI Branch-Price-and-Cut V1 实施报告

日期：2026-07-23  
结论：功能与证书闭环已实现；正式 paired promotion 已完成但 P0 未晋级；默认仍为 `no_cut`

## 1. 最终决策

本轮完成了冻结 no-cut 基线、SRI-3/SRI-5 separator、active-cut Phase-I、Native compact cut state、逐列 RC 审计、三类 hash、cut lineage、P0/P1/P2 节点循环、1040-slot 正式 paired promotion 和 50/100 安全回归。正式 promotion 结束后，又实现了只向 pricing 投影精确非零 dual cuts，以及 SRI-3 2-bit/SRI-5 3-bit 的精确 overlap 压缩；这两项属于下一候选的性能改进，不反向改写旧 promotion 结论。

没有切换默认主线。正式 P0 重复的 1040/1040 slots 全部 exact、目标值一致、零 redline、证书和 engine binding 合法；5/10/20 通过各自门槛，但 30 规模只通过 p50，未通过 mean、paired point estimate 和 paired 95% CI 上界。因此总状态是 `NOT_PROMOTED`，`default_switch_allowed=false`。这是一项性能否决，不是正确性否决。

## 2. Stage -1 冻结基线

冻结对象：`FROZEN_NATIVE_NO_CUT_BASELINE_V1`。

- git commit：`ee2f853c003589cb717399209fe232dc793a854b`；
- engine hash：`66ab52c9b33b4551`；
- frozen config SHA-256：`beef1cf0c5f20fffff35fb87c06826926f2d15fc62294237d7ba5007af9a9f1a`；
- 5/10/20/30 各 20 例，80/80 exact、80/80 no-cheat、80/80 objective closure、零 redline、无 engine 漂移；
- 所有历史恢复容差门禁通过。

| 规模 | fresh mean | fresh p50 | 历史比值 mean | 历史比值 p50 |
|---:|---:|---:|---:|---:|
| 5 | 0.395952s | 0.393683s | 0.9745 | 0.9684 |
| 10 | 0.820660s | 0.754397s | 0.9900 | 0.9902 |
| 20 | 32.352003s | 18.391300s | 1.0379 | 1.0421 |
| 30 | 493.045466s | 346.038290s | 1.0862 | 1.0563 |

正式证据位于 `runs/native_spprc_no_cut_5_30_full3600_frozen_v1/`。后续 promotion 的 control 必须重新 fresh 运行，不得复用这里的 wall-clock。

## 3. 代码交付

### 3.1 数学、context 与 lineage

- `exact/core/cuts.py`：canonical SRI、数学去重、active-context hash、lineage hash、true-dual hash、V1 capability validator；
- `exact/bpc/cuts/live_sri.py`：P0/P1/P2 策略、完整枚举、bitmask/popcount、top-cap heap、activation 和 telemetry；
- violation epsilon 固定 `1e-6`，global/local/active cap 固定 4/4/8，Native hard cap 16。

### 3.2 Phase-I、master 与 pricing

- Phase-I 在相同 branch+cut context 下建模；真实 journey objective=0；cover/fleet/cut dual 全进入 RC；
- artificial cover variables 对当前 SRI 的系数为 0；
- 每条 Native 返回列均执行 Python manual reconstruction，并记录 objective/cover/fleet/cut 分项；
- active cuts 下 completion bound 强制关闭；任何 incomplete frontier、label drop、hash/schema mismatch 均禁止签发 proof。

### 3.3 Native engine

- 正式 promotion 当时的 cut state 为 `uint8_t[16] + active_count`；
- 当前实现将每条 SRI-3 的精确 overlap 0..3 编码为 2 bit、SRI-5 的 0..5 编码为 3 bit，16 条 SRI-5 最多占 48 bit，统一内联到一个 `uint64_t`；
- dominance 仍比较完整精确 overlap state，不采用 reward-only 或 parity shortcut；
- 支持 divisor=2 的 SRI-3/SRI-5 threshold crossing；
- 17 cuts、未知 cut type/divisor、未知 task 或 capability mismatch 均 fail closed；
- request-binding echo 覆盖 objective、RMP iteration、branch/cut/lineage/policy/dual/schema/count/epsilon。

正式 promotion 冻结 binary/runtime：

- in-process engine hash：`dfaedf6d273c5c56`；
- 当时 host engine hash：`bddc7afddc232ceb`；
- `.so` SHA-256：`6608e051cfb17b309d67bb0dc9f672296ea4639f99427c33ce7d979355389a1f`；
- source/config/test diff SHA-256：`83964d7093387c9dbcdb0cf948c18ff6e3304d813b5b5b57b2643dcafa4a84fc`。

正式重复结束后先修复了 host IPC 对 signed zero dual 的保真问题，随后实现了非零-dual pricing projection、packed exact overlap state 和 Native binary state-schema fail-closed guard。当前 in-process engine hash 为 `8e255a88436e937c`，`.so` SHA-256 为 `6e37eeeee287395c294548afab35ff8093ffe18e941453c926feee6a3e9a3e4c`。

历史 1040-slot 结果仍严格绑定正式 engine `dfaedf6d273c5c56`。当前 engine 只完成了正确性门禁、定价重放和一个 scale20 端到端诊断对照，不能用旧结果声称新候选已晋级。

### 3.4 树节点循环

- P0：root SRI-3；
- P1：root SRI-3+SRI-5；
- P2：root SRI-3+SRI-5，branch node SRI-3；
- global inheritance、local descendant inheritance、sibling isolation 均落地；
- proposed cuts 先经过 `min_restricted_rmp_gain=1e-4` 的性能筛选。筛选失败时回退到已认证节点，且该筛选值不进入 official certificate。

## 4. Readiness 与 pilot 证据

冻结基线共提取并只读诊断 316 个 snapshot：

- scale20 root：9/20 有 violated SRI，最大 violation 0.500000001；
- scale30 root：15/20 有 violated SRI，最大 violation 0.5；
- 196 个 fractional branch snapshots 中 196/196 有 SRI-3 signal；
- P2 启动信号 gate 通过，但这只证明“存在违反”，不证明 node cuts 更快。

P0/P1 初始 scale20 三难例筛选均 exact、零 redline，并明显快于各自冻结单次基线。P0 三例为 13.679/12.766/14.977 秒；P1 为 12.926/12.454/16.423 秒。由于 P0 family 更小、三例总体略快，选择 P0 作为唯一后续候选。

P2 在 20_012 上验证了 4 global + 4 local、不同 sibling 的 local cuts 不串扰、后代继承正确；该受限 pilot 因 node limit 未形成整树 exact，故 P2 明确保留为 capability，默认关闭。

## 5. P0 筛选与正式 promotion

筛选阶段加入 restricted-RMP gain gate 后：

- 20_009：gain=0.035442，提交 4 条 SRI-3，终局完整分离无剩余 violated SRI；12.863606 秒 exact、零 redline；冻结单次为 17.251374 秒；
- 30_017：gain=0.000081，小于 0.0001，proposed cuts 被拒绝并回退到 no-cut；152.040423 秒 exact、零 redline；冻结单次为 165.922252 秒；比值约 0.916；
- 5_001：0.387791 秒，对冻结 0.372190 秒为 +4.19%；
- 10_001：0.676047 秒，对冻结 0.655835 秒为 +3.08%。

上述结果只用于选择唯一候选 P0，不进入 promotion 统计。之后冻结 policy/config/engine hash，并完成正式 AB/BA fresh paired promotion：

| 规模 | live/base mean | live/base p50 | paired point estimate | paired 95% CI | correctness | promotion |
|---:|---:|---:|---:|---|---|---|
| 5 | 1.003516 | 0.999396 | 1.003480 | [0.996809, 1.009628] | pass | pass |
| 10 | 0.981068 | 0.958215 | 0.979668 | [0.951791, 0.999489] | pass | pass |
| 20 | 0.805249 | 0.793010 | 0.864355 | [0.771307, 0.951162] | pass | pass |
| 30 | 1.087746 | 0.835094 | 0.959039 | [0.824718, 1.103403] | pass | **fail** |

30 规模失败项：

- mean 必须不高于 no-cut，实际为 `1.087746`；
- paired point estimate 必须不高于 `0.90`，实际为 `0.959039`；
- paired 95% CI 上界必须小于 `1.00`，实际为 `1.103403`。

正式 evidence 位于 `runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/`。最终决策由 `promotion_decision_manifest.json` 冻结。

## 6. 50/100 bounded no-cut regression

两例均使用 host backend、8 GiB effective limit、600 秒上限、新进程、no resume、`live_sri_policy=no_cut`。

第一次运行暴露 `native_dual_binding_hash_mismatch`：host IPC 把合法的 fleet dual `-0.0` 通过 `value or 0.0` 改成 `+0.0`。二者数学相等，但 canonical hash 区分 signed zero，所以 child 正确 fail closed。修复改为保留 present value，没有删除或放宽 hash 检查，并增加集成回归测试。

修复后两例真正进入 Native exact labeling，均在 8 GiB 限制上合法 incomplete：

| 规模 | 实例 | wall time | 状态 | 唯一 blocker | peak host RSS | redline |
|---:|---|---:|---|---:|---|---|
| 50 | instance_001 | 340.135371s | `BPC_INCOMPLETE_PRICING` | `host_memory_limit` | 8.0028 GiB | 0 |
| 100 | instance_001 | 300.159294s | `BPC_INCOMPLETE_PRICING` | `host_memory_limit` | 8.0006 GiB | 0 |

两例都满足：`search_exhaustive=false`、`frontier_empty=false`、`labels_dropped=false`，所以没有伪造 exact/no-negative proof；engine start/child/end hash 一致，`certificate_leak=0`、`pricing_rc_fail=0`、`manual_rc_fail=0`，未 resume，无 external/mature/manual columns，cut state 关闭且 active cut count 为 0。合并证据位于 `runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_v2_signed_zero_fix_20260723/`。

## 7. 测试门禁

- signed-zero host 定向回归：2 passed；
- 全量 pytest：414 passed，22 subtests passed；
- `tests/native`：39 passed，17 subtests passed；
- normal Native CTest：2/2 passed；
- ASAN+UBSAN Native CTest：2/2 passed；
- graph-cache 序列 `no-cut -> A -> A+B -> B -> no-cut` 通过；
- active cut count 0/1/8/16 通过，17 fail closed；
- stale binding、lineage/sibling、SRI validity/enumeration/ID/dedup、Native/Python RC audit 均有回归测试。

## 8. Promotion 状态

`scripts/run_live_sri_paired_promotion.py` 实际完成了严格 fresh subprocess、AB/BA、5/10 每实例每模式十次、20/30 每实例每模式三次、per-instance median、paired ratio、geometric mean 和 paired bootstrap 95% CI：

- expected/completed slots：1040/1040；
- solver resume：false；
- fresh Python/native runtime：true；
- correctness：1040/1040；
- engine hash：1040/1040 为 `dfaedf6d273c5c56`；
- `pricing_rc_fail`、`manual_rc_fail`、`certificate_leak` 总和均为 0；
- 总状态：`NOT_PROMOTED`。

冻结 reference objective 只有六位小数。原 harness 使用 `1e-8` 导致 scale20 instance010 的三条 live rows 被审计层误拒；三条差值都恰为 `1e-6`，1040/1040 全部在 `1e-6` 内。只把审计容差改为 `1e-6` 并从原始 rows 重汇总，solver/config/native 未变、solver slot 重跑数为 0；原 summary/report 已另存，amendment 与 post-amendment audit 均保留。

## 9. 当前推荐状态

```text
production default: no_cut
formal live candidate: P0, NOT_PROMOTED, experimental only
P1: implemented, not selected, default off
P2: implemented/tested node-cut capability, default off
50/100: no_cut only
formal paired promotion: completed 1040/1040, not passed
```

当前不应切换默认值，也不应按规模拆分默认策略。若继续研究 live cuts，优先解释 30_009、30_012、30_018—020 的树规模/定价退化，并重新形成新候选；旧 P0 结果不能通过重复汇总方式变成 promoted。用户提出的“pricing 只携带非零 dual cuts”和更紧凑 overlap state 是 exact-safe 的下一轮性能方向；放宽 cut-aware dominance 必须先给出完整证明，V1 仍保留保守完整 active-prefix 比较。

## 10. 2026-07-23 定价状态优化补充

### 10.1 精确非零-dual projection

RMP、primal feasibility、lineage 和完整 active-cut context 保持不变。Native pricing 只接收 dual 数值严格满足 `value != 0.0` 的 cuts；`+0.0` 与 `-0.0` 都投影掉，任何微小但非零的 dual（例如 `-1e-15`）都保留，不使用 epsilon。

证书同时绑定：

- 完整 `active_cut_context_hash` 与 active cut count；
- 实际 pricing `pricing_cut_context_hash` 与 pricing cut count；
- 完整 `true_dual_binding_hash`；
- projection enable flag 和 projection schema。

因此 dual 从零变为非零、full/projected context 任一变化或 binding echo 不一致，旧证书都会 fail closed。完整 active count=17 仍在投影前 fail closed，不能靠零 dual 绕过 Native capability。

### 10.2 2/3-bit 精确 overlap

压缩前 `CutState=17 bytes`、完整 `State=168 bytes`；压缩后分别为 8 和 152 bytes，降幅 52.9% 和 9.5%。编码保存完整 overlap，不保存有歧义的 `floor(overlap/2)`。状态布局 schema 已升为 `lunar_ice_bpc.native_cut_state.packed_exact_sri3_2bit_sri5_3bit_u64.v2`，旧 schema 证书自动失效。

scale20 instance009 的两个真实 root dual snapshots（一个负列轮、一个终局无负列轮）进行了 graph-cache-off、AB/BA、每模式每 snapshot 10 次的重放：

| 模式 | 压缩前 mean | 压缩后 mean | 压缩后/前 | labels mean |
|---|---:|---:|---:|---:|
| full active cuts | 0.567062s | 0.549063s | 0.9683 | 5,845,987 |
| nonzero projected cuts | 0.331303s | 0.321275s | 0.9697 | 3,568,258.5 |

投影本身在压缩后将 mean 从 0.549063s 降到 0.321275s，约快 41.5%；扩展 labels 减少约 39.0%。加入最终 binary-schema guard 后，用当前 hash `8e255a88436e937c` 再跑相同重放，full/projected mean 分别为 0.540599s/0.316356s，比例 0.585196，结论不变。所有配对的 global best/no-negative proof、穷尽状态、frontier、blocker 和逐列 RC audit 一致，`rc_mismatch_count=0`。负列 harvest surface 可因 exact subset dominance 合法省略不同的次优 dominated columns，因此不把“所有返回负列集合完全相同”误当成证书条件。

同一新 engine 上又做了一对不进入 promotion 统计的 strict cold-start scale20 instance009 端到端诊断：

| 模式 | total | root CG | tree | objective | 状态 |
|---|---:|---:|---:|---:|---|
| no-cut | 15.951197s | 7.725982s | 7.875293s | 1.893717 | exact/零 redline |
| P0 optimized | 11.883917s | 7.718583s | 3.826938s | 1.893717 | exact/零 redline |

单对比 P0/no-cut total ratio 为 0.7450，但这只是一例各一次的诊断结果。新 engine 尚未完成新的 frozen paired promotion，因此 production default 仍是 `no_cut`。

证据目录：`runs/native_live_sri_v1_state_optimizations_20260723/`。
