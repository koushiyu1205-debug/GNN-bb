# 20260627 V474-V477：V468 剩余失败分型与恢复性 smoke

## 结论

V468 仍是当前 random-TW 20-scale full-60 最好结果：

- `33/60 OPTIMAL`
- capped mean `348.26s`
- `<=200s OPTIMAL = 22`
- 仍有 `27/60` 未最优

V474-V477 没有产生新的可上线加速配置，但把剩余失败的主因分清了：

1. 剩余失败主因不是单纯 root pair 正例不够。
2. `27` 个未解中，`24` 个是 `branch_tree_plus_completion_tail`。
3. tail-minfill depth4 已真实触发，但没有救回最重的 4 个实例。
4. 从旧消融中恢复出来的两个 root pair，在当前代码下 forced-root replay 也没有复现 OPTIMAL。

因此下一步不能继续盲目扩大 root top-k 或裸开 GAT 分数。主线应转为深层 branch path、child ordering、completion retry/proof CPU 的反事实标签。

## V474 失败分型

输出：

- `BPC_future/results/journey_failure_typing_v474_v468_full60_20260627/summary.json`
- `BPC_future/results/journey_failure_typing_v474_v468_full60_20260627/failure_typing_rows.csv`
- `BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_failure_typing_v474_v468_full60_zh.md`

核心计数：

```text
status:
  OPTIMAL = 33
  TIME_LIMIT = 3
  EXTERNAL_TIME_LIMIT = 24

primary failure type on 27 unsolved:
  branch_tree_plus_completion_tail = 24
  completion_bound_proof_cost = 2
  lp_bound_below_incumbent = 1

failure tags:
  early_branch_before_final_probe_disabled = 27
  completion_bound_proof_cost = 26
  branch_tree_right_censored = 24
  negative_chain_continues = 24
  lp_bound_below_incumbent = 23
  branch_tree_too_wide_or_deep = 22
```

解释：

- `before_final_probe early branch` 确实有很多机会，但这不是充分解释；因为同一批实例还有大量深层分支右删失和 completion-bound retry。
- 对这些实例，简单提前分支很可能只是把 proof tail 从父节点搬到子树。
- GAT 需要学的不是“root 选哪个 pair”一个动作，而是“这条 branch path 后续是否能快速闭环”。

## V475 Tail-Minfill Depth4 Smoke

配置：

- V468 的 V467 conservative overlay branch-score
- early branch off
- admission off
- `journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True`
- `tail_min_fill=4`
- `tail_min_fill_max_depth=4`
- `final_probe_only=True`

测试 4 个 V474 completion profile time 最高的未解实例：

```text
tranq sector seed61206      EXTERNAL -> EXTERNAL
tranq greedy seed61744      EXTERNAL -> EXTERNAL
tranq greedy seed61206      EXTERNAL -> EXTERNAL
tranq random seed61309      EXTERNAL -> EXTERNAL
```

V476 审计确认开关确实生效：

```text
completion_retry_tail_min_fill_applied_count = 82
completion_retry_tail_min_fill_candidate_count = 82
completion_retry_tail_min_fill_optin_disabled_count = 0
completion_retry_total_profile_generation_time = 1323.63s
branch_count = 73
right_censored_branch_count = 73
child_completion_bound_retries = 316
```

结论：

tail-minfill 能改变 exact negative-column harvest 节奏，但对这 4 个最重失败没有形成闭环。它不是当前 60/60 的主杠杆。

## V477 旧成功 Root Pair 恢复

从 20260626 消融结果中，发现 V468 未解但旧配置已解的实例只有 2 个：

```text
tranq random seed61309:
  off/tasks020/branch_only = OPTIMAL 462.02s
  off/tasks020/branch_admission = OPTIMAL 466.58s

tranq sector seed61513:
  on/tasks020/branch_only = OPTIMAL 354.44s
  on/tasks020/branch_admission = OPTIMAL 347.37s
```

抽日志发现旧成功 run 中 `selected_pair_changed=0`，说明旧成功并不是 branch-score 显式覆盖了 root pair，而是旧 run 的默认分支路径/RMP 轨迹与 V468 当前轨迹不同。

当前代码下 forced-root replay：

```text
tranq random seed61309 force_pair:2,5  -> EXTERNAL 600s
tranq sector seed61513 force_pair:3,19 -> EXTERNAL 600s
```

结论：

这两条不能作为 root overlay 严格正例。旧成功如果要复用，需要提取并复现更深 branch path，或者把它作为“深层分支路径标签”的来源，而不是 root pair 标签。

## 对主线的修正

当前最有效的方向应改成：

1. 深层 branch path replay
   - 从已 OPTIMAL run 中抽完整 branch path。
   - 对 V468 未解但相似 context 的实例，做 limited forced-depth/path replay。
   - 标签不只看 root pair，而看 child proof CPU、completion retry、time-to-certificate。

2. child ordering / subtree proof-cost 模型
   - 当前 24 个失败都有明显右删失，说明选完 pair 后处理哪个 child、何时停止某个 child，同样关键。
   - GAT 应学习 child proof cost 和 certificate speed，而不是只给 pair 打分。

3. completion-tail 继续做诊断，不作为主加速线
   - V475 已证明 depth4 tail-minfill 对最重 4 个无效。
   - 可以保留为辅助特征或特定 root-tail 正例调度，但不要作为全量 20 的主线。

4. 对 `lp_bound_below_incumbent` 和宽平台节点，转 incumbent/cuts/formulation
   - pricing proof 不能让 `z_RMP < UB` 的节点直接 fathom。
   - 这类节点需要更好 incumbent、有效割或更强分支。

## 当前状态

本轮新增了只读分型脚本：

- `BPC_future/scripts/audit_journey_failure_typing.py`

它只合并已有日志和审计结果：

- 不运行 BPC / pricing / RMP
- 不影响 official bound
- 不产生 certificate
- 不参与剪枝

V468 仍是 best；V475/V477 都是 hard-negative 诊断结果。
