# GAT_BPC_moonTerk 当前主线与 Native SPPRC 交接文档

更新时间：2026-07-23

面向对象：接手本项目的下一个 Codex 对话

当前工作目录：`/home/kai/work/GAT_BPC_moonTerk`

## 0. 接手者先读结论

当前项目最成熟的生产主线不是“GAT 已经驱动求解”，也不是“live cuts 已经默认开启”。
Native Live SRI BPC V1 的功能、证书闭环和正式性能实验已经完成，但候选 P0 未通过全部
promotion 门槛。当前真正通过 release gate 的生产主线仍是：

> HiGHS restricted master + native exact SPPRC pricing + Ryan–Foster branching，
> 即具备真分支、真列生成和 exact no-negative pricing proof 的 Branch-and-Price。

具体边界如下：

- 生产默认 exact backend 已经是 `native_rcspp_inprocess`；
- 5/10/20/30 规模已有 exact closure 和 promotion 证据；
- 30 规模曾完成 20/20 strict cold-start exact，p50 为 `327.598609s`，最大
  `1679.705969s`；
- Ryan–Foster `same_journey/different_journey` 已进入真实 B&B 子节点；
- Python exact backend 没有删除，仍是 reference、fallback 和 rollback；
- SRI-3/SRI-5 live master cuts、active-cut Phase-I、lineage/hash/certificate、P0/P1/P2
  node loop 和 Native compact cut state 已完整实现并测试；
- P0 已完成 1040/1040 formal fresh paired slots，全部正确性门禁通过；5/10/20 性能门禁
  通过，但 30 规模 mean、paired point estimate 和 paired CI 上界失败，因此总状态
  `NOT_PROMOTED`；
- production default 和显式 rollback 都是 `no_cut`；P0/P1/P2 仅保留为实验能力，
  node cuts 默认关闭；
- 50/100 各 20 个正式实例已经生成并验收，但前 5 个实例的求解均在 root exact
  pricing 先达到 8 GiB host memory limit，尚未得到 50/100 最优解时间；
- 50/100 当前首要问题是 exact label frontier 的内存/数量增长，不是把 1800 秒改成
  3600 秒；
- 若继续 Live SRI，下一步先固定正式 30-scale 退化实例，解释树节点和 cut-aware pricing
  的慢化来源，再形成新候选；不得把旧 P0 改写为已晋级。
- 50/100 仍是 exact frontier 内存问题，但本轮优先级低于 5/10/20/30 主线的稳定性。

## 1. 当前代码与证据快照

### 1.1 Git 与实现基线

- 当前 Git 根目录：`/home/kai/work`；
- 本文核对时的 HEAD：`bd0d81839731fd2c41718dfb2be3d533f4c90c0d`，提交标题 `722`；
- native 实施最初冻结基线：`48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e`；
- upstream：`lab-core/rcspp@2f1d53ba6806844e30ce43ee9c41041a5a1b4e79`；
- 当前没有 solver-core fork，也没有 core patch；采用 pinned upstream + project-local
  C++ resource/extension + pybind adapter；
- feasibility spike 发现的 pressure/false-COMPLETE 风险可通过 exact 配置禁止 label
  trimming 规避，因此当前 patch queue 为空，`fork_required=false`。

Stage -1 冻结基线 engine hash 为 `66ab52c9b33b4551`。正式 P0 paired promotion 使用：

- in-process：`dfaedf6d273c5c56`；
- 当时 persistent host：`bddc7afddc232ceb`。

正式重复后修复 host IPC signed-zero dual 保真问题，当前 source binding 为：

- in-process：`7e4c1b7ade427e9e`；
- persistent host：`d44cd21da6dae8c0`。

5/10/20/30 formal slots 使用 in-process backend，没有执行被修复的 host IPC reconstruction；
历史正式证据仍严格绑定 `dfaedf6d273c5c56`，不得替换成当前 hash。

不要把 hash 当成手填版本号。正式 artifact 必须同时绑定 instance、model、objective、
config、dual、branch/cut context 和 engine build hash；运行中 hash 漂移必须 fail closed。

### 1.2 本次交接前的快速验证

最终源状态已重跑：

```text
ctest --test-dir build/native-spprc --output-on-failure
  -> 2/2 passed

python -m pytest -q tests/native
  -> 36 passed, 16 subtests passed

ctest --test-dir build/native-spprc-asan --output-on-failure
  -> 2/2 passed

python -m pytest -q
  -> 410 passed, 21 subtests passed
```

以上均在 signed-zero host 修复之后执行，失败数为 0。

### 1.3 当前机器资源边界

本文核对时：

- 物理内存约 15 GiB，约 12 GiB available；
- swap 约 4 GiB，当前使用约 589 MiB；
- 磁盘尚有约 818 GiB；
- 没有正在运行的 Moon Trek 求解进程；
- VS Code extension host 单进程约占 1.15 GiB，桌面常驻进程仍需保留安全余量。

此前机器已经发生过两次崩溃/重启。50/100 在这台机器上必须使用 host backend、单实例
串行和不高于 8 GiB 的临时安全上限，除非先完成内存降幅验证。不要直接使用 profile 的
24/32 GiB nominal 值；默认 effective limit 仍可能达到约 10.9 GiB，会显著压缩系统余量。

