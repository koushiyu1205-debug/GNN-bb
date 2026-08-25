# P0V5 Frontier Observability V7R 根因验证链

## 目的

V7R 不训练可部署候选，也不搜索安全 threshold。它只回答一个先于 V8 的问题：

> 在 literal Q0 已经弹出 4096 个 label 后，exact-safe QD1 的收益是否能由动作前可见的 Native frontier 稳定预测？

V7 的 `FAIL / NO_FRONTIER_SWITCH_HEADROOM` 永久只读。V7R 复用其冻结 Native binary、4096 probe、frontier graph 合同和 38 个 replay-eligible diagnostic contexts，但不导入已有 QPF0 wall outcome，也没有任何 QPD1 outcome 可导入。

第一次 V7R 启动尝试在完成 1 条 QPF0、0 条 QPD1 后，由 V7 replay 的“engine rebind 仅限 overhead”保护条件拒绝，已冻结为 `FAIL / V7R_QPD1_REBIND_CONTRACT_BLOCKED`，没有形成性能结论。V7R2 在任何新 arm outcome 前生成只改变 `engine_hash/state_hash` 的 rebound snapshot，并逐项冻结原始/重绑定 hash；正式 runner 不再使用 diagnostic rebind 开关。

## 固定顺序

1. 对 scale30/50 各 19 个固定 context 执行 `QPF0/QPD1 × 3` fresh blocked repeats。
2. 先按 context 取 matched median，再按实例内 GM 折叠。任一规模 `min(QPF0,QPD1)` oracle GM 大于 0.95 时立即停止。
3. 从 V2、V4、V5、V7 的 outcome-blind candidate census 估计自然 root frontier 命中率。未来 cap 使用 V7 同生成器/同引擎 cohort 的 Wilson 95% 下界，而不是观察命中率点估计。
4. 只做 diagnostic grouped-OOF：GAT、MLP、Linear、independent no-message、independent shuffled-topology。禁止 checkpoint、refit candidate、threshold、bundle 和 manifest。
5. 同时分析相似 frontier graph 是否对应相反的 benefit label。若 scale50 benefit/harm 无法区分，则停止 Context-GAT selector 方向。

## 预冻结门槛

- 每规模 determined context 比例至少 0.75，至少 12 个独立实例。
- 每规模 post-4096 switch oracle GM 不高于 0.95，QPD1 winner 至少 5 个实例。
- scale50 至少 4 个 benefit instances、4 个 neutral/harm instances。
- V7 cohort 的 Wilson-lower planning cap 对 37 个 eligible instances 不超过 600。
- scale50 diagnostic OOF 中，GAT benefit balanced accuracy 和 QD1-vs-Q0 rank accuracy均至少 0.65；GAT 不得比最佳 control 低超过 0.02。
- 最近 10% graph-distance pairs 的相反 benefit-label 比例不超过 0.35。

只有全部通过，terminal 才写 `PASS / FRONTIER_STATE_PREDICTABLE`。该 PASS 只允许另开一条正式候选训练链，不是加速证据、heldout 证据或部署授权。

## 运行

```bash
python scripts/initialize_p0v5_frontier_observability_v7r.py

python scripts/run_p0v5_frontier_switch_matrix_v7r.py --task-limit 6
# 使用相同命令恢复，直到 matrix gate 形成。

python scripts/analyze_p0v5_frontier_coverage_v7r.py
python scripts/run_p0v5_frontier_feature_sufficiency_v7r.py
```

任一 terminal 后，所有 writer 必须拒绝继续。整个链始终：

```json
{
  "candidate_trained": false,
  "manifest_generated": false,
  "development_only": true,
  "deployment_authorized": false,
  "production_switch_authorized": false
}
```
