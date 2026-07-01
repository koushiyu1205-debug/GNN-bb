# B2 第二轮优化计划：Pricing-Tail Kernel & Negative-Search Worker

## 0. 当前定位

当前 `Lunar-GAT-BPC-Exact` 的主线仍然是：

```text
fixed-graph direct-DP oracle
  → journey RMP
  → true-dual pricing / no-negative certificate
  → branch-and-price tree
  → cuts/formulation
  → GAT exact-safe guidance
```

本轮仍然只处在 **B2: Pricing-Tail Optimization Layer**。  
本轮不进入：

```text
B3 branch tree
B4 cuts / formulation
B5 GAT guidance
route-order branch
live completion-bound pruning
live dual stabilization
```

本轮要解决的是：

```text
B2 第一轮已经证明：
    B2_PRODUCT_EXACT_SOLVER 可以作为 fixed-graph product exact fallback；
    B2A full-universe RC audit fast path 很有效；
    B2B seeded-tail-CG 还没有在 10/20 上显示真实改进。

所以 B2 第二轮目标不是继续堆 addability/duplicate 诊断，
而是把 B2B timeout 拆开，优化 root pricing-tail 中最贵的部分：
    final-judge enumeration
    time-to-first-negative
    addable negative discovery
    pricing cache reuse
    limited exact-safe worker
```

## 1. 本轮优化目标

### 1.1 产品级目标

B2 作为产品求解器必须继续保证：

```text
5 / 10 / selected 20
    能稳定输出 fixed-graph exact solution。

certificate_scope:
    DIRECT_DP_FIXED_GRAPH_OPTIMAL
```

这属于 **product exact solver**，不是 BPC 证书。

### 1.2 BPC 主线目标

B2B 的目标是推进真正的 root column generation：

```text
seeded column pool
  → RMP dual
  → fast negative-search worker
  → true-RC validation
  → addability-aware harvesting
  → re-solve RMP
  → exact final judge only when needed
```

本轮希望看到：

```text
10-scale selected5:
    至少出现一个真实 BPC root improvement：
        timeout → BPC_NODE_LP_CERTIFIED
        或者 final_judge_call_count / pricing_round_count / wall_time 明显下降
        或者 time_to_first_addable_negative 显著下降并成功 add columns

20-scale selected direct20:
    不强求 BPC_NODE_LP_CERTIFIED；
    但必须输出足够清楚的 pricing-kernel profile，
    证明 timeout 卡在哪里。
```

### 1.3 成功与失败的边界

B2 第二轮可以产生三类结论：

```text
A. B2_PRODUCT accepted:
    fixed-graph exact product solution 可用。
    这是产品层成果，不是 BPC 主线成果。

B. B2A accepted:
    full-universe RC audit fast path 可用。
    这是 full-universe audit 加速器，不是 seeded-CG 成果。

C. B2B_R2 accepted:
    seeded-root-CG 在 10/20 上有真实边际收益。
    只有这条成立，才允许把 B2B 作为进入 B3 的 accepted baseline。
```

如果 C 不成立：

```text
B2B_R2 只能保留为 diagnostic；
不能进入 B3；
不能把 B2_PRODUCT 或 B2A 的成功冒充成 BPC seeded-CG 成功。
```

## 2. 非目标

本轮禁止：

```text
1. 不修改 certificate scope 语义。
2. 不把 direct-DP result 升级为 BPC certificate。
3. 不启用 branch tree。
4. 不启用 cuts。
5. 不启用 GAT guidance。
6. 不让 worker-local no-column 产生 certificate。
7. 不默认启用 completion-bound pruning。
8. 不默认启用 task-set dominance。
9. 不引入 route-order branch。
10. 不用 B2A 的 full-universe success 证明 B2B scalable success。
```

## 3. BPC_future 经验吸收

### 3.1 Worker 与 final judge 分工

从 BPC_future 吸取的首要教训：

```text
fast worker 的任务是快速找到 true-RC negative；
fast worker 找不到列时只能返回 LOCAL_NO_COLUMN_UNCERTIFIED；
true-dual final judge 才能返回 CERTIFIED_NO_NEGATIVE。
```

所以本轮引入 worker 时必须保持：

