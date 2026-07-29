# P0 V2 GAT 两个落点的因果 Oracle 验证

日期：2026-07-25

> 历史证据说明：本文绑定旧的 task-waiting P0 V2，只保留为动作空间
> 先验。当前 active experiment baseline 已更新为
> `FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3`。本文的 dual-center
> 和 branch top-3 数值不能直接用于 V3 训练或 promotion；V3 决策以
> `P0_NO_TASK_WAIT_V3_GAT_LANDING_REASSESSMENT_20260725_ZH.md` 为准。

## 1. 结论

本轮没有把“存在一个可评分的位置”误写成“GAT 已经有效”，而是把验证拆成四层：

1. exact-safe：排序不能改变合法候选宇宙、数学目标或 certificate；
2. action headroom：使用比可训练模型更强的反事实 oracle，动作本身是否有净收益；
3. model realizability：linear/MLP/GAT 是否能学到该动作，并覆盖完整推理开销；
4. held-out promotion：冻结模型在独立 calibration/final test 上是否仍有端到端收益。

本轮完成第 1–2 层，结论为：

| 落点 | exact-safe | action headroom | 当前决策 |
|---|---:|---:|---|
| GAT dual-center stabilization | 通过 | **失败** | `STOP`，不训练 |
| GAT top-3 branch ranking | 通过 | **通过** | 允许收集逐状态标签并从 linear baseline 开始；GAT 本身尚未验证 |

Production 默认和 P0 control 均未改变。

## 2. 为什么先做强 Oracle

如果一个使用同实例未来 true dual 的中心都不能产生端到端净收益，那么只根据当前历史预测中心的 GAT 不可能凭借更弱的信息可靠弥补该缺口。

同理，如果在完全相同的 exact root source 上，把 P0 已生成的合法 top-3 shortlist 分别作为真实分支动作运行到 exact closure，仍没有任何替代动作优于 P0，则没有理由训练 branch GAT。

因此本轮的判定对象是“动作空间是否值得学习”，不是网络拟合分数。

## 3. Dual-center stabilization

### 3.1 修正后的实验

旧实验的 L1 penalty 是固定线性 release，不是 ASCG 的自适应更新。本轮新增 development-only 的 faithful adaptive update：

```text
if stabilized_min_rc < 0:
    epsilon = stabilized_min_rc / (stabilized_min_rc - 1)
else:
    epsilon = 0

if epsilon < 0.01:
    release center
```

中心直接取同一 development 实例未来 exact closure 的 true dual。该信息发生未来泄漏，所以只能用于反事实上界，不能训练或部署；但它严格强于可训练 GAT 所能获得的信息。

所有 true-dual final judge、RC audit 和 certificate 语义保持不变。稳定化 dual 只影响发现轨迹，不能签发 no-negative certificate。

### 3.2 结果

| 实例 | P0 | adaptive oracle（含 20 ms 生命周期成本） | CG rounds | 净收益 |
|---|---:|---:|---:|---:|
| scale20/043 | 3.398512 s | 3.361303 s | 15 → 18 | +1.09% |
| scale30/017 | 83.016034 s | 137.728267 s | 53 → 35 | **-65.91%** |
| 合计 | 86.414546 s | 141.089570 s | — | **-63.27%** |

scale30 虽然把 rounds 从 53 降到 35，但 stabilized harvest 的单轮 exact 成本显著上升，最终慢 65.91%。这证明“减少 CG rounds”不能替代完整 wall-time 目标。

### 3.3 判定

```text
DUAL_CENTER_ACTION_SPACE_VALIDATED = false
DUAL_CENTER_TRAINING_AUTHORIZED = false
DECISION = STOP_DUAL_CENTER_STABILIZATION
```

scale20 的 1.09% 小收益不足以抵消 scale30 的明确反例，也小到无法与单次运行噪声可靠区分。不能为了保留 GAT 而只挑 scale20 正例。

## 4. Top-3 branch ranking

### 4.1 因果实验

每个实例只生成一次 exact root source，三个臂共享：

```text
rank-0: 选择 P0 shortlist 第 1 个候选
rank-1: 选择 P0 shortlist 第 2 个候选
rank-2: 选择 P0 shortlist 第 3 个候选
```

首轮固定 rank 实验的目的不是寻找可部署固定策略，而是验证 P0 shortlist 内是否存在可产生不同 exact 搜索成本的动作。所有臂均：

- 不扩大 shortlist；
- 不过滤候选；
- 排序前后 legal universe hash 相同；
- same/different 两个 child 均保留；
- 使用相同 root active columns；
- 运行到 `BPC_TREE_OPTIMAL`；
- 对比包含 20 ms 模拟 guidance 生命周期成本的 matched end-to-end wall time。

### 4.2 完整机会集合

只使用冻结 split manifest 中的 development 数据，未使用 full80 或既有 50/100：

| 规模 | manifest | 已有 tree artifact | exact tree | exact-actionable | exact 中机会率 |
|---|---:|---:|---:|---:|---:|
| 20 | 48 | 48 | 48 | 7 | 14.58% |
| 30 | 48 | 42 | 22 | 3 | 13.64% |

