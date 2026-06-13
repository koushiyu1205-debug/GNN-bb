# Sharded Pulse Phase 10I Negative-result Completion Audit 报告

日期：2026-06-13

## 目标

本轮不写新算法、不扩大 worker budget、不启用 official certificate gate。

目标是对 `目标.md` 的最终交付条件做一次完成性审计，特别是条件 B：

```text
证明当前 Pulse worker/proof 路线在安全约束下无 ROI：
- 连续两轮 A/B 无改善；
- worker 加列不降低 tail；
- refinement/resume 无降低 incomplete；
- 20-task 没明显改善；
则停止继续扩大 Pulse，输出 negative-result report 和建议转向 RMP stabilization / pool compression / legacy final judge optimization。
```

## 审计结论

当前证据已经足以停止继续扩大 `Pulse active hidden-negative worker / target-specific worker gate / early-column quota / profile-DP label-cap` 这些子路线。

但整个目标还不能标记为完成，原因是：

- `refinement` 已证明 exact-safe，但真实 driver/audit smoke 没证明 production incomplete 降低；
- `proof-closed resume` 仍未作为 Sharded Pulse proof route 实现和验证；
- 因此条件 B 中 `refinement/resume 无降低 incomplete` 仍是未完成审计项。

换句话说：

- active-worker 子路线：可以正式关闭；
- profile-DP / early-column quota 调参子路线：可以正式关闭；
- full Pulse proof-route negative result：还缺 proof-closed resume / full proof-route ROI 证据。

## 条件 B 审计表

| 条件 B 子项 | 当前状态 | 当前证据 | 判断 |
|---|---|---|---|
| 连续两轮 A/B 无改善 | 已满足，覆盖 active worker / profile-DP / early-column quota | Phase 7O/7P/7Z/7AG worker A/B；Phase 10B-10H profile-DP / early-column A/B | 支持停止对应子路线 |
| worker 加列不降低 tail | 已满足，覆盖 active worker 子路线 | Phase 7U-7AG residual attribution；worker 加 true-RC negative columns 后 residual ordinary/exact pricing tail 仍存在 | 支持停止 active worker |
| 20-task 没明显改善 | 已满足，覆盖当前候选 profiles | 7O/7P worker 无稳定 wall-time ROI；10B-10H label-cap / early quota 分裂且 incomplete tail 未下降 | 支持停止当前 Pulse 调参 |
| no critical disagreement / exactness | 已满足 | 多轮 summary 均 `critical_disagreement_count=0`；worker/certificate guard tests 通过；full tests 最新 `483 OK` | exactness 未发现 blocker |
| refinement 无降低 incomplete | 部分满足 | Phase 7J stress smoke 证明 refinement exactness 和 child certified 增加，但 global 仍 incomplete，driver smoke 未触发有效 refinement | 不足以完成 B |
| resume 无降低 incomplete | 未满足 | proof-closed resume 未作为 Sharded Pulse proof route 实现/验证；现有 archive 明确不是 proof-closed cache | B 仍缺口 |

## 已可正式关闭的路线

### 1. Active hidden-negative worker

证据来源：

- `20260613_sharded_pulse_worker_negative_result_synthesis_zh.md`
- `20260613_sharded_pulse_phase7ah_active_worker_closure_zh.md`
- Phase 7O / 7P / 7U-7AG result directories

结论：

- worker 能安全加入 true-RC negative columns；
- 但 5/10 no-regression 主要靠 gate 关闭 worker；
- worker 加列没有稳定减少 legacy final judge tail / completion retry / residual negative tail；
- target-specific priority 诊断能定位 `[8,15,5]` family，但没有转成 ROI；
- 不应继续增加 worker time limit、gate、target ordering 或默认启用。

### 2. Profile-DP cap / mask label-cap

证据来源：

- Phase 10B state-cap sensitivity；
- Phase 10C / 10D mask-hotspot sensitivity；
- Phase 10E ordering attribution；
- Phase 10F active-pool trajectory attribution；
- Phase 10G early-column attribution。

结论：

