# P0V4 精简优化实现交接（2026-07-29）

## 1. 边界

- `runs/frozen_native_live_sri_p0_memory_compact_baseline_v4_20260729/`
  未被修改。
- production `no_cut` 默认未切换。
- negative escape、batch admission 和 one-deviation GAT 默认全部关闭。
- GAT 只允许改变一次 root admission 边界；不参与合法性、reduced
  cost、bound、pruning 或 certificate。

## 2. 已实现的 Exact 路径

Native exact pricer 支持固定的 `E_K=(K,4K)`：

- `exact_negative_escape_enabled`；
- `exact_admission_batch_size`；
- `exact_raw_negative_pool_size`；
- `exact_negative_escape_policy_id`。

达到 raw pool 上限时返回 `FOUND_NEGATIVE_PARTIAL`，并强制
`can_certify_no_negative=false`。TIMEOUT、MEMORY_LIMIT 和
FRONTIER_LIMIT 仍然 fail closed。搜索空间先穷尽时保留 P0V4 exact
closure。Python 只在 escape 显式启用时调用冻结的 P0V4 diversity
selector；escape 关闭时保留原 Native exact 候选和顺序。

若 escape 返回的候选经 pool/view/branch/cut/addability 审计后为零，
final judge 会用剩余 wall clock 关闭 escape 并重跑 exhaustive proof。
不足 K 但存在 addable columns 时直接返回现有列，不签发证书。
`native_raw_unique_negative_count` 单独记录 Native 达到的 \(4K\) 触发量，
`audited_raw_unique_negative_count` 记录 Python true-RC/branch/cut 复算后
仍合规的数量，避免后者覆盖前者并造成固定 K 证据歧义。

ColumnPool 新增有序 `add_many`，MasterColumnView 新增跨 pool/view 的
原子 `admit_many_atomically`。批量路径先在 scratch pool 和 scratch
view 上逐项复现 P0V4 的 membership、重复、replacement 与 active-set
决策，再一次提交；RMP 只在 batch admission 完成后进入下一次
rebuild/solve。计时拆分为 true-RC audit、diversity selection、
pool/view admission、RMP assembly 和 LP solve；每个 CG round
持久化 batch 的 input、branch-feasible、pool-new、activated 数量及
view/total wall，避免这些计时只存在于临时 harvest payload。

## 3. 固定 E_K 实验

配置：

- `configs/experiments/p0v4_diverse_negative_escape_oracle_v1.yaml`

执行器：

- `scripts/run_p0v4_diverse_escape_oracle.py`

`prepare` 会核验 P0V4 freeze 并生成 E64/E128/E256 独立配置。
`collect-snapshots` 用当前候选 engine、全部新功能关闭的 P0V4 no-op
配置运行 scale50/001，并按 source final-judge wall time 自动冻结 4 个
heavy 与 12 个 ordinary 唯一 mathematical contexts；路径、snapshot、
binding、config、engine 和 source result 均以 SHA256 固定。
`snapshot` 以 P0V4/E64/E128/E256、3 个 blocked replicates、fresh
process 串行重放，支持 hash-checked resume。正式 summary v2 在允许
fixed-K development/selection 前严格核验 192 个
`(arm, snapshot, replicate)` tuple 无缺失、重复或额外行，blocked
轮转位置和 snapshot role 正确，snapshot 文件哈希与逻辑哈希分别绑定，
同一 snapshot 的数学 source binding 跨 arm/replicate 一致，Native
engine hash 全局一致，并逐 arm 核验 `K/4K`、partial-return、frontier
与 certificate blocker 的 fail-closed 契约；任何一项不满足都会令
`downstream_fixed_k_selection_authorized=false`。`development` 只有在该
严格 summary v2 为 PASS 后才可启动；它按实例分块串行运行 P0V4
control 与 E64/E128/E256，并随实例轮转 block 的起始 arm，避免最长约
40 小时实验中的 arm-major 时间漂移。resume 同时绑定 instance、
arm-config 和 result-state 文件哈希以及 block 位置，不会只凭 instance
名称复用旧结果。10 个独立 scale50 development instances 会自动记录
process tree RSS、natural route-opportunity
snapshots 和结果状态。该 corpus 由
`scripts/generate_p0v4_fixed_k_gat_development_instances.py` 在任何
算法 outcome 产生前冻结，scale30/50 各 10 例、content hash 全唯一，
且与官方评测 corpus 重叠为零。`summarize`
从持久化 state/probe 自动计算六项预注册指标，不需要手工制作
`oracle_metrics.json`。`select` 要求 snapshot control/arm 完整、零
redline 和 10 个开发实例，选择唯一固定 K；exact 少于 7/10 时只输出
bidirectional feasibility fallback 触发状态，不会自动同时启动其他
算法。固定 K 仅用于 scale50；scale30 继续使用 P0V4 的 64 列 admission。
E256 会显式关闭 P0V4 的 late adaptive harvest schedule，防止请求的
K=256 在 active pool 增大后被静默缩为 128；resume 会逐轮核验 effective
K、Native \(4K\)、audited \(\ge K\)、selected \(=K\) 和 certificate
blocker。development 的 `--dry-run` 只写
`development_stage_dry_run_rows.json`，不会污染正式 ledger。

