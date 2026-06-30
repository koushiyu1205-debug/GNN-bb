# CODEX 重构计划：月表水冰探测版 GAT+BPC，保留 Journey Master，删除通信建模

## 0. 目标与结论

本计划基于 `CODEX_lunar_ice_bpc_refactor_no_comm.md`，但修正一个关键决策：

> 新版必须保留 `journey master` 作为主线，而不是只保留 `trip_time master`。

原因：

- 研究问题本身是多车、多 sortie、多路径选择的 CVRPTW；`journey master` 更自然地表达“一辆月球车执行多个 sortie 后构成一个完整工作日/任务周期”的列。
- `BPC_future` 后期 exact-safe 证明边界、GAT target-mode、branch/proof tail 主线都围绕 journey-column BPC 展开；如果只保留 trip-time master，会丢掉最重要的算法主线。
- 论文叙事应是：月表水冰探测场景 + multi-sortie journey-column BPC + exact-safe GAT guidance，而不是退回较早的 trip-time 原型。

本计划仍保持以下决策不变：

- 不修改、不删除 `BPC_future/` 中任何文件。
- 第一版完全删除通信建模。
- 不改成 optional customer、orienteering、prize-collecting VRPTW。
- 多路径选项固定为三类：`low_time`、`low_energy`、`low_risk`；不要新增第四类或更多路径类型。
- GAT 只能做 discovery / priority / admission / dual anchor，不产生官方下界、证书或剪枝。
- 只迁移主要运行代码，不复制旧报告、runbook、probe、大量 audit 和历史结果。

## 0.1 已确认用户决策

以下决策作为实现约束：

1. 新项目固定在 `/home/kai/work/GAT_BPC_moonTerk`，包名使用 `src/lunar_ice_bpc/`。
2. Benchmark 规模固定为 `5 / 10 / 20 / 30 / 50 / 100` 六种，每种规模 `20` 个 accepted instances，总计 `120` 个实例。
3. 不再按地形 family 或时间窗 family 扩展 benchmark。
4. 允许先用 synthetic polar resource grid 跑通完整主线，再接真实 LOLA / Diviner / M3 / LEND 数据。
5. GAT 第一阶段只做 shadow；等 exact baseline 和数据 schema 稳定后，再开启 opt-in。
6. 保留 `draw_lunar_ice_instance.py`，但不复制旧 `BPC_future/draw/`。该脚本需要能画 resource map、targets、三条路径和 solution overlay。
7. 运行时间预算：
   - `5 / 10 / 20` 规模：每实例 `600s`。
   - `30 / 50 / 100` 规模：每实例 `3600s`。
8. 性能目标：
   - 5 规模：20/20 在 `600s` 内 exact OPTIMAL，且 20 个实例的平均最优解时间小于 `5s`。
   - 10 规模：20/20 在 `600s` 内 exact OPTIMAL，且 20 个实例的平均最优解时间小于 `10s`。
   - 20 规模：20/20 在 `600s` 内 exact OPTIMAL，且 20 个实例的平均最优解时间小于 `100s`。
   - 30 规模：exact OPTIMAL 数量不少于 `15/20`，且已求最优实例的平均最优解时间小于 `250s`。
   - 50 规模：必须能获得有效 gap，且 exact OPTIMAL 数量不少于 `3/20`。
   - 100 规模：作为 scalable benchmark，不强求 exact closure；必须报告 incumbent、gap、pricing workload 和 incomplete reason。
9. Benchmark 批量运行默认 `max_workers=4`。
10. `time_bucket_size` 第一版固定为 `10.0 min`，与旧 `BPC_future` journey 主线的常用配置保持一致。
11. 充电模型采用“能量缺口线性充电 + 固定对接开销”：每个 sortie 从 depot 满电出发，返回 depot 后按消耗能量线性充电，并叠加固定 dock overhead。
12. 目标函数采用月表大范围快速探测导向的 weighted discovery completion objective：所有水冰目标仍必须 exactly once 服务，但高科学价值目标应更早完成。
13. Benchmark fleet rule 固定为 `005/010/020/030/050/100 -> 1/2/3/4/5/8`。
14. 月球车速度采用快速探测设定：最大速度 `30 km/h`，目标平均速度约 `18 km/h`；旧 `BPC_future` 物理图使用 `base_speed_kmh=6.0`、`min_speed_kmh=1.0`，新场景不沿用旧慢速设定。
15. `science_weight_i = 0.6 * normalized_ice_confidence_i + 0.4 * normalized_expected_ice_kg_i`，第一版不使用 `site_priority`。
16. 正式 real-map benchmark 默认 resource map 使用 `50 x 50 km`，以同一个自动选出的南极高照明 depot 为中心。
17. 第一版 `operation_mode` 只保留 `detect / drill / sample` 三类，不使用 `extract`。
18. `max_tasks_per_trip` 固定为 `6`。
19. 第一版 operation mode 采样比例固定为 `detect 50% / sample 30% / drill 20%`，并使用固定参数表生成 service time、service energy 和 demand。
20. `Q_ice=6.0`，capacity demand 采用 operation-mode task units。
21. 能量使用无量纲 proxy，第一版不绑定真实 Wh/kWh。
22. `depot_chargers=unlimited`，不建 depot 充电位排队约束。
23. Horizon 按规模轻微放宽：`005/010 -> 960 min`，`020/030 -> 1680 min`，`050 -> 3000 min`，`100 -> 4560 min`。时间窗宽度 cap 不随 horizon 放宽。
24. 为靠近月表 PSR 作业现实，第一版使用 `max_shadow_exposure_per_sortie` 作为硬热控约束：`005/010 -> 180 min`，`020/030 -> 240 min`，`050/100 -> 300 min`。
25. 正式 real-map benchmark 的 active footprint 统一为 `50 x 50 km`；规模差异体现在同一底图上的任务点密度，而不是给不同规模裁不同范围。
26. Synthetic grid resolution 固定为 `100 m`。
27. Service energy 使用无量纲 proxy 区间：`detect -> 2-4`，`sample -> 6-10`，`drill -> 12-20`。
28. `B_use` 初始值暂定为 `500.0`，后续必须根据 exact baseline 的可行率、gap 和 optimal closure 结果校准，避免过宽导致难求或过窄导致无解/单点 sortie。
29. 当前默认 benchmark 使用 `sp50_three_temporal_modes_v1` 时间窗策略：正式 120 个实例不再按时间窗 family 扩展，但每个规模的 20 个实例按 `7 / 7 / 6` 分配到 `outer_to_inner`、`inner_to_outer`、`easy_to_hard` 三种任务节奏。
30. 批量 benchmark 的 `max_workers=4` 使用进程池执行 CPU-bound exact baseline；小规模平均最优时间按 `exact_baseline_wall_time_sec` 统计，diagnostic restricted RMP / pricing / CG 时间单独保留，不混入 exact baseline 时间目标。
31. 正式 benchmark 使用同一个 `50 x 50 km` 真实底图和同一个 depot，只改变 seed、任务点采样和时间窗模式；总数仍为 `6 * 20 = 120`。
32. depot 允许基于 LOLA DEM + illumination 自动选取，同时记录与 Shackleton rim / Shackleton-de Gerlache ridge / de Gerlache rim 等文献命名区域的近似比较证据。
33. 第一版真实数据链路允许用 LOLA DEM / slope / roughness / PSR / average solar visibility 建立 resource/risk/illumination 图；Diviner / M3 / LEND 后续再接入。
34. 任务点从固定候选池按 selection score 无放回加权采样。PSR 边缘偏向 `detect`，PSR 内部和高资源区偏向 `sample` / `drill`，总体比例仍保持 `detect 50% / sample 30% / drill 20%`。
35. 真实图输出使用 `lunar_ice_sp50_005/instance_001_logical_graph.json` 这类目录，不再沿用旧 `lunar_ice_real_*` 命名。
36. 论文可视化每种规模只保留一个典型实例图，另保留 resource/risk map、DEM map、targets、三条路径和 solution overlay。

## 0.2 当前落地记录（2026-06-30）

- 已清理 `GAT_BPC_moonTerk` 下旧 synthetic/real 实例、旧 figures 和旧 solutions；未修改或删除 `BPC_future/`。
- 已下载并接入 LOLA DEM / slope / roughness / PSR，以及 PGDA illumination 产品 `AVGVISIB_85S_060M_201608.TIF`。PGDA 页面上的 `*_COG.TIF` 链接返回 404，不作为当前 catalog URL。
- 当前正式 sp50 benchmark depot 固定为 `[-9.90, -19.10] km`，本地 ROI 中心为 `[25.0, 25.0] km`；该点来自 dense-depot 可视化对比，仍是高照明候选点，同时让 50km ROI 覆盖更密集的 PSR / 水冰结构。自动选址函数仍保留为诊断工具，但默认 preview / instance 不再使用 `[-7.25, -11.15] km`。
- depot 选择策略从“最高照明/高程”转为“高照明 depot 服务更密集水冰富集区”的论文叙事折中：保留 depot 永昼/高照明证据，同时优先让任务区域包含多个可见水冰/PSR hotspot。
- 当前 sp50 preview 的 target 候选也加入 4km 边缘缓冲，100 个候选点的最小边界距离约 `4.05 km`，不再出现候选点贴边。
- 已生成 `data/processed/real_maps/south_pole_sp50_preview.json`、`runs/figures/lunar_real_map_sp50_preview.svg` 和 `runs/figures/lunar_real_map_sp50_dem.svg`。
- 已生成并验证 005 规模样例 `data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json`：`grid_shape=[500,500]`、30 条 directed edge、每条 edge 固定三条 path option、`time_window_mode=outer_to_inner`、reference makespan 约 `462.63 min`、schema issues 为 0。
- 已改进 SVG 配色：预览图同时输出 resource/risk composite 和 DEM 两种底图；实例图支持 `--also-dem`，可同时输出 resource/risk 版和 DEM 底图版。当前采用参考遥感图的低饱和暖色假彩色风格：柔和沙金/月壤底色 + 低饱和蓝色水冰/PSR 结构 + 柔和红橙风险纹理；DEM 使用蓝色低洼、沙金中高地、低饱和红橙高差和浅金高岭渐变，并用 smoothstep 插值降低色带过渡生硬感，不再使用灰黑月面底图，也不强制色盲友好 palette。
- 已给 real-map preview 和 instance SVG 增加图例/色标：resource/risk 图包含 ice/resource 色标、risk 色标、三路径和 PSR 区域图例；DEM 图包含 elevation 色标和任务/区域图例。
- 已提高图像渲染分辨率：real-map preview SVG 从 260 cells 提到 360 cells；instance 内嵌 preview 从 72 cells 提到 180 cells。
- real-map target 生成已改为 `water_ice_hotspot_directional_v1`：候选池先识别 PSR / 水冰富集 hotspot，再把每个 hotspot 拓宽为坑内核心 `hotspot_core` 和坑缘/过渡带 `hotspot_edge`，同时加入中等置信、边界和区域覆盖探索点。正式实例采样使用 `water_ice_hotspot_directional_sampling_v1`，小规模约 60% 点来自强富集区、约 40% 点来自探索/边界区域；science quota 内显式保留一部分 `hotspot_edge`，避免任务只挤在陨石坑内部。
- 005 规模样例已更新为“富集区核心 + 坑缘过渡带 + 区域探索”：`sampled_hotspot_count=5`、任务点最小间距约 `17.53 km`，candidate role 分布为 `hotspot_edge=2 / hotspot_core=2 / exploration=1`，mode 分布为 `sample=3 / drill=1 / detect=1`；高资源/PSR 内部点偏向 `sample/drill`，坑缘和低置信区域偏向 `detect/sample`。
- 当前明显瓶颈是 500x500 真实栅格上逐 directed arc 运行三类 Dijkstra。005 样例可接受，但 020/030/050/100 的完整全连接图需要后续做路径缓存、多源最短路或候选路径预计算，否则正式 120 实例生成会很慢。

