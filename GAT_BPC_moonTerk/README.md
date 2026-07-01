# GAT_BPC_moonTerk

这是从 `BPC_future` 重构出来的新项目骨架。当前阶段只建立目录边界，不迁移、不修改、不删除 `BPC_future` 中的任何文件。

核心原则：

- `exact/` 是能影响数学证明的 Branch-Price-and-Cut 内核。
- `guidance/` 是 GAT / kNN / OOD / policy 引导层，只能影响排序、优先级、有限延迟和 shadow 决策。
- GAT 不是 pricing oracle，不能产生 certificate，不能产生 official lower bound，不能永久丢弃 true reduced-cost negative column。
- 所有 official bound、no-negative certificate、fathom / prune、OPTIMAL 声明必须来自 exact path。
- 数据、训练、replay、审计、benchmark 全部通过显式 artifact schema 连接，避免再把语义散落在脚本文件名里。

## 目录结构

```text
GAT_BPC_moonTerk/
  configs/
  docs/
  data/
  runs/
  src/
    lunar_ice_bpc/
      domain/
      io/
      runners/
      exact/
      guidance/
  scripts/
  tests/
```

## 根目录

| 路径 | 含义 |
| --- | --- |
| `README.md` | 项目目录边界、proof contract、文件夹职责说明。 |
| `configs/` | 所有可复现实验和求解配置。配置只声明行为，不放运行结果。 |
| `docs/` | 设计文档、交接文档、实验报告。文档不作为运行时输入。 |
| `data/` | 数据输入、中间数据、训练数据、manifest。原则上不放一次性日志。 |
| `runs/` | 一次运行产生的日志、CSV、solution、checkpoint 等输出。 |
| `src/` | 可 import 的正式代码。核心逻辑必须进入这里，而不是堆在 `scripts/`。 |
| `scripts/` | 薄命令入口。只负责参数解析和调用 `src/lunar_ice_bpc/` 中的实现。 |
| `tests/` | 单元测试、集成测试、proof/guidance contract 测试。 |

## configs

| 路径 | 含义 |
| --- | --- |
| `configs/base/` | 默认基础配置，例如 exact solver 默认参数、日志字段、数据路径模板。 |
| `configs/benchmarks/` | 固定 benchmark matrix 配置。只能放正式验收用配置，默认必须 exact-safe。 |
| `configs/experiments/` | 临时 opt-in 实验配置，例如 GAT priority、delay queue、branch probe。任何 unsafe 或 diagnostic-only 开关只能在这里显式出现。 |

配置规则：

- baseline config 不默认启用 GAT mutating behavior。
- benchmark config 不能让 GAT、kNN、OOD 参与 certificate 或 official bound。
- 任何 checkpoint、threshold、OOD rule、safe-source rule 都必须有版本/hash 字段。

## docs

| 路径 | 含义 |
| --- | --- |
| `docs/design/` | 长期设计和数学边界，例如 global remaining RC lower bound、frontier certificate、branch probe、cut context。 |
| `docs/handoffs/` | 给下一轮实现或新会话看的中文交接文档，记录主线、目标、阻塞、测试过的方法。 |
| `docs/reports/` | 实验和 benchmark 报告。报告必须区分 proof result、diagnostic result、heuristic result。 |

文档规则：

- 设计文档必须写明该方案是否能影响 official proof。
- 报告中不能用普通 F1 替代 ROI、safe precision、false-safe、coverage、OOD delay 等 gate 指标。
- 若实验只证明 heuristic acceleration，不能写成 exact optimality 改善。

## data

| 路径 | 含义 |
| --- | --- |
| `data/raw_maps/` | LOLA / Diviner / M3 / LEND 等真实栅格数据的本地落盘区；`README.md` 记录第一版期望文件名。 |
| `data/instances/` | synthetic polar resource grid 生成的 lunar-ice CVRPTW logical graph 实例。 |
| `data/interim/` | 可重新生成的中间文件，例如 replay capture、candidate pool、临时 tensor。 |
| `data/processed/` | 训练、审计、benchmark 可以直接消费的数据集，例如 target rows、batch samples、hard pairs。 |
| `data/manifests/` | 数据 manifest、split manifest、schema version、checkpoint/hash 绑定记录。 |

数据规则：

- label 字段和 model input 字段必须分开。
- kNN/OOD、threshold、stage4 gate 字段只能作为 audit outcome，不能进入 model input。
- true-RC negative 的 delay label 不能混成 reject/nonnegative label。

