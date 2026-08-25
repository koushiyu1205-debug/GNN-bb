# P0V4+V5 统一 Temporal-GAT Production：思路、模型、算法、计划与当前状态审阅稿

> 文档性质：独立审阅稿，不是 promotion manifest，也不构成 production 授权  
> 项目：`GAT_BPC_moonTerk`  
> 当前实验：`p0v5_temporal_gat_production_v1_round5_20260824`  
> 取证快照：2026-08-25 15:36:23 CST  
> 当前 production default：`no_cut`  
> 当前 GAT 状态：未训练、未校准、未进入 development、未获部署授权  
> 当前运行阶段：`CONTEXT_ELIGIBILITY`，活动进程不得因本文档编写而中断

> **2026-08-25 protocol revision：** 用户已批准将失败恢复流程升级为 failure-aware reuse V2。Round 5 在 eligibility 完整结束后封存为 `Data Epoch D5`；后续 Policy Round 复用经 hash/access audit 证明有效的 D5 corpus、snapshots 和 eligibility，不再因任意 terminal negative 无差别重建全部数据。首个三臂 outcome 前必须冻结新协议和 Policy Round。权威修订见 `plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825_ZH.md`。

---

## 1. 一页结论

这条路线的核心不是让 GAT 参与求解正确性，而是让它在一个已经 exact-safe 的定价请求中，观察一次很短、真实发生的 QD1 动态响应，然后只决定继续使用 QD1，还是把**当前 frontier**迁回 Q0 comparator。

正式算法是：

```text
P0V5 bidirectional witness/prepass
        |
        | 未完成 exact pricing，需要 P0V4 fallback
        v
P0V4 exact fallback 使用 literal Q0
        |
        | scale30: 4096 pops
        | scale50: 16384 pops
        v
完整 frontier: Q0 -> QD1
        |
        | 冻结的 K ∈ {128, 512, 2048} 次真实 QD1 pops
        v
构造 t0/tK temporal multi-resolution graph
        |
        +--> CONTINUE_QD1
        |
        +--> MIGRATE_BACK_TO_Q0
                  （恢复当前 frontier 的 Q0 comparator）
```

目前的判断是：

1. **技术路线是合理的。** 它直接针对旧 GAT 失败的根因：单时点 frontier 很难预测切换 QD1 后的 label/dominance 动力学。
2. **exact-safe 外壳已经实现。** Native 四种 temporal trial mode、双向迁移、creation ID conservation、telemetry、portable ensemble inference、OOD/fail-closed 和 Python runtime binding 都已有代码。
3. **当前还没有模型效果。** Round 5 尚未运行 Q0 / CONTINUE_QD1 / REVERT_Q0 三臂，因此没有本轮 K、监督标签、GAT bundle、activation coverage 或 E2E speedup。
4. **现在完成的是实验基础设施和 outcome-blind 数据入口，不是 GAT 成功。** Corpus 已冻结，root context collection 已完成，eligibility replay 正在进行。
5. **最近的首要 gate 是 scale30 train context capacity。** 当前 raw snapshot 只覆盖 33 个 scale30 train instances，而 K gate 至少要求 32 个 determined instances，只有 1 个实例余量。
6. **即使 eligibility 通过，后面仍有多重高风险 gate。** K 的 force-on oracle、scale50 strong-benefit 支持、calibration 的零 harm 激活、GAT 对 simple/no-message control 的优势、portable parity、development、sealed final 和 formal acceptance 均未开始。
7. **production 没有变化。** 当前仍是 `no_cut`，既没有 candidate registry activation，也没有任何 GAT request 获得 production authority。

因此，当前项目可以评价为：**工程实现进入可实验状态，科学有效性尚未被本轮数据验证，production 晋升距离仍远。**

---

## 2. 为什么选择 Temporal-GAT，而不是继续做静态 frontier GAT

### 2.1 已知的动作证据

历史 fresh evidence 对 scale30 和 scale50 给出了完全不同的信号。

#### scale30：QD1 信号强，selector 的必要性较弱

已有两条相互独立的数据链支持 scale30 late-switch QD1：

| 证据链 | 关键结果 |
|---|---:|
| V3 real-map，instance-weighted GM | `0.778757` |
| V10R1，4096 boundary，fixed QPD1 net GM | `0.820842` |
| V10R1 determined instances | `8/8` |
| V10R1 harmful instances | `0` |
| V10R1 probe overhead GM | `1.003691` |

这说明 scale30 的主要问题是能否在独立 E2E 和 formal acceptance 中兑现确定性 QD1 收益，而不是是否能训练出一个复杂 selector。

但统一方案仍然保留 scale30 独立 head，原因是 production contract 要求两个尺度采用同一 encoder 和统一的审计/部署外壳，同时允许 scale30 学到接近 always-continue 的策略。

#### scale50：有 oracle headroom，但固定 QD1 风险不可接受

V10R1 在不同 boundary 上的结果是：

| Boundary | Fixed QPD1 GM | Oracle GM | Strong benefit | Harm |
|---:|---:|---:|---:|---:|
| 4096 | `1.262341` | `0.987423` | 0 | 3 |
| 8192 | `1.260554` | `0.982355` | 1 | 3 |
| 16384 | `1.160861` | `0.936561` | 1 | 3 |

16384 是唯一达到 `oracle GM <= 0.95` 的 boundary，但 fixed QD1 仍慢 `16%` 左右，且 harmful tail 约为 `1.70941x` 和 `3.03615x`。因此 scale50 不能 always-continue，也不能只依赖平均收益。

### 2.2 静态 GAT 失败的根因

旧路线使用 boundary 时刻的单时点图预测“QD1 是否会更快”。问题是 queue ordering 的 wall-time 效果是后验动力学：

- QD1 会改变 label 被弹出的顺序；
- 顺序会改变 label 到达 dominance bucket 的时间；
- 继而改变 frontier 增长、frontier churn、extended/dominated label 数；
- 也会改变 dominance candidate checks、首次负列出现时间和 proof tail 分布；
- 这些变化最终才决定真实 solver wall。

换言之，单时点图主要回答“现在 frontier 里有什么”，却未直接回答“使用 QD1 后 frontier 会怎样响应”。

历史 observability 结果也支持这一判断：

| 旧模型/审计 | scale50 结果 |
|---|---:|
| V7R3 GAT benefit BA | `0.609091` |
| V7R3 best control benefit BA | `0.654545` |
| V9R1 GAT benefit BA | `0.654545` |
| V9R1 best simple benefit BA | `0.709091` |

