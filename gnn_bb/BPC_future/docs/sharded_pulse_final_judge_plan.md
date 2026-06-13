# Sharded Pulse Final Judge 计划

日期：2026-06-11

## 目标

`Sharded Pulse Final Judge` 的目标是把原本单体、不可中断的 true-dual final judge 重构为：

- first-task shard；
- 可中断、可诊断；
- 只在完整 proof-search 穷尽时给出 `CERTIFIED_NO_NEGATIVE`；
- `INCOMPLETE` / `DUPLICATE_ONLY` / `FOUND_NEGATIVE` 永远不产生 official lower bound；
- 默认关闭，通过 opt-in config 启用。

当前实现重点是证书状态机、Phase 3A leaf materialization contract、Phase 3B toy exhaustive Pulse、Phase 3C cheap exact-safe pruning、Phase 4 structural archive / harvesting、Phase 5 guarded first-task sharded engine。
Phase 7A 新增 test-only transition-level root-only Pulse core，用于替代“完成 trace 枚举后再验证”的方向性验证。
Phase 7B 已把该 transition core 接到 guarded sharded final judge 的 opt-in path，但仍不接默认 production benchmark。
Phase 7C 已把 `StructuralKeyDominanceArchive` 接入 transition state。
Phase 7D 已把 transition-state true-RC negative leaves 接入 support-aware harvest-after-negative path。
Phase 7E 已加入 safe prefix reduced-cost lower-bound ledger 和 opt-in 弱安全 bound pruning。
Phase 7F 已加入 bound/archive/harvest ROI diagnostics，并完成 very_small / 5-task / 10-task opt-in micro-smoke。
Phase 7G 已补 no-wait start interval 与 `candidate_start_times_for_trip()` 时间域对齐。
Phase 7H 已加入 audit-only small-instance legacy-equivalence smoke 链路并完成真实小矩阵 smoke：Pulse 只写审计日志，不影响 official lower bound / pricing_state。
Phase 7I-A 已加入 opt-in Sharded Pulse hidden-negative worker：Pulse 可在 legacy final judge 前主动找 true-RC 负列，但不得产生 official certificate。

## Exactness 边界

证书成立条件：

1. 当前 true dual / cuts / branch / forbidden signatures / config 下所有 required shards 完整穷尽；
2. 每个 certified shard 必须 `proof_closed=True` 或等价完整 proof-search；
3. `JourneyPricingResult.reason == "sharded_pulse_no_negative_journey"`；
4. `final_judge_engine == "sharded_pulse"` 或 test-only `sharded_pulse_dummy`；
5. `global_certificate_capable=True` 且 `final_judge_certificate_capable=True`；
6. `status == "OPTIMAL"` 且无返回负列。

非证书状态：

- `FOUND_NEGATIVE`：只表示发现 true-RC negative column；
- `DUPLICATE_ONLY`：只表示没有新可返回列，不表示无负列；
- `INCOMPLETE` / timeout / recursion limit / unsupported branch：不得更新 official lower bound；
- harvest-after-negative：已退出 proof mode，不得 certificate；
- dummy all-certified：仅 test-only，必须配置 guard、instance guard 和环境变量 guard 同时满足。

## 当前模块

- `BPC_future/pricing/sharded_pulse_final_judge.py`
  - `ShardProofStatus`
  - `ShardProofRecord`
  - `ShardLedger`
  - `ShardCacheKey`
  - dummy shard ledger

- `BPC_future/pricing/pulse_materialization.py`
  - `PulseSortieTrace`
  - `PulseLeafCandidate`
  - `materialize_pulse_sortie()`
  - `materialize_pulse_journey()`
  - `materialize_pulse_leaf_candidate()`
  - `materialize_negative_pulse_leaf()`

- `BPC_future/pricing/pulse_toy_exhaustive.py`
  - root-only toy exhaustive Pulse
  - guarded sharded engine 使用的 transition-level root-only Pulse
  - first-task shard
  - optional second-action child shard
  - exact-safe resource/time/return pruning
  - optional archive
  - optional harvest-after-negative
  - optional prefix RC lower-bound pruning

- `BPC_future/pricing/pulse_archive.py`
  - `PulseStructuralKey`
  - `PulseArchiveRecord`
  - `StructuralKeyDominanceArchive`

## Phase 状态

### Phase 1-2.5

已完成：

- ledger skeleton；
- cache key builder；
- dummy shard engine；
- driver smoke；
- certificate reason guard；
- dummy test-only guard。

### Phase 3A

已完成：

- Pulse leaf 不手搓 `JourneyColumn`；
- sortie 通过 `evaluate_timed_trip()` 回放；
- journey 通过 `make_journey()`；
- true RC 通过 `manual_journey_reduced_cost()`；
- arc option 数量不匹配是内部 trace 错误，测试中抛 `ValueError`。

### Phase 3B

已完成：

- root-only toy exhaustive Pulse；
- 与独立 brute-force enumerator 对齐；
- first-task shard partition；
- no-wait toy case；
- deadline / max_recursions fail-open。

### Phase 3C

已完成的 cheap exact-safe pruning：

- resource / capacity；
- time-window transition；
- return feasibility；
- bound pruning 目前 fail-open。

未实现：

- 完整 prefix reduced-cost lower-bound pruning；
- cut/fleet/branch row contribution 的通用安全下界。

### Phase 4

已完成：

- structural-key dominance archive；
- archive cap fail-open；
- waiting/no-wait dominance 边界；
- support-aware harvesting 接入；
- harvest-after-negative 退出 proof mode。

### Phase 5

已完成：

- first-task sharded production entry；
- opt-in driver path；
- true negative 返回 `FOUND_NEGATIVE`；
- all-certified toy/very_small guard 下返回 `CERTIFIED_NO_NEGATIVE`；
- same/separate branch 通过 leaf feasibility 过滤；
- unsupported branch 不证书；
- dummy 不进入 production path。

当前限制：

- production certificate guard 只允许 `very_small` / `test*`；
- 真实 5/10/20 大实例默认不会由 toy Pulse 证书化；
- Phase 5 仍是 root-only toy Pulse，不是完整连续时间 Pulse proof engine。

### Phase 6

已完成：

- cache key 包含 true dual / cut / branch / forbidden / config / schema / proof version；
- frontier snapshot 非 proof 的 ledger 语义；
- second-action child shard toy partition；
- parallel/resume config skeleton 默认关闭。

未实现：

- 持久化 frontier resume；
- proof-closed prefix cache；
- adaptive hierarchical refinement；
- parallel worker merge。

### Phase 7A

已完成：

- 新增 `transition_root_only_pulse()`；
- 搜索过程中维护 open-sortie state：
  - `phase`
  - `last_node`
  - `visited_task_mask`
  - `current_sortie_task_mask`
  - `sorties_used`
  - `current_time`
  - `travel_energy / service_energy / load_used`
  - `partial_exact_prefix_rc / partial_lb_prefix_rc`
  - `pending_same_mask`
  - `partial trace`
- 扩展 task transition 前检查：
  - no-wait ready time；
  - due time；
  - capacity；
  - partial energy；
  - optimistic safe return lower bound；
  - Ryan-Foster `same_vehicle` / `separate_vehicle` obligations；
- return action 仍通过 Phase 3A materialization helper 回放 `evaluate_timed_trip()`；
- completed journey 仍通过 `materialize_pulse_leaf_candidate()` 调 `make_journey()` 和 `manual_journey_reduced_cost()`；
- 与旧 completed-trace toy exhaustive engine 在 `very_small` focused tests 上对齐；
- 直接对齐 brute-force best true RC / found-negative / no-negative exhaustive；
- no-wait infeasible case 中 transition-level core 在生成完整 trace 前剪掉不可行扩展，`generated_sortie_traces` 明显下降。
- time-window / energy / return pruning 均有 `>0` toy focused tests。

未实现：

- production driver 默认接入；
- resume；
- parallel；
- adaptive hierarchical sharding；
- dominance archive / support-aware harvesting 之外的完整 production Pulse features。

### Phase 7B

已完成：

- guarded sharded final judge 的 first-task shards 改为调用 `transition_root_only_pulse()`；
- 旧 completed-trace toy engine 保留为测试/对照工具，不再作为 guarded sharded shard executor；
- `very_small` all-certified 仍可在显式 toy certificate guard 下返回 `sharded_pulse_no_negative_journey`；
- negative shard 返回 `FOUND_NEGATIVE`，不证书；
- incomplete shard 返回 `INCOMPLETE_LIMIT`，不证书；
- non-test instance 即使开启 toy certificate config，也不能被 test-only toy certificate 闭合；
- driver JSONL `journey_pricing` 日志增加并可观测：
  - `transition_time_window_pruned`
  - `transition_energy_pruned`
  - `transition_return_pruned`
  - `pulse_capacity_pruned`
  - `pulse_energy_pruned`

仍未实现：

- 默认 production benchmark 启用；
- resume；
- parallel；
- adaptive refinement；
- transition-state dominance archive；
- transition-state harvesting。

### Phase 7C

已完成：

- `transition_root_only_pulse()` 支持 opt-in `StructuralKeyDominanceArchive`；
- archive 只在单次 DFS 调用内剪枝，不写入 proof-closed ledger，不参与 resume；
- waiting-allowed 下使用同 structural key 且不差的 partial RC / energy / load / current_time 支配；
- no-wait 下 structural key 包含 exact current time，record 使用 singleton interval，避免“更早时间”自动支配；
- archive cap 继续 fail-open：表满只丢旧 record，不丢当前 state；
- guarded sharded path 透传 `pulse_archive_dominance_enabled` 与 cap；
- guarded path 在存在 forbidden signatures 时禁用 archive，避免 duplicate-only/forbidden signature 语义被 dominance 隐藏；
- `pulse_archive_pruned` 在 `JourneyPricingResult` 与 driver JSONL 中可观测。

验证：

- archive-enabled transition Pulse 与 archive-disabled 在 toy 上 best true RC / found-negative / no-negative exhaustive 一致；
- `pulse_archive_pruned > 0` 的 toy / guarded opt-in case；
- no-wait archive 不误剪；
- archive cap fail-open；
- driver JSONL 中 archive counter 可观测。

仍未实现：

- resume；
- parallel；
- adaptive refinement；
- transition-state harvesting。

### Phase 7D

已完成：

- `transition_root_only_pulse()` 支持 opt-in harvest-after-negative；
- 发现 true-RC negative 后，若启用 harvest mode，返回强制退出 proof mode：
  - `exhausted=False`
  - `status="FOUND_NEGATIVE_HARVESTED"` 或 `FOUND_NEGATIVE`
  - `reason="harvest_after_negative"`
  - `global_certificate_capable=False` 由 guarded result path 保持
- harvest 只影响返回列，不参与 shard proof closure；
- 复用现有 `harvest_support_aware_negative_journeys()`；
- 所有 harvested journeys 继续由 `manual_journey_reduced_cost()` 过滤为 true-RC negative；
- forbidden signatures 保守处理：forbidden negative 仍可形成 `DUPLICATE_ONLY`，但不会进入 harvested returned columns；
- archive + harvest 在 toy 上与 archive-disabled path 保持 best true RC / found-negative 语义一致；
- guarded sharded path 透传 support-aware harvest config；
- `JourneyPricingResult` 与 driver JSONL 增加：
  - `pulse_negative_pool_size`
  - `pulse_harvested_count`
  - `pulse_harvested_new_task_set_count`
  - `pulse_harvested_support_changing_count`
  - `pulse_harvested_replacement_count`
  - `pulse_best_true_rc`

验证：

- found-negative 后退出 proof mode；
- harvested columns 全部 true-RC negative；
- empty harvest 不证书；
- duplicate-only 仍不证书；
- archive + harvest consistency；
- guarded path 与 driver JSONL harvest counters 可观测。

仍未实现：

- resume；
- parallel；
- adaptive refinement；
- prefix RC lower-bound pruning；
- production benchmark 默认启用。

### Phase 7E

已完成：

- 新增 `PrefixReducedCostLedger`；
- 明确 `C_exact_prefix` / `C_lb_prefix`：
  - `C_exact_prefix` 只包含已经由 trace 固定的 fixed/fleet、已走 arc cost、service cost、cover dual；
  - `C_lb_prefix` 是用于 pruning 的安全 prefix lower-bound，Phase 7E 中保持与 exact prefix 一致；
- ledger 对重复 cover dual 和 fixed/fleet 双算 fail-fast；
- transition state 的 prefix RC 更新改为通过 ledger helper；
- `cuts != ()` 时 bound pruning fail-open；
- 若 arc/service cost 存在负成本，bound pruning fail-open；
- 新增弱安全 LB：
  - open sortie：`min_return_cost_lower_bound - remaining_positive_cover_reward_bound`
  - depot-ready after at least one sortie：`min_outbound_cost + min_return_cost - remaining_positive_cover_reward_bound`
  - root depot 不直接 bound-prune，避免测试/诊断路径被剪空；
- bound pruning 只在 `bound_pruning_enabled=True` / guarded config `pulse_bound_pruning_enabled=True` 时启用；
- open state 先物化可返回 leaf，再用 bound pruning 剪更深 extension，避免丢失当前可观测 leaf；
- guarded sharded path 透传 `pulse_bound_pruning_enabled` 并聚合 `pulse_bound_pruned`。

验证：

- prefix ledger 与 `manual_journey_reduced_cost()` 在 no-cut multi-sortie leaf 上一致；
- fixed/fleet 不双算；
- cover dual 不重复领取；
- cut dual 未安全处理时 fail-open；
- bound-pruned transition Pulse 与 unpruned 在 best true RC / found-negative / negative signatures 上一致；
- 至少一个 toy case `pulse_bound_pruned > 0`；
- guarded path 中 `pulse_bound_pruned` 可观测。

仍未实现：

- cut / subset-row / fleet-cut 的通用 prefix RC lower bound；
- resume；
- parallel；
- adaptive refinement；
- production benchmark 默认启用。

### Phase 7F

已完成：

- `JourneyPricingResult` 与 driver JSONL 增加 bound ROI diagnostics：
  - `pulse_bound_prune_enabled`
  - `pulse_bound_prune_supported`
  - `pulse_bound_prune_fail_open_reason`
  - `pulse_bound_prune_query_count`
  - `pulse_bound_prune_winner_count`
  - `pulse_bound_prune_time`
- fail-open reason 可观测：
  - `disabled`
  - `cuts_present`
  - `negative_arc_cost`
  - `negative_service_cost`
  - `missing_return_lb`
  - `missing_outbound_lb`
- `pulse_bound_pruned` 继续作为 winner counter，`pulse_bound_prune_winner_count` 与其保持一致；
- guarded sharded path 聚合所有 shard 的 bound query / winner / time diagnostics；
- toy regression 覆盖 archive off/on 与 bound off/on 组合：
  - best true RC 一致；
  - found-negative 一致；
  - negative signatures 一致；
- driver smoke 覆盖 JSONL 中 bound diagnostics 字段可观测；
- 完成 opt-in micro-smoke：
  - `very_small`
  - Apollo 5
  - Tranquillitatis 5
  - Apollo 10
  - 配置矩阵 A/B/C/D/E：default baseline、sharded transition、archive、bound、harvest。

micro-smoke 观察：

- bound on 在该批无 cut / 非负成本小实例中均 supported；
- `pulse_bound_pruned` 对 very_small / Apollo 5 / Tranquillitatis 5 / Apollo 10 均为正；
- bound on 明显减少 recursions / expanded states / materialized journeys；
- archive on 单独有正向但较弱的剪枝信号；
- harvest 在无负列 dual 场景中没有新增返回列，这是符合预期的；
- 非 test instance 仍由 toy certificate guard 返回 `INCOMPLETE_LIMIT`，不会形成 production certificate。

仍未实现：

- cut / subset-row / fleet-cut prefix lower bound；
- resume；
- parallel；
- adaptive hierarchical sharding；
- production benchmark 默认启用。

### Phase 7G

已完成：

- no-wait transition state 新增 start interval 与 offset：
  - `start_interval_lb`
  - `start_interval_ub`
  - `current_offset`
- no-wait 扩展 task 时用 arrival offset 更新 start interval：
  - `s >= r_i - arrival_offset_i`
  - `s <= D_i - sigma_i - arrival_offset_i`
  - interval 为空时直接 time-window prune；
- return action 使用 offset 计算 survival energy 与 horizon end-offset feasibility；
- completed sortie 不再只使用 fixed `root_start_time`：
  - 调用 `candidate_start_times_for_trip()`
  - 用当前 interval 过滤 start candidates
  - 对每个 fixed start 继续回放 `materialize_pulse_sortie()` / `evaluate_timed_trip()`
- no-wait archive record 改为使用 start interval containment，而不是“更早时间自动支配”；
- guarded certificate guard 收紧：
  - waiting-allowed 数据当前不能由 guarded toy Pulse 证书化；
  - 只有 no-wait start-domain complete path 才能走 toy certificate guard。

验证：

- fixed root start 会漏、interval Pulse 能找回的 no-wait toy case；
- Pulse completed-sortie start candidates 与 `candidate_start_times_for_trip()` 一致；
- interval Pulse 与 brute-force over candidate starts 在 toy 上 signatures / true RC / best RC 对齐；
- multi-sortie candidate-start compatibility 通过 brute-force 对齐覆盖；
- waiting-allowed 数据即使开启 toy certificate config 也不会 certificate；
- 旧 no-wait archive dominance 边界继续通过。

仍未实现：

- waiting-allowed start interval proof logic；
- resume；
- parallel；
- adaptive hierarchical sharding；
- cut / subset-row / fleet-cut prefix lower bound；
- production benchmark 默认启用。

### Phase 7H

已完成：

- 新增 sharded Pulse audit-only driver 链路，默认关闭；
- audit 在根节点 legacy final pricing 结果之后运行；
- audit 结果不改写 `pricing`，不加列，不设置 `dual_bound`，不触发 node fathoming；
- audit 使用独立 hard deadline / recursion cap：
  - `journey_sharded_pulse_audit_time_limit`
  - `journey_sharded_pulse_audit_max_recursions`
- audit 可用 dummy shard engine 构造 focused disagreement tests，但 official sharded final judge 仍默认关闭；
- audit JSONL 事件为 `journey_sharded_pulse_audit`；
- audit log 字段包含：
  - `pulse_audit_enabled`
  - `pulse_audit_status`
  - `pulse_audit_reason`
  - `pulse_audit_global_certificate_capable`
  - `pulse_audit_agrees_with_legacy`
  - `pulse_audit_comparison_type`
  - `pulse_audit_disagreement_type`
  - `pulse_audit_disagreement_severity`
  - `pulse_audit_legacy_state`
  - `pulse_audit_legacy_best_rc`
  - `pulse_audit_pulse_best_rc`
  - `pulse_audit_time`
  - `pulse_audit_recursions`
  - `pulse_audit_shards_total/certified/incomplete/negative`
  - `pulse_audit_bound_pruned`
  - `pulse_audit_archive_pruned`
  - `pulse_audit_time_window_pruned`
  - `pulse_audit_return_pruned`
  - `pulse_audit_harvested_count`
- audit context hash 覆盖同一 true dual / cuts / branch / forbidden signature：
  - `pulse_audit_context_hash`
  - `pulse_audit_true_dual_hash`
  - `pulse_audit_cut_hash`
  - `pulse_audit_branch_hash`
  - `pulse_audit_forbidden_signature_hash`
- comparison type 覆盖 3x3 matrix：
  - `legacy_certified_pulse_certified`
  - `legacy_certified_pulse_incomplete`
  - `legacy_certified_pulse_negative`
  - `legacy_negative_pulse_negative`
  - `legacy_negative_pulse_incomplete`
  - `legacy_negative_pulse_certified`
  - `legacy_incomplete_pulse_negative`
  - `legacy_incomplete_pulse_incomplete`
  - `legacy_incomplete_pulse_certified`
- critical disagreement type 覆盖：
  - `legacy_certified_pulse_negative`
  - `legacy_negative_pulse_certified`
- warning disagreement type 覆盖：
  - `legacy_certified_pulse_incomplete`
  - `legacy_incomplete_pulse_certified`
  - `legacy_negative_pulse_incomplete`
  - `legacy_incomplete_pulse_negative`
  - 其他非一致状态

验证：

- audit-only certified Pulse 不会设置 official `dual_bound`；
- audit-only certified Pulse 不会改变 driver 使用的 official `pricing_state`；
- legacy certified + Pulse certified 的 agreement payload；
- legacy certified + Pulse negative / legacy negative + Pulse certified 的 critical disagreement payload；
- 3x3 comparison matrix payload；
- audit context hash 字段非空；
- legacy incomplete + Pulse certified 只写 audit disagreement，不 certificate；
- audit timeout 记录 `AUDIT_INCOMPLETE`，不影响 official result；
- waiting-allowed instance 下 audit 可运行，但仍无 official certificate effect；
- audit log 中 bound/archive/time-window/return/harvest counters 可观测。
- 真实小矩阵 audit-only smoke：
  - `very_small`
  - Apollo 5
  - Tranquillitatis 5
  - Apollo 10
- 真实小矩阵中 official `status` / `dual_bound` / `pricing_state` / `best_rc` 均未被 audit 改写；
- 真实小矩阵中未出现 `legacy_certified_pulse_negative` 或 `legacy_negative_pulse_certified`；
- Apollo 10 出现一次 `legacy_negative_pulse_incomplete`，按 warning 记录，不阻塞。

仍未实现：

- branch-node audit；
- production default enable；
- direct official certificate effect；
- 20/100 A/B；
- cut / subset-row / fleet-cut prefix lower-bound 增强。

### Phase 7I-A

已完成：

- 新增 Sharded Pulse hidden-negative worker，默认关闭；
- 触发点为根节点 legacy final judge 前：
  - `journey_sharded_pulse_hidden_negative_worker_trigger="before_legacy_final_judge"`
- worker 使用当前 SCIP true dual / cuts / branch / forbidden-signature context；
- worker 与 audit 复用 context hash 口径：
  - `pulse_worker_context_hash`
  - `pulse_worker_true_dual_hash`
  - `pulse_worker_cut_hash`
  - `pulse_worker_branch_hash`
  - `pulse_worker_forbidden_signature_hash`
- worker 可启用 transition archive / weak safe bound / support-aware harvesting；
- worker 返回 journeys 前强制逐条 `manual_journey_reduced_cost()` 复算；
- 非 true-RC negative journey 会被过滤；
- worker no-negative / certified / duplicate-only / incomplete 都不会成为 official certificate；
- worker 只有在返回并成功加入 true-RC negative journeys 时，才通过正常 RMP 加列流程影响 official 求解。

新增配置：

- `journey_sharded_pulse_hidden_negative_worker_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_time_limit=3.0`
- `journey_sharded_pulse_hidden_negative_worker_max_recursions=100000`
- `journey_sharded_pulse_hidden_negative_worker_archive_enabled`
- `journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled`
- `journey_sharded_pulse_hidden_negative_worker_harvesting_enabled`
- `journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit`
- `journey_sharded_pulse_hidden_negative_worker_max_columns`

exactness 边界：

- `FOUND_NEGATIVE` / `FOUND_NEGATIVE_HARVESTED` 可作为 worker 找列结果；
- `INCOMPLETE_LIMIT` 不证书；
- `DUPLICATE_ONLY` 不证书；
- hidden worker 即使底层 Pulse 完整 no-negative，也会降级为 non-certificate incomplete；
- `global_certificate_capable=False`；
- `final_judge_certificate_capable=False`。

验证：

- real `very_small` worker 返回列均满足 true-RC `< -eps`；
- driver active path 中 worker 能加列，但不设置 `dual_bound` / certificate；
- duplicate-only worker 不证书；
- dummy certified worker 被降级为 `INCOMPLETE_LIMIT`；
- worker context hash 字段非空；
- audit / dummy / guarded sharded final judge focused regression 仍通过。
- real small smoke 已完成：
  - Apollo 5
  - Tranquillitatis 5
  - Apollo 10
- real small smoke 中 active worker 没有返回可加列 journeys；
- worker 有真实 transition pruning 信号，但仍以 `INCOMPLETE_LIMIT` 为主；
- Apollo 5 在短时限下因 worker/audit 额外开销从 baseline `OPTIMAL` 变为 `TIME_LIMIT`，说明当前不应默认启用 active worker。

### Phase 7J

已完成：

- 新增 adaptive second-action shard refinement 调度，默认关闭；
- 父 first-task shard 若满足 hard incomplete 条件，可 exact-safely refine 为二级 child shards：
  - `next-task k` for `k != first_task`
  - `return-after-first-task`
- refinement 只在以下条件同时满足时触发：
  - `pulse_adaptive_sharding_enabled=True`
  - `pulse_refine_incomplete_first_task_shards=True`
  - parent shard 未 exhausted；
  - parent shard 没有 found negative；
  - parent shard `recursions >= pulse_refinement_min_recursions`；
  - parent shard `expanded_states >= pulse_refinement_min_expanded`；
  - 完整 child 集合数量 `<= pulse_refinement_max_children`
- 若 `pulse_refinement_max_children` 无法覆盖完整 child partition，则不 refine，保持旧 first-task 行为，避免 partial partition 参与证明；
- parent refined 后只累计运行指标和 `final_judge_shards_refined`，不直接参与 certificate；
- required proof shard 改为完整 child 集合：
  - all children certified -> parent 可视为 certified；
  - any child negative -> parent negative；
  - any child incomplete and no negative -> parent incomplete；