## runs

| 路径 | 含义 |
| --- | --- |
| `runs/logs/` | JSONL、solver trace、audit trace。 |
| `runs/csv/` | benchmark summary、A/B summary、audit summary CSV。 |
| `runs/solutions/` | 求解输出 solution artifact。 |
| `runs/checkpoints/` | 训练 checkpoint、calibration artifact、safe-source export。 |

运行结果规则：

- `runs/` 只放输出，不作为长期源数据。
- 如果某个 run 要进入训练或报告，必须在 `data/manifests/` 中登记 provenance。
- checkpoint 不自动 production-ready；必须经过 Stage 3/Stage 4 gate 记录。

## src/lunar_ice_bpc

| 路径 | 含义 |
| --- | --- |
| `src/lunar_ice_bpc/domain/` | 月表水冰场景参数、synthetic polar resource grid、路径和可视化。 |
| `src/lunar_ice_bpc/io/` | instance / solution / manifest 的稳定读写和 schema 校验。 |
| `src/lunar_ice_bpc/runners/` | 生成、求解、benchmark 的薄运行实现。 |
| `src/lunar_ice_bpc/exact/` | exact BPC 内核。这里是 proof boundary；当前阶段包含 core data、timed sortie、journey column、manual reduced-cost 公式和小规模 canonical universe baseline。 |
| `src/lunar_ice_bpc/guidance/` | GAT 和安全壳引导层。这里只能给建议，不能证明。 |

当前可运行入口：

```bash
python scripts/self_check.py
python scripts/generate_lunar_ice_benchmark.py --scales 5,10 --per-scale 1
python scripts/run_lunar_ice_bpc.py --instance data/instances/lunar_ice_005/instance_001_logical_graph.json
python scripts/run_lunar_ice_bpc.py --config configs/benchmarks/lunar_ice_5_journey.yaml
python scripts/run_lunar_ice_benchmark.py --manifest data/manifests/lunar_ice_benchmark_manifest.json --max-workers 4
python scripts/run_lunar_ice_benchmark.py --config configs/benchmarks/lunar_ice_5_journey.yaml --max-workers 1
python scripts/audit_lunar_ice_benchmark.py --results-csv runs/csv/lunar_ice_005_benchmark.csv --scales 5 --expected-per-scale 20 --output-json runs/csv/lunar_ice_005_benchmark_audit.json
python scripts/audit_lunar_ice_refactor.py --output-json runs/logs/lunar_ice_refactor_audit.json --instance-samples-per-scale 1
python scripts/run_lunar_ice_gat_shadow.py --instance data/instances/lunar_ice_005/instance_001_logical_graph.json
python scripts/run_lunar_ice_gat_shadow.py --config configs/experiments/lunar_ice_20_gat_shadow.yaml
python scripts/run_lunar_ice_b5_guidance_suite.py --config configs/base/b5_guidance_suite_base.yaml
python scripts/run_lunar_ice_b5_guidance_suite.py --config configs/base/b5_guidance_ordering_suite_base.yaml
python scripts/run_lunar_ice_b5_guidance_suite.py --config configs/base/b5_guidance_pricing_ordering_suite_base.yaml
python scripts/run_lunar_ice_b5_guidance_suite.py --config configs/base/b5_guidance_branch_ordering_suite_base.yaml
python scripts/run_lunar_ice_b5_guidance_suite.py --config configs/base/b5_guidance_harvest_ordering_suite_base.yaml
python scripts/draw_lunar_ice_instance.py --instance data/instances/lunar_ice_005/instance_001_logical_graph.json
python scripts/download_lunar_real_maps.py --dry-run --print-curl
python scripts/download_lunar_real_maps.py --layers lola_avg_solar_visibility
python scripts/draw_lunar_real_map_preview.py
python scripts/download_lunar_real_maps.py --layers lola_dem
python scripts/draw_lunar_real_map_preview.py --target-count 100 --path-target-count 3 --output-json data/processed/real_maps/south_pole_sp50_preview.json --output-svg runs/figures/lunar_real_map_sp50_preview.svg --output-dem-svg runs/figures/lunar_real_map_sp50_dem.svg
python scripts/generate_lunar_real_map_instance.py --scale 5 --seed 629001 --index 1 --strict
python scripts/run_lunar_ice_bpc.py --instance data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json --solution runs/solutions/lunar_ice_sp50_005_instance_001_solution.json --direct-baseline-max-tasks 5 --canonical-dp-max-tasks 5 --direct-pricing-max-tasks 5
python scripts/draw_lunar_ice_instance.py --instance data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json --solution runs/solutions/lunar_ice_sp50_005_instance_001_solution.json --output runs/figures/lunar_ice_sp50_005_instance_001_solution.svg --also-dem --output-dem runs/figures/lunar_ice_sp50_005_instance_001_solution_dem.svg
```

