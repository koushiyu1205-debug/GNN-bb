# P0V5 QG2 V4：Real-Map 同分布、GAT 优先的训练与实验方案

## 1. 本轮重启的直接原因

旧 QG2 V3 Oracle 使用 `synthetic_polar_resource_grid_v1` 实例，而正式
scale30/50 使用 `lunar_ice_sp50_real_map_v1`。这不是普通随机波动：正式实例的
edge energy/time、任务时间窗和局部风险分布均明显超出旧训练 envelope。

因此停止旧候选的端到端推广。不得通过扩大 OOD 阈值、把所有特征压成 `[0,1]`
或把正式 001--020 混入训练来绕过该问题。

## 2. 冻结的算法边界

- Exact control 仍为 `P0V4 + V5 bidirectional Exact`；
- 学习模块只可选择一次 `Q0/QD1/QB1` queue ordering；
- QG2 label-state arm 只有在自身 force-on matched test 为正时才可进入动作集；
- 所有动作保持合法扩展、dominance、bound、RC、停止条件和 certificate 不变；
- 任一 hash、OOD、异常、低置信度或全部 arm 被拒绝时必须回 literal Q0；
- scale5/10/20 不加载模型。

## 3. 输入与模型结构

### 3.1 V3.1 输入契约

- edge risk 改为 `risk_integral / Exact objective_reference_risk`；
- normalization 只从 train instances 拟合；
- OOD 从 node/edge group 单一最大值改为逐名称、逐维 train envelope；
- input schema、normalization schema、checkpoint schema、runtime hash 全部升级；
- collection preflight 原子冻结 Native extension、Exact config、acceptance/cold runner、
  P0V4/V5 Python pricing/solver、V3 admission supervision、potential predictor、GAT
  model/runtime 依赖与全部 post-GAT controller 源码 SHA；
  E2E、formal 和 finalizer 沿用并复核同一 execution freeze；
- 正式实例分布不能仅靠输入归一化获得授权，必须有独立 real-map matched outcomes。

### 3.2 两层学习职责

1. **Label ranker**：GAT 输出 node/arc/state potential，只在同一 RC bucket 内重排。
   监督必须与 snapshot 的真实 milestone 一致，两种目标不得混用：
   - `ADMISSION_BATCH_READY` context 的正目标是最终 master-admitted route
     的祖先 label，而非 raw negative。训练入口必须显式交叉校验
     selector witness、`would_enter_master=true` 和冻结的
     `selected_master_ready_native_solution_indices`；三者不一致即
     fail closed，不能只靠“selector 最多 K 条且 master-ready 数达到 K”
     的间接推论。若 admission pairs 超过50,000上限，必须按
     route mass 分层截取、每条 admitted route 至少保留一对并恢复
     组质量，禁止按 selected rank 直接切片丢掉后排 routes。
   - `EXACT_PROOF_COMPLETION` context 不存在可入列的 admitted route；目标改为
     缩短 true-dual exhaustive proof。只使用同 terminal class、同 RC bucket 内的
     dominance winner 和能生成 terminal progress 的 parent label 偏好。这些样本
     必须标记为 proof supervision，不得伪装为 admission positive。
   训练与报告必须按 admission/proof milestone 分层，并另外报告合并效果。
2. **Context arm selector**：GAT 从 pre-action graph/context 同时预测 QD1/QB1 的
   benefit probability、conditional positive gain 和 adverse probability；Q0 是模型外
   fallback。QG2 只有在 train partition 的 force-on 至少获得 5 个可判定 outcome、
   覆盖至少5个 instance且两个规模各至少2个 instance，并且至少2个正收益 outcome
   来自至少2个不同 instance，才能增加为第三个可选 arm。单个 adverse 不再导致
   全局永久 veto；其风险由 adverse head 和 calibration threshold 处理。

若 QG2 进入动作面，必须分别收集 train/calibration/heldout 的真实 QG2 matched
outcome：train 决定它是否可学，calibration 决定阈值，heldout 只做一次冻结评估。
三者不能互换。

部署实现也遵循同一条件分支：QG2 hard-veto 时 runtime 只加载 context selector，
只能执行 Q0/QD1/QB1；QG2 获得 train force-on 支持时，context selector 选择 QG2
后再加载独立冻结的 label-GAT checkpoint，生成 node/arc/state potentials 并安装
ordering-only hints。任一 ranker hash/schema/nonfinite/zero-potential 异常都回 literal Q0。

