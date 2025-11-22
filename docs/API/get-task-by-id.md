# GET `/task/{task_id}`

- 入口：`code/hospital_scanner/main.py:202`
- 作用：查询单个任务的状态或结果。

## 执行流程
1. 调用 `TaskManager.get_task_result`：先查内存缓存，再查数据库并反序列化 `result`。
2. 若有结果，直接返回 `ScanResult`（Pydantic 对象）。
3. 若无结果，再调用 `db.get_task_info` 返回 `{code,message,data}` 结构的任务元信息。
4. 全部缺失则抛 404。

## 设计原因
- 优先返回完整结果，其次返回任务元数据，兼容未完成/已完成两种情况。

## 优点
- 内存命中可减少数据库访问。
- 基本信息包含错误字段，便于查看失败原因（如有）。

## 缺点与风险
- 返回结构不统一：可能是 `ScanResult`，也可能是 `{code,message,data}`，前端需分支解析。
- 由于 `/scan` 成功后状态未写 `completed`，此接口可能长期报告 `running`。
- 无鉴权，任务数据可被枚举。

## 改进建议
- 统一响应模型，显式返回 `status/created_at/completed_at/error` 等字段。
- 修正任务状态机，保证状态与结果一致。
- 添加鉴权/速率限制，防止任务信息泄露。
