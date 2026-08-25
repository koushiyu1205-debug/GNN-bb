# P0V5 QG2 V4 Real-Map GAT-First 状态

更新时间：2026-08-07

> **历史链已于 2026-08-07 终止。** bounded Oracle、当前 replay、旧父控制器与
> instance-balanced handoff 均已显式停止；下方自动区最后更新时间为11:11，仅保留
> 停止前快照，其中“RUNNING_BOUNDED_ORACLE/运行中”不再代表当前进程状态。后续以
> `runs/p0v5_qg2_v5_trace_first_20260807/STATUS_ZH.md` 为唯一实时状态。

<!-- AUTO_PROGRESS_BEGIN -->
## 自动进度（只读维护）

- 更新时间：`2026-08-07T11:11:42+08:00`；
- real-map development corpus：scale30 `20/20`，scale50 `20/20`；
- 生成进程：`STOPPED`；
- watcher 历史记录：`SNAPSHOT_COLLECTION_FAILED`；
- tree-supplement successor 历史记录：`GAT_FIRST_PIPELINE_EXECUTION_ERROR`；
- tree supplement：`TREE_SUPPLEMENT_PREFLIGHT_READY`；
- snapshot collection：`ORACLE_PREFLIGHT_READY_AFTER_TREE_SUPPLEMENT`；
- collection progress：s30 instances 20/20，tree 20/20，root-certified/cap/redline 18/2/0，tree-exact/redline 20/0，snapshots 65@13 instances，T/C/H 36/21/8 contexts @ 8/3/2 instances，preflight deficit total ctx/inst 0/0，T/C/H ctx 0/0/0，inst 0/0/0；s50 instances 20/20，tree 0/20，root-certified/cap/redline 6/14/0，tree-exact/redline 0/0，snapshots 29@17 instances，T/C/H 15/8/6 contexts @ 9/4/4 instances，preflight deficit total ctx/inst 0/0，T/C/H ctx 0/0/0，inst 0/0/0；
- GAT-first pipeline：`RUNNING_BOUNDED_ORACLE`。
- GAT-first controller 进程：`STOPPED`；
- instance-balanced handoff：`WAITING_FOR_FROZEN_ORACLE`；进程 `STOPPED`；
- 阶段判定以 GAT-first pipeline 与下表为准；上游历史记录不代表当前 Oracle/训练失败。

| 阶段 | 当前证据 |
|---|---|
| Real-map corpus | scale30 20/20；scale50 20/20 |
| Snapshot collection | s30 instances 20/20，tree 20/20，root-certified/cap/redline 18/2/0，tree-exact/redline 20/0，snapshots 65@13 instances，T/C/H 36/21/8 contexts @ 8/3/2 instances，preflight deficit total ctx/inst 0/0，T/C/H ctx 0/0/0，inst 0/0/0；s50 instances 20/20，tree 0/20，root-certified/cap/redline 6/14/0，tree-exact/redline 0/0，snapshots 29@17 instances，T/C/H 15/8/6 contexts @ 9/4/4 instances，preflight deficit total ctx/inst 0/0，T/C/H ctx 0/0/0，inst 0/0/0 |
| Bounded Oracle | 运行中；contexts touched 33/89（s30 33/60@10 instances/s50 0/29@0 instances）；trace contexts 33；replay outcomes 292；complete/timeout 275/17；latest 30_160c38eb8e93f9b1/random_61635_initial.json TIMEOUT 301.410535s |
| Initial-arm provisional GM | 仅为进行中 initial screen；QD1 0.838264（n=33，censored=0）；QB1 1.433596（n=33，censored=7）；QO2-1e-4 0.979254（n=32，censored=0）；QO2-3e-4 0.988938（n=32，censored=0）；QO2-1e-3 1.001635（n=32，censored=1） |
| Q0 milestone/headroom | 进行中 Q0 compact outcomes；s30 n=33 admission/proof/other 0/33/0，weighted Native-search 99.350%，audit+selector 0.650%；s50 n=0 |
| Training provenance | 等待完整 Oracle；尚无 training-only authority 或模型输出 |
| Fitting gate freeze | profile bounded_instance_supported_fitting_only.v2；pre-scale50 True；determined ctx/instances per scale 12/6 |
| Label GAT | 尚未训练 |
| Context GAT | 尚未训练 |
| Label MLP/Linear | 尚未训练 |
| Context MLP | 尚未训练 |
| Context Linear | 尚未训练 |
| GAT calibration fresh | 尚未开始 |
| GAT heldout fresh | 尚未开始 |
| GAT/MLP/Linear comparison | 尚未生成 |
| Development E2E | 尚未开始 |
| Formal full20 | 尚未开始 |
| Instance-balanced completion audit | 尚未开始 |
| Independent final candidate | 尚未冻结 |
<!-- AUTO_PROGRESS_END -->

