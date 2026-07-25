# P0 V2 GAT 定价方向：oracle action-headroom gate 收口

日期：2026-07-25

## 1. 执行结论

当前 P0 V2 上不应开始训练 root dual-center linear/MLP/GAT，也不应生成
checkpoint 或 deployment manifest。

原因不是现有网络不够复杂，而是对候选学习动作做完无模型、
实例内泄漏的 perfect-information oracle 检查后，scale30 仍没有达到
可以覆盖推理生命周期成本的端到端 headroom：

- scale30 P0 fresh root-CG control 为 `82.393–83.016 s`、53 rounds；
- 达到首轮 7% wall 改善至少需要进入约 `76.8–77.2 s`；
- 实测最好的完整候选是动态 tail batch256，`82.190 s`、53 rounds，
  只处于运行噪声量级；
- 其余对偶中心、ASCG L1 sidecar、任务/arc/prefix oracle 和全局
  多列 batch 均明显变慢，甚至在 300 秒内未完成。

因此本次 gate 的状态是：

```text
ROOT_DUAL_CENTER_TRAINING_AUTHORIZED = false
PRICING_PREFIX_GAT_TRAINING_AUTHORIZED = false
CHECKPOINT_CREATED = false
DEPLOYMENT_MANIFEST_CREATED = false
P0_V2_CONTROL_CHANGED = false
PRODUCTION_NO_CUT_CHANGED = false
```

这是对“当前 P0 V2 的 root pricing 中，这组学习动作是否值得建模”的
否决，不是说 GAT 在所有 BPC、所有问题和所有结构中都无效。

## 2. 文献方法与本次还原

近三年的相关工作给出了三类最有代表性的方向。