- child 调度顺序优先高 cover dual、低 transition cost，`return-after-first-task` 放在最后；排序只影响速度，不影响 exactness；
- audit / hidden-worker config builder 已接入同一组 adaptive refinement 字段，但默认关闭；
- `journey_sharded_pulse_audit` payload 新增 `pulse_audit_shards_refined`。

新增配置：

- `journey_pulse_adaptive_sharding_enabled=False`
- `journey_pulse_refine_incomplete_first_task_shards=False`
- `journey_pulse_refinement_min_recursions=1000`
- `journey_pulse_refinement_min_expanded=0`
- `journey_pulse_refinement_max_children=32`
- audit 前缀等价项：
  - `journey_sharded_pulse_audit_adaptive_sharding_enabled`
  - `journey_sharded_pulse_audit_refine_incomplete_first_task_shards`
  - `journey_sharded_pulse_audit_refinement_min_recursions`
  - `journey_sharded_pulse_audit_refinement_min_expanded`
  - `journey_sharded_pulse_audit_refinement_max_children`
- hidden-worker 前缀等价项已支持，但仍不建议默认启用 active worker。

验证：

- parent refined children union equals parent brute-force subset 的 toy partition 仍通过；
- child shards pairwise disjoint 的 toy partition 仍通过；
- parent certified iff all children certified；
- child negative propagates to parent negative；
- child incomplete blocks parent certificate；
- adaptive refinement 只在 incomplete threshold 满足后触发；
- refinement disabled / threshold too high / child cap 不能覆盖完整 partition 时保持旧 first-task 行为；
- refined parent frontier 不被当作 proof-closed；
- focused sharded Pulse / audit / hidden-worker 回归通过。

Smoke：

- driver-level audit no-refine/refine 小矩阵使用有效 mainline 配置后，official result 保持一致，但该短时限链路没有触发 `journey_sharded_pulse_audit` 事件，因此不能作为 refinement 效果证据；
- guarded-engine real smoke 在普通 cap 下 parents 已可穷尽，因此 refinement 不触发；
- guarded-engine stress smoke 用低 recursion cap 强制 hard parent：
  - Apollo 5：5 parent -> 5 refined parent / 25 child shards，其中 20 certified、5 incomplete；
  - Tranquillitatis 5：5 parent -> 5 refined parent / 25 child shards，其中 20 certified、5 incomplete；
  - Apollo 10：10 parent -> 10 refined parent / 100 child shards，其中 90 certified、10 incomplete；
- stress smoke 中 `global_certificate_capable=False`，未放开 official certificate。

当前边界：

- 不接 resume；
- 不接 parallel；
- 不做 adaptive multi-level refinement；
- 不做 production default enable；
- 不做 official certificate gate；
- active hidden-negative worker 仍默认关闭，且当前 real smoke 不支持默认启用。

### Phase 7K

已完成：

- 新增 shard scheduling，默认关闭；
- first-task shard 可按 cover dual / depot round-trip proxy / optional urgency 排序；
- second-action child shard 可按 next-task cover dual 与 transition cost proxy 排序，`return-after-first-task` 仍放在最后；
- 排序只影响运行顺序，不影响 shard partition、proof ledger 或 certificate 语义；
- 新增 shard ROI gate，默认关闭；
- 低 ROI shard 只会标记为 `LOW_ROI_INCOMPLETE` / `low_roi_incomplete`，不得 certificate；
- low ROI 判定不会吞掉 `FOUND_NEGATIVE` / `FOUND_NEGATIVE_HARVESTED`；
- parent shard 若被判为 low ROI，不触发 second-action refinement，避免把低收益空间继续膨胀成大量 child shards；
- `JourneyPricingResult` 与 JSONL 增加：
  - `pulse_shard_scheduling_enabled`
  - `pulse_shard_roi_gate_enabled`
  - `pulse_low_roi_shards`
- audit payload 增加 `pulse_audit_low_roi_shards`；
- worker payload 增加 `pulse_worker_low_roi_shards`；
- audit trigger observability 增强：
  - `pulse_audit_skipped`
  - `pulse_audit_skip_reason`
  - `pulse_audit_trigger`
- audit 支持 trigger 配置：
  - `after_legacy_final_judge`
  - `after_each_final_pricing`
  - `on_certificate_candidate`
- root 可通过 `journey_sharded_pulse_audit_force_on_root=True` 强制 audit trigger 检查；
- hidden-negative worker 支持 `hard_tail_only` 触发门控，默认仍关闭；
- hard-tail worker 可按 certificate candidate、remaining time、min tasks、previous audit signal 做 strict gate，避免小快实例默认启动 worker。

新增配置：

- `journey_pulse_shard_scheduling_enabled=False`
- `journey_pulse_shard_roi_gate_enabled=False`
- `journey_pulse_shard_roi_prune_rate_floor=0.0`
- `journey_pulse_shard_roi_min_time=0.0`
- `journey_pulse_shard_roi_min_expanded=0`
- audit 前缀等价项：
  - `journey_sharded_pulse_audit_shard_scheduling_enabled`
  - `journey_sharded_pulse_audit_shard_roi_gate_enabled`
  - `journey_sharded_pulse_audit_shard_roi_prune_rate_floor`
  - `journey_sharded_pulse_audit_shard_roi_min_time`
  - `journey_sharded_pulse_audit_shard_roi_min_expanded`
- hidden-worker 前缀等价项：
  - `journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled`
  - `journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled`
  - `journey_sharded_pulse_hidden_negative_worker_shard_roi_prune_rate_floor`
  - `journey_sharded_pulse_hidden_negative_worker_shard_roi_min_time`
  - `journey_sharded_pulse_hidden_negative_worker_shard_roi_min_expanded`
- audit trigger：
  - `journey_sharded_pulse_audit_trigger="after_legacy_final_judge"`
  - `journey_sharded_pulse_audit_force_on_root=False`
  - `journey_sharded_pulse_audit_log_skips=False`
- worker gate：
  - `journey_sharded_pulse_hidden_negative_worker_trigger="before_legacy_final_judge" | "hard_tail_only"`
  - `journey_sharded_pulse_hidden_negative_worker_min_tasks`
  - `journey_sharded_pulse_hidden_negative_worker_min_remaining_time`
  - `journey_sharded_pulse_hidden_negative_worker_audit_signal_max_age`

验证：

- audit skip 会写出 `pulse_audit_skipped=True` 和稳定 skip reason；
- root force-on-audit 可在 `after_each_final_pricing` trigger 下产生 audit event；
- first-task priority order 稳定，结果语义不变；
- child priority order 稳定，结果语义不变；
- low ROI shard 只产生 incomplete，不产生 certificate；
- low ROI gate 不改变 found-negative correctness；
- hard-tail worker gate 在小快实例上不会触发；
- hard-tail worker gate 在 certificate-candidate / sufficient remaining / min-task 条件满足时可触发；
- Phase 7J refinement、Phase 7H audit、Phase 7I worker 相关 focused regression 仍通过。

当前边界：

- ROI gate 是 fail-open / incomplete-only 机制，不是 proof；
- scheduling priority 只使用 proxy，不参与 reduced-cost proof；
- audit skip 日志只说明触发路径，不改变 official result；
- hidden-negative worker 仍不得 certificate；
- 不做 production default enable；
- 不做 20/100 A/B。

### Phase 7L

已完成：

- 新增 audit-only ROI calibration 脚本：
  - `BPC_future/scripts/run_sharded_pulse_roi_calibration.py`
- 默认实例矩阵：
  - `very_small`
  - Apollo5 balanced seed 36000
  - Tranquillitatis5 balanced seed 136000
  - Apollo10 balanced seed 41002
  - Tranquillitatis10_09 balanced seed 141817
- 默认 profile：
  - `baseline`
  - `audit_no_refine`
  - `audit_refine`
  - `audit_refine_roi_low`
  - `audit_refine_roi_mid`
  - `audit_refine_roi_high`
- ROI 三档：
  - low: `prune_rate_floor=0.001`, `min_expanded=10`, `min_time=0.0`
  - mid: `prune_rate_floor=0.01`, `min_expanded=25`, `min_time=0.01`
  - high: `prune_rate_floor=0.05`, `min_expanded=50`, `min_time=0.02`
- 输出：
  - `summary.json`
  - `summary.csv`
  - per-run JSONL logs
- summary 字段覆盖：
  - official status / dual bound / pricing state / best rc
  - `official_unchanged_vs_baseline`
  - audit status / comparison type / disagreement severity
  - shard total / certified / incomplete / negative / refined
  - low ROI shards
  - bound/archive/time-window/energy/return/capacity pruning counters
  - negative pool / harvested count
  - critical disagreement flag
- 脚本对齐 main runner，加载实例后先执行 `apply_fleet_bound_override()`，避免 Moon Trek real instances 因固定 fleet cap 造成初始 journey RMP infeasible；
- 若 audit profile 没有触发任何 audit event，summary 显式标记 `pulse_audit_skipped=True` 与 `pulse_audit_skip_reason=legacy_not_called`，避免校准表出现不可解释空白。

短时限 calibration smoke：

- 运行 5 instances x 6 profiles，共 30 rows；
- `official_unchanged_vs_baseline=True` for all rows；
- no `legacy_certified_pulse_negative`；
- no `legacy_negative_pulse_certified`；
- audit profiles 在当前短 cap 下均为 warning 级 `legacy_incomplete_pulse_negative`；
- very_small / Apollo5 / Tranquillitatis5 / Apollo10 / Tranquillitatis10_09 均出现 Pulse audit found-negative 与 harvesting signal；
- 当前短 cap 下 `low_roi_shards=0`，说明 ROI gate 未成为主导因素；这轮结果不能直接给出 ROI floor 生产阈值。

当前判断：

- 当前样本更像 hidden-negative signal calibration，而不是 no-negative proof / low-ROI threshold calibration；
- 不能据此放开 official certificate；
- 不能默认启用 hidden worker；
- 若继续 worker 路线，只能走 strict hard-tail retry，并继续 audit-only 对照；
- 若要校准 ROI gate 本身，需要补 no-negative / proof-hard / forced-incomplete 样本，使 low-ROI gate 实际触发。

### Phase 7M

已完成：

- 将 hidden-negative worker 收紧为 strict hard-tail mode：
  - `journey_sharded_pulse_hidden_negative_worker_trigger="hard_tail_only"`
  - 必须是 `certificate_candidate=True`
  - 必须满足 remaining time / min-task 门槛
  - 必须存在同一 node/depth、未超过 max-age 的 previous audit negative signal
  - previous audit signal 的 context hash 必须匹配当前 true dual / cuts / branch / forbidden-signature context
- previous audit signal 只接受 strongest signal：
  - audit status 为 `FOUND_NEGATIVE`
  - 或 audit comparison type 为 `legacy_incomplete_pulse_negative`
  - 或 audit comparison type 为 `legacy_negative_pulse_negative`
  - 或 audit shard negative count > 0
- prune-only signal 不触发 worker：
  - bound pruned / archive pruned / time-window pruned / return pruned 只能作为日志观测
  - 不会进入 hard-tail worker gate
- driver 层新增轻量 audit-signal cache：
  - 不是 proof cache
  - 不是 certificate cache
  - 只用于下一轮 hard-tail worker 触发判断
  - context mismatch 时 fail-closed 跳过 worker
- hidden-negative worker 的输出集合仍被严格限制为：
  - `FOUND_NEGATIVE`
  - `FOUND_NEGATIVE_HARVESTED`
  - `INCOMPLETE_LIMIT`
  - `DUPLICATE_ONLY`
- hidden-negative worker 永远不得产生：
  - `CERTIFIED_NO_NEGATIVE`
  - official lower bound
  - official certificate effect

新增/更新日志字段：

- worker skip 可观测：
  - `pulse_worker_skipped`
  - `pulse_worker_skip_reason`
  - `pulse_worker_trigger`
- worker audit-signal gate 可观测：
  - `pulse_worker_previous_audit_signal`
  - `pulse_worker_context_hash`
  - `pulse_worker_true_dual_hash`
  - `pulse_worker_cut_hash`
  - `pulse_worker_branch_hash`
  - `pulse_worker_forbidden_signature_hash`
- ROI calibration summary 新增 `audit_plus_strict_worker` profile，并记录：
  - worker events
  - skip reason
  - previous-audit-signal flag
  - returned journeys
  - added journeys
  - worker time / recursions
  - worker context hash
- `audit_plus_strict_worker` 是显式 opt-in profile，不进入脚本默认 profile 顺序；
- 脚本额外支持 `audit_only` alias，用于 small smoke 与报告矩阵对齐。

验证：

- previous audit negative signal 会触发 hard-tail worker；
- 没有 previous signal 会跳过 worker；
- prune-only signal 不触发 worker；
- context mismatch 会使 previous signal 失效；
- worker 返回 journeys 前逐条 true-RC 复算；
- worker found negative 只走正常 add-column path；
- worker incomplete 不设置 official lower bound；
- worker duplicate-only 不 certificate；
- default config 行为不变。

当前边界：

- strict worker 仍默认关闭；
- strict worker 不接 official certificate gate；
- strict worker 只作为 hidden-negative column finder；
- 当前不做 resume / parallel / 20/100 A/B；
- 当前不继续扩大 worker budget；若小矩阵 smoke 显示 no trigger 或 context mismatch，先作为 audit signal calibration 结果记录。

### Phase 7N

已完成：

- 新增 current-context signal probe / audit-seeded worker bridge；
- 新增 worker trigger：
  - `journey_sharded_pulse_hidden_negative_worker_trigger="audit_signal_or_current_probe"`
- hard-tail 条件仍然必须先满足：
  - `certificate_candidate=True`
  - task 数量达到 hidden-worker min-task gate
  - remaining time 达到 hidden-worker min-remaining gate
- signal source 分层：
  - `none`
  - `previous_audit`
  - `current_context_probe`
  - 兼容旧测试路径的 `ungated`
- 若 previous audit negative signal 存在且 context hash 匹配：
  - 直接按 strict worker path 运行；
- 若没有 previous audit signal，但 current probe 显式启用：
  - 运行短预算 current-context probe；
  - probe 找到 true-RC negative journeys 时走正常 add-column path；
  - probe incomplete / duplicate-only / certified-like no-negative 均不 certificate；
- 若 previous audit signal 存在但 context hash mismatch：
  - fail-closed，跳过 worker，不用 current probe 绕过 mismatch。

新增配置：

- `journey_sharded_pulse_worker_current_probe_enabled=False`
- `journey_sharded_pulse_worker_current_probe_time_limit=1.0`
- `journey_sharded_pulse_worker_current_probe_max_recursions=50000`
- `journey_sharded_pulse_worker_current_probe_min_tasks=10`
- `journey_sharded_pulse_worker_current_probe_min_remaining_time=8.0`
- `journey_sharded_pulse_worker_current_probe_harvesting_enabled=True`
- `journey_sharded_pulse_worker_current_probe_max_columns=16`
- `journey_sharded_pulse_worker_current_probe_negative_harvest_limit`

新增/更新日志字段：

- `pulse_worker_signal_source`
- `pulse_worker_current_probe_signal`
- `pulse_worker_previous_audit_signal`
- `pulse_worker_context_hash`
- `pulse_worker_skip_reason`

校准脚本新增显式 opt-in profiles：

- `strict_worker_previous_signal_only`
- `strict_worker_current_probe`

exactness 边界：

- current probe found negative -> 只可加列；
- current probe no negative -> 不证书；
- current probe incomplete -> 不证书；
- current probe duplicate-only -> 不证书；
- current probe empty found-negative -> 降级为 non-certificate incomplete；
- current probe certified-like no-negative -> 降级为 non-certificate incomplete；
- 所有 returned journeys 仍必须通过 `manual_journey_reduced_cost()` true-RC 过滤；
- `global_certificate_capable=False`；
- `final_judge_certificate_capable=False`；
- 不产生 official lower bound。

验证：

- no previous signal + current probe negative -> `FOUND_NEGATIVE`；
- no previous signal + current probe incomplete -> non-certificate incomplete；
- current probe duplicate-only -> no certificate；
- current probe empty found-negative -> non-certificate incomplete；
- current probe certified-like result -> downgraded to incomplete；
- previous audit negative + matching context -> worker triggers；
- previous audit negative + context mismatch -> worker skips；
- prune-only signal does not trigger strict mode；
- small-fast current-probe min-task gate prevents probe from running。

当前边界：

- current probe 默认关闭；
- current probe 不是 certificate oracle；
- current probe 不默认进入 benchmark；
- 不做 resume / parallel / 20/100 A/B；
- 若 current probe 仍无 ROI，停止 active-worker 主线，转向 resume 或 legacy final judge 优化。

### Phase 7O

已完成：

- 扩展 ROI calibration summary，使 hard-tail worker A/B 可直接从 JSONL 重建：
  - `solving_time`
  - `rmp_solves`
  - `pricing_calls`
  - `exact_pricing_calls`
  - `columns`
  - `legacy_final_judge_calls`
  - `legacy_final_judge_after_worker_calls`
  - `completion_bound_retry_count`
  - `exact_retry_calls`
  - `hidden_negative_audit_events`
  - `pulse_worker_added_new_journeys`
  - `pulse_worker_added_replacement_journeys`
  - `pulse_worker_added_new_task_set_count`
  - `pulse_worker_added_replacement_task_set_count`
  - `pulse_worker_added_support_changing_count`
  - `pulse_worker_addition_productivity_class`
  - `pulse_worker_next_rmp_objective_delta`
  - `pulse_worker_next_dual_l1_delta`
  - `pulse_worker_followup_legacy_final_judge_called`
  - `pulse_worker_followup_completion_retry_called`
  - `pulse_worker_followup_hidden_negative_found`
- 新增 instance presets：
  - `tranq10_01`
  - `tranq10_04`
- 跑 controlled short A/B：
  - Apollo5
  - Tranquillitatis5
  - Apollo10
  - Tranquillitatis10_09
  - Tranquillitatis10_04
  - Tranquillitatis10_01
- profiles：
  - `baseline`
  - `audit_only`
  - `strict_worker_previous_signal_only`
  - `strict_worker_current_probe`

短时限 A/B 观察：

- Apollo5 / Tranquillitatis5：
  - current probe 被 `current_probe_instance_too_small` gate 拦住；
  - no worker columns；
- Apollo10：
  - current probe returned 2 / added 2；
  - added columns 都是 replacement；
  - active support-changing count = 1；
  - next RMP objective delta = -0.220167；
  - next dual L1 delta = 0.36586；
- Tranquillitatis10_09：
  - current probe returned 4 / added 4；
  - new task-set count = 1；
  - replacement task-set count = 3；
  - active support-changing count = 1；
  - next RMP objective delta = -8.209058；
  - next dual L1 delta = 30.524704；
- Tranquillitatis10_04 / 10_01：
  - strict worker skipped as `not_certificate_candidate`；
- no critical disagreement；
- no certificate / official lower-bound side effect。

当前判断：

- Phase 7N 的 current probe 有真实 add-column signal；
- 本轮短时限 A/B 尚未证明 wall-time ROI；
- completion-bound retry count 没有下降；
- legacy final judge calls 没有下降；
- Apollo10 / tranq10_09 的正向信号主要是 RMP objective / dual movement；
- 下一步若继续 worker 主线，应优先做 column impact filter / active-support-aware return，而不是提高 worker budget 或放开默认启用。

2026-06-12 追加：

- 将 `run_sharded_pulse_roi_calibration.py` 从短矩阵脚本补齐为 Phase 7O profile-matrix 校准框架：
  - 新增 10-task presets：
    - `tranq10_06`
    - `apollo10_04`
    - `apollo10_09`
  - 新增 20-task presets：
    - `tranq20_01`
    - `apollo20_01`
    - `mt20_greedy_apollo_01`
    - `mt20_greedy_tranq_01`
  - 新增显式 opt-in profiles：
    - `strict_worker_current_probe_support_aware`
    - `strict_worker_current_probe_support_aware_low_budget`
    - `strict_worker_current_probe_support_aware_mid_budget`
    - `strict_worker_current_probe_support_aware_impact_filter`
    - `strict_worker_current_probe_hard_tail_only`
  - 新增 Phase 7O summary/gate 字段：
    - `scale`
    - `wall_time`
    - `primal`
    - `dual_bound`
    - `gap`
    - `pricing_state`
    - `best_rc`
    - `official_result_changed_vs_baseline`
    - `objective_mismatch_vs_baseline`
    - `root_rmp_rounds`
    - `generated_sequences`
    - `evaluated_timed_trips`
    - `final_judge_max_single_call_time`
    - `exact_completion_bound_retry_count`
    - `exact_completion_bound_retry_time`
    - `hidden_negative_audit_count`
    - worker alias fields without `pulse_` prefix
    - follow-up RMP / legacy / retry alias fields
    - `critical_disagreement_count`
    - `improvement_class`
- `improvement_class` 是 conservative diagnostic，不参与 solver 语义：
  - `unsafe` 只用于 critical disagreement 或两个 `OPTIMAL` 之间 objective/dual mismatch；
  - worker 加列导致短时限 incumbent / gap 变化不会自动被当作 correctness unsafe；
  - low-budget smoke 中的 extra overhead 会被标为 `worsened`。
- 低预算 profile-matrix smoke 已跑通：
  - instances：
    - `apollo5`
    - `apollo10`
    - `tranq20_01`
  - profiles：
    - `baseline`
    - `strict_worker_current_probe_support_aware_low_budget`
    - `strict_worker_current_probe_support_aware_impact_filter`
    - `strict_worker_current_probe_hard_tail_only`
  - output：
    - `BPC_future/results/sharded_pulse_phase7o_profile_matrix_smoke_20260612/summary.json`
    - `BPC_future/results/sharded_pulse_phase7o_profile_matrix_smoke_20260612/summary.csv`
- smoke 结论：
  - Apollo5 worker 未触发，但 audit/skip logging overhead 在极短 baseline 下被标为 `worsened`；
  - Apollo10 support-aware current probe 仍可加列，但低预算总 wall time worsened；
  - tranq20_01 在该短 cap 下 worker 未触发，skip reason 为 `not_certificate_candidate`；
  - 无 critical disagreement；
  - 无 certificate / official lower-bound side effect。

2026-06-12 扩展矩阵：

- 输出：
  - `BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/summary.csv`
- instances：
  - 5-task：`apollo5`, `tranq5`
  - 10-task：`apollo10`, `tranq10_09`, `tranq10_04`, `tranq10_01`, `tranq10_06`, `apollo10_04`, `apollo10_09`
  - 20-task：`tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`
- profiles：
  - `baseline`
  - `audit_only`
  - `strict_worker_previous_signal_only`
  - `strict_worker_current_probe`
  - `strict_worker_current_probe_support_aware`
  - `strict_worker_current_probe_support_aware_low_budget`
  - `strict_worker_current_probe_support_aware_mid_budget`
  - `strict_worker_current_probe_support_aware_impact_filter`
  - `strict_worker_current_probe_hard_tail_only`
- 结果：
  - 108 rows；
  - `critical_disagreement_count=0`；
  - no objective/dual mismatch between two `OPTIMAL` runs；
  - all non-baseline profiles classified `worsened` under the conservative short-budget wall-time gate；
  - 5-task worker 被 gate 拦住，但 audit/skip logging overhead 明显；
  - 10-task current-probe profiles 能加列：
    - `apollo10`: 2 added；
    - `tranq10_09`: 3-4 added depending budget/filter；
    - `apollo10_04`: 3-4 added；
  - 20-task only `mt20_greedy_apollo_01` returned columns in this short run:
    - current probe: 4 added；
    - low budget: 2 added；
    - mid budget: 5 added；
    - impact filter: 3 added；
  - `strict_worker_current_probe_hard_tail_only` did not trigger without previous audit negative signal.
- 判断：
  - current-context probe 的 hidden-negative signal 真实存在；
  - impact/low-budget 能减少返回列数；
  - 但在该受控短预算下没有 wall-time ROI；
  - 不能默认启用 worker；
  - 不能进入 official certificate gate；
  - 若继续 worker 主线，必须先减少 audit/skip overhead 或改成真正 hard-tail 延迟触发。

2026-06-12 delayed hard-tail gate：

- 新增显式 opt-in profiles：
  - `strict_worker_delayed_hard_tail_only`
  - `strict_worker_delayed_current_probe_impact`
- 语义：
  - 5-task 默认完全不注入 Pulse audit/worker 配置；
  - 10/20-task 才允许进入；
  - audit trigger 改为 `on_certificate_candidate`；
  - `journey_sharded_pulse_audit_force_on_root=False`；
  - skip logging 默认关闭，避免 no-op skip overhead；
  - `strict_worker_delayed_hard_tail_only` 只消费 previous audit negative signal；
  - `strict_worker_delayed_current_probe_impact` 在 certificate-candidate context 下允许 current probe，并启用 impact filter；
  - 不产生 certificate / official lower-bound effect。
- expanded smoke output：
  - `BPC_future/results/sharded_pulse_phase7o_delayed_hardtail_gate_expanded_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_delayed_hardtail_gate_expanded_20260612/summary.csv`
- 结论：
  - delayed hard-tail-only：
    - 5-task no-regression；
    - 10-task no-regression；
    - 20-task no-regression；
    - 但没有 worker 加列；
  - delayed current-probe impact：
    - 5-task no-regression；
    - 10-task active cases 仍能加列，但 0.15s cap 下 active cases 仍 worsened；
    - 20-task `mt20_greedy_apollo_01` 能加 3 列，但仍 worsened。
- 低 cap smoke output：
  - `BPC_future/results/sharded_pulse_phase7o_delayed_current_probe_lowcap_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_delayed_current_probe_lowcap_smoke_20260612/summary.csv`
