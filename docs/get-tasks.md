# GET `/tasks`

- 入口：`code/hospital_scanner/main.py:230`
- 作用：返回任务列表（默认最多 100 条）。

## 执行流程
1. 直接调用 `TaskManager.list_tasks(limit=100)`，从数据库按 `created_at DESC` 拉取。
2. TaskManager 会将新任务写回内存缓存后原样返回列表。

## 设计原因
- 提供简单的任务总览，便于调试。

## 优点
- 实现简单，直接复用数据库排序。
- 内存缓存可被后续查询复用。

## 缺点与风险
- 无分页/过滤参数，数据量大时接口不控流。
- 未返回总数或统计信息，前端无法做分页 UI。
- 缺少鉴权/审计，任务列表可被任意访问。

## 改进建议
- 支持 `page/page_size/status` 等查询参数并返回分页元数据。
- 添加鉴权与速率限制。
- 考虑复用 `TaskManager.get_statistics` 暴露统计信息。