## 当前结论

- 旧 V3 训练与实验已停止；没有旧 Native/Oracle/训练进程继续运行。
- 旧 Oracle corpus 是 synthetic map，正式 scale30/50 是 real-map，存在明确 domain shift。
- 旧 GAT 在正式 scale50/001 全部回退 Q0 的直接原因是 OOD，不是 GAT 动作退化。
- 当前候选尚未训练；独立 real-map corpus、自然 P0V5 fallback snapshot collection
  与 preflight 已完成并通过正式实例 hash 零重叠审计，正在运行冻结的 bounded Oracle。
- 冻结 Oracle selection 暴露了 scale30 partition 内 context 集中：train 最高
  `14/31` 来自同一 instance，calibration 最高 `15/21`，heldout 最高
  `5/8`。这不是跨 partition 泄漏，但会使 context 等权 loss、early stopping
  和 threshold 被少数 instance 主导。
- 当前 Oracle 子进程继续运行；GAT-first 父控制器已 `SIGSTOP`，只为
  防止 Oracle 结束后自动抢跑旧 context-等权训练器。不重采 Oracle，
  将从同一 outcome 生成独立 instance-balanced training freeze。
- 当前 real-map corpus 数量与控制器阶段以文首“自动进度”为准。

## 已完成修改

- edge risk 使用 `risk_integral / Exact objective_reference_risk`；
- normalization 只拟合 train instances；
- OOD 从 node/edge 单一最大值改为逐名称、逐特征 envelope；
- input/normalization/checkpoint/runtime hash schema 已升级；
- GAT-first 顺序冻结：GAT fresh validation 完成后才训练 MLP、Linear；
- 动作面为 Q0/QD1/QB1，QG2 必须先在 train partition 的 real-map
  force-on 中取得至少 5 个可判定 outcome 和至少 2 个正收益 outcome，才解除 hard veto；
- QG2 若解除 veto，必须补齐 train/calibration/heldout 三个 partition 的真实
  matched outcome；calibration 只选阈值，heldout 不参与动作面决定；
- combined runtime 已补齐条件 QG2 执行：context GAT 选择 QG2 后加载独立冻结的
  label GAT，安装 node/arc/15维state ordering potentials；hash/schema/nonfinite/
  zero-potential 任一失败均回 literal Q0；QG2 hard-veto 时完全不加载 ranker；
- combined runtime 已增加 QG2 ranker hash-drift、zero-potential 和 OOD 的直接
  fail-closed 回归；三种情形均保留原 request 对象、Q0 container 和空 guidance；
- Linear/MLP/GAT 接收相同 node、edge、context 输入；Linear 也保留 node/edge
  mean/max，防止因输入摘要缺失造成不公平对照；
- 阈值报告新增 harmful rate、beneficial precision 的 Wilson 95% 区间，以及
  instance-bootstrap GM 95% 区间；小 calibration 样本的区间只报告，不伪装成硬授权；
- calibration threshold 的实际选择键已与报告对齐：零有害优先，其后依次最小化
  harmful Wilson 95% 上界、最大化 beneficial-precision Wilson 95% 下界、最小化
  净 GM，再最大化 activation coverage；heldout 不参与选择；
- calibration 若找不到任何安全激活组合，现以范围合法的 threshold 加
  `forced_veto_arms=[QG2,QD1,QB1]` 显式冻结 no-op-only 策略；不再用 `p=2`、
  `gain=inf` 把正常 Q0 决策伪装成损坏配置；
