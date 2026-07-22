# Native Live SRI Branch-Price-and-Cut V1 计划评审意见

> 评审对象：`Native Live SRI Branch-Price-and-Cut V1 正式计划`  
> 评审基线：仓库最新审查提交 `ee2f853c003589cb717399209fe232dc793a854b`  
> 评审范围：SRI 数学有效性、RMP/Phase-I、Native Exact SPPRC、Ryan–Foster 分支、cut lineage、证书绑定、性能实验与晋级门槛

---

## 1. 执行摘要

### 1.1 总体结论

该计划在数学方向和总体架构上是可行的，但当前版本不宜直接作为“正式默认主线切换计划”执行。

建议采用以下结论：

```text
研发实施：Conditional GO
直接正式晋级：NO-GO
```

也就是说：

- 可以进入 Native Live SRI 的正确性闭环、root-only live-cut 原型和分层性能实验；
- 不应在第一轮就默认启用完整 root+node live cuts；
- 是否晋级为 5/10/20/30 默认主线，必须由冻结策略后的 fresh paired benchmark 决定；
- “20/30 p50 至少下降 10%”应作为晋级门槛，而不能当作当前已有证据支持的预期结果。

### 1.2 当前基础

当前代码已经具备较好的 Live SRI 基础：

- HiGHS RMP；
- Native exact SPPRC；
- Ryan–Foster same/different-journey branching；
- Native cut dual 和 overlap state；
- Python reconstruction 与 manual true-dual reduced-cost 审计；
- branch/cut context 及其 hash 接口；
- fail-closed certificate boundary；
- 5/10/20/30 no-cut exact baseline。

但以下能力仍未形成正式闭环：

- Phase-I + 非空 CutContext；
- branch tree 节点携带不可变 cut lineage；
- root/node cut separation 与 column generation 的完整循环；
- live-cut certificate 的完整 dual/context 绑定；
- cut-aware Phase-I node infeasibility proof；
- active cuts 下的性能稳定性；
- 逐列 Native/Python/RMP reduced-cost 三方一致性门禁。

---

## 2. 分项评判

| 模块 | 评判 | 说明 |
|---|---|---|
| SRI 数学模型 | 可行 | SRI-3/SRI-5、divisor=2 对 set-partitioning 整数解有效 |
| fleet lower-bound cut 保持诊断态 | 正确 | 不应在 V1 中扩大 cut family |
| global/local cut lineage | 可行 | 需要 canonical ordering、不可变 context 和 lineage hash |
| BPC 循环 | 基本可行 | 当前流程必须显式插入 Phase-I 分支 |
| Phase-I + active SRI | 可行 | 需要完整重建 RMP dual、pricing objective 和 certificate 语义 |
| Native cut state | 可行 | 固定数组方向正确，但必须使用紧凑类型并防止截断 |
| completion bound | 正确 | active cuts 下继续强制关闭 |
| separator | 不完整 | 缺少候选集合完整枚举/启发式生成的正式定义 |
| certificate binding | 不完整 | 仅 branch hash + cut hash 不足，必须绑定 true dual 等 |
| 性能目标 | 高风险但可测试 | cuts 可能缩树，却严重削弱 subset dominance |
| 50/100 不测试 | 不可接受 | 至少要保留 no-cut bounded regression |
| 实验设计 | 基本合理 | 30-scale 需要至少 3 次重复，且筛选与正式实验必须隔离 |

---

## 3. SRI 数学设计

### 3.1 有效性

对任务集合 \(S\)，令一条 journey column \(r\) 与 \(S\) 的交集大小为：

\[
k_r = |S \cap r|
\]

对于整数 set-partitioning 解，每个任务恰好被覆盖一次，因此：

\[
\sum_r k_r \lambda_r = |S|
\]

又有：

\[
\sum_r \left\lfloor \frac{k_r}{2} \right\rfloor \lambda_r
\le
\left\lfloor \frac{\sum_r k_r\lambda_r}{2} \right\rfloor
=
\left\lfloor \frac{|S|}{2} \right\rfloor
\]

因此以下 SRI 对全部整数可行解有效：

\[
\sum_r \left\lfloor |S\cap r|/2 \right\rfloor\lambda_r
\le
\left\lfloor |S|/2 \right\rfloor
\]