## 2. 数学模型到底是什么

### 2.1 Column 的语义

一个 column 不是单条普通 VRP route，而是一台探测器/车辆完成的一条完整 multi-sortie
journey：

```text
depot -> 若干任务 -> depot/recharge -> 若干新任务 -> depot -> ...
```

关键约束：

- task 在整条 journey 上 elementary，同一任务不能因 recharge 被再次访问；
- visited set 在回 depot、充电或资源 reset 后不清空；
- 每个 sortie 至少访问一个此前未访问任务；
- depot cycle 的 global time 和 visited cardinality 必须严格前进；
- 禁止 depot-to-depot 空 sortie、无新任务 recharge loop、零时间或负资源循环；
- 每个 sortie 分别受 task cap、capacity/demand、energy、shadow 等资源约束；
- 时间窗和全局 horizon 在跨 sortie 后继续累计；
- `sortie_count <= visited_task_count`。

这也是为什么通用单 route ESPPRC 的 DSSR、bidirectional join 或资源 bucket 不能未经证明
直接成为本项目的 exact certificate engine。

### 2.2 Restricted Master Problem

Master 以 journey columns 为变量，核心约束是：

- 每个 task 的 exact cover equality；
- fleet limit；
- 当前正式主线中的 Ryan–Foster branch constraints；
- live SRI master-cut framework 已实现并通过 correctness gate，但 promotion 未通过，所以
  live master cuts 默认关闭。

当前 reduced cost 的最终审计公式是：

```text
reduced_cost
= official_objective
  - sum(task_duals for tasks covered by journey)
  - fleet_dual
  - sum(cut_dual * supported_cut_coefficient)
```

Ryan–Foster branch context 只改变一条 journey 是否可行以及 terminal label 是否允许，不产生
所谓 branch dual，也不直接加入 reduced cost。

### 2.3 Official objective

native label 只累计原始加性数学分量：

```text
raw_operating_cost
raw_risk
raw_weighted_completion
task_dual_reward
cut_dual_reward
fleet_dual_applied
```

按需计算：

```text
official_objective
= w_cost       * raw_operating_cost      / ref_cost
  + w_risk       * raw_risk                / ref_risk
  + w_completion * raw_weighted_completion / ref_completion

reduced_cost
= official_objective
  - task_dual_reward
  - fleet_dual
  - cut_dual_reward
```

当前配置里的 completion 权重为 `0.4`。makespan 是报告指标，不是 official objective 的
第四项。native inner loop 全部使用 `double`，不做六位小数 rounding；返回 Python 后重建
`JourneyColumn`、执行 canonical rounding，并以项目现有
`manual_journey_reduced_cost()` 做 true-dual 终审。

负 RC、dominance、resource feasibility 和 reconstruction 使用分离的 epsilon，禁止拿一个
通用 epsilon 同时决定四类数学关系。

## 3. 当前求解算法的真实流程

```text
实例与稳定 arc mapping
        ↓
初始可行 columns / candidate harvest
        ↓
HiGHS Restricted Master LP
        ↓
读取真实 task/fleet/cut dual
        ↓
native negative-column harvest（可提前返回，不能作 proof）
        ↓
native exact proof pass（必须 exhaustive 或严格 threshold proof）
        ↓
Python reconstruction + physical feasibility + manual true-RC audit
        ↓
有负列：加入 column pool，重新求 RMP
无负列且 proof 合法：关闭当前 pricing row/node
        ↓
LP 解分数：Ryan–Foster same/different 分支
        ↓
child Phase-I artificial RMP 恢复 + child exact pricing
        ↓
所有节点由合法 bound/certificate/fathoming 关闭后得到树级最优证明
```

必须持续区分两类输出：

1. 候选列：可以来自提前 harvest、NG 或 incomplete search。只要完整返回并通过 Python
   reconstruction、feasibility、branch/cut 和 manual true-RC audit，就可以加入列池。
2. 证明：只有 exact global minimum 或严格 `proved_no_rc_below`，并且 frontier/drop/status
   全部满足 contract，才能进入 no-negative certificate audit。

`TIMEOUT`、`MEMORY_LIMIT`、`INTERRUPTED`、crash、`labels_dropped=true` 都不得生成
no-negative certificate。incomplete search 中已经完整返回并审计的负列可以保留，但丢弃全部
proof state。hard crash 只能保留崩溃前已经跨 IPC 完整传回并审计的列。

## 4. Backend 架构与默认值

统一 contract 位于：

- `src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py`
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/python_reference.py`
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py`

现有 backend：

- `PythonReferenceBackend`：reference、unsupported-feature fallback、显式 rollback；
- `NativeRcsppInprocessBackend`：5/10/20/30 默认 exact backend；
- `NativeRcsppHostBackend`：50/100 的隔离、RSS hard kill、cancellation、stale-hash
  restart 和 same-instance graph reuse。

生产默认为：

```text
native_rcspp_inprocess
```

显式回滚：

```bash
export LUNAR_ICE_SPPRC_EXACT_BACKEND=python_reference
```

`BackendResult` 已区分：

