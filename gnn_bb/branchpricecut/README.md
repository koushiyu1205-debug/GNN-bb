# BranchPriceCut 新主线

更新时间：2026-05-13 22:12:30 CST +0800

本目录现在提供两个求解入口，默认主力是 **hybrid route-level exact BPC**：

```text
master_type = "hybrid_route"      # 主力 exact solver
master_type = "vehicle_schedule"  # 完整 schedule-column baseline / ng-DSSR 对照
```

hybrid 模式复用根目录 `bpc/` 的 route-vehicle master、单 sortie RCSP pricing、schedule checker 和 valid cuts，但统一由 `branchpricecut/scripts/run_vehicle_schedule_bpc.py` 调度，结果仍写入 `branchpricecut/results/`。

## 目录

```text
branchpricecut/
  config/default.json
  config/medium_hybrid_route.json
  docs/vehicle_schedule_bpc_model.md
  scripts/run_vehicle_schedule_bpc.py
  results/
  data.py
  columns.py
  pricing.py
  ng_dssr.py
  route_pool.py
  schedule_dp.py
  rmp.py
  branching.py
  tree.py
  solver.py
  logger.py
```

## 当前状态

已实现：

- hybrid route-vehicle master：`lambda[p,r]` 单 sortie route-vehicle 变量 + `y[r]` 车辆启用变量；
- hybrid exact route pricing：单 sortie RCSP，节点 bound 只在 route pricing exhausted 后用于证明；
- integer route assignment exact schedule checker；
- schedule no-good cuts、crossing cuts、schedule capacity cuts，并把 cut dual 纳入 route reduced cost；
- route-compatible branching：Ryan-Foster、task-vehicle、arc on/off、vehicle-use；
- 统一入口 `master_type` 调度，hybrid 结果写入 `branchpricecut/results/`；
- vehicle-schedule set-partitioning master baseline；
- Phase-I artificial cover；
- fleet constraint；
- partitioning / covering 可配置 master，其中 covering incumbent 会先做 duplicate removal + shortcut rebuild + exact feasibility check；
- vehicle lower-bound cut 及 schedule-level dual reduced-cost 一致性检查；
- Layer 0 schedule column pool scan；
- Layer 1 portfolio sortie route pool；
- Layer 2 heuristic route-to-schedule composition DP；
- Layer 3 ng-relaxed DSSR pricing certificate，full-memory exact 仅作为可配置 debug fallback；
- pricing-compatible Ryan-Foster branching；
- JSONL 日志；
- summary CSV 和 solution JSON 输出到 `branchpricecut/results/`。

暂未实现：

- 2LBB；
- dual stabilization；
- route-level compact MILP reformulation；
- compiled RCSP labeling / bidirectional route pricing。

## 2026-05-13 22:12:30 CST +0800 Hybrid route-level exact BPC

本轮把 `branchpricecut` 的默认主力 exact solver 从完整 schedule-column master 切到 hybrid route-level master：

- `config/default.json` 和 `config/medium_prove.json` 默认 `master_type="hybrid_route"`。
- 新增 `config/medium_hybrid_route.json`，用于 20 规模 route-level proof run。
- `solver.py` 增加 hybrid wrapper：把 `branchpricecut.data.InstanceData` 转成 `bpc.data.BPCData`，调用 `bpc.solver.solve_bpc_clean(...)`，再转换成统一 `SolverResult`。
- `scripts/run_vehicle_schedule_bpc.py` 按 `master_type` 调度；`hybrid_route` 与 `vehicle_schedule` 共用 `branchpricecut/results/<run_id>/` 输出目录。
- `bpc` 侧补充 summary 字段 `branch_nodes`、`label_pops`、`generated_labels`，solution JSON 中增加每辆车 `schedule_checks`，记录 checker 可行性和 route 执行顺序。
- 保留完整 schedule-column/ng-DSSR 路径：配置中显式设置 `master_type="vehicle_schedule"` 即可继续跑 baseline。

hybrid exactness 边界：

