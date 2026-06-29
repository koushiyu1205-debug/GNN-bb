# 20260628 V667/V668：Paired-Probe Proof-Risk Overlay 状态报告

## 结论

本轮没有改 solver 求解逻辑，只补齐了一条 score-map 校准链路：

- paired child-probe 中标记为 `hard_negative_proxy` 的 branch pair，可以作为 proof-risk evidence 压低对应 score row；
- 该 evidence 只影响后续 opt-in branch ordering；
- 不运行 BPC / pricing / RMP；
- 不产生 official lower bound；
- 不产生 certificate；
- 不参与剪枝。

这一步的作用是减少下一版 branch score 继续选择“短 probe 看似有收益、但完整闭环风险高”的假阳性 pair。它本身还不能把 20-scale 推到 `60/60 OPTIMAL`。

## 代码改动

修改：

- `BPC_future/scripts/apply_gat_branch_score_proofrisk_overlay.py`
- `BPC_future/tests/test_gat_branch_score_proofrisk_overlay.py`

新增能力：

- `--paired-probe-evidence`
- 读取 `journey_paired_probe_summary` 输出的 `paired_probe_rows.jsonl`
- 对 `pair_role=alternative` 且 `paired_label_type=hard_negative_proxy` 的 row 生成 negative evidence
- 对 `paired_label_type=positive_proxy` 且 wall gain 达标的 row 保留正向入口，但本轮 V666 没有 positive proxy

## 验证

已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest BPC_future.tests.test_gat_branch_score_proofrisk_overlay
PYTHONDONTWRITEBYTECODE=1 python -m unittest BPC_future.tests.test_journey_branch_candidate_replay_runbook BPC_future.tests.test_gat_branch_action_checkpoint_ranking
```

测试边界覆盖：

- paired-probe hard negative 能按 instance/key 命中 score row；
- 命中后只压低 score；
- `diagnostic_only=True`
- `runs_bpc_or_pricing=False`
- `official_bound_effect=False`
- `certificate_effect=False`
- `production_ready=False`

## V667：叠到当前 V543 合并 overlay

输出：

- `BPC_future/results/gat_branch_action_proofrisk_overlay_v667_v543_plus_v666_paired_probe_20260628/`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_branch_action_proofrisk_overlay_v667_v543_plus_v666_paired_probe_zh.md`

输入：

- base score rows: `BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json`
- paired evidence: `BPC_future/results/journey_paired_probe_summary_v666_v664_external_score_child_probe_20260628/paired_probe_rows.jsonl`

机器结果：

```text
score_row_count = 20768
positive_overlay_keys = 0
negative_overlay_keys = 4
paired_probe_positive_overlay_keys = 0
paired_probe_negative_overlay_keys = 4
overlay_counts = {'suppress_paired_probe_hard_negative': 2}
production_ready = false
```

命中的 row：

| instance | pair key | old score | new score | paired wall gain | child proof CPU | label |
|---|---:|---:|---:|---:|---:|---|
| `apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510` | `node:0:depth:0:1,18` | 0.316227 | 0.050000 | +19.261906 | 36.333554 | hard_negative_proxy |
| `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817` | `node:0:depth:0:5,18` | 0.000019 | 0.000019 | -9.259593 | 62.143576 | hard_negative_proxy |

解释：

- 第一条 wall gain 为正，但仍是 hard negative proxy，说明短 probe 省了一些时间，但 paired summary 按完整风险信号判定它不适合作为正向选择。
- 第二条本来分数已经很低，overlay 主要是给 row 打上 proof-risk 元数据。

## V668：叠到 V661 direct wall-time score rows

输出：

- `BPC_future/results/gat_branch_action_proofrisk_overlay_v668_v661_plus_v666_paired_probe_20260628/`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_branch_action_proofrisk_overlay_v668_v661_plus_v666_paired_probe_zh.md`

输入：

- base score rows: `BPC_future/results/gat_branch_action_v661_v659_walltime_on_v545_full60_logs_20260628/journey_branch_score_rows.json`
- paired evidence: `BPC_future/results/journey_paired_probe_summary_v666_v664_external_score_child_probe_20260628/paired_probe_rows.jsonl`

机器结果：

```text
score_row_count = 18823
positive_overlay_keys = 0
negative_overlay_keys = 4
paired_probe_positive_overlay_keys = 0
paired_probe_negative_overlay_keys = 4
overlay_counts = {'suppress_paired_probe_hard_negative': 2}
production_ready = false
```

命中的 row：

| instance | pair key | old score | new score | paired wall gain | child proof CPU | label |
|---|---:|---:|---:|---:|---:|---|
| `apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510` | `node:0:depth:0:1,18` | 0.540920 | 0.050000 | +19.261906 | 36.333554 | hard_negative_proxy |
| `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817` | `node:0:depth:0:5,18` | 0.545281 | 0.050000 | -9.259593 | 62.143576 | hard_negative_proxy |

解释：

V668 更能说明问题：裸 V661 wall-time head 给这两条 hard-negative proxy 打了约 `0.54` 的分数。这意味着单纯预测短期 wall-time gain 容易高估 proof-tail 风险 pair；下一版训练不能只看 wall time，应把 gap/fathom/child certificate/retry 作为共同标签。

## 对 20-scale 目标的影响

正向影响：

- 把 V666 中真实暴露的 hard-negative proxy 回灌到 score map；
- 为下一版 GAT/overlay 提供了“高 wall-time score 但 proof-risk 高”的校准样本；
- 支持后续 RouteOpt-style BKF / staged testing：GAT 先筛候选，proof-risk evidence 再限制裸选高风险 pair。

局限：

- 本轮只命中 2 个实际 score row；
- 没有产生新的 full-solve positive；
- 没有跑新的 full60；
- 当前最佳 20-scale 仍是 V545：`36/60 OPTIMAL`，还没达到所有 20 规模 600s 内最优。

## 下一步

1. 把 V666/V667/V668 的 `paired_probe_hard_negative` 纳入下一版 branch-action 数据集，作为 hard negative 或 proof-risk auxiliary label。
2. score map 导出时加入多目标压制项：短 wall-time gain 不能单独覆盖 gap/fathom/retry 风险。
3. 借鉴 RouteOpt 的 BKF 思路，下一步不裸用最高分 pair，而是：
   - GAT / overlay 先选 topK；
   - 用 child width、balance、completion retry risk 做 Stage-1 筛选；
   - 对少量候选跑 fixed-budget child probe；
   - 只把左右 child 都改善的 pair 放入 score-gated branch/early-branch。
4. 暂不把 V667/V668 标为 production-ready；它们是 calibration 产物，不是最终可验收 score map。