示例：

```bash
/home/kai/miniconda3/bin/python \
  scripts/run_p0v4_diverse_escape_oracle.py \
  --stage prepare \
  --output-dir runs/p0v4_diverse_negative_escape_oracle_v2
```

## 4. One-deviation GAT

Opportunity census：

```bash
/home/kai/miniconda3/bin/python \
  scripts/run_p0v4_route_opportunity_census.py \
  --snapshot-root <post-E_K snapshot root> \
  --snapshot-root <另一自然采集 root，可重复> \
  --fixed-k-selection <fixed_k_selection.json> \
  --output-dir <census output>
```

它要求 scale30/50 各至少 20 个 eligible contexts、各至少 5 个实例、
至少 8 个 omitted candidates，并要求剩余 matched budget 分别达到
120/300 秒。不会延长 Native 搜索制造机会。同一 `snapshot_hash`
即使被复制到多个 run/path 也只计一个 context；预算不足、非 root、
审计不完整或 omitted 不足的 snapshot 不生成 action manifest。
eligible snapshot 索引、实例级 train/calibration split、fixed-K hash
和每个 source snapshot SHA256 统一写入
`census_content_binding_hash`。suite、单 context runner 和最终 auditor
都会重新计算该 binding，不接受只修改外层字段的旧 census/action 文件。

scale30 自然机会采集入口：

```bash
/home/kai/miniconda3/bin/python \
  scripts/collect_p0v4_route_opportunities.py \
  --fixed-k-selection <fixed_k_selection.json> \
  --scales 30 \
  --limit-per-scale 5 \
  --output-dir <opportunity collection>
```

scale50 的 natural snapshots 在 fixed-K 开发运行中同步记录；census
只读取最终被选中 arm 的目录。instance split 在任何 rollout outcome
产生前，按 scale 分层冻结为 train/calibration，保证实例级不交叉。
正式 official scale50/002--020 因而不参与 K 选择、GAT 训练或
calibration；scale50/001 仅按预注册计划用于 proof-snapshot screen，
最终结果需重新运行并明确其非 held-out 角色。

Oracle context 强制绑定 active columns、RMP basis、true dual、
branch/cut、worker、queue、cache、thread、binary/config/engine 和 fixed
K 的 hash。每个 context 必须有 3 个 blocked replicates、一个 no-op
和至少两个 promotion arms，最多跟踪 3 个 CG rounds。未达到 milestone
的 arm 保持 censored，不强制标为负样本。若同一 action 的 3 个
replicates 中只有一部分达到 milestone，该 action 不进入 probability
head 或 positive-magnitude head 的确定标签，也不能作为 oracle gate
的已观测正收益；其删失延迟仍进入 survival-aware loss。只有 3/3
uncensored 的 action 才能贡献确定的 action-level 正负标签。

Native 的 \(4K\) raw pool 不再被误缩成 final judge 返回的 \(K\) 条后
才进入机会统计。labeling pricer 会完整审计全部 raw routes 和
signature，但只读旁路只物化冻结 P0V4 selector 的前 \(K+32\) 条——
这正是唯一允许的 intervention universe，避免为了模型永远不能选择的
rank 继续做额外 greedy ordering。Exact admission 仍只接收原有前
\(K\) 条。solver 用 observation-only addability 审计在 Master 更新前
重建合法边界，按真实 P0 admission 顺序放置前 \(K\) 条，其余 32 条
保持冻结 selector 顺序。该旁路不向 ColumnPool、MasterColumnView 或
RMP 写入任何 omitted route，并已用随机前缀差分和 pool 不变性测试覆盖。

