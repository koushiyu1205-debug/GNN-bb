# Exact Pricing Completion Bounds Design Notes

This document records the agreed design contract for accelerating the
true-dual exact pricing certificate tail in `BPC_future`.  It complements
`learning_dual_stabilization_design.md`: learning-based Wentges smoothing is a
heuristic column generator, while the mechanisms below target the official
true-dual certificate path.

## Performance Goal

The current engineering target is:

```text
5-task instances:  under 5 seconds
10-task instances: under 60 seconds
20-task instances: under 200 seconds
```

The learning component should make the solver find the same or better incumbent
earlier, concentrate true-RC negative columns, and reduce RMP iterations.  The
completion-bound component should reduce the expensive true-dual exact pricing
proof tail.

## Exactness Contract

- This feature is an exact-pricing accelerator, not a heuristic certificate.
- It is enabled only in true-dual certificate pricing.
- It must never prune a label unless the bound is a valid optimistic lower bound
  on every feasible continuation.
- If a pricing run hits any limit, the result remains incomplete.
- Official lower bounds and optimality certificates still require true-dual
  exact pricing exhaustion.
- Historical probes kept the feature opt-in while benchmarking.  The current
  5/10/20 mainline configs require it as a Level-4 final-probe judge, with
  fail-closed validation and positive runtime/state budgets.

## Current Optimization Priorities (2026-06-06)

The current implementation and tuning work must follow this priority order.
The purpose is to keep the proof chain exact while turning the expensive final
judge back into a certificate oracle rather than a repeated negative-column
worker.

2026-06-06 reminder: this section records the active six-priority engineering
roadmap and is the authoritative order for the next code changes.  Before
making any pricing or learning change, identify which priority below the change
serves.  Do not jump straight to parameter tuning when the pricing status
semantics or hidden-negative audit evidence is still ambiguous.  If a pricing
result cannot be proven to come from the true-dual direct-label judge, treat it
as worker evidence only.  The default fallback for ambiguous no-column outcomes
is `LOCAL_NO_COLUMN_UNCERTIFIED`, never `CERTIFIED_NO_NEGATIVE`.

Operational rule: read this section before touching pricing dispatch,
direct-label pricing, completion bounds, profile/streaming workers, or learning
dual stabilization.  Changes should proceed in priority order unless there is a
fresh log proving that an earlier priority is already satisfied for the current
failure mode.  In particular, do not let a performance patch bypass the status
semantics, and do not let a worker-local no-column result become an official
certificate.

Self-reminder for future implementation sessions: the next optimization should
not be chosen by whichever knob looks convenient in the config.  The queue is:
status semantics, hidden-negative audit, final-judge harvesting, CB trigger
control, worker batching semantics, then tail dual center.  A patch that cannot
be mapped to one of these six priorities should be deferred or documented as a
diagnostic only.

### 中文执行清单：当前六个优先级

这一节是给后续实现和调参时反复回看的短清单。代码修改和优化必须按照下面六个优先级推进。不要跳过前面的语义修复去直接调性能参数，否则日志会继续混淆 worker 与 judge，难以判断到底是谁漏列、谁在证明。
后续每次改 pricing 或 learning 相关代码前，先标明该改动服务于哪一个优先级；
如果说不清，就先回到优先级 1 和 2 做语义与 hidden-negative 审计。

1. **优先级 1：修正 pricing 状态语义。**
   先把状态拆清楚：
   `FOUND_NEGATIVE`、`LOCAL_NO_COLUMN_UNCERTIFIED`、
   `CERTIFIED_NO_NEGATIVE`、`INCOMPLETE_LIMIT`、`DUPLICATE_ONLY`。
   只有 `CERTIFIED_NO_NEGATIVE` 可以产生官方 lower bound 或节点 LP
   certificate。`profile exhausted` 只能表示 profile universe 内没列，
   不能污染全局收敛语义。否则无法分清哪个 oracle 是 worker，哪个 oracle
   是 judge。这一步仍然是第一优先级，未确认前不要继续调 worker 或 CB
   参数。

2. **优先级 2：hidden-negative audit 定位漏列原因。**
   继续记录：
   `ordinary/profile local no-column -> direct-label / completion-bound found hidden negative`。
   每个 hidden negative 都要定位它为什么漏：没生成、被 task-set bound 剪、
   被 resource pruning 剪、被 profile dominance 剪、被 catalog/resume 漏、
   被 duplicate/signature filter 误过滤，还是 reduced cost 口径不一致。
   这一步的目标是修 worker，不是直接提速。若 direct-label / CB 已经构造出
   true-dual negative journey，可以把其中的 feasible timed sorties 作为
   fixed-start physical profiles 种回 profile worker 的 physical catalog，
   让后续 worker 不再重复漏同一类 sortie mask；但这种 seed 只修候选宇宙，
   不能改变 profile no-column 的 `LOCAL_NO_COLUMN_UNCERTIFIED` 语义。

3. **优先级 3：在 Final Judge 中加入 Pareto-Harvesting / Orthogonal Harvesting。**
   这是当前最值得立刻做的性能改动。completion-bound / direct-label judge
   找到负列后，不应立即返回少量列，而要收割一批 true-RC 负列，按 reduced
   cost 与 task-set diversity 批量返回给 RMP。优先记录：
   `harvest_candidate_negative_count`、`harvest_selected_count`、
   `harvest_rejected_overlap_count`、`harvest_fallback_fill_count`、
   `harvest_best_true_rc`、`harvest_worst_selected_true_rc`、
   `harvest_avg_pairwise_jaccard`。同时必须区分
   `harvest_selected_new_task_set_count` 与
   `harvest_selected_replacement_task_set_count`：replacement-only batch 只是在
   改善已有 task-set 的物理代表，不等价于扩张 RMP 方向。目标是让 Final
   Judge 盖证书或一次性收割一批正交负列，而不是每轮只交回 1-2 条列后继续
   充当昂贵 worker。

4. **优先级 4：控制 CB / Final Judge 的触发时机。**
   CB 是法官，不是早期工人，不能太早、太频繁变成 worker。建议触发条件：
   root node、`certificate_candidate=True` 或 objective flat、ordinary/profile
   返回 `LOCAL_NO_COLUMN_UNCERTIFIED`、remaining time 足够。不要在 early
   discovery 阶段频繁打开重型 CB。

5. **优先级 5：profile/streaming worker 改成批量找列，不承担证书。**
   profile/streaming 的职责是尽快批量发现有用负列，不是证明没有负列。
   它找不到列时必须返回 `LOCAL_NO_COLUMN_UNCERTIFIED`，而不是
   `CERTIFIED_NO_NEGATIVE`。如果 worker 找列成功，可以引入轻量版
   harvesting，按 true RC 与 task-mask diversity 返回列，但 Final Judge
   的 harvesting 优先做。

6. **优先级 6：tail dual center / stabilization 加强。**
   对偶震荡仍然是根本原因之一。进入 tail 后要维护更稳定的 dual center，
   减少 objective flat、`dual_l1_delta` 很大、hidden negative 一轮轮冒出的
   现象。GNN 暂时不要作为 tail breaker，只作为 early/mid worker 辅助或
   hidden-negative task-set 排序器。若学习 worker 连续产出被 true-RC
   过滤掉的列，可以把 anchor 权重降到专门的失败地板（10/20 主线为
   `0.05`），但不能让它参与 official certificate。tail dual center 的
   目标是减少乒乓式 hidden negative，而不是替代最终 true-dual judge。

Global constraints:

- Avoid per-instance special configs whenever possible.
- GNN anchors, resource-aware completion bounds, and 2-cycle bounding may be
  optimized and tightened, but must not be silently disabled.
- Pricing dispatch should remain a healthy multi-level funnel: cheap workers
  first, true-dual judge last.
- Exactness is non-negotiable; only a certified true-dual no-negative result may
  close a node or contribute an official lower bound.
- Pricing time budgets should leave a small deadline safety margin before the
  outer solver limit.  Internal pricing loops check deadlines at coarse
  granularity, so passing the full remaining wall-clock budget can overrun the
  engineering limit without improving proof validity.
- Benchmark limits for engineering runs: 5/10-task runs may use `120s`; 20-task
  runs may use `600s`.  Final performance targets remain 5-task under `10s`,
  10-task under `60s`, and 20-task under `200s`, all with exact solutions.
- Do not simply disable static SRC as a pricing shortcut.  A 10-task hard-case
  probe showed that this can certify the root faster but weakens the bound
  enough to force branching and still timeout.  If revisited, use delayed,
  budgeted, or ranked SRC activation.
- An opt-in compact-ranked SRC selector exists for experiments, but a budget-60
  hard-case probe still timed out at the root.  Do not enable it by default
  unless paired with stronger delayed activation or harvesting evidence.
- Keep hidden-negative audit bounded.  It is a diagnostic tool for worker
  repair, not part of the proof.  Use
  `journey_hidden_negative_audit_max_logged_journeys` to cap detailed journey
  payloads, especially before running 20-task probes.  In benchmark/mainline
  runs the current default is `0`, which disables the audit completely; turn it
  back on only for targeted leak hunts.
- Keep profile mask diagnostics disabled in benchmark/mainline runs unless a
  hidden-negative audit specifically needs the mask evidence.  The profile
  worker can still return columns and the final judge can still certify without
  constructing these diagnostic sets.
- Before re-enabling a previously rejected default, check
  `optimization_failure_notes.md`.

### Priority 1: Fix Pricing Status Semantics

Pricing status must be explicit.  Do not let a worker oracle's local
`no-column` result look like a global proof.

Implementation update, 2026-06-06:

- `JourneyPricingConfig` now carries an explicit
  `direct_journey_label_global_certificate_enabled` switch.
- `JourneyPricingResult` now carries `global_certificate_capable`.
- `completion_bound_enabled=True` is no longer sufficient to create an
  official certificate.  A no-negative result can become
  `CERTIFIED_NO_NEGATIVE` only when the direct-label result is also explicitly
  marked `global_certificate_capable=True`.
- Hidden-negative patrol, learning pricing, profile repair, replacement repair,
  and completion-bound audit fallback clear this flag.  They are workers even
  if they internally use direct-label or completion-bound machinery.
- `_journey_completion_bound_final_probe_needed()` now trusts only
  `CERTIFIED_NO_NEGATIVE`; it no longer skips the final judge merely because a
  previous worker had `completion_bound_enabled=True` and `exhausted=True`.
- A smoke run on
  `apollo15_20km_tasks05_01_seed6000_logical_graph.json` closed exactly in
  `2.295682s`; the log shows ordinary profile no-column as
  `LOCAL_NO_COLUMN_UNCERTIFIED`, hidden-negative patrol as non-certificate, and
  the completion-bound retry as `CERTIFIED_NO_NEGATIVE/global_certificate=true`.
- A hard-tail probe on
  `tranquillitatis_balmer_like_20km_tasks10_09_seed11144_logical_graph.json`
  still timed out at the root in `118.848344s`.  The semantic fix did not solve
  the performance bottleneck: ordinary exact/profile spent about `63.94s` in
  profile generation and `18.73s` in profile DP; completion-bound retries spent
  about `26.20s` and selected mostly replacement columns (`15` replacement vs
  `1` new task-set direction).  This confirms the next optimization must still
  target worker strength/new task-set directions or stronger proof bounds, not
  certificate semantics alone.

Priority-2 audit update, 2026-06-06:

- Hidden-negative audit now emits a compact
  `journey_hidden_negative_audit_reason_summary` event when a hidden-pricing
  call returns multiple true-dual negative journeys.  The summary aggregates
  primary and candidate miss reasons over the whole hidden-negative batch,
  instead of relying only on the first few detailed journey payloads capped by
  `journey_hidden_negative_audit_max_logged_journeys`.
- The audit primary-reason rule now prefers per-hidden-journey mask evidence
  over global worker counters.  For example, a global
  `weak_negative_journeys_filtered` counter is recorded as supporting evidence,
  but it should not hide the more actionable fact that the hidden task set was
  reached by profile DP and still failed to become a negative candidate.
- A 120s hard 10-task probe
  `probe_hna_reason_summary_tranq10_09_20260606.csv` still timed out at the
  root (`status=TIME_LIMIT`, `columns=496`).  The compact audit showed that all
  summarized hidden negatives had their final task masks and sortie masks
  present in the ordinary worker universe (`profile_mask_hit=20/20`,
  `reachable_mask_hit=20/20`, `all_trip_masks_hit=20/20`), but none appeared as
  ordinary negative or selected masks (`negative_mask_hit=0`,
  `selected_mask_hit=0`).  This narrows the current worker gap: the hard case is
  not primarily missing physical sortie profiles; the profile/journey DP
  objective and materialization layer are failing to turn already-reached
  hidden task sets into true-RC negative worker columns.

Required state vocabulary:

```text
FOUND_NEGATIVE
LOCAL_NO_COLUMN_UNCERTIFIED
CERTIFIED_NO_NEGATIVE
INCOMPLETE_LIMIT
DUPLICATE_ONLY
```

Only this state may produce an official lower bound or node LP certificate:

```text
CERTIFIED_NO_NEGATIVE
```

This remains the first priority.  Without this separation, logs and control flow
cannot reliably tell which oracle is a worker and which oracle is the judge.

### Priority 2: Hidden-Negative Audit For Worker Repair

Continue recording this transition:

```text
ordinary/profile local no-column
  -> direct-label / completion-bound found hidden negative
```

For each hidden negative, identify why the worker missed it:

- the journey was never generated;
- task-set bound pruning removed it;
- resource pruning removed it;
- profile dominance removed it;
- catalog/resume logic skipped it;
- duplicate or forbidden-signature filtering removed it incorrectly;
- reduced-cost components were inconsistent between worker and judge.

Minimum audit payload:

```text
instance
cg_iter
node_id
dual_hash
cut_hash
ordinary_status
ordinary_reason
ordinary_exhausted
CB_found_journey_signature
CB_journey_task_set
CB_journey_cost
CB_true_reduced_cost
CB_reduced_cost_components:
  journey_cost
  cover_dual_sum
  fleet_dual
  cut_dual_sum
forbidden_signature_hit?
duplicate_filtered?
```

For the same RMP state, the audit should be able to answer three questions:

1. Recompute the CB journey with `manual_journey_reduced_cost`, including
   cover dual, fleet dual, and cut dual, and verify that the true RC matches.
2. Re-run ordinary exact/profile with streaming early return disabled, caps
   disabled, and enough time, then check whether it finds the same journey or
   an equivalent negative journey.
3. If ordinary exact/profile still misses the negative journey, trace the miss
   through:
   `task_set_bound_pruning`, `task_set_resource_pruning`,
   `profile_cross_dominance`, `profile_online_dominance`,
   `physical_catalog_resume`, `forbidden_journey_signatures`,
   `dominant_task_set_costs`, and duplicate filtering.

This audit is for repairing worker pricing.  It must not be treated as a speed
optimization by itself.  Its immediate purpose is to confirm whether ordinary
exact/profile `exhausted` is really a complete certificate, or only a local
no-column result inside a restricted worker universe.

### Priority 3: Pareto-Harvesting / Orthogonal Harvesting In Final Judge

This is the highest-value immediate performance change.  When the
completion-bound or direct-label judge finds negative columns, it should not
return only one or two columns after paying the full exact-search cost.  It
should harvest a batch of true-RC negative journeys and select them by reduced
cost plus task-set diversity before returning them to the RMP.

Required logs:

```text
harvest_candidate_negative_count
harvest_selected_count
harvest_rejected_overlap_count
harvest_fallback_fill_count
harvest_best_true_rc
harvest_worst_selected_true_rc
harvest_avg_pairwise_jaccard
```

Implementation reminder: use the current orthogonal-harvest proposal below as
the default implementation sketch.  The fallback fill phase is allowed to fill
the batch with the remaining strongest true-RC negative columns after signature
filtering, even when task sets overlap, because the immediate goal is to stop
the final judge from returning only one or two columns after an expensive full
search.  This must be logged carefully with `harvest_rejected_overlap_count`,
`harvest_fallback_fill_count`, and duplicate-task-set/new-task-set counts so we
can verify whether fallback fill is widening RMP directions or merely inflating
the matrix with physical replacements.

