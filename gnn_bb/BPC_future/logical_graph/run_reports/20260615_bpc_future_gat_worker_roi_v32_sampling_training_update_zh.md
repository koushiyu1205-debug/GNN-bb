# GAT Worker ROI v32 采样与训练更新

日期：2026-06-15

## 核心校正

本轮确认：`v31_source_recovered` 中的 `51` 个正样本不是普通 source/add 弱标签，而是 paired worker A/B trajectory ROI 标签。它们应计入真实 ROI 标签池。

严格去重后：

- v31 标签池：180 个唯一候选；
- 可训练样本：156；
- 正 ROI：51；
- 负 ROI：105；
- unsupported / 不训练：24；
- 三份 solver A/B runbook 的 49 个候选全部已包含在 v31 中，不能重复相加。

## 去重修复

修复 `build_gat_worker_roi_solver_ab_runbook.py`：

- 同时识别 `roi_candidate_key`、`candidate_unique_key`、结构化 instance/context/sequence/arc key；
- 支持 `--exclude-candidate-jsonl`，可直接排除已有 ROI 标签池；
- 防止旧 summary 无显式 key、新 decision row 有显式 key 时重复采样。

相关 focused tests 已通过。

## 新增真实 A/B 标签

从 `gat_worker_roi_sampling_priority_v28_after_delay_positive_mining_20260615` 中筛出 v31 未覆盖的 8 个 random-wave 候选，并运行 paired baseline vs target-priority worker A/B。

运行边界：

- 5/10 no-regression sentinel 均为 `OPTIMAL`；
- 20-scale A/B 并行 4；
- 无命令失败；
- 无 certificate / official lower-bound effect；
- 内存稳定，运行中可用内存约 11GiB，结束后约 12GiB。

审计结果：

- 新增记录：8；
- 正 ROI：4；
- 负 ROI：2；
- no-observed：2；
- ROI class：`positive_primal_roi=2`、`positive_retry_roi=2`、`negative_primal_roi=1`、`negative_retry_roi=1`、`no_observed_roi=2`。

## v32 标签池

合并 v31 + 新增 random-wave A/B 后：

- 总唯一候选：188；
- 可训练样本：164；
- 正 ROI：55；
- 负 ROI：109；
- random-wave 正样本：从 2 增至 6；
- 仍全部为 20 规模样本。

## v32 GAT 训练与 kNN/OOD

v32 graph dataset：

- `sample_count=164`
- `add=55`
- `abstain=109`

v32 GAT 裸模型：

- validation add recall = 1.0；
- validation add precision = 0.382；
- 说明裸 GAT 仍偏激进，不能直接用作 worker gate。

v32 kNN/OOD 小网格：

- 严格 `max_neighbor_delay_fraction=0.0`：validation add recall = 0；
- `max_neighbor_delay_fraction=0.5`：validation precision = 0.40，recall = 0.308，可过当前 readiness；
- `max_neighbor_delay_fraction=0.8/1.0`：recall 高但 false high-priority 过高。

与 v31 相比，v32 覆盖更好，但当前 kNN/OOD 指标没有稳定优于 v31。因此 v32 仍是 audit-only，不应默认启用。

## 当前判断

这轮不是重新定义标签，也不是重新采同一批样本，而是在保持 ROI 标签语义不变的前提下：

1. 修正真实标签池统计；
2. 修复去重；
3. 补充 v31 未覆盖 random-wave 样本；
4. 重训 v32；
5. 验证 v32 尚不具备 production gate 条件。

下一步应继续补正 ROI，优先补：

- random-wave；
- 30/50/100 或更大规模，但需要先补配置/捕获路径，不能直接把 20 配置硬套成 production 结论。