Native 的 label-state score 不能按整条 parent path 重算：arc potential 随状态转移
增量累加，入队只构造固定15维特征并做点积，随后把 score 缓存在 queue entry 中。
因此每个 label 的额外 scoring 为常数阶，且 `State` 必须继续满足176 B硬约束。

Linear、MLP 与 GAT 使用同一 node/edge/context 输入、split、loss 和动作面。
Linear 也接收 node/edge mean/max；MLP 接收相同图级信息但不做 message passing；
只有 GAT 使用 topology/message passing。三者的 checkpoint 必须声明同一输入契约。
Linear 与 MLP 仅在 GAT 完成 fresh validation 以后训练，不能阻塞 GAT 结论。

## 4. 数据重新构造

### 4.1 独立 real-map corpus

- 使用正式 benchmark 的同一 real-map generator、resource map、time-window mode
  轮换和 Exact 配置；
- 使用与正式 001--020 不重叠的新 seed namespace；
- 每个规模冻结 20 个 development 实例和 12/4/4 split 后再观察任何 action outcome；
- 先在全部 20+20 实例上采集自然 root-pool fallback。若且仅若完整 pilot 因
  snapshot coverage 不足未通过 preflight，再只根据冻结 root index 和 pre-outcome
  split 确定缺失规模；每个被选规模仍对同一 20 个实例执行一次固定标准 BPC-tree
  supplement，采集自然 branch/cut fallback；若两个规模都缺则运行 20+20，若只有
  一个规模缺则不额外运行另一个规模。不丢弃 pilot、不使用 Oracle/arm outcome
  选择规模或实例、不延长单次 pricing、不降低数据门槛；
- tree supplement 仍不足则本轮停止并报告 opportunity 不足，不进入按结果循环扩样；
- 正式 001--020 永远不进入训练、阈值校准、OOD envelope 或 early stopping；
- 每个规模至少 10 个不同 development instances 产生合规 fallback context。

### 4.2 matched action outcomes

- 每个合规 snapshot fresh-process 运行 Q0、QD1、QB1；
- 初筛各一次；对可能获益或接近阈值的 arm 做 3 个 blocked replicates；
- scale30 matched replay budget 固定 300 秒，scale50 固定 600 秒；旧 180/300
  对 real-map heavy-tail censor 过多，本轮冻结后不再运行中修改；
- QD1/QB1 不能仅用一次 initial replay 作为 selector 标签；每个用于训练/校准/heldout
  的 context 使用 3 次 blocked replicates，以中位数 outcome 建标签；
- right censor 单独标记，双方都 censor 的 context 不伪装成负样本；
- timeout/memory-limit 下 `labels_dropped=true` 且未声称 exhaustive/certificate 时是
  fail-closed censor，不是 correctness redline；只有 exhaustive 与 label drop 并存、
  guidance filter/drop、合法宇宙漂移或双方 exact 结果不一致才判 unsafe；
- split 按 instance 固定为 60/20/20，禁止同实例跨 partition；
- partition 内不能继续把每个 context 当成独立等权样本。Label GAT 与
  Context GAT 的每个 epoch 保持原优化步数，但 instance 贡献的步数
  最多相差1；同一 instance 内部的 context 按 epoch 确定性轮换，不丢弃
  context-rich instance 的覆盖。
- checkpoint early stopping 使用 instance-average calibration metric；同时报告
  context-average、instance-average 和最大 instance context 占比。Threshold 搜索的
  net GM 也必须先在 instance 内聚合、再对 instance 等权，不能让同一
  instance 的多个近似 context 重复投票。
- label trace 只为 label-ranker 训练开启，context selector 不使用干预后字段。

### 4.3 两类 Oracle 门槛不得混用

- strict leaked-QO2 gate 继续报告固定 QO2 arm 的 GM、bootstrap 和收益集中度，
  作为“动作面是否可能改变 wall”的性能诊断；
