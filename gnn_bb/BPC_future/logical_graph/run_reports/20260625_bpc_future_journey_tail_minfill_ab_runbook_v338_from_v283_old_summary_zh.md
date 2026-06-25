# Journey Tail Min-Fill A/B Runbook

日期：2026-06-25

## 目的

把 completion-tail profile 中的低 min-fill audit-only 候选转成 paired replay 命令。该脚本只生成 runbook，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_minfill_ab_runbook = current
status = empty
raw_record_count = 8
candidate_instance_count = 0
entry_count = 0
command_count = 0
time_limit = 260
tail_min_fill = 4
tail_min_fill_max_depth = 0
tail_min_fill_final_probe_only = True
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

## 说明

每个 entry 有 baseline 与 tail_minfill_optin 两条命令。baseline 强制保持低 min-fill 关闭，opt-in 只打开低 min-fill 调度；两者都保持 exact oracle 负责 RC 与证书。

## Entries

```json
[]
```
