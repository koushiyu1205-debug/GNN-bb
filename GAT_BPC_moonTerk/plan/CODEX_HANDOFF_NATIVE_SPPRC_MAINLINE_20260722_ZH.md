# GAT_BPC_moonTerk 当前主线与 Native SPPRC 交接文档

更新时间：2026-07-22

面向对象：接手本项目的下一个 Codex 对话

当前工作目录：`/home/kai/work/GAT_BPC_moonTerk`

## 0. 接手者先读结论

当前项目最成熟的主线不是“GAT 已经驱动求解”，也不是“live cuts 已经投入正式
Branch-Price-and-Cut”。当前真正通过 release gate 的主线是：

> HiGHS restricted master + native exact SPPRC pricing + Ryan–Foster branching，
> 即具备真分支、真列生成和 exact no-negative pricing proof 的 Branch-and-Price。

具体边界如下：

- 生产默认 exact backend 已经是 `native_rcspp_inprocess`；
- 5/10/20/30 规模已有 exact closure 和 promotion 证据；
- 30 规模曾完成 20/20 strict cold-start exact，p50 为 `327.598609s`，最大
  `1679.705969s`；
- Ryan–Foster `same_journey/different_journey` 已进入真实 B&B 子节点；
- Python exact backend 没有删除，仍是 reference、fallback 和 rollback；
- native subset-row/fleet cut state 的代码和小规模 differential 已存在，但默认关闭，
  live master cuts 也关闭，所以不能把当前默认主线称为已经启用切割的完整 BPC；
- 50/100 各 20 个正式实例已经生成并验收，但前 5 个实例的求解均在 root exact
  pricing 先达到 8 GiB host memory limit，尚未得到 50/100 最优解时间；
- 50/100 当前首要问题是 exact label frontier 的内存/数量增长，不是把 1800 秒改成
  3600 秒；
- 下一步不建议继续扫参数，也不建议先开 live cuts、GAT 或 bidirectional。先补 native
  host 的搜索心跳与内存剖面，再根据“单标签太重”还是“活标签数量爆炸”决定优化路径。

## 1. 当前代码与证据快照

### 1.1 Git 与实现基线

- 当前 Git 根目录：`/home/kai/work`；
- 本文核对时的 HEAD：`c1a3f570dbe926af4d1e1dbb3ac45225e29a97d4`，提交标题 `720`；
- native 实施最初冻结基线：`48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e`；
- upstream：`lab-core/rcspp@2f1d53ba6806844e30ce43ee9c41041a5a1b4e79`；
- 当前没有 solver-core fork，也没有 core patch；采用 pinned upstream + project-local
  C++ resource/extension + pybind adapter；
- feasibility spike 发现的 pressure/false-COMPLETE 风险可通过 exact 配置禁止 label
  trimming 规避，因此当前 patch queue 为空，`fork_required=false`。

当前本机扩展返回的 engine hash：

- in-process：`66ab52c9b33b4551`；
- persistent host：`ee0ea1fb74eb8035`。

不要把 hash 当成手填版本号。正式 artifact 必须同时绑定 instance、model、objective、
config、dual、branch/cut context 和 engine build hash；运行中 hash 漂移必须 fail closed。

### 1.2 本次交接前的快速验证

本次只重跑了低风险的 native gate：

```text
ctest --test-dir build/native-spprc --output-on-failure
  -> 2/2 passed

python -m pytest -q tests/native
  -> 34 passed, 17 subtests passed
```

历史完整 gate 记录为 `395 passed + 22 subtests passed, 0 failed`，但本次没有重跑全量
pytest，接手者不要把“历史全量”和“本次快速验证”混写成同一次测试。

### 1.3 当前机器资源边界

本文核对时：

- 物理内存约 15 GiB，约 12 GiB available；
- swap 约 4 GiB，几乎未使用；
- 磁盘尚有约 822 GiB；
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
- cut framework 虽然存在，但 live master cuts 默认关闭。

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

