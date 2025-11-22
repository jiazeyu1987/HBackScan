# POST `/refresh/all`

- 入口：`code/hospital_scanner/main.py:241`
- 关联逻辑：`execute_full_refresh_task`（`main.py:435`）。
- 作用：触发完整数据刷新任务（当前为半成品，主要是模拟与日志）。

## 执行流程
1. 生成 `task_id`，向 `tasks` 表写入 `pending` 记录（hospital_name=“完整数据刷新任务”）。
2. **未放入 BackgroundTasks**，而是直接 `await execute_full_refresh_task`，阻塞当前请求。
3. `execute_full_refresh_task`：  
   - 将任务状态置为 `running`。  
   - 修改 `sys.path` 后再次导入 `TaskManager`（意义有限）。  
   - 获取数据库实例。  
   - 初始化 `LLMClient` 并做连通性测试（同步网络 IO，阻塞事件循环）。  
   - 向 LLM 请求全国省份列表，尝试解析 JSON，失败时用简单文本兜底。  
   - 将任务状态标记为 `completed`，随后为每个省份串行创建子任务并调用 `execute_province_refresh_task`（该函数存在 BUG，后续多半失败）。  
   - 绝大多数数据写库逻辑缺失，只是写日志。
4. 异常时将任务标记为 `failed` 并记录堆栈。

## 设计原因
- 期望通过一个入口触发全量采集，复用省级刷新逻辑。

## 优点
- 任务状态会落库，便于查询。
- 对 LLM 响应做了基本的 JSON 清洗容错。

## 缺点与风险
- 同步执行 + 同步 LLM IO，接口极易超时并阻塞整个事件循环。  
- 省级子任务调用 `TaskStatus.SUCCEEDED`（不存在的枚举值），导致子任务必抛异常，整体流程失败。  
- 无真实的省/市/区/医院入库逻辑，只有日志。  
- 无鉴权即可触发重度操作，可能耗尽 API 配额/算力。

## 改进建议
- 将刷新操作放入后台队列或 worker，HTTP 层仅返回 `task_id`。  
- LLM 请求改为异步/线程池，并增加重试、限流、超时。  
- 修正状态机（统一使用 `TaskStatus.COMPLETED`），实现幂等 upsert 写库。  
- 增加鉴权、速率限制与可选范围参数（只刷新部分区域）。
