# 2026-06-16 BPC_future GAT Target Mode Stage 4 Opt-in Admission Probe 报告

## 结论

本轮补齐了 Stage 4 default-off opt-in admission scheduling 的最小 solver 集成：

- `journey_gat_admission_scheduler_enabled=false` 时完全 no-op；
- opt-in 时只允许对已通过 true-RC 验证的候选 journey 做 admission scheduling；
- heuristic / worker 等可变路径可以把非 safe true-RC negative 暂放 `DELAY_QUEUE`；
- exact pricing 路径默认不被 GAT 阻断，只会释放 due delayed candidates 并透传当前 exact journeys；
- certificate 前如果 delay queue 里仍有 delayed candidates，必须先 release / re-expose，再回到 RMP，不允许直接进入 certificate；
- GAT / CBF / kNN / OOD 仍不能产生 official bound、pricing oracle 结论或 certificate。

本轮完成的是 Stage 4 opt-in admission preflight + 单例 smoke，不是 20-task ROI 证明，也不是 production-ready 声明。

## 代码边界

新增 / 修改点：

- `BPC_future/solver/journey_driver.py`
  - 新增 `_JourneyGATAdmissionRuntime`；
  - 新增 `_make_journey_gat_admission_runtime()`；
  - 新增 `_journey_gat_target_mode_admission_schedule()`；
  - branch-node heuristic add path 接入 admission scheduling；
  - branch-node exact add path保持 exact-path preserved，只做 due release / pass-through；
  - branch-node certificate promotion 前新增 release-before-certificate；
  - admission event 固定记录：
    - `selector_can_certificate=false`
    - `selector_is_pricing_oracle=false`
    - `official_bound_effect=false`
    - `hard_filter_enabled=false`
    - `requires_exact_pricing_full_scan=true`

- `BPC_future/scripts/audit_gat_target_mode_certificate_closure.py`
  - certificate audit 同时识别：
    - `journey_gat_target_mode_shadow`
    - `journey_gat_target_mode_admission`
  - summary 新增 `shadow_events` / `admission_events`。

- `BPC_future/tests/test_gat_target_mode_scheduler.py`
  - 覆盖 default-off；
  - 覆盖 heuristic delay 后 exact path release；
  - 覆盖 certificate candidate 立即 release；
  - 覆盖 safe candidate HIGH_PRIORITY。

- `BPC_future/tests/test_gat_target_mode_certificate_audit.py`
  - 覆盖 admission event 被 certificate-boundary audit 检查。

## 单例 Opt-in Smoke

### tasks5

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
  BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_5_journey.yaml \
  --results-csv BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/tasks5_optin_admission.csv \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/logs \
  --solution-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/solutions \
  --quiet \
  --set journey_gat_target_mode_shadow_enabled=true \
  --set journey_gat_admission_scheduler_enabled=true \
  --set journey_gat_admission_max_delay_rounds=1 \
  --set journey_gat_admission_log_shadow_decisions=true \
  --instances BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/tranquillitatis_balmer_like_20km/tasks_05/tranquillitatis_balmer_like_20km_balanced_tasks05_08_seed136715_logical_graph.json
```

结果：

```text
status = OPTIMAL
primal_bound = 181.307678
dual_bound = 181.307678
gap = 0.0
solving_time = 1.53564
node_count = 1
rmp_solves = 3
pricing_calls = 8
exact_pricing_calls = 5
columns = 17
```

该实例 heuristic 触发时已经是 certificate candidate，因此 admission 事件走
`certificate_candidate_release` pass-through，没有真正 delay。

### tasks10

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
  BPC_future/scripts/run_bpc_future.py \
  --config BPC_future/configs/moon_trek_10_journey.yaml \
  --results-csv BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/tasks10_optin_admission.csv \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/logs_tasks10 \
  --solution-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/solutions_tasks10 \
  --quiet \
  --set journey_gat_target_mode_shadow_enabled=true \
  --set journey_gat_admission_scheduler_enabled=true \
  --set journey_gat_admission_max_delay_rounds=1 \
  --set journey_gat_admission_log_shadow_decisions=true \
  --instances BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_balanced_tasks10_01_seed141000_logical_graph.json
```

结果：

```text
status = OPTIMAL
primal_bound = 341.918964
dual_bound = 341.918964
gap = 0.0
solving_time = 3.33785
node_count = 1
rmp_solves = 6
pricing_calls = 17
exact_pricing_calls = 11
columns = 91
```

该实例真实触发了 admission scheduling：

```text
cg_iter = 1
pricing_kind = heuristic
certificate_candidate = false
status = scheduled
delay_queue_journeys = 1
delayed_negative_journeys = 1
certificate_blocked_by_delayed_negative = true

cg_iter = 2
pricing_kind = exact
certificate_candidate = true
reason = certificate_candidate_release
released_journeys = 1
delay_queue_size = 0
```

这说明 opt-in scheduler 能 delay heuristic true-RC negative，并在 exact / certificate-facing path 前释放，不会把 delayed negative 留给 certificate。

## Certificate Audit

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/logs \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/logs_tasks10 \
  --output-dir BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/certificate_audit_combined \
  --report BPC_future/results/gat_target_mode_stage4_optin_admission_probe_20260616/certificate_audit_combined/report.md
```

结果：

```text
all_checks_pass = true
violation_count = 0
log_files = 2
finish_events = 2
optimal_finish_events = 2
global_certificate_pricing_events = 2
gat_events = 16
shadow_events = 8
admission_events = 8
candidate_journeys = 66
true_negative_journeys = 34
delay_queue_journeys = 34
reject_nonnegative_only_journeys = 0
pricing_kinds = exact:12, heuristic:4
```

## Unit / Static Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/solver/gat_admission_queue.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/tests/test_gat_target_mode_certificate_audit.py
```

通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_target_mode_scheduler \
  BPC_future.tests.test_gat_target_mode_certificate_safety \
  BPC_future.tests.test_gat_target_mode_certificate_audit
```

```text
Ran 14 tests in 0.062s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_target_mode_scheduler \
  BPC_future.tests.test_gat_target_mode_certificate_safety \
  BPC_future.tests.test_gat_target_mode_certificate_audit \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_dataset \
  BPC_future.tests.test_gat_batch_impact_model
```

```text
Ran 29 tests in 1.733s
OK
```

```bash
git diff --check -- \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/tests/test_gat_target_mode_certificate_audit.py
```

通过。

## Stage 4 状态

已完成：

- opt-in admission scheduler 的 branch-node 最小集成；
- default-off 边界；
- heuristic delay / exact release 单元测试；
- certificate candidate release 单元测试；
- admission event 纳入 certificate audit；
- tasks5 / tasks10 单例 opt-in smoke；
- combined certificate audit 无 violation。

未完成：

- 5/10 全量 opt-in no-regression A/B；
- 20-task opt-in A/B；
- repeatable wall-time / tail retry ROI；
- 20-task 200 秒 exact OPTIMAL；
- Stage 5 scale acceleration。

下一步应跑 5/10 全量 opt-in no-regression；只有通过后才进入 20-task hard-tail matrix A/B。