当前 `run_lunar_ice_bpc.py` 会先尝试小规模 exhaustive direct-DP baseline：当任务数不超过 `direct_baseline_max_tasks` 时，枚举固定 logical graph 上三条路径的所有 per-leg 组合、feasible sortie 和单车 journey，再做 fleet set-partition；此时可输出 `DIRECT_DP_BASELINE_OPTIMAL` 和 `exact_status=EXACT_BASELINE_OPTIMAL`。如果同一节点的 fixed-graph pricing closure 满足完整 task-subset 覆盖、RMP dual 绑定、completion-bound on/off 一致、且最小 reduced cost 非负，或 complete fixed-graph direct-root LP 满足 dual binding 与非负 reduced-cost 条件，则会生成作用域限定为固定三路径 logical graph 的 true-dual BPC certificate。当前 5-task benchmark 通过 pricing-closure 证书链闭合，10-task benchmark 通过 direct-root 证书链闭合；20-task benchmark 仍只有 fixed-graph exact baseline，大规模会退回 reference 或 seeded-pool incumbent，并报告 analytic relaxation gap 和 seeded RMP/pricing workload。

`download_lunar_real_maps.py` 只负责真实地图文件准备：默认选择 LOLA slope / roughness / PSR 三个必需层，支持 `--dry-run --print-curl` 输出下载命令，支持 `--probe-only` 做连通性诊断，也可以直接下载到 `data/raw_maps/` 并写 `data/manifests/lunar_real_map_download_manifest.json`。`lola_dem` 是可选但推荐下载的 80 m DEM 层；`lola_avg_solar_visibility` 是推荐下载的 illumination 层，用于 depot 选址和永昼峰证据。存在 DEM 时 real-map directed edge 会用 signed elevation gain/loss 区分上坡和下坡的时间、能耗和风险。失败时 manifest 会记录 source URL、错误和 partial 文件状态，便于换网络后继续处理。`draw_lunar_real_map_preview.py` 是真实数据接入的第一层，不会调用 BPC。它读取 `data/raw_maps/` 下的本地 GeoTIFF，默认使用 dense water-ice benchmark depot `[-9.90, -19.10] km`，并以该 depot 为中心裁剪 `50 x 50 km` ROI，生成 source catalog、preview JSON、resource/risk SVG 和 DEM SVG；缺少真实数据时输出 `MISSING_REQUIRED_REAL_MAP_LAYERS`，并明确记录 `uses_synthetic_fallback=false`。远程 URL 只作为 provenance 记录，只有显式加 `--allow-remote` 才尝试在线读取；如需恢复自动选址诊断，可显式使用 `--auto-select-depot`。当前 PGDA slope / roughness GeoTIFF 报告的实际 pixel size 是 1000 m；PSR 是 20 m；DEM 是 80 m；illumination 是 60 m。

`generate_lunar_real_map_instance.py` 把本地 LOLA/illumination raster 生成的 real-map preview 转成 `lunar_ice_bpc.instance.v1`。正式 real-map benchmark 使用同一个 `50 x 50 km` 底图和同一个 depot；规模差异来自同一底图上的任务点密度，实例差异来自 seed、候选点采样和时间窗模式。当前采样策略是 `water_ice_hotspot_directional_sampling_v1`：先识别 PSR / 水冰富集 hotspot，再把 hotspot 扩展为坑内核心 `hotspot_core` 和坑缘/过渡带 `hotspot_edge`，同时保留中等置信、边界和区域覆盖探索点；小规模实例约 60% 指向强富集区、约 40% 保留探索/边界区域。高资源/PSR 内部点偏向 `sample/drill`，坑缘和低置信区域偏向 `detect/sample`，避免任务点只挤在陨石坑内部。输出目录使用 `data/instances/lunar_ice_sp50_005/` 这类命名。每条 directed edge 固定三条 `low_time / low_energy / low_risk` raster path option，不新增第四类路径；该 real-map 路径仍是固定三路径 logical graph 的 scoped exact baseline，不声明对连续月面所有可能路径最优。

