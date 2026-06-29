# V729 V728 Greedy-Anchor Depth1/2 Paired Probe 结果判断

日期：2026-06-28

## 边界

本报告只解释已经完成的 V728 paired replay 输出，不创建 official bound、certificate 或剪枝依据。所有结论都只用于 branch score / RouteOpt-BKF controller 的诊断和训练标签筛选。

输入：

- runbook: `BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runbook.json`
- paired summary: `BPC_future/results/journey_paired_probe_summary_v729_v728_greedy_depth1_2_pairprobe_20260628/summary.json`
- report: `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_paired_probe_summary_v729_v728_greedy_depth1_2_pairprobe_zh.md`

## 完整性

V728 runbook 共 12 条 replay：

```text
paired_group_count = 4
baseline_entry_count = 4
alternative_entry_count = 8
result_available_entry_count = 12
missing_result_entry_count = 0
label_counts = {'neutral_proxy': 6, 'target_not_replayed': 2}
valid_observed_alternative_entry_count = 6
target_not_replayed_entry_count = 3
production_ready = false
official_bound_effect = false
certificate_effect = false
```

这说明 replay 全部完成，但只有 6 个 alternative 是有效命中目标节点的反事实；没有产生 strict positive / weak positive。

## 结果表

| instance | source | role | forced pair | status | wall | gap | primal | dual | branch | CB retry | target hit |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| seed61635 | d1 n1 | selected | `[11,15]` | TIME_LIMIT | 130.719 | 0.061278 | 561.030445 | 526.651393 | 7 | 7 | yes |
| seed61635 | d1 n1 | alt | `[15,18]` | TIME_LIMIT | 130.496 | 0.061278 | 561.030445 | 526.651393 | 7 | 7 | yes |
| seed61635 | d1 n1 | alt | `[15,17]` | TIME_LIMIT | 130.175 | 0.061278 | 561.030445 | 526.651393 | 7 | 7 | yes |
| seed61635 | d2 n4 | selected | `[7,14]` | TIME_LIMIT | 148.383 | 0.061278 | 561.030445 | 526.651393 | 8 | 8 | no |
| seed61635 | d2 n4 | alt | `[6,7]` | TIME_LIMIT | 148.320 | 0.061278 | 561.030445 | 526.651393 | 8 | 8 | no |
| seed61635 | d2 n4 | alt | `[6,15]` | TIME_LIMIT | 147.825 | 0.061278 | 561.030445 | 526.651393 | 8 | 8 | no |
| seed61311 | d1 n1 | selected | `[5,13]` | TIME_LIMIT | 127.804 | 0.048386 | 575.008740 | 547.186422 | 7 | 8 | yes |
| seed61311 | d1 n1 | alt | `[5,19]` | TIME_LIMIT | 127.784 | 0.048386 | 575.008740 | 547.186422 | 7 | 8 | yes |
| seed61311 | d1 n1 | alt | `[7,13]` | TIME_LIMIT | 128.350 | 0.048386 | 575.008740 | 547.186422 | 7 | 8 | yes |
| seed61311 | d1 n2 | selected | `[5,13]` | TIME_LIMIT | 111.418 | 0.048386 | 575.008740 | 547.186422 | 7 | 7 | yes |
| seed61311 | d1 n2 | alt | `[7,13]` | TIME_LIMIT | 131.650 | 0.048386 | 575.008740 | 547.186422 | 7 | 8 | yes |
| seed61311 | d1 n2 | alt | `[4,20]` | TIME_LIMIT | 123.524 | 0.048386 | 575.008740 | 547.186422 | 7 | 7 | yes |

## Paired group 判断

### seed61635 d1 n1

selected `[11,15]` 对比两个 alternatives：

- `[15,18]`: wall 快 `0.224s`，gap/primal/dual/branch/CB retry 完全不变。
- `[15,17]`: wall 快 `0.544s`，gap/primal/dual/branch/CB retry 完全不变。

判断：不是可训练正例。这个差异只是不稳定开销，不是 proof-cost 或 gap 改善。

### seed61635 d2 n4

加入 target replay 审计后，机器汇总已将该组标为：

