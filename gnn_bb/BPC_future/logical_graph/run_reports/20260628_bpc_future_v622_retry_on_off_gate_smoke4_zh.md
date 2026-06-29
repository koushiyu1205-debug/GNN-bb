# 20260628 V622：Retry On / Off / Gate Smoke4 对比

## 目的

本轮只比较 retry 策略，不改变实例集、branch score 背景和 admission 设置。

必须区分两类 retry：

1. `ordinary_incomplete_no_column`
   - 事件：`journey_exact_pricing_retry`
   - 作用：普通 exact pricing 返回 incomplete/no-column 后的补救 retry。
   - 本轮三组都保持打开，避免把补救 retry 与 final judge 混在一起。

2. `completion_bound_final_judge`
   - 事件：`journey_exact_pricing_completion_bound_retry`
   - 作用：completion-bound / final-judge 证明 retry；可能找到 hidden negative，也可能给出 `CERTIFIED_NO_NEGATIVE` 证书。
   - 本轮比较 on / off / gate。

Exact-safe 边界：

- retry gate 只改变是否继续执行 final-judge retry，或转为 exact-safe branch；
- 不把当前 RMP objective 当 official bound；
- 不用 gate 结果剪枝；
- gate branch child 仍继承非 exact lower bound，后续必须靠 exact pricing closure。

## 代码修正

- 在 retry 日志中新增 `retry_class`：
  - `ordinary_incomplete_no_column`
  - `completion_bound_final_judge`
- 补齐 `profile_exhausted_no_column` 和 escalation 入口的 completion-bound retry gate 检查。
- 新增单测：ordinary `exact_retry` 不会更新 completion-bound retry gate 历史。

验证：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_is_opt_in_and_requires_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_blocks_expensive_zero_harvest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_keeps_harvest_signal \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_ignores_ordinary_retry_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_context_scope_isolates_depth_trigger \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_is_opt_in_and_contextual \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_keeps_unseen_context_uncapped
```

结果：`Ran 7 tests ... OK`。

## 实验设置

输出目录：

```text
BPC_future/results/20260628_v622_retry_on_off_gate_smoke4_tasks20/
```

实例：复用 V620 的 4 个 20-scale hard smoke 实例。

共同配置：

- `moon_trek_20_smoke.yaml`
- 外部时限 `600s`
- `max_workers=4`
- V617 score map
- `journey_branch_candidate_score_max_depth=2`
- admission off
- early branch off
- ordinary incomplete/no-column retry on

对比组：

1. `retry_on`
   - completion-bound final-judge retry on
   - retry gate off

2. `retry_off`
   - completion-bound final-judge retry off
   - ordinary retry 仍 on

3. `retry_gate`
   - gate 只看 expensive incomplete zero-harvest

4. `retry_gate_total_profile120`
   - depth+trigger context 累计 profile time 上限 120s

5. `retry_gate_global_profile120`
   - global context 累计 profile time 上限 120s

## 结果

### Wall-Time / Gap

```text
retry_on:
  status = 4/4 EXTERNAL_TIME_LIMIT
  mean wall = 600.021s
  gaps = 0.051215, 0.061278, 0.034203, 0.043777

retry_off:
  status = 4/4 TIME_LIMIT
  mean wall = 15.255s
  gap = unavailable
  reason = no_exact_dual_bound

retry_gate:
  status = 4/4 EXTERNAL_TIME_LIMIT
  mean wall = 600.020s
  gaps unchanged

retry_gate_total_profile120:
  status = 4/4 EXTERNAL_TIME_LIMIT
  mean wall = 600.020s
  gaps unchanged

retry_gate_global_profile120:
  status = 4/4 EXTERNAL_TIME_LIMIT
  mean wall = 600.021s
  gaps unchanged
```

### Retry Events

```text
retry_on:
  completion-bound retry = 175
  ordinary retry = 3
  CB states = CERTIFIED_NO_NEGATIVE 170, FOUND_NEGATIVE 5
  CB profile time = 1116.709s
  branch nodes = 162
  fathom events = 8

retry_gate:
  completion-bound retry = 174
  ordinary retry = 4
  CB states = CERTIFIED_NO_NEGATIVE 169, FOUND_NEGATIVE 5
  CB profile time = 1113.858s
  gate events = 0

retry_gate_total_profile120:
  completion-bound retry = 175
  ordinary retry = 3
  CB states = CERTIFIED_NO_NEGATIVE 170, FOUND_NEGATIVE 5
  CB profile time = 1111.753s
  gate events = 0

retry_gate_global_profile120:
  completion-bound retry = 84
  ordinary retry = 1
  gate events = 203
  gate action = branch 203
  CB states = CERTIFIED_NO_NEGATIVE 82, FOUND_NEGATIVE 2
  CB profile time = 499.610s
  branch nodes = 240
  fathom events = 0