对应：

- SRI-3：RHS = 1；
- SRI-5：RHS = 2；
- divisor = 2。

### 3.2 建议补充的正式交付

除小规模穷举外，还应提交：

1. 解析有效性证明；
2. property-based tests；
3. SRI coefficient/RHS 单元测试；
4. 随机整数 journey cover 解上的 validity audit；
5. 稳定 cut ID 与去重测试。

穷举测试不能替代数学证明，两者都需要保留。

---

## 4. 每节点正式 BPC 闭环应改写

原计划中的主循环没有明确说明：当当前 branch+cut context 下的 RMP 不可行时，如何进入 Phase-I。

建议将节点算法改为以下固定流程。

```text
0. 构造该节点最终 active branch context 与 inherited cut context。

1. 求解 Phase-II RMP。

2. 如果 Phase-II RMP 不可行：
   2.1 构造 Phase-I RMP；
   2.2 在同一 branch+cut context 下运行 Phase-I pricing；
   2.3 若找到 Phase-I 负 reduced-cost 列，加入后继续 Phase-I；
   2.4 若人工目标降为 0，删除人工变量并返回 Phase-II；
   2.5 若人工目标 > eps，且 exact Phase-I pricing 已证明无负列，
       则节点可证明不可行；
   2.6 若 Phase-I pricing 不完整，则节点状态为 INCOMPLETE，
       不允许剪枝，不允许发不可行证书。

3. 如果 Phase-II LP 分数且仍有 cut 容量，执行 cut separation。

4. 若加入任何 cut：
   - 当前 RMP dual 失效；
   - 当前 pricing certificate 失效；
   - 当前 node LP certificate 失效；
   - 回到步骤 1。

5. 在最终 active branch+cut context 下执行 native exact pricing。

6. 若产生负 reduced-cost 列：
   - 加入列；
   - 回到步骤 1。

7. 若 exact pricing 证明无负列，执行终局 cut separation。

8. 若终局 separation 又加入 cut：
   - 旧 no-negative certificate 失效；
   - 回到步骤 1。

9. 若没有新 cut，或策略 cap 已达到：
   - 验证最终 RMP primal cut violations；
   - 验证 certificate 全部绑定；
   - 才允许按 integrality、bound 或 Ryan–Foster branching 处理节点。
```

### 4.1 关于 `CUT_CAP_REACHED`

达到 cut cap 后继续精确定价是正确的。

未加入的有效不等式不属于精确性证书义务，因为 cuts 是可选强化，不是原模型可行性的必要约束。只要：

- 已加入 cuts 全部有效；
- pricing 对当前最终 active context 完整；
- 原始主问题与 branch constraints 得到精确处理；

节点仍可被精确闭合。

但 telemetry 必须区分：

```text
separator_complete_for_configured_family
cut_cap_reached
violated_candidate_count_before_cap
selected_cut_count
unselected_violated_candidate_count
```

不得把“达到 cap 后停止”描述成“没有其他 violated SRI”。

---

## 5. Phase-I + SRI 的正式数学语义

### 5.1 Phase-I RMP

建议使用任务覆盖人工变量：

\[
\min \sum_i y_i
\]

满足：

\[
A\lambda + y = \mathbf{1}
\]

\[
\mathbf{1}^{\top}\lambda \le K
\]

\[
C\lambda \le b
\]

\[
\lambda,y\ge 0
\]

其中：

- \(A\) 是任务覆盖矩阵；
- \(C\) 是 active SRI coefficient matrix；
- 人工变量在 SRI rows 上系数为 0。

### 5.2 Phase-I reduced cost

对真实 journey column \(j\)：

\[
\bar c_j^{I}
=
0
-
\sum_i \pi_i a_{ij}
-
\mu
-
\sum_k \gamma_k c_{kj}
\]

即：

- 正式成本、风险、weighted completion 权重全部为 0；
- fleet dual 继续进入 RC；
- cover dual 继续进入 RC；
- active SRI dual 必须进入 RC。

人工变量 \(y_i\) 的 reduced cost 为：

\[
1-\pi_i
\]

### 5.3 节点不可行判定