增加 label sample、multi-resolution graph 和模型容量并没有形成 topology advantage。

### 2.3 为什么短试运行比双 prefix counterfactual 更合适

V8/V8R1 曾使用两个独立辅助请求分别执行 Q0/QD1 prefix，再启动正式请求。该方法获得了 counterfactual response，但快速 scale30 context 无法摊薄重复 prefix 的固定税，逐 context 2% overhead gate 失败。

Temporal trial 改为在**同一个正式 exact request**里：

- 前 4096/16384 个 Q0 pops 只执行一次；
- QD1 trial 真实发生且计入总 wall；
- 决策后继续当前状态，不重启 pricing；
- revert 只迁移当前 frontier，不重复前缀。

它保留了动态观测，同时移除了两个独立辅助请求的重复成本。

### 2.4 我的核心因果假设

本轮真正要验证的不是“GAT 能否拟合 wall ratio”，而是以下三层假设：

1. **Action support 假设**：至少存在一个 K，使 trial 后 continue/revert 的 oracle 对 Q0 有足够净收益，同时 revert 本身不会形成严重税负。
2. **Observability 假设**：t0→tK 的 frontier/dominance/label-growth response 能区分 continue-benefit 与 continue-adverse，而不是仍然主要由不可见因素决定。
3. **Topology value 假设**：图消息传递提供了 simple counters、MLP 或 no-message pooling 无法替代的信息。

只有三层都通过，才能称为 Temporal-GAT 成功。若第一层失败，不应训练；若第二或第三层失败，也不能用 simple controller 冒充 GAT。

---

## 3. 当前 exact 算法栈

### 3.1 Production 与实验候选必须分开

当前 production default 是：

```text
no_cut + P0V4/P0V5 Exact + literal Q0
```

Round 5 绑定的 exact candidate config 是：

```text
runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml
```

该配置自身明确记录 `production_default: false`。它是 Temporal-GAT 实验的 exact core，不代表当前 production 已切到 P0V4+V5 Temporal-GAT。

### 3.2 P0V4+V5 pricing 主流程

从算法职责看，当前实验中的定价流程是：

1. RMP 在当前 root-CG round 求解并产生 true dual、cut context、branch context。
2. P0V5 bidirectional candidate/prepass 尝试构造 negative witness。
3. P0V5 只具有 negative-column/partial-witness 作用，`certificate_authority: none`。
4. 若 P0V5 没有完成所需定价语义，进入 P0V4 exact fallback。
5. P0V4 fallback 保留原 dominance、reduced cost、cut state、branch feasibility、stopping condition 和 certificate path。
6. Temporal-GAT 仅在授权的 P0V4 fallback request 内改变 proof queue comparator。
7. 若 exhaustive search 未完成，返回 `BPC_INCOMPLETE_PRICING`、`MEMORY_LIMIT` 等 fail-closed 状态，不能把 candidate harvest 当作 no-negative proof。

### 3.3 本轮允许变化的唯一动作

本轮 action scope 冻结为：

```text
scale ∈ {30, 50}
lifecycle == root_cg
P0V5 已进入 P0V4 exact fallback
objective/exact binding 合法
```

允许：

- 将完整 current frontier 从 Q0 comparator 迁到 QD1 comparator；
- 运行冻结的 K 次 QD1 trial；
- 继续 QD1；
- 将完整 current frontier 迁回 Q0 comparator。

禁止：

- 删除、剪枝或过滤任何合法 label/route；
- 修改 dominance relation 或 dominance threshold；
- 修改 reduced-cost 计算、negative threshold 或 route reconstruction；
- 修改 cut、branch、dual、completion bound；
- 修改 exhaustive stopping 或 certificate authority；
- 让 GAT 产生 bound、closure 或 certificate；
- 把 scale5/10/20、scale100、tree pricing 或其他 lifecycle 接入 trial。

### 3.4 Q0、QD1 和 REVERT 的语义

- **Q0**：冻结的 literal P0 proof-queue comparator，是对照臂和 fail-closed comparator。
- **QD1**：deeper-first queue ordering，只改变合法 frontier label 的处理顺序。
- **REVERT_Q0**：trial 后将当时仍存活的完整 frontier 重新装入 Q0 queue，并从该状态继续。

最重要的声明边界是：

> REVERT_Q0 恢复的是“当前 frontier 的 Q0 comparator”，不恢复“从未执行过 QD1 trial”的反事实轨迹。

QD1 trial 已经改变过 label 到达与 dominance 的时间顺序，这段历史不能撤销。因此三臂实验必须真实测量 `trial + revert` 的净 wall，不能把 revert 当作无成本 Q0。

---

## 4. 当前 Temporal trial 算法

### 4.1 单个授权 pricing request

伪代码如下：

```python
def temporal_exact_pricing(request):
    assert request.scale in {30, 50}
    assert request.lifecycle == "root_cg"
    assert request.is_p0v4_exact_fallback

    boundary = 4096 if request.scale == 30 else 16384
    K = frozen_k_by_scale[request.scale]

    run_literal_q0_until(boundary)

    if frontier_is_empty_or_request_already_ended():
        # 自然结束，不需要也不允许调用模型
        return existing_exact_result()

    t0 = build_temporal_multires_graph(current_frontier, counters, context)
    migrate_complete_frontier_q0_to_qd1()
    run_qd1_for_at_most(K_pops)

    if request_ended_during_trial():
        # 不调用模型，沿用原 exact result/certificate checks
        return existing_exact_result()

    tK = build_temporal_multires_graph(current_frontier, counters, context)

    if bundle_or_schema_or_hash_invalid():
        return migrate_current_frontier_back_to_q0_fail_closed()
    if any_nonfinite_or_ood_or_excessive_disagreement():
        return migrate_current_frontier_back_to_q0_fail_closed()

    action = portable_temporal_gat(t0, tK, delta_counters, context)
    if action == "CONTINUE_QD1":
        continue_current_request_with_qd1()
    else:
        migrate_complete_frontier_back_to_q0_atomically()
        continue_current_request_with_q0()
```

### 4.2 四种 Native trial mode

`FrontierProbeMode` 已增加：