- GAT fitting gate 只授权训练，不授权部署。考虑到 scale50 的 frozen eligible universe
  只有29个 context且600秒 replay 仍可能 right-censor，门槛在任何 scale50 outcome
  出现前一次性冻结为：两个规模均至少12个可判定 context、6个 instance；每规模
  至少2个来自2个 instance的严格正收益样本、4个非正收益样本和来自1个 instance
  的有害样本；所有 exact-safety 与 binding 审计通过，单一 instance 节省占比不超过
  50%。这里不再要求单个正样本达到5%，
  小而严格的正收益也可用于拟合，真正采用仍由 fresh-process/E2E 决定；
- 为避免总量门槛通过但 train/calibration/heldout 某分区为空，每规模的合规
  context 还必须至少覆盖 train 4 contexts/2 instances、calibration 2/2、heldout
  2/2；否则不运行 smoke 或正式训练；
- 该放宽仅适用于 fitting-only authority；calibration 的逐规模不退化、heldout fresh
  净收益、正式 exact count、p99 和 correctness 门槛完全不变。达到完整 Oracle 后
  不再根据实际正负比例继续调整上述门槛；
- pre-outcome 证据冻结在
  `realmap_v4_instance_balanced_fitting_gate_freeze.json`：创建时 scale50 outcome
  directory 为0，并绑定门槛、旧 authorizer、新 wrapper 和 Oracle execution freeze
  SHA。authorizer 每次执行前必须验证该文件，禁止 post-outcome 改门槛；
- strict QO2 的固定-arm GM 或 bootstrap 未达旧阈值，不得单独阻止 selective GAT
  训练；否则会把“某个固定 Oracle arm 不稳定”错误等同于“没有可学习的选择问题”；
- 首轮 bounded Oracle 固定最多 120 contexts、每规模最多 60；旧 corpus 中从 initial
  到可判定 context 的留存率约一半，40/规模过于贴近 20-context 训练下限，容易在
  完整运行后才因 censor/trace exclusion 返工；
- fresh-process、heldout 与 E2E 仍是是否采用模型的唯一性能 authority。训练授权文件
  必须保持 `development_only/deployable=false`。

## 5. GAT 优先执行顺序

Oracle 采集与模型训练使用两阶段 freeze：第一阶段绑定 Exact engine、
snapshot、replay 与 matched outcomes；第二阶段在 Oracle summary 完成后另行
绑定 instance-balanced sampler、Label/Context GAT trainer、calibration 和 fresh
controllers。第二阶段 freeze 必须引用第一阶段 summary/hash，不得改写
或重采 Oracle outcomes。它在1轮 smoke 后、正式训练前创建，并递归绑定
training-only gate、instance split、smoke view/report/checkpoint 及正式 trainer sources；
不得把 smoke 已产生的诊断 checkpoint 误写成“所有训练之前”。

1. 生成并审计独立 real-map development corpus；
2. 完成 root-only census；coverage 不足时，对冻结判定出的缺失规模执行一次固定
   all20 BPC-tree supplement；
3. preflight 后冻结 index/config/engine/runtime/split/source hash；
4. 收集 Q0/QD1/QB1 matched outcomes并运行 strict Oracle 诊断；
5. 通过 training-only 数据 gate 后，先对 train/calibration 两个规模各抽取最多2个
   不同 instance，运行1轮 instance-balanced Label GAT smoke；smoke 必须验证
   sampler、normalization、checkpoint metadata 和训练曲线，随后才生成第二阶段
   training freeze；
6. 在第二阶段 freeze 下正式训练 label GAT，并立即做 pair accuracy、feature
   ablation 和小规模 force-on；
7. force-on 首屏为每规模5个 context，按 instance round-robin 选择，保证一个
   instance 获得第二个 context 前先覆盖其他 instance；若至少出现1个严格正收益或
   beneficial-censor，只允许一次固定的全 train 扩展。扩展不改变 eligible context
   宇宙，只改变确定性执行顺序；最终按至少5个可判定/5个 instance、两个规模各至少
   2个 instance、至少2个正收益/2个正收益 instance 裁决。首屏零信号或扩展后仍不足
   则 hard-veto QG2，不继续采样或调它；
   Context trainer 内部的 `qg2_arm_is_trainable` 使用完全相同的 instance/scale
   门槛；不得在外层 controller veto 后按旧的5 context/2 positive规则重新启用 QG2；
