# BranchPriceCut 新主线

更新时间：2026-05-13 10:52:35 CST +0800

本目录是独立于根目录 `bpc/` 的新实现。目标是构建更接近 You et al. / RouteOpt 思路的 vehicle-schedule Branch-Price-and-Cut：

```text
column = 一辆车完整多 sortie schedule
```

## 目录

```text
branchpricecut/
  config/default.json
  docs/vehicle_schedule_bpc_model.md
  scripts/run_vehicle_schedule_bpc.py
  results/
  data.py
  columns.py
  pricing.py
  rmp.py
  branching.py
  tree.py
  solver.py
  logger.py
```

## 当前状态

已实现：

- vehicle-schedule set-partitioning master；
- Phase-I artificial cover；
- fleet constraint；
- integrated schedule-labeling pricing；
- pricing-compatible Ryan-Foster branching；
- JSONL 日志；
- summary CSV 和 solution JSON 输出到 `branchpricecut/results/`。

暂未实现：

- 3PB 完整三阶段测试；
- 2LBB；
- cuts；
- dual stabilization；
- ng-route / bucket / bidirectional labeling 等工程加速。

## 运行 very_small

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_very_small_vehicle_schedule"

/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
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

注意：这是未加速的 exact schedule-labeling pricing，20 规模可能很慢。若设置 `max_labels_per_pricing > 0`，pricing 未 exhausted 时不能证明最优。

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_medium_vehicle_schedule"

/home/kai/miniconda3/envs/ecole/bin/python branchpricecut/scripts/run_vehicle_schedule_bpc.py \
  --instances medium \
  --time-limit 3600 \
  --run-id "$RUN_ID" \
  2>&1 | tee "branchpricecut/results/${RUN_ID}_terminal.log"
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
  "max_generated_labels_per_pricing": 300000,
  "max_queue_size_per_pricing": 100000,
  "max_candidate_pool_per_pricing": 5000,
  "max_pricing_seconds": 60
}
```

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