scale30 其余 20 个 artifact 和 6 个无 tree artifact 的实例没有 exact closure，未被伪装成负样本。反事实覆盖 exact-actionable 集合为 `10/10`。

### 4.3 结果

实例级 oracle 允许在 rank-0/1/2 中选择实测最快者，因而无收益时自动回退 P0：

| 集合 | 正收益实例 | P0 总时间 | oracle 总时间 | pooled 净收益 | instance-bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| scale20 | 4/7 | 244.514123 s | 226.602763 s | **+7.33%** | [2.43%, 12.27%] |
| scale30 | 1/3 | 692.784717 s | 682.567656 s | **+1.47%** | [0.00%, 4.99%] |
| 合计 | 5/10 | 937.298840 s | 909.170419 s | **+3.00%** | [0.82%, 7.20%] |

该 bootstrap 只覆盖实例抽样不确定性，不覆盖同一实例运行时噪声，也不代表 GAT 可实现该 oracle。

真实正例包括：

- scale20/002：不同运行顺序下 rank-1 均比 P0 快约 11–12%，排除了简单的 arm-order 偏差；
- scale20/014：rank-1 快 19.70%；
- scale20/034：rank-2 快 6.23%；
- scale30/035：rank-1 快 4.99%。

也存在明确反例：

- scale20/035：P0 50.26 s，rank-1 68.81 s，rank-2 74.20 s；
- scale30/004：P0 246.09 s，rank-1 313.34 s，rank-2 317.27 s；
- scale30/033：P0 242.02 s，rank-1 372.50 s，rank-2 332.15 s。

所以“永远选第二名”或“永远选第三名”都不可部署：

| 固定策略 | 10 个 exact-actionable 实例总时间 / P0 |
|---|---:|
| fixed rank-1 | **1.2229×** |
| fixed rank-2 | **1.2020×** |

这不是矛盾，而是 branch learning 的必要条件：替代动作有高杠杆，但正确动作高度依赖当前状态。

### 4.4 判定

```text
BRANCH_TOP3_ACTION_SPACE_VALIDATED = true
BRANCH_COUNTERFACTUAL_COLLECTION_AUTHORIZED = true
BRANCH_LINEAR_BASELINE_AUTHORIZED = true
BRANCH_GAT_TRAINING_AUTHORIZED = false
```

当前只有实例级 fixed-policy trajectory。它足以证明动作空间真实存在，但不足以证明 GAT 能识别动作。

## 5. 对实际 GAT 的约束

若继续 branch 方向，GAT 只能放在：

```text
exact node LP closure
  → P0 生成合法 Ryan-Foster shortlist
  → 对最多 3 个候选评分
  → 高置信时重排，否则 rank-0
  → 原 exact child creation / pricing / proof
```

它不能：

- 扩大或缩小候选宇宙；
- 删除 pair 或 child；
- 改变 bounds、pruning 或 certificate；
- 在 root-integral、shortlist 不足或 OOD 时导入 Torch；
- 使用固定 rank-1/rank-2 代替状态相关决策。

由于 exact-actionable 机会约占 exact 实例的 14%，模型不应在每个 pricing round 调用。只在真实 fractional branch node 调用，可以避免此前“稀疏收益、每处都付推理成本”的问题。

## 6. 下一步的最小实验

在训练任何 GAT 前：

1. 对每个 P0 actionable path 分别执行单次 rank-1/rank-2 deviation，其余节点恢复 P0，形成逐状态反事实；
2. 标签使用同 root、同 path 的 downstream exact work/time trajectory；incomplete 只作为删失下界；
3. 训练目标同时预测候选相对成本和 `abstain_to_p0`，而不是强迫每个状态改序；
4. 先跑 scale-equal、grouped-CV linear ranker；
5. linear 必须在 scale20 和 scale30 都优于 P0，并覆盖 fresh-runtime 生命周期成本，才允许 MLP/GAT；
6. GAT 只有显著优于 linear/MLP 才能晋级。

这一步将区分：

```text
动作存在收益
```

与

```text
现有状态特征足以让模型识别收益
```

后者尚未被本轮证明。

## 7. 可复现证据

- 汇总审计：
  `runs/p0v2_gat_landing_oracle_validation_20260725/two_landing_oracle_audit.json`
- 汇总脚本：
  `scripts/audit_p0v2_gat_two_landing_oracles.py`
- branch 配对运行器：
  `scripts/run_p0v2_branch_top3_oracle_gate.py`
- dual-center 配对运行器：
  `scripts/run_p0v2_oracle_dual_center_root_gate.py`
- branch exact-safe 实现：
  `src/lunar_ice_bpc/exact/bpc/solver/branch_tree_solver.py`
- adaptive penalty 实现：
  `src/lunar_ice_bpc/exact/bpc/pricing/dual_stabilization.py`
- 针对性测试：
  `tests/test_p0v2_gat_branch_oracle.py`
  `tests/test_p0v2_gat_dual_center.py`
