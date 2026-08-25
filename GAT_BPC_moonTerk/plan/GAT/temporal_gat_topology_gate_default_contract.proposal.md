# Temporal-GAT Topology Gate 默认合同提案

> 状态：`PROPOSAL_REQUIRES_USER_CONFIRMATION`
>
> 适用对象：D5 后续 scale50 post-trial Temporal-GAT Policy Round
>
> 本提案形成于任何 train arm、selected K、model/control、development 或 sealed outcome 之前；不是 freeze，不授权训练或 promotion。

## 1. Primary scientific claim

在相同 temporal response、instance split、action universe、训练预算和评估实例上，显式 topology/message passing 必须相对 simple/no-message/shuffled controls 产生 solver-relevant、可重复的增量价值。

以下结果均不构成 PASS：

- 只证明 GAT 能分类；
- 只超过一个弱 control；
- 只出现 row-level BA `+0.01`；
- 用更高 harmful/censor 或更低 coverage 换取平均 wall；
- 在 evaluation outcome 上选择 architecture、control、shuffle seed 或 threshold。

## 2. Frozen controls

至少包含：

1. Linear；
2. counters-only MLP；
3. no-message GAT；
4. shuffled-topology GAT；
5. always-continue；
6. always-revert；
7. literal Q0；
8. taxed oracle，仅作不可部署上界。

`best simple control` 必须只在 train-only/nested grouped procedure 中预选；不得用 Safety-B、development 或 sealed 选择最佳 control。

## 3. Primary hypotheses

预声明 family：

```text
H1: GAT vs preselected best Linear/MLP control
H2: GAT vs no-message GAT
H3: GAT vs frozen shuffled-topology distribution
```

每个 primary comparison 都必须同时满足：

```text
paired policy wall ratio point estimate <= 0.98
paired 95% CI upper bound < 1.00
additional harmful instances = 0
additional action-induced resource censor = 0
coverage 不得低于预冻结 noninferiority floor
```

ratio 小于 1 表示 GAT 更快。主要统计单位是 independent instance；同一 instance 的多个 contexts 和 repeats 只用于 instance 内 collapse，不得作为 bootstrap clusters。

## 4. CI 与 censor

- 对 complete paired instance log ratios 使用 instance-cluster paired bootstrap；
- 默认 bootstrap replicates：`10,000`；
- 默认 bootstrap seed：`2026082501`；
- 报告 two-sided 95% CI，并以 upper bound `<1.00` 判定不利边界；
- one-arm incomplete、both-incomplete、timeout 和 memory censor 的处理必须在 outcome 前冻结；
- action-induced censor 是 hard fail，不能从 utility sample 中静默删除；
- baseline-Q0 固有 censor 单独报告，不能归因于 GAT，也不能掩盖 scope 本身不可评价；
- 如果 complete independent pairs 不足，返回 `INSUFFICIENT_POWER`，不返回 PASS。

## 5. Topology shuffle

提议冻结 10 个独立 seeds：

```text
1061978086
377584259
1283788950
1482650917
817197819
611389827
1698615962
1067716362
1055590016
833730237
```

生成规则为：

```text
uint31(SHA256("temporal_gat_topology_shuffle_seed_v1:<index>")[0:4])
```

要求：

- seeds 在 outcome 前固定，与 model seeds `61635/91267/170141` 分开；
- shuffle 保留 node/edge feature marginal、node/edge count、task scale 和 training budget；
- 只破坏 proposal 明确指定的 topology relationship；
- 报告全部 seed 的 utility/BA/regret/harm/coverage 分布；
- H3 以每 instance 跨 frozen shuffle seeds 的预冻结 aggregate 进行 paired comparison；
- 另要求至少 `8/10` 个 shuffle seeds 的 policy-utility point estimate 不优于 unshuffled GAT；该项作为稳定性辅助 gate，不替代 H3 的 paired CI。

## 6. Multiplicity

- primary family 使用 Holm-Bonferroni family-wise error control；
- `alpha=0.05`；
- H1/H2/H3 的 hypothesis、direction、statistic 和 censor rule 必须在 outcome 前冻结；
- primary 失败后不得降级为 secondary；
- architecture candidates 超过 1 个时，将额外选择纳入同一 multiplicity/selection contract；
- exploratory metrics 明确标记 `EXPLORATORY_NOT_PROMOTION_EVIDENCE`。

## 7. Secondary representation effects

辅助指标包括 BA、AUROC、Brier、ECE、oracle regret 和 calibration error。

默认 proposal：

- GAT 相对 no-message 与 frozen shuffled aggregate 的 instance-clustered benefit BA 差值点估计至少 `+0.03`；
- 相应 95% CI lower bound `>0`；
- 若 power audit 表明 `0.03` 不可辨识，必须在任何 model outcome 前由用户重新确认 effect 或 sample capacity；
- secondary representation effect 不能弥补 primary policy utility failure。

## 8. Coverage 与 safety

coverage noninferiority floor 不能在本提案阶段凭空固定。应由 Calibration-A/Safety-B capacity audit 在 outcome 前提出，且至少保证：

- GAT 不通过大面积 abstain 人为消除 harmful；
- GAT 与 controls 比较使用相同授权 lifecycle population；
- OOD/disagreement/resource veto 分层报告；
- scale50 overall-policy harm 与 activated-subset harm 使用独立 harm contract；
- correctness、RC、certificate、migration、label-drop 和 action-induced censor redline 全为 0。

## 9. PASS 状态

只有同时满足以下条件才返回 `TOPOLOGY_GATE_PASS`：

1. H1/H2/H3 经 Holm-Bonferroni 后全部通过；
2. primary 2% effect 与 CI gate 通过；
3. hard safety/resource redline 为 0；
4. coverage noninferiority 通过；
5. shuffle stability 辅助 gate 通过；
6. secondary representation effect 通过；
7. independent sample/power audit 不为 insufficient。

否则只能返回：

```text
TOPOLOGY_GATE_FAIL
INSUFFICIENT_POWER
CORRECTNESS_OR_RESOURCE_REDLINE
CONTRACT_NOT_FROZEN
```

## 10. Freeze boundary

本提案需用户明确确认后才能转为 immutable contract。确认前禁止：

- 写入 Round 5 freeze；
- 启动 GAT/control training；
- 读取 future topology outcomes 后改 effect/CI/seeds/multiplicity；
- 将 proposal 状态误报为 scientific authorization。