Implementation invariant: the `top_k_strongest` phase must always be evaluated
on global true reduced cost before any new-task-set preference is applied.  The
new-task-set preference is useful for widening RMP directions, but it must not
displace the globally strongest negative column when the harvest budget is
small.

Reference pseudocode:

```python
def harvest_orthogonal_negative_journeys(
    candidate_journeys,
    *,
    true_duals,
    cuts,
    forbidden_signatures,
    eps=1e-6,
    max_columns=64,
    top_k_strongest=5,
    min_fill=20,
    max_jaccard=0.5,
    max_containment=0.8,
):
    scored = []
    for journey in candidate_journeys:
        if journey.signature in forbidden_signatures:
            continue
        true_rc = manual_journey_reduced_cost(journey, true_duals, cuts)
        if true_rc >= -eps:
            continue
        mask = int(journey.task_mask) if hasattr(journey, "task_mask") else _task_mask(journey.task_set)
        size = mask.bit_count()
        if size <= 0:
            continue
        scored.append((true_rc, mask, size, journey))

    scored.sort(key=lambda item: item[0])  # 越负越好

    selected = []
    selected_masks = []

    # 1. 强制保留最强负列。
    for true_rc, mask, size, journey in scored[:top_k_strongest]:
        selected.append((true_rc, journey))
        selected_masks.append(mask)

    # 2. 再做正交收割。
    for true_rc, mask, size, journey in scored[top_k_strongest:]:
        if len(selected) >= max_columns:
            break
        diverse = True
        for selected_mask in selected_masks:
            overlap = (mask & selected_mask).bit_count()
            selected_size = selected_mask.bit_count()
            union = size + selected_size - overlap
            jaccard = overlap / max(1, union)
            containment = overlap / max(1, min(size, selected_size))
            if jaccard > max_jaccard or containment > max_containment:
                diverse = False
                break
        if diverse:
            selected.append((true_rc, journey))
            selected_masks.append(mask)

    # 3. fallback：若太少，用剩余最负列补齐到 min_fill。
    if len(selected) < min_fill:
        selected_signatures = {journey.signature for _, journey in selected}
        for true_rc, mask, size, journey in scored:
            if len(selected) >= min(max_columns, min_fill):
                break
            if journey.signature in selected_signatures:
                continue
            selected.append((true_rc, journey))
            selected_signatures.add(journey.signature)

    selected.sort(key=lambda item: item[0])
    return [journey for _, journey in selected[:max_columns]]
```

### Probe Notes: 10-task hard tail batching (2026-06-05)

Instance:
`tranquillitatis_balmer_like_20km_tasks10_09_seed11144`.

Observed baseline after status-semantics and hidden-negative audit fixes:

- The hard tail is not mainly caused by repeated final-judge calls anymore.
- Ordinary true-dual exact/profile generation dominates wall-clock: about
  `1.45M` generated sequences and `64-69s` profile generation on this single
  instance.
- Early exact/profile returned exactly `16` negative journeys per call although
  many more true-dual negative candidates existed.

Batching decision:

- Raising late worker thresholds to
  `journey_pricing_late_early_return_negative_min_count = 48` and
  `journey_pricing_late_streaming_min_negative_batch = 48` is directionally
  useful.
- It moved the root LP objective to `203.102839` by CG iteration 9 instead of
  about iteration 19, reduced exact pricing calls from `34` to `29`, and
  increased useful true-dual exact columns from `235` to `290`.
- It still does not solve the hard instance within `120s`, because profile
  universe construction remains expensive.

Final-judge harvesting decision:

- Increasing the diverse-harvest soft return from `5@10s` to `15@15s` made the
  first completion-bound retry return 15 columns instead of 7.
- This reduced pricing calls slightly but did not solve the instance within
  `120s`; keep it as a modest improvement, not as the main breakthrough.

Negative result:

- Moving hidden-negative patrol before ordinary exact/profile was tested with a
  certificate-candidate guard.
- It can still trigger around a suboptimal incumbent plateau and cause the run
  to stall at `203.263873`, worse than the normal late-batch path.
- Therefore `journey_hidden_negative_patrol_before_exact_flat_enabled` must stay
  disabled by default.  It remains a diagnostic switch only.

Additional diagnostics added:

- Hidden-negative audit now flattens the true reduced-cost components:
  `CB_reduced_cost_journey_cost`, `CB_reduced_cost_cover_dual_sum`,
  `CB_reduced_cost_fleet_dual`, `CB_reduced_cost_cut_dual_sum`, and
  decomposition error.
- Profile DP now records a bounded `best objective by task mask` diagnostic so
  audits can report `ordinary_hidden_task_mask_best_profile_objective`.

Follow-up findings:

- For several hidden negatives, ordinary profile DP did reach the same task
  mask, but its best profile objective was exactly `0.0` while direct-label
  true RC was around `-0.9` to `-1.3`.  This means the profile worker's local
  route universe is missing a cheaper physical realization; it is not merely
  duplicate filtering.
- The diagnostic was refined to compare hidden direct-label trip
  contributions with the best profile contribution for the same sortie
  task-mask.  On the hard `tranq10_09` probe, comparable single-sortie hidden
  negatives showed profile contribution gaps of roughly `0.49` to `2.08`
  reduced-cost units, with mean about `1.17`.  This confirms the worker had
  the same sortie task-mask but a weaker physical representative.
- A late `orthogonal` worker selection mode was added and enabled in the
  5/10/20 mainline configs.  It is exact-safe because it only changes which
  already true-RC negative worker candidates are batched into the RMP.  On the
  hard `tranq10_09` case it had near-identical aggregate behavior to the
  previous reduced-cost late selection because most failing rounds had
  `profile_negative_candidate_count = 0`; therefore candidate selection is not
  the current primary bottleneck.
- A diagnostic override disabling physical-catalog resume showed the opposite
  tradeoff: dual-specific profile generation found more worker columns and
  avoided hidden-negative audits in the sampled run, but spent much more time
  in profile generation and still timed out.  The right direction is a hybrid
  repair worker after `LOCAL_NO_COLUMN_UNCERTIFIED`, not globally dropping the
  physical catalog.
- Disabling profile cross-count dominance was tested and rejected.  It increased
  DP states substantially without eliminating hidden negatives.
- Increasing hidden-negative patrol from `0.5s` to `1-2s` found more direct
  negative columns and reduced one CB call, but it also increased ordinary
  exact/profile work and did not improve wall-clock.
- Increasing completion-bound time/energy buckets from `10/10` to `15/15` was
  rejected.  Bound construction and two-cycle table size roughly doubled, while
  label pruning did not improve enough.
- Raising late batch all the way to `96` reduced exact calls but inflated the
  RMP column pool and shifted cost into CB; keep `48` as the current practical
  late-worker batch size.
- Later compact-SRC probes showed a different final-judge pathology:
  completion-bound direct-label pricing can accumulate hundreds of true-RC
  negative physical candidates but only a few unique task-set directions
  (`362` candidates, `358` duplicate-task-set rejections, `4` selected
  journeys).  This is not an overlap-threshold problem.  It is duplicate
  task-set saturation: the judge is rediscovering physical variants of the
  same few RMP directions.  The soft-return rule should therefore allow an
  early return when completion-bound harvesting is duplicate-saturated and the
  elapsed/remaining-time condition is met, instead of burning the rest of the
  pricing budget chasing an unreachable diversity target.

### Priority 4: Control CB / Final-Judge Trigger Timing

Completion Bound must not become an early discovery worker.  It should be
expensive, true-dual, and late.

Preferred trigger conditions:

- root node first;
- `certificate_candidate=True` or objective-flat tail behavior;
- ordinary/profile pricing returns `LOCAL_NO_COLUMN_UNCERTIFIED`;
- enough remaining time is available for the judge to finish or fail cleanly.

Do not frequently open heavy completion-bound pricing during early discovery
rounds.

### Priority 5: Profile/Streaming Worker Finds Columns In Batches

Profile/streaming pricing is a worker, not a proof oracle.  Its job is to find
useful negative columns quickly and in batches.  If it cannot find a column, it
should return:

```text
LOCAL_NO_COLUMN_UNCERTIFIED
```

It must not return:

```text
CERTIFIED_NO_NEGATIVE
```

When worker pricing does find columns, it may use a lightweight harvesting pass
based on true reduced cost and task-mask diversity.  Final-judge harvesting has
priority and should be implemented first.

If hidden-negative patrol or the completion-bound judge returns feasible
true-dual journeys, their timed sorties may seed the profile physical catalog as
fixed-start profiles.  This is worker repair only: the profiles are still
re-filtered under the current duals, and profile exhaustion still cannot certify
global no-negative-column status.

### Priority 6: Tail Dual Center / Stabilization

Dual oscillation remains one root cause of the tail.  In the tail, maintain a
more stable dual center to reduce:

- flat objective rounds;
- large `dual_l1_delta`;
- repeated hidden negatives appearing one round at a time.

The GNN anchor should not be used as a tail breaker or certificate object.  It
remains an early/mid worker guide, and may later help rank hidden-negative task
sets, while true-dual pricing remains responsible for proof.

## Primary Target

First implementation target:

```text
direct journey-label pricing at the root certificate tail
```

Do not start with sortie profile generation.  The root true-dual certificate is
the dominant bottleneck; sortie-profile generation can reuse the same idea later
if the direct-label version is validated.

Branch depth policy:

```text
depth = 0: eligible
depth > 0: disabled by default
```

Deep branch nodes have smaller search spaces and branch constraints that are
harder to represent safely in a relaxed lower bound.  Root-first keeps the first
implementation focused on the dominant proof tail.

## Activation Policy

Completion bounds are tail-only.  They should activate only after heuristic or
smoothed-dual pricing fails and the solver is entering true-dual certificate
pricing.

Do not enable this heavy bound in early or middle CG rounds.  In those rounds,
GNN-smoothed pricing and lightweight heuristics are expected to find negative
columns cheaply.

Role definition:

```text
Completion Bound is a final optimality-certificate generator, not a negative-column worker.
```

If ordinary heuristic/profile pricing can still cheaply produce even one true-RC
negative column, the completion-bound direct-label oracle should stay off.  A
standard exact pricing call that exhausts and returns no negative column is
already a valid certificate; it must not be followed by a redundant bound retry.
Completion Bound is reserved for a final probe after an ordinary exact attempt
is incomplete, for example because of a soft time limit or label budget.
Budget pre-reservation for that final probe must also be conservative: it must
not shorten ordinary Level 2/3 pricing during early discovery.  The current
mainline therefore gates pre-retry reserve on `certificate_candidate=True`, on
the final completion-bound probe being eligible, and on a low remaining-time
threshold.  The 5-task configuration keeps this reserve disabled.  The 10-task
configuration reserves up to `8s` only when remaining wall time is at most
`35s`; the 20-task smoke configuration reserves up to `15s` only when remaining
wall time is at most `180s`.  This protects the true-dual final judge from
being starved without letting Completion Bound become an early worker.  The
reserve must also leave at least the ordinary retry minimum time for the first
worker attempt; it must not create sub-second profile/direct-label calls that
cannot meaningfully search.

The `certificate_candidate` gate remains the default activation trigger.  Branch
nodes that need a true-dual exact-pricing proof but are not incumbent candidates
can opt in separately with:

```text
journey_certificate_completion_bound_exact_proof_enabled
journey_certificate_completion_bound_exact_proof_min_depth
journey_certificate_completion_bound_exact_proof_min_incomplete_rounds
```

This opt-in only affects exact-pricing proof calls.  Candidate-only controls such
as fast negative return and full-scan cadence remain gated by
`certificate_candidate`.  The default minimum depth is `1`, so non-candidate
root pricing is not rewritten into direct-label bound pricing.  The default
minimum incomplete count is `1`, so a non-candidate branch node first tries the
existing profile/streaming exact pricing path; the completion-bound direct-label
path is used only after an incomplete proof attempt.

## Bound Rebuild Policy

The lower bound must be rebuilt for each true-dual pricing call.  The reduced
cost network changes whenever task-cover duals change:

```text
arc/task reduced costs depend on the current true RMP pi
```

The rebuild is acceptable because the bound is a relaxed polynomial-time
precomputation, while exact pricing expansion is exponential in the hard tail.

## Bound State

Current V1 state:

```text
LB(node_id, time_bucket, energy_bucket)
```

Do not include NG memory, predecessor memory, remaining task slots, bitmasks, or
future-sortie counters in the main reverse-bound state.  The reverse bound is
intentionally memoryless and allows repeated node visits; this is safe as long
as the value stays optimistic.  Future sorties are represented only by a scalar
global optimistic sortie floor.

Configuration knobs:

```text
completion_bound_time_buckets: configurable, suggested 5-15
completion_bound_energy_buckets: configurable, suggested 5-15
```

The implemented direct journey-label bound uses a coarse time+energy resource
envelope for the main suffix table.  The state count is:

```text
(number_of_tasks + 1 depot) * (time_buckets + 1) * (energy_buckets + 1)
```

Energy buckets remain configurable; setting them to `0` falls back to the
time-only relaxation.  The unique-task helper is now enabled in the 5/10/20
mainline configs as an exact-safe tightening attempt.  The unique-route helper
remains off by default because it is heavier and still experimental.

Current mainline certificate activation:

```text
journey_certificate_completion_bound_enabled: true
journey_certificate_completion_bound_final_probe_only: true
journey_certificate_completion_bound_root_only: false
journey_certificate_completion_bound_exact_proof_enabled: true in mainline 5/10/20 configs
journey_certificate_completion_bound_exact_proof_min_depth: 1
journey_certificate_completion_bound_exact_proof_min_incomplete_rounds: 1
journey_certificate_completion_bound_min_flat_rounds: 0
journey_certificate_completion_bound_time_buckets: suggested 5-15
journey_certificate_completion_bound_energy_buckets: suggested 5-15
journey_certificate_completion_bound_audit_enabled: false by default
journey_certificate_completion_bound_unique_task_helper_enabled: true in mainline 5/10/20 configs
journey_certificate_completion_bound_unique_route_helper_enabled: false
```

The 10-task branch trial may set `journey_certificate_completion_bound_root_only:
false` and `journey_certificate_completion_bound_exact_proof_enabled: true`
with `journey_certificate_completion_bound_exact_proof_min_depth: 1` and
`journey_certificate_completion_bound_exact_proof_min_incomplete_rounds: 1` to
cover late branch-node final proof probes such as Apollo 10-04 while leaving
non-candidate root exact pricing, first branch exact pricing attempts, and
ordinary negative-column retries on the existing path.  This is still an
exact-pricing certificate feature, not an early CG heuristic.

Audit mode runs a bound-off direct pricing check after a bound-on no-negative
certificate.  It is intended for 5-task full validation and sampled 10-task
diagnostics, not for default benchmark timing.

## Reduced-Cost Components

The completion bound includes only task-cover duals:

```text
travel/service lower cost - task-cover pi
```

Do not include subset-row cuts, fleet cuts, branch-row duals, or other dynamic
rows in the first bound.  Omitting these terms makes the bound looser, but still
safe if it remains optimistic.  Including them would add state dimensions and
sign cases that slow down the bound and increase exactness risk.

The forward exact label still uses the full true RMP reduced cost when evaluating
actual candidate journeys.

## Cycle Control

Because the reverse bound is memoryless, it can otherwise create artificial
negative cycles by repeatedly collecting task dual rewards.  First-version cycle
control:

```text
coarse time/energy buckets: consume resource to truncate longer cycles
```

The main V1 table does not store predecessor or NG memory; it relies on coarse
time/energy consumption to truncate repeated visits.  The bound must remain
optimistic.  It is better to be too small and prune less than to be too large
and prune a valid negative column.

