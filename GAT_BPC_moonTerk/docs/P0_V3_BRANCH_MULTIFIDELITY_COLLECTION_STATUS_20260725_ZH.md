# P0 V3 分支 GAT 多保真采集阶段报告（2026-07-25）

## 结论

当前仍不允许训练 linear/MLP/GAT，也不允许在线改变 P0 分支顺序。

本轮已经解决“每条训练监督都必须完整运行 P0、rank1、rank2 三棵
BPC 树”的采集方式问题：对 P0 已产生的合法 Ryan-Foster top-3，
可以从同一列池、同一父 branch/cut context 出发，对 SAME 和
DIFFERENT child 做匹配预算的右删失轨迹采集。

但是，真正的瓶颈已经进一步定位为：actionable fractional top-3
状态本身稀疏，而且部分实例在预算内连 exact root opportunity
判断都无法完成。多保真 child 监督降低了“已有 actionable state
之后”的成本，没有证明 actionable state 足够密集。

## 已实现接口

- `run_p0_no_task_wait_v3_branch_child_trajectory.py`
  - 一个状态固定三个 P0 合法候选；
  - 每个候选同时保留 SAME/DIFFERENT 两个 child；
  - exact child 使用事件时间；
  - incomplete child 使用右删失时间；
  - 训练语义为 survival event/censoring，不把未探索候选当负例；
  - pair 观测成本只等于两个 child wall time 之和，加实测 guidance
    生命周期开销；
  - 不产生 normalized legacy cost、四系数成本或固定 timeout penalty；
  - 每个 child 原子落盘，支持严格 binding 的断点恢复；
  - censored lower-bound 排序只作诊断，不生成强 pairwise 标签。

- `run_p0_no_task_wait_v3_branch_priority_screen.py`
  - 运行有界 no-cut root prefix；
  - 在当前 active columns 上重解 restricted RMP；
  - 只记录 restricted-pool Ryan-Foster fractionality；
  - 不能产生训练标签、exact opportunity、certificate 或自然机会率；
  - 不能永久过滤 development 实例；
  - 至少 25% development 仍按 content hash 顺序探索；
  - engine hash 必须等于活动 V3 baseline 的
    `439e12be8bf04208`。

- `run_p0_no_task_wait_v3_branch_state_oracle.py`
  - 新增严格绑定的 censored-root column warm start；
  - 只复用合法 active columns，不复用 certificate；
  - content、split、baseline、engine、timing policy 任一不一致即拒绝；
  - 分别记录增量 wall time 与包含 warm-source 成本的总采集 wall time。

## scale20/058 早期多保真结果（历史诊断，已被替代）

下列端到端结果来自早期 shortlist snapshot。它们通过了各 arm 的
exact/universe 检查，但不能与后续 fresh parent snapshot 的 child
trajectory 绑定，因此不属于当前正式训练 gold，也不进入当前
readiness。保留它们只用于说明“历史 snapshot 上存在排序
headroom”：

- P0 matched end-to-end：589.429625 秒；
- rank1：705.883329 秒；
- rank2：540.078936 秒；
- 该历史 snapshot 的 oracle 选择 rank2；
- 该历史 snapshot 中 rank2 相对 P0 净收益 49.350689 秒，
  8.3726177%；
- 三个 arm 均 exact，目标一致，universe 不变。

90 秒/child 多保真结果：

- P0-SAME：70.453135 秒 exact；
- P0-DIFFERENT：90 秒 censored；
- rank1-SAME：90 秒 censored；
- rank1-DIFFERENT：90 秒 censored；
- rank2-SAME：90 秒 censored；
- rank2-DIFFERENT：53.394497 秒 exact；
- 共得到 6 条 survival rows：2 event、4 censored；
- 没有生成不可靠的强 pairwise 标签。

截断回放：

| child horizon | 诊断 lower-bound 第一名 | 是否匹配 E2E gold |
|---:|---:|---:|
| 15 秒 | P0 | 否 |
| 30 秒 | P0 | 否 |
| 60 秒 | rank2 | 是 |
| 90 秒 | rank2 | 是 |

这组截断回放同样只属于早期 snapshot 的 horizon discovery。它曾
支持后续 child trajectory 使用60秒起步、90秒抽样审计，但不能
作为当前E2E训练标签或部署规则。当前正式20/058 fresh matched
结果见“2026-07-26 action-aligned E2E目标与新增gold”一节：
`rank0=383.066842`、`rank1=310.176477`、
`rank2=512.043199`，oracle为rank1。

## opportunity 与 priority screen 结果

无偏 fresh scale20 exact opportunity 流：

| 实例 | 240 秒预算结果 | exact actionable |
|---|---|---:|
| 058 | exact actionable | 是 |
| 005 | exact nonactionable | 否 |
| 047 | root censored | 未知 |
| 030 | root censored | 未知 |

047 后续富集流使用严格 warm start：

- 前置 censored root：240.664473 秒；
- warm root 增量 exact closure：230.132871 秒；
- P0 opportunity 节点：203.736498 秒；
- 包含前置成本总计：674.533842 秒；
- 最终为 exact nonactionable，candidate count 为 0。

30/90 秒 restricted-RMP priority screen：

