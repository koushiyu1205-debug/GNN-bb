# 本目录不是正式 promotion 证据

状态：`INVALIDATED_EXTERNAL_INTERFERENCE`

2026-07-22 15:44:15 Asia/Shanghai，后台自动 `git gc --auto` 启动
`git pack-objects`，持续占用约 3.5 GiB RSS 和约 250% CPU，并使系统 swap 从约
12 MiB 增至约 248 MiB。该干扰与 strict paired performance benchmark 不兼容。

发现干扰后只停止了本次 promotion 进程树，原始 815 行、heartbeat、stdout/stderr 和
未完成 attempt 全部保留。最后一个被主动终止的 slot 会按 fail-closed 记录，不能解释为
算法 correctness failure。

本目录中的任何时间、paired ratio 或 partial summary 均不得用于 promotion。正式实验必须在
自动 git maintenance 完全结束、资源恢复后，从新的空目录重新执行全部 1040 fresh slots。
