# V752 Dynamic SRC Route-Region Audit

日期：2026-06-29

## 背景

V736/V737/V738/V740/V750 对 seed61635 的结果已经比较一致：

- 普通 dynamic SRC 加得更多，并没有推动 `best_dual`；
- child-only SRC 不但没有解决 seed61635，还会让 seed61311 明显退化；
- seed61635 更像是 lower-bound/formulation/cut family 不够强，而不是 branch pair 权重再调一下就能解决。

因此下一步不能继续只扩大普通 SRC 数量。需要先知道：

- 哪些 task hub / pair hub 在反复形成 violated SRC；
- 哪些 active journey/task-set 在支撑这些 violation；
- 是否存在稳定的 route-region，可用于后续 route-aware / rank-1-like cut 设计。

## 本轮改动

本轮新增 `journey_cut_separation` 的 route-region 诊断字段。

### Separation 级字段

```text
route_region_audit_enabled
route_region_active_journey_count
route_region_active_task_set_count
route_region_active_route_signature_count
route_region_top_task_hubs
route_region_top_pair_hubs
route_region_top_active_task_sets
```

这些字段只读 active RMP support 和 violated SRC candidates，记录 repeated hub/region。

### Candidate 级字段

`top_candidates` 每个候选新增：

```text
activity
active_overlap_journey_count
active_overlap_task_set_count
active_overlap_route_signature_count
active_overlap_max_value
active_overlap_top_task_hubs
active_overlap_top_task_sets
```

这使我们能区分：

- violation 是由少数高权重 task-set 撑起来；
- 还是由很多 route/task-set 分散贡献；
- 是否存在某个 hub/pair 在不同节点反复出现。

### Summarizer

`BPC_future/scripts/summarize_journey_dynamic_src_audit.py` 已同步读取新字段，输出：

```text
global_route_region_task_hubs
global_route_region_pair_hubs
run.route_region_task_hubs
run.route_region_pair_hubs
candidate.active_overlap_*
```

## Exact-Safe 边界

本轮没有新增任何 cut，也没有改变 existing SRC 的加入逻辑。

不改变：

- official lower bound；
- pricing certificate；
- fathom/prune；
- branch selection；
- cut gate；
- RMP formulation。

`route_region_audit_enabled` 是诊断字段；即使启用，也只是多写日志。

## 验证

已通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/summarize_journey_dynamic_src_audit.py \
  BPC_future/tests/test_bpc_future.py
```

已通过：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_audit_logs_violations_without_adding_cuts \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_cut_gate_blocks_low_violation_addition \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_min_add_depth_delays_root_cut_addition \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_cuts_are_branch_depth_opt_in
```

结果：

```text
Ran 4 tests
OK
```

## 对主线的意义

V752 不会直接让 20-scale 更多实例 OPTIMAL，但它补上了 stronger cuts/formulation 设计缺失的证据层。

下一次跑 seed61635 或 full60 hard cases 时，可以用 summarizer 直接回答：

1. ordinary SRC 是否总围绕同一批 task hub；
2. violated cut 的贡献是否集中在少数 active route/task-set；
3. 是否值得设计 route-aware / rank-1-like cut；
4. cut family 是否应与 branch state/depth 绑定。

## 下一步

1. 用 V752 字段对 V750/V736/V737/V738/V740 现有日志做一次汇总复盘。
2. 如果 seed61635 的 route-region hub 高度集中，优先设计 route-aware/rank-1-like diagnostic cut prototype。
3. 如果 hub 不集中，说明问题可能更偏 formulation/incumbent/branch-tree width，而不是某个局部 cut region。
4. 后续任何 live cut 原型都必须先证明 pricing coefficient 与 reduced-cost updater exact-safe。