| 实例 | S30 proxy count | S90 proxy count | 已知 exact opportunity |
|---|---:|---:|---|
| 058 | 3 | 3 | actionable |
| 005 | 0 | 未追加 | nonactionable |
| 047 | 3 | 0 | nonactionable |
| 030 | 0 | 241 秒末端仍为 0 | root censored |
| 043 | 0 | 未追加 | 未知 |
| 049 | 0 | 未追加 | 未知 |
| 028 | 0 | 未追加 | 未知 |
| 025 | 0 | 未追加 | 未知 |
| 052 | 0 | 未追加 | 未知 |

S30 的瞬时 top-3 有 false positive；S30/S90 persistence 在当前已知
样本上区分了 058 与 047，但样本量不足，尚不能固定进正式调度。

## 安全与审计

- legal shortlist before/after hash 相同；
- guidance filter/drop count 为 0；
- child incomplete 始终右删失，不产生 certificate；
- strong preference 只允许 exact-vs-exact 或 exact 明确击败 censored
  lower bound；
- censored-vs-censored 不生成硬偏好；
- lower-bound proxy 明确标记 `is_training_label=false`；
- full E2E gold 与 survival rows 分离；
- 所有结果仍为 `training_authorized=false`；
- V3 freeze verifier：162/162 source bundle 一致、80/80 frozen rows
  有效、issues 为空。

## 下一晋级门槛

在满足以下条件前不启动 linear ranker：

1. scale20、scale30 各至少取得 10 个独立 actionable instance-state；
2. 每个状态都有完整 top-3 × SAME/DIFFERENT 六条 survival rows；
3. 每个规模至少 5 个状态具有完整 E2E one-deviation gold；
4. 60 秒 survival/RMST 预测在 grouped validation 中稳定优于 P0
   原排序，且 E2E gold top-1 方向一致；
5. persistent S30/S90 screen 在 hash-order exploration 中没有不可接受
   的 false-negative；
6. full lifecycle 成本计入后，perfect-policy 可实现净收益置信上界为正。

如果继续收集后 actionable state 仍无法支持 grouped validation，
或 survival objective 与 E2E gold 排名不相关，应终止当前 top-3
branch-ranking 方向，而不是依靠增加网络复杂度掩盖监督稀疏。

## 2026-07-26 增量审计

### fresh scale30 筛选与 exact 反例

截至当前串行结果：

| 实例 | S30 | S90 | S90 frontier | exact opportunity |
|---|---:|---:|---|---|
| 001 | 0 | 未运行 | 未知 | 既有 600 秒 root censored |
| 058 | 0 | 未运行 | 未知 | 未运行 |
| 049 | 0 | 未运行 | 未知 | 未运行 |
| 039 | 3 | 3 | 末两轮均满额新增 32 列 | exact nonactionable |
| 008 | 3 | 3 | 末两轮新增 12/0 列 | exact 验证进行中 |

30/039 证明“持续 90 秒仍有 fractionality”本身仍会产生假阳性：
短前缀 restricted RMP 有 top-3，但 exact root-node LP 闭合后候选为
0。新增的 exact 升级条件因此同时要求：

1. S90 top-3 仍存在；
2. 最近两轮不再满额新增列，即 restricted frontier 接近饱和。

已知真阳性 20/058 满足该条件；假阳性 30/039 不满足。该规则仍只是
采集优先级，不能永久过滤实例，25% content-hash exploration 保留。

priority screen 现在可持久化 columns-only warm source，并支持
S30→增量 S60→累计 S90：

- 不复用 incomplete/exact 状态；
- 不复用 certificate；
- exact collector 会重新求解 RMP、重新定价和重新取证；
- 采集 wall time 按所有 prefix 累计。

### 正式训练目标与特征边界

新实验模块与 P0 V3 freeze 分离。P0 V3 verifier 仍为 162/162、
0 mismatch。

正式 branch objective 为：

- 每个合法 top-3 pair 分别预测 SAME、DIFFERENT child 的 4-bin
  discrete hazard；
- exact child 使用 event likelihood；
- incomplete child 使用 right-censored survival likelihood；
- pair score 等于两个 child 的预测 RMST 之和的相反数；
- E2E one-deviation gold 只用于 grouped held-out 选择和测试，不与
  survival NLL 混成一个加权标量训练成本；
- 旧 `branch_cost`、normalized cost、四系数成本和固定 timeout
  penalty 均被新 materializer 明确拒绝。

branch-specific 节点特征共 27 维，除静态任务图外加入动作前可用的：

- 当前 true RMP task dual；
- scale、memory、60 秒 target horizon 和 pricing mode；
- active SRI cut-dual 的 signed/absolute task exposure；
- 祖先 SAME/DIFFERENT Ryan-Foster degree。

pair context 为 fractionality、same fraction、log1p support count 和
child-pool normalized imbalance。pair 输入继续使用交换对称形式。

当前 collector 只对 depth=0 root 状态产生正式训练数据。深层节点缺少
node-specific column snapshot，若直接复用 root pool 会造成状态与标签
错配，因此在补齐该 snapshot 前一律拒绝深层训练 row。

### 当前 readiness

进一步检查发现，旧 20/058 child run 从 common root 的 805 列开始，
而真正分支前的 P0 root 已有 820 列。三个候选虽然 matched，但它们
共同缺少 parent node 新发现的 15 列，测到的是从较早列池重新闭合的
时间，而不是实际 branch action 后的 child time。因此下列旧统计只保留
为 diagnostic：