```text
valid_observed_alternative_count = 0
target_not_replayed_count = 3
best_alternative = null
label_counts = {'target_not_replayed': 2}
```

JSONL 中没有命中 source node `4` depth `2` 的 branch/candidate 事件。

判断：这一组反事实无效。它只能说明 replay 在小预算/改路径后没有复现到目标源节点，不能用于训练 pair 优劣。

### seed61311 d1 n1

selected `[5,13]` 对比两个 alternatives：

- `[5,19]`: wall 快 `0.020s`，gap/primal/dual/branch/CB retry 完全不变。
- `[7,13]`: wall 慢 `0.546s`，gap/primal/dual/branch/CB retry 完全不变。

判断：中性。不能作为正例，也不应作为 hard negative。

### seed61311 d1 n2

selected `[5,13]` 对比两个 alternatives：

- `[7,13]`: wall 慢 `20.232s`，CB retry 多 1 次，gap/primal/dual 不变。
- `[4,20]`: wall 慢 `12.106s`，CB retry 不变，gap/primal/dual 不变。

判断：`[7,13]` 可作为很弱的 proof-cost negative 参考，但不是 strict hard negative，因为所有 runs 都右删失，且最终 gap 没变。

## 核心结论

V728 没有给 greedy-anchor 产生新的可训练强正例。更重要的是，它强化了 V726 的判断：

```text
greedy-anchor 的 branch path 局部替换没有改变 dual，也没有改善 gap。
```

所以当前 greedy-anchor 的主要瓶颈不像是“depth1/depth2 某个 Ryan-Foster pair 选错了”，而更像是：

1. LP/formulation 下界太松；
2. pricing-compatible cuts 不足；
3. incumbent 虽可改善，但 dual bound 无法跟上；
4. 小预算 child probe 对这类实例的训练信号主要是右删失噪声。

## 对 Branch Score 主线的影响

1. RouteOpt/BKF controller 仍应保留，因为 sector-wave hard cases 已经稳定 `TIMEOUT -> OPTIMAL`。
2. greedy-anchor 不应继续靠盲目扩 depth1/depth2 alternatives 收正例；收益太低，且容易污染训练。
3. branch action 数据集中，V728 rows 应标为：
   - `diagnostic_only=true`
   - `production_ready=false`
   - 有效 depth1 rows: `neutral_proxy`
   - seed61311 d1 n2 `[7,13]`: 可选 `weak_proof_cost_negative`
   - seed61635 d2 n4 group: `target_not_replayed`，不能进入有效 pair 排名
4. 下一步不能只扩 branch replay，应并行推进 cuts/formulation。

## 下一步

优先级建议：

1. 已在 paired replay summarizer 中正式增加 `target_replay_status` / `target_not_replayed` / `valid_observed_alternative_count` 字段，避免未命中源节点的 group 被当作有效反事实。
2. 把 V726 的 sector-wave strict positives 和 V728 的 neutral/weak negative 作为不同权重写入 branch action 数据集。
3. 对 greedy-anchor 开始做 pricing-compatible cuts / route-aware cuts 设计；验证指标不是 wall time，而是 dual bound、root/child corrected LB 和 fathom count。
4. 保留 RouteOpt/BKF phased testing 为 solver 主分支 controller，但对 greedy-anchor 增加“branch replay 无收益 -> cuts/formulation”分型。

## 验证

已完成：

```text
python BPC_future/scripts/summarize_journey_paired_probe_runbook.py \
  --runbook BPC_future/results/journey_branch_candidate_replay_runbook_v728_v726_greedy_depth1_2_pairprobe_20260628/runbook.json \
  --output-dir BPC_future/results/journey_paired_probe_summary_v729_v728_greedy_depth1_2_pairprobe_20260628 \
  --report BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_paired_probe_summary_v729_v728_greedy_depth1_2_pairprobe_zh.md
```

输出：

```text
entry_count = 12
paired_group_count = 4
result_available_entry_count = 12
valid_observed_alternative_entry_count = 6
target_not_replayed_entry_count = 3
label_counts = {'neutral_proxy': 6, 'target_not_replayed': 2}
```

补充验证：

```text
python -m unittest BPC_future.tests.test_journey_paired_probe_summary
Ran 2 tests in 0.004s
OK
```