- fresh-process 与 attribution 默认原样使用 calibration 冻结 threshold，不再把
  `minimum_expected_gain` 隐式抬到1%；只有命令行显式传入 conservative override
  才允许收紧，最终 candidate manifest/runtime 继承 fresh 实际使用的同一组阈值；
- selector runtime 除 NaN/Inf 外也 fail closed 检查 threshold 范围：benefit/adverse
  probability 必须在[0,1]、expected gain和risk penalty不得为负；任一越界均 literal Q0；
- collection controller 会在 snapshot preflight 后原子冻结 Oracle engine/index/config/
  split/source hash；后续 outcome 不能悄悄改变执行面；
- freeze source 面已扩展到 acceptance/cold runner、P0V4/V5 Python pricing/solver、
  Native extension、GAT runtime 和全部 post-GAT controller；E2E/formal/finalizer 会沿链
  复核同一 Oracle execution freeze，防止训练后 Exact 实现漂移；
- Oracle execution freeze 现额外显式纳入实际训练调用的 V3 admission supervision、
  potential predictor、模型基础层、tensorization 和 context-arm helper；不再只冻结
  V2 supervision 名称而遗漏 V3 标签生成实现；
- strict QO2 性能 gate 保留为机制诊断，另设 training-only 数据充分性 gate；后者只
  允许拟合 GAT，不允许部署，最终 authority 仍为 fresh-process 与 E2E；
- V4 training-only gate 不再要求单个 context 至少快5%；鉴于 scale50 frozen universe
  只有29个 context，且其 outcome 尚为零时已将 fitting-only 门槛一次性冻结为每规模
  12个可判定 context/6个instance、2个正收益 context/2个正收益 instance、4个
  非正收益、1个有害 instance和50%收益集中度；完整 Oracle 后不得按观测结果再调。
  calibration/heldout fresh、正式 exact count、p99 和 correctness 门槛均未放松；
- fitting authority 另要求每规模 train 至少4 contexts/2 instances、calibration
  至少2/2、heldout至少2/2，防止总量达标但某分区没有独立实验单位；
- fitting gate 已在 scale50 outcome directory 仍为0时写入独立 pre-outcome freeze，
  绑定门槛、旧/新 authorizer 与 Oracle execution freeze SHA；新 authorizer 启动前
  强制复核该 freeze，后续不能根据 scale50 观测结果再修改；
- bounded Oracle selection 已绑定 pre-outcome split 并按 partition/structure/instance
  轮转；preflight 同时要求每个规模 train 至少 10 contexts/6 instances，calibration
  和 heldout 各至少 4 contexts/2 instances，避免 outcome 收完后才发现分区不可评估；
- bounded Oracle 固定上限调整为 `120`（每规模 `60`）；这是根据旧 corpus 约一半
  initial context 会因 censor/trace 条件不可判定而预留的覆盖余量，不在运行中扩样；
- `120/60` 现已同时写入 Oracle execution freeze；GAT-first 启动器和最终
  completion audit 会拒绝任何与该预先计划不一致的 context 预算；
- label ranker 与 context selector 都改为 calibration-only best-epoch selection；
  heldout 不参与 early stopping，避免固定训练到末轮造成小样本过拟合；
- V3/V4 label supervision 现显式交叉校验 selector witness、
  `would_enter_master` 与 `selected_master_ready_native_solution_indices`；只有冻结
  selector 后最终可进入 Master 的 route 祖先可作为 admission 正样本，selector
  选中但 Master 拒绝的 route 会 fail closed，不能静默污染 rank loss；
- label pair 超过50,000上限时不再按 selected rank 直接截断；现按 admitted-route
  mass 分层配额，每条 route 至少保留一对，并在截取后恢复各 route 原监督质量；
- V4 matched replay 预算冻结为 scale30 `300s`、scale50 `600s`，避免 heavy-tail
  context 在旧 180/300 秒预算下大面积双 censor；正式求解预算仍为 3600 秒；
- fresh safety 已区分 fail-closed resource censor 与 correctness redline：普通
  timeout/memory-limit 的非 exhaustive label drop 进入 censor mask；exhaustive 与
  label drop 并存、guidance filter/drop、合法宇宙漂移或 exact 不一致仍硬失败；