- 1 个 independent root state；
- 6 个 child observation；
- 1 个 60 秒内 event；
- 1 个完整 E2E gold，winner 为 rank2；
- 扣除 0.02 秒 guidance lifecycle 后 oracle net gain 为
  49.330689 秒。

对应 materialized rows 和 readiness report 已移动为带
`diagnostic_pre_parent_snapshot` / `invalidated_pre_parent_snapshot`
后缀的可恢复历史产物，不再计入正式样本。当前正式 row count 为 0。

collector V2 在六个 child 之前必须：

1. 从共同 root pool exact 重建当前 parent；
2. 重新验证 parent LP bound；
3. 验证 active cut context、cut lineage；
4. 验证重建的合法 top-3 ID 与顺序和 control 完全相同；
5. 持久化 parent active columns 与 true-RMP dual context；
6. 六个 child 全部从该 parent snapshot 开始。

正式 shadow-training gate 默认要求：

- scale20、scale30 各至少 10 个独立 root actionable instance；
- 总计至少 10 个完整 E2E gold，scale20/30 各至少 5 个；
- 至少 12 个 survival event；
- 至少 3 个扣除 lifecycle 后的正收益 gold；
- gold winner 同时覆盖 P0 与至少一个 alternative；
- 120 个 child observation 全部实际运行；
- perfect-policy net-gain bootstrap 95% 上界为正。

当前仅 oracle-headroom 上界为正，其余样本量与 winner diversity 门槛
均未通过，所以 dedicated trainer 已验证会 fail closed，尚未开始
linear、MLP 或 GAT 参数优化。

### 2026-07-26 parent primal 修复与分层 horizon 结果

exact opportunity/child collector 曾从
`raw.get("primal_columns")` 读取父 RMP primal，但 direct live-SRI
solver 的 canonical primal 位于 `raw["_master"].rmp.primal_columns`。
该遗漏导致 scale30/008 被错误写成 candidate count 0。修复后使用
原 exact parent certificate 绑定的 1287 条 active columns、4 条
SRI cuts 和相同 LP bound 做 restricted snapshot replay，得到合法
top-3：

1. `ice_site_020|ice_site_023`；
2. `ice_site_007|ice_site_019`；
3. `ice_site_027|ice_site_030`。

因此 30/008 的正式状态为 `EXACT_ACTIONABLE_ROOT`，此前
`EXACT_NONACTIONABLE_ROOT` 结论作废。snapshot replay 不重跑
pricing、不生成新 certificate，只恢复被 JSON serializer 省略的
primal rows；原 exact proof artifact 保留不覆盖。

20/058 的 fresh parent 重建还发现另一类现象：LP bound、4 条 cuts、
6 条正 primal rows、805+15 列数量均与历史 control 相同，但新定价
得到的 15 条非基列不同。P0 在 fractionality 同为 0.5 时使用整个
active pool 的 child-column balance 作 tie-break，因此 fresh top-3
可与历史 top-3 不同。正式采集语义调整为：

- 不修改冻结 P0 shortlist 规则；
- exact parent 关闭后立即冻结当次真实 top-3、active columns、primal
  和 cut context；
- 六个 child 只绑定该次 snapshot；
- 若 fresh shortlist 与历史 control 不同，survival 标签仍有效，
  但历史 E2E gold 强制失效；
- materializer 从 parent snapshot 读取 fresh candidates，不把旧
  control 候选偷换回来。

共同 60 秒 horizon 在两个状态上共得到 12 个 child observation，
全部右删失。将 20/058 提升到 90 秒后首次得到一个 exact event：
fresh rank0/SAME 在 78.341682 秒关闭。随后使用 columns-only
continuation 从 90 秒提升到 180 秒：

- exact parent 不重跑；
- 已 exact 的 child 不重跑；
- censored child 只复用列池并重新完成 pricing/certificate；
- `certificate_reused_for_pricing=false`；
- 累积时间包含此前阶段，未添加固定 timeout penalty。

20/058 的 180 秒结果为：

| fresh rank | SAME | DIFFERENT | pair exact work |
|---:|---:|---:|---:|
| 0 | 78.341682 | 173.325549 | 251.667231 |
| 1 | 148.292719 | 170.334692 | 318.647411 |
| 2 | 154.325072 | 173.927685 | 328.272757 |

六个 child 全部 exact，产生完整 listwise 顺序
`rank0 < rank1 < rank2` 和三条强 pairwise 关系。该结果证明此前长时
无正例主要由 60 秒截断和重复父求解造成，不能解释为“分支优化空间
必然不存在”。

当前正式 mixed-horizon 数据为：

- 2 个独立 root states（scale20/30 各 1）；
- 12 个完整 child observations；
- 6 个 survival events；
- 0 个与当前 snapshot 对齐的 E2E gold；
- training/deployment 均未授权；
- readiness 不终止方向，因为样本门槛尚未达到。

进一步审计确认 Native proof label queue/frontier 尚未随 columns-only
snapshot 持久化。因此分层 continuation 只能用于 horizon discovery：

- columns 和已闭合 child 可以避免重复计算；
- 纯 proof-tail child 的 queue 会从头启动；
- continuation 累计时间不是生产 solver 的 one-shot closure time；
- continuation report 禁止 materialize 为正式 survival row；
- 正式标签必须从 exact parent snapshot 做一次不间断 one-shot probe。

