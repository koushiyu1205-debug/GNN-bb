# Sharded Pulse Phase 11C Proof-route Refinement / Resume Audit 报告

日期：2026-06-13

## 目标

Phase 10I / 11A / 11B 已经排除了几条子路线：

- active hidden-negative worker / current-context probe 没有稳定 ROI；
- profile-DP state cap / label cap 没有稳定 ROI；
- early-column new-task-set quota 只是轨迹扰动，不降低 proof tail；
- pricing-time 扩张会增加 incomplete 风险；
- returned-column selection mode 不能稳定改善 official result。

`目标.md` 中最终条件 B 仍有一个明确缺口：

- refinement / resume proof-route 还没有形成“无 ROI / 无降低 incomplete”的完整证据。

本轮只审计这个缺口，不做新算法。

本轮不做：

- Sharded Pulse worker 扩张；
- official certificate gate；
- production default；
- persistent proof-closed resume 实现；
- parallel；
- adaptive sharding 新策略；
- cut / subset-row prefix bound；
- RMP stabilization。

## 静态实现审计

当前代码状态：

1. `BPC_future/pricing/sharded_pulse_final_judge.py` 只有 ledger / cache key / dummy shard engine scaffolding。
2. `ShardProofRecord.proof_closed=False` 时，即使 status 是 `CERTIFIED_NO_NEGATIVE`，ledger 也会返回 `INCOMPLETE_CACHE_INVALID`。
3. `frontier_state_count` 已被测试为“不是 proof-closed 证据”。
4. `JourneyPricingConfig.pulse_resume_enabled` 字段存在，driver mode 也会展示 `sharded_pulse_resume_enabled`。
5. 但当前 Sharded Pulse transition / guarded engine 没有 proof-closed persistent resume 消费路径。
6. 现有可运行 resume 主要是 legacy/profile catalog / profile labeling resume：
   - `profile_catalog_resume_enabled`
   - `profile_labeling_resume_enabled`
   - `profile_labeling_physical_catalog_resume_enabled`

结论：

- 当前不能把 `pulse_resume_enabled` 解释为 Sharded Pulse proof-closed resume 已实现；
- 当前也不能用 legacy/profile-label resume 证明 shard proof-route resume 有 ROI 或无 ROI；
- 因此最终条件 B 的 resume 子项仍未关闭。

## Dynamic Smoke 矩阵

输出目录：

- `BPC_future/results/sharded_pulse_phase11c_proof_route_refinement_resume_audit_20260613`

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase11c_proof_route_refinement_resume_audit_20260613 \
--instances phase7o_20_smoke \
--profiles baseline audit_no_refine audit_refine \
--time-limit 3.0 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1 \
--max-cg-iterations 3 \
--audit-time-limit 0.5 \
--audit-max-recursions 100000 \
--audit-negative-harvest-limit 16 \
--repeat-count 2 \
--quiet
```

矩阵：

- instances：
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`
- profiles：
  - baseline
  - `audit_no_refine`
  - `audit_refine`