```text
FOUND_NEGATIVE:
    worker 可以提供，经 manual RC 验证后加入 RMP。

LOCAL_NO_COLUMN_UNCERTIFIED:
    worker 可返回，但不能关闭 node。

CERTIFIED_NO_NEGATIVE:
    只能由完整 true-dual final judge 返回。
```

### 3.2 Harvesting 不是当前最大瓶颈

B2 第一轮显示，已跑通的负列几乎都是 addable：

```text
candidate_negative_count ≈ addable_negative_count
duplicate_only_count = 0
hidden_negative_count = 0
```

因此当前 10/20 timeout 的主因更可能是：

```text
final judge enumeration 太慢；
还没到 harvesting 能发挥作用的阶段。
```

所以 B2 第二轮应从“如何选择已找到的负列”转向：

```text
如何更快找到第一批 addable negative；
如何减少完整 final judge 的调用次数；
如何在不放松证明的情况下缓存/复用 fixed-universe 工作量。
```

### 3.3 优秀 BPC/VRPTW 文献中的通用思路

本轮吸收以下 branch-price / VRPTW labeling 思路，但全部保持 exact-safe：

```text
1. Heuristic pricing before exact pricing:
   先用 bounded worker 找负列；
   找不到不代表无负列；
   仍需 exact final judge closure。

2. Label-setting with dominance and resource extension:
   用资源可行性、时间窗、容量、能量、shadow 过滤标签；
   任何 pruning 都必须有 profiling 和 consistency audit。

3. Reduced-cost driven task ordering:
   使用正 cover dual、任务 science weight、active support deficit 排序扩展；
   只影响搜索顺序，不影响 universe。

4. Cache feasible structures, not reduced-cost conclusions:
   sortie / journey feasibility 可缓存；
   reduced cost 必须用当前 RMP dual 重新计算。

5. Early negative return:
   CG 中前期只需找到足够 addable negative；
   不必每轮都证明 no-negative；
   final judge 只在 closure 阶段完整扫描。
```

## 4. B2 第二轮模块设计

## 4.1 B2E: Negative-Search Worker

### 4.1.1 目标

实现一个新的 exact-safe worker：

```text
B2E_negative_search_worker
```

它的目标是：

```text
在给定当前 RMP dual 的情况下，
更快找到一批 true-RC negative journey columns。
```

它不能：

```text
certificate no-negative；
official lower bound；
prune node；
permanently reject true-RC negative；
改变 pricing universe。
```

### 4.1.2 输入

```text
LunarIceData
ReducedCostContext / JourneyDuals
ColumnPool
MasterColumnView
active_task_sets
hidden_negative_seed_catalog
negative_eps
worker_budget:
    max_task_sets
    max_sequences
    max_labels
    max_wall_time
    max_addable_negatives
```

### 4.1.3 候选生成顺序

按以下优先级产生 candidate task sets / sequences：

```text
1. positive cover dual tasks:
   pi_i > 0 的任务优先。

2. active support deficit:
   当前 RMP primal support 中覆盖薄弱或被 fractional 分散的 task sets。

3. B0 incumbent neighborhoods:
   direct-DP incumbent journeys 的 task set 子集、邻近替换、合并/拆分。

4. singleton + pair + triplet seeds:
   先小集合找强负列，避免直接爆 full sequence enumeration。

5. hidden-negative seed catalog:
   从上一轮 final judge / limited diagnostic 中记录的 hidden negative task sets。

6. science/risk/resource heuristic:
   science_weight 高、窗口紧、风险/能耗结构特殊的任务组合。
```

### 4.1.4 输出

```text
worker_status:
    FOUND_NEGATIVE
    LOCAL_NO_COLUMN_UNCERTIFIED
    INCOMPLETE_LIMIT

negative_columns:
    manual true-RC validated JourneyColumn list

metrics:
    time_to_first_negative
    time_to_first_addable_negative
    candidate_task_set_count
    candidate_sequence_count
    labels_generated
    labels_pruned_by_resource
    labels_pruned_by_time_window
    labels_pruned_by_dominance
    labels_pruned_by_completion_bound
    addable_negative_count
    duplicate_negative_count
    worker_wall_time
```

### 4.1.5 证书边界

硬规则：

