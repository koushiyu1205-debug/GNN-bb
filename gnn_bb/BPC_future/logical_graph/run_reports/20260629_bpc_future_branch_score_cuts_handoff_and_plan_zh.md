# 20260629 Branch Score + Cuts/Formulation 交接文档与优化计划

## 0. 总目标

当前主线不是单纯继续调 GAT branch score，而是：

```text
Random-TW canonical 5/10/20 exact-safe 加速
最终 20 规模 60/60 实例在 600s 内 OPTIMAL
长期目标平均/多数实例接近 200s 内闭环
```

硬约束：

- 所有学习组件只能影响排序、调度、触发时机。
- GAT / score map / heuristic probe 不能提供 official lower bound、certificate 或剪枝依据。
- early branch 只能 exact-safe：child 继承合法旧 lower bound，不能把当前 RMP objective 当 exact node bound。
- pricing-compatible cuts 只有在 RMP reduced cost、pricing reduced cost、completion-bound fail-closed 边界全部一致后，才能进入 live 求解。

## 1. 当前最重要结论

### 1.1 Branch score 有用，但覆盖太窄

V545 / V543 merged overlay 在 20-scale random-TW full60 上：

| 版本 | OPTIMAL | capped mean | <=200s OPTIMAL |
|---|---:|---:|---:|
| baseline | 26/60 | 381.773895s | 20 |
| V468 current best | 33/60 | 348.261332s | 22 |
| V545 merged overlay | 36/60 | 341.542949s | 22 |

说明 state-scoped branch replay 有真实收益，且 V545 没有 `OPTIMAL -> non-OPTIMAL` 回归。但收益主要来自少数覆盖到的 branch state：

```text
journey_branch = 566
selected score present = 68
selected score >= 0.67 = 37
selected pair changed = 26
```

所以不能学全局 pair，例如不能把 `[2,6]`、`[16,17]` 当作永远好的 pair；必须绑定 `branch_state_key / depth / family / support pattern / child width / retry risk`。

### 1.2 只看 child RMP gain 会误导

V771/V772 route-order partition child RMP probe 看到很多 finite-pool child RMP gain 很大，但 V772 child pricing probe 立刻发现强负列：

```text
cg=5 pair=[14,16]
not_same_route: rmp_gain=+48.05
child pricing: INCOMPLETE_LIMIT, best_rc=-53.77

cg=6 pair=[12,20]
after: rmp_gain=+48.26
child pricing: INCOMPLETE_LIMIT, best_rc=-67.74
```

这说明：

- finite-pool child LP gain 不是假的；
- 但它可能很快被后续 pricing 负列吃掉；
- branch score 必须同时学习 child pricing pressure，而不是只学习 LP gain。

### 1.3 seed61635 这类 hard case 不是继续调 pair 权重能解决

V750 用 `routeopt_bkf_v736` preset 跑 hard2：

| seed | status | wall | primal | dual | gap |
|---|---:|---:|---:|---:|---:|
| 61311 | OPTIMAL | 113.795881 | 570.891015 | 570.891015 | 0 |
| 61635 | EXTERNAL_TIME_LIMIT | 600.020446 | 560.618366 | 526.651393 | 0.060588 |

seed61311 属于 branch-cut 联动能解决的 hard case；seed61635 的 best dual 基本不动，说明 formulation/cuts 下界不足。对于 `z_RMP < UB` 的节点，pricing proof 再快也不能直接 fathom。

因此后续必须并行推进：

- score-gated phased branch testing；
- pricing-compatible cuts / route-aware formulation；
- retry 分类 gate；
- incumbent / branch ordering 辅助。

## 2. 当前代码状态

### 2.1 Solver 内 RouteOpt/BKF phased branch testing

主要文件：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

已有能力：

- `journey_branch_candidate_priority=routeopt_bkf_staged`
- Phase0 cheap screen / dynamic-K
- Phase1 child LP probe
- Phase1 cut snapshot diagnostic
- Phase2 short-budget heuristic pricing probe
- BKF weighted score
- V773 新增 phase2 pricing pressure penalty

V773 新增字段：

```text
phase2_same_child_negative_severity
phase2_separate_child_negative_severity
phase2_negative_severity_sum
phase2_negative_severity_gap
phase2_negative_severity_balance_ratio
phase2_negative_child_presence_balance_gap
```

这些字段用于：

- 识别一个 branch pair 是否把负列压力集中到某个 child；
- 降权 “child LP gain 大但 pricing pressure 更大” 的候选；
- 给 GAT branch action 数据集提供更接近真实闭环成本的 context feature。

验证：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_weighted_score_does_not_over_penalize_small_phase2_negative \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v762_preset_adds_route_order_penalty_only \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap
```

结果：`Ran 6 tests OK`。

### 2.2 Branch action dataset 已接入 child-balance / cut / route-order context

主要文件：

- `BPC_future/scripts/build_gat_branch_action_sanity_dataset.py`
- `BPC_future/tests/test_gat_branch_action_sanity_dataset.py`

当前 context feature 已包含：

- Phase1 双 child gain：
  - `phase1_min_child_lp_gain`
  - `phase1_child_lp_gain_product`
  - `phase1_child_lp_gain_gap`
  - `phase1_child_lp_gain_balance_ratio`
- Phase1 cut snapshot：
  - `phase1_cut_snapshot_min_child_lp_gain`
  - `phase1_cut_snapshot_child_lp_gain_product`
  - `phase1_cut_snapshot_child_lp_gain_gap`
  - `phase1_cut_snapshot_child_lp_gain_balance_ratio`
- Phase2 pricing pressure：
  - 旧字段：negative child count、negative journey count、best RC、wall-time gap 等；
  - 新字段：severity sum/gap/balance/presence gap。
- Cut context：
  - dynamic SRC regime、active cut count、subset row count、gate threshold 等。
- Route-order context：
  - active journey / route signature / conflict count / conflict mass；
  - candidate direction / adjacency conflict mass 和 balance ratio。

最新验证：

```text
python -m py_compile \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset
```

结果：`Ran 1 test OK`。

### 2.2.1 V777 数据链硬 gate 实施状态

本轮已把 V773/V774 pressure 字段从 solver log 继续补到 audit、runbook、paired delta 和 GAT dataset manifest。当前事实：

```text
V777 seed61635 45s:
status = TIME_LIMIT
primal = 561.030445
dual = 526.651393
gap = 0.061278
node_count = 3
columns = 353
```

这说明 Phase2 pressure 字段链路可以观测，但 seed61635 的 dual 仍未移动；这仍支持“formulation/cuts 下界不足”的判断。

字段语义固定为：

```text
same/separate negative severity = max(0, -best_reduced_cost)
severity_sum = same + separate
severity_gap = abs(same - separate)
balance_ratio = min(severity_same, severity_separate) / max(...)
  max = 0 时显式记为 0.0；不能把缺失解释成 0 pressure
presence_gap = abs(1[same_has_negative] - 1[separate_has_negative])
```

同一条链还必须保留：

```text
phase2_same_child_budget
phase2_separate_child_budget
phase2_generated_sequences
phase2_evaluated_timed_trips
phase2_child_wall_time_balance_gap
phase2_child_status_mismatch
```

硬 gate 当前状态：

| Gate | 状态 | 证据 |
|---|---|---|
| A solver JSONL event | 通过 | V777 log 中 59 个 candidate 记录有 pressure key；`phase2_probe_count_total=3`，非零 severity candidate=2 |
| B impact audit row | 通过但 selected 非零覆盖不足 | `journey_branch_impact_row_v2` / `training_row_v2` 已有字段；本次 selected `[3,4]` pressure 为 0 |
| C replay runbook row | 通过 | `routeopt_bkf_staged` runbook 正常避开高 pressure；另建 `pressure_coverage` runbook 包含 `[1,9]`，`severity_sum=14.881469` |
| D paired delta row | 通过 | `baseline_raw_row` 和 `alternative_raw_row` 都保留 pressure keys；`[1,9]` alternative 非零穿透到 delta row |
| E GAT manifest schema | 通过 | `phase2_pressure_context_features`、observed/nonzero counts、`missing_phase2_pressure_is_not_low_pressure=true` 已写入 manifest |
| F tensor 非零覆盖 | 局部通过，不可训练 | V777 pressure dataset `sample_count=1`、`phase2_pressure_nonzero_sample_count=1`、`phase2_pressure_coverage_ready=true`，但 `pressure_aware_training_dataset_ready=false` |

新增/更新产物：

```text
BPC_future/results/20260629_v777_v773_phase2_seed61635_45/
BPC_future/results/journey_branch_impact_v777_v773_phase2_seed61635_45/
BPC_future/results/journey_branch_candidate_replay_runbook_v777_v773_phase2_seed61635_45/
BPC_future/results/journey_branch_candidate_replay_runbook_v777_pressure_coverage_seed61635_45/
BPC_future/results/journey_paired_probe_summary_v777_pressure_coverage_seed61635_45/
BPC_future/results/journey_paired_probe_delta_rows_v777_pressure_coverage_seed61635_45/
BPC_future/data/gat_branch_action_sanity/v777_pressure_coverage_seed61635_45/
```

对应报告：

```text
BPC_future/logical_graph/run_reports/20260629_bpc_future_v777_v773_phase2_seed61635_impact_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v777_v773_phase2_seed61635_replay_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v777_pressure_coverage_seed61635_replay_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v777_pressure_coverage_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v777_pressure_coverage_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v777_pressure_coverage_gat_dataset_zh.md
```

重要边界：这些 row 和 dataset 仍是 diagnostic/proxy-only。缺失 pressure 不等于低 pressure；pressure 字段只能用于排序、调度、诊断和离线训练，不提供 official lower bound、certificate、fathom 或 prune。

### 2.2.2 06月29日 16:37 V778/V779 seed61311 pressure 扩样结论

本轮把 hard gate 从 seed61635 扩到 seed61311，但结论要分开看：

```text
V778 seed61311 routeopt_bkf_v762 150s source run:
status = TIME_LIMIT
primal = 575.008740
dual = 547.186422
gap = 0.048386
node_count = 10
columns = 439
```

这不是 seed61311 no-regression 通过；它反而提示当前 `routeopt_bkf_v762` / pressure-aware opt-in 配置可能相对 V750 `routeopt_bkf_v736` 有回归风险。后续必须单独复跑 v736/v762 对照，不能把 seed61311 150s TIME_LIMIT 当作成功路径。

V778 solver log 的 pressure 字段覆盖是有效的：

```text
branch_candidate_events = 8
phase2_probe_count_total = 24
pressure observed count = 290 / field
nonzero severity count = 5 / field
nonzero presence_gap count = 0
```

其中 node=2/depth=1 的 selected baseline `[5,13]` 和 alternative `[7,13]` 都有真实非零 pressure：

| pair | same severity | separate severity | sum | gap | balance |
|---|---:|---:|---:|---:|---:|
| [5,13] | 0.300191 | 3.193010778 | 3.493201778 | 2.892819778 | 0.094015029 |
| [7,13] | 0.300191 | 3.497742704 | 3.797933704 | 3.197551704 | 0.085824209 |

但 V778 的 45s paired child-probe 没有到达 source target state：

```text
summary label_counts = {"missing_result": 3, "target_not_replayed": 3}
delta output_row_count = 0
```

根因不是字段缺失，而是 replay budget 太短。source run 约 78s 才到 node=2/depth=1；45s replay 只重放到 root forced branch，无法产生可转换 paired row。

为验证 reachability，本轮新增 V779 窄 replay：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v779_pressure_coverage_seed61311_120/
time_limit = 120s
executed entries = node=2 baseline [5,13] + alternative [7,13]
baseline replay wall = 82.02s
alternative replay wall = 83.31s
```

V779 成功命中 target state：

```text
baseline node=2 selected_pair = [5,13], forced_pair = [5,13]
alternative node=2 selected_pair = [7,13], forced_pair = [7,13]
paired summary label_counts = {"missing_result": 5, "neutral_proxy": 1}
delta output_row_count = 1
delta label = paired_probe_neutral_proxy
```

