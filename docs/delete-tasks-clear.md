# DELETE `/tasks/clear`

- 入口：`code/hospital_scanner/main.py:143`，调用 `db.clear_all_tasks()`。
- 作用：删除任务表全部记录（不触及医院/层级数据表）。

## 执行流程
1. 记录请求日志。
2. 调用 `db.clear_all_tasks`：执行 `DELETE FROM tasks` 并尝试重置 `sqlite_sequence`。
3. 成功返回 code 200，失败抛 HTTP 500。

## 设计原因
- 为测试或批量重跑任务提供快捷清理入口。

## 优点
- 逻辑简单，直接清空主任务表，便于回到初始状态。

## 缺点与风险
- 仍然无鉴权与确认，容易误删线上任务记录。
- 未级联清理 `hospital_info`，可能留下孤儿记录。
- `sqlite_sequence` 针对自增列，但 `tasks.task_id` 为文本主键；重置无意义且暴露设计混乱。

## 改进建议
- 增加鉴权与幂等保护，可限定仅调试环境可用。
- 级联清理 `hospital_info`、任务结果缓存，保证数据一致性。
- 提供分页删除或按状态清理（如仅删除 completed/failed）。