- 低 cap 观察：
  - 5-task 仍 no-regression；
  - `apollo10` 加 1 列，保留 objective delta `-0.220167`，classified `no_regression`；
  - `tranq10_09` 加 1 个 new task-set，保留 objective delta `-8.209058`，classified `no_regression`；
  - `apollo10_04` 仍加 3 new task-set 但 classified `worsened`；
  - `mt20_greedy_apollo_01` 加 2 new task-set，但 classified `worsened`。
- 当前判断：
  - delayed gate 解决了 small-fast fixed overhead；
  - current probe low cap 保留部分 10-task signal；
  - 仍未证明 20-task improvement；
  - 下一步应把 delayed low-cap current probe 作为候选继续做更正式 5/10 no-regression gate，而不是恢复 after-each-pricing audit。

2026-06-12 5/10 gate:

- Calibration script 新增 reproducible instance groups：
  - `balanced5_all`
  - `balanced10_all`
  - `phase7o_5_gate`
  - `phase7o_10_gate`
  - `phase7o_20_smoke`
  - `phase7o_gate`
- 新增候选 profile：
  - `strict_worker_delayed_current_probe_impact_low_budget`
- 该 profile 内置：
  - delayed certificate-candidate trigger；
  - 5-task no-op gate；
  - impact filter；
  - current probe time / recursion / max-columns 缩小；
  - no certificate effect。
- 5/10 gate output：
  - `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612/summary.csv`
- 5/10 gate 结果：
  - 5-task full balanced set：20 instances；
  - 5-task candidate profile：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - avg wall time 0.024503 vs baseline 0.025109；
    - class：1 `improved`, 19 `no_regression`；
  - 10-task specified gate：7 instances；
  - 10-task candidate profile：
    - added columns = 2；
    - changed = 2；
    - objective mismatch = 0；
    - critical disagreement = 0；
    - classes：7 `no_regression`；
    - `apollo10`: added 1 support-changing replacement, objective delta `-0.220167`；
    - `tranq10_09`: added 1 new task-set, objective delta `-8.209058`。
- 20 smoke output：
  - `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612/summary.csv`
- 20 smoke 结果：
  - 3 instances；
  - `tranq20_01`: no_regression, no worker；
  - `mt20_greedy_tranq_01`: no_regression, no worker；
  - `mt20_greedy_apollo_01`: added 2 new task-set, objective delta `-31.551683`, classified `worsened`；
  - no critical disagreement。
- 当前判断：
  - delayed low-budget profile 已满足本短预算下的 5-task full no-regression；
  - 指定 10-task gate 也无 regression，并保留两个 hidden-negative add-column signals；
  - 20-task 仍未达标，因为唯一 active 20-task case 仍 worsened；
  - 下一步应针对 20-task / apollo10_04 加更严格 trigger 或 per-instance ROI gate，而不是扩大 worker budget。

2026-06-12 ultra-low candidate:

- 新增候选 profile：
  - `strict_worker_delayed_current_probe_impact_ultra_low_budget`
- 该 profile 相比 low-budget 进一步缩小：
  - current probe time factor；
  - current probe recursion factor；
  - current probe max columns。
- output：
  - `BPC_future/results/sharded_pulse_phase7o_delayed_ultralow_profile_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_delayed_ultralow_profile_gate_20260612/summary.csv`
- 结果：
  - 5-task full balanced set：
    - 20 instances；
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - avg wall time 0.024757 vs baseline 0.025147；
    - class：1 `improved`, 19 `no_regression`；
  - 10-task specified gate：
    - 7 instances；
    - worker events = 6；
    - added columns = 2；
    - changed = 2；
    - objective mismatch = 0；
    - critical disagreement = 0；
    - classes：7 `no_regression`；
    - `apollo10`: added 1 support-changing replacement, objective delta `-0.220167`；
    - `tranq10_09`: added 1 new task-set, objective delta `-8.209058`；
    - `apollo10_04` and `apollo10_09`: worker triggered but no returned column, still `no_regression`；
  - 20-task smoke：
    - 3 instances；
    - worker events = 1；
    - added columns = 0；
    - changed = 0；
    - critical disagreement = 0；
    - classes：3 `no_regression`。
- 当前判断：
  - ultra-low profile 是目前最好的 5/10 no-regression candidate；
  - 它保留了两个 10-task useful add-column signals；
  - 它没有提供 20-task improvement；
  - 下一步必须单独寻找 20-task improvement path，不能把当前 result 解释为达标。

2026-06-12 20-task longer signal smoke:

- output：
  - `BPC_future/results/sharded_pulse_phase7o_20_longer_signal_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_20_longer_signal_smoke_20260612/summary.csv`
- profiles：
  - `baseline`
  - `strict_worker_delayed_current_probe_impact_low_budget`
  - `strict_worker_delayed_current_probe_impact`
- 结果：
  - `tranq20_01`: no worker, no change, no_regression；
  - `mt20_greedy_tranq_01`: no worker, no change, no_regression；
  - `mt20_greedy_apollo_01`:
    - baseline primal `1061.554044`；
    - low-budget profile primal `1022.575388`, added 2 new task-set；
    - uncapped delayed impact profile primal `1021.815054`, added 3 columns；
    - wall time increased from `0.212456` to `0.683411/0.692277`；
    - classified `worsened` by wall-time gate despite better primal.
- 当前判断：
  - 20-task 有 solution-quality / column-quality signal；
  - 但仍没有 wall-time ROI；
  - 不能作为 20-task improvement success；
  - 后续如果继续，应增加 ROI-aware early stop / post-addition productivity gate，而不是单纯提高 worker time。

2026-06-12 worker success cooldown smoke:

- 新增 opt-in profile：
  - `strict_worker_delayed_current_probe_impact_low_budget_cooldown`
- 新增 opt-in 配置：
  - `journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds`
- 语义：
  - worker 成功加入列后，后续若干轮只跳过可选 hidden-negative worker；
  - exact pricing / legacy final judge 仍照常运行；
  - skip reason = `success_cooldown`；
  - 不产生 certificate；
  - 不影响 official lower bound。
- output：
  - `BPC_future/results/sharded_pulse_phase7o_worker_cooldown_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_worker_cooldown_smoke_20260612/summary.csv`
- 结果：
  - `tranq20_01`: no worker, no change, no_regression；
  - `mt20_greedy_tranq_01`: no worker, no change, no_regression；
  - `mt20_greedy_apollo_01`:
    - baseline primal `1061.554044`, wall time `0.254094`；
    - low-budget profile primal `1022.575388`, added 2 new task-set, wall time `0.865410`；
    - cooldown profile primal `1030.002361`, added 1 new task-set, wall time `0.513372`；
    - worker time 从 `0.212501` 降到 `0.070875`；
    - 但仍 classified `worsened`。
- 当前判断：
  - cooldown 能降低部分 worker overhead；
  - cooldown 会牺牲一部分 column-quality signal；
  - cooldown 仍没有证明 wall-time ROI；
  - 不能作为 20-task improvement success；
  - worker 路线若继续，应优先做更严格的 ROI / productivity gate，而不是放大预算或默认启用。

2026-06-12 quality classification smoke:

- summary 字段补齐 `目标.md` 要求的短名别名：
  - `worker_added_new_task_set_count`
  - `worker_added_replacement_count`
  - `worker_addition_productivity_class`
- `improvement_class` 调整：
  - 5/10 regression gate 仍保留原 wall-time/no-regression 逻辑；
  - `OPTIMAL` vs `OPTIMAL` objective / dual mismatch 仍为 `unsafe`；
  - 只有 `scale >= 20`、同为 non-OPTIMAL、无 critical disagreement、无 objective mismatch，且 primal 明显优于 baseline 时，才允许标为 `improved`；
  - 该 `improved` 表示 20-task under-budget primal / column-quality improvement，不表示 wall-time speedup。
- output：
  - `BPC_future/results/sharded_pulse_phase7o_quality_classification_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_quality_classification_smoke_20260612/summary.csv`
- 结果：
  - `mt20_greedy_apollo_01` low-budget：
    - primal `1061.554044 -> 1022.575388`；
    - added 2 new task-set；
    - class `improved`；
    - wall time 仍明显慢于 baseline。
  - `mt20_greedy_apollo_01` low-budget + cooldown：
    - primal `1061.554044 -> 1030.002361`；
    - added 1 new task-set；
    - class `improved`；
    - wall time 仍慢于 baseline。
- 当前判断：
  - 20-task 已有可记录的 primal / column-quality improvement signal；
  - wall-time ROI 仍未成立；
  - 最终目标尚未完成；
  - 后续应做 productivity / ROI gate，把同类 signal 的 overhead 压低，而不是继续放大 worker budget。

2026-06-12 20-only cooldown gate:

- 新增 calibration profile：
  - `strict_worker_delayed_current_probe_impact_20_only_cooldown`
- 语义：
  - `task_count < 20` 时不注入 Pulse audit/worker 配置；
  - `task_count >= 20` 时复用 delayed current-context probe、impact filter、low-budget probe 与 success cooldown；
  - 默认 solver 配置不变；
  - 不产生 certificate / official lower-bound effect。
- output：
  - `BPC_future/results/sharded_pulse_phase7o_20_only_cooldown_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_20_only_cooldown_gate_20260612/summary.csv`
- 结果：
  - 5-task full balanced gate：
    - 20 instances；
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - avg wall time `0.025658 -> 0.025209`；
    - classes：1 `improved`, 19 `no_regression`。
  - 10-task specified gate：
    - 7 instances；
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - median wall time `0.103810 -> 0.101739`；
    - classes：7 `no_regression`。
  - 20-task smoke：
    - 3 instances；
    - worker events = 1；
    - added columns = 1；
    - added new task-set = 1；
    - critical disagreement = 0；
    - classes：1 `improved`, 2 `no_regression`；
    - `mt20_greedy_apollo_01`: primal `1061.554044 -> 1030.002361`, next RMP objective delta `-31.551683`。
- 当前判断：
  - 这是当前最干净的 Phase 7O 候选：5/10 no-regression，20 有 primal / new-task-set signal；
  - 它仍没有 wall-time speedup；
  - final judge / retry tail 仍未下降；
  - 不能默认启用，也不能进入 official certificate gate；
  - 后续应压低 20-task worker overhead，而不是放大 worker budget。

2026-06-12 pre-heuristic worker gate:

- 新增 opt-in 配置：
  - `journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled`
- 新增 calibration profile：
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`
- 语义：
  - `task_count < 20` 时 no-op；
  - `task_count >= 20` 时在 heuristic pricing 前先运行 bounded Pulse worker；
  - 若 worker 找到 true-RC negative column 并 add-column，本轮跳过 heuristic / exact，直接进入下一轮 RMP；
  - 若 worker no-column / incomplete，则原 heuristic / exact path 照常运行；
  - 不产生 certificate / official lower-bound effect。
- output：
  - `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_gate_20260612/summary.csv`
- 结果：
  - 5-task full balanced gate：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - avg wall time `0.025284 -> 0.025203`。
  - 10-task specified gate：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - median wall time `0.101716 -> 0.102372`。
  - 20-task smoke：
    - worker events = 1；
    - added columns = 1；
    - added new task-set = 1；
    - generated sequences `735 -> 734`；
    - evaluated timed trips `3698 -> 3689`；
    - classes：1 `improved`, 2 `no_regression`；
    - `mt20_greedy_apollo_01`: primal `1061.554044 -> 1030.002361`, wall time `0.158182 -> 0.222174`。
- tighter-probe smoke：
  - output：
    - `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_tighter_probe_smoke_20260612/summary.json`
    - `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_tighter_probe_smoke_20260612/summary.csv`
  - probe cap 降到约 `0.03s` 后，`mt20_greedy_apollo_01` worker returned / added = `0 / 0`；
  - 当前 useful new-task-set signal 大约需要 `0.05s` / `180` recursions。
- 当前判断：
  - pre-heuristic 顺序是正确方向，能避免第一轮 heuristic 后才跑 worker；
  - 但 active 20-task wall time 仍慢于 baseline；
  - 不能作为最终成功；
  - 下一步需要更便宜的 probe ordering / shard priority / high-yield fingerprint，而不是继续降低 cap 或增加预算。

2026-06-12 stop-after-first-negative gate:

- 新增 opt-in 配置：
  - `journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative`
- 新增 `JourneyPricingConfig` / `JourneyPricingResult` 字段：
  - `pulse_stop_after_first_negative`
- 语义：
  - guarded sharded Pulse worker 一旦找到 true-RC negative candidates，停止继续扫描后续 first-task / child shards；
  - 已找到候选仍经过 true-RC sanitize、impact filter 和 normal add-column path；
  - incomplete / no-column / duplicate-only 仍不 certificate；
  - default solver 配置不变。
- profile：
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown` 现在同时启用 pre-heuristic worker 和 stop-after-first-negative。
- 20-task smoke output：
  - `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_20_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_20_smoke_20260612/summary.csv`
- full gate output：
  - `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_gate_20260612/summary.csv`
- full gate 结果：
  - 5-task full balanced：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - classes：20 `no_regression`。
  - 10-task specified gate：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0；
    - classes：7 `no_regression`。
  - 20-task smoke：
    - `mt20_greedy_apollo_01` worker triggered；
    - `pulse_worker_shards_total=2`；
    - added 1 new task-set；
    - primal `1061.554044 -> 1030.002361`；
    - next RMP objective delta `-31.551683`；
    - active worker time still about `0.05s` / `190` recursions；
    - classes：1 `improved`, 2 `no_regression`。
- 当前判断：
  - stop-after-first-negative 是 exact-safe 的外层 shard guard；
  - 它减少了找到负列后的后续 shard 扫描；
  - 但没有明显降低 active hard shard 内部成本；
  - 20-task wall time 仍慢于 baseline；
  - 不能默认启用，也不能进入 official certificate gate；
  - 若继续 Phase 7O/7P，应优化 active shard 内部 ordering / high-yield fingerprint / productivity gate，而不是继续加预算。

2026-06-12 leaf-level stop-after-first-negative gate:

- `transition_root_only_pulse()` 新增 opt-in 参数：
  - `stop_after_first_negative`
- 语义：
  - 在 worker-only opt-in path 中，transition Pulse 一旦 materialize 出非 forbidden、非已有 task-set 的 true-RC negative leaf，就停止当前 shard；
  - leaf 仍必须通过 `evaluate_timed_trip()` / `make_journey()` / `manual_journey_reduced_cost()` 语义；
  - result 返回 `FOUND_NEGATIVE` 且 `exhausted=False`；
  - 不参与 no-negative proof，不产生 certificate / official lower-bound effect。
- `JourneyPricingConfig.pulse_stop_after_first_negative` 现在同时控制：
  - active shard 内 leaf-level stop；
  - 外层 first-task / child shard stop。
- focused tests：
  - `test_transition_pulse_stop_after_first_negative_exits_current_shard`
  - `test_sharded_pulse_stop_after_first_negative_passes_to_transition_core`
- 20-task smoke output：
  - `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_20_smoke_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_20_smoke_20260612/summary.csv`
- full gate output：
  - `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_gate_20260612/summary.csv`
- 结果：
  - 5-task full balanced：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0。
  - 10-task specified gate：
    - worker events = 0；
    - changed = 0；
    - critical disagreement = 0。
  - 20-task `mt20_greedy_apollo_01`：
    - worker time `0.050740 -> 0.031975` compared with outer-stop gate；
    - recursions `190 -> 115`；
    - added 1 new task-set；
    - primal `1061.554044 -> 1030.002361`；
    - next RMP objective delta `-31.551683`。
- 当前判断：
  - leaf-level stop 是真实 overhead reduction；
  - 但 active 20-task wall time 仍慢于 baseline；
  - final judge / retry tail 仍未证明下降；
  - 不能默认启用，也不能进入 official certificate gate；
  - 后续应继续降低 active shard 内部 search cost 或做更强 productivity trigger。

### Phase 7P-alt

已完成：

- 新增 Sharded Pulse hidden-negative worker column impact filter；
- 默认关闭，不改变 production path；
- 新配置：
  - `journey_sharded_pulse_hidden_negative_worker_impact_filter_mode`
    - `off`
    - `prefer_new_or_active_support`
    - `require_new_or_active_support`
  - `journey_sharded_pulse_hidden_negative_worker_impact_filter_max_columns`
- `require_new_or_active_support` 只保留：
  - new task-set；
  - active support-changing replacement；
- 若全部候选被 filter 掉：
  - 返回 non-certificate `INCOMPLETE_LIMIT`；
  - reason = `sharded_pulse_hidden_negative_worker_impact_filtered_empty`；
  - 不产生 certificate；
  - 不产生 official lower bound；
- 所有 filter 输入都已经先通过 true-RC negative sanitize；
- filter 不参与 proof / certificate，仅用于 hidden-negative worker 返回列选择。

新增日志字段：

- `pulse_worker_impact_filter_enabled`
- `pulse_worker_impact_filter_mode`
- `pulse_worker_impact_filter_candidate_count`
- `pulse_worker_impact_filter_selected_count`
- `pulse_worker_impact_filter_dropped_count`
- `pulse_worker_impact_filter_selected_new_task_set_count`
- `pulse_worker_impact_filter_selected_replacement_task_set_count`
- `pulse_worker_impact_filter_selected_active_support_changing_count`
- `pulse_worker_impact_filter_selected_weak_replacement_count`

校准脚本新增显式 opt-in profile：

- `strict_worker_current_probe_impact`

短时限 A/B 观察：

- Apollo10：
  - unfiltered current probe added 2 replacement columns；
  - impact filter selected 1 / dropped 2；
  - selected column 是 active support-changing replacement；
  - next RMP objective delta 仍为 -0.220167；
- Tranquillitatis10_09：
  - unfiltered current probe added 4 columns；
  - impact filter selected 2 / dropped 3；
  - selected columns 包含 1 个 new task-set 与 1 个 active support-changing replacement；
  - next RMP objective delta 仍为 -8.209058；
- Apollo5 / Tranquillitatis5 仍被 current-probe min-task gate 拦住；
- Tranquillitatis10_04 / 10_01 仍因 `not_certificate_candidate` 跳过。

当前判断：

- impact filter 能减少弱 replacement 返回，同时保留当前样本中的 RMP movement；
- 这仍未证明 wall-time ROI；
- 下一步若继续，应该评估 impact profile 在更长 hard-tail run 中是否减少 tail/retry，而不是默认启用。

## 默认行为

默认 benchmark 行为不变：

- `journey_final_judge_sharding_enabled=False`
- `journey_pulse_final_judge_enabled=False`
- dummy engine 默认关闭；
- production sharded Pulse 只有 opt-in 才进入。

## 风险

1. 当前 production sharded Pulse 是 guarded toy root-only engine，不应当解释为完整 20/100 规模 proof engine。
2. `pulse_max_recursions` 必须在大实例上设置上限；否则 exhaustive toy search 会非常慢。
3. bound pruning 当前只支持 no-cut / 非负 arc/service cost 的弱安全 LB；遇到未证明安全的 row/cost context 必须 fail-open。
4. harvest-after-negative 能返回更多 true-RC negative columns，但不会产生 certificate。
5. second-action sharding 已接入 guarded adaptive refine 调度，但仍默认关闭，且不是 production 20/100 proof engine。
6. waiting-allowed 时间域尚未完整 proof 化，guarded toy Pulse 不得用它产生 certificate。

## 后续建议

1. 7I-A real small smoke 已完成但没有 active-worker ROI；下一步优先做 adaptive second-action shard refinement，而不是继续放大 worker 预算。
2. Phase 7L 已完成 audit-only calibration 脚本与短矩阵 smoke；当前短 cap 下主要观察到 hidden-negative signal，而非 low-ROI threshold signal。
3. 若继续 hidden-negative worker 路线，必须保持 hard-tail gate：只在 audit 已显示 negative / high-prune ROI / hard-tail incomplete 后运行。
4. experimental certificate path 仍需等待：no-wait start-domain complete、无 unsupported cuts/branch、无 timeout、无 duplicate-only、所有 shards certified 且显式实验配置同时满足。
5. 若后续 audit/worker 中出现 support-changing hidden negative，可继续做 Pulse hidden-negative worker mode 增强，但不得直接产生 official certificate。
6. 若 bound ROI 在更宽小实例中持续为正，再做单项安全 bound 增强；每个 cut/fleet contribution 必须先有 exact-safe 证明和 pruned/unpruned 对照测试。
7. 实现 proof-closed prefix cache 时，必须继续严格区分 frontier snapshot 与 proof-closed record。
8. 大实例上只使用 bounded shard slices，配合 resume 和 hierarchical refine。

2026-06-12 Phase 7O full-profile gate:

- 输出：
  - `BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/summary.csv`
  - `BPC_future/logical_graph/run_reports/20260612_sharded_pulse_phase7o_full_profile_gate_zh.md`
- 矩阵：
  - balanced 5-task 全量 20 个；
  - 10-task 指定 7 个；
  - 20-task smoke 3 个；
  - 10 个 profiles，共 300 runs。
- 字段：
  - Phase 7O 要求的 worker / follow-up / critical disagreement / improvement fields 全部存在；
  - `summary.csv` 301 行，per-run logs 300 个。
- 结果：
  - 普通 `audit_only` / `current_probe` / `support_aware` profiles 在 5/10 上明显拖慢，不可作为候选；
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown` 在 5-task 和 10-task 不触发 worker，保持 no-regression；
  - 该候选在 `mt20_greedy_apollo_01` 触发一次 worker，加入 1 个 new task-set，worker time `0.031042s`，recursions `115`，next RMP objective delta `-31.551683`；
  - 20-task candidate 平均 wall `0.192061 -> 0.206804`，仍未证明 wall-time ROI；
  - 所有 profiles critical disagreement 为 0，未产生 official certificate side effect。
- 判断：
  - Phase 7O 仍不满足进入 Phase 7P production tuning 的条件；
  - 不默认启用 worker，不开启 official certificate gate，不扩大 worker time limit；
  - 若继续 worker 路线，应优先降低 active shard 内部成本或做更严格 productivity gate，而不是加预算。

2026-06-12 Phase 7O task-ordering probe:

- 新增 opt-in transition task ordering：
  - `pulse_task_ordering`
  - `journey_pulse_task_ordering`
  - `journey_sharded_pulse_audit_task_ordering`
  - `journey_sharded_pulse_hidden_negative_worker_task_ordering`
- 支持：
  - `natural`
  - `cover_dual_desc`
  - `reduced_cost_proxy`
- 默认仍为 `natural`。
- 新增独立实验 profile：
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered`
- 当前候选 profile 保持不启用 ordering：
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`
- focused tests：
  - exhaustive surface 不变；
  - toy early-stop 中 `generated_sortie_traces 10 -> 1`，`recursions 5 -> 2`；
  - sharded path 正确传参。
- 20-task smoke：
  - output: `BPC_future/results/sharded_pulse_phase7o_task_ordering_compare_20_smoke_20260612/summary.json`
  - natural candidate active row worker time `0.033576s`，recursions `115`；
  - ordered experiment active row worker time `0.035687s`，recursions `115`；
  - 两者都加 1 个 new task-set，primal 相同；
  - ordering 未降低当前 active 20-task shard 成本。
- 判断：
  - ordering 机制保留为 opt-in；
  - 不作为当前 candidate 默认配置；
  - 当前 20-task overhead 更可能在 worker 后 follow-up exact tail / RMP 退化路径，而不是 task expansion ordering；
  - 后续应优先诊断 worker 后 exact tail、productivity gate 或 column-pool/RMP impact。

2026-06-12 Phase 7O follow-up tail attribution:

- 新增 ROI calibration follow-up fields：
  - `followup_wall_after_worker`
  - `followup_pricing_calls`
  - `followup_heuristic_pricing_calls`
  - `followup_exact_pricing_calls`
  - `followup_exact_retry_pricing_calls`
  - `followup_generated_sequences`
  - `followup_evaluated_timed_trips`
  - `followup_legacy_final_judge_calls`
  - `followup_legacy_final_judge_time`
  - `followup_completion_retry_count`
  - `followup_completion_retry_time`
  - `followup_last_pricing_kind/state/reason/best_rc`
- 输出：
  - `BPC_future/results/sharded_pulse_phase7o_followup_attribution_single_20260612/summary.json`
  - `BPC_future/results/sharded_pulse_phase7o_followup_attribution_single_20260612/summary.csv`
  - `BPC_future/logical_graph/run_reports/20260612_sharded_pulse_phase7o_followup_attribution_zh.md`
- Active sample：
  - instance：`mt20_greedy_apollo_01`
  - profile：`strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`
  - worker returned / added = `1 / 1`
  - worker addition class = `changed_inactive_only`
  - next RMP objective delta = `-31.551683`
  - follow-up wall after worker = `0.103100`
  - follow-up pricing calls = `2`，其中 `heuristic=1`、`exact=1`
  - follow-up generated / evaluated = `405 / 1577`
  - last follow-up pricing = `exact` / `INCOMPLETE_LIMIT` / `profile_dp_incomplete` / best RC `0.034526`
- 结论：
  - worker column 是 true-RC negative 且能改善 under-budget primal；
  - 但该列没有消掉 follow-up exact tail；
  - 当前 overhead 不是 task ordering 单独能解决的问题；
  - 后续应优先做 productivity / impact gate 或 active-support-changing return，同时继续保留 5/10 no-regression gate。

2026-06-12 Phase 7P follow-up probe / deadline guard:

- Worker deadline guard:
  - hidden-negative worker call time is now clipped by solver `remaining_time`;
  - current-context probe uses the same clipping rule;
  - focused test verifies `worker_config.time_limit == remaining_time` and `absolute_deadline` is set.
- New opt-in profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup`
  - same 20-only / pre-heuristic / low-budget / stop-first-negative / impact-filter setup as the cooldown candidate;
  - does not set `journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds=2`;
  - therefore a successful worker can continue probing in the next CG iteration.