```text
if worker_status == LOCAL_NO_COLUMN_UNCERTIFIED:
    node cannot close.

if worker_status == FOUND_NEGATIVE:
    every selected column must pass manual_journey_reduced_cost < -eps
    and ColumnPool.addability_check(...).would_enter_master == true.

if worker hits limit:
    status = INCOMPLETE_LIMIT.
```

## 4.2 B2F: Final-Judge Invocation Policy

### 4.2.1 目标

减少不必要的完整 final judge 调用。

新的 root loop：

```text
RMP solve
  → B2E negative-search worker
  → if enough addable negatives:
         harvest + add + continue
    else:
         exact final judge
  → if final judge finds negatives:
         harvest + add + continue
    else if final judge certifies no-negative:
         BPC_NODE_LP_CERTIFIED
    else:
         fail-closed incomplete
```

### 4.2.2 Worker-before-final-judge 规则

默认策略：

```text
run B2E worker before final judge
unless:
    round_index == final closure round
    or worker repeatedly found nothing
    or worker budget exhausted with no progress
```

必须记录：

```text
worker_call_count
worker_found_negative_count
worker_no_column_uncertified_count
worker_incomplete_count
final_judge_call_count
final_judge_saved_by_worker_count
```

### 4.2.3 Addable-negative early stop

如果 worker 找到：

```text
addable_negative_count >= max_addable_negatives_per_round
```

可以提前返回 `FOUND_NEGATIVE`，不继续枚举。

这不是剪枝，只是 CG 前期的 early return；closure 阶段仍需 exact final judge。

## 4.3 B2G: Feasibility Cache and Universe Reuse

### 4.3.1 目标

减少每轮重复构造 sortie / journey universe 的成本。

### 4.3.2 可缓存内容

允许缓存：

```text
sortie feasibility templates
task sequence feasibility
path-option signature feasibility
resource feasibility payload
journey structural signature
service timing under earliest-service lemma
```

不允许缓存为证书结论：

```text
negative / nonnegative reduced-cost conclusion
no-negative conclusion
dual-dependent reduced cost
official bound
```

### 4.3.3 Dual-dependent recomputation

每轮 RMP dual 变化后，必须重新计算：

```text
rc(p) = c_p - sum pi_i - mu - cut dual terms
```

缓存只能减少 feasible column materialization 成本，不能替代 RC audit。

### 4.3.4 Full-universe completion promotion

当 B2E/B2B 在某个 instance 上已经完整枚举固定 universe 时，可以把该 universe 标记为：

```text
full_universe_complete = true
```

之后允许走：

```text
B2A full-universe RC audit fast path
```

前提：

```text
all universe columns are present in current MasterColumnView
manual RC audit over all universe columns passes
dual_fingerprint_bound_to_rmp = true
proof_debt_queue empty
```

## 4.4 B2H: Proof-Tail Profiling

### 4.4.1 目标

让 10/20 timeout 可解释。

每个 failed row 必须回答：

```text
卡在 RMP？
卡在 worker negative search？
卡在 final judge label generation？
卡在 journey materialization？
卡在 completion-bound audit？
卡在 addability/duplicate？
```

### 4.4.2 必须新增字段

```text
rmp_wall_time
worker_wall_time
final_judge_wall_time
time_to_first_negative
time_to_first_addable_negative
labels_generated
labels_extended
sortie_templates_generated
journey_labels_generated
candidate_sequences_generated
path_option_assignments_generated
resource_prune_count
time_window_prune_count
dominance_prune_count
completion_bound_prune_count
bound_check_time
dominance_time
cache_hit_count
cache_miss_count
max_queue_size
peak_label_count
exit_reason
```

### 4.4.3 Exit reason taxonomy

```text
RMP_NOT_OPTIMAL
WORKER_FOUND_ADDABLE_NEGATIVE
WORKER_NO_COLUMN_UNCERTIFIED
WORKER_INCOMPLETE_LIMIT
FINAL_JUDGE_FOUND_NEGATIVE
FINAL_JUDGE_CERTIFIED_NO_NEGATIVE
FINAL_JUDGE_INCOMPLETE_LIMIT
DUPLICATE_ONLY
ROW_TIME_LIMIT
TASK_COUNT_EXCEEDS_MAX_DIRECT_TASKS
```

## 4.5 B2I: Exact-First-Step Bound Profile

### 4.5.1 目标

引入 BPC_future 中较有价值的窄优化思想：