## NG-Route And DSSR

The forward exact pricing route should use:

```text
NG-route relaxation + DSSR
```

Do not use full elementary bitmask DP for 20-task pricing.  A full `2^20`
subset state becomes too large once time and energy dimensions are added.

DSSR policy:

- If the best bound-guided negative column violates elementary constraints,
  extract the cycle/conflict tasks.
- Add those tasks to a node-level critical forbidden memory set.
- Do not globally expand all NG neighborhoods.

This keeps state growth local to the actual conflicts seen by pricing.

## Retry NG-DSSR Opt-In Probe (2026-06-04)

A small exact-safe retry hook was added for diagnostics:

```text
journey_retry_incomplete_no_column_force_ng_enabled
journey_retry_incomplete_no_column_force_ng_root_only
journey_retry_incomplete_no_column_force_ng_max_labels
journey_retry_incomplete_no_column_force_ng_min_negative_journeys
journey_retry_incomplete_no_column_force_ng_probe_time_limit
journey_retry_incomplete_no_column_force_ng_probe_min_journeys_for_early_return
```

Default status:

```text
disabled
root-only when enabled
```

Purpose:

- When a short true-dual exact pricing pass is incomplete and returns no column,
  the existing retry pass can optionally force NG-DSSR even if the normal
  `journey_pricing_direct_journey_label_ng_min_cg_iter` gate would disable it.
- This retry still uses true RMP duals.
- It does not create a proof by itself unless an explicit exact-safe NG
  certificate flag is also enabled.  Otherwise, it is only a front-end for
  finding elementary negative journeys before the existing fallback logic.

Validation:

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_retry_force_ng_config_is_opt_in_and_root_only_by_default \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_config_maps_ng_probe_controls \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_learning_defaults_are_conservative_but_overridable \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_can_close_profile_pricing \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_can_close_ryan_foster_branch_pricing \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_rejects_non_ryan_foster_branch_pricing
```

Result: 6 tests passed.

Probe:

```text
BPC_future/results/retry_force_ng_tranq10_06_20260604.csv
  instance = tranquillitatis_balmer_like_20km_tasks10_06_seed11090
  status = OPTIMAL
  objective = 196.791797
  time = 48.306388s
  retry_force_ng = true on cg_iter 3 and 4
  NG retry found negative journeys, but wall-clock was roughly neutral
```

Interpretation:

- The hook is useful for controlled experiments and logging.
- On Tranq 10-06 it did not beat the default result (`47.588866s` in the
  current all-10 rerun), so it should remain opt-in.
- It does not address the Apollo 10-04 branch-tail failure by default because
  the first version is root-only.

## Path-Option Rule

For a pure reduced-cost bound without resource dimensions, each ordered node pair
can use the path option with the lowest current reduced cost.

If the bound uses time or energy buckets, do not blindly keep only the lowest-RC
option when that option consumes extreme resources.  Dropping a slower or
lower-energy option can make the relaxed continuation artificially worse and
therefore unsafe.  In resource-aware mode, retain a coarse resource envelope:

```text
for each pair and coarse resource transition, keep the minimum reduced cost
```

The Moon Trek graph is physically asymmetric.  Uphill and downhill costs differ,
so reverse-bound construction must use the correct directed option data.  A
reverse relaxation from `j` to predecessor `i` must account for the original
directed arc `i -> j`, not assume symmetry.

## Branch Constraints

First version:

```text
root only
branch depth > 0: disabled
```

If simple separate-vehicle constraints are later supported, represent them by
setting incompatible edge or mask transitions to infinity in the relaxed graph.
If a branch condition cannot be represented one-sided and safely, disable the
bound for that node.

## Pruning Rule

Prune immediately when a new forward direct-journey label is generated:

```text
current_rc + LB(last_node, remaining_slots, time_bucket) >= -1e-5
```

Do not wait until the label is pushed to the heap.  Fail-fast pruning avoids
heap growth and priority-queue churn.

During exact certificate pricing, do not use heuristic thresholds such as
`min_add_reduced_cost` to prune weak negative columns.  The certificate threshold
must be the true pricing epsilon.

## Debug Safety

Early development must use a dual-run audit mode:

```text
bare exact DP without completion-bound pruning
bound-pruned exact DP
```

Required assertions:

```text
small instances:
  best_true_rc(bound_on) == best_true_rc(bound_off)

all debug modes:
  if bound_on declares no negative, bound_off must also declare no negative
```

If these disagree, the bound is unsafe and experiments must stop until the bug
is fixed.

Debug tiers:

```text
Debug mandatory:
  all 5-task instances, strict equality on best RC and certificate status

Diagnostic sampled:
  selected 10-task instances, limit-aware mismatch audit

Hard-case limited:
  selected 20-task hard cases, limited diagnostic only, not default benchmark
```

## Logging And Paper Metrics

Metrics should be grouped into three layers.

Bound construction:

```text
bound_build_time
lb_state_count
lb_min_value
lb_mean_value
lb_negative_state_count
ng_memory_size_avg
```

Pricing search:

```text
expanded_labels_before_bound
expanded_labels_after_bound
lb_pruned_labels
energy_return_pruned_labels
time_return_pruned_labels
dominance_pruned_labels
generated_next_sorties_before_bound
generated_next_sorties_after_bound
evaluated_timed_trips
```

Certificate:

```text
best_true_rc
true_negative_journeys
certificate_status
exact_pricing_time
tail_certificate_time
bound_enabled
branch_depth
dual_source = true_dual
```

Paper-facing ratios:

```text
label_reduction_ratio = lb_pruned_labels / expanded_labels_before_bound
certificate_speedup   = T_no_bound / T_with_bound
```

The wall-clock speedup should be reported together with label-pruning evidence
so the improvement is attributable to the exact pricing proof mechanism, not
only solver-path noise.

## Relationship To Learning Stabilization

Learning stabilization and completion bounds have separate roles:

```text
GNN/Wentges smoothing:
  get useful columns and incumbents earlier, reduce RMP trajectory noise

Completion bounds:
  accelerate true-dual exact pricing after heuristic/smoothed pricing fails
```

The handoff is:

```text
smoothed/heuristic pricing fails
alpha forced to 0
true-dual exact pricing starts
tail-only completion bound becomes eligible
```

No GNN output participates in this certificate bound.

## External References To Inspect

These references were identified as useful implementation comparisons.  They
should be inspected before copying design details, because their modeling
assumptions differ from Moon Trek.

- `mouadmorabit/MLColumnSelection`: TensorFlow code for the machine-learning
  part of Morabit, Desaulniers, and Lodi's 2021 Transportation Science paper on
  ML-based column selection for column generation.
- `INFORMSJoC/2023.0404`: JOC archive for the Electric Vehicle Routing and
  Overnight Charging Scheduling Problem on a Multigraph, with BPC code and data.
- `inria-UFF/VRPSolverEasy`: Python interface to VRPSolver / BaPCod-style
  Branch-Cut-and-Price exact VRP solving.
- `Zhengzhong-You/RouteOpt`: modern C++ exact VRP optimization framework related
  to learning-to-branch Branch-Price-and-Cut work.

Use these as architecture references, not as authority to relax the exactness
contract in this project.

## First Implementation Checklist

- Add config flags for root/tail-only completion-bound activation.
- Implement a true-dual direct-label completion bound with state
  `LB(last_node, remaining_slots, time_bucket)`.
- Rebuild the bound every true-dual pricing call.
- Include only task-cover duals in the bound.
- Preserve directed Moon Trek arc asymmetry.
- Add immediate label-generation pruning.
- Keep branch-depth > 0 disabled by default.
- Add debug dual-run assertions on all 5-task instances.
- Log bound construction, pricing search, and certificate metrics.
- Compare against the same config with the bound disabled.

## Current Implementation Snapshot

Implemented in `BPC_future/pricing/journey_pricing.py` and
`BPC_future/solver/journey_driver.py`:

- opt-in direct journey-label completion-bound flags;
- root-only certificate activation through
  `journey_certificate_completion_bound_enabled`;
- optional all-true-dual direct-pricing activation through
  `journey_pricing_direct_journey_label_completion_bound_enabled`;
- directed-arc coarse suffix table with configurable time buckets;
- cut-safe activation for subset-row and fleet cuts;
- immediate pruning for completed direct journey labels;
- online no-waiting partial-sortie pruning when completion bounds are active;
- O(N) unique-task reward lower bound so each remaining task dual is collected
  at most once in partial-sortie pruning;
- logging for bound construction and pruning counters.

Diagnostic evidence collected on 2026-06-03, using no-waiting direct-label mode:

```text
5-task apollo15_20km_tasks05_01:
  status OPTIMAL, primal = dual = 102.041475
  solving_time about 1.3s
  bound_build_time about 0.0009s
  lb_pruned_labels / expanded_labels_before_bound = 9404 / 14520

10-task apollo15_20km_tasks10_01:
  status OPTIMAL, primal = dual = 264.024007
  solving_time about 6.6s
  bound_build_time about 0.0039s
  lb_pruned_labels / expanded_labels_before_bound = 61993 / 85679
```

The 5-task and 10-task diagnostics are below the wall-clock targets, but the
10-task label reduction is not yet a full order of magnitude in the latest
safe unique-task version.

20-task status:

```text
apollo15_20km_tasks20_02:
  bounded diagnostic with max_sequences = 50000
  bound_build_time about 0.058s
  lb_pruned_labels / expanded_labels_before_bound = 0 / 50000
```

This means the current first-version bound is still too loose for 20-task proof.
The bottleneck is direct next-sortie generation before any complete journey
label can be certified.  Do not run unbounded 20-task direct-label scans from
Python while this remains true; they can create severe memory pressure.

Next required improvement for 20-task:

```text
add a stronger physical completion bound with coarse time and energy buckets,
or move the proof-critical pricing core to NG-route/DSSR style labeling.
```

The current O(N) unique-task bound is memory-safe, but it ignores too much route
physics.  It cannot by itself prove the 20-task hard cases under the requested
200s target.

## Root 10-Task Tail Diagnostics (2026-06-03)

`tranquillitatis_balmer_like_20km_tasks10_01` remains the most useful root
certificate hard case.  Current default exact run:

```text
status = TIME_LIMIT
primal = 202.698698
dual = None
time ~= 60.05s
columns = 412
```

Important negative results:

- `journey_certificate_completion_bound_min_flat_rounds=0` is unsafe as a
  performance policy.  It is still mathematically exact, but it activates direct
  completion-bound pricing before the solver has enough columns.  On the hard
  root case it found no negative journey, consumed the full pricing budget, and
  left a worse incumbent (`206.709701`).
- `journey_certificate_proof_round_metric=no_column` with
  `journey_certificate_completion_bound_min_flat_rounds=1` also failed on the
  same case.  The retry used completion-bound direct pricing, pruned many labels,
  but replaced the streaming retry that normally finds a large batch of negative
  columns.
- For this instance, completion bounds must remain true tail-only.  They should
  not replace early or mid CG negative-column discovery.

NG-route/DSSR observations:

```text
NG from cg_iter=1, max_labels=50000:
  status = TIME_LIMIT
  primal = 202.698698
  columns = 333
  pricing calls = 19

NG from cg_iter=1, max_labels=100000:
  status = TIME_LIMIT
  primal = 202.698698
  columns = 333
  pricing calls = 17

NG from cg_iter=5, max_labels=50000:
  status = TIME_LIMIT
  primal = 202.698698
  columns = 404
```

Starting NG at iteration 1 reaches the incumbent earlier but returns too few
columns per pricing call and increases RMP iterations.  Raising the label cap to
100k did not solve the proof bottleneck.  Starting NG at iteration 5 perturbs the
default path less, but still does not close the certificate.

An opt-in diagnostic control now exists for profile-mode NG preprobes:

```text
journey_pricing_direct_journey_label_ng_probe_time_limit
journey_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return
```

With a small NG probe budget (`1.5s`) and a high early-return threshold (`16`),
the solver can continue streaming/profile pricing and merge true-negative NG
journeys into the returned candidate list.  This is exact-safe and useful for
experiments, but on the hard root case it did not improve the 60s certificate.

Next exact-pricing direction:

- keep streaming/profile as the early batch negative-column engine;
- use NG-route/DSSR later, but improve its certificate-tail behavior rather than
  simply starting it earlier or increasing the label cap;
- investigate a real NG certificate path with better dominance/state-space
  refinement, or a stronger resource-aware completion bound that helps only
  after negative-column discovery has slowed.

## Exact-Safe Dual Stabilization Evidence (2026-06-04)

Before replacing exact pricing, the current best safe speedup is to allow the
existing true-RMP dual stabilization to operate in the certificate-candidate
tail, but only after the first few CG rounds:

```text
journey_dual_stabilization_min_cg_iter = 3
journey_dual_stabilization_disable_on_certificate_candidate = False
journey_dual_stabilization_tail_only_enabled = True
journey_dual_stabilization_certificate_candidate_enabled = True
journey_dual_stabilization_mode = l1_reference
```

This is not GNN smoothing.  It uses a dual selected from the current RMP/column
pool and is accepted only when the stabilized dual passes the solver's existing
objective and current-pool dual-feasibility checks.  Official node completion
still requires true-dual exact pricing exhaustion.

Full 5-task regression after applying the 10-task config change:

```text
BPC_future/results/all_tasks05_after_10stabcfg_20260604.csv
20/20 OPTIMAL
mean time = 0.342575s
max time  = 1.130299s
```

Full 10-task rerun with the new default 10-task config:

```text
BPC_future/results/all_tasks10_default_stabcfg_20260604.csv
17/20 OPTIMAL
17/20 closed
mean time  = 26.450225s
total time = 529.004500s
max time   = 60.065157s
```

Compared with the previous default run:

```text
BPC_future/results/all_tasks10_current_docsread_20260603.csv
15/20 OPTIMAL
15/20 closed
mean time  = 28.518331s
total time = 570.366629s
```

Key improved instances:

```text
apollo15_20km_tasks10_02:
  10.189s -> 3.948s, same certified objective

tranquillitatis_balmer_like_20km_tasks10_01:
  TIME_LIMIT -> OPTIMAL, 56.455s, same objective 202.698698

tranquillitatis_balmer_like_20km_tasks10_05:
  31.948s -> 22.408s, same certified objective

tranquillitatis_balmer_like_20km_tasks10_07:
  TIME_LIMIT -> OPTIMAL, 43.173s, same objective 202.288221

tranquillitatis_balmer_like_20km_tasks10_10:
  30.784s -> 24.183s, same certified objective
```

Remaining failures:

```text
apollo15_20km_tasks10_04:
  TIME_LIMIT, primal = 288.332462, dual = 268.585633, gap = 0.068486

tranquillitatis_balmer_like_20km_tasks10_04:
  TIME_LIMIT, primal = 207.893439, no certificate dual

tranquillitatis_balmer_like_20km_tasks10_09:
  TIME_LIMIT, primal = 203.102839, no certificate dual
```

Implication: traditional stabilized-dual selection should stay enabled in the
10-task default because it is exact-safe and improves the root certificate tail
on multiple instances.  It does not solve the remaining root hard cases, so the
next work should still target NG-route/DSSR certificate behavior or a stronger
tail-only completion bound.

## Tail Diagnostics After Stabilization (2026-06-04)

The remaining root hard cases are not all the same:

```text
tranquillitatis_balmer_like_20km_tasks10_04:
  60s default: TIME_LIMIT, primal = 207.893439, no certificate dual
  90s default: OPTIMAL, time = 72.504419s, columns = 445

tranquillitatis_balmer_like_20km_tasks10_09:
  60s default: TIME_LIMIT, primal = 203.102839, no certificate dual