- Single-instance output:
  - `BPC_future/results/sharded_pulse_phase7p_followup_probe_deadline_single_20260612/summary.json`
- Gate output:
  - `BPC_future/results/sharded_pulse_phase7p_followup_probe_gate_20260612/summary.json`
- Single-instance result on `mt20_greedy_apollo_01`:
  - baseline primal `1061.554044`;
  - cooldown candidate primal `1030.002361`, worker added `1`, follow-up official pricing calls `2`;
  - follow-up probe primal `1022.575388`, worker added `3`, follow-up official pricing calls `0`;
  - follow-up probe reached an `active_replacement_task_set` in the single run, but used nearly the full `0.3s` budget.
- Phase 7O gate result:
  - 5-task full gate: worker events `0`, no regression;
  - 10-task gate: worker events `0`, no regression;
  - 20-task smoke: worker events `3`, added `2`, avg wall `0.211294 -> 0.254920`;
  - `mt20_greedy_apollo_01` primal improved `1061.554044 -> 1022.575388`;
  - critical disagreement `0`, objective mismatch `0`, no certificate side effect.
- Conclusion:
  - deadline guard is a correctness/budget fix and should remain;
  - follow-up probe is an experimental under-budget primal-improvement signal, not wall-time ROI;
  - do not enter production tuning, default enablement, or official certificate gate from this result;
  - next work should add productivity/continuation gates that continue worker only when expected active-support or objective movement is high enough.

2026-06-12 Phase 7P follow-up reserve gate:

- Added opt-in worker post-call reserve:
  - `journey_sharded_pulse_hidden_negative_worker_post_call_time_reserve`;
  - worker/current-probe call time is capped by `remaining_time - reserve`;
  - if reserve leaves no usable time, worker skips with `post_call_reserve_too_low`;
  - default is `0.0`, so default benchmark behavior is unchanged.
- Added experimental profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve`;
  - 20-task only, pre-heuristic, current-context, impact-filtered, stop-after-first-negative, no success cooldown;
  - reserve is `0.08s`;
  - 5/10-task profile expansion remains empty.
- Focused tests:
  - remaining-time cap;
  - post-call reserve cap;
  - ROI profile registry fields;
  - opt-in profile config rules.
- Single-instance `mt20_greedy_apollo_01`:
  - follow-up probe without reserve: wall `0.301354`, worker time `0.181922`, recursions `602`, added `3`, primal `1022.575388`;
  - follow-up reserve: wall `0.289048`, worker time `0.103519`, recursions `332`, added `2`, primal `1022.575388`;
  - reserve reduces worker cost while preserving the under-budget primal signal, but follow-up exact pricing still occurs.
- Gate output:
  - `BPC_future/results/sharded_pulse_phase7p_followup_reserve_gate_20260612/summary.json`
  - `BPC_future/logical_graph/run_reports/20260612_sharded_pulse_phase7p_followup_reserve_gate_zh.md`
- Gate result:
  - 5-task full: worker events `0`, avg wall `0.025536 -> 0.024793`;
  - 10-task selected: worker events `0`, avg wall `0.117756 -> 0.118310`;
  - 20-task smoke: worker events `3`, added `2`, new task-set `2`, avg wall `0.209741 -> 0.249095`;
  - active row remains `mt20_greedy_apollo_01`, primal improves `1061.554044 -> 1022.575388`;
  - critical disagreement `0`, no certificate side effect.
- Conclusion:
  - reserve is a useful budget guard, not a production candidate;
  - it does not establish wall-time ROI;
  - keep worker disabled by default, keep certificate gate closed, and do not expand worker budget from this result.

2026-06-12 Phase 7P active-support continuation gate:

- Added opt-in worker continuation gate:
  - `journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support`;
  - `journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds`;
  - default disabled, so default benchmark behavior is unchanged.
- Semantics:
  - after a successful Pulse worker add, if changed task-sets do not intersect current RMP active support, apply inactive-success cooldown;
  - if the add changes active support, do not apply the inactive-only cooldown;
  - the gate only controls future worker attempts and does not affect true-RC sanitize, impact filter, or normal RMP insertion.
- Added experimental profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`;
  - inherits 20-only pre-heuristic current probe, impact filter, low-budget, stop-after-first-negative, and `0.08s` post-call reserve;
  - adds active-support continuation gate with inactive cooldown `2`.
- Single-instance `mt20_greedy_apollo_01`:
  - reserve profile: wall `0.290116`, primal `1022.575388`, worker events `3`, added `2`;
  - active-gate profile: wall `0.224746`, primal `1030.002361`, worker events `1`, added `1`;
  - the gate cuts repeated inactive-only worker budget but also gives up the second inactive-only improvement.
- Gate output:
  - `BPC_future/results/sharded_pulse_phase7p_active_gate_gate_20260612/summary.json`
  - `BPC_future/logical_graph/run_reports/20260612_sharded_pulse_phase7p_active_support_continuation_gate_zh.md`
- Gate result:
  - 5-task full: worker events `0`, avg wall `0.025458 -> 0.024506`;
  - 10-task selected: worker events `0`, avg wall `0.117733 -> 0.117807`;
  - 20-task smoke: worker events `1`, added `1`, new task-set `1`, avg wall `0.209673 -> 0.228497`;
  - active row remains `mt20_greedy_apollo_01`, primal improves `1061.554044 -> 1030.002361`;
  - critical disagreement `0`, no certificate side effect.
- Conclusion:
  - active-support continuation gate is a safer experimental worker continuation guard than unrestricted follow-up probing;
  - it still does not establish wall-time ROI;
  - keep worker disabled by default and keep official certificate gate closed.

2026-06-13 Phase 7P follow-up active-support attribution:

- Added diagnostic-only RMP follow-up fields:
  - `worker_followup_changed_task_set_count`;
  - `worker_followup_active_changed_task_set_count`;
  - `worker_followup_inactive_changed_task_set_count`;
  - `worker_followup_changed_task_set_hash`;
  - `worker_followup_active_changed_task_set_hash`.
- Added ROI summary aliases:
  - `followup_worker_changed_task_set_count`;
  - `followup_worker_active_task_set_count`;
  - `followup_worker_inactive_task_set_count`;
  - `followup_worker_active_task_set_ratio`;
  - `pulse_worker_followup_*` variants.
- Semantics:
  - track only task-sets changed by the previous Pulse hidden-negative worker add;
  - on the next RMP solve, measure whether those task-sets appear in current active support;
  - clear the pending worker task-set list after logging;
  - no pricing/RMP/certificate behavior changes.
- Single-instance `mt20_greedy_apollo_01`:
  - profile `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`;
  - worker added `1` new task-set;
  - next RMP objective delta `-31.551683`;
  - follow-up active / changed task-set count `1 / 1`, ratio `1.0`;
  - follow-up pricing calls `2`, generated/evaluated `404 / 1535`;
  - last follow-up pricing state remains `INCOMPLETE_LIMIT`.
- Gate output:
  - `BPC_future/results/sharded_pulse_phase7p_followup_active_attribution_gate_20260613/summary.json`
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7p_followup_active_support_attribution_zh.md`
- Gate result:
  - 5-task full: worker events `0`, avg wall `0.025222 -> 0.024956`;
  - 10-task selected: worker events `0`, avg wall `0.117479 -> 0.117581`;
  - 20-task smoke: worker events `1`, added `1`, follow-up active / changed `1 / 1`, avg wall `0.209234 -> 0.224759`;
  - active row `mt20_greedy_apollo_01` improves primal `1061.554044 -> 1030.002361`;
  - critical disagreement `0`, no certificate side effect.
- Conclusion:
  - worker columns can enter active support and move the RMP objective;
  - follow-up exact pricing tail still remains;
  - current ROI gap is not simply caused by worker columns staying inactive;
  - do not expand worker budget or default-enable worker from this result.

2026-06-13 Phase 7P follow-up tail outcome classifier:

- Added diagnostic-only ROI classifier for pricing after worker add:
  - `followup_tail_outcome`;
  - `followup_negative_pricing_calls`;
  - `followup_incomplete_pricing_calls`;
  - `followup_min_best_rc`;
  - `pulse_worker_followup_*` aliases.
- Outcome classes include:
  - `no_worker_add`;
  - `no_followup_pricing`;
  - `followup_found_negative`;
  - `followup_certified_no_negative`;
  - `followup_incomplete_negative_best_rc`;
  - `followup_incomplete_near_zero_best_rc`;
  - `followup_incomplete_positive_best_rc`;
  - `followup_incomplete_unknown_best_rc`;
  - `followup_nonnegative_state_negative_best_rc`;
  - `followup_no_negative_observed`.
- Single-instance `mt20_greedy_apollo_01`:
  - worker added `1`;
  - follow-up active ratio `1.0`;
  - follow-up pricing calls `2`;
  - follow-up negative pricing calls `0`;
  - follow-up incomplete pricing calls `2`;
  - follow-up min best RC `0.034526`;
  - tail outcome `followup_incomplete_positive_best_rc`.
- Gate output:
  - `BPC_future/results/sharded_pulse_phase7p_tail_outcome_gate_20260613/summary.json`
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7p_followup_tail_outcome_classifier_zh.md`
- Gate result:
  - 5-task full: worker events `0`, all `no_worker_add`;
  - 10-task selected: worker events `0`, all `no_worker_add`;
  - 20-task smoke: one active worker row, outcome `followup_incomplete_positive_best_rc`;
  - critical disagreement `0`, no certificate side effect.
- Conclusion:
  - the active worker column enters support and moves objective, but follow-up pricing does not show residual negative best RC;
  - remaining tail is an incomplete/proof-tail issue, not evidence that Pulse should simply run longer;
  - next work should target legacy/profile final judge proof tail, profile-DP incomplete attribution, RMP stabilization/pool compression, or negative-result synthesis.

2026-06-13 Phase 7P failure-cooldown worker gate:

- Added opt-in config:
  - `journey_sharded_pulse_hidden_negative_worker_failure_cooldown_rounds`;
  - default `0`, nonnegative, no default benchmark effect.
- Semantics:
  - if optional Pulse worker returns no-column / incomplete / empty / duplicate-no-change, future worker attempts may be skipped for configured rounds;
  - if worker adds a changed column, failure cooldown is not applied;
  - skip reason is `failure_cooldown`;
  - this only skips optional worker calls and never participates in certificate / official lower-bound logic.
- Added ROI profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`;
  - 20-task only, same-iteration, RC threshold `-30.0`, follow-up reserve `0.4`, failure cooldown `2`.
- Verification:
  - focused tests cover helper semantics, profile registration, and opt-in config;
  - `BPCFutureTests`: `Ran 464 tests`, `OK (skipped=1)`;
  - `py_compile` and `git diff --check` passed.
- 20-only 1s smoke:
  - baseline avg wall `0.806675`;
  - RC + follow-up reserve avg wall `0.821722`, worker triggered `2`, added `1`;
  - failure cooldown avg wall `0.817907`, worker triggered `2`, added `1`.
- 5/10/20 short matrix:
  - 5-task worker triggered `0`;
  - 10-task worker triggered `0`;
  - 20-task worker triggered `0` under short budget.
- Conclusion:
  - failure cooldown is exact-safe and can prevent repeated no-change worker attempts;
  - it does not establish stable wall-time ROI;
  - worker remains opt-in, and official certificate gate remains closed.

2026-06-13 Phase 7P hard-tail fingerprint gate:

- Added opt-in current-probe fingerprint gate:
  - `journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled`;
  - `journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds`;
  - `journey_sharded_pulse_worker_current_probe_min_no_column_rounds`.
- Semantics:
  - when enabled, current-context Pulse probe is allowed only after either flat certificate-candidate rounds or no-column rounds reach threshold;
  - skip reason is `current_probe_hard_tail_fingerprint_missing`;
  - this only skips optional worker calls and never affects official certificate / lower-bound logic.
- Also fixed the pre-heuristic failure-cooldown path so empty worker results can trigger `failure_cooldown`.
- Added ROI profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint`;
  - 20-task only, same-iteration, RC threshold `-30.0`, follow-up reserve `0.4`, failure cooldown `2`, fingerprint thresholds `1 / 1`.
- Verification:
  - focused tests cover helper semantics, skip-before-call behavior, profile registration, and opt-in config;
  - `BPCFutureTests`: `Ran 466 tests`, `OK (skipped=1)`;
  - `py_compile` and `git diff --check` passed.
- 20-only 1s smoke:
  - baseline avg wall `0.806852`;
  - failure cooldown avg wall `0.821690`, worker triggered `2`, added `1`, changed `1`;
  - hard-tail fingerprint avg wall `0.816895`, worker triggered `1`, added `1`, changed `0`.
- 5/10/20 short matrix:
  - 5-task worker triggered `0`;
  - 10-task worker triggered `0`;
  - 20-task worker triggered `0`.
- Conclusion:
  - the fingerprint gate reduces one no-impact current probe;
  - it also removes the effective `mt20_greedy_apollo_01` worker impact observed in the looser profile;
  - this is not a production candidate;
  - repeated Pulse worker gate variants still do not establish stable ROI, so the next step should be negative-result synthesis and a pivot toward RMP / pool / legacy proof-tail optimization.

2026-06-13 Worker negative-result synthesis:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_worker_negative_result_synthesis_zh.md`.
- Scope:
  - active hidden-negative worker;
  - current-context probe;
  - impact filter / follow-up reserve / early-CG / failure-cooldown / hard-tail-fingerprint gate variants.
- Synthesis:
  - Pulse worker can safely return and add true-RC negative columns;
  - some rows improve under-budget primal and can enter active support;
  - small-scale no-regression mainly comes from gates disabling worker, not from worker speedup;
  - 20-task smokes do not show stable wall-time / proof-tail ROI;
  - stricter gates reduce invalid probes but also remove useful worker impact.
- Decision:
  - stop expanding active worker gate-stacking;
  - do not default-enable worker;
  - do not increase worker time limit;
  - keep official certificate gate closed;
  - pivot next optimization work toward RMP stabilization, column pool compression, or legacy final-judge proof-tail optimization.
- Boundary:
  - this is a negative result for the active worker sub-route only;
  - it is not the full final condition B yet, because refinement/resume no-ROI evidence is not complete.

2026-06-13 Phase 7U RMP / column-pool structure diagnostics:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7u_pool_structure_diagnostics_zh.md`.
- Added diagnostic-only driver event:
  - `journey_pool_structure_diagnostics`.
- Added helper:
  - `_journey_pool_structure_diagnostics(...)`.
- Logged fields include:
  - pool journey / unique task-set counts;
  - duplicate task-set pressure;
  - task-set size histogram;
  - active journey / active task-set counts;
  - active duplicate and fractional support;
  - active task-set hash and task union size.
- ROI calibration summary now exports:
  - `pool_diag_events`;
  - `pool_journeys_last`;
  - `pool_unique_task_sets_last`;
  - `pool_duplicate_task_sets_last`;
  - `pool_duplicate_task_set_ratio_last/max`;
  - `pool_active_journeys_last`;
  - `pool_active_task_sets_last`;
  - `pool_active_fractional_ratio_last/max`;
  - `pool_active_task_set_hash_last`.
- Verification:
  - focused tests for driver diagnostics and ROI summary extraction passed;
  - `BPCFutureTests`: `Ran 468 tests`, `OK (skipped=1)`;
  - very_small ROI smoke produced the new pool fields in `summary.json`.
- Boundary:
  - diagnostic-only;
  - no RMP model changes;
  - no pricing / worker / certificate behavior changes.
- Next use:
  - compare baseline vs strongest 20-only worker profiles to decide whether the blocker is column-pool/RMP degeneration or legacy proof-tail.

2026-06-13 Phase 7U diagnostic matrix:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7u_pool_diagnostics_matrix_zh.md`.
- Ran diagnostic-only outputs:
  - `BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_matrix_20260613/summary.json`;
  - `BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_20_smoke_1s_20260613/summary.json`.
- 5/10 gate:
  - apollo5 / tranq5 / apollo10 / tranq10_09 had worker events `0`;
  - official result unchanged;
  - critical disagreement `0`.
- 20-task findings:
  - `pool_duplicate_task_set_ratio_last=0.0` for all rows;
  - `mt20_greedy_apollo_01` worker added 1 new task-set;
  - pool unique task-sets changed `166 -> 167`;
  - RMP objective moved by `-171.465431`;
  - active support hash changed;
  - follow-up still returned `followup_found_negative`;
  - average 20-task wall still did not improve.
- Interpretation:
  - active worker columns can be absorbed by RMP;
  - current failure is not primarily task-set duplicate pool pressure;
  - worker does not replace the residual ordinary/exact pricing negative tail.
- Next recommended phase:
  - Phase 7V residual pricing / legacy tail attribution;
  - compare worker changed task-sets against follow-up negative task-sets and true-RC decomposition before changing algorithms.

2026-06-13 Phase 7V residual pricing / legacy tail attribution:

- Added diagnostic-only task-set sample fields to `journey_pricing`:
  - `negative_journey_task_set_count`;
  - `negative_journey_task_set_hash`;
  - `negative_journey_task_set_samples`;
  - `negative_journey_task_set_sample_count`;
  - `negative_journey_task_set_samples_truncated`.
- Added capped task-set samples to `journey_column_addition`:
  - requested / changed / new / replacement task-set samples;
  - active / inactive changed task-set samples when active support is available.
- Extended ROI calibration summary with residual follow-up attribution:
  - first follow-up negative task-set hash/sample/count;
  - overlap and Jaccard to worker changed task-sets;
  - relation class: `same_task_set`, `overlapping_task_set`, `disjoint_task_set`, or `unknown`.
- Verification:
  - py_compile for changed files passed;
  - focused log/ROI attribution tests passed;
  - `BPCFutureTests`: `Ran 469 tests`, `OK (skipped=1)`;
  - short opt-in 20-task smoke wrote the new JSONL fields and kept official result unchanged.
- Boundary:
  - diagnostic-only;
  - no RMP model changes;
  - no pricing/worker trigger changes;
  - no certificate or official lower-bound effect.
- Current interpretation:
  - Phase 7U showed worker columns can enter the pool and move RMP, but do not remove the residual pricing tail;
  - Phase 7V now makes the residual tail classifiable by task-set overlap before any further algorithm changes.
- Next recommended use:
  - re-run the strongest 20-only worker profiles with Phase 7V fields;
  - if residual negatives are mostly disjoint/new, worker is not covering the ordinary negative tail;
  - if residual negatives mostly overlap worker task-sets, investigate replacement quality, start-time variants, and column impact filters before increasing worker budget.

2026-06-13 Phase 7W residual tail matrix:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7w_residual_tail_matrix_zh.md`.
- Updated ROI follow-up attribution:
  - follow-up events are now all JSONL records after the first worker addition event;
  - this includes same-iteration heuristic / exact pricing after `continue_same_iteration_after_add`.
- Ran outputs:
  - `BPC_future/results/sharded_pulse_phase7w_residual_tail_matrix_20260613/summary.json`;
  - `BPC_future/results/sharded_pulse_phase7w_residual_tail_apollo_probe_20260613/summary.json`.
- Narrow 20-task matrix:
  - `tranq20_01`: worker did not trigger;
  - `mt20_greedy_tranq_01`: worker did not trigger;
  - `mt20_greedy_apollo_01`: worker added 1 new inactive task-set `[6,19]`; follow-up under low cap was profile-DP incomplete, no returned residual negative.
- Deeper Apollo probe:
  - worker added `[6,19]`;
  - next RMP objective moved by about `-169.988908`;
  - under-budget primal improved from `923.116819` to `891.565136`;
  - follow-up heuristic negatives were `[5,8,15]`, `[5,12,18]`, `[12,16,17]`;
  - first residual relation to worker was `disjoint_task_set`.
- Interpretation:
  - worker can add a true-RC negative column and RMP can absorb it;
  - residual ordinary pricing tail is not same-task-set replacement pressure;
  - the current worker is missing disjoint new negative task-set families that ordinary heuristic later finds;
  - this argues against increasing worker budget or enabling worker by default.
- Boundary:
  - diagnostic / opt-in only;
  - no certificate effect;
  - no official lower bound from Pulse;
  - no production default change.
- Next recommended decision:
  - stop active-worker gate stacking unless diagnosing worker candidate ordering / task-set coverage;
  - otherwise pivot toward ordinary pricing/profile-DP tail, RMP stabilization, column impact filter, or legacy final-judge proof-tail optimization.

2026-06-13 Phase 7X worker ordering / task-set coverage diagnostic:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7x_worker_ordering_coverage_zh.md`.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7x_worker_ordering_coverage_20260613/summary.json`.
- Compared:
  - natural worker profile;
  - `reduced_cost_proxy` ordered worker profile.
- Result on `mt20_greedy_apollo_01`:
  - natural worker first task-set: `[6,19]`;
  - ordered worker first task-set: `[6,19]`;
  - ordinary follow-up first residual negative: `[5,8,15]`;
  - relation remained `disjoint_task_set`;
  - recursions stayed `115`.
- Interpretation:
  - current task ordering does not fix worker coverage;
  - the worker is missing a disjoint ordinary-negative family, not merely producing a weak same-task-set replacement;
  - continuing active-worker budget/gate stacking is not justified.
- Boundary:
  - opt-in diagnostic only;
  - no certificate effect;
  - no production default change.
- Next recommended decision:
  - stop expanding active worker as the main route;
  - if more Pulse work is needed, first diagnose candidate-universe mismatch with ordinary heuristic;
  - otherwise pivot toward ordinary pricing/profile-DP tail, RMP stabilization, column impact filtering, or legacy final-judge proof-tail optimization.

2026-06-13 Phase 7Y worker coverage-scan diagnostic:

- Added opt-in ROI calibration profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`.
- Profile boundary:
  - 20-task only;
  - current-context, pre-heuristic, impact-filtered hidden-negative worker;
  - same small probe budget as the low-budget current-probe family;
  - explicitly sets `journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative=False`;
  - limits active diagnostic to early CG with `journey_sharded_pulse_hidden_negative_worker_max_cg_iter=1`;
  - not in default `PROFILE_ORDER`;
  - no certificate effect and no production default change.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7y_worker_coverage_scan_20260613/summary.json`.
- Compared on `mt20_greedy_apollo_01`:
  - baseline;
  - early-stop worker profile `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`;
  - coverage-scan profile with early stop disabled.
- Result:
  - early-stop worker returned `[6,19]`, recursions `115`, worker time about `0.032s`;
  - coverage-scan worker still returned only `[6,19]`, recursions `245`, worker time about `0.073s`;
  - coverage-scan time-window pruning increased from `5930` to `12666`;
  - ordinary follow-up first residual negative remained `[5,8,15]`;
  - relation to worker remained `disjoint_task_set`;
  - coverage-scan did not return the ordinary residual negative family.
- Interpretation:
  - the current worker coverage gap is not fixed by merely disabling `stop_after_first_negative`;
  - the issue is more likely a candidate-universe / search-path mismatch with ordinary heuristic, or a later filter / context interaction, than simple first-negative early exit;
  - active-worker gate stacking and simple worker budget increases are not justified.
- Boundary:
  - opt-in diagnostic only;
  - no certificate effect;
  - all worker additions still use normal add-column path;
  - no official lower bound from Pulse.
- Next recommended decision:
  - stop pushing active worker as the primary production route until candidate-universe mismatch is explained;
  - if continuing Pulse diagnostics, compare transition Pulse candidate universe directly against ordinary heuristic/profile-DP on the same dual/cut/forbidden context;
  - otherwise pivot to ordinary pricing/profile-DP tail, RMP stabilization, stronger column impact filtering, or legacy final-judge proof-tail optimization.

2026-06-13 Phase 7Z worker no-ROI-gate coverage diagnostic:

- Added summary fields:
  - `worker_shards_total`;
  - `worker_shards_certified`;
  - `worker_shards_incomplete`;
  - `worker_shards_negative`;
  - `worker_shards_refined`;
  - `worker_low_roi_shards`;
  - matching `pulse_worker_shards_*` / `pulse_worker_low_roi_shards` fields.
- Added opt-in ROI calibration profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`.
- Profile boundary:
  - 20-task only;
  - current-context, pre-heuristic, impact-filtered hidden-negative worker;
  - same small probe budget as coverage-scan;
  - `stop_after_first_negative=False`;
  - `journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False`;
  - `journey_sharded_pulse_hidden_negative_worker_max_cg_iter=1`;
  - not in default `PROFILE_ORDER`;
  - no certificate effect and no production default change.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7z_worker_no_roi_gate_coverage_20260613/summary.json`.
- Compared on `mt20_greedy_apollo_01`:
  - baseline;
  - early-stop worker profile;
  - coverage-scan profile;
  - coverage no-ROI-gate profile.
- Result:
  - early-stop worker: returned `[6,19]`, `worker_shards_total=2`, `worker_shards_negative=1`;
  - coverage-scan: returned `[6,19]` and `[7,19]` in this run, `worker_shards_total=20`, `worker_shards_incomplete=17`, `worker_shards_negative=2`;
  - coverage no-ROI-gate: returned only `[6,19]`, `worker_shards_total=20`, `worker_shards_incomplete=18`, `worker_shards_negative=1`;
  - ordinary follow-up first residual negative remained `[5,8,15]`;
  - relation to worker remained `disjoint_task_set`;
  - no profile returned the ordinary residual negative family.