## 1. 新项目位置与包名

项目目录使用当前已有目录：

```text
/home/kai/work/GAT_BPC_moonTerk/
```

建议 Python 包名：

```text
src/lunar_ice_bpc/
```

不要再在 `gnn_bb/` 下另开平行 `lunar_ice_bpc/` 目录。当前目录就是新主线。

## 2. 新目录结构

建议最终结构：

```text
GAT_BPC_moonTerk/
  README.md
  CODEX_lunar_ice_bpc_refactor_no_comm.md
  CODEX_lunar_ice_bpc_refactor_with_journey_master_plan.md
  pyproject.toml

  configs/
    base/
      journey_base.yaml
      gat_shadow_base.yaml
    benchmarks/
      lunar_ice_5_journey.yaml
      lunar_ice_10_journey.yaml
      lunar_ice_20_journey.yaml
      lunar_ice_30_journey.yaml
      lunar_ice_50_journey.yaml
      lunar_ice_100_journey.yaml
    experiments/
      lunar_ice_20_gat_shadow.yaml
      lunar_ice_20_gat_optin.yaml

  data/
    raw_maps/
    instances/
      lunar_ice_005/
      lunar_ice_010/
      lunar_ice_020/
      lunar_ice_030/
      lunar_ice_050/
      lunar_ice_100/
    manifests/

  runs/
    logs/
    csv/
    solutions/
    checkpoints/
    figures/

  scripts/
    generate_lunar_ice_benchmark.py
    run_lunar_ice_bpc.py
    draw_lunar_ice_instance.py
    self_check.py

  src/lunar_ice_bpc/
    __init__.py

    domain/
      __init__.py
      polar_resources.py
      scenario.py
      scheduling.py
      visualization.py

    exact/
      __init__.py
      core/
        __init__.py
        data.py
        columns.py
        journey.py
        branching.py
        cuts.py
        fleet_bound.py
      master/
        __init__.py
        journey_rmp.py
        trip_rmp.py
      pricing/
        __init__.py
        journey_pricing.py
        trip_pricing.py
        journey_harvesting.py
        completion_bounds.py
        resource_pareto.py
      solver/
        __init__.py
        journey_driver.py
        trip_driver.py
        logger.py
      certificates/
        __init__.py
        pricing_state.py
        corrected_node_bound.py

    guidance/
      __init__.py
      graph_builder.py
      gnn_model.py
      column_selector.py
      dual_stabilizer.py
      admission_queue.py
      candidate_id.py

    io/
      __init__.py
      config.py
      instance_io.py
      solution_io.py
      manifest.py

    runners/
      __init__.py
      generate_instances.py
      solve.py
      benchmark.py

    utils/
      __init__.py
      hashes.py
      numeric.py
      paths.py
```

说明：

- `exact/` 是 proof boundary，不能依赖 torch/checkpoint/GAT 分数。
- `guidance/` 是 learned guidance，不得产生 certificate。
- `domain/` 只负责月表水冰场景数据、资源图、调度字段和可视化。
- `scripts/` 只做薄入口，核心逻辑放进 `src/lunar_ice_bpc/`。
- 不复制旧 `docs/`、`logical_graph/run_reports/`、历史 `results/`、probe/runbook/audit 脚本。

## 3. 从 `BPC_future` 迁移的模块

### 3.1 必须迁移并改包名

```text
BPC_future/core/data.py
  -> src/lunar_ice_bpc/exact/core/data.py

BPC_future/core/columns.py
  -> src/lunar_ice_bpc/exact/core/columns.py

BPC_future/core/journey.py
  -> src/lunar_ice_bpc/exact/core/journey.py

BPC_future/core/branching.py
  -> src/lunar_ice_bpc/exact/core/branching.py

BPC_future/core/cuts.py
  -> src/lunar_ice_bpc/exact/core/cuts.py

BPC_future/core/fleet_bound.py
  -> src/lunar_ice_bpc/exact/core/fleet_bound.py

BPC_future/master/journey_rmp.py
  -> src/lunar_ice_bpc/exact/master/journey_rmp.py

BPC_future/pricing/journey_pricing.py
  -> src/lunar_ice_bpc/exact/pricing/journey_pricing.py

BPC_future/pricing/journey_harvesting.py
  -> src/lunar_ice_bpc/exact/pricing/journey_harvesting.py

BPC_future/pricing/resource_pareto_completion.py
  -> src/lunar_ice_bpc/exact/pricing/resource_pareto.py

BPC_future/pricing/available_mask_completion_bound.py
  -> src/lunar_ice_bpc/exact/pricing/completion_bounds.py

BPC_future/pricing/trip_pricing.py
  -> src/lunar_ice_bpc/exact/pricing/trip_pricing.py

BPC_future/solver/journey_driver.py
  -> src/lunar_ice_bpc/exact/solver/journey_driver.py

BPC_future/solver/logger.py
  -> src/lunar_ice_bpc/exact/solver/logger.py

BPC_future/solver/gat_admission_queue.py
  -> src/lunar_ice_bpc/guidance/admission_queue.py

BPC_future/solver/gat_candidate_id.py
  -> src/lunar_ice_bpc/guidance/candidate_id.py

BPC_future/learning/graph_builder.py
  -> src/lunar_ice_bpc/guidance/graph_builder.py

BPC_future/learning/gnn_model.py
  -> src/lunar_ice_bpc/guidance/gnn_model.py

BPC_future/learning/column_selector.py
  -> src/lunar_ice_bpc/guidance/column_selector.py

BPC_future/learning/dual_stabilizer.py
  -> src/lunar_ice_bpc/guidance/dual_stabilizer.py
```

### 3.2 可选迁移，仅用于兼容或 bootstrap

```text
BPC_future/master/rmp.py
  -> src/lunar_ice_bpc/exact/master/trip_rmp.py

BPC_future/solver/driver.py
  -> src/lunar_ice_bpc/exact/solver/trip_driver.py
```

说明：

- `trip_rmp.py` 和 `trip_driver.py` 不作为论文主线。
- 它们可以用于早期 smoke、初始 trip pool、对照实验或故障定位。
- 默认运行入口应走 `journey_driver.py`。

### 3.3 必须重写

```text
src/lunar_ice_bpc/domain/polar_resources.py
src/lunar_ice_bpc/domain/scenario.py
src/lunar_ice_bpc/domain/scheduling.py
src/lunar_ice_bpc/domain/visualization.py
src/lunar_ice_bpc/io/config.py
src/lunar_ice_bpc/io/instance_io.py
src/lunar_ice_bpc/runners/generate_instances.py
src/lunar_ice_bpc/runners/solve.py
src/lunar_ice_bpc/runners/benchmark.py
scripts/generate_lunar_ice_benchmark.py
scripts/run_lunar_ice_bpc.py
scripts/draw_lunar_ice_instance.py
scripts/self_check.py
```

## 4. 不迁移的内容

不要复制以下内容：

```text
BPC_future/docs/
BPC_future/tests/
BPC_future/logical_graph/run_reports/
BPC_future/paper_rewriting_output/
BPC_future/results/
BPC_future/draw/  # 不整包复制，只重写一个轻量可视化入口
BPC_future/scripts/build_*_runbook.py
BPC_future/scripts/audit_*.py
BPC_future/scripts/evaluate_*.py
BPC_future/scripts/analyze_*.py
BPC_future/scripts/run_*_probe.py
BPC_future/scripts/run_*_external_timeout_batch.py
```

例外：

- 可以保留一个很小的 `scripts/self_check.py`。
- 可以保留一个很小的 `scripts/draw_lunar_ice_instance.py`，因为论文需要图。
- 不复制旧测试套件，但要有最小运行自检，防止重构后无从验证。

## 5. 数学模型：Journey Master 主线

### 5.1 集合

```text
0      = fixed Peak-of-Eternal-Light charging base
I      = PSR / permanently shadowed water-ice targets
R      = homogeneous lunar rover set
P_ij   = fixed physical path options from node i to node j
T      = feasible timed sortie set
J      = feasible journey set, each journey is a sequence of compatible sorties for one rover
```

其中：

```text
i, j in {0} union I, i != j
```

### 5.2 Timed sortie

一个 timed sortie：

```text
tau = 0 -> i1 -> i2 -> ... -> ik -> 0
```

包含：

```text
task sequence
selected path option for every leg
start time
service start times
return time
recharge-inclusive end time
load
energy
distance
shadow exposure
terrain / thermal risk
cost
```

### 5.3 Journey column

一个 journey column：

```text
j = (tau_1, tau_2, ..., tau_m)
```

表示同一辆月球车按时间顺序执行多个 sortie。必须满足：

```text
tau_l.end_time <= tau_{l+1}.start_time
task sets are disjoint
all sorties belong to the same rover schedule
```

Journey 的成本采用“快速发现/快速覆盖”导向，而不是普通路程最短。所有水冰目标仍必须 exactly once 服务，但高科学价值目标应更早完成。

```text
c_j =
  F_rover
  + alpha * sum_{i in S_j} science_weight_i * completion_time_i(j)
  + beta  * journey_end_time(j)
  + gamma * total_lunar_ice_risk(j)
  + delta * total_energy_used(j)
```

其中：

```text
science_weight_i =
  0.6 * normalized_ice_confidence_i
  + 0.4 * normalized_expected_ice_kg_i

completion_time_i(j) = service_start_i + service_time_i
journey_end_time(j) = recharge-inclusive end time of the last sortie
total_lunar_ice_risk(j) includes terrain, PSR/shadow, cold-trap thermal, and ice-operation risk
```