direct-DP 和 direct-pricing 在枚举三条路径时会先做 per-arc 支配过滤：如果某个 path option 在 `travel_time_min`、`energy_proxy`、`risk_integral`、`shadow_exposure_min` 四个单调维度上都不优于另一条路径，且至少一个维度严格更差，则该 path option 不会被枚举。这是 exact-safe 的，因为它不能改善时间窗、能量、shadow 可行性或当前目标函数。

30/50 的 fixed-graph direct baseline 在 fleet set-partition 阶段还会使用 service-only remaining lower bound、dual-feasible task-cover lower bound、cardinality-cost relaxation、有限宽度 beam incumbent、静态最少支持任务分支和同状态累计成本支配缓存做搜索剪枝；当剩余 wall-time 足够时，还会构造一个缩放后可行的 LP cover-dual lower bound。这些机制都只在已有 fixed-graph column universe 内工作，只用于 exact-safe 搜索，不生成 official lower bound 或 BPC certificate。

求解输出现在包含 `bound_ledger`。其中只有 `official_lower_bound=true` 的记录能进入 solution / CSV 的 `lower_bound` 和 `relaxation_gap`；普通大规模 fallback 的 official source 仍是 `analytic_relaxation`。当 fixed-graph pricing closure 满足证书条件时，`fixed_graph_pricing_closure_lp` 会作为 scoped BPC node bound 进入 official lower bound；当 complete fixed-graph direct-root LP 满足 scoped true-dual 条件时，`direct_fixed_graph_root_lp` 也可以成为 official lower bound。`restricted_journey_rmp` 始终只作为 diagnostic bound 写入 `best_diagnostic_bound_*`。

求解输出也包含 `pricing_certificate`。该 artifact 统一管理 no-negative certificate 状态：direct / restricted / seeded diagnostic pricing 仍会 fail closed 为 `NOT_PORTED_TRUE_DUAL_BPC`。只有 fixed-graph closure、complete fixed-graph direct-root LP 或未来 full BPC pricing 明确使用 true-dual source、complete coverage、RMP dual 已绑定且 `min_reduced_cost >= -eps` 时，验证器才允许输出 `CERTIFIED_NO_NEGATIVE`。

`exact/certificates/dual_binding.py` 提供 RMP dual-vector binding artifact。它记录 pricing evidence 使用的是哪个 solved RMP 的 task-cover / fleet / cut dual，并生成稳定 fingerprint。该 artifact 是 true-dual pricing tail 的 proof input，不是 no-negative certificate；即使 dual 已绑定，只要 pricing source 不是 true-dual BPC path，仍必须 fail closed。

`exact/certificates/true_dual_pricing_tail.py` 提供 true-dual pricing tail 的单一证书入口。当前 runner 会把 fixed-graph closure、complete direct-root LP 或 direct-pricing 诊断 evidence 绑定到这个 artifact；诊断 evidence 继续 fail closed，满足严格闭合条件的小规模 fixed-graph closure / direct-root LP 会输出 `TRUE_DUAL_PRICING_TAIL_CERTIFIED`。

顶层 `pricing_certificate` 现在通过 `select_effective_pricing_certificate()` 选择证书来源：只有 certified true-dual tail 会被提升为 active no-negative certificate；否则保留 diagnostic fallback，并在 CSV 中记录 `pricing_certificate_selected_source`。

`exact/certificates/pricing_frontier.py` 提供 reduced-cost frontier ledger。`pricing_certificate` 会内嵌该 ledger，记录 frontier scope、pricing/coverage complete 状态、`min_reduced_cost`、`global_remaining_rc_lower_bound`、是否 official，以及 fail-closed issues。当前 diagnostic direct pricing 的 frontier status 可能是 `DIAGNOSTIC_FRONTIER_ONLY` 或 `NEGATIVE_REDUCED_COST_FOUND`，但 `lower_bound_official=false`；只有未来 true-dual complete coverage 且 `min_reduced_cost >= -eps` 时，frontier ledger 才能变成 official no-negative 证据。

`exact/certificates/certificate_readiness.py` 提供 true-dual BPC certificate readiness artifact。它汇总当前 pricing certificate、restricted RMP、node-bound artifact 和 direct-pricing 诊断，输出 `WAITING_TRUE_DUAL_PRICING_PROOF` / `BLOCKED_*` / `TRUE_DUAL_CERTIFICATE_READY` 等状态，并把缺失的 proof inputs 写进 solution / CSV / summary。它不改变 solver、不升级 diagnostic pricing；5-task fixed-graph closure 或 10-task direct-root LP 闭合时会报告 `TRUE_DUAL_CERTIFICATE_READY`。