- Interpretation:
  - shard ROI gate alone is not the reason `[5,8,15]` is missed;
  - disabling early stop and disabling ROI gate both leave most first-task shards incomplete under the same small budget;
  - current worker coverage gap is more likely due to incomplete Pulse exploration under small budgets or a candidate-universe mismatch with ordinary heuristic/profile-DP, not a single gate setting;
  - active-worker gate stacking and simple worker budget increases remain unjustified.
- Boundary:
  - opt-in diagnostic only;
  - no certificate effect;
  - all worker additions still use normal add-column path;
  - no official lower bound from Pulse;
  - default benchmark behavior unchanged.
- Next recommended decision:
  - stop active worker production tuning;
  - if Pulse diagnostics continue, replay the exact ordinary residual task-set family under the same context or compare ordinary heuristic/profile-DP candidate generation against transition Pulse state semantics;
  - otherwise pivot to ordinary pricing/profile-DP tail, RMP stabilization, column impact filtering, or legacy final-judge proof-tail optimization.

2026-06-13 Phase 7AA residual sequence / signature diagnostics:

- Added journey-pricing log fields for returned negative journeys:
  - `negative_journey_signature_count`;
  - `negative_journey_signature_hash`;
  - `negative_journey_signature_samples`;
  - `negative_journey_sequence_samples`;
  - sample counts and truncation flags.
- Added ROI summary fields:
  - `worker_negative_journey_sequence_samples`;
  - `worker_negative_journey_signature_samples`;
  - `followup_first_negative_sequence`;
  - `followup_first_negative_signature_sample`;
  - matching `pulse_worker_followup_*` aliases.
- Boundary:
  - logging and summary only;
  - capped samples;
  - no pricing, pool, certificate, bound, or worker-trigger semantic changes.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7aa_residual_sequence_diagnostics_20260613/summary.json`.
- Result on `mt20_greedy_apollo_01`:
  - worker negative task-set `[6,19]` has sequence `[6,19]`;
  - worker signature sample starts at `241.411702`;
  - ordinary follow-up first residual task-set `[5,8,15]` has sequence `[8,15,5]`;
  - ordinary follow-up first residual signature sample starts at `0.0`;
  - ordinary follow-up second residual task-set `[5,12,18]` has sequence `[12,18,5]`, start `3.086313`;
  - relation to worker remains `disjoint_task_set`.
- Interpretation:
  - the residual coverage gap can now be localized to concrete first-task shard / sequence families, not just unordered task sets;
  - current worker returned a late-start `[6,19]` family, while ordinary heuristic found early-start `[8,15,5]` and `[12,18,5]` families;
  - this supports same-context targeted replay of those residual signatures before further worker tuning.
- Boundary:
  - opt-in diagnostic evidence only;
  - no certificate effect;
  - no official lower bound from Pulse;
  - default benchmark behavior unchanged.
- Next recommended decision:
  - implement or run a same-context targeted replay diagnostic for ordinary residual sequence `[8,15,5]` under the exact dual/cut/forbidden context where ordinary heuristic found it;
  - determine whether transition Pulse can materialize and score that journey if forced into the relevant first-task shard;
  - only after that decide whether the issue is search-budget coverage, start-time/candidate-domain mismatch, path-option enumeration mismatch, or filtering.

2026-06-13 Phase 7AB residual Pulse leaf replay diagnostic:

- Added opt-in config:
  - `journey_pulse_residual_replay_diagnostics_enabled`;
  - `journey_pulse_residual_replay_diagnostics_max_journeys`.
- Enabled it only in coverage diagnostic profiles:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`.
- Added diagnostic event:
  - `journey_pulse_residual_replay_diagnostic`.
- Replay contract:
  - takes returned ordinary `JourneyColumn.trips`;
  - reconstructs arc options from `trip.arc_option_ids`;
  - calls Phase 3A `materialize_pulse_leaf_candidate`;
  - recomputes true RC with current true duals and cuts;
  - logs signature/task-set equality and RC delta;
  - does not mutate pool, pricing result, certificate state, or official lower bound.
- Added ROI summary fields:
  - `pulse_residual_replay_events`;
  - `pulse_residual_replay_checked`;
  - `pulse_residual_replay_materialized`;
  - `pulse_residual_replay_negative`;
  - `pulse_residual_replay_rc_mismatch_count`;
  - `pulse_residual_replay_signature_mismatch_count`;
  - `pulse_residual_replay_first_status`;
  - `pulse_residual_replay_first_sequence`;
  - `pulse_residual_replay_first_original_true_rc`;
  - `pulse_residual_replay_first_replay_true_rc`;
  - `pulse_residual_replay_first_rc_delta`.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7ab_residual_replay_diagnostics_20260613/summary.json`.
- Result on `mt20_greedy_apollo_01`:
  - ordinary follow-up sequence `[8,15,5]` replay status: `materialized`;
  - original true RC: `-138.437225`;
  - replay true RC: `-138.437225`;
  - RC delta: `0.0`;
  - signature mismatch count: `0`;
  - ordinary follow-up sequence `[12,18,5]` also replayed as materialized with RC delta `0.0`;
  - replayed journeys remained true-RC negative.
- Interpretation:
  - the residual family is compatible with Pulse leaf materialization semantics;
  - the true-dual/cut context used for replay matches ordinary heuristic RC;
  - the current mismatch is not caused by `evaluate_timed_trip` / `make_journey` / manual RC materialization;
  - the problem is now localized to transition DFS / shard scheduling / small-budget exploration not reaching those early-start residual sequence families.
- Boundary:
  - opt-in diagnostics only;
  - no certificate effect;
  - no official lower-bound effect;
  - default benchmark behavior unchanged.
- Next recommended decision:
  - instrument transition Pulse shard-level sequence reachability for first-task shard `8` / sequence `[8,15,5]`;
  - determine whether it is pruned by time/resource/return/bound/archive, skipped by shard budget ordering, or simply not reached before the recursion/time cap;
  - do not increase production worker budget or enable worker by default before that reachability evidence exists.

2026-06-13 Phase 7AC target-sequence transition reachability diagnostic:

- Added opt-in transition Pulse target-sequence diagnostics:
  - `journey_pulse_target_sequence_diagnostics_enabled`;
  - `journey_pulse_target_sequence_diagnostics_sequence`;
  - worker override keys under `journey_sharded_pulse_hidden_negative_worker_*`;
  - audit override keys under `journey_sharded_pulse_audit_*`.
- The diagnostic records, without changing search semantics:
  - target sequence;
  - max reached prefix length;
  - whether the target sequence completed/materialized/was true-RC negative;
  - first blocked reason / blocked prefix / blocked next task;
  - transition attempts / accepted transitions;
  - prune reason counts.
- The diagnostic is constrained to the target first-task shard:
  - for `[8,15,5]`, only first-task shard `8` contributes target reachability data;
  - non-target first-task shards are ignored, so later-sortie attempts from other parents do not pollute the first-task coverage diagnosis.
- Added worker / pricing log fields:
  - `pulse_target_sequence_*`;
  - `pulse_worker_target_sequence_*`.
- Added ROI summary fields:
  - `worker_target_sequence`;
  - `worker_target_sequence_reached_prefix_len`;
  - `worker_target_sequence_completed`;
  - `worker_target_sequence_materialized`;
  - `worker_target_sequence_negative`;
  - `worker_target_sequence_blocked_reason`;
  - `worker_target_sequence_blocked_prefix`;
  - `worker_target_sequence_blocked_next_task`;
  - `worker_target_sequence_transition_attempts`;
  - `worker_target_sequence_transition_accepted`;
  - `worker_target_sequence_prune_reason_counts`.
- Enabled target sequence diagnostics only for coverage diagnostic profiles:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`;
  - target sequence: `8,15,5`.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7ac_target_sequence_reachability_20260613_rerun/summary.json`.
- Result on `mt20_greedy_apollo_01`:
  - coverage-scan worker still returned sequence `[6,19]`;
  - ordinary follow-up first residual sequence remained `[8,15,5]`;
  - target sequence: `[8,15,5]`;
  - `worker_target_sequence_reached_prefix_len = 0`;
  - `worker_target_sequence_transition_attempts = 0`;
  - `worker_target_sequence_transition_accepted = 0`;
  - `worker_target_sequence_materialized = False`;
  - `worker_target_sequence_blocked_reason = deadline`;
  - no target prune reason counts were recorded in the target first-task shard.
- Interpretation:
  - within the target first-task shard scope, `[8,15,5]` was not pruned by time-window, energy, return, bound, archive, or branch logic;
  - the worker reached the global deadline before making even the first target transition attempt in first-task shard `8`;
  - the current residual coverage gap is therefore best explained by shard scheduling / per-shard budget allocation under the current small worker budget, not by Pulse leaf materialization or transition feasibility misclassification.
- Boundary:
  - opt-in diagnostics only;
  - no certificate effect;
  - no official lower-bound effect;
  - no default benchmark behavior change.

2026-06-13 Phase 7AD target first-task shard priority diagnostic:

- Added an opt-in target first-task priority switch:
  - `journey_pulse_target_first_task_priority_enabled`;
  - `journey_pulse_target_first_task_priority_sequence`;
  - worker override keys under `journey_sharded_pulse_hidden_negative_worker_*`;
  - audit override keys under `journey_sharded_pulse_audit_*`.
- The switch only reorders required first-task shards:
  - target first task is moved to the front;
  - all other first-task shards remain required;
  - no shard is filtered out;
  - no certificate / lower-bound semantics are changed.
- Added ROI diagnostic profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`;
  - enabled only for 20-task coverage diagnostics;
  - target sequence remains `8,15,5`;
  - target first-task priority sequence is also `8,15,5`.
- Added log / summary fields:
  - `pulse_target_first_task_priority_enabled`;
  - `pulse_target_first_task_priority_sequence`;
  - `pulse_worker_target_first_task_priority_enabled`;
  - `pulse_worker_target_first_task_priority_sequence`;
  - `worker_target_first_task_priority_enabled`;
  - `worker_target_first_task_priority_sequence`.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7ad_target_shard_priority_20260613/summary.json`.
- Result on `mt20_greedy_apollo_01` with the same narrow budget:
  - old coverage-scan:
    - worker returned one journey, sequence `[6,19]`;
    - ordinary follow-up first residual sequence remained `[8,15,5]`;
    - target sequence reached prefix length `0`;
    - target transition attempts `0`;
    - blocked reason `deadline`.
  - target-priority coverage:
    - priority flag was enabled and sequence was `[8,15,5]`;
    - worker returned two journeys, sequences `[8,4,18]` and `[8,4]`;
    - target sequence reached prefix length increased to `1`;
    - target transition attempts / accepted transitions were both `1`;
    - target sequence still did not complete or materialize;
    - blocked reason remained `deadline`.
- Interpretation:
  - first-task shard priority successfully moves the worker into shard `8` before the deadline;
  - this fixes the Phase 7AC symptom where shard `8` was not entered at all;
  - the residual coverage gap for `[8,15,5]` is now inside shard `8`, likely task/transition ordering or per-shard budget, not first-task shard scheduling alone.
- Boundary:
  - opt-in coverage diagnostic only;
  - no production default enable;
  - no certificate effect;
  - no official lower-bound effect.

2026-06-13 Phase 7AE target transition priority diagnostic:

- Added an opt-in target transition priority switch:
  - `target_transition_priority_enabled`;
  - `target_transition_priority_sequence`;
  - pricing config keys `journey_pulse_target_transition_priority_*`;
  - worker override keys under `journey_sharded_pulse_hidden_negative_worker_*`;
  - audit override keys under `journey_sharded_pulse_audit_*`.
- The switch only reorders same-state transition candidates:
  - if the current sortie sequence is a prefix of the target sequence, the next target task is moved to the front;
  - all other candidate tasks remain available;
  - no transition is filtered;
  - no certificate / official lower-bound semantics are changed.
- Added ROI diagnostic profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority`;
  - enabled only for 20-task coverage diagnostics;
  - target diagnostics sequence is `8,15,5`;
  - target first-task priority sequence is `8,15,5`;
  - target transition priority sequence is `8,15,5`.
- Added log / summary fields:
  - `pulse_target_transition_priority_enabled`;
  - `pulse_target_transition_priority_sequence`;
  - `pulse_worker_target_transition_priority_enabled`;
  - `pulse_worker_target_transition_priority_sequence`;
  - `worker_target_transition_priority_enabled`;
  - `worker_target_transition_priority_sequence`.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7ae_target_transition_priority_20260613/summary.json`.
- Result on `mt20_greedy_apollo_01` with the same narrow budget:
  - old coverage-scan:
    - target sequence reached prefix length `0`;
    - target transition attempts `0`;
    - blocked reason `deadline`.
  - target first-task priority:
    - target sequence reached prefix length `1`;
    - target transition attempts / accepted transitions were `1 / 1`;
    - blocked reason `deadline`.
  - target transition priority:
    - target sequence reached prefix length increased to `2`;
    - target transition attempts / accepted transitions were `9 / 3`;
    - worker returned four journeys with prefix `[8,15]`:
      - `[8,15,18,4]`;
      - `[8,15,18]`;
      - `[8,15,4]`;
      - `[8,15]`;
    - target sequence still did not complete or materialize;
    - blocked reason became `time_window`;
    - blocked prefix was `[8,15]`;
    - blocked next task was `5`;
    - target prune reason counts recorded `time_window = 6`.
- Interpretation:
  - target task ordering now reaches the residual family prefix `[8,15]`;
  - the remaining gap is path-specific: the transition states reached for `[8,15]` prune task `5` by time window;
  - because Phase 7AB replay proved `[8,15,5]` is materializable under the same true-dual context, the next likely issue is arc-option / start-time path ordering within the target prefix, not first-task or next-task scheduling.
- Boundary:
  - opt-in coverage diagnostic only;
  - no production default enable;
  - no certificate effect;
  - no official lower-bound effect.

2026-06-13 Phase 7AF target path-option / start-time diagnostics:

- Added opt-in target path diagnostics to transition Pulse:
  - `target_path_diagnostics_enabled`;
  - `target_path_diagnostics_max_samples`;
  - pricing config keys `journey_pulse_target_path_diagnostics_*`;
  - worker override keys under `journey_sharded_pulse_hidden_negative_worker_*`;
  - audit override keys under `journey_sharded_pulse_audit_*`.
- The diagnostics are capped and read-only:
  - prefix samples record `prefix`, `arc_ids`, `start_lb`, `start_ub`, `offset`, and `current_time`;
  - blocked transition samples record `reason`, `prefix`, `next`, `arc_ids`, `option`, interval values, and reason-specific details;
  - no search order, pruning rule, candidate return, certificate, or official lower-bound semantics are changed.
- Added ROI diagnostic profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic`;
  - enabled only for 20-task coverage diagnostics;
  - inherits target first-task and target transition priority for `8,15,5`;
  - enables target path diagnostics with sample cap `12`.
- Added log / summary fields:
  - `pulse_target_path_diagnostics_enabled`;
  - `pulse_target_path_prefix_samples`;
  - `pulse_target_path_blocked_samples`;
  - `pulse_worker_target_path_diagnostics_enabled`;
  - `pulse_worker_target_path_prefix_samples`;
  - `pulse_worker_target_path_blocked_samples`;
  - `worker_target_path_diagnostics_enabled`;
  - `worker_target_path_prefix_samples`;
  - `worker_target_path_blocked_samples`.
- Ran output:
  - `BPC_future/results/sharded_pulse_phase7af_target_path_diagnostics_20260613/summary.json`.
- Result on `mt20_greedy_apollo_01` with the same narrow budget:
  - target transition profile:
    - target sequence reached prefix length `2`;
    - blocked at `[8,15] -> 5` by `time_window`;
    - no path samples because path diagnostics were disabled.
  - target path diagnostic profile:
    - target sequence reached prefix length `2`;
    - blocked at `[8,15] -> 5` by `time_window`;
    - prefix samples included:
      - `prefix=8; arc_ids=0->8:low_risk:2; start_ub=11.880447; offset=260.843506`;
      - `prefix=8,15; arc_ids=0->8:low_risk:2|8->15:low_risk:2; offset=296.942537`;
      - `prefix=8,15; arc_ids=0->8:low_risk:2|8->15:low_time:0; offset=296.068747`.
    - blocked samples show attempts for:
      - `15->5:low_risk:2`;
      - `15->5:low_time:0`;
      - `15->5:low_energy:1`;
    - all blocked samples had negative `next_start_ub` under the reached prefix state.
- Interpretation:
  - Phase 7AB residual replay proved the feasible target signature uses:
    - `0->8:low_time:0`;
    - `8->15:low_risk:2`;
    - `15->5:low_risk:2`;
    - `5->0:low_time:0`;
    - start `0.0`.
  - The Phase 7AF worker path samples reached `[8,15]` only through `0->8:low_risk:2` before the cap/deadline;
  - with that slower first arc, `15 -> 5` is time-window infeasible for all sampled options;
  - the remaining coverage gap is therefore best explained by arc-option ordering inside the target prefix, not by first-task shard ordering or next-task ordering.
- Boundary:
  - opt-in diagnostics only;
  - no production default enable;
  - no certificate effect;
  - no official lower-bound effect.
- Next recommended decision:
  - do not increase global worker budget or open certificate gate yet;
  - add a narrow shard-scheduling / target-shard priority experiment that moves residual/high-dual target first-task shards earlier under diagnostic profiles;
  - compare whether first-task shard `8` starts before deadline and whether `[8,15,5]` is then materialized or safely pruned.

2026-06-13 Phase 7AG target arc-option priority diagnostic:

- Added opt-in target arc-option priority to transition Pulse:
  - `target_arc_option_priority_enabled`;
  - `target_arc_option_priority_sequence`;
  - pricing config keys `journey_pulse_target_arc_option_priority_*`;
  - worker override keys under `journey_sharded_pulse_hidden_negative_worker_*`;
  - audit override keys under `journey_sharded_pulse_audit_*`.
- The switch only reorders path options on the target prefix:
  - if the current sortie sequence is a prefix of the target sequence, the configured option id for that edge is moved to the front;
  - all other path options remain available;
  - no task, path option, shard, or column is filtered;
  - no certificate / official lower-bound semantics are changed.
- Added ROI diagnostic profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority`;
  - enabled only for 20-task coverage diagnostics;
  - target diagnostics sequence is `8,15,5`;
  - target first-task priority sequence is `8,15,5`;
  - target transition priority sequence is `8,15,5`;
  - target arc-option priority sequence is:
    - `0->8:low_time:0`;
    - `8->15:low_risk:2`;
    - `15->5:low_risk:2`;
    - `5->0:low_time:0`;
  - target path diagnostics remain enabled with sample cap `12`.
- Added log / summary fields:
  - `pulse_target_arc_option_priority_enabled`;
  - `pulse_target_arc_option_priority_sequence`;
  - `pulse_worker_target_arc_option_priority_enabled`;
  - `pulse_worker_target_arc_option_priority_sequence`;
  - `worker_target_arc_option_priority_enabled`;
  - `worker_target_arc_option_priority_sequence`.
- Ran outputs:
  - `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_20260613/summary.json`;
  - `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_budget_probe_20260613/summary.json`.
- Result on `mt20_greedy_apollo_01`:
  - 7AF target path diagnostic:
    - target sequence reached prefix length `2`;
    - prefix samples started with `0->8:low_risk:2`;
    - `[8,15] -> 5` was pruned by `time_window`;
    - worker returned / added four journeys.
  - 7AG target arc-option priority with the same narrow budget:
    - target arc-option priority was enabled;
    - prefix sample changed to `prefix=8;arc_ids=0->8:low_time:0`;
    - target sequence reached prefix length only `1`;
    - blocked reason was `deadline`;
    - worker returned / added zero journeys.
  - 7AG 1.0s diagnostic budget probe:
    - still reached only prefix length `1`;
    - blocked reason remained `deadline`;
    - worker returned / added zero journeys.
- Interpretation:
  - the arc-option priority plumbing works and can force the residual replay option `0->8:low_time:0` to the front;
  - it did not improve coverage of `[8,15,5]` under the narrow Apollo20 diagnostic budgets;
  - this is not a worker ROI positive signal and does not justify opening certificate effect or default worker usage.
- Boundary:
  - opt-in coverage diagnostic only;
  - no production default enable;
  - no certificate effect;
  - no official lower-bound effect.
- Next recommended decision:
  - do not keep stacking active-worker gates solely to chase `[8,15,5]`;
  - use the 7AB replay plus 7AF/7AG path samples for a local transition/replay comparator if continuing diagnostics;
  - otherwise pause worker-gate expansion and return to broader ROI decisions.

2026-06-13 Phase 7AH active-worker closure audit:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase7ah_active_worker_closure_zh.md`.
- This phase makes no solver-code change.
- Evidence reviewed:
  - `phase7o_worker_roi_ab_expanded`;
  - `phase7o_delayed_lowcap_5_10_gate`;
  - `phase7o_delayed_lowcap_20_smoke`;
  - `phase7p_failure_cooldown_gate_20_smoke_1s`;
  - `phase7z_worker_no_roi_gate_coverage`;
  - `phase7ag_target_arc_option_priority`;
  - Phase 7J refinement report and Phase 7U-7AG diagnostics.
- Closure decision:
  - stop expanding `current-context Pulse hidden-negative active worker`;
  - do not increase worker budget;
  - do not keep stacking active-worker trigger / cooldown / follow-up reserve gates;
  - do not keep writing target-specific worker ordering gates for `[8,15,5]`;
  - do not open official certificate gate from this line of evidence;
  - do not enable Pulse worker by default.
- Rationale:
  - original current-probe worker can add true-RC negative columns but slows 5/10/20 average wall time;
  - delayed / low-cap gates protect 5-task mainly by disabling worker, while 10-task remains slower when worker triggers;
  - follow-up reserve and failure cooldown remain slower than baseline on 20-task smoke averages;
  - coverage scan / no-ROI gate do not cover the residual `[5,8,15]` / `[8,15,5]` family;
  - target diagnostics show exact coverage gaps but do not convert into ROI;
  - refinement is exact-safe but does not yet prove production incomplete reduction, and proof-closed resume is not implemented.
- Final-condition audit:
  - active-worker subroute satisfies the negative ROI evidence;
  - the full objective is not complete because final condition B still lacks proof-closed resume / full proof-route no-ROI evidence;
  - no correctness blocker has been found.
- Recommended next line:
  - pivot away from active Pulse worker gate-stacking;
  - investigate RMP stabilization, column-pool compression, or legacy final-judge proof-tail optimization;
  - only implement proof-closed resume if the explicit goal is to complete final condition B for the proof route.

2026-06-13 Phase 8A ROI pivot classifier:

- Added read-only summary classifier to `run_sharded_pulse_roi_calibration.py`:
  - `pivot_recommendation_class`;
  - `pivot_recommendation_reason`.
- Classifier priority:
  - `correctness_blocker`;
  - `profile_dp_state_cap`;
  - `profile_dp_incomplete`;
  - `residual_disjoint_negative`;
  - `residual_overlapping_negative`;
  - `pool_duplicate_pressure`;
  - `rmp_fractional_active_pressure`;
  - `worker_column_impact_unclear`;
  - `no_clear_pivot_signal`.
- This is summary-only:
  - no solver behavior changes;
  - no worker trigger changes;
  - no pricing changes;
  - no certificate / official lower-bound changes.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8a_roi_pivot_classifier_zh.md`.
- Verification:
  - `py_compile` for ROI script and tests passed;
  - focused ROI profile/field and classifier tests passed;
  - very_small smoke wrote the new fields to summary JSON / CSV.
- Offline reclassification of existing summaries:
  - `phase7u_pool_diagnostics_matrix`:
    - mostly `no_clear_pivot_signal`, plus 20-task `rmp_fractional_active_pressure`;
  - `phase7w_residual_tail_matrix`:
    - `profile_dp_state_cap` appears for worker follow-up on `mt20_greedy_apollo_01`;
  - `phase7w_residual_tail_apollo_probe` and `phase7z_worker_no_roi_gate_coverage`:
    - classify worker follow-up as `residual_disjoint_negative`;
  - `phase7ag_target_arc_option_priority`:
    - target path diagnostic still leaves residual overlapping negative / no clear worker impact.
- Interpretation:
  - pool duplicate pressure is not the primary current signal;
  - active fractional pressure and profile-DP/follow-up proof tail are stronger pivot candidates;
  - this supports stopping active Pulse worker gate-stacking and moving to legacy/profile-DP proof-tail or RMP stabilization diagnostics.

2026-06-13 Phase 8B profile-DP cap sensitivity:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8b_profile_dp_cap_sensitivity_zh.md`.
- No solver-code change.
- Ran narrow probes on `mt20_greedy_apollo_01`:
  - `pricing_max_dp_states=1000`;
  - `pricing_max_dp_states=5000`;
  - short `time_limit=0.3`;
  - diagnostic `time_limit=1.5`;
  - profiles `baseline` and `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`.
- Outputs:
  - `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap1000_short_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap5000_short_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap1000_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap5000_probe_20260613`.
- Observations:
  - short cap `0.3s`:
    - increasing cap changed pricing from `INCOMPLETE_LIMIT` to `FOUND_NEGATIVE`;
    - it did not give stable wall / primal ROI.
  - `1.5s`:
    - no follow-up `profile_dp_state_cap` incomplete was reproduced;
    - worker follow-up remained `residual_disjoint_negative`;
    - increasing cap raised search effort / wall time.
