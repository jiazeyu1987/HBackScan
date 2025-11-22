# POST `/refresh/province/{province_name}`

- 入口：`code/hospital_scanner/main.py:271`
- 关联逻辑：`execute_province_refresh_task`（`main.py:789`）
- 作用：触发指定省份的城市数据刷新（当前为模拟实现且存在致命 Bug）。

## 执行流程
1. 生成 `task_id`，向 `tasks` 表插入一条 `pending` 记录（hospital_name 为“省份数据刷新: {province_name}”）。
2. 将 `execute_province_refresh_task` 加入 FastAPI `BackgroundTasks`，立即返回 `RefreshTaskResponse`。
3. 后台函数步骤：  
   - 校验参数类型并将任务状态置为 `running`。  
   - 导入并实例化 `LLMClient`。若未配置 `LLM_API_KEY`，实例化时抛异常导致任务失败。  
   - 获取数据库实例。  
   - 构造城市查询提示词，但随后跳过 LLM 调用，直接使用硬编码响应。  
   - 随即调用 `await task_manager.update_task_status(task_id, TaskStatus.SUCCEEDED)` 然后 `return`，意图直接标记成功。  
   - 后续 JSON 解析、数据落库逻辑被短路，不会执行。

## 设计原因
- 计划将省份刷新抽象为独立任务，便于全量刷新或单省刷新复用。
- 通过后台任务异步执行，避免阻塞 HTTP 请求。

## 优点
- 使用后台任务，接口返回速度快。
- 早期日志覆盖了多步进度，便于追踪。

## 缺点与风险
- `TaskStatus.SUCCEEDED` 在枚举中不存在，调用时会抛 AttributeError，任务必失败；调用者只能看到 running/failed。
- 跳过 LLM 调用且直接 `return`，没有任何数据写入 `provinces/cities`，接口功能名不副实。
- 数据库方法 `get_province_by_name` 查询表名写成 `province`（缺少 s），即便后续代码运行也会一直返回 None。
- LLM 调用使用同步 IO，将阻塞事件循环；缺少重试与限流。

## 改进建议
- 将状态值统一为 `TaskStatus.COMPLETED` 或新增枚举后全局替换。
- 恢复/实现真实的数据获取与落库逻辑，并对不存在的省份执行 upsert。
- 把 LLM 请求放入线程池或使用异步客户端，增加失败重试与限速。
- 返回结构中附带实时进度与错误信息，方便前端判断失败原因。