- QD1/QB1 selector 标签改用 3 次 blocked replicates 的中位数，不再把单次 wall
  抖动直接当作 arm 真值；
- selector 的 benefit/adverse loss 增加 train-only class balancing；报告 balanced
  accuracy、precision/recall、Brier 与 confusion，不再只看可能受多数类支配的 accuracy；
- context selector 的 `rank_loss` 不再恒为0：matched、uncensored outcomes 以
  `clip(1-wall_ratio,-1,1)` 构造 arm-vs-Q0/arm-vs-arm 相对监督，权重0.25；
  censored outcomes 对 rank 完全 mask，仍由 benefit/adverse heads 表达；
- selector report 新增 train/calibration/heldout 的 arm-vs-Q0/arm-vs-arm pair
  accuracy，三模型比较不再只依赖可能接近的独立分类准确率；
- context attribution 同步改以 arm-rank accuracy drop 排序单特征和 group 贡献，
  并保留 classification drop、action disagreement 与真实 matched GM；
- label 与 context 两层的 GAT/MLP/Linear report 均记录 parameter count，后续解释
  准确率接近时可同时检查容量、单特征贡献和 topology ablation；
- Native QG2 priority 已完成复杂度复核：arc potential 随状态转移增量累加，入队时
  只构造固定15维 label-state feature 并做一次点积，结果写入缓存队列键；不会沿
  parent chain 重算路径，单 label 额外工作为常数阶，`State` 继续保持176 B；
- 当前结构的参数量诊断：label GAT/MLP/Linear 为
  `24,337/8,625/3,537`，context GAT/MLP/Linear 为
  `20,137/4,425/792`；三者接近不能归因于容量完全相同；
- label 与 context GAT attribution 均已覆盖 node/edge/context 整组、逐特征、
  no-message 和 shuffled-topology 消融；context report 额外记录单特征相对整组
  accuracy-drop 占比，用于诊断 Linear/MLP/GAT 接近是否由单一特征主导；
- Label attribution 也已补齐 top feature 在全部正向单特征 drop 中的占比及相对所属
  feature-group drop 的占比；两种占比只用于定位支配候选，不把非可加的 ablation
  误解释成因果贡献；
- Oracle selection 的 partition 内集中已完成定量审计；scale30 train/
  calibration/heldout 的最大单 instance context 占比分别为
  `14/31`、`15/21`、`5/8`，不再允许 context 等权直接进入训练。
- 已实现 Label/Context GAT 共用的 instance-balanced epoch sampler：保持
  epoch 总步数，各 instance 步数最多相差1，instance 内 context 随 epoch
  确定性轮换；normalization、class balance、early stopping 与 threshold GM
  也均以 instance 为实验单元。
- 新增两阶段 provenance：Oracle execution freeze 保持不变；Oracle summary
  完成并通过 training-only gate 后，先运行覆盖 scale30/50、train/calibration
  不同 instance 的1轮 Label GAT smoke；smoke 通过后才生成独立
  instance-balanced training freeze，并在每个 GAT/MLP/Linear 训练、fresh 和
  final-candidate 阶段重新校验。freeze 语义明确为“smoke 后、正式训练前”，并
  递归复核 gate、split、smoke view/report/checkpoint，不只锁 smoke JSON 外壳。
- 已用旧 synthetic 双规模授权 corpus 在独立 `/tmp` 目录完成一次 wrapper 工程预检：
  scale30/50、train/calibration 共8个不同 instance，1轮 Label GAT rank loss
  `0.63944`、calibration instance pair accuracy `0.74121`、epoch wall约`0.25s`；
  该结果只证明新训练入口可运行，不混入 real-map 正式训练或性能结论；
- 已增加固定 GAT-first controller：Oracle -> training gate -> label GAT -> attribution
  -> force-on -> replicated arms -> context GAT -> calibration/heldout fresh；GAT fresh
  结论出来前不会训练 MLP/Linear；GAT fresh 安全且净收益为正后，才运行 label 与
  context 两层的 MLP/Linear 公平对照；