```

`tranq10_04` is still discovering useful negative columns near the 60s cutoff.
At 90s it closes after two more pricing/RMP rounds.  This is not a pure
no-negative proof bottleneck; the solver still needs better late negative-column
discovery or better initial columns.

`tranq10_09` reaches a final certificate candidate, then the current NG/DSSR
tail returns only weak/small batches and can consume the last pricing budget.

Negative configuration diagnostics:

```text
certificate fast negative return, min_count = 16:
  tranq10_01 regressed from OPTIMAL to TIME_LIMIT.
  tranq10_04 remained TIME_LIMIT with fewer columns.

NG/DSSR min_cg_iter = 5:
  tranq10_01 regressed from OPTIMAL to TIME_LIMIT.

completion bound enabled at certificate_flat_rounds >= 4:
  tranq10_01 regressed from OPTIMAL to TIME_LIMIT.

streaming_profile_batch_size = 1000:
  tranq10_04 remained TIME_LIMIT and returned fewer columns.

streaming_profile_batch_size = 10000:
  tranq10_04 remained TIME_LIMIT and returned fewer columns.

journey_pricing_time_limit = 60:
  tranq10_04 reached more CG rounds and more columns, but still remained
  TIME_LIMIT at 60.050615s.  The final short tail switched to NG/DSSR and did
  not certify.

journey_pricing_time_limit = 60 plus NG/DSSR disabled:
  tranq10_04 still remained TIME_LIMIT at 61.427989s.  The last round returned
  profile_dp_incomplete, so simply removing the 4-second short-pass/retry
  cadence is not enough.
```

No-default-change diagnostic:

```text
disable NG/DSSR tail:
  single tranq10_09 run closed in 59.249901s,
  but the full 10-task rerun did not improve overall results.

Full 10-task with NG tail disabled:
  BPC_future/results/all_tasks10_default_stabcfg_no_ngtail_20260604.csv
  17/20 OPTIMAL
  mean time  = 27.387274s
  total time = 547.745470s

Default stabilized config with NG tail enabled:
  BPC_future/results/all_tasks10_default_stabcfg_20260604.csv
  17/20 OPTIMAL
  mean time  = 26.450225s
  total time = 529.004500s
```

Therefore the 10-task default should keep the current NG/DSSR tail enabled for
now, even though it is not yet the right long-term certificate replacement.  The
next NG/DSSR work should avoid one-column weak tail returns and should provide a
real proof-tail advantage before being made more aggressive.  The next
completion-bound work should be stricter than simple flat-round activation,
because even flat round 4 was too early for instances that still need negative
columns.

## NG/DSSR Short-Budget Gate (2026-06-04)

Additional root-tail evidence showed that `tranq10_09` fails when the final
certificate rounds spend the last few seconds in NG/DSSR:

```text
default stabilized config:
  cg7 remaining = 5.223099s
  ng_dssr_elementary_negative_journey, 50000 labels, 1 column
  cg8 remaining = 2.143798s
  ng_dssr_time_limit, no certificate
  final status = TIME_LIMIT

single diagnostic with NG tail disabled:
  final status = OPTIMAL
  time = 59.249901s
```

The accepted V1 fix is a budget gate:

```text
journey_pricing_direct_journey_label_ng_disable_below_remaining = 8.0
```

When the exact-pricing budget remaining is below this threshold, NG/DSSR is
disabled and the solver falls back to the original exact profile/DP pricing
path.  This is exact-safe because it only removes a heuristic/relaxed front-end;
the official no-negative certificate is still produced by true-dual exact
pricing.

Validation:

```text
BPC_future/results/probe_ng_remaining_gate8_t09_20260604.csv
  tranq10_09: OPTIMAL, time = 59.169420s

BPC_future/results/probe_ng_remaining_gate8_t04_t01_20260604.csv
  tranq10_04: TIME_LIMIT, time = 61.409052s, columns = 445
  tranq10_01: OPTIMAL, time = 57.480601s

BPC_future/results/all_tasks10_ng_remaining_gate8_20260604.csv
  18/20 OPTIMAL
  mean time  = 26.513728s
  total time = 530.274563s
  max time   = 61.393672s

BPC_future/results/all_tasks05_after_ng_gate8_20260604.csv
  20/20 OPTIMAL
  mean time = 0.345386s
  max time  = 1.156171s
```

Compared with `all_tasks10_default_stabcfg_20260604.csv`, the gate improves
the full 10-task closure count from `17/20` to `18/20`.  The new certified
instance is:

```text
tranquillitatis_balmer_like_20km_tasks10_09:
  TIME_LIMIT 60.045788s -> OPTIMAL 57.839864s
```

Remaining 10-task failures after this gate:

```text
apollo15_20km_tasks10_04:
  TIME_LIMIT, primal = 288.332462, dual = 268.585633, gap = 0.068486

tranquillitatis_balmer_like_20km_tasks10_04:
  TIME_LIMIT, primal = 207.893439, no certificate dual
```

Implication: the 8-second NG/DSSR short-budget gate should stay in the 10-task
trial config.  It solves the known one-column NG tail failure without sacrificing
exactness.  It does not solve `tranq10_04`, whose logs still show late strong
negative-column discovery and insufficient CG rounds before the 60-second
cutoff.

Rerun audit after a temporary config drift to `0.0`:

```text
BPC_future/results/all_tasks10_current_20260604_rerun.csv
  current config with NG short-budget gate = 0.0
  17/20 OPTIMAL
  mean time  = 26.300761s
  total time = 526.015227s
  max time   = 61.378340s
  failed: apollo10_04, tranq10_04, tranq10_09

BPC_future/results/all_tasks10_doc_gate8_20260604_rerun.csv
  same current code, command-line override gate = 8.0
  18/20 OPTIMAL
  mean time  = 26.011679s
  total time = 520.233583s
  max time   = 61.175973s
  failed: apollo10_04, tranq10_04

BPC_future/results/all_tasks05_current_20260604_rerun.csv
  20/20 OPTIMAL
  mean time = 0.398405s
  max time  = 1.147436s
```

The only status difference in the 10-task rerun was:

```text
tranquillitatis_balmer_like_20km_tasks10_09:
  gate = 0.0: TIME_LIMIT, primal = 203.102839, no certificate dual
  gate = 8.0: OPTIMAL, primal = dual = 203.102839, time = 57.443249s
```

Therefore the 10-task trial config must keep:

```text
journey_pricing_direct_journey_label_ng_disable_below_remaining = 8.0
```

## NG Probe Certificate Switch (2026-06-04)

An opt-in certificate return path now exists for profile-mode NG preprobes:

```text
journey_pricing_direct_journey_label_ng_probe_certificate_enabled
```

Default is `False`.  When enabled, profile pricing lets the NG preprobe run with
`direct_journey_label_ng_certificate_enabled=True`.  The preprobe may close the
pricing call only if all of the following hold:

```text
ng_probe.exhausted = True
ng_probe.status = OPTIMAL
ng_probe.ng_certificate_from_relaxation = True
```

This is exact-safe because NG-route relaxation is a superset of elementary
journeys: if the relaxed pricing is exhausted and has no negative reduced-cost
journey, then no elementary journey can be negative either.  In all incomplete
or time-limited cases the solver still falls back to the ordinary profile/DP
pricing path.

Initial hard-case probes with:

```text
journey_pricing_direct_journey_label_ng_probe_certificate_enabled = True
journey_pricing_direct_journey_label_ng_min_cg_iter = 6
journey_pricing_direct_journey_label_ng_disable_below_remaining = 0.0
journey_pricing_direct_journey_label_ng_max_labels = 200000
```

did not close the two remaining 10-task failures:

```text
BPC_future/results/probe_t04_ng_probe_cert_200k_20260604.csv
  tranq10_04: TIME_LIMIT, time = 60.050383s, columns = 445

BPC_future/results/probe_a04_ng_probe_cert_200k_20260604.csv
  apollo10_04: TIME_LIMIT, time = 60.092921s, gap = 0.068486
```

For `tranq10_04`, the final NG probe had positive best relaxed RC
(`0.266823346`) but stopped with `ng_dssr_time_limit`, so it could not issue an
official relaxed certificate.  The conclusion is that the certificate return
path is useful infrastructure, but the current NG/DSSR implementation still
needs stronger dominance/state-space control or more targeted activation before
it can replace the profile proof tail.

Follow-up diagnostics that were not adopted:

```text
direct long certificate pricing after flat round 1:
  tranq10_04 remained TIME_LIMIT, columns increased to 467.
  It removed short 4s empty passes but still found late strong negative columns.
  tranq10_09 regressed from OPTIMAL to TIME_LIMIT, so this must not be default.

late fast-negative return after proof round 6, min_count = 8:
  tranq10_04 remained TIME_LIMIT, columns = 461.
  The late 8 negative journeys were still found near the end of the search, so
  the smaller batch did not buy enough extra RMP/certificate time.

streaming negative batch = 128 with direct long pricing:
  tranq10_04 remained TIME_LIMIT, columns = 468.
  Larger batches changed the column mix but did not reduce the proof tail.

skip initial journey pool MIP:
  tranq10_04 remained TIME_LIMIT, columns = 461.

SCIP original duals on certificate candidates:
  tranq10_04 remained TIME_LIMIT, columns = 468.

profile catalog/resume instead of label physical catalog:
  tranq10_04 remained TIME_LIMIT, columns = 252.
  This generated too few useful columns and should not replace the current label
  physical catalog path.

streaming final-DP time reserve:
  New opt-in control:
    journey_pricing_streaming_final_dp_time_reserve
  Default remains 0.0.  The control shortens only streaming profile-generation
  time, leaving the final journey DP with the original pricing deadline.  This
  is exact-safe because interrupted generation leaves the pricing result
  incomplete; it cannot produce a no-negative certificate.

  tranq10_04, reserve = 0.75:
    TIME_LIMIT, time = 60.775519s, columns = 418.
    It did make cg2/cg3 run nonzero final-DP labels before returning negative
    columns, but later rounds still fell back to retry/incomplete behavior.

  tranq10_04, reserve = 1.5:
    TIME_LIMIT, time = 60.039870s, columns = 380.

  Conclusion:
    This is useful diagnostic infrastructure for separating profile generation
    time from final DP time, but it is not a default 10-task speedup.

profile record time-filter cache:
  The compatible-profile cache now also memoizes repeated
  `(used_mask, min_upper_start)` filtered record lists for 10-task-and-smaller
  DP calls.  This does not change the candidate set or exactness; it only avoids
  rebuilding identical filtered tuples during profile-journey DP.

  tranq10_04:
    BPC_future/results/probe_t04_profile_record_cache_20260604.csv
    TIME_LIMIT, time = 60.456623s, columns = 445.

  sanity:
    tranq05_03 OPTIMAL, time = 0.612373s.
    apollo10_07 OPTIMAL, time = 21.421739s.

  Conclusion:
    Safe to keep as a small default cache, but it does not solve the remaining
    certificate bottleneck.

profile-DP cut-aware suffix bound:
  The profile-journey DP suffix bound was extended to stay enabled when the
  active cut duals are subset-row cuts and fleet cuts.  The safe pruning formula
  now evaluates:

    base_rc + current_profile_value + optimistic_suffix_profile_value
      - realized_cut_dual_value(current_mask)
      - future_positive_src_reward_upper_bound
      - future_positive_fleet_reward_upper_bound

  Positive subset-row duals are handled by subtracting an upper bound on the
  extra reward reachable with the remaining sortie/task capacity.  Negative SRC
  duals only add future penalties, so ignoring those future penalties remains
  optimistic.  Fleet cuts are safe because their journey coefficient is fully
  realized once the partial mask is non-empty; for the empty start mask the
  bound subtracts the maximum positive fleet reward that could appear in any
  future non-empty completion.  Other dynamic cut families still disable this
  profile-DP suffix pruning path.

  Unit tests added:
    journey_profile_dp_bound_pruning_keeps_positive_src_reward_negative
    journey_profile_dp_bound_pruning_uses_positive_src_reward_bound
    journey_profile_dp_bound_pruning_keeps_positive_fleet_reward_negative

  Probes:
    tranq05_03 sanity:
      OPTIMAL, time = 0.594562s / 0.613241s in the follow-up sanity run.

    tranq10_04 default with cut-aware bound:
      TIME_LIMIT, time = 60.303189s, columns = 445.
      dp_bound_pruned_labels stayed 0.  In the early rounds, optimistic
      continuation values were still negative enough that no label could be
      pruned; in later rounds, profile generation exhausted the capped pricing
      deadline before profile-DP processed labels.

    tranq10_04 with streaming_final_dp_time_reserve = 0.75:
      TIME_LIMIT, time = 60.772686s, columns = 418.
      profile-DP processed labels in cg2-cg4, but dp_bound_pruned_labels still
      stayed 0.  Cross-count dominance, not completion-bound pruning, remained
      the dominant reducer.

  Conclusion:
    This is exact-safe and covered by tests, but it is not the main bottleneck
    on the current tranq10_04 proof tail.

certificate-stage parameter probes, not adopted:
  immediate certificate no-reserve:
    Added as an opt-in helper
      journey_certificate_immediate_no_reserve_enabled
    but kept disabled in the 10-task trial config.  On tranq10_04 it changed the
    column generation path and worsened the result:
      TIME_LIMIT, time = 61.302478s, columns = 467.

  streaming negative batch = 128:
    TIME_LIMIT, time = 61.515639s, columns = 455.
    More negative journeys per batch increased per-round work and did not remove
    the proof tail.

  SCIP original duals on certificate candidates:
    TIME_LIMIT, time = 60.941419s, columns = 422.
    This reduced columns versus the stabilized path but still did not close
    within 60s, so it is not enough by itself.

  retry generation fraction = 0.0:
    TIME_LIMIT, time = 61.408900s, columns = 445.
    It followed essentially the same capped-exact plus retry pattern, so this
    did not remove the repeated profile-generation cost.

NG/DSSR certificate safety note:
  Current default 10-task runs use NG/DSSR only as a probe/helper; relaxed
  no-negative certificates are not accepted unless
  `direct_journey_label_ng_certificate_enabled=True`.

  A safety guard was added for that future certificate mode: when NG relaxed
  dominance is used with nonzero cut duals, the dominance key includes the
  unique visited-task mask.  Without this, two labels with the same NG memory,
  current partial state, and completed-sortie count but different SRC/fleet cut
  masks could incorrectly dominate each other.  That would be unacceptable for
  an official relaxed no-negative certificate.

  Unit test added:
    direct_ng_certificate_dominance_key_can_include_visit_mask

  Sanity:
    apollo10_01 with the current default probe behavior:
      OPTIMAL, time = 1.824199s, primal/dual = 264.024007.

profile-DP time-filter index:
  The compatible-profile cache now uses a lazy per-mask segment index for
  `upper_start >= current_label_end_time` queries.  It preserves the existing
  profile-DP scan order but avoids linearly scanning time-infeasible profiles
  for every DP label.  This is exact-safe because it returns the same records
  as the old filter in the same order.

  Unit tests added/updated:
    compatible_profile_cache_time_index_preserves_scan_order
    compatible_profile_cache_reuses_time_filtered_records

  Probes:
    tranq05_03 sanity:
      OPTIMAL, time = 0.602224s.

    apollo10_01 sanity:
      OPTIMAL, time = 1.772932s, primal/dual = 264.024007.

    tranq10_04:
      TIME_LIMIT, time = 60.059618s, columns = 445.
      This is slightly faster than the prior 60.303s/60.178s probes, and cg6
      reached the final negative batch at about 60.01s, but it still cannot
      complete the next RMP solve and no-negative certificate within 60s.

  Conclusion:
    Safe to keep as a small default micro-optimization, but the remaining
    10-task hard-case gap still requires a larger certificate-tail change.

NG dominance key experiment:
  Added an opt-in control:

    journey_pricing_direct_journey_label_ng_sequence_key_enabled

  Default remains True.  When disabled, NG dominance keys use the current sortie
  task mask instead of the full current sequence.  This can strengthen
  dominance for future NG certificate work, while the certificate cut-mask guard
  described above remains active when relaxed certificates are enabled.

  Probe:
    tranq10_04 with sequence key disabled:
      TIME_LIMIT, time = 60.142769s, columns = 445.
      NG did not become active before the 60s cutoff on this run, so this did
      not improve the current hard case.  Keep it opt-in for now.

