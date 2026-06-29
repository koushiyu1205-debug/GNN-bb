# V558：context-aware final-judge retry gate 诊断（seed61717）

## 目的

V556 的全局 retry gate 能减少 completion-bound / final-judge retry 时间，但把大量节点直接转成 branch，导致 branch tree 扩张。V558 将 retry gate 改成 context-aware，并给 gate 后的 branch fallback 加 score / width / open-node 控制。

本轮仍只 gate 第二类 retry：

- `exact_completion_bound_retry`
- `exact_completion_bound_escalation_retry`

不 gate 普通 no-column 补救 retry：

- `exact_retry`

## 配置差异

V558 使用：

- `journey_certificate_completion_bound_retry_gate_context_scope=depth_trigger`
- `journey_certificate_completion_bound_retry_gate_min_observations=2`
- `journey_certificate_completion_bound_retry_gate_max_expensive_zero_harvest_retries=2`
- `journey_certificate_completion_bound_retry_gate_action=branch`
- `journey_certificate_completion_bound_retry_gate_branch_score_gate_enabled=True`
- `journey_certificate_completion_bound_retry_gate_branch_min_score=0.67`
- `journey_certificate_completion_bound_retry_gate_branch_max_pool_total_child_width=900`
- `journey_certificate_completion_bound_retry_gate_branch_max_pool_balance_gap=200`
- `journey_certificate_completion_bound_retry_gate_branch_max_open_nodes=8`

## seed61717 三组对比

| 组别 | status | wall time | gap | final-judge retry | final profile s | gate | branch nodes | incomplete nodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V555 retry on | EXTERNAL_TIME_LIMIT | 600.039 | 0.039594 | 8 | 295.850 | 0 | 6 | 2 |
| V556 global gate + branch | EXTERNAL_TIME_LIMIT | 600.033 | 0.039594 | 2 | 71.127 | 24 | 22 | 4 |
| V558 context gate + score branch | EXTERNAL_TIME_LIMIT | 600.019 | 0.039594 | 9 | 292.780 | 2 | 8 | 3 |

三组都没有 fathom，最终 gap 相同。

## 观察

V558 修正了 V556 的主要副作用：branch tree 没有爆炸。

- V556 branch nodes：`22`
- V558 branch nodes：`8`

但 V558 没有减少完整 proof tail 成本。

- V555 final profile：`295.850s`
- V558 final profile：`292.780s`

V558 的 gate 只触发 2 次，且两次都没有转 branch：

- gate reason：`expensive_zero_harvest_limit`
- gate action：`incomplete`
- branch gate reason：`missing_score_source`

这说明 context-aware gate 是安全的，但当前 score map 对深层 context 覆盖不足。它识别到了昂贵 zero-harvest proof tail，却没有足够可信的 branch score 来接管，只能 fail-closed。

## 判断

retry gate 这条线目前只能局部降低 final-judge retry 成本，不能单独带来完整求解优化。

V556 证明：

- 粗粒度 gate 能大幅减少 final-judge retry；
- 但会把成本转成 branch-tree 扩张。

V558 证明：

- context-aware + score gate 可以避免无脑扩树；
- 但深层 score source 不足时，gate 只能 fail-closed；
- 最终仍然没有改变 `EXTERNAL_TIME_LIMIT`。

## 意料之外

最意外的是 `depth_trigger` 太保守。它避免了 blanket gate，但同类 proof-tail 分散到不同 depth/context 后，gate 很晚才触发，final-judge retry 成本几乎回到 V555。

第二个意外是 score map 的深层覆盖不足。gate 在 depth=2 识别到昂贵 zero-harvest 后，branch fallback 被 `missing_score_source` 拦住。这说明当前 branch score 主要还在浅层/root 层有效，不能可靠接管 proof tail 深层分支。

## 下一步优化方向

1. 不继续用 hard skip 作为主线。

hard skip 的两端都不好：

- 全局 skip：树爆炸；
- context skip：触发太晚或缺 score。

2. 改成 final-judge retry budget cap。

更合理的策略：

- 第一次 full final-judge retry 保留；
- 后续同类 context 只给小预算 probe；
- 小预算无 harvest / no certificate 时 fail-closed；
- 只有 score map 覆盖且 branch gate 通过时才转 branch。

3. 补深层 branch score 数据。

训练标签要覆盖：

- depth>=2 的 branch candidate；
- child final-judge retry count；
- child final-judge profile time；
- gate 后 open-node growth；
- child time-to-certificate；
- child fathom probability。

4. context scope 应从 `depth_trigger` 改成更粗但不全局的分桶。

候选：

- `trigger`
- `depth_band_trigger`
- `trigger + profile_shape`

不要再用全局 blanket，也不要用太细的 branch-state key。

## 当前结论

retry off 不可用；global retry gate 太粗；context retry gate 安全但收益不足。

下一步应实现 `budget-capped final-judge retry`，并把 branch fallback 严格依赖深层 score coverage。