`exact/certificates/node_bound.py` 提供 BPC node-bound certificate artifact。它把 incumbent、bound ledger、pricing certificate、branch context 和 cut context 汇总成一个节点证书判断；analytic relaxation、restricted RMP 和未通过 true-dual 检查的 fixed-graph root LP 不会被当作 official BPC node bound。只有 true-dual no-negative certificate 和 official BPC node bound 同时存在，才允许节点被 bound fathom。

`exact/pricing/completion_bounds.py` 提供第一版 direct-label completion-bound 前置结构。当前 bound 只使用 task-cover dual 的正奖励项，为 label extension 给出乐观 reduced-cost 下界；fleet、cut、branch dual 均不进入 bound。`price_direct_journey_columns()` 默认用它剪掉不可能优于当前 best reduced cost 的 direct-label 扩展，并在 solution / CSV / summary 中报告 evaluated/pruned label 数。该剪枝仍属于 diagnostic direct pricing，不产生 official lower bound 或 no-negative certificate。

`exact/certificates/completion_bound_consistency.py` 提供 bound-on / bound-off 一致性审计。它在同一 RMP dual 下分别运行启用和关闭 completion-bound 的 exhaustive direct pricing，检查 best reduced cost 与 negative-found 判定是否一致。该审计是 future true-dual tail 加速前的 safety check，不改变 solver、不产生 certificate。

`price_direct_journey_columns(..., cut_context=...)` 现在能按 active cut rows 计算 journey reduced cost，`run_direct_pricing_column_generation(..., cut_context=...)` 也会在 RMP re-solve 和 pricing 中保留同一 cut context。为了保持 exact-safe，cut context 非空时 direct-label completion-bound pruning 会自动关闭；cut dual 只进入最终 reduced-cost 比较，不进入 optimistic tail bound。

`price_direct_journey_columns(..., branch_context=...)` 也支持 Ryan-Foster branch context：返回的 priced columns 会先经过 branch feasibility 过滤，payload 记录 `branch_context_active`、`branch_decision_count` 和 `branch_filtered_column_count`。branch context 非空时 completion-bound pruning 同样自动关闭，避免用 branch-infeasible incumbent 触发错误剪枝。`run_direct_pricing_column_generation(..., branch_context=...)` 会在 node RMP re-solve 和 direct pricing 中保留同一 context。

`price_exhaustive_direct_journey_columns()` 提供小规模 fixed-graph exhaustive pricing 前置能力：当 `task_count <= max_direct_tasks` 时，对所有非空 task subset 做 direct-label pricing，并报告 `pricing_complete_for_all_task_subsets=true`。该 wrapper 本身不单独发证；只有经过 fixed-graph closure、dual binding 和 completion-bound consistency 检查后，才会进入 true-dual tail。

`exact/certificates/fixed_graph_pricing_proof.py` 会把当前 restricted RMP duals、branch/cut context 和 exhaustive direct-label pricing 绑定成 fixed-logical-graph node pricing proof snapshot。它能报告 `FIXED_GRAPH_NO_NEGATIVE_PROVED` 或 `FIXED_GRAPH_NEGATIVE_REDUCED_COST_FOUND`，并写入 `fixed_graph_pricing_proof_*` CSV 字段；但 `uses_true_dual_bpc_certificate=false`、`lower_bound_official=false`、`can_certify_no_negative=false`，所以它不会被当成 official BPC no-negative certificate。

`exact/solver/fixed_graph_pricing_closure.py` 提供小规模 fixed-graph exhaustive pricing closure 循环：每轮重解 restricted RMP，用 exhaustive direct-label pricing 找 fixed-graph negative reduced-cost columns，加入新列后继续，直到固定图上无负列或达到轮次上限。闭合且通过 dual-binding / completion-bound consistency 检查时，输出 `uses_true_dual_bpc_certificate=true`、`lower_bound_official=true`、`can_certify_no_negative=true`；否则仍 fail closed。

