# V735 Dynamic SRC Cut Gate

日期：2026-06-28

## 背景

V734 显示 dynamic SRC cut-on 对 greedy-anchor seed61311 有强正信号：

```text
seed61311: EXTERNAL_TIME_LIMIT -> OPTIMAL 110.710595s
```

但 seed61635 仍然 timeout，且 gap/dual 不变。因此 dynamic SRC 不能直接全局裸开；需要 gate 控制，只在当前 node 的 SRC violation 足够强时才加入 cut。

## 实现

修改位置：

- `BPC_future/solver/journey_driver.py`
- `BPC_future/tests/test_bpc_future.py`

新增配置：

```text
journey_dynamic_subset_row_cut_gate_enabled
journey_dynamic_subset_row_cut_gate_min_violated
journey_dynamic_subset_row_cut_gate_min_best_violation
```

逻辑：

```text
if cut_gate_enabled:
    if violated_count < min_violated:
        do not add SRC
    elif best_violation < min_best_violation:
        do not add SRC
    else:
        allow SRC addition
```

日志字段：

```text
cut_gate_enabled
cut_gate_passed
cut_gate_reason
cut_gate_min_violated
cut_gate_min_best_violation
```

可能原因：

```text
disabled
passed
violated_count_below_threshold
best_violation_below_threshold
```

## Exact-Safe 边界

这个 gate 只控制是否加入已经按当前 RMP fractional support 检出的 SRC。它不会：

- 生成 lower bound；
- 剪枝；
- 替代 exact pricing；
- 把 corrected/audit bound 当 certificate。

低信号时的行为是 fail-closed 到“不加 cut”，因此不会破坏精确性。

## 轻量验证

构造 `very_small` 上的 violated SRC：

```text
j12={1,2}, value=0.6
j23={2,3}, value=0.6
best_violation=0.2
```

验证结果：

```json
{
  "blocked_reason": "best_violation_below_threshold",
  "passed_added": 1,
  "passed_best_violation": 0.2
}
```

含义：

- `min_best_violation=0.3` 时不加 cut；
- `min_best_violation=0.1` 时加 cut；
- gate 行为可控。

## 推荐下一轮 V736

在 V733/V734 hard2 上做 cut-gated A/B：

```text
journey_dynamic_subset_row_cuts_enabled=True
journey_dynamic_subset_row_cut_gate_enabled=True
journey_dynamic_subset_row_cut_gate_min_violated=1
journey_dynamic_subset_row_cut_gate_min_best_violation=0.25
```

预期：

- seed61311 root/depth1 best violation 为 `0.333/0.5/0.428`，应通过 gate；
- seed61635 的部分 node best violation 为 `0.142/0.25/0.266`，弱节点会被过滤；
- 如果 seed61635 仍不改善，则说明需要更强 cuts/formulation，而不是继续加普通 SRC 数量。

## 验证

已完成：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
```

已完成轻量函数验证。未重新跑完整 `test_bpc_future` unittest runner，因为本机该 runner 曾进入 D 状态；后续整体验收时需要在干净环境跑完整 focused suite。