只有同时满足以下条件，才允许声明节点不可行：

```text
phase_one_artificial_objective > eps
AND
native exact Phase-I pricing complete
AND
no Phase-I negative reduced-cost journey exists
AND
branch/cut/dual/objective-mode binding all valid
AND
certificate redlines = 0
```

若 exact Phase-I pricing 超时、内存中止、frontier 非空或 hash 不匹配，则只能返回：

```text
INCOMPLETE
```

不能剪枝。

### 5.4 V1 边界

“人工变量在 cut rows 上系数为 0”仅适用于当前 V1 的 `<=` 型 SRI。

未来若加入：

- `>=` cuts；
- equality cuts；
- 需要 row artificials 的其他 formulation rows；

必须单独设计 Phase-I，不能自动复用本方案。

---

## 6. Certificate binding 必须加强

计划中仅绑定：

```text
branch_context_hash + cut_context_hash
```

不够。

同一个 branch/cut context 在不同 RMP 迭代下可产生不同 dual，因此 no-negative proof 必须绑定当前真实 dual。

建议每个正式 pricing/node certificate 至少绑定：

```text
instance_hash
model_id
config_hash
live_cut_policy_hash
native_engine_build_hash
objective_mode                  # official / phase_one
rmp_iteration_id
true_dual_binding_hash
branch_context_hash
cut_context_hash
cut_lineage_hash
negative_epsilon
active_cut_count
cut_state_schema_version
separator_policy_version
```

### 6.1 证书失效规则

旧 certificate 仅在以下全部相同时可复用：

```text
instance
model/config/policy
engine build
objective mode
RMP dual binding
branch context
cut context
epsilon
cut-state schema
```

发生以下任一事件必须失效：

- 加入或删除 cut；
- cut ordering 改变；
- RMP 重新求解导致 dual 改变；
- branch context 改变；
- 从 Phase-I 切换到 Phase-II；
- engine 或 config hash 改变；
- resume 的 context/dual binding 不匹配。

---

## 7. Cut context、lineage 与 column identity

### 7.1 Canonical ordering

固定数组中索引与 cut 的对应关系必须在以下层完全一致：

- HiGHS RMP；
- Python manual RC；
- Native request；
- C++ label state；
- checkpoint；
- resume；
- certificate。

建议 canonical ordering 使用：

```text
(cut_type, divisor, sorted_task_ids, stable_cut_id)
```

稳定 ID 可采用：

```text
sri:d2:n3:task001,task007,task012
sri:d2:n5:task002,task004,task009,task015,task020
```

### 7.2 三类 hash

应区分：

```text
active_cut_context_hash
    最终 active cuts 的 canonical 数学集合。

cut_lineage_hash
    global/local 来源、祖先继承路径和 policy version。

true_dual_binding_hash
    cover/fleet/cut dual 的当前数值绑定。
```

### 7.3 不要把 cut context 混入物理 column identity

建议保留两层签名：

```text
PhysicalColumnSignature
    用于 column pool 存储与物理 journey 去重；
    不随 cut context 改变。

PricingStateSignature
    用于 dominance、RC audit 与 certificate；
    包含 branch/cut state。
```

否则每次加入 cut 都可能把同一条物理 journey 误当成新列重复存储。

---

## 8. Native fixed cut state 的建议

当前动态 `vector<size_t>` cut overlap 会在 label copy 时引入堆分配与复制成本。使用内联定长数组方向正确，但类型必须紧凑。

不建议：

```cpp
std::array<std::size_t, 16>
```

因为这会给每个 label 增加约 128 字节。

建议：

```cpp
static constexpr std::size_t kMaxActiveCuts = 16;

struct CutState {
    std::array<std::uint8_t, kMaxActiveCuts> overlap{};
    std::uint8_t active_count = 0;
};
```

当前 V1 只包含 SRI-3/SRI-5，overlap 最大为 5，`uint8_t` 足够。

### 8.1 必须加入的安全门禁

```text
active_count <= 16
cut count 17 必须 UNSUPPORTED_FEATURE / fail closed
未知 cut type 必须 fail closed
overlap 不允许溢出
非空 cut context 不允许静默截断
只比较 active prefix
array tail 必须初始化为 0
cache/reuse 后不得残留旧请求 cut state
```

