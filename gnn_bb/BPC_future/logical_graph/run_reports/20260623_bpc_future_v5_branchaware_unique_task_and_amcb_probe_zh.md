# BPC_future V5 branch-aware unique-task 与 AMCB 探针

日期：2026-06-23

## 目的

验证 20 规模 canonical random-TW `seed61000` 的 branch proof tail 是否主要来自 final-probe frontier suffix bound 中的 branch 松弛。

本轮只做 exact-safe bound 收紧，不改变 GAT 证书边界：

- GAT 继续用于 true-RC filter / support-aware admission；
- 不用 GAT 做 pruning 或 certificate；
- branch-aware unique-task 只收紧 optimistic lower bound；
- corrected-bound fathom 仍只在 opt-in 且 proof artifact valid 时触发。

## 代码改动

`_UniqueTaskVisitLowerBound` 新增 branch-aware 查询：

- `branch_value`
- `branch_incoming_value`
- `branch_outgoing_value`

规则：

- `same_vehicle(i,j)`：未选中时按组件整体作为 optional group；当前 journey 已含组件一部分时，缺失部分视为 forced；
- `separate_vehicle(i,j)`：当前 journey 已含一侧时，从剩余可选 mask 中排除另一侧；
- forced same 组件不可补齐时返回 `inf`，允许 exact-safe prune；
- 无 branch constraints 时回退原 `value/incoming/outgoing`。

接线范围：

- partial sortie completion-bound pruning；
- completed journey suffix pruning；
- direct-label heap priority；
- open frontier lower-bound scan；
- frontier ledger active-token diagnostics。

## 验证

通过：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m compileall -q \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/tests/test_bpc_future.py
```

通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_unique_task_branch_value_groups_same_vehicle_components \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_open_label_frontier_lower_bound_scans_active_heap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_mainline_learning_anchor_configs_are_exact_safe
```

通过：

```bash
git diff --check -- BPC_future/pricing/journey_pricing.py BPC_future/tests/test_bpc_future.py
```

## V5 branch-aware unique-task 300s 探针

实例：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
```

输出：

- CSV: `BPC_future/results/20260623_v5_branchaware_unique_task_300b_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v5_branchaware_unique_task_300b_randomtw20_seed61000/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl`

结果：

- status: `EXTERNAL_TIME_LIMIT`
- wall: `300.023155s`
- 200 秒内未 OPTIMAL；
- corrected-bound fathom: `0`。

与 V4 support-aware GAT 300s 对比：

| 指标 | V4 | V5 branch-aware |
|---|---:|---:|
| root CB certificate time | `105.698614s` | `104.934808s` |
| node 1 CB time | `181.373387s` | `181.254894s` |
| node 1 `global_remaining_rc_lb` | `-426.051783667` | `-412.683770667` |
| node 1 suffix winner | `unique_task` | `unique_task` |
| node 1 suffix LB | `-364.336188667` | `-350.968175667` |
| node 1 corrected node LB | `-6662.658868667` | `-6435.402647667` |
| node 2 CB certificate time | `233.308815s` | `233.885283s` |

结论：

branch-aware unique-task 是正确方向，但收益很小：

- node 1 `global_remaining_rc_lb` 只收紧约 `13.368013`；
- corrected node LB 仍极低，完全不能剪枝；
- tail bottleneck 仍未解决。

关键发现：

node 1 final probe 的 `direct_label_completion_bound_unique_route_enabled=False`。原因是 20 个任务超过默认 `unique_route_max_tasks=16`，所以真正更强的 route-aware helper 没参与；最后仍由较松的 unique-task helper 主导 frontier LB。

## AMCB opt-in 300s 探针

配置额外打开：

```text
journey_available_mask_completion_bound_enabled=true
```

输出：

- CSV: `BPC_future/results/20260623_v5_branchaware_amcb_300_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v5_branchaware_amcb_300_randomtw20_seed61000/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl`

结果：

- status: `EXTERNAL_TIME_LIMIT`
- wall: `300.038439s`
- 200 秒内未 OPTIMAL；
- root CB certificate time 从 V5 的 `104.934808s` 变慢到 `130.663574s`；
- node 1 CB time 为 `200.059707s`；
- node 1 `global_remaining_rc_lb=-414.107463667`，比 V5 branch-aware 的 `-412.683770667` 更差；
- node 1 suffix winner 仍是 `unique_task`；
- AMCB 在 root/node2 因 `state_budget` disabled，在 node1 因 `deadline` disabled。

结论：

全局打开 AMCB 不是可用主线：

- 开销明显增大；
- 没有成为 suffix winner；
- 没有改善 corrected bound；
- state/deadline budget 容易打满。

## 当前判断

V5 说明 branch-aware unique-task 能修掉一小部分 branch 松弛，但 20 规模 proof tail 的主因仍是 frontier suffix bound 与 branch-node fathom 水位之间的 gap：

- unique-route 默认因 `max_tasks=16` 不覆盖 20 任务；
- 全局 unique-route 20 的历史探针会显著拖慢 root；
- 全局 AMCB 也会打满 budget；
- 因此下一步不应全局打开更重 bound，也不能只盯一个最差 token；应先计算当前 `fathom_rc_target`，只对阻碍达到水位的 critical tokens 做局部收紧。

V7 后续修正：

1. 若 `z_RMP < UB - eps`，即使所有 token 都证明到 `g>=0` 也不能 fathom，应跳过 final-probe refinement；
2. 若 critical token 数很大，top-1/top-2 refinement 不可能改变 global floor，应 fail-fast；
3. refinement 必须 fail closed：超时或 budget hit 时保留旧 lower bound，不降级证书；
4. 下一层应实现 critical-token micro-expansion，而不是全局 unique-route20 或 AMCB。

最新水位诊断见：

- `BPC_future/logical_graph/run_reports/20260623_bpc_future_v7_waterline_frontier_refinement_diag_zh.md`