```text
exact first step uses real travel/resource numbers；
suffix remains optimistic。
```

本轮先作为：

```text
audit / ordering / profiling
```

不默认 pruning。

### 4.5.2 可记录字段

```text
exact_first_step_bound_enabled
exact_first_step_bound_pruning_enabled = false
exact_first_step_bound_evaluated_count
exact_first_step_bound_tightened_count
exact_first_step_bound_time
would_prune_count_if_enabled
consistency_status
```

### 4.5.3 后续升级条件

只有同时满足：

```text
bound-on/off consistency
direct-DP/BPC alignment unchanged
no missing negative due to bound
profiling shows net benefit
```

才允许进入 opt-in pruning。默认仍关闭。

## 5. B2 第二轮求解器模式

### 5.1 B2_PRODUCT_EXACT_SOLVER

用途：

```text
产品级 fixed-graph exact solution。
```

允许使用：

```text
direct-DP fixed universe solver
```

输出：

```text
certificate_scope = DIRECT_DP_FIXED_GRAPH_OPTIMAL
uses_true_dual_bpc_certificate = false
```

它不证明 BPC。

### 5.2 B2A_FULL_UNIVERSE_RC_AUDIT

用途：

```text
full universe 已经完整时的 root LP certificate fast path。
```

输出可以是：

```text
BPC_NODE_LP_CERTIFIED
```

前提：

```text
full universe complete
all columns in master
manual RC audit pass
dual fingerprint bound
proof debt empty
```

### 5.3 B2B_R2_SEEDED_TAIL_CG

用途：

```text
真正的 seeded root column generation 主线。
```

新流程：

```text
seed pool
  → RMP
  → B2E worker
  → addable-negative harvest
  → repeat
  → exact final judge closure
```

### 5.4 B2C_LIMITED_PRICING_DIAGNOSTIC

用途：

```text
bounded diagnostic only。
```

不能 certificate。

### 5.5 B2D_PROOF_TAIL_KERNEL_PROFILE

用途：

```text
更详细 profiling。
```

不能 certificate。

## 6. 消融实验设计

每轮输出：

```text
CSV rows
JSON summary
中文 markdown report
```

### 6.1 必跑矩阵

```text
5-scale full:
    B0
    B1A
    B1B
    B2_PRODUCT
    B2A
    B2B_R2
    B2C
    B2D

10-scale selected5:
    same modes

10-scale full:
    如果 selected5 的 B2B_R2 wall time / profiling 可接受，则继续 full 20。

20-scale fail-closed guard:
    max_direct_tasks < 20
    验证所有 BPC modes fail-closed。

20-scale selected direct20 probe:
    至少 5 instances
    modes:
        B0
        B1A
        B1B
        B2_PRODUCT
        B2A
        B2B_R2
        B2C
        B2D

30-scale fail-closed diagnostic:
    max_direct_tasks < 30
```

### 6.2 Row 字段

至少输出：

```text
scale
instance_id
candidate_name
baseline_name
algorithm_status
certificate_scope
uses_true_dual_bpc_certificate
pricing_state
product_exact_solution_scope
product_exact_solution_count
direct_dp_fallback_used
B0_direct_objective
root_lp_bound
root_lp_bound_official
root_bound_le_B0_objective
pricing_round_count
rmp_wall_time
worker_call_count
worker_wall_time
worker_found_negative_count
worker_no_column_uncertified_count
worker_incomplete_count
time_to_first_negative
time_to_first_addable_negative
final_judge_call_count
final_judge_wall_time
labels_generated
labels_extended
sortie_templates_generated
journey_labels_generated
candidate_sequences_generated
path_option_assignments_generated
cache_hit_count
cache_miss_count
candidate_negative_count
addable_negative_count
selected_count
added_to_master_count
duplicate_only_count
hidden_negative_count
replacement_only_round_count
manual_rc_audit_pass
pricing_rc_audit_pass
proof_debt_unreleased_count
wall_time
exit_reason
fail_closed_reason
improvement_reason
```

### 6.3 Summary 指标

