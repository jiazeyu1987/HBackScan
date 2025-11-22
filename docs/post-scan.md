# POST `/scan`

- 入口：`code/hospital_scanner/main.py:173`
- 相关实现：`TaskManager.create_task`（`tasks.py`），`execute_scan_task`（`main.py:410`），`LLMClient.analyze_hospital_hierarchy`（`llm_client.py`）。
- 作用：创建医院层级扫描任务，并在后台调用 LLM 生成结果。

## 执行流程
1. FastAPI 解析 `ScanTaskRequest`（必填 `hospital_name`，可选 `query`/`options`）。
2. `TaskManager.create_task` 生成 `task_id`，在内存字典与 SQLite `tasks` 表写入状态 `pending`。
3. 将 `execute_scan_task(task_id, request)` 加入 `BackgroundTasks`。
4. 立即返回 `ScanTaskResponse`，状态标记为 `pending`。
5. `execute_scan_task` 异步运行：  
   - 将任务状态更新为 `running`（内存+数据库）。  
   - 调用全局 `llm_client.analyze_hospital_hierarchy`（内部使用同步 `requests` 调用外部 LLM，需 `LLM_API_KEY` 环境变量，否则初始化即抛错）。  
   - 构造 `ScanResult(status=completed)` 并通过 `TaskManager.save_task_result` 写入内存与数据库，同时保存医院详情到 `hospital_info`。  
   - 异常时仅将状态置为 `failed`，不返回错误详情给客户端。

## 设计原因
- 前台快速响应，耗时的 LLM 调用放入后台，避免阻塞 HTTP 请求。
- 结果与状态双存储（内存 + SQLite）以兼顾查询速度与持久化。

## 优点
- 任务模式适合高延迟的 LLM 调用。
- 使用 Pydantic 校验基础参数，避免空医院名。

## 缺点与风险
- 成功路径未将任务状态更新为 `completed`（只在结果对象里标记），`tasks` 表会长期停留在 `running`，导致前端轮询永不结束。
- LLMClient 在全局初始化时即检查 `LLM_API_KEY`，缺失时应用启动失败；此外 `_make_request` 使用同步 `requests`，在事件循环线程中阻塞。
- 缺少并发/速率控制与重试，容易触发 LLM 限流或把异常标记为永久失败。
- 未捕获/返回错误详情给调用方，调试困难。

## 改进建议
- 在 `execute_scan_task` 成功后调用 `update_task_status(..., TaskStatus.COMPLETED)`，并记录完成时间。
- 将 LLM 调用改为异步或移到线程池，避免阻塞事件循环；同时增加重试与超时控制。
- 为任务请求添加幂等键/速率限制，并在响应中返回更丰富的错误上下文。