`exact/core/branching.py` 提供第一版 Ryan-Foster 风格 pair branch context：`same_journey` 要求一对任务同车同 journey 或同时不在该 column 中，`different_journey` 禁止一对任务出现在同一 journey column 中。`solve_restricted_journey_rmp()` 已支持可选 `branch_context` 并在 solution / CSV 中记录 `restricted_rmp_branch_decision_count` 和 `restricted_rmp_branch_filtered_column_count`。默认 root context 为空，所以现有 benchmark 行为不变；未来 branch-and-price 节点应通过这个 exact context 过滤 master columns 和 pricing columns，GAT 只能排序 branch candidates。

`exact/solver/branch_probe.py` 提供 diagnostic branch candidate artifact。它从当前 supplied column pool 统计任务对在同一 journey column 与分离 column 中的支持度，输出 `same_child_context` / `different_child_context`，但不读取 GAT、不改变 solver、不产生 certificate。benchmark CSV 中的 `branch_probe_*` 字段只用于检查候选和 workload。

`solve_restricted_journey_rmp()` 现在也导出 restricted LP 的 diagnostic primal lambda payload：`primal_columns`、`primal_cover_residual_max` 和 `primal_fleet_usage`。`exact/solver/branch_probe.py` 的 `build_fractional_branch_probe()` 会基于这些 lambda 计算 Ryan-Foster 任务对的 same-journey fraction，并优先给 branch-node queue 使用；如果当前 restricted LP 没有 fractional pair，则回退到 support-based probe。该 primal/fractional 信息只来自 supplied column pool，不是 full BPC proof，也不能产生 no-negative certificate。

`exact/solver/branch_tree.py` 提供第一版 branch-node context ledger。它把 `branch_probe` 的首个候选对展开成 root、same-child、different-child 三个节点 payload，记录每个节点携带的 `BranchContext`、列池过滤计数，并可在当前 supplied column pool 上重解 root/child restricted RMP。当前输出 `BRANCH_TREE_RESTRICTED_RMP_EVALUATED`、`evaluated_node_count=3` 和 `child_evaluated_count=2` 只表示受限列池诊断值已经算出；这些值不是 full pricing lower bound，不改变 solver `node_count`，不能用于 fathom、OPTIMAL 或 true-dual BPC certificate。benchmark CSV 中的 `branch_tree_probe_*` 字段只能作为诊断证据。

`exact/solver/branch_node_queue.py` 提供 restricted branch-node queue 诊断驱动。它从 root `BranchContext` 开始，用当前 supplied journey-column pool 重解每个节点的 restricted RMP，再用 support-based `branch_probe` 生成下一层 same/different 子节点；默认只评估 `max_nodes=7`、`max_depth=2`。该队列还会对前 3 个节点运行 capped direct-label pricing probe，并把返回列按当前 `BranchContext` 过滤后报告 branch-feasible reduced-cost 诊断。如果 probe 返回新的 branch-feasible 负 reduced-cost column，runner 会把这些列临时加入该节点列池并重解一次 restricted RMP，输出 `post_pricing_restricted_rmp_*` 诊断字段。该队列是后续真正 branch-and-price node queue 的接口前置：它能报告 `branch_node_queue_node_count`、`expanded_node_count`、`max_depth_reached`、受限列池 RMP 诊断值和 node-level pricing workload，但不运行 full exact pricing、不产生 official lower bound、不允许 bound fathom，也不改变 true-dual BPC certificate 状态。

branch-node queue 的每个 evaluated node 也会写入 fail-closed `pricing_certificate` 和 `node_bound_certificate` 快照。queue 构建时还不知道最终 incumbent；`solve_reference()` 选出 incumbent 后会回填 `incumbent_objective` 并刷新节点级 `node_bound_certificate`。当前这些节点证书全部应保持 `NOT_PORTED_TRUE_DUAL_BPC` / `NODE_BOUND_FAIL_CLOSED`：node-level direct pricing probe 只能提供 workload 和负列诊断，restricted node RMP 也只是 supplied-pool diagnostic bound，不能让节点 fathom。benchmark CSV 中的 `branch_node_queue_node_pricing_certificate_can_certify_count` 和 `branch_node_queue_node_bound_can_fathom_count` 应保持为 0。

`exact/core/cuts.py` 提供第一版 cut context artifact：当前实现 `subset_row` 和 `fleet_lower_bound` 的 journey-column 系数计算，并能把系数传给 `manual_journey_reduced_cost()` 的 cut-dual 项。`solve_restricted_journey_rmp()` 已支持可选 active `CutContext`，会把 cut rows 加入 supplied-column-pool LP、导出 cut dual、primal cut activity 和 violation 诊断。默认 runner 仍只传空 `cut_context`，`cut_rows_active=false`，`cut_probe.rows_added_to_rmp=0`；即使显式启用 active cut rows，所得 bound 也仍是 restricted-pool diagnostic bound，不能提升 official lower bound、pricing certificate 或 OPTIMAL 声明。

