# P0V5 QG2 V3 GAT-first 实验状态

> 本文件由 `scripts/update_p0v5_qg2_v3_status.py` 从持久化 artifact 重建；性能数字不是部署授权。

## 当前结论

- P0V4+V5 Exact control 未修改；Q0 始终是全部 arm 被拒绝后的唯一回退。
- label-state GAT arm（QG2）已因固定 force-on screen 全面退化而 hard-veto。
- 当前有效学习问题是 context-level selector 在 Q0/QD1/QB1 间选择；其收益不能归因于 QG2 label ordering。
- GAT 已按约定第一个训练并第一个完成 heldout fresh-process 三重复；MLP/Linear 只作为结构对照。

## Admission ranker

- contexts：`110`；模型：`GAT-first`。
- ranker report：`runs/p0v5_qg2_v3_gat_first_20260806/training_rankers/training_report.json`。

### QG2 force-on

- context：4；beneficial：0；adverse：4；GM：1.325996。

## Context selector 离线对照

| 模型 | train/cal/heldout | heldout 激活 | beneficial | harmful | heldout GM | scale30 GM | scale50 GM |
|---|---:|---:|---:|---:|---:|---:|---:|
| GAT | 66/22/22 | 6 | 4 | 2 | 0.779801 | 0.978111 | 0.645626 |
| MLP | 66/22/22 | 8 | 5 | 3 | 0.782409 | 0.981286 | 0.647836 |
| Linear | 66/22/22 | 16 | 14 | 2 | 0.368734 | 0.845817 | 0.184605 |

## Fresh-process heldout

| 模型 | 当前进度 | 激活 | beneficial | harmful | GM | scale30 GM | scale50 GM | safety |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GAT | 22/22 | 4 | 4 | 0 | 0.777369 | 0.977753 | 0.642134 | PASS |
| MLP | 22/22 | 5 | 4 | 1 | 0.778708 | 0.979596 | 0.643154 | PASS |
| Linear | 16/22 | 2 | 1 | 1 | 0.985990 | 0.977678 | 1.000000 | PASS |

## 判定边界与后续

1. fresh-process 结果优先于离线旧 outcome；Linear 的高激活离线结果不能直接视为运行权限。
2. 先完成 MLP fresh 对照；再依据 harmful 数、GM 和动作覆盖决定是否支付 Linear fresh 成本。
3. 结构胜负确定后，冻结单一 selector、阈值、gain floor、checkpoint 与 hash，再做 scale30/50 development E2E。
4. development E2E 通过后才运行 scale5/10/20/30/50 full20；scale5/10/20 必须零模型调用。
