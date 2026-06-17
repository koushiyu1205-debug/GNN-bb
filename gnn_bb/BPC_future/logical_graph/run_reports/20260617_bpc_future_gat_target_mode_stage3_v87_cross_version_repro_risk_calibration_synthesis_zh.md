# 2026-06-17 BPC_future GAT Stage 3 v87 跨版本复现与 Risk-head 校准综合报告

## 读取范围

本轮按目标模式计划复读并对照了 Stage 3 关键版本：

```text
v15/v32/v43
v39/v41/v44/v45/v46
v50/v53/v55/v60
v61-v72
v75-v86
Stage 4 v53 execution / A-B ROI / certificate audit
```

边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 跨版本主线

| 版本线 | 观察 | 当前解释 |
|---|---|---|
| v15/v32/v43 | missed high-ROI 不是 near-threshold，16 个 missed 中 near-threshold 为 0。 | 早期主因是 candidate-head score gap 和 embedding structural gap，不能靠降 threshold 解决。 |
| v39/v41 | coverage 上升后 false-delay 约 `0.449`，集中在 `sector-wave|20` 少数 context。 | candidate head 退化时，delay gate 单独兜底会失败；hard-negative 是 context-local action ranking 问题。 |
| v44/v45/v46 | false-delay contrast 可把 false-delay 压到 `0.0`，但 v45 smoke accepted 只有 `3/123`。 | delay-safe shell 存在，但过窄；zero-FP 低覆盖不能满足加速目标。 |
| v50/v53 | context-batch A/B 多数为 negative，但 v53 发现 `79fde` 内部有 positive individual target。 | context-level hard-negative 标签太粗，必须落到 individual target / trace / path 粒度。 |
| v61-v72 | trace scalar 改善 macro coverage 和 random-wave capture，但 v71 focused strict 仍只有 `0.25`。 | trace/timing/resource scalar 有效但不充分，宏观 ROI 会掩盖同 context 排序失败。 |
| v75-v78 | path-token/slack 后 focused raw/admission 从 `0.25` 到 `1.0`，delay-risk 仍为 `0.0`。 | path-token/slack 是真实结构进步，应保留；blocker 转向 delay-risk head。 |
| v79/v80 | delay-risk pairwise weight `1.0` 后 focused delay-risk 到 `0.5`，accepted `37`，false-delay `0.0071`。 | risk-head 方向有效，但 strict focused gate 仍不过，不能进 Stage 4。 |
| v81/v82 | weight `3.0` false-delay 为 `0.0`，但 accepted 降到 `14`，raw/admission 回退到 `0.75`。 | 盲目增大 risk loss 会回到窄安全壳，并破坏 candidate ranking。 |
| v85 | 用训练内 focused gate 复跑 v79 配置，focused raw/admission 变成 `0.0/0.0`，accepted `15`。 | gate 口径不是问题；旧 v79/v80 可被 focused 审计复现。更像训练配置、seed 或 provenance 不完整暴露出的复现问题。 |
| v86 | 同时开启 hard ROI negative/safe delay calibration weight `1.0/1.0`，accepted `60`，ROI CI 很高，但 false-delay = `1.0`。 | risk-head 校准不能粗暴双开；高 coverage/high ROI point estimate 可以伴随安全性完全失败。 |

## v85 / v86 新证据

### v85：复现性问题

```text
dataset = v75_v66_path_tokens_slack_20260617
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused gate row_index_min = 383
accepted_batch_count = 15
accepted_batch_roi = 0.7002375960350037
accepted_batch_roi_ci_low = 0.40042289048287344
safe_precision_ci_low = 0.7961107336956521
false_high_priority_on_delay = 0.0
focused raw/admission/delay-risk/strict = 0.0 / 0.0 / 0.25 / 0.0
primary = candidate_head_context_ranking_failure
stage4_candidate_ready = false
```

v85 没有重现旧 v79/v80 的 `raw=1.0, admission=1.0, delay-risk=0.5`。但训练内 focused gate 对旧 v79 checkpoint 的结果与外部 v80 审计一致，因此问题不在 focused gate 口径。当前判断是：旧训练 artifact 缺完整 `training_run_config`，导致复跑不可解释。

本轮已经把 `training_run_config` 写入新 checkpoint / metrics / report，以后必须记录 seed、split、epochs、optimizer、model_config、loss_options、gate_config、focused_pair_gate_config 和 checkpoint selection。

### v86：risk-head 校准负结果

```text
hard_roi_negative_delay_loss_multiplier = 1.0
hard_roi_safe_delay_loss_multiplier = 1.0
pairwise_delay_risk_contrast_loss_multiplier = 1.0
accepted_batch_count = 60
accepted_batch_roi = 5.5014368367148565
accepted_batch_roi_ci_low = 3.0197149083421886
high_priority_precision = 0.8923643054277829
high_priority_precision_ci_low = 0.87253887789687
safe_precision_ci_low = 0.939826069522067
false_high_priority_on_delay = 1.0
false_safe_rate_union = 1.0
focused raw/admission/delay-risk/strict = 0.25 / 0.25 / 0.25 / 0.25
primary = candidate_head_context_ranking_failure
stage4_candidate_ready = false
```