- `best_found_rc`；
- `global_min_rc` 与 `global_min_rc_is_exact`；
- `proved_no_rc_below`；
- `unexplored_rc_lower_bound`；
- `search_exhaustive`、`frontier_empty`、`labels_dropped`；
- `partial_columns_valid`；
- `certificate_blockers`。

不要为了填字段而把 best-found 冒充 global minimum，也不要把找到若干负列后的提前返回冒充
exhaustive search。

## 5. Phase 状态

| Phase | 当前状态 | 已完成内容 / 边界 |
|---:|---|---|
| 0 | 完成 | baseline、hardware/config/instance/build hash 与 cold-start gate 已建立 |
| 1 | 完成 | pinned upstream feasibility spike；无 fork；false-COMPLETE 风险通过 exact 配置规避 |
| 2 | 完成 | 5-task、empty branch/cut、forward elementary、in-process pybind、多 sortie reset |
| 3 | 完成 | 5 full、10 representative differential；timeout/memory/drop 等 fail closed |
| 4 | 完成 | backend registry、shadow、official adapter、hash/telemetry contract |
| 5 | 完成 | 20-task 20/20 exact correctness/performance/RSS gate |
| 6 | 完成 | 30-instance001 root proof promotion |
| 7 | 完成 | 30-scale 001–005 technical promotion |
| 8 | 完成 | Ryan–Foster same/different 与 child differential、child Phase-I |
| 9 | 完成 | persistent host、50/100 bounded stability、RSS/cancel/hash/resume gate |
| 10 | 部分完成 | cut-state differential、completion-bound differential、visited-subset dominance；resource partition 与 bidirectional join 未实现 |
| 11 | 完成 | 30-scale 20/20 release gate，通过后默认 exact backend 切到 native |
| 12 | 完成但未晋级 | Native Live SRI BPC V1 功能/证书闭环、P0/P1/P2、1040-slot formal promotion；P0 因 30 性能门槛失败保持默认关闭 |

这里有一个容易误读的地方：Phase 11 的默认 release 是在明确定义的默认 feature scope 上通过
的，并不等于 Phase 10 列出的所有高级能力都实现或启用了。

## 6. 高级能力：实现了什么，启用了什么

当前 acceptance 默认配置：

```yaml
native_completion_bound_enabled: false
native_subset_dominance_enabled: true
native_cut_state_enabled: false
```

### 6.1 已实现并默认启用

- exact-proof pass 的 visited-subset dominance；
- Gray-code proper-subset key 复用；
- bucket optimistic-min 必要条件筛选；
- 等价 state comparator；
- `task_count <= 100` 的 inline 128-bit visited mask；
- 30-scale 非空 branch node 的 adaptive sparse harvest，2 秒后切 proof-only；
- Ryan–Foster same/different branch feasibility 与 terminal acceptance；
- persistent host 的隔离、RSS hard kill、cancel、hash restart、graph delta reuse。

注意：这里的“bucket optimistic minima”只是 dominance 索引优化，不等于完整的 resource
bucket/partition 算法。

### 6.2 已实现并完整测试，但默认关闭

- SRI-3/SRI-5 live separator、master rows 和 `floor(overlap/2)` threshold-crossing state；
- fleet-cut coefficient state；
- active-cut Phase-I；
- global/local lineage、sibling isolation、三类独立 hash；
- P0/P1 root cuts、P2 branch-node cuts；
- active-cut Native/Python/HiGHS reduced-cost reconstruction；
- positive-cover completion bound。

关闭原因：

- P0 正确性通过，但 30-scale 正式性能 promotion 未通过；
- P1/P2 没有被选择为正式候选，node cuts 仅保留 capability；
- completion bound 在真实 RMP dual 上 prune count 为 0，并出现慢例，尚未提供生产收益；
- fleet lower-bound cut 仍是 diagnostic，不属于 V1 live family。

### 6.3 尚未实现或尚未获得 exact role

- resource partition/bucket algorithm；
- bidirectional join；
- PathWyse/DSSR/NG 的 exact-certificate role。

NG/DSSR/其他 worker 现在最多只能产生候选列，不是 proof source。将来只有完成 lunar
multi-sortie 表达、license 审计和 certificate differential，才能重新评估 exact role。

## 7. 当前各规模的可复用证据

### 7.1 5/10/20/30

| Scale | 当前 exact 证据 | total-wall 统计 | 备注 |
|---:|---|---|---|
| 5 | 20/20 exact | mean `0.395952s`，p50 `0.393683s` | Stage -1 frozen fresh baseline |
| 10 | 20/20 exact | mean `0.820660s`，p50 `0.754397s` | Stage -1 frozen fresh baseline |
| 20 | 20/20 exact | mean `32.352003s`，p50 `18.391300s` | Stage -1 frozen fresh baseline |
| 30 | 20/20 exact | mean `493.045466s`，p50 `346.038290s` | Stage -1 frozen fresh baseline |

30 的难例曾采用“先给 3600 秒拿到真 exact 时间，再剖析结构热点”的策略：

- instance012 旧实现 `3326.290682s` exact，定位 subset dominance 索引热点后降到
  `1474.584039s`；
- instance014 旧实现 `2069.018683s` exact，inline visited mask 后 production run 为
  `1679.304927s`。

