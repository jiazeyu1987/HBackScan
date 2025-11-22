# GET `/task/{task_id}`

- 入口：`code/hospital_scanner/main.py:202`
- 作用：查询单个任务的状态或结果。

## 执行流程
1. 首先调用 `TaskManager.get_task_result`：先查内存缓存，再查 `tasks` 表并尝试反序列化 `result`。
2. 如取到结果，直接返回 `ScanResult` 对象（Pydantic 转 JSON）。
3. 若无结果，再调用 `db.get_task_info` 读取任务基本字段并返回包裹了 `code/message/data` 的字典。
4. 若数据库也无记录，抛出 404。

## 设计原因
- 优先返回完整结果对象，其次返回基本任务元数据，兼顾未完成和已完成两种情况。

## 优点
- 内存命中可减少 SQLite 访问。
- 结果/任务信息都能被查到时返回较完整的字段（含错误信息）。

## 缺点与风险
- 响应结构不统一：成功时可能返回 `ScanResult`，也可能返回 `{code,message,data}`，前端需分支解析。
- 任务状态与结果不一致问题（/scan 成功后状态仍可能是 running），会导致轮询逻辑混乱。
- 缺少权限控制，任意人可枚举任务 ID 查询历史结果。

## 改进建议
- 统一响应结构并显式返回 `status/created_at/completed_at/error` 等字段。
- 完善任务状态更新逻辑，保证状态机一致性。
- 添加鉴权和速率限制，避免任务信息泄露或被暴力枚举。