Branch-node NG preprobe support:
  NG/DSSR profile preprobes can now run at branch nodes.  Returned candidate
  journeys are filtered with the same task-set branch semantics used by the
  profile-pricing path:

    same_vehicle(i, j): returned journey must contain either both tasks or
      neither task.

    separate_vehicle(i, j): returned journey must not contain both tasks.

  This is exact-safe because NG still contributes only feasible true-negative
  candidate columns.  Relaxed NG no-negative certificates remain disabled when
  branch constraints are present, and the elementary direct-label fallback is
  not used under branch constraints because that fallback currently does not
  carry branch rows.

  Unit coverage:
    ng_preprobe_profile_pricing_filters_branch_infeasible_journeys

  Probes on `apollo15_20km_tasks10_04`:

    branch NG from cg1, probe time limit = 0.5s:
      TIME_LIMIT, time = 60.191749s, nodes = 10, columns = 236.
      The branch tree became smaller than the default 14-node path, but repeated
      NG probes consumed enough time that the instance still did not close.

    branch NG from cg1, probe time limit = 0.2s:
      TIME_LIMIT, time = 60.129714s, nodes = 12, columns = 240.
      This kept some tree reduction, but still did not produce a 60s
      certificate.  Logs show 28 NG probe events and about 93k NG label pops,
      so all-node probing is still too expensive as a default policy.

  Default sanity after the branch-NG implementation:

    apollo10_01:
      OPTIMAL, time = 1.774874s, primal/dual = 264.024007.

    tranq10_09:
      OPTIMAL, time = 57.364718s, primal/dual = 203.102839.

  Conclusion:
    Branch-node NG preprobe is now available for controlled experiments and is
    branch-safe, but it should stay off by default until a more selective
    trigger is identified.

Streaming profile/DP time split audit:
  The streaming-profile pricing path now honors
  `profile_generation_time_fraction` when computing the generation deadline,
  matching the non-streaming profile oracle semantics.  The existing
  `streaming_final_dp_time_reserve` remains active and can shorten that
  deadline further.  Unit coverage was added for both controls.

  The current 10-task default config intentionally sets:

    journey_pricing_profile_generation_time_fraction = 1.0
    journey_retry_incomplete_no_column_generation_fraction = 1.0

  Rationale:
    Before this fix, streaming mode effectively behaved like fraction 1.0.
    Enabling the old configured 0.9/0.95 split changed the hard-case column
    path and did not improve the certificate tail.

  Probes on `tranquillitatis_balmer_like_20km_tasks10_04`:

    default after honoring 0.9/0.95:
      TIME_LIMIT, time = 61.305140s, columns = 418.
      cg2 found 31 negative journeys in the first 4s call, but the later path
      still failed to certify within 60s.

    restore streaming behavior with 1.0/1.0:
      TIME_LIMIT, time = 60.233080s, columns = 445.
      This is closer to the previous streaming path but still not a certificate.

    streaming negative batch 32:
      TIME_LIMIT, time = 61.093953s, columns = 321.

    streaming negative batch 16:
      TIME_LIMIT, time = 60.631526s, columns = 286.
      It reached cg7 but still only found more negative columns before the
      deadline; no no-negative certificate was obtained.

    static/dynamic SRC disabled:
      TIME_LIMIT, time = 60.843978s, columns = 249.
      Startup remained expensive because the initial trip/journey pool build,
      not SRC construction, is the dominant pre-CG cost on this instance.

    initial savings seed budget reduced to 1000 evaluations / 80 trips:
      TIME_LIMIT, time = 61.377330s, columns = 402.

  Sanity with restored 1.0/1.0 config:

    apollo10_01:
      OPTIMAL, time = 1.791404s, primal/dual = 264.024007.

    tranq10_09:
      OPTIMAL, time = 56.983726s, primal/dual = 203.102839.

  Conclusion:
    The streaming time-split control is now correctly wired and can be used for
    future experiments, but the current hard 10-task root tail still requires a
    stronger pricing/certificate mechanism.  Do not lower the default
    generation fraction or negative-batch threshold based on the current probes.
```

Root-only late NG preprobe default audit (2026-06-04):

  Default change:
    Enable direct journey-label NG/DSSR probing only at the root, only from the
    late CG tail, with a small probe budget:

      journey_pricing_direct_journey_label_ng_min_cg_iter = 7
      journey_pricing_direct_journey_label_ng_disable_below_remaining = 0.0
      journey_pricing_direct_journey_label_ng_probe_time_limit = 0.4
      journey_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return = 4
      journey_branch_pricing_direct_journey_label_ng_dssr_enabled = False

    This keeps branch nodes on the original exact path and keeps NG as a
    candidate-column preprobe, not as a relaxed certificate.

  Full 5-task audit:

    BPC_future/results/all_tasks05_after_ng_root_tail_default_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.754659s
      mean solver time  = 0.337733s
      max solver time   = 1.119035s

    Compared with
    BPC_future/results/all_tasks05_docread_current_20260604_060015.csv:
      20 / 20 OPTIMAL before and after
      no objective/status changes

  Full 10-task audit:

    BPC_future/results/all_tasks10_ng_root_tail_default_20260604.csv
      18 / 20 OPTIMAL
      total solver time = 517.997096s
      mean solver time  = 25.899855s
      max solver time   = 61.157995s

    Compared with
    BPC_future/results/all_tasks10_docread_current_20260604_060015.csv:
      17 / 20 OPTIMAL -> 18 / 20 OPTIMAL
      total solver time 522.382398s -> 517.997096s
      tranq10_09 closed:
        TIME_LIMIT 61.116034s -> OPTIMAL 58.219922s
        columns 437 -> 436

    Remaining failures:
      apollo15_20km_tasks10_04:
        TIME_LIMIT, primal = 288.332462, dual = 268.585633,
        gap = 0.068486, nodes = 14, columns = 241.

      tranquillitatis_balmer_like_20km_tasks10_04:
        TIME_LIMIT, primal = 207.893439, no certificate dual,
        root node only, columns = 445.

  Conclusion:
    The root-only late NG preprobe is a safe small default improvement: it
    closes one boundary 10-task instance without changing 5-task behavior.  It
    does not solve the main hard-case bottleneck.  The next acceleration target
    remains true-dual exact-pricing proof work, especially completion bounds and
    a production NG-route+DSSR certificate path.

Completion-bound activation probes (2026-06-04):

  The code already contains an opt-in direct-label completion bound:

    journey_certificate_completion_bound_enabled
    journey_certificate_completion_bound_min_flat_rounds
    journey_certificate_completion_bound_time_buckets
    journey_certificate_completion_bound_energy_buckets

  A new diagnostic switch was added:

    journey_certificate_completion_bound_partial_pruning_enabled

  Default remains True.  When True, completion-bound pruning can run inside
  sortie partial-label generation, and direct-label pricing disables the
  next-sortie profile cache because the partial bound depends on the parent
  journey label value, count, and end time.  When False, pruning is only applied
  after a complete sortie has been instantiated as a journey-label extension,
  allowing the next-sortie profile cache to stay active.  This is exact-safe
  because disabling partial pruning only removes pruning.

  Probes on `tranquillitatis_balmer_like_20km_tasks10_04`:

    completion bound, flat metric, min round = 1, time buckets = 10:
      BPC_future/results/probe_tranq10_04_completion_min1_20260604.csv
      TIME_LIMIT, time = 60.459384s, columns = 240.
      Final retry pruned 28,013 labels out of 466,257 checked labels.
      Max RSS about 3.38 GB.

    completion bound, energy buckets = 10:
      BPC_future/results/probe_tranq10_04_completion_energy10_20260604.csv
      TIME_LIMIT, time = 60.459124s, columns = 240.
      Final retry pruned 34,068 labels out of 473,002 checked labels.
      Max RSS about 3.38 GB.

    completion bound with no-column proof metric:
      BPC_future/results/probe_tranq10_04_completion_nocolumn_20260604.csv
      TIME_LIMIT, time = 60.447595s, columns = 240.
      The first 4-second profile call at cg2 returned no column, so the retry
      immediately switched to direct-label completion-bound proof and skipped
      the streaming retry that normally finds another 64 negative journeys.
      This is now classified as the wrong role for Completion Bound: it was used
      as a worker before ordinary retry pricing was exhausted.

    cache-preserving completion bound:
      BPC_future/results/probe_tranq10_04_completion_cache_20260604.csv
      TIME_LIMIT, time = 61.054846s, columns = 240.
      Max RSS rose to about 8.53 GB because the cached profile set became large,
      and no journey-label pruning occurred before the profile generation time
      limit.  Keep this mode experimental only.

  Conclusion:
    Do not enable completion bounds by default yet.  The current bound is cheap
    to build and exact-safe, but on this hard root-tail instance it activates
    too early and diverts time away from streaming negative-column discovery.
    The next useful step is a stricter activation contract: completion-bound
    proof should start only after the normal exact retry path has also failed to
    return a true-RC negative column, or inside a dedicated final certificate
    call with enough remaining time.

  Default-path regression after adding the partial-pruning switch:

    BPC_future/results/all_tasks05_after_completion_switch_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.299535s
      mean solver time  = 0.314977s
      max solver time   = 1.435529s
      max RSS about 78 MB

    BPC_future/results/probe_apollo10_01_after_completion_switch_20260604.csv
      OPTIMAL, time = 1.960886s, primal/dual = 264.024007.

    Since completion bounds remain disabled by default, the new switch does not
    change the normal 5-task path or the representative fast 10-task path.

    Default-path regression after adding the after-retry switch:

      BPC_future/results/all_tasks05_after_afterretry_switch_20260604.csv
        20 / 20 OPTIMAL
        total solver time = 6.360781s
        mean solver time  = 0.318039s
        max solver time   = 1.475342s
        max RSS about 78 MB

      BPC_future/results/probe_apollo10_01_after_afterretry_switch_20260604.csv
        OPTIMAL, time = 1.830687s, primal/dual = 264.024007.

  After-retry activation contract:

    A stricter opt-in activation switch was added:

      journey_certificate_completion_bound_after_retry_enabled

    When enabled, normal exact pricing and the normal incomplete-no-column retry
    do not activate completion bounds.  Completion-bound direct-label pricing is
    only eligible for a final retry after that normal retry also returns no
    true-RC negative journey and remains incomplete.  This preserves the
    streaming/profile retry path that is still useful for discovering negative
    columns.

    Probe:

      BPC_future/results/probe_tranq10_04_completion_after_retry_20260604.csv
        TIME_LIMIT, time = 61.404445s, columns = 445.
        Max RSS about 310 MB.

    The log confirms that cg2-cg5 normal retries still returned 64 negative
    journeys each, matching the default column-discovery path.  No
    completion-bound final retry ran because the last cg6 exact call had only
    about 1 second left, below the useful final-retry budget.

    Conclusion:
      The after-retry contract fixes the premature-activation problem and keeps
      memory under control, but by itself it does not close `tranq10_04`.  The
      next bottleneck is budget allocation: the normal retry can consume nearly
      all tail time while still finding negative columns, leaving no time for a
      final certificate attempt.

  Final-retry time reserve probe:

    A second opt-in budget switch was added:

      journey_certificate_completion_bound_after_retry_reserve_time

    When a final after-retry completion-bound call is eligible, this caps the
    normal incomplete-no-column retry so the requested reserve remains for the
    final certificate attempt.  The default is `0.0`, so the normal retry budget
    is unchanged unless this probe switch is explicitly set.

    Probe:

      BPC_future/results/probe_tranq10_04_completion_after_retry_reserve8_20260604.csv
        TIME_LIMIT, time = 60.110976s, columns = 390.
        Max RSS about 746 MB.

    The log confirms:

      cg2-cg4 normal retries still returned 64 negative journeys each.
      cg5 normal retry was capped from about 13.0s to about 5.0s.
      cg5 final completion-bound retry then ran for about 6.7s.
      The final bound pruned only 72 labels out of 53,818 checked labels and
      remained incomplete.

    Default-path regression after adding the reserve switch:

      BPC_future/results/all_tasks05_after_retry_reserve_switch_20260604.csv
        20 / 20 OPTIMAL
        total solver time = 6.336102s
        mean solver time  = 0.316805s
        max solver time   = 1.438991s
        max RSS about 78 MB

      BPC_future/results/probe_apollo10_01_after_retry_reserve_switch_20260604.csv
        OPTIMAL, time = 1.834156s, primal/dual = 264.024007.

    Conclusion:
      Reserving time for the current completion bound is not enough.  The
      direct-label completion bound is too loose on this instance.  Future work
      should focus on a stronger certificate oracle, most likely production
      NG-route+DSSR with tighter dominance and completion bounds, rather than
      spending more default budget on the current direct-label bound.

NG memory boundary audit (2026-06-04):

  The direct NG labeler previously carried `ng_memory` across a completed
  sortie into the next depot-started sortie.  That is too restrictive for a
  relaxed certificate oracle: NG neighborhood memory is local route-segment
  memory and should reset at a depot/recharge boundary.  Only DSSR critical
  tasks should remain globally forbidden across sorties.

  Implementation:

    direct_journey_label_ng_reset_memory_between_sorties_enabled

  Default is `False` for ordinary NG preprobes to preserve the current
  performance path.  When `direct_journey_label_ng_certificate_enabled=True`,
  the reset is forced internally because a relaxed no-negative certificate must
  be based on a true relaxation rather than on an over-restricted state space.

  Probe on `tranquillitatis_balmer_like_20km_tasks10_04`:

    Baseline diagnostic with earlier NG and 2s probe:
      BPC_future/results/probe_tranq10_04_ng_mincg5_probe2_20260604.csv
      TIME_LIMIT, time = 60.046173s, columns = 445.
      NG best relaxed RC stayed positive at about 0.56458.

    Opt-in boundary reset with same 2s probe:
      BPC_future/results/probe_tranq10_04_ng_reset_probe2_20260604.csv
      TIME_LIMIT, time = 61.462557s, columns = 390.
      NG still did not find negative columns; the extra NG search displaced
      streaming retry time and reduced the column count.

  Default-path regression after adding the switch:

    BPC_future/results/all_tasks05_after_ng_memory_switch_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.342126s
      mean solver time  = 0.317106s
      max solver time   = 1.497842s
      max RSS about 78 MB

    BPC_future/results/probe_apollo10_01_after_ng_memory_switch_20260604.csv
      OPTIMAL, time = 1.846687s, primal/dual = 264.024007.

    BPC_future/results/probe_tranq10_09_after_ng_memory_switch_20260604.csv
      OPTIMAL, time = 58.340447s, primal/dual = 203.102839.

  Conclusion:
    The boundary reset is necessary infrastructure for a future relaxed NG
    certificate, but it is not a speed improvement for the current ordinary
    preprobe.  Keep it opt-in outside certificate mode.

NG branch partial-mask pruning audit (2026-06-04):

  Branch-side NG probing is still not a default speedup, but the NG labeler now
  has one exact-safe partial pruning rule for branch nodes:

    when all active branch rows are same/separate Ryan-Foster rows,
    immediately reject a partial relaxed NG label whose unique visited-task mask
    already violates a `separate_vehicle(i, j)` row.

  This is one-sided and exact-safe:

    - `separate_vehicle`: once both tasks are already in the same journey label,
      no future sortie can repair the violation.
    - `same_vehicle`: partial labels are not pruned just because only one side
      has appeared; the missing side may still be added later.
    - task-vehicle or unknown branch rows are not handled by this partial rule.

  Unit coverage:

    `test_direct_ng_relaxed_iteration_prunes_separate_branch_partial_mask`
    constructs a two-task case where single-task journeys are nonnegative but
    the two-task journey is negative.  Without the branch row, relaxed NG returns
    the two-task negative journey.  With `separate_vehicle(1,2)`, it returns no
    negative journey and the relaxed best RC is nonnegative.

  Opt-in probe on `apollo15_20km_tasks10_04`, with branch NG enabled from cg1
  and a 0.2s probe budget:

    Before partial pruning:
      BPC_future/results/probe_apollo10_04_branch_ng_20260604_0730.csv
      TIME_LIMIT, time = 60.119274s, nodes = 12, columns = 238.
      NG events generated 104,619 labels and pruned 57,222 by dominance.

    After partial pruning:
      BPC_future/results/probe_apollo10_04_branch_ng_partialprune_20260604.csv
      TIME_LIMIT, time = 60.006230s, nodes = 12, columns = 240.
      NG events generated 102,401 labels and pruned 55,193 by dominance.

  Interpretation:

    The pruning is directionally correct and useful infrastructure for future
    branch NG/DSSR, but the observed reduction is too small to justify enabling
    branch NG by default.  Keep
    `journey_branch_pricing_direct_journey_label_ng_dssr_enabled=False`.

  Negative streaming-batch probe on `tranquillitatis_balmer_like_20km_tasks10_04`:

    BPC_future/results/probe_tranq10_04_stream_min32_20260604.csv
      TIME_LIMIT, time = 61.398115s, columns = 321.

    Lowering `streaming_min_negative_batch` from 64 to 32 returned smaller
    batches too early and reduced useful column volume.  Do not adopt this
    parameter as a default.

Skip-short exact-pricing cadence probe (2026-06-04):

  Diagnostic conclusion from comparing 60s and 90s logs on
  `tranquillitatis_balmer_like_20km_tasks10_04`:

    - The 60s and 90s default paths are essentially identical through cg5.
    - At about 58.7s the 90s run still has enough time to finish cg6 negative
      pricing and cg7 no-negative certification.
    - The 60s run reaches cg6 with only about 1.3s of pricing budget left.

  An opt-in cadence switch was added:

    journey_skip_short_exact_after_retry_negative_enabled
    journey_skip_short_exact_min_retry_negative_rounds
    journey_skip_short_exact_min_cg_iter
    journey_skip_short_exact_root_only
    journey_skip_short_exact_certificate_only
    journey_skip_short_exact_max_time_limit

  Default is disabled.  When enabled, after repeated rounds where a short exact
  pass returns no column but the retry returns true-negative columns, the next
  short exact pass can be skipped and replaced by the same true-dual pricing
  oracle using the longer retry-style budget.  This is exact-safe because an
  incomplete pricing run remains incomplete; the switch never creates a
  no-negative certificate.

  Probe:

    BPC_future/results/probe_tranq10_04_skip_short_exact_h2_20260604.csv
      TIME_LIMIT, time = 61.516166s, columns = 463.

    BPC_future/results/probe_tranq10_04_skip_short_h2_nggate8_20260604.csv
      TIME_LIMIT, time = 61.576554s, columns = 463.

  Interpretation:

    The switch behaved as intended and skipped the short pass at cg4-cg7.  It
    increased the number of generated columns from the default 445 to 463, but
    still did not leave enough time for a certificate.  Adding the 8-second NG
    remaining-time gate changed the final oracle back to profile/DP, but the
    final cg7 call still had only about 2.2s and remained incomplete.  Keep this
    switch as diagnostic infrastructure only; do not enable it by default.

  Default-path regression after adding the disabled switch:

    BPC_future/results/all_tasks05_after_skip_short_switch_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.907732s
      mean solver time  = 0.345387s
      max solver time   = 1.158440s

    BPC_future/results/probe_10_representative_after_skip_short_switch_20260604.csv
      apollo15_20km_tasks10_01:
        OPTIMAL, time = 1.799659s, primal/dual = 264.024007.
      tranquillitatis_balmer_like_20km_tasks10_09:
        OPTIMAL, time = 58.848515s, primal/dual = 203.102839.
        Max RSS for the two-instance run was about 297 MB.

Streaming timing diagnostics (2026-06-04):

  The streaming-profile partial-return path now records nonzero timing and DP
  counters for both callback returns and ordinary incomplete returns:

    - `profile_generation_time` for time spent generating/resuming sortie
      profiles before the callback/final DP.
    - `profile_dp_time` for the profile-to-journey DP call.
    - `dp_processed_labels`, `dp_state_count`, `dp_profile_record_scans`, and
      `dp_extension_attempts` even when the profile DP returns early with a
      negative journey.

  Tests:

    test_streaming_partial_result_records_callback_times
    test_journey_profile_dp_early_return_records_stats

  Diagnostic probe:

    BPC_future/results/probe_tranq10_04_stream_stats25_fulltiming_20260604.csv
      TIME_LIMIT by design at 25s, columns = 339, max RSS about 202 MB.

  Key log evidence on `tranquillitatis_balmer_like_20km_tasks10_04`:

    cg1 exact:
      streaming_partial_negative_journey
      profile_generation_time = 1.356716s
      profile_dp_time         = 0.250966s
      dp_processed_labels     = 3998

    cg2 exact short pass:
      profile_dp_incomplete
      profile_generation_time = 4.139769s
      profile_dp_time         = 0.064591s
      dp_processed_labels     = 0

    cg2 exact_retry:
      streaming_partial_negative_journey
      profile_generation_time = 5.586094s
      profile_dp_time         = 0.446298s
      dp_processed_labels     = 5

    cg4 exact short pass:
      profile_dp_incomplete
      profile_generation_time = 4.139720s
      profile_dp_time         = 0.238820s

  Interpretation:

    The expensive part of the `tranq10_04` tail is not the profile-to-journey
    DP.  The short no-column passes are spending almost all of their 4-second
    budget inside sortie profile generation/resume before the DP sees enough
    profiles.  The next real speed target is therefore the profile-label
    generation/resume engine, especially why later batches require many more
    evaluated timed trips to append another useful block of profiles.

  Default-path regression after adding the timing-only diagnostics:

    BPC_future/results/all_tasks05_after_stream_timing_stats_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.885955s
      mean solver time  = 0.344298s
      max solver time   = 1.147544s

    BPC_future/results/probe_apollo10_01_after_stream_timing_stats_20260604.csv
      OPTIMAL, time = 1.809634s, primal/dual = 264.024007.

  Default-path regression after adding the partial-mask pruning:

    BPC_future/results/all_tasks05_after_ng_branch_partialprune_20260604.csv
      20 / 20 OPTIMAL
      total solver time = 6.848770s
      mean solver time  = 0.342439s
      max solver time   = 1.133384s

    BPC_future/results/probe_10_representative_after_ng_branch_partialprune_20260604.csv
      apollo15_20km_tasks10_01:
        OPTIMAL, time = 1.827224s, primal/dual = 264.024007.
      tranquillitatis_balmer_like_20km_tasks10_09:
        OPTIMAL, time = 59.159807s, primal/dual = 203.102839.
        Max RSS for the two-instance run was about 296 MB.

## Resume Label Active-Set Check (2026-06-04)

The sortie profile resume heap uses lazy deletion: dominated partial labels can
remain in the heap until they are popped.  The old validity check used:

```text
label in state.labels_by_key[(mask, last)]
```

which is a linear list membership test.  In late `tranq10_04` root-tail rounds,
the resume state contains tens of thousands of labels/profiles, so this check
adds Python overhead on every stale heap pop.

Implemented exact-safe data-structure change:

```text
_SortieLabelResumeState.active_label_ids: set[int]
```

When a partial label is inserted, its `id()` is added to the set.  When it is
removed by partial-label dominance, its `id()` is removed.  Heap-pop validity
now uses O(1) membership in this active-id set.  This does not change dominance,
profile generation, reduced-cost calculations, candidate filtering, or the
certificate path.

Unit coverage:

```text
test_sortie_partial_active_label_ids_track_dominance
```

Validation:

```text
python -m unittest BPC_future.tests.test_bpc_future -k sortie_partial_active_label_ids
python -m unittest BPC_future.tests.test_bpc_future -k direct_ng
python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/tests/test_bpc_future.py
```

Representative probes:

```text
BPC_future/results/probe_t05_active_label_ids_sanity_20260604.csv
  tranq05_03: OPTIMAL, time = 0.614287s