这说明 30 规模优化不是纯调参：先获得合法 exact closure，再固定 instance/dual/branch
context 做结构 A/B，是正确做法。

### 7.2 冻结基线与正式 paired promotion

旧 `/tmp` 证据缺口已经通过 Stage -1 正式恢复消除。冻结 baseline 位于：

```text
runs/native_spprc_no_cut_5_30_full3600_frozen_v1/
  baseline_freeze_manifest.json
  frozen_config.yaml
  ...
```

它包含 80/80 exact、80/80 no-cheat、零 redline、无 engine 漂移和历史恢复容差审计，正式
ID 为 `FROZEN_NATIVE_NO_CUT_BASELINE_V1`。paired promotion 没有复用 baseline 的单次时间，
而是重新 fresh 运行 control。

正式 P0 paired promotion：

| Scale | live/base mean | live/base p50 | paired point | 95% CI | promotion |
|---:|---:|---:|---:|---|---|
| 5 | 1.003516 | 0.999396 | 1.003480 | [0.996809, 1.009628] | pass |
| 10 | 0.981068 | 0.958215 | 0.979668 | [0.951791, 0.999489] | pass |
| 20 | 0.805249 | 0.793010 | 0.864355 | [0.771307, 0.951162] | pass |
| 30 | 1.087746 | 0.835094 | 0.959039 | [0.824718, 1.103403] | **fail** |

证据目录：

```text
runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/
  promotion_rows.json
  promotion_summary.json
  promotion_post_amendment_audit.json
  promotion_decision_manifest.json
```

30 规模 mean、paired point estimate 和 CI 上界失败，所以总状态为 `NOT_PROMOTED`。

### 7.3 50/100 数据与求解状态

正式 manifest：

```text
data/manifests/lunar_ice_sp50_real_benchmark_manifest.json
```

当前六种规模 5/10/20/30/50/100 均有 20 个 accepted 实例。50 和 100 各 20 个已经完成
生成和 schema/acceptance 检查；50 目录约 973 MiB，100 目录约 3.7 GiB。

持久化试跑目录：

```text
runs/native_spprc_50_100_5x3600_20260717/
```

在 8 GiB 安全 cap 下的前五例：

| Scale | exact | mean | p50 | max | 终止原因 |
|---:|---:|---:|---:|---:|---|
| 50 | 0/5 | `440.744088s` | `404.561351s` | `641.914692s` | 5/5 `MEMORY_LIMIT` |
| 100 | 0/5 | `880.900929s` | `860.160410s` | `1093.099068s` | 5/5 `MEMORY_LIMIT` |

所有行都满足 no-cheat、zero certificate leak、manual/pricing RC audit 和 engine hash
一致，但均为：

```text
BPC_INCOMPLETE_PRICING / INCOMPLETE_LIMIT
search_exhaustive = false
frontier_empty = false
can_certify_no_negative = false
```

这不是 50/100 的最优时间。它只说明当前主线可以安全、可复现地运行，并在内存边界上正确
fail closed。由于 host 在提交完整 BackendResult 前被 hard-kill，这十条行也没有从最后一次
pricing call 留下可审计的 partial native payload；此前已经加入 master 的 harvest columns 不受
影响。

Live SRI 共享代码完成后的最新 bounded regression 位于：

```text
runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_v2_signed_zero_fix_20260723/
```

50/100 的 instance001 都使用 `no_cut`、host、600 秒、8 GiB、单实例串行：

| Scale | wall time | 状态 | 唯一 blocker | peak host RSS |
|---:|---:|---|---|---:|
| 50 | 340.135371s | legal incomplete | `host_memory_limit` | 8.0028 GiB |
| 100 | 300.159294s | legal incomplete | `host_memory_limit` | 8.0006 GiB |

第一次运行发现 host IPC 会把 legal fleet dual `-0.0` 改成 `+0.0`，触发
`native_dual_binding_hash_mismatch`。修复只保留 signed zero，没有放宽 hash 检查；新运行
dual mismatch 为 0，engine start/child/end hash 一致，zero redline，cut state off，
active cut count=0。两例仍不是 exact closure，只是符合计划的安全回归。

## 8. GAT/B5 当前状态

项目名中虽然有 GAT，但当前代码里的 `shadow_policy.py` 不是训练完成的 GAT 模型。它使用固定
启发式权重：

```text
0.45 * science
+ 0.25 * shadow
+ 0.20 * thermal
+ 0.10 * drill
```

输出模式是 `shadow_only`，文件自身也声明它不是 pricing oracle、lower bound 或 certificate。

现有 B5 的 shadow/pricing-ordering/branch-ordering/harvest-ordering/combined-ordering suite 都满足
do-no-harm，但 `suite_performance_success_count = 0`。因此目前结论是：

- GAT/Guidance 是 exact-safe 的实验脚手架和未来数据接口；
- 它不参与 official bound/certificate；
- 还没有证据证明它能加速当前主线；
- 在 50/100 exact engine 的内存瓶颈解决前，不应把主要工程资源转去训练/调 GAT。

以后恢复该线时，应使用真实 50/100 workload 的 label/dual/branch 轨迹做 shadow-only 学习，
以“减少 exact workload 且无 proof 语义变化”为 gate，而不是只比较一个 ranking score。