8. 训练 context multi-arm GAT；
9. calibration instances 冻结 threshold/risk veto/OOD envelope；
10. heldout snapshots 做 3-repeat fresh-process GAT test；
11. 只有 GAT fresh test 安全且净收益为正，才训练 MLP、Linear 对照；
12. 冻结 GAT 候选，运行未参与训练的 development E2E；
13. 最后运行正式 scale5/10/20/30/50 full20。

正式 full20 与旧 V4 completion audit 通过后，还必须运行独立的
instance-balanced completion audit。该审计重跑 sampler/force-on/wrapper/controller
专项测试，复核5份模型报告、2份 attribution、6份 fresh report、5条 curve、QG2
force support 与最终动作面的一致性，并将所有产物和测试源码 SHA 绑定到外层候选。
旧审计通过但新审计缺失或失败时不得冻结 instance-balanced candidate。
外层 finalizer 还必须逐项重算该审计内部记录的全部 artifact SHA；只绑定 audit JSON
自身或只读取 `passed=true` 不构成冻结授权。

实际控制器把两层对照分开：label-ranker 的 MLP/Linear 使用与 label GAT 相同的
milestone-conditional pairs（admission context 使用 master-admitted route ancestors；
proof context 使用 action-reachable dominance/terminal-progress pairs）；context-selector
的 MLP/Linear 使用与 context GAT 相同的 GAT-QG2/QD1/QB1 matched outcomes。这样前者
回答 ordering supervision 是否需要图结构，后者回答 multi-arm 选择是否需要 message
passing，不把两个问题混成一个 accuracy。

GAT heldout fresh 结论会先写入事件日志，之后才启动 MLP/Linear。对照结果不会反向
改变 GAT 是否进入 development E2E，只决定论文能否宣称 graph architecture advantage；
若 GAT 相对最佳对照不足2%，只能报告 learned ordering/selector 有效。

不再要求 GAT 必须先达到 5% 才能进入 development E2E；但正式部署仍要求
common-exact 净收益为正、exact 数不下降且 correctness redline 为零。

## 6. 阈值与选择规则

- threshold 只在 calibration instances 选择；
- 候选阈值按“零 unsafe/censor -> harmful 上界 -> 净 GM -> activation coverage”排序；
- 同时报告 harmful rate、beneficial precision 的 Wilson 95% 区间，以及按 instance
  bootstrap 的 GM 95% 区间；首批每规模只有 4 个 calibration instance，这些区间用于
  说明不确定性，不作为通过扩大样本才能解除的无限硬门；
- benefit/adverse head 的 BCE 使用 train-only、按 arm 裁剪到 `[0.25,4]` 的正类权重；
  除 raw accuracy 外必须报告 prevalence、balanced accuracy、precision、recall、
  specificity、Brier score 和 confusion matrix，防止多数类造成虚高且三模型看似接近；
- context selector 另使用权重0.25的同-context pairwise utility rank loss：只对
  matched、uncensored outcome 以裁剪后的 `1-wall_ratio` 比较 arm-vs-Q0 和
  arm-vs-arm；right-censored outcome 不进入 rank target，仍只进入已有的
  benefit/adverse censor-aware heads；三种模型使用完全相同 loss；
- 不用 heldout 反复调阈值；heldout 只执行一次冻结决策；
- 高阈值的 Q0 回退不计推理退化，但报告 inference/tensorization wall；
- 最终可选 arm 的风险调整分数为 `p * positive_gain - lambda * adverse_p`；
- 若无 arm 同时通过 probability、gain、risk、OOD 和 binding gate，则执行 Q0。
- calibration 若没有任何可行激活组合，冻结范围合法的 threshold 并将全部非 Q0
  arm 写入 `forced_veto_arms`；不得用越界概率或无穷 gain 表示 no-op-only。

## 7. 测试与正式验收

### 7.1 单元/差分测试

- objective-normalized edge risk、schema drift 和幂等变换；
- per-feature OOD 的名称、维度、范围和 fail-closed 行为；
- GAT/MLP/Linear 输出维度、NaN/Inf、checkpoint roundtrip；
- Q0/QD1/QB1 单次动作、下一轮恢复、Q0 fallback；
- QG2-enabled manifest 必须验证 selector/ranker 双 checkpoint hash，实际安装 15 维
  label-state coefficients；QG2-veto manifest 不得加载 ranker；
