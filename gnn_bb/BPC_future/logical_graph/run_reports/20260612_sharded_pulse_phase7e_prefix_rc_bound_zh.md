# Sharded Pulse Phase 7E Safe Prefix RC Bound 报告

日期：2026-06-12

## 目标

本轮只实现 Phase 7E：`Safe Prefix Reduced-Cost Lower-Bound Ledger`。

目标不是做强 completion bound，而是先把 transition Pulse 的 prefix RC 账本语义钉牢，并只启用一版弱但安全的 lower-bound pruning。

本轮不做：

- resume；
- parallel；
- adaptive hierarchical sharding；
- production benchmark 默认启用；
- 20/100 正式 A/B；
- cut / subset-row / fleet-cut 的通用 prefix lower bound。

## 实现摘要

### 1. PrefixReducedCostLedger

新增 `PrefixReducedCostLedger`，显式维护：

- `exact_prefix_rc`
- `lb_prefix_rc`
- `covered_tasks`
- `fixed_fleet_charged`

语义：

- `C_exact_prefix`：只包含已经由 prefix trace 固定的 fixed/fleet、已走 arc cost、service cost、cover dual；
- `C_lb_prefix`：用于 pruning 的 safe prefix lower-bound。Phase 7E 中保持与 exact prefix 一致；
- duplicate cover dual 会 fail-fast；
- fixed/fleet contribution 重复 charge 会 fail-fast。

### 2. Transition state 使用 ledger 更新

`transition_root_only_pulse()` 中扩展 task 时不再手写：

```python
fixed_vehicle_cost - fleet_limit + arc_cost + service_cost - cover_dual
```

而是通过 ledger helper 更新。

return-to-depot 时也通过 ledger helper 加入 return cost。

### 3. Weak Safe LB

Phase 7E 只启用 no-cut / nonnegative-cost 场景下的弱 lower bound。

open sortie:

```text
LB_remaining =
    min_return_cost_lower_bound(current_or_remaining_final_node)
    - remaining_positive_cover_reward_bound
```

depot-ready after at least one sortie:

```text
LB_remaining =
    min_outbound_cost
    + min_return_cost
    - remaining_positive_cover_reward_bound
```

root depot 不直接 bound-prune，避免把测试/诊断路径剪成空 candidate surface。

### 4. Fail-open 规则

以下情况 bound pruning 直接 fail-open：

- `cuts != ()`；
- arc option cost 存在负值；
- service cost 存在负值；
- 缺少 outbound / return cost lower bound。

当前不纳入：

- subset-row cut dual；
- fleet cut；
- branch row dual；
- 任何未证明安全的 row contribution。

### 5. Guarded path

guarded sharded path 透传：

```python
bound_pruning_enabled=bool(config.pulse_bound_pruning_enabled)
```

默认仍关闭。该开关独立于 `pulse_exact_safe_pruning_enabled`，避免旧的 return/resource pruning 配置隐式打开 RC bound pruning。开启后 `pulse_bound_pruned` 会聚合到 `JourneyPricingResult` 和 driver JSONL 的既有字段。

## 新增测试

新增 Phase 7E focused tests：

- `test_prefix_rc_ledger_matches_manual_rc_without_cuts_multisortie`
- `test_prefix_rc_ledger_rejects_duplicate_cover_and_fixed_double_charge`
- `test_transition_pulse_bound_pruning_fails_open_with_cuts`
- `test_transition_pulse_bound_pruning_matches_unpruned_and_prunes`
- `test_sharded_pulse_guarded_bound_counter_surfaces`

覆盖语义：

- prefix ledger 与 `manual_journey_reduced_cost()` 在 no-cut multi-sortie leaf 上一致；
- fixed/fleet 不双算；
- cover dual 不重复领取；
- cut dual 未安全处理时 fail-open；
- pruned transition Pulse 与 unpruned 在 best true RC / found-negative / negative signatures 上一致；
- 至少一个 toy case `pulse_bound_pruned > 0`；
- guarded path 可观测 `pulse_bound_pruned`。

## 验证命令

Phase 7E focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_prefix_rc_ledger_matches_manual_rc_without_cuts_multisortie \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_prefix_rc_ledger_rejects_duplicate_cover_and_fixed_double_charge \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_bound_pruning_fails_open_with_cuts \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_bound_pruning_matches_unpruned_and_prunes \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_bound_counter_surfaces
```

结果：

```text
Ran 5 tests in 0.009s
OK
```

Phase 7A-7E focused regression：

```text
Ran 29 tests in 0.141s
OK
```

## 当前边界

- bound pruning 默认关闭；
- production benchmark 默认不启用 sharded Pulse；
- cuts 下 bound pruning fail-open；
- root depot 不直接 bound-prune；
- 该 LB 很弱，只用于建立安全框架和回归约束。

## 结论

Phase 7E 已完成最小安全版：transition Pulse 现在有明确的 prefix RC ledger，并支持 opt-in 的弱安全 lower-bound pruning。

当前最重要的结果是：

1. prefix RC 不再散落在 transition 更新逻辑中；
2. fixed/fleet 和 cover dual 的账本语义有测试保护；
3. cut contribution 未处理时不会进入 bound pruning；
4. pruned / unpruned 结果有直接对照测试；
5. `pulse_bound_pruned > 0` 的 toy case 已覆盖。

下一步如果继续做 Phase 7F，应只逐项加入已证明安全的 cut/fleet contribution lower bound，并为每个 contribution 加单独的 pruned/unpruned exactness tests。