BPC_future/results/probe_a10_01_active_label_ids_sanity_20260604.csv
  apollo10_01: OPTIMAL, time = 1.744645s

BPC_future/results/probe_t04_active_label_ids_20260604.csv
  tranq10_04: TIME_LIMIT, primal = 207.893439, no certificate dual
  columns = 445
```

`tranq10_04` did not close within 60 seconds, but the profile-generation path
did improve:

```text
before active-id check:
  cg5 exact_retry returned 64 negative journeys at t = 58.579s
  total profile_generation_time through finish = 48.508s

after active-id check:
  cg5 exact_retry returned 64 negative journeys at t = 56.487s
  cg6 found the final 6 negative journeys at t = 59.355s
  total profile_generation_time through finish = 46.545s
```

The run still missed the final no-negative certificate because after cg6 only
about `0.42s` remained for cg7 exact pricing.

Additional timing-only instrumentation now records final streaming
`profile_filter_time`, separating it from generation and DP time.  A 25-second
diagnostic showed:

```text
BPC_future/results/probe_t04_active_filter_timing25_20260604.csv
  cg2 exact:
    profile_generation_time = 4.118362s
    profile_filter_time     = 0.106996s
    profile_dp_time         = 0.065324s

  cg3 exact:
    profile_generation_time = 4.203755s
    profile_filter_time     = 0.239933s
    profile_dp_time         = 0.194178s
```

Interpretation:

- The active-id check is safe and worth keeping as a small default
  micro-optimization.
- It is not enough to meet the 60-second target on `tranq10_04`.
- The next larger exact-pricing target should be a faster exhausted-catalog
  filter/index path or a stronger NG/DSSR certificate path.  At the very end of
  `tranq10_04`, the solver can have an exhausted sortie profile catalog but too
  little remaining time to filter the catalog and run the final profile DP.

20-task status remains substantially harder.  Existing `tasks20_02` trials with
the current physical/journey branch configurations remain `TIME_LIMIT` at about
200s, with no certificate dual.  The best incumbent in those trials is around
`486.081224`, so the 20-task target will require a stronger pricing/column
generation change rather than further small tail toggles.

## Streaming Online-Dominance Filter Skip (2026-06-04)

The streaming profile-pricing callback was still applying the full offline
cross-dominance filter to every streamed profile batch even when profile
generation had already applied online skyline dominance:

```text
journey_pricing_profile_online_dominance_enabled = True
journey_pricing_profile_cross_dominance_enabled  = True
```

For the label physical catalog path, the streamed profile list is already the
per-mask skyline.  Re-running `_filter_dominated_sortie_profiles` on the same
skyline does not change the candidate set, but it costs around `0.5-0.8s` per
late pricing call on 10-task Tranquillitatis hard-tail instances.

Implemented exact-safe change:

```text
if catalog_stats["online_dominance_applied"]:
  reuse streamed profiles directly
else:
  run the existing offline dominance filter
```

This preserves exactness because the online skyline uses the same dominance
predicate as the offline filter.  In a fixed task mask, subtracting task-cover
duals shifts every profile by the same dual sum, so the dominance relation does
not depend on the current dual vector.

Unit coverage:

```text
test_sortie_profile_filter_skips_batch_when_online_dominance_applied
test_label_physical_catalog_marks_online_dominance_applied
test_label_online_profile_dominance_matches_batch_filter
test_sortie_profile_online_skyline_matches_filter
```

Validation:

```text
python -m unittest BPC_future.tests.test_bpc_future \
  BPCFutureTests.test_sortie_profile_filter_skips_batch_when_online_dominance_applied \
  BPCFutureTests.test_label_physical_catalog_marks_online_dominance_applied \
  BPCFutureTests.test_label_online_profile_dominance_matches_batch_filter \
  BPCFutureTests.test_sortie_profile_online_skyline_matches_filter
python -m unittest BPC_future.tests.test_bpc_future -k direct_ng
python -m unittest BPC_future.tests.test_bpc_future -k compatible_profile_cache
python -m py_compile BPC_future/pricing/journey_pricing.py BPC_future/tests/test_bpc_future.py
git diff --check
```

Representative probes:

```text
BPC_future/results/probe_t05_online_filter_skip_20260604.csv
  tranq05_03: OPTIMAL, time = 0.616741s

BPC_future/results/probe_a10_01_online_filter_skip_20260604.csv
  apollo10_01: OPTIMAL, time = 1.718229s

BPC_future/results/probe_t09_online_filter_skip_20260604.csv
  tranq10_09: OPTIMAL, time = 51.477815s
  previous comparable single run: 59.775550s
  total profile_filter_time: about 5.066s -> about 0.000018s

BPC_future/results/probe_t04_online_filter_skip_20260604.csv
  tranq10_04: OPTIMAL, time = 57.105744s

BPC_future/results/probe_a10_04_online_filter_skip_20260604.csv
  apollo10_04: TIME_LIMIT, primal = 288.332462, dual = 268.585633
```

Full 10-task rerun:

```text
BPC_future/results/all_tasks10_online_filter_skip_20260604.csv
  18 / 20 OPTIMAL
  mean time  = 24.643803s
  total time = 492.876069s
  max time   = 60.157575s

remaining failures:
  apollo10_04:
    TIME_LIMIT, primal = 288.332462, dual = 268.585633, gap = 0.068486
  tranq10_04:
    TIME_LIMIT in full batch, primal = 207.893439, no certificate dual
    single-instance probe closes at 57.105744s
```

The full rerun improves over the previous current rerun:

```text
BPC_future/results/all_tasks10_current_docsread_20260604_final.csv
  17 / 20 OPTIMAL
  mean time  = 25.433208s
  total time = 508.664159s
```

`tranq10_09` is now comfortably below 60 seconds in both single and full runs.
`tranq10_04` remains a timing-borderline instance: after the filter skip it can
close as a single run, but in the full batch it still sometimes finds one late
negative column and leaves less than one second for the final no-negative
certificate.  `apollo10_04` is a different bottleneck: branch-tree search and a
remaining dual gap, not root profile filtering.

## Bound-Fathom Pool Integer Skip (2026-06-04)

In branch nodes, `_process_journey_branch_node` previously ran a node-local
integer journey-pool MIP after true-dual exact pricing had already exhausted,
even when the certified node LP objective was no better than the incumbent.
The outer branch driver would then immediately fathom the node by bound.

Implemented exact-safe skip:

```text
if exact pricing exhausted and LP bound >= incumbent - integer_tol:
  log journey_pool_integer_skip
  return COMPLETE with the certified LP bound
  let the outer branch driver fathom by bound
```

This cannot miss a better incumbent because every integer solution in that node
has objective at least the certified LP bound, and that bound is already no
smaller than the incumbent.

Unit coverage:

```text
test_journey_branch_node_skips_pool_integer_when_bound_fathoms
```

Validation:

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.\
  test_journey_branch_node_skips_pool_integer_when_bound_fathoms
python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.\
  test_journey_branch_node_reuses_pricing_trip_cache_across_cg_rounds \
  BPCFutureTests.test_journey_branch_node_trip_cache_override_is_branch_only
```

`apollo10_04` single-instance probe:

```text
BPC_future/results/probe_apollo10_04_skip_pool_bound_20260604.csv
  TIME_LIMIT, time = 60.080067s
  primal = 288.332462
  dual   = 268.585633
  gap    = 0.068486
  nodes  = 15
  columns = 241

log evidence:
  journey_pool_integer_skip events = 7
  journey_pool_integer events      = 7
```

The skip removed several redundant pool MIP calls, but those calls were not the
dominant cost on this instance.  A 90-second diagnostic still closes the same
instance:

```text
BPC_future/results/probe_apollo10_04_90s_20260604.csv
  OPTIMAL, time = 65.740480s
  nodes = 17
  columns = 242
```

Additional negative probes on `apollo10_04`:

```text
journey_child_priority_mode = lp_rounding:
  TIME_LIMIT, time = 60.070542s

journey_pricing_dp_same_completion_pruning_enabled = True:
  TIME_LIMIT, time = 60.078141s
  same-completion pruning triggered heavily
  total dp_same_completion_pruned_labels = 92815

lp_rounding + same-completion pruning:
  TIME_LIMIT, time = 60.098102s

journey_pool_integer_heuristic_enabled = False:
  TIME_LIMIT, time = 60.074913s
```

Representative regression after the skip:

```text
BPC_future/results/all_tasks05_after_pool_skip_20260604.csv
  20 / 20 OPTIMAL
  max time = 1.036385s

BPC_future/results/probe_10_representative_after_pool_skip_20260604.csv
  apollo10_01: OPTIMAL, time = 1.730391s
  apollo10_04: TIME_LIMIT, primal = 288.332462, dual = 268.585633
  tranq10_04:  TIME_LIMIT, primal = 207.893439, no certificate dual
  tranq10_09:  OPTIMAL, time = 53.481913s
```

Conclusion:

- Keep the skip as a small exact-safe cleanup.
- It does not solve the remaining 10-task target by itself.
- `apollo10_04` needs branch-node pricing/tree improvement.  The 90-second
  close shows the gap is about 5-6 seconds, not a fundamental objective gap.
- `tranq10_04` remains a separate root-tail timing-borderline case.

## Apollo 10-04 Branch Tail Diagnostics (2026-06-04)

After rereading the learning and exact-pricing design notes, all 5-task and
10-task instances were rerun with the current default path:

```text
BPC_future/results/all_tasks05_reread_docs_20260604.csv
  20 / 20 OPTIMAL
  mean time = 0.323019s
  max time  = 1.059167s

BPC_future/results/all_tasks10_reread_docs_20260604.csv
  19 / 20 OPTIMAL
  mean time = 24.664350s
  max time  = 60.050616s

remaining failure:
  apollo15_20km_tasks10_04_seed11055
    TIME_LIMIT, primal = 288.332462
    dual = 268.585633, gap = 0.068486
```

Current-code single-instance diagnostic:

```text
BPC_future/results/probe_apollo10_04_current70_20260604.csv
  OPTIMAL, time = 65.964770s
  nodes = 17
  columns = 242
```

The remaining 60-second miss is concentrated in the late branch certificate
tail.  In the 70-second run, the final expensive no-negative pricing calls were:

```text
node11: profile_generation_time ~= 3.52s
node12: profile_generation_time ~= 1.74s + 0.51s
node15: profile_generation_time ~= 2.33s
node16: profile_generation_time ~= 2.04s
```

Negative probes:

```text
BPC_future/results/probe_apollo10_04_child_incumbent_relation_20260604.csv
  TIME_LIMIT, time = 60.079820s

BPC_future/results/probe_apollo10_04_cert_fullscan1_20260604.csv
  TIME_LIMIT, time = 60.081645s

BPC_future/results/probe_apollo10_04_no_dual_stab_20260604.csv
  TIME_LIMIT, time = 60.081955s
```

These confirm that child ordering by incumbent relation, early certificate
full-scan, and disabling dual stabilization do not address this bottleneck.

An opt-in cross-node branch pricing cache was added for future experiments:

```text
journey_branch_pricing_cross_node_cache_enabled = False by default
journey_branch_pricing_cross_node_cache_max_entries = 20000
```

It is exact-safe because it only reuses pricing cache objects through the same
`price_journeys` API.  It remains disabled by default because the Apollo probe
did not improve:

```text
BPC_future/results/probe_apollo10_04_cross_node_cache_20260604.csv
  TIME_LIMIT, time = 60.059610s
```

RF same/separate transitive-closure pruning was also tested.  It is
mathematically safe and reduced local profile generation on `node11` from about
`3.52s` to about `1.09s`, but it changed the column/tree trajectory and worsened
the complete 70-second diagnostic:

```text
BPC_future/results/probe_apollo10_04_rf_closure_20260604.csv
  TIME_LIMIT, time = 60.049441s

BPC_future/results/probe_apollo10_04_rf_closure70_20260604.csv
  OPTIMAL, time = 68.320067s
```

Therefore RF closure pruning was not adopted as a default path.  The next
`apollo10_04` work should focus on reducing branch-node no-negative profile
generation without perturbing the column trajectory as strongly, or on a
production NG-route/DSSR certificate that can prove these late branch nodes
faster.

## Physical Catalog Key Probe (2026-06-04)

After the `apollo10_04` branch-tail diagnostic, two physical-catalog cache
experiments were tested.

1. Branchless physical catalog sharing was implemented as an opt-in diagnostic:

```text
journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled = False
```

The implementation shares only physical sortie profiles.  Current pricing still
recomputes reduced costs from the active true duals and applies branch filtering
before profile-DP selection.  It is therefore exact-safe, but it is not a
default speed improvement.

Probe result:

```text
BPC_future/results/probe_apollo10_04_shared_physical_catalog2_20260604.csv
  TIME_LIMIT, time = 60.074454s
  primal = 288.332462, dual = 268.585633
```

The shared branchless catalog lost useful `separate_vehicle` mask pruning and
did not close the hard branch-tail instance.  Keep it off by default.

2. A temporary task-order-key experiment closed `apollo10_04`:

```text
BPC_future/results/probe_apollo10_04_ignore_task_order_catalog_20260604.csv
  OPTIMAL, time = 53.242785s
  nodes = 5, columns = 233
```

However, this was caused by accidentally changing the historical root physical
catalog key semantics.  The old key is intentionally independent of
`task_order`; adding `task_order` to the key damaged root-tail behavior on
Tranquillitatis boundary instances.  The task-order-key change was reverted.

Restored-key validation:

```text
BPC_future/results/probe_tranq10_09_default_key_restored_20260604.csv
  OPTIMAL, time = 51.343195s

BPC_future/results/all_tasks05_after_catalog_key_restore_20260604.csv
  20 / 20 OPTIMAL
  mean time = 0.292046s
  max time  = 1.329532s
```

Conclusion: preserve the task-order-independent physical catalog key.  The
remaining useful path is still branch-tail profile generation reduction or an
NG-route/DSSR certificate, not branchless physical catalog sharing.

Additional diagnostic:

```text
BPC_future/results/probe_apollo10_04_no_physical_catalog_resume_20260604.csv
  TIME_LIMIT, time = 60.066382s
  nodes = 3, columns = 233
```

Disabling physical-catalog resume changes the tree but still does not produce a
60-second certificate.  Do not use this as a default either.

## Apollo20 Final-Probe Funnel Diagnostics (2026-06-04)

The current Resource-Aware Completion Bound funnel was tested on the historical
20-task hard representative:

```text
BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_20/
  apollo15_20km_tasks20_02_seed21018_logical_graph.json
```

The baseline final-probe configuration used the 20-task partial-bound trial
settings plus:

```text
journey_certificate_completion_bound_enabled = True
journey_certificate_completion_bound_final_probe_only = True
journey_certificate_completion_bound_root_only = False
journey_certificate_completion_bound_time_buckets = 6
journey_certificate_completion_bound_energy_buckets = 6
```

Result:

```text
BPC_future/results/probe_apollo20_02_cb_finalprobe_600s_20260604.csv
  TIME_LIMIT, time = 600.337800s
  primal = 486.360054
  nodes = 5, columns = 757
  completion-bound pricing calls = 0
```

Interpretation: this instance did not reach the Level-4 final-probe phase.
Ordinary Level 2/3 profile pricing kept finding true negative journeys for most
of the run.  The bottleneck is therefore not yet the final certificate cliff; it
is expensive profile generation while negative columns are still available.

Two Level 2/3 scheduling probes were tested and rejected as defaults:

```text
BPC_future/results/probe_apollo20_02_batch4000_partial8_600s_20260604.csv
  TIME_LIMIT, time = 600.025451s
  primal = 486.568881
  nodes = 5, columns = 745
```

Reducing the streaming batch to 4000 and returning 8 columns earlier lowers the
per-call latency, but it increases CG rounds and produces a worse incumbent.

```text
BPC_future/results/probe_apollo20_02_densecols_600s_20260604.csv
  TIME_LIMIT, time = 600.340165s
  primal = 486.533368
  nodes = 4, columns = 853
```

Returning denser 48/24-column batches strengthens the root LP faster, but delays
root exit and still misses the 200-second target.  Do not adopt either probe as
the mainline 20-task setting.

Current next target: reduce physical/profile generation cost before the final
certificate phase, or add a separate true-RC heuristic level that supplies
high-quality columns earlier.  Completion Bound should remain the Level-4 judge
and should not be promoted back into a negative-column worker.

## Apollo20 Dual-Oscillation Diagnostic (2026-06-04)

The same 20-task representative above was inspected for column-generation dual
oscillation.  The baseline log shows a real degeneracy/dual-jump component:

```text
baseline: probe_apollo20_02_cb_finalprobe_600s_20260604
  adjacent dual hash changes = 26 / 26
  adjacent support hash changes = 23 / 26
  dual_l1_delta mean/median/max = 101.15 / 95.86 / 220.13
  dual_linf_delta mean/median/max = 13.53 / 12.18 / 30.11
  rounds with |objective_delta| < 1 and dual_l1_delta > 50 = 9
  traditional dual stabilization accepted = 2 / 31
  main skip reason = not_tail_degenerate
```

Interpretation: this is not only a raw-label-pricing bottleneck.  The RMP is
highly degenerate and the active dual extreme point moves substantially between
column-generation rounds.  This supports the learning-dual-stabilization
direction, but it does not justify using smoothed/stabilized duals for official
proof.

A controlled diagnostic moved the existing traditional stabilized-dual selector
earlier in the funnel while forcing certificate exact pricing back to SCIP
original duals:

```text
BPC_future/results/probe_apollo20_02_stab_nontail_truecert_600s_20260604.csv
  TIME_LIMIT, time = 600.353307s
  primal = 485.864724
  nodes = 5, columns = 767
  rmp_solves = 32, pricing_calls = 31
  generated_sequences = 3,197,639
  evaluated_timed_trips = 4,310,611
  completion-bound pricing calls = 0

dual/pricing diagnostics:
  stabilized pricing calls = 7
  scip_certificate pricing calls = 3
  stabilization accepted = 8
  stabilization infeasible = 18
  adjacent dual hash changes = 26 / 26
  adjacent support hash changes = 20 / 26
  dual_l1_delta mean/median/max = 104.74 / 107.32 / 238.90
```

This slightly improved the incumbent (`486.360054 -> 485.864724`) and reduced
generated/evaluated profile work, but it did not reduce RMP or pricing rounds
and still timed out at the same tree size.  Do not promote non-tail traditional
dual stabilization as the 20-task mainline.  It is diagnostically useful, but
the stabilized-dual LP is too brittle (`INFEASIBLE` in 18 rounds) and does not
solve the proof bottleneck.

Exactness guard added after this diagnostic:

- exact pricing uses stabilized pricing duals only in non-certificate column
  search;
- if `certificate_candidate` is true, exact pricing uses SCIP/RMP original
  duals and logs `pricing_dual_source = scip_certificate`;
- if completion-bound direct-label pricing is enabled, exact pricing also uses
  SCIP/RMP original duals;
- learning-smoothed duals remain heuristic-only and certificate pricing uses
  `scip_learning_certificate`.

Current conclusion: dual oscillation is real, so GNN/Wentges-style task-cover
anchors remain a valid direction for Level 1/early column search.  However, the
20-task target still requires a stronger Level 2/3 true-RC column generator or a
tighter Level-4 resource-aware completion bound that is reached only after the
ordinary funnel stops adding columns.

## Standard-Phase Completion Bound Probe (2026-06-04)

The current `Resource-Aware Completion Bound` was tested as a non-final exact
pricing worker on the slow 10-task Tranquillitatis instance.  This is
intentionally outside the preferred "judge only" role, but it checks whether the
bound is tight enough to safely move earlier in the funnel.

Probe:

```text
instance:
  tranquilllitatis_balmer_like_20km_tasks10_04_seed11054

config overrides:
  journey_certificate_completion_bound_final_probe_only = False
  journey_certificate_completion_bound_after_retry_enabled = False

result:
  TIME_LIMIT at 120.298714s
  primal = 207.893439
  dual = None
  columns = 233
  exact pricing calls = 4
  max RSS ~= 4.6 GB
```

Detailed pricing evidence:

```text
cg=1 exact:
  completion_bound_enabled = True
  bound_build_time ~= 0.0025s
  lb_state_count = 539
  lb_pruned_labels = 98
  expanded before/after = 37,821 / 37,723
  status = INCOMPLETE, reason = time_limit

cg=1 exact_retry:
  completion_bound_enabled = True
  lb_pruned_labels = 39,528
  expanded before/after = 1,196,456 / 1,156,928
  status = INCOMPLETE, reason = direct_label_partial_negative_journey

cg=2 exact_retry:
  completion_bound_enabled = True
  lb_pruned_labels = 25,585
  expanded before/after = 294,011 / 268,426
  status = INCOMPLETE, reason = time_limit
```

Interpretation:

- Bound construction itself is cheap.
- The bound is still too loose to justify switching ordinary exact/profile
  pricing into direct-label completion-bound mode.
- Earlier activation caused label expansion and memory blow-up instead of a
  certificate speedup.

Mainline rule: keep Completion Bound as a Level-4 final-probe judge.  Do not
promote it into Level 2/3 negative-column work until its pruning ratio is strong
enough under an on/off audit.

## Mainline Enforcement Update (2026-06-04)

The official journey configs now encode Completion Bound as a required judge,
not as an ordinary worker:

- `journey_completion_bound_required = True` for the 5/10/20 mainline configs.
- `journey_certificate_completion_bound_enabled = True` and
  `journey_certificate_completion_bound_after_retry_enabled = True`.
- `journey_certificate_completion_bound_final_probe_only = True`; the bound is
  reached only after ordinary true-dual pricing is incomplete and adds no column.
- If ordinary exact pricing exhausts the state space and returns no column, that
  is already the certificate; the final-probe bound is not retried.
- The official bucket settings are coarse resource-aware bounds:
  `time_buckets = 6`, `energy_buckets = 6`.  Required configs reject values
  outside `[5, 10]` to avoid both raw-node bounds and memory-heavy fine grids.
- Required configs also reject non-positive
  `journey_certificate_completion_bound_after_retry_reserve_time`, because a
  final-probe judge with no reserved time is only nominally enabled.
- Completion-bound certificate pricing uses true SCIP/RMP duals.  Smoothed
  learning duals remain heuristic-only and are never used for the proof.

Operational run limits are 120 seconds for 5/10-scale runs and 600 seconds for
the 20-task smoke/proof config.  These limits are benchmark budgets; they do not
relax the exact certificate rule.

## Benchmark Update (2026-06-04)

Full 5-task and 10-task mainline runs were executed after learning prewarm:

```text
5-task:
  csv = BPC_future/results/mainline_required_tasks05_all_prewarm_20260604.csv
  OPTIMAL = 20 / 20
  max solver time = 1.506685s

10-task:
  csv = BPC_future/results/mainline_required_tasks10_all_prewarm_20260604.csv
  OPTIMAL = 20 / 20
  max solver time = 74.085263s
  >60s = 3 / 20
```

Completion Bound did not trigger in the 10-task slow cases, and that is the
correct behavior under the current funnel.  The ordinary true-dual profile
pricing was still finding valid negative columns in Level 2/3, and the final
rounds that returned `exhausted=True, no_negative_journey` already provided the
certificate.  Therefore, activating Completion Bound earlier would violate its
"judge only" role and repeat the previously observed memory-heavy failure mode.

Current bottleneck classification:

- `Tranq10_04` and `Tranq10_09`: root-node true-dual profile pricing tail.
- `Apollo10_04`: branch-tree proof cost, with 17 processed nodes.
- Completion-bound construction/pruning is not the active bottleneck on these
  10-task runs because the Level 4 gate is not reached.

Rejected probe:

