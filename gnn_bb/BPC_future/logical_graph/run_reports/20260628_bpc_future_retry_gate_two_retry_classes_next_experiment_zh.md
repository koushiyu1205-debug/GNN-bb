# 20260628：两类 Retry、Gate 对比与后续优化计划

## 结论

当前必须把 retry 分成两类：

1. 普通 no-column 补救 retry
   - 事件：`journey_exact_pricing_retry`
   - `pricing_kind`：`exact_retry`
   - 作用：ordinary/profile pricing 不完整或 no-column 后，再用真实 reduced cost 找负列。
   - 边界：它不能产生 official certificate；不能把它的 no-column 结果当全局无负列证明。

2. completion-bound / final-judge retry
   - 事件：`journey_exact_pricing_completion_bound_retry`
   - `pricing_kind`：`exact_completion_bound_retry` / `exact_completion_bound_escalation_retry`
   - 作用：用 direct-label / completion-bound final judge 证明 no-negative certificate，或者发现隐藏负列。
   - 边界：只有真实返回 certificate 时才支持闭合；被 gate/cap/off 后必须 fail-closed，不能剪枝。

当前 retry gate / budget cap 只应控制第二类。普通 no-column 补救 retry 继续保留，不进入 completion-bound retry gate 统计。

## 当前代码状态

已完成：

- `journey_driver.py` 的 retry gate stats 只接受 `exact_completion_bound_retry` / `exact_completion_bound_escalation_retry`。
- ordinary `exact_retry` 不会计入 completion-bound retry gate/cap。
- gate/cap 均为 opt-in。
- gate/cap 只改变是否继续执行或缩短 final-judge retry 预算，不提供 bound、不提供 certificate、不剪枝。
- gate/cap 日志保留：
  - `retry_gate_context_key`
  - `retry_gate_context_*`
  - `retry_budget_cap_*`
  - branch fallback 的 score/width/open-node gate reason。
- 审计脚本已修正：`completion_bound_retry_count` 不再把 `journey_exact_pricing_retry` 算进去。

定向测试已通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/audit_journey_branch_impact.py \
  BPC_future/scripts/audit_journey_completion_tail_profile.py \
  BPC_future/scripts/audit_journey_tail_action_counterfactual_delta.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_is_opt_in_and_contextual \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_keeps_unseen_context_uncapped \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_is_opt_in_and_requires_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_blocks_expensive_zero_harvest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_keeps_harvest_signal \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_context_scope_isolates_depth_trigger \
  BPC_future.tests.test_journey_branch_impact_audit.JourneyBranchImpactAuditTests.test_completion_bound_retry_count_excludes_ordinary_no_column_retry
