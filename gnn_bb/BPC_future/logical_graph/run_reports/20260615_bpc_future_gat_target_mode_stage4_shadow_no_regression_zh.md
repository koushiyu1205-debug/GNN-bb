# 2026-06-15 BPC_future GAT Target Mode Stage 4 Shadow No-Regression 报告

## 结论

Stage 4 的 default-off shadow logging hook 已接入 journey column 入池前路径，并完成
balanced60 tasks5/tasks10 shadow no-regression smoke。

本阶段仍然不是 production enable：

- 没有启用 GAT admission scheduler；
- 没有改变 pricing 搜索顺序；
- 没有过滤任何 true-RC negative column；
- 没有新增 certificate 来源；
- final optimality proof 仍只来自当前 branch/cut/dual 下 exact pricing / final judge 的完整 no-negative closure。

## 本轮代码边界

新增/补齐的是 `journey_gat_target_mode_shadow` 事件：

- 事件在 `_add_priced_journeys(...)` 前记录；
- 使用当前 RMP/SCIP true dual 和 active cuts 重新计算 `manual_journey_reduced_cost(...)`；
- true-RC negative 只会被 shadow 标成 `HIGH_PRIORITY` 或 `DELAY_QUEUE`；
- true-RC nonnegative 才允许 shadow 标成 `REJECT_NONNEGATIVE_ONLY`；
- event payload 固定：
  - `selector_is_pricing_oracle=false`
  - `selector_can_certificate=false`
  - `official_bound_effect=false`
  - `production_ready=false`
  - `hard_filter_enabled=false`

当前 shadow run 没有配置 safe candidate ids，因此所有 true-RC negative shadow candidate 都进入
`DELAY_QUEUE`，没有任何 online 行为变化。

## 单实例 probe

先用一个已知会 add exact columns 的实例确认 hook 触发：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
  BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml \
  --results-csv BPC_future/results/gat_target_mode_shadow_probe_20260615/tasks5_shadow_probe.csv \
  --log-dir BPC_future/results/gat_target_mode_shadow_probe_20260615/logs \
  --solution-dir BPC_future/results/gat_target_mode_shadow_probe_20260615/solutions \
  --quiet \
  --set journey_gat_target_mode_shadow_enabled=true \
  --set journey_gat_admission_log_shadow_decisions=true \
  --instances BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/apollo15_20km/tasks_05/apollo15_20km_balanced_tasks05_09_seed36836_logical_graph.json
```

结果：

```text
status=OPTIMAL
primal=171.862032
dual=171.862032
gap=0.0
nodes=1
cols=21
```

probe 日志确认：

- exact pricing 第一次返回 `8` 个 true-RC negative journeys；
- shadow event 在 `journey_column_addition` 前出现；
- `candidate_journeys=8`
- `true_negative_journeys=8`
- `delay_queue_journeys=8`
- `reject_nonnegative_only_journeys=0`
- `selector_can_certificate=false`
- `official_bound_effect=false`

## 5/10 Shadow Smoke

数据集：

```text
BPC_future/data/generated/moon_trek_balanced_60_20260609
```

baseline CSV 使用本轮前已跑出的：

```text
BPC_future/results/gat_target_mode_shadow_smoke_20260615/tasks5_baseline.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615/tasks10_baseline.csv
```

shadow rerun 输出：

```text
BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/tasks5_shadow.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/tasks10_shadow.csv
```

### tasks5

```text
instances = 20
baseline OPTIMAL = 20/20
shadow OPTIMAL = 20/20
official_mismatch_count = 0
baseline_total_time = 8.241215
shadow_total_time = 7.337385
avg_delta = -0.0451915
max_delta = 0.003877
avg_ratio = 0.960261
max_ratio = 1.009589
```

Shadow event summary：

```text
shadow_events = 24
candidate_journeys = 82
true_negative_journeys = 82
high_priority_journeys = 0
delay_queue_journeys = 82
reject_nonnegative_only_journeys = 0
blocked_events = 24
pricing_kinds = exact:23, heuristic:1
```

### tasks10

```text
instances = 20
baseline OPTIMAL = 20/20
shadow OPTIMAL = 20/20
official_mismatch_count = 0
baseline_total_time = 269.417666
shadow_total_time = 269.368748
avg_delta = -0.0024459
max_delta = 0.139205
avg_ratio = 1.001021
max_ratio = 1.011135
```

Shadow event summary：

```text
shadow_events = 89
candidate_journeys = 494
true_negative_journeys = 494
high_priority_journeys = 0
delay_queue_journeys = 494
reject_nonnegative_only_journeys = 0
blocked_events = 89
pricing_kinds = exact:81, exact_completion_bound_retry:3, exact_hidden_negative_patrol:2, heuristic:3
```

## 比对字段

本报告的 no-regression 判定只看 official / proof-facing 字段：

```text
status
primal_bound
dual_bound
gap
node_count
rmp_solves
pricing_calls
exact_pricing_calls
columns
cuts_added
subset_row_cuts_added
sortie_lb_cut_added
fleet_lb_cut_added
```

`generated_sequences` 和 `evaluated_timed_trips` 在 smoke 中仍存在 run-to-run drift，不作为
exactness 回归字段。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/solver/gat_admission_queue.py \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/scripts/audit_gat_batch_impact_knn_ood.py \
  BPC_future/learning/batch_impact_model.py \
  BPC_future/learning/gnn_model.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
  BPC_future.tests.test_gat_target_mode_scheduler \
  BPC_future.tests.test_gat_target_mode_certificate_safety \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_dataset \
  BPC_future.tests.test_gat_batch_impact_model
```

结果：

```text
Ran 23 tests in 0.190s
OK
```

另补充运行 GAT target-mode certificate boundary 日志审计：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  --log-dir BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/logs_tasks5_shadow \
  --log-dir BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/logs_tasks10_shadow \
  --output-dir BPC_future/results/gat_target_mode_certificate_audit_20260615 \
  --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_target_mode_certificate_audit_zh.md
```

结果：

```text
all_checks_pass = true
violation_count = 0
log_files = 40
gat_events = 113
candidate_journeys = 576
true_negative_journeys = 576
delay_queue_journeys = 576
reject_nonnegative_only_journeys = 0
global_certificate_pricing_events = 152
```

审计报告：

```text
BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_target_mode_certificate_audit_zh.md
```

## Stage 4 状态

已满足：

- default-off shadow hook；
- 5/10 official no-regression；
- shadow 事件能覆盖真实 exact column addition；
- shadow selector 不产生 certificate / official bound；
- true-RC negative 没有被 reject。
- certificate boundary 日志审计无 violation。

仍未满足：

- 没有 opt-in online admission scheduling；
- 没有 20-task opt-in A/B；
- 没有证明 20-task wall-time ROI；
- 没有进入 Stage 5；
- 没有 20-task 200 秒 exact OPTIMAL 证明。

下一步应先做 Stage 4 opt-in A/B 设计，而不是直接打开 production gate。
