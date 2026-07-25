# P0 V2 GAT 稀疏机会、采集偏差与净收益门槛

日期：2026-07-24

## 结论

“很久采不到可用标签”不能单独证明 GAT 没有空间，因为它也可能来自动作
定义错误、action universe 不可达或采集被资源限制删失。但如果在结果无关的
无偏 context 流中，oracle-positive 机会仍然稀疏，并且完美可弃权策略都无法
覆盖构图、推理和启动成本，那么继续训练或常驻部署 GAT 没有意义。

本轮把这个判断变成训练前硬门槛：

```text
全部 sentinel contexts
→ cheap gate 可进入
→ 至少两个合法动作
→ formal counterfactual 可用
→ action value 可识别
→ oracle-positive
→ matched end-to-end 节时可识别
→ 扣除 cheap gate、模型调用和启动分摊后仍为正
```

target-mode 只负责富集训练正例，永远不进入 population opportunity rate。
pressure AUC 只能判断机制 headroom，不能冒充墙钟节时。

## 顶会、顶刊如何处理相同或相邻问题

### 1. 不在每个节点无条件运行昂贵模块

Khalil 等在 IJCAI 2017 的
[Learning to Run Heuristics in Tree Search](https://www.ijcai.org/proceedings/2017/92)
直接学习“当前节点是否值得运行 heuristic”，而不是默认每个节点都运行。
这与本项目的 pre-import eligibility gate 最接近。

Gupta 等在 NeurIPS 2020 的
[Hybrid Models for Learning to Branch](https://proceedings.neurips.cc/paper_files/paper/2020/hash/d1e946f4e67db4b362ad23818a6fb78a-Abstract.html)
发现 CPU 上每个 B&B 节点执行完整 GNN 不具竞争力，因此只在 root 做一次
GNN 结构编码，后续节点使用廉价 MLP。其关键经验不是“GNN 越强越好”，而是
必须优化 time-accuracy trade-off。

Alvarez 等在 INFORMS Journal on Computing 2017 的
[A Machine Learning-Based Approximation of Strong Branching](https://pubsonline.informs.org/doi/10.1287/ijoc.2016.0723)
以及 Khalil 等在 AAAI 2016 的
[Learning to Branch in Mixed Integer Programming](https://ojs.aaai.org/index.php/AAAI/article/view/10080)
都用廉价 surrogate 逼近昂贵 strong branching，思路接近 reliability
branching：昂贵信号用于监督，在线必须换成便宜决策。

### 2. 数据采集必须同时解决效率与干扰偏差

Chmiela 等在 NeurIPS 2021 的
[Learning to Schedule Heuristics in Branch and Bound](https://proceedings.neurips.cc/paper_files/paper/2021/file/cb7c403aa312160380010ee3dd4bfc53-Paper.pdf)
明确指出两个问题：

- 为每个 heuristic/instance 单独重跑 B&B 的采集成本不可接受；
- 多个 heuristic 在同一求解路径上相互改变 incumbent，会产生标签偏差。

他们在一次 B&B 中以 sandbox/shadow 方式收集多个 reward，同时限制
heuristic 的执行预算，并以 heuristic duration、success 与整体 primal
performance 共同评价。这支持当前 fixed-P0 counterfactual replay 的隔离方向，
也支持新增的 censored/context funnel，而不是把未采到标签当负样本。

### 3. 排名精度不能代替完整求解时间

Gasse 等在 NeurIPS 2019 的
[Exact Combinatorial Optimization with Graph Convolutional Neural Networks](https://proceedings.neurips.cc/paper/2019/hash/d14c2267d848abeb81fd590f371d39bd-Abstract.html)
以 strong branching expert 的 imitation loss 训练 GNN。这证明结构表示可以
跨规模泛化，但后续 NeurIPS 2020 的结果也说明，更高预测精度不保证 CPU
端到端更快。

Morabit、Desaulniers 和 Lodi 在 Transportation Science 2021 的
[Machine-Learning-Based Column Selection for Column Generation](https://pubsonline.informs.org/doi/10.1287/trsc.2021.1045)
以及 INFORMS Journal on Optimization 2023 的
[Machine-Learning-Based Arc Selection for Constrained Shortest Path Problems in Column Generation](https://pubsonline.informs.org/doi/10.1287/ijoo.2022.0082)
最终都以完整计算时间评价列/弧选择。它们允许启发式缩减子问题，而本项目为了
exact safety 不能照搬过滤，只能吸收“限制调用成本、比较完整求解时间”的部分。

## 已实施

### 1. 两条不可混用的数据流

新增 `sampling_stream`：

- `sentinel`：选择必须在 action/outcome 出现前完成，绑定冻结的 selection
  manifest；只有它能估计线上机会密度；
- `targeted`：允许按已知困难结构富集，只用于训练，不进入机会率或净收益估计。

`scripts/build_p0v2_gat_sentinel_manifest.py` 使用 content hash、scale 和冻结
seed 做伯努利选择。当前 development pool 的 manifest 为：

```text
candidate instances = 192
selected instances  = 105
scale5 / 10 / 20 / 30 = 22 / 27 / 24 / 32
```

scale30 的选择概率提高到 `0.75`，其余为 `0.5`，使每个规模至少可以达到
20 个 sentinel instances。calibration、full80 和现有 50/100 protected
instances 均未进入。

### 2. Opportunity funnel 与删失语义

新增：

- `FORMAL_COUNTERFACTUAL`；
- `STRUCTURAL_ZERO_NO_LEGAL_ACTION`；
- `CENSORED_RESOURCE_OR_DISCOVERY`；
- `NOT_PROBED_RANDOM`。

资源删失或未 probe 不再当负样本。审计同时报告：

- cheap-gate eligibility rate；
- legal multi-action rate；
- formal-label yield；
- identifiable-label rate；
- oracle-positive rate；
- model invocation rate；
- censored/unprobed rate；
- 两个正机会之间的 context/time gap。

抽样率通过 inverse-probability weighting 进入总体估计，bootstrap 单位仍是
instance，避免慢实例通过大量 contexts 支配结论。

### 3. 完美可弃权策略净收益门槛

对每个 sentinel context：

```text
reachable benefit =
    matched end-to-end time-saving LCB
    if cheap gate admits the context and oracle action beats P0
    else 0

guidance cost =
    cheap-gate wall
  + model-call upper bound when invoked
  + amortized fresh-runtime startup share

net gain = reachable benefit - guidance cost
```

oracle 可以选择最佳已观测动作或 `P0_KEEP_ORDER`。如果这个理想策略的
instance-bootstrap net-gain LCB 仍不大于零，真实模型不可能被允许训练或上线。
若样本充足且 net-gain UCB 也不大于零，审计返回
`STOP_ACTION_FAMILY_AS_FUTILE`。

formal 默认要求每个目标规模：

- 至少 100 个 outcome-observed sentinel contexts；
- 至少 20 个 outcome-observed sentinel instances；
- oracle-positive fraction 的 95% LCB 至少 `0.02`；
- censored/unprobed fraction 不超过 `0.10`；
- perfect-policy net-gain 95% LCB 严格大于零。

### 4. 训练和 promotion 已 fail closed

`train_p0v2_gat_model_ladder.py` 现在同时要求：

- 与训练 records SHA-256 绑定且通过的 oracle-headroom report；
- 与 opportunity observations SHA-256 绑定且通过的 opportunity-ROI report。

model-rung selection 和正式 deployment freeze 新增：

```text
unbiased_sentinel_opportunity_density_gate
perfect_policy_net_benefit_gate
cheap_preimport_eligibility_gate
```

缺少其中任一项都不能生成正式 online manifest。
selection report 还必须携带 `opportunity_roi_eligible_scales`；deployment
freezer 检查所有 online scales 都在该列表中，禁止用 scale20 的收益替
scale5/10/30/50/100 背书。

### 5. Torch 前廉价 gate

正式 harvest runtime 在导入 Torch、读取 checkpoint 和构图之前检查：

- 当前规模是否 online eligible；
- legal harvest candidate 数是否达到该规模冻结门槛；
-候选 true-RC negative mass 是否达到该规模冻结门槛。

未通过时直接返回 P0，并记录：

```text
guidance_cheap_gate_sec
cheap_gate_candidate_count
cheap_gate_negative_mass
bypassed_before_import = true
```

shadow 仍可收集预测，但正式 online manifest 必须显式给出每个在线规模的
candidate-count 和 negative-mass 门槛。

## 首轮新管线实测

### targeted smoke

development `scale5/039`：

- 形成 10 个合法 route actions；
- formal rollout 完整；
- pressure oracle gain 为 `0`；
- observation 正确标成 `targeted`；
- ROI audit 中 sentinel denominator 为零，因此 targeted 正例无法人为提高
  population opportunity rate。

### sentinel smoke

冻结 manifest 预先选中的 development `scale5/003`：

- 形成 12 个合法 route actions；
- formal rollout 完整；
- pressure oracle gain 为 `0`；
- 以诊断性 frozen budget `model=0.010s`、
  `startup share=0.002s` 计算，perfect-policy net 为约
  `-0.012001s/context`。

该结果只有一个实例，不能形成正式 scale5 结论；它只验证了用户指出的机制：
当 action 没有收益时，即使模型决策完美，调用成本也会直接变成负收益。正式
默认门槛仍要求 100 contexts 和 20 instances。

## 当前仍缺少的关键证据

`fixed_pool_pricing_pressure_auc` 是机制监督，不是秒数。当前正 pressure gain
必须继续通过 matched end-to-end counterfactual 转换成
`oracle_solver_time_saved_sec_lcb`。缺少这个字段时：

- opportunity density 可以继续观察；
- pressure ranker 不能开始正式训练；
- perfect-policy net ROI 必定不能通过；
- 任何模型都保持 shadow/P0 bypass。

已新增 `bind_p0v2_gat_end_to_end_benefits.py` 作为严格绑定入口。每个正
context 至少需要三个 paired replicates，并强制检查 P0/action 的 exact
status、objective、legal universe、zero filtering、extra incomplete 和
certificate semantics 一致；最后写入
`mean_saving - 1.96 * standard_error` 的非负 LCB。模型成本仍单独扣除，
不能混进 solver benefit。

下一步应先在已冻结的 scale20/30 sentinel instances 上收集 matched
end-to-end 时间轨迹；target-mode 只补足正例。若正式样本达到门槛后
net-gain UCB 仍不大于零，就停止 route-admission 这一动作族，不再增加网络
复杂度。

## 代码与工件

- `src/lunar_ice_bpc/guidance/opportunity_gate.py`
- `scripts/build_p0v2_gat_sentinel_manifest.py`
- `scripts/audit_p0v2_gat_opportunity_roi.py`
- `scripts/bind_p0v2_gat_end_to_end_benefits.py`
- `scripts/collect_p0v2_gat_harvest_rmp_rollouts.py`
- `src/lunar_ice_bpc/guidance/deployment.py`
- `src/lunar_ice_bpc/guidance/runtime.py`
- `scripts/train_p0v2_gat_model_ladder.py`
- `scripts/select_p0v2_gat_model_rung.py`
- `scripts/freeze_p0v2_gat_deployment_manifest.py`
- `data/gat_p0v2/p0v2_gat_opportunity_sentinel_manifest_v1.json`
- `runs/p0v2_gat_opportunity_gate_pilot_20260724/`
