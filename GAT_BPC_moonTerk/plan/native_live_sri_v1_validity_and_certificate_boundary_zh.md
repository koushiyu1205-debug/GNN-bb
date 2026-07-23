# Native Live SRI BPC V1 数学有效性与证书边界

日期：2026-07-23  
状态：实现完成；正式 P0 promotion 未通过；默认策略仍为 `no_cut`  
适用范围：divisor=2 的 SRI-3/SRI-5、HiGHS journey RMP、Native exact SPPRC、Ryan–Foster branching

## 1. SRI 的有效性

给定任务子集 \(S\)，对 journey column \(r\) 记

\[
k_r=|S\cap r|.
\]

整数 set-partitioning 解满足每个任务恰好覆盖一次，因此

\[
\sum_r k_r\lambda_r=|S|,\qquad \lambda_r\in\mathbb Z_+.
\]

对任意非负整数序列都有

\[
\sum_r\left\lfloor\frac{k_r}{2}\right\rfloor\lambda_r
\leq
\left\lfloor\frac{\sum_r k_r\lambda_r}{2}\right\rfloor.
\]

故

\[
\sum_r\left\lfloor\frac{|S\cap r|}{2}\right\rfloor\lambda_r
\leq
\left\lfloor\frac{|S|}{2}\right\rfloor
\]

对原整数可行域有效。V1 只启用：

- SRI-3：系数 \(\lfloor|S\cap r|/2\rfloor\)，RHS=1；
- SRI-5：系数 \(\lfloor|S\cap r|/2\rfloor\)，RHS=2；
- row sense 固定为 `<=`，divisor 固定为 2。

fleet lower-bound cut 仍是诊断信息，不属于 V1 live family。

## 2. 分离器的证明范围

正式 separator 只读取当前 RMP 中 primal value 大于 0 的列，将每列任务集合预编码为 bitmask，并用 `popcount` 计算 SRI activity。对策略配置的 family：

- P0 在根节点完整枚举所有 SRI-3；
- P1 在根节点完整枚举所有 SRI-3 和 SRI-5；
- P2 在 P1 基础上，在非根节点完整枚举 SRI-3；
- violation 判定为 `activity - rhs > 1e-6`；
- capacity heap 只决定选择哪些 violated cuts，不减少被检查的候选集合。

只有 `full_enumeration_completed=true` 时，才能陈述“当前配置 family 中没有 violated SRI”。达到 cap 时必须同时记录未选 violated 数量，不能把 cap 停止写成无违反。

canonical cut ID 由 cut type、divisor、排序后 task IDs 唯一决定。`CutContext` 对数学重复和 ID 重复均拒绝，排序与 hash 与发现顺序无关。

## 3. Phase-I 与 active cuts

Phase-I 主问题为

\[
\min \sum_i y_i
\]

且满足

\[
A\lambda+y=\mathbf 1,\quad
\mathbf 1^\top\lambda\le K,\quad
C\lambda\le b,\quad
\lambda,y\ge0.
\]

真实 journey 在 Phase-I 中的原始目标为 0。其 reduced cost 为

\[
\bar c_j^I=0-\sum_i\pi_i a_{ij}-\mu-\sum_k\gamma_k c_{kj}.
\]

cover、fleet 和 active-cut dual 全部进入 pricing。覆盖人工变量在当前 `<=` SRI row 上的系数固定为 0；这个结论只适用于本 V1 SRI，不推广到未来 cut type。

只有同时满足以下条件才能证明节点不可行：人工目标严格为正；Phase-I exact pricing 已证明无负列；frontier 为空；无 label drop；所有 hash/capability binding 成立。其他情况一律返回 `INCOMPLETE`，不得剪枝。

## 4. Reduced-cost 一致性门禁

每条 Native 返回列均重建：

- Native reported reduced cost；
- Python manual reduced cost；
- objective、cover、fleet、cut 各分项；
- Native/Python 绝对误差。

正式 no-negative 证书必须满足：

```text
rc_mismatch_count = 0
max_abs_rc_delta <= reconstruction_eps
search_exhaustive = true
frontier_empty = true
labels_dropped = false
certificate_blockers = empty
```

若 request echo 或任一 binding 不一致，证书 fail closed。已经逐列审计为负 RC 的列可以作为候选列保留，但不允许用该次调用签发 no-negative proof；“列可用”和“证明可用”是两个独立结论。

## 5. 三类独立 hash

- `active_cut_context_hash`：只绑定 canonical active-cut 数学集合；
- `cut_lineage_hash`：绑定 global/local scope、origin node、ancestor path 和 policy；
- `true_dual_binding_hash`：绑定当前 cover/fleet/cut dual。

证书同时绑定 instance、model、config、policy、engine、objective mode、RMP iteration、branch context、cut-state schema、epsilon 和 active cut count。加入 cut、改变 branch、重解 RMP、dual 改变、Phase-I/II 切换或 resume binding 不符，都会使旧证书失效。

非零-dual projection 启用后，证书还独立绑定实际传入 Native 的
`pricing_cut_context_hash`、pricing cut count、projection enable flag 和 projection schema。
完整 `true_dual_binding_hash` 不做投影；所以即使 active row 当前 dual 为零，它的 dual 状态变化
仍会使旧证书失效。

