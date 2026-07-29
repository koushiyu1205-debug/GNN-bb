# P0 禁止任务点等待：5/10/20/30 冷启动基准

- 状态：`COMPLETE`
- 服务时序策略：`no_task_wait_base_departure_shift_v1`
- 完成 / 计划：1 / 1
- exact / correctness：1 / 1
- 旧 P0 V2 冻结证据保留：`True`
- 新基准允许冻结：`False`

| scale | 完成 | exact | mean s | p50 s | max s | mean ratio vs V2 | 目标不变/升高/降低 | peak RSS GiB |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 0.432211 | 0.432211 | 0.432211 | 1.149623 | 0/1/0 | 0.006851 |

目标值只能保持或升高：新模型删除了任务点等待可行性，未增加任何可行解。
若出现目标降低、哈希漂移、非 P0 策略、resume、外部 pool 或证书红线，运行立即 fail closed。