建议第一版权重顺序：

```text
alpha >> beta >= gamma > delta
```

解释：

- `alpha` 最大，强调大范围快速探测和高价值水冰点早完成。
- `beta` 控制整体任务周期，不让最后一个 sortie 拖太久。
- `gamma` 保留月表 PSR/cold-trap 风险惩罚。
- `delta` 较小，因为能耗已经通过充电时间部分进入 `journey_end_time`。
- 第一版不使用 `site_priority`，避免引入没有明确数据来源的主观字段。

禁止通信项：

```text
comm_blackout
comm_visible_fraction
link_margin
Earth visibility
relay visibility
communication window
```

### 5.4 Journey RMP

决策变量：

```text
x_j >= 0
```

RMP：

```text
min sum_{j in pool} c_j x_j

s.t.
  sum_{j: i in S_j} x_j = 1          for all water-ice targets i in I
  sum_j x_j <= active_fleet_limit
  cut rows
  branch rows
```

整数解释：

```text
x_j = 1 means one rover executes journey j
```

### 5.5 Journey reduced cost

设：

```text
pi_i  = cover dual for task i
mu    = fleet limit dual
gamma = cut duals
```

则：

```text
rc(j) = c_j - mu - sum_{i in S_j} pi_i - sum_k gamma_k a_kj
```

这个公式必须由 `exact/master/journey_rmp.py` 统一实现，GAT 不得改写。

## 6. Column feasibility：月表水冰资源约束

每个 sortie 必须检查：

```text
capacity:
  sum_i q_i <= Q_ice
  Q_ice = 6.0

time window:
  r_i <= service_start_i <= D_i - sigma_i

energy:
  E_ice[tau] <= B_use
  E_ice and B_use are dimensionless energy proxies in v1

return and recharge:
  recharge_time[tau] = dock_overhead_min + E_ice[tau] / recharge_power_proxy_per_min
  end_time[tau] = return_time[tau] + recharge_time[tau]
  end_time[tau] <= H
  depot_chargers = unlimited

thermal / shadow:
  shadow_exposure[tau] <= max_shadow_exposure_per_sortie
  thermal_survival_energy[tau] included in E_ice[tau]
```

第一版固定：

- `Q_ice=6.0`。
- `q_i` 使用 operation-mode demand：`detect=0.5`，`sample=1.0`，`drill=1.5`。
- 能量量纲使用 proxy，不绑定真实 Wh/kWh。
- time window 只来自 thermal-safe / operation-safe 窗口，不来自通信。
- `max_shadow_exposure_per_sortie` 是第一版靠近现实的核心热控硬约束；shadow exposure 同时进入 risk 和 thermal survival energy。
- depot 充电功率先设常数，不加入 time-dependent solar power。
- depot 充电位无限，不建充电排队或 charger capacity rows。
- 每个 sortie 从 depot 满电出发，中途不充电；若 `E_ice[tau] > B_use`，该 sortie infeasible。
- `expected_ice_kg` 和 `ice_confidence` 用于 target sampling、GAT feature 和 `science_weight_i`，不把目标改成 optional prize。

## 7. 数据 schema

### 7.1 Task schema

每个 water-ice target 只对应一个任务点，并且 exactly once 服务。`operation_mode` 是该任务点的作业属性：一个 target 在 `detect / drill / sample` 中选择一种 mode，不表示同一 target 要被服务三次。

第一版 operation mode 采样比例和参数表固定：

```text
detect: 50%, sigma 10-20 min, service_energy low,    d=0.5
sample: 30%, sigma 25-45 min, service_energy medium, d=1.0
drill:  20%, sigma 45-90 min, service_energy high,   d=1.5
```

其中 `sigma` 写入 service time，`g` 写入 service energy，`d` 写入 capacity demand，`c_srv` 由 mode-specific operation cost 生成。

```json
{
  "id": "ice_site_001",
  "kind": "psr_water_ice_target",
  "xy_km": [0.0, 0.0],
  "expected_ice_kg": 0.0,
  "ice_confidence": 0.0,
  "science_weight": 1.0,
  "operation_mode": "detect | drill | sample",
  "planned_depth_m": 0.0,
  "planned_sample_mass_kg": 0.0,
  "local_shadow_score": 0.0,
  "local_thermal_risk": 0.0,
  "local_slope_risk": 0.0,
  "d": 1.0,
  "sigma": 0.0,
  "g": 0.0,
  "c_srv": 0.0,
  "r": 0.0,
  "D": 0.0
}
```

禁止字段：

```text
comm_window
communication_window
earth_visibility_window
relay_window
comm_score
link_margin_db
```

### 7.2 Path option schema

每条 directed logical edge 只保留三条候选路径，类型固定为：

```text
low_time
low_energy
low_risk
```

不要新增 `low_shadow`、`thermal_safe`、`low_comm`、`high_comm` 或其他路径类型。阴影暴露、热控能耗、坡度风险和粗糙度风险都作为这三条路径的属性或权重进入，不单独生成第四类路径。

`travel_time_min` 使用新场景的快速探测速度模型生成：`rover_max_speed_kmh=30.0`，目标平均速度约 `18.0 km/h`。旧 `BPC_future` 的 `base_speed_kmh=6.0` / `min_speed_kmh=1.0` 只作为历史对照，不作为新 benchmark 默认值。

```json
{
  "path_type": "low_time | low_energy | low_risk",
  "aliases": ["low_time"],
  "path_distance_km": 0.0,
  "travel_time_min": 0.0,
  "energy_proxy": 0.0,
  "risk_integral": 0.0,
  "generalized_cost": 0.0,
  "shadow_exposure_min": 0.0,
  "thermal_survival_energy_proxy": 0.0,
  "slope_risk": 0.0,
  "roughness_risk": 0.0,
  "path_cells": [],
  "path_xy": []
}
```

固定三类 path option：

```text
low_time   = shortest by travel time
low_energy = shortest by drive + survival/thermal energy
low_risk   = shortest by terrain + shadow/thermal risk
```

不加入：

```text
low_shadow
thermal_safe
low_comm
high_comm
low_blackout
```

### 7.3 月表水冰版风险计算模型

新场景不能沿用旧 `BPC_future` 中只由坡度/粗糙度组成的 terrain risk。旧风险只能作为其中两个分量，不能作为完整风险模型。

月表水冰探测的风险必须显式包含：

```text
slope_risk              # 坡度导致的通行/翻覆风险
roughness_risk          # 粗糙度导致的行驶风险
psr_shadow_risk         # 永夜坑/永久阴影区暴露风险
cold_trap_thermal_risk  # 极低温冷阱导致的热控风险
ice_operation_risk      # 钻探/取样/取冰作业复杂度风险
```

每个栅格 cell 的基础风险定义为：

```text
lunar_ice_cell_risk =
  alpha_slope   * slope_risk
+ alpha_rough   * roughness_risk
+ alpha_shadow  * psr_shadow_risk
+ alpha_thermal * cold_trap_thermal_risk
```

其中：

```text
slope_risk = clipped_normalized_slope
roughness_risk = clipped_normalized_local_dem_std
psr_shadow_risk = 1.0 if cell is PSR else shadow_fraction
cold_trap_thermal_risk = clipped_normalized_coldness_or_temperature_deficit
```

任务点局部作业风险定义为：

```text
ice_operation_risk_i =
  beta_depth  * normalized_planned_depth_m
+ beta_sample * normalized_planned_sample_mass_kg
+ beta_ice    * (1.0 - ice_confidence)
+ beta_therm  * local_thermal_risk
```

路径风险定义为路径上 cell/edge 风险的长度加权积分：

```text
risk_integral(path) =
  sum_{edge or cell on path} length_weight * lunar_ice_cell_risk
```

阴影暴露和热控能耗单独保留为 path attributes：

```text
shadow_exposure_min(path) =
  sum_{edge on path} travel_time_edge * shadow_indicator_or_fraction

thermal_survival_energy_proxy(path) =
  shadow_exposure_min(path) * thermal_survival_power_proxy
```

`low_risk` 路径使用的权重是：

```text
low_risk_edge_weight =
  eta_risk   * lunar_ice_cell_risk
+ eta_shadow * shadow_exposure_edge
+ eta_therm  * thermal_survival_energy_edge
+ eta_dist   * distance_edge
```

但仍然只输出三条 path options：

```text
low_time
low_energy
low_risk
```

风险模型的 exactness 边界：

- 风险计算发生在 preprocessing / instance generation 阶段。
- BPC pricing 只读取固定后的 `risk_integral`、`shadow_exposure_min` 和 `thermal_survival_energy_proxy`。
- 风险模型不在 pricing 中动态预测，不产生 certificate，不影响 official lower-bound 语义。
- 如果后续更换风险公式，必须 bump instance schema / risk schema version，并重新生成 logical graph。

## 8. 数据来源与生成链路

第一版可以先用 synthetic resource grid 跑通代码，再接真实公开数据。

推荐生成链路：

```text
polar resource layers
  -> passable / impassable grid
  -> high-illumination depot selection
  -> PSR / cold-trap / high-ice-confidence target sampling
  -> physical grid graph
  -> all-pairs multi-option paths
  -> logical graph JSON
  -> journey BPC instance
```

资源层建议：

```text
terrain elevation / slope
PSR mask
illumination fraction
temperature / cold-trap proxy
ice probability or hydrogen proxy
lunar_ice_cell_risk
```

第一版文件输出：

```text
data/instances/lunar_ice_005/*.json
data/instances/lunar_ice_010/*.json
data/instances/lunar_ice_020/*.json
data/instances/lunar_ice_030/*.json
data/instances/lunar_ice_050/*.json
data/instances/lunar_ice_100/*.json
data/manifests/lunar_ice_benchmark_manifest.json
```

规模生成规则：

- 固定六种规模：`5 / 10 / 20 / 30 / 50 / 100`。
- 每种规模生成 `20` 个 accepted instances。
- 第一版总实例数为 `6 * 20 = 120`。
- 默认 synthetic resource map 尺寸为 `30 x 30 km`。
- synthetic grid resolution 固定为 `100 m`，即 `30 x 30 km` 对应约 `300 x 300` cells。
- active footprint 随规模扩大：`005/010 -> 12 x 12 km`，`020/030 -> 20 x 20 km`，`050/100 -> 30 x 30 km`。
- 每个规模固定 fleet rule：`005 -> 1`，`010 -> 2`，`020 -> 3`，`030 -> 4`，`050 -> 5`，`100 -> 8`。
- manifest 必须记录每个规模的 accepted count、attempt count、skip reason、risk schema version、time-window policy id。