物理列去重使用不含 branch/cut context 的 `PhysicalColumnSignature`。branch/cut 只进入 pricing state 与 certificate signature，避免同一物理 journey 因上下文变化被错误复制。

## 6. Native cut state 与 dominance

Native state 当前固定为：

```text
uint64_t packed_exact_overlap
SRI-3: 2 bits, exact 0..3
SRI-5: 3 bits, exact 0..5
maximum: 16 * 3 = 48 bits
```

策略 cap 为 global=4、lineage-local=4、active=8；engine 能力上限仍为 16。cut count=17、未知 type/divisor、task 不存在、state 截断或 schema/capability 不匹配都 fail closed。

packed state 保存完整 overlap，不只保存 `floor(overlap/2)`。dominance 比较完整精确 packed overlap，不使用未经证明的 parity 或 reward-only shortcut。cut dual reward 在 overlap 跨越 divisor 阈值时累加。completion bound 在完整 RMP active-cut context 非空时仍强制关闭，并记录 `active_live_sri_cuts` 原因。

## 7. 节点闭环

节点正式顺序是：Phase-II RMP；必要时在同一 branch+cut context 进入 Phase-I；exact pricing；完整 separation；若选中 cuts 则重解并重新 exact pricing；最后再次完整 separation；验证最终 primal cut activity 与全部 binding 后，才允许 integrality、bound pruning 或 Ryan–Foster branching。

global cuts 由整棵后代树继承。local cuts 只沿其产生节点的后代路径继承，siblings 隔离。P0/P1 不在非根节点继续分离，但根 cuts 仍属于所有后代的 active context。

## 8. 性能门控不是证明来源

在正式激活 proposed cuts 前，代码会解一次只用于筛选的 restricted RMP：只有 proposed RMP 已整数，或 restricted bound gain 至少为 `1e-4`，才提交 cuts；否则回退到此前已认证的 no-cut/current-cut 节点状态。

该门控只决定是否采用可选有效不等式，不是 lower bound、不可行性或 optimality 的正式证明来源。正式证书仍只来自最终 active context 下的 HiGHS RMP 与 exhaustive Native pricing。

## 9. 当前发布边界

- `no_cut` 是生产默认和显式 rollback；
- P0/P1/P2 能力已实现并测试；
- P0 已完成 1040-slot 正式 fresh paired promotion，但总状态为 `NOT_PROMOTED`；
- P2 node-cut 能力保留但默认关闭；
- 正式重复全部通过正确性门禁，但 P0 在 30 规模未通过 mean、paired point estimate 和 paired 95% CI 上界门槛，因此不得把任何 live policy 描述为默认主线；
- 5/10/20 虽分别通过性能门槛，也不得绕过“所有规模全部通过”条件而拆分切换；
- 50/100 始终默认 no-cut，bounded regression 的合法 incomplete 不等于 exact closure。

正式结果绑定 in-process engine `dfaedf6d273c5c56`。之后修复了仅由 host backend 执行的
signed-zero dual IPC 保真缺陷：合法 `-0.0` 不再被重建为 `+0.0`。该修复没有放宽 hash
检查；修复后的 50/100 host 回归都只因 `host_memory_limit` 合法 incomplete，dual-binding
mismatch 为 0。由于 source binding 随代码变化，当前 engine hash 与历史正式 hash 不同，
两者不得混写。

## 10. 已实现的 projection/状态压缩与 dominance 边界

以下两项已经实现，并保持如下边界：

1. RMP 必须维护全部 active cuts，以保证 primal feasibility 和 lineage；pricing request
   只携带当前 dual 数值严格非零的 active cuts。投影判断不用 epsilon；`±0.0` 删除，
   `-1e-15` 仍保留。certificate 继续绑定完整 RMP context、完整 true dual，同时另行绑定
   projected context。完整 active count=17 在投影前仍 fail closed。
2. SRI-3 overlap 最大为 3，使用 2 bit；SRI-5 最大为 5，使用 3 bit。实现保存精确 overlap，
   因而延伸时下一次 threshold crossing、terminal coefficient 和 dominance 都与压缩前相同。
   仅存 \(\lfloor overlap/2\rfloor\) 仍被禁止。
3. V1 dominance 继续要求完整 active-prefix overlap 相同。仅比较当前
   `cut_dual_reward` 大小不足以证明未来延伸下仍保持优势，因为两个 label 到下一次 threshold
   crossing 的距离可能不同。任何 reward-aware 或 componentwise dominance 都必须先证明
   对所有共同可行 suffix 保持 reduced-cost、资源和 branch/cut 可行性单调，再进入 exact
   proof engine。

当前 schema 为
`lunar_ice_bpc.native_cut_state.packed_exact_sri3_2bit_sri5_3bit_u64.v2`。
压缩前后真实 dual snapshot 的扩展 label 数完全一致，Native/Python SRI-3/SRI-5 reduced
cost 差分、Phase-I、0/1/8/16/17 cuts、graph-cache 序列、full/projected binding、全量 pytest
和 ASAN+UBSAN 均通过。