正式部署也显式使用同一完整审计后的 \(K+32\) order。acceptance runner 只在
候选配置绑定了已授权 deployment manifest 时设置 one-deviation
runtime；solver 先保存真实 Exact 前 \(K\) 的 candidate IDs，再在完整
pool 上重做只读 addability 审计，并把这 \(K\) 条强制设为 no-op 前缀。
模型只能让 rank \(K+1\ldots K+32\) 中的一条替换 rank \(K\)，且正式
deployment rank-offset scope 被进一步冻结为所有 calibration contexts
都真实 rollout 覆盖过的 offset 交集；未被校准的 rank 不参与最大分
选择。低置信、OOD、hash 失败、memory adverse 或已干预 root 都返回
原前 \(K\)；这条 full-pool wrapper 关闭时完全不进入 Exact-only 热路径。

训练数据继续携带 oracle context 的 exact binary/config/engine hash。
deployment manifest 冻结训练所见的 engine/binary allowlist、fixed-K
hash、允许规模（当前只可能是 30/50）、runtime policy ID 和
feature-schema hash；正式 runtime 在推理前逐项核对当前 Native
engine/binary/config、模型 checkpoint、fixed K、规模、校准 rank
scope、特征维度/语义和 OOD envelope。输入 hash 覆盖实际送入模型的
node/edge features、edge index、candidate task masks/context 和 global
context，而不是只覆盖部分张量。acceptance runner 对 allowlist 外的
scale 根本不注入模型 manifest，scale5/10/20/100 的正式安全复验因此
走零推理、零 full-pool 旁路的 Exact no-op。

Oracle 包审计：

```bash
/home/kai/miniconda3/bin/python \
  scripts/audit_p0v4_one_deviation_oracle.py \
  --rollout-root <matched rollout packages> \
  --opportunity-census <opportunity_census.json> \
  --fixed-k-selection <fixed_k_selection.json> \
  --output-dir <oracle output>
```

真实 matched rollout 由以下两层执行器产生，而不是要求人工构造包：

```bash
/home/kai/miniconda3/bin/python \
  scripts/run_p0v4_one_deviation_oracle_suite.py \
  --action-manifest-root <census/action_manifests> \
  --opportunity-census <opportunity_census.json> \
  --fixed-k-selection <fixed_k_selection.json> \
  --instance-root data/p0v4_fixed_k_gat_development_v1/scale_030 \
  --instance-root data/p0v4_fixed_k_gat_development_v1/scale_050 \
  --output-dir <rollout suite> \
  --resume
```

suite 串行启动 context runner；context runner 将 no-op 与 promotion arm
按 blocked replicate 轮换顺序，每个 arm 使用 fresh process。P0V4
没有跨 CG round 保留 HiGHS basis，因此 replay 明确绑定 ordered active
column matrix 和“deterministic cold rebuild”basis state，不虚构 warm
basis。worker/source-frontier/cache/thread 的 source state 与 fresh-arm
重建语义均被独立 hash；当前 Native engine、source exact config、线程、
instance、scale、fixed K 与 matched budget 任一不符即拒绝运行。每个
root 仅首轮可替换 rank K，后续 round 的 one-deviation runtime 关闭并
恢复 Exact P0 顺序。昂贵 arm 启动前必须同时存在与 snapshot 相邻的
pre-action harvest features；package、selected-action manifest、
source snapshot、census 和 fixed-K 的 SHA256/content binding 在最终
auditor 中重新核验。重复 context package 不会重复增加 oracle 样本数。

只有 instance-bootstrap 的 gain LCB、positive-context LCB、context/
instance 数量和全部 redline 同时通过，才生成
`gat_training_authorized=true`。

训练器只构建一个 two-head GAT：

```bash
/home/kai/miniconda3/bin/python \
  scripts/train_p0v4_one_deviation_gat.py \
  --dataset <one_deviation_dataset.jsonl> \
  --oracle-gate <oracle_gate.json> \
  --fixed-k-selection <fixed_k_selection.json> \
  --output-dir <model output>
```