时间窗生成规则：

- 每种规模只生成一个 canonical lunar-ice time-window family。
- 不再按每个规模生成三类时间窗场景。
- 不保留 `easy / medium / hard`、`wide / normal / narrow`、`randomtw_*` 这类时间窗模式矩阵。
- 时间窗只由月表水冰任务语义生成：thermal-safe operation window、mission operation window、detect/drill/sample operation availability。
- 规模维度只保留 `5 / 10 / 20 / 30 / 50 / 100`，第一版 benchmark 不再扩展成 `scale x time-window-mode`。

时间窗不能太松。过松会让 timed-trip 和 journey universe 爆炸，pricing exact closure 更难。因此时间窗必须围绕一个构造性可行参考调度收紧生成，而不是直接从 `[0, H]` 宽范围随机取。

Canonical time-window policy：

1. 先生成 depot、targets、三类 path options、service time、service energy。
2. 用 deterministic constructive scheduler 生成一个参考可行计划 `S_ref`：
   - 按 PSR/cold-trap 区域和方位角做 sector grouping。
   - 每个 sortie 使用 `low_energy` 或 `low_risk` path 做保守可行性检查。
   - 检查 capacity、energy、shadow exposure、recharge、horizon。
   - 若无法覆盖所有任务，则 reject 当前采样并重新生成。
3. 任务 horizon 按规模固定，不由时间窗 family 扩展：

```text
horizon_by_scale:
  005 ->  960 min   # 16 h
  010 ->  960 min   # 16 h
  020 -> 1680 min   # 28 h
  030 -> 1680 min   # 28 h
  050 -> 3000 min   # 50 h
  100 -> 4560 min   # 76 h
```

若参考调度 `reference_makespan > H`，reject 当前实例并重新采样；不通过放宽 horizon 来接受实例。

4. 记录每个任务在参考计划中的服务开始时间 `t_i_ref`。
5. 对每个任务生成：

```text
left_slack_i  = max(2 * time_bucket_size, 0.10 * local_sortie_duration_i)
right_slack_i = max(3 * time_bucket_size, 0.15 * local_sortie_duration_i)

window_width_cap_by_scale:
  005 -> 180 min
  010 -> 150 min
  020 -> 120 min
  030 -> 100 min
  050 ->  80 min
  100 ->  60 min

raw_r_i = t_i_ref - left_slack_i
raw_D_i = t_i_ref + sigma_i + right_slack_i

r_i = snap_down_to_bucket(max(0, raw_r_i))
D_i = snap_up_to_bucket(min(H, raw_D_i))

if D_i - r_i > cap_by_scale:
    shrink symmetrically around [t_i_ref, t_i_ref + sigma_i]
```

6. 最终必须保证：

```text
r_i <= t_i_ref
t_i_ref + sigma_i <= D_i
D_i - r_i >= sigma_i + 2 * time_bucket_size
D_i - r_i <= window_width_cap_by_scale[scale]
```

7. 生成后运行 time-window acceptance filter；不通过则 reject instance：

```text
feasible_by_reference_schedule == true
all_targets_covered_by_S_ref == true
all_windows_contain_reference_service == true
mean_window_width <= mean_width_cap_by_scale[scale]
max_window_width  <= window_width_cap_by_scale[scale]
min_window_width  >= service_time_i + 2 * time_bucket_size
```

建议第一版均值上限：

```text
mean_width_cap_by_scale:
  005 -> 150 min
  010 -> 130 min
  020 -> 100 min
  030 ->  85 min
  050 ->  70 min
  100 ->  65 min
```

当前实现的时间窗策略号为 `canonical_lunar_ice_ref_tight_v2`。相对 v1，v2 只调整 100 规模的 mean-window acceptance cap：`55 min -> 65 min`；其他规模的 cap 保持不变。

8. 如果 exact baseline 显示某一规模太难，优先调整 synthetic grid 的目标空间分布、resource budget 和 journey 初始列生成，而不是把时间窗整体放宽。时间窗只允许小幅调 slack/cap，并且必须记录 `time_window_policy_id`，保证 benchmark 可复现。

这样时间窗是“可行但收紧”的：参考计划保证至少存在一个解，固定 horizon 和 scale cap 防止窗口/候选 start 过宽导致 pricing 空间失控。

## 9. GAT 保留方式

### 9.1 GAT 可以做

```text
predict task-cover dual anchors
rank journey candidates
rank pricing target sequence / transition / path option
prioritize true-RC negative candidates
shadow branch pair scoring
opt-in branch candidate ordering
```

### 9.2 GAT 不可以做

```text
certify no negative column
change official lower bound
permanently discard true-RC negative columns
change branch feasibility
create cuts
replace exact pricing
```

注意：

- GAT 可以参与 branch candidate ranking，但不能把 learned branch score 当 proof。
- 如果 GAT 找不到有用列，必须回到 true-dual exact pricing。
- 旧 Moon Trek checkpoint 不能静默用于水冰 schema；feature schema/version 必须严格校验。

### 9.3 Feature schema

Node features：

```text
demand_or_sample_load
service_time
time_window_start
time_window_end
x_coord
y_coord
is_depot
service_energy
local_slope_risk
local_shadow_score
local_thermal_risk
expected_ice_kg
ice_confidence
planned_depth_m
planned_sample_mass_kg
```

Option features：

```text
distance
travel_time
energy
risk
generalized_cost
shadow_exposure
thermal_survival_energy
slope_risk
roughness_risk
is_low_time
is_low_energy
is_low_risk
option_rank
option_count_for_pair
```

不含任何通信特征。

## 10. 运行入口

主入口：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/run_lunar_ice_bpc.py \
  --config configs/benchmarks/lunar_ice_5_journey.yaml
```

推荐参数：

```text
--config
--instances
--time-limit
--results-csv
--log-dir
--solution-dir
--max-workers
--set key=value
--quiet
```

默认：

```yaml
master_mode: journey
journey_branching_enabled: true
journey_gat_shadow_enabled: false
journey_gat_optin_enabled: false
```

如果配置出现：

```yaml
master_mode: trip_time
```

只允许作为 smoke / ablation，不作为默认论文主线。

## 11. 配置建议

`configs/benchmarks/lunar_ice_5_journey.yaml` 最小起步：

```yaml
instances:
  - "data/instances/lunar_ice_005/instance_001_logical_graph.json"
instance_dir: "."
master_mode: "journey"
time_limit: 600
max_nodes: 100
pricing_eps: 1.0e-6
integer_tol: 1.0e-6

time_bucket_size: 10.0
pricing_start_time_step: 10.0
max_tasks_per_trip: 6
Q_ice: 6.0
resource_map_extent_km: 30.0
synthetic_grid_resolution_m: 100.0
active_footprint_by_scale:
  "005": 12.0
  "010": 12.0
  "020": 20.0
  "030": 20.0
  "050": 30.0
  "100": 30.0
horizon_min: 960.0
horizon_by_scale:
  "005": 960.0
  "010": 960.0
  "020": 1680.0
  "030": 1680.0
  "050": 3000.0
  "100": 4560.0
operation_modes:
  - detect
  - drill
  - sample
operation_mode_mix:
  detect: 0.50
  sample: 0.30
  drill: 0.20
operation_mode_params:
  detect:
    service_time_min_range: [10.0, 20.0]
    service_energy_proxy_range: [2.0, 4.0]
    demand: 0.5
  sample:
    service_time_min_range: [25.0, 45.0]
    service_energy_proxy_range: [6.0, 10.0]
    demand: 1.0
  drill:
    service_time_min_range: [45.0, 90.0]
    service_energy_proxy_range: [12.0, 20.0]
    demand: 1.5
active_fleet_limit: 1
benchmark_fleet_rule:
  "005": 1
  "010": 2
  "020": 3
  "030": 4
  "050": 5
  "100": 8

rover_max_speed_kmh: 30.0
rover_target_mean_speed_kmh: 18.0

energy_unit: "dimensionless_proxy"
B_use: 100.0
B_use_tunable_after_exact_baseline: true
recharge_model: "linear_deficit_with_dock_overhead"
dock_overhead_min: 8.0
recharge_power_proxy_per_min: 1.0
depot_chargers: "unlimited"
max_shadow_exposure_per_sortie_by_scale:
  "005": 180.0
  "010": 180.0
  "020": 240.0
  "030": 240.0
  "050": 300.0
  "100": 300.0

objective_mode: "weighted_discovery_completion"
science_weight_ice_confidence_weight: 0.6
science_weight_expected_ice_kg_weight: 0.4
objective_alpha_discovery_completion: 1.0
objective_beta_journey_end_time: 0.05
objective_gamma_lunar_ice_risk: 0.10
objective_delta_energy: 0.01

journey_branching_enabled: true
journey_max_cg_iterations: 80
journey_initial_source_trip_limit: 1200
journey_initial_max_columns: 5000
journey_pool_max_columns: 10000
journey_pool_max_trips_per_journey: 6
journey_pool_max_extensions_per_prefix: 80
journey_pool_time_limit: 3.0

journey_exact_pricing_enabled: true
journey_certificate_completion_bound_enabled: true
journey_corrected_node_bound_audit_enabled: true
journey_corrected_node_bound_fathom_enabled: false

journey_gat_shadow_enabled: false
journey_gat_optin_enabled: false

fleet_bound_mode: "computed"
fleet_bound_slack: 1
fleet_bound_cost_safe: true
fleet_bound_log: true

cuts_enabled: true
fleet_lower_bound_cut_enabled: true
subset_row_cuts_enabled: true

