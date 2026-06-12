# Sharded Pulse Phase 7I-A Hidden-negative Worker 报告

日期：2026-06-12

## 目标

本轮实现 Phase 7I-A：`Sharded Pulse hidden-negative / harvest worker`。

目标不是放开 official certificate，也不是跑 20/100 A/B，而是让 Sharded Pulse 先作为 bounded true-RC negative finder：

```text
legacy final judge 即将启动前
    -> bounded Sharded Pulse worker
    -> 找到 true-RC negative journeys：走正常 RMP 加列流程
    -> 没找到 / incomplete / duplicate-only：不证书，继续 legacy final judge
```

## 实现摘要

### 1. 新增 opt-in worker

新增配置默认关闭：

- `journey_sharded_pulse_hidden_negative_worker_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_trigger="before_legacy_final_judge"`
- `journey_sharded_pulse_hidden_negative_worker_time_limit=3.0`
- `journey_sharded_pulse_hidden_negative_worker_max_recursions=100000`
- `journey_sharded_pulse_hidden_negative_worker_archive_enabled`
- `journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled`
- `journey_sharded_pulse_hidden_negative_worker_harvesting_enabled`
- `journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit`
- `journey_sharded_pulse_hidden_negative_worker_max_columns`

触发位置为根节点 legacy exact/final pricing 前。worker 使用 SCIP true dual，不使用 smoothed / dual-average dual。

### 2. 只找列，不证书

hidden-negative worker 的 exactness 边界：

- `FOUND_NEGATIVE` / `FOUND_NEGATIVE_HARVESTED`：可返回 true-RC negative journeys；
- `INCOMPLETE_LIMIT`：继续 legacy final judge，不证书；
- `DUPLICATE_ONLY`：继续 legacy final judge，不证书；
- bottom Pulse no-negative / certified：在 worker path 中降级为 non-certificate incomplete；
- `global_certificate_capable=False`；
- `final_judge_certificate_capable=False`。

### 3. True-RC 复验

worker 返回 journeys 前会逐条调用：

```text
manual_journey_reduced_cost(journey, true_duals, cuts)
```

只有 true-RC `< -eps` 的 journeys 可以保留并进入正常 `_add_priced_journeys()` 流程。被复验过滤空的结果会返回 `INCOMPLETE_LIMIT`，不会 certificate。

### 4. 日志

新增事件：

```text
journey_sharded_pulse_hidden_negative_worker
```

主要字段：

- `pulse_worker_status`
- `pulse_worker_reason`
- `pulse_worker_returned_journeys`
- `pulse_worker_true_rc_filtered`
- `pulse_worker_global_certificate_capable`
- `pulse_worker_context_hash`
- `pulse_worker_true_dual_hash`
- `pulse_worker_cut_hash`
- `pulse_worker_branch_hash`
- `pulse_worker_forbidden_signature_hash`
- `pulse_worker_bound_pruned`
- `pulse_worker_archive_pruned`
- `pulse_worker_time_window_pruned`
- `pulse_worker_return_pruned`
- `pulse_worker_harvested_count`
- `pulse_worker_harvested_support_changing_count`

worker 结果同时通过既有 `journey_pricing` 日志记录，`pricing_kind="sharded_pulse_hidden_negative_worker"`。

## 新增测试

新增 4 个 focused tests：

- `test_sharded_pulse_hidden_negative_worker_returns_true_rc_negative_only`
- `test_sharded_pulse_hidden_negative_worker_driver_adds_negative_not_certificate`
- `test_sharded_pulse_hidden_negative_worker_duplicate_only_not_certificate`
- `test_sharded_pulse_hidden_negative_worker_no_negative_not_certificate`

覆盖：