训练器检查 instance-disjoint split、context hash 唯一性、fixed-K
SHA256、pre-action feature hash 和 post-action leakage。calibration
不是把同一 context 的所有过阈值候选都当独立安全样本，而是复现正式
部署的 max-score winner，再使用 Wilson bound：harmful promotion rate
的 95% 上界不超过 5%，beneficial precision 的 95% 下界至少 80%。
memory-adverse action 即使 milestone 被删失也作为 harmful；普通
right-censored action 不写入负类 BCE，也不会从安全校准中静默消失，
而以 unknown winner 阻断相应阈值，并以相对 observed P0 milestone 的
delay lower bound 进入 hurdle likelihood。任一 hash、OOD、memory
adverse event、校准或模型校验失败均回退 no-op。运行时用线程安全
ledger 保证每个 root 最多一次；Native memory pressure/host memory
kill 会自动触发 no-op veto。p99 以 warmed cached model 的
tensorization + CPU forward 测量。

## 5. 正式验收与独立冻结

正式验收配置和执行器为：

- `configs/experiments/p0v4_final_acceptance_v1.yaml`；
- `scripts/run_p0v4_final_acceptance.py`。

执行器在 fixed K 未通过或 GAT deployment manifest 未获授权时分别
fail closed。它把代表例、Exact small30、scale50/002--020 held-out、
最终重跑 scale50/001、GAT 配对正式集和 scale100/001--005 诊断拆成
可恢复 stage；scale50/100 始终单进程。scale50 即使部分实例在 3600
秒 fail closed，只要全部 state 已持久化，stage 仍允许进入汇总，由
预注册的 14/20、13/19 等门槛判断，而不会把 runner 的“非全 exact”
退出码误当成数据缺失。

prepare 会额外物化并哈希绑定五个论文消融配置：P0V4、仅 batch
admission、仅 diverse negative escape、escape+batch，以及
escape+batch+one-deviation GAT。bidirectional 只有实际触发 fallback
时才加入。scale100 阶段按 P0V4 与最终候选配对运行；最终候选在
scale100 因 allowlist 外安全回退而不执行 GAT inference。

`summarize` 自动核验各规模 exact 数、P0V4 配对几何均值、20/30 与
5--30 合并加速、全部 redline、GAT exact 不退化、GAT 增量收益和
inference p99。只有所有正式 100 例 Exact 与 100 例 GAT 结果齐全且
scale100 的 5 组 P0V4/最终候选配对诊断也完整、全部正式门槛通过，
`freeze` 才能创建新的独立
`frozen_final_candidate/`；P0V4、P0V3 和 production `no_cut` 都不被
覆盖。

## 6. 当前尚未形成的证据

- 当前源码和当前 Native binding 在三个新功能全部关闭时完成了
  scale5/10/20 full20 兼容性复验：三个规模均 20/20 exact，
  fail-closed 和全部 correctness/certificate redline 均为零。该结果是
  新代码对 P0V4 no-op 语义的兼容性证据，不替代 frozen capsule 的历史
  性能证据。
- snapshot/development 门、raw/audited telemetry、formal/dry-run
  ledger 隔离、五个论文消融配置、500 组原子 batch differential、
  fixed-horizon oracle metric、GAT winner calibration、census
  去重/content binding 和 partial-censor 标签补强后的 P0V4 定向回归
  为 47/47，与既有 route-admission 兼容回归合计 50/50；Native Python
  回归为 61/61、
  28 个 subtests，Native CTest 为 2/2。此前 141/24 和 197/29
  属于继续补强前的源码，不能替代当前结果。
- 第一轮 source 采集曾得到 4 heavy + 2 ordinary，但审计发现采集器
  错把两类都限定为 `exact_proof`；这不是预注册协议失败。该旧 run
  原样保留为无效采集诊断，没有进入 arm 比较。
- 修正后在独立 v2 run 中重新执行同一 P0V4 scale50/001 自然轨迹：
  3596.14 秒、95 个 CG rounds、加入 11297 列，最终为
  `BPC_INCOMPLETE_PRICING`，全部 correctness/certificate redline 为零。
  generic pre-solve 采集得到 5 个 proof contexts 和 90 个不与任何
  proof 数学状态重合的 pure negative-harvest contexts；最终按 source
  wall 冻结 4 heavy exact-proof + 12 ordinary negative-harvest，
  16 个 mathematical-context hash 全部唯一。
- snapshot replay 使用
  `snapshot_replicate_rotating_arm_blocks_v1`，按 snapshot/replicate
  旋转 P0V4/E64/E128/E256 的运行位置，避免长时间机器漂移与 arm
  混淆。SIGINT/异常会终止完整 fresh-process group，不再遗留孤儿
  Native host。旧的两条连续 P0V4 诊断行保留在独立旧 ledger，不进入
  正式 blocked summary。