results_csv: "runs/csv/lunar_ice_5_journey.csv"
log_dir: "runs/logs/lunar_ice_5_journey"
solution_dir: "runs/solutions/lunar_ice_5_journey"
```

`lunar_ice_5/10/20` benchmark 配置默认 `time_limit: 600`；`lunar_ice_30/50/100` benchmark 配置默认 `time_limit: 3600`。

禁止配置键：

```text
communication_enabled
comm_window_enabled
comm_blackout_weight
link_margin_weight
earth_visibility_enabled
relay_visibility_enabled
```

## 12. 实施顺序

### Step 1：项目骨架收敛

- 在 `GAT_BPC_moonTerk` 下采用 `src/lunar_ice_bpc/` 包名。
- 保留当前 README 中的 proof/guidance 边界。
- 新增 `pyproject.toml`。
- 不再新建平行 `gnn_bb/lunar_ice_bpc/`。

### Step 2：迁移 exact journey 主干

- 迁移 `core/data.py`、`core/columns.py`、`core/journey.py`。
- 迁移 `master/journey_rmp.py`。
- 迁移 `pricing/journey_pricing.py` 及必要 helper。
- 迁移 `solver/journey_driver.py`，但删除旧 runbook/probe/report 专用分支。
- 所有 import 从 `BPC_future` 改为 `lunar_ice_bpc`。

### Step 3：跑通旧格式兼容 smoke

先用一个极小手写 logical graph，不急着接真实水冰数据：

```text
load data
seed timed trips
build initial journey pool
solve journey RMP
run pricing
write solution
```

### Step 4：重写月表水冰数据生成

- 固定一个高照明 depot。
- 在 PSR / cold-trap / high ice-confidence 区域采样 target。
- 计算月表水冰版 `lunar_ice_cell_risk`，不要沿用旧的 slope/roughness-only risk。
- 对每条 directed logical edge 只构造 low_time / low_energy / low_risk 三条 path options。
- 写 logical graph JSON 和 manifest。

### Step 5：重写 scheduling augmentation

生成：

```text
service time
service energy
service cost
thermal/operation time windows
shadow exposure
recharge time
```

不生成通信窗口。
不生成三类时间窗场景；每个规模只使用一套 canonical thermal/operation time-window policy。

### Step 6：迁移 GAT guidance

- 迁移 graph builder、GNN model、column selector、dual stabilizer。
- 替换 feature schema 为水冰 schema。
- 默认 shadow-only。
- checkpoint schema 必须严格校验。

### Step 7：轻量可视化

实现一个轻量入口：

```bash
python scripts/draw_lunar_ice_instance.py --instance data/instances/lunar_ice_005/instance_001_logical_graph.json
```

只输出：

```text
resource map
depot / target layout
logical graph
path option overlay
solution route overlay
```

不复制旧 `BPC_future/draw/`。

### Step 8：5/10/20/30/50/100 benchmark

按顺序建立：

```text
lunar_ice_5_journey
lunar_ice_10_journey
lunar_ice_20_journey
lunar_ice_30_journey
lunar_ice_50_journey
lunar_ice_100_journey
```

每种规模生成 20 个 accepted instances。每一档先跑 exact baseline，再跑 GAT shadow，再考虑 GAT opt-in。

运行时间预算：

```text
005 / 010 / 020: 600s per instance
030 / 050 / 100: 3600s per instance
```

批量运行默认：

```text
max_workers: 4
```

验收口径：

```text
005: 20/20 exact OPTIMAL within 600s, mean optimal solve time over 20 instances < 5s
010: 20/20 exact OPTIMAL within 600s, mean optimal solve time over 20 instances < 10s
020: 20/20 exact OPTIMAL within 600s, mean optimal solve time over 20 instances < 100s
030: exact OPTIMAL count >= 15/20, mean optimal solve time over OPTIMAL instances < 250s
050: valid gap for benchmark runs, and exact OPTIMAL count >= 3/20
100: scalable benchmark only; exact closure not required
```

对 50/100 规模，如果 exact closure 失败，必须报告 incumbent、best bound / gap、pricing workload、node count、incomplete reason 和 timeout reason，不能声称 exact optimality。

### 12.1 当前 exact baseline 实现边界

当前实现已经把 benchmark 输出中的 exact claim 分成三个 scope：

```text
fixed_logical_graph_exhaustive_direct_dp
  -> 固定三路径 logical graph 上的 exhaustive direct-DP exact baseline。
  -> 当前 5 / 10 / 20 规模可用。

restricted_canonical_path_universe
  -> 只在 canonical path universe 上求得 restricted optimum。
  -> 不能计入 exact baseline closure。

none
  -> 只有 reference / seeded incumbent 和 relaxation gap。
  -> 不能计入 exact baseline closure。
```

CSV / summary / audit 必须同时报告：

```text
exact_status
exact_claim_scope
bpc_certificate_status
uses_true_dual_bpc_certificate
```

当前 certificate 边界已经分层：

- `005` 规模在 fixed logical graph 上完成 exhaustive pricing closure、RMP dual binding 和 completion-bound on/off 一致性审计后，可输出 scoped true-dual BPC certificate。
- `010` 规模在 fixed logical graph 上完成 complete direct-root LP、RMP dual binding 和非负 reduced-cost 检查后，可输出 scoped true-dual BPC certificate；该证书只覆盖 root LP、无 cuts、无 branching。
- `020` 规模当前只作为 fixed-graph direct exact baseline 证据，不自动升级为 BPC certificate。
- `030/050/100` 当前仍是 reference / seeded incumbent + scalable gap 证据，不产生 BPC certificate。

当前 direct exact baseline 不再使用显式 `permutation x path-choice` 全枚举。旧 10 规模 direct universe 需要约 `354,004,920` 个 route/path 模板，不可用；当前实现改为 label-setting direct DP：

- sortie 内按 `(visited task set, last task)` 做 Pareto 剪枝；
- journey 内按 `(covered task set, end time, base cost)` 做 Pareto 剪枝；
- 仍覆盖每条 leg 的三种 path choice：`low_time / low_energy / low_risk`；
- direct-DP / direct-pricing 会先删除 per-arc dominated path option：若另一条 path 在 `travel_time_min`、`energy_proxy`、`risk_integral`、`shadow_exposure_min` 四个单调维度上均不差且至少一个维度更好，则被支配 path 不枚举。这不改变 fixed-graph optimum。
- `direct_baseline_max_tasks` 与 `direct_pricing_max_tasks=5` 解耦，避免 diagnostic pricing / root certificate 的规模上限限制 fixed-graph direct exact baseline。
- 当前 benchmark 配置中，`005/010` 使用 `direct_baseline_max_tasks=10`，`020` 使用 `direct_baseline_max_tasks=20`。
- direct-root certificate 的默认上限封顶为 `10`；20 规模 direct-root LP 探针因内存压力被系统杀死，当前必须 skip，不能默认打开。

当前验证证据：

```text
005: 20/20 EXACT_BASELINE_OPTIMAL, exact_claim_scope=fixed_logical_graph_exhaustive_direct_dp,
     mean exact_baseline_wall_time_sec = 0.020173 < 5.0
     true_dual_bpc_certificate_count = 20/20
     pricing_certificate_selected_source = true_dual_pricing_tail

010: 20/20 EXACT_BASELINE_OPTIMAL, exact_claim_scope=fixed_logical_graph_exhaustive_direct_dp,
     mean exact_baseline_wall_time_sec = 4.254416 < 10.0
     true_dual_bpc_certificate_count = 20/20
     pricing_certificate_selected_source = true_dual_pricing_tail
     lower_bound_source = direct_fixed_graph_root_lp

020: 20/20 EXACT_BASELINE_OPTIMAL, exact_claim_scope=fixed_logical_graph_exhaustive_direct_dp,
     mean exact_baseline_wall_time_sec = 7.908368 < 100.0
     max exact_baseline_wall_time_sec = 17.771096 < 600.0
     true_dual_bpc_certificate_count = 0/20
```

因此当前 fixed-graph exact baseline 已覆盖 `005/010/020` 三档 benchmark，并满足计划中的平均运行时间目标。`005` 已进一步形成 fixed-graph pricing-closure true-dual certificate 和 node-bound fathom；`010` 已进一步形成 direct-root scoped true-dual certificate 和 node-bound fathom；`020` 仍不产生 true-dual BPC certificate。
当前 `005/010/020` benchmark CSV 已按现有 schema 刷新，包含 `pricing_certificate_selected_source`、`true_dual_pricing_tail_status` 和 `completion_bound_consistency_*` 字段；`005/010` 会选择 `true_dual_pricing_tail`，`020` 诊断路径保持 fail-closed。

当前环境可 import `gurobipy 13.0.2`，但 license 是 size-limited；简单 3000 binary model 会被拒绝。因此后续 30/50 或 true-dual closure 不能依赖大 MIP，应优先移植/实现 true-dual journey BPC proof path，或继续扩展不受 license 限制的 exact label-pricing + branch-and-price。

30 规模当前边界：

- 代表实例 `lunar_ice_030_001_seed929001` 的 single-start sortie candidate 生成仍可控：约 `0.908s`，`3842` 个 Pareto sortie candidates。
- 但完整 fixed-graph direct exact baseline 在当前 DP/DFS 下超过 `5 min` 仍未闭合，不适合作为默认 30 benchmark exact path。
- 因此 `030` benchmark 配置暂时保持 `direct_baseline_max_tasks=10`，不默认打开 direct30。
- 已新增 `direct_baseline_time_limit` / `--direct-baseline-time-limit` fail-closed 机制；当 direct baseline 超时，CSV / summary / audit 会报告 `direct_baseline_status=DIRECT_DP_BASELINE_TIME_LIMIT`，主结果回退到 reference / seeded incumbent，`exact_claim_scope=none`。
- 当前 direct baseline 超时会保留 partial enumeration diagnostics，而不是把计数清零。加入 dominated path option 过滤和 large-partition 剪枝后，`lunar_ice_030/instance_001` 在 `30s` hard timeout 下返回：
  - `generated_journey_count=285742`
  - `generated_sortie_count=53892103`
  - `route_template_count=767979`
  - `pareto_label_count=415780`
  - `set_partition_state_count=0`
  这说明同样 30 秒内 journey label DP 推进更深，且 route-template 分支更少。
- 同一实例在 `120s` hard timeout 下已经能完成 single-vehicle journey label DP 并进入 fleet set-partition：
  - `generated_journey_count=535160`
  - `generated_sortie_count=95866502`
  - `route_template_count=1430820`
  - `pareto_label_count=806906`
  - `set_partition_state_count=37550`
  当前 30 exact closure 的主要瓶颈已转向 partition / branch-price proof，而不只是 sortie candidate generation。
- 当前默认 large partition 搜索保留多类 exact-safe 辅助：service-only remaining lower bound、dual-feasible task-cover lower bound、cardinality-cost relaxation、有限宽度 beam cover incumbent、静态最少支持任务分支、同一 `(remaining_mask, vehicle_slots)` 下的累计成本支配缓存。当剩余 wall-time 至少约 `180s` 时，还会构造缩放后可行的 LP cover-dual lower bound。它们都不改变 fixed-graph optimum，不产生 official lower bound 或 BPC certificate；120 秒探针仍未闭合，说明它们只能缓解而不能解决 30/50 exact closure。
- LP cover-dual 单独探针在该实例上可得到 fixed-column-universe feasible bound `5436.315639`，当前 greedy incumbent 约 `5596.579726`；但接入后 `300s` direct baseline 仍超时于 fleet set-partition，`set_partition_state_count=169124`，尚未形成 30 exact closure。
- 已验证但未保留的 direct-DP 剪枝尝试：
  - `(start_time, remaining_mask)` 级 sortie candidate 生成会减少无关候选，但破坏 start-time cache 复用；`lunar_ice_020/instance_001` 探针从旧 CSV 约 `18.95s` 上升到约 `28.48s`。
  - hybrid `(start_time, remaining_mask)` cache 只在剩余任务数较小时启用，也未改善 30 秒探针；`lunar_ice_030/instance_001` 仍在 sortie candidate generation 阶段超时，且计数略差，因此已回滚。
  - 全局 fleet-label A* 原型使用 reference incumbent 和 service-only admissible lower bound，`60s` 内仍膨胀到约 `5.28M` heap states、`3.47M` Pareto states，未找到 full cover；说明仅调整搜索组织而没有更强 lower bound 不足以关闭 30。
  - reference journey task partition 可以提供可行上界，但作为 runner 默认 seed 未改善 30 的固定时限探针，因此未保留。
  - task-share set-partition lower bound 是 exact-safe 的，但该实例只剪掉 `1866` 个 partition search node，整体探针上升到约 `32.76s`。
  - 动态“当前 feasible candidate 最少任务”分支用 Python 列表扫描时剪枝很强，但单状态扫描成本过高；`120s` 探针只到约 `1724` 个 partition states，未闭合，因此未保留。
  - 基于 Python 大整数 column bitset 的动态分支同样 exact-safe，但索引构建和每状态过滤成本偏高；`300s` 探针只到约 `1977` 个 partition states，未闭合，因此未保留。
  - two-slot exact cache / three-slot tail 直接闭合会让 deep tail 扫描前移，`120s` 探针只到约 `3` 个可解释 partition states，未改善闭合，因此未保留。
  - 因此这些尝试不作为当前默认实现保留；后续 30/50 closure 应优先做真正 branch-and-price / true-dual pricing proof path，或更强的 DP 状态压缩，而不是增加递归节点内重计算。
- 30 规模后续要达成 `>=15/20` exact closure，不能只靠当前 root-level fixed-graph DP，下一步应实现 branch-and-price / true-dual pricing proof path，或继续加强 direct label DP 的 exact partition 剪枝。

当前大规模默认 benchmark 证据：

```text
030 default benchmark:
  audit_status = FAIL
  exact_optimal_count = 0/20, required = 15/20
  valid_gap_count = 20/20
  pricing_workload_reported_count = 20/20
  incomplete_reason_reported_count = 20/20
  mean_wall_time_sec = 11.913857
  mean_relaxation_gap = 0.074912543