曾由 continuation h180 派生的 mixed-horizon materialized row/readiness
已改名为 `diagnostic_continuation_not_oneshot`，可恢复但不再进入正式
gate。materializer 已新增 fail-closed 拒绝。

E2E gold 也新增跨 arm universe binding：control、rank1、rank2 的
top-3 candidate IDs、顺序和 shortlist hash 必须完全相同。只检查
“单个 arm 内 before/after 一致”不再足够；任一 arm 漂移时
`oracle_selected_rank_index=null`，不会默认记为 P0 胜。旧 20/058
三棵 E2E tree 经新逻辑回放后 universe 确实一致，因此其历史
49.350689 秒 oracle headroom 仍有效，但不能绑定到 fresh shortlist
不同的 survival row。

scale20/058 的 180 秒 one-shot 正式复核已经完成：

| fresh rank | SAME | DIFFERENT | pair exact work |
|---:|---:|---:|---:|
| 0 | 78.053982 | 174.104327 | 252.158309 |
| 1 | 158.314604 | 124.914411 | 283.249015 |
| 2 | 107.015020 | 179.920109 | 286.955129 |

结果仍为 `rank0 < rank1 < rank2`，6/6 exact、三条强 pairwise，
且 `formal_one_shot_survival_label=true`。当前正式 one-shot 数据：

- 2 个 states（scale20/30 各 1）；
- 12 个 child observations；
- 6 个 exact events；
- 0 个与同 snapshot 对齐的 E2E gold；
- readiness 未通过且未达到终止方向的样本门槛。

scale30/008 的 rank2/SAME 单个 600 秒 one-shot horizon probe 已在
243.347139 秒 exact-safe 闭合，0 新列，确认真实 proof-tail 约 4 分钟。
正式共同 horizon 因此设为 600 秒。

首次全六 child h600 还暴露了进程级内存问题：rank0/SAME 到 600 秒
仍 censored，随后同一 Python 进程 RSS 已约 9.85 GB。数学求解器没有
越过 10 GB hard limit，但 Native allocator/cache 没有在 child 间
完全向 OS 归还内存。collector 因此新增
`--max-new-probes-per-process 1`：

- 每进程最多完成一个新 child；
- child summary 和 columns snapshot 原子落盘；
- 进程退出后由 OS 回收全部 Native memory；
- 下一进程用同一 progress binding `--resume`；
- 不复用 child certificate 或 proof frontier；
- 六个 child 的 parent、top-3、cut context 和 600 秒 horizon 不变。

linear/MLP/GAT 训练仍须等待原 readiness 数量、同 snapshot E2E gold
和 oracle-headroom 门槛。

### 2026-07-26 action-aligned E2E 目标与新增 gold

继续采集后，局部 child closure time 已被证实不能作为在线 branch
score 的主目标。三个具有同 snapshot E2E gold 的 scale20 状态均出现
局部排序与真实端到端排序不一致：

| 实例 | 两 child 局部 work 最优 | matched E2E 最优 |
|---|---:|---:|
| 024 | rank1 | rank0 |
| 048 | rank2 | rank1 |
| 058 fresh | rank0 | rank1 |

传统 strong-branching 的 child LP bound 也不能替代 E2E 标签：上述
三个状态中仅 058 命中，024 三个动作完全并列，048 明确选错。

因此正式训练接口升级为 V2：

- `branch_scores` 来自独立的 E2E score head；
- 主损失为同一 parent snapshot 内的 listwise cross-entropy 加
  expected normalized E2E regret；
- normalized regret 只表示
  `(arm_wall - oracle_wall) / P0_wall`，不再与早期四系数成本混用；
- child discrete survival NLL 仅保留为权重 0.25 的辅助任务；
- E2E gold 与 child survival 必须分别绑定到同一个 parent snapshot；
- 没有 E2E gold 时 trainer 继续 fail closed；
- 更复杂模型不能依靠 survival NLL 晋级，必须在 grouped held-out
  上至少减少 1% P0-time 的 E2E regret，各规模不退化、辅助 NLL
  恶化不超过 5%，forward p50 不超过 20 ms。

三个严格 matched post-certified-parent E2E 结果为：

| scale20 实例 | rank0 | rank1 | rank2 | gold | P0 净收益 |
|---|---:|---:|---:|---:|---:|
| 024 | 30.958656 | 37.434460 | 40.188841 | rank0 | 0 |
| 048 | 545.323183 | 543.204665 | 556.559430 | rank1 | 2.118518 |
| 058 fresh | 383.066842 | 310.176477 | 512.043199 | rank1 | 72.890365 |

所有 arm 均 exact-safe、目标一致、top-3 universe 一致，descendant
pricing/certificate 从正常路径重新运行。当前正式 materialized 数据为：

- 4 个 states：scale20 三个、scale30/008 一个；
- 24 个 child observations，20 个 exact events；
- 3 个完整同 snapshot E2E gold；
- gold winner 为 rank0 一个、rank1 两个；
- 扣除每次 0.02 秒 guidance 生命周期成本后，perfect-policy
  mean gain 为 24.982961 秒，bootstrap 95% CI 为
  `[-0.02, 72.870365]`；