- post-GAT controls 完成后新增独立 instance-balanced comparison addendum：纠正旧
  comparison 中仅写 admission-ancestor 的过窄文字，并强制绑定 Label/Context 的
  GAT、MLP、Linear 共5份报告；最终外层 candidate 必须复核这些 hash；
- 正式 full20 后新增独立 instance-balanced completion audit：重跑新 sampler、
  force-on、fresh/attribution wrapper 与 controller 测试，并复核5份模型报告、2份
  attribution、6份 fresh、5条 training curve、QG2 force support 和最终动作面一致性；
  旧 V4 completion audit 单独通过不再足以冻结外层候选；
- 外层 finalizer 会再次逐项重算 instance-balanced audit 记录的全部 artifact SHA；
  audit 之后任何 curve、force report、fresh report或测试源码漂移都会拒绝冻结；
- label GAT force-on 首屏仍固定为每规模5个 context，但改为 instance round-robin：
  同一 instance 获得第二个 context 前先覆盖其他 instance；出现1个正收益信号才允许
  唯一一次全 train 扩展，扩展保持 eligible context 宇宙不变。最终开放 QG2 要求
  至少5个可判定 context/5个 instance、两个规模各至少2个 instance，并且至少2个
  正收益来自2个不同 instance；首屏零信号或扩展后不足均 hard-veto，不循环扩样；
- Context trainer 内部的 QG2 enable gate 已同步为同一 instance/scale 规则；外层
  controller veto 后，trainer 不再可能按旧5-context/2-positive门槛偷偷重新启用QG2；
- 新增 V4 专用 development E2E 与 formal full20 控制器；guided 路径加载
  context multi-arm selector manifest，control 路径清空全部 learning 环境变量；
- 历史5%门槛保留为 legacy profile；V4 使用 positive-net profile，只要求严格净
  加速即可进入正式实验，但 exact count、redline、selector action、inference p99
  和小规模零模型调用仍为硬门；
- formal full20 通过后自动复跑 Native 500组随机 exact differential、176 B状态约束
  和 Python 安全回归，再生成独立候选 freeze；production 默认始终不切换；
- completion audit 会冻结全部 E2E/comparison/attribution/curve/report 和被测源码
  SHA；finalizer 会再次逐项核验，审计后的任何证据或测试源码漂移都拒绝冻结；
- V4 multi-arm telemetry、inference p99 与 positive-net gate 已迁入独立
  `analyze_p0v5_qg2_realmap_v4_acceptance.py`；不再扩展被历史 V2/V3 freeze
  绑定的 legacy acceptance analyzer；
- watcher 已加载冻结的 120/60 Oracle 预算（session `96447`）；corpus audit
  已通过，当前正在 snapshot collection。只有 snapshot preflight 通过才会依次启动
  bounded Oracle 与 GAT-first pipeline；任一 gate 失败即停止，不会自动放宽。
- fixed tree supplement 已完成 scale30 20/20 exact、redline为0；自动后继首次启动时
  暴露状态机漏分支：GAT-first 只接受 root-only 的 `ORACLE_PREFLIGHT_READY`，未接受
  tree 路径的 `ORACLE_PREFLIGHT_READY_AFTER_TREE_SUPPLEMENT`。Oracle outcome 尚为零时
  已补显式白名单与回归测试，重新生成131文件 execution freeze，SHA drift为0，并
  成功启动120/60 bounded Oracle；
- 新 real-map collection controller 已实现，强制正式实例 hash 零重叠、单 Native 进程和 literal Q0 collection。
- root-only pilot 若因 coverage 不足结束，固定后继控制器只会在全部40例完成后，
  根据冻结 root index 与同一12/4/4 split确定缺失规模；每个被选规模固定运行同一
  20个实例的标准 BPC-tree supplement。它保留现有 snapshots、采集自然 branch/cut
  fallback，仍为单 Native、literal Q0，不使用 Oracle/arm outcome 选择规模或实例，
  也不降低 preflight 门槛。
- 自动进度现直接扫描正在生成的 snapshot 目录并报告 total 与 T/C/H context/instance
  preflight deficit；阶段中尚未重建的 `realmap_v4_snapshot_index.json` 不再被误当成
  scale50 实时 coverage。