050 default benchmark:
  audit_status = FAIL
  exact_optimal_count = 0/20, required = 3/20
  valid_gap_count = 20/20
  pricing_workload_reported_count = 20/20
  incomplete_reason_reported_count = 20/20
  mean_wall_time_sec = 12.114320
  mean_relaxation_gap = 0.037085657

100 default benchmark:
  audit_status = PASS
  exact_optimal_count = 0/20, required = 0/20
  valid_gap_count = 20/20
  pricing_workload_reported_count = 20/20
  incomplete_reason_reported_count = 20/20
  mean_wall_time_sec = 14.587853
  mean_relaxation_gap = 0.026705592
```

这说明 scalable reporting 链已经可用：30/50/100 都能报告 incumbent、analytic lower bound / gap、pricing workload、node count 和 incomplete reason；但 30/50 的 exact closure 目标仍未满足。
当前 `030/050/100` benchmark CSV 也已按现有 schema 刷新；三档均记录 `pricing_certificate_selected_source=diagnostic_fallback`，`true_dual_pricing_tail_status=TRUE_DUAL_PRICING_TAIL_NEGATIVE_FOUND`，表示 diagnostic pricing 发现负 reduced-cost 候选，仍需继续 column generation / true-dual pricing proof，不能关闭节点。

当前 lower-bound ledger 边界：

- 已新增 `exact/certificates/bound_ledger.py`，把 official lower bound 与 diagnostic bound 分开记录。
- 当前 `lower_bound` / `relaxation_gap` 只读取 `official_lower_bound=true` 的记录；默认 source 仍是 `analytic_relaxation`，scope 为 `global_relaxation`。
- `restricted_journey_rmp` 始终只进入 `best_diagnostic_bound_*` 字段，`diagnostic_bound_is_official=false`，不能提升 official gap，不能用于 `OPTIMAL` 或 BPC certificate 声明。
- `direct_fixed_graph_root_lp` 只有在 complete fixed-graph direct-root LP 通过 scoped true-dual certificate 条件时，才会作为 official lower bound；否则仍按 diagnostic record 处理。
- 5-task smoke 输出：
  - `status=DIRECT_DP_BASELINE_OPTIMAL`
  - `lower_bound_source=direct_fixed_graph_root_lp`
  - `gap_type=official_bpc_node_bound`
- 30-task fallback smoke 输出：
  - `status=FEASIBLE_REFERENCE`
  - `exact_status=NOT_SOLVED`
  - `exact_claim_scope=none`
  - `lower_bound_source=analytic_relaxation`
  - `best_diagnostic_bound_source=restricted_journey_rmp`

当前 no-negative pricing certificate 边界：

- 已新增 `exact/certificates/pricing_certificate.py`，集中管理 no-negative certificate artifact。
  - 顶层 `pricing_certificate` 通过 `select_effective_pricing_certificate()` 选择证书来源；
  - 只有 certified true-dual tail 可以成为 active no-negative certificate；
  - 默认仍应为 `selected_certificate_source=diagnostic_fallback`。
- 已新增 `exact/certificates/pricing_frontier.py`，集中管理 reduced-cost frontier ledger。
- 已新增 `exact/certificates/dual_binding.py`，集中管理 RMP dual-vector binding artifact：
  - 记录 pricing evidence 使用的是哪个 solved RMP 的 task-cover / fleet / cut dual；
  - 输出稳定 `dual_vector_fingerprint`，供后续 true-dual pricing tail 审计；
  - 它只是 proof input，不是 no-negative certificate。
- 已新增 `exact/certificates/true_dual_pricing_tail.py`，作为 true-dual pricing tail 的单一证书入口：
  - 当前 runner 会把 fixed-graph closure、complete direct-root LP 或 direct-pricing 诊断 evidence 绑定到该 artifact；
  - 诊断 evidence 继续 fail closed；
  - 当 fixed-graph closure 满足 complete coverage、RMP dual vector 已绑定、completion-bound on/off 一致且 `min_reduced_cost >= -eps`，或 complete direct-root LP 满足 dual binding 与非负 reduced-cost 检查时，允许变成 `TRUE_DUAL_PRICING_TAIL_CERTIFIED`。
- 已新增 `exact/certificates/node_bound.py`，集中管理 BPC node-bound / fathom artifact。
- 已新增 `exact/certificates/certificate_readiness.py`，集中记录 true-dual BPC certificate readiness：
  - 汇总 pricing certificate、restricted RMP、node-bound artifact 和 direct-pricing 诊断；
  - 输出 `WAITING_TRUE_DUAL_PRICING_PROOF` / `BLOCKED_*` / `TRUE_DUAL_CERTIFICATE_READY`；
  - solution / CSV / summary 记录缺失 proof inputs，但不会把 diagnostic pricing 升级成 certificate。
- 当前 direct / restricted / seeded diagnostic pricing 仍 fail closed 为 `status=NOT_PORTED_TRUE_DUAL_BPC`，`can_certify_no_negative=false`。
- 只有 fixed-graph closure、complete direct-root LP 或未来 full BPC pricing 同时满足：
  - `uses_true_dual_bpc_certificate=true`
  - `pricing_complete=true`
  - `coverage_complete=true`
  - `min_reduced_cost >= -negative_eps`
  才允许输出 `CERTIFIED_NO_NEGATIVE`。
- `pricing_certificate` 现在内嵌 `frontier_ledger`，记录 `pricing_frontier_status`、`global_remaining_rc_lower_bound`、`lower_bound_official`、`can_certify_no_negative` 和 fail-closed issues。
- 当前 diagnostic direct pricing 的 frontier status 可能是 `DIAGNOSTIC_FRONTIER_ONLY` 或 `NEGATIVE_REDUCED_COST_FOUND`，但 `lower_bound_official=false`；只有通过 true-dual fixed-graph closure、complete direct-root LP 或未来 full BPC pricing coverage 时才可升级为 official no-negative evidence。
- `node_bound_certificate` 现在汇总 incumbent、bound ledger、pricing certificate、branch context 和 cut context；analytic relaxation、restricted RMP 和未通过 true-dual 检查的 fixed-graph root LP 都不会被当作 official BPC node bound，因此默认：
  - `node_bound_certificate_status=NODE_BOUND_FAIL_CLOSED`
  - `node_bound_lower_bound_official=false`
  - `node_bound_can_fathom_by_bound=false`
- 5-task certificate smoke：
  - `status=DIRECT_DP_BASELINE_OPTIMAL`
  - `bpc_certificate_status=CERTIFIED_NO_NEGATIVE`
  - `pricing_certificate_status=CERTIFIED_NO_NEGATIVE`
  - `pricing_certificate_selected_source=true_dual_pricing_tail`
  - `pricing_certificate_can_certify_no_negative=true`
  - `pricing_frontier_status=CERTIFIED_FRONTIER_NO_NEGATIVE`
  - `pricing_frontier_lower_bound_official=true`
  - `node_bound_certificate_status=NODE_BOUND_FATHOMED`
  - `lower_bound_source=fixed_graph_pricing_closure_lp`
  - `gap_type=official_bpc_node_bound`
- 30-task fallback certificate smoke：
  - `status=FEASIBLE_REFERENCE`
  - `exact_status=NOT_SOLVED`
  - `bpc_certificate_status=NOT_PORTED_TRUE_DUAL_BPC`
  - `pricing_certificate_can_certify_no_negative=false`

当前 completion-bound 边界：

- 已新增 `exact/pricing/completion_bounds.py`，提供第一版 direct-label completion-bound 前置结构。
- 当前 bound 只使用 task-cover dual 的正奖励项：

```text
LB_tail(R) = - sum_{i in R} max(pi_i, 0)
LB_label = reduced_base(label)
         + beta * end_time(label)
         + LB_tail(remaining_tasks)