- state cap 提高没有稳定 ROI；
- mask label-cap 可改变 Apollo short-time trajectory，但不是 proof-tail optimization；
- label-cap16/32 不降低 incomplete tail；
- active-pool divergence 更像 early-column ordering effect；
- 不应继续扩大 label cap 或简单提高 DP cap。

### 3. Early-column new-task-set quota

证据来源：

- `20260613_sharded_pulse_phase10h_early_new_task_set_quota_zh.md`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_5_10_guard_20260613`

结论：

- 5/10 guard 通过，profiles 是 no-op；
- 20-task 轨迹确实被强烈改变；
- `tranq20_01` 稳定改善；
- `mt20_greedy_tranq_01` 对 quota 参数方向敏感；
- `mt20_greedy_apollo_01` 大多回退；
- incomplete tail 不下降；
- 不能默认启用，也不能作为 worker/certificate gate 的依据。

## 尚未完成的 B 条件缺口

### 1. Refinement

Phase 7J 已证明：

- second-action child partition exact-safe；
- parent `REFINED` 不当 proof-closed；
- child incomplete 阻断 certificate；
- child negative 正确传播；
- child cap 无法覆盖完整 partition 时不 refine。

但它没有证明：

- production driver/audit 中 refinement 能降低 `INCOMPLETE_LIMIT`；
- selected 20-task hard smoke 的 incomplete tail 被降低；
- refinement 触发后 wall time 或 proof-tail 指标有稳定改善。

### 2. Proof-closed resume

当前实现中：

- `StructuralKeyDominanceArchive` 只在单次 DFS 调用内剪枝；
- archive 不是 proof-closed cache；
- frontier snapshot 不能参与 certificate；
- Sharded Pulse proof-closed resume 没有作为 production proof route 实现；
- 因此没有证据证明 resume 对 incomplete tail 有 ROI，也没有证据证明它无 ROI。

这正是当前目标不能标记完成的原因。

## 对最终交付条件的判断

### 条件 A

未满足。

原因：

- 5/10 guard 可以通过，但主要靠 20-only/no-op gate；
- 20-task selected hard set 没有稳定 wall-time / gap / proof-tail 改善；
- early quota 和 label-cap 的改善方向分裂；
- Pulse worker 没有稳定减少 tail。

### 条件 B

尚未完全满足。

已满足：

- active-worker 连续 A/B 无稳定改善；
- worker 加列不降低 residual tail；
- 当前 20-task candidates 没有稳定改善；
- no critical disagreement。

未满足：

- proof-route 层面的 `refinement/resume 无降低 incomplete` 证据不完整；
- proof-closed resume 未实现/验证。

### 条件 C

未触发。

当前没有发现：

- critical disagreement；
- true-RC mismatch；
- forbidden / branch / cut context mismatch。

## 下一步建议

不要继续：

- Pulse active worker gate stacking；
- worker time-limit 扩大；
- target-specific ordering；
- profile-DP cap / mask label-cap 调参；
- early-column quota 调参；
- official certificate gate；
- production default enable。

下一步有两条可选路线：

1. 若目标是尽快满足最终条件 B：
   - 做一个极窄的 proof-route completion phase；
   - 要么实现并验证 proof-closed resume 的 no-ROI / no-incomplete-reduction；
   - 要么明确把 proof-closed resume 从当前候选路线中撤销，并给出工程理由与替代路径。

2. 若目标是继续追求条件 A：
   - 转向 `RMP stabilization / pool compression / legacy final judge proof-tail optimization`；
   - 不再从 Pulse worker / label-cap / early-column quota 主线扩展。

## Exactness 边界

本轮为报告/审计更新：

- 不改变 solver semantics；
- 不改变 default config；
- 不启用 Pulse worker；
- 不启用 certificate effect；
- 不放宽 official lower-bound 规则。

## 验证

本轮文档审计依赖最新 Phase 10H 回归：

```text
BPCFutureTests: Ran 483 tests in 1.453s OK (skipped=1)
git diff --check: 通过
```

本报告写入后已运行：

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
git diff --check: 通过
Ran 483 tests in 1.439s
OK (skipped=1)
```

本轮没有求解代码改动。
