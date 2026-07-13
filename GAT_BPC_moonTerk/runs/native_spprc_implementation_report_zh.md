# Native SPPRC backend 实施与 promotion 报告

## 1. 实施边界

基线提交为 `48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e`，upstream 固定为
`lab-core/rcspp@2f1d53ba6806844e30ce43ee9c41041a5a1b4e79`。未建立 fork，未修改
solver core；当前采用 standalone CMake、project-local C++ resource/extension、pybind
adapter 与 Python reference fallback。upstream pressure false-COMPLETE 可通过 exact 配置
禁用 label trimming，因此 patch queue 为空，`fork_required=false`。

当前 engine hash：

- in-process：`3d5081528195f028`；
- persistent host：`7b697d461682dda3`。

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
  visited-subset dominance。v1 acceptance 默认全部关闭。

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
- `tests/native`：26 passed，另 4 个 subtests passed；
- 最终 cut/subset state 版本的 ASAN/UBSAN CTest 2/2 通过；
- 全量 pytest：379 passed、4 failed、4 subtests passed；4 个已知失败在 detached baseline
  上同样复现，不属于本轮 regression。

## 4. 性能与规模 gate

### 4.1 5/10 pricing-core 与 total-wall

最终代码、warm import、固定 zero-dual snapshot 的 pricing-core p50：

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

完整 20/20 acceptance：20 个实例全部 `BPC_OPTIMAL`、zero redline；batch wall
`753.150091s`，total p50 `20.336471s`，root p50 `9.427522s`，最大 total
`251.347976s`。难例 instance012 使用最终默认 feature flags 的基线为约 251.35 秒。

completion bound A/B 虽保持 exact certificate，但真实 RMP dual 下 prune count 为 0，
instance012 为 257.43 秒；不 promotion。visited-subset dominance 保持 global optimum/proof，
但会省略被支配的 negative variants，且集成试验未触发有效 checks；同样默认关闭。

### 4.3 30-task technical promotion

- instance001：`BPC_OPTIMAL`，245.67 秒（另一次 cache run 241.49 秒），远小于 1800 秒；
- 001–003：分别约 245.67、998.07、357.24 秒，均 exact；
- 004 最终代码复跑：总 1805.16 秒（含 runner 收尾），root 150.02 秒、tree
  1654.37 秒；合法 `BPC_INCOMPLETE_PRICING`，无 certificate leak。005 的既有最终映射
  结果同为合法 1800 秒 incomplete；
- instance009：加入 native branch + Phase-I 后约 18 秒 `BPC_OPTIMAL`；
- instance012：提高 branch-depth gate 后约 247 秒、19 nodes exact。

这满足“正确 closure 或合法 incomplete、无证书泄漏”的 technical opt-in 边界，但不满足
Phase 11 默认切换所需的完整 20/20 exact closure。

### 4.4 50/100 persistent-host bounded gate

60 秒单时钟 bounded run：

| scale | rounds | 审计加入列 | host graph reuse | peak RSS | 结果 |
|---:|---:|---:|---:|---:|---|
| 50 real-map | 56 | 5376 | build 1 / hit 55 | 784,183,296 B | legal incomplete |
| 100 synthetic acceptance | 56 | 7168 | build 1 / hit 55 | 125,497,344 B | legal incomplete |

两行最终均为 `BPC_INCOMPLETE_PRICING / INCOMPLETE_LIMIT`、zero redline；最后的
MAX_SOLUTIONS partial columns 分别保留 96/128 列。100-task fixture 由
`domain.scheduling.generate_instance(100, seed=1629001)` 生成，100 tasks、10,100 edges、
schema issues 0、`validation.accepted=true`。

同 config 的 terminal-row resume 在约 0.17 秒返回且不重跑；将 row limit 从 60 改为 61
后，runner 以不同 `config_hash` 立即拒绝 resume（return code 2）。host 不序列化内部 labels。

## 5. Release 结论

Technical promotion 已通过：native in-process exact 可以显式 opt-in，Ryan–Foster 可用于
非 root，Python reference 始终保留。Default release 尚未通过，原因仅陈述为当前证据：

- 30-scale 004/005 尚未在 1800 秒内 closure；
- 完整 30-scale 20/20 default-release batch 尚未达到 median ≤900 秒；
- completion bound、subset dominance、bidirectional 等高级优化尚未形成可 promotion 收益。

因此 `exact_backend` 默认值不得切到 native；live cut certification 也保持默认关闭。