- real `very_small` worker 返回列均满足 true-RC `< -eps`；
- active driver path 中 worker 可加列；
- worker 加列不设置 official `dual_bound` 或 certificate；
- duplicate-only 不证书；
- dummy certified / no-negative 在 worker path 中降级为 `INCOMPLETE_LIMIT`；
- context hash 字段非空；
- worker 返回列通过现有 `_add_priced_journeys()` 进入 RMP 池。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_returns_true_rc_negative_only \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_driver_adds_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_no_negative_not_certificate
```

结果：

```text
Ran 4 tests in 0.103s
OK
```

Phase 7H / guarded Pulse 回归：

```text
Ran 18 tests in 0.249s
OK
```

## 当前边界

- 默认关闭；
- 只接根节点 legacy final judge 前；
- 不做 branch-node worker；
- 不做 resume；
- 不做 parallel；
- 不做 adaptive hierarchical sharding；
- 不做 official certificate effect；
- 已跑 Apollo / Tranquillitatis / Apollo10 三组 real smoke，但结果不支持默认启用 active worker。

## Phase 7I-A Real Small Smoke

运行目录：

```text
BPC_future/results/sharded_pulse_phase7ia_hidden_worker_smoke_20260612/
```

矩阵：

- Apollo 5：`apollo15_20km_tasks05_01_seed6000`
- Tranquillitatis 5：`tranquillitatis_balmer_like_20km_tasks05_01_seed6000`
- Apollo 10：`apollo15_20km_tasks10_01_seed11000`

每个实例跑三组：

- baseline；
- audit-only；
- hidden-negative worker active。

结果摘要：

| 实例 | 模式 | status | dual_bound | official pricing_state | exact calls | worker events | worker returned | worker added | worker time-window pruned | worker return pruned |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Apollo 5 | baseline | `OPTIMAL` | 102.041475 | `CERTIFIED_NO_NEGATIVE` | 4 | 0 | 0 | 0 | 0 | 0 |
| Apollo 5 | audit | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 1 | 0 | 0 | 0 | 0 | 0 |
| Apollo 5 | worker | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 2 | 1 | 0 | 0 | 50385 | 2907 |
| Tranquillitatis 5 | baseline | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 1 | 0 | 0 | 0 | 0 | 0 |
| Tranquillitatis 5 | audit | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 1 | 0 | 0 | 0 | 0 | 0 |
| Tranquillitatis 5 | worker | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 2 | 1 | 0 | 0 | 41995 | 1942 |
| Apollo 10 | baseline | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 2 | 0 | 0 | 0 | 0 | 0 |
| Apollo 10 | audit | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 2 | 0 | 0 | 0 | 0 | 0 |
| Apollo 10 | worker | `TIME_LIMIT` | - | `LOCAL_NO_COLUMN_UNCERTIFIED` | 4 | 2 | 0 | 0 | 206833 | 2471 |

观察：

- active worker 在这组真实小实例中没有返回可加列 journeys；
- worker 有真实 transition pruning 信号，但仍以 `INCOMPLETE_LIMIT` 结束；
- Apollo 5 baseline 能在本轮配置下闭合到 `OPTIMAL`，audit/worker 额外开销导致短时限 smoke 进入 `TIME_LIMIT`；
- Apollo 10 audit 仍出现 `legacy_negative_pulse_incomplete` warning，worker active path 没能提前找到该类负列；
- worker context hash 无缺失；
- 没有 worker certificate effect。

结论：

- 当前 7I-A active worker 机制是安全的，但这组 real smoke 没有显示 ROI；
- 不应默认启用 hidden-negative worker；
- 下一步优先做 adaptive second-action shard refinement 或更严格触发门控，而不是 official certificate gate；
- 后续若继续 worker 路线，应要求 `worker_returned_journeys > 0`、`worker_added_journeys > 0` 或 legacy final judge calls 明显下降，才考虑扩大范围。

## 结论

Phase 7I-A 已完成最小可验证实现和 real small smoke：Sharded Pulse 可以作为 bounded hidden-negative worker 主动找列，但不能盖 no-negative 证书。本轮真实小矩阵没有显示 active worker ROI，因此当前不应默认启用；下一步应优先做 adaptive second-action shard refinement 或更严格 worker 触发门控。