这说明 seed61311 的 Gate D 已经闭合：`baseline_raw_row` 和 `alternative_raw_row` 均保留了 phase2 severity、budget、generated/evaluated/wall-time 字段。由于该 comparison 是 neutral proxy，它不会进入当前 GAT training samples；合并 V777+V779 的 dataset smoke 仍只有 1 个可训练样本：

```text
raw_row_count = 4
sample_count = 1
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 1
pressure_aware_training_dataset_ready = false
```

这个 fail-closed 状态是正确的：V779 扩展了真实 hard-case row 覆盖，但还没满足训练门槛。

### 2.2.3 06月29日 16:41 V780 seed61311 v736 对照

为确认 seed61311 回归是否由 v762/pressure-aware penalty 单独引入，本轮用同一当前代码态复跑了 `routeopt_bkf_v736` 150s：

```text
V780 seed61311 routeopt_bkf_v736 150s:
status = TIME_LIMIT
primal = 575.008740
dual = 547.186422
gap = 0.048386
node_count = 10
columns = 439
```

该结果与 V778 `routeopt_bkf_v762` 150s 完全一致。两者 branch sequence 也一致：

```text
(0,d0) [2,16]
(1,d1) [5,13]
(2,d1) [5,13]
(5,d2) [16,20]
(6,d2) [17,20]
(7,d3) [5,14]
(8,d3) [3,20]
(9,d3) [3,10]
```

因此当前证据不支持“v762 pressure penalty 单独导致 seed61311 回归”。更准确的判断是：当前代码态/配置组合没有复现 V750 中 `routeopt_bkf_v736` 的 `OPTIMAL 113.795881s`，需要先做版本差分或配置差分定位，再把 seed61311 当作 no-regression smoke。

### 2.2.4 06月29日 16:48 V781 seed61311 V750-equivalent 配置定位

本轮继续定位 V780 与 V750 的差异，发现 V780 不是 V750-equivalent 复跑。V780 只设置了 `routeopt_bkf_v736` preset 和 Phase1/Phase2/BKF score order，缺少 V750 中三个关键 opt-in：

```text
journey_branch_candidate_phased_testing_dynamic_k_enabled=True
journey_branch_candidate_phased_testing_phase1_cut_snapshot_enabled=True
journey_dynamic_subset_row_cuts_enabled=True
```

日志也直接确认 V780 root candidate event：

```text
phased_testing_preset = routeopt_bkf_v736
phased_testing_dynamic_k_enabled = False
phased_testing_phase1_cut_snapshot_enabled = False
subset_row_cuts_added = 0
```

注意：`routeopt_bkf_v736` preset 只填入 staged 参数默认值，例如 `base_priority=fractionality`、Phase1/Phase2 candidate cap、Phase2 0.08s budget、dynamic-K 的 min/max/diverse-pool 参数；它不会自动打开 `dynamic_k_enabled`，也不会自动打开 dynamic SRC cuts 或 snapshot。这是一个很容易误判的配置边界。

V781 在当前代码态补齐 V750-equivalent seed61311 配置：

```text
journey_branch_candidate_priority = routeopt_bkf_staged
journey_branch_candidate_phased_testing_preset = routeopt_bkf_v736
journey_branch_candidate_phased_testing_dynamic_k_enabled = True
journey_branch_candidate_phased_testing_phase1_cut_snapshot_enabled = True
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_*_weight = 0
journey_dynamic_subset_row_audit_enabled = True
journey_dynamic_subset_row_cuts_enabled = True
journey_dynamic_subset_row_cut_gate_enabled = True
journey_dynamic_subset_row_cut_gate_min_violated = 1
journey_dynamic_subset_row_cut_gate_min_best_violation = 0.25
journey_dynamic_subset_row_cut_budget = 600
journey_dynamic_subset_row_max_depth = 1
journey_dynamic_subset_row_max_rounds = 2
journey_dynamic_subset_row_max_subset_size = 6
journey_dynamic_subset_row_max_added = 20
```

结果：

```text
V781 seed61311 V750-equivalent 180s:
status = OPTIMAL
primal = 570.891015
dual = 570.891015
gap = 0.0
time = 110.045925s
node_count = 7
columns = 463
pricing_calls = 59
exact_pricing_calls = 30
subset_row_cuts_added = 20
```

与 V736/V749/V750 的核心证据一致：seed61311 好路径可以在当前代码态复现；上一轮 V778/V780 的 timeout 是配置不等价导致，而不是当前代码态必然回归，也不是 v762 pressure penalty 的独立证据。

V781 branch path 的关键前缀也回到 V750/V736 好路径：

```text
node0 depth0: RF(2,16)
node1 depth1: RF(5,13)
node2 depth1: RF(5,14)
```

对比 V780：

| run | status | time | node_count | columns | subset SRC | dynamic-K | snapshot | branch after node2 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| V780 v736-only | TIME_LIMIT | 150.021203 | 10 | 439 | 0 | off | off | bad tail `[5,13] -> [16,20] -> ...` |
| V781 V750-equivalent | OPTIMAL | 110.045925 | 7 | 463 | 20 | on | on | good tail after `[5,14]` |

后续凡是用 seed61311 做 no-regression smoke，必须显式说明是：

1. `v736-only staged preset`，只测 branch controller；
2. 还是 `V750-equivalent branch + dynamic SRC + snapshot`，测 branch-cut 联动。

不能再把二者混用。pressure-aware 扩样如果要判断“seed61311 不回归”，应优先使用 V750-equivalent 模板；如果只做字段链路和 raw row coverage，可以使用 v736-only，但报告必须标为 diagnostic-only。

### 2.2.5 06月29日 16:52 V782 V762 pressure-aware no-regression 对照

本轮用同一个 V750-equivalent 模板，把 preset 从 `routeopt_bkf_v736` 换成 `routeopt_bkf_v762`，验证 V773/V774 pressure-aware 字段和 v762 route-order penalty 是否破坏 seed61311 好路径。

结果：

```text
V782 seed61311 routeopt_bkf_v762 + V750-equivalent template 180s:
status = OPTIMAL
primal = 570.891015
dual = 570.891015
gap = 0.0
time = 111.296544s
node_count = 7
columns = 463
pricing_calls = 59
exact_pricing_calls = 30
subset_row_cuts_added = 20
```

与 V781 `routeopt_bkf_v736 + V750-equivalent template` 对比：

| run | preset | status | time | node_count | columns | pricing | exact pricing | subset SRC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| V781 | v736 | OPTIMAL | 110.045925 | 7 | 463 | 59 | 30 | 20 |
| V782 | v762 | OPTIMAL | 111.296544 | 7 | 463 | 59 | 30 | 20 |

两者 branch path 一致：

```text
node0 depth0: RF(2,16)=same_vehicle
node1 depth1: RF(5,13)=same_vehicle
node2 depth1: RF(5,14)=same_vehicle
node5 depth2: RF(13,14)=same_vehicle
node6 depth2: RF(13,14)=same_vehicle
```

因此 seed61311 的 no-regression gate 在正确 V750-equivalent 模板下通过。上一轮 V778/V780 的 timeout 不是 v762 pressure-aware 本身破坏好路径，而是少开了 dynamic-K / gated dynamic SRC / snapshot 这些 branch-cut 联动开关。

V782 也提供了 pressure 字段覆盖：

```text
candidate_events = 5
pressure observed count = 268 / field
nonzero separate severity / severity_sum / severity_gap / presence_gap count = 6
```

但这仍是 solver candidate-row 覆盖，不等价于 GAT 可训练样本覆盖。训练前仍需要 paired replay/delta rows 中出现非 neutral positive/negative，并且 `pressure_aware_training_dataset_ready=true`。

### 2.2.6 06月29日 17:00 V783 V750-equivalent high-pressure paired replay

本轮继续执行 seed61311 pressure 扩样，但不再使用 v736-only replay。source log 选择 V782 的 V750-equivalent `routeopt_bkf_v762` run，并把 replay command 显式补齐 V750-equivalent 配置：

```text
dynamic-K = on
phase1 cut snapshot = on, BKF snapshot weights = 0
dynamic SRC audit/cuts/gate = on
cut_gate_min_violated = 1
cut_gate_min_best_violation = 0.25
cut_budget = 600
max_depth = 1
max_rounds = 2
max_subset_size = 6
max_added = 20
```

注意：这是对生成 runbook 的 post-process patch。当前 `build_journey_branch_candidate_replay_runbook.py` 还没有正式参数来继承 V750-equivalent replay sets，因此本轮先把 patched runbook 作为实证产物；如果后续继续大量使用这个模板，应把它固化成脚本参数并加测试。

V782 source log 中 node=2 的 alternatives 基本没有非零 pressure；真正有压力的是 node=6/depth=2：

| pair | role | severity_sum | presence_gap | source min child gain |
|---|---|---:|---:|---:|
| [13,14] | selected baseline | 1.992541 | 1 | 4.8692635 |
| [3,13] | high-pressure alternative | 11.024517 | 1 | 1.17132325 |

本轮只执行 node=6 的两条 paired child-probe：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v783_v782_v750_equiv_seed61311_depth2_pressure/
baseline [13,14] solver wall = 85.80s
alternative [3,13] solver wall = 85.10s
```

两条 replay 都命中 target state，并且日志确认 replay 中仍是 V750-equivalent：

```text
node0: forced [2,16], preset routeopt_bkf_v762, dynamic_k=True, snapshot=True
node2: forced [5,14], preset routeopt_bkf_v762, dynamic_k=True, snapshot=True
node6 baseline: forced [13,14], selected [13,14]
node6 alternative: forced [3,13], selected [3,13]
```

paired summary / delta 结果：

```text
summary label_counts = {"missing_result": 5, "neutral_proxy": 1}
target_hit_count for node6 group = 2
valid_observed_alternative_count = 1
best_wall_time_gain = 0.696127
delta output_row_count = 1
delta label = paired_probe_neutral_proxy
```

V783 的 delta row 中 `baseline_raw_row` 和 `alternative_raw_row` 都保留了非零 pressure 字段：

| raw row | same severity | separate severity | severity_sum | severity_gap | presence_gap |
|---|---:|---:|---:|---:|---:|
| baseline [13,14] | 0.0 | 1.992541 | 1.992541 | 1.992541 | 1 |
| alternative [3,13] | 0.0 | 11.024517 | 11.024517 | 11.024517 | 1 |

合并 V777 + V779 + V783 后的 dataset smoke：

```text
raw_row_count = 5
sample_count = 1
row_kind_counts = {"paired_probe_neutral_proxy": 4, "paired_probe_positive_proxy": 1}
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 1
pressure_aware_training_dataset_ready = false
sanity_training_dataset_ready = false
```

结论：V783 增加了 V750-equivalent high-pressure raw coverage，并再次验证 Gate D/E 能保留 nonzero pressure；但它仍是 neutral proxy，不增加训练样本。下一轮如果还沿 seed61311 扩样，应优先：

1. 运行 node6 另外两个 alternatives `[3,19]`、`[13,19]`，补全同 context 对照，确认是否存在非 neutral；
2. 或转向 V545 未闭环实例，避免在 seed61311 上继续产出大量 neutral rows。

### 2.2.7 06月29日 17:06 V784 seed61311 node6 剩余 alternatives 补完

本轮继续使用 V783 patched V750-equivalent runbook，补跑 node6/depth2 的剩余两个 alternatives：

```text
[3,19] solver wall = 85.06s
[13,19] solver wall = 85.26s
```

它们都命中 target state，并且 replay 日志继续确认：

```text
preset = routeopt_bkf_v762
dynamic_k = True
snapshot = True
node6 [3,19] forced_pair 命中 selected_pair
node6 [13,19] forced_pair 命中 selected_pair
```

重建 V783 paired summary 后，node6 同 context 结果为：

```text
observed_alternative_count = 3
valid_observed_alternative_count = 3
target_hit_count = 4
target_not_replayed_count = 0
target_pair_not_selected_count = 0
label_counts = {"neutral_proxy": 3}
best_wall_time_gain = 0.740418
```

delta rows：

```text
output_row_count = 3
output_counterfactual_label_counts = {"paired_probe_neutral_proxy": 3}
```

合并 V777 + V779 + V784 后的 dataset smoke：

```text
raw_row_count = 7
sample_count = 1
row_kind_counts = {"paired_probe_neutral_proxy": 6, "paired_probe_positive_proxy": 1}
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 1
pressure_aware_training_dataset_ready = false
```

结论：seed61311 的 V750-equivalent node6 context 已完整补完，replay reachability 没问题，high-pressure raw 字段也能穿透到 delta rows；但三个 alternatives 全是 neutral proxy，没有新增可训练 positive/negative。继续在 seed61311 上扩同类 child-probe 的边际收益很低。

因此从下一轮开始，Track A 应停止把 seed61311 作为主要扩样对象，转向 2-4 个 V545 未闭环 20-scale 实例；seed61311 只保留为 no-regression / schema gate / V750-equivalent 模板检查。

下一步优先级是：

1. 选择 2-4 个 V545 未闭环 20-scale 实例，按 V779/V783 的 reachability + V750-equivalent replay 经验生成 paired rows；
2. 对新实例优先挑 high pressure / misleading LP-gain contexts，而不是只按 depth 或 wall time 扩；
3. seed61635 继续走 cuts/formulation 主线，不能因为 seed61311 no-regression 通过就回到只调 pair 权重。

### 2.2.8 06月29日 17:45 V785-V789 V545 未闭环实例首轮扩样

本轮开始从 V545 未闭环 20-scale 实例里挑新对象，先看两个 greedy-anchor failure：

```text
seed61308 apollo15 greedy-anchor:
  V545 old log first branch around 243.65s
  V785 V750-equivalent 180s source:
    status = TIME_LIMIT
    primal = 513.366132
    dual = None
    node_count = 1
    branch_candidate_events = 0