1. ICML 2024 的
   [Adaptive Stabilization Based on Machine Learning for Column Generation](https://proceedings.mlr.press/v235/shen24e.html)
   预测最优 dual，并通过自适应稳定化把当前 dual 拉向预测中心。
   该方法的关键不是网络名称，而是“高质量 dual center +
   solver-side stabilization”。本次实现了 development-only 的
   L1 stabilized RMP sidecar，并直接使用同一实例的未来 true-dual
   trajectory 作为泄漏 oracle；这比真实可训练模型更强。
2. INFORMS Journal on Computing 2023/2024 的
   [dual prediction and stabilized CG](https://pubsonline.informs.org/doi/abs/10.1287/ijoc.2023.1277)
   与
   [ML warmstart for column generation](https://pubsonline.informs.org/doi/10.1287/ijoc.2022.0140)
   同样依赖“预测 dual 对当前问题确实能改善后续 CG 轨迹”。本次既测试
   final true dual，也测试 tail dual face 和从真实 route trajectory
   反向拟合的中心。
3. AAAI 2024 的
   [RL multiple-column selection](https://ojs.aaai.org/index.php/AAAI/article/view/28661)
   和 AAAI 2025 的
   [FFCG](https://ojs.aaai.org/index.php/AAAI/article/view/33222)
   用多列或可变列族减少 CG 迭代，同时惩罚冗余列。本次把这一想法还原
   为固定 batch128、动态 tail batch256，以及从 P0 未来轨迹泄漏得到
   的 task/arc/prefix 优先级。

这些论文证明相应动作在它们的 cutting stock、graph coloring、
unit commitment 或 VRPTW 设置中有效，但不能替代 Moon Trek 当前
exact solver 上的 action-headroom 检查。先运行 oracle 的意义正是：
如果 perfect-information action 都不快，GAT 不可能靠逼近这个 action
获得稳定净收益。

## 3. 新训练目标已经与旧四系数成本隔离

虽然 gate 不允许正式训练，训练接口已按无泄漏目标实现，供后续在
动作空间发生实质变化后复用。

主目标不是对任意一个最终 dual 做 coordinate MSE，而是同一 early
root context 下的 route trajectory ranking：

```text
observed_batch_utility =
    max(0, current_RMP_bound - next_RMP_bound)
    / measured_pricing_wall_sec

L =
    1.00 * counterfactual_route_trajectory_loss
  + 0.10 * set_valued_dual_face_regularizer
  + 0.05 * active_column_feasibility_hinge
```

约束如下：

- utility 只来自实际观测的 matched trajectory；
- 未探索 route 永远不当负样本；
- 下一轮 bound gain 只能分配到整个已选 batch，不伪造 per-column
  Shapley credit；
- 多个等价 dual 用 set-valued face regularizer，不强迫模型拟合某个
  偶然的退化 dual；
- 模型同时输出 normalized residual 和 log variance；
- `1.00/0.10/0.05` 是三个 loss 的无量纲权重，不是求解目标中的旧
  operating/risk/completion 四系数成本；
- prefix oracle 使用 reciprocal-rank ordinal credit，不把 seconds、
  labels、RC 等不同物理量线性混合；
- official objective 仍由 exact solver 的 normalized objective
  唯一定义。

所以当前代码中：

```text
legacy_four_coefficient_cost_used = false
mixed_physical_unit_cost_formula_used = false
```

旧 route-admission/branch 研究对象与新的 dual-center objective 分属
不同模块，不能互相作为 checkpoint-selection metric。

## 4. Oracle 实测

所有实例均来自冻结 development split：

- scale20：`lunar_ice_020_043_seed100766001`，
  content hash `fabdf89b92bcde3b`；
- scale30：`lunar_ice_030_017_seed110740001`，
  content hash `6d085f5edc474c17`。

未读取 full80 的 5/10/20/30 正式 test outcome，也未读取现有
50/100 shadow test outcome。

### 4.1 scale20

| 动作 | wall | rounds | 结果 |
|---|---:|---:|---|
| fresh P0 collected control | 3.398512 s | 15 | exact closed |
| positive-unlabeled Native prefix oracle | 3.135797 s | 17 | exact closed |
| ASCG-style leaked dual-center sidecar | 2.808499 s，含 20 ms 模拟推理 | 12 | exact closed |

scale20 存在局部可利用信号，但它不能单独授权共享模型。尤其 prefix
oracle 虽然 wall 较低，却增加了 rounds；必须由 scale30 同方向收益
确认，不能把单次 wall 波动当作稳定机制。

### 4.2 scale30

| 动作 | wall | rounds | 相对 P0 的判断 |
|---|---:|---:|---|
| fresh P0 controls | 82.393–83.016 s | 53 | control |
| future-final-dual harvest | 109.469 s | 56 | 明显退化 |
| ASCG L1 sidecar + future final dual | 152.487 s | 34 | rounds 少但 wall 大幅退化 |
| trajectory-RC fitted center + L1 sidecar | 96.190 s | 40 | 退化 |
| one-shot early leaked center | 178.329 s | 60 | 大幅退化 |
| whole-run leaked task priority | 300.205 s | 54 | incomplete |
| nearest-context prefix priority | 181.399 s | 67 | 大幅退化 |
| exact round48-only prefix priority | 99.337 s | 56 | 退化 |
| global batch128 | 123.882 s | 52 | 退化 |
| dynamic tail batch256 | 82.190 s | 53 | 噪声量级，远未达到 7% |
| tail-mean6 L1，round49 才激活 | 96.048 s | 54 | 退化 |

所有 closed arm 的最终状态均为 `CERTIFIED_NO_NEGATIVE`，certificate
仍来自 current true RMP dual。oracle discovery dual 不具备 certificate
权限，其候选必须在 true dual 下重新计算 reduced cost。

### 4.3 统计边界

这组运行是 action-class mechanistic oracle gate，不是总体性能
promotion test。每个规模只有一个 development sentinel，因此不能用
重复运行伪造独立样本，也不报告 population bootstrap CI。

但这里仍足以停止训练：

- 训练的必要条件是 perfect-information action 的 point estimate
  先明显越过包含生命周期成本的 7% 门槛；
- scale30 最佳 point estimate 仅约 1% 且在噪声范围；
- 更强的未来信息、多种 release timing 与多列动作全部未跨过门槛；
- 没有 oracle headroom 时继续扩大 sentinel quota，只是在估计
  “接近零的动作效果”，不会让 GAT 超越其监督策略。

若未来改变了定价算法的动作空间，必须重新跑这道 oracle gate；不能
拿本次 scale20 的局部结果直接开始 linear ranker。

## 5. 为什么在 scale30 不生效

证据支持以下机制解释。

1. **dual 退化使“最终 dual 更接近”不等于“更快”。**
   Moon Trek root RMP 存在多个近似等价 dual face。把 early dual 拉向
   某个未来 dual 会改变新负列出现的顺序，却不保证减少 exact pricing
   或 RMP 重优化的总工作。
2. **定价是序列决策，不是静态 top-k。**
   在第 `t` 轮看来最好的 route 会改变第 `t+1` 轮 RMP 和 dual。
   使用未来路线作静态 task/arc/prefix priority 产生 distribution
   shift，scale30 上 rounds 从 53 增到 56/67，甚至无法在 300 秒关闭。
3. **少 rounds 不是端到端收益。**
   ASCG arm 从 53 rounds 降到 34，但 sidecar、不同列集和更重的
   final-judge 轨迹令 wall 从约 83 秒升到 152 秒。
4. **多列不是越多越好。**
   batch128/256 会减少部分重新求解机会，但引入大量冗余列；只有
   tail batch256 接近持平，没有足够余量支付 GAT tensorize/forward。
5. **scale20 信号不能外推到 scale30。**
   同一个 prefix/dual-center 思路在 20 上改善、30 上退化，正是
   跨规模训练计划必须先设 worst-scale gate 的原因。

## 6. Exact-safe 边界

新增路径全部默认关闭，并满足：

- development oracle 只能接受 development content hash；
- oracle center 标记 `development_only=true`、`deployable=false`；
- guidance 只影响 discovery/order，不过滤合法 route/label；
- true reduced cost 必须复核；
- oracle、stabilized dual 和 heuristic priority 均不能产生
  no-negative certificate、lower bound 或 pruning；
- incomplete arm 仍为 `BPC_INCOMPLETE_PRICING`，没有 certificate
  泄漏；
- scale5/10、engine mismatch 和 cheap gate 均能在导入 Torch、
  读取 checkpoint、构图之前 bypass。

## 7. 代码与证据

主要实现：

- `src/lunar_ice_bpc/exact/bpc/pricing/dual_stabilization.py`：
  development oracle center 和 release schedule；
- `src/lunar_ice_bpc/exact/master/journey_rmp.py`：
  ASCG-style L1 stabilized RMP sidecar；
- `src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py`：
  oracle discovery 与 true-dual re-audit；
- `src/lunar_ice_bpc/exact/bpc/solver/pricing_tail_solver.py`：
  bounded trajectory collection、adaptive tail batch 和 sidecar wiring；
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py`：
  no-filter task/arc/prefix priority 与 bounded prefix trace；
- `src/lunar_ice_bpc/guidance/dual_center_features.py`：
  framework-free 图与预算特征；
- `src/lunar_ice_bpc/guidance/dual_center_model.py`：
  linear、MLP、1-layer GAT、2-layer GAT 模型阶梯；
- `src/lunar_ice_bpc/guidance/dual_center_training.py`：
  route trajectory、dual face 和 feasibility losses。

可复现脚本：

- `scripts/run_p0v2_oracle_dual_center_root_gate.py`；
- `scripts/fit_p0v2_dual_center_trajectory_oracle.py`；
- `scripts/fit_p0v2_native_prefix_priority_oracle.py`。

持久证据位于：

```text
runs/p0v2_oracle_dual_center_root_gate_20260725/
```

该目录约 61 MiB；`data/gat_p0v2` 约 478 MiB。审计时文件系统剩余
约 806 GiB，主机可用内存约 12 GiB，没有遗留求解 worker。

测试结果：

```text
102 passed, 17 subtests passed
3 explicit fresh-subprocess pre-import bypass tests passed
git diff --check passed
```

## 8. 下一步建议

不建议继续在当前 root route ordering、dual-center 或 batch admission
动作上调 GAT。下一步应二选一：

1. 保持 P0 V2，转做无需在线 Torch 的 deterministic exact-pricing
   算法改进，直接减少 dominance/extension/RMP 的证明工作；
2. 若仍要求 GAT，则先提出一个与本次不同的可执行动作空间，并先做
   perfect-information oracle。例如真正改变定价分解、route family
   construction 或可证明安全的下界结构；仍需先通过跨 scale20/30
   action-headroom gate，再从 linear 开始。

在当前证据下直接训练 linear/MLP/GAT，会把“拟合成功”误当作“求解
加速成功”，并重复此前有效标签稀疏、每次调用都有成本、总体反而变慢
的问题。