## 9. 当前最关键的技术卡点

50/100 的 host 报告只告诉我们“RSS 到 8 GiB 后被杀”，还没有在 hard kill 前稳定传回足够的
exact-core 内部状态。因此目前不能严谨地区分：

1. 单个 label/索引对象过重；
2. live label 数量本身指数爆炸；
3. 两者同时发生。

从代码结构看，两种风险都存在：

- upstream `Label` 单独拥有 heap-backed `Resource`；
- label pool 使用 `vector<unique_ptr<Label>>`；
- live label 还进入 `std::list`；
- project-local visited index 额外维护 visited-mask bucket、`vector<Label*>` 和
  `unordered_map<Label*, Location>`；
- predecessor/ref-count 为 reconstruction 固定住一部分历史 labels；
- 当前 proper-subset enumeration 只在较短 visited set 上执行；visited task 较多时，50/100
  的 subset dominance 能力会显著减弱。

这些是代码审阅得到的“高概率结构原因”，不是已经完成分配剖析后的最终结论。下一步必须先
测量，再决定先改数据布局还是先改 dominance 算法。

## 10. 建议的下一步执行顺序

### P0：先补可观测性，不改变求解数学语义

给 native core/host 增加低开销、定期覆盖式 heartbeat。至少采集：

- extended/dominated/live/free/unprocessed label 数；
- label pool total/available；
- queue/frontier size；
- 每个 graph node、visited_count、at_depot、sortie_count 的 label 分布；
- visited bucket 数、最大 bucket、p50/p95/p99；
- dominance checks、subset-key queries、nonempty bucket hits、subset rejects；
- predecessor-pinned label 数；
- RSS 和可估算的 label/resource/list/bucket/location 开销；
- 当前 pricing pass、round、last-completed phase、wall time；
- 最新的 best-found RC 和可用的 lower-bound 状态，但不得把 heartbeat 当作 proof。

host 在 `MEMORY_LIMIT` 返回时要附上最后一份 heartbeat。实现方式应是固定大小、覆盖旧值的
共享内存或轻量单向通道，不能不断累积 telemetry 导致新的内存问题。hard kill 后该心跳只能
用于诊断，不能恢复 certificate。

### P0：建立固定 true-dual snapshot，而不是反复跑完整 B&B

从真实 scale50 instance001 固定：

- instance/model/objective/build hash；
- RMP column pool；
- task/fleet dual；
- branch/cut context；
- exact threshold 和 epsilon；
- stable graph/arc mapping。

然后单进程串行运行 2/4/6/8 GiB 或 2/4/8 GiB cap，每档 300–600 秒，采集 heartbeat，比较：

- live-label 增长曲线；
- bytes per live label；
- dominated/extended 比；
- bucket 长尾；
- visited_count 增长后 subset dominance 的失效率；
- best RC 和 frontier 状态随时间变化。

本阶段不追求 50 最优解，只回答“内存花在哪里、标签为什么留着”。任何时刻只允许一个
native host，运行前后检查：

```bash
free -h
df -h /home/kai/work
ps -eo pid,ppid,rss,etime,cmd --sort=-rss | head -25
```

### P1：根据剖面选择第一类结构优化

若 `bytes/live label` 很高，优先 project-local packed arena/slab：

- label 用稳定 integer ID，而不是多处 raw pointer/unique_ptr；
- State/Resource 尽量 inline；
- 降低 list node、unordered_map location、bucket vector 的重复元数据；
- predecessor 使用稳定 32/64-bit label ID；
- free-list/arena 按批次回收；
- reconstruction 前后必须保持 stable arc 和 manual RC audit。

先在 project-local extension 实现，不要因为数据布局优化直接 fork upstream。只有确认 solver
core API 无法安全承载并满足既定 fork 触发条件，才建立 patch queue/fork。

若主要是 `live label count` 爆炸，优先设计长 visited-mask 的 exact subset-dominance index：

- current Gray-code proper-subset enumeration 不适合 50/100 的长 visited set；
- 可研究 trie、meet-in-the-middle、inverted postings 或分层 mask index；
- 索引必须同时比较 resource state、depot phase、sortie state、branch/cut compatibility；
- 只能安全漏剪，不能错误多剪；
- 每次优化必须固定 snapshot 做 dominance on/off、Python/native threshold differential。

两类问题很可能同时存在，但应根据 heartbeat 决定先后，避免同时大改导致无法归因。

### P1：重新设计有实际剪枝力的 completion bound

现有 positive-cover bound 是 exact-safe 的，但在真实 RMP dual 上 prune count 为 0，不应默认
开启。下一版可研究：

- 按剩余 horizon、最小服务时间和 sortie cap 得到最多还能访问的 task 数；
- 对可达的正 dual reward 取安全 top-K 上界；
- 加入不可避免的 return/depot objective lower bound；
- 保持 optimistic：宁可漏剪，不能过估未来 reduced-cost 改善；
- 先固定 5/10 full、20 representative、30 hard-node snapshot 做 certificate differential；
- 只有 `prune > 0`、wall/RSS 有收益且 global-min/threshold 完全一致才 promotion。

### P2：逐级 gate，不直接跑 100 全树

