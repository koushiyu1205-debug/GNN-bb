# Sharded Pulse Phase 11D 最终负结果与 Pivot 报告

日期：2026-06-13

## 目标

本轮不继续写算法，也不实现新的 proof-closed resume。

目标是基于 Phase 7O 到 Phase 11C 的受控证据，正式关闭当前 `Sharded Pulse worker/proof` 路线的继续扩张，并明确后续 pivot：

1. 不默认启用 Pulse worker；
2. 不开放 official certificate gate；
3. 不继续扩大 worker budget / pricing time / profile-DP cap / label cap / early quota / selection mode / refinement threshold；
4. 将未实现的 proof-closed resume 从当前路线中移除，作为未来新 proof-route 能力，而不是当前 negative-result 证据的一部分；
5. 输出完整 negative-result / pivot 结论，建议转向 RMP stabilization / pool compression / legacy final judge proof-tail optimization。

## 关键边界

`proof-closed resume` 当前没有实现为 Sharded Pulse proof-ledger 的可恢复证据路径。

现有代码里：

- `ShardProofRecord.proof_closed=False` 不能 certificate；
- frontier snapshot 已被测试为非 proof；
- `JourneyPricingConfig.pulse_resume_enabled` 只是配置字段；
- 当前可运行 resume 主要是 legacy/profile-DP catalog / profile-label resume，不等价于 Sharded Pulse proof-closed resume。

因此本轮选择：

- 不实现 proof-closed resume skeleton；
- 不把 profile-DP resume 当成 Sharded Pulse proof resume；
- 不声称 resume 已经实验证明无 ROI；
- 明确将 proof-closed resume 从当前 Pulse worker/proof 路线移除。

若以后重新做 proof-closed resume，它应被视为新的 Phase，而不是当前路线的继续调参。

## 证据汇总

### 1. Worker 能加列，但没有稳定降低 tail

Phase 7O hard-tail worker ROI A/B：

- summary：`BPC_future/results/sharded_pulse_phase7o_hard_tail_worker_roi_ab_20260612/summary.json`
- rows：24
- profiles：
  - baseline
  - audit_only
  - strict_worker_previous_signal_only
  - strict_worker_current_probe
- official status：24 / 24 `TIME_LIMIT`
- official pricing state：24 / 24 `INCOMPLETE_LIMIT`
- critical disagreement：0
- worker events：14
- legacy final judge calls：48
- completion-bound retry count：0
- audit shards incomplete：152
- audit harvested：33

结论：

- Pulse worker 可以安全进入 add-column path；
- 但没有稳定把 hard-tail 从 `TIME_LIMIT / INCOMPLETE_LIMIT` 拉出；
- 没有观察到 completion retry / final judge tail 的稳定下降。

### 2. Passed-source / target-specific worker 信号仍不构成 ROI

Phase 8Q passed-source ROI validation：

- summary：`BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613/summary.json`
- rows：35
- official status：35 / 35 `TIME_LIMIT`
- critical disagreement：0
- worker returned / added journeys：10 / 10
- worker added new task sets：8
- worker added support-changing：2

结论：

- worker 确实能返回 true-RC negative columns；
- 这些列包含 new task-set / support-changing 信号；
- 但矩阵整体仍没有稳定求解改善；
- 因此“能加列”不等于“能减少 tail”。

### 3. RMP / dual stabilization 方向没有给出正向替代信号

Phase 9J previous/zero dual stabilization repeat A/B：

- summary：`BPC_future/results/sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613/summary.json`
- rows：36
- official status：36 / 36 `TIME_LIMIT`
- pricing state：
  - 17 `INCOMPLETE_LIMIT`
  - 19 `FOUND_NEGATIVE`
- critical disagreement：0
- worker triggered：0

结论：

- 当前轻量 dual stabilization diagnostic 没有形成目标 A 所需的稳定改善；
- 但它继续支持“问题不只是 Pulse worker 接线”，而是 RMP / profile-DP / final judge tail 的结构性问题。

### 4. Profile-DP / selection / budget 调参没有稳定改善

Phase 11B profile selection mode sensitivity：

- 20-task state1000 smoke 中 selected counts 变为 `72 / 18 / 18`，但没有 official 改善；
- 5/10 guard：
  - summary：`BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_5_10_guard_20260613/summary.json`
  - rows：15
  - official status：15 / 15 `TIME_LIMIT`
  - pricing state：15 / 15 `INCOMPLETE_LIMIT`
  - critical disagreement：0
  - official result changed：0

结论：

