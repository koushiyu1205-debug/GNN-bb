# P0V5 QG2 V5 Trace-First 关闭审计

审计日期：2026-08-07。

## 结论

本轮计划以“候选被fresh-process性能权威否决”结束，而不是以部署成功结束。
用户明确要求停止继续实验；当前TinyGAT不得部署，后续阶段不再执行。

## 要求与证据

| 要求 | 状态 | 当前证据 |
|---|---|---|
| P0V5 Exact control保持冻结 | 通过 | 本轮未修改Exact、dominance、bound、RC或certificate路径 |
| Q0-only trace corpus | 完成 | 45个完整context；scale30 33、scale50 12 |
| TinyGAT优先训练 | 完成 | 27 epochs，best epoch 19，24,337参数 |
| 每轮training curve | 完成 | `label_gat/training_curve.jsonl` |
| train/calibration/heldout诊断 | 完成 | `label_gat/training_report.json` |
| feature/message-passing归因 | 完成 | `label_gat_attribution.json` |
| fresh-process Q0/QG2性能权威 | 已形成否决证据 | 3个完整context全退化，GM 1.2969；重尾QG2三次超时 |
| correctness与fail-closed边界 | 通过已运行范围 | 所有完整replay safe；超时不签certificate；无label/filter/RC红线 |
| scale50 force-on | 按用户终止 | 未运行，不用于宣称跨规模收益 |
| Context GAT | 不适用 | Label QG2未通过force-on且用户要求停止 |
| MLP/Linear对照 | 不适用 | 设计规定仅在GAT fresh为正后运行 |
| E2E与full20 | 不适用 | 没有通过fresh gate的候选，禁止进入正式基准 |
| production部署 | 明确禁止 | terminal decision中deployable与production switch均为false |

## 未完成项的解释

scale50、Context GAT、MLP/Linear和正式full20不是被当作“默认为通过”，而是因为
前置fresh-process gate失败而没有资格启动。后续若重开multi-arm Context GAT，必须作为
新的研究方向建立独立freeze、数据和验收，不能复用本轮关闭状态宣称成功。

## 最终状态

- 当前模型结果：负；
- 当前模型部署：禁止；
- 当前实验进程：全部停止；
- Exact control：保持原样；
- 本轮计划：按性能失败停止条件关闭。