```text
product_exact_solution_count_by_scope
BPC_NODE_LP_CERTIFIED_count
B2A_fast_path_certified_count
B2B_R2_certified_count
B2B_R2_real_scale_improvement_count
mean_wall_time
p90_wall_time
mean_time_to_first_negative
mean_time_to_first_addable_negative
mean_labels_generated
mean_final_judge_wall_time
mean_worker_wall_time
mean_added_to_master_count
duplicate_only_count
hidden_negative_count
root_bound_gt_B0_violation_count
direct_root_official_leak_count
manual_rc_fail_count
pricing_rc_fail_count
proof_debt_unreleased_certified_count
```

## 7. 通过标准

### 7.1 红线

必须全部为 0：

```text
root_bound_gt_B0_violation_count
direct_root_official_leak_count
manual_rc_fail_count
pricing_rc_fail_count
certificate_scope_regression_count
objective_mismatch_count
b1_5scale_regression_count
proof_debt_unreleased_certified_count
```

### 7.2 Product exact 通过标准

```text
5/10/selected20:
    B2_PRODUCT_EXACT_SOLVER returns DIRECT_DP_FIXED_GRAPH_OPTIMAL
    objective matches B0 direct-DP
    uses_true_dual_bpc_certificate=false
```

### 7.3 B2A 通过标准

```text
5-scale full:
    no regression vs B1A

10-scale selected5:
    B2A gives BPC_NODE_LP_CERTIFIED where B1A timed out or is slower

No redline violations.
```

### 7.4 B2B_R2 通过标准

B2B_R2 才是是否进入 B3 的关键。

强通过：

```text
10-scale selected5:
    at least 1 instance:
        B1B/B2B_v1 timeout or fail-closed
        B2B_R2 returns BPC_NODE_LP_CERTIFIED
```

或中等通过：

```text
10-scale selected5:
    B2B_R2 does not close,
    but shows at least two of:
        time_to_first_addable_negative decreases
        final_judge_call_count decreases
        final_judge_wall_time decreases
        labels_generated before addable negative decreases
        added_to_master_count increases before timeout
        fail_closed_reason becomes materially more specific
```

20-scale selected direct20:

```text
B2B_R2 not required to close.
But it must produce clear pricing-kernel profile.
```

如果 B2B_R2 没有 10/20 real-scale improvement：

```text
B2B_R2 remains diagnostic.
Do not enter B3 with B2B_R2 as accepted baseline.
```

## 8. 下一步决策

### 8.1 可以进入 B3 的条件

```text
B2B_R2 strong pass
and all redlines = 0
```

### 8.2 只能进入 B3 diagnostic 的条件

```text
B2B_R2 only improves 5-scale
or only improves reporting/profile quality
or only B2A succeeds
```

此时 B3 只能做 5-scale branch correctness smoke，不能宣称 scalable BPC improvement。

### 8.3 继续 B2 的条件

```text
B2B_R2 no 10/20 improvement
and profiling shows final judge enumeration bottleneck
```

继续方向：

```text
stronger negative-search worker
exact-first-step bound opt-in
feasibility cache reuse
dual-aware task ordering
B0 incumbent neighborhood worker
```

## 9. Codex 实现纪律

Codex 必须遵守：

```text
1. 不修改 certificate scope 语义。
2. 不让 B2C/B2D 产生 official bound。
3. 不让 B2_PRODUCT 冒充 BPC。
4. 不默认启用 completion-bound pruning。
5. 不启用 GAT/cuts/branch tree。
6. 所有 worker no-column 都是 LOCAL_NO_COLUMN_UNCERTIFIED。
7. 所有 true-RC negative 必须经过 manual RC 验证。
8. 所有 selected harvest 必须 would_enter_master=true。
9. 所有 report 必须分 scope 统计 exact/optimal。
```

## 10. 本轮最终目标总结

本轮 B2 第二轮不是为了“写更多诊断字段”，而是为了回答：

```text
1. 5/10/20 是否有产品级 fixed-graph exact solver？
2. B2A 是否稳定作为 full-universe audit fast path？
3. B2B seeded-CG 为什么在 10/20 timeout？
4. worker-before-final-judge 能否让 B2B 在 10-scale 出现真实改善？
5. 如果不能，下一轮究竟该优化哪个 pricing kernel bottleneck？
```

最终接受标准：

```text
B2_PRODUCT accepted
B2A accepted
B2B_R2 either accepted as next BPC baseline
    or remains diagnostic with a precise bottleneck profile.
```
