# Native SPPRC backend 实施与 promotion 报告

## 1. 实施边界

基线提交为 `48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e`，upstream 固定为
`lab-core/rcspp@2f1d53ba6806844e30ce43ee9c41041a5a1b4e79`。未建立 fork，未修改
solver core；当前采用 standalone CMake、project-local C++ resource/extension、pybind
adapter 与 Python reference fallback。upstream pressure false-COMPLETE 可通过 exact 配置
禁用 label trimming，因此 patch queue 为空，`fork_required=false`。

当前 engine hash：

- in-process：`66ab52c9b33b4551`；
- persistent host：`ee0ea1fb74eb8035`。

## 2. 已实现能力

- forward elementary cyclic multi-sortie graph；全 journey visited bitset 在 recharge 后不清空；
- depot cycle 严格时间/visited 进展、禁止空 sortie 与 recharge self-loop；
- raw operating-cost/risk/weighted-completion/task-dual/cut-dual 单一数学状态；
- Python reconstruction、physical feasibility、canonical objective 与 manual true-RC 终审；
- `BackendResult` 分离 best-found、exact global-min、threshold proof、frontier、drop/blocker；
- visited-set-indexed exact dominance、stable arc reconstruction 与 LRU graph cache；
- Ryan–Foster same/different feasibility，branch context 不进入 reduced cost；
- branch child Phase-I artificial RMP 恢复；
- persistent spawn host、versioned pickle-safe IPC、same-instance delta、RSS hard kill、
  cancellation、stale-build restart；
- incomplete search 保留已审计负列但丢弃 proof state；
- 六规模独立 profile/runner，原 30-scale B4.3 runner 保持不变；
- Phase 10 feature flags：subset-row/fleet cut state、positive-cover completion bound、
  visited-subset dominance。当前 acceptance 仅启用 exact-proof visited-subset dominance；
  completion bound 与 cut state 关闭，resource partition 与 bidirectional join 未实现。
- visited-subset dominance hot path 使用 Gray-code proper-subset key 复用、bucket optimistic-min
  必要条件筛选和等价 state comparator；这是 dominance 索引优化，不是尚未实现的 resource
  bucket/partition 算法。
- 由于 v1/v2 acceptance 明确限定 `task_count <= 100`，visited state 使用 inline
  `std::array<uint64_t, 2>`，取代每个 label 的 heap-backed `std::vector<uint64_t>`；这是
  等价的 128-bit elementarity 表示，不改变 visited、dominance 或 certificate 关系。
- 30-scale branch node 使用 `branch_adaptive_sparse_harvest_v1`：root 保留完整 legacy
  harvest，只有非空 Ryan–Foster branch context 在稀疏 harvest 后切 proof-only；scale-30
  candidate harvest 显式限制为 2 秒，proof 使用同一 absolute deadline 的剩余时间。
- acceptance runner 绑定 start/child/end 三处 engine hash；运行中代码或 binary 漂移返回
  `HASH_DRIFT`，对应 artifact 不得进入正式 acceptance；adaptive harvest cap 同时进入 row
  telemetry 与 official config hash，runner 会清除继承环境，避免非目标规模受污染。
- acceptance report schema v2 以每个 `NativeSpprcScaleProfile` 的 row time limit 计算
  exact/no-cheat/under-limit gate，并报告 mean/p50/max；child B4.2 的历史 300/500 秒诊断字段
  不再错误覆盖 native release gate。

## 3. Correctness 与 certificate

5-task 完整、10-task representative differential 已通过；native/Python 的 feasibility、
objective、best RC、negative/no-negative 与 threshold certificate 一致。Ryan–Foster root、
same child、different child differential 通过。subset-row 的
`floor(overlap/divisor)` threshold crossing 与 fleet coefficient 也通过 5-task differential；
Phase-I + 非空 cut 显式 fail closed。

状态注入覆盖 COMPLETE、MAX_SOLUTIONS、TIMEOUT、MEMORY_LIMIT、interrupt、labels-dropped、
malformed reconstruction、instance/build/config hash mismatch。任何 incomplete/drop 状态均不能
产生 no-negative certificate。persistent host 的 read-only `mappingproxy` dual IPC、同 PID
delta reuse、1 MiB memory-limit kill 后恢复、stale hash restart 均有回归测试。

最终本地 gate：

- CTest：2/2；
- Python reference-internal labeling suite：102 passed、5 subtests passed；
- 最终 cut/subset state 版本的 ASAN/UBSAN CTest 2/2 通过；
- 默认 backend 切换后的全量 pytest：395 passed、22 个 subtests passed，0 failed；其中包含
  default-native、显式 Python rollback、unsupported-cut fallback、persistent-host/hash/resume
  回归。

## 4. 性能与规模 gate

### 4.1 5/10 pricing-core 与 total-wall

promotion 基线、warm import、固定 zero-dual snapshot 的 pricing-core p50：