```

## 解释

### 1. 关掉 completion-bound retry 不可行

`retry_off` 很快结束，但不是求解变快，而是没有合法 exact dual bound：

```text
status = TIME_LIMIT
gap_unavailable_reason = no_exact_dual_bound
```

这说明 completion-bound/final-judge retry 仍是证书路径的一部分。直接关闭会 fail closed，不能证明最优，也不能给出可用 gap。

### 2. 当前 retry 大多不是“失败重试”

`retry_on` 的 175 次 completion-bound retry 中：

- 170 次给出 `CERTIFIED_NO_NEGATIVE`
- 5 次找到负列

所以这批 retry 不是大量无效失败；它们是在很多 child/node 上反复做必要证明。问题不是“一个坏 retry 无限重试”，而是搜索树产生了很多需要证明的节点。

### 3. 细粒度 gate 没有触发

`retry_gate` 和 `retry_gate_total_profile120` 没有 gate event。

原因：

- 单次 retry 平均 profile time 不高；
- 按 depth+trigger 分桶后，累计 profile time 被分散；
- expensive incomplete zero-harvest 不是这 4 个 hard 实例的主形态。

### 4. 全局 gate 能降 retry 成本，但不能降 wall time

`retry_gate_global_profile120` 把 completion-bound retry 从 175 降到 84，profile time 从 1116.709s 降到 499.610s，说明 gate 能减少 final-judge 成本。

但结果仍然 4/4 外部超时，并且 branch nodes 从 162 增加到 240，fathom events 从 8 降到 0。

这表示 gate 省下的 final-judge 时间被更多 exact-safe branch/search 吃回去了。换句话说，gate 只是把证明压力从 “final judge retry” 转移到了 “更多 child 证明”，没有改善闭环能力。

## 当前判断

retry gate 可以作为成本阀，但不是当前 hard 20-scale 的主加速杠杆。

它适合做：

- 防止明显无收益的 global proof tail 无限消耗；
- 给日志提供 retry pressure / proof pressure 标签；
- 在未来 branch score 更可靠后，作为 branch/continue-final-judge 的动作选择器。

它暂时不适合做：

- 默认替代 completion-bound final judge；
- 单独承担 20-scale 求最优加速；
- 用 total profile cap 粗暴全局 branch。

## 意料之外的点

比较意外的是：completion-bound retry 的大多数结果是 `CERTIFIED_NO_NEGATIVE`，不是 incomplete 失败。

这改变了优化判断：

- 之前直觉是“retry 很贵，所以关掉或 gate 掉可能快”；
- 实际上这些 retry 多数在做合法证明；
- 真正问题是 branch/score 产生的子节点太多，每个子节点都要消耗 final-judge certificate。

另一个意外点是：全局 gate 明显减少 retry CPU 后，wall time 完全没有改善。这说明系统当前不是单点 final-judge 热点，而是 branch tree / child proof cost 的结构性问题。

## 后续优化方向

1. branch decision 仍是主线
   - 需要学习哪个 Ryan-Foster pair 能减少 child proof 总量；
   - 标签要更重视 `child_completion_bound_retry_count`、`child_proof_cpu`、`child_time_to_certificate`；
   - 不是只看 pair score 是否高。

2. retry gate 改为诊断和辅助动作
   - 保留 `retry_class` 和 gate 日志；
   - 默认不启用 global hard cap；
   - 后续可让 GAT/tail controller 学习 `continue final judge` vs `branch`，而不是固定阈值。

3. 优化 final-judge 证明复用
   - 当前很多 `CERTIFIED_NO_NEGATIVE` 是跨 child 重复证明；
   - 应检查 completion-bound / direct-label profile cache 是否能跨 sibling 复用更多状态；
   - 重点不是减少一次 retry，而是减少相似 child 的重复 certificate cost。

4. branch score 需要惩罚 proof-tail 扩张
   - `retry_gate_global_profile120` 中 branch nodes 变多，说明简单 early branch 会扩大树；
   - score map 需要把 “分支后 child 数量和证书成本” 作为硬负标签，而不只是 wall-time gain。

5. gap 记录继续保留
   - retry_on / gate 的外部超时仍可从 root corrected bound 得到 gap；
   - retry_off 无 exact dual bound，gap 不可用，这是重要负面信号。

## 结论

本轮结果不支持把 retry gate 作为主优化方向。

可以优化的是：减少一部分 final-judge retry CPU。

不能解决的是：20-scale hard proof tail 的完整闭环。当前瓶颈更像是 branch tree 质量和 child certificate 复用不足，而不是 completion-bound retry 本身失控。