### 6.2 已实现/差分，但默认关闭

- subset-row `floor(overlap/divisor)` threshold-crossing state；
- fleet-cut coefficient state；
- positive-cover completion bound。

关闭原因：

- cut state 尚未通过正式 live-master-cut promotion；
- completion bound 在真实 RMP dual 上 prune count 为 0，并出现慢例，尚未提供生产收益；
- `Phase-I + nonempty cut` 当前仍显式 fail closed。

### 6.3 尚未实现或尚未获得 exact role

- resource partition/bucket algorithm；
- bidirectional join；
- live cut certification；
- PathWyse/DSSR/NG 的 exact-certificate role。

NG/DSSR/其他 worker 现在最多只能产生候选列，不是 proof source。将来只有完成 lunar
multi-sortie 表达、license 审计和 certificate differential，才能重新评估 exact role。

## 7. 当前各规模的可复用证据

### 7.1 5/10/20/30

| Scale | 当前 exact 证据 | total-wall 统计 | 备注 |
|---:|---|---|---|
| 5 | 20/20 exact | mean `0.406318s`，p50 `0.406548s`，max `0.431486s` | pricing-core native `0.000328s` vs Python `0.002829s`，8.64x |
| 10 | 20/20 exact | mean `0.828971s`，p50 `0.761838s`，max `1.252164s` | pricing-core native `0.008953s` vs Python `0.034181s`，3.82x |
| 20 | 20/20 exact | mean `31.171581s`，p50 `17.648412s`，max `124.627828s` | root mean `10.767889s`，tree mean `20.067419s` |
| 30 | 20/20 exact | mean `453.915594s`，p50 `327.598609s`，max `1679.705969s` | root p50 `124.933467s`，tree p50 `213.869142s` |

30 的难例曾采用“先给 3600 秒拿到真 exact 时间，再剖析结构热点”的策略：

- instance012 旧实现 `3326.290682s` exact，定位 subset dominance 索引热点后降到
  `1474.584039s`；
- instance014 旧实现 `2069.018683s` exact，inline visited mask 后 production run 为
  `1679.304927s`。

这说明 30 规模优化不是纯调参：先获得合法 exact closure，再固定 instance/dual/branch
context 做结构 A/B，是正确做法。

### 7.2 一个必须补救的证据问题

上述 5/10/20/30 最终数字已写入仓库报告，但当时的部分完整 raw artifacts 位于：

```text
/tmp/native-spprc-fixed-mask-gate-5-10-20-current
/tmp/native-spprc-fixed-mask-scale30-full20-current
/tmp/native-spprc-subset-index-scale30-012-1800-current
/tmp/native-spprc-fixed-mask-scale30-014-1800-current
```

本文核对时这些目录已经不存在。因此：

- 报告内仍保留当时结论、hash、aggregate 和关键 differential 数据；
- 但下一个正式 release 不能继续依赖已消失的 `/tmp` 原始目录；
- 需要把一次最小复现 gate，以及下一次计划内的完整 30 batch，直接写入 `runs/`；
- 新 artifact 必须含 row JSON/CSV、config、engine/instance hash、summary 和 no-cheat audit。

不要因为原始目录缺失就否定已经完成的实现，也不要反过来把只有 Markdown 汇总的旧数字冒充
当前 HEAD 的新鲜重跑证据。

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

### P3：之后再 promotion cuts 和其他高级功能

live cuts 的建议顺序：

1. 5/10 nonempty cut full/representative differential；
2. 20/30 固定 root 和 branch-child dual snapshot；
3. Phase-I + nonempty cut 的 fail-closed 边界改为正式支持；
4. cut-state-aware dominance 和 certificate ledger；
5. 小规模 live master cut A/B；
6. 有稳定收益且无 certificate leak 后才进入默认主线。

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

建议下一个对话接受以下任务，而不是直接跑大规模实例：

