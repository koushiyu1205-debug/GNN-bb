# DSSR V2 实施与门槛状态（2026-07-29）

## 结论

`multi_sortie_counterexample_pressure_refinement_v2` 已完成独立后端、绑定、
telemetry、IPC、测试、验证数据隔离和 fail-closed promotion 基础设施。

当前候选没有通过性能门槛，因此：

- P0 V3 继续作为正式基准；
- DSSR V1 继续作为失败候选归档；
- DSSR V2 不得物化 selected config，不得冻结，不得运行 locked test；
- 不得启动 DSSR 冻结后的 GAT one-deviation oracle；
- production `no_cut` 不变。

这不是正确性失败。九个预提交压力配置均 exact-safe 地闭合了
scale20/011；失败原因是运行时间显著高于 P0。

## P0、纯 DSSR 与 ng-DSSR 的状态结构

### P0 elementary pricer

P0 的标签维护完整 `visited` task bitset。已经访问的 task 不能再次扩展，
dominance 也比较完整访问状态。一次搜索直接求 elementary SPPRC。

### 当前 DSSR V2

当前实现是纯 DSSR，不是 ng-DSSR：

```text
dominance key = visited & (critical_mask | branch_mask)
```

初始 `critical_mask` 为空。非critical task 可在内部松弛路线中重复；若负路线
不是 elementary，则审计其全部重复 task，将它们加入 critical mask 后重启。
压力触发时，从最拥挤 bucket 选择访问位分割最均衡的非critical task加入
critical mask，再确定性重启。

任何 non-elementary 路线都不能公开为 master column。只有搜索穷尽、
frontier empty、zero label drop 且没有负路线时才可签发 no-negative
certificate。

### ng-DSSR

ng-DSSR 需要另一种标签状态：每个 task/node 有独立邻域集合，标签携带沿路径
更新的 ng-memory。循环修复不再只是把一个 task 全局加入 critical mask，
而是更新造成 ng-cycle 的局部邻域记忆关系。

当前代码没有 ng-memory、每节点邻域状态或 ng-DSSR policy。若研究它，必须
建立新的 policy/config/engine hash，并继续对公开列做完整 elementarity
审计；不能把它静默归入 DSSR V2。

## 已实现内容

- DSSR V2 公开 elementary 负列批次：
  - public target 继承请求，最大 64；
  - Native raw pool 为其四倍，最大 256；
  - 审计全部 raw 负路线；
  - elementary 路线去重后批量返回；
  - 所有 non-elementary 路线的重复 task 都进入 critical set。
- dominance-pressure refinement：
  - bucket 网格：4096、8192、16384；
  - candidate-check 网格：5000万、2亿、8亿；
  - 确定性 balanced split 与 task-ID tie-break；
  - 压力轮不公开 column 或 certificate；
  - 所有 task 已 critical 时不再错误触发无可用 split，而是继续完整
    elementary 搜索。
- 新增请求、canonical binding、Native binding 和 telemetry 字段。
- 新增 V2 in-process/host backend ID，V1 与 P0 ID 不变。
- 新增 90 个 content-hash 锁定实例：
  - 5/10/20/30：每规模 12 development、8 locked；
  - 50/100：每规模 3 development、2 locked；
  - development 54，locked 36；
  - 与已有正式/历史实例 content-hash overlap 为零。
- 新增：
  - fresh-runtime P0/DSSR 配对验证器；
  - locked test single-use receipt；
  - sentinel、development、locked、freeze、GAT oracle 顺序门禁；
  - 隔离 host RSS 测量；
  - 只在全部门槛通过后才能物化配置和冻结 candidate 的脚本。

## scale20/011 预提交网格结果

持久证据：

```text
runs/dssr_v2_development_20260729/grid_scale20_011/summary.json
```

| bucket | checks | DSSR/P0 wall ratio | 结果 |
|---:|---:|---:|---|
| 4096 | 5000万 | 1.613 | fail |
| 4096 | 2亿 | 2.787 | fail |
| 4096 | 8亿 | 3.085 | fail |
| 8192 | 5000万 | 1.599 | fail |
| 8192 | 2亿 | 2.923 | fail |
| 8192 | 8亿 | 9.027 | fail |
| 16384 | 5000万 | 1.622 | fail |
| 16384 | 2亿 | 3.239 | fail |
| 16384 | 8亿 | 9.983 | fail |

最优配置的 P0 为 16.84 秒，DSSR V2 为 26.93 秒，峰值 RSS 约
1.26 GiB。它做了 18 次 pressure refinement，最终 20/20 task 全部
critical，累计约 22.4 亿 dominance candidate checks。

因此当前退化不是内存造成的，而是：

```text
多轮松弛搜索和重启成本
+ 最终接近 P0 的 full-elementary proof
> DSSR 在早期松弛中节省的工作
```

九组全部达到 safety、zero extra incomplete；没有一组达到
scale20/011 的 `DSSR wall <= 1.10 * P0 wall`。由于该门槛是进入
scale30 sentinel 的前置必要条件，验证在此确定性停止。

## 测试

隔离 build：

```text
build/native-spprc-dssr-v2
```

最终结果：

```text
CTest: 2/2 passed
Pytest: 105 passed, 22 subtests passed
```

覆盖批量 mixed elementary/non-elementary、压力轮零结果泄漏、
branch/cut context、host IPC、timeout/memory fail-closed、canonical
binding、split/freeze 门禁和 locked-test 防泄漏。

## 后续边界

若继续定价松弛方向，最有根据的下一候选是独立 ng-DSSR V3，因为当前失败
证据正是纯 DSSR 的 global critical mask 最终退化到 full critical。
但 ng-DSSR 也会增加标签状态、削弱 dominance，不能假定必然更快。

在修改任何代码前，应先冻结同一 scale20/011 dual snapshot，比较：

```text
P0 elementary
vs pure DSSR V2
vs ng-DSSR V3
```

并要求 ng-DSSR V3 首先通过同一 `<=1.10 * P0` 门槛。未通过时仍不得运行
六规模 development、locked test 或 GAT。

后续验证已经完成，结论为否决，详见：

```text
docs/NG_DSSR_V3_IMPLEMENTATION_AND_GATE_STATUS_20260729_ZH.md
```