```

- fleet dual、cut dual、branch dual 不进入 completion bound；fleet dual 只在 direct-label pricing 调用侧作为所有 column 的常数项参与比较。
- `price_direct_journey_columns()` 默认启用该 bound，用于剪掉不可能优于当前 best reduced cost 的 direct-label 扩展，并在 solution / CSV / summary 记录：
  - `direct_pricing_completion_bound_enabled`
  - `direct_pricing_completion_bound_pruned_label_count`
  - `direct_pricing_completion_bound_evaluated_label_count`
  - `direct_pricing_completion_bound_can_certify=false`
- 已新增 `exact/certificates/completion_bound_consistency.py`：
  - 在同一 RMP dual 下分别运行 bound-on / bound-off exhaustive direct pricing；
  - 检查 best reduced cost 与 negative-found 判定是否一致；
  - 作为 future true-dual tail 加速前的 safety check，不改变 solver、不产生 certificate。
- 已新增 `price_exhaustive_direct_journey_columns()` 小规模 fixed-graph exhaustive pricing wrapper：
  - 当 `task_count <= max_direct_tasks` 时，对所有非空 task subset 做 direct-label pricing；
  - 输出 `pricing_complete_for_all_task_subsets=true` 和 `exhaustive_candidate_set_count`；
  - wrapper 本身仍 `can_certify_no_negative=false`，只有进入 fixed-graph closure 并通过 dual-binding / consistency 条件后才可发证。
- 已新增 `exact/certificates/fixed_graph_pricing_proof.py`：
  - 把当前 restricted RMP duals、branch/cut context 和 exhaustive direct-label pricing 绑定成 fixed-logical-graph node pricing proof snapshot；
  - 可报告 `FIXED_GRAPH_NO_NEGATIVE_PROVED` 或 `FIXED_GRAPH_NEGATIVE_REDUCED_COST_FOUND`；
  - benchmark CSV 输出 `fixed_graph_pricing_proof_*` 字段；
  - 当前仍 `uses_true_dual_bpc_certificate=false`、`lower_bound_official=false`、`can_certify_no_negative=false`，不能作为 official BPC no-negative certificate。
- 已新增 `exact/solver/fixed_graph_pricing_closure.py`：
  - 每轮重解 restricted RMP，用 exhaustive direct-label pricing 找 fixed-graph negative reduced-cost columns；
  - 把新 negative fixed-graph columns 加入 supplied pool 后继续；
  - 闭合时输出 `FIXED_GRAPH_PRICING_CLOSED` 和 `fixed_graph_pricing_closure_*` CSV 字段；
  - 若闭合后同时满足 complete coverage、RMP dual binding、completion-bound on/off 一致和非负 reduced cost，则输出 `uses_true_dual_bpc_certificate=true`、`lower_bound_official=true`、`can_certify_no_negative=true`；
  - 否则仍 fail closed，不能作为 official BPC no-negative certificate。
- direct-label pricing 现在支持 `cut_context`：
  - `price_direct_journey_columns(..., cut_context=...)` 会把 active cut coefficients 纳入最终 reduced-cost 比较；
  - `run_direct_pricing_column_generation(..., cut_context=...)` 会在 restricted RMP re-solve 和 pricing 中保留同一个 cut context；
  - 当 `cut_context` 非空时，completion-bound pruning 自动关闭；cut dual 不进入 optimistic tail bound，避免错误剪枝。
- direct-label pricing 现在也支持 `branch_context`：
  - `price_direct_journey_columns(..., branch_context=...)` 会过滤掉 Ryan-Foster branch-infeasible journey columns；
  - payload 记录 `branch_context_active`、`branch_decision_count` 和 `branch_filtered_column_count`；
  - `run_direct_pricing_column_generation(..., branch_context=...)` 会在 node RMP re-solve 和 direct pricing 中保留同一个 branch context；
  - 当 `branch_context` 非空时，completion-bound pruning 也自动关闭，避免 branch-infeasible incumbent 导致错误剪枝。
- 该结构是 true-dual pricing tail 的前置能力；小规模 fixed-graph closure 已可在严格闭合条件下产生 scoped official lower bound 和 no-negative certificate，未闭合或 partial pricing 仍 fail closed。

当前 branch context 边界：

- 已新增 `exact/core/branching.py`，提供第一版 Ryan-Foster 风格 pair branch context。
- 已新增 `exact/solver/branch_probe.py`，提供 supplied-column-pool 上的 deterministic branch candidate artifact。
- 当前支持两类 exact branch decision：
  - `same_journey`：一对任务必须出现在同一个 journey column 中，或同时不出现在该 column 中；只覆盖其中一个任务的 column 会被过滤。
  - `different_journey`：一对任务禁止出现在同一个 journey column 中。
- `solve_restricted_journey_rmp()` 已支持可选 `branch_context`，并在 solution / CSV 中记录：
  - `branch_context.pair_decision_count`
  - `branch_filtered_column_count`
  - `restricted_rmp_branch_decision_count`
  - `restricted_rmp_branch_filtered_column_count`
- 默认 root context 为空，5-task branch smoke 输出：
  - `restricted_rmp_branch_decision_count=0`
  - `restricted_rmp_branch_filtered_column_count=0`
  - `exact_status=EXACT_BASELINE_OPTIMAL`
  - `bpc_certificate_status=NOT_PORTED_TRUE_DUAL_BPC`
- 5-task branch-probe smoke 输出：
  - `branch_probe_status=BRANCH_PROBE_READY`
  - `branch_probe_candidate_count=10`
  - `branch_probe_reported_candidate_count=10`
  - `branch_probe_mutates_solver=false`
  - `branch_probe_can_certify=false`
- restricted RMP 现在输出 supplied-column-pool LP 的 diagnostic primal lambda payload：
  - `restricted_rmp_primal_active_column_count>=1`
  - `restricted_rmp_primal_cover_residual_max<=1e-6`
  - `restricted_rmp_primal_fleet_usage>0`
- 已新增 `build_fractional_branch_probe()`，基于 restricted RMP primal lambda 计算 Ryan-Foster pair 的 same-journey fraction：
  - `fractional_branch_probe_status=FRACTIONAL_BRANCH_PROBE_READY 或 NO_FRACTIONAL_BRANCH_CANDIDATE`
  - `fractional_branch_probe_mutates_solver=false`
  - `fractional_branch_probe_can_certify=false`
- branch-node queue 会优先使用 fractional RMP-primal branch candidate；如果当前 restricted LP 没有 fractional pair，则回退到 support-based branch probe。
- 已新增 `exact/solver/branch_tree.py`，提供第一版 branch-node context ledger。
- 当前 `branch_tree_probe` 把 `branch_probe` 的首个候选对展开成 root、same-child、different-child 三个 diagnostic node，并在当前 supplied column pool 上重解 root/child restricted RMP：
  - `branch_tree_probe_status=BRANCH_TREE_RESTRICTED_RMP_EVALUATED`
  - `branch_tree_probe_node_count=3`
  - `branch_tree_probe_child_count=2`
  - `branch_tree_probe_reported_branch_pair_count=1`
  - `branch_tree_probe_restricted_rmp_evaluation_enabled=true`
  - `branch_tree_probe_evaluated_node_count=3`
  - `branch_tree_probe_child_evaluated_count=2`
  - `branch_tree_probe_child_restricted_rmp_value_count>=1`
  - `branch_tree_probe_mutates_solver=false`
  - `branch_tree_probe_can_certify=false`
- 这只是 branch feasibility / filtering / candidate-diagnostic / branch-node-ledger 前置能力，不是真正 branch-and-price tree search，也不产生 certificate。fractional branch probe 只读取 supplied-column-pool restricted RMP primal lambda；branch tree probe 的 child RMP 只在 supplied column pool 上求诊断值，不做 full journey pricing、不改变 solver `node_count`、不改变 official lower bound。未来接入真正 BPC node 后，GAT branch score 只能排序 branch candidates，不能改变 `BranchContext` 的 exact feasibility 语义。
- 已新增 `exact/solver/branch_node_queue.py`，提供 restricted branch-node queue 诊断驱动。
- 当前 `branch_node_queue` 从 root context 出发，在 supplied journey-column pool 上做多节点 restricted RMP 评估，并用 support-based `branch_probe` 生成下一层子节点；默认 `max_nodes=7`、`max_depth=2`：
  - `branch_node_queue_status=RESTRICTED_BRANCH_NODE_QUEUE_EVALUATED`
  - `branch_node_queue_node_count>=3`
  - `branch_node_queue_evaluated_node_count=branch_node_queue_node_count`
  - `branch_node_queue_expanded_node_count>=1`
  - `branch_node_queue_restricted_rmp_value_count>=1`
  - `branch_node_queue_direct_pricing_probe_enabled=true`
  - `branch_node_queue_direct_pricing_probe_node_count=3`
  - `branch_node_queue_branch_feasible_negative_count>=0`
  - `branch_node_queue_direct_pricing_probe_can_certify_no_negative=false`
  - `branch_node_queue_post_pricing_restricted_rmp_node_count>=0`
  - `branch_node_queue_post_pricing_added_column_count>=0`
  - `branch_node_queue_post_pricing_lower_bound_official=false`
  - `branch_node_queue_node_pricing_certificate_can_certify_count=0`
  - `branch_node_queue_node_bound_incumbent_attached_count=branch_node_queue_node_count`
  - `branch_node_queue_node_bound_incumbent_missing_count=0`
  - `branch_node_queue_node_bound_fail_closed_count=branch_node_queue_node_count`
  - `branch_node_queue_node_bound_can_fathom_count=0`
  - `branch_node_queue_lower_bound_official=false`
  - `branch_node_queue_mutates_solver=false`
  - `branch_node_queue_can_certify=false`
- 前 3 个 evaluated node 会运行 capped direct-label pricing probe，并把返回列按该 node 的 `BranchContext` 过滤后记录 branch-feasible reduced-cost 诊断；这只能发现已返回的负列，不能证明没有负列。
- 如果 node pricing probe 返回新的 branch-feasible 负 reduced-cost column，会把这些列临时加入该节点列池并重解一次 restricted RMP，记录 `post_pricing_restricted_rmp_*` 诊断字段；该 re-solve 仍只覆盖 supplied pool + returned direct columns。
- 每个 evaluated node 会写入 fail-closed `pricing_certificate` 和 `node_bound_certificate` 快照；`solve_reference()` 选出 incumbent 后会回填 `incumbent_objective` 并刷新节点级 node-bound artifact。当前节点级证书状态应保持 `NOT_PORTED_TRUE_DUAL_BPC` / `NODE_BOUND_FAIL_CLOSED`。
- 这一步让新项目具备可审计的 branch-node queue + node-level pricing workload + single-step diagnostic CG re-solve 形态，但仍不是最终 BPC driver：队列节点没有 full exact pricing、没有 true-dual no-negative certificate、没有 official node bound、没有 fathom 权限，不能改善 `certified_optimal_count` 或 `true_dual_bpc_certificate_count`。

当前 cut context 边界：

- 已新增 `exact/core/cuts.py`，提供第一版 cut context artifact。
- 当前支持：
  - `subset_row`：按 `floor(|S intersect S_j| / divisor)` 计算 journey-column cut coefficient。
  - `fleet_lower_bound`：对非空 journey column 给出系数 `1.0`。
- `manual_journey_reduced_cost(journey, duals, cut_coefficients=...)` 已能读取 cut dual 项：

```text
rc(j) = c_j - mu - sum_i pi_i a_ij - sum_k gamma_k a_kj
```

- `solve_restricted_journey_rmp(..., cut_context=...)` 已支持可选 active cut rows：
  - subset-row cut 按 `<= rhs` 加入 dual LP，导出的 cut dual 为非正值；
  - fleet-lower-bound cut 按 `>= rhs` 加入 dual LP，导出的 cut dual 为非负值；
  - RMP payload 会记录 `cut_duals`、`primal_cut_activities` 和 `primal_cut_violation_max`；
  - 这仍只覆盖 supplied column pool，是 restricted diagnostic bound，不是 official BPC lower bound。
- 默认 runner 不激活 cut rows，只记录空 cut context：
  - `restricted_rmp_cut_count=0`
  - `restricted_rmp_cut_rows_active=false`
  - `exact_status=EXACT_BASELINE_OPTIMAL`
  - `bpc_certificate_status=NOT_PORTED_TRUE_DUAL_BPC`
- 现在额外输出 `cut_probe` 诊断 artifact：
  - 基于 restricted RMP primal lambda 计算 `subset_row` / `fleet_lower_bound` candidate activity；
  - benchmark CSV / summary 记录 `cut_probe_status`、候选数量、violated subset candidate 数量；
  - `cut_probe.rows_added_to_rmp=0`，`cut_probe.cut_rows_active=false`，`cut_probe.can_certify=false`。
- 已新增 `exact/solver/cut_separator.py`，提供一轮 restricted cut separation 诊断：
  - 默认只从 `cut_probe.subset_candidates` 中选 violated subset-row cut；
  - 默认不加入 `fleet_lower_bound` cut，因为 journey 模型允许单车多 sortie，fleet lower-bound 需要额外 exact-safe 证明后才能自动启用；
  - 如果选中 cut，会重解一次 active-cut restricted RMP，并输出 `cut_separation_probe` / CSV 字段；
  - `cut_separation_lower_bound_official=false`、`cut_separation_mutates_solver=false`、`cut_separation_can_certify=false`。
- 因此 cut context 目前已经具备 optional LP-row 和 one-round separation 通路，但默认 benchmark 仍不把 cut re-solve 作为 official bound；显式 active cut rows 也只能影响 restricted diagnostic RMP，不能影响 official lower bound、pricing certificate 或 OPTIMAL 声明。

当前 GAT shadow 批处理验证证据：

```text
005/010/020 GAT shadow:
  reports = 60/60
  mode_counts = {"shadow_only": 60}
  mutates_solver_count = 0
  can_certify_count = 0
  exact_status_effect_counts = {"none": 60}
  summary = runs/logs/gat_shadow_005_010_020_summary.json