seed61744 tranquillitatis greedy-anchor:
  V545 old log first branch around 107.98s
  V786 V750-equivalent 180s source:
    status = TIME_LIMIT
    primal = 501.805380
    dual = None
    node_count = 1
    branch_candidate_events = 0
```

结论一：V750-equivalent 模板是 no-regression / performance 对照必须保留的模板，但对部分 V545 未闭环实例在 180s 内过于 root-sticky，不能直接作为高效扩样 source。seed61308 至少需要更长 source budget；seed61744 在 V750-equivalent 下也没产出 candidate。

为获得 pressure context，本轮额外跑了 diagnostic-only 的 V787 v762-only source：

```text
V787 seed61744 v762-only 180s:
  status = TIME_LIMIT
  primal = 497.385738
  dual = 460.336407
  gap = 0.074488
  node_count = 3

branch path:
  node0 selected [3,6] at 114.025544s
  node1 selected [2,11] at 174.181757s

node1 pressure:
  selected [2,11] severity_sum = 8.570685
  alt [2,17] severity_sum = 10.543190
  alt [15,20] severity_sum = 0
  alt [9,20] severity_sum = 0
```

V788/V789 runbook 用这个 node1 context 生成 paired replay。V788 初版漏掉 source-side phased-testing 参数，summary 为 `target_not_replayed`。V789 patched runbook 已补上：

```text
journey_branch_candidate_phased_testing_preset=routeopt_bkf_v762
journey_branch_candidate_phased_testing_enabled=True
journey_branch_candidate_phased_testing_phase1_lp_enabled=True
journey_branch_candidate_phased_testing_phase2_heuristic_enabled=True
journey_branch_candidate_phased_testing_bkf_score_order_enabled=True
```

但 V789 实跑 baseline `[2,11]` 和 high-pressure alternative `[2,17]` 后仍未命中 target：

```text
baseline [2,11]:
  status = TIME_LIMIT
  solving_time = 100.060978
  wall_time = 102.188337
  node_count = 1
  label = target_not_replayed

alternative [2,17]:
  status = TIME_LIMIT
  solving_time = 100.058180
  wall_time = 102.153038
  node_count = 1
  label = target_not_replayed

V789 paired summary:
  result_available_entry_count = 2
  target_hit_count = 0
  valid_observed_alternative_count = 0
  production_ready = false

V789 delta:
  output_row_count = 0
  skipped_counts = {"not_convertible": 4}
```

日志核对显示 V789 两条 replay 都停在 root，只记录到 `journey_tail_action_no_column_early_branch_gate`，没有 `journey_branch_candidates` 或 `journey_branch`。根因不是 pressure 字段缺失，而是 replay 模板没有稳定复现 V787 的 source branch reachability；实际求解约 100s 就返回 TIME_LIMIT，早于 V787 第一次正常 branch 的 114s。该结果不能进入训练。

本轮同时补做了 Gate D/E/F 级别核验：

```text
V777 delta rows: rows=3, baseline_raw_row/alternative_raw_row raw_ok=3
V779 delta rows: rows=1, baseline_raw_row/alternative_raw_row raw_ok=1
V783 delta rows: rows=3, baseline_raw_row/alternative_raw_row raw_ok=3

pressure keys 在 alternative_raw_row 中全部 present；
V777/V779/V783 均有 nonzero pressure 覆盖；
V789 runbook source rows 也保留 nonzero pressure 字段，但 replay target miss，所以 delta=0。
```

合并 V777 + V779 + V783 + V789 后的 dataset builder 结果：

```text
raw_row_count = 7
sample_count = 1
row_kind_counts = {"paired_probe_neutral_proxy": 6, "paired_probe_positive_proxy": 1}
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 1
pressure_aware_training_dataset_ready = false
DATASET_EXIT = 1
```

这次失败样本反而强化了下一轮 gate：

1. source runbook row 有 pressure 字段不等于可训练；
2. paired replay 必须 `target_hit_count > 0` 且 baseline/alternative 同 context 可比，才能进 delta；
3. missing pressure 不能当 0，target miss 更不能当 neutral；
4. V750-equivalent 用于验收和 no-regression，v762-only source 只能标成 diagnostic-only；
5. 如果继续用 runbook replay V787 这类 source，必须先修 source-template replay：至少把 solver budget / early-branch reachability / forced path 配置作为显式模板参数，而不是事后 patch `commands.sh`。

新增产物：

```text
BPC_future/results/20260629_v785_v762_v750_equiv_seed61308_180/
BPC_future/results/20260629_v786_v762_v750_equiv_seed61744_180/
BPC_future/results/20260629_v787_v762_only_seed61744_180/
BPC_future/results/journey_branch_candidate_replay_runbook_v789_v787_seed61744_depth1_pressure_patched/
BPC_future/results/journey_paired_probe_summary_v789_v787_seed61744_depth1_pressure/
BPC_future/results/journey_paired_probe_delta_rows_v789_v787_seed61744_depth1_pressure/
BPC_future/data/gat_branch_action_sanity/v789_pressure_coverage_seed61635_seed61311_seed61744/
```

对应报告：

```text
BPC_future/logical_graph/run_reports/20260629_bpc_future_v789_v787_seed61744_depth1_replay_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v789_v787_seed61744_depth1_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v789_v787_seed61744_depth1_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v789_pressure_coverage_gat_dataset_zh.md
```

### 2.2.9 06月29日 17:58 V790 replay source-template gate

本轮先把 V789 的失败原因继续收窄，不继续盲跑更多 alternatives。代码侧新增了两个 runbook builder 参数：

```text
--replay-set key=value
  显式把 source run 的 opt-in replay 模板写进每条 command；
  例如 v762-only phased testing preset / phase1 / phase2 / score-order。

--probe-time-margin-after-source-event FLOAT
  对 child_probe entry，把 effective time-limit 提高到：
    max(base_time_limit, ceil(source_event_time + margin))
  防止 late source context 被统一短预算 replay，尚未到 target branch 就提前结束。
```

focused 验证：

```text
python -m py_compile \
  BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py \
  BPC_future/tests/test_journey_branch_candidate_replay_runbook.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook

结果：Ran 23 tests OK
```

用新参数重建 seed61744 depth1 runbook：

```text
V790 runbook:
  source = V787 seed61744 v762-only log
  probe_mode = child_probe
  paired_probe = true
  source_event_time = 174.178222
  base time_limit = 220
  probe_time_margin_after_source_event = 90
  effective_time_limit = 265
  replay_overrides =
    journey_branch_candidate_phased_testing_preset=routeopt_bkf_v762
    journey_branch_candidate_phased_testing_enabled=True
    journey_branch_candidate_phased_testing_phase1_lp_enabled=True
    journey_branch_candidate_phased_testing_phase2_heuristic_enabled=True
    journey_branch_candidate_phased_testing_bkf_score_order_enabled=True

entries:
  baseline [2,11], severity_sum = 8.570685
  alternative [2,17], severity_sum = 10.543190
```

V790 baseline 实跑结果：

```text
status = TIME_LIMIT
solving_time = 253.053377
wall_time = 256.173324
node_count = 4
primal = 497.385738
dual = 460.336407
gap = 0.074488

branch events:
  depth0 node0 selected [3,6], forced_pair=[3,6], time=113.890004
  depth1 node2 selected [2,10], forced_pair=None, time=195.541501
  depth2 node3 selected [1,13], forced_pair=None, time=254.922979
```

这说明 V790 修掉了 V789 的第一个问题：不再在 100s 左右提前停在 root，且 root `[3,6]` force 成功。但它没有命中 V787 的 target context：

```text
V787 source:
  depth1 node1 在 same_vehicle child 上 173.703182s 得到 FULL_LP_CERTIFICATE；
  随后 selected [2,11]。

V790 replay:
  same_vehicle child node1 在 154.053412s 变成 INCOMPLETE_LIMIT；
  没有产生 branch_candidates；
  solver 转到 separate_vehicle child node2；
  node2 selected [2,10]，force path 不匹配，所以 forced_pair=None。
```

V790 paired summary / delta：

```text
result_available_entry_count = 1
target_hit_count = 0
target_not_replayed_entry_count = 1
valid_observed_alternative_entry_count = 0
production_ready = false

delta output_row_count = 0
skipped_counts = {"not_convertible": 2}
```

结论：

1. `--replay-set` 和 adaptive `effective_time_limit` 是必要的，后续 runbook 不应再手工 patch `commands.sh`；
2. V789 的短预算/root miss 已被 V790 修掉，但 target-hit gate 仍未通过；
3. 下一层 gate 不是继续增大 alt 数，而是验证同一 ancestor branch direction 下的 target node 是否可复现；
4. 对 V787 这种 child-probe source，必须记录 `target_node_path_stable=false`，不能把 V790 row 作为 neutral 或 hard negative；
5. 继续做 V545 未闭环扩样前，runbook / summary 最好新增一个更硬的 reachability reason：`ancestor_forced_but_target_child_no_branch`，用于区分 V789 的 `root_not_reached` 和 V790 的 `target_child_no_branch`。

新增/更新产物：

```text
BPC_future/results/journey_branch_candidate_replay_runbook_v790_v787_seed61744_depth1_template_gate/
BPC_future/results/journey_paired_probe_summary_v790_v787_seed61744_depth1_template_gate/
BPC_future/results/journey_paired_probe_delta_rows_v790_v787_seed61744_depth1_template_gate/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v790_v787_seed61744_depth1_template_gate_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v790_v787_seed61744_depth1_template_gate_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v790_v787_seed61744_depth1_template_gate_delta_rows_zh.md
```

### 2.2.10 06月29日 18:04 V791 target reachability reason gate

本轮把 V790 的人工判断固化到 paired summary 脚本中：不改变训练标签、不生成训练 row，只给 target miss 增加更细的 `target_replay_reason`。

代码更新：

```text
BPC_future/scripts/summarize_journey_paired_probe_runbook.py
  新增 source_path_edges 解析；
  replay log 中按 ancestor branch direction 追踪 replay_target_node_id；
  兼容旧 target_replay_status；
  新增 target_replay_reason / target_node_path_stable / source_path_edge_count；
  summary.json / report 新增 target_replay_reason_counts。