> 在不改变任何 official result、column pool 或 certificate 语义的前提下，为
> `NativeRcsppHostBackend` 和 native exact core 加入固定大小 heartbeat telemetry；建立真实
> scale50 instance001 的固定 true-dual snapshot；在 2/4/6/8 GiB cap 下串行测量 label
> 数量、bucket 分布、dominance 效率和 bytes/live-label；输出一份决定“先做 packed arena
> 还是先做长-mask subset index”的证据报告。

该任务的 Definition of Done：

- default-off 或 telemetry-only，不改变 solver/certificate；
- host hard kill 后能返回最后 heartbeat；
- telemetry 本身有固定内存上限；
- 5/10/20 differential 和 current native tests 不回归；
- scale50 snapshot 每档都有 hash、RSS 曲线、label 曲线和结论；
- 未运行 20 个 scale100，不触发系统 OOM/reboot；
- 报告和 raw artifact 写入 `runs/`，不写 `/tmp`。

## 13. 常用入口与文件地图

### 当前结论与计划

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

. .venv-native-spprc/bin/activate
ctest --test-dir build/native-spprc --output-on-failure
python -m pytest -q tests/native
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

项目已经把 5–30 规模推进到可认证的 native exact Branch-and-Price，并通过 30 规模默认
release；高级 cut/completion 框架只完成了部分实现和 differential，尚未进入默认 live-cut
主线。50/100 的数据已齐，但求解先被 exact pricing 的 8 GiB 标签内存压垮。下一步最有价值
的工作是补 hard-kill 前的 label/frontier 内存遥测和固定 dual snapshot，再用证据决定 packed
label arena 与长-mask dominance index 的先后，而不是继续调时间、开 GAT 或堆更多高级功能。

## 16. 2026-07-22 Native Live SRI BPC V1 实施补充

上述“live cuts 尚未形成闭环”的状态已经被本轮实现更新，但默认策略没有改变。

已完成：

- 冻结 `FROZEN_NATIVE_NO_CUT_BASELINE_V1`：commit `ee2f853c...`、engine `66ab52c9b33b4551`，5/10/20/30 共 80/80 exact、no-cheat、零 redline；
- divisor=2 的 SRI-3/SRI-5 完整枚举、canonical ID、top-cap selection；
- active-cut Phase-I、逐列 Native/Python RC reconstruction；
- active-cut mathematics、lineage、true-dual 三类独立 hash 与完整 certificate invalidation；
- Native `uint8_t[16] + active_count` state、完整 active-prefix dominance、17 cuts fail closed；
- P0/P1 root cuts 和 P2 branch cuts，global/local inheritance 与 sibling isolation；
- 50/100 instance001 host/8 GiB/600 秒 bounded no-cut regression，两例均合法 incomplete、零 redline；
- paired promotion runner 已实现并通过 dry-run。

当前选择 P0 作为唯一 screened candidate。最终 policy hash 为
`9f0e7c4f7e2cab50267e197d55a17950aeee35aad388e47448f24873a7e92ba1`，加入了
`min_restricted_rmp_gain=1e-4` 的预提交性能门控。该门控只决定是否采用可选 cuts，不是 official
proof 来源。

当前不能切换默认值：P0 尚未完成正式 fresh paired promotion，30_017 的门控版单次比值约
0.916，也未达到计划要求的 0.90。故 production default 仍是 `no_cut`；P2 能力保留但默认关闭；
50/100 继续只允许 no-cut。

接手时优先阅读：

- `plan/native_live_sri_v1_validity_and_certificate_boundary_zh.md`；
- `plan/native_live_sri_bpc_v1_implementation_report_zh.md`；
- `runs/native_live_sri_v1_candidate_freeze_20260722/candidate_freeze_manifest.json`；
- `runs/native_spprc_no_cut_5_30_full3600_frozen_v1/baseline_freeze_manifest.json`。

测试快照：全量 pytest 406 passed + 21 subtests；normal Native CTest 2/2；ASAN+UBSAN CTest 2/2。