`exact/solver/cut_separator.py` 提供一轮 restricted cut separation 诊断：从 `cut_probe` 的 subset-row 候选中选择 violated cut，重解一次 active-cut restricted RMP，并输出 `cut_separation_probe_*` CSV 字段。默认不自动加入 `fleet_lower_bound` 候选，因为 journey 模型允许单车多 sortie；未经证明的 fleet lower-bound 只能显式 opt-in。该 cut re-solve 仍只覆盖 supplied column pool，不改变 incumbent、official bound、certificate 或 exact status。

`validate_instance()` 现在把月表水冰场景参数当作 schema contract 检查：`50 x 50 km` resource map、`100 m` grid、统一 `50 km` active footprint、fleet / horizon / `max_shadow_exposure_per_sortie`、`B_use=500.0`、`recharge_power_proxy_per_min=4.0`、`Q_ice=6.0`、`max_tasks_per_trip=6` 和 reference sortie 的 shadow / energy / capacity / horizon 可行性都会被验证。`generate_lunar_ice_benchmark.py` 生成的 manifest 同步记录这些参数，防止后续调参后 benchmark 数据和计划漂移。

`configs/benchmarks/lunar_ice_*_journey.yaml` 现在统一使用 `manifest + scales` 选择对应规模；生成正式 120 实例 manifest 后，每个配置会自动跑自己的 scale slice。命令行也可以用 `--scales 5,10` 临时覆盖。

`audit_lunar_ice_benchmark.py` 读取 benchmark CSV 后按计划中的 scale acceptance targets 输出 JSON：5/10/20 检查全量 exact baseline、平均最优时间和超时；30 检查 exact 数量与均时；50/100 检查有效 gap、pricing workload、node count、incomplete reason 和 timeout reason。5-task fixed-graph true-dual closure 和 10-task fixed-graph direct-root certificate 会计入 true-dual certificate 统计；20-task fixed-graph exact baseline 仍不自动计入 certificate。

`audit_lunar_ice_refactor.py` 是项目级边界审计：扫描运行代码/配置中的禁用旧链路字段，检查 120 实例 manifest、样本 instance schema、GAT shadow summary，以及 5/10/20/30/50/100 benchmark audit 证据。当前输出仍为 `IN_PROGRESS` 而不是 `COMPLETE`，因为 30/50 exact closure 未完成；这不是脚本失败，而是防止提前宣称最终重构完成。

direct baseline 超时时保持 fail closed：`status=DIRECT_DP_TIME_LIMIT`、`exact_status=NOT_SOLVED`、不输出 incumbent 或 BPC certificate；但会保留已完成的 partial enumeration counts，方便比较 30/50 exact-safe 优化是否真正推进了 journey label DP。

`configs/base/` 放 exact-safe 默认配置，`configs/experiments/` 放显式实验配置。`run_lunar_ice_gat_shadow.py --config ...` 只接受 `guidance_mode: shadow_only` 且 `journey_gat_optin_enabled: false`；如果拿 opt-in/mutating 配置运行 shadow CLI，会直接报错。`run_lunar_ice_b5_guidance_suite.py --config ...` 输出 B5 do-no-harm / ordering suite JSON；它只接受 shadow-only 或 dry-run ordering opt-in，拒绝 `mutates_solver`、`can_certify`、prune/fathom-capable 配置。当前 B5 suite 的 workload observation 是 `dry_run_no_solver_mutation_zero_diff`，只能证明 dry-run ordering 没有额外 workload 或证书副作用，不能声明性能收益。

## exact

| 路径 | 含义 |
| --- | --- |
| `exact/core/` | 基础数据结构：任务、车辆、arc option、timed trip、journey column、pool。 |
| `exact/master/` | RMP/LP/MIP master、dual extraction、manual reduced-cost 公式。 |
| `exact/pricing/` | true-dual pricing、completion bound、frontier ledger、global remaining RC LB。 |
| `exact/branching/` | branch constraint、Ryan-Foster / route-order branching、branch feasibility。 |
| `exact/cuts/` | pricing-compatible cuts、cut coefficient、cut context snapshot。 |
| `exact/certificates/` | no-negative certificate、corrected node bound、proof artifact validation。 |
| `exact/solver/` | branch-price driver、node queue、incumbent、final result assembly。 |