### 8.2 Dominance

Native dominance 必须继续比较完整 active-prefix overlap state。

不能只比较：

- 当前 cut coefficient；
- 当前 cut dual reward；
- overlap 的奇偶性；

因为两个当前贡献相同的 label，后续访问同一 cut 中剩余任务时可能产生不同的 marginal cut coefficient。

除非另行给出 dominance 有效性证明，否则保持保守的完整 overlap equality。

---

## 9. Separator 必须明确候选集合

原计划说明了 violation 计算，但未定义任务集合 \(S\) 如何产生。

必须正式选择以下一种语义。

### 9.1 完整枚举

30-scale 下：

\[
\binom{30}{3}=4060
\]

\[
\binom{30}{5}=142506
\]

根节点总计约 146,566 个候选，使用 bitmask/popcount 并只扫描正值列时是可行的。

推荐 V1：

```text
SRI-3：完整枚举
SRI-5：仅根节点完整枚举
```

实现建议：

- 将正值 RMP columns 预先编码为 task bitmask；
- 使用整数 `bit_count()` 或 Native popcount；
- 只保留 violation > tolerance 的候选；
- 使用容量受限 heap 维护 top candidates；
- 不要先构造全部候选对象再全量排序；
- 记录完整枚举数、实际 evaluated 数和总 separation wall time。

### 9.2 启发式候选生成

启发式 separator 也不会破坏精确性，因为 cut 是可选强化。

但输出必须明确：

```text
separator_complete_for_sri3 = false/true
separator_complete_for_sri5 = false/true
candidate_generation_policy
```

未找到 cut 时，只能说：

```text
当前候选生成策略未找到 violated SRI
```

除非确实完整枚举，否则不能说：

```text
不存在 violated SRI
```

---

## 10. 最大性能风险：cut-aware dominance 退化

当前 30-scale no-cut 性能高度依赖 visited-subset dominance。

加入 active cuts 后，保守 dominance 通常要求：

```text
lhs.cut_overlap_state == rhs.cut_overlap_state
```

active cuts 越多，可比较 labels 越少，因此可能出现：

```text
root/tree 节点数下降
但每次 exact pricing 的 labels、dominance checks 和内存大幅增加
最终 total wall 上升
```

因此第一轮不应只比较两个都启用 node cuts 的策略。

建议策略矩阵至少包括：

| 策略 | 根节点 | 非根节点 |
|---|---|---|
| P0 | SRI-3 | 无 |
| P1 | SRI-3 + SRI-5 | 无 |
| P2 | SRI-3 + SRI-5 | SRI-3 |

推荐分层逻辑：

1. 先验证 root-only cuts；
2. 仅当节点存在稳定 violated SRI-3 信号时测试 P2；
3. 若 root-only 已达到性能目标，不必为了“完整 BPC”强行加入 node cuts；
4. “正式 BPC”不要求每个节点都必须分离 cut，只要求支持合法的 live cut loop。

### 10.1 初始 cap 建议

原计划最大 active cuts = 16 在正确性上可行，但 V1 性能风险偏高。

建议第一轮：

```text
global_cut_cap = 4
lineage_local_cut_cap = 4
active_cut_cap = 8
```

确认 label count、peak memory、dominance rejection 和 proof time 没有明显退化后，再测试：

```text
8 + 8 = 16
```

---

## 11. Reduced-cost audit 必须逐列进行

正式 Live SRI certificate 不应只比较全局最小 RC。

应对每条 Native 返回 route 输出：

```text
column_signature
native_rc
python_manual_rc
rmp_cover_dual_contribution
rmp_fleet_dual_contribution
rmp_cut_dual_contribution
absolute_delta
accepted
```

正式门禁：

```text
rc_mismatch_count = 0
max_abs_rc_delta <= reconstruction_eps
all returned negative columns manually re-audited
cut dual sign audit pass
active cut coefficient vector audit pass
```

对于 no-negative proof，由于 Native 不会返回完整空间所有 columns，还必须要求：

```text
search_exhaustive = true
frontier_empty = true
labels_dropped = false
certificate_blockers = empty
cut state version/capability match
true-dual/context hashes match
completion bound effective = false under active cuts
```