| scale | native | Python reference | speedup |
|---:|---:|---:|---:|
| 5 | 0.000328s | 0.002829s | 8.64× |
| 10 | 0.008953s | 0.034181s | 3.82× |

因此分别通过 1.5×/2× pricing-core 替代门槛。三次 cold-start total-wall p50 为：

| scale | native | Python reference | 结果 |
|---:|---:|---:|---|
| 5 | 0.403403s | 0.413530s | -2.45%，无回归；使用 pricing-core gate |
| 10 | 0.738076s | 1.797509s | -58.94%，通过 total-wall gate |

### 4.2 20-task

当前 engine/config（engine hash `66ab52c9b33b4551`、acceptance config hash
`4b8389b5229d6e81c6164dbcf049bacaaa7d2a99ab03e8de56f44bacc585c03c`）的完整
5/10/20 strict cold-start gate 共 60 行全部 exact、zero redline、engine hash drift 0；三档
start/child/end engine hash 均一致。scale-20 的 20 个实例全部 `BPC_OPTIMAL`，total mean
`31.171581s`、p50 `17.648412s`、最大 `124.627828s`，root mean `10.767889s`，tree mean
`20.067419s`。同批 scale-5 mean/p50/max 为
`0.406318s / 0.406548s / 0.431486s`，scale-10 为
`0.828971s / 0.761838s / 1.252164s`。相对上一稳定 hash 的 scale-20 p50
`21.573175s` 下降约 18.2%；5/10 未触发 5% total-wall 回归红线。完整 artifact 位于
`/tmp/native-spprc-fixed-mask-gate-5-10-20-current`。

completion bound A/B 虽保持 exact certificate，但真实 RMP dual 下 prune count 为 0，
instance012 为 257.43 秒；不 promotion。visited-subset dominance differential 保持 global
optimum/no-negative proof，并只在 exact-proof pass 使用；negative-harvest pass 不启用，以保留
候选列 surface。当前 acceptance 已启用该 proof accelerator，但它不是 live cut 或
bidirectional acceleration。

### 4.3 30-task technical promotion

- technical promotion 的早期 instance001 与 001–005 gate 均已通过；随后继续运行完整 20 例
  default-release gate，不用早期 incomplete 作为最终结论；
- 固定 branch-node cap A/B 使用相同 instance012 root pool、分支上下文
  和 300 秒节点预算：node002 保持 3 个新增列、2 轮、官方 LP 下界 `1.497591` 与合法
  no-negative certificate，墙钟由 `63.930797s` 降至 `55.943808s`（-12.49%）；node004
  保持官方 LP 下界 `1.501920` 与合法 certificate，墙钟由 `114.484406s` 降至
  `110.297002s`（-3.66%），定价轮数由 3 降至 2。两组均通过 manual RC 与 pricing RC
  audit，因此 promotion 2 秒 branch harvest cap；它不改变 root 或 certificate 数学语义。

#### instance012：先取 3600 秒最优时间，再做结构剖析

在不改生产配置的 3600 秒 strict cold-start 运行中，instance012 于
`3326.290682s` 自然 exact closure：root `583.752279s`、tree `2741.427974s`，17 个 evaluated
nodes、16 次 Ryan–Foster branch、1024 个 tree-shared 新列，最优值与全局下界均为
`1.503078`。全部 node lower bound、true-dual pricing proof 和 certificate ledger 有效，说明
此前 1800 秒 incomplete 不是错误证书，而是确实尚需约 1522 秒 tree 工作。

剖析显示 tree node wall 的 99.57% 位于 final judge，97.78% 位于 exact proof；最终
no-negative calls 共扩展约 20.81 亿 labels，执行约 121.12 亿次 dominance candidate checks。
最慢 node016 的旧 final proof 为 `129.624s`，其中 dominance `113.122s`，proper-subset
candidate checks `1,222,320,505` 次而 subset rejection 仅 `2,487,928` 次。固定同一 instance、
true dual、branch context 与 300 秒上限关闭 subset dominance，仍得到相同 COMPLETE threshold
proof，核心时间为 `57.666s`；这确认热点在 subset 索引实现，而非 B&B 参数。

实现级修复后，同一 node016 保持完全相同的 `188,738,767` extended labels、`5,590,737`
dominated labels、`2,487,928` subset rejects 和 `proved_no_rc_below=-1e-6`，但 subset candidate
逐 label 比较降到 `15,975,167`，核心时间降到 `39.288s`（相对旧实现 -69.7%）。其中
760,721,310 次 proper-subset key lookup 找到 130,098,884 个 nonempty buckets，安全 optimistic
minima 跳过 105,303,351 个不可能含 dominator 的 buckets。

随后使用 production 1800 秒 profile、strict cold-start、no-resume 重跑，结果为：

| 指标 | 旧实现 3600 run | 新实现 1800 run | 变化 |
|---|---:|---:|---:|
| total | 3326.290682s | 1474.584039s | -55.67% / 2.256× |
| root | 583.752279s | 433.832707s | -25.68% / 1.346× |
| tree | 2741.427974s | 1039.734964s | -62.07% / 2.637× |