BPC_future/tests/test_journey_paired_probe_summary.py
  新增 ancestor forced 但 target child 无 branch 的测试；
  新增 root 未到达 ancestor branch 的测试。
```

focused 验证：

```text
python -m py_compile \
  BPC_future/scripts/summarize_journey_paired_probe_runbook.py \
  BPC_future/tests/test_journey_paired_probe_summary.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_journey_paired_probe_summary

结果：Ran 4 tests OK
```

用 V791 重新汇总 V789 / V790：

```text
V791 over V789:
  target_replay_reason_counts =
    log_missing: 2
    root_not_reached: 2
  target_not_replayed_entry_count = 2
  delta output_row_count = 0

V791 over V790:
  target_replay_reason_counts =
    ancestor_forced_but_target_child_no_branch: 1
    log_missing: 1
  target_not_replayed_entry_count = 1
  delta output_row_count = 0
```

这正式区分了两类失败：

1. V789：短预算/root 还没到 ancestor branch，属于 `root_not_reached`；
2. V790：root ancestor force 成功，但 same-child target node 没复现 branch，属于 `ancestor_forced_but_target_child_no_branch`。

合并旧可用 delta + V791 空 delta 的 dataset smoke：

```text
raw_row_count = 7
sample_count = 1
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 1
pressure_aware_training_dataset_ready = false
DATASET_EXIT = 1
```

结论：

1. V791 reachability reason gate 解决了“target_not_replayed 太粗”的问题；
2. 所有 target miss row 仍 fail-closed，不进入 delta/training；
3. 下一步不应继续增加 V787 alternatives，而应决定如何处理 `ancestor_forced_but_target_child_no_branch`：
   - 要么只采样 source path 更稳定的 branch contexts；
   - 要么把 replay budget / child certificate budget 做成更贴近 source 的模板；
   - 要么把这种 row 作为不可训练的 reachability-negative 统计，而不是 branch quality label。

新增产物：

```text
BPC_future/results/journey_paired_probe_summary_v791_v789_reason_audit/
BPC_future/results/journey_paired_probe_summary_v791_v790_reason_audit/
BPC_future/results/journey_paired_probe_delta_rows_v791_v789_reason_audit/
BPC_future/results/journey_paired_probe_delta_rows_v791_v790_reason_audit/
BPC_future/data/gat_branch_action_sanity/v791_pressure_coverage_with_reachability_reason_empty_deltas/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v791_v789_reason_audit_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v791_v790_reason_audit_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v791_v789_reason_audit_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v791_v790_reason_audit_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v791_pressure_coverage_with_reason_gat_dataset_zh.md
```

### 2.2.11 06月29日 18:08 V792 delta-stage reachability reason preservation

本轮把 V791 的 reachability reason 继续传到 paired delta summary，避免进入 delta/dataset 阶段后只剩粗粒度 `not_convertible`。

代码更新：

```text
BPC_future/scripts/build_journey_paired_probe_delta_rows.py
  summary/report 新增：
    nonconvertible_label_counts
    nonconvertible_target_replay_reason_counts

BPC_future/tests/test_journey_paired_probe_delta_rows.py
  新增 target_not_replayed row 的 nonconvertible reason 统计测试；
  确认 target miss row 不输出 delta。
```

focused 验证：

```text
python -m py_compile \
  BPC_future/scripts/build_journey_paired_probe_delta_rows.py \
  BPC_future/tests/test_journey_paired_probe_delta_rows.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_journey_paired_probe_delta_rows

结果：Ran 2 tests OK
```

V792 over V791 reason summaries：

```text
V792 over V789:
  output_row_count = 0
  nonconvertible_label_counts =
    baseline: 1
    missing_result: 2
    target_not_replayed: 1
  nonconvertible_target_replay_reason_counts =
    log_missing: 2
    root_not_reached: 2

V792 over V790:
  output_row_count = 0
  nonconvertible_label_counts =
    baseline: 1
    missing_result: 1
  nonconvertible_target_replay_reason_counts =
    ancestor_forced_but_target_child_no_branch: 1
    log_missing: 1
```

合并旧可用 delta + V792 空 delta 的 dataset smoke：

```text
raw_row_count = 7
sample_count = 1
phase2_pressure_coverage_ready = true
pressure_aware_training_dataset_ready = false
DATASET_EXIT = 1
```

当前处理策略正式固定为：

1. `target_not_replayed` / `target_pair_not_selected` / missing-result rows 只做 reachability diagnostics；
2. `root_not_reached`、`ancestor_forced_but_target_child_no_branch` 不能当 neutral、hard negative 或 branch quality label；
3. paired delta 继续 fail-closed，不输出训练 row；
4. dataset 只读取可转换 delta rows，V792 空 delta 不改变 `raw_row_count` 和 `sample_count`；
5. 下一步 V545 扩样应优先挑 source-stable contexts，或先提高 replay target stability，而不是在 V787 这个不稳定 context 上继续补 alternatives。

新增产物：

```text
BPC_future/results/journey_paired_probe_delta_rows_v792_v789_reason_audit/
BPC_future/results/journey_paired_probe_delta_rows_v792_v790_reason_audit/
BPC_future/data/gat_branch_action_sanity/v792_pressure_coverage_with_delta_reason_counts/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v792_v789_reason_audit_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v792_v790_reason_audit_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v792_pressure_coverage_with_delta_reason_counts_gat_dataset_zh.md
```

### 2.2.12 06月29日 18:20 CST V793 source-stable root replay budget gate

本轮按 V792 结论转向 source-stable root context，而不是继续补 V787 depth1 alternatives。选择 V787 seed61744 的 root branch event：

```text
source depth/node = 0 / 0
source selected pair = [3,6]
source event time = 114.02376
pressure alternative = [1,20]
source_alt_phase2_negative_severity_sum = 0.700773
source_alt_phase2_negative_child_presence_balance_gap = 1
```

V793 runbook 生成 4 条 entry：

```text
1 selected_baseline [3,6]
2 alternative [3,4]
3 alternative [1,20]  # pressure-bearing
4 alternative [18,20]
effective_time_limit = 220
probe_time_margin_after_source_event = 80
```

实际只跑最小闭环的 baseline `[3,6]` 和 pressure alt `[1,20]`：

```text
[3,6] status = TIME_LIMIT, solving_time = 100.057962, wall = 134.488738, nodes = 1, columns = 651
[1,20] status = TIME_LIMIT, solving_time = 100.057207, wall = 102.212317, nodes = 1, columns = 651
```

paired summary 结论：

```text
target_hit_count = 0
valid_observed_alternative_count = 0
label_counts =
  missing_result: 2
  target_not_replayed: 1
target_replay_reason_counts =
  log_missing: 2
  source_node_not_replayed: 2
```

delta / dataset gate 结论：

```text
V793 delta output_row_count = 0
nonconvertible_label_counts =
  baseline: 1
  missing_result: 2
  target_not_replayed: 1
nonconvertible_target_replay_reason_counts =
  log_missing: 2
  source_node_not_replayed: 2

combined dataset:
  raw_row_count = 7
  sample_count = 1
  phase2_pressure_coverage_ready = true
  phase2_pressure_nonzero_sample_count = 1
  pressure_aware_training_dataset_ready = false
  DATASET_EXIT = 1
```

关键诊断：

1. V793 并没有证明 root source-stable context 不可用；它证明当前 replay 模板仍会在进入 branch candidate 前 fail-closed。
2. replay 日志没有 `journey_branch_candidates` / phased probe 事件；root CG 后 completion/final pricing 以 `reason=time_limit,status=INCOMPLETE` 结束，节点被判 `PRICING_INCOMPLETE`。
3. 原始 V787 在同一 root 位置先出现 `journey_tail_action_no_column_early_branch_gate`，随后 `direct_label_no_negative_journey`，再记录 root branch candidates；当前 V793 replay 没复现这个 final-probe path。
4. 这说明下一步必须做 matched-budget / matched-template reachability gate，例如用 V787 的 180s source budget 重放 root `[3,6]` 和 `[1,20]`，或显式固定 final-probe reserve 设置；不要把旧 V787 source log 直接当成可训练 row。
5. V793 的 0-row delta 是正确 fail-closed 行为：不当 neutral、不当 hard negative、不进入 branch-quality label。

新增产物：

```text
BPC_future/results/journey_branch_candidate_replay_runbook_v793_v787_seed61744_root_source_stable/
BPC_future/results/journey_paired_probe_summary_v793_v787_seed61744_root_source_stable/
BPC_future/results/journey_paired_probe_delta_rows_v793_v787_seed61744_root_source_stable/
BPC_future/data/gat_branch_action_sanity/v793_pressure_coverage_with_source_stable_root/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v793_v787_seed61744_root_source_stable_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v793_v787_seed61744_root_source_stable_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v793_v787_seed61744_root_source_stable_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v793_pressure_coverage_with_source_stable_root_gat_dataset_zh.md
```

执行边界：

- V793 仍是 diagnostic/proxy-only；
- pressure fields 只用于排序、调度、诊断和离线数据 gate；
- `source_node_not_replayed` 只说明 replay target 未闭合，不说明 `[1,20]` branch 质量差；
- missing pressure / missing replay 不能按 0 pressure 处理。

### 2.2.13 06月29日 18:34 CST V794 matched-180 root reachability gate

本轮执行 V793 的下一步：用更贴近 V787 source run 的 matched replay 模板重放 root baseline `[3,6]` 和 pressure alt `[1,20]`。

V794 runbook 设置：

```text
source = V787 seed61744 root branch event
time_limit = 180
probe_max_nodes = 1000
probe_time_margin_after_source_event = None
paired entries = 4
minimal executed entries = [3,6] baseline + [1,20] pressure alternative
```

这修正了 V793 的 root reachability miss：

```text
baseline [3,6]:
  external status = EXTERNAL_TIME_LIMIT
  wall = 180.02543
  root branch_candidates time = 113.031087
  forced_pair = [3,6]
  selected_pair = [3,6]
  best_primal_bound = 497.385738
  best_dual_bound = 460.336407
  gap = 0.074488

pressure alt [1,20]:
  external status = EXTERNAL_TIME_LIMIT
  wall = 180.01715
  root branch_candidates time = 111.479769
  forced_pair = [1,20]
  selected_pair = [1,20]
  best_primal_bound = 499.994967
  best_dual_bound = 460.336407
  gap = 0.079318
```

paired summary：

```text
target_hit_count = 2
valid_observed_alternative_count = 1
label_counts =
  hard_negative_proxy: 1
  missing_result: 2
target_replay_reason_counts =
  target_pair_selected: 2
  log_missing: 2
best_alternative_forced_pair = [1,20]
best_wall_time_gain = 0.00828
```

delta：

```text
output_row_count = 1
output_counterfactual_label_counts =
  paired_probe_hard_negative_proxy: 1
nonconvertible_label_counts =
  baseline: 1
  missing_result: 2
```

这条 row 的 pressure 字段在 `alternative_raw_row` 中真实非零：

```text
alternative_pair = [1,20]
alternative_forced_pair_matched = true
paired_label_type = hard_negative_proxy
paired_wall_time_gain = 0.00828
paired_gap_improvement = -0.00483
source_alt_phase2_negative_severity_sum = 0.700773
source_alt_phase2_same_child_negative_severity = 0.700773
source_alt_phase2_separate_child_negative_severity = 0.0
source_alt_phase2_negative_severity_gap = 0.700773
source_alt_phase2_negative_child_presence_balance_gap = 1
```

合并 dataset gate：

```text
raw_row_count = 8
sample_count = 2
row_kind_counts =
  paired_probe_positive_proxy: 1
  paired_probe_hard_negative_proxy: 1
  paired_probe_neutral_proxy: 6
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 2
phase2_pressure_nonzero_counts =
  phase2_negative_severity_sum: 2
  phase2_negative_severity_gap: 2
  phase2_same_child_negative_severity: 2
  phase2_negative_child_presence_balance_gap: 2