| Mode | 用途 | K 结束后的动作 |
|---|---|---|
| `CollectTrial` | 采集 temporal graph/telemetry | 默认 revert |
| `ForceTrialContinue` | 三臂 CONTINUE arm | 固定 continue QD1 |
| `ForceTrialRevert` | 三臂 REVERT arm | 固定 migrate back Q0 |
| `LearnedAfterTrial` | 模型/控制器 E2E | 调用 portable bundle 决策 |

对应接口位于：

- `native/lunar_spprc/include/lunar_spprc/native_pricer.hpp`
- `native/lunar_spprc/src/native_pricer.cpp`
- `native/lunar_spprc/src/pybind_module.cpp`
- `src/lunar_ice_bpc/guidance/temporal_frontier_gat_runtime_v1.py`

### 4.3 双向 frontier migration

Q0→QD1 时检查：

- source frontier size；
- drained count；
- migrated count；
- creation ID hash before/after；
- duplicate creation ID count；
- target queue size。

QD1→Q0 使用更严格的两阶段迁移：

1. 从 live QD1 queue 的副本构造完整 staging Q0 queue；
2. 在 staging 中检查 size、hash、duplicate、label→creation-ID binding；
3. 所有检查通过后才 `swap` 到 live Q0 queue；
4. 再清空 QD1 container，并更新 comparator 状态。

因此 reverse migration 在验证失败时不会留下半空 live queue。creation ID 跨双向迁移保留，新 label 继续使用单调 creation sequence。

### 4.4 Exact-safe fail-closed

存在两个 fail-closed 层次：

1. **Trial 前 runtime binding 失败**：registry、manifest、bundle file、schema、scale/lifecycle 等不合法时，Python runtime 不安装 learned trial，请求保持 literal Q0。
2. **Trial 后推理失败**：graph 非有限、OOD、bundle invalid、ensemble disagreement 超阈值或 inference exception 时，Native 返回 false action，并把 current frontier 原子迁回 Q0。

资源语义保持原样：

- timeout、memory pressure、label drop、frontier 非空均不能形成 certificate；
- request 在 K 内自然结束时不调用模型；
- candidate negative routes 仍需原 route-RC reconstruction/audit；
- `State` ABI 仍为 `176 bytes`。

---

## 5. 当前 GAT 模型：是已实现规格，不是已训练 candidate

### 5.1 状态声明

当前代码已经实现训练侧模型和 Native portable forward，但 Round 5 尚未产生 train outcome，因此：

- 没有 Round 5 checkpoint；
- 没有 Round 5 calibration；
- 没有 `temporal_frontier_gat_bundle.v2.json`；
- 没有冻结的 scale30/50 K；
- 没有可用于 production 的 threshold；
- 当前不能报告模型 accuracy、BA、utility、coverage 或 speedup。

以下内容描述的是**冻结架构合同**。

### 5.2 输入一：完整 64-cell depth×RC graph

每个时点都构造一个完整的 8×8 depth/partial-RC cell graph，共 64 个 cell nodes：

- node width：16；
- edge width：10；
- cell self-edge；
- 相邻 depth cell edge；
- 相邻 RC cell edge；
- parent→child / child→parent 聚合关系；
- 每个 cell 保留 count、partial-RC 分布、depth、age、terminal 比例、last-task diversity 等统计。

这一层保留完整 frontier mass，不因 256-label sample 丢失大尺度分布。

### 5.3 输入二：最多 256 个 label 的 label-task graph

每个时点还构造确定性分层采样图：

- 最多 256 个 label nodes；
- 与采样 label 相关的 task nodes；
- label node width：40；
- edge width：11；
- parent/child edge；
- label↔last-task edge；
- task interaction edge；
- 同一 depth×RC cell membership edge；
- label creation ID、parent creation ID、last task、visited/task state 等结构信息。

采样是确定性的，并通过 graph hash、creation ID 和 telemetry hash 审计可复现性。

### 5.4 输入三：跨时点 temporal response

t0 是进入 QD1 trial 前，tK 是完成 K 次 QD1 pops 后。跨时点关系包括：

- 64 个同 cell temporal edges；
- surviving creation ID 的 label identity edges；
- surviving/new label count；
- frontier survival fraction；
- frontier churn；
- extended/dominated label delta；
- processed、dominance checks、subset dominance 等 delta/ratio；
- negative-label event 和 best true RC 变化。

这里的重点不是用两个图各自分类，而是让模型看到真实 response：

```text
h0, hK, hK-h0, |hK-h0|
```

### 5.5 Context features

冻结 context width 为 28，覆盖：

- true task dual 数量、均值、绝对均值、最小/最大；
- fleet dual；
- cut dual count/absolute sum；
- active cut/branch context；
- harvest target、admission batch、raw negative pool；
- active column count；
- root-CG round；
- true-dual L1 delta；
- memory/wall cap；
- exact negative escape context；
- P0V5 midpoint/prepass wall。

这些特征只描述授权 request context，不改变任何 exact value。

### 5.6 Encoder 与 pooling

模型参数冻结为：

| 项目 | 配置 |
|---|---:|
| hidden width | 32 |
| GAT layers | 2 |
| attention heads | 4 |
| per-head width | 8 |
| residual | yes |
| LayerNorm | yes |
| dropout | 0.1 |
| ensemble seeds | `61635, 91267, 170141` |

cell graph 和 label-task graph 使用各自的 raw node/edge adapter，将不同 width 投影到 32 维；之后两个 resolution、两个时点和两个尺度共享同一组两层 edge-aware GAT message encoder。

每层使用：

- query/key/value attention；
- edge embedding 对 attention logits 的修正；
- four-head target-wise softmax aggregation；
- output projection；
- residual + LayerNorm + ReLU。

Pooling 为 type-wise `mean + max + attention`：

- cell graph：一种 node type，得到 `3×32=96` 维；
- label-task graph：label/task 两类分别 pool，得到 `2×3×32=192` 维。

### 5.7 Temporal fusion 与 scale-specific heads

每个 resolution 组合：

```text
h0 || hK || (hK-h0) || |hK-h0|
```

再拼接 24 个 counter features、28 个 context features 和 2 维 scale one-hot。当前 fusion width 为 1206，经过：

```text
1206 -> 128 -> 64
```

共享 trunk 后，scale30 和 scale50 分别使用独立的 64→3 sigmoid head，输出：

- `p_benefit`；
- `positive_gain`；
- `p_adverse`。

