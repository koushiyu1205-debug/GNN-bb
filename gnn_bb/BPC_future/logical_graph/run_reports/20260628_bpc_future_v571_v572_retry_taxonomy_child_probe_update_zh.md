# 20260628 V571/V572：Retry 分类修正与 Child-Probe 风险证据

## 本轮做了什么

本轮没有改 BPC、pricing、RMP、bound、certificate 或剪枝逻辑，只改了离线审计和数据输出口径。

核心修正：

- `journey_exact_pricing_retry` 继续定义为普通 no-column 后的补救 retry；
- `journey_exact_pricing_completion_bound_retry` / `exact_completion_bound_*` 才定义为 completion-bound / final-judge retry；
- `audit_journey_branch_impact.py` 不再把普通 `journey_exact_pricing_retry` 计入 `child_completion_bound_retry_count`。

这个修正很重要，因为后续 retry on/off/gate 对比只应该控制第二类 retry，不能把找隐藏负列的普通补救 retry 混进去。

## 代码与测试

修改文件：

- `BPC_future/scripts/audit_journey_branch_impact.py`
- `BPC_future/tests/test_journey_branch_impact_audit.py`

新增/更新能力：

- `child_probe_rows.jsonl` 升为 `journey_branch_child_probe_row_v2`；
- 保留原来的 nested `child_labels`；
- 同时把关键 child label 展平成顶层字段：
  - `child_completion_bound_retry_count`
  - `child_exact_pricing_event_count`
  - `child_negative_pricing_event_count`
  - `child_proof_cpu`
  - `child_max_corrected_bound_gain`
  - `child_fathomed`
- 增加 `instance_id` / `source_log_file`，方便后续按实例和上下文筛选。

已验证：

```text
python -m unittest BPC_future.tests.test_journey_branch_impact_audit BPC_future.tests.test_journey_child_score_map
python -m py_compile BPC_future/scripts/audit_journey_branch_impact.py BPC_future/tests/test_journey_branch_impact_audit.py
```

结果：通过。

## V571 重算结果

输入：

`BPC_future/results/journey_branch_candidate_replay_runbook_v570_v568_v569_deep_missing_child_probe_20260628/runs`

输出：

- `BPC_future/results/journey_branch_impact_v571_v570_smoke4_child_probe_20260628/summary.json`
- `BPC_future/results/journey_branch_impact_v571_v570_smoke4_child_probe_20260628/branch_impact_rows.jsonl`
- `BPC_future/results/journey_branch_impact_v571_v570_smoke4_child_probe_20260628/branch_training_rows.jsonl`
- `BPC_future/results/journey_branch_impact_v571_v570_smoke4_child_probe_20260628/child_probe_rows.jsonl`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_impact_v571_v570_smoke4_child_probe_zh.md`

关键指标：

```text
branch_count = 12
child_probe_row_count = 24
right_censored_branch_count = 12
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 6, 'unprocessed_children': 6}
total_child_completion_bound_retries = 27
total_child_exact_pricing_events = 38
total_child_negative_pricing_events = 40
total_child_fathom_events = 0
unprocessed_child_count = 15
max_child_corrected_bound_gain = 13.828117375
```

解释：

- V571 仍是 right-censored 风险证据，不是完整 branch-impact 正例；
- 已启动的 child 仍有明显 proof-tail 压力；
- 15 个 child 未启动，说明当前 child-probe 预算还不足以形成完整子树标签；
- 没有任何 child fathom，所以不能把这批行标成 production-ready。

## V572 Child-Score 输出

生成了两个版本。

### complete-only

输出：

`BPC_future/results/journey_child_score_map_v572_v571_complete_only_20260628/`

结果：

```text
raw_child_probe_row_count = 24
child_probe_row_count = 0
child_score_row_count = 0
right_censored_filter_skip_count = 9
production_ready = false
```

结论：

严格完整标签下没有可用 child score。这个结果是预期内的，也是正确的 fail-closed。

### right-censored risk

输出：

`BPC_future/results/journey_child_score_map_v572_v571_rightcensored_risk_20260628/`

结果：

```text
raw_child_probe_row_count = 24
child_probe_row_count = 9
child_score_row_count = 9
include_right_censored = true
production_ready = false
```

这个版本只用于风险诊断和后续采样导航，不能作为生产 score map。

## 当前判断

1. `retry_off` 仍然不是优化方向。

它可能显著缩短 wall time，但会丢失 exact dual / gap / certificate。它只能作为诊断下界。

2. `retry_gate` 有价值，但前提是只 gate 第二类 retry。

普通 no-column 补救 retry 要继续保留；completion-bound / final-judge retry 才进入 on/off/gate 对比。

3. 当前 V571 证明了一个问题：child-probe 太容易右删失。

这意味着后续如果继续采 child proof-cost 标签，需要更明确地控制：

- 每个 probe 的目标 depth；
- child 启动覆盖率；
- 每个 child 的最小观测预算；
- right-censored 样本只能作为风险/负证据，不能当完整正例。

4. 当前主线仍然是 branch score，而不是关 retry。

下一步应该用更干净的 retry taxonomy 和 V571/V572 风险证据，继续补深层 branch context 的 score coverage，并用 score-gated early branch / retry gate 作为 opt-in 控制器。

## 下一步建议

先不要直接跑 full60 retry gate。

更合理的下一步是：

1. 用修正后的审计口径重跑/汇总已有 V545/V568/V569/V571 日志；
2. 从深层 missing-score context 里挑更小但更有信息量的 child-probe；
3. 对每个 forced branch 至少保证两个 child 都启动，否则该行只能做右删失风险；
4. 形成一批 complete child proof-cost / branch-impact rows 后，再训练或更新 score map；
5. 最后再做 `retry_on / retry_off / retry_gate / retry_gate+adaptive_cap` 对比。

验收仍保持 exact-safe：

- score 只改排序或调度；
- retry gate/cap 不能提供 official bound；
- child 仍靠 exact pricing closure；
- 没有 certificate 的结果只记录 gap 或诊断，不算已证明最优。
