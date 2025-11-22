# POST `/refresh/all`

- 入口：`code/hospital_scanner/main.py:241`
- 关联逻辑：`execute_full_refresh_task`（`main.py:435`）。
- 作用：触发“完整数据刷新”任务，按省份递归抓取行政区数据（当前实现仍为半成品/模拟）。

## 执行流程
1. 生成 `task_id`，在 `tasks` 表插入一条状态为 `pending` 的记录（hospital_name 填“完整数据刷新任务”）。
2. **未使用 `BackgroundTasks`**，而是直接 `await execute_full_refresh_task`，导致 HTTP 请求被长时间占用。
3. `execute_full_refresh_task` 内部步骤：  
   - 将任务置为 `running`。  
   - 调整 `sys.path`，导入 `TaskManager`（再次导入意义不大）。  
   - 获取数据库连接。  
   - 初始化 `LLMClient` 并调用 `_make_request` 进行连通性测试（同步网络请求，阻塞事件循环）。  
   - 向 LLM 发送“列出全部省份”的提示词并尝试解析 JSON；失败则粗暴按行拆分。  
   - 记录 `provinces` 数量后将任务状态置为 `completed`。  
   - 遍历每个省份：为每个省份创建子任务记录并串行调用 `execute_province_refresh_task`（当前函数内部为模拟实现，且包含 Bug）。  
   - 过程中大量日志、无实际数据入库。
4. 异常时将任务状态标记为 `failed` 并记录堆栈。

## 设计原因
- 期望通过一个入口触发全量行政区/医院数据的采集，串行调用省级刷新以复用逻辑。

## 优点
- 任务状态会写回数据库，便于后续查询。
- 对 LLM 响应尝试做 JSON 清洗，预留了容错。

## 缺点与风险
- 同步执行导致接口极易超时，且阻塞整个事件循环；LLM/网络异常会直接让 HTTP 请求挂死或长时间占用资源。
- 调用 `_make_request` 属同步 IO，事件循环无法处理其他请求。
- 省级子任务调用 `execute_province_refresh_task`，该函数内部使用不存在的 `TaskStatus.SUCCEEDED`，实际会抛 AttributeError，导致全量刷新必然失败。
- 未真正将省/市/区/医院数据写入数据库，实际效果只是写日志。
- 无鉴权即可清空并刷新全量数据，潜在安全/资源风险。

## 改进建议
- 将刷新操作放入后台队列（Celery、FastAPI BackgroundTasks 或单独 worker），HTTP 层仅返回 `task_id`。
- 用异步 HTTP 客户端或线程池封装 LLM 请求，避免阻塞。
- 修正状态机（统一使用 `TaskStatus.COMPLETED`），并实现真实的省/市/区/医院入库逻辑与幂等 Upsert。
- 为接口增加鉴权/速率限制，并允许指定仅刷新部分数据。