共享 encoder 的目的是让两个尺度共享“frontier 动态如何变化”的表示，独立 head/calibration/threshold 则避免 scale30 的多数 continue 信号淹没 scale50 的 selective/harmful 分布。

### 5.8 三 seed ensemble 与保守聚合

Native 对三 seed 都执行 portable forward：

- `p_benefit`：三 seed 均值；
- `positive_gain`：三 seed最小值；
- `p_adverse`：三 seed最大值；
- `disagreement`：三个输出维度中最大的 seed range。

这是偏保守的聚合：收益取均值/下界，风险取上界。

### 5.9 Calibration、OOD 与动作阈值

训练 partition 仅用于拟合模型和 5-fold grouped CV；12 个 calibration instances/scale 专门用于：

- benefit/adverse Platt calibration；
- positive gain scale；
- 从预冻结 threshold grid 中选动作阈值。

阈值 grid 为：

| 阈值 | 候选值 |
|---|---|
| minimum benefit probability | `0.5, 0.6, 0.7, 0.8, 0.9` |
| maximum adverse probability | `0.05, 0.1, 0.2` |
| minimum expected gain | `0, 0.02, 0.05` |
| maximum disagreement | `0.02, 0.05, 0.1` |

continue 条件同时要求：

```text
calibrated p_benefit >= benefit threshold
calibrated p_adverse <= adverse threshold
expected_gain >= gain threshold
expected_gain - p_adverse > 0
disagreement <= disagreement threshold
not OOD
```

OOD envelope 仅由 fold-train/final-train rows 拟合，逐特征使用 `mean ± 8σ`，零方差 epsilon 为 `1e-12`。OOD 不是 request-hash allowlist，而是数值分布 veto。

### 5.10 一个需要重点审阅的 calibration 难点

阈值 gate 要求：

- 至少 4 个 activated instances；
- activated rows 中观察到的 adverse 为 0；
- 95% 单侧 harm 上界 `<=0.10`。

代码对零 harm 使用精确上界：

```text
harm_upper = 1 - 0.05^(1 / activated_rows)
```

这意味着仅有 4 个 activated instances 并不够；在零 observed harm 下，通常至少要有 **29 个 activated rows** 才能使该上界不超过 0.10。每尺度 calibration 最多 12×3=36 个 contexts，因此这是一个非常严格、且可能成为终止原因的 coverage gate。

该严格性是当前冻结合同的一部分。本轮见到 outcome 后不能放宽；若未来认为过严，只能在新的 experiment round、生成新 calibration/development/sealed partitions 之前重新冻结。

---

## 6. 监督标签、loss 与 controls

### 6.1 标签直接比较 CONTINUE 与 REVERT

对同一个 context、同一个 K、同一个 blocked repeat block：

```text
ratio = median_wall(CONTINUE_QD1) / median_wall(MIGRATE_BACK_TO_Q0)
```

标签为：

- `benefit = 1`：`ratio <= 0.98`；
- `adverse = 1`：`ratio >= 1.05`，或 continue 发生 timeout/memory censor；
- `positive_gain = max(0, 1-ratio)`；
- 两臂均 incomplete：不进入 supervised loss，但保留 resource audit。

标签不直接比较“boundary 前的静态图”与 Q0，而是比较在**相同 trial 历史后** continue 和 revert 的动作差异。这使模型学习的问题与 production 决策一致。

### 6.2 Instance-balanced loss

每个 instance 的 row weight 为该 instance supervised row 数量的倒数，避免具有 3 个 contexts 的实例压过只有 1 个 context 的实例。

GAT loss 包含：

- benefit binary cross entropy；
- adverse binary cross entropy；
- positive gain Smooth-L1；
- instance-balance weight。

### 6.3 必须保留的 controls

训练和验证同时保留：

- Linear；
- MLP；
- no-message GAT；
- shuffled-topology GAT；
- deterministic always-continue；
- deterministic always-revert。

scale50 representation gate 要求：

- GAT benefit BA 严格优于最佳 simple/no-message control；
- GAT policy utility 严格优于最佳 simple/no-message control；
- shuffled topology 的 benefit BA 至少退化 `0.01`。

如果失败，本轮必须 `TERMINATED_NEGATIVE`，不能把 MLP/Linear/no-message controller 包装成 GAT candidate。

---

## 7. Round 5 冻结实验设计

### 7.1 不可变绑定

Round 5 关键文件：

| 类型 | 路径/值 |
|---|---|
| config | `configs/experiments/p0v5_temporal_gat_production_v1_round5.json` |
| run root | `runs/p0v5_temporal_gat_production_v1_round5_20260824` |
| corpus manifest | `data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json` |
| corpus manifest SHA256 | `24ed33a714c6f459594f8f753a6be7136cfc16c4e120d5d6f65c22a60848b6b1` |
| exact config | `runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml` |
| formal contract | `configs/experiments/p0v4_final_acceptance_v1.yaml` |
| temporal Native build | `build/native-spprc-temporal-frontier-v10` |
| reference Native build | `build/native-spprc-counterfactual-prefix-v8r1` |
| exact engine hash | `5d752a393e54ae2d` |
| source git commit | `5453fbcdab4cd5febfea745fdb0a23b91af92c61` |

`source.freeze.json` 绑定了 222 个 source paths、Native binary、Native test binary、reference binary、selected exact config、formal contract、corpus manifest 和 protected-history cache。

### 7.2 Fresh real-map corpus

每尺度 80 个实例，共 160 个：

| Partition | 每尺度 | 两尺度合计 | 用途 |
|---|---:|---:|---|
| train | 40 | 80 | K selection、grouped CV、final model fit |
| calibration | 12 | 24 | calibration、threshold selection |
| development E2E | 12 | 24 | 首次完整模型策略验证 |
| sealed final | 16 | 32 | development PASS 后揭盲 |

Corpus freeze 记录：

- `official_or_historical_overlap_count = 0`；
- generator/driver/map-source hash；
- seed 和 retry contract；
- 每个实例的 content/file hash；
- split 在任何 queue outcome 前冻结。

旧 round 和历史/official outcome 不允许进入 Round 5 training，也不允许成为 Round 5 promotion evidence。

### 7.3 Outcome-blind context selection

每个 train/calibration instance 最多选 3 个 context：

1. 仅 root-CG；
2. 仅 P0V4 fallback request；
3. 按时间顺序选择最早达到本尺度 boundary 的三个 request；
4. selection row 禁止包含 wall ratio、benefit、adverse、selected action 或 queue outcome。