- Decision:
 - do not treat larger `journey_pricing_max_dp_states` as a production fix;
 - if continuing proof-tail work, diagnose profile-DP state explosion structurally instead of only raising cap;
  - RMP stabilization / active fractional degeneracy remains an equally strong or stronger pivot candidate.

2026-06-13 Phase 8C profile-DP state attribution:

- Added read-only profile-DP state-explosion diagnostics:
  - `nonempty_mask_count`;
  - `max_labels_per_mask_observed`;
  - `labels_by_sortie_count`;
  - `top_mask_label_counts`.
- The diagnostics are derived inside `_solve_best_journey_profile_dp().record_dp_stats()` by scanning `labels_by_count`.
- They do not participate in:
  - profile-DP transitions;
  - dominance;
  - pruning;
  - candidate selection;
  - certificates;
  - official lower-bound acceptance.
- `JourneyPricingResult` / JSONL now expose:
  - `dp_nonempty_mask_count`;
  - `dp_max_labels_per_mask_observed`;
  - `dp_labels_by_sortie_count`;
  - `dp_top_mask_label_counts`.
- `_journey_pricing_audit_stats()` also carries the same fields so audit / worker events can preserve structure attribution.
- ROI summary now includes:
  - `followup_profile_dp_max_labels_per_mask_observed`;
  - `followup_profile_dp_nonempty_mask_count`;
  - `followup_profile_dp_labels_by_sortie_count`;
  - `followup_profile_dp_top_mask_label_counts`;
  - `pulse_worker_followup_profile_dp_max_labels_per_mask_observed`;
  - `pulse_worker_followup_profile_dp_nonempty_mask_count`;
  - `pulse_worker_followup_profile_dp_labels_by_sortie_count`;
  - `pulse_worker_followup_profile_dp_top_mask_label_counts`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8c_profile_dp_state_attribution_zh.md`.
- Verification:
  - py_compile passed for changed pricing / driver / ROI / test files;
  - focused profile-DP stats and ROI follow-up summary tests passed;
  - very_small summary smoke wrote the new fields to summary JSON / CSV.
- Interpretation:
  - this phase provides attribution only;
  - it does not show performance ROI;
  - next profile-DP cap / proof-tail probe can distinguish a few overloaded task masks from broad reachable-mask expansion instead of only observing `state_count >= max_dp_states`.

2026-06-13 Phase 8D profile-DP state attribution probe:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8d_profile_dp_state_attribution_probe_zh.md`.
- No solver-code change beyond the already implemented Phase 8C diagnostics.
- Ran narrow attribution probes:
  - `mt20_greedy_apollo_01`, cap1000;
  - `mt20_greedy_apollo_01`, cap5000;
  - `mt20_greedy_tranq_01`, cap1000.
- Outputs:
  - `BPC_future/results/sharded_pulse_phase8d_profile_dp_attribution_cap1000_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8d_profile_dp_attribution_cap5000_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8d_profile_dp_attribution_tranq_cap1000_probe_20260613`.
- Apollo20 cap1000:
  - max `dp_state_count=1001`;
  - max `dp_nonempty_mask_count=132`;
  - max `dp_max_labels_per_mask_observed=24`;
  - representative labels by sortie count: `[[1,873]]`.
- Apollo20 cap5000:
  - max `dp_state_count=5001`;
  - max `dp_nonempty_mask_count=439`;
  - max `dp_max_labels_per_mask_observed=63`;
  - representative labels by sortie count reaches `[[1,1252],[2,2433]]`;
  - top buckets are mainly 2-sortie task sets.
- Tranq20 cap1000:
  - max `dp_state_count=1001`;
  - max `dp_nonempty_mask_count=90`;
  - max `dp_max_labels_per_mask_observed=30`.
- Worker profile behavior:
  - Apollo worker still adds one journey but follow-up first negative remains disjoint `5,8,15`;
  - Tranq worker adds no journeys in this narrow run.
- Interpretation:
  - current profile-DP tail is not a single-mask bucket disaster;
  - it is broad reachable-mask expansion, and cap5000 opens a 2-sortie combination layer that expands both mask count and bucket size;
  - simply raising `journey_pricing_max_dp_states` is not a stable fix;
  - these results do not justify default Pulse worker or official certificate gate.
- Recommended next direction:
  - if continuing profile-DP proof-tail, prefer structural mask/label control or targeted materialization over global cap increases;
  - for solver ROI, RMP stabilization / active fractional degeneracy or column-pool compression remains at least as plausible as further Pulse worker tuning.

2026-06-13 Phase 8E active fractional / pool pressure attribution:

- Added read-only active support diagnostics to `_journey_pool_structure_diagnostics()`:
  - `pool_active_duplicate_task_set_ratio`;
  - `pool_active_avg_journeys_per_task_set`;
  - `pool_active_fractional_value_sum`;
  - `pool_active_fractional_value_max`;
  - `pool_active_fractional_value_min`;
  - `pool_active_fractional_small_value_count`;
  - `pool_active_top_task_set_value_samples`.
- Added ROI summary fields:
  - `pool_active_duplicate_task_set_ratio_last`;
  - `pool_active_duplicate_task_set_ratio_max`;
  - `pool_active_avg_journeys_per_task_set_last`;
  - `pool_active_fractional_value_sum_last`;
  - `pool_active_fractional_value_max_last`;
  - `pool_active_fractional_value_min_last`;
  - `pool_active_fractional_small_value_count_last`;
  - `pool_active_top_task_set_value_samples_last`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8e_active_fractional_attribution_zh.md`.
- Verification:
  - py_compile passed for changed driver / ROI / test files;
  - focused pool diagnostics and ROI summary tests passed.
- Probe outputs:
  - `BPC_future/results/sharded_pulse_phase8e_active_fractional_attribution_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8e_active_fractional_short_probe_20260613`.
- Probe observations:
  - Apollo20 greedy baseline / worker:
    - active duplicate ratio `0.0`;
    - active avg journeys per task set `1.0`;
    - fractional ratio `0.0`;
    - worker still leaves follow-up disjoint negative `5,8,15`.
  - Tranq20 greedy baseline / worker:
    - active duplicate ratio `0.0`;
    - active avg journeys per task set `1.0`;
    - fractional ratio `0.0`.
  - short-budget `tranq20_01`:
    - active duplicate ratio `0.0`;
    - active avg journeys per task set `1.0`;
    - fractional ratio `0.272727273`;
    - fractional values are exactly three `0.5` entries, not many tiny values.
- Interpretation:
  - current observed hard-tail is not active duplicate task-set pressure;
  - the fractional pressure observed in short `tranq20_01` is not a many-tiny-column degeneracy pattern;
  - column-pool duplicate compression is not the next best mainline unless a larger matrix shows high active duplicate ratio or many tiny fractional columns.
- Recommended next direction:
  - continue residual pricing / legacy proof-tail and profile-DP structural control;
  - keep RMP stabilization as a separate line, but do not conflate it with duplicate pool compression based on current evidence.

2026-06-13 Phase 8F residual vs profile-DP top-mask attribution:

- Added ROI summary fields:
  - `followup_first_negative_profile_dp_top_overlap`;
  - `followup_first_negative_profile_dp_top_jaccard`;
  - `followup_first_negative_profile_dp_top_relation`;
  - `followup_first_negative_profile_dp_top_exact`;
  - `pulse_worker_followup_first_negative_profile_dp_top_overlap`;
  - `pulse_worker_followup_first_negative_profile_dp_top_jaccard`;
  - `pulse_worker_followup_first_negative_profile_dp_top_relation`;
  - `pulse_worker_followup_first_negative_profile_dp_top_exact`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8f_residual_dp_topmask_attribution_zh.md`.
- Probe outputs:
  - `BPC_future/results/sharded_pulse_phase8f_residual_dp_topmask_cap1000_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8f_residual_dp_topmask_cap5000_probe_20260613`.
- Apollo20 worker profile, cap1000:
  - follow-up first negative remains `5,8,15`;
  - relation to worker task set is `disjoint_task_set`;
  - relation to profile-DP top masks is only `overlapping_task_set`;
  - exact top-mask hit is `False`;
  - overlap `2`, jaccard `0.5`.
- Apollo20 worker profile, cap5000:
  - follow-up first negative remains `5,8,15`;
  - relation to profile-DP top masks is `overlapping_task_set`;
  - exact top-mask hit is `False`;
  - overlap `2`, jaccard `0.333333333`;
  - top masks shift toward larger 2-sortie task sets.
- Interpretation:
  - residual `[5,8,15]` is not a profile-DP top-bucket exact hit;
  - direct materialization of only the most overloaded profile-DP masks is unlikely to be sufficient;
  - residual tail is more likely tied to residual task-set / active context targeting, rough-vs-true RC ordering, or ordinary heuristic candidate-selection differences.
- Exactness boundary:
  - summary-only;
  - no pricing / worker / RMP / certificate behavior changes.

2026-06-13 Phase 8G residual profile-mask visibility:

- Added opt-in task-set samples decoded from existing profile mask diagnostics:
  - `diagnostic_profile_task_set_samples`;
  - `diagnostic_reachable_task_set_samples`;
  - `diagnostic_negative_task_set_samples`;
  - `diagnostic_selected_task_set_samples`.
- Added JSONL / ROI summary attribution fields:
  - `followup_first_negative_profile_reachable_*`;
  - `followup_first_negative_profile_negative_*`;
  - `followup_first_negative_profile_selected_*`;
  - matching `pulse_worker_followup_*` aliases.
- Added CLI opt-in:
  - `run_sharded_pulse_roi_calibration.py --profile-mask-diagnostics`;
  - default benchmark/profile behavior remains unchanged.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8g_residual_profile_mask_visibility_zh.md`.
- Probe outputs:
  - `BPC_future/results/sharded_pulse_phase8g_residual_profile_mask_cap1000_probe_20260613`;
  - `BPC_future/results/sharded_pulse_phase8g_residual_profile_mask_cap5000_probe_20260613`.
- Apollo20 worker profile:
  - follow-up first negative remains `5,8,15`;
  - profile-DP top-mask exact hit remains `False`;
  - cap1000 / cap5000 both show exact hits in:
    - reachable task-set samples;
    - negative task-set samples;
    - selected task-set samples.
- Interpretation:
  - residual `5,8,15` is not absent from the profile-DP universe;
  - top-bucket materialization alone is unlikely to be sufficient;
  - the next likely bottleneck is selected-negative materialization / return path, candidate scan order, or post-selection filters.
- Exactness boundary:
  - diagnostics only;
  - no DP transition, pruning, candidate selection, RMP insertion, certificate, or lower-bound behavior change;
  - diagnostics are opt-in and sample-capped.

2026-06-13 Phase 8H selected materialization / return path diagnostics:

- Added selected-candidate return-path diagnostics:
  - `profile_selected_candidate_input_count`;
  - `profile_selected_candidate_scanned_count`;
  - `profile_selected_candidate_materialized_count`;
  - `profile_selected_candidate_returned_count`;
  - branch / duplicate-signature / duplicate-task-set / forbidden-signature / dominated-task-set filtered counts;
  - `profile_selected_candidate_return_limit_truncated_count`.
- Added selected-candidate task-set samples:
  - materialized;
  - returned;
  - unmaterialized;
  - weak-filtered;
  - filtered.
- Added JSONL and ROI summary fields for follow-up first negative overlap against:
  - selected materialized samples;
  - selected returned samples;
  - selected unmaterialized samples;
  - selected weak-filtered samples;
  - selected filtered samples.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8h_selected_materialization_return_path_zh.md`.
- Probe output:
  - `BPC_future/results/sharded_pulse_phase8h_selected_materialization_cap1000_probe_20260613`.
- Apollo20 worker profile:
  - worker still adds one `[6,19]` journey;
  - ordinary follow-up first negative remains `5,8,15`;
  - `5,8,15` is selected exact, materialized exact, and returned exact;
  - it is not unmaterialized, weak-filtered, or post-materialization filtered;
  - JSONL confirms ordinary heuristic cg_iter=1 returned and then added `5,8,15`.
- Interpretation:
  - ordinary follow-up selected materialization / return path is not dropping the residual candidate;
  - the remaining problem is that Pulse worker's `[6,19]` addition does not cover or remove the residual family `[5,8,15]`;
  - next attribution should compare worker-vs-ordinary candidate family, ordering, start-time/arc-option domain, deadline, and true-RC ranking.
- Exactness boundary:
  - diagnostics only;
  - no profile-DP transition, ordering, materialization, RMP insertion, worker trigger, certificate, or lower-bound behavior changes.

2026-06-13 Phase 8I worker-vs-ordinary candidate family contrast:

- Added ROI summary fields for direct worker-vs-ordinary task-set contrast:
  - `worker_vs_ordinary_first_worker_task_set`;
  - `worker_vs_ordinary_first_followup_task_set`;
  - overlap / jaccard / relation;
  - `worker_vs_ordinary_disjoint`;
  - worker and follow-up task counts plus count delta;
  - `worker_vs_ordinary_contrast_class`.
- Added matching `pulse_worker_vs_ordinary_*` aliases for CSV inspection.
- Contrast classes are diagnostic-only:
  - `no_worker_add`;
  - `no_followup_negative`;
  - `same_task_set`;
  - `overlapping_task_set`;
  - `disjoint_residual_after_worker`;
  - `unknown_worker_task_set`;
  - `unknown`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8i_worker_vs_ordinary_candidate_contrast_zh.md`.
- Probe output:
  - `BPC_future/results/sharded_pulse_phase8i_worker_vs_ordinary_contrast_probe_20260613`.
- Apollo20 worker profile:
  - worker added `[6,19]`;
  - ordinary follow-up first negative was `[5,8,15]`;
  - overlap was `0`, jaccard was `0.0`, relation was `disjoint_task_set`;
  - contrast class was `disjoint_residual_after_worker`;
  - ordinary follow-up still selected, materialized, and returned `[5,8,15]` exactly.
- Interpretation:
  - ordinary materialization / return path is not the current bottleneck;
  - the immediate ROI gap is that the worker first addition is an inactive disjoint column and does not cover the residual negative family;
  - next attribution should inspect worker-internal candidate family coverage and stop-after-first-negative / ordering behavior.
- Exactness boundary:
  - diagnostics only;
  - no Pulse transition, profile-DP ordering, materialization, RMP insertion, worker trigger, certificate, or lower-bound behavior changes.

2026-06-13 Phase 8J worker internal candidate-family coverage:

- Added read-only Pulse candidate-family samples:
  - `pulse_negative_pool_task_set_samples`;
  - `pulse_negative_pool_sequence_samples`;
  - `pulse_negative_pool_signature_samples`;
  - `pulse_harvested_task_set_samples`;
  - `pulse_harvested_sequence_samples`;
  - `pulse_harvested_signature_samples`;
  - `pulse_returned_candidate_task_set_samples`;
  - `pulse_returned_candidate_sequence_samples`;
  - `pulse_returned_candidate_signature_samples`.
- Added ROI summary comparisons for ordinary follow-up first negative against:
  - worker negative pool;
  - worker harvested pool;
  - worker returned-candidate pool.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8j_worker_internal_candidate_family_zh.md`.
- Probe output:
  - `BPC_future/results/sharded_pulse_phase8j_worker_internal_candidate_family_probe_20260613`.
- Apollo20 worker profile:
  - worker added `[6,19]`;
  - ordinary follow-up first negative was `[5,8,15]`;
  - worker negative pool samples were only `[[6,19]]`;
  - worker harvested samples were only `[[6,19]]`;
  - worker returned-candidate samples were only `[[6,19]]`;
  - overlap to `[5,8,15]` was `0`, jaccard `0.0`, exact hit `False` for all three pools;
  - no critical disagreement.
- Interpretation:
  - residual `[5,8,15]` is not being dropped by impact filtering or returned-candidate selection;
  - in this worker call, the residual family is absent from the worker internal negative / harvested / returned pools;
  - the next attribution point is same-context residual reachability, stop-after-first-negative behavior, shard/order/deadline coverage, or context drift between worker and ordinary follow-up.
- Exactness boundary:
  - diagnostics only;
  - no worker trigger, search ordering, pruning, impact filter, RMP insertion, certificate, or lower-bound behavior changes.

2026-06-13 Phase 8K same-context residual reachability:

- Added target-sequence task-set overlap fields to the ROI summary:
  - `worker_target_sequence_task_set`;
  - `worker_target_negative_pool_*`;
  - `worker_target_harvested_*`;
  - `worker_target_returned_candidate_*`;
  - matching `pulse_worker_target_*` aliases.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8k_same_context_residual_reachability_zh.md`.
- Probe output:
  - `BPC_future/results/sharded_pulse_phase8k_same_context_residual_reachability_probe_20260613`.
- Apollo20 worker profiles:
  - basic coverage scan with `stop_after_first_negative=False` returned `[7,19]`, `[6,19]`, and `[11,12]`, but target `5,8,15` remained absent and target prefix length stayed `0`;
  - disabling the ROI gate did not change that conclusion;
  - target first-task priority returned exact target task-set `[5,8,15]` among eight returned candidates;
  - target transition priority reached prefix `8,15` but was blocked by `time_window`;
  - target arc-option priority produced no worker additions under the same small budget.
- Interpretation:
  - residual task-set family `[5,8,15]` is reachable by the worker when the first-task shard is prioritized;
  - the base worker misses it mainly because first-task shard ordering / budget prevents reaching that family;
  - exact ordinary sequence `8,15,5` is not the only feasible residual task-set representation, and forcing that transition can be time-window blocked;
  - the next useful direction is residual-aware shard scheduling / first-task priority with strict ROI gates, not default worker enablement or certificate gating.
- Exactness boundary:
  - diagnostics only;
  - no DFS transition, pruning, impact filter, RMP insertion, certificate, or lower-bound behavior changes.

2026-06-13 Phase 8L residual-aware first-task priority ROI gate:

- Added calibration profile:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate`.
- The strict gated profile is 20-task only and combines:
  - target first-task priority for `8,15,5`;
  - `stop_after_first_negative=False`;
  - same-iteration follow-up;
  - active-support continuation guard;
  - true-RC gate;
  - follow-up reserve;
  - failure cooldown;
  - current-probe hard-tail fingerprint.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8l_residual_target_priority_roi_gate_zh.md`.
- Probe outputs:
  - `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_roi_gate_smoke_20260613`;
  - `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_probe_no_gate_20260613`;
  - `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_tranq20_probe_20260613`.
- Strict gated matrix:
  - Apollo5 / Tranq5 / Apollo10 / Tranq10_09 / Apollo20 had no worker trigger;
  - official results unchanged;
  - no critical disagreement.
- Diagnostic no-gate target-priority matrix:
  - 5/10 remained no-op and unchanged;
  - Apollo20 triggered worker, returned eight candidates including exact `[5,8,15]`, and short-run primal improved from `921.640296` to `857.401315`;
  - worker additions were still `changed_inactive_only`, with zero active-support-changing additions;
  - follow-up still found residual negative `[4,12,18]`;
  - Tranq20 saw no trigger/improvement with the hardcoded Apollo residual target.
- Interpretation:
  - strict gate is safe but too conservative in this smoke;
  - target first-task priority has a local Apollo20 positive signal;
  - hardcoded residual targets do not generalize;
  - next work should extract residual targets from current/previous diagnostic evidence and apply residual-aware scheduling under strict context gates.
- Exactness boundary:
  - calibration profiles only;
  - no production default change;
  - no certificate or lower-bound side effect.

2026-06-13 Phase 8M automatic residual target extraction:

- Added calibration profiles:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate`.
- Added automatic residual target extraction:
  - consumes only previous rows for the same instance;
  - requires 20-task scale;
  - requires non-empty worker context hash;
  - prefers `followup_first_negative_sequence`, then falls back to `followup_first_negative_task_set`;
  - does not hard-code `8,15,5`.
- Added worker expected-context guard:
  - `journey_sharded_pulse_hidden_negative_worker_expected_context_hash`;
  - mismatches skip the worker with `residual_target_context_mismatch`.
- Added summary fields:
  - `auto_residual_target_applied`;
  - `auto_residual_target_sequence`;
  - `auto_residual_target_source_profile`;
  - `auto_residual_target_source_context_hash`;
  - `auto_residual_target_context_match`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8m_auto_residual_target_extraction_zh.md`.
- Probe output:
  - `BPC_future/results/sharded_pulse_phase8m_auto_residual_target_diagnostic_20260613`.
- Smoke result:
  - Apollo5 / Tranq5 / Apollo10 / Tranq10_09 remained no-op for auto residual target and unchanged;
  - Apollo20 seed profile found follow-up residual `[5,8,15]`;
  - Apollo20 auto diagnostic extracted `8,15,5`, matched context hash `080a188d2484ee3e`, returned and added eight worker columns including `[5,8,15]`, and improved short-run primal from `921.640296` to `857.401315`;
  - the additions were still `changed_inactive_only`, with zero active-support-changing additions;
  - follow-up residual negative remained and shifted to `[4,12,18]`;
  - strict auto ROI profile matched context but did not trigger under the hard-tail / max-iteration gates.
- Interpretation:
  - automatic residual extraction and context guarding work;
  - diagnostic target scheduling can reproduce the local Apollo20 positive signal without hard-coded target configuration;
  - ROI is still not proven because the added columns are inactive-only and residual negatives continue.
- Exactness boundary:
  - opt-in calibration profiles only;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or 20/100 A/B.

2026-06-13 Phase 8N active-support-aware residual source gate:

- Added calibration profiles:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate`.
- Added active residual source gate:
  - a source row must have active-support-changing signal;
  - residual target relation to the worker-added family must be `same_task_set` or `overlapping_task_set`;
  - `disjoint_task_set` residuals are rejected;
  - rejected candidates do not fall back to ordinary untargeted worker.
- Added summary fields:
  - `auto_residual_target_candidate_sequence`;
  - `auto_residual_target_source_gate`;
  - `auto_residual_target_source_gate_reason`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8n_active_source_gate_zh.md`.
- Probe output:
  - `BPC_future/results/sharded_pulse_phase8n_active_source_gate_smoke_20260613`.
- Smoke result:
  - Apollo5 / Tranq5 / Apollo10 / Tranq10_09 remained no-op and unchanged;
  - Apollo20 seed profile produced follow-up residual `[5,8,15]`;
  - active auto profiles detected candidate `8,15,5` but rejected it with `residual_disjoint_from_worker`;
  - worker did not trigger after rejection;
  - official result stayed unchanged;
  - no critical disagreement.
- Interpretation:
  - the 8M residual target is reachable but not an active-support-related source;
  - active source gating prevents the inactive-only residual chasing observed in 8M;
  - next work should search for source rows whose residual relation is `same_task_set` or `overlapping_task_set`, then test whether active auto target can produce support-changing additions.
- Exactness boundary:
  - opt-in calibration profiles only;
  - no production default change;
  - no certificate or lower-bound effect;
  - no resume, parallel, or 20/100 A/B.

2026-06-13 Phase 8O active residual source search / seed matrix:

- Added profile group:
  - `phase8o_active_source_search`.
- The group expands to:
  - `baseline`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate`.
- Added row-level active source diagnostics:
  - `active_residual_source_candidate`;
  - `active_residual_source_candidate_sequence`;
  - `active_residual_source_context_hash`;
  - `active_residual_source_relation`;
  - `active_residual_source_active_signal_count`;
  - `active_residual_source_gate_reason`;
  - `active_residual_source_passed`.
- Added previous-row source-search diagnostics for auto-active profiles:
  - `active_residual_source_search_candidate_count`;
  - `active_residual_source_search_passed_count`;
  - `active_residual_source_search_blocked_count`;
  - `active_residual_source_search_blocked_disjoint_count`;
  - `active_residual_source_search_blocked_no_active_count`;
  - `active_residual_source_search_blocked_relation_count`;
  - `active_residual_source_search_first_passed_*`;
  - `active_residual_source_search_first_blocked_*`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8o_active_source_search_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase8o_active_source_search_smoke_20260613`.
- Smoke matrix:
  - Apollo5 / Tranq5 / Apollo10 / Tranq10_09 / Apollo20 / Tranq20;
  - no production default or certificate behavior changed.
- Result:
  - 5/10 remained no-op for 20-task-only profiles;
  - Apollo20 seed rows had active-support signal but residual relation remained `disjoint_task_set`;
  - auto-active rows observed `candidate=2`, `passed=0`, `blocked_disjoint=2`;
  - Tranq20 produced no candidate source under the same short budget;
  - no critical disagreement.
- Interpretation:
  - current short seed matrix did not find a same/overlapping active residual source;
  - the new source-search fields make this negative result explicit rather than conflating it with missing target extraction;
  - next work should either broaden source search safely or pivot away from Pulse worker expansion if another A/B remains negative.
- Exactness boundary:
  - diagnostics/profile grouping only;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe prefix/cut bound change.

2026-06-13 Phase 8P expanded active source seed matrix:

- Added instance group:
  - `phase8p_20_source_seed_matrix`.
- The 20-task group uses feasible short-smoke seeds:
  - `mt20_greedy_apollo_01`;
  - `mt20_greedy_tranq_01`;
  - `tranq20_01`.
- The old `apollo20_01` preset was not included in the default group because the initial grid preflight failed with a no-feasible-single-task trip error for task 17; this is treated as an instance/grid issue, not an algorithm failure.
- Added profile group:
  - `phase8p_active_source_seed_matrix`.
- The group expands to:
  - `baseline`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate`.