v86 的 ROI 和 coverage 看起来很强，但 safety 完全失败。这是一个明确负结果：不能用 high accepted ROI 抵消 false HIGH_PRIORITY on delay，也不能把 risk-head calibration loss 以 `1.0/1.0` 粗暴开启。

## 新理解

1. v75 path-token/slack 仍是当前最可靠的结构改进。它把 focused raw/admission ranking 拉到 `1.0` 的证据没有被推翻；v85 只是说明复跑不可解释，需要补 provenance 和 seed sweep。

2. delay-risk head 是独立 blocker，不是 admission threshold 的附属项。v79 说明 pairwise delay-risk 监督可改善一半 pair；v81/v86 说明权重或校准过强会压坏 coverage、candidate ranking 或 safety。

3. Stage 3 必须继续按硬 admission 目标训练：precision、safe precision、ROI CI、false-delay、false-safe、coverage、family holdout、focused strict gate 任一失败都只能 diagnostic。

4. 高 ROI point estimate 不可信，必须看 safety 和 CI。v86 是反例：accepted ROI 很高，但 false-delay 和 false-safe 都是 `1.0`。

5. 当前 focused gate 是 regression sentinel，不是完整验证集。它只有 9 rows / 4 pairs，适合防止已知 context-local failure 回归，但不能替代 family/context holdout、kNN/OOD 和 Stage 4 shadow。

6. Stage 4 v53 的价值仍是安全执行和标签回流，不是 proof。5/10 sentinel 无回归、certificate audit 无 violation，但 20-task 仍是 `TIME_LIMIT` / `dual_bound=None`，不能支撑 Stage 5。

## 当前问题

1. 旧 v79 checkpoint 的训练配置不可完全复现。没有完整 run config 的旧 checkpoint 只能当参考 baseline，不能当可复现实验结论。
2. candidate head 与 delay-risk head 之间有冲突：过强 risk 目标可能把模型推回窄壳，或直接把 delay hard-negative 放进 HIGH_PRIORITY。
3. v86 暴露了 calibration loss 的方向性风险：同时惩罚 hard ROI negative delay 和 hard ROI safe delay 可能让 risk-head 学到错误安全边界。
4. focused tranche 太小，当前只覆盖 sector-wave 的 3 个 context；random-wave 和更大 task count 的 hard pair 仍不足。
5. v85/v86 都没有 kNN/OOD holdout，且没有 Stage 4 shadow / opt-in A/B；不能推进 mutating admission。
6. Stage 5 仍未接近：没有 20-task 稳定 `OPTIMAL < 200s`，没有 official dual bound，final exact pricing closure 仍是唯一 proof source。

## 下一步

1. 以旧 v79/v80 的 focused 行为作为参考，不把 v85 当成 v79 被推翻；先做带 `training_run_config` 的 controlled seed sweep。
2. 固定 v75 path-token/slack schema，继续保留 candidate pairwise loss 和 focused strict gate。
3. risk-head 校准不要再双开 `1.0/1.0`。下一轮只做小权重、单变量消融，例如 `0.1`、`0.25`，并分别测试 negative-delay 与 safe-delay 分量。
4. 每个训练结果必须同时报告：
   - macro ROI / precision / CI；
   - false HIGH_PRIORITY on delay / false-safe；
   - family holdout；
   - focused raw/admission/delay-risk/strict；
   - kNN/OOD。
5. 扩展 focused regression tranche：加入 v15/v43 missed high-ROI、v53 `79fde/ac15/ac056` individual rows，以及 random-wave same-context positive/hard-negative。
6. 在 focused strict `1.0`、threshold frontier、family holdout、kNN/OOD 都通过前，不进入 Stage 4 mutating admission；Stage 4 最多继续 shadow / opt-in diagnostic A/B。

## Verification

```text
py_compile train_gat_batch_impact.py + test_gat_batch_impact_training.py = pass
unittest BPC_future.tests.test_gat_batch_impact_training = 26 tests OK
v85 delay-risk pairwise + focused gate training smoke = pass, gate failed as diagnostic
v86 risk-head calibration + focused gate training smoke = pass, gate failed as diagnostic
runs_bpc_or_pricing = false
production_ready = false
stage4_candidate_ready = false
stage5_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## Exactness Boundary

本轮只做离线训练、诊断审计和报告综合，不改变 solver、pricing、RMP、branch/cut、final judge 或 benchmark 默认配置。

GAT 可以帮助 pricing 更早搜索可能改善 RMP trajectory 的列族、路径序列和候选 batch；GAT+CBF/kNN/OOD 可以对 true-RC verified negative candidates 做有限延迟 admission scheduling。最终 optimality proof 仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