先完成 literal-Q0 boundary eligibility，再一次性写出：

```text
contexts.freeze.json
```

只有 context freeze 后才允许生成三臂 schedule。

### 7.4 K 候选与三臂任务量

K 候选：

```text
128, 512, 2048
```

Train 对每个 context 执行：

```text
3 K × 3 blocked repeats × 3 arms = 27 tasks/context
```

三臂为：

- literal Q0；
- QD1 trial 后继续 QD1；
- QD1 trial 后迁回 Q0。

当前 raw train snapshot 上限为 212 contexts，因此若全部 eligibility 通过，train schedule 最多约 `212×27=5724` 个 fresh-process tasks；实际 task count 必须等 `contexts.freeze.json` 生成后才能确定。

Calibration 只运行选定 K：

```text
3 repeats × 3 arms = 9 tasks/context
```

### 7.5 K selection gate

每尺度选择 taxed oracle GM 最小且完整通过 gate 的 K：

| Gate | 要求 |
|---|---:|
| determined instances | `>=32` |
| correctness redline | `0` |
| resource censor | `0` |
| oracle GM vs Q0 | `<=0.95` |
| trial-revert GM vs Q0 | `<=1.02` |
| trial-revert worst vs Q0 | `<=1.10` |
| scale30 continue instances | `>=24` |
| scale30 revert/adverse support | `>=4` |
| scale50 continue instances | `>=8` |
| scale50 revert instances | `>=8` |
| scale50 strong-benefit instances | `>=5` |

无 K 通过时，本轮直接 terminal negative，不训练 GAT。

---

## 8. 完整阶段计划与 gate

### 阶段 0：设计、代码与 freeze contract

目标：实现 temporal trial，同时冻结 exact-safe scope、架构、K grid、threshold grid、资源上限和所有 promotion gates。

当前状态：**已完成。**

主要产物：Native/Python implementation、Round 5 config、research contract、source freeze、corpus freeze。

### 阶段 1：Fresh corpus generation

目标：生成 scale30/50 各 80 个无历史 hash 重叠的 real-map instances，并在 outcome 前冻结 split。

当前状态：**已完成。**

### 阶段 2：Root context collection

目标：只对 train/calibration 运行 current exact stack，收集候选 root-CG P0V4 fallback snapshots。

当前状态：**已完成。**

Round 5 raw snapshot：

| Scale | Partition | collection instances | 有 snapshot 的 instances | raw snapshots |
|---:|---|---:|---:|---:|
| 30 | train | 40 | 33 | 34 |
| 30 | calibration | 12 | 10 | 10 |
| 50 | train | 40 | 39 | 178 |
| 50 | calibration | 12 | 12 | 52 |
| **合计** |  | **104** | **94** | **274** |

104 个 collection marker 均已形成。marker return code 为 1 是因为这些 collection 任务允许以 incomplete/fail-closed 结束并保留 snapshot，不等同于 exact closure，也不等同于 collection artifact 缺失。

### 阶段 3：Boundary eligibility replay

目标：对 274 个 raw snapshots 使用 literal Q0 重放，确认能到达 scale-specific boundary，并构造确定性 graph；此阶段不运行 QD1 trial、不调用模型、不产生 queue outcome。

当前状态：**进行中。**

2026-08-25 15:36:23 CST 快照：

| 项目 | 当前值 |
|---|---:|
| 完成 eligibility files | `30/274` |
| boundary reached | `30/30` |
| graph built | `30/30` |
| model called | `0` |
| label drop | `0` |
| `FOUND_NEGATIVE_PARTIAL` | `24` |
| `COMPLETE` | `5` |
| `MEMORY_LIMIT` | `1` |

活动 parent process：

```text
PID 97836
collect_p0v5_temporal_gat_root_contexts_v1.py eligibility
```

快照时的 child 是一个 scale50 replay，已运行约 18 分 47 秒，RSS 约 6.61 GB，低于 10.867 GiB native cap。PID/RSS 是瞬时运行信息，后续会变化。

已出现的一个 `MEMORY_LIMIT` row：

```text
state hash: 9c06b3621eb056c2161a6b97e28cecf749b8561969361b758cef8baed88e4220
scale: 50
boundary reached: true
graph built: true
processed labels: 20,887,000
wall: 669.233781356 s
labels_dropped: false
```

该 row 可以保留 eligibility/representation audit，但 memory limit 仍是 resource censor，不能形成 certificate，也预示后续三臂可能面临资源风险。

### 阶段 4：Context freeze 与 train schedule preflight

进入条件：274 个 eligibility replay 全部结束，且没有 partial writer/绑定漂移。

步骤：

1. outcome-blind 选择每 instance 最早最多 3 个 eligible contexts；
2. 写出 immutable `contexts.freeze.json`；
3. 检查 train distinct eligible instances 每尺度是否 `>=32`；
4. 确认 arm outcome artifact count 仍为 0；
5. 写出 `train_trial_schedule.freeze.json`。

当前状态：**未开始。**

如果任何尺度 capacity `<32`，脚本会写 `train_trial_preflight.audit.json` 和 `terminal_decision.json`，三臂不得启动。

### 阶段 5：Train 三臂和 K selection

进入条件：train schedule 已在零 outcome 状态冻结并通过 capacity preflight。

步骤：

1. 单 host、单 instance、fresh process 串行执行 schedule；
2. 每个 matched block 内按 SHA256 rotation 改变三臂顺序；
3. 三重复 collapse 使用 complete repeats 的 median wall；
4. 汇总 correctness/resource audit；
5. 对每个 K 计算 per-instance continue/revert/oracle ratio；
6. 每尺度冻结唯一 K。

当前状态：**未开始。**

这才是 Q0 / CONTINUE_QD1 / REVERT_Q0 三臂可以正式开始的阶段。

### 阶段 6：Calibration 三臂、dataset、训练与 calibration

进入条件：两个尺度均存在通过全部 gate 的冻结 K。

步骤：

1. 用 selected K 冻结 calibration schedule；
2. 执行 calibration 三臂三重复；
3. 构建只包含 train/calibration 的 immutable dataset；
4. 5-fold instance-grouped CV；
5. 训练 GAT 和全部 controls；
6. 执行 scale50 representation/topology gate；
7. 用 calibration-only rows 做 Platt/gain calibration；
8. 选择满足无 adverse activation 与 harm upper gate 的阈值；
9. 导出 `temporal_frontier_gat_bundle.v2.json`。