- Added source-search outcome fields:
  - `active_residual_source_search_outcome_class`;
  - `active_residual_source_search_recommendation`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8p_active_source_seed_matrix_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase8p_active_source_seed_matrix_smoke_v2_20260613`.
- Smoke matrix:
  - Apollo5 / Tranq5 / Apollo10 / Tranq10_09;
  - `mt20_greedy_apollo_01`;
  - `mt20_greedy_tranq_01`;
  - `tranq20_01`.
- Result:
  - 5/10 remained no-op and unchanged;
  - no critical disagreement;
  - Apollo20 target-priority seed produced an overlapping residual source:
    - candidate sequence `12,4,18`;
    - relation `overlapping_task_set`;
    - active source passed;
  - Apollo20 auto-active diagnostic consumed that passed source and added one active-replacement column;
  - after that diagnostic worker call, the follow-up residual negative returned to disjoint `8,15,5`;
  - strict auto-active ROI profile had the same target extracted but did not trigger due `max_cg_iter_exceeded`;
  - Tranq greedy / Tranq20 did not produce a passed active source in this short matrix.
- Interpretation:
  - expanded source search can find a same/overlapping source, so the 8O negative result was not final;
  - however, applying that source still did not produce stable ROI or eliminate the residual tail;
  - the active-worker line still lacks production evidence and should not be default-enabled;
  - next work should test whether passed sources have repeatable tail impact, otherwise pivot away from Pulse active worker expansion.
- Exactness boundary:
  - opt-in calibration matrix only;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 8Q passed-source ROI validation:

- Added validation profiles:
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate`.
- Added profile group:
  - `phase8q_passed_source_roi_validation`.
- The group expands to:
  - `baseline`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`;
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8q_passed_source_roi_validation_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613`.
- Smoke matrix:
  - Apollo5 / Tranq5 / Apollo10 / Tranq10_09;
  - `mt20_greedy_apollo_01`;
  - `mt20_greedy_tranq_01`;
  - `tranq20_01`.
- Result:
  - 5/10 remained no-op and unchanged;
  - no critical disagreement;
  - Apollo20 coverage-target seed produced the passed source `12,4,18`;
  - auto-active diagnostic consumed `12,4,18`, added one active-replacement column, but follow-up residual negative remained `8,15,5`;
  - validation diagnostic repeated the same behavior:
    - target `12,4,18`;
    - one active-replacement column;
    - follow-up residual negative `8,15,5`;
  - validation ROI-gate profile extracted the same target but did not trigger worker due `max_cg_iter_exceeded`;
  - under this 1.8s smoke budget, Apollo20 auto-active validation rows had worse primal than baseline and did not reduce residual tail;
  - Tranq seeds produced no passed source.
- Interpretation:
  - the passed source is reproducible but does not provide stable worker ROI;
  - active-replacement additions still fail to remove the disjoint residual tail;
  - strict ROI gate still refuses to run in the same short setup;
  - this is evidence for stopping Pulse active-worker expansion and preparing a negative-result/pivot report, not for production tuning.
- Exactness boundary:
  - opt-in calibration validation only;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 8R active-worker negative-result / pivot:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase8r_active_worker_negative_result_pivot_zh.md`.
- Decision:
  - stop expanding the `current-context Pulse hidden-negative active worker` sub-route;
  - do not enable production Pulse worker by default;
  - do not open official certificate gate;
  - do not increase worker time limit or keep stacking active-worker gates;
  - do not keep writing target-specific ordering gates for the `8,15,5` residual family.
- Evidence:
  - Phase 7O-7P showed worker can add true-RC negative columns but does not produce stable wall-time ROI;
  - Phase 7U-7Z showed worker-added columns can enter the pool/support, while follow-up residual negatives remain;
  - Phase 7AA-7AG localized the Apollo residual gap to path/arc-option/start-time coverage, but target-specific priority still did not convert to ROI;
  - Phase 8A-8F pivot diagnostics pointed to residual disjoint negative / profile-DP tail / active fractional signals, not simple active duplicate pressure;
  - Phase 8Q repeated the passed source `12,4,18`, but it only added an active-replacement column and follow-up residual returned to `8,15,5`.
- Final requirement audit:
  - active-worker sub-route satisfies the negative evidence for repeated A/B no stable ROI;
  - worker additions do not reliably reduce residual tail;
  - 20-task selected smoke still has no clear improvement;
  - the full overall goal is not complete because proof-closed resume / full proof-route ROI has not been established or ruled out.
- Recommended pivot:
  - `legacy/profile-DP proof-tail structural control`;
  - `RMP stabilization / active fractional degeneracy`;
  - proof-closed resume only if needed to complete the formal proof-route negative evidence.
- Exactness boundary:
  - report/docs only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9A profile-DP proof-tail bridge diagnostics:

- Added summary fields:
  - `followup_proof_tail_bridge_class`;
  - `followup_proof_tail_bridge_reason`;
  - `pulse_worker_followup_proof_tail_bridge_class`;
  - `pulse_worker_followup_proof_tail_bridge_reason`.
- Added helper:
  - `_classify_followup_proof_tail_bridge()`.
- Added profile group:
  - `phase9a_profile_dp_bridge_diagnostics`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9a_profile_dp_bridge_diagnostics_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9a_profile_dp_bridge_diagnostics_smoke_20260613`.
- Result:
  - 5/10 rows remained no-op with no critical disagreement;
  - Apollo20 opt-in worker rows classified as `profile_returned_residual_exact`;
  - the observed follow-up residual task sets were already reachable, negative, selected, materialized, and returned by profile-DP.
- Interpretation:
  - the observed Apollo residual tail is not primarily a profile-DP selected/materialization/returned bridge miss;
  - next work should analyze the post-return tail sequence, RMP movement, rough-vs-true RC ordering, and active fractional/replacement behavior;
  - do not restart Pulse active-worker tuning based on this result.
- Exactness boundary:
  - summary classification only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect.

2026-06-13 Phase 9B returned-residual tail attribution:

- Added summary fields:
  - `followup_returned_residual_tail_class`;
  - `followup_returned_residual_tail_reason`;
  - `followup_negative_task_set_sequence`;
  - `followup_negative_task_set_unique_count`;
  - `followup_negative_task_set_repeat_count`;
  - `followup_first_negative_addition_productivity_class`;
  - `followup_first_negative_added_journeys`;
  - `followup_first_negative_added_new_task_set_count`;
  - `followup_first_negative_added_replacement_count`;
  - `followup_first_negative_added_support_changing_count`;
  - `followup_post_first_negative_rmp_objective_delta`;
  - `followup_post_first_negative_dual_l1_delta`;
  - plus `pulse_worker_followup_*` aliases.
- Added helpers:
  - `_first_matching_column_addition_after()`;
  - `_first_rmp_after_index()`;
  - `_classify_returned_residual_tail()`.
- Added profile group:
  - `phase9b_returned_residual_tail_attribution`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9b_returned_residual_tail_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9b_returned_residual_tail_attribution_smoke_20260613`.
- Result:
  - 5/10 remained no-op with no critical disagreement;
  - Apollo20 opt-in worker rows classified as `returned_residual_then_new_negative_family`;
  - first follow-up residual columns were new task sets but not active-support-changing;
  - after first residual addition, objective/dual moved, but additional negative task-set families continued to appear.
- Interpretation:
  - tail is not a same-residual repeat and not a profile-DP visibility bridge miss;
  - the current signal points to inactive/weak-impact new columns, residual-family regeneration, active fractional pressure, or RMP/dual degeneracy;
  - next work should do RMP residual impact / active-support attribution.
- Exactness boundary:
  - summary attribution only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect.

2026-06-13 Phase 9C RMP residual active-support attribution:

- Added summary fields:
  - `followup_first_negative_active_after_addition`;
  - `followup_first_negative_active_value_after_addition`;
  - `followup_first_negative_active_journey_count_after_addition`;
  - `followup_first_negative_active_relation_after_addition`;
  - `followup_active_fractional_ratio_after_first_negative`;
  - `followup_active_total_value_after_first_negative`;
  - `followup_active_task_set_hash_after_first_negative`;
  - `followup_rmp_residual_impact_class`;
  - `followup_rmp_residual_impact_reason`;
  - plus `pulse_worker_followup_*` aliases.
- Added helpers:
  - `_first_pool_after_index()`;
  - `_active_task_set_value_from_pool_record()`;
  - `_classify_rmp_residual_impact()`.
- Added profile group:
  - `phase9c_rmp_residual_active_support_attribution`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9c_rmp_residual_active_support_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9c_rmp_residual_active_support_attribution_smoke_20260613`.
- Result:
  - 5/10 rows remained worker no-op with no critical disagreement;
  - `tranq20_01` also remained worker no-op in this short smoke;
  - Apollo20 coverage-target row added 8 worker journeys / 8 new task sets, then first follow-up residual task set became active with value `1.0`;
  - Apollo20 auto-active validation row added 1 worker journey / 1 support-changing column, then first follow-up residual task set also became active with value `1.0`;
  - both Apollo20 worker rows still produced 3 unique follow-up negative task sets after the first residual became active.
- Interpretation:
  - the residual tail is not a profile-DP bridge miss;
  - the first returned residual is not simply ignored by the next RMP;
  - active residual absorption still does not eliminate subsequent negative families;
  - current evidence points to residual-family regeneration, active-basis churn, or RMP/dual degeneracy rather than a missing Pulse worker trigger.
- Exactness boundary:
  - summary attribution only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9D residual-family chain attribution:

- Added summary fields:
  - `followup_first_negative_active_persistence_count`;
  - `followup_first_negative_active_value_sequence`;
  - `followup_first_negative_active_last_value`;
  - `followup_active_basis_hash_sequence_after_first_negative`;
  - `followup_active_basis_unique_count_after_first_negative`;
  - `followup_active_basis_churn_count_after_first_negative`;
  - `followup_negative_family_after_first_count`;
  - `followup_negative_family_after_first_relation_sequence`;
  - `followup_negative_family_after_first_disjoint_count`;
  - `followup_negative_family_after_first_overlapping_count`;
  - `followup_negative_family_after_first_same_count`;
  - `followup_negative_family_after_first_max_overlap`;
  - `followup_negative_family_after_first_max_jaccard`;
  - `followup_residual_family_chain_class`;
  - `followup_residual_family_chain_reason`;
  - plus `pulse_worker_followup_*` aliases.
- Added helpers:
  - `_pool_records_after_index()`;
  - `_active_residual_persistence_summary()`;
  - `_negative_family_after_first_summary()`;
  - `_classify_residual_family_chain()`.
- Added profile group:
  - `phase9d_residual_family_chain_attribution`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9d_residual_family_chain_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9d_residual_family_chain_attribution_smoke_20260613`.
- Result:
  - 5/10 rows remained worker no-op with no critical disagreement;
  - `tranq20_01` also remained worker no-op in this short smoke;
  - Apollo20 coverage-target row had one follow-up residual, active value `1.0`, and no observed later family in this smoke;
  - Apollo20 auto-active validation row kept the first residual active with value sequence `[1.0,1.0]`;
  - auto-active validation active basis hash stayed constant, but two later overlapping negative families still appeared.
- Interpretation:
  - the active residual can persist across later pool diagnostics;
  - the observed later negative families are weakly overlapping rather than same-family repeats;
  - active basis hash churn is not required for the tail to continue;
  - current evidence points away from further Pulse worker tuning and toward RMP degeneracy / pool compression / active-family stabilization diagnostics.
- Exactness boundary:
  - summary attribution only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9E RMP degeneracy / pool-pressure attribution:

- Added summary fields:
  - `followup_post_first_negative_pool_duplicate_task_sets`;
  - `followup_post_first_negative_pool_duplicate_task_set_ratio`;
  - `followup_post_first_negative_pool_active_duplicate_task_sets`;
  - `followup_post_first_negative_pool_active_duplicate_task_set_ratio`;
  - `followup_post_first_negative_pool_avg_journeys_per_task_set`;
  - `followup_post_first_negative_pool_max_journeys_per_task_set`;
  - `followup_post_first_negative_pool_active_avg_journeys_per_task_set`;
  - `followup_post_first_negative_pool_active_fractional_value_sum`;
  - `followup_post_first_negative_pool_active_fractional_value_max`;
  - `followup_post_first_negative_pool_active_fractional_value_min`;
  - `followup_post_first_negative_pool_active_fractional_small_value_count`;
  - `followup_rmp_degeneracy_pressure_class`;
  - `followup_rmp_degeneracy_pressure_reason`;
  - plus `pulse_worker_followup_*` aliases.
- Added helper:
  - `_classify_rmp_degeneracy_pressure()`.
- Added profile group:
  - `phase9e_rmp_degeneracy_pool_pressure_attribution`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9e_rmp_degeneracy_pool_pressure_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9e_rmp_degeneracy_pool_pressure_attribution_smoke_20260613`.
- Result:
  - 5/10 rows remained worker no-op with no critical disagreement;
  - `tranq20_01` also remained worker no-op in this short smoke;
  - Apollo20 coverage-target row classified as `active_fractional_pressure` with active fractional ratio `0.583333333`;
  - Apollo20 auto-active validation row classified as `stable_basis_overlapping_family_with_dual_move`;
  - both Apollo20 rows had pool duplicate ratio `0.0` and active duplicate ratio `0.0` after the first residual.
- Interpretation:
  - the residual tail is not explained by simple duplicate task-set pressure;
  - one row shows active fractional pressure;
  - another row shows stable active basis plus dual movement plus overlapping negative family;
  - this supports pivoting away from Pulse worker expansion toward RMP stabilization / active-family stabilization / legacy final judge tail optimization.
- Exactness boundary:
  - summary attribution only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9F RMP stabilization / pool-compression diagnostics:

- Added summary fields:
  - `followup_post_first_negative_dual_objective_abs_ratio`;
  - `followup_post_first_negative_dual_move_class`;
  - `followup_pool_compression_candidate_class`;
  - `followup_pool_compression_candidate_reason`;
  - `followup_rmp_stabilization_candidate_class`;
  - `followup_rmp_stabilization_candidate_reason`;
  - plus `pulse_worker_followup_*` aliases.
- Added helpers:
  - `_dual_objective_abs_ratio()`;
  - `_classify_dual_move()`;
  - `_classify_pool_compression_candidate()`;
  - `_classify_rmp_stabilization_candidate()`.
- Added profile group:
  - `phase9f_rmp_stabilization_pool_compression_diagnostics`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9f_rmp_stabilization_pool_compression_diagnostics_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9f_rmp_stabilization_pool_compression_diagnostics_smoke_20260613`.
- Result:
  - 5/10 rows remained worker no-op with no critical disagreement;
  - `tranq20_01` also remained worker no-op in this short smoke;
  - Apollo20 coverage-target row classified as `active_family_stabilization_candidate`;
  - Apollo20 auto-active validation row classified as `stable_basis_dual_stabilization_candidate`;
  - both Apollo20 rows had `no_pool_compression_signal`.
- Interpretation:
  - current evidence does not support a pool-compression policy as the next primary move;
  - active-worker expansion remains unsupported;
  - the next useful direction is a narrow RMP/dual stabilization diagnostic, still opt-in and non-certifying.
- Exactness boundary:
  - summary attribution only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9G RMP/dual stabilization diagnostic design:

- Added summary fields:
  - `followup_stabilization_diagnostic_design_class`;
  - `followup_stabilization_diagnostic_design_reason`;
  - `followup_stabilization_diagnostic_recommended_profile`;
  - `followup_stabilization_diagnostic_guarded_config_keys`;
  - `followup_stabilization_diagnostic_certificate_effect_allowed`;
  - plus `pulse_worker_followup_*` aliases.
- Added helper:
  - `_stabilization_diagnostic_design()`.
- Added profile group:
  - `phase9g_rmp_dual_stabilization_diagnostic_design`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9g_rmp_dual_stabilization_diagnostic_design_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9g_rmp_dual_stabilization_diagnostic_design_smoke_20260613`.
- Result:
  - 5/10 rows remained worker no-op with no critical disagreement;
  - `tranq20_01` also remained worker no-op in this short smoke;
  - Apollo20 coverage-target row produced `active_family_stabilization_diagnostic`;
  - Apollo20 auto-active validation row produced `stable_basis_dual_stabilization_diagnostic`;
  - all diagnostic designs had `certificate_effect_allowed=False`.
- Interpretation:
  - Phase 9G is a design bridge only, not an ROI claim;
  - the next possible implementation must be audit-only, context-hash guarded, and unable to affect official certificate/lower bound;
  - active-worker expansion remains unsupported.
- Exactness boundary:
  - summary design only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9H RMP/dual stabilization probe skeleton:

- Added summary fields:
  - `followup_stabilization_probe_enabled`;
  - `followup_stabilization_probe_status`;
  - `followup_stabilization_probe_reason`;
  - `followup_stabilization_probe_mode`;
  - `followup_stabilization_probe_candidate_source`;
  - `followup_stabilization_probe_anchor_weight`;
  - `followup_stabilization_probe_context_hash_required`;
  - `followup_stabilization_probe_context_hash`;
  - `followup_stabilization_probe_certificate_effect_allowed`;
  - `followup_stabilization_probe_official_effect_allowed`;
  - `followup_stabilization_probe_mutates_rmp`;
  - `followup_stabilization_probe_design_profile`;
  - plus `pulse_worker_followup_*` aliases.
- Added helper:
  - `_stabilization_probe_skeleton()`.
- Added profile group:
  - `phase9h_rmp_dual_stabilization_probe_skeleton`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9h_rmp_dual_stabilization_probe_skeleton_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9h_rmp_dual_stabilization_probe_skeleton_smoke_20260613`.
- Result:
  - 5/10 rows remained worker no-op with no probe plan and no critical disagreement;
  - `tranq20_01` also remained worker no-op in this short smoke;
  - Apollo20 coverage-target row produced an `active_family_dual_anchor` audit-only probe plan;
  - Apollo20 auto-active validation row produced a `stable_basis_dual_anchor` audit-only probe plan;
  - both Apollo20 probe plans carried a non-empty context hash and fixed `certificate_effect_allowed=False`, `official_effect_allowed=False`, `mutates_rmp=False`.
- Interpretation:
  - Phase 9H is still a logging / guard skeleton, not a stabilization ROI claim;
  - Apollo20 profile-level official-result differences come from the existing worker profile path, not from the probe skeleton;
  - the next real stabilization experiment must remain opt-in, audit-only, context-hash guarded, and non-certifying.
- Exactness boundary:
  - summary probe-plan only;
  - no solver semantics change;
  - no production default change;
  - no official certificate or lower-bound effect;
  - no resume, parallel, or unsafe bound changes.

2026-06-13 Phase 9I RMP/dual stabilization A/B smoke:

- Added experimental calibration profiles:
  - `experimental_l1_previous_dual_stabilization_20_only`;
  - `experimental_l1_zero_dual_stabilization_20_only`.
- Added profile group:
  - `phase9i_rmp_dual_stabilization_ab`.
- Added summary fields:
  - `dual_stabilization_events`;
  - `dual_stabilization_accepted_count`;
  - `dual_stabilization_skipped_count`;
  - `dual_stabilization_status_sequence`;
  - `dual_stabilization_source_sequence`;
  - `dual_stabilization_mode_sequence`;
  - `dual_stabilization_reference_sequence`;
  - `dual_stabilization_first_accepted_cg_iter`;
  - `dual_stabilization_current_pool_negative_count_max`;
  - `dual_stabilization_objective_mismatch_count`;
  - `dual_stabilization_current_pool_infeasible_count`;
  - `dual_stabilization_time`;
  - `dual_stabilization_effect_class`.
- Added helper:
  - `_dual_stabilization_metrics()`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9i_rmp_dual_stabilization_ab_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9i_rmp_dual_stabilization_ab_smoke_20260613`.
- Result:
  - 5/10 experimental profiles were no-op with no regression;
  - Apollo20 accepted stabilized duals under both previous-anchor and zero-anchor profiles, but official result stayed unchanged;
  - Tranq20 accepted stabilized duals under both profiles;
  - Tranq20 zero-anchor profile changed final short-smoke state from `INCOMPLETE_LIMIT` baseline to `FOUND_NEGATIVE` and improved primal from `783.715884` to `781.398505`;
  - all accepted stabilized dual events had `current_pool_negative_count_max=0`, `objective_mismatch_count=0`, and `current_pool_infeasible_count=0`.
- Interpretation:
  - RMP/dual stabilization is a more promising next line than expanding Pulse worker;
  - the Tranq20 zero-anchor result is only a short-smoke signal and cannot be called stable ROI;
  - next work should repeat / lengthen the zero-anchor and previous-anchor A/B while preserving 5/10 no-regression.
- Exactness boundary:
  - calibration profiles only;
  - no production default change;
  - no Sharded Pulse worker/certificate effect;
 - stabilized dual uses existing objective-match and current-pool feasibility guard;
 - experimental profiles disable stabilized dual on certificate candidates.

2026-06-13 Phase 9J RMP/dual stabilization repeat A/B:

- Added repeat support to ROI calibration:
  - `--repeat-count`;
  - `repeat_index` summary field;
  - repeat-aware log paths, with baseline comparison isolated per repeat.
- Added profile group:
  - `phase9j_rmp_dual_stabilization_repeat_ab`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613`.
- Smoke matrix:
  - `apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `mt20_greedy_apollo_01`, `tranq20_01`;
  - profiles: baseline, previous-anchor stabilization, zero-anchor stabilization;
  - repeat count = 2;
  - time limit = 2.4s, max CG = 6.
- Result:
  - 5/10 experimental rows remained no-op with no critical disagreement;
  - 20-task accepted stabilized duals with `current_pool_negative_count_max=0`, `objective_mismatch_count=0`, and `current_pool_infeasible_count=0`;
  - Apollo20 zero-anchor improved primal once but did not repeat the improvement;
  - Tranq20 previous-anchor improved once and no-regressed once;
  - Tranq20 zero-anchor improved once but worsened once by wall/pricing path.
- Interpretation:
  - dual stabilization remains exactness-guarded and worth further study;
  - the observed 20-task gains are not stable enough for production tuning;
  - next work should expand repeats / hard instances / time limits before making any candidate-profile claim.
- Exactness boundary:
  - calibration profiles only;
 - no production default change;
 - no Sharded Pulse worker/certificate effect;
 - stabilized dual remains disabled on certificate candidates;
  - no official certificate or lower-bound rule was relaxed.

2026-06-13 Phase 10A profile-DP / legacy proof-tail diagnostics:

- Added global profile-DP tail summary fields:
  - `profile_dp_tail_records`;
  - `profile_dp_tail_incomplete_count`;
  - `profile_dp_tail_negative_count`;
  - `profile_dp_tail_no_negative_count`;
  - `profile_dp_tail_state_cap_hit_count`;
  - `profile_dp_tail_mask_cap_incomplete_count`;
  - `profile_dp_tail_time`;
  - `profile_dp_tail_state_count_max`;
  - `profile_dp_tail_processed_labels_max`;
  - `profile_dp_tail_extension_attempts`;
  - `profile_dp_tail_nonempty_mask_count_max`;
  - `profile_dp_tail_max_labels_per_mask_observed_max`;
  - `profile_dp_tail_top_mask_label_counts`;
  - `profile_dp_tail_min_best_rc`;
  - `profile_dp_tail_class`;
  - `profile_dp_tail_reason`.
- Added helpers:
  - `_official_pricing_records()`;
  - `_profile_dp_tail_metrics()`;
  - `_classify_profile_dp_tail()`.
- Added profile group:
  - `phase10a_profile_dp_tail_diagnostics`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10a_profile_dp_tail_diagnostics_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10a_profile_dp_tail_diagnostics_smoke_20260613`.
- Smoke matrix:
  - 20 balanced 5-task rows;
  - 20 balanced 10-task rows;
  - 3 feasible 20-task hard-smoke rows;
  - baseline only.
- Result:
  - 5-task: mostly `profile_dp_negative_tail`, no profile-DP incomplete/state-cap blocker;
  - 10-task: all `profile_dp_negative_tail`, many state-cap hits but still negative-returning;
  - 20-task: `tranq20_01` and `mt20_greedy_apollo_01` are `profile_dp_incomplete_tail`; `mt20_greedy_tranq_01` is `profile_dp_negative_tail`;
  - 20-task retry count remained zero, so current proof-tail is not primarily completion-bound retry overhead.
- Interpretation:
  - stop Pulse worker and dual-stabilization production expansion;
  - next optimization should target profile-DP proof-tail, especially incomplete tails and state-cap / mask-hotspot structure;
  - do not simply raise caps globally without controlled A/B.
- Exactness boundary:
  - diagnostics only;
  - no solver/pricing path change;
  - no production default change;
  - no certificate/lower-bound rule relaxed.

2026-06-13 Phase 10B profile-DP state-cap sensitivity:

- Added calibration-only 20-task profiles:
  - `experimental_profile_dp_cap_2000_20_only`;
  - `experimental_profile_dp_cap_3000_20_only`.
- Added aliases:
  - `phase10b_profile_dp_state_cap_gate`;
  - `phase10b_profile_dp_state_cap_sensitivity`.
- The cap profiles are no-op for 5/10-task instances and only override
  `journey_pricing_max_dp_states` for 20-task calibration runs.
- The profiles explicitly keep these disabled:
  - Sharded Pulse audit;
  - Sharded Pulse hidden-negative worker;
  - dual stabilization.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613`.