- oracle-headroom 上界为正，但 readiness 数量门槛仍未达到，
  training 仍未授权。

### scale20/30 全开发池 priority census

严格锁定的 48 个 development 实例由每规模 12 个
`UNBIASED_OPPORTUNITY_CENSUS` 和 36 个
`BOUNDED_ACTIONABILITY_DISCOVERY` 组成。calibration 仍未读取。

完成全部 48+48 个 cut-aware S30 screen 后：

- scale20 有 8 个优先升级命中：037、059、048、024、001、013、
  021、004；另有早期 schema 已知 exact actionable 的 058；
- scale30 有 017、033、028 三个新命中，另有已知 008；
- 这些比例不能解释为自然发生率，因为 36/48 本来就是有界
  discovery；只有最初 12 个 hash-order rows 可用于无偏机会描述；
- screen 仍只是调度信号，exact collector 已观察到 false positive，
  不产生训练标签也不永久过滤实例。

exact 升级新增确认：

- scale20/048 parent exact，六个 h180 child 均 exact；
- scale20/024 parent exact，六个 h180 child 均 exact；
- scale30/017 parent 在 3600 秒预算内 exact actionable；
- scale30/017 的前三个 h600 child 全部在 600 秒右删失。

由于 survival 已降为辅助目标，scale30/017 不再继续把后三个 child
各运行 600 秒；改采统一 h60 censoring row，把主要预算投入 matched
E2E counterfactual。h600 产物保留为诊断，不混入 h60 正式 row。

### 深层 actionable snapshot 加速

只采 root 状态会同时造成样本稀疏和 node-phase 偏置。现有三个
scale20 P0 control arms 中实际包含：

- 024：1 个 actionable（root）；
- 048：root 加 depth1、depth2，共 3 个；
- 058 fresh：root 加 depth1，共 2 个。

因此新增 development-only deep snapshot 接口：

1. P0 exact tree 在每个已认证、合法 top-3 的 branch node，分支动作前
   原子保存 target node、全局 column pool、cut/lineage、incumbent、
   processed nodes、尚未处理 queue 和 next node ID；
2. counterfactual arm 复用的仅是动作前已认证 prefix；
3. target 之后的所有 pricing/certificate 仍从正常 exact 路径运行；
4. rank0/rank1/rank2 使用相同 prefix、相同 open queue 和相同合法
   shortlist，只改变 target node 的排序选择；
5. 任一 content/split/solver/column/cut/universe hash 不一致即拒绝。

这使一次昂贵 P0 exact tree 能提供多个独立的 decision-state gold，
但同一实例的多个状态在 split、bootstrap 和采样权重中仍必须 grouped
到同一个 instance，不能伪装成独立实例扩大统计量。

### 冻结基准与反事实实验代码的物理隔离

深层 snapshot 需要扩展 tree continuation 接口，但不能修改已经登记的
P0 V3 control。为此，反事实实现已经迁移到
`guidance/branch_counterfactual_tree_solver.py`：

- frozen `branch_tree_solver.py` 和 frozen oracle test 保持登记字节；
- exact backend、旧 P0 V3 freeze 和 production `no_cut` 均不改；
- 只有 development-only state/E2E oracle 显式导入实验模块；
- 每次结构变更后运行 freeze verifier，目前为 162/162 source
  bundle 一致、0 mismatch；
- 实验模块生成的 deep snapshot 仍绑定 baseline ID、engine hash、
  content hash、cut/lineage、column pool 和合法 shortlist universe。

因此新增功能不是“悄悄改变基准后复用旧结果”，而是在不变 control
旁边运行可审计的 counterfactual continuation。

### 独立实例数量上限与预注册扩容

原 development pool 每规模只有 48 例，且 scale30 的 cut-aware S30
命中仅 4 例。即使把已有 P0 tree 的所有深层状态都采完，也只能增加
state 数，不能达到 readiness 所要求的每规模至少 10 个独立
instances。因此在读取任何新实例的 screen/label 之前，新增一批 IID
候选并冻结分区：

- scale20、scale30 各生成 60 个 accepted 实例；
- 每规模 content-hash 前 12 个标为
  `UNBIASED_EXPANSION_CENSUS`，其余 48 个标为
  `BOUNDED_ACTIONABILITY_DISCOVERY_EXPANSION`；
- 原 development 48 例和 calibration 12 例逐行原样保留；
- 扩展后 development 为每规模 108 例，calibration 仍为每规模
  12 例且不可读；
- 五折按 content hash 和结构属性重新冻结，fold 大小为
  44/43/43/43/43，未使用任何 branch label；
- 新旧 content hash、instance ID 均零冲突，protected test 未读取。

扩展 S30 census 使用可恢复的单进程调度器，先交错完成两个规模的
12+12 个无偏 census，再交错 discovery。所有 120 个预注册实例最终
都会被 screen；screen 只决定昂贵 exact collection 的先后次序，
不形成训练标签，也不永久丢弃 screen-negative。

加入 scale30/017 的统一 h60 auxiliary row 后，当前正式 survival
材料为 5 个 states、5 个 instances、30 个 child observations 和
20 个 exact events；完整 matched E2E gold 仍只有上述 3 个 scale20
状态，因此 readiness 继续为 false。

### 2026-07-26 deep replay 与训练前接口复核