当前状态：**未开始。**

### 阶段 7：Native differential 与 portable parity

要求：

- Round 5 绑定的 500-case exact differential mismatch = 0；
- migration empty/single/large/duplicate/fault injection tests PASS；
- size/hash/creation-ID conservation PASS；
- telemetry canonical hash repeat 完全一致；
- calibration 全图 + 500 synthetic graphs 的 Python/C++ action mismatch = 0；
- max absolute numeric error `<=1e-9`；
- Native inference p99 `<=10 ms`；
- graph overhead GM `<=1.01`，worst `<=1.05`。

当前状态：**Round 5 promotion artifact 未完成。**

历史 implementation-level 验证曾报告 500-case disabled-Q0 differential 0 mismatch、单组 portable error 约 `5.55e-17` 和 20 synthetic scale50 graphs inference 小于约 3.3 ms；这些说明代码路径可工作，但不能代替 Round 5 frozen source/binary/bundle 绑定的持久化 audit。

### 阶段 8：Development E2E

进入条件：training、calibration、representation、portable、source/bundle gate 全部通过。

四个 E2E arms：

- Q0；
- MODEL；
- ALWAYS_CONTINUE；
- BEST_CONTROL。

任务量：

```text
12 instances/scale × 2 scales × 3 repeats × 4 arms = 288 tasks
```

关键 gate：

- exact status/objective/certificate semantics 一致；
- route RC reconstruction 全部通过；
- correctness redline、label drop、resource censor = 0；
- scale30、scale50 相对 P0V4+V5 Q0 的 GM 都 `<=0.95`；
- 不出现 collapsed ratio `>=1.05` 的 harmful instance；
- scale30 相对 always-continue 退化 `<=1%`；
- scale50 相对最佳 deterministic/simple policy 再改善 `>=2%`；
- peak RSS ratio `<=1.05`，且不突破 dynamic cap。

当前状态：**未开始。**

### 阶段 9：Sealed final

进入条件：development 全部 PASS；model、K、threshold、engine、bundle 不得变化。

任务量：

```text
16 instances/scale × 2 scales × 3 repeats × 4 arms = 384 tasks
```

重复全部 development gates。任何失败都使本轮 terminal negative。

当前状态：**未开始、未揭盲。**

### 阶段 10：Formal acceptance

使用：

```text
configs/experiments/p0v4_final_acceptance_v1.yaml
```

要求：

- scale5/10/20/30 各 20 个 exact；
- small-scale ratio 各 `<=1.03`；
- scale20+30 combined speedup `>=5%`；
- scale5–30 combined speedup `>=5%`；
- scale50 exact `>=14/20`；
- scale50 heldout exact `>=13`；
- GAT 至少增加 1 个 scale50 closure；
- correctness redline = 0；
- scale100 只作 diagnostic。

当前状态：**未开始。**

### 阶段 11：Candidate、canary、activation 与 rollback

只有 sealed final、formal、portable、source/binary/bundle audit 全部 PASS，才允许：

1. 生成 immutable production candidate manifest；
2. 在独立 registry 中新增 `AWAITING_CANARY` candidate；
3. 用固定 canary 验证 bundle load、fail-closed fallback、monitoring；
4. canary PASS 后 activate `P0V4+V5_TEMPORAL_GAT_V1`；
5. 保留 `no_cut` rollback。

当前状态：**未开始，production switch unauthorized。**

---

## 9. 已完成内容的证据清单

### 9.1 已完成：Native 与 runtime 实现

- temporal trial 四 modes；
- `trial_pop_budget`、scale/lifecycle、manifest/bundle binding；
- t0/tK cell graph、label-task graph、temporal identity edges；
- Q0→QD1 conservation check；
- staging-based atomic QD1→Q0 migration；
- creation ID preservation；
- three-seed Native portable inference；
- calibration/threshold/OOD/disagreement action；
- Python runtime fail-closed literal-Q0 fallback；
- pybind telemetry exposure；
- `sizeof(State)==176` static assertion 和 build-info binding。

### 9.2 已完成：研究与数据冻结

- Round 5 experiment ID、seed range、K grid、threshold grid、model architecture、gates 已冻结；
- 160 个 fresh real-map instances 已生成并冻结；
- train/calibration/development/sealed split 已在 queue outcome 前冻结；
- historical/official content hash overlap 为 0；
- corpus/source/config/contract/native binary hashes 已绑定；
- source inventory 222 paths 已记录。

### 9.3 已完成：Root collection

- 104/104 train+calibration collection tasks 已形成 marker；
- 共获得 274 个 raw root-CG P0V4 fallback snapshots；
- development 和 sealed final 没有参与 context/outcome 生成；
- 当前仍不存在任何三臂 queue outcome。

### 9.4 正在完成：Eligibility

- 30 个 completed eligibility artifacts；
- 30/30 到达 boundary 并成功构图；
- 0 次模型调用；
- 0 label drop；
- 活动串行 replay 仍在运行。

---

## 10. 过去 Round 3/4 的负结果及 Round 5 的 restart 边界

> 本节记录原 Round 5 restart 事实；其“每次失败全面刷新”策略已被 2026-08-25 V2 protocol revision 修订。此后 terminal 只 invalidates 与 failure class 有依赖的层和已揭示 partition，未受影响的 Platform/Data evidence 与未揭示 heldout 可以通过机器 reuse audit 继续使用。

### Round 3

Round 3 在 train trial preflight 后发现 scale30 maximum determined instances 为 31，小于 gate 32：

```text
NO_PASSING_TEMPORAL_TRIAL_K_SCALE30_MAX_DETERMINED_INSTANCES_31_LT_32
```

该 round 已 `TERMINATED_NEGATIVE`，不是可继续的 partial run。

### Round 4

Round 4 更早进行 outcome-independent capacity audit，最大可能 scale30 train snapshot instances 仍为 31：

```text
NO_PASSING_TEMPORAL_TRIAL_K_SCALE30_MAX_SNAPSHOT_INSTANCE_CAPACITY_31_LT_32
```

Round 4 在产生三臂 outcome 前终止，`arm_outcome_count=0`。

### Round 5 为什么合法

Round 5 使用：

- 新 experiment ID；
- 新 seed range；
- 新 corpus；
- 新 calibration/development/sealed partitions；
- 不把 Round 3/4 revealed data 用作 training 或 promotion evidence；
- 继承的是冻结的研究合同与失败原因，不是旧 outcome。