- Smoke matrix:
  - `apollo5`, `tranq5`;
  - `apollo10`, `tranq10_09`, `tranq10_04`;
  - `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - baseline, cap2000, cap3000;
  - repeat count = 1.
- Result:
  - 5/10 no-op guard worked: no official result change and no critical disagreement;
  - 20-task cap2000 did not reduce incomplete tail and worsened two rows;
  - 20-task cap3000 increased profile-DP time and also worsened two rows;
  - `mt20_greedy_apollo_01` and `mt20_greedy_tranq_01` show that more-negative
    profile-DP candidates do not necessarily improve the short CG tail.
- Interpretation:
  - do not pursue global or coarse profile-DP cap increases as the next mainline;
  - pivot to profile-DP mask-hotspot ordering / selected-mask materialization diagnostics;
  - keep 5/10 no-regression and certificate semantics unchanged.
- Exactness boundary:
  - calibration profiles only;
  - no Sharded Pulse worker/audit/certificate effect;
  - no dual stabilization;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 10D profile-DP mask-hotspot repeat validation:

- Ran repeat-count 3 validation for:
  - baseline;
  - `experimental_profile_dp_mask_label_cap_16_20_only`;
  - `experimental_profile_dp_mask_label_cap_32_20_only`.
- Used the same gate:
  - `phase10c_profile_dp_mask_hotspot_gate`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613`.
- Result:
  - 5/10 no-op guard worked across all repeats;
  - 20-task baseline, label-cap16, and label-cap32 all had 6 incomplete and 3 found-negative rows;
  - label-cap16 pruned 1729 labels but did not reduce incomplete or stabilize incumbent improvement;
  - label-cap32 had one improved and one worsened row, so the Phase 10C single-repeat improvement is not stable evidence;
  - no critical disagreement.
- Interpretation:
  - stop profile-DP mask-label-cap tuning as a mainline;
  - current bottleneck looks more like profile-DP ordering / column trajectory / RMP degeneracy than bucket width;
  - next phase should compare first returned task sets and active-pool interaction across improved/worsened repeats.
- Exactness boundary:
  - calibration only;
  - no Sharded Pulse worker/audit/certificate effect;
  - no dual stabilization;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 10E profile-DP ordering attribution:

- Added official negative task-set attribution fields to the calibration summary:
  - `official_negative_journey_task_set_count`;
  - `official_negative_journey_task_set_hash`;
  - `official_negative_journey_task_set_samples`;
  - `official_negative_journey_sequence_samples`;
  - `official_negative_journey_signature_samples`;
  - `official_negative_first_task_set`;
  - `official_negative_first_task_count`;
  - `official_negative_profile_dp_top_overlap`;
  - `official_negative_profile_dp_top_jaccard`;
  - `official_negative_profile_dp_top_relation`;
  - `official_negative_profile_dp_top_exact`.
- Ran 20-task repeat attribution:
  - `phase7o_20_smoke`;
  - `phase10c_profile_dp_mask_hotspot_sensitivity`;
  - repeat count = 3.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10e_profile_dp_ordering_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613`.
- Result:
  - no returned negative task-set exactly matched a profile-DP top mask;
  - in `mt20_greedy_tranq_01`, the best baseline repeat returned disjoint task-set `[13,16]` and reached incumbent `721.502279`;
  - label-cap profiles returned overlapping task-set `[1,6,15]` and worsened back to `761.814403`;
  - `mt20_greedy_apollo_01` differences had no returned negative task-set and appear to be active-pool / early trajectory differences.
- Interpretation:
  - stop top-mask chasing and label-cap tuning as optimization mainlines;
  - next phase should inspect active-pool / early column trajectory divergence;
  - do not re-enable Pulse worker or certificate gate.
- Exactness boundary:
  - diagnostics only;
  - no Sharded Pulse worker/audit/certificate effect;
  - no dual stabilization;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 10C profile-DP mask-hotspot sensitivity:

- Added global profile-DP hotspot summary fields:
  - `profile_dp_tail_label_cap_pruned`;
  - `profile_dp_tail_selected_candidate_input_count`;
  - `profile_dp_tail_selected_candidate_scanned_count`;
  - `profile_dp_tail_selected_candidate_materialized_count`;
  - `profile_dp_tail_selected_candidate_returned_count`;
  - `profile_dp_tail_selected_candidate_filtered_count`;
  - `profile_dp_tail_selected_unmaterialized_candidate_count`;
  - `profile_dp_tail_materialization_candidate_count`;
  - `profile_dp_tail_materialization_selected_candidate_count`;
  - `profile_dp_tail_materialization_infeasible_filtered_count`;
  - `profile_dp_tail_hotspot_class`;
  - `profile_dp_tail_hotspot_reason`.
- Added calibration-only 20-task profiles:
  - `experimental_profile_dp_mask_label_cap_16_20_only`;
  - `experimental_profile_dp_mask_label_cap_32_20_only`.
- Added aliases:
  - `phase10c_profile_dp_mask_hotspot_gate`;
  - `phase10c_profile_dp_mask_hotspot_sensitivity`.
- The mask-label-cap profiles are no-op for 5/10-task instances and only set
  `journey_pricing_profile_dp_max_labels_per_mask` for 20-task calibration runs.
- The profiles explicitly keep these disabled:
  - Sharded Pulse audit;
  - Sharded Pulse hidden-negative worker;
  - dual stabilization.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10c_profile_dp_mask_hotspot_sensitivity_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10c_profile_dp_mask_hotspot_sensitivity_smoke_20260613`.
- Result:
  - 5/10 no-op guard worked: no official result change and no critical disagreement;
  - 20-task label-cap16 pruned 574 labels and capped max labels/mask at 16, but did not reduce incomplete tails or improve incumbent;
  - 20-task label-cap32 improved one row (`mt20_greedy_apollo_01`) in a single repeat, but did not activate label-cap pruning and increased profile-DP time;
  - all selected profile-DP candidates in the smoke materialized and returned, so current blocker is not selected-mask materialization failure.
- Interpretation:
  - do not use label-cap as a production/default or certificate path;
  - label-cap16 is not a useful mainline optimization;
  - label-cap32 needs repeat validation before considering any further tuning;
  - if repeat is unstable, pivot to profile-DP ordering attribution / RMP column trajectory.
- Exactness boundary:
  - calibration profiles only;
  - no Sharded Pulse worker/audit/certificate effect;
  - no dual stabilization;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 9L previous-anchor dual stabilization gate:

- Added Phase 9L aliases:
  - `phase9l_previous_dual_stabilization_gate`;
  - `phase9l_previous_dual_stabilization_gate_ab`.
- The instance gate expands to:
  - all `balanced5_all` instances;
  - all `balanced10_all` instances;
  - the 3 feasible 20-task hard-smoke instances in `phase7o_20_smoke`.
- The profile group keeps only:
  - baseline;
  - `experimental_l1_previous_dual_stabilization_20_only`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9l_previous_dual_stabilization_gate_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9l_previous_dual_stabilization_gate_ab_smoke_20260613`.
- Smoke matrix:
  - 43 instances;
  - 2 profiles;
  - repeat count = 2;
  - 172 summary rows.
- Result:
  - 5-task full smoke gate: previous-anchor no-op, no official changes, no critical disagreement;
  - 10-task full smoke gate: previous-anchor no-op, no official changes, no critical disagreement;
  - 20-task hard smoke: previous-anchor had 4 improved rows and 2 worsened rows;
  - `mt20_greedy_tranq_01` was stable positive in both repeats;
  - `tranq20_01` and `mt20_greedy_apollo_01` remained mixed;
  - all accepted stabilized dual events had no current-pool negative, objective mismatch, current-pool infeasibility, or critical disagreement.
- Interpretation:
  - previous-anchor remains a useful diagnostic but is not stable enough for production tuning;
  - dual-stabilization production expansion should stop for now;
  - next work should pivot to legacy final judge / profile-DP proof-tail optimization.
- Exactness boundary:
  - calibration profiles only;
  - no production default change;
  - no Sharded Pulse worker/certificate effect;
  - stabilized dual remains disabled on certificate candidates;
  - no official certificate or lower-bound rule was relaxed.

2026-06-13 Phase 9K RMP/dual stabilization hardset A/B:

- Added Phase 9K aliases:
  - `phase9k_dual_stabilization_gate`;
  - `phase9k_rmp_dual_stabilization_hardset_ab`.
- Fixed ROI classifier:
  - for non-OPTIMAL 20-task comparisons, a worse incumbent primal is now `worsened` even if wall time is shorter;
  - this prevents reporting shorter TIME_LIMIT paths as improvement when incumbent quality degrades.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613`.
- Smoke matrix:
  - instances: `apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`, `mt20_greedy_apollo_01`, `tranq20_01`, `mt20_greedy_tranq_01`;
  - profiles: baseline, previous-anchor stabilization, zero-anchor stabilization;
  - repeat count = 3;
  - time limit = 3.0s, max CG = 8.
- Result:
  - 5/10 experimental rows remained no-op with no critical disagreement;
  - previous-anchor accepted 35 stabilized duals over 9 20-task rows and improved 6 rows, worsened 2, no-regressed 1;
  - zero-anchor accepted 42 stabilized duals over 9 20-task rows but improved 0 rows, worsened 5, no-regressed 4;
  - `mt20_greedy_tranq_01` previous-anchor was the stable positive signal: all 3 repeats improved primal from `761.814403` to `721.502279`;
  - all accepted stabilized dual events had no current-pool negative, objective mismatch, current-pool infeasibility, or critical disagreement.
- Interpretation:
  - zero-anchor should be paused as a candidate profile;
  - previous-anchor deserves one stricter validation round because it shows stable improvement on one 20-task hard smoke but mixed behavior elsewhere;
  - final target A is still not met.
- Exactness boundary:
  - calibration profiles only;
  - no production default change;
  - no Sharded Pulse worker/certificate effect;
  - stabilized dual remains disabled on certificate candidates;
  - no official certificate or lower-bound rule was relaxed.

2026-06-13 Phase 10F active-pool trajectory attribution:

- Added read-only ROI summary fields:
  - `pool_active_task_set_hash_first`;
  - `pool_active_task_set_hash_sequence`;
  - `pool_active_task_set_hash_unique_count`;
  - `pool_active_task_set_hash_churn_count`;
  - `pool_active_top_task_set_value_samples_first`;
  - `pool_active_trajectory_class`;
  - `pool_active_trajectory_reason`.
- Added `_classify_active_pool_trajectory()` for reporting-only labels:
  - `no_pool_diagnostics`;
  - `no_active_basis`;
  - `stable_active_basis`;
  - `churn_active_basis`;
  - `high_churn_active_basis`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10f_active_pool_trajectory_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10f_active_pool_trajectory_attribution_smoke_20260613`.
- Smoke matrix:
  - instances: `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - profiles: baseline, label-cap16, label-cap32;
  - repeat count = 3;
  - rows = 27.
- Result:
  - all 27 rows had no critical disagreement;
  - each profile still had 6 `INCOMPLETE_LIMIT` and 3 `FOUND_NEGATIVE` 20-task rows;
  - label-cap16/32 did not reduce incomplete tails;
  - label-cap16 and label-cap32 each improved only one `mt20_greedy_apollo_01` repeat;
  - the improved Apollo rows coincided with active-basis trajectory divergence to `c36666e846435b59` or `98e14b42b7f3753c`;
  - `tranq20_01` and `mt20_greedy_tranq_01` active trajectories were stable across profiles and had no outcome improvement.
- Interpretation:
  - profile-DP mask label-cap is not a stable mainline optimization;
  - label-cap behaves more like an early-column / active-pool trajectory perturbation than a proof-tail fix;
  - next work should target early active-pool trajectory attribution or controlled intervention, not wider label caps.
- Exactness boundary:
  - summary/reporting only;
  - no profile-DP transition change;
  - no Sharded Pulse worker/certificate effect;
  - no default benchmark change;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 10G early-column / active-pool attribution:

- Added read-only ROI summary fields:
  - `early_column_addition_events`;
  - `early_column_addition_kind_sequence`;
  - `early_column_primary_task_set_sequence`;
  - `early_column_changed_task_set_hash_sequence`;
  - `early_column_new_task_set_hash_sequence`;
  - `early_column_productivity_class_sequence`;
  - `early_column_active_hash_before_sequence`;
  - `early_column_active_hash_after_sequence`;
  - `early_column_active_hash_transition_count`;
  - `early_column_changed_active_relation_before_sequence`;
  - `early_column_changed_active_relation_after_sequence`;
  - `early_column_active_changed_task_set_count`;
  - `early_column_trajectory_class`;
  - `early_column_trajectory_reason`.
- Added `_early_column_trajectory_metrics()` and `_classify_early_column_trajectory()`.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10g_early_column_active_pool_attribution_zh.md`.
- Smoke output:
  - `BPC_future/results/sharded_pulse_phase10g_early_column_active_pool_attribution_smoke_20260613`.
- Smoke matrix:
  - instances: `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - profiles: baseline, label-cap16, label-cap32;
  - repeat count = 3;
  - rows = 27.
- Result:
  - all 27 rows had no critical disagreement;
  - each profile still had 6 `INCOMPLETE_LIMIT` and 3 `FOUND_NEGATIVE` rows;
  - all 27 rows were classified as `inactive_addition_enters_active_basis`;
  - early additions generally entered as inactive task sets, then appeared in later active-basis samples;
  - label-cap32 changed two `mt20_greedy_apollo_01` rows but did not reduce incomplete count;
  - `tranq20_01` and `mt20_greedy_tranq_01` early sequences stayed stable across profiles.
- Interpretation:
  - active-pool trajectory divergence is a plausible explanation for Apollo short-time incumbent changes;
  - label-cap is still not a stable proof-tail optimization;
  - next work should be either a very narrow early-column controlled intervention or a negative-result split, not more label-cap tuning.
- Exactness boundary:
  - summary/reporting only;
  - no pricing transition or pruning change;
  - no Sharded Pulse worker/certificate effect;
  - no default benchmark change;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 10H early-column controlled intervention:

- Added 20-only calibration profiles:
  - `experimental_early_new_task_set_quota_3_20_only`;
  - `experimental_early_new_task_set_quota_3_return12_20_only`.
- Added profile group:
  - `phase10h_early_new_task_set_quota`.
- Profile semantics:
  - only active for `task_count >= 20`;
  - require early-return to keep at least 3 new task sets;
  - return8 profile sets pricing/heuristic max returned journeys to 8;
  - return12 profile sets pricing/heuristic max returned journeys to 12;
  - selection mode is `diverse`;
  - Sharded Pulse audit, hidden-negative worker, and dual stabilization remain disabled.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10h_early_new_task_set_quota_zh.md`.
- Smoke outputs:
  - `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613`;
  - `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_5_10_guard_20260613`.
- 5/10 guard:
  - instances: `apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`;
  - both experimental profiles were no-op;
  - `official_result_changed_vs_baseline=False` for all 10 experimental rows;
  - primal/status/pricing matched baseline exactly.
- 20-task smoke:
  - instances: `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - repeat count = 3;
  - all 27 rows had no critical disagreement;
  - all profiles still had 6 `INCOMPLETE_LIMIT` and 3 `FOUND_NEGATIVE` rows.
- Result:
  - `tranq20_01` improved in all quota repeats;
  - `mt20_greedy_tranq_01` worsened under return8 but improved under return12;
  - `mt20_greedy_apollo_01` mostly worsened, with only one return8 repeat improving;
  - return8 profile had 4 improved / 5 worsened 20-task rows;
  - return12 profile had 6 improved / 3 worsened 20-task rows.
- Interpretation:
  - early new-task-set quota is a real trajectory intervention, not a stable optimization;
  - it changes active-pool / early-column paths, but does not reduce incomplete tails;
  - it should not be default-enabled and should not feed certificate or worker gates;
  - evidence now favors a negative-result synthesis or pivot toward RMP stabilization / pool compression / legacy final judge optimization.
- Exactness boundary:
  - calibration-only;
  - 20-only;
  - no Sharded Pulse worker/certificate effect;
  - no dual-stabilization effect;
  - no production default change;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 10I negative-result completion audit:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase10i_negative_result_completion_audit_zh.md`.
- Purpose:
  - audit `目标.md` final condition B against current evidence;
  - separate closed subroutes from the remaining full proof-route gap.
- Closed subroutes:
  - active hidden-negative worker / current-context probe / target-specific worker gates;
  - profile-DP state-cap and mask label-cap tuning;
  - early-column new-task-set quota profiles.
- Evidence now supports:
  - repeated worker/profile A/B did not establish stable ROI;
  - worker-added true-RC negative columns do not reliably reduce residual tail;
  - current 20-task candidates have no stable wall-time / proof-tail improvement;
  - no critical disagreement has been observed.
- Remaining final-condition B gap:
  - Phase 7J refinement proves exact-safe partition / aggregation, but does not prove production incomplete reduction;
  - proof-closed Sharded Pulse resume remains unimplemented / unverified as a proof route;
  - therefore the overall goal is still not complete.
- Decision:
  - do not expand Pulse worker, target ordering, label cap, DP cap, or early quota tuning;
  - do not enable production worker or official certificate gate;
  - next work should either:
    - complete the formal proof-route negative evidence for refinement/resume; or
    - pivot to RMP stabilization / pool compression / legacy final judge proof-tail optimization.
- Exactness boundary:
  - report/docs only;
  - no solver semantics change;
  - no default config change;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 11A profile-DP pricing-time sensitivity:

- Added 20-only calibration profiles:
  - `experimental_pricing_time_0_6_20_only`;
  - `experimental_pricing_time_1_0_20_only`.
- Added profile group:
  - `phase11a_profile_pricing_time_sensitivity`.
- Profile semantics:
  - only active for `task_count >= 20`;
  - set `journey_pricing_time_limit` to `0.6` or `1.0`;
  - Sharded Pulse audit, hidden-negative worker, and dual stabilization remain disabled.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase11a_profile_pricing_time_sensitivity_zh.md`.
- Smoke outputs:
  - `BPC_future/results/sharded_pulse_phase11a_profile_pricing_time_sensitivity_smoke_20260613`;
  - `BPC_future/results/sharded_pulse_phase11a_profile_pricing_time_sensitivity_5_10_guard_20260613`.
- 5/10 guard:
  - instances: `apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`;
  - both pricing-time profiles were no-op;
  - `official_result_changed_vs_baseline=False`;
  - primal/status/pricing matched baseline exactly.
- 20-task smoke:
  - instances: `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - repeat count = 2;
  - baseline had 4 `INCOMPLETE_LIMIT` and 2 `FOUND_NEGATIVE` rows;
  - both 0.6s and 1.0s profiles had 6 `INCOMPLETE_LIMIT` rows;
  - no critical disagreement.
- Result:
  - 0.6s profile had 4 improved / 2 worsened incumbent rows, but all rows hit `INCOMPLETE_LIMIT` and wall time approached the 3s cap;
  - 1.0s profile had 1 improved / 5 worsened rows;
  - `mt20_greedy_tranq_01` regressed from `FOUND_NEGATIVE` baseline to `INCOMPLETE_LIMIT` under both profiles.
- Interpretation:
  - profile-DP / legacy proof tail is not fixed by simply increasing pricing time;
  - more pricing time can perturb column-entry trajectory and convert negative-returning paths into incomplete paths;
  - do not use global pricing-time expansion as a production candidate;
  - if continuing condition A, focus on structured candidate ordering / returned-column selection or RMP trajectory, not coarse budget expansion.
- Exactness boundary:
  - calibration-only;
  - 20-only;
  - no Sharded Pulse worker/certificate effect;
  - no dual-stabilization effect;
  - no production default change;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 11B profile-DP selection-mode sensitivity:

- Added 20-only calibration profiles:
  - `experimental_profile_selection_integer_diverse_20_only`;
  - `experimental_profile_selection_orthogonal_20_only`.
- Added profile group:
  - `phase11b_profile_selection_mode_sensitivity`.
- Profile semantics:
  - only active for `task_count >= 20`;
  - set `journey_pricing_selection_mode` and `journey_heuristic_selection_mode` to `integer_diverse` or `orthogonal`;
  - Sharded Pulse audit, hidden-negative worker, and dual stabilization remain disabled.
- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase11b_profile_selection_mode_sensitivity_zh.md`.
- Smoke outputs:
  - `BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_smoke_20260613`;
  - `BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_state1000_smoke_20260613`;
  - `BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_5_10_guard_20260613`.
- 5/10 guard:
  - instances: `apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`;
  - both experimental profiles were no-op;
  - `official_result_changed_vs_baseline=False`;
  - primal/status/pricing matched baseline exactly.
- 20-task state-cap smoke:
  - instances: `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - repeat count = 2;
  - with `pricing_max_dp_states=1`, all profiles had 6 `INCOMPLETE_LIMIT` rows;
  - selected-candidate input/materialized/returned counts were all zero, so selection mode did not get a chance to operate.
- 20-task activation smoke:
  - same instances and repeat count;
  - with `pricing_max_dp_states=1000`, all profiles had 6 `FOUND_NEGATIVE` rows;
  - integer-diverse and orthogonal did not change official outcomes;
  - selected-candidate counts matched baseline at 72 input / 18 materialized / 18 returned;
  - one orthogonal `mt20_greedy_tranq_01` repeat changed the returned task set but did not improve primal/status.
- Interpretation:
  - simple returned-column selection-mode changes are not a stable optimization;
  - in the hardest cap setting, the blocker is before selection;
  - when selection runs, it can perturb individual returned columns but does not reduce tail or improve official result.
- Exactness boundary:
  - calibration-only;
  - 20-only;
  - no Sharded Pulse worker/certificate effect;
  - no dual-stabilization effect;
  - no production default change;
  - no official certificate or lower-bound rule relaxed.

2026-06-13 Phase 11C proof-route refinement / resume audit:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase11c_proof_route_refinement_resume_audit_zh.md`.
- Purpose:
  - audit the remaining final-condition-B gap around refinement / proof-closed resume;
  - avoid treating worker / selection / budget negative evidence as a complete proof-route negative result.
- Static implementation audit:
  - `sharded_pulse_final_judge.py` has ledger/cache-key/dummy scaffolding;
  - `ShardProofRecord.proof_closed=False` cannot become certificate;
  - frontier snapshot is tested as non-proof;
  - `JourneyPricingConfig.pulse_resume_enabled` exists, but no Sharded Pulse proof-closed persistent resume consumption path is implemented;
  - existing profile catalog / profile-label resume is legacy/profile-DP resume, not shard proof-ledger resume.
- Dynamic smoke output:
  - `BPC_future/results/sharded_pulse_phase11c_proof_route_refinement_resume_audit_20260613`.
- Smoke matrix:
  - instances: `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`;
  - profiles: baseline, `audit_no_refine`, `audit_refine`;
  - repeat count = 2;
  - rows = 18.
- Official-result guard:
  - all rows had no critical disagreement;
  - `official_result_changed_vs_baseline=False`;
  - audit-only caused no worker, certificate, or official lower-bound effect.
- Result:
  - `audit_no_refine`: 120 total shards, 2 certified, 108 incomplete, 10 negative, 0 refined, 46 harvested;
  - `audit_refine`: 120 total shards, 2 certified, 108 incomplete, 10 negative, 0 refined, 46 harvested;
  - adaptive refinement did not reduce incomplete or increase certified shards in the hard-tail smoke.
- Interpretation:
  - current 20-task audit contexts quickly produce negative shard signals, so the path is hidden-negative/audit signal rather than no-negative proof-completion;
  - second-action refinement does not activate in this shape and therefore does not reduce incomplete;
  - proof-closed resume remains unimplemented/unverified, so final condition B is still not closed.
- Exactness boundary:
  - audit-only;
  - no worker/certificate/lower-bound effect;
  - no default config change;
  - no unsafe pruning;
  - no resume cache reuse as proof.

2026-06-13 Phase 11D final negative-result / pivot:

- Added report:
  - `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase11d_final_negative_result_pivot_zh.md`.
- Purpose:
  - stop expanding the current `Sharded Pulse worker/proof` route;
  - avoid treating an unimplemented proof-closed resume path as current-route evidence;
  - record the final negative-result / pivot decision for the implemented route.
- Resume boundary:
  - Sharded Pulse proof-closed persistent resume is not implemented;
  - `pulse_resume_enabled` remains a configuration field, not a consumed shard proof-ledger resume path;
  - profile catalog / profile-label resume is not equivalent to Sharded Pulse proof-closed resume;
  - future proof-closed resume work must be a new phase with context-hash validation and fresh-vs-resume exactness tests.
- Evidence summary:
  - Phase 7O: 24 hard-tail A/B rows, all `TIME_LIMIT / INCOMPLETE_LIMIT`, no critical disagreement, worker events present but no stable tail reduction;
  - Phase 8Q: worker returned/added 10 true-RC negative journeys, including 8 new task sets and 2 support-changing additions, but the matrix still had no stable official improvement;
  - Phase 9J: dual-stabilization repeat A/B did not create a stable improvement signal;
  - Phase 11B: 5/10 guard had no official regression, but profile-selection changes did not improve the hard set;
  - Phase 11C: adaptive refinement did not reduce incomplete shards (`audit_no_refine` and `audit_refine` both 120 / 2 / 108 / 10 / 0 total/certified/incomplete/negative/refined).
- Final condition-B interpretation:
  - for the currently implemented Pulse worker/proof route, the negative-result / pivot condition is satisfied;
  - proof-closed resume is explicitly removed from this route rather than claimed as tested;
  - no certificate, lower-bound, or production-default semantics are changed.
- Pivot recommendation:
  - stop worker budget/gate/profile-DP-cap/label-cap/early-quota/selection-mode expansion;
  - do not open official certificate gate;
  - pivot to RMP stabilization, active-family stabilization, column pool compression / impact filtering, or legacy final judge / profile-DP proof-tail optimization.
