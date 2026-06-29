# V772 Route-Order Child Pricing Probe

## 目的

这一步不是继续单纯调 `branch score`。它补的是 RouteOpt 启发里的 stronger branching / formulation 诊断链路：

- V771 已经能看到 route-order 三分支的 child RMP 有明显 finite-pool bound lift；
- 但 finite-pool RMP lift 可能会被后续 pricing 产生的新负列吃掉；
- 因此 V772 增加 audit-only child pricing probe，用 child RMP dual 在每个 route-order child 上跑短预算 profile/materialized pricing。

它不加列、不更新 RMP、不提供 official bound，也不参与 fathom。

## 代码修改

### 1. route-order branch 允许进入 materialized profile pricing

文件：

- `BPC_future/pricing/journey_pricing.py`

新增支持判断：

- same/separate Ryan-Foster branch 仍保持原有支持；
- route-order branch 只允许在 `profile_pricing_enabled=True` 时进入 pricing；
- direct label / completion-bound certificate 对 route-order branch 仍 fail-closed，返回 `UNSUPPORTED`。

原因：route-order 约束必须等完整 journey materialize 后才能安全判断；direct NG certificate 目前不能对这类约束给 no-negative 证书。

### 2. route-order partition audit 增加 child pricing probe

文件：

- `BPC_future/solver/journey_driver.py`

新增配置：

```text
journey_route_order_partition_audit_child_pricing_enabled=False
journey_route_order_partition_audit_child_pricing_top_n=<child_rmp_top_n>
journey_route_order_partition_audit_child_pricing_min_mass=<child_rmp_min_mass>
journey_route_order_partition_audit_child_pricing_time_limit=0.0
journey_route_order_partition_audit_child_pricing_max_dp_states=50000
journey_route_order_partition_audit_child_pricing_max_returned_journeys=3
```

日志字段：

- event 顶层：
  - `child_pricing_probe_enabled`
  - `child_pricing_probe_top_n`
  - `child_pricing_probe_min_mass`
  - `child_pricing_probe_time_limit`
- 每个 top partition row：
  - `child_pricing_probe_enabled`
  - `child_pricing_probe_rows`
- 每个 child pricing row：
  - `kind`
  - `status`
  - `reason`
  - `pricing_state`
  - `pricing_proof_kind`
  - `best_reduced_cost`
  - `negative_journey_count`
  - `generated_sequences`
  - `evaluated_timed_trips`
  - `branch_infeasible_journeys_filtered`
  - `wall_time`
  - `official_bound_effect=False`
  - `certificate_effect=False`

## 验证

聚焦测试：

```text
python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_respects_ryan_foster_branch_constraints \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_profile_pricing_supports_route_order_after_materialization \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_route_order_branch_direct_pricing_remains_fail_closed \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_reports_child_width_and_coverage \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_child_rmp_probe_is_diagnostic
```

结果：

```text
Ran 5 tests in 0.015s
OK
```

## seed61635 45s smoke

命令要点：

```text
time-limit = 45
route-order partition audit = on
child RMP probe = on
child pricing probe = on
child pricing time limit = 0.35s
routeopt_bkf_v762 = on
```

结果：

```text
status = TIME_LIMIT
primal = 561.030445
dual = 526.651393
gap = 0.061278
time = 45.017457s
nodes = 2
cols = 350
```

日志：

```text
partition_events = 11
rows_with_child_pricing = 11
```

## 关键观察

有限池 child RMP gain 明显，但短预算 pricing 往往立刻找到负列。

典型记录：

```text
cg=3 pair=[14,16]
  before:        rmp_gain=+2.55,  pricing FOUND_NEGATIVE, rc=-10.12
  after:         rmp_gain=+0.07,  pricing FOUND_NEGATIVE, rc=-10.12
  not_same_route:rmp_gain=+38.31, pricing FOUND_NEGATIVE, rc=-9.37

cg=5 pair=[14,16]
  before:        rmp_gain=+4.92,  pricing FOUND_NEGATIVE, rc=-44.06
  after:         rmp_gain=+1.38,  pricing FOUND_NEGATIVE, rc=-13.68
  not_same_route:rmp_gain=+48.05, pricing INCOMPLETE_LIMIT, best_rc=-53.77

cg=6 pair=[12,20]
  before:        rmp_gain=+27.37, pricing FOUND_NEGATIVE, rc=-10.24
  after:         rmp_gain=+48.26, pricing INCOMPLETE_LIMIT, best_rc=-67.74
  not_same_route:rmp_gain=+8.88,  pricing INCOMPLETE_LIMIT, best_rc=-12.70

cg=14 pair=[12,13]
  before:        rmp_gain=+28.99, pricing FOUND_NEGATIVE, rc=-0.59
  after:         rmp_gain=+7.90,  pricing FOUND_NEGATIVE, rc=-3.40
  not_same_route:rmp_gain=+19.78, pricing FOUND_NEGATIVE, rc=-1.04
```

## 解释

这说明 V771 的 child RMP gain 不是假的，但也不能直接当成闭环收益：

- route-order 分支确实能改变 finite-pool LP；
- 但很多 child 下面还有负列链条，当前 relaxation / formulation 仍然松；
- 所以只靠 branch score 选择一个 RMP gain 大的 pair，不足以保证 20 规模闭环；
- branch testing 标签必须加入 child pricing 状态、best RC、是否 immediately found negative、是否 incomplete-limit；
- cuts/formulation 仍然必须并行推进，否则 hard case 的 best dual 可能继续不动。

## 当前判断

V772 支持了你指出的结论：

1. 不能只调 branch score。
2. route-order branch 是一个值得继续验证的 stronger formulation / branching 方向。
3. 有限池 child RMP gain 必须经过 pricing closure 过滤。
4. 后续 phased testing 应把 `child_rmp_gain` 和 `child_pricing_best_rc` 组合使用。
5. 对 seed61635 这类 hard case，仍需继续攻 pricing-compatible cuts / route-aware formulation。

## 下一步

优先级：

1. 将 route-order child pricing probe 接入 phased branch testing controller 的 phase-2/phase-3 诊断字段。
2. 形成双 child 均衡指标：
   - `min_child_rmp_gain`
   - `child_rmp_gain_product`
   - `max_child_pricing_best_rc_pressure`
   - `child_found_negative_count`
   - `child_incomplete_limit_count`
3. route-order branch 仍保持 audit/probe，不直接 live branch，直到 child pricing replay 证明它能减少 proof tail。
4. cuts/formulation 侧不继续盲目扩大 task-subset weighted rows；转向 route/order/resource-aware cuts 或更强 master 表达。