建议 gate 顺序：

1. native CTest、ASAN/UBSAN、5-task full differential；
2. 10-task representative differential；
3. scale20 20/20 exact；
4. 固定 scale30 root/branch-node snapshots；
5. scale30 001–005 cold-start do-no-harm；
6. scale50 instance001 root exact，在本机 RSS 不超过 8 GiB；
7. scale50 001–005；
8. 只有 scale50 root closure 后，才开始 scale100 instance001；
9. 50/100 的完整 B&B 和 live cuts 放在 root exact 能稳定闭合以后。

不要现在并行扫 20 个 scale100 实例。当前机器资源和算法状态都不支持这种做法。

### P3：Live SRI 后续只允许形成新候选

V1 的 correctness、Phase-I、certificate ledger 和正式 P0 promotion 已完成，不要重复执行
旧的 readiness 清单。若继续，建议顺序：

1. 固定 30_009、30_012、30_018、30_019、30_020 的 paired evidence；
2. 分解 root、tree node count、pricing、separation、final-judge 时间，确定退化来自树形改变
   还是 cut-aware label state；
3. 实现并证明 pricing projected-cut context：RMP 保留全部 active cuts，pricing 只携带
   nonzero-dual cuts，同时 certificate 仍绑定完整 active context；
4. 评估更紧凑的 SRI threshold state；不能只存 coefficient 而丢失下一次 crossing 所需状态；
5. cut-aware dominance 只有在给出对所有共同 suffix 的完整单调性证明后才能放宽；
6. 形成新的唯一候选并重新冻结 config/policy/engine hash；旧 P0 的 screening 或 formal rows
   不能混入新 promotion。

resource partition、bidirectional join、PathWyse/DSSR exact role 均应在内存/长-mask dominance
问题得到测量和首轮解决后再评估。尤其 bidirectional join 面对 multi-sortie recharge cycle，
拼接状态和全 journey elementarity证明复杂，不应作为近期第一改动。

## 11. 不建议下一步做什么

- 不要继续把 50/100 的 1800 秒机械改成 3600 秒；当前先撞 8 GiB 内存。
- 不要提高到 10.9 GiB 或更高后无人看守运行；机器已经重启过两次。
- 不要把 `MEMORY_LIMIT` 行称为最优时间或 exact closure。
- 不要把已审计负列的可用性与 no-negative proof 混为一谈。
- 不要把 Ryan–Foster branch context 写成 branch dual。
- 不要因为 cut-state 代码存在就声称 live cuts 已启用。
- 不要把 fixed heuristic shadow policy 称为训练完成的 GAT。
- 不要先 fork upstream；先用 project-local extension 和数据布局优化验证。
- 不要把新的正式 gate 继续写入 `/tmp`。
- 不要同时修改 arena、dominance、completion bound、cuts 和 GAT；每次固定 snapshot 归因。

## 12. 接手后的推荐第一项具体任务

如果继续 Live SRI，建议下一个对话接受以下任务：

> 冻结正式 promotion 中 30-scale 的 gain/regression paired instances，逐例重建 root cut
> selection、active dual、tree-node count、pricing/separation/final-judge 时间与 cut lineage；
> 解释为什么 P0 的 p50 改善但 mean 和 paired CI 失败，并提出一个不会破坏完整 active-context
> certificate 的 projected-cut-state 优化设计。

该任务的 Definition of Done：

- 不修改或覆盖 1040-slot 正式 raw evidence；
- 每个重点实例给出 no-cut/live 的 root、tree、pricing 和 active-cut 对比；
- 区分有真实 active cuts 的退化与 `active_cut_count=0` 的运行波动；
- RMP 全 active context 与 pricing nonzero-dual projection 分开建模和绑定；
- 任何 dominance 放宽先给数学证明，未证明时保持完整 active-prefix equality；
- 新策略默认关闭，只有重新冻结并通过全量 paired promotion 才可切换；
- 50/100 不扩大运行，继续保持 no-cut。

## 13. 常用入口与文件地图

### 当前结论与计划

- `plan/native_live_sri_bpc_v1_implementation_report_zh.md`
- `plan/native_live_sri_v1_validity_and_certificate_boundary_zh.md`
- `runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/promotion_decision_manifest.json`
- `plan/07_native_spprc_backend_execution_plan.md`
- `runs/native_spprc_implementation_report_zh.md`
- `runs/native_spprc_feasibility_spike_report_zh.md`
- `runs/native_spprc_50_100_5x3600_20260717/summary_report_zh.md`
- `runs/b4_3_current_model_full_report_zh.md`：重要历史报告，但不是当前 native release
  状态的最终来源。

### Runner 与配置

- `scripts/run_lunar_ice_native_spprc_acceptance.py`
- `src/lunar_ice_bpc/runners/native_spprc_acceptance.py`
- `configs/benchmarks/native_spprc_acceptance.yaml`
- `scripts/run_lunar_ice_b4_3_spprc_labeling.py`：保留 30-scale 固定语义，不应扩展成通用
  50/100 runner。

通用 acceptance 内部仍可能调用历史命名的 B4.2 cold-exact runner；不要只看文件名判断它
使用 Python 还是 native，必须看 acceptance 注入的 backend 环境、engine hash 和 row
telemetry。