- force-on 有界初筛必须先覆盖不同 instance；full-train 扩展必须保持原 eligible
  context 宇宙，QG2 support 不能由同一 instance 的重复 context 单独满足；
- branch/cut/root binding、legal universe、global minimum、certificate 一致；
- 500 组可穷举 differential test；
- `sizeof(State)==176`，无 per-label embedding。

### 7.2 模型诊断

- 每轮落盘 `training_curve.jsonl`；
- label ranker 默认最多 40 轮、patience 8；context selector 默认最多 200 轮、
  patience 25。两者只按 calibration 指标选择 best epoch，不能用 heldout early stop；
- 报告 train/calibration/heldout pair accuracy；
- 每个 label/context 模型同时报告 parameter count，避免把容量差异误判成图结构收益；
- context selector 同时报告 matched outcomes 上的 arm-vs-Q0 与 arm-vs-arm
  pair accuracy，避免只用独立 benefit/adverse classification accuracy 判断策略选择；
- 报告 no-message、shuffle topology、node/edge/context group 和单特征 ablation；
- Label/Context attribution 都显式给出 top feature、全部正向单特征 drop 中的占比和
  相对所属 feature-group drop 的占比，用于检验“一个特征主导所以三模型接近”的
  假设；ablation 不可加，故该指标只作诊断，不能代替 fresh-process wall；
- context attribution 以 arm-rank accuracy drop 为首要特征贡献诊断，同时保留
  classification drop、selected-action disagreement 和 matched wall GM；
- GAT 若不比最佳 MLP/Linear 明显更好，只能宣称 learned selector 有效，不能宣称
  graph architecture 优势。

### 7.3 最终实验

- scale5/10/20：20/20 exact，模型调用为零，time ratio <= 1.01；
- scale30：20/20 exact，common-exact GM < 1.0；
- scale50：exact 数不得低于 Exact control，common-exact GM < 1.0；
- inference p99 <= 10 ms；
- objective、RC、global minimum、certificate 和所有 no-cheat redline 为零；
- P0V4/P0V5 Exact control、正式 001--020 和 production 默认均不覆盖。

V4 验收使用独立的 `analyze_p0v5_qg2_realmap_v4_acceptance.py` 和
`v4_positive_net` profile；历史5% analyzer 不再修改，继续由旧 V2/V3 freeze
校验。这样新 telemetry/p99 门槛不会污染历史实验。该 profile 与“只要存在严格净
优化就进入正式实例试验”的决定一致。
它不放松 correctness：scale30/50 仍分别要求 GM < 1.0，scale50 exact 不低于 control
且至少15/20；scale5/10/20 保持20/20、ratio <= 1.01、selector inference 为零，
scale30/50 inference p99 <= 10 ms。

## 8. 当前执行入口（2026-08-07）

- 实时状态统一维护在
  `runs/p0v5_qg2_v4_realmap_gat_first_20260806/STATUS_ZH.md`；本设计文件不复制
  易过期的 context 数和 wall；
- 旧 context-equal GAT-first 父控制器已暂停，正在运行的冻结 Oracle 子进程不重采、
  不改 arm 和预算；
- 新入口为
  `scripts/run_p0v5_qg2_realmap_v4_instance_balanced_gat_first.py`，只接受完整 Oracle
  summary，并强制执行 training-only gate、1轮 smoke 和第二阶段 freeze；
- 新入口首先训练 Label GAT，再训练 Context GAT；GAT heldout fresh 净收益未确认前，
  MLP/Linear 输出目录必须不存在；
- instance-balanced sampler、两层训练/attribution/fresh wrapper、force-on
  instance-round-robin、独立 completion audit 与两阶段 freeze 专项回归当前为
  `89 passed`；全部
  `test_p0v5_qg2_*.py` 为 `403 passed`，另4项仅为历史 V2 freeze 对旧 acceptance
  analyzer 的已知 SHA drift，V4 当前链路无新增失败；正式训练尚未开始。
- 新 wrapper 已在独立临时目录用旧 synthetic 双规模授权 corpus 完成1轮工程 smoke：
  8个不同 instance，rank loss `0.63944`，calibration instance pair accuracy
  `0.74121`，epoch wall约`0.25s`；它不属于 real-map 模型证据，正式 smoke 仍由
  完整 real-map Oracle 后的两阶段 freeze 流程唯一生成。