- RMP column 是单 sortie route，不是完整 schedule。
- 节点 lower bound 来自 route-level exact pricing exhausted 后的 route-vehicle LP。
- 整数解必须通过 exact schedule checker；不可排程 route 集会生成 valid schedule no-good cuts 后重新求解。
- no-good、crossing、schedule-capacity cut dual 都进入 route pricing reduced cost。
- greedy / repair incumbent 只作为 primal upper bound，不参与 lower-bound 证明。

本轮验证：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile branchpricecut/*.py branchpricecut/scripts/run_vehicle_schedule_bpc.py bpc/*.py tests/test_branchpricecut_vehicle_schedule.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean tests.test_branchpricecut_vehicle_schedule
Ran 32 tests in 0.280s
OK
```

`very_small` hybrid smoke：

```text
run_id=smoke_20260513_hybrid_route_very_small
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
nodes=1
rmp_solves=4
pricing_calls=3
label_pops=102
generated_labels=96
```

`medium` guard smoke 使用临时配置 `hybrid_max_labels_per_pricing=1000`：

```text
run_id=smoke_20260513_hybrid_route_medium_guard
status=PRICING_INCOMPLETE
nodes=1
rmp_solves=6
pricing_calls=5
label_pops=5000
generated_labels=5772
dual_bound=None
```

该 smoke 只验证中断边界：pricing 未 exhausted 时不输出证明 bound。

## 2026-05-13 16:26:46 CST +0800 revise_plan 落地内容

本轮按 `docs/revise_plan.md` 对代码做了实际修改，核心路径如下：

- `rmp.py`：新增 `master_cover_mode`、vehicle LB row、manual-vs-solver reduced cost audit，以及 `check_schedule_reduced_cost_consistency`。
- `tree.py`：Phase-I artificial sum 为 0 后直接切 Phase-II 并重新求 RMP；只有 Layer 3 exact fallback exhausted 后才认证节点；新增 covering incumbent 后处理；扩展 JSONL/CSV 统计。
- `route_pool.py`：实现 Layer 1 portfolio route generation，包含 low-cbar、per-task、route-size bucket、time-flexible、micro、branch-relevant、historical、diverse buckets，并在 component 层过滤 `separate`。
- `schedule_dp.py`：实现 Layer 2 heuristic schedule DP，包含 component-level branch state、subset dominance、beam pruning、top-K negative schedule 输出、相同 task-set 去重、Jaccard 相似度限制，以及负列候选达到 `max_negative_schedules_per_pricing` 后的 opportunistic early-stop。
- `pricing.py`：该阶段保留 integrated exact schedule-labeling 作为 Layer 3 certificate fallback；`DSSRSchedulePricing` 进入 full-memory exact mode，启用 exact-safe label dominance，并预留后续 relaxed-memory DSSR 迭代。
- `tests/test_branchpricecut_vehicle_schedule.py`：按 `revise_plan.md` R 节拆成 10 个 unittest，覆盖 reduced cost、Phase-I/II、vehicle LB dual、Layer 1/2、partitioning/covering、tiny enumeration 和 RF branching 分类。

精确性边界：

- Layer 0/1/2 只用于找 negative reduced-cost schedule columns，不能证明 no negative column。
- 该阶段节点 lower bound 只在 Layer 3 integrated exact fallback exhausted 且 `certificate=true` 后使用。
- 若 exact pricing 触发 label/time/queue/candidate limit 且没有 exhausted，状态保持 `PRICING_LIMIT`，不会认证节点。
- RF branching 当前通过 column filtering 和 pricing feasibility enforce；不是 RMP dual row。
- covering 是 experimental mode；post-processing 会先检查 triangle/shortcut 非增和服务成本非负，再做 duplicate removal、shortcut rebuild 和 exact feasibility check；失败的整数解不会作为 incumbent。

## 2026-05-13 16:55:57 CST +0800 部分落地项补齐

补齐项：

- Phase-I RMP objective 为 0 后不再运行 Phase-I pricing，直接切到 Phase-II、重新 solve RMP、提取 Phase-II true dual。
- `exact_pricing_required_for_certificate` 现在被真实读取；默认 `true` 时，未调用 exact fallback 不能认证节点。
- `schedule_dp_max_seconds` 现在作为 Layer 2 DP 独立时间上限参与 `min(schedule_dp_max_seconds, max_pricing_seconds, remaining_time)`。
- `schedule_dp_early_stop_on_full_batch` 默认开启；Layer 2 找到足够一批负 reduced-cost schedules 后会提前返回，并把 `schedule_dp_exhausted=false`，不参与节点认证。
- Layer 0 pool scan 改成按当前节点 RMP column signature 判断，而不是只按全局 active set。
- Layer 1 `diverse_routes` 改成按 covered task set、route length、time cluster 组合筛选。
- Layer 2 top-K negative schedules 增加相同 covered task set 去重和 Jaccard 相似度限制。
- `summary.csv` 新增 `master_cover_mode` 字段。
- DSSR/ng-schedule 预留接口补成 `DSSRSchedulePricing`，该阶段使用 full-memory exact pricing + dominance，后续可接 relaxed-memory DSSR。

## 2026-05-13 17:29:43 CST +0800 文档一致性补齐

本轮把除以下三项外的文档不一致点继续落到代码：

- `PricingResult` 新增 `certificate` 字段；`DSSRSchedulePricing.run(...)` 现在返回带 certificate 的 `PricingResult`。
- Layer 3 认证显式要求 `result.certificate=true`；如果 exact layer 找到负列但没有成功加入 RMP，不再认证节点。
- `historical_useful_routes` 改成只记录由 negative pricing/pool scan 加入的 useful route，不再把初始列和 greedy incumbent 自动作为 historical useful routes。
- `time_flexible_routes` 改成按 duration/ready time 与任务 deadline slack 排序。
- `branch_relevant_routes` 在存在 same component 时优先保留与 same component 相关的 routes。
- JSONL 增加与 `revise_plan.md` 更一致的字段别名，例如 `pool_scan_columns_found`、`schedule_dp_labels_created`、`exact_pricing_called`。

## 2026-05-13 17:37:37 CST +0800 测试补齐

`tests/test_branchpricecut_vehicle_schedule.py` 现在按 `docs/revise_plan.md` R 节组织为 10 个测试：

1. reduced-cost consistency；
2. Phase-I to Phase-II dual transition；
3. vehicle lower-bound dual sign consistency；
4. Layer 1 separate filtering；
5. Layer 1 portfolio buckets；
6. Layer 2 subset dominance；
7. Layer 2 beam pruning triggers Layer 3；
8. partitioning / covering post-processing；
9. tiny full enumeration vs CG LP；
10. schedule-level Ryan-Foster branching coverage classification。

当时按你的要求，这三项在完整 schedule-column baseline 中仍不改；新的 hybrid route-level 主线已启用 route-compatible branching：

- arc-on / arc-off / route-level branching；
- `check_schedule_reduced_cost_consistency(phase, num_samples=20)` 的文档签名；
- branching coverage 测试里的 column-level `intersection empty` 表述。

## 运行 very_small

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_very_small_vehicle_schedule"

/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
  --config branchpricecut/config/default.json \
  --instances very_small \
  --time-limit 300 \
  --run-id "$RUN_ID"
```

输出：

```text
branchpricecut/results/${RUN_ID}/summary.csv
branchpricecut/results/${RUN_ID}/logs/very_small.jsonl
branchpricecut/results/${RUN_ID}/solutions/solution_very_small.json
```

## 运行 20 规模

默认 20 规模证明使用 hybrid route-level exact BPC。若要回到完整 schedule-column/ng-DSSR baseline，需要把配置中的 `master_type` 改为 `"vehicle_schedule"`。

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_medium_hybrid_route"

/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
  --config branchpricecut/config/medium_hybrid_route.json \
  --instances medium \
  --time-limit 3600 \
  --run-id "$RUN_ID" \
  2>&1 | tee "branchpricecut/results/${RUN_ID}_terminal.log"
```

## 严肃 Benchmark

固定 benchmark 配置：

```text
branchpricecut/config/benchmark_10_20_30.json
```

该配置生成并固定 30 个实例：

```text
size=10: bench_10_01 ... bench_10_10
size=20: bench_20_01 ... bench_20_10
size=30: bench_30_01 ... bench_30_10
```

默认运行 3 个核心 variant：

```text
bpc_clean_full
hybrid_full
vehicle_schedule_ng_dssr
```

选择逻辑：

- `hybrid_full`：当前主模型；
- `bpc_clean_full`：旧 route-level BPC 核心对照；
- `vehicle_schedule_ng_dssr`：完整 schedule-column/ng-DSSR baseline，对比数学更自然但 pricing 更重的路线。

总计 90 个 job。每个 job 独立 worker 进程运行，完成后立即写：

```text
branchpricecut/results/benchmark/<RUN_ID>/job_results/<job_id>.json
branchpricecut/results/benchmark/<RUN_ID>/summary.csv
branchpricecut/results/benchmark/<RUN_ID>/aggregate.csv
```

断点续跑规则：重复使用同一个 `RUN_ID` 运行同一命令，会自动跳过已完成 job，继续未完成或中断的 job。`summary.csv` 和 `aggregate.csv` 每个 job 结束后都会重建。

一次性正式命令：

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_benchmark_10_20_30"
mkdir -p branchpricecut/results/benchmark

/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_benchmark.py \
  --config branchpricecut/config/benchmark_10_20_30.json \
  --run-id "$RUN_ID" \
  2>&1 | tee "branchpricecut/results/benchmark/${RUN_ID}_driver.log"
```

如果中断，使用同一个 `RUN_ID` 续跑：

```bash
cd /home/kai/work/gnn_bb
mkdir -p branchpricecut/results/benchmark
/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_benchmark.py \
  --config branchpricecut/config/benchmark_10_20_30.json \
  --run-id "$RUN_ID" \
  2>&1 | tee -a "branchpricecut/results/benchmark/${RUN_ID}_driver.log"
```

## 数学模型

详见：

```text
branchpricecut/docs/vehicle_schedule_bpc_model.md
```

## 2026-05-13 11:31:12 CST +0800 验证记录

编译检查：

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
  branchpricecut/*.py \
  branchpricecut/scripts/run_vehicle_schedule_bpc.py
```

`very_small` smoke：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
  --instances very_small \
  --time-limit 60 \
  --max-nodes 100 \
  --run-id smoke_20260513_113112_vehicle_schedule
```

结果：

```text
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
nodes=1
rmp_solves=4
pricing_calls=4
generated_columns=47
label_pops=440
```

输出位置：

```text
branchpricecut/results/smoke_20260513_113112_vehicle_schedule/summary.csv
branchpricecut/results/smoke_20260513_113112_vehicle_schedule/logs/very_small.jsonl
branchpricecut/results/smoke_20260513_113112_vehicle_schedule/solutions/solution_very_small.json
```

## 2026-05-13 11:41:59 CST +0800 Pricing 保护

### 问题

20 规模在根节点 Phase-I pricing 会出现 label 数量快速增长。第一版默认：

```text
max_labels_per_pricing = 0
```

表示无限 exact pricing，因此存在卡在根节点并撑爆内存的风险。

### 修改

新增 pricing 保护：

```text
max_labels_per_pricing
max_generated_labels_per_pricing
max_queue_size_per_pricing
max_candidate_pool_per_pricing
max_pricing_seconds
```

默认配置：

```json
{
  "max_labels_per_pricing": 200000,
  "max_generated_labels_per_pricing": 0,
  "max_queue_size_per_pricing": 100000,
  "max_candidate_pool_per_pricing": 5000,
  "max_pricing_seconds": 60,
  "max_pricing_memory_mb": 8192,
  "pricing_memory_check_interval": 4096,
  "exact_pricing_enable_dominance": true
}
```

20 规模证明冲刺配置：

```text
branchpricecut/config/medium_prove.json
```

该配置不再使用 fixed generated-label 硬截断：`max_generated_labels_per_pricing=0`。它把 `max_queue_size_per_pricing` 提高到 `1000000`，设置 `max_pricing_memory_mb=8192`，并默认使用 `ng_dssr` certificate；若 ng-DSSR 因 label、queue、memory 或 time guard 未 exhausted，结果仍会是 `PRICING_LIMIT`，不会认证节点。

### 精确性边界

这些保护只防止 Python pricing 无限占用内存和时间。只要任一保护触发：

```text
exhausted = false
status = PRICING_LIMIT
```

该节点不会被认为 full priced，也不会用当前 RMP bound 证明最优。

### 5 秒 medium 保护测试

命令：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
  --instances medium \
  --time-limit 5 \
  --max-nodes 10 \
  --run-id smoke_20260513_114126_medium_guard_5s
```

结果：

```text
status=PRICING_LIMIT
labels=200000
generated_labels=200079
queue_peak=106
stop_reason=label_pop_limit
```

这说明保护生效：pricing 没有卡死根节点，且因为未 exhausted，没有错误使用 lower bound。

## 2026-05-13 17:29:43 CST +0800 验证记录

编译检查：

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
  branchpricecut/*.py \
  branchpricecut/scripts/run_vehicle_schedule_bpc.py
```

新增 unittest：

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
```

结果：

```text
Ran 10 tests
OK
```

`very_small` smoke：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
  --instances very_small \
  --time-limit 60 \
  --max-nodes 100 \
  --run-id smoke_20260513_171500_doc_alignment \
  --quiet
```

结果：

```text
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
nodes=1
rmp_solves=4
pricing_calls=1
generated_columns=5
label_pops=110
generated_labels=109
phase_switch_count=1
manual_rc_check_max_error=0.0
exact_pricing_called=1
exact_pricing_exhausted=1
pricing_certificate_layer=integrated_exact_fallback
```

输出位置：

```text
branchpricecut/results/smoke_20260513_171500_doc_alignment/summary.csv
branchpricecut/results/smoke_20260513_171500_doc_alignment/logs/very_small.jsonl
branchpricecut/results/smoke_20260513_171500_doc_alignment/solutions/solution_very_small.json
```

## 2026-05-13 19:08:36 CST +0800 DSSR full-memory exact 与内存保护调整

本轮开始把 Layer 3 往 DSSR 方向推进：

- `DSSRSchedulePricing` 不再只是空壳委托；该阶段第一版使用 full-memory elementary exact pricing，启用 exact-safe label dominance。
- exact pricing label 增加 `total_cost`，dominance 在相同 covered set、当前 sortie task 集合、当前节点和已完成 sortie 数一致时，按 ready/current time、load、energy、current cost、total cost 剪掉资源更差标签。
- `max_generated_labels_per_pricing=0` 表示不再使用 generated-label 硬截断 proof run；当前保护改为 queue、time、RSS memory guard。
- 新增配置：`max_pricing_memory_mb`、`pricing_memory_check_interval`、`exact_pricing_enable_dominance`。
- JSONL exact pricing event 增加 `algorithm`、`labels_pruned_by_dominance`、`memory_peak_mb`。

验证：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile branchpricecut/*.py branchpricecut/scripts/run_vehicle_schedule_bpc.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
Ran 10 tests in 0.131s
OK
```

`very_small` smoke：

```text
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
exact_pricing: algorithm=dssr_full_memory_exact
labels_pruned_by_dominance=6
memory_peak_mb=70.93
```

## 2026-05-13 19:35:39 CST +0800 memory guard、exact dominance 与 heuristic 退化检测

本轮继续围绕 20 规模 proof run 的瓶颈做三处真实代码调整：

- `pricing.py` 的 RSS guard 改为 Linux 下读取 `/proc/self/statm` 当前 RSS，并只把采样值累计成 `memory_peak_mb`；fallback 才使用 `resource.getrusage`，避免 Linux `ru_maxrss` 单位误判，也避免历史峰值导致后续 pricing 被错误截停。
- Layer 3 exact dominance 加强：dominance key 从“当前 route task 顺序”放宽到“当前 route task set”，同时把 `current_cost` 加入资源劣势比较。这个 dominance 仍保持 elementary full-memory exact，不是 relaxed-memory DSSR。
- `tree.py` 增加 node 内 heuristic 退化检测：当 Layer 1/2 加列后 RMP objective 连续 `heuristic_degradation_max_stagnant_rounds` 次改善不超过 `heuristic_degradation_min_obj_improvement`，后续该节点跳过 Layer 1/2，直接进入 Layer 3 exact pricing。
- `summary.csv` 新增 `heuristic_degradation_skips`；JSONL 新增 `heuristic_degradation` event。
- `default.json` 和 `medium_prove.json` 新增配置：`heuristic_degradation_detection_enabled`、`heuristic_degradation_max_stagnant_rounds`、`heuristic_degradation_min_obj_improvement`。

验证结果已保存到：

```text
tests/branchpricecut_vehicle_schedule_test_results_20260513_memory_guard_dominance_heuristic.txt
```

验证命令：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile branchpricecut/*.py branchpricecut/scripts/run_vehicle_schedule_bpc.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
Ran 10 tests in 0.118s
OK
```

`very_small` smoke 同步通过，用于确认新增 `summary.csv` 字段可写：

```text
run_id=smoke_20260513_193539_memory_guard_dominance_heuristic
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
labels=83
generated_labels=82
queue_peak=10
```

## 2026-05-13 19:46:19 CST +0800 Phase-II heuristic 退化检测与 exact heartbeat

针对 20 规模 run 卡在 root `phase1 cg=8` 后直接进入 full-memory exact 的问题，本轮调整：

- `heuristic_degradation` 只在 `phase2` 生效；`phase1` artificial objective 未清零时，不再因为 heuristic 加列后 objective 停滞而跳过 Layer 1/2。
- Layer 3 exact pricing 增加 `exact_pricing_progress` JSONL heartbeat，默认每 30 秒或每 500000 个 popped labels 写一次，字段包含 labels、generated labels、queue size/peak、candidate count、best_rc、dominance prune 和 RSS memory。
- 新增配置：`exact_pricing_progress_interval_seconds`、`exact_pricing_progress_label_interval`。

验证结果已保存到：

```text
tests/branchpricecut_vehicle_schedule_test_results_20260513_phase2_degradation_progress.txt
```

验证命令：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile branchpricecut/*.py branchpricecut/scripts/run_vehicle_schedule_bpc.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
Ran 10 tests in 0.121s
OK
```

`very_small` smoke：

```text
run_id=smoke_20260513_heuristic_phase2_progress
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
labels=83
generated_labels=82
queue_peak=10
```

## 2026-05-13 21:07:02 CST +0800 degradation reset、restricted integer master 与 relaxed-memory DSSR

本轮按 20 规模运行暴露的问题继续落地三项：

- `tree.py`：Layer 3 exact pricing 找到并加入负列后，重置 node 内 `heuristic_degradation` 状态；下一轮会重新尝试 Layer 1/2，避免同一节点里连续昂贵 exact。
- `rmp.py`：新增 `solve_restricted_master_integer(...)`，在当前 schedule pool 上解 binary restricted master，支持 partitioning/covering、vehicle upper bound、vehicle lower-bound cut 和 RF branch filtering。
- `tree.py`：新增 restricted master incumbent 更新路径，默认在 Phase-II 每 10 个 CG 轮次、exact 添加列后、节点认证后尝试一次；成功时写 `restricted_master_integer` 与 `incumbent` 日志。
- `pricing.py`：`DSSRSchedulePricing` 增加 relaxed-memory DSSR 迭代。该层从小 memory set 开始，允许非 memory task 重访；遇到 negative non-elementary schedule 会扩大 memory；遇到 elementary negative schedule 会直接返回列。
- 精确性边界：该阶段 relaxed-memory DSSR 主要用于更快找 negative elementary columns；节点 no-negative certificate 仍由 full-memory exact fallback 或 full-memory memory state 给出。
- `summary.csv` 新增 restricted master 字段：`restricted_master_integer_calls`、`restricted_master_integer_feasible`、`restricted_master_integer_time`、`restricted_master_integer_best_objective`。
- `exact_pricing` JSONL event 新增 DSSR 字段：`dssr_iterations`、`dssr_memory_size`、`dssr_non_elementary_negative`。
- 新增配置：`dssr_relaxed_memory_enabled`、`dssr_initial_memory_size`、`dssr_max_iterations`、`dssr_memory_growth`、`dssr_relaxed_iteration_seconds`、`dssr_relaxed_max_labels`、`restricted_master_integer_enabled`、`restricted_master_integer_time_limit`、`restricted_master_integer_cg_interval`、`restricted_master_integer_after_exact_added`。

验证结果已保存到：

```text
tests/branchpricecut_vehicle_schedule_test_results_20260513_dssr_integer_master_reset.txt
```

验证命令：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile branchpricecut/*.py branchpricecut/scripts/run_vehicle_schedule_bpc.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
Ran 10 tests in 0.154s
OK
```

`very_small` smoke：

```text
run_id=smoke_20260513_dssr_integer_master_reset
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
restricted_master_integer_feasible=1
restricted_master_integer_best_objective=132.270984
pricing_certificate_layer=dssr_full_memory_exact
```

## 2026-05-13 21:43:49 CST +0800 真正 ng-DSSR Layer 3

本轮把 Layer 3 从“relaxed-memory 找列 + full-memory exact 证明”改成默认 `ng_dssr`：

- 新增 `ng_dssr.py`：实现 ng-neighborhood、ng-relaxed schedule labeling、DSSR memory growth、negative non-elementary schedule 触发 memory 扩张，以及 relaxed exhaustive no-negative certificate。
- `pricing.py`：`DSSRSchedulePricing` 外部接口保持不变，默认 `exact_pricing_algorithm="ng_dssr"`；`full_memory_fallback_enabled=false` 时不再回 full-memory exact。
- `tree.py`：exact pricing 日志增加 `ng_size`、`non_elementary_negative_count`、`certificate_from_relaxation`、`full_memory_fallback_called`；summary 同步增加 ng-DSSR 汇总字段。
- `branching.py/tree.py` 路径保持 schedule-level RF branching；pricing label 的 dominance key 纳入当前 sortie task set、ng memory、DSSR memory 和 same-component branch state，`separate` 继续早剪枝，`same` 继续 final all-or-none 检查。
- `config/default.json` 与 `config/medium_prove.json` 新增：`exact_pricing_algorithm`、`full_memory_fallback_enabled`、`ng_neighborhood_size`、`ng_include_time_compatible`、`ng_include_branch_components`、`dssr_certificate_without_full_memory`。
- `tests/test_branchpricecut_vehicle_schedule.py` 从 10 个测试扩展到 17 个测试，新增 ng-DSSR tiny LP 对齐、memory growth、elementary negative 返回、relaxed certificate、limit no-certificate、dominance key 和 branch constraint 覆盖。

验证：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile branchpricecut/*.py branchpricecut/scripts/run_vehicle_schedule_bpc.py tests/test_branchpricecut_vehicle_schedule.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
Ran 17 tests in 0.173s
OK
```

`very_small` smoke：

```text
run_id=smoke_20260513_ng_dssr_branch_state
status=OPTIMAL
primal_bound=132.270984
dual_bound=132.270984
gap=0.0
pricing_certificate_layer=ng_dssr
dssr_certificate_from_relaxation=1
full_memory_fallback_called=0
```