scale30/017 的 rank0 control 首次在真实运行中生成了一个 depth-1
snapshot。该状态在写出时已经：

- 使用 true-dual exhaustive certificate 关闭 node LP；
- 保持 legal top-3 before/after universe hash 一致且 drop count 为0；
- 绑定 1053 个全局列、24 个 target-active 列；
- 绑定已处理的1个prefix node和另一个尚未处理的open node；
- 记录decision-time incumbent 1.418612和node bound 1.401327。

独立的deep E2E runner以零arm预算完成全量binding校验；child
trajectory adapter也以零pricing call恢复出相同的三个候选对。因此
root E2E、deep E2E和auxiliary survival现在使用同一个decision-state
定义。

复核同时发现并修正三个实现问题：

1. tree node与standalone child probe的branch/cut audit字段命名不同，
   原validator会误拒绝合法tree snapshot；现在通过相同数学条件统一
   验证，显式失败字段仍然fail closed；
2. deep E2E runner曾把`max-new-arms=0`解释成unlimited；现已固定为
   validation-only。误启动的重复进程在53秒时定向SIGTERM，未写出
   arm、未进入数据；
3. materializer虽然允许deep snapshot，旧row validator却只接受
   root phase；现仅接受来源为`exact_p0_deep_parent_snapshot`的
   deep row，任何root-pool伪重建deep row继续拒绝。

训练feature升级到V2，除static graph、true dual、cut和parent branch
degree外，增加仅在动作发生前可知的：

- `log1p(depth)`；
- normalized incumbent gap和incumbent-available indicator；
- processed/open node counts；
- global column count。

现有5条正式记录已在扩展后的grouped split上重新物化，feature维数
为33，gold/event/headroom统计与V1完全一致。trainer新增：

- E2E primary与survival auxiliary各自的encoder gradient norm；
- encoder gradient cosine；
- 各epoch、各fold的validation conflict连续计数；
- 只有连续3次validation cosine低于-0.2才从下一epoch启用PCGrad。

这些变化不授权提前训练；feature V2 readiness仍为false。

### scale30 matched E2E删失语义

scale30/017的root rank0在3604.934714秒结束时仍未关闭整棵树：

- root和`node_001`已经exact certified并发生合法分支；
- `node_002`运行2204.433892秒后right-censored；
- tree保留incumbent 1.418612和global lower bound 1.400912；
- 结果为legal incomplete，不能把3600秒预算当作真实branch cost。

为避免这种昂贵轨迹完全丢失，同时不制造timeout罚项，E2E supervision
增加严格pairwise censoring规则：

1. 两个arm均exact且最终objective一致时，可按真实wall time比较；
2. 一个arm exact，且其closure time严格早于另一个arm的observed
   censor horizon时，可形成`exact winner > censored loser`；
3. 两个arm均censored、exact arm晚于对方censor、未运行arm或
   universe/parent binding不一致时，不形成任何偏好；
4. 未探索arm永远不作为负样本；
5. partial pairwise只补充E2E score head训练，不能代替完整gold，
   也不计入oracle-headroom/readiness的gold门槛。

trainer对该标签使用pairwise logistic loss，并单独报告held-out
trusted-censored pairwise accuracy；模型晋级仍只由完整matched E2E
regret及其统计门槛决定。

root rank2随后在3581.258953秒exact-safe关闭：

- 选择原P0 shortlist的rank2，即
  `branch_pair:ice_site_005|ice_site_013`；
- final objective与global lower bound均为1.401924；
- incomplete node为0，未复用任何descendant certificate；
- legal shortlist before/after hash与rank0完全一致；
- 相比rank0的3604.934714秒observed censor horizon，至少提前
  23.675761秒完成exact closure。

因此该状态产生一条可信
`rank2 > rank0 / EXACT_BEFORE_OTHER_CENSOR_HORIZON`偏好。由于rank0
仍是incomplete且rank1尚未运行，它继续不是完整gold：
`oracle_selected_rank_index`、`oracle_net_gain_sec`均保持null。
materializer重新检查原始arm后，当前正式V2材料增加为1个scale30
trusted-censored pairwise state，但完整gold仍为3，readiness仍为
false。

成本实现的再次复核还发现：冻结P0 V2公共训练模块仍包含历史四系数
`branch_cost`。当前P0 V3 branch路径现已把right-censored survival
likelihood放在独立的`guidance/survival_losses.py`，并由
`branch_survival.py`直接导入；旧模块保留原始字节，仅服务历史回放。
freeze verifier曾准确拒绝一次对旧模块注释/导出的无害改动，恢复原始
字节后重新达到162/162、0 mismatch、valid=true。

### 2026-07-26 跨生成器止损门与深层合成样本终止

进一步核对发现，当前扩展候选池来自
`synthetic_polar_resource_grid_v1`，而冻结full80 scale30来自
`real_lunar_south_pole_sp50_benchmark_v1`。两者不是同一数据分布。
因此上述合成实例上的headroom只能证明合成域存在局部机会，不能授权
面向正式real-map基准的模型训练或GAT复杂度扩展。

训练前流程改为以下不可跳过的顺序：

1. 先在fresh、与full80零content-hash重叠的real-map 20/30小样本上
   收集matched E2E；
