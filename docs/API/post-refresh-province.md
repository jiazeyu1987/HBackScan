# POST `/refresh/province/{province_name}`

- 入口：`code/hospital_scanner/main.py:271`
- 关联逻辑：`execute_province_refresh_task`（`main.py:789`）
- 作用：触发指定省份的城市数据刷新（当前为模拟实现且存在致命 Bug）。

## 执行流程
1. 生成 `task_id`，向 `tasks` 表插入 `pending` 记录（hospital_name=“省份数据刷新: {province_name}”）。
2. 将 `execute_province_refresh_task` 加入 `BackgroundTasks`，立即返回 `RefreshTaskResponse`。
3. 后台函数：  
   - 校验参数，状态置为 `running`。  
   - 导入并实例化 `LLMClient`，未配置 `LLM_API_KEY` 时抛异常。  
   - 获取数据库实例。  
   - 构造提示词但跳过真实 LLM 调用，直接使用硬编码响应。  
   - 随即调用 `update_task_status(task_id, TaskStatus.SUCCEEDED)` 并 `return`，后续解析/落库逻辑被短路。

## 设计原因
- 将省份刷新抽象成独立任务，便于全量/单省复用。
- 后台执行，避免阻塞 HTTP。

## 优点
- 接口响应快（后台任务执行）。
- 日志较多，便于定位步骤。

## 缺点与风险
- `TaskStatus.SUCCEEDED` 不存在，调用必抛 AttributeError，任务必失败；客户端只能看到 running/failed。
- 跳过 LLM 与落库，实际上没有写入任何省/市数据，功能名不符。
- 数据库 `get_province_by_name` 表名写成 `province`（缺 s），即便执行也会查不到。
- LLM 客户端使用同步 IO，阻塞事件循环；无重试/限流。

## 改进建议
- 统一使用合法枚举（`TaskStatus.COMPLETED`），或补充枚举后全局替换。
- 恢复真实的 LLM 调用与幂等 upsert 落库逻辑；修正表名。
- LLM 请求放入线程池/异步客户端，增加重试与速率限制。
- 返回/日志中增加进度与错误上下文，方便前端判断失败原因。