- Raising `journey_pricing_streaming_min_negative_batch` and
  `journey_pricing_early_return_negative_min_count` from `16` to `32` worsened
  Apollo10_04 from `71.279s` to `79.188s`, so the next step should not be a
  global batch-size increase.

## 20-Task Final-Probe Budget Update (2026-06-04)

The first required-learning 20-task Tranquillitatis run did not hit memory
limits but failed to certify within the 600s budget:

```text
csv = BPC_future/results/mainline_required_tranq20_01_prewarm_20260604.csv
status = TIME_LIMIT
primal = 391.818439
nodes = 1
columns = 816
pricing_incomplete_nodes = 1
max RSS ~= 2.05 GB
```

Tail evidence:

```text
cg=55 exact:
  no negative journey found, but profile DP incomplete

cg=55 exact_retry:
  time ~= 188.7s
  no negative journey found, but profile DP incomplete

cg=55 exact_completion_bound_retry:
  reserve time ~= 3.9s
  completion_bound_enabled = True
  lb_state_count = 1029
  lb_pruned_labels = 1354
  expanded before/after = 9167 / 7813
  status = INCOMPLETE, reason = time_limit
```

Interpretation:

- The final-probe trigger is correct: it only fired after ordinary true-dual
  pricing and retry were incomplete, not after an exhausted no-column proof.
- The budget allocation was wrong for 20-task proof.  The ordinary retry spent
  nearly all remaining time and left the completion-bound judge only a few
  seconds.
- `moon_trek_20_smoke.yaml` now reserves `120s` for the after-retry
  completion-bound final probe.
- The next 20-task run should compare `lb_pruned_labels`,
  `expanded_labels_before_bound`, and final certificate status under this larger
  reserve.  If it still times out, the bound itself is too loose and must be
  tightened rather than activated earlier.

## 20-Task Capguard Update (2026-06-04)

The 120-second final-probe reserve was validated on the same 20-task
Tranquillitatis root instance.  The first uncapped reserve run confirmed the
role of the reserve but exposed an inner direct-label memory risk:

```text
result = manually killed during final-probe direct-label pricing
RSS before final probe ~= 2.1 GB
RSS after entering uncapped final probe ~= 4.5 GB -> 9.2 GB
```

Action taken:

- `JourneyPricingConfig.direct_journey_label_partial_max_states` was added as
  an inner partial-label budget for direct journey-label pricing.
- Required completion-bound configs now fail closed unless this budget is
  positive.
- The budgeted final probe returns `INCOMPLETE` with reason
  `direct_label_partial_state_budget` when the guard is hit.  This is exact-safe:
  it prevents a false certificate and reports the node as incomplete instead of
  exhausting memory.
- The final-probe override now maps three independent budgets:
  `max_sequences`, `max_dp_states`, and
  `direct_journey_label_partial_max_states`.

Budgeted rerun:

```text
csv = BPC_future/results/mainline_required_tranq20_01_capguard_20260604.csv
status = TIME_LIMIT
primal = 389.873056
nodes = 1
columns = 824
solver time = 492.750414s
max RSS ~= 2.40 GB
```

Final-probe evidence:

```text
remaining at final probe ~= 119.9s
completion_bound_enabled = True
lb_state_count = 1029
bound_build_time ~= 0.009s
lb_pruned_labels = 9,598
expanded_labels_before_bound = 87,170
expanded_labels_after_bound = 77,572
status = INCOMPLETE
reason = direct_label_partial_state_budget
```

Interpretation:

- The larger reserve now reaches the judge phase with meaningful time.
- The capguard fixes the immediate memory cliff.
- The current bound is still too loose for a 20-task certificate: the pruning
  ratio is useful but not decisive, and the partial-state budget is reached
  before proof exhaustion.
- The mainline now enables the exact-safe unique-task helper for the 5/10/20
  configs as the next tightening attempt.  This helper must be validated under
  the same on/off certificate semantics; it is not a license to move Completion
  Bound earlier in the funnel.

## Two-Cycle Top-2 Bound Contract (2026-06-04)

The next Completion Bound tightening target is 2-cycle elimination inside the
reverse bound DP.  This is motivated by the 20-task root final-probe failure:
the current resource-aware bound is safe but too loose, partly because a
memoryless reverse relaxation can create artificial local cycles such as
`A -> B -> A` and repeatedly collect task-cover dual reward.  The goal is to
tighten the final-probe judge without adding full NG memory or changing the
forward exact DP.

Scope:

- Apply 2-cycle elimination only to the Completion Bound reverse DP.
- Do not change ordinary forward exact pricing.  The forward exact oracle keeps
  its own exact/NG/DSSR state management and remains responsible for the final
  certificate.
- Activate V1 only for root final-probe experiments, initially through a feature
  flag such as `journey_certificate_completion_bound_two_cycle_enabled`.
- Keep it off by default until bound-on/off audits pass.

Reverse label memory:

```text
BackwardLabel:
  node
  time_bucket
  energy_bucket
  remaining_sorties
  slots
  cost
  prev_in_dp
```

`prev_in_dp` is the parent in the reverse DP search tree, i.e. the physical
successor node in the real path.  For a physical suffix `A -> B -> C -> Depot`,
when reverse DP expands from `C` to `B`, the label at `B` has
`prev_in_dp = C`.

Depot rule:

- Depot and virtual depot nodes are immune to 2-cycle checks.
- Only real task nodes participate in `prev_in_dp` collision tests.
- This is mandatory for exactness: `Depot -> A -> Depot` is a legal one-task
  sortie and must never be pruned as a 2-cycle.

State bucket:

```text
(node, time_bucket, energy_bucket, remaining_sorties, slots)
```

`slots` means the number of additional task visits available in the current
sortie.  `remaining_sorties` handles the macro sortie count separately.  Top-2
labels compete only inside this full bucket key.  Labels with different
remaining sorties or slots are not equivalent and must not evict each other.

Reverse extension rule:

```text
# Physical arc u -> v, reverse DP extends from v to u.
if u != depot and v != depot and u == label_at_v.prev_in_dp:
    block extension
else:
    create label_at_u with prev_in_dp = v
```

The initial depot label uses a dummy predecessor such as `-1`, which must not
collide with any real task id.

Top-2 storage rule:

- Do not include `prev_in_dp` in the state key.
- For each full bucket key, keep at most two labels with different
  `prev_in_dp`.
- If a new label has the same `prev_in_dp` as an existing label, keep only the
  lower-cost label.
- If the bucket already has two labels with different predecessors, replace the
  current higher-cost label only when the new label has a lower cost.
- Inside a bucket, compare only cost.  Do not preserve continuous time or energy
  residuals.  The bucket is the state-space relaxation; keeping residual
  sub-states would reintroduce memory growth.

Forward stitching rule:

When the forward final-probe label is at task `u`, use the physical predecessor
within the current sortie as `p`.  For the first task of a sortie, `p` is depot
and therefore immune to the 2-cycle collision rule.

```text
best_lb = inf
for reverse_label in top2_bucket(u, time_bucket, energy_bucket, remaining_sorties, slots):
    if p == depot or reverse_label.prev_in_dp != p:
        best_lb = min(best_lb, reverse_label.cost)
```

If the completed two-cycle table has no compatible label, return `inf`.  This
is safe only when the table was fully built; it means even the relaxed suffix
cannot complete without a forbidden immediate backtrack.

Budget and fallback rule:

- If two-cycle table construction hits any build budget, discard the entire
  two-cycle table.
- Fall back to the older memoryless resource-aware bound table.
- Never use a partially built two-cycle table for pruning.  Missing states in a
  partial table could create false `inf` values and invalid pruning.

Combination with set-based bounds:

```text
if two_cycle_table_complete:
    route_lb = LB_two_cycle(node, prev, time, energy, remaining_sorties, slots)
else:
    route_lb = LB_memoryless(node, time, energy, remaining_sorties, slots)

set_lb = LB_unique_task(available_tasks, remaining_visit_capacity)
final_lb = max(route_lb, set_lb)
```

The two-cycle bound is a resource/path lower bound; the unique-task helper is a
set/elementarity lower bound.  Taking the maximum of valid optimistic lower
bounds is exact-safe and should tighten pruning.

Required diagnostics:

```text
two_cycle_blocked_extensions
two_cycle_second_best_queries
two_cycle_incompatible_queries
two_cycle_top2_replacements
two_cycle_table_complete
two_cycle_fallback_to_memoryless
```

Validation:

- 5-task debug audit: strict equality of best true reduced cost with bound on
  and bound off.
- 10/20-task diagnostic audit: at minimum,
  `bound_on declares no negative => bound_off also declares no negative`.
- A budget-hit two-cycle table must not be used for audit certificates; it must
  report fallback to memoryless mode.

Implementation priority:

1. Add the feature flag and data structures.
2. Implement Top-2 reverse bucket maintenance and Depot immunity.
3. Add diagnostics and table-completeness fallback.
4. Run 5-task strict audit before any 20-task benchmark.
5. Probe the 20-task root final-probe with the flag enabled only at depth `0`.

Implementation status:

- `JourneyPricingConfig` now exposes
  `direct_journey_label_completion_bound_two_cycle_enabled` and
  `direct_journey_label_completion_bound_two_cycle_max_states`.
- Certificate configs map these through
  `journey_certificate_completion_bound_two_cycle_enabled` and
  `journey_certificate_completion_bound_two_cycle_max_states`.
- Two-cycle is forcibly disabled when `depth > 0`, even if branch-node
  Completion Bound itself is enabled.
- `moon_trek_5_journey.yaml`, `moon_trek_10_journey.yaml`, and
  `moon_trek_20_smoke.yaml` all enable the two-cycle probe at the root final
  probe.  The feature is still forcibly disabled at branch depth `> 0`.
- If the Top-2 table exceeds its build-state budget, the implementation clears
  the table and falls back to the older memoryless bound.
- Runtime logs include the required two-cycle diagnostic counters.

## Two-Cycle Probe Result (2026-06-04)

### 5/10-Task Mainline Probe

The 5/10 configs were also tested with two-cycle enabled through CLI overrides
before making the flag explicit in the YAML configs:

```text
5-task two-cycle override:
  csv = BPC_future/results/mainline_required_tasks05_all_twocycle_override_20260604.csv
  status = 20 OPTIMAL / 20
  solver-time sum = 9.460941s
  mean = 0.473047s
  max = 1.516591s
  completion-bound events = 0
  two-cycle events = 0

10-task two-cycle override:
  csv = BPC_future/results/mainline_required_tasks10_all_twocycle_override_20260604.csv
  status = 19 OPTIMAL / 20, 1 TIME_LIMIT
  solver-time sum = 572.349007s
  mean = 28.617450s
  max = 75.283105s
  completion-bound events = 1
  two-cycle events = 1
  two_cycle_table_complete = 1
  two_cycle_fallback_to_memoryless = 0
  two_cycle_blocked_extensions = 15,390
  two_cycle_second_best_queries = 10,935
  two_cycle_incompatible_queries = 10,935
  two_cycle_top2_replacements = 33,728
  two_cycle_build_time ~= 0.30s
```

A same-code-version 10-task run with two-cycle disabled was then executed for a
clean A/B comparison:

```text
csv = BPC_future/results/mainline_required_tasks10_all_current_twocycle_off_20260604.csv
status = 19 OPTIMAL / 20, 1 TIME_LIMIT
solver-time sum = 569.640s
mean = 28.482s
max = 75.192s
```

Interpretation:

- Enabling two-cycle on 5-task has no runtime effect because the final
  Completion Bound probe is never reached.
- On 10-task, the only two-cycle activation completed its table and did not
  fall back.  It added about 0.30s of reverse-DP build time and did not change
  the proof outcome.
- The `tranquillitatis_balmer_like_20km_tasks10_03_seed11036` TIME_LIMIT occurs
  with two-cycle both enabled and disabled.  Its direct reason is
  `direct_label_partial_state_budget`, so it is a current final-probe budget
  issue rather than a two-cycle correctness regression.

Follow-up probes on the same 10-task instance showed that the certificate probe
was being cut off by generic proof budgets, not by wall-clock time:

```text
failed current config:
  reason = direct_label_partial_state_budget
  partial_max_states = 40,000
  expanded_labels_before_bound = 60,674
  status = TIME_LIMIT
  solver time ~= 22.5s

partial_max_states = 200,000:
  reason = direct_label_sequence_budget
  max_sequences = 100,000
  status = TIME_LIMIT
  solver time ~= 26.6s

certificate budgets = 1,500,000 sequences / 1,500,000 partial states:
  csv = BPC_future/results/probe_tasks10_03_cert1500k_20260604.csv
  status = OPTIMAL
  primal = dual = 197.875013
  solver time = 48.311273s
  max RSS ~= 1.85 GB
  generated_sequences = 978,460
  expanded_labels_before_bound = 1,211,881
  expanded_labels_after_bound = 403,371
  lb_pruned_labels = 808,510
  two_cycle_table_complete = True
```

The first attempt to make these large budgets the default for every 10-task
final probe was rejected: it made
`tranquillitatis_balmer_like_20km_tasks10_01_seed11000` spend the remaining
time in an unnecessarily heavy certificate probe and return TIME_LIMIT.  The
accepted design is therefore a proper multi-level certificate funnel:

1. Keep the normal lightweight final-probe budgets.
2. If, and only if, the lightweight final probe reports a proof-budget reason
   such as `direct_label_partial_state_budget` or `direct_label_sequence_budget`,
   and enough wall-clock time remains, run one escalated true-dual
   Completion-Bound probe.
3. The escalated probe keeps Resource-Aware Completion Bound and two-cycle
   bounding enabled; it only raises the generic proof budgets.

`moon_trek_10_journey.yaml` enables this escalation path with:

```text
base final probe:
  max_sequences = 100,000
  max_dp_states = 150,000
  partial_max_states = 40,000

escalated final probe:
  min_remaining_time = 90s
  max_sequences = 1,500,000
  max_dp_states = 500,000
  partial_max_states = 1,500,000
```

### 20-Task Root Probe

The two-cycle Top-2 implementation was tested on the same 20-task
Tranquillitatis root instance used for the capguard baseline:

```text
csv = BPC_future/results/mainline_required_tranq20_01_twocycle_20260604.csv
status = TIME_LIMIT
primal = 389.873056
nodes = 1
columns = 824
solver time = 494.826498s
max RSS ~= 2.42 GB
```

Final-probe comparison against the previous capguard run:

```text
capguard final probe:
  lb_pruned_labels = 9,598
  expanded_labels_before_bound = 87,170
  expanded_labels_after_bound = 77,572
  reason = direct_label_partial_state_budget

two-cycle final probe:
  two_cycle_table_complete = True
  two_cycle_fallback_to_memoryless = False
  two_cycle_state_count = 64,827
  two_cycle_blocked_extensions = 42,354
  two_cycle_second_best_queries = 2,407
  two_cycle_incompatible_queries = 2,407
  two_cycle_top2_replacements = 129,244
  two_cycle_build_time ~= 1.17s
  lb_pruned_labels = 9,598
  expanded_labels_before_bound = 87,170
  expanded_labels_after_bound = 77,572
  reason = direct_label_partial_state_budget
```

Interpretation:

- The two-cycle table built completely and did not fall back to memoryless mode.
- The reverse DP did eliminate many artificial two-cycle extensions, so the
  mechanism is active.
- It did not increase forward pruning on this hard 20-task root certificate:
  `lb_pruned_labels` and expanded-label counts are identical to the capguard
  baseline.
- Therefore the current root proof bottleneck is not primarily caused by
  immediate 2-cycles in the reverse bound.  The direct-label final probe still
  exhausts the inner partial-label budget before proving no negative journey.

Next implication:

- Keep the two-cycle implementation and diagnostics because they are exact-safe
  and useful for future instances.
- Do not expect two-cycle alone to close the 20-task certificate gap.
- The next tightening should target the forward partial-label explosion directly
  or add a stronger suffix lower bound than immediate 2-cycle elimination.