- GAT/MLP/Linear 开始训练后，自动进度会逐轮显示 model、epoch、total/rank/
  benefit/positive-gain/adverse loss、epoch wall 和 best-epoch 标记；完整 JSONL 仍保留。
- label model 完成后，同一状态行还会从冻结 training report 显示 train/calibration/
  heldout mean-context pair accuracy，避免只看 loss 或最后一轮。

## 诊断训练（非候选）

V3.1 GAT 在旧 synthetic corpus 上完成 40 轮，仅用于验证输入实现：

| 指标 | 结果 |
|---|---:|
| Rank loss | 0.5731 -> 0.4273 |
| Train mean-context pair accuracy | 77.84% |
| Calibration | 71.16% |
| Heldout | 64.10% |

该 checkpoint 不得进入正式 E2E，因为训练分布仍不匹配 real-map benchmark。

## 正在运行

- 任务：在已冻结的89个 real-map fallback contexts 上运行 bounded Oracle；
- 顺序：先 scale30 的60个 context，再 scale50 的29个 context；每个 arm、repeat、
  scale30/50 的300/600秒预算和约10.867 GiB内存上限均已写入 execution freeze；
- 同一时刻只有一个 fresh Native replay；当前没有训练进程，也没有模型产物；
- 旧 context-equal 父控制器处于 `SIGSTOP`，不会在 Oracle 结束后进入旧 trainer；
  独立 handoff 会先将其退出，再启动新的 instance-balanced GAT-first 入口；
- 当前 context、arm、complete/timeout 和 provisional GM 以文首“自动进度”为准；
- 正式 benchmark 001--020 未读入训练、未参与 threshold、未进入 OOD envelope。

## 测试

- V3.1/V4 ranker、selector、runtime、bidirectional gate、label-state safety：
  `159 passed`；
- 当前 GAT-first ranker、multi-arm selector、calibration/runtime authority 和全部
  V4 post-GAT controller 扩展回归：`250 passed in 14.82s`；
- 新增 instance-balanced sampler、metric、bootstrap、Label/Context wrapper、
  pretraining smoke、force-on instance round-robin、controls 重定向与两阶段 freeze
  专项回归：`89 passed in 0.78s`；
- Label GAT、milestone supervision、Context GAT、selector runtime、formal ordering、
  post-GAT controller 与新交接链合并回归：`208 passed in 14.44s`；
- 同次目标回归仅1项历史 positive-net V2 freeze SHA audit 报告
  `analyze_p0v5_qg2_paired_acceptance.py` source drift；没有改写旧 freeze。
  V4 analyzer 已独立，当前候选不复用该历史 execution freeze；
- 全部 `test_p0v5_qg2_*.py` 扩大回归：`403 passed`，另4项失败均来自同一历史
  V2 freeze 对 `analyze_p0v5_qg2_paired_acceptance.py` 的已知 SHA drift；本次 V4
  instance-balanced 改造没有新增行为失败；
- Native QG2 500组随机 exact differential、`label_state_bytes == 176`：passed；
- collection freeze 复核：88个 Exact Python sources、Exact config、corpus manifest、
  split、QG2 snapshot runtime/model 和唯一 Native extension 的 SHA drift 均为0；
- `git diff --check`：passed；
- Oracle/GAT/controls/E2E/formal/audit/finalizer 全冻结链路 `py_compile`：passed；
- correctness/certificate redline：未触碰 Exact 逻辑。

## 后续固定顺序

1. 完成当前 frozen bounded Oracle；不改预算、不重采、不追加 outcome-driven context；
2. 通过 training-only gate 后运行1轮 Label GAT engineering smoke，并在 smoke 后、
   正式训练前生成 instance-balanced training freeze；
3. 正式训练 Label GAT，运行 attribution 和 instance-balanced force-on；
4. 收集 replicated QD1/QB1 matrix，训练 Context multi-arm GAT；
5. 立即运行 calibration/heldout fresh-process；若不安全或净收益不为正则停止；
6. 只有 GAT fresh 为正后才训练 MLP、Linear 对照；
7. development E2E；
8. 正式 scale5/10/20/30/50 full20、旧 V4 safety audit；
9. 独立 instance-balanced completion audit 通过后才生成外层 candidate freeze。
