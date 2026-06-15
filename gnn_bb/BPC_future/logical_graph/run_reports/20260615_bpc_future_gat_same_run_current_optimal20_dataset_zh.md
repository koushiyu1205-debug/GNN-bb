# GAT Same-Run Batch Impact Dataset 报告

日期：2026-06-15

## 目的

本报告从同一次求解日志中配对 capture、column addition 和下一轮 RMP，
构造不会发生 context replay drift 的 GAT batch-impact 标签。
它不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_same_run_batch_impact_dataset = current
status = no_rows
source_file_count = 1
row_count = 0
positive_objective_improvement_count = 0
non_improving_objective_count = 0
objective_positive_rate = 0.0
objective_non_improving_rate = 0.0
active_support_changing_count = 0
new_task_set_added_count = 0
instance_count = 0
instance_region_count = 0
instance_regions = []
pricing_kinds = []
label_distribution_ready = false
training_blockers = ['need_more_same_run_rows', 'need_more_positive_objective_rows', 'need_more_non_improving_objective_rows', 'need_more_instances', 'need_more_regions']
non_improving_rows_needed_for_training = 10
objective_label_by_region = {}
addition_productivity_class_counts = {}
skipped_counts = {'missing_matching_column_addition': 1}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
training_ready = false
all_checks_pass = false
```

## 样例

```json
[]
```

## 结论

- 这类样本比 offline replay 更干净，因为 target/context/加列/下一轮 RMP 都来自同一次运行；
- 只有 `training_ready=true` 才允许进入 GAT 训练；当前若为 false，说明样本量、正负标签或实例/family 分布不足；
- 如果 `need_more_non_improving_objective_rows` 存在，说明当前 exact add-column 样本天然偏向改善动作，需要继续采 hard-tail 中加列但 RMP 不动或弱动的同一上下文对照；
- 该数据只允许做离线 GAT trajectory-impact 监督，不能参与 pricing certificate。