---

## 12. `native_cut_state_enabled` 的改法

将“是否需要 cut state”由独立环境变量改成：

```text
cut_state_required = not CutContext.empty
```

是正确的，可以避免配置错误导致数学语义丢失。

但后端 capability gate 仍必须保留。

建议：

```text
请求层：
    cut_state_required = not CutContext.empty

Native capability：
    supported_cut_state_version
    supported_cut_types
    max_active_cuts
    supported_divisors
```

若不兼容：

```text
UNSUPPORTED_FEATURE
certificate fail closed
```

不应允许静默关闭 cut state，也不应在正式 live-cut 模式下自动退回不支持 cut 的后端后继续声称同等性能结果。

---

## 13. Completion bound

原计划规定 active cuts 时禁用 completion bound，这是正确的。

正式 telemetry 应记录：

```text
completion_bound_requested
completion_bound_effective
completion_bound_forced_off
completion_bound_forced_off_reason = active_cut_context
```

V1 不应顺便实现 cut-aware completion bound，以免范围失控。

---

## 14. 50/100 规模不能完全不测试

50/100 可以不做 Live SRI 性能验收，也可以保持 cuts 关闭和现有 host/native 调度策略。

但本计划会修改共享 Native 代码：

- `State` 内存布局；
- cut state 启用逻辑；
- graph cache 动态刷新；
- Native request schema；
- Phase-I objective mode；
- dominance hot path；
- context hash 和 IPC。

因此至少必须保留现有 no-cut bounded regression：

```text
50-scale：至少 1 个 bounded host run
100-scale：至少 1 个 bounded host run
```

门禁：

```text
legal incomplete or exact result
zero redline
no-cut path unchanged
host hash/restart/resume valid
peak RSS 无异常回归
cut_count = 0
cut_state_effective = false
```

建议将计划中的：

```text
50、100 规模暂不测试
```

改为：

```text
50、100 不参与 Live SRI 性能 promotion，
但必须运行现有 bounded no-cut regression。
```

---

## 15. Graph cache 专项测试

同一 instance、同一进程内依次执行：

```text
no-cut
→ cut A
→ cut A+B
→ cut B
→ no-cut
```

每一步检查：

- active cut count；
- canonical ordering；
- cut dual；
- Native/Python RC；
- proof state；
- graph cache hit；
- array tail 清零；
- context hash；
- 无上一请求 cut overlap 残留。

边界测试：

```text
cut count = 0, 1, 8, 16, 17
```

其中 17 必须 fail closed。

---

## 16. 策略筛选建议

### 16.1 Gate A：Non-mutating cut readiness

先不改变正式 solver 行为：

1. 在 fresh no-cut 20/30 root 和 selected branch nodes 上执行 diagnostic separation；
2. 记录 violated SRI 数量、最大 violation、support 和 restricted-RMP bound movement；
3. 确认 SRI signal 是否稳定存在；
4. 完成 Phase-I+cut、RC、hash、capacity、cache 测试。

若几乎不存在 violated SRI，停止 V1，不进入 live phase。

### 16.2 Gate B：Root-only Live SRI

比较：

```text
P0：root SRI-3 only
P1：root SRI-3 + SRI-5
```

运行：

- 5/10 full correctness；
- 20/30 selected hard instances；
- 50/100 bounded no-cut regression。

### 16.3 Gate C：Node-local SRI

仅在以下条件满足时加入 P2：

```text
branch nodes 存在稳定 violated SRI-3
root-only 没有明显 cut-aware pricing 回归
Phase-I+cut 节点闭环完整
label/memory/dominance telemetry 可控
```

P2：

```text
root SRI-3/SRI-5
node SRI-3
```

### 16.4 Gate D：Frozen promotion benchmark

策略筛选完成后：

1. 冻结 strategy；
2. 冻结 config hash；
3. 冻结 engine hash；
4. 新建全新输出目录；
5. 筛选运行不得进入 promotion 统计；
6. 开始全规模 paired benchmark。

---

## 17. 正式实验设计修正

### 17.1 重复次数

建议：

```text
5-scale：每实例每模式 10 次
10-scale：每实例每模式 10 次
20-scale：每实例每模式 3 次
30-scale：每实例每模式至少 3 次
```

