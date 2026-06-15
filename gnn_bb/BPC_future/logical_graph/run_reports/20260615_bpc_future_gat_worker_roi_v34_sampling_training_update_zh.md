# GAT Worker ROI v34 采样与训练更新报告

日期：2026-06-15

## 目标

本轮继续推进 `GAT = trajectory ROI predictor` 主线。

核心标签语义保持不变：

- 正标签不是 `rc < 0`；
- 正标签不是 same-run proxy；
- 正标签不是 GAT/OOD 通过；
- 正标签只能来自 paired baseline vs worker A/B 后观察到的 trajectory ROI；
- GAT 只做优先级排序，不能证书，不能永久丢弃负列。

## 本轮新增采样

### v33

- 推荐候选：17 条；
- 内部重复：0；
- 与 v32 已有 ROI key 重叠：0；
- A/B 命令：36 个；
- 5/10 sentinel：通过，均为 `OPTIMAL`；
- 20-task A/B：全部完成，失败 0。

v33 审计结果：

- record_count = 17；
- positive_trajectory_roi_count = 3；
- negative_trajectory_roi_count = 11；
- no_observed_roi_count = 2；
- columns_only_roi = 1；
- certificate / official bound effect = false。

### v34

- 推荐候选：24 条；
- 内部重复：0；
- 与 v33 合并 ROI key 重叠：0；
- A/B 命令：50 个；
- 5/10 sentinel：通过，均为 `OPTIMAL`；
- 20-task A/B：全部完成，失败 0；
- 并行度：4；
- 内存：available 约 11-12GiB，未出现内存压力。

v34 审计结果：

- record_count = 24；
- positive_trajectory_roi_count = 2；
- negative_trajectory_roi_count = 14；
- no_observed_roi_count = 5；
- columns_only_roi = 3；
- certificate / official bound effect = false。

## 当前合并数据集

路径：

```text
BPC_future/results/gat_worker_roi_dataset_v34_after_v33_sampling_20260615
BPC_future/data/gat_worker_roi/v34_after_v33_sampling_20260615
```

统计：

- row_count = 229；
- training_row_count = 197；
- positive_trajectory_roi_count = 61；
- training positive = 60；
- training negative = 137；
- duplicate_candidate_count = 0；
- family 覆盖：greedy-anchor / random-wave / sector-wave；
- region 覆盖：Apollo / Tranquillitatis；
- 当前仍主要是 20-task ROI 标签。

这已经达到“总样本 150-200+、正样本 50+”的最低训练门槛，但距离更稳的正样本 80+ 仍有缺口。

## GAT 训练结果

v34 裸 GAT：

- validation add recall = 0.941；
- validation add precision = 0.381；
- validation add F1 = 0.542；
- false positive 仍偏多。

解释：

裸 GAT 已能覆盖大部分正 ROI，但会把大量无效/负 ROI 也推成 add。因此不能直接用于生产 worker。

## kNN/OOD 安全壳

strict shell：

- predicted_high_priority = 5；
- add precision = 0.800；
- add recall = 0.235；
- false high priority rate = 0.028；
- production_ready = false。

放宽 `max_neighbor_delay_fraction` 网格：

| max_neighbor_delay_fraction | high priority | precision | recall | false HP rate |
|---:|---:|---:|---:|---:|
| 0.0 | 5 | 0.800 | 0.235 | 0.028 |
| 0.2 | 5 | 0.800 | 0.235 | 0.028 |
| 0.33 | 5 | 0.800 | 0.235 | 0.028 |
| 0.5 | 18 | 0.278 | 0.294 | 0.361 |
| 0.67 | 33 | 0.424 | 0.824 | 0.528 |
| 0.8 | 33 | 0.424 | 0.824 | 0.528 |
| 1.0 | 42 | 0.381 | 0.941 | 0.722 |

结论：

- strict shell 很安全，但 recall 太低；
- 放宽 shell 可提高 recall，但误报率迅速失控；
- 主要瓶颈不是 shell 参数，而是 embedding / 样本分布仍未把正负 ROI 清楚分开。

## 关键判断

本轮 v34 继续证明：

1. same-run candidate 不能当最终标签；
2. paired worker A/B ROI 标签没有重复；
3. 5/10 sentinel 没有退化；
4. 20-task 采样并行 4 在当前机器内存安全；
5. 新增样本提升了 strict shell precision，但 recall 仍不足；
6. 简单按 family positive gap 采样效率不高，v34 正样本率只有 2/24。

## 下一步建议

不要继续盲目放宽 kNN/OOD，也不要默认启用 worker。

下一步应该改采样策略：

1. 采 `strict shell false-negative` 附近的候选，重点补“模型错放进 DELAY_QUEUE 的真正正 ROI”；
2. 采与历史 `positive_primal_roi` 在 embedding / sequence / context 上相近的候选；
3. 减少单纯按 random-wave positive_gap 的盲采；
4. 继续保留 paired A/B 标签语义；
5. 正样本目标继续推到 80+；
6. 仍然只做 audit-only，不接 official certificate。

## 验证

单元测试：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_worker_roi_dataset \
BPC_future.tests.test_gat_target_priority_worker_ab_runbook \
BPC_future.tests.test_gat_worker_roi_solver_ab_runbook
```

结果：

```text
Ran 16 tests in 0.025s
OK
```

