# 20260628 V600-V606 Paired Probe 进展与判断

## 结论

本轮完成了 paired child-probe 工具链，但这批 V600 样本没有产生可训练的正例或硬负例。

核心结果：

- V600 runbook：6 个 paired group，18 条 child-probe 命令。
- V601/V603/V605 audit：18 条全部完成审计，但 branch-impact 仍全是 right-censored，`usable_branch_impact_training_count=0`。
- V606 paired summary：12 个 observed alternatives 全部是 `neutral_proxy`。
- 没有 `positive_proxy`，也没有 `hard_negative_proxy`。

这说明：当前这种“同一 deep context 下 selected baseline + 两个 alternative，额外 2 个节点、36 CG iter、220s”的 fixed-budget probe 太短，或者采样到的候选差异太弱，无法给 GAT 提供有效的 branch pair 学习信号。

## 本轮代码改动

### `build_journey_branch_candidate_replay_runbook.py`

新增 `--paired-probe`：

- 每个 source event 先导出 selected baseline pair；
- 再导出 alternative pair；
- 同一组共享 `pair_group_id`；
- entry 新增 `pair_role`：
  - `selected_baseline`
  - `alternative`

边界不变：

- runbook 只生成命令；
- forced pair 只影响 branch candidate priority；
- 不产生 official bound；
- 不产生 certificate；
- 不改变 fathom/prune 逻辑。

### `summarize_journey_paired_probe_runbook.py`

新增只读汇总脚本：

- 读取 paired runbook；
- 读取每个 run 的 `results.csv`；
- 可选合并 completion-tail summary 和 child-probe rows；
- 输出：
  - `paired_probe_rows.jsonl`
  - `paired_probe_group_rows.jsonl`
  - `summary.json`
  - 中文报告

它只做诊断汇总，不运行 BPC/pricing/RMP。

修正过一个重要问题：未运行 entry 现在标记为 `missing_result`，不会再被误算成 `neutral_proxy`。

## 测试

通过：

```text
python -m py_compile \
  BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py \
  BPC_future/tests/test_journey_branch_candidate_replay_runbook.py

python -m unittest BPC_future.tests.test_journey_branch_candidate_replay_runbook
```

结果：

```text
Ran 15 tests ... OK
```

新增 paired summary 测试通过：

```text
python -m py_compile \
  BPC_future/scripts/summarize_journey_paired_probe_runbook.py \
  BPC_future/tests/test_journey_paired_probe_summary.py

python -m unittest BPC_future.tests.test_journey_paired_probe_summary
```

结果：

```text
Ran 1 test ... OK
```

合并定向测试通过：

```text
python -m unittest \
  BPC_future.tests.test_journey_paired_probe_summary \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook
```

结果：

```text
Ran 16 tests ... OK
```

## V600 Runbook

输出：

```text
BPC_future/results/journey_branch_candidate_replay_runbook_v600_v597_paired_deep_child_probe_20260628/
```

报告：

```text
BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_candidate_replay_runbook_v600_v597_paired_deep_child_probe_zh.md
```

配置：

- 来源：V597 logs
- depth：1 到 3
- event time：<= 360s
- 每个 event：selected baseline + 2 alternatives
- total entries：18
- paired groups：6
- probe mode：child_probe
- probe node budget：`source_depth + 1 + 2`
- max CG iter：36
- time limit：220s

## V606 Paired Summary

输出：

```text
BPC_future/results/journey_paired_probe_summary_v606_v600_full18_20260628/
```

报告：

```text
BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_paired_probe_summary_v606_v600_full18_zh.md
```

聚合：

| metric | value |
|---|---:|
| paired groups | 6 |
| baseline entries | 6 |
| alternative entries | 12 |
| observed alternatives | 12 |
| missing result | 0 |
| positive_proxy | 0 |
| hard_negative_proxy | 0 |
| neutral_proxy | 12 |

单组结果：