30-scale 仅两次重复时，中位数等于两次的均值，不够稳健。

5/10 运行极快，5% 性能门槛很容易被进程启动和系统调度噪声影响，因此应增加重复次数。

### 17.2 进程级 strict cold-start

每次正式重复应满足：

```text
新 Python process
新 Native runtime
空 graph cache
不复用上一模式 checkpoint
不复用上一模式 column pool
不共享 no-cut/live-cut 的进程内 cache
```

单次 solver run 内部的同实例 graph reuse 可以保留，因为它属于算法正式实现。

### 17.3 AB/BA 顺序

AB/BA 交替顺序合理，但应与进程隔离同时使用。

建议根据 instance index 和 repeat index 确定性生成顺序，并写入 artifact。

### 17.4 配对统计

对每个实例：

\[
r_i =
\frac{\operatorname{median}(T_i^{live})}
     {\operatorname{median}(T_i^{base})}
\]

正式报告至少包含：

```text
scale-level live/base mean
scale-level live/base p50
median(instance paired ratio)
geometric mean(instance paired ratio)
improved instance count
regressed instance count
paired bootstrap 95% confidence interval
```

### 17.5 晋级门槛建议

20/30：

```text
live p50 <= 0.90 × no-cut p50
live mean <= no-cut mean
paired ratio point estimate <= 0.90
paired 95% CI upper bound < 1.00
all runs exact and zero redline
```

5/10：

```text
live mean <= 1.05 × no-cut mean
live p50 <= 1.05 × no-cut p50
无显著系统性实例回归
all runs exact and zero redline
```

---

## 18. Correctness 测试清单

### 18.1 SRI 基础

- SRI-3/SRI-5 coefficient；
- RHS；
- violation；
- stable ID；
- canonical ordering；
- dedup；
- deterministic top-k；
- 完整枚举 candidate count；
- 整数可行解 validity。

### 18.2 RMP 与 dual

- HiGHS cut row sense；
- cut dual sign；
- primal cut activity；
- primal cut violation；
- Phase-II manual RC；
- Phase-I manual RC；
- artificial variable reduced cost；
- Phase-I objective 与人工变量一致。

### 18.3 Native differential

至少覆盖：

```text
root/no-cut
root/cut-only
branch-only
branch+cut
Phase-I/no-cut
Phase-I+cut
cut count 1/8/16
```

比较：

- feasibility；
- objective；
- best RC；
- negative columns；
- no-negative proof；
- cut overlap state；
- certificate blockers。

### 18.4 Tree/lineage

- global cut 全树继承；
- local cut 仅后代继承；
- sibling isolation；
- immutable context；
- child context hash；
- checkpoint/resume；
- cut policy version；
- old certificate invalidation；
- branch+cut Phase-I infeasibility proof。

### 18.5 Fail-closed

以下任一情况必须禁止正式证书：

```text
active cut violation > tolerance
cut context hash mismatch
true dual hash mismatch
engine hash mismatch
cut count > 16
native cut-state capability missing
Phase-I+cut unsupported
RC mismatch
labels dropped
frontier nonempty
incomplete exact pricing
completion bound active under cuts
```

### 18.6 Native memory safety

- ASAN；
- UBSAN；
- fixed-array bounds；
- overlap overflow；
- graph-cache request switching；
- host IPC schema；
- cut count 17 rejection；
- repeated no-cut/cut/no-cut sequence。

---

## 19. 必须新增的 telemetry

每节点：

```text
node_id
parent_node_id
depth
branch_context_hash
cut_context_hash
cut_lineage_hash
global_cut_count
local_cut_count
active_cut_count
```

每次 separation：

```text
separation_round
subset_sizes
candidate_generation_policy
candidate_count
evaluated_candidate_count
violated_candidate_count
selected_cut_count
unselected_violated_count
cut_cap_reached
separator_complete_for_family
separation_wall_time_sec
termination_reason
```

每次 RMP：

```text
rmp_iteration_id
objective_mode
rmp_status
rmp_bound
positive_column_count
active_cut_violation_max
cut_dual_min/max/mean/nonzero_count
```

每次 pricing：

