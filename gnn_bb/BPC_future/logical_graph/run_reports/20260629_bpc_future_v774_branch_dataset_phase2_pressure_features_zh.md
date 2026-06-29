# V774 Branch Action Dataset Phase2 Pricing Pressure Features

日期：2026-06-29

## 目的

V773 已经把 Phase2 child pricing pressure 接进 solver 内 `routeopt_bkf_staged` 日志和 BKF opt-in score。V774 把这些字段继续接入 GAT branch action dataset，避免后续训练仍然只按 child LP gain / wall-time gain 学分支。

核心原因：

```text
child RMP gain 大，不代表 child proof tail 会变短。
如果 child pricing 立刻发现强负列，或者两侧 child pressure 极度不均衡，
这个 branch pair 对完整闭环可能是 hard negative。
```

## 修改文件

- `BPC_future/scripts/build_gat_branch_action_sanity_dataset.py`
- `BPC_future/tests/test_gat_branch_action_sanity_dataset.py`

## 新增 context features

新增到 `BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA`：

```text
phase2_same_child_negative_severity
phase2_separate_child_negative_severity
phase2_negative_severity_sum
phase2_negative_severity_gap
phase2_negative_severity_balance_ratio
phase2_negative_child_presence_balance_gap
```

含义：

- `same/separate_child_negative_severity`：两侧 child 的负列压力；
- `negative_severity_sum`：总负列压力；
- `negative_severity_gap`：两侧压力差；
- `negative_severity_balance_ratio`：压力均衡程度；
- `negative_child_presence_balance_gap`：是否只有一侧 child 有负列压力。

这些字段只进入训练/诊断特征，不改变 solver 行为。

## Exact-Safe 边界

V774 不影响：

- official lower bound；
- pricing certificate；
- branch candidate live score；
- fathom/prune；
- RMP 或 pricing 逻辑。

它只改变离线数据集样本的 context feature schema 和 `.pt` 样本张量。

## 验证

编译：

```text
python -m py_compile \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py
```

结果：通过。

聚焦测试：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset
```

结果：

```text
Ran 1 test in 0.391s
OK
```

测试覆盖：

- manifest `context_feature_schema` 包含新字段；
- 生成的 sample context tensor 长度与 schema 一致；
- 样例 row 中新字段数值正确写入 `.pt` 样本。

## 对主线的意义

V774 是 Branch Score 主线和 formulation/cuts 线之间的桥：

- V772/V773 说明强 formulation/child pricing probe 能发现 branch pair 的真实 proof pressure；
- V774 让这些 proof-pressure 信号进入 GAT branch action 数据集；
- 后续训练可以把 “LP gain 大但 child pricing pressure 也大” 学成 hard negative，而不是继续误认为正例。

## 下一步

1. 重建最新 branch action dataset manifest。
2. 统计新字段非零覆盖率。
3. 如果覆盖不足，优先对 hard instances 做 state-scoped replay/probe，不急着训练。
4. 并行继续推进 route/order/resource-aware cuts，让 seed61635 这类 best dual 不动的 hard case 真正移动 lower bound。