- 192 行正式 snapshot replay 已在
  `runs/p0v4_diverse_negative_escape_oracle_v2/` 串行完成。严格
  summary v2 的 SHA256 为
  `e551785e427998f1a58c513fd96ecc197aaa911abc771c36700fca5623e4b657`：
  192/192、无 missing/unexpected/duplicate、Native engine hash
  唯一、全部 redline 为零并授权 fixed-K development。P0V4 与
  E64/E128/E256 各 48 行；三种 E_K 均 48/48 达到 4K partial-return。
  P0V4/E64/E128/E256 的 mean wall 分别约为
  487.29/23.44/25.26/31.57 秒，median 分别约为
  480.12/6.63/8.88/16.31 秒。它们只作为 snapshot 筛除证据，不直接
  决定固定 K。
- scale50/001--010 的 P0V4/E64/E128/E256 端到端 development oracle
  已按实例分块轮转、单进程、每 arm 3600 秒正式启动；固定 K 尚未
  选择。instance_001 的四个 arm 已全部形成合法 ledger：
  P0V4/E64/E128/E256 分别为 3593.92/3592.31/2542.72/3594.48 秒，
  81/94/73/60 个 CG rounds，9951/5600/9029/13472 条 active columns，
  峰值 process-tree RSS 为 11.39/11.16/11.24/11.30 GiB；四者均为
  fail-closed `BPC_INCOMPLETE_PRICING`，no-cheat 通过且 redline 为零。
  E128 的提前结束原因为 Native `MEMORY_LIMIT`，其 2542.72 秒不是速度
  优势。development metric 已修正为真实累计 wall 的固定 3600 秒
  horizon；不完整搜索的零候选不再冒充零负压，资源失败后的剩余时段
  按同实例各 arm 的最坏可信 pressure 补齐，并记录
  `resource_adverse_count`。按该修正仅重算 instance_001，
  P0V4/E64/E128/E256 的 combined root-gap/pressure AUC 约为
  0.5002/0.2916/0.4186/0.3324；它仍不能用于选出 K，完整 10 例结束后
  必须用新进程重新执行 summarize。
- E256/instance_001 的有效 fixed-K 触发发生在第 46 个 CG round：
  Native raw unique negative 为 1024，Python true-RC/branch/cut
  审计后为 1019，P0V4 selector 选择并由 batch admission 激活 256
  条；termination 为 `RAW_TRUE_NEGATIVE_POOL_REACHED`，
  `can_certify_no_negative=false`。该 run 同时自然产生 1 个
  \(K+32=288\) 的 route-opportunity snapshot，但 census 门槛远未满足，
  未启动 counterfactual rollout。
- development queue 已自动推进到 E64/instance_002，仍保持唯一一个
  scale50 solve process。正式 ledger 只含上述 4 条有效结果；两次旧
  E256 telemetry/schedule 失效 run 和两次中断的 E64/instance_002
  均隔离在 `development_invalidated/`，不会参与 fixed-K summary。
- route-opportunity snapshot 已升级到 v2，只接受
  `post_candidate_generation_pre_admission` 时刻的真实剩余预算；v1 中
  候选生成前预算可能虚假授权晚到 context，现由 census 作为
  `invalid_snapshot` fail closed。升级时已经加载旧模块的 active arm
  只会产生不可用于 GAT 的 v1 telemetry，不影响 Exact 列、bound、
  pruning 或 certificate；固定 K 后仍需补采满足规模/实例门槛的 v2
  contexts。
- 因 K 未冻结，matched counterfactual rollout、GAT 训练和正式
  scale50/100 评测均未获授权。
- 已实现并测试 state-hash/action/replicate/censor 契约、fresh-process
  arm/context/suite 执行器、包审计、two-head 训练、Wilson harmful gate、
  OOD/hash/memory no-op 安全壳和 checkpoint reload。正式 rollout 仍必须
  等 K 冻结且 census 通过后才获授权。
- bidirectional pricing 未触发，也未实现；它只在预注册 fallback 条件
  成立后进入单独 feasibility 阶段。

以上缺口是实验状态，不是以空数据冒充通过。任何下游 stage 都通过
hash/status gate fail closed。