pressure_aware_training_dataset_ready = false
DATASET_EXIT = 1
```

解释：

1. V794 证明 V793 的失败主要是 replay 模板问题；matched-180 能复现 root target branch。
2. `[1,20]` 是一个有真实 phase2 pressure 的 hard-negative proxy：它在 root 可合法强制，但 180s 内 gap 更差，且没有 wall-time / proof gain。
3. 这条 row 是有用的 D/F gate evidence：`alternative_raw_row` 保留非零 pressure，dataset tensor 样本数和非零 pressure 样本数都增加。
4. 它仍是 proxy-only / diagnostic-only，不能当 official proof、certificate、prune 或 production score 依据。
5. 训练仍不能启动；下一步应继续用 matched-180 模板补 2-4 个 V545 未闭环实例或同实例更多 pressure-bearing alternatives，目标是同时增加 positive、hard negative、neutral/misleading LP-gain 覆盖。

新增产物：

```text
BPC_future/results/journey_branch_candidate_replay_runbook_v794_v787_seed61744_root_matched180/
BPC_future/results/journey_paired_probe_summary_v794_v787_seed61744_root_matched180/
BPC_future/results/journey_paired_probe_delta_rows_v794_v787_seed61744_root_matched180/
BPC_future/data/gat_branch_action_sanity/v794_pressure_coverage_with_matched_root_hard_negative/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v794_v787_seed61744_root_matched180_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v794_v787_seed61744_root_matched180_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v794_v787_seed61744_root_matched180_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v794_pressure_coverage_with_matched_root_hard_negative_gat_dataset_zh.md
```

### 2.2.14 06月29日 18:50 CST V795 depth1 widened-node reachability check

本轮继续阶段 A 的 pressure-aware data-chain 扩样，但只在 V787 seed61744 内补 depth1 pressure candidates，原因是：

```text
V785 seed61308 V750-equivalent source: 180s 内无 branch_candidates；
V786 seed61744 V750-equivalent source: 180s 内无 branch_candidates；
V787 seed61744 v762-only source:
  root 非零 pressure alternative 只有 [1,20]，已由 V794 覆盖；
  depth1 有两个非零 pressure candidates：
    selected baseline [2,11], severity_sum = 8.570685
    alternative [2,17], severity_sum = 10.54319
```

V795 runbook：

```text
source = V787 depth1 node1 event
baseline = [2,11]
alternative = [2,17]
ancestor path = force_pair_path:0:3,6=same_vehicle
effective_time_limit = 265
probe_max_nodes = 1000
probe_time_margin_after_source_event = 90
```

实际 replay 结果：

```text
[2,11] baseline:
  external status = EXTERNAL_TIME_LIMIT
  root forced_pair [3,6] 命中
  source child node1 在 time=152.783243 以 reason=time_limit incomplete
  后续 node2 depth1 branch selected_pair = [2,10], forced_pair = None

[2,17] pressure alt:
  external status = EXTERNAL_TIME_LIMIT
  root forced_pair [3,6] 命中
  source child node1 在 time=152.33379 以 reason=time_limit incomplete
  后续 node2 depth1 branch selected_pair = [2,10], forced_pair = None
```

paired summary：

```text
target_hit_count = 0
result_available_entry_count = 2
label_counts =
  target_not_replayed: 1
target_replay_reason_counts =
  ancestor_forced_but_target_child_no_branch: 2
```

delta / dataset gate：

```text
delta output_row_count = 0
nonconvertible_label_counts =
  baseline: 1
  target_not_replayed: 1
nonconvertible_target_replay_reason_counts =
  ancestor_forced_but_target_child_no_branch: 2

combined dataset:
  raw_row_count = 8
  sample_count = 2
  phase2_pressure_nonzero_sample_count = 2
  pressure_aware_training_dataset_ready = false
  DATASET_EXIT = 1
```

解释：

1. V795 证明 V794 的 matched-180 方法只解决了 root source-stable replay；depth1 source path 仍不稳定。
2. 即使把 node budget 放宽到 1000、time-limit 提到 source time + 90s，source child node1 仍在 final pricing time_limit 后 incomplete，不能复现 `[2,11]` / `[2,17]` target branch。
3. 这类 row 只能保留为 reachability diagnostic，不能当 neutral、hard negative 或 branch quality label。
4. 后续阶段 A 扩样应优先找 root-level source-stable contexts，或者设计更强的 child-source replay template；继续在 V787 depth1 上加 alternatives 价值不高。

新增产物：

```text
BPC_future/results/journey_branch_candidate_replay_runbook_v795_v787_seed61744_depth1_matched265_widenodes/
BPC_future/results/journey_paired_probe_summary_v795_v787_seed61744_depth1_matched265_widenodes/
BPC_future/results/journey_paired_probe_delta_rows_v795_v787_seed61744_depth1_matched265_widenodes/
BPC_future/data/gat_branch_action_sanity/v795_pressure_coverage_with_depth1_reachability_fail_closed/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v795_v787_seed61744_depth1_matched265_widenodes_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v795_v787_seed61744_depth1_matched265_widenodes_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v795_v787_seed61744_depth1_matched265_widenodes_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v795_pressure_coverage_with_depth1_reachability_fail_closed_gat_dataset_zh.md
```

### 2.2.15 06月29日 19:05 CST V796 batch root-level pressure pool

本轮根据执行效率问题，把阶段 A 从“单点扩样”改成“批量候选池 + 去重 + 小批次 replay”。

批量 root-level pressure 扫描范围：

```text
BPC_future/results/20260629_*/logs
filter:
  event = journey_branch_candidates
  depth = 0
  phase2_negative_severity_sum > 0
```

扫描结果只有 5 个 root-level 非零 pressure candidates：

```text
seed61311 V781 root:
  selected [2,16], candidate [4,12], severity_sum = 27.972509
seed61635 V776 root:
  selected [3,4], candidate [1,9], severity_sum = 14.881469
seed61635 V777 root:
  selected [3,4], candidate [1,9], severity_sum = 14.881469
seed61311 V782 root:
  selected [2,16], candidate [4,12], severity_sum = 10.719811
seed61744 V787 root:
  selected [3,6], candidate [1,20], severity_sum = 0.700773
```

去重/覆盖判断：

```text
seed61635 [1,9] 已由 V777 进入 delta，label = paired_probe_positive_proxy；
seed61744 [1,20] 已由 V794 进入 delta，label = paired_probe_hard_negative_proxy；
seed61311 [4,12] root 尚未作为 root-level paired delta 覆盖。
```

V796 因此只跑最小小批次：

```text
source = V781 seed61311 root
runbook = V796 wide root runbook
entry_count = 16
实际执行:
  baseline [2,16]
  high-pressure alternative [4,12]
```

两条 replay 都 target-hit：

```text
baseline [2,16]:
  external status = EXTERNAL_TIME_LIMIT
  root branch_candidates time = 25.450602
  forced_pair = [2,16]
  selected_pair = [2,16]
  best_primal_bound = 570.891016
  best_dual_bound = 547.186422
  gap = 0.041522

alternative [4,12]:
  external status = EXTERNAL_TIME_LIMIT
  root branch_candidates time = 25.682444
  forced_pair = [4,12]
  selected_pair = [4,12]
  best_primal_bound = 570.891016
  best_dual_bound = 547.186422
  gap = 0.041522
```

paired summary / delta：

```text
target_hit_count = 2
label_counts =
  neutral_proxy: 1
  missing_result: 14
target_replay_reason_counts =
  target_pair_selected: 2
  log_missing: 14

delta output_row_count = 1
output_counterfactual_label_counts =
  paired_probe_neutral_proxy: 1
```

V796 delta row 的 pressure 字段：

```text
baseline_pair = [2,16]
alternative_pair = [4,12]
alternative_forced_pair_matched = true
paired_label_type = neutral_proxy
paired_wall_time_gain = -0.001163
wall_time_delta = 0.001163
gap_delta = -0.0
alternative source_alt_phase2_negative_severity_sum = 27.972509
alternative source_alt_phase2_same_child_negative_severity = 0.0
alternative source_alt_phase2_separate_child_negative_severity = 27.972509
alternative source_alt_phase2_negative_severity_gap = 27.972509
alternative source_alt_phase2_negative_child_presence_balance_gap = 1
```

合并 dataset gate：

```text
raw_row_count = 9
sample_count = 2
row_kind_counts =
  paired_probe_positive_proxy: 1
  paired_probe_hard_negative_proxy: 1
  paired_probe_neutral_proxy: 7
phase2_pressure_coverage_ready = true
phase2_pressure_nonzero_sample_count = 2
pressure_aware_training_dataset_ready = false
skipped_counts =
  not_training_sample:paired_probe_neutral_proxy = 7
DATASET_EXIT = 1
```

解释：

1. 批量候选池比单点扩样更有效：当前 root-level 非零 pressure source 很少，已覆盖的就不应重复跑。
2. V796 证明 seed61311 root `[4,12]` 是高 pressure、target-stable、raw-row 可转换的 neutral proxy。
3. 它增加 raw coverage（`raw_row_count 8 -> 9`），但不增加 training sample，因为当前 dataset builder 仍跳过 `paired_probe_neutral_proxy`。
4. 这暴露了阶段 A 的一个新门槛：如果我们需要“neutral / misleading LP-gain”进入训练张量，必须明确训练契约；否则 neutral 只能作为 D gate/raw coverage，不计入 F gate sample。
5. 下一轮阶段 A 不应再盲目跑 root candidates；要么补更多未覆盖 root-level source logs，要么调整 dataset/training contract 对 high-pressure neutral rows 的处理。

新增产物：

```text
BPC_future/results/journey_branch_candidate_replay_runbook_v796_v781_seed61311_root_highpressure_wide/
BPC_future/results/journey_paired_probe_summary_v796_v781_seed61311_root_highpressure_wide/
BPC_future/results/journey_paired_probe_delta_rows_v796_v781_seed61311_root_highpressure_wide/
BPC_future/data/gat_branch_action_sanity/v796_pressure_coverage_with_root_highpressure_neutral/

BPC_future/logical_graph/run_reports/20260629_bpc_future_v796_v781_seed61311_root_highpressure_wide_runbook_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v796_v781_seed61311_root_highpressure_wide_paired_probe_summary_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v796_v781_seed61311_root_highpressure_wide_delta_rows_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v796_pressure_coverage_with_root_highpressure_neutral_gat_dataset_zh.md
```

### 2.2.16 06月29日 19:20 CST V797 pressure candidate pool 批量化

本轮阶段位置：

```text
大阶段 = 阶段 A，Branch-score pressure-aware data chain / pressure hard gate 扩样
阶段内步骤 = A-6，批量 source-log 扫描、coverage 去重、focused replay queue
阶段内剩余 = 需要新 source logs 或训练标签契约决策；不再继续手工 one-by-one 扩样
```

本轮动机：

- 前一轮 V796 已证明手工扩大单个 root candidates 的效率很低；
- 继续“一个一个扩、时不时不命中”会浪费 replay 预算；
- 因此本轮把 A 阶段扩样方式改成工具化 gate：先批量扫 source logs，再按已有 delta/runbook 去重，再只对未覆盖 pressure candidate 生成 focused runbook。

代码改动：

```text
新增:
  BPC_future/scripts/build_journey_pressure_candidate_pool.py
  BPC_future/tests/test_journey_pressure_candidate_pool.py

扩展:
  BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py
    --focus-candidate-input
  BPC_future/tests/test_journey_branch_candidate_replay_runbook.py
    test_focus_candidate_input_prioritizes_pressure_queue_pairs
```

新工具边界：

- 只读 solver JSONL logs；
- 输出 `candidate_pool.jsonl`、`replay_queue.jsonl`、`summary.json`、中文 report；
- 可读已有 `branch_counterfactual_delta_rows.jsonl` 和 `runbook.json` 做 coverage 去重；
- 可把 queue 直接传给 replay runbook builder 的 `--focus-candidate-input`；
- 不运行 BPC/pricing/RMP，不产生 official lower bound、certificate、fathom 或 prune。

Focused 测试：

```text
python -m py_compile \
  BPC_future/scripts/build_journey_pressure_candidate_pool.py \
  BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py