- selection mode 可以扰动返回列；
- 但不稳定改善 20-task；
- 5/10 guard 说明当前 20-only 调参没有破坏小实例，但也没有带来目标收益。

### 5. Adaptive refinement 未降低 incomplete

Phase 11C proof-route refinement / resume audit：

- summary：`BPC_future/results/sharded_pulse_phase11c_proof_route_refinement_resume_audit_20260613/summary.json`
- rows：18
- profiles：
  - baseline
  - audit_no_refine
  - audit_refine
- critical disagreement：0
- official result changed：0
- worker events：0
- all official status：`TIME_LIMIT`
- all official pricing state：`INCOMPLETE_LIMIT`

20-task audit 聚合：

| profile | shards total | certified | incomplete | negative | refined | harvested | recursions |
|---|---:|---:|---:|---:|---:|---:|---:|
| audit_no_refine | 120 | 2 | 108 | 10 | 0 | 46 | 6070 |
| audit_refine | 120 | 2 | 108 | 10 | 0 | 46 | 6090 |

结论：

- adaptive refinement 没有降低 incomplete；
- 没有增加 certified shards；
- `final_judge_shards_refined=0`；
- 当前 hard-tail audit 主要进入 hidden-negative / incomplete signal，不进入 no-negative proof-completion/refinement path。

## Final Condition Audit

### 条件 A：未满足

未达到：

- 5-task 无回退；
- 10-task 无回退；
- selected 20-task 明显改善和求解加速。

虽然多个 guard 矩阵保持了小实例不变，但 20-task 没有稳定 wall-time / status / gap 改善。

### 条件 B：当前路线满足负结果交付

本报告将条件 B 解释为“当前已实现的 Pulse worker/proof 路线”：

- 连续多轮 A/B 无稳定改善；
- worker 能加 true-RC negative columns，但不降低 tail；
- adaptive refinement 没有降低 incomplete；
- proof-closed resume 未实现，已从当前路线移除，不再作为当前路线继续扩张的理由；
- 20-task 没有明显改善；
- no critical disagreement；
- no certificate / lower-bound side effect。

因此当前路线应停止继续扩大。

如果未来仍要评估 proof-closed resume，它必须作为新的独立 proof-route Phase 进入，先实现 proof-closed record 持久化、上下文 hash 校验、resume/fresh exactness 对照和 frontier-not-proof guard，不能被当前 negative-result report 自动覆盖。

### 条件 C：未触发

没有发现：

- critical disagreement；
- true-RC mismatch；
- forbidden / branch / cut context mismatch。

因此没有进入 correctness blocker 修复路线。

## 决策

停止继续扩大当前 Pulse worker/proof 路线。

不要继续做：

- worker 默认启用；
- official certificate gate；
- 20/100 A/B；
- parallel；
- proof-closed resume 作为当前路线的补丁；
- cut / subset-row unsafe prefix bound；
- 简单增加 worker time limit；
- 继续调 profile-DP cap / label cap / pricing time；
- 继续调 early quota / selection mode / target ordering。

建议转向：

1. RMP stabilization / active-family stabilization；
2. column pool compression / column impact filter；
3. legacy final judge / profile-DP proof-tail optimization；
4. returned-column quality 与 RMP trajectory 的直接因果诊断。

## Exactness 边界

本轮只写文档和结论，不改求解行为。

保持：

- 默认 Sharded Pulse 关闭；
- Pulse worker 不影响 official certificate；
- Pulse incomplete / duplicate-only / empty harvest 不影响 lower bound；
- audit / worker context hash 不复用为 proof；
- frontier snapshot 不是 proof；
- proof-closed resume 未实现、不伪装、不证书化。

## 验证

本轮运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/sharded_pulse_final_judge.py \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

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

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

```bash
git diff --check
```

结果：

```text
py_compile: passed
focused tests: Ran 8 tests in 0.005s OK
full BPCFutureTests: Ran 483 tests in 1.431s OK (skipped=1)
git diff --check: passed
```

## 最终结论

当前 Sharded Pulse worker/proof 路线的安全性边界已经基本证明，但 ROI 不成立：

- worker 能加列，但没有稳定缩短 hard tail；
- target / source / ordering / budget / selection 调参没有稳定改善；
- adaptive refinement 没有降低 incomplete；
- proof-closed resume 不存在，不能作为当前路线的继续理由；
- 20-task selected hard set 没有明显改善；
- 5/10 guard 没有回退；
- 没有 critical disagreement。

因此本轮将当前 Pulse worker/proof 路线归档为 negative result，并建议后续主线 pivot 到 RMP stabilization / pool compression / legacy final judge proof-tail optimization。