### Pricing 与 master

- `src/lunar_ice_bpc/exact/bpc/pricing/labeling_pricer.py`
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py`
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py`
- `src/lunar_ice_bpc/exact/bpc/pricing/backends/python_reference.py`
- `src/lunar_ice_bpc/exact/master/journey_rmp.py`
- `src/lunar_ice_bpc/exact/core/branching.py`
- `src/lunar_ice_bpc/exact/bpc/solver/branch_tree_solver.py`

host worker、spawn/IPC、RSS hard kill 和 graph delta 目前也实现在
`pricing/backends/native_rcspp.py` 内，并没有单独的 `native_host.py`。

### Native engine

- `native/lunar_spprc/`
- `native/lunar_spprc/include/lunar_spprc/`
- `native/lunar_spprc/src/`
- `tests/native/`

### GAT/Guidance

- `src/lunar_ice_bpc/guidance/shadow_policy.py`
- `src/lunar_ice_bpc/guidance/graph_builder.py`
- `runs/logs/b5_guidance_suite_summary.json`
- `runs/logs/b5_guidance_*_ordering_suite_summary.json`

### 数据与 50/100 证据

- `data/manifests/lunar_ice_sp50_real_benchmark_manifest.json`
- `runs/native_spprc_50_100_5x3600_20260717/acceptance_config.yaml`
- `runs/native_spprc_50_100_5x3600_20260717/scale50_acceptance/`
- `runs/native_spprc_50_100_5x3600_20260717/scale100_acceptance/`

## 14. 安全的基础命令

```bash
REPO_ROOT="$(git -C /home/kai/work rev-parse --show-toplevel)"
PROJECT_ROOT="$REPO_ROOT/GAT_BPC_moonTerk"
cd "$PROJECT_ROOT"

git status --short
free -h
df -h "$PROJECT_ROOT"
ps -eo pid,ppid,rss,etime,cmd --sort=-rss | head -25

export PYTHONPATH=src:build/native-spprc
ctest --test-dir build/native-spprc --output-on-failure
/home/kai/miniconda3/bin/python -m pytest -q tests/native
```

若要做 5/10/20 acceptance：

```bash
python scripts/run_lunar_ice_native_spprc_acceptance.py \
  --config configs/benchmarks/native_spprc_acceptance.yaml \
  --scales 5 10 20 \
  --backend native_rcspp_inprocess \
  --no-resume
```

50/100 在当前机器上必须使用 host、`--limit 1`、单实例串行，并优先复用已经持久化的 8 GiB
安全配置。正式开始前先确认没有其他 builder/solver，运行中持续观察 RSS；不要无人看守地直接
启动全 20 例。

## 15. 一句话交接

项目已经把 5–30 规模推进到可认证的 native exact Branch-and-Price，也完整实现了 Live SRI
BPC V1；但正式 1040-slot P0 promotion 因 30 规模性能分布失败而 `NOT_PROMOTED`，所以生产
默认和 rollback 都继续是 `no_cut`。若继续 live cuts，先解释正式 30-scale 退化并形成新候选；
50/100 仍由 8 GiB exact label frontier 内存限制主导，暂不扩大求解。

## 16. 2026-07-23 Native Live SRI BPC V1 最终补充

上述“live cuts 尚未形成闭环”的状态已经被本轮实现更新，但默认策略没有改变。

已完成：

- 冻结 `FROZEN_NATIVE_NO_CUT_BASELINE_V1`：commit `ee2f853c...`、engine `66ab52c9b33b4551`，5/10/20/30 共 80/80 exact、no-cheat、零 redline；
- divisor=2 的 SRI-3/SRI-5 完整枚举、canonical ID、top-cap selection；
- active-cut Phase-I、逐列 Native/Python RC reconstruction；
- active-cut mathematics、lineage、true-dual 三类独立 hash 与完整 certificate invalidation；
- Native `uint8_t[16] + active_count` state、完整 active-prefix dominance、17 cuts fail closed；
- P0/P1 root cuts 和 P2 branch cuts，global/local inheritance 与 sibling isolation；
- 1040/1040 formal paired slots：strict cold-start、fresh runtime、AB/BA、no resume、全部 exact、零 redline和合法 certificate binding；
- 50/100 instance001 host/8 GiB/600 秒 bounded no-cut regression，两例都仅因 `host_memory_limit` 合法 incomplete、零 redline；
- signed-zero host dual binding 缺陷已修复，未放宽 hash 检查。

P0 是唯一正式候选。policy hash 为
`9f0e7c4f7e2cab50267e197d55a17950aeee35aad388e47448f24873a7e92ba1`，加入了
`min_restricted_rmp_gain=1e-4` 的预提交性能门控。该门控只决定是否采用可选 cuts，不是 official
proof 来源。

最终不能切换默认值：P0 在 5/10/20 通过性能门槛，但 30 的 live/base mean=`1.087746`、
paired point=`0.959039`、CI 上界=`1.103403`，未达到正式门槛。故
`default_switch_allowed=false`；production default 仍是 `no_cut`，P2 能力保留但默认关闭，
50/100 继续只允许 no-cut。

接手时优先阅读：