exact 规则：

- `exact/` 不依赖 torch、torch_geometric、checkpoint 或 learned score。
- `manual_journey_reduced_cost()` 语义和 official dual path 必须集中在 `exact/master/`。
- `CERTIFIED_NO_NEGATIVE` 只能由 exact certificate path 产生。
- pricing 如果 coverage incomplete，必须 fail closed。

## guidance

| 路径 | 含义 |
| --- | --- |
| `guidance/graph/` | logical graph 到 GAT tensor 的确定性构图、feature schema。 |
| `guidance/models/` | GAT、batch-impact、branch-impact、dual-anchor 等模型定义。 |
| `guidance/policies/` | priority policy、admission policy、delay queue policy、branch score policy。 |
| `guidance/safety/` | kNN/OOD safety shell、safe-source gate、threshold/calibration rule。 |
| `guidance/inference/` | checkpoint loading、batch scoring、shadow decision generation。 |

guidance 规则：

- learned score 只能影响 priority、delay、shadow 或 opt-in scheduling。
- `DELAY_QUEUE` 不是 reject；true-RC negative 必须有限延迟后重新暴露给 exact path。
- safe-source 不完整时，mutating GAT policy 必须 pass-through 或 shadow-only。
- guidance 不能导入 exact solver 的内部可变状态来偷偷剪枝。

## pipelines

| 路径 | 含义 |
| --- | --- |
| `pipelines/datasets/` | target rows、batch samples、hard pairs、graph dataset 构建。 |
| `pipelines/training/` | 训练、校准、checkpoint 选择、threshold sweep。 |
| `pipelines/replay/` | forced replay、counterfactual replay、runbook 生成与解析。 |
| `pipelines/audits/` | kNN/OOD、ROI、false-safe、certificate closure、no-regression 审计。 |
| `pipelines/benchmarks/` | 5/10/20/30/50/100 benchmark matrix、A/B runner、summary。 |

pipeline 规则：

- build/audit/train/runbook 逻辑放在这里，`scripts/` 只做薄包装。
- 每个 pipeline 输出必须写 manifest 或 summary。
- benchmark 报告必须分清 exact status、heuristic status、incomplete reason。

## artifacts

| 路径 | 含义 |
| --- | --- |
| `artifacts/schemas/` | JSON/CSV/Tensor schema、字段含义、版本迁移规则。 |
| `artifacts/readers/` | 读取日志、CSV、manifest、checkpoint metadata 的稳定接口。 |
| `artifacts/writers/` | 写出 manifest、summary、runbook、audit report 的稳定接口。 |

artifact 规则：

- schema version 不匹配时 fail closed。
- cut context、branch context、dual hash、checkpoint id、threshold hash 必须可追踪。
- 禁止脚本私自发明未登记字段并直接进入训练。

## scripts

| 路径 | 含义 |
| --- | --- |
| `scripts/` | 人手执行的薄 CLI 脚本，例如 `generate_lunar_ice_benchmark.py`、`run_lunar_ice_bpc.py`、`draw_lunar_ice_instance.py`。 |

脚本规则：

- 脚本不保存核心业务逻辑。
- 脚本不直接拼接复杂 schema。
- 脚本应调用 `src/lunar_ice_bpc/` 中的 runner 或 domain 实现。

## tests

| 路径 | 含义 |
| --- | --- |
| `tests/exact/` | exact core/master/pricing/branching/certificate 单元测试。 |
| `tests/guidance/` | GAT model、policy、safety shell、inference 单元测试。 |
| `tests/pipelines/` | dataset/training/replay/audit/benchmark pipeline 测试。 |
| `tests/integration/` | 小实例端到端 smoke 和 benchmark no-regression 测试。 |
| `tests/contracts/` | proof boundary contract 测试。 |

必须优先写的 contract tests：

- GAT / kNN / OOD 不能产生 `CERTIFIED_NO_NEGATIVE`。
- `DELAY_QUEUE` 中存在 current true-RC negative 时不能 certificate。
- global remaining RC LB coverage incomplete 时不能 official bound。
- cut context schema/signature 不匹配时 GAT decision fail closed。
- smoothed/learned dual no-column 不能完成 node proof。
- exact baseline 与 guidance shadow-only 在 certified objective 上一致。