因此 Round 5 是独立 restart，而不是删除 terminal artifact 后续跑旧 round。

---

## 11. 当前没有完成、也不能声称完成的内容

截至本文快照，以下 artifact 均不存在或尚未合法生成：

- Round 5 `contexts.freeze.json`；
- Round 5 `train_trial_schedule.freeze.json`；
- Round 5 train three-arm outcomes；
- per-scale selected K；
- calibration three-arm outcomes；
- Round 5 Temporal-GAT dataset；
- Round 5 GAT/control checkpoints；
- Round 5 calibration 和 thresholds；
- Round 5 `temporal_frontier_gat_bundle.v2.json`；
- representation/topology PASS；
- Round 5 portable parity PASS；
- Round 5 persistent 500-case differential PASS；
- development E2E speedup；
- sealed final evidence；
- formal acceptance；
- immutable production candidate；
- canary；
- production activation。

因此当前不能说：

- “GAT 已训练”；
- “GAT 有效”；
- “已经提高 5%”；
- “scale50 已安全选择”；
- “candidate 已可部署”；
- “production 已改为 P0V4+V5 Temporal-GAT”。

---

## 12. 当前风险与我的评价

### 12.1 Scale30 capacity 风险：高

scale30 train raw snapshot instances 为 33，gate 为 32。只要两个 distinct instances 的 snapshots 在 eligibility/context freeze 后不可用，本轮就会再次因 capacity 终止。

这不是模型问题，也不能通过降低 threshold 补救。应让当前 eligibility 完整结束，然后只按冻结规则判断。

### 12.2 Scale50 resource 风险：高

前 30 个 eligibility 中已经有一个 scale50 request 在到达 boundary、构图后触发 `MEMORY_LIMIT`，processed labels 超过 2088 万。后续三臂要求 resource censor 为 0，因此即使 context 可用于 representation audit，也可能使对应 K 无法晋升。

### 12.3 K 的 action-support gate：高

scale50 历史上只有很少 strong-benefit instances，而本轮要求至少 5 个 strong-benefit、8 个 continue、8 个 revert。这个 gate 正是在验证“可学的选择问题是否真实存在”。若不通过，停止训练是正确结论。

### 12.4 Revert tax 风险：中高

反向 migration 工程上 exact-safe，不代表 wall 成本一定低。K 越大，trial 导致的不可逆 ordering history 越多；K 越小，动态信号可能不足。`revert GM<=1.02` 和 worst `<=1.10` 会直接约束这一权衡。

### 12.5 Calibration coverage 风险：高

零 adverse activation + 95% harm upper `<=0.10` 隐含需要约 29 个 activated rows，而每尺度最多约 36 calibration contexts。阈值既要保守又要高覆盖，可能没有合法点。

### 12.6 GAT representation gate 风险：高

旧模型没有超过 simple controls。本轮只有 temporal response 真正包含 topology-specific 信息，GAT 才能通过 shuffled/no-message gate。这个 gate 是本路线区别于普通 MLP controller 的关键。

### 12.7 Promotion 工期风险：高

即使 eligibility 通过，train three-arm 最多仍可能有数千个 fresh-process tasks，之后还有 calibration、288 development tasks、384 sealed tasks 和 formal acceptance。单 host 串行与资源 cap 是 correctness/reproducibility contract，不能为了工期随意并发。

### 12.8 总体评价

| 维度 | 当前评价 | 原因 |
|---|---|---|
| 问题定义 | 强 | 直接针对旧静态 GAT 的 observability 根因 |
| Exact safety | 强 | queue-only、双向 conservation、atomic revert、无 certificate authority |
| 数据防泄漏 | 强 | fresh corpus、pre-outcome split/context/schedule freeze |
| 工程完成度 | 中高 | 核心代码与 orchestration 已实现，实验链尚未跑完 |
| Action support | 未知/高风险 | Round 5 三臂未开始，scale50 历史正例稀疏 |
| GAT 必要性 | 未知/高风险 | 必须超过 simple/no-message/shuffled controls |
| 当前效果 | 无法评价 | 尚无 Round 5 outcome/model/E2E |
| Production readiness | 低 | development、sealed、formal、canary 均未开始 |

我的总体判断是：**这已经是目前最值得验证的 GAT queue-acceleration 方案，但它仍是一项高淘汰率的受控实验，不应预设最终一定能晋升。**

---

## 13. 什么时候可以开始三臂，以及紧接着做什么

三臂开始需要同时满足：

1. 当前 274 个 eligibility replay 全部结束；
2. 没有 writer partial/immutable binding drift；
3. `freeze` 按 outcome-blind 规则生成 `contexts.freeze.json`；
4. train distinct eligible instances 在 scale30 和 scale50 都 `>=32`；
5. arm outcome artifact count 仍为 0；
6. `train_trial_schedule.freeze.json` 成功写入且 hash 固定；
7. host 满足 `MemAvailable reserve >=2 GiB`，只运行一个 task。

当前 eligibility 结束后，下一组命令是：

```bash
python scripts/collect_p0v5_temporal_gat_root_contexts_v1.py freeze \
  --config configs/experiments/p0v5_temporal_gat_production_v1_round5.json \
  --corpus data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json \
  --run-root runs/p0v5_temporal_gat_production_v1_round5_20260824

python scripts/freeze_p0v5_temporal_gat_trial_schedule_v1.py \
  --config configs/experiments/p0v5_temporal_gat_production_v1_round5.json \
  --contexts runs/p0v5_temporal_gat_production_v1_round5_20260824/contexts.freeze.json \
  --partition train \
  --output runs/p0v5_temporal_gat_production_v1_round5_20260824/train_trial_schedule.freeze.json
```

只有第二条命令成功且没有 terminal decision，才能启动：

```bash
python scripts/run_p0v5_temporal_gat_trial_schedule_v1.py \
  --schedule runs/p0v5_temporal_gat_production_v1_round5_20260824/train_trial_schedule.freeze.json \
  --contexts runs/p0v5_temporal_gat_production_v1_round5_20260824/contexts.freeze.json \
  --native-build build/native-spprc-temporal-frontier-v10 \
  --output-dir runs/p0v5_temporal_gat_production_v1_round5_20260824/train_trial_tasks \
  --run-root runs/p0v5_temporal_gat_production_v1_round5_20260824 \
  --memavailable-reserve-gb 2.0
```