两次运行均有 3463 个 root columns、root bound `1.496360`；17 个 tree nodes 的访问顺序、
node status、pricing rounds、新增列数和 LP bound 逐项完全一致。新运行是
`BPC_OPTIMAL / BPC_TREE_OPTIMAL`，最优值/全局下界 `1.503078`、gap 0、engine hash
`6b114ace37179347` 从 start 到 child/end 一致，所有 redline 为 0。artifact 位于
`/tmp/native-spprc-subset-index-scale30-012-1800-current`。

#### instance014 与 inline visited state

旧实现下先用 3600 秒 profile 获取 instance014 的精确闭合时间，而不是继续扫参数；它在
`2069.018683s` exact closure。固定该实例 node011 的同一 instance、true dual、branch context 和
threshold proof 后，确认 label 的 heap-backed visited bitset 分配仍是结构热点。改为 inline
128-bit fixed mask 后，该固定证明保持 `COMPLETE`、frontier empty、相同
`proved_no_rc_below=-1e-6`，native core 由 `53.650985s` 降至 `40.646477s`（约 -24.2%）。

最终 production 1800 秒 profile、strict cold-start、no-resume 的 instance014 独立复跑为
`BPC_OPTIMAL / BPC_TREE_OPTIMAL`：total `1679.304927s`、root `420.359563s`、tree
`1257.727287s`，21 evaluated、11 closed、0 open/incomplete、20 次 branch，incumbent/global
lower bound 均为 `1.454416`。全部 ledger/lower-bound/pricing-proof/fathoming audit 有效，所有
redline 为 0。artifact 位于 `/tmp/native-spprc-fixed-mask-scale30-014-1800-current`。

#### Phase 11 完整 20-instance gate

当前 engine `66ab52c9b33b4551` 的 strict cold-start、no-resume 完整批次为 20/20
`BPC_OPTIMAL`，20/20 no-cheat，budget-exhausted 0，所有 redline 为 0，start/child/end engine
hash 一致。统计如下：

| total 指标 | 时间 |
|---|---:|
| mean | 453.915594s |
| p50 | 327.598609s |
| max | 1679.705969s |
| root mean / p50 | 159.562473s / 124.933467s |
| tree mean / p50 | 293.503039s / 213.869142s |

因此同时满足 20/20、每例不超过 1800 秒、median 不超过 900 秒及 stretch median 不超过
600 秒。相对前一稳定 hash 的 p50 `398.769626s`，当前 p50 下降约 17.8%。个别实例存在
运行波动（例如 009 比前一批慢约 24%），但 scale-30 aggregate p50 明显改善且不存在规模级
超过 5% 的 total-wall 回归。完整 artifact 位于
`/tmp/native-spprc-fixed-mask-scale30-full20-current`。

### 4.4 50/100 persistent-host bounded gate

60 秒单时钟 bounded run：

| scale | rounds | 审计加入列 | host graph reuse | peak RSS | 结果 |
|---:|---:|---:|---:|---:|---|
| 50 real-map | bounded | 已审计 partial | same-instance delta | 745,439,232 B | legal incomplete |
| 100 synthetic acceptance | bounded | 已审计 partial | same-instance delta | 122,658,816 B | legal incomplete |

当前 host engine `ee0ea1fb74eb8035` 的两行最终均为
`BPC_INCOMPLETE_PRICING / INCOMPLETE_LIMIT`、zero redline；最后的 MAX_SOLUTIONS search
均明确 `search_exhaustive=false`、`partial_columns_valid=true`、proof state discarded。
100-task fixture 由
`domain.scheduling.generate_instance(100, seed=1629001)` 生成，100 tasks、10,100 edges、
schema issues 0、`validation.accepted=true`。

同 config 的 terminal-row resume 在约 0.17 秒返回且不重跑；将 row limit 从 60 改为 61
后，runner 以不同 `config_hash` 立即拒绝 resume（return code 2）。host 不序列化内部 labels。

## 5. Release 结论

Technical promotion 与 default release 均已通过：30-scale 20/20 exact、最大
`1679.705969s`、p50 `327.598609s`，5/10/20 gate、50/100 bounded host、Ryan–Foster、hash、
resume、fallback 和 rollback 均有证据。因此 production `exact_backend` 默认值已切为
`native_rcspp_inprocess`。

Python reference 没有删除：显式设置
`LUNAR_ICE_SPPRC_EXACT_BACKEND=python_reference` 可 rollback；native 遇到尚未 promotion 的
非空 cut/branch capability 会 fail closed 后走 Python exact fallback。live cut certification、
completion bound 仍默认关闭；resource partition 与 bidirectional join 尚未实现。当前默认只
启用已经 differential 的 exact-proof visited-subset dominance，不把候选列 heuristic 或
partial search 当作 no-negative proof。
