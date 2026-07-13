# 给 Codex 的主提示词：为 GAT_BPC_moonTerk 制定 Native SPPRC/ESPPRC 执行计划

你现在处于 **PLAN ONLY（只制定计划，不修改生产代码）** 模式。

## 仓库与工作范围

- 仓库：`https://github.com/koushiyu1205-debug/GNN-bb`
- 目标目录：`GAT_BPC_moonTerk/`
- 已审计基线提交：`48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e`
- 实际开始时先执行 `git rev-parse HEAD`。如果当前 HEAD 已变化，记录与上述基线的差异，并基于当前 HEAD 制定计划。
- **不要修改、迁移或删除** `gnn_bb/BPC_future/`。
- 不要复用同实例历史成熟列池、mature probe、source probe、人工补列或 per-instance override。

首先完整阅读随本提示提供的：

```text
CODEX_NATIVE_SPPRC_EXECUTION_SPEC.md
```

然后重点检查下列真实文件及其调用关系：

```text
GAT_BPC_moonTerk/README.md
GAT_BPC_moonTerk/scripts/run_lunar_ice_b4_3_spprc_labeling.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/spprc_pricer.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/labeling_pricer.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/resource_label_core.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/bpc/solver/pricing_tail_solver.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/pricing/journey_pricing.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/data.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/columns.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/journey.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/objective.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/branching.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/core/cuts.py
GAT_BPC_moonTerk/src/lunar_ice_bpc/exact/master/journey_rmp.py
GAT_BPC_moonTerk/tests/test_lunar_ice_labeling_pricer.py
GAT_BPC_moonTerk/tests/test_lunar_ice_smoke.py
GAT_BPC_moonTerk/runs/b4_3_current_model_full_report_zh.md
```

## 核心任务

为项目制定一个可执行、文件级、测试级、基准级的实施计划，把当前：

```text
SPPRC_ENGINE_SOURCE = internal_resource_label_core
```

升级为高性能 native C++ SPPRC/ESPPRC 后端，同时完整保留现有 Python BPC orchestration、true-dual audit、branch/cut context、certificate ledger 和 fail-closed 语义。

首选技术路线是：

```text
定制 lab-core/rcspp C++ backend
+ pybind11/scikit-build-core 或等价的稳定 Python binding
+ 现有 SpprcPricingRequest / SpprcPricingResult facade
+ 现有 JourneyColumn 重建与 manual true-RC 复核
```

同时把 `RoutePricer/PathWyse` 作为可选的 **uncertified candidate worker** 评估；BALDES 只作为未来 live subset-row/rank-1 cuts 或完整 BCP 的备选，不要在第一阶段大范围接管当前 BPC 栈。

但是不要盲目接受上述首选。计划中必须先安排一个最小可行性 spike，验证：

1. `lab-core/rcspp` 是否能精确表达循环 multi-sortie journey；
2. 是否能实现 depot-return 后的 capacity/energy/shadow reset；
3. 是否能按当前时间状态计算 weighted completion objective；
4. 是否能保存全局 visited-task elementarity；
5. 是否能返回稳定 arc IDs 以重建 `path_type` 和 sortie partition；
6. 是否能对 `COMPLETE/TIMEOUT/MEMORY_LIMIT/INTERRUPTED/MAX_SOLUTIONS` 做严格状态映射；
7. 是否支持或能够以小范围扩展实现 Ryan–Foster branch state；
8. 若公共 API 不足，应明确选择“最小 fork/extension”还是“项目内自研 native labeler”，不得用不精确的图展开掩盖模型缺口。

## 必须达到的效果

修改后的代码必须：

