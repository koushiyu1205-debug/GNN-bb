# Sharded Pulse Phase 7W Residual Tail Matrix 报告

日期：2026-06-13

## 目标

Phase 7W 继续 Phase 7V 的 residual pricing / legacy tail attribution，不新增算法。

目标是用 `negative_journey_task_set_samples` 和 `changed_task_set_samples` 判断：

1. worker 加入的负列是否被后续 ordinary / exact pricing 以同一 task-set 继续替换；
2. 后续 residual negative 是否与 worker 加入列重叠；
3. 还是 worker 找到的是孤立列，后续 tail 来自完全不同 task-set。

## 实现补充

本轮修正了 ROI 脚本的 follow-up 归因口径。

原口径只统计：

```text
cg_iter > first_worker_add_iter
```

这会漏掉 `continue_same_iteration_after_add` 场景中 worker 加列后同一 `cg_iter` 内继续运行的 heuristic / exact pricing。

现口径改为：

```text
JSONL 中 first worker addition event 之后的所有非 worker pricing
```

这是诊断脚本改动，不改变 solver、worker、RMP 或 certificate。

新增/更新测试覆盖：

- no worker add 默认值；
- follow-up residual negative overlap / Jaccard；
- same-iteration follow-up negative 也计入 attribution。

## 窄 20-task matrix

运行命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7w_residual_tail_matrix_20260613 \
--instances phase7o_20_smoke \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 2.0 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.12 \
--pricing-max-dp-states 1 \
--max-cg-iterations 3 \
--audit-max-recursions 20000 \
--worker-max-recursions 20000 \
--current-probe-max-recursions 12000 \
--current-probe-min-tasks 20 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7w_residual_tail_matrix_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7w_residual_tail_matrix_20260613/summary.csv`

### Matrix 结果

| instance | worker triggered | added | follow-up outcome | first residual relation | official changed |
|---|---:|---:|---|---|---:|
| `tranq20_01` | 0 | 0 | `no_worker_add` | `no_worker_add` | False |
| `mt20_greedy_apollo_01` | 1 | 1 | `followup_incomplete_near_zero_best_rc` | `unknown` | False |
| `mt20_greedy_tranq_01` | 0 | 0 | `no_worker_add` | `no_worker_add` | False |

`mt20_greedy_apollo_01` 细节：

- worker returned / added 1 journey；
- worker task-set sample：`[6, 19]`;
- follow-up non-worker pricing calls：3；
- follow-up generated sequences：457；
- follow-up evaluated timed trips：1766；
- follow-up pricing state 全部为 `INCOMPLETE_LIMIT`;
- 未返回 residual negative journey，因此 task-set relation 为 `unknown`;
- `pool_duplicate_task_set_ratio_last=0.0`。

这一组说明：低 DP cap 下，worker 后主要暴露的是 proof / profile-DP incomplete tail，而不是可分类的 residual negative replacement tail。

## Apollo 加深 probe

为确认不是 DP cap 太低导致看不到 residual negative，对 `mt20_greedy_apollo_01` 单实例加深：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7w_residual_tail_apollo_probe_20260613 \
--instances mt20_greedy_apollo_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 4.0 \
--audit-time-limit 0.2 \
--worker-time-limit 0.2 \
--current-probe-time-limit 0.2 \
--pricing-time-limit 0.4 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--audit-max-recursions 30000 \
--worker-max-recursions 30000 \
--current-probe-max-recursions 20000 \
--current-probe-min-tasks 20 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7w_residual_tail_apollo_probe_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7w_residual_tail_apollo_probe_20260613/summary.csv`

### Apollo probe 结果

baseline：

- status：`TIME_LIMIT`;
- wall time：`1.267816`;
- primal：`923.116819`;
- dual bound：`None`。

worker profile：

- status：`TIME_LIMIT`;
- wall time：`1.276517`;
- primal：`891.565136`;
- dual bound：`None`;
- worker added journeys：1；
- worker added new task-set count：1；
- worker task-set：`[6, 19]`;
- next RMP objective delta：`-169.988908`;
- official lower bound 未产生。

follow-up residual negatives：

| cg_iter | pricing kind | best RC | task-set | relation to worker `[6,19]` |
|---:|---|---:|---|---|
| 1 | heuristic | `-138.437225` | `[5, 8, 15]` | `disjoint_task_set` |
| 2 | heuristic | `-128.547499` | `[5, 12, 18]` | disjoint |
| 3 | heuristic | `-123.681417` | `[12, 16, 17]` | disjoint |

summary 中首个 residual negative：

- `followup_first_negative_task_set=5,8,15`;
- `followup_first_negative_relation_to_worker=disjoint_task_set`;
- `followup_first_negative_jaccard_to_worker=0.0`;
- `followup_negative_pricing_calls=3`;
- `followup_profile_dp_incomplete_count=0`。

## 解释

本轮最重要的信号是：

```text
worker added task-set [6,19]
follow-up residual negatives are disjoint new task-sets
```

这说明当前 worker 没有覆盖 ordinary pricing 仍能快速找到的负列族。它不是简单的 duplicate pool pressure，也不主要是同 task-set replacement 质量问题。

更具体地说：

1. worker 可找到 true-RC negative column；
2. worker 加入列可推动 RMP，Apollo probe 中 primal 改善；
3. 但后续 ordinary heuristic 仍能找到更强、完全 disjoint 的负列；
4. 因此当前 worker 触发/排序/覆盖范围不够，不能宣称减少 legacy / ordinary pricing tail；
5. 当前证据不支持放开 active worker 默认启用，也不支持 official certificate gate。

## Exactness 边界

- Pulse worker 只作为 add-column path；
- no-column / incomplete / duplicate-only 没有 official lower-bound side effect；
- 本轮没有改变 certificate inference；
- 本轮没有改变 RMP；
- 本轮没有开启 production default；
- Apollo probe 的 `dual_bound=None`，不能当作 exact proof improvement。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields
```

结果：

```text
Ran 2 tests in 0.002s
OK
```

全量 `BPCFutureTests`：

```text
Ran 469 tests in 1.424s
OK (skipped=1)
```

`git diff --check`：通过。

## 当前结论

Phase 7W 给出比 Phase 7U/7V 更清楚的原因：

```text
active worker 当前能加列，但没有覆盖后续 ordinary negative tail；
follow-up residual negatives 是 disjoint new task-sets。
```

这进一步削弱了继续加 active-worker gate stacking / time-limit 的理由。

## 下一步建议

不要继续扩大 worker 预算，也不要做 official certificate gate。

更合理的下一步是二选一：

1. 若继续 Pulse worker 路线，只做 `worker candidate ordering / task-set coverage` 诊断：
   - 比较 worker candidate ranking 与 ordinary heuristic 首个 residual negative task-set；
   - 查 `[5,8,15]` 为什么没被 current-context probe 优先找到；
   - 不增加 worker time limit。
2. 或者按负结果路线转向：
   - ordinary pricing / profile-DP tail；
   - RMP stabilization；
   - column impact filter；
   - legacy final judge proof-tail 优化。

当前不能宣称 Phase 7O 达标，也不能标记最终目标完成。