python -m unittest \
  BPC_future.tests.test_journey_pressure_candidate_pool \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook

结果:
  Ran 25 tests in 0.414s
  OK
```

真实 V797 batch 扫描：

```text
输入 source logs:
  find BPC_future/results -maxdepth 2 -type d -name logs | rg '/20260629_'
  LOG_DIR_COUNT = 32

coverage 输入:
  journey_paired_probe_delta_rows_v7*
  journey_branch_candidate_replay_runbook_v7*
  COVERED_INPUT_COUNT = 33

输出:
  BPC_future/results/journey_pressure_candidate_pool_v797_20260629_batch/
  BPC_future/logical_graph/run_reports/20260629_bpc_future_v797_pressure_candidate_pool_batch_zh.md

source_event_count = 147
candidate_row_count = 6
queue_row_count = 0
coverage_key_count = 73
coverage_status_counts =
  delta_observed: 5
  runbook_queued: 1
candidate_depth_counts =
  depth0: 3
  depth1: 2
  depth2: 1
low_pressure_skip_count = 4811
duplicate_candidate_count = 4
```

批量扫描出的 6 个 unique nonzero pressure candidates：

```text
1. seed61311 depth0 node0 sel [2,16] alt [4,12]
   severity_sum = 27.972509
   status = delta_observed

2. seed61635 depth0 node0 sel [3,4] alt [1,9]
   severity_sum = 14.881469
   status = delta_observed

3. seed61311 depth2 node6 sel [13,14] alt [3,13]
   severity_sum = 11.024517
   status = delta_observed

4. seed61744 depth1 node1 sel [2,11] alt [2,17]
   severity_sum = 10.54319
   status = runbook_queued

5. seed61311 depth1 node2 sel [5,13] alt [7,13]
   severity_sum = 3.797933704
   status = delta_observed

6. seed61744 depth0 node0 sel [3,6] alt [1,20]
   severity_sum = 0.700773
   status = delta_observed
```

Delta-only 对照扫描：

```text
coverage 输入只用 journey_paired_probe_delta_rows_v7*

输出:
  BPC_future/results/journey_pressure_candidate_pool_v797_20260629_delta_only/
  BPC_future/logical_graph/run_reports/20260629_bpc_future_v797_pressure_candidate_pool_delta_only_zh.md

candidate_row_count = 6
queue_row_count = 1
coverage_status_counts =
  delta_observed: 5
  uncovered: 1

唯一 uncovered:
  seed61744 depth1 node1 sel [2,11] alt [2,17]
  severity_sum = 10.54319
```

`[2,17]` 的 replay 状态复核：

```text
V788/V789:
  target_not_replayed
  reason = root_not_reached

V795:
  template = matched265 + widenodes
  wall = 265.017925
  status = EXTERNAL_TIME_LIMIT
  label = target_not_replayed
  reason = ancestor_forced_but_target_child_no_branch
```

因此本轮没有重跑 solver。原因不是缺少 queue，而是唯一未形成 delta 的 pressure candidate 已经被 widened-node / 265s 模板证明是 target reachability blocker；继续跑同一个 pair 只会重复无效样本。

Focused runbook 生成验证：

```text
输入:
  BPC_future/results/journey_pressure_candidate_pool_v797_20260629_delta_only/replay_queue.jsonl

输出:
  BPC_future/results/journey_branch_candidate_replay_runbook_v797_pressure_candidate_pool_focus_delta_only/
  BPC_future/logical_graph/run_reports/20260629_bpc_future_v797_pressure_candidate_pool_focus_runbook_zh.md

entry_count = 2
paired_baseline_entry_count = 1
paired_alternative_entry_count = 1
focus_candidate_context_count = 1
focus_candidate_pair_count = 1
focus_candidate_pair_available_count = 1
focus_candidate_pair_missing_count = 0
focus_candidate_entry_count = 1

entries:
  1 selected_baseline forced [2,11], source depth1 node1, time 265, nodes 1000
  2 alternative forced [2,17], source depth1 node1, reason focus_candidate_pool, time 265, nodes 1000
```

资源状态：

```text
disk /home/kai/work/gnn_bb:
  1007G total, 124G used, 833G available, 13% used

memory:
  15Gi total, 12-13Gi available

solver residue:
  no BPC_future / routeopt solver process left running
```

结论：

1. V797 把阶段 A 的扩样入口从手工 pair 扩成了批量候选池工具；
2. 当前 20260629 source logs 在 depth <= 2 的 nonzero pressure candidate 已基本耗尽；
3. 严格按 delta + runbook 去重时，`replay_queue` 为 0；
4. 只按 delta 去重时，唯一 uncovered 是 V787/V795 已知 target reachability blocker `[2,17]`；
5. 下一步不要继续对旧 20260629 logs 盲目 replay；要么采集新的 source logs，要么先修 child-source target replay template；
6. 训练仍不能启动：当前缺口不是 raw pressure 字段，而是可训练 positive/hard-negative pressure-aware sample 太少，且 high-pressure neutral 是否进训练仍未定。

### 2.2.17 06月29日 19:30 CST V798 V545 未闭环实例 V750-equivalent source gate

本轮阶段位置：

```text
大阶段 = 阶段 A，Branch-score pressure-aware data chain / pressure hard gate 扩样
阶段内步骤 = A-7，补新 source logs 并先跑 pressure candidate pool gate
阶段内剩余 = 若 V750-equivalent 仍无 branch candidates，应转向 source 模板/target replay 修复或 neutral 训练契约，而不是继续盲目加 replay
```

执行原因：

- V797 已证明旧 `20260629_*` logs 的 pressure candidates 基本耗尽；
- 文档中 V785/V786 说明 seed61308 / seed61744 在 V750-equivalent 180s 内 root-sticky；
- seed61308 历史 V545 old log first branch 约 243s，因此本轮把两个 V545 未闭环实例拉到 360s source-only；
- 这一步只采集 source logs，不做 replay，不训练。

V798 source 命令要点：

```text
instances:
  apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308
  tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744

time_limit = 360
max_workers = 2
template = routeopt_bkf_v762 + V750-equivalent switches

关键 switches:
  journey_branch_candidate_priority=routeopt_bkf_staged
  journey_branch_candidate_phased_testing_preset=routeopt_bkf_v762
  journey_branch_candidate_phased_testing_dynamic_k_enabled=True
  journey_branch_candidate_phased_testing_phase1_cut_snapshot_enabled=True
  journey_dynamic_subset_row_cuts_enabled=True
  journey_dynamic_subset_row_cut_gate_enabled=True
  journey_dynamic_subset_row_cut_gate_min_best_violation=0.25
  journey_dynamic_subset_row_cut_budget=600
  journey_dynamic_subset_row_max_depth=1
  journey_dynamic_subset_row_max_rounds=2
  journey_dynamic_subset_row_max_subset_size=6
  journey_dynamic_subset_row_max_added=20
```

V798 source 结果：

```text
output_dir = BPC_future/results/20260629_v798_v750_equiv_source_seed61308_seed61744_360/

seed61308 apollo15 greedy-anchor:
  status = TIME_LIMIT
  solving_time = 240.092742
  external wall = 260.544565
  primal = 513.366132
  node_count = 1
  branch_candidate_events = 0
  journey_branch_events = 0
  subset_row_cuts_added = 0

seed61744 tranquillitatis greedy-anchor:
  status = TIME_LIMIT
  solving_time = 136.029099
  external wall = 167.998963
  primal = 501.805380
  node_count = 1
  branch_candidate_events = 0
  journey_branch_events = 0
  subset_row_cuts_added = 1
```

V798 pressure candidate pool gate：

```text
output_dir = BPC_future/results/journey_pressure_candidate_pool_v798_v750_equiv_source_seed61308_seed61744_360/
report = BPC_future/logical_graph/run_reports/20260629_bpc_future_v798_v750_equiv_source_pressure_candidate_pool_zh.md

source_event_count = 0
candidate_row_count = 0
queue_row_count = 0
coverage_key_count = 73
candidate_pool.jsonl = 0 bytes
replay_queue.jsonl = 0 bytes
```

资源状态：

```text
run peak:
  2 solver child processes
  each about 5-7% mem
  system memory stayed above about 11-12Gi available

after run:
  no BPC_future / routeopt solver process left running
  disk available = about 833G