2. 每规模至少3个development instances、2个完整gold，且至少一个
   正收益；达到样本门槛后若完美策略净收益95%置信上界不大于0，
   立即终止branch-ranking方向；
3. headroom通过后只授权real-only linear pilot；
4. 合成域gold自然充足时，才额外比较synthetic-only zero-shot、
   synthetic pretrain到real fine-tune和domain-balanced joint；
5. 合成数据只有在相对real-only的real-map held-out改善最坏规模
   95%置信下界不小于0时才能保留；
6. linear在real-map上必须严格快于P0、每规模/每generator domain
   不退化且最坏规模置信下界不小于0，才授权下一层MLP；
7. 每次只能增加一个复杂度rung，必须提交上一层绑定相同records、
   split、readiness和training regime的授权报告，禁止一次性训练
   linear、MLP和全部GAT后再挑结果。

pilot report现在保存每条输入row的content hash、path hash和完整
canonical row SHA256。后续扩容可以增加row，但任何pilot row缺失或
改变都会使readiness fail closed，不能复用旧授权。normalization和
训练权重按generator domain、scale、instance、state逐层等权，避免
合成域的大量states压过少量real-map状态。

scale30/017 deep rank0 continuation最终运行3489.393804秒，扩展3个
节点后触发Native 10240 MiB硬内存门，保留objective 1.414878和
global lower bound 1.401327。结果为legal incomplete：

- exact-safe=false；
- incomplete node=4；
- universe hash一致且filter count为0；
- 没有no-negative/optimal certificate泄漏；
- 只有rank0 observed，rank1/rank2未运行，因此没有gold或可信
  pairwise preference。

该实例既属于合成域，又已表现出单arm约一小时、10 GiB仍无法闭合。
按照跨域止损原则，不再为它追加deep rank2/rank1。当前正式记录重新
物化后仍为5 states、3个完整scale20 gold、1个scale30 root删失偏好；
新增generator-domain门使training继续为false。

fresh real-map首批又从原计划每规模8例收缩为每规模4例：content-hash
排序后3例进入development、1例进入锁定calibration。该最小批正好能
回答headroom门槛；只有它通过，才扩成6+2或进入linear。这样避免先
生成、筛选和求解大量图，最后才发现目标域本身没有可学习收益。

headroom的统计分母也从“已经命中actionable top-3的状态”改成全部
预注册且exact-screened的real-map development实例：

- `EXACT_NONACTIONABLE`实例以零收益计入，不能从分母删除；
- `EXACT_ACTIONABLE`实例必须存在同content hash的完整matched E2E
  gold，否则只授权补gold，不允许训练或扩模型；
- censored/infrastructure-failed screen不伪装成nonactionable；
- 首批每规模3例exact screen后若没有任何正信号或置信上界不大于0，
  直接终止；
- 若有正信号但每规模不足2个gold，只允许一次有界扩容到最多6个
  development实例/规模；
- 达到6例上限仍不能满足gold密度门槛，按标签机会密度过低终止，
  不继续无限寻找正例。

opportunity census新增显式`instance_generator_domain`过滤，fresh
real-map试点不会再因为combined manifest中合成实例更多而错误地先
运行合成域。census、records和grouped split的hash必须互相一致。

为避免headroom尚未证明时先花费六个child probes、构图和辅助标签
预算，训练准备又拆成两个物理阶段：

1. `branch_target_headroom_gate.v1`只读取precommitted census和三个
   matched E2E arm的安全摘要，不需要child trajectory或GAT tensor；
2. 只有该门通过，才授权为相同content/path收集formal feature和
   censored child-survival auxiliary；
3. formal row中的gold rank、三臂wall和net gain必须与早期headroom
   report的label SHA256逐项一致；
4. 然后才允许real-only linear cross-validation。

因此最昂贵的六child辅助采集已从“证明方向可行之前”移到“目标域
E2E headroom已经通过之后”。早期门本身仍明确
`linear_training_authorized=false`和`gat_training_authorized=false`。

### 2026-07-26 fresh real-map 有界扩样最终结论

首批real-map每规模3个development的exact census结果为：

- scale20：1个`EXACT_ACTIONABLE`、2个`EXACT_NONACTIONABLE`；
- scale30：0个`EXACT_ACTIONABLE`、3个`EXACT_NONACTIONABLE`。

唯一scale20动作完成matched rank0/1/2：

- P0 control raw wall为3.834803秒；
- 对所有guided action统一计入0.02秒生命周期成本后，rank0/1/2
  分别为3.854803、37.261259、3.138586秒；
- rank2为gold，完美策略净收益为0.696217秒。

由于置信上界仍为正但每规模不足2个gold，gate只批准一次扩展到
6个development/规模。扩展时旧development和calibration成员逐个
保持不变；新增实例先按content hash盲分配3个development和1个锁定
calibration，旧split hash通过显式祖先授权链只读复用。

扩展后的12个冻结development结果为：

- 9个`EXACT_NONACTIONABLE`；
- 2个完整`EXACT_ACTIONABLE`，scale20/30各1个；
- 1个scale20难例root在337.843656秒exact并出现top-3，但P0控制树
  在额外300.245797秒后仍未闭合，严格保留为`TREE_CENSORED`。

新增scale30动作的matched E2E三臂全部exact、objective均为1.608027：

- P0 control raw wall为44.190635秒；
- canonical guided rank0/1/2 wall为44.210635、775.551566、
  26.627491秒；