```text
objective_mode
true_dual_binding_hash
branch_context_hash
cut_context_hash
cut_state_version
native_exact_status
cut_aware_pricing_wall_time
extended_labels
dominated_labels
dominance_candidate_checks
subset_dominance_rejected_labels
peak_memory
best_found_rc
proved_no_rc_below
```

每个 certificate：

```text
certificate_scope
certificate_valid
certificate_blockers
instance/config/engine hashes
objective mode
RMP iteration ID
dual/branch/cut bindings
active cut primal violation max
RC mismatch count
```

---

## 20. 建议修改后的正式阶段定义

### Stage 0：Readiness

```text
Live cuts 默认关闭。
完成数学证明、separator、Phase-I+cut、RC/hash/cache/array 测试。
```

### Stage 1：Root-only Pilot

```text
P0/P1 root-only live SRI。
不启用 node cuts。
完成 5/10 full correctness 和 20/30 selected A/B。
```

### Stage 2：Node-local Pilot

```text
仅在节点存在稳定 cut signal 时测试 P2。
严格监控 label、dominance、memory 与 proof time。
```

### Stage 3：Frozen Paired Benchmark

```text
冻结 strategy/config/engine。
全新 cold-start paired experiments。
筛选数据不得混入 promotion 数据。
```

### Stage 4：Promotion

仅当所有规模门槛全部通过：

```text
将获胜策略设为 5/10/20/30 默认主线；
保留显式 no_cut rollback；
50/100 继续默认 no-cut；
更新交接文档和 certificate boundary。
```

---

## 21. 最终批准条件

在进入正式 paired promotion benchmark 前，必须全部满足：

### Correctness gate

- SRI 解析证明完成；
- Phase-I+cut 可运行并可证书化；
- Native/Python/HiGHS 逐列 RC 一致；
- global/local lineage 正确；
- old certificate invalidation 正确；
- cut count 17 fail closed；
- active cuts 下 completion bound 强制关闭；
- ASAN/UBSAN 通过。

### Integration gate

- branch tree queue node 携带不可变 CutContext；
- checkpoint/resume 保存 cut lineage 和 context hash；
- root/node/final separation loop 完整；
- certificate 绑定 dual、branch、cut、objective mode、engine/config；
- no-cut 配置与原主线等价。

### Performance-readiness gate

- diagnostic 中存在稳定 violated SRI signal；
- root-only pilot 至少不显著恶化 exact pricing；
- active cuts 未造成不可控的 label/memory 增长；
- 50/100 bounded no-cut regression 通过。

---

## 22. 最终评审结论

修正后的推荐结论如下：

> Native Live SRI Branch-Price-and-Cut V1 在数学上成立，现有 Native SPPRC 与 RMP 代码也具备实现基础，因此可以进入分层研发和正确性闭环。第一阶段应先做完整 SRI readiness 和 root-only live-cut，随后根据真实节点 cut signal 决定是否启用 node-local cuts。Phase-I 必须在最终 branch+cut context 下完成 exact pricing，证书必须绑定 true dual、objective mode、branch/cut context、config 和 engine。固定 cut state 应采用紧凑内联数组并对超过容量的请求 fail closed。50/100 不参与 Live SRI promotion，但必须保留 bounded no-cut regression。最终是否切换默认主线，只能由冻结策略后的 fresh paired benchmark 决定。

正式状态建议：

```text
Native Live SRI V1 implementation: CONDITIONAL GO
Root-only pilot: GO after readiness gates
Node-local live cuts: gated experiment
Default-mainline promotion: pending paired benchmark
```

---

## 23. 相关代码与报告位置

以下仓库位置应作为实施与审计重点：

```text
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/cuts.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/master/journey_rmp.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/cuts/cut_audit.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/solver/cut_formulation_solver.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/solver/branch_tree_solver.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/labeling_pricer.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py
GAT_BPC_moonTerk/native/lunar_spprc/src/native_pricer.cpp
GAT_BPC_moonTerk/tests/native/test_native_spprc_backend.py
GAT_BPC_moonTerk/tests/test_lunar_ice_labeling_pricer.py
GAT_BPC_moonTerk/runs/native_spprc_implementation_report_zh.md
```