| group | baseline pair | best alt | best wall gain | best profile gain | label |
|---|---:|---:|---:|---:|---|
| seed61206 d1 n2 | `[1,6]` | `[1,7]` | -0.109s | -1.412s | neutral |
| seed61206 d2 n5 | `[3,5]` | `[4,5]` | +0.813s | +0.245s | neutral |
| seed61206 d3 n9 | `[1,8]` | `[1,11]` | -0.735s | -1.025s | neutral |
| seed61717 d1 n1 | `[4,5]` | `[4,7]` | +0.003s | +0.048s | neutral |
| seed61717 d1 n2 | `[3,8]` | `[3,9]` | -0.005s | +0.108s | neutral |
| seed61718 d1 n2 | `[5,13]` | `[8,19]` | +0.903s | +0.805s | neutral |

解释：

- seed61206/61718 有微小 wall/profile 差异，但都远低于可训练阈值。
- seed61717 两组 baseline 和 alternatives 都同步 `EXTERNAL_TIME_LIMIT`，说明这个 context 下短 probe 无法区分 pair。
- gap 都没有改善。

## V605 Audit

branch-impact audit：

```text
BPC_future/results/journey_branch_impact_v605_v600_full18_paired_child_probe_20260628/
```

关键指标：

| metric | value |
|---|---:|
| branch_count | 75 |
| right_censored_branch_count | 75 |
| usable_branch_impact_training_count | 0 |
| child completion-bound retries | 218 |
| child exact pricing events | 276 |
| child certificate pricing events | 57 |
| tail classes | completion_bound_tail 35, unprocessed_children 36, negative_chain_continues 4 |

completion-tail audit：

```text
BPC_future/results/journey_completion_tail_profile_v605_v600_full18_paired_child_probe_20260628/
```

关键指标：

| metric | value |
|---|---:|
| completion retry count | 18 certified-no-negative |
| total profile generation time | 1182.359s |
| generated sequences | 49,504,585 |
| negative journeys from completion retry | 18 |
| harvest tail class | 9 harvest_returned_new_task_set, 6 expensive_no_harvest_candidate, 3 no_harvest_candidate |

这再次说明 proof-tail 成本确实重，但短 paired child-probe 没把 pair 间差异放大出来。

## 当前判断

V600-V606 的价值是工具链，而不是训练数据。

已经确认：

1. paired runbook 能稳定生成 selected baseline + alternatives；
2. forced pair 在 replay 中能匹配；
3. paired summary 能正确输出相对 wall/profile/retry gain；
4. 当前 short child-probe 采样没有产生正例。

这意味着下一步不能继续简单扩大同类 short probe。否则只会积累大量 neutral/right-censored 样本，稀释训练。

## 下一步方向

需要换成更接近闭环的 paired 标签来源。

优先级：

1. **full replay / larger-budget paired probe**
   - 对少量 high-risk context 跑更深预算；
   - 不再只给 `extra_nodes_after_branch=2`；
   - 指标看 gap、completion profile、child CB retry、是否减少 external timeout。

2. **从已有 full60 / full-open 差异中提取 paired path 标签**
   - 利用已经出现过的真实求解差异；
   - 例如 full-open 里 `511.8s -> 291.7s` 这类真实 OPTIMAL 加速路径；
   - 这比短 child-probe 更接近最终目标。

3. **proof-tail risk overlay 继续保留**
   - 对导致同步 external timeout 的 pair/context 做风险记录；
   - 但不要把 V600 这种 neutral 当正例训练。

4. **采样策略要避开“整组都超时”的 context**
   - seed61717 的两个 depth1 groups 都同步 external timeout；
   - 这种 context 可能需要更强 formulation/branch depth，而不是换一两个 pair。

## 对主目标的影响

当前目标仍未达成：

- 20-scale random-TW 还没有做到 600 秒内全量 OPTIMAL；
- V600 没有产生能直接改善 score map 的 positive pair；
- 但现在已经有了 paired probe 工具链，可以用更强的标签来源继续推进 branch score 主线。
