# P0V5 Temporal Frontier Late-Switch V10R1 只读审计

## 目的

V10 完成了冻结的 `240/240` 个 fresh blocked tasks，但冻结 analyzer 存在
instance identity 传播错误：`collapse_matched_blocks()` 已将 `metadata` 展开到
collapsed row 顶层，V10 `_boundary_rows()` 却再次读取不存在的嵌套
`row["metadata"]`。因此所有 `instance_hash` 被写成 `null`，两个规模的
`determined_instances` 都被错误统计为 `1`。

V10R1 只做 post-terminal audit：

- V10 terminal、raw rows、collapsed rows、config 和全部 freeze 保持只读；
- instance identity 只从 outcome 前冻结的 `pilot_corpus.freeze.json` 恢复；
- 不产生任何新 wall outcome；
- 不修改 gate、boundary、删失规则或样本；
- 按实例先折叠，再复用 V10 的原始 gate。

## 解释边界

V10R1 不能把 V10 改写为成功，也不能授权模型训练。只有修正后的两个规模都通过
原冻结 gate，才允许另建 fresh temporal-GAT chain。若 scale50 仅有 oracle GM
headroom、但 strong-benefit instance 支持不足，仍必须停止训练。

执行命令：

```bash
PYTHONPATH=src:. pytest -q \
  tests/test_p0v5_temporal_frontier_late_switch_v10r1_audit.py

python scripts/audit_p0v5_temporal_frontier_late_switch_v10r1.py
```

输出进入独立目录：

```text
runs/p0v5_temporal_frontier_late_switch_oracle_v10r1_audit_20260818/
```
