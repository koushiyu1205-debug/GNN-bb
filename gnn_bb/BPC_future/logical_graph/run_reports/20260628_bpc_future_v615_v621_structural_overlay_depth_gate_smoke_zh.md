# 20260628 V615-V621：结构性 Proof-Tail Overlay 与 Branch Score Depth Gate

## 结论

本轮做了两件事：

1. 把 V614/V618 的失败分支路径转成 hard-negative evidence；
2. 尝试用结构性 proof-tail overlay 和 branch score depth gate 避免 GAT 继续把搜索带进 completion-bound proof tail。

结果：两种办法都没有让 4 个 20-scale 难例闭合。

- V618：V617 结构性 overlay，4/4 `EXTERNAL_TIME_LIMIT`；
- V620：V617 + `journey_branch_candidate_score_max_depth=2`，4/4 `EXTERNAL_TIME_LIMIT`；
- V620 的 changed branch 从 V618 的 `70` 降到 `25`，但 CB retry 仍有 `175` 次，和 V614/V618 基本同量级。

这说明当前失败不只是“深层 GAT 选错 pair”。即使深层 score 回退，浅层分支和 proof structure 仍会进入同类 completion-bound 证明尾巴。

## 代码与工具

新增：

- `BPC_future/scripts/apply_journey_branch_score_structural_risk_overlay.py`
- `BPC_future/tests/test_journey_branch_score_structural_risk_overlay.py`

修改：

- `BPC_future/scripts/build_journey_branch_score_failure_evidence.py`
  - 支持 flat batch layout：`results.csv` + `logs/**/*.jsonl`
- `BPC_future/tests/test_journey_branch_score_failure_evidence.py`
  - 增加 flat batch 覆盖
- `BPC_future/solver/journey_driver.py`
  - 新增 opt-in 配置：`journey_branch_candidate_score_max_depth`
  - 超过该深度时，branch score 排序回退到原 fractionality 规则
  - 日志增加 `branch_score_max_depth`、`branch_score_depth_allowed`
- `BPC_future/tests/test_bpc_future.py`
  - 增加 branch score max-depth 单测

已验证：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/apply_journey_branch_score_structural_risk_overlay.py \
  BPC_future/scripts/build_journey_branch_score_failure_evidence.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/tests/test_journey_branch_score_structural_risk_overlay.py \
  BPC_future/tests/test_journey_branch_score_failure_evidence.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_branch_score_opt_in \
  BPC_future.tests.test_journey_branch_score_failure_evidence \
  BPC_future.tests.test_journey_branch_score_structural_risk_overlay
```

结果：`OK`。

## Evidence 生成

### V615：V614 失败路径

输入：

```text
BPC_future/results/20260628_v614_v613_failure_overlay_smoke4_tasks20
```

输出：

```text
BPC_future/results/journey_branch_score_failure_evidence_v615_v614_v613_smoke4_20260628
```

汇总：

```text
result_rows = 4
nonoptimal_result_rows = 4
branch_events = 137
scored_branch_events = 58
hard_negative_rows = 58
completion_bound_retry_count = 178
ordinary_retry_count = 4
status_counts = {'EXTERNAL_TIME_LIMIT': 4}
```

### V619：V618 失败路径

输出：

```text
BPC_future/results/journey_branch_score_failure_evidence_v619_v618_v617_smoke4_20260628
```

汇总：

```text
result_rows = 4
nonoptimal_result_rows = 4
branch_events = 154
scored_branch_events = 70
hard_negative_rows = 70
completion_bound_retry_count = 174
ordinary_retry_count = 0
status_counts = {'EXTERNAL_TIME_LIMIT': 4}
```

### V621：V620 失败路径

输出：

```text
BPC_future/results/journey_branch_score_failure_evidence_v621_v620_depth2_smoke4_20260628
```

汇总：

```text
result_rows = 4
nonoptimal_result_rows = 4
branch_events = 162
scored_branch_events = 44
hard_negative_rows = 44
selected_pair_changed_count = 25
completion_bound_retry_count = 175
ordinary_retry_count = 3
status_counts = {'EXTERNAL_TIME_LIMIT': 4}
```

## V617 Overlay

V616 初版触碰 `9508/18823` 行，过于激进，因此保留为诊断。

V617 改为保守结构性 overlay：

```text
output_dir = BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v617_conservative_structural_prooftail_overlay_on_v613
score_row_count = 18823
evidence_row_count = 224
exact_evidence_scope_count = 448
overlay_counts = {
  'exact_timeout_hard_negative': 224,
  'family_deep_high_score': 492,
  'family_retry_tail_risk': 607,
  'repeated_failed_pair': 3135
}
touched_row_count = 4329
depth_p75 = 6
score_p75 = 0.90072864625
root_touched = 8
```

V615 的 `58` 个新失败 exact row 全部被压到 `0.03`。

## Smoke 对比

固定 4 个 V609/V614 难例，600s，max-workers=4，early branch off，admission off。

| run | score/control | status | mean wall | mean gap | branch | changed branch | CB retry |
|---|---|---:|---:|---:|---:|---:|---:|
| V614 | V613 exact overlay | 4/4 EXT TL | 600.022s | 0.045914 | 137 | 58 | 178 |
| V618 | V617 structural overlay | 4/4 EXT TL | 600.033s | 0.047320 | 154 | 70 | 174 |
| V620 | V617 + score max depth 2 | 4/4 EXT TL | 600.019s | 0.047618 | 162 | 25 | 175 |

V620 中：

```text
branch_score_depth_allowed = True: 26 branch
branch_score_depth_allowed = False: 136 branch
```

这证明 depth gate 生效：深层分支基本回退到 baseline/fractionality；但 proof-tail 仍然没有消失。

## 解释

V617 exact/structural suppress 后，V618 仍能找到新的高分失败路径。V620 进一步关闭深层 score 后，changed branch 明显下降，但 CB retry 几乎不变。

这说明当前 branch score 问题有两层：

1. 深层模型确实不可靠，应该 gate 或重新训练；
2. 但当前 4 个难例的主要 proof burden 不是只由深层 GAT 假阳性造成，浅层分支和 formulation/proof-tail 结构本身也会产生大量 certified no-negative 证明。

所以继续堆 exact hard-negative overlay 不是主线。它只会让模型绕开旧坏 row，再走新坏 row。

## 下一步

1. 保留 `journey_branch_candidate_score_max_depth` 作为 opt-in 安全阀，但不要把它当最终优化。
2. 把 V615/V619/V621 加入训练/风险数据，明确标记为 right-censored proof-tail hard negative。
3. 下一轮 branch score 不应只输出 pair score，还要输出 context action：
   - `USE_BRANCH_SCORE`
   - `FALLBACK_BASELINE`
   - `NEED_STRONG_BRANCH_PROBE`
   - `NEED_CUT_OR_FORMULATION`
4. 对这 4 个实例做 shallow strong-branch probe：root/depth1 的 alternative pair 是否能显著减少 child CB retry。V620 已经证明“只关深层 GAT”不够，必须重新评估浅层 pair。
5. 同时推进 completion-bound proof cost 本身的窄优化，因为大量 CB retry 是合法 certificate proof，不是可直接跳过的浪费。

## Exact-Safe 边界

本轮新增工具和 depth gate 都只影响 branch ordering / offline score map：

- 不运行 BPC/pricing 的离线脚本不产生 certificate；
- score/overlay/depth gate 不提供 official bound；
- early branch 仍关闭；
- child/fathom 仍依赖 exact pricing closure；
- 所有非最优实例继续记录 gap，而 `EXTERNAL_TIME_LIMIT` 不能被当成成功。
