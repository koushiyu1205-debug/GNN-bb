# V567/V568：两类 retry 的 on/off/gate-cap 对比与当前优化判断

## 背景

这轮实验必须分清两类 retry：

1. 普通 no-column 补救 retry
   - 日志事件：`journey_exact_pricing_retry`
   - 作用：普通 exact pricing 不完整或 no-column 后，再尝试用真实 reduced cost 找负列。
   - 边界：它不能给 certificate；只能加入真实 RC 验证过的列。

2. completion-bound / final-judge retry
   - 日志事件：`journey_exact_pricing_completion_bound_retry`
   - 作用：用 completion-bound / direct-label final judge 尝试证明没有遗漏负列，或者发现隐藏负列。
   - 边界：只有完成并返回合法 certificate 时才支持节点闭合；gate/cap/off 都不能提供 official bound 或剪枝依据。

本轮只控制第二类 retry，普通 no-column 补救 retry 始终保持开启。

## 实验设置

实例：4 个 random-TW canonical 20-scale V545 难例。

结果目录：

- V567 三组对比：`BPC_future/results/20260628_v567_retry_on_off_gate_cap_smoke4_tasks20/`
- V568 修复后 gate/cap：`BPC_future/results/20260628_v568_retry_gate_cap_profile_trigger_fix_smoke4_tasks20/`

三组策略：

- `retry_on`：保持 V545 final-judge retry 行为。
- `retry_off`：关闭 final-judge retry，并关闭 required completion-bound，仅用于对照。
- `retry_gate_cap`：开启 certificate-aware retry gate/cap，保留 exact-safe 边界。

## V567 结果

| 组别 | OPTIMAL | EXTERNAL_TIME_LIMIT | TIME_LIMIT | mean wall | gap 可用 | final retry | cap applied | gate events | branch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| retry_on | 0/4 | 4/4 | 0/4 | 600.03s | 4/4 | 116 | 0 | 0 | 104 |
| retry_off | 0/4 | 0/4 | 4/4 | 37.56s | 0/4 | 0 | 0 | 0 | 0 |
| retry_gate_cap | 0/4 | 3/4 | 1/4 | 595.55s | 4/4 | 114 | 7 | 5 | 101 |

关键判断：

- `retry_off` 不是优化。它很快返回，但全部 `no_exact_dual_bound`，没有可用 gap，也没有 certificate。
- `retry_gate_cap` 没有带来完整求解改善。只有 seed61717 从外部 600s 变成内部 582s，但 gap 从 `0.036955` 退到 `0.039594`，不是有效加速。
- gate/cap 只在 seed61717 的 `no_retry_budget` trigger 上明显生效；其他实例几乎没有触发。

## 代码缺口

V567 暴露了一个统计覆盖问题：

- `profile_exhausted_no_column` 是大量 proof-tail retry 的 trigger；
- 但 node 内这条路径执行 completion-bound retry 后，没有调用 `note_completion_bound_retry(...)`；
- 因此 cap/gate 的 context history 一直是 0，表现为大量 `insufficient_observations`。

已修复：

- 在 node 内 `profile_exhausted_no_column` retry 后补 `note_completion_bound_retry(...)`；
- 在 `profile_exhausted_no_column_escalation` retry 后也补同样统计；
- 只补日志/统计链路，不改变 pricing、bound、certificate 或剪枝逻辑。

