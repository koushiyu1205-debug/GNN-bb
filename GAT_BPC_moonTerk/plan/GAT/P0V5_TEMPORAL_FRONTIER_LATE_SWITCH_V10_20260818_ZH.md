# P0V5 Temporal-Frontier Late-Switch Oracle V10

## 1. 研究边界

V9R1 已冻结为 `FAIL / MULTIRES_FRONTIER_NOT_IDENTIFIABLE`。该结果说明：4096-pop 单时点无论使用完整 64-cell mass 还是 256-label local graph，scale50 的 QD1 benefit/harm 都没有稳定的 message-passing 可分性。V10 因此不训练新 GAT，而先回答更靠前的问题：**在同一个正式 exact request 内更晚切换 QD1，是否仍存在足够的真实 wall oracle headroom？**

本链只允许：

- scale30 在 4096 pop 测量 Q0/QD1；
- scale50 在 4096、8192、16384 pop 测量 Q0/QD1；
- 每个边界前始终使用 literal Q0；
- 同一 request 在观测点保存 telemetry-only frontier graph；
- 只有最终 decision boundary 可以原位迁移全部剩余 label 到 QD1。

QB1、QGR1、label-GAT 继续 veto。V10 不改变 dominance、bound、reduced cost、route universe、branch/cut、停止条件或 certificate。

## 2. 证据链

运行根目录：

```text
runs/p0v5_temporal_frontier_late_switch_oracle_v10_20260818/
```

三段冻结顺序：

1. `bootstrap.freeze.registry.json`：冻结 Native/Python source、两个 binary、38-context pre-action source 和 outcome-blind 8+8 pilot selection。
2. `native_differential.report.json`：新旧 binary 做 500-case disabled-Q0 differential，必须零 mismatch。
3. `performance.freeze.registry.json`：只有 differential PASS 后，才把选中 snapshot 的 engine/state hash 重绑定到 V10，并冻结全部 240 个 fresh-process task。

V7R2/V7R3 的 QPF0/QPD1 wall outcome 不导入。V10 选取每实例一个 primary context，再按冻结 SHA256 顺序取每规模 8 个实例。该链仍属于旧实例上的机制诊断；只有 V10 oracle PASS，才允许另建全新实例 temporal-GAT pilot。

## 3. Native 合同

新增 request 字段：

```text
proof_queue_frontier_observation_boundaries
```

合法值必须是 decision boundary 的 canonical prefix：

```text
4096  -> [4096]
8192  -> [4096,8192]
16384 -> [4096,8192,16384]
```

每个 snapshot 包含当时的 64-cell graph、完整 context counters、graph hash 和 build wall。中间 snapshot 不决策、不迁移、不释放 Q0 queue；最终 boundary 才按 QPF0/QPD1 继续 Q0 或原位迁移。`State` 不增加字段，继续要求 `sizeof(State)==176`。

## 4. Oracle gate

每个 context/action 运行三次 blocked fresh process。边界至少 2/3 block 可比较才 determined。QPF0/Q0 用于计量多时点 graph tax；QPD1/Q0 是净加速比；`min(Q0,QPD1)` 是 measured oracle。

scale30 4096 gate：

- 至少 7/8 determined instances；
- QPF0/Q0 GM `<=1.01`、worst `<=1.05`；
- fixed QPD1/Q0 GM `<=0.98`；
- oracle GM `<=0.95`；
- QPD1 winner 至少 5 个实例。

scale50 每个 boundary 独立判定：

- 至少 7/8 determined instances；
- QPF0/Q0 GM `<=1.01`、worst `<=1.05`；
- oracle GM `<=0.95`；
- QPD1 winner 至少 3 个实例；
- strong benefit 和 neutral/harm 各至少 2 个实例。

通过多个 scale50 boundary 时，先选 oracle GM 最低者，完全相同时选更早 boundary。任何 label migration、graph determinism、route RC 或 certificate redline 都立即终止。

## 5. 执行命令

```bash
python scripts/initialize_p0v5_temporal_frontier_late_switch_oracle_v10.py
python scripts/audit_p0v5_temporal_frontier_native_differential_v10.py
python scripts/freeze_p0v5_temporal_frontier_late_switch_pilot_v10.py

python scripts/run_p0v5_temporal_frontier_late_switch_matrix_v10.py \
  --task-limit 6
```

最后一条重复执行至完成。V10 PASS 只授权“全新实例 temporal-GAT pilot”，不产生 checkpoint、runtime manifest 或 deployment authority。V10 FAIL 表明在已测边界上缺少足够 late-switch headroom，应停止继续提高单时点 GAT 表达能力。