```

结果：`Ran 7 tests ... OK`。

## 已有对比实验

已有 4 个 random-TW canonical 20-scale 难例 smoke：

- 报告：`BPC_future/logical_graph/run_reports/20260628_bpc_future_v567_v568_retry_on_off_gate_cap_smoke4_zh.md`
- 结果目录：
  - `BPC_future/results/20260628_v567_retry_on_off_gate_cap_smoke4_tasks20/`
  - `BPC_future/results/20260628_v568_retry_gate_cap_profile_trigger_fix_smoke4_tasks20/`

三组含义：

| 组别 | 含义 | 是否生产候选 |
|---|---|---:|
| `retry_on` | completion-bound / final-judge retry 全开 | 是，安全基线 |
| `retry_off` | 关闭 final judge，并关闭 required completion-bound | 否，只作诊断 |
| `retry_gate_cap` | completion-bound retry gate + certificate-aware budget cap | 候选机制，但当前未达可用 |

V567 结果：

| 组别 | OPTIMAL | EXTERNAL_TIME_LIMIT | TIME_LIMIT | mean wall | gap 可用 | final retry | cap applied | gate events | branch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| retry_on | 0/4 | 4/4 | 0/4 | 600.03s | 4/4 | 116 | 0 | 0 | 104 |
| retry_off | 0/4 | 0/4 | 4/4 | 37.56s | 0/4 | 0 | 0 | 0 | 0 |
| retry_gate_cap | 0/4 | 3/4 | 1/4 | 595.55s | 4/4 | 114 | 7 | 5 | 101 |

V568 修复 `profile_exhausted_no_column` history 后：

| 实例 | status | wall | gap | final retry | CB profile | cap applied | gate | branch | score missing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| seed61717 | TIME_LIMIT | 577.25s | 0.039594 | 8 | 248.06s | 7 | 5 | 6 | 5 |
| seed61103 | EXTERNAL_TIME_LIMIT | 600.02s | 0.026290 | 21 | 216.90s | 0 | 0 | 14 | 13 |
| seed61206 | EXTERNAL_TIME_LIMIT | 600.02s | 0.085809 | 22 | 316.08s | 0 | 0 | 20 | 19 |
| seed61718 | EXTERNAL_TIME_LIMIT | 600.02s | 0.043777 | 64 | 203.86s | 0 | 0 | 62 | 61 |

## 能不能优化

能优化局部 proof-tail 成本，但当前还不能作为完整求解优化上线。

证据：

- `retry_off` 很快结束，但没有 exact dual bound / gap，不是求解加速。
- `retry_gate_cap` 能在 seed61717 上减少部分 completion-bound retry 时间，但没有 OPTIMAL，也没有改善 gap。
- 修复后 gate/cap 统计更准确，但另外 3 个实例基本不触发有效 cap；很多 retry 是合法且相对便宜的 certificate retry，不应被当作坏样本。
- branch fallback 多数被 `missing_score_source` 拦住，说明深层 branch score 覆盖不足；这个 fail-closed 行为是正确的。

因此，retry controller 的定位应是辅助 proof-tail controller，不是独立主线。

## 如果要继续优化，应该怎么做

1. 保留 `retry_on` 作为 exact-safe 默认基线。

2. `retry_off` 只作为诊断对照。
   - 不能用它的 wall time 判断加速。
   - 报告必须单独列出 `gap_available=false` / `no_exact_dual_bound`。

3. gate/cap 只处理真正昂贵的 incomplete tail。
   - 默认不 gate certified zero-harvest。
   - `certified_zero_harvest_profile_time_max + margin` 应作为 cap floor，防止把本来能认证的节点 cap 成 incomplete。
   - expensive incomplete zero-harvest 才触发硬 gate。

4. gate 后不能裸 branch。
   - 必须有 branch score source。
   - top score 过阈值。
   - child width / balance / open-node 不超限。
   - 否则 fail-closed 为 incomplete，不剪枝。

5. Branch Score 是主线。
   - 当前主要缺口是 depth 1/2/3/4 的 score coverage。
   - 需要把 V567/V568 的深层 branch event 和 child retry 后果转成训练标签：
     - child completion-bound retry count
     - child completion-bound profile time
     - child certificate / incomplete
     - child gap / primal / dual 改善
     - score missing / score low / width blocked reason

## 后续实验计划

不建议现在直接跑 full60 的 retry gate 大实验。先做两个前置条件：

1. 深层 score coverage 明显提升。
   - 至少让 gate 触发位置有非 root score source。
   - `missing_score_source` 不能仍是主失败原因。

2. smoke 中证明 gate/cap 不退化 gap。
   - 至少在 4 到 12 个固定 20-scale 难例上比较：
     - `retry_on`
     - `retry_off`
     - `retry_gate`
     - `retry_gate + adaptive cap`
   - 关键不是 wall time 是否变短，而是：
     - OPTIMAL 数是否提升；
     - gap 是否改善或不退化；
     - capped mean 是否降低；
     - final retry profile 是否下降；
     - branch tree 是否没有变宽；
     - incomplete child 是否没有明显增加。

通过 smoke 后再跑 full60。

full60 报告应固定输出：

- `OPTIMAL` / `TIME_LIMIT` / `EXTERNAL_TIME_LIMIT`
- capped mean wall time
- `<=200s OPTIMAL`
- 未最优实例 gap、primal bound、dual bound、gap source、gap_available
- ordinary no-column retry count
- completion-bound retry count
- completion-bound retry class
- completion-bound profile time
- gate action：`branch` / `incomplete`
- cap applied count
- branch score missing / low score / width blocked / open-node blocked

## 当前判断

如果问“retry gate 能不能优化”，答案是：

- 能优化局部 final-judge proof-tail 成本；
- 但当前不能单独优化完整求解；
- 真正可行的方向是：

```text
Branch Score 主线
+ completion-bound retry adaptive budget
+ score-gated branch fallback
+ 深层 proof-tail 标签
```

最意料之外的地方是：很多 retry 不是纯浪费，而是在提供合法 certificate；另一个意外是深层 score coverage 比 root 层差得多，导致 gate 识别到 proof-tail 后没有可信 branch 策略接管。