定向测试通过：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
python -m unittest ... retry gate/cap 相关 8 个用例
```

## V568 修复后结果

| 实例 | status | wall | gap | final retry | cb profile | cap applied | gate | branch | score missing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| seed61717 | TIME_LIMIT | 577.25s | 0.039594 | 8 | 248.06s | 7 | 5 | 6 | 5 |
| seed61103 | EXTERNAL_TIME_LIMIT | 600.02s | 0.026290 | 21 | 216.90s | 0 | 0 | 14 | 13 |
| seed61206 | EXTERNAL_TIME_LIMIT | 600.02s | 0.085809 | 22 | 316.08s | 0 | 0 | 20 | 19 |
| seed61718 | EXTERNAL_TIME_LIMIT | 600.02s | 0.043777 | 64 | 203.86s | 0 | 0 | 62 | 61 |

V568 相对 V567 的变化：

- `profile_exhausted_no_column` 已经能形成 history；
- seed61206：`t=profile_exhausted_no_column max_total=21`；
- seed61718：`t=profile_exhausted_no_column max_total=62`；
- 但 cap 仍不触发，因为这些 history 主要是 certified zero-harvest，且 profile time 低于 `20s` expensive 阈值。

这说明统计修复是必要的，但不是直接加速。

## V569 补充：降低 root score gate 阈值不可行

为排除“只是 branch score gate 阈值过高”的可能性，追加了一个受控 smoke：

- 结果目录：`BPC_future/results/20260628_v569_v543_root035_strict_state_smoke4_tasks20/`
- score map：V543 merged overlay；
- `journey_branch_candidate_score_require_state_key=True`；
- `journey_branch_candidate_score_selection_gate_min_score=0.35`；
- retry gate/cap、early branch、admission 全部关闭。

这组只测试 branch ordering，不改变 bound、certificate 或剪枝。

结果：

| 实例 | status | wall | gap | primal | dual | gap source |
|---|---:|---:|---:|---:|---:|---|
| seed61717 | EXTERNAL_TIME_LIMIT | 600.02s | 0.037603 | 614.965804 | 591.841542 | `root_corrected_node_bound` |
| seed61103 | EXTERNAL_TIME_LIMIT | 600.02s | 0.026290 | 580.681229 | 565.415232 | `root_corrected_node_bound` |
| seed61206 | EXTERNAL_TIME_LIMIT | 600.02s | 0.086396 | 501.500258 | 458.172676 | `root_corrected_node_bound` |
| seed61718 | EXTERNAL_TIME_LIMIT | 600.02s | 0.043777 | 664.008983 | 634.940487 | `root_corrected_node_bound` |

对照 V568：

- V568：`3/4 EXTERNAL_TIME_LIMIT + 1/4 TIME_LIMIT`，capped mean `594.31s`；
- V569：`4/4 EXTERNAL_TIME_LIMIT`，capped mean `600.00s`；
- dual bound 基本一致，gap 均值从 `0.0488675` 到 `0.0485165`，没有求解闭环收益。

重要现象：

- V569 的 run log 为空，这是 `--quiet` 模式下正常现象；
- JSONL event 实际已经可靠落盘，只是路径按实例名深层嵌套在 `logs/BPC_future/logical_graph/.../*.jsonl`；
- branch decision event 中能看到 root 4 个实例全部通过 `score>=0.35` gate 并改变 selected pair；
- 但 4 个实例最终仍全部 `EXTERNAL_TIME_LIMIT`，因此这些 root 中等分数选择应作为 hard negative，而不是放宽阈值的依据。

已导出训练/采样证据：

- evidence 目录：`BPC_future/results/20260628_v569_branch_timeout_evidence/`
- root hard negative：`root_timeout_hard_negative_rows.jsonl`，4 行；
- deep missing context：`deep_missing_context_rows.jsonl`，193 行；
- summary：`summary.json`。
- 生成脚本：`BPC_future/scripts/build_journey_branch_timeout_evidence.py`。

判断：

降低 root score gate 阈值不是当前突破口。即便 root 有一些中等分数候选，20-scale proof tail 的主要缺口仍在深层 branch context coverage 和 child proof-cost 标签，而不是把现有 root score 放宽。

## 当前结论

不能关 retry。

`retry_off` 的短时间只是放弃 final-judge certificate，结果没有 exact dual bound，也没有 gap。它不能作为生产策略，也不能当训练正例。

当前 gate/cap 不能独立优化完整求解。

它能在 seed61717 上减少一部分 final-judge retry，但没有带来 OPTIMAL，也没有改善 gap；在另外 3 个实例上，修复后也没有触发有效 cap，因为这些 retry 不是昂贵 incomplete tail，而是相对便宜的 certified no-negative retry。

真正意料之外的点：

- proof-tail 不是单纯“final-judge retry 太多”；不少 retry 是合法且相对便宜的 certificate。
- 当前 score map 在深层几乎失效：V568 中 branch score missing 为 `98/102`，branch score gate pass 为 0。
- retry gate 想转 branch 时，多数被 `missing_score_source` 拦住；这反而是正确的 exact-safe 行为，说明不能裸 branch。
- 仅降低 root score gate 阈值没有带来闭环收益；现有中等分数不能直接扩大使用。
- run log 不是 event log；后续分析必须直接读深层 JSONL，否则会误判 timeout 下没有 branch event。

## 下一步优化方向

1. 保留 retry on 作为安全默认

final-judge retry 仍是 certificate 路径，不能全关。后续 `retry_off` 只保留为诊断对照。

2. retry controller 只处理真正昂贵的 incomplete tail

不要把 certified zero-harvest 当坏样本。当前 certificate-aware 逻辑是对的，应该继续保留：

- certified zero-harvest 更新 `certified_zero_harvest_profile_time_max`；
- expensive incomplete zero-harvest 才触发 hard gate；
- cap floor 至少是历史 certificate profile max + margin。

3. 补深层 branch score coverage

当前主要瓶颈不是 retry 开关，而是 proof-tail 分支闭环缺 score：

- root 有少量 score；
- depth 1/2/3/4 基本 missing；
- gate 想转 branch 时无法安全判断 pair。

下一步应把 V567/V568 的深层 branch events 和 child completion-bound retry 后果转成训练数据，重点标注：

- branch_state_key；
- child completion-bound retry count/profile time；
- child certificate / incomplete；
- child gap/primal 改善；
- gate 后是否 score missing。

4. retry gate/cap 后续实验条件

不要直接上 full60。先满足：

- profile_exhausted_no_column history 确认非 0；
- deep branch score coverage 明显提升；
- score-gated branch fallback 至少有一批 non-root context 能通过；
- smoke 中至少不退化 gap，且 final retry profile 或 branch tree 有明显改善。

## 当前优化思路

主线仍应是 Branch Score，而不是 retry-off。

retry controller 的角色是辅助：识别“明显昂贵、无收获、且已有替代 branch score”的 final-judge retry，然后 exact-safe 地转 branch 或降预算。真正让 20-scale 进入 600s/200s 目标，需要让 GAT 学会深层 Ryan-Foster pair 对 child proof cost/certificate time 的影响。