```

结论：

1. V798 证明“把 seed61308/seed61744 的 V750-equivalent source 从 180s 拉到 360s”仍不能产生 branch candidates；
2. seed61308 即使过了历史 first-branch 约 243s 的窗口，在当前 V750-equivalent routeopt_bkf_v762 模板下仍 `node_count=1`；
3. 这两个实例当前不能作为 pressure-aware paired replay 的 source；
4. 下一步不应继续简单加长同模板 source budget；应优先：
   - 修复/改进 child-source target replay template；
   - 或采集不同 family / different source template 的新 logs；
   - 或先明确 high-pressure neutral / misleading LP-gain 的训练契约。

### 2.3 Route-order branch / formulation 诊断

主要文件：

- `BPC_future/core/branching.py`
- `BPC_future/pricing/journey_pricing.py`
- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

已有能力：

- same-route order / not-same-route 三分支原型；
- partition coverage audit；
- child RMP diagnostic probe；
- child pricing diagnostic probe；
- route-order branch 只在 materialized profile pricing 下支持；
- direct pricing / completion-bound certificate 对 route-order branch 仍 fail-closed。

当前状态：

- route-order 是 promising formulation/branching 方向；
- 但仍是 audit/probe，不是默认 live branch；
- 不能直接用于 certificate 或 official fathom。

### 2.4 Weighted rank-1 / SRC cut 方向

主要文件：

- `BPC_future/core/cuts.py`
- `BPC_future/master/journey_rmp.py`
- `BPC_future/pricing/journey_pricing.py`
- `BPC_future/solver/journey_driver.py`

已有能力：

- `WeightedSubsetRowCut` contract；
- RMP coefficient 支持；
- manual reduced cost 支持；
- pricing reduced cost 支持；
- completion-bound / profile pruning 在 nonzero weighted cut dual 下 fail-closed；
- opt-in separator 存在，但默认关闭，`production_ready=False`。

V758/V759 观察：

- weighted rank-1 audit 对 seed61635 能发现 violated candidates；
- 但 audit-only 不改变 dual；
- 普通 dynamic SRC 即使 binding / 有 dual，也没推动 seed61635 best dual。

当前判断：

- 不能继续只扩大普通 SRC；
- 要转向 route/order/resource-aware cuts 或更强 master formulation。

## 3. 当前问题清单

### P0：20-scale 还没有达到全量 600s OPTIMAL

当前明确已验证的最好 full60 量级仍是 V545 的 `36/60 OPTIMAL`。后续 V750/V772/V773 更多是 hard-case 诊断和局部 smoke，不是 full60 验收。

### P1：branch score 覆盖不足

V545 有效，但 score-present branch decision 很少。继续盲目扩大 top pair 正例不够，必须 state-scoped 扩数据：

```text
instance family
branch_state_key
depth
parent constraints
support / fractional pattern
child width / retry risk
phase2 pricing pressure
cut context
route-order context
```

### P2：child LP gain 与真实闭环成本不一致

V772 已证明，child RMP gain 大的分支下面可能仍有强负列链。因此新 score/标签必须加入：

```text
min_child_gain
child_gain_product
child_gain_balance_ratio
phase2_negative_severity_sum
phase2_negative_severity_gap
phase2_negative_child_presence_balance_gap
child pricing status
best reduced cost
incomplete-limit count
```

### P3：best dual 不动时，branch score 不是根解

seed61635 的 `dual=526.651393` 多轮配置不动，说明它需要 stronger formulation/cuts。只靠更快选 branch 可能减少部分 proof-tail，但无法把所有 hard case 压到 600s 内。

### P4：retry 不能关，只能分类 gate

retry 同时承担：

- incomplete no-column 后补 hidden negative；
- completion-bound / final-judge certificate 补强。

不能把 uncertified no-column 升级为证书。优化方向是：

- 分开两类 retry；
- 对 expensive-no-harvest 降低重复；
- 对 harvest-returned-new-task-set 统计后续是否真的改善闭环。

### P5：admission 暂时不是主线

候选列 admission 曾经有局部加速，但当前主要瓶颈已经转向 branch proof tail / formulation lower bound。Admission 可以保留审计，不应与 branch/cut 主实验混在一起。

## 4. 意料之外或需要特别注意的发现

1. **V545 的 state-scoped overlay 有真实收益，但没有提升 <=200s 数量。**  
   它解决了少数覆盖状态，不是普遍加速器。

2. **route-order child RMP gain 很大，但 pricing pressure 更大。**  
   这说明 formulation/branching 方向是对的，但不能把 finite-pool gain 当最终 proof gain。

3. **普通 dynamic SRC 不够。**  
   seed61635 上普通 SRC 能加、能 binding、能有 cut dual，但 best dual 还是不动。

4. **cut snapshot 作为诊断成本低。**  
   V750 中 snapshot overhead 小，权重为 0 时没有破坏 seed61311 好路径，适合作为训练/诊断字段保留。

5. **RouteOpt/BKF preset 比裸 staged 更重要。**  
   不能把所有 phased knobs 一起放开；需要稳定 preset + dynamic-K + fail-closed。

## 5. 下一轮优化计划

### 阶段 A：完成 V774/V777 数据链硬 gate

目的：让 GAT branch action 数据集真正看到 V773 的 phase2 pricing pressure。

已完成代码和测试：

- `build_gat_branch_action_sanity_dataset.py` 新增 phase2 severity context feature；
- `audit_journey_branch_impact.py` schema bump 到 impact row v2 / training row v2 / audit v2；
- `build_journey_branch_candidate_replay_runbook.py` selected baseline 和 alternative 都透传 pressure 字段；
- `summarize_journey_paired_probe_runbook.py` 对旧 runbook 也从 `source_selected` fail-closed 补 selected baseline pressure；
- `build_journey_paired_probe_delta_rows.py`、forced/full/v437 delta builders 都保留 `baseline_raw_row` 和 `alternative_raw_row`；
- `test_gat_branch_action_sanity_dataset.py` 已验证 schema、样本张量值、manifest coverage counters 和 `missing_phase2_pressure_is_not_low_pressure`。

当前结果：

1. V777 已证明 A-F 链路可跑通；
2. V779 已证明 seed61311 在 120s reachability budget 下可以生成非零 pressure 的 paired neutral delta row；
3. V781/V782 已证明 seed61311 no-regression 必须用 V750-equivalent branch-cut 模板判断，v762 pressure-aware 在该模板下不破坏 110s OPTIMAL 好路径；
4. V783 已把 V750-equivalent node6 high-pressure baseline/alternative 穿透到 paired delta raw rows，但仍是 neutral proxy；
5. V784 已补完 seed61311 node6 剩余 alternatives，三条 alternatives 全是 neutral proxy，应停止把 seed61311 作为主要扩样对象；
6. `pressure_aware_training_dataset_ready=false` 是正确状态；
7. 当前可训练 tensor 仍只有 V777 的 1 个 sample，V779/V783/V784 neutral rows 只用于 hard gate/D gate 和 raw coverage，不足以训练；
8. V785/V786 说明 V750-equivalent source 在部分 V545 未闭环实例上 180s 内可能 root-sticky，无 candidate 可扩；
9. V787/V789 说明 diagnostic-only source 即使有 high-pressure context，也必须先通过 replay source-template / target-hit gate；target miss 的 row 不能进入 delta 或训练；
10. V790 已把 source-template 显式化为 `--replay-set`，并支持按 `source_event_time + margin` 自适应 child-probe time-limit；
11. V790 修掉了 V789 的 root 短预算 miss，但暴露了更细的 target path instability：ancestor root force 成功后，source 的 same child target node 未复现 branch；
12. V791 已补 target reachability reason gate，能区分 `root_not_reached` 和 `ancestor_forced_but_target_child_no_branch`；
13. V792 已把 nonconvertible reason 传到 paired delta summary，并固定处理策略：只统计、不训练、不当 branch quality label；
14. V793 已尝试 source-stable root context，但当前 replay 模板仍在 root branch candidate 前以 `source_node_not_replayed` fail-closed；这不是 branch-quality label，而是 replay budget / final-probe reproducibility blocker；
15. V794 已完成 matched-180 root reachability gate：root `[3,6]` 和 pressure alt `[1,20]` 都 `target_pair_selected`，并生成 1 条 `paired_probe_hard_negative_proxy`；
16. 当前 pressure-aware dataset 从 `sample_count=1` 增到 `sample_count=2`，非零 pressure sample 从 1 增到 2，但 `pressure_aware_training_dataset_ready=false` 仍正确；
17. V795 证明同一 V787 的 depth1 pressure candidates 即使用 widened-node / 265s matched template，仍是 `ancestor_forced_but_target_child_no_branch`，不能进入 delta/training；
18. V796 已把阶段 A 扩样方式改为批量 root-level pressure candidate pool；当前未覆盖 root pressure source 很少，seed61311 root `[4,12]` 已作为 high-pressure neutral proxy 进入 raw delta；
19. 当前 dataset `raw_row_count=9`、`sample_count=2`，说明 high-pressure neutral 只增加 raw coverage，不增加 training tensor；下一步要先明确 neutral/misleading LP-gain 是否应进入训练契约，或继续找 positive/hard-negative root-level source。
20. V797 已把批量 source-log pressure candidate pool 固化为脚本，并让 replay runbook 支持 `--focus-candidate-input`，后续不再靠手工扩大 `alt-pairs-per-event` 碰运气；
21. V797 对 32 个 `20260629_*` source log 扫描出 depth <= 2 unique nonzero pressure candidate 只有 6 个；其中 5 个已有 delta，1 个只是 runbook queued；
22. 严格按 delta + runbook 去重时 `queue_row_count=0`；只按 delta 去重时唯一 queue 是 seed61744 depth1 `[2,17]`，但 V795 已证明它是 `ancestor_forced_but_target_child_no_branch` reachability blocker，不应重复 replay。
23. V798 对 seed61308 / seed61744 两个 V545 未闭环实例补了 360s V750-equivalent source logs，但两者仍 `node_count=1`、`branch_candidate_events=0`；
24. V798 pressure candidate pool gate `source_event_count=0`、`candidate_row_count=0`、`queue_row_count=0`，说明这两个实例当前不能直接供 pressure-aware paired replay 扩样；
25. 下一步不应继续简单加长同模板 V750-equivalent source budget；要么换 source template/family，要么先修 child-source target replay template，要么明确 high-pressure neutral training contract。

### 阶段 B：把 routeopt_bkf_staged 从日志/诊断推向可控 opt-in

目标：不是 top200 硬扫，而是 solver 内正式 phased controller。

执行顺序：

1. Cheap screen：
   - fractionality；
   - child width；
   - balance gap；
   - state score coverage；
   - retry risk；
   - route-order/cut context。
2. Phase1 LP probe：
   - min child gain；
   - gain product；
   - balance ratio。
3. Phase2 short heuristic pricing probe：
   - child best RC；
   - negative severity sum/gap；
   - incomplete-limit risk。
4. 只对 dynamic-K 个候选做 expensive replay/exact paired probe。

验收：

- 日志必须记录每阶段通过/淘汰原因；
- full60 之前先 hard-case smoke；
- 不允许因 score 缺失而强行 early branch。

### 阶段 C：state-scoped branch action 训练

训练标签不要只看 wall time。建议标签/辅助头：

```text
capped_wall_time_gain
gap_improvement
fathom_gain
min_child_lb_gain
child_gain_product
child_width_balance
phase2_negative_severity_sum/gap
completion_bound_retry_delta
time_to_certificate
hard_negative: gain <= -30s 或 OPTIMAL -> timeout 或 phase2 pressure 明显升高
```

训练前最低数据门槛：

- 20-scale 至少覆盖 10 个实例；
- 至少 20 个跨 context positive wall-time/proof gain；
- hard negative 数量不低于 positive；
- 同实例不跨 train/validation 泄漏。

如果 strict full replay 正例不足，可以先用 child-probe/proof-cost 辅助训练，但导出的 score map 必须标记 `production_ready=false`。

### 阶段 D：pricing-compatible cuts / formulation 主线

这是当前最关键的并行方向。

优先级：

1. **route/order/resource-aware cut diagnostic**  
   从 seed61635 的 high-pressure states 开始，不再盲目扩大普通 SRC。

2. **weighted rank-1 opt-in live 最小闭环**  
   只选择 reduced-cost 已支持、completion-bound fail-closed 的安全候选。先做 1-2 个 hard seed smoke，不直接 full60。

3. **route-order partition formulation**  
   继续验证三分支 coverage 和 child pricing pressure。如果能找到 pricing pressure 同时下降的 region，再考虑 live branching / score feature 正权重。

4. **official cut 条件**  
   每类 cut 必须满足：
   - RMP coefficient 正确；
   - manual reduced cost 一致；
   - pricing reduced cost 一致；
   - completion-bound 在不支持时 fail-closed；
   - integer feasibility validity 有单元测试；
   - no-negative certificate 不被 unsupported cut 污染。

### 阶段 E：retry gate 分类实验

不要直接关 retry。做三组对比：

```text
retry on
retry off
retry gate
```

但要分两类统计：

- incomplete no-column 补救 retry；
- completion-bound / final-judge retry。

指标：

- `would_skip`；
- `actually_skipped`；
- `negative_later_found`；
- `certificate_later_needed`；
- `status_regression`；
- retry trigger count；
- retry harvest new task set；
- retry no-harvest CPU；
- child certificate time；
- best dual / gap movement；
- timeout -> optimal；
- optimal -> timeout；
- exact certificate 是否保持。

### 阶段 F：全量验收顺序

1. hard seed smoke：
   - seed61311：不能回归；
   - seed61635：优先观察 dual/gap 是否移动；
   - 另选 2-4 个 V545 未闭环实例。
2. 12-instance smoke：
   - 5/10/20 各固定 12 个；
   - 对比 current best vs 新 opt-in。
3. full60：
   - 5/10 必须 60/60 OPTIMAL 且 capped mean 不明显退化；
   - 20 先看 OPTIMAL 数、capped mean、gap 分布；
   - 最终才看 60/60 600s OPTIMAL。

## 6. 新对话优先执行入口

建议新对话先做下面三件事。

### 6.1 确认当前测试状态

```bash
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset
```

### 6.2 继续 V777 pressure hard gate 扩样

目标不是马上训练，而是把当前 A-F 链从 1 个 seed61635 coverage sample 扩到最低可训练前置覆盖。必须同时检查：

```text
phase2_same_child_negative_severity
phase2_separate_child_negative_severity
phase2_negative_severity_sum
phase2_negative_severity_gap
phase2_negative_severity_balance_ratio
phase2_negative_child_presence_balance_gap
baseline_raw_row
alternative_raw_row
phase2_pressure_observed_counts
phase2_pressure_nonzero_counts
missing_phase2_pressure_is_not_low_pressure
```

硬 gate 要按 A-F 检，不允许用 row_count 代替字段闭环：

```text
Gate A: solver JSONL event 中字段存在；
Gate B: audit row 中同名字段存在，且 schema version bump；
Gate C: replay runbook entry 中同名字段存在；
Gate D: forced replay / paired replay delta row 的 baseline_raw_row 和 alternative_raw_row 均保留字段；
Gate E: GAT dataset manifest 的 context_feature_schema 中出现字段；
Gate F: tensor 中字段非全 0 / 非全 missing，hard-case probe 至少有真实非零覆盖。
```

缺失字段必须 fail-closed：

```text
missing pressure != low pressure
missing replay != neutral label
pressure-aware score 只能在 pressure 字段真实观测时启用；
字段缺失时只能 fallback 到旧 score / baseline ranking，不能把 missing 填 0 后参与 pressure-aware 排序。
```

下一步实例顺序：

```text
Step 0: 修 replay source-template / target-hit gate
  V789 已证明 diagnostic-only source 有 pressure 也可能 replay target miss；
  V790 已补 runbook 显式 source-template 参数：
    --replay-set
    --probe-time-margin-after-source-event
  但 V790 仍证明 target node/path 不稳定：
    root ancestor force 成功；
    source same-child target node 没有复现 branch；
    paired summary 仍 target_hit_count=0。
  V791 已补 reachability reason：
    V789 = root_not_reached；
    V790 = ancestor_forced_but_target_child_no_branch。
  V792 已把 reason 传到 delta summary，并固定处理策略：
    只做 reachability diagnostics；
    不进入 delta/training；
    不当 neutral/hard-negative/branch-quality label。
  V793 已转向 source-stable root context，但当前 replay 在 branch candidates 前
  因 completion/final pricing time_limit 变成 source_node_not_replayed；
  V794 matched-180 已通过 root reachability：
    root [3,6] / pressure alt [1,20] 均 target_pair_selected；
    产出 1 条 paired_probe_hard_negative_proxy；
    sample_count = 2，pressure_aware_training_dataset_ready = false。
  V795 depth1 widened-node replay 仍失败：
    [2,11] / [2,17] 均 ancestor_forced_but_target_child_no_branch；
    output_row_count = 0；
    dataset raw/sample 维持 8/2。
  V796 批量 root-level pressure pool 已覆盖 seed61311 [4,12]：
    target_pair_selected = 2；
    output_row_count = 1，label = paired_probe_neutral_proxy；
    raw_row_count = 9，sample_count = 2；
    neutral raw row 不进入当前 training tensor。
  后续 replay 仍必须满足 paired summary target_hit_count > 0 才能进 delta。