- rank2为gold，净收益17.563144秒；
- rank1相对P0灾难性变慢，说明错误排序的风险远大于0.02秒推理成本。

统计分母包含所有exact nonactionable零收益实例；不把censored当零，
也不删除。11个可判定实例的完美策略跨规模等权均值为
1.533217033秒，cluster bootstrap 95%区间为[0, 4.4604077]。它证明
局部oracle headroom真实存在，但可训练机会密度仍不足：

- 每规模只有1个完整gold，低于预注册的2个/规模；
- 12实例上限已经达到；
- 所有已观察actionable均已完成gold；
- calibration和protected final test均未读取。

因此最终reason code为
`TARGET_CAP_REACHED_WITH_INSUFFICIENT_EVALUABLE_GOLD`：

- `terminate_target_direction=true`；
- `formal_feature_aux_collection_authorized=false`；
- `linear_training_authorized=false`；
- `gat_training_authorized=false`；
- `deployment_authorized=false`。

该结论终止的是“仅对P0合法Ryan-Foster top-3做学习排序”的当前
训练路线，不否定两个局部oracle正例本身。按照止损契约，不允许用
合成域、大模型或继续寻找正例来掩盖目标域监督密度不足，也不进入
linear、MLP或GAT训练。

本轮同时统一了E2E成本语义：
`p0_control_raw_wall_vs_all_guided_actions_uniform_lifecycle_overhead.v1`。
P0 control不承担guidance成本；所有模型动作包括选择rank0均承担同一
生命周期成本。runner已计入的替代臂成本先还原raw wall，再统一加
成本，禁止二次扣减。formal row、loss归一化、评估和headroom label
hash均复用该语义；历史四系数`branch_cost`继续被新row validator
显式拒绝。

### 2026-07-26 tail-selective one-shot GAT 落点验证

在直接top-3训练路线终止后，另行冻结了一个不复用其训练授权的新
落点：

`确定性尾部触发器 + 可弃权小GAT + P0合法top-3一次性排序`。

触发器固定为
`first_exact_legal_top3_elapsed_per_task_ge_1s.v1`，只允许读取
动作发生前已经存在的：

- exact node LP和true-dual pricing certificate状态；
- 合法shortlist before/after hash；
- candidate count；
- root wall加当前tree elapsed；
- scale；
- 本实例是否已经消费过一次调用。

触发条件为exact合法top-3且
`event_elapsed_sec / scale >= 1.0`。每个实例最多触发一次。触发前
模块不导入Torch、不加载checkpoint、不构图；shortlist缺失、hash
不一致、pair/filter drop非零或P0 control没有选择rank0均直接bypass。

可弃权语义也计入完整成本：模型已经运行后选择`ABSTAIN_TO_P0`仍
承担guidance lifecycle overhead，不能把弃权写成零成本。完整
selective action set为：

`ABSTAIN_TO_P0、guided rank0、guided rank1、guided rank2`。

此前已经有反事实标签的12个real-map development仅作为
`DESIGN_ONLY`审计，不作为fresh验证或训练数据。11个可判定实例中：

- scale20触发0/5，弱正例因低于固定尾部阈值被pre-import bypass；
- scale30触发1/6，命中已有强正例，selective oracle净省
  17.563144秒；
- 跨规模等权净收益均值1.463595333秒，bootstrap 95%区间
  [0, 4.390786]；
- 按命中率推算，scale30约需120个实例才能获得20个独立触发gold，
  scale20无法估计。

因此design evidence只授权一个fresh小样本，不授权特征、linear或
GAT训练。

fresh池随后使用相同real-map生成器独立生成每规模4例。内容哈希排序
后每规模3例进入development、1例进入锁定calibration；与此前
prior/protected共616个内容哈希零重叠，分区未使用任何tail或反事实
标签。grouped split hash为
`25e49533ae35412f5e4bf7f457fa2d0f887877ad4e1a2866f92a11f9bf0bd344`。

fresh root census的6个development全部在预算内exact完成：

- scale20：3/3为`NO_FRACTIONAL_BRANCH_CANDIDATE`；
- scale30：3/3为`NO_FRACTIONAL_BRANCH_CANDIDATE`；
- tail trigger count为0/6；
- matched E2E三臂调用数为0；
- selective oracle净收益均值和bootstrap区间均为0。

这些实例不是因为tail阈值过高而被过滤，而是P0没有产生合法
Ryan-Foster候选，因而不存在可供一次性GAT排序的动作。降低阈值、
扩大网络或改变abstention threshold均不能修复候选宇宙为空。

fresh gate最终给出：

- reason code：`FRESH_EXACT_PILOT_ZERO_TAIL_TRIGGER`；
- `terminate_tail_selective_landing=true`；
- `bounded_fresh_expansion_authorized=false`；
- `matched_e2e_collection_authorized=false`；
- `tail_selective_landing_validated=false`；
- formal feature、linear、GAT和deployment全部false。

因此该tail-selective top-3落点也按预注册止损终止，不再生成更多
实例、采集反事实或训练模型。结论不否定“尾部条件调用”和“可弃权”
机制本身；它否定的是把二者绑定到当前P0 Ryan-Foster top-3候选宇宙
后，目标域能提供足够动作和监督这一前提。