实际 CLI 在执行前仍应以脚本 `--help` 和 frozen schedule 字段为准；不要在当前 eligibility 进程仍运行时并发启动三臂。

---

## 14. 审阅时建议重点检查的问题

### 算法边界

- 是否同意 GAT 只控制 current-frontier comparator，而无 certificate authority？
- 是否接受 REVERT 不等于 counterfactual never-trial Q0 的声明？
- 是否同意 scale5/10/20/100、tree 和其他 lifecycle 继续 literal Q0？

### 数据合同

- 是否认可 train/calibration/development/sealed 的 40/12/12/16 split？
- 是否认可每实例最多 3 个、最早 boundary-reaching contexts 的 outcome-blind 规则？
- 是否同意旧 round outcome 完全不能进入 Round 5 training/promotion？

### K gate

- `>=32 determined instances` 是否维持？
- scale30 的 24 continue + 4 revert support 是否足够验证双动作？
- scale50 的 8/8/5 support 是否足够严格？
- revert GM/worst gate 是否正确表达最大可接受 trial tax？

### 模型与 GAT 必要性

- shared encoder + scale-specific heads 是否合理？
- cell graph 与 label-task graph 的 shared message layers 是否是预期设计？
- 3-seed conservative aggregation是否合适？
- topology degradation `>=0.01` 是否足以证明 message passing 有用？

### Calibration

- 是否有意保留零 adverse activation？
- 是否有意保留 exact 95% harm upper `<=0.10`，并接受其约 29 activated rows 的隐含 coverage 要求？
- 若本轮因此终止，是否坚持只在新 round 修改，而不在 revealed calibration 上调 threshold？

### Promotion

- development 和 sealed 是否都要求 per-scale GM `<=0.95`？
- scale50 是否必须相对最佳 control 再改善 2%？
- production 是否必须等 formal acceptance 和 canary 都 PASS？
- `no_cut` 是否继续作为独立 registry 的一键 rollback？

---

## 15. 权威证据路径

### 当前设计与历史结论

- `plan/GAT/CODEX_HANDOFF_P0V5_GAT_QUEUE_ACCELERATION_CURRENT_STATE_20260819_ZH.md`
- `plan/GAT/P0V4_V5_TEMPORAL_GAT_V1_IMPLEMENTATION_20260819_ZH.md`
- `plan/GAT/P0V5_TEMPORAL_FRONTIER_LATE_SWITCH_V10R1_CLOSEOUT_20260818_ZH.md`
- `plan/GAT/CODEX_HANDOFF_P0V5_QG2_TINYGAT_CLOSEOUT_20260807_ZH.md`

### Round 5 freeze

- `configs/experiments/p0v5_temporal_gat_production_v1_round5.json`
- `data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json`
- `runs/p0v5_temporal_gat_production_v1_round5_20260824/bootstrap.freeze.registry.json`
- `runs/p0v5_temporal_gat_production_v1_round5_20260824/config.freeze.json`
- `runs/p0v5_temporal_gat_production_v1_round5_20260824/research_contract.freeze.json`
- `runs/p0v5_temporal_gat_production_v1_round5_20260824/source.freeze.json`
- `runs/p0v5_temporal_gat_production_v1_round5_20260824/state.json`

### Native/model/runtime source

- `native/lunar_spprc/include/lunar_spprc/native_pricer.hpp`
- `native/lunar_spprc/src/native_pricer.cpp`
- `native/lunar_spprc/src/pybind_module.cpp`
- `src/lunar_ice_bpc/guidance/temporal_frontier_gat_v1.py`
- `src/lunar_ice_bpc/guidance/temporal_frontier_gat_runtime_v1.py`
- `scripts/build_p0v5_temporal_gat_dataset_v1.py`
- `scripts/train_p0v5_temporal_gat_production_v1.py`

### 实验控制器

- `scripts/collect_p0v5_temporal_gat_root_contexts_v1.py`
- `scripts/freeze_p0v5_temporal_gat_trial_schedule_v1.py`
- `scripts/run_p0v5_temporal_gat_trial_schedule_v1.py`
- `scripts/select_p0v5_temporal_gat_trial_k_v1.py`
- `scripts/verify_p0v5_temporal_gat_portable_v1.py`
- `scripts/run_p0v5_temporal_gat_full_bpc_v1.py`
- `scripts/run_p0v5_temporal_gat_formal_acceptance_v1.py`
- `scripts/run_p0v5_temporal_gat_canary_v1.py`
- `scripts/finalize_p0v5_temporal_gat_production_v1.py`

### 负结果与 restart 证据

- `runs/p0v5_temporal_gat_production_v1_round3_20260821/terminal_decision.json`
- `runs/p0v5_temporal_gat_production_v1_round3_20260821/train_trial_early_terminal.audit.json`
- `runs/p0v5_temporal_gat_production_v1_round4_20260823/terminal_decision.json`
- `runs/p0v5_temporal_gat_production_v1_round4_20260823/context_collection_capacity_early_terminal.audit.json`

### Formal contract 与 production registry

- `configs/experiments/p0v4_final_acceptance_v1.yaml`
- `runs/production_policy_registry_v2.json`（只有合法 candidate/finalize 阶段才允许创建或更新）

---

## 16. 最终审阅结论

当前工作不是“训练一个更大的 GAT”，而是把学习问题重新定义成一个 exact request 内、经过真实短响应后才做的可撤销 queue decision。这个定义比旧静态 frontier selector 更接近实际 wall-time 因果机制，也避免了双 prefix 的重复成本。

工程上，关键 exact-safe 机制、数据冻结和实验控制器已经具备；Round 5 已完成 fresh corpus 和 root collection，正在进行 boundary eligibility。科学上，本轮还没有三臂 outcome，因而不能对 K、GAT、scale50 安全性或生产收益作正面结论。

下一道真实决策点不是“调模型”，而是：

```text
eligibility 完成
    -> scale30/50 eligible train capacity 是否都 >=32
    -> 若 PASS，冻结三臂 schedule
    -> force-on 三臂是否存在通过全部 gate 的 K
    -> 若 PASS，才允许训练 Temporal-GAT
```

在这之前，最正确的动作是让当前串行 eligibility 完整、可审计地结束，不中断、不并发污染、不提前生成 outcome，也不修改任何已冻结 gate。