Step 1: seed61635 pressure-coverage
  已有 1 sample，但还要补更多 candidate/child-probe；
  同时保持 cuts/formulation 主线独立，不和 score 训练混合归因。

Step 2: 2-4 个 V545 未闭环 20-scale 实例
  优先用 build_journey_pressure_candidate_pool.py 批量扫描 source-stable pressure candidates；
  必须先检查 candidate_pool / replay_queue / coverage_status，再小批次 replay；
  严格去重时如果 queue_row_count = 0，不得继续手工 one-by-one 扩旧 logs；
  V750-equivalent source 先看是否能在 budget 内产生 branch candidates；
  若只能用 v762-only source，必须标记 diagnostic-only，且 replay 成功后才可进 dataset；
  每个实例至少检查 root/child target_hit、alternative_raw_row pressure 字段、hard-negative/neutral/positive label 分布；
  不要继续在 V787 depth1 上加 alternatives，除非先改进 child-source replay template；
  V797 已证明旧 20260629 logs 的唯一 delta-uncovered pressure candidate [2,17] 是 reachability blocker；
  V798 已证明 seed61308 / seed61744 的 V750-equivalent source 拉到 360s 仍无 branch candidates，
  因此不要继续简单加长同模板 source budget。

Step 2b: high-pressure neutral training contract
  V796 暴露出高 pressure neutral row 只进 raw、不进 sample；
  若阶段 A 需要 neutral / misleading LP-gain 参与训练，必须先修改 dataset label contract 和测试；
  否则继续把 neutral 仅作为 D gate/raw coverage，不把 sample_count 当作已经覆盖 neutral。

Step 3: seed61311
  只作为 no-regression / schema gate / V750-equivalent 模板检查；
  不再作为主要扩样对象。
```

如果大部分为 0 或缺失，先补 hard-case replay/probe 数据；如果 `pressure_aware_training_dataset_ready=false`，不得启动训练。

### 6.3 继续攻 formulation/cuts

首选 seed61635，因为它多轮结果证明：

```text
primal ≈ 560.618366
dual ≈ 526.651393
gap ≈ 0.060588
```

下一步不要再只调 pair 权重，而是：

- 找 high route-order conflict / high phase2 pressure 状态；
- 尝试 route/order/resource-aware cut；
- 验证 cut 是否能实际移动 best dual；
- 如果不能移动 dual，就不要进入 full60。

### 6.3.1 06月29日19:46 阶段 C / C-1 seed61635 formulation-cut readiness gate

本轮正式从阶段 A（branch-score / replay 扩样）切到阶段 C（Formulation/Cuts 下界主线），当前完成的是 C-1：把 seed61635 现有 cut/formulation 证据整理成机器可复核的 live-readiness gate，而不是继续 one-by-one 扩 replay。

新增只读审计：

```text
BPC_future/scripts/summarize_seed61635_formulation_cut_readiness.py
BPC_future/results/20260629_v799_seed61635_formulation_cut_readiness/summary.json
BPC_future/results/20260629_v799_seed61635_formulation_cut_readiness/readiness_rows.jsonl
BPC_future/logical_graph/run_reports/20260629_bpc_future_v799_seed61635_formulation_cut_readiness_zh.md
```

V799 汇总结论：

```text
observed_signal_family_count = 3
live_ready_family_count = 0
dual_plateau_holds_for_inputs = true
decision = do_not_enter_live_cut; pursue state-scoped formulation/pricing-compatible row design
```

三条 family 的当前状态：

- `weighted_rank1_task_subset`：有 separation/add/nonzero dual，`max_best_violation = 0.25`、`max_weighted_abs_dual = 3.130013`，但 V760 live opt-in 后 `dual = 526.651393` 仍未移动；不要继续盲目扩大 task-subset weighted rows。
- `route_resource_cut_audit`：route/order conflict 有信号，`max_order_direction_candidate_count = 1`、`max_adjacent_direction_candidate_count = 1`，但 `max_global_valid_candidate_count = 0`、`max_pricing_supported_candidate_count = 0`；不能把 order conflict 直接当全局 cut。
- `route_order_partition_formulation`：partition contract 在 11 条 row 上成立，finite-pool child RMP gain 最大 `48.259783375`，但 `child_pricing_found_negative_row_count = 33/33`、`min_child_pricing_best_reduced_cost = -67.736614`，且 direct certificate 仍不支持 route-order；说明 formulation 方向有信号，但不能直接 live branch / live cut。

进入 live cut 或正式 formulation 前必须同时过以下硬 gate：

```text
global_valid_or_state_scoped_partition_proven
rmp_coefficient_and_manual_reduced_cost_match
pricing_reduced_cost_matches_rmp_coefficient
completion_bound_and_certificate_paths_fail_closed_or_supported
seed61635_probe_moves_dual_or_reduces_child_pricing_pressure
```

验证：

```text
python -m py_compile BPC_future/scripts/summarize_seed61635_formulation_cut_readiness.py BPC_future/tests/test_seed61635_formulation_cut_readiness.py
python -m unittest BPC_future.tests.test_seed61635_formulation_cut_readiness
python BPC_future/scripts/summarize_seed61635_formulation_cut_readiness.py
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_resource_cut_audit_classifies_order_rows_as_not_live_cuts \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_reports_child_width_and_coverage \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_child_rmp_probe_is_diagnostic \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_weighted_subset_row_live_pricing_is_rc_consistent_and_fail_closed_for_bounds \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_route_order_branch_direct_pricing_remains_fail_closed
```

以上均通过。资源检查：磁盘 `/dev/sdd` 约 `13%` 使用，内存约 `12Gi` available。

阶段 C 下一步应进入 C-2：不要启动新的 branch-score/replay 扩样；先设计最小的 state-scoped order/resource formulation 或真正 pricing-compatible route-resource row contract。C-2 的第一步不是开 live cut，而是写出 row/branch 的 RMP coefficient、manual RC、pricing RC、completion-bound fail-closed 和 integer validity 测试清单；清单不齐不得跑 seed61635 live smoke。

### 6.3.2 06月29日19:51 阶段 C / C-2 formulation contract gate

本轮继续 C-2，没有跑新的 replay，也没有改 live solver。目标是把 V799 readiness 结果转成下一步 formulation/cut contract gate，避免把 route-order branch、route-resource cut、weighted rows 混在一起推进。

新增只读 contract gate：

```text
BPC_future/scripts/build_seed61635_formulation_contract_gate.py
BPC_future/results/20260629_v800_seed61635_formulation_contract_gate/summary.json
BPC_future/results/20260629_v800_seed61635_formulation_contract_gate/contract_gate_rows.jsonl
BPC_future/logical_graph/run_reports/20260629_bpc_future_v800_seed61635_formulation_contract_gate_zh.md
```

V800 汇总结论：

```text
candidate_count = 3
live_ready_candidate_count = 0
selected_next_candidate = state_scoped_route_order_partition_branch
decision = continue_C2_design_only; no_live_cut_or_live_branch
```

候选 gate：

- `state_scoped_route_order_partition_branch`：选为 C-3 设计入口，但仍非 live。已通过 `observed_seed61635_signal`、`state_scoped_partition_contract`，并有 finite-pool RMP lift；但 `child_pricing_pressure_cleared = fail`，`direct_certificate_support = fail_closed`，`completion_bound_certificate_path = fail_closed`，`task_set_dominance_safety = fail_closed`。
- `pricing_compatible_route_resource_row`：不选为下一步实现。当前 `global_valid_row_family = fail`，`rmp_coefficient_defined = fail`，`manual_reduced_cost_coefficient_defined = fail`，`pricing_reduced_cost_coefficient_defined = fail`，`integer_validity_test_defined = fail`；在没有明确 globally valid 或 state-scoped row family 前不得做 live row。
- `weighted_rank1_task_subset_row`：不作为 C-2 主线。coefficient/pricing 底座已有，但 `seed61635_dual_moved = fail`，继续扩大这一族不是当前高 ROI 方向。

C-3 入口因此固定为：

```text
C-3.1 只写 opt-in state-scoped route-order partition branch controller contract tests；
C-3.2 明确它只允许 diagnostic/opt-in，不允许 direct certificate/no-negative fathom；
C-3.3 禁用 task-set dominance 或任何只看 mask 的 certificate 路径；
C-3.4 只有 child pricing pressure 明显下降，才允许 seed61635 live-smoke；
C-3.5 live-smoke 仍不得把 route-order child RMP gain 当 official lower bound。
```

验证：

```text
python -m py_compile BPC_future/scripts/build_seed61635_formulation_contract_gate.py BPC_future/tests/test_seed61635_formulation_contract_gate.py
python -m unittest BPC_future.tests.test_seed61635_formulation_contract_gate
python BPC_future/scripts/build_seed61635_formulation_contract_gate.py
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_reports_child_width_and_coverage \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_child_rmp_probe_is_diagnostic \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_profile_pricing_supports_route_order_after_materialization \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_route_order_branch_direct_pricing_remains_fail_closed \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_resource_cut_audit_classifies_order_rows_as_not_live_cuts
```

以上均通过。资源检查：磁盘 `/dev/sdd` 约 `13%` 使用，内存约 `12Gi` available。

## 7. 当前不要做的事

- 不要把 `z_RMP` 当 exact node bound 用于 early branch 剪枝。
- 不要因为 child RMP gain 大就直接认为 branch 好。
- 不要把 route-order branch 用进 direct no-negative certificate。
- 不要把 weighted rank-1 cut 默认打开进 full60。
- 不要只按 200s 二值阈值定义正例；500s -> 300s 的真实 OPTIMAL 加速也应是正向训练信号。
- 不要把 admission scheduler 和 branch/cut 主实验混在一起，除非是单独消融。

## 8. 当前工作区提示

当前工作树包含一批连续版本的修改和报告，主要集中在：

```text
BPC_future/core/branching.py
BPC_future/pricing/journey_pricing.py
BPC_future/solver/journey_driver.py
BPC_future/scripts/build_gat_branch_action_sanity_dataset.py
BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py
BPC_future/tests/test_bpc_future.py
BPC_future/tests/test_gat_branch_action_sanity_dataset.py
BPC_future/tests/test_journey_branch_candidate_replay_runbook.py
```

以及 V761-V774 附近的 run reports。不要随手 revert；这些是当前主线连续证据链。
