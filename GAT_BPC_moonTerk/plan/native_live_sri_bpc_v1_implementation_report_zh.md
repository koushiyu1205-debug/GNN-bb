# Native Live SRI Branch-Price-and-Cut V1 实施报告

日期：2026-07-22  
结论：功能与证书闭环已实现；P0 冻结为 screened candidate；默认仍为 `no_cut`

## 1. 最终决策

本轮完成了冻结 no-cut 基线、SRI-3/SRI-5 separator、active-cut Phase-I、Native compact cut state、逐列 RC 审计、三类 hash、cut lineage、P0/P1/P2 节点循环、paired-promotion runner 和 50/100 安全回归。

没有切换默认主线。原因不是正确性失败，而是正式晋级证据尚不成立：当前 P0 只有筛选级样本，30_017 的最终门控版本相对冻结单次基线比值约为 0.916，尚未达到 0.90 门槛，更没有 20 个实例、3 次重复和 paired bootstrap 95% CI。

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

- cut state 改为 `uint8_t[16] + active_count`；
- dominance 比较完整 active prefix；
- 支持 divisor=2 的 SRI-3/SRI-5 threshold crossing；
- 17 cuts、未知 cut type/divisor、未知 task 或 capability mismatch 均 fail closed；
- request-binding echo 覆盖 objective、RMP iteration、branch/cut/lineage/policy/dual/schema/count/epsilon。

当前开发 binary：

- in-process engine hash：`dfaedf6d273c5c56`；
- host engine hash：`bddc7afddc232ceb`；
- `.so` SHA-256：`6608e051cfb17b309d67bb0dc9f672296ea4639f99427c33ce7d979355389a1f`；
- source/config/test diff SHA-256：`83964d7093387c9dbcdb0cf948c18ff6e3304d813b5b5b57b2643dcafa4a84fc`。

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

## 5. 最终 P0 性能筛选

加入 restricted-RMP gain gate 后：

- 20_009：gain=0.035442，提交 4 条 SRI-3，终局完整分离无剩余 violated SRI；12.863606 秒 exact、零 redline；冻结单次为 17.251374 秒；
- 30_017：gain=0.000081，小于 0.0001，proposed cuts 被拒绝并回退到 no-cut；152.040423 秒 exact、零 redline；冻结单次为 165.922252 秒；比值约 0.916；
- 5_001：0.387791 秒，对冻结 0.372190 秒为 +4.19%；
- 10_001：0.676047 秒，对冻结 0.655835 秒为 +3.08%。

小规模单例均在 5% do-no-harm 范围内，但它们不是 20 实例、10 次重复的正式结果。30_017 也未达到正式 0.90 点估计门槛。因此当前只能给出“P0 值得继续重复”的结论，不能给出“P0 已晋级”。

## 6. 50/100 bounded no-cut regression

两例均使用 host backend、8 GiB effective limit、600 秒上限、新进程、no resume、`live_sri_policy=no_cut`。二者都快速返回合法 incomplete，而非伪造 exact：

| 规模 | 实例 | cold time | 状态 | redline | engine binding | no-cheat |
|---:|---|---:|---|---:|---|---|
| 50 | instance_001 | 1.862652s | `BPC_INCOMPLETE_PRICING` | 0 | valid | true |
| 100 | instance_001 | 6.704785s | `BPC_INCOMPLETE_PRICING` | 0 | valid | true |

两例 `certificate_leak=0`、`pricing_rc_fail=0`、`manual_rc_fail=0`、未 resume、无 external/mature/manual columns。运行后系统可用内存约 12 GiB、swap 仍仅约 12 MiB，无异常增长。

## 7. 测试门禁

- 全量 pytest：406 passed，21 subtests passed；
- normal Native CTest：2/2 passed；
- ASAN+UBSAN Native CTest：2/2 passed；
- graph-cache 序列 `no-cut -> A -> A+B -> B -> no-cut` 通过；
- active cut count 0/1/8/16 通过，17 fail closed；
- stale binding、lineage/sibling、SRI validity/enumeration/ID/dedup、Native/Python RC audit 均有回归测试。

## 8. Promotion 状态

`scripts/run_live_sri_paired_promotion.py` 已实现严格 fresh subprocess、AB/BA、5/10 十次、20/30 三次、per-instance median、paired ratio、geometric mean 和 paired bootstrap 95% CI；dry-run 已验证命令与冻结 hash 编排。

本轮没有把筛选数据伪装成 promotion，也没有启动高成本正式重复。当前候选先被标记为 `SCREENED_NOT_PROMOTION_ELIGIBLE`：30 单例尚未达到 0.90，且缺少全实例 paired evidence。只有未来正式结果同时通过计划中的所有 correctness/performance 门槛，才允许切换 5/10/20/30 默认值。

## 9. 当前推荐状态

```text
production default: no_cut
screened live candidate: P0
P1: implemented, not selected
P2: implemented/tested capability, default off
50/100: no_cut only
formal paired promotion: pending, not passed
```

下一步不应继续扩 cut family。若继续投入，应先对 P0 做更多 30-scale 独立筛选；只有稳定观察到超过 10% 的收益，再运行完整 paired promotion。否则冻结 no-cut 主线即可。
