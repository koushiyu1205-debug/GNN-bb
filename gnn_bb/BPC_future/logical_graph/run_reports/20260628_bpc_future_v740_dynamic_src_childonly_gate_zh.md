# V740 Dynamic SRC Child-Only Gate

日期：2026-06-28

## 目的

V737/V738 显示 seed61635 不是“多加普通 SRC”能解决，且 stronger root SRC 可能改变 root branch pair 并带来更差路径。V740 因此测试一个 branch-preserving 变体：

```text
journey_dynamic_subset_row_min_add_depth=1
```

含义：

- root 仍做 dynamic SRC audit；
- root 不注册 dynamic SRC；
- depth >= 1 的 child 才允许通过 gate 后注册 dynamic SRC。

这个开关只控制有效 cut 的加入时机，不产生 official bound、不产生 certificate、不参与剪枝。

## 代码改动

在 `journey_driver.py` 的 `_separate_journey_subset_row_cuts` 增加：

```text
journey_dynamic_subset_row_min_depth
journey_dynamic_subset_row_min_add_depth
cut_add_depth_min
cut_add_depth_passed
cut_add_depth_reason
```

当 `depth < journey_dynamic_subset_row_min_add_depth` 时：

- 仍可枚举 violation 并写 `journey_cut_separation`；
- `added=0`；
- `cut_gate_reason=add_depth_below_min`；
- parent/ledger/RMP/certificate 逻辑不变。

新增测试：

```text
test_journey_dynamic_subset_row_min_add_depth_delays_root_cut_addition
```

已验证 root depth=0 不加 cut，depth=1 正常加 cut。

## 实验设置

对照 V736：

- 实例：greedy-anchor hard2
  - `tasks020_04_seed61311`
  - `tasks020_07_seed61635`
- time limit: `600s`
- max workers: `2`
- branch: `routeopt_bkf_staged`
- dynamic SRC: audit + cut-on + gate
- gate: `min_violated=1`, `min_best_violation=0.25`

V740 唯一区别：

```text
journey_dynamic_subset_row_min_add_depth=1
```

输出：

- `BPC_future/results/20260628_v740_dynamic_src_childonly_gated_hard2_600/results.csv`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_v740_dynamic_src_childonly_audit_summary_zh.md`

## 结果对比

| seed | config | status | wall | gap | nodes | pricing | exact pricing | SRC added | branch | fathom | CB retry |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 61311 | V736 root+child gated SRC | OPTIMAL | 110.914 | 0.000000 | 7 | 59 | 30 | 20 | 5 | 6 | 7 |
| 61311 | V740 child-only gated SRC | OPTIMAL | 360.263 | 0.000000 | 21 | 158 | 97 | 9 | 10 | 11 | 62 |
| 61635 | V736 root+child gated SRC | EXTERNAL_TIME_LIMIT | 600.019 | 0.060588 | - | - | - | 9 | 26 | 12 | 40 |
| 61635 | V740 child-only gated SRC | EXTERNAL_TIME_LIMIT | 600.019 | 0.060588 | - | - | - | 6 | 31 | 1 | 68 |

V740 cut audit：

```text
seed61311 root: violated=8, added=0, reason=add_depth_below_min
seed61311 depth1: added=9

seed61635 root: violated=1, added=0, reason=add_depth_below_min
seed61635 depth1: added=6
```

## 判断

V740 是一个负结果，但信息量很高。

1. root SRC 不能简单关掉。

seed61311 仍能 OPTIMAL，但 wall 从 `110.914s` 退化到 `360.263s`，nodes 从 `7` 增到 `21`，exact pricing 从 `30` 增到 `97`，CB retry 从 `7` 增到 `62`。这说明 root SRC 对这个实例不是小修小补，而是早期改变了整个 proof landscape。

2. child-only SRC 没有解决 seed61635。

seed61635 的 dual/gap 仍是：

```text
dual = 526.651393
gap  = 0.060588
```

而且 fathom 从 V736 的 `12` 降到 `1`，CB retry 从 `40` 增到 `68`。这说明 seed61635 的瓶颈不是 root 普通 SRC 是否提前加入，而是普通 SRC family 本身不够强，或 branch-cut 组合没有打中有效区域。

3. cut 与 branch 必须联合测试。

V740 root 不加 SRC 后，root branch 由 phased testing 选择：

```text
seed61311: [2,8]
seed61635: [1,9]
```

V737/V738 已经显示“更多 root SRC”也可能改变 root pair 并走坏路径。因此正确方向不是固定 root 加/不加，而是让 branch controller 看到 cut regime：

```text
pair under no-root-cut
pair under root-gated-SRC
pair under child-only-SRC
```

然后比较两个 child 的 LP gain、width balance、fathom、CB retry 和 gap。

## 下一步

1. 不采用 child-only SRC 作为默认主线。

V740 对 seed61311 明显退化，对 seed61635 无改善。

2. 保留 `journey_dynamic_subset_row_min_add_depth` 作为实验开关。

它有助于后续隔离 root cut 对 branch pair 的影响，但不是当前 best config。

3. 下一步应做 branch-cut joint testing。

优先实现/测试：

```text
phase1 branch LP probe + dynamic SRC snapshot
```

对 top-K pair 同时记录：

- no-cut child LP gain；
- root-gated-SRC child LP gain；
- child-only-SRC child LP gain；
- child width balance；
- expected CB retry risk；
- cut family/task hubs。

4. seed61635 需要更强 cut family。

V736/V737/V738/V740 都显示普通 dynamic SRC 不推动 dual，因此下一阶段应进入：

- route-aware/rank-1-like cut audit；
- limited-memory cut coefficient / RC updater 原型；
- repeated hub task region cut；
- branch pair 与 cut family 的联合选择。

## 验证

已通过：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py BPC_future/scripts/summarize_journey_dynamic_src_audit.py
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_min_add_depth_delays_root_cut_addition \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_cut_gate_blocks_low_violation_addition \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_audit_logs_violations_without_adding_cuts
```

## Exact-Safe

V740 的新开关只影响 valid dynamic SRC 的加入时机。它不会：

- 把 RMP objective 当 exact bound；
- 生成 learned certificate；
- 使用 audit result 剪枝；
- 改写 child lower bound exactness。

OPTIMAL/TIME_LIMIT 结论仍来自 solver finish event / external timeout 与真实 pricing closure。