005/010/020/030/050/100 GAT shadow:
  reports = 120/120
  mode_counts = {"shadow_only": 120}
  mutates_solver_count = 0
  can_certify_count = 0
  exact_status_effect_counts = {"none": 120}
  summary = runs/logs/gat_shadow_all_summary.json
```

这表示 GAT 当前只产出诊断性排序/图特征报告，不改变 solver、不提供 lower bound、不提供 certificate，也不改变任何 exact status。GAT opt-in 仍应等 true-dual BPC 证书路径和数据 schema 稳定后再打开。

当前项目级 refactor audit 证据：

```text
command:
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  python scripts/audit_lunar_ice_refactor.py \
    --output-json runs/logs/lunar_ice_refactor_audit.json \
    --instance-samples-per-scale 1

result:
  overall_status = IN_PROGRESS
  hard_failures = 0
  incomplete_sections = ["benchmark_evidence"]

passing sections:
  runtime_legacy_link_scan = PASS
  manifest = PASS
  gat_shadow = PASS

incomplete evidence:
  030: final exact closure target is not met yet
  050: final exact closure target is not met yet
```

该 audit 的目标不是提前声明完成，而是把计划中的边界变成可执行验收：运行代码/配置不能含旧通信建模字段，120 实例 manifest 必须完整，GAT shadow 必须保持 non-mutating / non-certifying，benchmark evidence 必须明确区分已通过、小规模 fixed-graph exact baseline、scoped true-dual certificate、scalable gap，以及仍未完成的 30/50 exact closure。最终验收时可使用 `--validate-all-instances --strict-final` 做更强检查。

当前 benchmark audit 已单独统计 fixed-graph pricing closure 诊断证据：

```text
fixed_graph_pricing_closure_closed_count
fixed_graph_pricing_closure_diagnostic_only_count
fixed_graph_pricing_closure_status_counts
completion_bound_consistency_pass_count
completion_bound_consistency_status_counts
pricing_certificate_selected_source_counts
true_dual_readiness_fixed_graph_closure_complete_count
true_dual_readiness_waiting_true_dual_count
true_dual_readiness_status_counts
true_dual_pricing_tail_certified_count
true_dual_pricing_tail_not_ported_count
true_dual_pricing_tail_dual_vector_bound_count
true_dual_pricing_tail_status_counts
```

这些字段说明固定三路径 logical graph 上的 pricing closure / direct-root LP 状态、RMP dual-vector 是否已作为 proof input 绑定，以及 true-dual pricing tail 是否已认证。只有 closure 闭合、coverage complete、dual binding 成功、completion-bound consistency 通过且最小 reduced cost 非负，或 complete direct-root LP 通过 dual binding 与非负 reduced-cost 检查时，才会增加 `true_dual_bpc_certificate_count` 和 `certified_optimal_count`。

当前 lunar scenario schema 边界：

- 用户已确认第一版靠近现实的核心是控制单个 sortie 在 PSR / shadow 区域的最大暴露时间；active footprint 按规模扩大，synthetic grid resolution 固定 `100 m`，`B_use` 可由 exact baseline 结果继续校准。
- `validate_instance()` 已把第一版月表水冰场景参数作为 schema contract 检查，而不是只依赖计划文档说明。
- 检查项包括：
  - `30 x 30 km` resource map；
  - `100 m` synthetic grid，`grid_shape=[300, 300]`；
  - scale-dependent active footprint；
  - benchmark fleet / horizon rule；
  - `B_use=100.0`、`Q_ice=6.0`、`max_tasks_per_trip=6`；
  - scale-dependent `max_shadow_exposure_per_sortie`；
  - reference sortie 不得超过 shadow / energy / capacity / horizon 约束。
- `generate_lunar_ice_benchmark.py` 生成的 manifest 会同步记录 resource map、grid resolution、active footprint、fleet、horizon、`B_use` 和 shadow cap。
- 这保证“靠近现实”的 PSR/shadow 暴露约束不会只存在于文字计划中；如果后续 exact baseline 后调 `B_use` 或 shadow cap，需要同步修改 scenario constants 和重新生成 benchmark。

## 13. 验收标准

### 13.1 文件边界

- `BPC_future/` 未被修改。
- `GAT_BPC_moonTerk/src/lunar_ice_bpc/` 可以独立 import。
- 新目录不复制旧 reports/runbooks/probes/audits。
- 新目录没有通信字段进入运行代码、schema、config 或 GAT feature。

### 13.2 运行边界

- `scripts/run_lunar_ice_bpc.py` 可运行 5-task journey instance。
- 输出 CSV、JSONL log、solution JSON。
- 默认 master 是 `journey`。
- `trip_time` 只作为 smoke/ablation。
- `5 / 10 / 20` 规模单实例运行预算为 `600s`。
- `30 / 50 / 100` 规模单实例运行预算为 `3600s`。
- 批量 benchmark 默认 `max_workers=4`。

### 13.3 模型边界

- 每个 task exactly once。
- `operation_mode` 是 task 属性，不创建同一物理目标的 detect/drill/sample 三次服务链。
- 每个 journey 是一辆车的多 sortie schedule。
- 每个 sortie 是 depot -> PSR targets -> depot。
- 每条 logical edge 固定只有三条 path options：`low_time`、`low_energy`、`low_risk`。
- capacity、time window、energy、return recharge、horizon 都在 column feasibility 中检查。
- RMP 使用 journey cover、fleet limit、cuts、branch rows。

### 13.4 Exactness 边界

- GAT 不参与 official lower bound。
- GAT 不参与 no-negative certificate。
- GAT 不能永久丢弃 true-RC negative columns。
- learned dual / smoothed dual 只能用于 candidate generation。
- official certificate 仍由 true-dual exact pricing 给出。
- pricing coverage incomplete 时 fail closed。

### 13.5 Benchmark 验收

- 5 规模：`20/20` 在 `600s` 内 exact `OPTIMAL`，且 20 个实例平均最优解时间小于 `5s`。
- 10 规模：`20/20` 在 `600s` 内 exact `OPTIMAL`，且 20 个实例平均最优解时间小于 `10s`。
- 20 规模：`20/20` 在 `600s` 内 exact `OPTIMAL`，且 20 个实例平均最优解时间小于 `100s`。
- 30 规模：exact `OPTIMAL` 数量不少于 `15/20`，且已求最优实例的平均最优解时间小于 `250s`。
- 50 规模：benchmark run 必须能获得有效 gap，且 exact `OPTIMAL` 数量不少于 `3/20`。
- 100 规模：只做 scalable benchmark，不强求 exact closure；必须报告 incumbent、gap、pricing workload、node count 和 incomplete reason。

小规模 “平均最优解时间” 使用 benchmark CSV 中的 `exact_baseline_wall_time_sec` 字段；`wall_time_sec` 仍保留完整 runner 时间，包括 restricted RMP、direct pricing、direct CG 等诊断步骤。这样既保留诊断证据，又不把非必要诊断开销计入 exact baseline 目标。

### 13.6 通信删除边界

以下关键词不应出现在运行代码、schema、config、feature builder 中：

```text
comm
communication
blackout
link_margin
earth_visibility
relay_visibility
direct_to_earth
DTE
LOS_to_earth
LOS_to_base
```

例外：

- Markdown 文档可以出现这些词，因为是在说明“不实现”。

## 14. 最终一句话

新版 `GAT_BPC_moonTerk` 应重构为一个轻量但保留 journey master 的月表水冰探测 GAT+BPC 项目：固定一个永昼峰充电基地，PSR 水冰目标必须被服务一次，journey column 表示一辆月球车的多 sortie 多路径计划，exact journey BPC 给出官方下界和证书，GAT 只做 exact-safe guidance；第一版完全删除通信建模，只保留主要运行代码、最小自检和论文必要的轻量可视化。
