# V730 Dynamic SRC Audit Entry

日期：2026-06-28

## 目的

V726/V729 的共同结论是：greedy-anchor hard case 中，局部 Ryan-Foster pair 替换没有明显改变 dual/gap。继续盲目扩 depth1/depth2 branch replay 会产生大量右删失 neutral rows，训练价值低。

因此本轮开始推进 cuts/formulation 线，但先不直接改变求解结果，而是补一个 exact-safe 的 `dynamic subset-row cut audit` 入口：

- 只枚举当前 RMP fractional support 上 violated subset-row 候选；
- 记录 violation、route compactness、top candidates；
- audit-only 时不加入 cuts，不改变 RMP，不改变 pricing，不改变 official bound/certificate。

## 代码变化

修改位置：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

新增配置：

```text
journey_dynamic_subset_row_audit_enabled
journey_dynamic_subset_row_audit_top_n
```

行为：

```text
journey_dynamic_subset_row_audit_enabled=True
journey_dynamic_subset_row_cuts_enabled=False
```

时，`_separate_journey_subset_row_cuts` 会执行候选枚举和日志记录，但 `added=0`，`cuts` 和 `cut_keys` 不变。

`journey_cut_separation` 现在额外记录：

```text
audit_enabled
audit_only
best_violation
best_compactness
top_candidates = [
  {tasks, k, rhs, violation, compactness}
]
```

其中 `compactness` 使用已有 `_journey_static_subset_row_compactness_score`，只是诊断排序/解释字段，不是 cut 有效性来源。

## Exact-Safe 边界

本轮没有让 audit 结果参与：

- official lower bound；
- node fathom；
- pricing certificate；
- child lower bound；
- branch pruning。

audit-only 模式只是回答一个问题：

```text
在 greedy-anchor 这类 dual 不动节点上，当前 RMP fractional support 是否已经暴露出可用的 subset-row-like violation？
```

只有后续确认这些 cut 能稳定提高 dual/corrected LB，才考虑进入 opt-in cut-on 实验。

## 轻量验证

直接构造 very_small 的两个 fractional journey：

```text
j12 = {1,2}, value=0.6
j23 = {2,3}, value=0.6
```

audit-only 结果：

```json
{
  "added": 0,
  "cuts": 0,
  "violated": 1,
  "best_violation": 0.2,
  "top0": {
    "tasks": [1, 2, 3],
    "k": 2,
    "rhs": 1.0,
    "violation": 0.2,
    "compactness": 5.870667417
  }
}
```

这验证了：

1. violated SRC 能被发现；
2. audit-only 不改 cut set；
3. 日志中有后续 greedy-anchor 分型需要的字段。

## 测试

已完成：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/scripts/summarize_journey_paired_probe_runbook.py \
  BPC_future/tests/test_journey_paired_probe_summary.py
```

已完成轻量函数验证。一次 `python -m unittest ...test_journey_dynamic_subset_row...` 在本机进入 D 状态并被终止；因此本轮未把该 unittest 结果作为验证依据。

## 下一步

1. 在 greedy-anchor seed61311/seed61635 的 V726/V729 配置上打开：

```text
journey_dynamic_subset_row_audit_enabled=True
journey_dynamic_subset_row_cuts_enabled=False
journey_dynamic_subset_row_cut_budget=600
journey_dynamic_subset_row_audit_top_n=20
```

2. 跑短预算 root/depth1 audit，不比较 wall time，先看：

```text
violated count
best_violation
top candidate task sets
是否集中在 greedy-anchor hard family
```

3. 若 audit 显示 violated SRC 稳定存在，再做 cut-on A/B：

```text
audit-only vs cut-on
指标：dual bound、corrected LB、fathom count、CB retry、是否仍 exact pricing closure
```

4. 若 audit 中几乎没有 useful violation，则 greedy-anchor 的 dual 不动更可能来自 formulation 更深层问题，需要转 route-region aggregation 或 incumbent/branch-cuts 联动。
