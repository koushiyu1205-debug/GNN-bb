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