- repeat-count：2
- rows：18

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/sharded_pulse_final_judge.py \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_ledger_refined_parent_uses_children \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_frontier_snapshot_is_not_proof_closed \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_cache_key_tracks_context \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_all_children_certify_parent \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_child_incomplete_blocks_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_child_negative_propagates \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_threshold_and_cap_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_low_roi_gate_blocks_refinement_not_certificate
```

结果：

```text
Ran 8 tests in 0.008s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 483 tests in 1.455s
OK (skipped=1)
```

```bash
git diff --check
```

结果：通过。

## Official Result Guard

全部 rows：

- `critical_disagreement_count=0`
- `official_result_changed_vs_baseline=False`
- official status 均为 `TIME_LIMIT`
- official pricing_state 均为 `INCOMPLETE_LIMIT`
- audit-only 没有 official lower-bound / certificate effect
- worker events = 0

## 20-task Audit 结果

整体聚合：

| profile | audit status | comparison | shards total | certified | incomplete | negative | refined | harvested | recursions | audit time |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | none | none | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.000000 |
| audit_no_refine | 6 `FOUND_NEGATIVE` | 6 `legacy_incomplete_pulse_negative` | 120 | 2 | 108 | 10 | 0 | 46 | 6070 | 3.123122 |
| audit_refine | 6 `FOUND_NEGATIVE` | 6 `legacy_incomplete_pulse_negative` | 120 | 2 | 108 | 10 | 0 | 46 | 6090 | 3.146500 |

逐实例形态：

- `tranq20_01`：
  - no-refine：每 repeat `20 total / 0 certified / 19 incomplete / 1 negative / 0 refined`
  - refine：同型
- `mt20_greedy_apollo_01`：
  - no-refine：每 repeat `20 total / 1 certified / 16 incomplete / 3 negative / 0 refined`
  - refine：同型
- `mt20_greedy_tranq_01`：
  - no-refine：每 repeat `20 total / 0 certified / 19 incomplete / 1 negative / 0 refined`
  - refine：同型

## 解释

`audit_refine` 没有降低 incomplete，也没有增加 certified shards：

- `pulse_audit_shards_incomplete`：108 -> 108
- `pulse_audit_shards_certified`：2 -> 2
- `pulse_audit_shards_refined`：0 -> 0
- `pulse_audit_shards_negative`：10 -> 10

原因不是 refinement 聚合语义错误；已有 focused tests 覆盖了：

- parent certified iff all children certified；
- child incomplete blocks parent certificate；
- child negative propagates；
- threshold/cap guard；
- low-ROI gate 不会错误 certificate。

本轮 smoke 显示的是更具体的 production-hard-tail 事实：

- 当前 20-task audit contexts 很快出现 negative shard；
- audit 状态转为 `FOUND_NEGATIVE` warning signal；
- 该路径不是 no-negative proof-completion 路径；
- 因而 first-task incomplete shard 没有进入 second-action refinement proof route；
- adaptive refinement 对当前 hard-tail audit 形态没有降低 incomplete。

## Resume 结论

当前不能声称 proof-closed resume 已验证。

原因：

- Sharded Pulse 没有持久 proof-closed resume implementation；
- 没有 frontier snapshot / proof-closed record 的跨调用恢复测试；
- 没有 resume 后 shard incomplete 下降的 dynamic evidence；
- 现有 profile catalog / profile-label resume 不等价于 shard proof ledger resume。

因此：

- Phase 11C 为 final condition B 补充了 refinement smoke 负证据；
- 但 final condition B 仍不能关闭，因为 proof-closed resume 子项仍是未实现 / 未验证。

## Exactness 边界

- audit-only；
- no certificate effect；
- no official lower-bound effect；
- no worker effect；
- no production default change；
- no unsafe pruning；
- no duplicate-only promotion；
- no smoothed / GNN dual certificate；
- no resume cache reuse as proof。

## 判断

Phase 11C 不支持继续扩大 refinement 作为当前主线。

证据：

1. 5/10 未在本轮触碰；
2. 20-task official result 没有被 audit 改变；
3. no critical disagreement；
4. `audit_refine` 与 `audit_no_refine` 在 hard-tail smoke 中同型；
5. refinement 没有减少 incomplete；
6. 当前 Sharded Pulse proof-closed resume 仍未实现，不能作为已验证路线。

当前最终目标仍未完成：

- 条件 A：未满足，20-task 没有稳定改善和求解加速；
- 条件 B：仍缺 proof-closed resume 的实现/验证或正式负结果；
- 条件 C：未发现 correctness blocker。

## 下一步建议

不要继续扩大：

- worker time；
- worker trigger；
- pricing time；
- state cap；
- label cap；
- early quota；
- selection mode；
- refinement threshold。

如果要完成条件 B，下一步应该二选一：

1. 实现最小 proof-closed resume skeleton，并做 resume vs no-resume 的 exact-safe smoke；
2. 明确将 proof-closed resume 从当前路线移除，并写完整 negative-result / pivot report，建议转向 RMP stabilization / pool compression / legacy final judge proof-tail optimization。

在没有这一步前，不能宣称当前 Pulse worker/proof 路线已经被完整证伪。