- `plan/native_live_sri_v1_validity_and_certificate_boundary_zh.md`；
- `plan/native_live_sri_bpc_v1_implementation_report_zh.md`；
- `runs/native_live_sri_v1_candidate_freeze_20260722/candidate_freeze_manifest.json`；
- `runs/native_spprc_no_cut_5_30_full3600_frozen_v1/baseline_freeze_manifest.json`；
- `runs/native_live_sri_v1_p0_frozen_paired_promotion_clean_v2_20260722/promotion_decision_manifest.json`；
- `runs/native_live_sri_v1_post_promotion_no_cut_50_100_bounded_regression_v2_signed_zero_fix_20260723/bounded_regression_summary.json`。

测试快照：全量 pytest 410 passed + 21 subtests；`tests/native` 36 passed + 16 subtests；
normal Native CTest 2/2；ASAN+UBSAN CTest 2/2。

## 17. 2026-07-23 非零-dual projection 与 packed state 更新

上一节列出的正式 P0 promotion 结论不变：production default 仍为 `no_cut`。在旧候选
`NOT_PROMOTED` 后，已完成两个 exact-safe 性能改进：

1. RMP 保留全部 active cuts，Native pricing 只接收 dual 数值严格非零的 cuts；不用 epsilon，
   `±0.0` 投影掉，任意微小非零值保留。
2. Native overlap state 从 `uint8_t[16]+active_count` 改为精确 packed `uint64_t`：
   SRI-3 用 2 bit 表示 0..3，SRI-5 用 3 bit 表示 0..5。

证书新增 full/projected 双 context hash、双 count、projection flag/schema binding；完整 true
dual hash 仍保留。17 条完整 active cuts 仍在投影前 fail closed。cut-state schema 已升为
`lunar_ice_bpc.native_cut_state.packed_exact_sri3_2bit_sri5_3bit_u64.v2`，旧证书不可复用。
dominance 仍要求精确 overlap state 相等，未实现未经证明的 reward-aware dominance。

当前 in-process engine hash：`8e255a88436e937c`。当前最终代码的定价重放中 projection 使
engine mean 0.540599s 降至 0.316356s（约 -41.5%），packed state 在 guard 前的受控前后
对比中再带来约 3% 的定价时间下降；
`CutState` 17→8 bytes，完整 label `State` 168→152 bytes。scale20 instance009 的单次
strict cold-start 诊断为 no-cut 15.951197s、P0 11.883917s，双方 objective=1.893717、
exact、no-cheat、零 redline。该单例不属于正式 promotion，不能据此切换默认值。

新证据目录：

- `runs/native_live_sri_v1_state_optimizations_20260723/projection_pre_packing_scale20_009.json`；
- `runs/native_live_sri_v1_state_optimizations_20260723/projection_post_packing_scale20_009.json`；
- `runs/native_live_sri_v1_state_optimizations_20260723/projection_post_packing_schema_guard_scale20_009.json`；
- `runs/native_live_sri_v1_state_optimizations_20260723/end_to_end_schema_guard_scale20_009_no_cut/`；
- `runs/native_live_sri_v1_state_optimizations_20260723/end_to_end_schema_guard_scale20_009_p0/`。

最新测试快照：全量 pytest 414 passed + 22 subtests；`tests/native` 39 passed + 17
subtests；normal Native CTest 2/2；ASAN+UBSAN CTest 2/2。

## 18. 2026-07-23 新实验基准冻结与 GAT 主线

完成 projection/packed-state 后的全量单重复 paired benchmark：

- 5/10/20/30 各 20 个实例；
- P0/no-cut 各一次，共 160 slots；
- strict cold-start、fresh runtime、AB/BA、solver resume 关闭；
- 160/160 exact、零 redline；
- P0 在 5/10/20/30 的 mean 为
  `0.389514 / 0.808323 / 24.104670 / 371.514460s`；
- P0 在 5/10/20/30 的 p50 为
  `0.389853 / 0.738066 / 14.371486 / 274.684953s`。

该结果只有单重复，不能改写为 10/3 正式 promotion，但已经冻结为后续 GAT 实验的新 control：

`FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`

入口：

- `runs/frozen_native_live_sri_p0_optimized_baseline_v2_20260723/baseline_freeze_manifest.json`；
- `runs/native_bpc_baseline_registry.json`；
- `plan/GAT_PRICING_AND_BRANCH_GUIDANCE_PREIMPLEMENTATION_PLAN_20260723_ZH.md`。

旧 `FROZEN_NATIVE_NO_CUT_BASELINE_V1` 没有删除或覆盖，继续用于历史复现、纵向比较和 rollback。
production default 仍是 `no_cut`；“新 P0 基准”表示后续 GAT on/off 实验的主要 control，不表示
已经越过正式 release promotion。

GAT 主线已明确为：

1. 引导 pricing candidate/label/harvest 顺序，缓解负列发现和 exact proof tail；
2. 对合法 Ryan–Foster pair 排序；
3. 不引导 cuts，不启用 node-level cut separation；
4. 只允许 immutable typed hints，不能删候选、剪枝、提供 lower bound 或签发 certificate；
5. 最终 official closure 继续由当前 true dual 下的 exhaustive Native exact SPPRC 提供。
