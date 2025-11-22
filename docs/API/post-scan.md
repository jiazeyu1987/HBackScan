# POST `/scan`

- 入口：`code/hospital_scanner/main.py:173`
- 相关实现：`TaskManager.create_task`、`execute_scan_task`、`LLMClient.analyze_hospital_hierarchy`。
- 作用：创建医院层级扫描任务并后台调用 LLM。

## 执行流程
1. FastAPI 解析 `ScanTaskRequest`（必填 hospital_name）。
2. `TaskManager.create_task` 生成 `task_id`，在内存和 SQLite `tasks` 表写入 `pending`。
3. 将 `execute_scan_task(task_id, request)` 加入 `BackgroundTasks`，立即返回 `ScanTaskResponse`（状态 `pending`）。
4. 后台执行：  
   - 更新任务状态为 `running`（内存+数据库）。  
   - 调用全局 `llm_client.analyze_hospital_hierarchy`（同步 `requests` 调用外部 LLM；`LLM_API_KEY` 缺失时应用启动就会失败）。  
   - 构造 `ScanResult(status=completed)` 并通过 `TaskManager.save_task_result` 持久化结果与医院详情。  
   - 异常时仅将状态标记为 `failed`，未返回错误上下文给客户端。

## 设计原因
- 耗时的 LLM 调用放后台，前台快速返回任务 ID。
- 结果双存储（内存+SQLite）兼顾查询性能与持久化。

## 优点
- 任务模式适配高延迟操作。
- Pydantic 校验基础参数，避免空医院名。

## 缺点与风险
- 成功路径未将任务状态写回 `completed`（只在结果对象里），`tasks` 表会停留在 `running`，导致轮询逻辑失真。
- LLM 调用使用同步 IO 阻塞事件循环；缺少重试/限流。
- 未返回错误详情，调试困难。

## 改进建议
- 在成功后调用 `update_task_status(..., TaskStatus.COMPLETED)` 并记录完成时间。
- 将 LLM 请求改为异步或放线程池，增加重试/超时/速率控制。
- 丰富错误响应与任务上下文（失败原因、耗时），并支持幂等/限流。
