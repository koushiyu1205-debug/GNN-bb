# Sharded Pulse Phase 7X Worker Ordering Coverage 报告

日期：2026-06-13

## 目标

Phase 7X 只做 worker candidate ordering / task-set coverage 诊断。

Phase 7W 已经显示：

```text
worker first task-set: [6,19]
ordinary follow-up residual negatives: [5,8,15], [5,12,18], [12,16,17]
relation: disjoint_task_set
```

本轮问题是：

当前已有的 `reduced_cost_proxy` task ordering 是否能让 Pulse worker 更早覆盖 ordinary heuristic 后续找到的 disjoint negative task-set。

本轮不做：

- 新算法；
- 新 worker budget；
- resume / parallel；
- official certificate gate；
- production default enable。

## 运行

使用已有 opt-in profile 对比：

1. baseline；
2. natural worker：
   - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`
3. ordered worker：
   - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered`
   - `journey_sharded_pulse_hidden_negative_worker_task_ordering=reduced_cost_proxy`

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7x_worker_ordering_coverage_20260613 \
--instances mt20_greedy_apollo_01 \
--profiles baseline \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered \
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

- `BPC_future/results/sharded_pulse_phase7x_worker_ordering_coverage_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7x_worker_ordering_coverage_20260613/summary.csv`

## 结果

| profile | ordering | worker task-set | worker RC | worker recursions | first follow-up task-set | relation |
|---|---|---|---:|---:|---|---|
| natural | `natural` | `[6,19]` | `-39.453983` | 115 | `[5,8,15]` | `disjoint_task_set` |
| ordered | `reduced_cost_proxy` | `[6,19]` | `-39.453983` | 115 | `[5,8,15]` | `disjoint_task_set` |

Natural profile：

- worker time：`0.031382279`;
- worker added journeys：1；
- next RMP objective delta：`-169.988908`;
- follow-up negative calls：3；
- first follow-up best RC：`-138.437225`;
- first follow-up task-set：`[5,8,15]`。

Ordered profile：

- worker time：`0.037196106`;
- worker added journeys：1；
- next RMP objective delta：`-31.551683`;
- follow-up negative calls：2；
- first follow-up best RC：`-138.437225`;
- first follow-up task-set：`[5,8,15]`。

二者共同点：

- worker 首列都是 `[6,19]`;
- ordinary heuristic 首个 residual negative 都是 `[5,8,15]`;
- relation 都是 `disjoint_task_set`;
- ordered profile 没有降低 worker recursions，也没有改变 worker 首列覆盖。

## 解释

`reduced_cost_proxy` ordering 当前没有解决 Phase 7W 暴露的问题。

更具体地说：

1. worker 在当前 budget / stop-after-first-negative / impact-filter 条件下仍先返回 `[6,19]`；
2. ordinary heuristic 后续仍立即找到更强的 disjoint task-set `[5,8,15]`；
3. 这不是简单的任务排序微调能解决的证据；
4. 当前 active worker 的搜索 universe / stop rule / candidate selection 与 ordinary heuristic 的高收益负列族仍不一致。

## Exactness 边界

- Pulse worker 仍只通过 add-column path；
- 本轮无 certificate；
- `dual_bound=None`，没有 official lower-bound effect；
- 不改变 default config；
- 不扩大 worker time limit；
- 不把 `TIME_LIMIT` / `INCOMPLETE` 当 proof。

## 验证

本轮复用 Phase 7W 的代码改动，并额外确认：

```text
Focused ROI tests: Ran 2 tests in 0.002s OK
BPCFutureTests: Ran 469 tests in 1.424s OK (skipped=1)
git diff --check: OK
```

## 当前结论

Phase 7X 进一步支持停止 active-worker gate stacking：

```text
natural ordering and reduced_cost_proxy ordering both miss the same ordinary residual negative family.
```

继续增加 worker budget 或继续叠 gate 的 ROI 依据不足。

## 下一步建议

不要继续扩大 active worker。

下一步建议转入负结果路线的下一项证据闭环：

1. 若仍沿 Pulse 路线，只能做更深的 candidate universe 对齐诊断：
   - 为什么 ordinary heuristic 可快速找到 `[5,8,15]`；
   - current-context Pulse worker 为什么不覆盖该 task-set；
   - 是否是 first-task shard scheduling、stop-after-first-negative、impact-filter 或 transition universe 差异。
2. 更推荐转向非 worker 主线：
   - ordinary pricing / profile-DP tail；
   - RMP stabilization；
   - column impact filter；
   - legacy final-judge proof-tail 优化。

当前仍不能宣称 Phase 7O 达标，也不能标记最终目标完成。