- 在 `5, 10, 20, 30, 50, 100` 六种规模上都能启动、建模、定价、输出稳定状态和审计数据；
- `5/10/20` 保持 exact objective、列语义、true reduced cost 和证书不变，并有明确性能优化；
- `30` 规模首先在严格 cold-start、无 mature probe 条件下获得 `BPC_TREE_OPTIMAL`，硬门槛不超过 1800 秒；目标不超过 900 秒，stretch goal 不超过 600 秒；
- `50/100` 至少达到 exact-safe 可用：不崩溃、不 OOM 失控、支持时间/内存限制与恢复、能返回 true-dual 复核通过的负列；若搜索未完整，必须返回 `INCOMPLETE_LIMIT` 等非证书状态，不允许假装最优；
- 在任何规模上都不能因为 worker 没找到列、超时、K-column early stop、稳定化 dual 或 GAT 建议而发出 no-negative certificate；
- 任何 official no-negative/optimality 结论必须来自当前 true RMP dual 下的完整 exact search，并通过现有 manual reduced-cost、branch、cut、reconstruction 和 certificate audit；
- 保留 cold-start no-cheat 规则、config hash、engine build hash、依赖版本、column provenance 和可复现实验记录。

## 允许安装依赖

环境中缺少库、编译器或构建工具时，可以自行下载和安装，包括但不限于：

```text
cmake
ninja
scikit-build-core
pybind11
highspy
pytest
numpy
lab-core/rcspp
routepricer
合适的 GCC/Clang C++23 工具链
```

要求：

- 优先使用隔离虚拟环境；
- 记录完整安装命令、版本、Git commit 和许可证；
- 固定依赖版本或 commit；
- 下载只能用于工具链和开源依赖，不得下载预先求好的同实例列池、probe、solution 或其他会污染 cold-start 的求解结果；
- 若依赖许可证与项目目标冲突，计划中必须标红并给出替代方案。

## 计划必须包含

请输出一份实施计划，而不是泛泛建议。计划至少包含：

1. 当前代码调用图与 bottleneck 复核；
2. 架构决策记录：为何选定某个 backend；
3. native state、graph、arc、resource、dominance、elementarity、objective、depot reset、branch/cut state 的具体设计；
4. exact mode 与 worker mode 的严格分工；
5. 需要新增、修改、保留不动的文件清单；
6. 每个阶段的前置条件、改动、测试、退出门槛和回滚点；
7. 依赖安装及构建命令；
8. 5/10/20/30/50/100 的测试和 benchmark matrix；
9. 与当前 internal oracle 的 differential test 方案；
10. timeout、interrupt、memory limit、K-solution early stop 的 fail-closed 测试；
11. Ryan–Foster branch 和 fleet/subset-row cut 的逐级支持计划；
12. 30-scale cold-start 性能目标和逐层 profile 方法；
13. 50/100 的内存、checkpoint/resume 和 exact-safe 可用性方案；
14. 风险清单、替代路线、停止条件；
15. 完成定义（Definition of Done）。

计划需要精确到函数、类、文件、命令和验收指标。不要只写“优化 C++”“增加测试”“跑 benchmark”这种抽象条目。

## 不可违反的规则

- 不得删除或绕过现有 certificate/audit 逻辑。
- 不得把 `RoutePricer/PathWyse` 的 no-column 结果直接当 official certificate。
- 不得用 GAT/kNN/OOD 永久删除 exact search 中的可行 arc 或 true-negative column。
- 不得把 timeout、memory limit、interrupt、label cap、max solutions 或 incomplete frontier 解释为 exhaustive completion。
- 不得只针对 `30-instance001` 写硬编码或 per-instance 调参。
- 不得以历史成熟列池证明 cold-start 性能。
- 不得在 exact mode 开启未经证明安全的 dominance、completion bound、bidirectional join 或 discretization。
- 不得静默改变 objective、时间窗、recharge、path type、branch 或 cut 语义。
- 不得在计划阶段直接实施大规模重构。

## 本次只输出计划

本次不要修改生产代码。可以做只读检查、构建能力探测和最小临时 feasibility experiment，但不要提交实现。

将最终计划写入：

```text
GAT_BPC_moonTerk/plan/07_native_spprc_backend_execution_plan.md
```

同时在回答中给出：

- 计划文件路径；
- 关键架构选择；
- 最大的三个风险；
- 第一阶段最小可验证里程碑；
- 需要安装的依赖及其固定方式。
